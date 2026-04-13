# backend for the movie booking system
from collections import defaultdict

from flask import Flask, render_template, flash, redirect, session, url_for, request
from flask_migrate import migrate
from flask_wtf import CSRFProtect, FlaskForm
import requests
from wtforms import StringField, PasswordField,BooleanField, TextAreaField, DateField, SubmitField, TimeField
from wtforms.validators import DataRequired, Email, equal_to
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extension import db, login_manager
from form import LoginForm, RegistrationForm
from models import Screen, User, Movie, Showtime, Seat, Booking, Review, BookingSeat
from colorthief import ColorThief
import io


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

def get_dominant_color(image_url):
    """
    Takes an image URL, downloads it into memory, and returns the dominant Hex color.
    """
    if not image_url:
        return '#1a1a1a'  # A default dark color if no URL exists

    try:
        # Download the image data from the URL
        response = requests.get(image_url, timeout=5)
        response.raise_for_status() 
        
        # Wrap raw bytes in a file-like object for ColorThief
        image_stream = io.BytesIO(response.content)
        
        # Extract the dominant color
        color_thief = ColorThief(image_stream)
        dominant_rgb = color_thief.get_color(quality=1)
        
        # Convert RGB tuple to Hex string
        hex_code = '#%02x%02x%02x' % dominant_rgb
        return hex_code
        
    except Exception as e:
        print(f"Color extraction failed for {image_url}: {e}")
        return '#1a1a1a'  # Fallback color if the URL is broken or times out


def get_color_palette(image_url):
    """
    Takes an image URL and returns the top TWO dominant Hex colors for a gradient.
    """
    # Default fallback colors (a nice dark grey to black gradient) if no URL exists
    if not image_url:
        return '#1a1a1a', '#000000'  

    try:
        response = requests.get(image_url, timeout=5)
        response.raise_for_status() 
        
        image_stream = io.BytesIO(response.content)
        color_thief = ColorThief(image_stream)
        
        # Extract a palette of 2 colors
        palette = color_thief.get_palette(color_count=2, quality=1)
        
        # Convert both RGB tuples to Hex strings
        color1 = '#%02x%02x%02x' % palette[0]
        color2 = '#%02x%02x%02x' % palette[1]
        
        return color1, color2
        
    except Exception as e:
        print(f"Color extraction failed for {image_url}: {e}")
        return '#1a1a1a', '#000000' # Fallback

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
    all_bookings = Booking.query.all()

    grouped = defaultdict(list)

    for booking in all_bookings:
        # Fetch related data
        showtime = Showtime.query.get(booking.showtime_id)
        movie = Movie.query.get(showtime.movie_id)
        user = User.query.get(booking.user_id) # Getting the buyer!
        screen = Screen.query.get(showtime.screen_id)

        # Fetch and format seats
        booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
        seat_names = []
        for bs in booking_seats:
            seat = Seat.query.get(bs.seat_id)
            if seat:
                seat_names.append(f"{seat.row}{seat.number}")
        formatted_seats = ", ".join(seat_names)

        # Package everything together
        booking_info = {
            'booking': booking,
            'showtime': showtime,
            'movie': movie,
            'seats': formatted_seats,
            'screen': screen,
            'user': user
        }

        # Group by the DATE of the showtime
        date_key = showtime.show_time.date()
        grouped[date_key].append(booking_info)

    # Sort the dictionary so the newest dates appear at the top
    sorted_grouped = dict(sorted(grouped.items(), key=lambda item: item[0], reverse=True))

    return render_template('booking_list.html', grouped=sorted_grouped)

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

@app.route('/movie-detail/<int:movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    dynamic_hex = get_dominant_color(movie.poster_url)
    color1, color2 = get_color_palette(movie.poster_url)

    # 1. Determine the selected date (default to today)
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()

    # 2. Get all future/current showtimes for this movie to build the Date Selector
    now = datetime.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    all_showtimes = Showtime.query.filter(
        Showtime.movie_id == movie_id,
        Showtime.show_time >= start_of_today
    ).order_by(Showtime.show_time).all()

    # Extract unique dates for the top selector
    dates = []
    for st in all_showtimes:
        st_date = st.show_time.date()
        if st_date not in dates:
            dates.append(st_date)

    # 3. Group showtimes for the SELECTED date by Screen
    cinemas_dict = {}
    for st in all_showtimes:
        if st.show_time.date() == selected_date:
            # Skip past showtimes if the user is looking at today's schedule
            if st.show_time.date() == now.date() and st.show_time <= now:
                continue 

            screen = st.screen
            if screen.id not in cinemas_dict:
                cinemas_dict[screen.id] = {
                    'name': screen.name,
                    # We are passing a string here since your Screen model lacks a location column
                    'location': 'Dehradun', 
                    'showtimes': []
                }
            cinemas_dict[screen.id]['showtimes'].append(st)

    # Convert the dictionary into a list so Jinja can iterate over it easily
    cinemas = list(cinemas_dict.values())

    return render_template(
        'movie_detail.html', 
        movie=movie, 
        color1=color1, 
        color2=color2, 
        dates=dates,
        selected_date=selected_date,
        cinemas=cinemas
    )

@app.route('/book/<int:showtime_id>', methods=['GET', 'POST'])
@login_required
def book(showtime_id):
    # Fetch the exact showtime, movie, and screen
    showtime = Showtime.query.get_or_404(showtime_id)
    movie = showtime.movie
    screen = showtime.screen

    # 1. Get all seats for this specific screen
    all_seats = Seat.query.filter_by(screen_id=screen.id).order_by(Seat.row, Seat.number).all()

    # 2. THE MAGIC: Check which seats are booked FOR THIS SPECIFIC SHOWTIME
    booked_seat_records = BookingSeat.query.filter_by(showtime_id=showtime_id).all()
    booked_seat_ids = [bs.seat_id for bs in booked_seat_records]

    # 3. Group seats by Row letter (e.g., {'A': [Seat1, Seat2], 'B': [Seat1, Seat2]})
    seats_by_row = {}
    for seat in all_seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        seats_by_row[seat.row].append(seat)

    # 4. Handle the Booking Form Submission
    if request.method == 'POST':
        selected_seat_ids = request.form.get('selected_seats') 
        
        if not selected_seat_ids:
            flash('Please select at least one seat to continue.', 'danger')
            return redirect(url_for('book', showtime_id=showtime_id))
            
        # Convert the string of IDs ("1,2,3") into a list of integers [1, 2, 3]
        seat_id_list = [int(s_id) for s_id in selected_seat_ids.split(',')]

        # Calculate total
        total_price = len(seat_id_list) * showtime.price

        # Step A: Create the main Booking receipt
        new_booking = Booking(
            user_id=current_user.id,
            showtime_id=showtime_id,
            total_price=total_price
        )
        db.session.add(new_booking)
        db.session.flush() # Flush to get the new_booking.id before committing

        # Step B: Link the individual seats to the booking AND the showtime
        for seat_id in seat_id_list:
            # Race condition check: Did someone buy it in the last 5 seconds?
            if seat_id in booked_seat_ids:
                db.session.rollback()
                flash('Someone just booked one of those seats! Please select different ones.', 'danger')
                return redirect(url_for('book', showtime_id=showtime_id))
                
            bs = BookingSeat(
                booking_id=new_booking.id,
                seat_id=seat_id,
                showtime_id=showtime_id # <--- We are now saving the showtime_id here!
            )
            db.session.add(bs)

        # Save everything to the database
        db.session.commit()
        flash(f'Booking confirmed! Total paid: ₹{total_price}', 'success')
        return redirect(url_for('my_bookings'))

    return render_template('book.html', 
                           showtime=showtime, 
                           movie=movie, 
                           screen=screen, 
                           seats_by_row=seats_by_row, 
                           booked_seat_ids=booked_seat_ids)

@app.route('/my_bookings', methods=['GET', 'POST'])
def my_bookings():
    # 1. Get all bookings of the current user
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()

    grouped = defaultdict(list)
    now_showing = []
    now = datetime.now()

    for booking in bookings:
        # Fetch related data
        showtime = Showtime.query.get(booking.showtime_id)
        movie = Movie.query.get(showtime.movie_id)
        end_time = showtime.show_time + timedelta(minutes=movie.duration_min)

        # 2. Fetch all seats for this specific booking
        booking_seats = BookingSeat.query.filter_by(booking_id=booking.id).all()
        
        # Translate the seat IDs into readable names (e.g., "A1", "C4")
        seat_names = []
        for bs in booking_seats:
            seat = Seat.query.get(bs.seat_id)
            if seat:
                seat_names.append(f"{seat.row}{seat.number}")
        
        # Join them into a nice string: "A1, A2, A3"
        formatted_seats = ", ".join(seat_names)

        # 3. Package all the data together into a dictionary
        booking_info = {
            'booking': booking,
            'showtime': showtime,
            'movie': movie,
            'seats': formatted_seats,
            'screen': Screen.query.get(showtime.screen_id)
        }

        # 4. Sort into groups
        date_key = showtime.show_time.date()
        grouped[date_key].append(booking_info)

        # 🎬 NOW SHOWING
        if showtime.show_time.date() == now.date():
            now_showing.append(booking_info)

    return render_template(
        'my_bookings.html',
        grouped=grouped,
        now_showing=now_showing
    )

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
        
        # if the showtime is in the past, skip it (we only want to show current/future showtimes here)
        if end_time < now:
            continue
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