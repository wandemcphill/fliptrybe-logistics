from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User

# --- 🛰️ 1. IDENTITY FORMS (Registration & Access) ---

class RegistrationForm(FlaskForm):
    """Build #7: Secure Identity Node Initialization."""
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Grid Email', 
                        validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField('Signal Phone (Nigerian Format)', 
                        validators=[DataRequired(), Length(min=11, max=15)])
    password = PasswordField('Access Key', 
                             validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Access Key', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Initialize Node')

    # 🛡️ Audit: Prevent Duplicate Identity Nodes
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered in the grid.')

    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError('This phone signal is already linked to a node.')

class LoginForm(FlaskForm):
    """Access Control Handshake."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Maintain Connection')
    submit = SubmitField('Authorize Access')

# --- 💸 2. FINANCIAL FORMS (Liquidity Exits) ---

class WithdrawalForm(FlaskForm):
    """Build #10: Liquidity Exit Protocol."""
    amount = DecimalField('Withdrawal Amount (₦)', 
                          validators=[DataRequired(), NumberRange(min=1000)], 
                          places=2)
    bank_name = SelectField('Destination Bank', 
                            choices=[('access', 'Access Bank'), ('gtb', 'GTBank'), ('zenith', 'Zenith Bank'), ('opay', 'OPay'), ('kuda', 'Kuda Bank')],
                            validators=[DataRequired()])
    account_number = StringField('Account Number', 
                                 validators=[DataRequired(), Length(min=10, max=10)])
    account_name = StringField('Account Holder Name', 
                               validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Request Liquidity Exit')

# --- ⚖️ 3. JUDICIAL FORMS (Conflict Resolution) ---

class DisputeForm(FlaskForm):
    """Build #6: Judicial Conflict Documentation."""
    reason = SelectField('Primary Conflict', 
                         choices=[('no_delivery', 'Asset Not Received'), 
                                  ('wrong_item', 'Wrong Asset Delivered'), 
                                  ('damaged', 'Asset Compromised/Damaged'), 
                                  ('fraud', 'Suspicious Activity Detected')],
                         validators=[DataRequired()])
    description = TextAreaField('Detailed Incident Log', 
                                validators=[DataRequired(), Length(min=20, max=1000)])
    submit = SubmitField('Signal Dispute // Freeze Vault')

# --- 📦 4. ASSET FORMS (Marketplace Listings) ---

class ListingForm(FlaskForm):
    """Asset Deployment Protocol."""
    title = StringField('Asset Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Technical Description', validators=[DataRequired(), Length(max=2000)])
    price = DecimalField('Liquidity Signal (Price)', validators=[DataRequired(), NumberRange(min=1)], places=2)
    category = SelectField('Classification', 
                           choices=[('electronics', 'Electronics'), ('fashion', 'Fashion'), ('vehicles', 'Vehicles'), ('real_estate', 'Real Estate')],
                           validators=[DataRequired()])
    state = StringField('Deployment State (e.g. Lagos)', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Deploy Asset to Grid')