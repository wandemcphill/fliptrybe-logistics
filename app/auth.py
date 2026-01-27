from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        # Check if user exists and hash matches
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        
        # 🧠 Smart Redirect: Send them to their specific dashboard
        if user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        elif user.is_driver:
            return redirect(url_for('main.driver_dashboard'))
        elif user.is_agent:
            return redirect(url_for('main.agent_office'))
        else:
            return redirect(url_for('main.dashboard'))

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        phone = request.form.get('phone')
        role = request.form.get('role') # 👈 Capturing the role selection

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email address already exists.', 'error')
            return redirect(url_for('auth.register'))

        # 🎭 ROLE ASSIGNMENT LOGIC
        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method='sha256'),
            phone=phone,
            is_agent=(role == 'agent'),
            is_driver=(role == 'driver'),
            # Admin is never created via UI for security
            is_admin=False,
            wallet_balance=0.0
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    # ✅ FIXED: Changed 'register.html' to 'signup.html' to match your file
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))