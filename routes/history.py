import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, request, session, Response
from routes.auth import login_required
from models import ReminderLogModel

history_bp = Blueprint('history', __name__, url_prefix='/history')

CATEGORIES = ['Medicine', 'Water', 'Exercise', 'Appointment', 'Health Check', 'Sleep', 'Other']
ACTIONS = ['Completed', 'Missed', 'Snoozed']

@history_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    category = request.args.get('category', 'All')
    action = request.args.get('action', 'All')
    search = request.args.get('search', '').strip()

    logs = ReminderLogModel.list_by_user(
        user_id,
        category=category,
        action=action,
        search=search,
        limit=200
    )

    return render_template(
        'history/index.html',
        logs=logs,
        categories=CATEGORIES,
        actions=ACTIONS,
        selected_category=category,
        selected_action=action,
        search_query=search
    )

@history_bp.route('/export-csv')
@login_required
def export_csv():
    user_id = session['user_id']
    category = request.args.get('category', 'All')
    action = request.args.get('action', 'All')
    search = request.args.get('search', '').strip()

    logs = ReminderLogModel.list_by_user(
        user_id,
        category=category,
        action=action,
        search=search,
        limit=1000
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Log ID', 'Reminder Title', 'Category', 'Scheduled Date', 'Scheduled Time', 'Action', 'Action Timestamp', 'Notes'])

    for log in logs:
        writer.writerow([
            log['log_id'],
            log['reminder_title'],
            log['category'],
            log['scheduled_date'],
            log['scheduled_time'],
            log['action'],
            log['action_timestamp'],
            log['notes'] or ''
        ])

    csv_data = output.getvalue()
    filename = f"health_reminder_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
