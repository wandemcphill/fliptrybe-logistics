from app.database import SessionLocal
from app.models import SystemSetting

def toggle_payment_mode():
    db = SessionLocal()
    
    # Find the setting
    setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    
    if not setting:
        print("❌ Error: Run seed.py first!")
        return

    # Flip the switch
    if setting.value == "MANUAL":
        setting.value = "GATEWAY"
        print("🔄 Switched to: GATEWAY (Paystack Mode)")
    else:
        setting.value = "MANUAL"
        print("🔄 Switched to: MANUAL (Bank Transfer Mode)")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    toggle_payment_mode()