import os
import requests
from flask import current_app
from app import db, celery # 🟢 Integrated Celery
from app.models import Notification

# --- 🛰️ SIGNAL TRANSMITTER (TERMII ASYNC) ---

@celery.task
def transmit_termii_signal(to_phone, message, channel="dnd"):
    """
    Transmits an industrial-grade SMS signal via Termii in the background.
    """
    if not to_phone:
        return None
    
    # 1. Standardize Phone Format
    clean_phone = to_phone.strip()
    if clean_phone.startswith('0'):
        clean_phone = '234' + clean_phone[1:]
    elif not clean_phone.startswith('234'):
        clean_phone = '234' + clean_phone

    # 2. Prepare Payload
    api_key = os.environ.get('TERMII_API_KEY')
    sender_id = os.environ.get('TERMII_SENDER_ID', 'FlipTrybe')
    
    payload = {
        "to": clean_phone,
        "from": sender_id,
        "sms": message,
        "type": "plain",
        "channel": channel,
        "api_key": api_key
    }
    
    url = "https://api.ng.termii.com/api/sms/send"
    try:
        # No context needed for requests, but api_key must be passed or pulled from env
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"⚠️ Worker Signal Failure: {str(e)}")
        return None

# --- 🔐 SECURITY (OTP ASYNC) ---

@celery.task
def send_otp_signal(phone_number):
    """Sends OTP via Termii API as a background task."""
    clean_phone = phone_number
    if clean_phone.startswith('0'):
        clean_phone = '234' + clean_phone[1:]
        
    url = "https://api.ng.termii.com/api/sms/otp/send"
    payload = {
        "api_key": os.environ.get('TERMII_API_KEY'),
        "message_type": "NUMERIC",
        "to": clean_phone,
        "from": "FlipTrybe",
        "channel": "dnd",
        "pin_attempts": 3,
        "pin_time_to_live": 5,
        "pin_length": 6,
        "pin_placeholder": "< 1234 >"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"Termii OTP Error: {e}")
        return {}

# --- 🔔 INTERNAL DASHBOARD NOTIFICATIONS ---
# These stay synchronous because db.commit() is fast local logic

def create_grid_notification(user_id, title, message, category='info'):
    """Persists a notification to the database for the user dashboard."""
    from app.models import Notification # Local import to avoid circular dependency
    note = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category
    )
    db.session.add(note)
    db.session.commit()

# --- 📲 TRANSACTIONAL LOGIC ---

def sync_escrow_notifications(order):
    """
    Buyer/Seller Dashboard + Async SMS alerts.
    """
    # Dashboard (Instant)
    create_grid_notification(order.listing.seller.id, "New Order", f"Funds locked for '{order.listing.title}'.", "success")
    create_grid_notification(order.buyer_id, "Escrow Secured", f"Funds secured for '{order.listing.title}'.", "info")

    # SMS (Offloaded to Worker)
    seller_sms = f"💰 FlipTrybe: Item Sold! Funds locked for '{order.listing.title}'. Prepare for dispatch."
    buyer_sms = f"🛡️ FlipTrybe Escrow: Funds secured for '{order.listing.title}'. Seller notified."
    
    transmit_termii_signal.delay(order.listing.seller.phone, seller_sms)
    transmit_termii_signal.delay(order.buyer.phone, buyer_sms)

def notify_pilot_assignment(order):
    if order.driver_id:
        msg = f"New Mission: Pickup '{order.listing.title}' at {order.listing.state}."
        create_grid_notification(order.driver_id, "Mission Assigned", msg, "warning")
        transmit_termii_signal.delay(order.driver.phone, f"🚁 FlipTrybe Logistics:\n{msg}")

# --- 💳 FINANCIAL GATEWAY ---

def initialize_paystack_payment(email, amount, reference):
    """Handles Paystack initialization."""
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {os.environ.get('PAYSTACK_SECRET_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": reference,
        "callback_url": os.environ.get('PAYSTACK_CALLBACK_URL')
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        return {"status": False, "message": str(e)}