import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm, KYCVerificationForm

auth = Blueprint('auth', __name__)

def save_signal_file(file_obj, folder):
    if not file_obj: return None
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file_obj.filename)
    filename = random_hex + f_ext
    path = os.path.join(current_app.root_path, 'static/uploads', folder)
    if not os.path.exists(path): os.makedirs(path)
    file_obj.save(os.path.join(path, filename))
    return filename

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.lower(),
            email=form.email.data.lower(),
            role=form.role.data,
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            is_driver=(form.role.data == 'driver'),
            is_agent=(form.role.data == 'agent')
        )
        user.set_password(form.password.data)
        
        # Identity Signal Capture
        if 'kyc_selfie' in request.files:
            user.kyc_selfie_file = save_signal_file(request.files['kyc_selfie'], 'kyc_docs')
        if 'kyc_id_card' in request.files:
            user.kyc_id_card_file = save_signal_file(request.files['kyc_id_card'], 'kyc_docs')

        db.session.add(user)
        db.session.commit()
        flash('Terminal Identity Created.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.dashboard'))
        flash('Signal Error: Identity Key Invalid.', 'error')
    return render_template('login.html', form=form)

@auth.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_identity():
    form = KYCVerificationForm()
    if form.validate_on_submit():
        current_user.kyc_id_card_file = save_signal_file(form.id_image.data, 'kyc_docs')
        current_user.kyc_selfie_file = save_signal_file(form.selfie_image.data, 'kyc_docs')
        db.session.commit()
        flash('Signals Transmitted for HQ Audit.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('verify.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))