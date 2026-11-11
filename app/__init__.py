
import os

from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

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

    # Import models and create tables
    from app import models

    with app.app_context():
        db.create_all()

    # Register routes
    from app.routes import main
    app.register_blueprint(main)

    return app
