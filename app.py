from flask import Flask, request, redirect, render_template, 
from flask import session
app.secret_key = "isurehopethisworks"  # change this to something more secure
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import os
import uuid  # at the top with other imports

app = Flask(__name__)

# Use SQLite (local file database)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)



# User table model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Home route
@app.route("/")
def home():
    return "<h1>Welcome to Friend Library 📚</h1><p><a href='/signup'>Sign Up</a> | <a href='/login'>Login</a></p>"

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
            session["user_guid"] = user.guid
            session["display_name"] = user.display_name

            return f"✅ Logged in! Welcome, {user.display_name}."
        else:
            return "❌ Invalid email or password"

    return render_template("login.html")


# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT
    app.run(host="0.0.0.0", port=port, debug=True)
