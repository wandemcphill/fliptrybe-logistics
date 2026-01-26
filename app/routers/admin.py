from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Driver, SystemSetting, User

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 🚛 LOGISTICS CONTROL (Drivers & Modes)
# ==========================================

@router.get("/status")
def get_admin_status(db: Session = Depends(get_db)):
    """Returns the current Payment Mode and List of Drivers."""
    # 1. Get Payment Mode
    mode_setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    current_mode = mode_setting.value if mode_setting else "MANUAL"

    # 2. Get Drivers
    drivers = db.query(Driver).all()
    
    return {"mode": current_mode, "drivers": drivers}

@router.post("/toggle-mode")
def toggle_payment_mode(db: Session = Depends(get_db)):
    """Switches between MANUAL (Cash) and GATEWAY (Paystack)."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    
    if not setting:
        setting = SystemSetting(key="payment_mode", value="MANUAL")
        db.add(setting)
    
    # Flip the switch
    if setting.value == "MANUAL":
        setting.value = "GATEWAY"
    else:
        setting.value = "MANUAL"
        
    db.commit()
    return {"status": "success", "new_mode": setting.value}

@router.post("/reset-drivers")
def reset_all_drivers(db: Session = Depends(get_db)):
    """Emergency Button: Sets all drivers to AVAILABLE."""
    drivers = db.query(Driver).all()
    for d in drivers:
        d.status = "AVAILABLE"
    db.commit()
    return {"status": "success", "message": "All drivers reset to AVAILABLE"}


# ==========================================
# 🛍️ MARKETPLACE TOOLS (Seeding & Tests)
# ==========================================

@router.get("/seed-market-users")
def seed_market_users(db: Session = Depends(get_db)):
    """
    Creates test users for the Marketplace (Bisi & Ayo).
    Run this once after deployment to populate the database.
    """
    # Check if Bisi already exists
    if not db.query(User).filter(User.email == "bisi@example.com").first():
        # Create Seller (B)
        seller = User(
            full_name="Bisi Seller",
            phone="08099999999",
            email="bisi@example.com",
            address="123 Allen Avenue, Ikeja"
        )
        # Create Buyer (A)
        buyer = User(
            full_name="Ayo Buyer",
            phone="08055555555",
            email="ayo@example.com",
            address="456 Victoria Island, Lagos"
        )
        
        db.add(seller)
        db.add(buyer)
        db.commit()
        return {"status": "Success", "message": "Created Bisi (Seller) and Ayo (Buyer)"}
    
    return {"status": "Info", "message": "Users already exist."}