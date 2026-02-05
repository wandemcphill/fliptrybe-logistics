import os
import requests
from flask import current_app
from app import db, celery

# --- 🎖️ 1. GRID PERFORMANCE PROTOCOLS (Build #1) ---

def update_merchant_tier(user_id):
    """
    Build #1: Automated Trust Signals.
    Synchronizes with release_funds to promote merchants based on success.
    """
    from app.models import User, Order, Listing
    
    user = User.query.get(user_id)
    if not user:
        return None

    # Audit successful handshake volume
    success_count = Order.query.join(Listing).filter(
        Listing.user_id == user.id, 
        Order.status == 'Completed'
    ).count()

    # Tier Thresholds
    if success_count >= 50:
        user.merchant_tier = "Grid-Master"
    elif success_count >= 10:
        user.merchant_tier = "Verified Merchant"
    else:
        user.merchant_tier = "Novice"
    
    db.session.commit()
    return user.merchant_tier

def release_order_funds(order, pilot_rating=None):
    """
    Releases funds for an order already confirmed delivered.
    Returns (released: bool, message: str|None).
    """
    from app.models import Transaction, User

    if not order:
        return False, "order missing"
    if order.status == 'Disputed':
        return False, "order disputed"
    if order.status == 'Completed':
        return False, "already completed"

    release_ref = f"RELEASE-{order.handshake_id}"
    if Transaction.query.filter_by(reference=release_ref).first():
        return False, "already released"

    merchant = User.query.get(order.listing.user_id) if order.listing else None
    if not merchant:
        return False, "merchant not found"

    merchant.wallet_balance += order.total_price
    order.status = 'Completed'
    if order.listing:
        order.listing.status = 'Sold'

    if pilot_rating is not None and order.driver_id:
        try:
            rating = int(pilot_rating)
        except Exception:
            rating = 5
        pilot = User.query.get(order.driver_id)
        if pilot:
            pilot.pilot_rating_sum += rating
            pilot.pilot_rating_count += 1

    db.session.add(Transaction(amount=order.total_price, type='Credit', reference=release_ref, user_id=merchant.id))
    db.session.commit()

    # Build #1: Tiering update
    update_merchant_tier(merchant.id)
    return True, None

# --- 🛰️ 2. SIGNAL TRANSMITTER (TERMII ASYNC) ---

@celery.task(name='app.utils.transmit_termii_signal')
def transmit_termii_signal(to_phone, message, channel="dnd"):
    """
    Industrial-grade SMS signal via Termii.
    Offloaded to Celery to prevent web-node latency.
    """
    if not to_phone:
        return None
    
    # Standardize Nigerian Format
    clean_phone = str(to_phone).strip()
    if clean_phone.startswith('0'):
        clean_phone = '234' + clean_phone[1:]
    elif not clean_phone.startswith('234'):
        clean_phone = '234' + clean_phone

    api_key = os.environ.get('TERMII_API_KEY')
    url = "https://api.ng.termii.com/api/sms/send"
    
    payload = {
        "to": clean_phone,
        "from": os.environ.get('TERMII_SENDER_ID', 'FlipTrybe'),
        "sms": message,
        "type": "plain",
        "channel": channel,
        "api_key": api_key
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"⚠️ SIGNAL FAILURE: Termii Node Unreachable: {str(e)}")
        return None

@celery.task(name='app.utils.send_otp_signal')
def send_otp_signal(phone_number):
    """Build #7: Secure Identity Handshake via Numeric PIN."""
    clean_phone = str(phone_number).strip()
    if clean_phone.startswith('0'):
        clean_phone = '234' + clean_phone[1:]
        
    url = "https://api.ng.termii.com/api/sms/otp/send"
    payload = {
        "api_key": os.environ.get('TERMII_API_KEY'),
        "message_type": "NUMERIC",
        "to": clean_phone,
        "from": os.environ.get('TERMII_SENDER_ID', 'FlipTrybe'),
        "channel": "dnd",
        "pin_attempts": 3,
        "pin_time_to_live": 5,
        "pin_length": 6
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"⚠️ SECURITY FAILURE: OTP Node Error: {e}")
        return {}

# --- 🔔 3. INTERNAL GRID NOTIFICATIONS ---

def create_grid_notification(user_id, title, message, category='info'):
    """
    Persists an internal UI notification.
    Synchronous because DB commit is localized and fast.
    """
    from app.models import Notification
    note = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category
    )
    db.session.add(note)
    db.session.commit()

# --- 📲 4. TRANSACTIONAL PULSE (Build #5) ---

def sync_handshake_pulse(order):
    """
    Build #5: The Pulse.
    Multi-channel synchronization for Escrow events.
    """
    from app.models import User
    seller = User.query.get(order.listing.user_id)
    buyer = User.query.get(order.buyer_id)

    # 1. Internal Grid Alerts
    create_grid_notification(seller.id, "Asset Secured", f"Funds for '{order.listing.title}' are locked in Vault.", "success")
    create_grid_notification(buyer.id, "Vault Active", f"Liquidity for '{order.listing.title}' is now in Escrow.", "info")

    # 2. External SMS Signals
    seller_msg = f"💰 FlipTrybe: Sold! ₦{order.total_price:,.0f} locked for '{order.listing.title}'. Prepare dispatch."
    buyer_msg = f"🛡️ FlipTrybe: Handshake Secured! Funds for '{order.listing.title}' are in the Vault."
    
    transmit_termii_signal.delay(seller.phone, seller_msg)
    transmit_termii_signal.delay(buyer.phone, buyer_msg)

def notify_pilot_assignment(order):
    """Logistics Sync: Alerts the Pilot of a mission."""
    from app.models import User
    pilot = User.query.get(order.driver_id)
    if pilot:
        msg = f"Mission: Pickup '{order.listing.title}' in {order.listing.state}."
        create_grid_notification(pilot.id, "Mission Assigned", msg, "warning")
        transmit_termii_signal.delay(pilot.phone, f"🚁 FlipTrybe Logistics: {msg}")

# --- 💳 5. FINANCIAL GATEWAY ---

def initialize_paystack_bridge(email, amount, reference):
    """Paystack liquidity bridge for wallet funding."""
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {os.environ.get('PAYSTACK_SECRET_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": int(amount * 100), # Naira to Kobo
        "reference": reference,
        "callback_url": os.environ.get('PAYSTACK_CALLBACK_URL')
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        return {"status": False, "message": f"Gateway Node Error: {str(e)}"}
