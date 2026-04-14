# 🎬 Movie Booking System (Flask)

A full-stack movie ticket booking web application built using **Flask**, featuring user authentication, movie management, showtime scheduling, and seat booking.

---

## 🚀 Features

### 👤 User Features

* User registration & login system
* Browse currently showing and upcoming movies
* View movie details with showtimes
* Book seats for a show
* View personal booking history

### 🎟️ Booking System

* Real-time seat selection
* Prevents double booking of seats
* Calculates total price dynamically
* Stores booking details with seat info

### 🧑‍💼 Admin Features

* Add new movies
* Create showtimes
* Add screens and auto-generate seats
* View all bookings (grouped by date)

### 🎨 UI Enhancements

* Dynamic color theme based on movie posters
* Clean and structured layout

---

## 🛠️ Tech Stack

* **Backend:** Flask
* **Database:** SQLite (via SQLAlchemy)
* **Authentication:** Flask-Login
* **Forms:** Flask-WTF / WTForms
* **Migrations:** Flask-Migrate
* **Image Processing:** ColorThief
* **Other:** Requests, Werkzeug

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd project
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate it:

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup

This project uses **SQLite**.

The database will be automatically created when you run the app:

```python
db.create_all()
```

---

## ▶️ Running the App

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## 📁 Project Structure

```
project/
│
├── app.py
├── models.py
├── form.py
├── extension.py
├── requirements.txt
│
├── templates/
├── static/
```

---

## 🔐 Default Behavior

* New users are created as normal users
* Admin access must be manually assigned (`is_admin = True` in database)

---

## ⚠️ Known Issues / Notes

* No payment gateway integration (demo only)
* SQLite used (not ideal for production)
* No role-based UI separation (admin routes protected only in backend)

---

## 🧠 Future Improvements

* Add payment integration (Stripe/Razorpay)
* Use PostgreSQL/MySQL for production
* Add seat layout UI improvements
* Implement REST API version
* Add email notifications

---

## 🙌 Credits

Built as a learning + project system using Flask ecosystem.

---

## 📬 Contact

For improvements or collaboration, feel free to reach out.

---

⭐ If you found this useful, consider starring the repo!
