import os, secrets
from datetime import datetime
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import (
    User, Listing, Order, Transaction, Dispute, Favorite, 
    PriceHistory, Notification, Withdrawal
)
from app.utils import (
    sync_escrow_notifications, 
    notify_pilot_assignment,
    create_grid_notification,
    transmit_termii_signal
)

main = Blueprint('main', __name__)

# --- 🛠️ PRODUCTION PATH HELPER ---
def get_upload_path(folder):
    """
    Routes file saves to Persistent Disk on Render, or local static in Dev.
    """
    if os.environ.get('RENDER'):
        # Matches the 'Mount Path' in your Render Disk settings
        base_path = os.path.join('/var/lib/data', folder)
    else:
        base_path = os.path.join(current_app.root_path, 'static', folder)
    
    os.makedirs(base_path, exist_ok=True)
    return base_path

# --- 🛰️ SYSTEM SIGNALS (HEARTBEAT & MARQUEE) ---
@main.app_context_processor
def inject_signals():
    """Provides real-time activity signals and worker heartbeat."""
    from app import celery # Local import to avoid circular dependency
    
    # 💓 Worker Heartbeat Logic
    worker_status = "Offline"
    try:
        # Pings the Redis Synapse to see if any workers are active
        inspect = celery.control.inspect()
        active = inspect.active()
        if active and len(active) > 0:
            worker_status = "Optimal"
    except Exception:
        worker_status = "Disconnected"

    # 📡 Activity Signals
    recent_orders = Order.query.order_by(Order.timestamp.desc()).limit(3).all()
    recent_listings = Listing.query.filter_by(status='Available').order_by(Listing.date_posted.desc()).limit(2).all()
    
    signals = []
    for order in recent_orders:
        signals.append({'type': 'handshake', 'msg': f"Handshake {order.handshake_id}: {order.listing.title} Locked"})
    for item in recent_listings:
        signals.append({'type': 'delivery', 'msg': f"Asset Deployed: {item.title} in {item.state}"})
    
    if not signals:
        signals = [{'type': 'system', 'msg': 'Grid Status: Initialized'}]

    return dict(
        activity_signals=signals,
        grid_status=worker_status # 🟢 Injected for base.html heartbeat
    )

# --- 🏠 PUBLIC GRID ---

@main.route("/")
def index():
    items = Listing.query.filter_by(status='Available').order_by(Listing.date_posted.desc()).limit(8).all()
    return render_template('index.html', items=items)

@main.route("/product/<int:listing_id>")
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    sales_count = Order.query.join(Listing).filter(Listing.user_id == item.seller.id, Order.status == 'Released').count()
    dispute_count = Dispute.query.join(Order).join(Listing).filter(Listing.user_id == item.seller.id).count()
    trust_score = max(0, (sales_count * 10) - (dispute_count * 50))
    tier = "Elite" if trust_score > 100 else "Verified" if trust_score > 20 else "Standard"
    similar_items = Listing.query.filter(Listing.category == item.category, Listing.id != item.id, Listing.status == 'Available').limit(6).all()
    history = PriceHistory.query.filter_by(listing_id=item.id).order_by(PriceHistory.timestamp.asc()).all()
    return render_template('product_detail.html', item=item, tier=tier, trust_score=trust_score, similar_items=similar_items, price_history=history)

# --- 👤 USER DASHBOARD ---

@main.route("/dashboard")
@login_required
def dashboard():
    orders_bought = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.timestamp.desc()).all()
    history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template('dashboard.html', orders_bought=orders_bought, history=history)

# --- 🏪 MERCHANT HUB ---

@main.route("/merchant/hub")
@login_required
def merchant_hub():
    total_sales_count = Order.query.join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Released').count()
    pending_escrow_count = Order.query.join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Escrowed').count()
    total_revenue = db.session.query(db.func.sum(Order.total_price)).join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Released').scalar() or 0.0
    pending_liquidity = db.session.query(db.func.sum(Order.total_price)).join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Escrowed').scalar() or 0.0
    dispute_count = Dispute.query.join(Order).join(Listing).filter(Listing.user_id == current_user.id).count()
    trust_score = max(0, (total_sales_count * 10) - (dispute_count * 50))
    tier = "Elite" if trust_score > 100 else "Verified" if trust_score > 20 else "Standard"
    my_listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.date_posted.desc()).all()
    active_escrows = Order.query.join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Escrowed').order_by(Order.timestamp.desc()).all()

    return render_template('merchant_hub.html', sales_count=total_sales_count, escrow_count=pending_escrow_count, 
                           revenue=total_revenue, pending_liquidity=pending_liquidity, trust=trust_score,
                           tier=tier, listings=my_listings, pending_orders=active_escrows)

# --- 🚁 PILOT CONSOLE ---

@main.route("/pilot/console")
@login_required
def pilot_console():
    if not current_user.is_driver:
        flash("Unauthorized: Pilot clearance required.", "danger")
        return redirect(url_for('main.index'))
    active_missions = Order.query.filter_by(driver_id=current_user.id, status='Escrowed').all()
    completed_missions = Order.query.filter_by(driver_id=current_user.id, status='Released').all()
    return render_template('pilot_console.html', active=active_missions, history=completed_missions)

@main.route("/order/update-delivery/<int:order_id>/<string:status>", methods=['POST'])
@login_required
def update_delivery(order_id, status):
    order = Order.query.get_or_404(order_id)
    if order.driver_id != current_user.id:
        return jsonify({"error": "Unauthorized Node"}), 403
    
    if 'delivery_photo' in request.files:
        f = request.files['delivery_photo']
        if f.filename:
            filename = secure_filename(f"POD_{order.handshake_id}_{secrets.token_hex(4)}.jpg")
            f.save(os.path.join(get_upload_path('deliveries'), filename))
    
    order.delivery_status = status
    db.session.commit()
    create_grid_notification(order.buyer_id, "Logistics Update", f"Mission {order.handshake_id} is now {status}.", "info")
    transmit_termii_signal.delay(order.buyer.phone, f"FlipTrybe Logistics: Your order is {status}.")
    flash(f"Status Synced: {status}", "success")
    return redirect(url_for('main.pilot_console'))

# --- 🤝 ESCROW OPERATIONS ---

@main.route("/order/place/<int:listing_id>", methods=['POST'])
@login_required
def place_order(listing_id):
    item = Listing.query.get_or_404(listing_id)
    if current_user.wallet_balance < item.price:
        flash("Insufficient liquidity.", "danger")
        return redirect(url_for('main.product_detail', listing_id=item.id))
    
    current_user.wallet_balance -= item.price
    order = Order(user_id=current_user.id, listing_id=item.id, total_price=item.price, status='Escrowed')
    item.status = 'Sold'
    db.session.add(order)
    db.session.commit()
    sync_escrow_notifications(order)
    flash(f"Handshake Locked: ₦{item.price:,.0f} secured.", "success")
    return redirect(url_for('main.dashboard'))

@main.route("/order/release/<int:order_id>", methods=['POST'])
@login_required
def release_funds(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.dashboard'))
    
    merchant = order.listing.seller
    merchant.wallet_balance += order.total_price
    order.status = 'Released'
    order.delivery_status = 'Completed'
    db.session.commit()
    create_grid_notification(merchant.id, "Funds Released", f"Payment for {order.handshake_id} added.", "success")
    transmit_termii_signal.delay(merchant.phone, f"FlipTrybe: ₦{order.total_price:,.0f} released.")
    flash("Transaction Closed. Funds Released.", "success")
    return redirect(url_for('main.dashboard'))

# --- 🤝 DISPUTE MODULE ---

@main.route("/order/dispute/<int:order_id>", methods=['GET', 'POST'])
@login_required
def raise_dispute(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        return redirect(url_for('main.dashboard'))
    
    form = DisputeForm()
    if form.validate_on_submit():
        if form.evidence.data:
            f = form.evidence.data
            filename = secure_filename(f"DISPUTE_{order.handshake_id}_{secrets.token_hex(4)}.jpg")
            f.save(os.path.join(get_upload_path('disputes'), filename))
        
        dispute = Dispute(reason=form.reason.data, order_id=order.id, claimant_id=current_user.id)
        order.status = 'Disputed'
        db.session.add(dispute)
        db.session.commit()
        create_grid_notification(order.listing.seller.id, "Dispute Alert", f"Dispute on {order.handshake_id}.", "danger")
        flash("Escrow Frozen. HQ will review.", "info")
        return redirect(url_for('main.dashboard'))
    return render_template('dispute.html', form=form, order=order)

# --- 🏗️ ASSET MANAGEMENT ---

@main.route("/listing/add", methods=['GET', 'POST'])
@login_required
def add_listing():
    form = ListingForm()
    if form.validate_on_submit():
        filename = 'default.jpg'
        if form.image.data:
            f = form.image.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(get_upload_path('products'), filename))
        
        new_item = Listing(title=form.title.data, price=float(form.price.data), description=form.description.data, 
                           category=form.category.data, section=form.section.data, state=form.state.data, 
                           image_filename=filename, seller=current_user)
        db.session.add(new_item)
        db.session.commit()
        db.session.add(PriceHistory(listing_id=new_item.id, price=new_item.price))
        db.session.commit()
        flash("Asset Deployed to Grid.", "success")
        return redirect(url_for('main.merchant_hub'))
    return render_template('add_listing.html', form=form)

@main.route("/listing/favorite/<int:listing_id>", methods=['POST'])
@login_required
def toggle_favorite(listing_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, listing_id=listing_id).first()
    if fav:
        db.session.delete(fav)
        msg = "Asset removed."
    else:
        db.session.add(Favorite(user_id=current_user.id, listing_id=listing_id))
        msg = "Asset synchronized."
    db.session.commit()
    return jsonify({"status": "success", "message": msg})

@main.route("/wallet/withdraw", methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawalForm()
    if form.validate_on_submit():
        if current_user.wallet_balance < form.amount.data:
            flash("Insufficient liquidity.", "danger")
            return redirect(url_for('main.withdraw'))
        current_user.wallet_balance -= float(form.amount.data)
        withdrawal = Withdrawal(user_id=current_user.id, amount=float(form.amount.data), bank_name=form.bank_name.data, 
                                account_number=form.account_number.data, account_name=form.account_name.data)
        tx = Transaction(user_id=current_user.id, amount=float(form.amount.data), type='Debit', 
                         reference=f"WTH-{secrets.token_hex(4).upper()}")
        db.session.add_all([withdrawal, tx])
        db.session.commit()
        flash("Withdrawal transmitted to HQ.", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('withdraw.html', form=form)

# --- 🛑 ERROR HANDLERS ---
@main.app_errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500