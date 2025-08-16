from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object("config")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --------- Models ----------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(280))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    activities = db.relationship("Activity", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    mood = db.Column(db.String(30))
    category = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_text = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

# --------- Forms ----------
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

class ActivityForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("What did you do?", validators=[Length(max=5000)])
    is_public = BooleanField("Make this public?")
    mood = StringField("Mood (happy/sad/etc.)", validators=[Length(max=30)])
    category = StringField("Category (study, gym, work...)", validators=[Length(max=50)])
    latitude = FloatField("Latitude")
    longitude = FloatField("Longitude")
    location_text = StringField("Location (text)", validators=[Length(max=200)])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------- Routes ----------
@app.route("/")
def home():
    # Public feed (recent first)
    feed = Activity.query.filter_by(is_public=True).order_by(Activity.created_at.desc()).limit(50).all()
    return render_template("home.html", feed=feed)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        user = User(name=form.name.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome! Account created.", "success")
        return redirect(url_for("home"))
    return render_template("auth/register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        flash("Invalid credentials.", "error")
    return render_template("auth/login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("home"))

@app.route("/me")
@login_required
def me():
    my = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).all()
    return render_template("me.html", activities=my)

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ActivityForm()
    if form.validate_on_submit():
        act = Activity(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            is_public=form.is_public.data,
            mood=form.mood.data,
            category=form.category.data,
            latitude=form.latitude.data if form.latitude.data not in (None, "") else None,
            longitude=form.longitude.data if form.longitude.data not in (None, "") else None,
            location_text=form.location_text.data
        )
        db.session.add(act)
        db.session.commit()
        flash("Activity posted.", "success")
        return redirect(url_for("home"))
    return render_template("create.html", form=form)

@app.route("/u/<int:user_id>")
def profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Activity.query.filter_by(user_id=user.id, is_public=True).order_by(Activity.created_at.desc()).all()
    return render_template("profile.html", user=user, posts=posts)

@app.route("/api/feed")
def api_feed():
    items = Activity.query.filter_by(is_public=True).order_by(Activity.created_at.desc()).limit(100).all()
    return jsonify([{
        "id": a.id,
        "user": a.author.name,
        "title": a.title,
        "description": a.description,
        "mood": a.mood,
        "category": a.category,
        "lat": a.latitude,
        "lng": a.longitude,
        "location_text": a.location_text,
        "created_at": a.created_at.isoformat()
    } for a in items])

# CLI init
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
