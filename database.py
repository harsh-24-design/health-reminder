import sqlite3
import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from flask import g, current_app

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initializes the database schema and seeds initial demonstration data."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Reminders Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                frequency TEXT NOT NULL DEFAULT 'Once',
                status TEXT NOT NULL DEFAULT 'Pending',
                priority TEXT NOT NULL DEFAULT 'Medium',
                dosage TEXT,
                medicine_name TEXT,
                target_volume TEXT,
                exercise_type TEXT,
                duration_mins INTEGER,
                metric_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

        # Appointments Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                doctor_name TEXT NOT NULL,
                specialization TEXT,
                hospital TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

        # Notifications Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'Unread',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (reminder_id) REFERENCES reminders(reminder_id) ON DELETE SET NULL
            )
        ''')

        # Reminder Logs (History Tracking) Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminder_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER,
                user_id INTEGER NOT NULL,
                reminder_title TEXT NOT NULL,
                category TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                action TEXT NOT NULL,
                action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (reminder_id) REFERENCES reminders(reminder_id) ON DELETE SET NULL
            )
        ''')

        # Health Vitals / Measurements Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                metric_type TEXT NOT NULL,
                value_primary REAL NOT NULL,
                value_secondary REAL,
                unit TEXT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

        # Water Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount_ml INTEGER NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

        db.commit()

        # Seed initial admin and sample user if not already present
        admin_check = cursor.execute("SELECT user_id FROM users WHERE email = 'admin@health.com'").fetchone()
        if not admin_check:
            admin_pw = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (name, email, password, phone, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Administrator', 'admin@health.com', admin_pw, '+1 800-555-0199', 'admin'))

        user_check = cursor.execute("SELECT user_id FROM users WHERE email = 'john@example.com'").fetchone()
        if not user_check:
            user_pw = generate_password_hash('john123')
            cursor.execute('''
                INSERT INTO users (name, email, password, phone, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('John Doe', 'john@example.com', user_pw, '+1 555-0143', 'user'))
            john_id = cursor.lastrowid

            today_str = date.today().isoformat()
            tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
            yesterday_str = (date.today() - timedelta(days=1)).isoformat()

            # Seed realistic reminders for John
            sample_reminders = [
                (john_id, 'Morning Metformin', 'Medicine', 'Take with breakfast', today_str, '08:00', 'Daily', 'Completed', 'High', '500 mg', 'Metformin', None, None, None, None),
                (john_id, 'Drink 500ml Water', 'Water', 'Stay hydrated during morning work session', today_str, '10:30', 'Every 2 Hours', 'Completed', 'Medium', None, None, '500 ml', None, None, None),
                (john_id, 'Blood Pressure Check', 'Health Check', 'Measure morning resting blood pressure', today_str, '14:00', 'Daily', 'Pending', 'High', None, None, None, None, None, 'Blood Pressure'),
                (john_id, 'Afternoon Walk', 'Exercise', 'Brisk 30 min park walk', today_str, '17:30', 'Daily', 'Pending', 'Medium', None, None, None, 'Walking', 30, None),
                (john_id, 'Night Multivitamin', 'Medicine', 'Take after dinner', today_str, '21:00', 'Daily', 'Pending', 'Low', '1 Tablet', 'Multivitamin', None, None, None, None),
                (john_id, 'Wind Down for Sleep', 'Sleep', 'No screens 30 mins before bed', today_str, '22:30', 'Daily', 'Pending', 'Medium', None, None, None, None, None, None),
                (john_id, 'Cardiologist Consultation', 'Appointment', 'Routine heart checkup with Dr. Sarah Smith', tomorrow_str, '11:00', 'Once', 'Pending', 'High', None, None, None, None, None, None)
            ]

            cursor.executemany('''
                INSERT INTO reminders (
                    user_id, title, category, description, date, time, frequency, status, priority,
                    dosage, medicine_name, target_volume, exercise_type, duration_mins, metric_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_reminders)

            # Seed sample appointment
            cursor.execute('''
                INSERT INTO appointments (user_id, doctor_name, specialization, hospital, date, time, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (john_id, 'Dr. Sarah Smith', 'Cardiologist', 'City General Hospital, Room 304', tomorrow_str, '11:00', 'Bring recent blood work and ECG reports', 'Scheduled'))

            # Seed sample health vitals
            cursor.execute('''
                INSERT INTO health_metrics (user_id, metric_type, value_primary, value_secondary, unit, recorded_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (john_id, 'Blood Pressure', 120, 80, 'mmHg', f"{yesterday_str} 09:00:00", 'Normal resting'))
            cursor.execute('''
                INSERT INTO health_metrics (user_id, metric_type, value_primary, value_secondary, unit, recorded_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (john_id, 'Blood Sugar', 98, None, 'mg/dL', f"{yesterday_str} 08:00:00", 'Fasting'))
            cursor.execute('''
                INSERT INTO health_metrics (user_id, metric_type, value_primary, value_secondary, unit, recorded_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (john_id, 'Weight', 72.5, None, 'kg', f"{yesterday_str} 07:30:00", 'Morning weight'))

            # Seed water logs
            cursor.execute('''
                INSERT INTO water_logs (user_id, amount_ml, logged_at)
                VALUES (?, ?, ?)
            ''', (john_id, 250, f"{today_str} 08:30:00"))
            cursor.execute('''
                INSERT INTO water_logs (user_id, amount_ml, logged_at)
                VALUES (?, ?, ?)
            ''', (john_id, 500, f"{today_str} 10:30:00"))

            # Seed sample log history
            cursor.execute('''
                INSERT INTO reminder_logs (reminder_id, user_id, reminder_title, category, scheduled_date, scheduled_time, action, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (1, john_id, 'Morning Metformin', 'Medicine', today_str, '08:00', 'Completed', 'Taken with whole wheat breakfast'))
            cursor.execute('''
                INSERT INTO reminder_logs (reminder_id, user_id, reminder_title, category, scheduled_date, scheduled_time, action, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (2, john_id, 'Drink 500ml Water', 'Water', today_str, '10:30', 'Completed', 'Hydration logged'))

        db.commit()
