import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True) 
    
    # 🚐 LOGISTICS & TRUST SCHEMA
    vehicle_type = db.Column(db.String(50), nullable=True)
    vehicle_year = db.Column(db.String(10), nullable=True)
    vehicle_color = db.Column(db.String(20), nullable=True)
    license_plate = db.Column(db.String(20), nullable=True)
    rating = db.Column(db.Float, default=5.0)
    profile_pic = db.Column(db.String(200), nullable=True)
    
    wallet_balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    is_agent = db.Column(db.Boolean, default=False)
    is_driver = db.Column(db.Boolean, default=False)

    # Relationships
    listings = db.relationship('Listing', backref='agent', lazy=True)
    orders_bought = db.relationship('Order', backref='buyer', lazy=True, foreign_keys='Order.buyer_id')
    orders_delivered = db.relationship('Order', backref='driver', lazy=True, foreign_keys='Order.driver_id')
    
    # 💬 CHAT RELATIONSHIPS (NEW)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50)) 
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    image_filename = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Available')
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    orders = db.relationship('Order', backref='listing', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    delivery_status = db.Column(db.String(50), default='Pending') 
    verification_pin = db.Column(db.String(4), nullable=True) 
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    disputes = db.relationship('Dispute', backref='order', lazy=True)

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    is_emergency = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='disputes_filed', lazy=True)

# 💬 NEW MESSAGE TABLE
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)