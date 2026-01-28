import os, secrets, logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Transaction, Notification, Dispute, Review
from sqlalchemy import func, or_

# 🧪 PHYSICAL SIGNAL ENGINE
# (Ensure app/signals.py exists, or comment this line out if not ready)
# from app.signals import transmit_termii_signal 

main = Blueprint('main', __name__)

# ==========================================
# 🏠 LANDING NODE (The 'Fresh Drops' Fuel)
# ==========================================
@main.route("/")
@main.route("/home")
def index():
    """
    Fetches the 4 newest items to display on the landing page.
    """
    # 🛒 Fetch 4 newest items that are 'Available'
    items = Listing.query.filter_by(status='Available').order_by(Listing.created_at.desc()).limit(4).all()
    
    return render_template('index.html', items=items)

# ==========================================
# 🛰️ MARKETPLACE: SEARCH & DISCOVERY NODE
# ==========================================
@main.route('/market')
def market():
    """High-velocity asset discovery with multi-vector filtering."""
    # 1. Capture incoming signals
    query_signal = request.args.get('q', '')
    state_signal = request.args.get('state', '')
    cat_signal = request.args.get('category', '')
    min_p = request.args.get('min_price', type=float)
    max_p = request.args.get('max_price', type=float)

    # 2. Build base query (Using 'Available' to match your Database Model default)
    listings_query = Listing.query.filter_by(status='Available')

    # 3. Apply Multi-Vector Filters
    if query_signal:
        listings_query = listings_query.filter(Listing.title.ilike(f'%{query_signal}%'))
    
    if state_signal:
        listings_query = listings_query.filter(Listing.state == state_signal)
        
    if cat_signal:
        listings_query = listings_query.filter(Listing.category == cat_signal)
        
    if min_p is not None:
        listings_query = listings_query.filter(Listing.price >= min_p)
        
    if max_p is not None:
        listings_query = listings_query.filter(Listing.price <= max_p)

    # 4. Execute Discovery
    listings = listings_query.order_by(Listing.created_at.desc()).all()

    # 5. Extract Active Hubs for the UI Filter
    active_hubs = db.session.query(Listing.state).filter_by(status='Available').distinct().all()
    active_hubs = [h[0] for h in active_hubs if h[0]]

    # ✅ FIXED: 'listings' is renamed to 'items' here so market.html can read it
    return render_template('market.html', 
                           items=listings, 
                           hubs=active_hubs,
                           current_filters=request.args)

# ==========================================
# 📦 ASSET DETAIL NODE
# ==========================================
@main.route("/listing/<int:listing_id>")
def product_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=listing, title=listing.title)

# ==========================================
# 👤 PROFILE NODE (Minimal Placeholder)
# ==========================================
@main.route("/user/<string:username>")
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)

# ==========================================
# 🚀 DASHBOARD REDIRECTOR
# ==========================================
@main.route("/dashboard")
@login_required
def dashboard():
    # Redirect to the correct panel based on role
    if current_user.is_admin:
        return redirect(url_for('admin.admin_panel')) # Ensure 'admin' blueprint exists
    if current_user.is_driver:
        # If you haven't built the driver panel yet, send them to market
        return redirect(url_for('main.market')) 
    return redirect(url_for('main.market')) # Default user dashboard is the market for now