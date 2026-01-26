from app.database import SessionLocal, engine, Base
from app.models import User

# Create Tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if users exist
if not db.query(User).first():
    print("🌱 Seeding Market Users...")
    
    # User 1: The Seller (B)
    seller = User(
        full_name="Bisi Seller",
        phone="08099999999",
        email="bisi@example.com",
        address="123 Ikeja Way, Lagos"
    )
    
    # User 2: The Buyer (A)
    buyer = User(
        full_name="Ayo Buyer",
        phone="08055555555",
        email="ayo@example.com",
        address="456 VI Close, Lagos"
    )
    
    db.add(seller)
    db.add(buyer)
    db.commit()
    print("✅ Seed Complete: Created Bisi (Seller) and Ayo (Buyer)")
else:
    print("info: Users already exist.")

db.close()