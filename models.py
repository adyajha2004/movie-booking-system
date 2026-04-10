from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extension import db


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100))
    duration_min = db.Column(db.Integer)          # in minutes
    language = db.Column(db.String(50))
    rating = db.Column(db.Float, default=0.0)     # aggregate rating
    poster_url = db.Column(db.String(500))

    showtimes = db.relationship('Showtime', backref='movie', lazy=True)
    reviews = db.relationship('Review', backref='movie', lazy=True)


class Showtime(db.Model):
    __tablename__ = 'showtime'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    screen_no = db.Column(db.Integer, nullable=False)
    show_time_date = db.Column(db.Date, nullable=False)
    show_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)

    seats = db.relationship('Seat', backref='showtime', lazy=True)
    bookings = db.relationship('Booking', backref='showtime', lazy=True)


class Seat(db.Model):
    __tablename__ = 'seat'
    id = db.Column(db.Integer, primary_key=True)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtime.id'), nullable=False)
    row = db.Column(db.String(5), nullable=False)     # e.g. 'A', 'B'
    number = db.Column(db.Integer, nullable=False)    # e.g. 1, 2, 3
    type = db.Column(db.String(20), default='regular')  # regular / premium / recliner
    is_booked = db.Column(db.Boolean, default=False)


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtime.id'), nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed / cancelled
    total_price = db.Column(db.Float, nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    seats = db.relationship('BookingSeat', backref='booking', lazy=True)


class BookingSeat(db.Model):
    __tablename__ = 'booking_seat'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)    # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_review'),
    )