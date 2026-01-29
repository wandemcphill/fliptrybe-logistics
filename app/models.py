import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login utility for session persistent user retrieval."""
    return User.query.get(int(user_id))

# --- 👥 IDENTITY NODE (Integrated KYC, Trust & Financials) ---

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # 🛡️ Access Control & Trust Signals (Build #1, #7)
    is_admin = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False) 
    is_verified = db.Column(db.Boolean, default=False)
    merchant_tier = db.Column(db.String(30), default='Novice') # Novice, Verified, Grid-Master
    
    # ⭐ Pilot Performance Metrics (Build #4)
    pilot_rating_sum = db.Column(db.Integer, default=0)
    pilot_rating_count = db.Column(db.Integer, default=0)
    
    # 💸 Financial Node
    wallet_balance = db.Column(db.Float, default=0.0)
    
    # 🧬 Dynamic Relationships
    listings = db.relationship('Listing', backref='seller', lazy=True, cascade="all, delete-orphan")
    orders_bought = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy=True)
    orders_driven = db.relationship('Order', foreign_keys='Order.driver_id', backref='driver', lazy=True)
    
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade="all, delete-orphan")
    disputes = db.relationship('Dispute', foreign_keys='Dispute.claimant_id', backref='claimant', lazy=True)

    @property
    def pilot_score(self):
        """Calculates real-time reliability for Build #4."""
        if self.pilot_rating_count == 0: return 0
        return round(self.pilot_rating_sum / self.pilot_rating_count, 1)

    def __repr__(self):
        return f"<User {self.name} // Tier: {self.merchant_tier}>"

# --- 📦 ASSET NODE (Integrated Price History & FOMO) ---

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # 🏷️ Classification
    category = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False, default='Lagos')
    image_filename = db.Column(db.String(100), nullable=False, default='default.jpg')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Available') # Available, Pending Handshake, Sold
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 📈 Build #3: Price Drop Tracking
    price_history = db.relationship('PriceHistory', backref='listing', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='listing', lazy=True)

    @property
    def price_drop(self):
        """Build #3: Scans PriceHistory nodes to identify 'Deals'."""
        from app.models import PriceHistory
        hist = PriceHistory.query.filter_by(listing_id=self.id).order_by(PriceHistory.timestamp.desc()).limit(2).all()
        if len(hist) < 2: return 0
        if hist[0].price < hist[1].price:
            return round(((hist[1].price - hist[0].price) / hist[1].price) * 100)
        return 0

    def __repr__(self):
        return f"<Listing {self.title} // ₦{self.price}>"

# --- 🤝 HANDSHAKE PROTOCOL (Transaction State Machine) ---

class Order(db.Model):
    __tablename__ = 'orders' 
    id = db.Column(db.Integer, primary_key=True)
    handshake_id = db.Column(db.String(12), unique=True, nullable=False, 
                             default=lambda: f"HS-{datetime.now().strftime('%H%M%S')}")
    total_price = db.Column(db.Float, nullable=False)
    
    # 🚦 Status Lifecycle
    # Escrowed -> Dispatched -> In Transit -> Delivered -> Completed (or Disputed)
    status = db.Column(db.String(20), default='Escrowed') 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 🧬 Foreign Links
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    
    disputes = db.relationship('Dispute', backref='order', lazy=True)

# --- 💸 FINANCIAL & AUDIT NODES ---

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False) # Debit (PAY), Credit (RELEASE)
    reference = db.Column(db.String(50), unique=True, nullable=False) # e.g., PAY-HS-123, RELEASE-HS-123
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    bank_name = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Completed, Frozen (Build #5)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# --- ⚖️ JUDICIAL & ANALYTIC NODES ---

class Dispute(db.Model):
    __tablename__ = 'disputes'
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True) # Detailed context for Build #6
    status = db.Column(db.String(20), default='Open') # Open, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class PriceHistory(db.Model):
    __tablename__ = 'price_histories'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(20), default='info') # success, danger, warning
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    listing_rel = db.relationship('Listing') # Cross-reference helper