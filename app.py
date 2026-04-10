# backend for the movie booking system
from collections import defaultdict

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
from models import Screen, User, Movie, Showtime, Seat, Booking, Review, BookingSeat


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


# functions
def format_date_with_suffix(value):
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value 
    else:
        date_obj = value

    day = date_obj.day
    if 11 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    return f"{day}{suffix} {date_obj.strftime('%B %Y')}"

app.jinja_env.filters['date_suffix'] = format_date_with_suffix

# routes

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # showing only movies that are currently showing today
    now = datetime.now()
    now_showing_movies = Movie.query.join(Showtime).filter(
        Showtime.show_time <= now
    ).distinct().all()
    return render_template('home.html', now_showing_movies=now_showing_movies)

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
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


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

@app.route('/movies')
def movies():
    now = datetime.now()

    movies = Movie.query.join(Showtime).filter(
        Showtime.show_time >= now
    ).distinct().all()

    return render_template('movies_admin.html', movies=movies)

@app.route('/add-movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    if request.method == 'POST':
        movie = Movie(
            title=request.form.get('title'),
            genre=request.form.get('genre'),
            duration_min=int(request.form.get('duration')),
            language=request.form.get('language'),
            poster_url=request.form.get('poster_url')
        )

        db.session.add(movie)
        db.session.commit()

        flash("Movie added!", "success")
        return redirect(url_for('movies'))

    return render_template('add_movie.html')

@app.route('/view/<int:movie_id>')
def view_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('view_movie.html', movie=movie)

@app.route('/movie-detail/<int:movie_id>', methods=['POST'])
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie_detail.html', movie=movie)

@app.route('/showtimes')
def showtimes():
    showtimes = Showtime.query.order_by(Showtime.show_time).all()

    grouped = defaultdict(list)
    now_showing = []

    now = datetime.now()

    for st in showtimes:
        movie = Movie.query.get(st.movie_id)
        end_time = st.show_time + timedelta(minutes=movie.duration_min)

        date_key = st.show_time.date()
        grouped[date_key].append((st, movie))

        # 🎬 NOW SHOWING
        if st.show_time <= now <= end_time:
            now_showing.append((st, movie, end_time))

    return render_template(
        'showtimes.html',
        grouped=grouped,
        now_showing=now_showing
    )

@app.route('/add-showtime', methods=['GET', 'POST'])
@login_required
def add_showtime():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    movies = Movie.query.all()
    screens = Screen.query.all()

    if request.method == 'POST':
        movie_id = int(request.form.get('movie_id'))
        screen_id = int(request.form.get('screen_id'))
        show_time_str = request.form.get('show_time')

        show_time = datetime.strptime(show_time_str, "%Y-%m-%dT%H:%M")
        
        movie = Movie.query.get(movie_id)
        
        # 1. Add a 20-minute buffer for theater cleaning
        cleaning_buffer = timedelta(minutes=20)
        
        new_start = show_time
        # The screen is "occupied" until the movie ends AND the cleaning is done
        new_end = show_time + timedelta(minutes=movie.duration_min) + cleaning_buffer

        # 2. Optimization: Only fetch showtimes for this specific day
        start_of_day = show_time.replace(hour=0, minute=0, second=0)
        end_of_day = start_of_day + timedelta(days=1)

        existing_showtimes = Showtime.query.filter(
            Showtime.screen_id == screen_id,
            Showtime.show_time >= start_of_day,
            Showtime.show_time < end_of_day
        ).all()

        # 3. CONFLICT CHECK
        for st in existing_showtimes:
            # Look how clean this is! We use the relationship (st.movie) instead of making a new query
            existing_end = st.show_time + timedelta(minutes=st.movie.duration_min) + cleaning_buffer

            if (st.show_time < new_end) and (existing_end > new_start):
                # Pro-tip: Include the conflicting movie name in the error message for better UX
                flash(f"Time conflict! {st.movie.title} is occupying this screen until {existing_end.strftime('%H:%M')}.", "danger")
                return redirect(url_for('add_showtime'))

        # If it passes the loop, save it!
        showtime = Showtime(
            movie_id=movie_id,
            screen_id=screen_id,
            show_time=show_time,
            price=float(request.form.get('price'))
        )

        db.session.add(showtime)
        db.session.commit()

        flash("Showtime added!", "success")
        return redirect(url_for('showtimes'))
    
    # movie shown right now
    now = datetime.now()
    
    # (Otherwise you will load years of history into memory!)
    four_hours_ago = now - timedelta(hours=4)
    
    recent_shows = Showtime.query.filter(
        Showtime.show_time <= now,
        Showtime.show_time >= four_hours_ago
    ).all()

    current_showtimes = []
    
    for st in recent_shows:
        movie_end_time = st.show_time + timedelta(minutes=st.movie.duration_min)
        
        if movie_end_time >= now:
            current_showtimes.append(st)

    return render_template('add_showtime.html', movies=movies, screens=screens, current_showtimes=current_showtimes)

@app.route('/screens')
def screens():
    screens = Screen.query.all()
    return render_template('screens.html', screens=screens)

@app.route('/add-screen', methods=['GET', 'POST'])
@login_required
def add_screen():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        rows = request.form.get('rows')   # e.g. A,B,C,D
        seats_per_row = int(request.form.get('seats'))

        screen = Screen(name=name)
        if Screen.query.filter_by(name=name).first():
            flash('Screen name already exists. Please choose a different one.', 'danger')
            return redirect(url_for('add_screen'))
        db.session.add(screen)
        db.session.commit()

        # AUTO GENERATE SEATS
        row_list = rows.split(',')

        for row in row_list:
            for num in range(1, seats_per_row + 1):
                seat = Seat(
                    screen_id=screen.id,
                    row=row.strip(),
                    number=num
                )
                db.session.add(seat)

        db.session.commit()

        flash("Screen + Seats created!", "success")
        return redirect(url_for('screens'))
    return render_template('add_screen.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)