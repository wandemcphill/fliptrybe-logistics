import requests
from flask import current_app

def send_whatsapp_signal(phone, message):
    """Transmits a logistics update via Termii WhatsApp."""
    url = "https://api.ng.termii.com/api/whatsapp/messages/send"
    payload = {
        "to": phone,
        "from": current_app.config.get('TERMII_SENDER_ID', 'FlipTrybe'),
        "type": "whatsapp",
        "channel": "whatsapp",
        "api_key": current_app.config.get('TERMII_API_KEY'),
        "message": message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Termii Error: {e}")
        return None

def resolve_bank_account(account_number, bank_code):
    """Verifies a Nigerian bank account via Paystack before payout."""
    url = f"https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}"
    headers = {"Authorization": f"Bearer {current_app.config.get('PAYSTACK_SECRET_KEY')}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json()
    except:
        return None