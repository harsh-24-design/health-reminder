# Health Reminder Application 🩺⏰

A comprehensive, production-ready web application designed to help users manage their daily health-related activities through timely reminders, notifications, and adherence tracking.

Built directly in accordance with the **Health Reminder Application Specification & Requirements Document**.

---

## 🌟 Key Features

### 1. User Authentication & Profile Management
* **Secure Registration & Login**: Password hashing with Werkzeug (`pbkdf2:sha256`) and session-based authentication.
* **Role-Based Access Control**:
  * **User**: Manage personal reminders, doctor appointments, health vitals, and view history.
  * **Administrator**: Manage system users (activate/deactivate, toggle roles), monitor application-wide statistics, and view audit logs.
* **Profile Settings**: Update name, phone number, and change passwords securely.

### 2. Comprehensive Dashboard
* **Today's Schedule**: Real-time status of all activities scheduled for the day.
* **Adherence Progress**: Interactive progress bar and percentage of completed vs. pending tasks.
* **Hydration Tracker**: Daily water intake logger with instant `+250ml (Glass)` and `+500ml (Bottle)` quick buttons.
* **Health Vitals Quick Overview**: Displays latest Blood Pressure, Blood Sugar, Weight, and Heart Rate.
* **Upcoming Appointments**: Timeline of scheduled doctor visits.

### 3. Smart Reminders & Categories
* Organized by health activity categories:
  * 💊 **Medicine**: Drug name, dosage (e.g., `500 mg`), instructions (`After food`).
  * 💧 **Water**: Target hydration volume (e.g., `250 ml`), interval reminders.
  * 🏃 **Exercise**: Workout type (`Walking`, `Running`, `Yoga`, `Gym`), target duration in minutes.
  * 🩺 **Health Check**: Routine measurements (`Blood Pressure`, `Blood Sugar`, `Weight`, `Heart Rate`).
  * 😴 **Sleep**: Nighttime wind-down and sleep schedule routines.
  * 📅 **Appointment**: Linked to doctor visits.
  * 📌 **Other**: Custom daily health activities.
* **Recurring Scheduling (FR-10)**:
  * Supports `Once`, `Daily`, `Weekly`, `Monthly`, `Every 2 Hours`, `Every 4 Hours`.
  * Marking a recurring reminder as completed automatically logs the completion and computes the next scheduled date/time.
* **Overdue / Missed Detection**:
  * Automatically marks past-due reminders as `Missed`.
* **Snooze Functionality**:
  * Easily snooze reminders by 10 or 15 minutes when busy.

### 4. Real-Time Notification & Alert System
* **Browser Push Notifications**: Integrated with the HTML5 Web Notifications API for desktop alerts.
* **Synthesized Audio Chime**: Dual-tone chime synthesized in real-time via the Web Audio API (zero audio file dependencies).
* **In-App Toast Alerts**: Floating toasts with direct `Mark Done` and `Snooze 10m` buttons.
* **Notification Center**: Bell icon dropdown in navigation with unread count badge.

### 5. Doctor Appointments Management
* Track doctor consultations with Doctor Name, Specialization, Hospital/Clinic, Date, Time, and Status (`Scheduled`, `Attended`, `Cancelled`).

### 6. Health Vitals & Measurements Tracker
* Record and monitor clinical parameters:
  * Blood Pressure (Systolic & Diastolic mmHg)
  * Blood Glucose (mg/dL)
  * Body Weight (kg)
  * Heart Rate (bpm)
* Historical readings table with filtering and notes.

### 7. Activity History & Adherence Log
* Complete audit trail of completed, missed, and snoozed reminders.
* Search and filter by category and action.
* **CSV Export**: One-click download of activity history for personal records or sharing with doctors.

### 8. Administrator Control Panel
* System overview metrics (Total Users, Total Reminders, Overall Completion Rate, Total Appointments).
* Category distribution breakdown.
* User directory management (activate/deactivate accounts, toggle admin privileges).
* Recent system activity audit log.

---

## 🗄️ Database Architecture (SQLite)

The application uses an SQLite database (`health_app.db`) with foreign key constraints enabled:

* `users`: `user_id`, `name`, `email`, `password`, `phone`, `role`, `is_active`, `created_at`
* `reminders`: `reminder_id`, `user_id`, `title`, `category`, `description`, `date`, `time`, `frequency`, `status`, `priority`, `dosage`, `medicine_name`, `target_volume`, `exercise_type`, `duration_mins`, `metric_type`, `created_at`, `updated_at`
* `appointments`: `appointment_id`, `user_id`, `doctor_name`, `specialization`, `hospital`, `date`, `time`, `notes`, `status`, `created_at`
* `notifications`: `notification_id`, `user_id`, `reminder_id`, `title`, `message`, `notification_time`, `status`
* `reminder_logs`: `log_id`, `reminder_id`, `user_id`, `reminder_title`, `category`, `scheduled_date`, `scheduled_time`, `action`, `action_timestamp`, `notes`
* `health_metrics`: `metric_id`, `user_id`, `metric_type`, `value_primary`, `value_secondary`, `unit`, `recorded_at`, `notes`
* `water_logs`: `log_id`, `user_id`, `amount_ml`, `logged_at`

---

## 🛠️ Technology Stack

* **Backend**: Python 3.10+ / Flask 3.x
* **Database**: SQLite3
* **Security**: Werkzeug password hashing, session management
* **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, FontAwesome 6
* **Notifications**: Web Notifications API & Web Audio API
* **Testing**: Python `unittest` framework

---

## 🚀 Getting Started

### 1. Prerequisites
Python 3.10 or higher.

### 2. Installation
Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default Demo Accounts

Initial seed data is populated on first run:

| Role | Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@health.com` | `admin123` | Full access to Admin Panel & user management |
| **Standard User** | `john@example.com` | `john123` | Pre-populated with realistic reminders, appointments, and vitals |

You can also register a new account at `/auth/register`.

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
python -m unittest discover -s tests -v
```

All 12 unit and integration test cases cover:
* User registration and duplicate email prevention
* Authentication and session management
* Reminder creation with category-specific metadata
* Recurring reminder rescheduling (e.g. Daily recurrence +1 day)
* Snooze functionality
* Doctor appointment management
* Health vitals recording
* Overdue/missed status transitions
* Notification polling API
* Admin role-based access control
