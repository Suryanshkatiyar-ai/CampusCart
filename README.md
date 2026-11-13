# CampusCart – Secure Student E-Commerce Platform

CampusCart is a student-focused campus marketplace built with Python Flask. It helps students list, discover, request, and reserve academic and everyday items within a college community.

## Project Overview

CampusCart is designed to make campus exchanges more organized through student accounts, moderated product listings, a shopping cart, and order management. It also includes a semester-kit recommendation page and a wanted-products board that helps students find items they need.

## Key Features

- **Student authentication:** Register, log in, and log out securely.
- **Password security:** Passwords are stored as hashes, not plain text.
- **Product marketplace:** Students can create listings with a title, category, condition, price, listing type, description, and optional image URL.
- **Admin moderation:** New listings enter a pending state and can be approved or rejected by an administrator.
- **Shopping cart:** Add eligible listings to a cart and remove them before checkout.
- **Order management:** Place orders and view order history and order details.
- **Smart Semester Kits:** View suggested academic items based on branch and semester.
- **Wanted Products Board:** Post an item request and view matching marketplace listings.
- **Security controls:** CSRF protection, login-protected routes, and role-based admin access.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Jinja2 templates |
| Backend | Python, Flask |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login |
| Form security | Flask-WTF CSRF protection |
| Configuration | python-dotenv |

> **Database note:** The submitted version uses a local SQLite database. Azure SQL / cloud hosting is not required to run this version. Cloud deployment can be added later as a separate enhancement.

## Project Structure

```text
CampusCart/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes.py
│   ├── kit_data.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── new_listing.html
│   │   ├── listing_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── orders.html
│   │   ├── order_detail.html
│   │   ├── semester_kits.html
│   │   ├── wanted.html
│   │   ├── new_wanted.html
│   │   ├── wanted_detail.html
│   │   └── admin_dashboard.html
│   └── static/
│       ├── css/style.css
│       ├── js/main.js
│       └── images/
├── instance/                 # Local SQLite database is created here
├── create_admin.py           # Creates/promotes an administrator account
├── run.py                    # Application entry point
├── requirements.txt
├── .env                      # Local secrets; do not commit
└── README.md
```

## Requirements

- Python 3.10 or newer recommended
- pip
- Git (optional, for cloning the repository)

## Setup and Run (Windows / VS Code)

1. Open the project folder in VS Code.
2. Open the integrated terminal in the `CampusCart` project root.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation in the current terminal, run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

5. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

6. Create a `.env` file in the project root (next to `run.py`) with a unique local secret:

   ```env
   SECRET_KEY=replace-this-with-a-long-random-secret
   DATABASE_URL=sqlite:///campuscart.db
   ```

   Do not publish your real `.env` file or share its secret. If no `DATABASE_URL` is provided, the application is configured to use SQLite by default.

7. Start the application:

   ```powershell
   python run.py
   ```

8. Open the local URL shown in the terminal, normally:

   ```text
   http://127.0.0.1:5000
   ```

The database tables are created by the application when it starts. Keep the `instance` directory and its database file if you need to preserve local demo accounts and records.

## Create an Administrator Account

From the project root, with the virtual environment activated, run:

```powershell
python create_admin.py
```

Follow the prompts to enter an administrator email, name, and password. The password input may not display characters while typing; this is expected. Use a strong password and do not commit credentials to GitHub.

After the script completes:

1. Start the app with `python run.py` if it is not already running.
2. Open `http://127.0.0.1:5000/login`.
3. Sign in with the administrator account.
4. Open `http://127.0.0.1:5000/admin` to manage pending listings and orders.

## Typical Demo Flow

1. Register a student account and sign in.
2. Create a marketplace listing.
3. Sign in as the administrator and review the pending listing.
4. Approve the listing.
5. Return to the student account and add the approved item to the cart.
6. Proceed through checkout and view the order in the Orders section.
7. Explore Smart Semester Kits and the Wanted Products Board.

## Security and Deployment Notes

- Passwords are hashed using Werkzeug's password-hashing utilities.
- CSRF protection is enabled for supported form submissions.
- Administrative pages are restricted to users with the administrator role.
- Keep secret keys and credentials out of source control.
- This is an academic/local demonstration project. Before public production deployment, configure a strong environment-specific secret, HTTPS, secure cookie settings, database backups, logging, input validation, and a production WSGI server.
- Online payment processing, institutional email/OTP verification, and cloud deployment are not represented as completed features in this version.

## Academic Project Context

CampusCart can be discussed across these subject areas:

- **RDBMS:** relational entities, primary/foreign keys, relationships, and data persistence.
- **System Design:** student, listing, cart, order, wanted-request, and administrator workflows.
- **Cloud Security:** authentication, authorization, secret management, CSRF protection, and future secure deployment considerations.
- **DP-900 concepts:** relational data and SQL database concepts. The current submitted runtime uses SQLite; an Azure SQL deployment is a possible future extension.

## Author

Developed as an academic project: **CampusCart – Secure Student E-Commerce Platform**.
