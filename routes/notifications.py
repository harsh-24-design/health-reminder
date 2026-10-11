from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from models import ReminderModel, NotificationModel
from database import get_db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/check-due')
@login_required
def check_due():
    user_id = session['user_id']
    due_reminders = ReminderModel.get_due_reminders(user_id, window_minutes=2)

    db = get_db()
    ten_min_ago = (datetime.now() - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')

    notifications_to_send = []

    for r in due_reminders:
        # Check if we already created an unread notification recently for this reminder
        existing = db.execute('''
            SELECT notification_id FROM notifications
            WHERE user_id = ? AND reminder_id = ? AND notification_time >= ?
        ''', (user_id, r['reminder_id'], ten_min_ago)).fetchone()

        if not existing:
            title = f"Reminder: {r['title']}"
            msg_details = []
            if r['category'] == 'Medicine' and r['dosage']:
                msg_details.append(f"Dosage: {r['dosage']}")
            if r['category'] == 'Water' and r['target_volume']:
                msg_details.append(f"Drink: {r['target_volume']}")
            if r['description']:
                msg_details.append(r['description'])

            body = " | ".join(msg_details) if msg_details else f"Your {r['category']} reminder is scheduled for {r['time']}."

            nid = NotificationModel.create(user_id, title, body, reminder_id=r['reminder_id'])
            notifications_to_send.append({
                'notification_id': nid,
                'reminder_id': r['reminder_id'],
                'title': title,
                'category': r['category'],
                'message': body,
                'time': r['time']
            })

    # Also fetch existing unread notifications count
    unread_rows = NotificationModel.list_unread(user_id)
    unread_list = [
        {
            'notification_id': row['notification_id'],
            'reminder_id': row['reminder_id'],
            'title': row['title'],
            'message': row['message'],
            'notification_time': str(row['notification_time'])
        }
        for row in unread_rows
    ]

    return jsonify({
        'status': 'ok',
        'due_count': len(notifications_to_send),
        'new_notifications': notifications_to_send,
        'unread_count': len(unread_list),
        'unread_notifications': unread_list
    })

@notifications_bp.route('/mark-read', methods=['POST'])
@login_required
def mark_read():
    user_id = session['user_id']
    NotificationModel.mark_all_read(user_id)
    return jsonify({'status': 'success'})
