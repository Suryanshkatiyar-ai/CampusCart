from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.extensions import db
from app.models import User, Listing


main = Blueprint("main", __name__)


# ======================================
# HOMEPAGE
# ======================================

@main.route("/")
def home():

    products = [
        {
            "name": "Engineering Mathematics",
            "category": "Books",
            "price": 320,
            "mode": "SELL",
            "condition": "Gently Used",
            "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=900&q=85&fit=crop"
        },
        {
            "name": "Scientific Calculator",
            "category": "Electronics",
            "price": 450,
            "mode": "RENT",
            "condition": "Excellent Condition",
            "image": "https://images.pexels.com/photos/8276182/pexels-photo-8276182.jpeg?auto=compress&cs=tinysrgb&w=900"
        },
        {
            "name": "Wireless Headphones",
            "category": "Electronics",
            "price": 699,
            "mode": "SELL",
            "condition": "Like New",
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&q=85&fit=crop"
        },
        {
            "name": "Student Study Essentials",
            "category": "Stationery",
            "price": 250,
            "mode": "BORROW",
            "condition": "Good Condition",
            "image": "https://burst.shopifycdn.com/photos/school-supplies-knolling.jpg?width=1000&format=pjpg"
        }
    ]

    return render_template("index.html", products=products)


# ======================================
# STUDENT REGISTRATION
# ======================================

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

        # Required field validation
        if not all([full_name, email, college, password, confirm_password]):
            flash("Please fill in all the fields.", "error")
            return redirect(url_for("main.register"))

        # Basic email validation
        email_parts = email.split("@")

        if (
            len(email_parts) != 2
            or not email_parts[0]
            or "." not in email_parts[1]
            or email_parts[1].startswith(".")
            or email_parts[1].endswith(".")
        ):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("main.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("main.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("main.register"))

        # Check existing email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("main.register"))

        # Create new student
        new_user = User(
            full_name=full_name,
            email=email,
            college=college,
            password_hash=generate_password_hash(password),
            role="student",
            is_verified=False
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


# ======================================
# STUDENT LOGIN
# ======================================

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


# ======================================
# STUDENT LOGOUT
# ======================================

@main.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("main.home"))


# ======================================
# STUDENT DASHBOARD
# ======================================

@main.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user=current_user
    )

# ======================================
# CREATE MARKETPLACE LISTING
# ======================================

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

        # Allowed options
        allowed_categories = [
            "Books",
            "Electronics",
            "Stationery",
            "Lab Essentials",
            "Other"
        ]

        allowed_types = ["SELL", "RENT", "BORROW"]

        allowed_conditions = [
            "New",
            "Like New",
            "Good",
            "Fair"
        ]

        # Basic validation
        if not all([title, description, category, listing_type, condition]):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("main.create_listing"))

        if len(title) > 120 or len(description) > 2000:
            flash("Title or description is too long.", "error")
            return redirect(url_for("main.create_listing"))

        if category not in allowed_categories:
            flash("Invalid product category.", "error")
            return redirect(url_for("main.create_listing"))

        if listing_type not in allowed_types:
            flash("Invalid listing type.", "error")
            return redirect(url_for("main.create_listing"))

        if condition not in allowed_conditions:
            flash("Invalid product condition.", "error")
            return redirect(url_for("main.create_listing"))

        # Borrowing is free in this project
        if listing_type == "BORROW":
            price = Decimal("0.00")

        else:
            try:
                price = Decimal(price_text)
            except (InvalidOperation, TypeError):
                flash("Please enter a valid price.", "error")
                return redirect(url_for("main.create_listing"))

            if not price.is_finite() or price <= 0:
                flash("Price must be greater than zero.", "error")
                return redirect(url_for("main.create_listing"))

            if price > Decimal("99999999.99"):
                flash("Price is too high.", "error")
                return redirect(url_for("main.create_listing"))

        # Validate optional image URL
        if image_url:

            parsed_url = urlparse(image_url)

            if (
                len(image_url) > 500
                or parsed_url.scheme not in ("http", "https")
                or not parsed_url.netloc
            ):
                flash("Please enter a valid image URL.", "error")
                return redirect(url_for("main.create_listing"))

        # Create listing
        new_listing = Listing(
            seller_id=current_user.id,
            title=title,
            description=description,
            category=category,
            price=price,
            listing_type=listing_type,
            condition=condition,
            image_url=image_url or None,
            is_active=True
        )

        try:
            db.session.add(new_listing)
            db.session.commit()

            flash("Your product listing was created successfully!", "success")

            return redirect(url_for("main.dashboard"))

        except Exception:
            db.session.rollback()

            flash("Unable to create listing. Please try again.", "error")
            return redirect(url_for("main.create_listing"))

    return render_template("new_listing.html")
