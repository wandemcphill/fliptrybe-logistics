from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.database import engine, Base, SessionLocal
from app.models import Driver, SystemSetting
# ⚠️ IMPORT ALL ROUTERS HERE
from app.routers import payment, driver, admin, market

# --- 1. SYSTEM STARTUP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 FlipTrybe Server Starting Up...")
    Base.metadata.create_all(bind=engine)
    
    # HIRE DRIVERS (Legacy Logic)
    db = SessionLocal()
    try:
        team = [
            {"name": "Musa (Bike)", "phone": "08011111111", "vehicle": "Bike"},
            {"name": "Chinedu (Van)", "phone": "08022222222", "vehicle": "Van"},
            {"name": "Seyi (Bike)", "phone": "08033333333", "vehicle": "Bike"}
        ]
        
        for member in team:
            exists = db.query(Driver).filter(Driver.name == member["name"]).first()
            if not exists:
                print(f"✨ Hiring {member['name']}...")
                db.add(Driver(
                    name=member["name"], 
                    phone=member["phone"], 
                    vehicle_type=member["vehicle"], 
                    status="AVAILABLE"
                ))
        
        # SET DEFAULT PAYMENT MODE
        if not db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first():
            db.add(SystemSetting(key="payment_mode", value="MANUAL"))
            
        db.commit()
    except Exception as e:
        print(f"❌ Startup Error: {e}")
    finally:
        db.close()
        
    yield 
    print("🛑 Server Shutting Down...")

app = FastAPI(lifespan=lifespan)

# --- 2. SECURITY ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. CONNECT THE ROUTERS (The Missing Link) ---
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(driver.router, prefix="/api/driver", tags=["Driver"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
# 👇 THIS LINE WAS LIKELY MISSING
app.include_router(market.router, prefix="/api/market", tags=["Marketplace"])

# --- 4. FRONTEND PAGE SERVING ---
def serve_file(filename: str):
    path = os.path.join(os.getcwd(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": f"File '{filename}' not found"}

@app.get("/")
def home(): return serve_file("index.html")

@app.get("/admin-panel")
def admin_page(): return serve_file("admin.html")

@app.get("/driver-app")
def driver_page(): return serve_file("driver.html")

@app.get("/success")
def success_page(): return serve_file("success.html")