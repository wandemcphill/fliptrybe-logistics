from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import db, User, Order, Dispute, Listing
from sqlalchemy import func

admin = Blueprint('admin', __name__)

@admin.route('/admin')
@login_required
def dashboard():
    # 🔒 Security: Only let real Admins in
    if not current_user.is_admin:
        flash("Unauthorized access!", "error")
        return redirect(url_for('main.index'))

    # 💰 FINANCIAL INTELLIGENCE
    # 1. Gross Volume: Total of all orders
    total_sales = db.session.query(func.sum(Order.total_price)).scalar() or 0
    
    # 2. Net Revenue: FlipTrybe's 5% cut
    net_revenue = total_sales * 0.05

    # 📊 TRIBE STATS
    stats = {
        'gross_volume': total_sales,
        'net_revenue': net_revenue,
        'user_count': User.query.count(),
        'pending_tasks': Order.query.filter_by(delivery_status='Pending').count()
    }

    # 👤 USER SEARCH & MANAGEMENT
    user_query = request.args.get('user_q')
    if user_query:
        users = User.query.filter(User.name.ilike(f"%{user_query}%")).all()
    else:
        users = User.query.limit(10).all()

    orders = Order.query.order_by(Order.order_date.desc()).all()
    disputes = Dispute.query.filter_by(status='Open').all()

    return render_template('admin.html', 
                           stats=stats, 
                           users=users, 
                           orders=orders, 
                           disputes=disputes)

@admin.route('/admin/resolve/<int:dispute_id>', methods=['POST'])
@login_required
def resolve(dispute_id):
    """Admin resolves a dispute by releasing funds to the agent."""
    if not current_user.is_admin: return redirect(url_for('main.index'))
    
    dispute = Dispute.query.get_or_404(dispute_id)
    order = dispute.order
    
    # Release 95% of funds to the Agent
    payout = order.total_price * 0.95
    order.listing.agent.wallet_balance += payout
    
    order.delivery_status = 'Delivered'
    dispute.status = 'Resolved'
    db.session.commit()
    
    flash("Dispute resolved. Funds released to Agent.", "success")
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/refund/<int:dispute_id>', methods=['POST'])
@login_required
def refund(dispute_id):
    """Admin resolves a dispute by refunding the buyer."""
    if not current_user.is_admin: return redirect(url_for('main.index'))
    
    dispute = Dispute.query.get_or_404(dispute_id)
    order = dispute.order
    
    # Return 100% of funds to the Buyer
    order.buyer.wallet_balance += order.total_price
    
    order.delivery_status = 'Refunded'
    dispute.status = 'Refunded'
    db.session.commit()
    
    flash("Refund processed successfully.", "success")
    return redirect(url_for('admin.dashboard'))