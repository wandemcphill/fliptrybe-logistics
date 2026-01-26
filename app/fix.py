from app.database import SessionLocal, engine, Base
from app.models import SystemSetting, Driver

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("🔧 Starting System Repair...")

# 1. Fix Payment Mode
setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
if not setting:
    print("⚙️  Missing Setting Found: defaulting to GATEWAY mode.")
    new_setting = SystemSetting(key="payment_mode", value="GATEWAY")
    db.add(new_setting)
else:
    print(f"✅ Payment Mode is safe: {setting.value}")

# 2. Fix Drivers (Ensure we have at least one driver)
if db.query(Driver).count() == 0:
    print("🚕 No drivers found. Hiring Musa and team...")
    driver1 = Driver(name="Musa Ahmed", phone="08011111111", vehicle_type="Bike", status="AVAILABLE")
    driver2 = Driver(name="Chinedu Okeke", phone="08022222222", vehicle_type="Van", status="AVAILABLE")
    db.add_all([driver1, driver2])
else:
    print("✅ Drivers are already hired.")

db.commit()
db.close()
print("🚀 System Repaired & Ready!")