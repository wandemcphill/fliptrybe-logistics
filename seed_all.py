from app import create_app, db
from app.models import User, Listing
import os

app = create_app()

def run_genesis():
    with app.app_context():
        print("🧹 SCRUBBING GRID...")
        db.drop_all()
        db.create_all()

        print("👤 CREATING IDENTITIES...")
        # Merchant Node
        buyer = User(
            name="Lekan Merchant", 
            username="lekan_m", 
            email="buyer@fliptrybe.com", 
            role="user", 
            wallet_balance=2500000.0,
            is_verified=True
        )
        buyer.set_password("buyer123")
        db.session.add(buyer)
        
        # Ensure the user is saved so we can use their ID for listings
        db.session.commit()
        print(f"✅ Created User: {buyer.email}")

        print("📦 STOCKING MARKETPLACE...")
        item1 = Listing(
            title="MacBook Pro M3 Max", 
            description="Silicon Valley Spec 14-inch.", 
            price=1850000.0, 
            section="declutter", 
            category="Electronics", 
            state="Lagos", 
            city="Ikeja", 
            user_id=buyer.id
        )
        
        item2 = Listing(
            title="Lekki Phase 1 Shortlet", 
            description="Luxury 2-Bed Serviced Apartment.", 
            price=120000.0, 
            section="shortlet", 
            category="Real Estate", 
            state="Lagos", 
            city="Lekki", 
            user_id=buyer.id
        )
        
        db.session.add(item1)
        db.session.add(item2)
        
        db.session.commit()
        print("🚀 GENESIS COMPLETE. 2 Items & 1 User Live.")

if __name__ == '__main__':
    run_genesis()