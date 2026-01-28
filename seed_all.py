from app import create_app, db
from app.models import User, Listing
import os

app = create_app()

def run_genesis():
    with app.app_context():
        print("🧹 PURGING OLD GRID DATA...")
        db.drop_all()
        db.create_all()

        print("🚀 DEPLOYING GENESIS NODES...")
        
        # 1. Admin Node
        admin = User(name="Overseer", username="admin_hq", email="admin@fliptrybe.com", 
                     role="admin", is_admin=True, is_verified=True)
        admin.set_password("admin123")
        db.session.add(admin)

        # 2. Pilot Alpha
        pilot = User(name="Musa Pilot", username="pilot_alpha", email="driver@fliptrybe.com", 
                     role="driver", is_driver=True, is_verified=True,
                     state="Lagos", vehicle_type="Van", license_plate="LAG-504-FT")
        pilot.set_password("driver123")
        db.session.add(pilot)

        # 3. Merchant Node
        buyer = User(name="Lekan Merchant", username="lekan_m", email="buyer@fliptrybe.com", 
                     role="user", wallet_balance=2500000.0)
        buyer.set_password("buyer123")
        db.session.add(buyer)

        db.session.commit()

        # 4. Market Assets
        item1 = Listing(title="MacBook Pro M3 Max", description="Silicon Valley Spec.", 
                       price=1850000.0, section="declutter", category="Electronics", 
                       state="Lagos", city="Ikeja", user_id=buyer.id)
        
        item2 = Listing(title="Lekki Phase 1 Shortlet", description="Luxury 2-Bed Serviced.", 
                       price=120000.0, section="shortlet", category="Real Estate", 
                       state="Lagos", city="Lekki", user_id=buyer.id)
        
        db.session.add(item1)
        db.session.add(item2)
        
        db.session.commit()
        print("✅ GENESIS COMPLETE. Tribe is operational.")

if __name__ == '__main__':
    run_genesis()