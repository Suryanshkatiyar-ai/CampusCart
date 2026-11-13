
import os

from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text

from app.extensions import db
from app.models import User

load_dotenv()

login_manager = LoginManager()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def create_app():
    app = Flask(__name__)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "campuscart-development-key"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///campuscart.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message = "Please login to access this page."

    # Import models and routes
    from app import models
    from app.routes import main

    # Register routes
    app.register_blueprint(main)

    # Create database tables and update old database schema
    with app.app_context():
        db.create_all()

        listing_columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("listings")
        }

        if "moderation_status" not in listing_columns:
            db.session.execute(text("""
                ALTER TABLE listings
                ADD COLUMN moderation_status VARCHAR(20)
                NOT NULL DEFAULT 'APPROVED'
            """))
            db.session.commit()

    return app
