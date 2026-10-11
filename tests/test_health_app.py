import os
import unittest
import tempfile
from datetime import date, datetime, timedelta
from app import create_app
from database import get_db, init_db
from models import UserModel, ReminderModel, AppointmentModel, HealthMetricModel, WaterLogModel

class HealthAppTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # 1. Test User Registration
    def test_user_registration_success(self):
        response = self.client.post('/auth/register', data={
            'name': 'Alice Wonder',
            'email': 'alice@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alice Wonder', response.data)

        with self.app.app_context():
            user = UserModel.get_by_email('alice@example.com')
            self.assertIsNotNone(user)
            self.assertEqual(user['name'], 'Alice Wonder')

    def test_user_registration_duplicate_email(self):
        # Register first
        self.client.post('/auth/register', data={
            'name': 'Bob Ross',
            'email': 'bob@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        # Logout so guest can submit registration
        self.client.get('/auth/logout')
        # Try duplicate
        response = self.client.post('/auth/register', data={
            'name': 'Bob Duplicate',
            'email': 'bob@example.com',
            'phone': '9999999999',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'An account with this email already exists', response.data)

    # 2. Test User Login
    def test_login_valid_credentials(self):
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'john123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, John Doe', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

    # 3. Test Reminder Creation & Details
    def test_create_medicine_reminder(self):
        # Login first
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        today_str = date.today().isoformat()
        response = self.client.post('/reminders/new', data={
            'title': 'Evening Insulin',
            'category': 'Medicine',
            'medicine_name': 'Insulin Glargine',
            'dosage': '10 units before dinner',
            'date': today_str,
            'time': '19:30',
            'frequency': 'Daily',
            'priority': 'High',
            'description': 'Subcutaneous injection'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Evening Insulin', response.data)

        with self.app.app_context():
            user = UserModel.get_by_email('john@example.com')
            reminders = ReminderModel.list_by_user(user['user_id'], search='Evening Insulin')
            self.assertEqual(len(reminders), 1)
            self.assertEqual(reminders[0]['dosage'], '10 units before dinner')
            self.assertEqual(reminders[0]['frequency'], 'Daily')

    # 4. Test Recurring Reminder Completion (Rescheduling to Next Day)
    def test_recurring_daily_reminder_completion(self):
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        today = date.today()
        today_str = today.isoformat()
        tomorrow_str = (today + timedelta(days=1)).isoformat()

        with self.app.app_context():
            user = UserModel.get_by_email('john@example.com')
            rid = ReminderModel.create(
                user_id=user['user_id'],
                title='Daily Vitamin C',
                category='Medicine',
                description='After meal',
                reminder_date=today_str,
                reminder_time='09:00',
                frequency='Daily',
                dosage='1000mg'
            )

        # Mark as completed
        response = self.client.post(f'/reminders/{rid}/complete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            updated = ReminderModel.get_by_id(rid)
            # Must be rescheduled to tomorrow and status reset to Pending
            self.assertEqual(updated['date'], tomorrow_str)
            self.assertEqual(updated['status'], 'Pending')

    # 5. Test Snooze Reminder
    def test_snooze_reminder(self):
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        with self.app.app_context():
            user = UserModel.get_by_email('john@example.com')
            rid = ReminderModel.create(
                user_id=user['user_id'],
                title='Drink Water Snooze Test',
                category='Water',
                description='',
                reminder_date=date.today().isoformat(),
                reminder_time='12:00',
                frequency='Once'
            )

        response = self.client.post(f'/reminders/{rid}/snooze', data={'minutes': 15}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            updated = ReminderModel.get_by_id(rid)
            self.assertEqual(updated['status'], 'Pending')

    # 6. Test Doctor Appointment Scheduling
    def test_doctor_appointment_crud(self):
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        apt_date = (date.today() + timedelta(days=3)).isoformat()
        response = self.client.post('/appointments/new', data={
            'doctor_name': 'Dr. Emily Watson',
            'specialization': 'Dentist',
            'hospital': 'Downtown Dental Clinic',
            'date': apt_date,
            'time': '14:00',
            'notes': 'Routine 6-month dental scaling'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dr. Emily Watson', response.data)

        with self.app.app_context():
            user = UserModel.get_by_email('john@example.com')
            appointments = AppointmentModel.list_by_user(user['user_id'])
            watson = [a for a in appointments if a['doctor_name'] == 'Dr. Emily Watson']
            self.assertEqual(len(watson), 1)

    # 7. Test Health Vitals Logging
    def test_log_health_vitals(self):
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        response = self.client.post('/vitals/log', data={
            'metric_type': 'Blood Pressure',
            'value_primary': 118,
            'value_secondary': 76,
            'unit': 'mmHg',
            'notes': 'Resting seated reading'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user = UserModel.get_by_email('john@example.com')
            summary = HealthMetricModel.get_latest_summary(user['user_id'])
            bp = summary['Blood Pressure']
            self.assertIsNotNone(bp)
            self.assertEqual(bp['value_primary'], 118.0)
            self.assertEqual(bp['value_secondary'], 76.0)

    # 8. Test Notifications Check API
    def test_notifications_poll_api(self):
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})

        response = self.client.get('/api/notifications/check-due')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('unread_count', data)
        self.assertIn('new_notifications', data)

    # 9. Test Administrator Access Control
    def test_admin_access_restricted_to_users(self):
        # Login as normal user
        self.client.post('/auth/login', data={'email': 'john@example.com', 'password': 'john123'})
        response = self.client.get('/admin/', follow_redirects=True)
        self.assertIn(b'Access restricted to administrators', response.data)

    def test_admin_access_allowed_for_admin(self):
        # Login as administrator
        self.client.post('/auth/login', data={'email': 'admin@health.com', 'password': 'admin123'})
        response = self.client.get('/admin/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrator Control Panel', response.data)
        self.assertIn(b'TOTAL USERS', response.data)

if __name__ == '__main__':
    unittest.main()
