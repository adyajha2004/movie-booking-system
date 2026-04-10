from app import app
from extension import db
from models import *
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    print("Tables created!")

    admin = User.query.filter_by(username="admin").first()

    if not admin:
        admin = User(
            username="admin",
            name="Admin",
            password=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created!")
    else:
        print("Admin already exists.")