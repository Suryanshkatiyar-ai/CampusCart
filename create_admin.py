
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

def create_admin():

    print("\n================================")
    print("      CAMPUSCART ADMIN SETUP")
    print("================================\n")

    email = input("Admin email: ").strip().lower()

    if not email or "@" not in email:
        print("Invalid email address.")
        return

    password = getpass("Create admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if len(password) < 12:
        print("Admin password must have at least 12 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with app.app_context():

        user = User.query.filter_by(email=email).first()

        if user:

            print("\nExisting account found:", user.email)

            confirm = input(
                "Promote this existing account to ADMIN? (yes/no): "
            ).strip().lower()

            if confirm != "yes":
                print("Admin creation cancelled.")
                return

            user.role = "admin"
            user.is_verified = True

        else:

            full_name = input("Admin full name: ").strip()
            college = input("College / University: ").strip()

            if not full_name or not college:
                print("Name and college are required.")
                return

            user = User(
                full_name=full_name,
                email=email,
                college=college,
                password_hash=generate_password_hash(password),
                role="admin",
                is_verified=True
            )

            db.session.add(user)

        user.password_hash = generate_password_hash(password)

        try:

            db.session.commit()

            print("\nAdmin account created successfully!")
            print("Email:", email)
            print("Role:", user.role)
            print("Verified:", user.is_verified)

        except Exception:

            db.session.rollback()

            print("Unable to create admin account.")

if __name__ == "__main__":
    create_admin()