from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles  # 🆕 IMPORT THIS
from contextlib import asynccontextmanager
import os

from app.database import engine, Base, SessionLocal
from app.models import Driver, SystemSetting, User, UserRole
from app.routers import payment, driver, admin, market, agent_office

# --- 1. SYSTEM STARTUP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Flip Trybe Server Starting Up...")
    
    # ⚠️ DATABASE RESET (Only for Development)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # SEED DATA
    db = SessionLocal()
    try:
        # 1. Create Default Logistics Drivers
        team = [
            {"name": "Musa (Bike)", "phone": "08011111111", "vehicle": "Bike"},
            {"name": "Chinedu (Van)", "phone": "08022222222", "vehicle": "Van"},
        ]
        for member in team:
            db.add(Driver(name=member["name"], phone=member["phone"], vehicle_type=member["vehicle"], status="AVAILABLE"))

        # 2. Create Agent Chidi
        agent = User(
            full_name="Agent Chidi", 
            phone="080AGENT001", 
            role=UserRole.AGENT, 
            email="agent@fliptrybe.com",
            state="Lagos",
            city="Ikorodu",
            rating=5.0,
            wallet_balance=0.0
        )
        db.add(agent)
        
        # 3. Create User Tunde
        buyer = User(
            full_name="Tunde Buyer", 
            phone="080BUYER001", 
            role=UserRole.USER, 
            email="tunde@fliptrybe.com",
            state="Lagos",
            city="Ikeja",
            rating=3.0
        )
        db.add(buyer)
        
        db.add(SystemSetting(key="payment_mode", value="MANUAL"))
        db.commit()
        print("✅ Database Reset & Seeded")
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
app.include_router(agent_office.router, prefix="/api/agent", tags=["Agent Office"])

# --- 4. SERVE STATIC FILES (VIDEO) ---
# This line makes the 'app/static' folder accessible at '/static'
if not os.path.exists("app/static"):
    os.makedirs("app/static")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- 5. FRONTEND PAGES ---
def serve_file(filename: str):
    path = os.path.join(os.getcwd(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": f"File '{filename}' not found inside {os.getcwd()}"}

@app.get("/")
def home(): return serve_file("index.html")

@app.get("/market")
def market_page(): return serve_file("market.html")

@app.get("/agent-office")
def agent_page(): return serve_file("agent.html")

@app.get("/admin-panel")
def admin_page(): return serve_file("admin.html")

@app.get("/driver-app")
def driver_page(): return serve_file("driver.html")

@app.get("/success")
def success_page(): return serve_file("success.html")