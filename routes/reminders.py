from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from models import ReminderModel

reminders_bp = Blueprint('reminders', __name__, url_prefix='/reminders')

CATEGORIES = ['Medicine', 'Water', 'Exercise', 'Appointment', 'Health Check', 'Sleep', 'Other']
FREQUENCIES = ['Once', 'Daily', 'Weekly', 'Monthly', 'Every 2 Hours', 'Every 4 Hours']
PRIORITIES = ['Low', 'Medium', 'High']

@reminders_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    category = request.args.get('category', 'All')
    status = request.args.get('status', 'All')
    date_filter = request.args.get('date', 'all')
    search = request.args.get('search', '').strip()

    reminders = ReminderModel.list_by_user(
        user_id,
        category=category,
        status=status,
        date_filter=date_filter,
        search=search
    )

    return render_template(
        'reminders/index.html',
        reminders=reminders,
        categories=CATEGORIES,
        frequencies=FREQUENCIES,
        priorities=PRIORITIES,
        selected_category=category,
        selected_status=status,
        selected_date=date_filter,
        search_query=search,
        today_str=date.today().isoformat()
    )

@reminders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    user_id = session['user_id']
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '').strip()
        reminder_date = request.form.get('date', '').strip()
        reminder_time = request.form.get('time', '').strip()
        frequency = request.form.get('frequency', 'Once')
        priority = request.form.get('priority', 'Medium')

        # Category specific fields
        dosage = request.form.get('dosage', '').strip() or None
        medicine_name = request.form.get('medicine_name', '').strip() or None
        target_volume = request.form.get('target_volume', '').strip() or None
        exercise_type = request.form.get('exercise_type', '').strip() or None
        duration_mins = request.form.get('duration_mins', type=int)
        metric_type = request.form.get('metric_type', '').strip() or None

        if not title or not reminder_date or not reminder_time:
            flash('Title, Date, and Time are required fields.', 'danger')
            return render_template(
                'reminders/form.html',
                action='Create',
                reminder={},
                categories=CATEGORIES,
                frequencies=FREQUENCIES,
                priorities=PRIORITIES,
                today_str=date.today().isoformat()
            )

        ReminderModel.create(
            user_id=user_id,
            title=title,
            category=category,
            description=description,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            frequency=frequency,
            priority=priority,
            dosage=dosage,
            medicine_name=medicine_name,
            target_volume=target_volume,
            exercise_type=exercise_type,
            duration_mins=duration_mins,
            metric_type=metric_type
        )

        flash(f'Reminder "{title}" has been successfully scheduled!', 'success')
        return redirect(url_for('reminders.index'))

    # Pre-filled values if passed as query params (e.g. category)
    prefill = {
        'category': request.args.get('category', 'Medicine'),
        'date': date.today().isoformat(),
        'time': datetime.now().strftime('%H:%M')
    }

    return render_template(
        'reminders/form.html',
        action='Create',
        reminder=prefill,
        categories=CATEGORIES,
        frequencies=FREQUENCIES,
        priorities=PRIORITIES,
        today_str=date.today().isoformat()
    )

@reminders_bp.route('/<int:reminder_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(reminder_id):
    user_id = session['user_id']
    reminder = ReminderModel.get_by_id(reminder_id, user_id)
    if not reminder:
        flash('Reminder not found or access denied.', 'danger')
        return redirect(url_for('reminders.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '').strip()
        reminder_date = request.form.get('date', '').strip()
        reminder_time = request.form.get('time', '').strip()
        frequency = request.form.get('frequency', 'Once')
        priority = request.form.get('priority', 'Medium')
        status = request.form.get('status', 'Pending')

        dosage = request.form.get('dosage', '').strip() or None
        medicine_name = request.form.get('medicine_name', '').strip() or None
        target_volume = request.form.get('target_volume', '').strip() or None
        exercise_type = request.form.get('exercise_type', '').strip() or None
        duration_mins = request.form.get('duration_mins', type=int)
        metric_type = request.form.get('metric_type', '').strip() or None

        if not title or not reminder_date or not reminder_time:
            flash('Title, Date, and Time are required fields.', 'danger')
            return render_template(
                'reminders/form.html',
                action='Edit',
                reminder=reminder,
                categories=CATEGORIES,
                frequencies=FREQUENCIES,
                priorities=PRIORITIES,
                today_str=date.today().isoformat()
            )

        ReminderModel.update(
            reminder_id=reminder_id,
            user_id=user_id,
            title=title,
            category=category,
            description=description,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            frequency=frequency,
            priority=priority,
            dosage=dosage,
            medicine_name=medicine_name,
            target_volume=target_volume,
            exercise_type=exercise_type,
            duration_mins=duration_mins,
            metric_type=metric_type,
            status=status
        )

        flash(f'Reminder "{title}" has been updated.', 'success')
        return redirect(url_for('reminders.index'))

    return render_template(
        'reminders/form.html',
        action='Edit',
        reminder=reminder,
        categories=CATEGORIES,
        frequencies=FREQUENCIES,
        priorities=PRIORITIES,
        today_str=date.today().isoformat()
    )

@reminders_bp.route('/<int:reminder_id>/delete', methods=['POST'])
@login_required
def delete(reminder_id):
    user_id = session['user_id']
    reminder = ReminderModel.get_by_id(reminder_id, user_id)
    if reminder:
        ReminderModel.delete(reminder_id, user_id)
        flash(f'Reminder "{reminder["title"]}" was removed.', 'info')
    else:
        flash('Reminder not found.', 'danger')

    next_page = request.referrer or url_for('reminders.index')
    return redirect(next_page)

@reminders_bp.route('/<int:reminder_id>/complete', methods=['POST'])
@login_required
def complete(reminder_id):
    user_id = session['user_id']
    notes = request.form.get('notes', '')
    success = ReminderModel.complete(reminder_id, user_id, notes=notes)
    if success:
        flash('Activity completed! History has been recorded.', 'success')
    else:
        flash('Unable to complete reminder.', 'danger')

    next_page = request.referrer or url_for('reminders.index')
    return redirect(next_page)

@reminders_bp.route('/<int:reminder_id>/snooze', methods=['POST'])
@login_required
def snooze(reminder_id):
    user_id = session['user_id']
    minutes = request.form.get('minutes', 10, type=int)
    success = ReminderModel.snooze(reminder_id, user_id, minutes=minutes)
    if success:
        flash(f'Reminder snoozed by {minutes} minutes.', 'info')
    else:
        flash('Unable to snooze reminder.', 'danger')

    next_page = request.referrer or url_for('reminders.index')
    return redirect(next_page)
