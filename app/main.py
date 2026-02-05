import os, secrets
from datetime import datetime
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename
from app import db
from app.models import (
    User, Listing, Order, Transaction, Dispute, Favorite, 
    PriceHistory, Notification, Withdrawal
)
from app.forms import WithdrawalForm, DisputeForm
from app.utils import (
    create_grid_notification,
    transmit_termii_signal,
    update_merchant_tier,
    sync_handshake_pulse,
    release_order_funds
)

main = Blueprint('main', __name__)

# --- 🛰️ 1. GRID SIGNALS (HEARTBEAT & LIQUIDITY) ---

@main.app_context_processor
def inject_signals():
    """Provides heartbeats and liquidity visibility to all templates."""
    from app import celery 
    worker_status = "Scanning"
    try:
        with celery.connection_or_acquire() as conn:
            conn.ensure_connection(max_retries=1)
            worker_status = "Optimal"
    except Exception: 
        worker_status = "Offline"
    
    # Heatmap calculation for Build #9
    vault_total = db.session.query(func.sum(Order.total_price)).filter_by(status='Escrowed').scalar() or 0
    return dict(grid_status=worker_status, vault_total=vault_total)

# --- 🏠 2. PUBLIC GRID (GLOBAL SEARCH & BUILD #8: DEAL MARQUEE) ---

@main.route("/")
def index():
    """The Public Marketplace with Multi-State filtering & Deal of the Day."""
    q = request.args.get('q')
    state = request.args.get('state')
    category = request.args.get('category')
    
    query = Listing.query.filter_by(status='Available')
    if q: query = query.filter((Listing.title.ilike(f'%{q}%')) | (Listing.description.ilike(f'%{q}%')))
    if state: query = query.filter_by(state=state)
    if category: query = query.filter_by(category=category)
    
    items = query.order_by(Listing.date_posted.desc()).all()

    # Build #8: Scans current grid for the item with the highest price drop
    deal_of_the_day = max([l for l in items if l.price_drop > 0], key=lambda x: x.price_drop, default=None)
    
    return render_template('index.html', items=items, deal_of_the_day=deal_of_the_day)

@main.route("/product/<int:listing_id>")
def product_detail(listing_id):
    item = Listing.query.get_or_404(listing_id)
    return render_template('product_detail.html', item=item)

# --- 🤝 3. THE HANDSHAKE PROTOCOL (ESCROW & RELEASE) ---

@main.route("/place_order/<int:listing_id>", methods=['POST'])
@login_required
def place_order(listing_id):
    """Initiates the Escrow Handshake and locks liquidity."""
    item = Listing.query.get_or_404(listing_id)
    if item.user_id == current_user.id:
        flash("Unauthorized: You cannot purchase your own asset.", "danger")
        return redirect(url_for('main.product_detail', listing_id=item.id))

    if current_user.wallet_balance < item.price:
        flash(f"Insufficient Funds.", "danger")
        return redirect(url_for('main.dashboard'))

    try:
        current_user.wallet_balance -= item.price
        new_order = Order(total_price=item.price, buyer_id=current_user.id, listing_id=item.id, status='Escrowed')
        item.status = 'Pending Handshake'
        
        db.session.add(new_order)
        db.session.add(Transaction(amount=item.price, type='Debit', reference=f"PAY-{new_order.handshake_id}", user_id=current_user.id))
        db.session.commit()
        
        # Build #5: Dual-Channel Signal (SMS + Dashboard)
        sync_handshake_pulse(new_order)
        
        flash("Handshake Successful! Funds locked in Vault.", "success")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        db.session.rollback(); flash(f"System Error: {str(e)}", "danger")
    return redirect(url_for('main.product_detail', listing_id=item.id))

@main.route("/release_funds/<int:order_id>", methods=['POST'])
@login_required
def release_funds(order_id):
    """The Final Handshake: Syncs funds, ratings, and merchant tiers."""
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id: return "Unauthorized", 403
    
    # ❄️ AUDIT: Dispute Check (Build #6 lockout)
    if order.status == 'Disputed':
        flash("Vault Locked: Order is under judicial investigation.", "danger")
        return redirect(url_for('main.dashboard'))
    
    try:
        pilot_rating = None
        if order.driver_id:
            try:
                pilot_rating = int(request.form.get('pilot_rating', 5))
            except Exception:
                pilot_rating = 5

        released, msg = release_order_funds(order, pilot_rating=pilot_rating)
        if released:
            flash("Handshake Finalized. Funds released.", "success")
        else:
            flash(f"Release skipped: {msg}", "warning")
    except Exception as e:
        db.session.rollback(); flash(f"Failure: {str(e)}", "danger")
    return redirect(url_for('main.dashboard'))

# --- ⚖️ 4. JUDICIAL NODE (DISPUTES & VERIFICATION) ---

@main.route("/raise_dispute/<int:order_id>", methods=['GET', 'POST'])
@login_required
def raise_dispute(order_id):
    """Protocol to freeze funds and signal a transaction failure."""
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id: return "Unauthorized", 403
    
    form = DisputeForm()
    if form.validate_on_submit():
        order.status = 'Disputed'
        new_dispute = Dispute(reason=form.reason.data, order_id=order.id, claimant_id=current_user.id)
        db.session.add(new_dispute)
        db.session.commit()
        flash("Dispute Registered. Vault Frozen.", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('raise_dispute.html', form=form, order=order)

@main.route("/admin/resolve-dispute/<int:dispute_id>/<string:command>", methods=['POST'])
@login_required
def resolve_dispute(dispute_id, command):
    """The Judge Terminal: Forced resolution (Build #6)."""
    if not current_user.is_admin: return "Unauthorized", 403
    dispute = Dispute.query.get_or_404(dispute_id)
    order = Order.query.get(dispute.order_id)

    if command == 'pay_merchant':
        merchant = User.query.get(order.listing.user_id)
        merchant.wallet_balance += order.total_price
        order.status = 'Completed'
        flash("Justice: Merchant Paid.", "success")
    elif command == 'refund_buyer':
        order.buyer.wallet_balance += order.total_price
        order.status = 'Refunded'
        flash("Justice: Buyer Refunded.", "info")
    
    dispute.status = 'Resolved'
    db.session.commit()
    return redirect(url_for('main.admin_dispute_center'))

@main.route("/admin/verify-user/<int:user_id>", methods=['POST'])
@login_required
def toggle_verification(user_id):
    """Build #7: KYC Verification Node."""
    if not current_user.is_admin: return "Unauthorized", 403
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    return redirect(url_for('main.admin_vault_control'))

# --- 📦 5. MERCHANT HUB (ASSET & REVENUE CONTROL) ---

@main.route("/merchant/hub")
@login_required
def merchant_hub():
    """Terminal for managing merchant assets and revenue stats."""
    my_listings = Listing.query.filter_by(user_id=current_user.id).all()
    revenue = db.session.query(func.sum(Order.total_price)).join(Listing).filter(Listing.user_id == current_user.id, Order.status == 'Completed').scalar() or 0
    pending_revenue = db.session.query(func.sum(Order.total_price)).join(Listing).filter(Listing.user_id == current_user.id, Order.status != 'Completed').scalar() or 0
    incoming_orders = Order.query.join(Listing).filter(Listing.user_id == current_user.id, Order.status != 'Completed').all()
    return render_template('merchant_hub.html', listings=my_listings, revenue=revenue, pending_revenue=pending_revenue, incoming_orders=incoming_orders)

@main.route("/listing/edit/<int:listing_id>", methods=['POST'])
@login_required
def edit_listing(listing_id):
    """Build #3: Log price fluctuations for FOMO badges."""
    item = Listing.query.get_or_404(listing_id)
    if item.user_id != current_user.id: return "Unauthorized", 403
    old_price = item.price
    try:
        new_price = float(request.form.get('price'))
        if new_price != old_price:
            db.session.add(PriceHistory(price=new_price, listing_id=item.id))
            item.price = new_price
        db.session.commit()
        flash("Signal Updated.", "success")
    except Exception as e:
        db.session.rollback(); flash(f"Update Error: {str(e)}", "danger")
    return redirect(url_for('main.merchant_hub'))

@main.route("/dispatch_order/<int:order_id>", methods=['POST'])
@login_required
def dispatch_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'Dispatched'
    db.session.commit()
    flash("Injected into Logistics Queue.", "success")
    return redirect(url_for('main.merchant_hub'))

# --- 🚁 6. PILOT COMMAND (MISSIONS & POD) ---

@main.route("/pilot/console")
@login_required
def pilot_console():
    if not current_user.is_driver: return redirect(url_for('main.index'))
    available = Order.query.filter_by(status='Dispatched', driver_id=None).all()
    active = Order.query.filter_by(driver_id=current_user.id).filter(Order.status != 'Completed').all()
    history = Order.query.filter_by(driver_id=current_user.id, status='Completed').all()
    return render_template('pilot_console.html', available=available, active=active, history=history)

@main.route("/claim_mission/<int:order_id>", methods=['POST'])
@login_required
def claim_mission(order_id):
    order = Order.query.get_or_404(order_id)
    order.driver_id = current_user.id
    db.session.commit()
    return redirect(url_for('main.pilot_console'))

@main.route("/update_delivery/<int:order_id>/<string:status>", methods=['POST'])
@login_required
def update_delivery(order_id, status):
    """Handles transit states & POD photo binary stream."""
    order = Order.query.get_or_404(order_id)
    try:
        order.status = status
        if status == 'Delivered' and 'delivery_photo' in request.files:
            file = request.files['delivery_photo']
            filename = secure_filename(f"POD_{order.handshake_id}.jpg")
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'deliveries', filename))
        db.session.commit()
    except Exception: db.session.rollback()
    return redirect(url_for('main.pilot_console'))

# --- 🛡️ 7. ADMIN TREASURY (VAULT & WITHDRAWALS) ---

@main.route("/admin/vault-control")
@login_required
def admin_vault_control():
    """Build #9 Master Admin Terminal."""
    if not current_user.is_admin: return redirect(url_for('main.index'))
    pending_wdr = Withdrawal.query.filter_by(status='Pending').all()
    releases = Transaction.query.filter(Transaction.reference.like('RELEASE-%')).order_by(Transaction.timestamp.desc()).limit(20).all()
    all_merchants = User.query.filter_by(is_driver=False, is_admin=False).all()
    return render_template('admin_vault.html', pending_wdr=pending_wdr, releases=releases, all_merchants=all_merchants)

@main.route("/admin/emergency-lock", methods=['POST'])
@login_required
def vault_emergency_lock():
    """🛑 RED BUTTON (Build #5): Instant global freeze."""
    if not current_user.is_admin: return "Unauthorized", 403
    Withdrawal.query.filter_by(status='Pending').update({Withdrawal.status: 'Frozen'})
    db.session.commit()
    flash("VAULT SECURED: All exits FROZEN.", "danger")
    return redirect(url_for('main.admin_vault_control'))

@main.route("/admin/approve-withdrawal/<int:wdr_id>", methods=['POST'])
@login_required
def approve_withdrawal(wdr_id):
    """Build #10: Audit trail payout."""
    if not current_user.is_admin: return "Unauthorized", 403
    wdr = Withdrawal.query.get_or_404(wdr_id)
    wdr.status = 'Completed'
    create_grid_notification(wdr.user_id, "Liquidity Dispatched", f"₦{wdr.amount:,.0f} sent.", "success")
    db.session.commit()
    return redirect(url_for('main.admin_vault_control'))

# --- 💸 8. FINANCIAL & BUYER DASHBOARD ---

@main.route("/withdraw", methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawalForm()
    if form.validate_on_submit():
        if current_user.wallet_balance < form.amount.data:
            flash("Insufficient Liquidity.", "danger")
            return redirect(url_for('main.withdraw'))
        try:
            amt = float(form.amount.data)
            current_user.wallet_balance -= amt
            db.session.add(Withdrawal(amount=amt, bank_name=form.bank_name.data, account_number=form.account_number.data, account_name=form.account_name.data, user_id=current_user.id))
            db.session.add(Transaction(amount=amt, type='Debit', reference=f"WDR-{secrets.token_hex(4).upper()}", user_id=current_user.id))
            db.session.commit()
            
            msg = f"FlipTrybe: WDR Received for ₦{amt:,.0f}. PENDING."
            try: transmit_termii_signal.delay(current_user.phone, msg)
            except: pass 
            
            flash(f"Withdrawal Initiated.", "success")
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback(); flash(f"Error: {str(e)}", "danger")
    return render_template('withdraw.html', form=form)

@main.route("/dashboard")
@login_required
def dashboard():
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.timestamp.desc()).all()
    history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template('dashboard.html', orders_bought=orders, history=history)
