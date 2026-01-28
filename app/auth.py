import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User
from app.forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # 🛡️ Establish secure session
            login_user(user, remember=form.remember.data)
            
            flash(f"Transmission Established. Welcome, {user.name}.", "success")
            
            # 🛰️ Dynamic Routing Logic
            next_page = request.args.get('next')
            if next_page: return redirect(next_page)
            if user.is_admin: return redirect(url_for('admin.admin_panel'))
            if user.is_driver: return redirect(url_for('main.pilot_console'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Failed. Identity mismatch or invalid key.', 'error')
            
    return render_template('login.html', title='Login', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        
        # 🛠️ Helper function to save files safely
        def save_kyc_file(file_obj, prefix):
            if file_obj and file_obj.filename:
                random_hex = secrets.token_hex(4)
                fname = secure_filename(f"{prefix}_{random_hex}_{file_obj.filename}")
                # Ensure the folder exists on the server
                path = os.path.join(current_app.root_path, 'static', 'uploads', 'kyc')
                os.makedirs(path, exist_ok=True)
                file_obj.save(os.path.join(path, fname))
                return fname
            return None

        # 📸 Capture Files from Request
        # Note: Your HTML form must have enctype="multipart/form-data"
        kyc_selfie = save_kyc_file(request.files.get('kyc_selfie'), "SELFIE")
        kyc_id = save_kyc_file(request.files.get('kyc_id_card'), "ID")
        kyc_video = save_kyc_file(request.files.get('kyc_video'), "VIDEO")
        kyc_plate = save_kyc_file(request.files.get('kyc_plate'), "PLATE")

        # 🔐 Signal Sanitization
        phone_raw = request.form.get('phone', '')
        sanitized_phone = ''.join(filter(str.isdigit, phone_raw))

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # ✅ FIXED: Exact column match with models.py
        new_user = User(
            username=form.username.data.lower(),
            email=form.email.data.lower(),
            name=request.form.get('name'), # Ensure your HTML input has name="name"
            password=hashed_pw,
            phone=sanitized_phone,
            address=request.form.get('address'),
            state=request.form.get('state'),
            city=request.form.get('city'),
            role=form.role.data,
            is_driver=(form.role.data == 'driver'),
            
            # 👇 Mapped correctly to User class
            kyc_selfie_file=kyc_selfie,
            kyc_id_file=kyc_id,
            kyc_video_file=kyc_video,
            kyc_plate=kyc_plate, # This one has no _file suffix in model
            
            # Set profile picture
            image_file=kyc_selfie if kyc_selfie else 'default.jpg'
        )

        db.session.add(new_user)
        db.session.commit()
        
        flash('Identity Registered. Terminal access granted.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', title='Register', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash("Signal Terminated. Securely logged out.", "success")
    return redirect(url_for('main.index'))