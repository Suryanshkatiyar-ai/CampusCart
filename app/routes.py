"""CampusCart Flask routes.

Includes authentication, student dashboard, marketplace listings,
cart/checkout/orders, Smart Semester Kits, Wanted Product matching,
and admin moderation/management.

Prerequisites in app/models.py:
- User has UserMixin, role, created_at, listings, cart_items, orders.
- Listing has moderation_status, is_active, seller_id, seller relationship.
- CartItem has user_id, listing_id, added_at, listing relationship.
- Order has user_id, total_amount, status, fulfillment_method,
  created_at, items relationship.
- OrderItem has order_id, listing_id, product_title, listing_type, price.
- ProductRequest has user_id, title, category, description, max_price,
  status, created_at, user relationship.
"""

from functools import wraps
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.kit_data import BRANCHES, get_semester_kit
from app.models import CartItem, Listing, Order, OrderItem, ProductRequest, User


main = Blueprint("main", __name__)


# ============================================================================
# SHARED HELPERS AND ACCESS CONTROL
# ============================================================================

ALLOWED_CATEGORIES = {
    "Books",
    "Electronics",
    "Stationery",
    "Lab Essentials",
    "Other",
}

ALLOWED_LISTING_TYPES = {"SELL", "RENT", "BORROW"}
ALLOWED_CONDITIONS = {"New", "Like New", "Good", "Fair"}
MAX_PRICE = Decimal("99999999.99")


def admin_required(view):
    """Allow access only to authenticated users with the admin role."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def approved_active_listings():
    """Base query for listings visible to ordinary marketplace users."""
    return Listing.query.filter(
        Listing.is_active.is_(True),
        Listing.moderation_status == "APPROVED",
    )


def extract_keywords(text):
    """Return simple, normalized keywords for wanted-product matching."""
    stop_words = {
        "a", "an", "the", "is", "are", "for", "to", "in", "on",
        "of", "and", "or", "with", "need", "needed", "want", "wanted",
        "looking", "find", "please", "good", "condition", "any",
        "btech", "student", "students", "required",
    }
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {word for word in words if len(word) > 1 and word not in stop_words}


def find_matching_listings(wanted_request):
    """Find approved active listings matching category, keywords and budget."""
    listings = approved_active_listings().filter(
        Listing.category == wanted_request.category
    ).all()

    wanted_keywords = extract_keywords(
        f"{wanted_request.title} {wanted_request.description}"
    )
    max_budget = Decimal(str(wanted_request.max_price or 0))
    matches = []

    for listing in listings:
        # Do not show the request owner's own listing as a match.
        if listing.seller_id == wanted_request.user_id:
            continue

        # A zero/blank budget means no budget limit. Borrow listings are free.
        listing_price = Decimal(str(listing.price or 0))
        if (
            max_budget > 0
            and listing.listing_type != "BORROW"
            and listing_price > max_budget
        ):
            continue

        listing_keywords = extract_keywords(
            f"{listing.title} {listing.description}"
        )
        common_keywords = wanted_keywords.intersection(listing_keywords)

        if common_keywords:
            matches.append((len(common_keywords), listing))

    matches.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [listing for _score, listing in matches[:12]]


# ============================================================================
# HOMEPAGE AND MARKETPLACE
# ============================================================================

@main.route("/")
def home():
    search = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()

    listing_query = approved_active_listings()

    if search:
        search_term = f"%{search}%"
        listing_query = listing_query.filter(
            or_(
                Listing.title.ilike(search_term),
                Listing.description.ilike(search_term),
                Listing.category.ilike(search_term),
            )
        )

    if category in ALLOWED_CATEGORIES:
        listing_query = listing_query.filter(Listing.category == category)
    else:
        category = ""

    products = listing_query.order_by(Listing.created_at.desc()).all()

    return render_template(
        "index.html",
        products=products,
        search=search,
        selected_category=category,
    )


# ============================================================================
# STUDENT REGISTRATION, LOGIN AND LOGOUT
# ============================================================================

@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        college = request.form.get("college", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, college, password, confirm_password]):
            flash("Please fill in all the fields.", "error")
            return redirect(url_for("main.register"))

        if len(full_name) > 100 or len(email) > 150 or len(college) > 150:
            flash("One or more fields exceed the allowed length.", "error")
            return redirect(url_for("main.register"))

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("main.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("main.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("main.register"))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("main.register"))

        new_user = User(
            full_name=full_name,
            email=email,
            college=college,
            password_hash=generate_password_hash(password),
            role="student",
            is_verified=False,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Welcome to CampusCart! Your account is created.", "success")
            return redirect(url_for("main.dashboard"))
        except Exception:
            db.session.rollback()
            flash("Something went wrong. Please try again.", "error")

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login successful. Welcome back!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("main.home"))


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# ============================================================================
# CREATE, VIEW AND MODERATE MARKETPLACE LISTINGS
# ============================================================================

@main.route("/listing/new", methods=["GET", "POST"])
@login_required
def create_listing():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        listing_type = request.form.get("listing_type", "").strip().upper()
        condition = request.form.get("condition", "").strip()
        price_text = request.form.get("price", "").strip()
        image_url = request.form.get("image_url", "").strip()

        if not all([title, description, category, listing_type, condition]):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("main.create_listing"))

        if len(title) > 120 or len(description) > 2000:
            flash("Title or description is too long.", "error")
            return redirect(url_for("main.create_listing"))

        if category not in ALLOWED_CATEGORIES:
            flash("Invalid product category.", "error")
            return redirect(url_for("main.create_listing"))

        if listing_type not in ALLOWED_LISTING_TYPES:
            flash("Invalid listing type.", "error")
            return redirect(url_for("main.create_listing"))

        if condition not in ALLOWED_CONDITIONS:
            flash("Invalid product condition.", "error")
            return redirect(url_for("main.create_listing"))

        if listing_type == "BORROW":
            price = Decimal("0.00")
        else:
            try:
                price = Decimal(price_text)
            except (InvalidOperation, TypeError, ValueError):
                flash("Please enter a valid price.", "error")
                return redirect(url_for("main.create_listing"))

            if not price.is_finite() or price <= 0 or price > MAX_PRICE:
                flash("Please enter a valid price greater than zero.", "error")
                return redirect(url_for("main.create_listing"))

        if image_url:
            parsed_url = urlparse(image_url)
            if (
                len(image_url) > 500
                or parsed_url.scheme not in ("http", "https")
                or not parsed_url.netloc
            ):
                flash("Please enter a valid image URL.", "error")
                return redirect(url_for("main.create_listing"))

        new_listing = Listing(
            seller_id=current_user.id,
            title=title,
            description=description,
            category=category,
            price=price,
            listing_type=listing_type,
            condition=condition,
            image_url=image_url or None,
            is_active=True,
            moderation_status="PENDING",
        )

        try:
            db.session.add(new_listing)
            db.session.commit()
            flash(
                "Your listing has been submitted for admin approval!",
                "success",
            )
            return redirect(url_for("main.dashboard"))
        except Exception:
            db.session.rollback()
            flash("Unable to create listing. Please try again.", "error")
            return redirect(url_for("main.create_listing"))

    return render_template("new_listing.html")


@main.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    product = approved_active_listings().filter(
        Listing.id == listing_id
    ).first_or_404()

    return render_template("listing_detail.html", product=product)


# ============================================================================
# CART
# ============================================================================

@main.route("/cart/add/<int:listing_id>", methods=["POST"])
@login_required
def add_to_cart(listing_id):
    product = approved_active_listings().filter(
        Listing.id == listing_id
    ).first_or_404()

    if product.seller_id == current_user.id:
        flash("You cannot add your own listing to cart.", "error")
        return redirect(url_for("main.listing_detail", listing_id=listing_id))

    existing_item = CartItem.query.filter_by(
        user_id=current_user.id,
        listing_id=listing_id,
    ).first()

    if existing_item:
        flash("This product is already in your cart.", "error")
        return redirect(url_for("main.cart"))

    try:
        db.session.add(CartItem(user_id=current_user.id, listing_id=listing_id))
        db.session.commit()
        flash("Product successfully added to your cart!", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to add this product. Please try again.", "error")

    return redirect(url_for("main.cart"))


@main.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(
        user_id=current_user.id
    ).order_by(CartItem.added_at.desc()).all()

    total = sum(
        (
            Decimal(str(item.listing.price))
            for item in cart_items
            if item.listing is not None
            and item.listing.is_active
            and item.listing.moderation_status == "APPROVED"
            and item.listing.seller_id != current_user.id
        ),
        Decimal("0.00"),
    )

    return render_template("cart.html", cart_items=cart_items, total=total)


@main.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(
        id=item_id,
        user_id=current_user.id,
    ).first_or_404()

    try:
        db.session.delete(item)
        db.session.commit()
        flash("Product removed from cart.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to remove product.", "error")

    return redirect(url_for("main.cart"))


# ============================================================================
# CHECKOUT AND ORDER MANAGEMENT
# ============================================================================

@main.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("main.cart"))

    def item_is_unavailable(item):
        product = item.listing
        return (
            product is None
            or not product.is_active
            or product.moderation_status != "APPROVED"
            or product.seller_id == current_user.id
        )

    if any(item_is_unavailable(item) for item in cart_items):
        flash(
            "Some cart products are unavailable. Remove them before checkout.",
            "error",
        )
        return redirect(url_for("main.cart"))

    total = sum(
        (Decimal(str(item.listing.price)) for item in cart_items),
        Decimal("0.00"),
    )

    if request.method == "POST":
        try:
            # Re-fetch cart items and recheck availability before creating the order.
            valid_items = CartItem.query.filter_by(user_id=current_user.id).all()

            if not valid_items or any(item_is_unavailable(item) for item in valid_items):
                raise ValueError(
                    "A product is no longer available. Please review your cart."
                )

            final_total = sum(
                (Decimal(str(item.listing.price)) for item in valid_items),
                Decimal("0.00"),
            )

            new_order = Order(
                user_id=current_user.id,
                total_amount=final_total,
                status="PLACED",
                fulfillment_method="CAMPUS_PICKUP",
            )
            db.session.add(new_order)
            db.session.flush()

            for item in valid_items:
                product = item.listing

                db.session.add(
                    OrderItem(
                        order_id=new_order.id,
                        listing_id=product.id,
                        product_title=product.title,
                        listing_type=product.listing_type,
                        price=product.price,
                    )
                )

                product.is_active = False
                db.session.delete(item)

            db.session.commit()
            flash("Your order has been placed successfully!", "success")
            return redirect(
                url_for("main.order_detail", order_id=new_order.id)
            )

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
            return redirect(url_for("main.cart"))
        except Exception:
            db.session.rollback()
            flash("Order could not be placed. Please try again.", "error")
            return redirect(url_for("main.cart"))

    return render_template("checkout.html", cart_items=cart_items, total=total)


@main.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.created_at.desc()).all()

    return render_template("orders.html", orders=user_orders)


@main.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id,
    ).first_or_404()

    return render_template("order_detail.html", order=order)


# ============================================================================
# SMART SEMESTER KIT GENERATOR
# ============================================================================

@main.route("/semester-kits", methods=["GET"])
def semester_kits():
    branch = request.args.get("branch", "").strip()
    semester_value = request.args.get("semester", "").strip()

    kit_items = []
    matching_listings = []
    generated = False
    selected_semester = ""

    if branch or semester_value:
        try:
            semester = int(semester_value)
        except (ValueError, TypeError):
            semester = 0

        if branch not in BRANCHES or semester not in range(1, 9):
            flash("Please select a valid branch and semester.", "error")
        else:
            selected_semester = semester
            kit_items = get_semester_kit(branch, semester)
            categories = list({item["category"] for item in kit_items})

            if categories:
                matching_listings = approved_active_listings().filter(
                    Listing.category.in_(categories)
                ).order_by(Listing.created_at.desc()).limit(8).all()

            generated = True

    return render_template(
        "semester_kits.html",
        branches=BRANCHES,
        selected_branch=branch,
        selected_semester=selected_semester,
        kit_items=kit_items,
        matching_listings=matching_listings,
        generated=generated,
    )


# ============================================================================
# WANTED PRODUCTS AND SMART MATCHING
# ============================================================================

@main.route("/wanted")
def wanted_board():
    wanted_requests = ProductRequest.query.filter_by(
        status="open"
    ).order_by(ProductRequest.created_at.desc()).all()

    return render_template("wanted.html", wanted_requests=wanted_requests)


@main.route("/wanted/new", methods=["GET", "POST"])
@login_required
def create_wanted_request():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        budget_text = request.form.get("max_price", "").strip()

        if not title or not category or not description:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("main.create_wanted_request"))

        if len(title) > 120 or len(description) > 2000:
            flash("Title or description is too long.", "error")
            return redirect(url_for("main.create_wanted_request"))

        if category not in ALLOWED_CATEGORIES:
            flash("Please select a valid category.", "error")
            return redirect(url_for("main.create_wanted_request"))

        if budget_text:
            try:
                max_price = Decimal(budget_text)
            except (InvalidOperation, TypeError, ValueError):
                flash("Please enter a valid budget.", "error")
                return redirect(url_for("main.create_wanted_request"))

            if not max_price.is_finite() or max_price < 0 or max_price > MAX_PRICE:
                flash("Please enter a valid positive budget.", "error")
                return redirect(url_for("main.create_wanted_request"))
        else:
            max_price = Decimal("0.00")

        new_request = ProductRequest(
            user_id=current_user.id,
            title=title,
            category=category,
            description=description,
            max_price=max_price,
            status="open",
        )

        try:
            db.session.add(new_request)
            db.session.commit()
            flash("Your wanted request has been published!", "success")
            return redirect(
                url_for("main.wanted_detail", request_id=new_request.id)
            )
        except Exception:
            db.session.rollback()
            flash("Unable to publish your request. Please try again.", "error")

    return render_template("new_wanted.html")


@main.route("/wanted/<int:request_id>")
def wanted_detail(request_id):
    wanted_request = ProductRequest.query.filter_by(
        id=request_id,
        status="open",
    ).first_or_404()

    matched_listings = find_matching_listings(wanted_request)

    return render_template(
        "wanted_detail.html",
        wanted_request=wanted_request,
        matched_listings=matched_listings,
    )


# ============================================================================
# ADMIN DASHBOARD AND MANAGEMENT
# ============================================================================

@main.route("/admin")
@admin_required
def admin_dashboard():
    pending_listings = Listing.query.filter_by(
        moderation_status="PENDING"
    ).order_by(Listing.created_at.desc()).all()

    approved_listings = Listing.query.filter_by(
        moderation_status="APPROVED"
    ).order_by(Listing.created_at.desc()).limit(20).all()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    stats = {
        "total_users": User.query.count(),
        "total_listings": Listing.query.count(),
        "pending_listings": Listing.query.filter_by(
            moderation_status="PENDING"
        ).count(),
        "approved_listings": Listing.query.filter_by(
            moderation_status="APPROVED"
        ).count(),
        "total_orders": Order.query.count(),
    }

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        pending_listings=pending_listings,
        approved_listings=approved_listings,
        recent_orders=recent_orders,
        recent_users=recent_users,
    )


@main.route("/admin/listings/<int:listing_id>/moderate", methods=["POST"])
@admin_required
def moderate_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        abort(404)

    action = request.form.get("action", "").strip().lower()

    if action == "approve":
        listing.moderation_status = "APPROVED"
        listing.is_active = True
        message = "Listing approved successfully!"
    elif action == "reject":
        listing.moderation_status = "REJECTED"
        listing.is_active = False
        message = "Listing rejected successfully."
    else:
        flash("Invalid moderation action.", "error")
        return redirect(url_for("main.admin_dashboard"))

    try:
        db.session.commit()
        flash(message, "success")
    except Exception:
        db.session.rollback()
        flash("Unable to update listing.", "error")

    return redirect(url_for("main.admin_dashboard"))


@main.route("/admin/listings/<int:listing_id>/toggle", methods=["POST"])
@admin_required
def toggle_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        abort(404)

    if listing.moderation_status != "APPROVED":
        flash("Only approved listings can be managed here.", "error")
        return redirect(url_for("main.admin_dashboard"))

    listing.is_active = not listing.is_active

    try:
        db.session.commit()
        flash("Listing availability updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to update listing.", "error")

    return redirect(url_for("main.admin_dashboard"))


@main.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)

    new_status = request.form.get("status", "").strip().upper()
    allowed_statuses = {
        "CONFIRMED",
        "READY_FOR_PICKUP",
        "COMPLETED",
        "CANCELLED",
    }

    if new_status not in allowed_statuses:
        flash("Invalid order status.", "error")
        return redirect(url_for("main.admin_dashboard"))

    if order.status in {"COMPLETED", "CANCELLED"}:
        flash("This order is already in a final status.", "error")
        return redirect(url_for("main.admin_dashboard"))

    try:
        if new_status == "CANCELLED":
            # Restore only approved listings belonging to this order.
            for item in order.items:
                if item.listing_id is not None:
                    listing = db.session.get(Listing, item.listing_id)
                    if listing and listing.moderation_status == "APPROVED":
                        listing.is_active = True

        order.status = new_status
        db.session.commit()
        flash(
            f"Order #{order.id} status updated to {new_status}.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Unable to update order status.", "error")

    return redirect(url_for("main.admin_dashboard"))
