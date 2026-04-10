# backend for the movie booking system
from flask import Flask, render_template, flash, redirect, session, url_for, request
from flask_migrate import migrate
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import StringField, PasswordField,BooleanField, TextAreaField, DateField, SubmitField, TimeField
from wtforms.validators import DataRequired, Email, equal_to
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extension import db, login_manager
from form import LoginForm, RegistrationForm
from models import User, Movie, Showtime, Seat, Booking, Review, BookingSeat


secret_key = 'aksaslknmckjdnoaekmdaksmc'  # Replace with a secure key in production
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # This give our code information of what, where and how our database is stored
#db = SQLAlchemy(app) #creating an instance of SQLAlchemy so we can use it to interact with our database... like storing it in a variable and calling variable when we need to access it

db.init_app(app)
login_manager.init_app(app)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# @login_manager.user_loader
# def load_user(user_id):
#     user_type = session.get("user_type")
#     if user_type == "admin":
#         return Admin.query.get(int(user_id))
#     else:
#         return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user = current_user, request = request)


# routes

@app.route('/')
def home():
    if not current_user.is_authenticated:
        flash('Please log in to access the home page.', 'info')
        return redirect(url_for('login'))
    
    movies = Movie.query.all()
    return render_template('home.html', movies=movies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        password = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, username=form.username.data, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Your account has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/movies')
def movies():
    movies = Movie.query.all()
    return render_template('movies.html', movies=movies)

@app.route('/booking_list')
@login_required
def booking_list():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    bookings = Booking.query.all()
    return render_template('booking_list.html', bookings=bookings)

@app.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('my_bookings.html', bookings=bookings)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)