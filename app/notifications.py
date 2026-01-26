import logging

# Setup logging to see messages in Render Dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_whatsapp(phone: str, message: str):
    """
    Simulates sending a WhatsApp message.
    In V2, we will replace this print statement with the Twilio/InfoBip API.
    """
    logger.info(f"🟢 [WHATSAPP to {phone}]: {message}")

def notify_parties_of_sale(buyer_phone, buyer_name, seller_phone, seller_name, item_title, pickup_details):
    """
    The 'Double-Blind' Logic:
    1. Buyer gets Seller's Pickup Info.
    2. Seller gets Buyer's Contact Info.
    """
    
    # 1. Message to BUYER (A) - Giving them B's Pickup Info
    buyer_msg = (
        f"✅ Payment Confirmed for '{item_title}'.\n\n"
        f"📦 PICKUP DETAILS:\n"
        f"Contact: {pickup_details['contact_name']}\n"
        f"Phone: {pickup_details['contact_phone']}\n"
        f"Address: {pickup_details['address']}\n"
        f"Time: {pickup_details['days']}\n\n"
        f"Please contact the seller to arrange pickup/delivery."
    )
    send_whatsapp(buyer_phone, buyer_msg)
    
    # 2. Message to SELLER (B) - Giving them A's Contact Info
    seller_msg = (
        f"💰 Item Sold! '{item_title}' has been purchased.\n\n"
        f"👤 BUYER DETAILS:\n"
        f"Name: {buyer_name}\n"
        f"Phone: {buyer_phone}\n\n"
        f"The buyer has received your pickup address."
    )
    send_whatsapp(seller_phone, seller_msg)