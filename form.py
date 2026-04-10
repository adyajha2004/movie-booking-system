from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class MovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    genre = StringField('Genre')
    duration_min = IntegerField('Duration (min)')
    language = StringField('Language')
    poster_url = StringField('Poster URL')
    submit = SubmitField('Add Movie')

class ShowtimeForm(FlaskForm):
    movie_id = SelectField('Movie', coerce=int, validators=[DataRequired()])
    screen_no = IntegerField('Screen Number', validators=[DataRequired()])
    show_time_date = DateField('Show Date', validators=[DataRequired()])
    show_time = TimeField('Show Time', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Showtime')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Comment')
    submit = SubmitField('Submit Review')

class BookingForm(FlaskForm):
    showtime_id = SelectField('Showtime', coerce=int, validators=[DataRequired()])
    seat_ids = StringField('Seat IDs (comma separated)', validators=[DataRequired()])
    submit = SubmitField('Book Now')
