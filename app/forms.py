from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
from app.models import User

# ==========================================
# 🛰️ CUSTOM SIGNAL SHIELDS
# ==========================================
class SignalSizeLimit(object):
    """Prevents Signal Flooding by gating file size at the form level."""
    def __init__(self, max_size_mb):
        self.max_size = max_size_mb * 1024 * 1024

    def __call__(self, form, field):
        if field.data:
            if len(field.data.read()) > self.max_size:
                raise ValidationError(f"Signal too heavy. Maximum allowed size is {self.max_size / (1024*1024)}MB.")
            field.data.seek(0) # Reset pointer after reading

# ==========================================
# 👤 IDENTITY REGISTRATION
# ==========================================
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Deployment Type', choices=[
        ('user', 'Buy & Sell Items'), 
        ('driver', 'Logistics Pilot'),
        ('agent', 'Property Agent')
    ], default='user')
    submit = SubmitField('Initialize Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower()).first()
        if user:
            raise ValidationError('This coordinate (username) is already occupied.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email is already linked to a Tribe account.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Persistent Signal (Remember Me)')
    submit = SubmitField('Access Terminal')

# ==========================================
# 🛠️ DATA SYNCHRONIZATION (Profile & KYC)
# ==========================================
class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_pic = FileField('Update Identity Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg']),
        SignalSizeLimit(max_size_mb=2) # 2MB limit for avatars
    ])
    
    # Pilot-Specific Signals
    vehicle_type = StringField('Vehicle Model')
    vehicle_year = StringField('Vehicle Year')
    license_plate = StringField('License Plate')
    
    # KYC Signal Node
    id_card = FileField('Verification ID (NIN/License)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'pdf']),
        SignalSizeLimit(max_size_mb=5) # 5MB limit for IDs
    ])
    
    submit = SubmitField('Synchronize Data')

# ==========================================
# 📦 ASSET DEPLOYMENT (Marketplace)
# ==========================================
class SellItemForm(FlaskForm):
    title = StringField('Asset Title', validators=[DataRequired(), Length(min=5, max=100)])
    price = FloatField('Valuation (₦)', validators=[DataRequired()])
    section = SelectField('Listing Protocol', choices=[
        ('declutter', 'Declutter Item'), 
        ('shortlet', 'Shortlet Property')
    ], validators=[DataRequired()])
    category = SelectField('Asset Class', choices=[
        ('Electronics', 'Tech & Mobile'),
        ('Vehicles', 'Logistics & Motors'),
        ('Home', 'Home & Energy'),
        ('Fashion', 'Apparel & Style'),
        ('Real Estate', 'Real Estate / Hubs')
    ], validators=[DataRequired()])
    
    brand = StringField('Manufacturer/Brand')
    specifications = StringField('Core Metric (Size/Spec)')
    condition = SelectField('Condition Status', choices=[
        ('New', 'Mint Condition'),
        ('Like New', 'Used - High Grade'),
        ('Good', 'Used - Standard'),
        ('Fair', 'Used - Needs Maintenance')
    ])
    description = TextAreaField('Technical Narrative', validators=[DataRequired()])
    
    state = SelectField('Regional Hub', choices=[
        ('Lagos', 'Lagos'), ('Abuja', 'Abuja'), ('Rivers', 'Rivers'), ('Kano', 'Kano')
    ], validators=[DataRequired()])
    city = StringField('Specific Sector (City)', validators=[DataRequired()])
    
    image = FileField('Visual Documentation', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'png', 'jpeg']),
        SignalSizeLimit(max_size_mb=4) # 4MB limit for product shots
    ])
    submit = SubmitField('Deploy to Marketplace')

class WithdrawalForm(FlaskForm):
    amount = FloatField('Withdrawal Amount (₦)', validators=[DataRequired()])
    bank_name = StringField('Financial Institution', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=10, max=10)])
    account_name = StringField('Beneficiary Name', validators=[DataRequired()])
    submit = SubmitField('Initialize Off-Ramp')