from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    wallet_balance = db.Column(db.Float, default=0.0)
    
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Pilot specifics
    vehicle_type = db.Column(db.String(50))
    vehicle_year = db.Column(db.String(10)) 
    license_plate = db.Column(db.String(20))
    
    # KYC Signals
    kyc_selfie_file = db.Column(db.String(120))
    kyc_id_card_file = db.Column(db.String(120))
    kyc_video_file = db.Column(db.String(120))

    # Relationships
    listings = db.relationship('Listing', backref='seller', lazy='dynamic')
    orders_as_buyer = db.relationship('Order', backref='buyer', lazy='dynamic', foreign_keys='Order.user_id')
    deliveries = db.relationship('Order', backref='pilot', lazy='dynamic', foreign_keys='Order.driver_id')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy='dynamic')

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    condition = db.Column(db.String(50)) 
    image_filename = db.Column(db.String(120))
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    status = db.Column(db.String(20), default='Pending') 
    delivery_status = db.Column(db.String(20), default='Unassigned')
    total_price = db.Column(db.Float)
    escrow_reference = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    listing = db.relationship('Listing', backref='order_record')

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(10))
    status = db.Column(db.String(20), default='Pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reason = db.Column(db.String(255))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', backref='dispute_record', uselist=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(64))
    message = db.Column(db.String(256))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)