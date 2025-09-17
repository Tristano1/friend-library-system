from flask import Flask, request, redirect, render_template, session
app.secret_key = ("SECRET_KEY", "dev-secret")
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import os
import uuid

app = Flask(__name__)

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
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        display_name = request.form["display_name"]

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "⚠️ Email already registered. Try logging in instead."

        # Hash password before saving
        hashed_pw = generate_password_hash(password, method="sha256")
        new_user = User(email=email, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")
    return render_template("signup.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Look up user by email
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # ✅ Successful login → store info in session
            session["user_guid"] = user.user_guid
            session["display_name"] = user.display_name

            return f"✅ Logged in! Welcome, {user.display_name}."
        else:
            return "❌ Invalid email or password"

    return render_template("login.html")

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

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT
    app.run(host="0.0.0.0", port=port, debug=True)
