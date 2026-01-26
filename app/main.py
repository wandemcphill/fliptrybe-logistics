from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.database import engine, Base, SessionLocal
from app.models import Driver, SystemSetting, User, UserRole
# ⚠️ IMPORT ALL ROUTERS
from app.routers import payment, driver, admin, market

# --- 1. SYSTEM STARTUP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Flip Trybe Server Starting Up...")
    
    # ⚠️ DATABASE RESET (Crucial for the new Agent features)
    # This deletes old tables and builds new ones with the "Agent" columns
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # SEED DATA (So you don't start empty)
    db = SessionLocal()
    try:
        # 1. Create Default Logistics Drivers
        team = [
            {"name": "Musa (Bike)", "phone": "08011111111", "vehicle": "Bike"},
            {"name": "Chinedu (Van)", "phone": "08022222222", "vehicle": "Van"},
        ]
        for member in team:
            db.add(Driver(name=member["name"], phone=member["phone"], vehicle_type=member["vehicle"], status="AVAILABLE"))

        # 2. Create an Agent (Chidi)
        agent = User(
            full_name="Agent Chidi", 
            phone="080AGENT001", 
            role=UserRole.AGENT,
            email="agent@fliptrybe.com"
        )
        db.add(agent)
        
        # 3. Create a Buyer (Tunde)
        buyer = User(
            full_name="Tunde Buyer", 
            phone="080BUYER001", 
            role=UserRole.USER,
            email="buyer@fliptrybe.com"
        )
        db.add(buyer)
        
        # 4. Create Default Payment Setting
        db.add(SystemSetting(key="payment_mode", value="MANUAL"))
        
        db.commit()
        print("✅ Database Reset & Seeded with Agents/Users")
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

# --- 3. CONNECT ROUTERS ---
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(driver.router, prefix="/api/driver", tags=["Driver"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(market.router, prefix="/api/market", tags=["Marketplace"])

# --- 4. FRONTEND PAGES ---
def serve_file(filename: str):
    path = os.path.join(os.getcwd(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": f"File '{filename}' not found"}

@app.get("/")
def home(): return serve_file("index.html")

@app.get("/market")
def market_page(): return serve_file("market.html")

@app.get("/admin-panel")
def admin_page(): return serve_file("admin.html")

@app.get("/driver-app")
def driver_page(): return serve_file("driver.html")

@app.get("/success")
def success_page(): return serve_file("success.html")