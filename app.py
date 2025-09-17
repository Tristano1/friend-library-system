from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import os
import uuid

app = Flask(__name__)
app.secret_key = ("SECRET_KEY", "dev-secret")

# Use SQLite (local file database)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

default_global_loan_length = 21  # days

# ----------- MODELS --------------------
# User table model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    default_user_loan_length = db.Column(db.Integer, default=21)  # user-specific default
    is_active = db.Column(db.Boolean, default=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_length = db.Column(db.Integer, nullable=True)  # item-specific override

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Home route
@app.route("/")
def home():
    user_guid = session.get("user_guid")
    if user_guid:
        user = User.query.filter_by(user_guid=user_guid).first()
        if user:
            return f"Welcome, {user.display_name}!"
    return "Welcome to Friend Library! <a href='/signup'>Sign Up</a> | <a href='/login'>Login</a>"

# Sign up route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        display_name = request.form.get("display_name")

        if not email or not password or not display_name:
            error = "All fields are required."
        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = "This email is already registered. Try logging in."
            else:
                try:
                    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
                    new_user = User(
                        email=email,
                        password=hashed_password,
                        display_name=display_name
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    session["user_guid"] = new_user.user_guid
                    return redirect(url_for("home"))
                except Exception as e:
                    db.session.rollback()
                    error = f"Error creating account: {e}"

    return render_template("signup.html", error=error)


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_guid"] = user.user_guid
            return redirect(url_for("home"))
        else:
            error = "Invalid email or password."

    return render_template("login.html", error=error)


# Adding items stuff
@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    user_guid = session.get("user_guid")
    user = User.query.filter_by(guid=user_guid).first()
    if not user:
        return "User not found. Please log in first."

    if request.method == "POST":
        item_name = request.form["item_name"]
        loan_length = int(request.form["loan_length"])  # comes from the input box

        new_item = Item(
            name=item_name,
            owner_id=user.id,
            loan_length=loan_length  # always set from form
        )
        db.session.add(new_item)
        db.session.commit()
        return f"Added item '{item_name}' with loan length {loan_length} days."

    # When showing the form, pass in the user’s default loan length
    return render_template("add_item.html", default_loan_length=user.default_loan_length)

@app.route("/my_items")
def my_items():
    if "user_guid" not in session:
        return redirect("/login")

    user = User.query.filter_by(user_guid=session["user_guid"]).first()
    if not user:
        return redirect("/login")

    items = Item.query.filter_by(user_id=user.id).all()
    return render_template("my_items.html", items=items)


# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT
    app.run(host="0.0.0.0", port=port, debug=True)
