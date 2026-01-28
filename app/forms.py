from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'User'), ('agent', 'Agent'), ('driver', 'Driver')])
    submit = SubmitField('Register Identity')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username occupied. Choose another.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Signal')
    submit = SubmitField('Initialize Login')

class KYCVerificationForm(FlaskForm):
    full_name = StringField('Full Legal Name', validators=[DataRequired()])
    id_type = SelectField('ID Type', choices=[('NIN', 'NIN'), ('License', 'Drivers License'), ('Passport', 'Passport')])
    id_image = FileField('ID Document Image', validators=[DataRequired()])
    selfie_image = FileField('Live Selfie Image', validators=[DataRequired()])
    submit = SubmitField('Transmit Signals')