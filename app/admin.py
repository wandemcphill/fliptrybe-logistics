from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import db, User, Order, Dispute, Listing, Transaction, Notification
from datetime import datetime
from functools import wraps

# 🧪 PHYSICAL SIGNAL BRIDGE
from app.signals import transmit_termii_signal

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Unauthorized Access: Admins Only.", "error")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@admin_required
def admin_panel():
    """Renders Command Center - Focus: Disputes, KYC, and User Registry."""
    disputes = Dispute.query.filter_by(status='Open').all()
    pending_kyc = User.query.filter_by(kyc_status='Pending').all()
    tribe_revenue = db.session.query(func.sum(Transaction.fee_deducted)).scalar() or 0
    
    # 🏎️ PILOT LEADERBOARD
    leaderboard = db.session.query(
        User.name, 
        func.sum(Order.total_price).label('vol')
    ).join(Order, User.id == Order.driver_id)\
     .filter(Order.delivery_status == 'Delivered')\
     .group_by(User.id).order_by(func.desc('vol')).limit(5).all()

    user_query = request.args.get('user_q')
    users = User.query.filter(User.name.ilike(f"%{user_query}%")).all() if user_query else \
            User.query.order_by(User.last_seen.desc()).limit(50).all()

    return render_template('admin.html', 
                           disputes=disputes, 
                           pending_kyc=pending_kyc,
                           users=users,
                           tribe_revenue=tribe_revenue,
                           leaderboard=leaderboard)

# ==========================================
# 🛡️ IDENTITY JUDGMENT (KYC Audit)
# ==========================================
@admin.route('/admin/verify-user/<int:user_id>/<status>', methods=['POST'])
@admin_required
def audit_kyc(user_id, status):
    """Calibrated Decision Engine: Approve or Reject identity signals."""
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason', 'Signal requirements not met.')

    if status == 'approve':
        user.kyc_status = 'Verified'
        user.is_verified = True
        msg = f"FlipTrybe: Node Verified! Welcome to the Tribe, {user.name}."
        notif_title, notif_msg = "✅ IDENTITY VERIFIED", "HQ has verified your signal. Full terminal access granted."
    else:
        # 🛡️ RESET SIGNAL: Allow user to re-upload
        user.kyc_status = 'Unverified'
        user.is_verified = False
        msg = f"FlipTrybe: KYC Rejected. Reason: {reason}. Please re-upload your signal."
        notif_title, notif_msg = "❌ KYC REJECTED", f"Your identity signal was rejected. Reason: {reason}"

    # Dispatch Signals
    db.session.add(Notification(user_id=user.id, title=notif_title, message=notif_msg))
    if user.phone:
        transmit_termii_signal(user.phone, msg)
    
    db.session.commit()
    flash(f"User {user.name} audit complete: {status.upper()}", "success")
    return redirect(url_for('admin.admin_panel'))

# ==========================================
# ⚖️ SOS RESOLUTION (Disputes)
# ==========================================
@admin.route('/admin/resolve-dispute/<int:dispute_id>/<action>', methods=['POST'])
@admin_required
def resolve_dispute(dispute_id, action):
    dispute = Dispute.query.get_or_404(dispute_id)
    order = dispute.order

    if action == 'refund':
        order.buyer.wallet_balance += order.total_price
        order.delivery_status, order.listing.status = 'Refunded', 'Available'
        if order.buyer.phone:
            transmit_termii_signal(order.buyer.phone, f"FT-HQ: ₦{order.total_price:,.0f} returned to wallet.")
    
    elif action == 'unlock':
        fee = order.total_price * 0.05
        payout = order.total_price - fee
        order.listing.seller.wallet_balance += payout
        order.delivery_status = 'Delivered (HQ Release)'
        db.session.add(Transaction(amount=order.total_price, fee_deducted=fee, type='Sale', user_id=order.listing.seller.id))
        if order.listing.seller.phone:
            transmit_termii_signal(order.listing.seller.phone, f"FT-HQ: Escrow released. ₦{payout:,.0f} added to wallet.")
    
    dispute.status = 'Resolved'
    db.session.commit()
    flash(f"Dispute {dispute_id} signal terminated via {action}.", "success")
    return redirect(url_for('admin.admin_panel'))