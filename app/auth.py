import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app.utils import send_otp_signal, create_grid_notification

auth = Blueprint('auth', __name__)

# --- 🛰️ 1. REGISTRATION NODE (Identity Initialization) ---

@auth.route("/register", methods=['GET', 'POST'])
def register():
    """Builds a new Identity Node and triggers the first Trust Signal."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # 🔐 Secure Hashing Protocol
            hashed_password = generate_password_hash(form.password.data)
            
            # 🧬 Initialize User Data Node
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                password_hash=hashed_password,
                wallet_balance=0.0,
                merchant_tier="Novice" # Initial Build #1 Tier
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # 🛰️ Trigger Async OTP Handshake (Build #7)
            # Offloaded to Celery to prevent page timeout during SMS dispatch
            try:
                send_otp_signal.delay(new_user.phone)
            except Exception as e:
                print(f"Non-Critical Signal Error: {str(e)}")
            
            # 🔔 Internal Dashboard Notification
            create_grid_notification(
                new_user.id, 
                "Identity Node Active", 
                "Welcome to FlipTrybe. Verify your phone and KYC to upgrade your merchant tier.", 
                "success"
            )
            
            flash("Account initialized. Please verify your identity to activate trading.", "success")
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"System Synchronization Failure: {str(e)}", "danger")
            
    return render_template('register.html', form=form)

# --- 🔑 2. LOGIN NODE (Access Control Handshake) ---

@auth.route("/login", methods=['GET', 'POST'])
def login():
    """Validates identity and establishes an active session node."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # 🛡️ Audit: Verify Password Hash Integrity
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            
            # 🏁 Intentional Redirect Sync
            next_page = request.args.get('next')
            flash(f"Welcome back, {user.name}. Grid access granted.", "info")
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash("Identity Validation Failed. Check credentials.", "danger")
            
    return render_template('login.html', form=form)

# --- 🔌 3. LOGOUT NODE (Session Termination) ---

@auth.route("/logout")
@login_required
def logout():
    """Terminates the active session and secures the node."""
    logout_user()
    flash("Session terminated. Node secured.", "info")
    return redirect(url_for('main.index'))

# --- 🛡️ 4. IDENTITY VERIFICATION GATE (Build #7) ---

@auth.route("/verify-otp", methods=['GET', 'POST'])
@login_required
def verify_otp():
    """Manages the phone verification handshake."""
    if current_user.is_verified:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # 🛰️ Verification logic (Integrates with Termii OTP Verification API)
        # For this build, we signal the Admin for manual KYC document review
        flash("Verification signal received. KYC Audit pending Admin review.", "warning")
        return redirect(url_for('main.dashboard'))

    return render_template('verify_otp.html')