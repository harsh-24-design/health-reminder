from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash
from models import UserModel

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an administrator.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('user_role') != 'admin':
            flash('Access restricted to administrators.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()

        if not name or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html', name=name, email=email, phone=phone)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', name=name, email=email, phone=phone)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', name=name, email=email, phone=phone)

        existing = UserModel.get_by_email(email)
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_id = UserModel.create(name, email, password, phone, role='user')
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = 'user'

        flash(f'Welcome to Health Reminder, {name}! Your account has been created.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = UserModel.get_by_email(email)
        if not user or not check_password_hash(user['password'], password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user['is_active']:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('auth/login.html', email=email)

        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']

        flash(f'Welcome back, {user["name"]}!', 'success')
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = UserModel.get_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name:
            flash('Name cannot be empty.', 'danger')
            return render_template('auth/profile.html', user=user)

        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('auth/profile.html', user=user)
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return render_template('auth/profile.html', user=user)

        UserModel.update_profile(user['user_id'], name, phone, new_password if new_password else None)
        session['user_name'] = name
        flash('Your profile has been successfully updated.', 'success')
        user = UserModel.get_by_id(session['user_id'])

    return render_template('auth/profile.html', user=user)
