from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Driver, SystemSetting

router = APIRouter()

# 1. GET STATUS (Fixes "Loading..." & Empty Table)
@router.get("/status")
def get_admin_status(db: Session = Depends(get_db)):
    # Get Payment Mode
    mode_setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    mode = mode_setting.value if mode_setting else "MANUAL"
    
    # Get All Drivers
    drivers = db.query(Driver).all()
    
    return {"mode": mode, "drivers": drivers}

# 2. TOGGLE MODE (Fixes Payment Logic Switch)
@router.post("/toggle-mode")
def toggle_mode(db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    if not setting:
        setting = SystemSetting(key="payment_mode", value="MANUAL")
        db.add(setting)
    
    # Flip the switch
    new_mode = "GATEWAY" if setting.value == "MANUAL" else "MANUAL"
    setting.value = new_mode
    db.commit()
    return {"status": "success", "mode": new_mode}

# 3. RESET DRIVERS (Fixes the "Force Reset" Button)
@router.post("/reset-drivers")
def reset_all_drivers(db: Session = Depends(get_db)):
    drivers = db.query(Driver).all()
    for driver in drivers:
        driver.status = "AVAILABLE"
    db.commit()
    return {"success": True}