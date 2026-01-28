import os, secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models import Listing, Order

main = Blueprint('main', __name__)

# ... (keep your save_file helper here)

@main.route("/escrow")
@login_required
def escrow_dashboard():
    """Handshake Terminal: Where buyers track their pending trades."""
    pending_trades = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('escrow_dashboard.html', trades=pending_trades)

@main.route("/escrow/release/<int:order_id>", methods=['POST'])
@login_required
def release_funds(order_id):
    """Release Signal: Finalizes the escrow handshake."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    order.status = 'Completed'
    order.delivery_status = 'Delivered'
    db.session.commit()
    flash('Handshake Finalized. Funds released to Seller.', 'success')
    return redirect(url_for('main.escrow_dashboard'))

# ... (keep your market, settings, and product_detail routes)