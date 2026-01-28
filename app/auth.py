import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User
# ✅ FIXED: Added KYCVerificationForm to imports
from app.forms import RegistrationForm, LoginForm, KYCVerificationForm

auth = Blueprint('auth', __name__)

# ==========================================
# 🛠️ HELPER: SECURE FILE SAVER
# ==========================================
def save_file(file_obj, folder_name):
    """Saves a file to a specific folder in static/uploads and returns the filename."""
    if not file_obj:
        return None
    
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file_obj.filename)
    filename = random_hex + f_ext
    
    # Build path
    folder_path = os.path.join(current_app.root_path, 'static/uploads', folder_name)
    
    # Create folder if it doesn't exist (Safety Check)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    file_path = os.path.join(folder_path, filename)
    file_obj.save(file_path)
    
    return filename

# ==========================================
# 🔐 AUTHENTICATION NODES
# ==========================================

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # ✅ FIXED: Changed 'user.password' to 'user.password_hash' to match your Model
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Transmission Established. Welcome, {user.username}.", "success")
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Failed. Identity mismatch or invalid key.', 'error')
            
    return render_template('login.html', title='Login', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        
        # Create User Instance
        new_user = User(
            username=form.username.data.lower(),
            email=form.email.data.lower(),
            role=form.role.data,
            is_driver=(form.role.data == 'driver')
        )
        new_user.set_password(form.password.data) # Uses the method from your Model

        db.session.add(new_user)
        db.session.commit()
        
        flash('Identity Registered. Terminal access granted.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', title='Register', form=form)

# ==========================================
# 🛡️ IDENTITY VERIFICATION NODE (NEW!)
# ==========================================
@auth.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_identity():
    # 1. Block if already verified
    if current_user.is_verified:
        flash("Identity already confirmed. You are a trusted node.", "info")
        return redirect(url_for('main.dashboard'))

    form = KYCVerificationForm()
    
    if form.validate_on_submit():
        # 2. Save the Evidence Files
        id_filename = save_file(form.id_image.data, 'kyc_docs')
        selfie_filename = save_file(form.selfie_image.data, 'kyc_selfies')
        
        # 3. Update User Record
        current_user.kyc_id_card_file = id_filename
        current_user.kyc_selfie_file = selfie_filename
        
        # Note: We do NOT set is_verified=True here. 
        # The Admin must approve it manually in the Admin Panel.
        
        db.session.commit()
        
        flash('Verification Data Transmitted. Pending Admin Approval.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('verify.html', title='Verify Identity', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash("Signal Terminated. Securely logged out.", "success")
    return redirect(url_for('main.index'))