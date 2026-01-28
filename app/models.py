from datetime import datetime, timedelta
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import relationship

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# 👤 USER ARCHITECTURE (Identity & Surveillance)
# ==========================================
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) 
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    image_file = db.Column(db.String(200), nullable=False, default='default.jpg')
    
    # 📱 Multi-Node Contact Signals
    phone = db.Column(db.String(20), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    mobile_2 = db.Column(db.String(20), nullable=True)
    whatsapp_2 = db.Column(db.String(20), nullable=True)
    
    # 📍 Regional Hub & Billing
    address = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.String(255), nullable=True) 
    state = db.Column(db.String(50), nullable=True, index=True)
    city = db.Column(db.String(50), nullable=True)
    vat_number = db.Column(db.String(50), nullable=True) 
    
    # 🛡️ THE KYC SIGNAL LAYER
    kyc_selfie_file = db.Column(db.String(200), nullable=True)
    kyc_id_file = db.Column(db.String(200), nullable=True)
    kyc_video_file = db.Column(db.String(200), nullable=True)
    kyc_plate = db.Column(db.String(200), nullable=True) 
    is_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    kyc_status = db.Column(db.String(20), default='Unverified') 
    kyc_notes = db.Column(db.String(255), nullable=True)
    last_kyc_update = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 🚐 Logistics & Last-Mile Radar
    role = db.Column(db.String(20), default='user')
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)
    vehicle_type = db.Column(db.String(50), nullable=True)
    license_plate = db.Column(db.String(20), nullable=True) 
    current_lat = db.Column(db.Float, nullable=True) 
    current_lng = db.Column(db.Float, nullable=True) 
    signal_strength = db.Column(db.Integer, default=100) 
    
    wallet_balance = db.Column(db.Float, default=0.0)
    handshake_count_weekly = db.Column(db.Integer, default=0)

    # 🔗 RELATIONS
    listings = db.relationship('Listing', backref='seller', lazy='dynamic')
    orders_bought = db.relationship('Order', backref='buyer', lazy='dynamic', foreign_keys='Order.buyer_id')
    orders_handled = db.relationship('Order', backref='driver', lazy='dynamic', foreign_keys='Order.driver_id')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy='dynamic')
    
    # ⭐ REPUTATION ENGINE RELATIONS
    reviews_received = db.relationship('Review', backref='reviewee', lazy='dynamic', foreign_keys='Review.reviewee_id')
    reviews_given = db.relationship('Review', backref='reviewer', lazy='dynamic', foreign_keys='Review.reviewer_id')

# ==========================================
# 📦 ASSET SIGNAL (Marketplace Inventory)
# ==========================================
class Listing(db.Model):
    __tablename__ = 'listing'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False, index=True)
    section = db.Column(db.String(50), nullable=False, default='declutter') 
    category = db.Column(db.String(50), nullable=False, index=True)
    brand = db.Column(db.String(50), nullable=True)
    condition = db.Column(db.String(50), nullable=True)
    specifications = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(100), nullable=True, index=True)
    city = db.Column(db.String(100), nullable=True)
    image_filename = db.Column(db.String(200), nullable=False, default='default_product.jpg')
    status = db.Column(db.String(20), default='Available', index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('ShortletBooking', backref='listing', lazy='dynamic')

# ==========================================
# 🚚 THE HANDSHAKE (Escrow & Safety)
# ==========================================
class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    handshake_id = db.Column(db.String(50), unique=True, index=True) 
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=True)
    tax_amount = db.Column(db.Float, default=0.0)
    
    delivery_status = db.Column(db.String(50), default='Pending') 
    verification_pin = db.Column(db.String(10), nullable=True)
    estimated_arrival = db.Column(db.DateTime, nullable=True) 
    is_locked_for_dispute = db.Column(db.Boolean, default=False)
    
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    disputes = db.relationship('Dispute', backref='order', lazy='dynamic')
    reviews = db.relationship('Review', backref='order', lazy='dynamic')
    booking = db.relationship('ShortletBooking', backref='order', uselist=False)

# ==========================================
# ⭐ TRIBE REPUTATION ENGINE (Objective: Reviews)
# ==========================================
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5 stars
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Review Vectors
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    target_role = db.Column(db.String(20)) # 'seller' or 'driver'

# [Remaining Auxiliary Models: ShortletBooking, Transaction, Notification, Withdrawal, Dispute, Message]

class ShortletBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    fee_deducted = db.Column(db.Float, nullable=False) 
    type = db.Column(db.String(50)) # 'Sale', 'Withdrawal', 'Bonus', 'Refund', 'Deposit'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending', index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=False)
    evidence_image = db.Column(db.String(200), nullable=True)
    evidence_video = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='Open')
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read = db.Column(db.Boolean, default=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)