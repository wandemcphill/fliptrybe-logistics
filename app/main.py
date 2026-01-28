import os, random, secrets, logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Transaction, Notification, Dispute, Review
from sqlalchemy import func, or_

# 🧪 PHYSICAL SIGNAL ENGINE
from app.signals import transmit_termii_signal

main = Blueprint('main', __name__)

# ... [Keep dispatch_system_signal, save_signal_asset, and inject_activity_pulse as previously hardened] ...

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

    # 2. Build base query (Active Assets only)
    listings_query = Listing.query.filter_by(status='Active')

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
    active_hubs = db.session.query(Listing.state).filter_by(status='Active').distinct().all()
    active_hubs = [h[0] for h in active_hubs if h[0]]

    return render_template('market.html', 
                           listings=listings, 
                           hubs=active_hubs,
                           current_filters=request.args)

# ... [Keep product_detail, user_profile, and mission routes as previously hardened] ...