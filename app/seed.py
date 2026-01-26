from app.database import SessionLocal, engine
from app.models import Base, SystemSetting

# Create tables just in case
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    
    # Check if we already have a setting
    existing_setting = db.query(SystemSetting).filter(SystemSetting.key == "payment_mode").first()
    
    if not existing_setting:
        print("🌱 Seeding Database: Setting Payment Mode to MANUAL...")
        new_setting = SystemSetting(
            key="payment_mode", 
            value="MANUAL", 
            description="Controls if we use Bank Transfer (MANUAL) or Paystack (GATEWAY)"
        )
        db.add(new_setting)
        db.commit()
        print("✅ Success! Database is ready.")
    else:
        print(f"ℹ️ Database already set to: {existing_setting.value}")
    
    db.close()

if __name__ == "__main__":
    seed_data()