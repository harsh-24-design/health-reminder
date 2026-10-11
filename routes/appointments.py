from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from models import AppointmentModel

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    appointments = AppointmentModel.list_by_user(user_id)
    return render_template(
        'appointments/index.html',
        appointments=appointments,
        today_str=date.today().isoformat()
    )

@appointments_bp.route('/new', methods=['POST'])
@login_required
def create():
    user_id = session['user_id']
    doctor_name = request.form.get('doctor_name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    hospital = request.form.get('hospital', '').strip()
    apt_date = request.form.get('date', '').strip()
    apt_time = request.form.get('time', '').strip()
    notes = request.form.get('notes', '').strip()

    if not doctor_name or not apt_date or not apt_time:
        flash('Doctor Name, Date, and Time are required.', 'danger')
        return redirect(url_for('appointments.index'))

    AppointmentModel.create(
        user_id=user_id,
        doctor_name=doctor_name,
        specialization=specialization,
        hospital=hospital,
        apt_date=apt_date,
        apt_time=apt_time,
        notes=notes
    )

    flash(f'Appointment with {doctor_name} scheduled successfully!', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/<int:appointment_id>/update', methods=['POST'])
@login_required
def update(appointment_id):
    user_id = session['user_id']
    doctor_name = request.form.get('doctor_name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    hospital = request.form.get('hospital', '').strip()
    apt_date = request.form.get('date', '').strip()
    apt_time = request.form.get('time', '').strip()
    notes = request.form.get('notes', '').strip()
    status = request.form.get('status', 'Scheduled')

    if not doctor_name or not apt_date or not apt_time:
        flash('Doctor Name, Date, and Time are required.', 'danger')
        return redirect(url_for('appointments.index'))

    AppointmentModel.update(
        appointment_id=appointment_id,
        user_id=user_id,
        doctor_name=doctor_name,
        specialization=specialization,
        hospital=hospital,
        apt_date=apt_date,
        apt_time=apt_time,
        notes=notes,
        status=status
    )

    flash('Appointment details updated successfully.', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/<int:appointment_id>/delete', methods=['POST'])
@login_required
def delete(appointment_id):
    user_id = session['user_id']
    AppointmentModel.delete(appointment_id, user_id)
    flash('Appointment removed.', 'info')
    return redirect(url_for('appointments.index'))
