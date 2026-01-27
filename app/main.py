import os
import requests
import uuid
import random
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from .models import db, User, Listing, Order, Dispute, Message
from sqlalchemy import func, or_, and_
from .notifications import sync_sale_notifications, notify_driver_assigned, notify_driver_arrival

main = Blueprint('main', __name__)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_34d39847e8d590a6967487d95f60f421409e0b08")

# ==========================================
# 🚨 ERROR HANDLERS & SUPPORT (NEW)
# ==========================================

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        # In a real app, this would send an email via SendGrid/Mailgun
        email = request.form.get('email')
        subject = request.form.get('subject')
        flash("Ticket received! Support will contact you shortly.", "success")
        return redirect(url_for('main.support'))
    return render_template('support.html')

# ==========================================
# 💬 CHAT SYSTEM (PHASE 2)
# ==========================================

@main.route('/inbox')
@login_required
def inbox():
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids = set([x[0] for x in sent.all()] + [x[0] for x in received.all()])
    contacts = User.query.filter(User.id.in_(contact_ids)).all()
    return render_template('inbox.html', contacts=contacts)

@main.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    partner = User.query.get_or_404(user_id)
    if request.method == 'POST':
        body = request.form.get('message')
        if body:
            msg = Message(sender_id=current_user.id, receiver_id=partner.id, body=body)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('main.chat', user_id=partner.id))
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == partner.id),
            and_(Message.sender_id == partner.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', partner=partner, messages=messages)

@main.route('/start-chat/<int:listing_id>')
@login_required
def start_chat(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return redirect(url_for('main.chat', user_id=listing.agent_id))

# ==========================================
# ⚙️ SETTINGS & PROFILE
# ==========================================

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        if current_user.is_driver:
            current_user.vehicle_type = request.form.get('vehicle')
        new_pass = request.form.get('password')
        if new_pass:
            current_user.password = generate_password_hash(new_pass, method='sha256')
            flash("Password updated.", "success")
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            filename = secure_filename(f"user_{current_user.id}_{file.filename}")
            path = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
            os.makedirs(path, exist_ok=True)
            file.save(os.path.join(path, filename))
            current_user.profile_pic = filename
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('main.settings'))
    return render_template('settings.html')

# ==========================================
# 👑 ADMIN COMMAND CENTER
# ==========================================

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access Denied: Admins Only.", "error")
        return redirect(url_for('main.dashboard'))
    completed_orders = Order.query.filter_by(delivery_status='Delivered').all()
    total_volume = sum(o.total_price for o in completed_orders)
    platform_revenue = total_volume * 0.05 
    active_disputes = Dispute.query.filter_by(status='Open').order_by(Dispute.is_emergency.desc()).all()
    all_users = User.query.all()
    return render_template('admin_dashboard.html', revenue=platform_revenue, volume=total_volume, disputes=active_disputes, users=all_users)

@main.route('/admin/resolve/<int:dispute_id>/<action>', methods=['POST'])
@login_required
def resolve_dispute(dispute_id, action):
    if not current_user.is_admin: return redirect(url_for('main.index'))
    dispute = Dispute.query.get_or_404(dispute_id)
    order = dispute.order
    if action == 'refund_buyer':
        order.buyer.wallet_balance += order.total_price
        order.delivery_status = 'Refunded'
        dispute.status = 'Resolved (Refunded)'
        flash(f"Refused ₦{order.total_price:,.0f} to Buyer.", "success")
    elif action == 'release_agent':
        payout = order.total_price * 0.95
        order.listing.agent.wallet_balance += payout
        order.delivery_status = 'Delivered (Force Released)'
        dispute.status = 'Resolved (released)'
        flash(f"Funds released to Agent. Dispute closed.", "success")
    db.session.commit()
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin: return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("You cannot delete another Admin.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.name} has been banned/deleted.", "success")
    return redirect(url_for('main.admin_dashboard'))

# ==========================================
# 🌐 MARKET & PUBLIC ROUTES
# ==========================================

@main.route('/')
def index():
    featured = Listing.query.filter_by(status='Available').limit(4).all()
    return render_template('index.html', items=featured)

@main.route('/market')
def market():
    q = request.args.get('q')
    cat = request.args.get('category')
    state = request.args.get('state')
    query = Listing.query.filter_by(status='Available')
    if q: query = query.filter(Listing.title.ilike(f'%{q}%'))
    if cat: query = query.filter_by(category=cat)
    if state: query = query.filter(Listing.state.ilike(f'%{state}%'))
    items = query.order_by(Listing.price.asc()).all()
    return render_template('market.html', items=items)

# ==========================================
# 🛰️ LOGISTICS TRACKING
# ==========================================

@main.route('/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Unauthorized access.", "error")
        return redirect(url_for('main.index'))
    return render_template('success.html', order=order)

# ==========================================
# 💰 PAYMENT & TRANSACTION ENGINE
# ==========================================

@main.route('/buy/<int:listing_id>', methods=['POST'])
@login_required
def buy_item(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if current_user.id == listing.agent_id:
        flash("You cannot buy your own listing!", "error")
        return redirect(url_for('main.market'))
    if current_user.wallet_balance < listing.price:
        flash('Insufficient funds.', 'error')
        return redirect(url_for('main.dashboard'))
    secret_pin = str(random.randint(1000, 9999))
    current_user.wallet_balance -= listing.price
    listing.status = 'Sold'
    order = Order(total_price=listing.price, buyer_id=current_user.id, listing_id=listing.id, delivery_status='Pending', verification_pin=secret_pin)
    db.session.add(order)
    db.session.commit()
    try: sync_sale_notifications(order)
    except: pass
    flash(f'Success! Tracking started.', 'success')
    return redirect(url_for('main.order_success', order_id=order.id))

@main.route('/initiate-paystack', methods=['POST'])
@login_required
def initiate_paystack():
    amount = request.form.get('amount', type=float)
    if not amount: return jsonify({"success": False})
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    data = {"email": current_user.email, "amount": int(amount * 100), "callback_url": url_for('main.dashboard', _external=True), "reference": str(uuid.uuid4())}
    try:
        response = requests.post(url, json=data, headers=headers)
        res_data = response.json()
        if res_data["status"]: return redirect(res_data["data"]["authorization_url"])
    except: pass
    return redirect(url_for('main.dashboard'))

# ==========================================
# 👤 DASHBOARDS & ROLES
# ==========================================

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        amt = request.form.get('amount', type=float)
        if amt:
            current_user.wallet_balance += amt
            db.session.commit()
            flash(f'₦{amt:,.0f} added.', 'success')
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, orders=orders)

@main.route('/agent-office')
@login_required
def agent_office():
    if not current_user.is_agent: return redirect(url_for('main.dashboard'))
    listings = Listing.query.filter_by(agent_id=current_user.id).all()
    return render_template('agent_office.html', listings=listings, s_avg=45000, d_avg=15000)

@main.route('/driver-dashboard')
@login_required
def driver_dashboard():
    if not current_user.is_driver: return redirect(url_for('main.dashboard'))
    avail = Order.query.filter_by(driver_id=None, delivery_status='Pending').all()
    act = Order.query.filter_by(driver_id=current_user.id).filter(Order.delivery_status != 'Delivered').all()
    return render_template('driver.html', available=avail, active=act)

# ==========================================
# 🚚 LOGISTICS ACTIONS
# ==========================================

@main.route('/accept-task/<int:order_id>', methods=['POST'])
@login_required
def accept_task(order_id):
    order = Order.query.get_or_404(order_id)
    order.driver_id = current_user.id
    order.delivery_status = 'Assigned'
    db.session.commit()
    try: notify_driver_assigned(order)
    except: pass
    return redirect(url_for('main.driver_dashboard'))

@main.route('/mark-arrived/<int:order_id>', methods=['POST'])
@login_required
def mark_arrived(order_id):
    order = Order.query.get_or_404(order_id)
    if order.driver_id != current_user.id: return redirect(url_for('main.index'))
    order.delivery_status = 'Driver Arrived'
    db.session.commit()
    try: notify_driver_arrival(order)
    except: pass
    flash("Arrival sent!", "success")
    return redirect(url_for('main.driver_dashboard'))

@main.route('/complete-task/<int:order_id>', methods=['POST'])
@login_required
def complete_task(order_id):
    order = Order.query.get_or_404(order_id)
    if order.driver_id == current_user.id:
        provided_pin = request.form.get('pin')
        if provided_pin != order.verification_pin:
            flash("Invalid PIN!", "error")
            return redirect(url_for('main.driver_dashboard'))
        order.delivery_status = 'Delivered'
        payout = order.total_price * 0.95
        order.listing.agent.wallet_balance += payout
        db.session.commit()
        flash(f'Verified! ₦{payout:,.0f} released.', 'success')
    return redirect(url_for('main.driver_dashboard'))

# ==========================================
# 🛠️ UPLOAD & MANAGEMENT
# ==========================================

@main.route('/upload', methods=['POST'])
@login_required
def upload_item():
    if not current_user.is_agent: return redirect(url_for('main.dashboard'))
    file = request.files.get('image')
    filename = secure_filename(file.filename) if file else None
    if file:
        path = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        os.makedirs(path, exist_ok=True)
        file.save(os.path.join(path, filename))
    listing = Listing(title=request.form.get('title'), price=float(request.form.get('price')), category=request.form.get('category'), state=request.form.get('state'), city=request.form.get('city'), image_filename=filename, agent_id=current_user.id)
    db.session.add(listing)
    db.session.commit()
    return redirect(url_for('main.agent_office'))

@main.route('/delete-listing/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.agent_id == current_user.id:
        db.session.delete(listing)
        db.session.commit()
        flash('Listing removed.', 'success')
    return redirect(url_for('main.agent_office'))

@main.route('/file-dispute/<int:order_id>', methods=['POST'])
@login_required
def file_dispute(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id == current_user.id:
        d = Dispute(reason=request.form.get('reason'), details=request.form.get('details'), order_id=order.id, user_id=current_user.id, is_emergency=(request.form.get('reason') == 'EMERGENCY SOS'))
        order.delivery_status = 'Flagged'
        db.session.add(d)
        db.session.commit()
        flash('Dispute filed. Admin will review.', 'error')
    return redirect(url_for('main.dashboard'))