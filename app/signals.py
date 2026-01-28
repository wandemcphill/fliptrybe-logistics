import requests
from flask import current_app

def transmit_termii_signal(to_phone, message, channel="generic"):
    """
    Transmits an industrial-grade SMS/WhatsApp signal via Termii.
    Channels: 'generic' (SMS), 'dnd' (Premium SMS), 'whatsapp'
    """
    api_key = current_app.config.get('TERMII_API_KEY')
    sender_id = current_app.config.get('TERMII_SENDER_ID')
    
    # Standardize phone format for Nigerian Nodes (234...)
    if to_phone.startswith('0'):
        to_phone = '234' + to_phone[1:]
    elif not to_phone.startswith('234'):
        to_phone = '234' + to_phone

    payload = {
        "to": to_phone,
        "from": sender_id,
        "sms": message,
        "type": "plain",
        "channel": channel,
        "api_key": api_key
    }
    
    headers = {'Content-Type': 'application/json'}
    url = "https://api.ng.termii.com/api/sms/send"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        current_app.logger.error(f"Signal Transmission Failure: {str(e)}")
        return None