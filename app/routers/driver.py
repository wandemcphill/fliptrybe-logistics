from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Driver

router = APIRouter()

# 1. LOGIN (Fixes "Login Failed")
@router.post("/login")
def driver_login(phone: str, db: Session = Depends(get_db)):
    # Remove any spaces from phone number just in case
    clean_phone = phone.strip()
    
    driver = db.query(Driver).filter(Driver.phone == clean_phone).first()
    
    if not driver:
        # If not found, print to terminal so you can see why
        print(f"❌ Login Failed for: {clean_phone}")
        raise HTTPException(status_code=401, detail="Driver not found")
    
    print(f"✅ Driver Logged In: {driver.name}")
    return {
        "success": True,
        "driver_id": driver.id,
        "name": driver.name,
        "vehicle_type": driver.vehicle_type
    }

# 2. STATUS CHECK (For the Driver App "Online/Offline" circle)
@router.get("/status/{driver_id}")
def get_driver_status(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"status": driver.status}

# 3. UPDATE STATUS (For "Complete Job" Button)
@router.post("/{driver_id}/status")
def update_driver_status(driver_id: int, status: str, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if driver:
        driver.status = status
        db.commit()
    return {"success": True}