import os
import hmac
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from app import db, login_manager
from app.models import User, Listing, Order, Transaction, Dispute, Withdrawal, Notification
from app.utils import create_grid_notification, transmit_termii_signal, release_order_funds

admin = Blueprint('admin', __name__)

# --- 🛰️ MASTER ACCESS BARRIER ---
@admin.before_request
def restrict_to_admins():
    """Build-Bundle Audit: Ensures only 'Admin' nodes can access these routes."""
    cron_secret = (os.getenv("ESCROW_CRON_TOKEN") or "").strip()
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.replace("Bearer ", "", 1).strip() if auth_header.startswith("Bearer ") else ""
    token_ok = bool(cron_secret and bearer and hmac.compare_digest(bearer, cron_secret))
    if token_ok:
        return None
    if not current_user.is_authenticated:
        if request.endpoint == 'admin.escrow_run':
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return login_manager.unauthorized()
    if not current_user.is_admin:
        if request.endpoint == 'admin.escrow_run':
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        flash("CRITICAL: Unauthorized access attempt to Command Node.", "danger")
        return redirect(url_for('main.index'))

# --- ESCROW AUTO-RELEASE (CRON SAFE) ---

@admin.route("/escrow/run", methods=['POST'])
def escrow_run():
    cron_secret = (os.getenv("ESCROW_CRON_TOKEN") or "").strip()
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.replace("Bearer ", "", 1).strip() if auth_header.startswith("Bearer ") else ""

    token_ok = bool(cron_secret and bearer and hmac.compare_digest(bearer, cron_secret))
    admin_ok = current_user.is_authenticated and getattr(current_user, "is_admin", False)
    if not (token_ok or admin_ok):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    try:
        limit = int(payload.get("limit", 50))
    except Exception:
        limit = 50
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    # Delivery-confirmed state(s) based on current lifecycle in models.py
    delivery_states = {"Delivered"}
    if not delivery_states:
        return jsonify({
            "status": "ok",
            "processed": 0,
            "skipped": 0,
            "processed_order_ids": [],
            "errors": ["Auto-release disabled: no delivery-confirmed state configured"]
        }), 200

    orders = Order.query.filter(Order.status.in_(delivery_states)).limit(limit).all()
    processed_ids = []
    skipped = 0
    errors = []

    for order in orders:
        if order.status == 'Disputed':
            skipped += 1
            errors.append(f"order {order.id}: disputed")
            continue
        try:
            released, msg = release_order_funds(order, pilot_rating=None)
            if released:
                processed_ids.append(order.id)
            else:
                skipped += 1
                if msg:
                    errors.append(f"order {order.id}: {msg}")
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            errors.append(f"order {order.id}: {str(e)}")

    return jsonify({
        "status": "ok",
        "processed": len(processed_ids),
        "skipped": skipped,
        "processed_order_ids": processed_ids,
        "errors": errors
    }), 200

# --- 💰 1. TREASURY CONTROL (Build #5, #9, #10) ---

@admin.route("/vault-control")
def vault_control():
    """
    Build #9: Master Treasury Terminal.
    Displays global liquidity (Heatmap), pending payouts, and release logs.
    """
    pending_wdr = Withdrawal.query.filter_by(status='Pending').order_by(Withdrawal.request_date.desc()).all()
    releases = Transaction.query.filter(Transaction.reference.like('RELEASE-%')).order_by(Transaction.timestamp.desc()).limit(20).all()
    
    # Calculate Total Grid Liquidity (Build #9 Heatmap Signal)
    vault_total = db.session.query(func.sum(Order.total_price)).filter_by(status='Escrowed').scalar() or 0
    
    # Registry for Build #7
    all_merchants = User.query.filter_by(is_driver=False).all()
    
    return render_template('admin_vault.html', 
                           pending_wdr=pending_wdr, 
                           releases=releases, 
                           vault_total=vault_total,
                           all_merchants=all_merchants)

@admin.route("/emergency-lock", methods=['POST'])
def emergency_lock():
    """Build #5: The Red Button. Instantly freezes all pending exits."""
    try:
        pending = Withdrawal.query.filter_by(status='Pending').all()
        for wdr in pending:
            wdr.status = 'Frozen'
        
        db.session.commit()
        flash("VAULT SECURED: All pending liquidity signals have been FROZEN.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Security Failure: {str(e)}", "danger")
    return redirect(url_for('admin.vault_control'))

@admin.route("/approve-payout/<int:wdr_id>", methods=['POST'])
def approve_payout(wdr_id):
    """Build #10: Audited Payout Release."""
    wdr = Withdrawal.query.get_or_404(wdr_id)
    if wdr.status != 'Pending':
        flash("Signal Error: Payout is no longer pending.", "warning")
        return redirect(url_for('admin.vault_control'))

    try:
        wdr.status = 'Completed'
        # Trigger internal notification
        create_grid_notification(wdr.user_id, "Liquidity Dispatched", f"₦{wdr.amount:,.0f} sent to your bank.", "success")
        
        db.session.commit()
        flash(f"Liquidity Released to {wdr.user.name}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Transaction Failure: {str(e)}", "danger")
    return redirect(url_for('admin.vault_control'))

# --- ⚖️ 2. JUDICIAL TERMINAL (Build #6) ---

@admin.route("/dispute-terminal")
def dispute_terminal():
    """Build #6: Judicial Node to settle active grid conflicts."""
    active_disputes = Dispute.query.filter_by(status='Open').all()
    return render_template('admin_disputes.html', disputes=active_disputes)

@admin.route("/resolve-conflict/<int:dispute_id>/<string:verdict>", methods=['POST'])
def resolve_conflict(dispute_id, verdict):
    """Execution of judicial verdicts: Forces refund or merchant payment."""
    dispute = Dispute.query.get_or_404(dispute_id)
    order = dispute.order

    try:
        if verdict == 'pay_merchant':
            # Force Payout
            order.listing.seller.wallet_balance += order.total_price
            order.status = 'Completed'
            flash("VERDICT: Merchant Paid. Vault node cleared.", "success")
        
        elif verdict == 'refund_buyer':
            # Force Refund
            order.buyer.wallet_balance += order.total_price
            order.status = 'Refunded'
            flash("VERDICT: Buyer Refunded. Liquidity returned.", "info")

        dispute.status = 'Resolved'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Judicial Failure: {str(e)}", "danger")
    
    return redirect(url_for('admin.dispute_terminal'))

# --- 🛡️ 3. IDENTITY REGISTRY (Build #7) ---

@admin.route("/verify-merchant/<int:user_id>", methods=['POST'])
def verify_merchant(user_id):
    """Build #7: KYC Verification Node. Manages Blue Badge status."""
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified # Instant Toggle
    
    status_msg = "VERIFIED" if user.is_verified else "REVOKED"
    db.session.commit()
    
    flash(f"Merchant ID-{user.id}: Trust Signal {status_msg}.", "success")
    return redirect(url_for('admin.vault_control'))
