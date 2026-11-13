from flask_login import UserMixin
from datetime import datetime, timezone
from app.extensions import db


def current_time():
    return datetime.now(timezone.utc)


# ======================================
# USER TABLE
# ======================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(db.String(255), nullable=False)

    college = db.Column(db.String(150), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="student"
    )

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    listings = db.relationship(
        "Listing",
        back_populates="seller",
        cascade="all, delete-orphan"
    )

    requests = db.relationship(
        "ProductRequest",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    cart_items = db.relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    orders = db.relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"


# ======================================
# MARKETPLACE LISTINGS TABLE
# ======================================

class Listing(db.Model):

    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(120), nullable=False)

    description = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(50), nullable=False)

    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    listing_type = db.Column(
        db.String(20),
        nullable=False
    )

    condition = db.Column(db.String(30), nullable=False)

    image_url = db.Column(db.String(500), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    moderation_status = db.Column(
    db.String(20),
    nullable=False,
    default="PENDING"
)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    seller = db.relationship(
        "User",
        back_populates="listings"
    )

    cart_items = db.relationship(
        "CartItem",
        back_populates="listing",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Listing {self.title}>"


# ======================================
# WANTED PRODUCT REQUESTS TABLE
# ======================================

class ProductRequest(db.Model):

    __tablename__ = "product_requests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(120), nullable=False)

    category = db.Column(db.String(50), nullable=False)

    description = db.Column(db.Text, nullable=False)

    max_price = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(
        db.String(20),
        default="open",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="requests"
    )

    def __repr__(self):
        return f"<ProductRequest {self.title}>"

# ======================================
# CART ITEMS TABLE
# ======================================

class CartItem(db.Model):

    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id"),
        nullable=False
    )

    added_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "listing_id",
            name="unique_cart_listing"
        ),
    )

    user = db.relationship(
        "User",
        back_populates="cart_items"
    )

    listing = db.relationship(
        "Listing",
        back_populates="cart_items"
    )


# ======================================
# ORDERS TABLE
# ======================================

class Order(db.Model):

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PLACED"
    )

    fulfillment_method = db.Column(
        db.String(30),
        nullable=False,
        default="CAMPUS_PICKUP"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="orders"
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


# ======================================
# ORDER ITEMS TABLE
# ======================================

class OrderItem(db.Model):

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id"),
        nullable=True
    )

    product_title = db.Column(
        db.String(120),
        nullable=False
    )

    listing_type = db.Column(
        db.String(20),
        nullable=False
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    order = db.relationship(
        "Order",
        back_populates="items"
    )
