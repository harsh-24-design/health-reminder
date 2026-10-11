from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from models import ReminderModel, AppointmentModel, HealthMetricModel, WaterLogModel
from database import get_db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    user_id = session['user_id']

    # Update any past reminders to Missed status
    ReminderModel.check_and_update_missed(user_id)

    today_str = date.today().isoformat()
    now_time = datetime.now().strftime('%H:%M')

    # Today's reminders
    today_reminders = ReminderModel.list_by_user(user_id, date_filter='today')

    # Upcoming reminders (strictly future: today with time > now, or future dates)
    upcoming_reminders = ReminderModel.list_by_user(user_id, date_filter='upcoming')

    # Stats calculation
    total_today = len(today_reminders)
    completed_today = sum(1 for r in today_reminders if r['status'] == 'Completed')
    pending_today = sum(1 for r in today_reminders if r['status'] == 'Pending')
    missed_today = sum(1 for r in today_reminders if r['status'] == 'Missed')

    adherence_pct = int((completed_today / total_today * 100)) if total_today > 0 else 0

    # Water intake today
    water_today = WaterLogModel.get_today_total(user_id)
    water_goal = 2000 # Standard 2000ml
    water_pct = min(100, int((water_today / water_goal) * 100))

    # Health vitals summary
    vitals = HealthMetricModel.get_latest_summary(user_id)

    # Upcoming appointments (next 3)
    appointments = AppointmentModel.list_by_user(user_id)
    upcoming_appointments = [
        a for a in appointments
        if (a['date'] > today_str or (a['date'] == today_str and a['time'] >= now_time)) and a['status'] == 'Scheduled'
    ][:3]

    # Category counts for today
    categories = ['Medicine', 'Water', 'Exercise', 'Appointment', 'Health Check', 'Sleep', 'Other']
    cat_counts = {cat: 0 for cat in categories}
    for r in today_reminders:
        if r['category'] in cat_counts:
            cat_counts[r['category']] += 1

    return render_template(
        'dashboard/index.html',
        today_reminders=today_reminders,
        upcoming_reminders=upcoming_reminders[:5],
        total_today=total_today,
        completed_today=completed_today,
        pending_today=pending_today,
        missed_today=missed_today,
        adherence_pct=adherence_pct,
        water_today=water_today,
        water_goal=water_goal,
        water_pct=water_pct,
        vitals=vitals,
        upcoming_appointments=upcoming_appointments,
        cat_counts=cat_counts,
        current_date_display=date.today().strftime('%A, %B %d, %Y')
    )

@dashboard_bp.route('/quick-water', methods=['POST'])
@login_required
def quick_water():
    user_id = session['user_id']
    amount = request.form.get('amount', type=int)
    if amount and amount > 0:
        WaterLogModel.log(user_id, amount)
        flash(f'Logged {amount} ml of water! Keep staying hydrated.', 'success')
    return redirect(url_for('dashboard.index'))
