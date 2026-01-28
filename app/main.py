import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Listing, Order, Notification, Dispute, Transaction

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_signals():
    return dict(activity_signals=[
        {'type': 'handshake', 'msg': 'New Handshake: MacBook Pro M3 in Ikeja'},
        {'type': 'transmission', 'msg': 'Pilot Musa active on Lekki Grid'},
        {'type': 'handshake', 'msg': 'Liquidity Released: Order #8829'}
    ])

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
    # 📜 Fetch Transactions for the Audit Trail
    history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template('dashboard.html', orders_bought=orders_bought, listings=listings, history=history)

@main.route('/wallet/withdraw', methods=['POST'])
@login_required
def withdraw_funds():
    if not current_user.is_verified:
        flash("Identity Signal Missing: Please complete KYC to withdraw funds.", "error")
        return redirect(url_for('main.dashboard'))
    
    amount = request.form.get('amount', type=float)
    if not amount or amount < 500:
        flash("Minimum withdrawal threshold is ₦500.", "error")
        return redirect(url_for('main.dashboard'))

    if current_user.wallet_balance >= amount:
        current_user.wallet_balance -= amount
        
        # 🧪 Create Transaction Record
        tx = Transaction(user_id=current_user.id, amount=amount, type='Debit', status='Pending')
        db.session.add(tx)
        db.session.commit()
        
        flash(f"Withdrawal Signal Transmitted: ₦{amount:,.2f} is being processed.", "success")
    else:
        flash("Insufficient Liquidity in Node Wallet.", "error")
    return redirect(url_for('main.dashboard'))

@main.route('/settings')
@login_required
def settings():
    return render_template('dashboard.html')

@main.route('/pilot/cockpit')
@login_required
def pilot_console():
    if not current_user.is_driver:
        flash("Unauthorized: Pilot Node access only.", "error")
        return redirect(url_for('main.dashboard'))
    deliveries = Order.query.filter_by(driver_id=current_user.id).all()
    return render_template('pilot_console.html', deliveries=deliveries)

@main.route('/product/<int:listing_id>')
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=item)

@main.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        flash("SIGNAL_CONFIRMED", "success")
        return redirect(url_for('main.support'))
    return render_template('support.html')