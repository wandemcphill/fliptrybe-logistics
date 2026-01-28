import logging
import os

# Setup logging for terminal diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_whatsapp(phone: str, message: str):
    """
    SIGNAL TRANSMISSION ENGINE
    SIMULATION: Console Output. 
    PROD: Replace with Termii/Twilio API for Nigerian SMS/WA delivery.
    """
    if not phone:
        logger.warning("⚠️ ATTENTION: No phone number provided for signal transmission.")
        return

    logger.info(f"\n📡 [SIGNAL SENT TO {phone}]:\n{message}\n" + "—"*40)

def sync_sale_notifications(order):
    """
    Primary Escrow Synchronization: 
    Notifies Buyer and Seller immediately after a successful 'Escrow Lock'.
    """
    # 🛒 1. THE BUYER (Transmission confirming safe funds hold)
    buyer_msg = (
        f"🛡️ FLIPTRYBE ESCROW SECURED\n\n"
        f"Asset: '{order.listing.title}'\n"
        f"Status: Funds Locked & Protected\n\n"
        f"📍 SELLER LOCATION:\n"
        f"Territory: {order.listing.city}, {order.listing.state}\n"
        f"Contact: {order.listing.seller.name}\n\n"
        f"🔗 MONITOR TRANSMISSION: http://fliptrybe.com/success/{order.id}\n"
        f"Stand by for driver assignment."
    )
    send_whatsapp(order.buyer.phone, buyer_msg)
    
    # 💰 2. THE SELLER (Transmission confirming sale)
    seller_msg = (
        f"💰 ASSET LIQUIDATED: '{order.listing.title}'\n\n"
        f"Buyer: {order.buyer.name}\n"
        f"Contact: {order.buyer.phone}\n\n"
        f"PROTOCOL: Please prepare the asset for logistics pickup. "
        f"Your payout is held in escrow until delivery is verified."
    )
    # Using .seller instead of .agent to match updated models.py
    send_whatsapp(order.listing.seller.phone, seller_msg)

def notify_driver_assigned(order):
    """
    Logistics Deployment Signal:
    Triggered when a driver initializes the 'Deployment' button.
    """
    msg = (
        f"🚐 LOGISTICS UNIT DEPLOYED\n\n"
        f"Pilot: {order.driver.name} ({order.driver.phone})\n"
        f"Vehicle: {order.driver.vehicle_color} {order.driver.vehicle_type}\n"
        f"Plate: {order.driver.license_plate}\n\n"
        f"🔐 YOUR VERIFICATION PIN: {order.verification_pin}\n"
        f"⚠️ CRITICAL: Provide this PIN ONLY when the asset is in your hands. "
        f"The PIN releases your funds to the seller."
    )
    send_whatsapp(order.buyer.phone, msg)

def notify_driver_arrival(order):
    """
    Proximity Signal:
    Triggered when the driver hits 'Mark Arrived' on their terminal.
    """
    msg = (
        f"🔔 PROXIMITY ALERT: Pilot has arrived!\n\n"
        f"Unit: {order.driver.vehicle_color} {order.driver.vehicle_type}\n"
        f"Tag: {order.driver.license_plate}\n\n"
        f"ACTION: Please meet the pilot at the destination. "
        f"Have your 4-digit Verification PIN ready for the final handoff."
    )
    send_whatsapp(order.buyer.phone, msg)