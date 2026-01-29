import os
import secrets
import requests
from datetime import datetime, timedelta
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app.utils import send_otp_signal

auth = Blueprint('auth', __name__)

# --- 🛰️ SIGNAL OPTIMIZATION (FILE HANDLING) ---

def save_signal_file(form_picture, folder):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    upload_root = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static/uploads'))
    picture_path = os.path.join(upload_root, folder, picture_fn)

    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    try:
        output_size = (800, 800)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    except Exception as e:
        form_picture.save(picture_path)

    return picture_fn

# --- 👥 REGISTRATION & AUTHENTICATION ---

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data, 
            email=form.email.data, 
            phone=form.phone.data, 
            password_hash=hashed_password 
        )
        db.session.add(user)
        db.session.commit()
        flash('Node Initialized! Please authenticate to secure your session.', 'success')
        return redirect(url_for('auth.login'))
        
    # 🟢 FIXED PATH: Now points to the auth subfolder
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            
            if not user.is_verified:
                flash("Signal unverified. Please secure your phone node.", "info")
                return redirect(url_for('auth.verify_phone'))
                
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Authentication Failed. Check your credentials.', 'danger')
            
    # 🟢 FIXED PATH: Now points to the auth subfolder
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    session.pop('otp_pin_id', None)
    session.pop('last_otp_sent', None)
    return redirect(url_for('main.index'))

# --- 📡 TERMII OTP VERIFICATION & COOLDOWN ---

@auth.route("/verify/resend")
@login_required
def resend_verification():
    last_sent = session.get('last_otp_sent')
    if last_sent:
        try:
            last_sent_time = datetime.fromisoformat(last_sent)
            if datetime.utcnow() < last_sent_time + timedelta(seconds=60):
                seconds_left = int((last_sent_time + timedelta(seconds=60) - datetime.utcnow()).total_seconds())
                flash(f"Signal cooling down. Please wait {seconds_left}s.", "warning")
                return redirect(url_for('auth.verify_phone'))
        except ValueError:
            session.pop('last_otp_sent', None)

    otp_data = send_otp_signal(current_user.phone)
    
    if otp_data and otp_data.get('pinId'):
        session['last_otp_sent'] = datetime.utcnow().isoformat()
        session['otp_pin_id'] = otp_data.get('pinId')
        flash(f"New security signal transmitted.", "success")
    else:
        flash("Signal transmission failed.", "danger")
        
    return redirect(url_for('auth.verify_phone'))

@auth.route("/verify-phone", methods=['GET', 'POST'])
@login_required
def verify_phone():
    if current_user.is_verified:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        pin_id = session.get('otp_pin_id')
        
        if not pin_id:
            flash("Session expired.", "warning")
            return redirect(url_for('auth.verify_phone'))
        
        url = "https://api.ng.termii.com/api/sms/otp/verify"
        payload = {
            "api_key": current_app.config.get('TERMII_API_KEY'), 
            "pin_id": pin_id, 
            "pin": otp
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            res = response.json()
            
            if res.get('verified') in [True, "True"]:
                current_user.is_verified = True
                db.session.commit()
                session.pop('otp_pin_id', None) 
                session.pop('last_otp_sent', None)
                flash("Identity Node Secured.", "success")
                return redirect(url_for('main.dashboard'))
            else:
                flash("Invalid code.", "danger")
        except Exception as e:
            flash("Communication error.", "danger")
        
    if not session.get('otp_pin_id'):
        otp_data = send_otp_signal(current_user.phone)
        if otp_data and otp_data.get('pinId'):
            session['otp_pin_id'] = otp_data.get('pinId')
            session['last_otp_sent'] = datetime.utcnow().isoformat()
            flash(f"Security Code transmitted.", "info")

    # 🟢 FIXED PATH: Point to auth/ subfolder
    return render_template('auth/verify_phone.html')

@auth.route('/kyc/upload', methods=['POST'])
@login_required
def upload_kyc():
    if 'selfie' in request.files and 'id_card' in request.files:
        selfie_file = request.files['selfie']
        id_card_file = request.files['id_card']
        
        if selfie_file.filename == '' or id_card_file.filename == '':
            flash("No selected file.", "warning")
            return redirect(url_for('main.dashboard'))

        try:
            selfie_fn = save_signal_file(selfie_file, 'kyc_docs')
            id_card_fn = save_signal_file(id_card_file, 'kyc_docs')
            current_user.kyc_selfie_file = selfie_fn
            current_user.kyc_id_card_file = id_card_fn
            db.session.commit()
            flash("KYC Documents uploaded.", "success")
        except Exception as e:
            flash(f"Upload failed: {str(e)}", "danger")
    else:
        flash("Incomplete files.", "danger")
        
    return redirect(url_for('main.dashboard'))