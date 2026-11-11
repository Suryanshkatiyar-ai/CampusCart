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

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        nullable=False
    )

    seller = db.relationship(
        "User",
        back_populates="listings"
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
