from app.database import SessionLocal, engine, Base
from app.models import Driver

# Create the new tables if they don't exist yet
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if we already have drivers
if db.query(Driver).count() == 0:
    print("Hire Drivers...")
    driver1 = Driver(name="Musa Ahmed", phone="08011111111", vehicle_type="Bike", status="AVAILABLE")
    driver2 = Driver(name="Chinedu Okeke", phone="08022222222", vehicle_type="Van", status="AVAILABLE")
    driver3 = Driver(name="Seyi Johnson", phone="08033333333", vehicle_type="Bike", status="AVAILABLE")
    
    db.add_all([driver1, driver2, driver3])
    db.commit()
    print("✅ Successfully hired Musa, Chinedu, and Seyi!")
else:
    print("Drivers already exist.")

db.close()