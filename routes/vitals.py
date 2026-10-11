from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from models import HealthMetricModel
from database import get_db

vitals_bp = Blueprint('vitals', __name__, url_prefix='/vitals')

@vitals_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    selected_metric = request.args.get('metric', 'All')

    metrics_list = HealthMetricModel.list_by_user(user_id, metric_type=selected_metric)
    summary = HealthMetricModel.get_latest_summary(user_id)

    return render_template(
        'vitals/index.html',
        metrics_list=metrics_list,
        summary=summary,
        selected_metric=selected_metric
    )

@vitals_bp.route('/log', methods=['POST'])
@login_required
def log_vital():
    user_id = session['user_id']
    metric_type = request.form.get('metric_type', '').strip()
    val_primary = request.form.get('value_primary', type=float)
    val_secondary = request.form.get('value_secondary', type=float)
    unit = request.form.get('unit', '').strip()
    notes = request.form.get('notes', '').strip()

    if not metric_type or val_primary is None:
        flash('Metric type and value are required.', 'danger')
        return redirect(url_for('vitals.index'))

    # Assign default units if not provided
    if not unit:
        defaults = {
            'Blood Pressure': 'mmHg',
            'Blood Sugar': 'mg/dL',
            'Weight': 'kg',
            'Heart Rate': 'bpm'
        }
        unit = defaults.get(metric_type, '')

    HealthMetricModel.log(
        user_id=user_id,
        metric_type=metric_type,
        value_primary=val_primary,
        value_secondary=val_secondary,
        unit=unit,
        notes=notes
    )

    flash(f'Logged {metric_type} reading successfully!', 'success')
    return redirect(url_for('vitals.index'))

@vitals_bp.route('/<int:metric_id>/delete', methods=['POST'])
@login_required
def delete(metric_id):
    user_id = session['user_id']
    db = get_db()
    db.execute('DELETE FROM health_metrics WHERE metric_id = ? AND user_id = ?', (metric_id, user_id))
    db.commit()
    flash('Reading deleted.', 'info')
    return redirect(url_for('vitals.index'))
