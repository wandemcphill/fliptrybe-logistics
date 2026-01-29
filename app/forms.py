from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, SelectField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User

# --- 👥 IDENTITY PROTOCOLS ---

class RegistrationForm(FlaskForm):
    """
    Standard Node Initialization Form.
    Includes database checks to prevent duplicate identities.
    """
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email Node', validators=[DataRequired(), Email()])
    phone = StringField('Phone Signal', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Security Key', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Key', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Initialize Node')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email signal is already active on the Grid. Please login.')

    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError('This phone node is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email Node', validators=[DataRequired(), Email()])
    password = PasswordField('Security Key', validators=[DataRequired()])
    remember = BooleanField('Remember Session')
    submit = SubmitField('Authenticate')

class OTPForm(FlaskForm):
    """6-Digit Security Handshake for Phone Verification."""
    otp = StringField('Security Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify Signal')

class KYCForm(FlaskForm):
    """Identity Verification Uploads (Tier 2 Access)."""
    selfie = FileField('Live Capture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    id_card = FileField('Government ID', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'pdf'])])
    submit = SubmitField('Upload Documents')

# --- 📦 ASSET DEPLOYMENT ---

class ListingForm(FlaskForm):
    """
    Asset Injection Form.
    Enforces strict categorization for the 'market/shortlet/declutter' logic.
    """
    title = StringField('Asset Title', validators=[DataRequired(), Length(max=100)])
    price = DecimalField('Unit Price (₦)', validators=[DataRequired(), NumberRange(min=500, message="Minimum listing price is ₦500")])
    
    category = SelectField('Category', choices=[
        ('Electronics', 'Electronics'),
        ('Vehicles', 'Vehicles'),
        ('Real Estate', 'Real Estate'),
        ('Fashion', 'Fashion'),
        ('Home & Garden', 'Home & Garden'),
        ('Services', 'Services')
    ], validators=[DataRequired()])
    
    # Critical for filtering logic in main.py
    section = SelectField('Grid Section', choices=[
        ('market', 'Standard Market'),
        ('shortlet', 'Shortlet/Rental'),
        ('declutter', 'Declutter (Used)')
    ], validators=[DataRequired()])
    
    # Regional Nodes
    state = SelectField('Location Node', choices=[
        ('Lagos', 'Lagos'),
        ('Abuja', 'Abuja'),
        ('Rivers', 'Rivers'),
        ('Kano', 'Kano'),
        ('Oyo', 'Oyo'),
        ('Enugu', 'Enugu')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Technical Specs', validators=[DataRequired()])
    image = FileField('Asset Visual', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Deploy Asset')

# --- 💸 FINANCIAL GATEWAYS ---

class WithdrawalForm(FlaskForm):
    """Liquidity Extraction Request."""
    amount = DecimalField('Liquidity Amount (₦)', validators=[DataRequired(), NumberRange(min=1000, message="Minimum withdrawal is ₦1,000")])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=10, max=10, message="Account number must be 10 digits")])
    account_name = StringField('Account Name', validators=[DataRequired()])
    submit = SubmitField('Transmit Request')

# --- ⚖️ DISPUTE RESOLUTION ---

class DisputeForm(FlaskForm):
    """Emergency Brake Protocol."""
    reason = SelectField('Issue Type', choices=[
        ('Item Not Received', 'Item Not Received'),
        ('Item Damaged', 'Item Damaged/Defective'),
        ('Wrong Item', 'Wrong Item Sent'),
        ('Fraud Suspicion', 'Fraud Suspicion')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Detailed Report', validators=[DataRequired(), Length(min=20, message="Please provide at least 20 characters of detail.")])
    evidence = FileField('Visual Evidence (Optional)', validators=[FileAllowed(['jpg', 'png', 'mp4'])])
    submit = SubmitField('Freeze Escrow & Open Ticket')