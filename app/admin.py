from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import User, Order, Dispute, Listing, Transaction, Notification
from datetime import datetime
from functools import wraps

# 🧪 PHYSICAL SIGNAL BRIDGE (Commented out to prevent crash if file missing)
# from app.signals import transmit_termii_signal 

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
    
    # 1. Fetch Disputes
    disputes = Dispute.query.filter_by(status='Open').all()
    
    # 2. ✅ FIXED: Fetch Pending KYC (Users with ID uploaded but NOT verified)
    pending_kyc = User.query.filter(
        User.kyc_id_card_file != None, 
        User.is_verified == False
    ).all()
    
    # 3. Revenue Logic (Safe Match)
    # tribe_revenue = db.session.query(func.sum(Transaction.fee_deducted)).scalar() or 0
    tribe_revenue = 0 # Placeholder until you build Transaction Logic

    # 4. User Search
    user_query = request.args.get('user_q')
    if user_query:
        users = User.query.filter(User.username.ilike(f"%{user_query}%")).all()
    else:
        users = User.query.order_by(User.id.desc()).limit(20).all()

    return render_template('admin.html', 
                           disputes=disputes, 
                           pending_kyc=pending_kyc,
                           users=users,
                           tribe_revenue=tribe_revenue)

# ==========================================
# 🛡️ IDENTITY JUDGMENT (KYC Audit)
# ==========================================
@admin.route('/admin/verify-user/<int:user_id>/<status>', methods=['POST'])
@admin_required
def audit_kyc(user_id, status):
    """Calibrated Decision Engine: Approve or Reject identity signals."""
    user = User.query.get_or_404(user_id)

    if status == 'approve':
        # ✅ FIXED: Just set the boolean
        user.is_verified = True
        flash(f"Node Verified! {user.username} is now a trusted member.", "success")
        
        # (Optional) Send Notification Logic Here
        # db.session.add(Notification(user_id=user.id, title="Verified", message="Access Granted."))

    elif status == 'reject':
        # 🛡️ RESET SIGNAL: Delete files so they can upload again
        user.is_verified = False
        user.kyc_id_card_file = None
        user.kyc_selfie_file = None
        flash(f"KYC Rejected for {user.username}. Files cleared for re-upload.", "warning")

    db.session.commit()
    return redirect(url_for('admin.admin_panel'))