from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 👥 IDENTITY NODE ---

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    kyc_selfie_file = db.Column(db.String(100), nullable=True)
    kyc_id_card_file = db.Column(db.String(100), nullable=True)
    
    wallet_balance = db.Column(db.Float, default=0.0)
    
    listings = db.relationship('Listing', backref='seller', lazy=True)
    orders_bought = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy=True)
    orders_driven = db.relationship('Order', foreign_keys='Order.driver_id', backref='driver', lazy=True)
    
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    disputes = db.relationship('Dispute', foreign_keys='Dispute.claimant_id', backref='claimant', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"

# --- 📦 ASSET NODE ---

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    category = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False, default='market')
    state = db.Column(db.String(50), nullable=False, default='Lagos')
    
    image_filename = db.Column(db.String(100), nullable=False, default='default.jpg')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Available')
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    price_history = db.relationship('PriceHistory', backref='listing', lazy=True, cascade="all, delete-orphan")

# --- 🤝 HANDSHAKE PROTOCOL (ORDERS) ---

class Order(db.Model):
    # 🟢 FIXED: Explicitly renamed to avoid SQL keyword conflict
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    handshake_id = db.Column(db.String(12), unique=True, nullable=False, default=lambda: f"HS-{datetime.now().strftime('%H%M%S')}")
    total_price = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.String(20), default='Escrowed')
    delivery_status = db.Column(db.String(20), default='Pending')
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    listing = db.relationship('Listing', backref='orders')

# --- 💸 FINANCIAL AUDIT TRAIL ---

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    bank_name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# --- ⚖️ DISPUTE RESOLUTION ---

class Dispute(db.Model):
    __tablename__ = 'disputes'
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    order = db.relationship('Order', backref='disputes_list')

# --- 📡 INTELLIGENCE & SIGNALS ---

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class PriceHistory(db.Model):
    __tablename__ = 'price_histories'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    listing = db.relationship('Listing')