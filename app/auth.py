import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
        if not user or not check_password_hash(user.password, password):
            flash('Invalid credentials.', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=remember)
        
        # Route based on Role
        if user.is_admin: return redirect(url_for('main.admin_dashboard'))
        elif user.is_driver: return redirect(url_for('main.driver_dashboard'))
        elif user.is_agent: return redirect(url_for('main.agent_office'))
        else: return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))

        # 📂 UNIVERSAL FILE SAVER HELPER
        def save_file(file_obj, prefix):
            if file_obj and file_obj.filename:
                fname = secure_filename(f"{prefix}_{email}_{file_obj.filename}")
                path = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
                os.makedirs(path, exist_ok=True)
                file_obj.save(os.path.join(path, fname))
                return fname
            return None

        # 📸 Save Files
        kyc_selfie = save_file(request.files.get('kyc_selfie'), "SELFIE")
        kyc_id = save_file(request.files.get('kyc_id_card'), "ID")
        kyc_video = save_file(request.files.get('kyc_video'), "VIDEO")
        kyc_plate = save_file(request.files.get('kyc_plate'), "PLATE")

        new_user = User(
            email=email,
            name=request.form.get('name'),
            password=generate_password_hash(request.form.get('password'), method='sha256'),
            
            # Contact & Location
            phone=request.form.get('phone'),
            whatsapp=request.form.get('whatsapp'),
            mobile_2=request.form.get('mobile_2'),
            whatsapp_2=request.form.get('whatsapp_2'),
            address=request.form.get('address'),
            state=request.form.get('state'),
            city=request.form.get('city'),

            # Roles
            is_agent=(role == 'agent'),
            is_driver=(role == 'driver'),
            is_admin=False,

            # KYC Files
            kyc_selfie=kyc_selfie,
            kyc_id_card=kyc_id,
            kyc_video=kyc_video,
            kyc_plate=kyc_plate,
            
            # Default Profile Pic is the Selfie
            profile_pic=kyc_selfie
        )

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))