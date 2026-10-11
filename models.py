from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

class UserModel:
    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        return db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()

    @staticmethod
    def get_by_email(email):
        db = get_db()
        return db.execute('SELECT * FROM users WHERE LOWER(email) = LOWER(?)', (email.strip(),)).fetchone()

    @staticmethod
    def create(name, email, password, phone='', role='user'):
        db = get_db()
        hashed = generate_password_hash(password)
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO users (name, email, password, phone, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (name.strip(), email.strip().lower(), hashed, phone.strip(), role))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update_profile(user_id, name, phone, password=None):
        db = get_db()
        if password and len(password.strip()) > 0:
            hashed = generate_password_hash(password)
            db.execute('''
                UPDATE users SET name = ?, phone = ?, password = ? WHERE user_id = ?
            ''', (name.strip(), phone.strip(), hashed, user_id))
        else:
            db.execute('''
                UPDATE users SET name = ?, phone = ? WHERE user_id = ?
            ''', (name.strip(), phone.strip(), user_id))
        db.commit()

    @staticmethod
    def list_all():
        db = get_db()
        return db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()

    @staticmethod
    def toggle_active(user_id):
        db = get_db()
        user = UserModel.get_by_id(user_id)
        if user:
            new_status = 0 if user['is_active'] else 1
            db.execute('UPDATE users SET is_active = ? WHERE user_id = ?', (new_status, user_id))
            db.commit()
            return new_status
        return None

    @staticmethod
    def set_role(user_id, role):
        db = get_db()
        db.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
        db.commit()


class ReminderModel:
    @staticmethod
    def create(user_id, title, category, description, reminder_date, reminder_time,
               frequency='Once', priority='Medium', dosage=None, medicine_name=None,
               target_volume=None, exercise_type=None, duration_mins=None, metric_type=None):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO reminders (
                user_id, title, category, description, date, time, frequency, priority,
                dosage, medicine_name, target_volume, exercise_type, duration_mins, metric_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (
            user_id, title.strip(), category, description.strip() if description else '',
            reminder_date, reminder_time, frequency, priority,
            dosage, medicine_name, target_volume, exercise_type, duration_mins, metric_type
        ))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(reminder_id, user_id=None):
        db = get_db()
        if user_id:
            return db.execute('SELECT * FROM reminders WHERE reminder_id = ? AND user_id = ?', (reminder_id, user_id)).fetchone()
        return db.execute('SELECT * FROM reminders WHERE reminder_id = ?', (reminder_id,)).fetchone()

    @staticmethod
    def list_by_user(user_id, category=None, status=None, date_filter=None, search=None):
        db = get_db()
        query = 'SELECT * FROM reminders WHERE user_id = ?'
        params = [user_id]

        if category and category != 'All':
            query += ' AND category = ?'
            params.append(category)

        if status and status != 'All':
            query += ' AND status = ?'
            params.append(status)

        today_str = date.today().isoformat()
        if date_filter == 'today':
            query += ' AND date = ?'
            params.append(today_str)
        elif date_filter == 'upcoming':
            query += ' AND (date > ? OR (date = ? AND time >= ?))'
            now_time = datetime.now().strftime('%H:%M')
            params.extend([today_str, today_str, now_time])
        elif date_filter == 'past':
            query += ' AND date < ?'
            params.append(today_str)

        if search and search.strip():
            query += ' AND (title LIKE ? OR description LIKE ? OR medicine_name LIKE ?)'
            term = f"%{search.strip()}%"
            params.extend([term, term, term])

        query += ' ORDER BY date ASC, time ASC'
        return db.execute(query, params).fetchall()

    @staticmethod
    def update(reminder_id, user_id, title, category, description, reminder_date, reminder_time,
               frequency, priority, dosage=None, medicine_name=None, target_volume=None,
               exercise_type=None, duration_mins=None, metric_type=None, status='Pending'):
        db = get_db()
        db.execute('''
            UPDATE reminders SET
                title = ?, category = ?, description = ?, date = ?, time = ?,
                frequency = ?, priority = ?, dosage = ?, medicine_name = ?,
                target_volume = ?, exercise_type = ?, duration_mins = ?,
                metric_type = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE reminder_id = ? AND user_id = ?
        ''', (
            title.strip(), category, description.strip() if description else '',
            reminder_date, reminder_time, frequency, priority,
            dosage, medicine_name, target_volume, exercise_type, duration_mins, metric_type,
            status, reminder_id, user_id
        ))
        db.commit()

    @staticmethod
    def delete(reminder_id, user_id):
        db = get_db()
        db.execute('DELETE FROM reminders WHERE reminder_id = ? AND user_id = ?', (reminder_id, user_id))
        db.commit()

    @staticmethod
    def complete(reminder_id, user_id, notes=None):
        """Marks reminder as completed and handles recurrence if recurring."""
        db = get_db()
        reminder = ReminderModel.get_by_id(reminder_id, user_id)
        if not reminder:
            return False

        # Add to reminder logs history
        db.execute('''
            INSERT INTO reminder_logs (reminder_id, user_id, reminder_title, category, scheduled_date, scheduled_time, action, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'Completed', ?)
        ''', (reminder['reminder_id'], user_id, reminder['title'], reminder['category'], reminder['date'], reminder['time'], notes or 'Completed on time'))

        # If water reminder, log water intake automatically if volume specified
        if reminder['category'] == 'Water' and reminder['target_volume']:
            try:
                # e.g., "250 ml" -> 250
                amount = int(''.join(filter(str.isdigit, reminder['target_volume'])))
                if amount > 0:
                    WaterLogModel.log(user_id, amount)
            except Exception:
                pass

        freq = reminder['frequency']
        cur_date_obj = datetime.strptime(reminder['date'], '%Y-%m-%d').date()

        if freq == 'Daily':
            next_date = (cur_date_obj + timedelta(days=1)).isoformat()
            db.execute('''
                UPDATE reminders SET date = ?, status = 'Pending', updated_at = CURRENT_TIMESTAMP WHERE reminder_id = ?
            ''', (next_date, reminder_id))
        elif freq == 'Weekly':
            next_date = (cur_date_obj + timedelta(days=7)).isoformat()
            db.execute('''
                UPDATE reminders SET date = ?, status = 'Pending', updated_at = CURRENT_TIMESTAMP WHERE reminder_id = ?
            ''', (next_date, reminder_id))
        elif freq == 'Monthly':
            # Approximate 30 days
            next_date = (cur_date_obj + timedelta(days=30)).isoformat()
            db.execute('''
                UPDATE reminders SET date = ?, status = 'Pending', updated_at = CURRENT_TIMESTAMP WHERE reminder_id = ?
            ''', (next_date, reminder_id))
        elif freq in ('Every 2 Hours', 'Every 4 Hours'):
            hours = 2 if freq == 'Every 2 Hours' else 4
            cur_time = datetime.strptime(reminder['time'], '%H:%M')
            next_dt = datetime.combine(cur_date_obj, cur_time.time()) + timedelta(hours=hours)
            db.execute('''
                UPDATE reminders SET date = ?, time = ?, status = 'Pending', updated_at = CURRENT_TIMESTAMP WHERE reminder_id = ?
            ''', (next_dt.strftime('%Y-%m-%d'), next_dt.strftime('%H:%M'), reminder_id))
        else:
            # One-off
            db.execute('''
                UPDATE reminders SET status = 'Completed', updated_at = CURRENT_TIMESTAMP WHERE reminder_id = ?
            ''', (reminder_id,))

        db.commit()
        return True

    @staticmethod
    def snooze(reminder_id, user_id, minutes=10):
        """Snoozes a reminder by N minutes."""
        db = get_db()
        reminder = ReminderModel.get_by_id(reminder_id, user_id)
        if not reminder:
            return False

        now = datetime.now()
        snoozed_dt = now + timedelta(minutes=minutes)

        db.execute('''
            UPDATE reminders SET date = ?, time = ?, status = 'Pending', updated_at = CURRENT_TIMESTAMP
            WHERE reminder_id = ? AND user_id = ?
        ''', (snoozed_dt.strftime('%Y-%m-%d'), snoozed_dt.strftime('%H:%M'), reminder_id, user_id))

        db.execute('''
            INSERT INTO reminder_logs (reminder_id, user_id, reminder_title, category, scheduled_date, scheduled_time, action, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'Snoozed', ?)
        ''', (reminder['reminder_id'], user_id, reminder['title'], reminder['category'], reminder['date'], reminder['time'], f'Snoozed by {minutes} minutes'))

        db.commit()
        return True

    @staticmethod
    def check_and_update_missed(user_id):
        """Updates past overdue pending reminders to Missed status."""
        db = get_db()
        today_str = date.today().isoformat()
        now_time = datetime.now().strftime('%H:%M')

        # Items strictly before today
        db.execute('''
            UPDATE reminders SET status = 'Missed', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'Pending' AND date < ?
        ''', (user_id, today_str))

        # Items today whose time is more than 30 minutes in the past
        thirty_min_ago = (datetime.now() - timedelta(minutes=30)).strftime('%H:%M')
        db.execute('''
            UPDATE reminders SET status = 'Missed', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'Pending' AND date = ? AND time < ?
        ''', (user_id, today_str, thirty_min_ago))

        db.commit()

    @staticmethod
    def get_due_reminders(user_id, window_minutes=2):
        """Returns reminders due within window_minutes around now for live notification triggers."""
        db = get_db()
        today_str = date.today().isoformat()
        now = datetime.now()
        start_time = (now - timedelta(minutes=1)).strftime('%H:%M')
        end_time = (now + timedelta(minutes=window_minutes)).strftime('%H:%M')

        return db.execute('''
            SELECT * FROM reminders
            WHERE user_id = ? AND status = 'Pending' AND date = ? AND time BETWEEN ? AND ?
        ''', (user_id, today_str, start_time, end_time)).fetchall()


class AppointmentModel:
    @staticmethod
    def create(user_id, doctor_name, specialization, hospital, apt_date, apt_time, notes=''):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, doctor_name, specialization, hospital, date, time, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled')
        ''', (user_id, doctor_name.strip(), specialization.strip() if specialization else '',
              hospital.strip() if hospital else '', apt_date, apt_time, notes.strip() if notes else ''))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(appointment_id, user_id=None):
        db = get_db()
        if user_id:
            return db.execute('SELECT * FROM appointments WHERE appointment_id = ? AND user_id = ?', (appointment_id, user_id)).fetchone()
        return db.execute('SELECT * FROM appointments WHERE appointment_id = ?', (appointment_id,)).fetchone()

    @staticmethod
    def list_by_user(user_id):
        db = get_db()
        return db.execute('''
            SELECT * FROM appointments WHERE user_id = ? ORDER BY date ASC, time ASC
        ''', (user_id,)).fetchall()

    @staticmethod
    def update(appointment_id, user_id, doctor_name, specialization, hospital, apt_date, apt_time, notes, status):
        db = get_db()
        db.execute('''
            UPDATE appointments SET
                doctor_name = ?, specialization = ?, hospital = ?, date = ?, time = ?, notes = ?, status = ?
            WHERE appointment_id = ? AND user_id = ?
        ''', (doctor_name.strip(), specialization.strip(), hospital.strip(), apt_date, apt_time, notes.strip(), status, appointment_id, user_id))
        db.commit()

    @staticmethod
    def delete(appointment_id, user_id):
        db = get_db()
        db.execute('DELETE FROM appointments WHERE appointment_id = ? AND user_id = ?', (appointment_id, user_id))
        db.commit()


class HealthMetricModel:
    @staticmethod
    def log(user_id, metric_type, value_primary, value_secondary=None, unit='', notes=''):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO health_metrics (user_id, metric_type, value_primary, value_secondary, unit, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, metric_type, value_primary, value_secondary, unit, notes.strip() if notes else ''))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def list_by_user(user_id, metric_type=None, limit=50):
        db = get_db()
        if metric_type and metric_type != 'All':
            return db.execute('''
                SELECT * FROM health_metrics WHERE user_id = ? AND metric_type = ? ORDER BY recorded_at DESC LIMIT ?
            ''', (user_id, metric_type, limit)).fetchall()
        return db.execute('''
            SELECT * FROM health_metrics WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?
        ''', (user_id, limit)).fetchall()

    @staticmethod
    def get_latest_summary(user_id):
        db = get_db()
        metrics = ['Blood Pressure', 'Blood Sugar', 'Weight', 'Heart Rate']
        summary = {}
        for m in metrics:
            row = db.execute('''
                SELECT * FROM health_metrics WHERE user_id = ? AND metric_type = ? ORDER BY recorded_at DESC LIMIT 1
            ''', (user_id, m)).fetchone()
            summary[m] = row
        return summary


class WaterLogModel:
    @staticmethod
    def log(user_id, amount_ml):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO water_logs (user_id, amount_ml) VALUES (?, ?)
        ''', (user_id, amount_ml))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_today_total(user_id):
        db = get_db()
        today_str = date.today().isoformat()
        row = db.execute('''
            SELECT COALESCE(SUM(amount_ml), 0) AS total
            FROM water_logs
            WHERE user_id = ? AND date(logged_at) = ?
        ''', (user_id, today_str)).fetchone()
        return row['total'] if row else 0


class NotificationModel:
    @staticmethod
    def create(user_id, title, message, reminder_id=None):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, reminder_id, title, message, status)
            VALUES (?, ?, ?, ?, 'Unread')
        ''', (user_id, reminder_id, title, message))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def list_unread(user_id):
        db = get_db()
        return db.execute('''
            SELECT * FROM notifications WHERE user_id = ? AND status = 'Unread' ORDER BY notification_time DESC
        ''', (user_id,)).fetchall()

    @staticmethod
    def mark_all_read(user_id):
        db = get_db()
        db.execute('''
            UPDATE notifications SET status = 'Read' WHERE user_id = ? AND status = 'Unread'
        ''', (user_id,))
        db.commit()


class ReminderLogModel:
    @staticmethod
    def list_by_user(user_id, category=None, action=None, search=None, limit=100):
        db = get_db()
        query = 'SELECT * FROM reminder_logs WHERE user_id = ?'
        params = [user_id]

        if category and category != 'All':
            query += ' AND category = ?'
            params.append(category)

        if action and action != 'All':
            query += ' AND action = ?'
            params.append(action)

        if search and search.strip():
            query += ' AND (reminder_title LIKE ? OR notes LIKE ?)'
            term = f"%{search.strip()}%"
            params.extend([term, term])

        query += ' ORDER BY action_timestamp DESC LIMIT ?'
        params.append(limit)
        return db.execute(query, params).fetchall()
