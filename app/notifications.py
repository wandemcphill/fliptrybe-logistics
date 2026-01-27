import logging
import os

# Setup logging to see messages in your Terminal/Console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_whatsapp(phone: str, message: str):
    """
    SIMULATION MODE: Prints to console. 
    LIVE MODE: Replace with Twilio/Termii API call.
    """
    logger.info(f"\n🟢 [WHATSAPP to {phone}]:\n{message}\n" + "-"*30)

def sync_sale_notifications(order):
    """
    Synchronizes Buyer, Agent (Seller), and Driver immediately after purchase.
    """
    # 🛒 1. THE BUYER (Gets Agent's Pickup Info)
    buyer_msg = (
        f"✅ Payment Confirmed for '{order.listing.title}'.\n\n"
        f"📦 PICKUP/DELIVERY DETAILS:\n"
        f"Agent: {order.listing.agent.name}\n"
        f"Phone: {order.listing.agent.phone}\n"
        f"Location: {order.listing.city}, {order.listing.state}\n\n"
        f"🔗 TRACK LIVE: http://fliptrybe.com/success/{order.id}\n"
        f"A driver will be assigned shortly."
    )
    send_whatsapp(order.buyer.phone, buyer_msg)
    
    # 💰 2. THE AGENT/SELLER (Gets Buyer's Info)
    agent_msg = (
        f"💰 Item Sold! '{order.listing.title}' has been purchased.\n\n"
        f"👤 BUYER DETAILS:\n"
        f"Name: {order.buyer.name}\n"
        f"Phone: {order.buyer.phone}\n\n"
        f"Please prepare the item for pickup."
    )
    send_whatsapp(order.listing.agent.phone, agent_msg)

def notify_driver_assigned(order):
    """Triggered when Musa clicks 'Accept'"""
    msg = (
        f"🚐 Driver Assigned!\n\n"
        f"Driver: {order.driver.name} ({order.driver.phone})\n"
        f"Vehicle: {order.driver.vehicle_color} {order.driver.vehicle_type}\n"
        f"Plate: {order.driver.license_plate}\n\n"
        f"🔐 YOUR SECURE PIN: {order.verification_pin}\n"
        f"IMPORTANT: Give this PIN to the driver ONLY when you have received your item."
    )
    send_whatsapp(order.buyer.phone, msg)

def notify_driver_arrival(order):
    """Triggered when Musa clicks 'I Have Arrived'"""
    msg = (
        f"🔔 Musa has arrived at your location!\n"
        f"🚗 Look for: {order.driver.vehicle_color} {order.driver.vehicle_type}\n"
        f"🔢 Plate: {order.driver.license_plate}\n\n"
        f"Please meet him and provide your 4-digit PIN to complete the delivery."
    )
    send_whatsapp(order.buyer.phone, msg)