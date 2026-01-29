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

# --- 🛰️ SYSTEM SIGNALS (HEARTBEAT & MARQUEE) ---
@main.app_context_processor
def inject_signals():
    from app import celery
    worker_status = "Offline"
    try:
        inspect = celery.control.inspect()
        active = inspect.active()
        if active and len(active) > 0:
            worker_status = "Optimal"
    except Exception:
        worker_status = "Disconnected"

    recent_orders = Order.query.order_by(Order.timestamp.desc()).limit(3).all()
    signals = [{'type': 'handshake', 'msg': f"Handshake {o.handshake_id}: Locked"} for o in recent_orders]
    
    return dict(activity_signals=signals or [{'type': 'system', 'msg': 'Grid Online'}], grid_status=worker_status)

# --- 🏠 PUBLIC GRID & PRODUCT VIEW ---

@main.route("/")
def index():
    items = Listing.query.filter_by(status='Available').order_by(Listing.date_posted.desc()).limit(8).all()
    return render_template('index.html', items=items)

@main.route("/product/<int:listing_id>")
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=item)

# --- 🛡️ ADMIN OVERRIDE PROTOCOLS ---

@main.route("/grid/reset-vault", methods=['POST'])
@login_required
def reset_vault():
    """🧨 Emergency Protocol: Wipes all transaction data. Requires Admin."""
    if not current_user.is_admin:
        flash("Unauthorized: Admin clearance required.", "danger")
        return redirect(url_for('main.index'))

    try:
        # Delete in order to satisfy Foreign Key constraints
        db.session.query(Notification).delete()
        db.session.query(Transaction).delete()
        db.session.query(Order).delete()
        db.session.query(Listing).delete()
        db.session.query(PriceHistory).delete()
        db.session.commit()
        flash("Vault Reset: All test data purged.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Reset Failed: {str(e)}", "danger")
    return redirect(url_for('main.dashboard'))

@main.route("/grid/test-signal/<string:phone>")
@login_required
def test_signal(phone):
    """🛰️ Manual Transmission Check: Fires a background SMS via Worker."""
    if not current_user.is_admin:
        return "Unauthorized Access", 403
        
    msg = f"🛰️ FlipTrybe Signal Test: {datetime.now().strftime('%H:%M:%S')}. Grid Optimal."
    transmit_termii_signal.delay(phone, msg) # 👈 Hits the Worker Node
    
    return jsonify({"status": "Transmitted", "target": phone, "engine": "Celery Worker"})

# --- 👤 DASHBOARDS (BUYER, MERCHANT, PILOT) ---

@main.route("/dashboard")
@login_required
def dashboard():
    orders_bought = Order.query.filter_by(buyer_id=current_user.id).all()
    return render_template('dashboard.html', orders_bought=orders_bought)

@main.route("/merchant/hub")
@login_required
def merchant_hub():
    my_listings = Listing.query.filter_by(user_id=current_user.id).all()
    return render_template('merchant_hub.html', listings=my_listings)

@main.route("/pilot/console")
@login_required
def pilot_console():
    if not current_user.is_driver:
        return redirect(url_for('main.index'))
    active = Order.query.filter_by(driver_id=current_user.id, status='Escrowed').all()
    return render_template('pilot_console.html', active=active)

# --- 🛑 ERROR HANDLERS ---
@main.app_errorhandler(404)
def error_404(error): return render_template('404.html'), 404

@main.app_errorhandler(500)
def error_500(error): return render_template('500.html'), 500