from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import admin_required
from models import UserModel
from database import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    db = get_db()

    # System metrics
    total_users = db.execute('SELECT COUNT(*) AS c FROM users').fetchone()['c']
    total_reminders = db.execute('SELECT COUNT(*) AS c FROM reminders').fetchone()['c']
    completed_reminders = db.execute("SELECT COUNT(*) AS c FROM reminders WHERE status = 'Completed'").fetchone()['c']
    total_appointments = db.execute('SELECT COUNT(*) AS c FROM appointments').fetchone()['c']

    completion_rate = int((completed_reminders / total_reminders * 100)) if total_reminders > 0 else 0

    # Category breakdown
    cat_rows = db.execute('''
        SELECT category, COUNT(*) as count FROM reminders GROUP BY category ORDER BY count DESC
    ''').fetchall()
    categories_breakdown = {row['category']: row['count'] for row in cat_rows}

    # All users list
    users = UserModel.list_all()

    # Recent system logs
    recent_logs = db.execute('''
        SELECT l.*, u.name as user_name FROM reminder_logs l
        JOIN users u ON l.user_id = u.user_id
        ORDER BY l.action_timestamp DESC LIMIT 15
    ''').fetchall()

    return render_template(
        'admin/index.html',
        total_users=total_users,
        total_reminders=total_reminders,
        completed_reminders=completed_reminders,
        total_appointments=total_appointments,
        completion_rate=completion_rate,
        categories_breakdown=categories_breakdown,
        users=users,
        recent_logs=recent_logs
    )

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('admin.index'))

    new_status = UserModel.toggle_active(user_id)
    status_label = 'activated' if new_status else 'deactivated'
    flash(f'User account has been {status_label}.', 'info')
    return redirect(url_for('admin.index'))

@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def toggle_user_role(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot change your own administrative role.', 'warning')
        return redirect(url_for('admin.index'))

    user = UserModel.get_by_id(user_id)
    if user:
        new_role = 'user' if user['role'] == 'admin' else 'admin'
        UserModel.set_role(user_id, new_role)
        flash(f"Updated role for {user['name']} to {new_role.upper()}.", 'success')

    return redirect(url_for('admin.index'))
