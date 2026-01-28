import os
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
    role = db.Column(db.String(20), default='user') # user, driver, agent, admin
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    wallet_balance = db.Column(db.Float, default=0.0)
    address = db.Column(db.String(200))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 🛡️ Permission Nodes
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)
    is_agent = db.Column(db.Boolean, default=False) 
    is_verified = db.Column(db.Boolean, default=False)

    # 📡 Identity Signals (KYC)
    kyc_id_card_file = db.Column(db.String(120))
    kyc_selfie_file = db.Column(db.String(120))
    kyc_video_file = db.Column(db.String(120))
    kyc_plate_file = db.Column(db.String(120))
    
    # 🚚 Pilot Telemetry
    vehicle_type = db.Column(db.String(50))
    vehicle_year = db.Column(db.String(20))
    license_plate = db.Column(db.String(20))
    current_lat = db.Column(db.Float, default=6.5244) 
    current_lng = db.Column(db.Float, default=3.3792)
    signal_strength = db.Column(db.Integer, default=100)

    # 🖇️ Relationships
    listings = db.relationship('Listing', backref='seller', lazy='dynamic')
    orders_bought = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy='dynamic')
    orders_handled = db.relationship('Order', foreign_keys='Order.driver_id', backref='driver', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(120), default='default_item.jpg') 
    category = db.Column(db.String(50)) 
    section = db.Column(db.String(20), default='declutter') 
    condition = db.Column(db.String(20))
    brand = db.Column(db.String(50))
    specifications = db.Column(db.String(100))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    status = db.Column(db.String(20), default='Available')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    escrow_reference = db.Column(db.String(20), unique=True)
    verification_pin = db.Column(db.String(4))
    total_price = db.Column(db.Float, nullable=False)
    delivery_status = db.Column(db.String(20), default='Processing')
    status = db.Column(db.String(20), default='Pending') 
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    listing = db.relationship('Listing', backref='orders_list')

    @property
    def handshake_id(self):
        return f"HSK-{self.escrow_reference or self.id + 10000}"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False) 
    status = db.Column(db.String(20), default='Success')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Dispute(db.Model): # 🛡️ RESTORED MODEL
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    reason = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open')
    order = db.relationship('Order', backref='order_disputes')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)