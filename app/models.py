from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    
    # ✅ SECURITY FIX: 256 chars to prevent "Value too long" crash
    password_hash = db.Column(db.String(256))
    
    role = db.Column(db.String(20), default='user')
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    # ✅ FIX: Wallet Balance (This was missing!)
    wallet_balance = db.Column(db.Float, default=0.0)
    
    # Relationships
    listings = db.relationship('Listing', backref='seller', lazy='dynamic')
    orders = db.relationship('Order', backref='buyer', lazy='dynamic', foreign_keys='Order.user_id')
    
    # ✅ NEW: Notification Relationship (Fixes the undefined error)
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')
    
    # KYC Fields
    kyc_selfie_file = db.Column(db.String(120))
    kyc_id_card_file = db.Column(db.String(120))
    kyc_video_file = db.Column(db.String(120))
    kyc_plate_number_file = db.Column(db.String(120))

    # ✅ SECURITY METHODS
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    section = db.Column(db.String(50), default='market') # market, declutter, shortlet
    condition = db.Column(db.String(50)) # Brand New, Pre-owned
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    image_filename = db.Column(db.String(120))
    status = db.Column(db.String(20), default='Available') # Available, Sold, Pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Buyer
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Driver
    
    # ✅ Expanded for Admin Panel & Logistics
    status = db.Column(db.String(20), default='Pending') # Pending, Escrowed, Delivered, Completed
    delivery_status = db.Column(db.String(20), default='Pending')
    total_price = db.Column(db.Float)
    escrow_reference = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    listing = db.relationship('Listing', backref='orders')

# ✅ Fully Constructed Models (Required for Admin/Notifications)
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(64))
    message = db.Column(db.String(256))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    fee_deducted = db.Column(db.Float, default=0.0)
    type = db.Column(db.String(20)) # Deposit, Withdrawal, Sale
    status = db.Column(db.String(20), default='Success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order', backref='disputes')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)