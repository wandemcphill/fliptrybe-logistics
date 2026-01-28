import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Notification, Dispute

main = Blueprint('main', __name__)

@main.route('/')
def index():
    items = Listing.query.filter_by(status='Available').order_by(Listing.date_posted.desc()).limit(8).all()
    return render_template('index.html', items=items)

@main.route('/market')
def market():
    section = request.args.get('section', 'declutter')
    state = request.args.get('state')
    q = request.args.get('q')
    max_price = request.args.get('max_price', type=float)
    
    query = Listing.query.filter_by(section=section, status='Available')
    if state: query = query.filter_by(state=state)
    if q: query = query.filter(Listing.title.ilike(f'%{q}%'))
    if max_price: query = query.filter(Listing.price <= max_price)
        
    items = query.order_by(Listing.date_posted.desc()).all()
    hubs = [h[0] for h in db.session.query(Listing.state).distinct().all() if h[0]]
    
    return render_template('market.html', items=items, hubs=hubs, current_filters=request.args)

@main.route('/dashboard')
@login_required
def dashboard():
    orders_bought = Order.query.filter_by(buyer_id=current_user.id).all()
    listings = Listing.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', orders_bought=orders_bought, listings=listings)

@main.route('/api/balance-signal')
@login_required
def balance_signal():
    return jsonify({'wallet_balance': current_user.wallet_balance})

@main.route('/pilot/cockpit')
@login_required
def pilot_console():
    if not current_user.is_driver:
        flash("Unauthorized: Pilot Node access only.", "error")
        return redirect(url_for('main.dashboard'))
    deliveries = Order.query.filter_by(driver_id=current_user.id).all()
    return render_template('pilot_console.html', deliveries=deliveries)

@main.route('/order/update-status/<int:order_id>/<status>', methods=['POST'])
@login_required
def update_delivery(order_id, status):
    order = Order.query.get_or_404(order_id)
    if order.driver_id == current_user.id:
        order.delivery_status = status
        db.session.commit()
        flash(f"Transmission Updated: {status}", "success")
    return redirect(url_for('main.pilot_console'))

@main.route('/order/release/<int:order_id>', methods=['POST'])
@login_required
def release_funds(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id == current_user.id:
        seller = order.listing.seller
        seller.wallet_balance += order.total_price
        order.status = 'Released'
        db.session.commit()
        flash("Handshake Confirmed. Liquidity Released.", "success")
    return redirect(url_for('main.dashboard'))

@main.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        flash("SIGNAL_CONFIRMED", "success")
        return redirect(url_for('main.support'))
    return render_template('support.html')

@main.route('/product/<int:listing_id>')
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=item)