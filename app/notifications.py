import time

def send_receipt_email(email: str, name: str, amount: float, vehicle: str, ref: str):
    print("\n" + "="*50)
    print(f"📧 EMAIL TO: {email}")
    print(f"SUBJECT: Your FlipTrybe Receipt [{ref}]")
    print("-" * 50)
    print(f"Thank you, {name}!")
    print(f"Your {vehicle} is on the way.")
    print(f"Total: ₦{amount:,.2f}")
    print("="*50 + "\n")
    time.sleep(1)

def send_driver_sms(phone: str, pickup_loc: str):
    print("\n" + "*"*40)
    print(f"📱 SMS TO DRIVER: {phone}")
    print(f"ACTION: New Job at {pickup_loc}")
    print("*"*40 + "\n")