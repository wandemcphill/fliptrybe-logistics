from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests
import uuid

from app.database import get_db
from app.models import SystemSetting, Driver

router = APIRouter()

# 🔐 YOUR PAYSTACK SECRET KEY
# In production, this would be loaded from an environment variable (.env)
PAYSTACK_SECRET_KEY = "sk_test_34d39847e8d590a6967487d95f60f421409e0b08"

# 1. THE DATA CONTRACT
class OrderRequest(BaseModel):
    buyer_email: str
    vehicle_type: str  # "Bike" or "Van"
    distance_km: float

@router.post("/initiate")
def initiate_payment(order: OrderRequest, db: Session = Depends(get_db)):
    print(f"🚀 NEW ORDER RECEIVED: {order.vehicle_type} for {order.distance_km}km")

    # 2. SERVER-SIDE PRICING
    RATES = {"Bike": 100, "Van": 500}
    
    if order.vehicle_type not in RATES:
        raise HTTPException(status_code=400, detail=f"Invalid vehicle. Available: {list(RATES.keys())}")
        
    amount_ngn = int(order.distance_km * RATES[order.vehicle_type])
    amount_kobo = amount_ngn * 100 

    # 3. CHECK DRIVER AVAILABILITY
    driver = db.query(Driver).filter(
        Driver.vehicle_type == order.vehicle_type,
        Driver.status == "AVAILABLE"
    ).first()

    if not driver:
        print("❌ ORDER REJECTED: No drivers available.")
        return {"success": False, "message": "No drivers available right now."}

    # 4. CHECK SYSTEM MODE
    mode_setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    mode = mode_setting.value if mode_setting else "MANUAL"

    # ==========================================
    # 🅰️ MANUAL MODE (Cash)
    # ==========================================
    if mode == "MANUAL":
        print(f"✅ MANUAL MODE: Skipping Gateway. Collect ₦{amount_ngn:,.2f}")
        
        # Dispatch Logic
        print(f"🎯 MATCHED DRIVER: {driver.name}")
        
        # 🧾 PRINT RECEIPT
        print("\n" + "="*50)
        print(f"📧 EMAIL RECEIPT TO: {order.buyer_email}")
        print("SUBJECT: Your FlipTrybe Receipt")
        print("-" * 50)
        print(f"Vehicle: {order.vehicle_type}")
        print(f"Distance: {order.distance_km}km")
        print(f"Driver: {driver.name} ({driver.phone})")
        print(f"TOTAL DUE: ₦{amount_ngn:,.2f}")
        print("=" * 50 + "\n")
        
        # Lock driver
        driver.status = "BUSY"
        db.commit()
        
        # ✅ THE FIX: Redirect to local success page, not Google
        return {"success": True, "payment_mode": "/success", "message": "Driver dispatched"}

    # ==========================================
    # 🅱️ GATEWAY MODE (Paystack)
    # ==========================================
    else:
        print(f"💳 GATEWAY MODE: Initializing Paystack for ₦{amount_ngn}...")
        
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": order.buyer_email,
            "amount": amount_kobo,
            "reference": str(uuid.uuid4()),
            "callback_url": "https://fliptrybe-app.onrender.com/success", # Redirects here after paying
            "metadata": {
                "vehicle_type": order.vehicle_type,
                "driver_id": driver.id
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            res_data = response.json()
            
            if res_data["status"]:
                auth_url = res_data["data"]["authorization_url"]
                print(f"🔗 PAYSTACK URL: {auth_url}")
                return {"success": True, "payment_mode": auth_url}
            else:
                print(f"❌ PAYSTACK ERROR: {res_data['message']}")
                raise HTTPException(status_code=400, detail="Payment initialization failed")
                
        except Exception as e:
            print(f"❌ NETWORK ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not connect to payment gateway")