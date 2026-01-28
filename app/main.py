import os, secrets, logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Transaction, Notification, Dispute, Review
from sqlalchemy import func, or_

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
    section_signal = request.args.get('section', '') # 'shortlet' or 'declutter'
    state_signal = request.args.get('state', '')
    cat_signal = request.args.get('category', '')
    min_p = request.args.get('min_price', type=float)
    max_p = request.args.get('max_price', type=float)

    # 2. Build base query
    listings_query = Listing.query.filter_by(status='Available')

    # 3. Apply Multi-Vector Filters
    
    # ✅ FIX: Filter by Section (Shortlet vs Market)
    if section_signal == 'shortlet':
        listings_query = listings_query.filter(Listing.section == 'shortlet')
    elif section_signal == 'declutter':
        # 'declutter' shows general market items (Electronics, Vehicles, etc.)
        listings_query = listings_query.filter(Listing.section != 'shortlet')

    # Search Text
    if query_signal:
        listings_query = listings_query.filter(Listing.title.ilike(f'%{query_signal}%'))
    
    # Location
    if state_signal:
        listings_query = listings_query.filter(Listing.state == state_signal)
        
    # Category
    if cat_signal:
        listings_query = listings_query.filter(Listing.category == cat_signal)
        
    # Price Range
    if min_p is not None:
        listings_query = listings_query.filter(Listing.price >= min_p)
    if max_p is not None:
        listings_query = listings_query.filter(Listing.price <= max_p)

    # 4. Execute Discovery
    listings = listings_query.order_by(Listing.created_at.desc()).all()

    # 5. Extract Active Hubs for the UI Filter
    active_hubs = db.session.query(Listing.state).filter_by(status='Available').distinct().all()
    active_hubs = [h[0] for h in active_hubs if h[0]]

    return render_template('market.html', 
                           items=listings, 
                           hubs=active_hubs,
                           current_filters=request.args)

# ==========================================
# 📦 ASSET DETAIL NODE
# ==========================================
@main.route("/listing/<int:listing_id>")
def product_detail(listing_id):
    # ✅ FIXED: Changed variable name to 'item' to match the template
    item = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=item, title=item.title)

# ==========================================
# 🤝 TRADE INITIALIZATION (This was missing!)
# ==========================================
@main.route("/trade/initiate/<int:listing_id>", methods=['POST'])
@login_required
def initiate_trade(listing_id):
    """
    Starts the escrow process for a specific item.
    """
    listing = Listing.query.get_or_404(listing_id)
    
    # Prevent buying your own item
    if listing.seller == current_user:
        flash("You cannot trade with yourself.", "warning")
        return redirect(url_for('main.product_detail', listing_id=listing_id))

    # Placeholder for actual Escrow Logic
    # In the future, this will create an Order and redirect to Paystack
    flash(f"Trade initialized for {listing.title}! (Escrow System Loading...)", "success")
    
    return redirect(url_for('main.product_detail', listing_id=listing_id))

# ==========================================
# 👤 PROFILE NODE
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
    if current_user.is_admin:
        return redirect(url_for('admin.admin_panel'))
    return redirect(url_for('main.market'))