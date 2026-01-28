from app import create_app, db
from app.models import User, Listing, Order
from datetime import datetime
import os

app = create_app()

def run_genesis():
    with app.app_context():
        print("🧹 SCRUBBING GRID (PURGING OLD DATA)...")
        db.drop_all()
        db.create_all()

        print("👤 CREATING MASTER IDENTITIES...")
        
        # 1. HQ COMMAND (Admin)
        admin = User(
            name="FlipTrybe HQ", 
            username="overseer", 
            email="admin@fliptrybe.com", 
            role="admin", 
            is_admin=True, 
            is_verified=True
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # 2. PILOT ALPHA (Logistics Expert)
        pilot = User(
            name="Musa Logistics", 
            username="pilot_musa", 
            email="driver@fliptrybe.com", 
            role="driver", 
            is_driver=True, 
            is_verified=True,
            state="Lagos", 
            city="Ikeja",
            vehicle_type="Toyota Hiace Van", 
            license_plate="FT-LOG-01L"
        )
        pilot.set_password("driver123")
        db.session.add(pilot)

        # 3. MERCHANT NODE (Liquidity/Buyer)
        buyer = User(
            name="Lekan Merchant", 
            username="lekan_m", 
            email="buyer@fliptrybe.com", 
            role="user", 
            wallet_balance=2500000.0, 
            is_verified=True,
            state="Lagos",
            city="Lekki"
        )
        buyer.set_password("buyer123")
        db.session.add(buyer)

        db.session.commit() # Lock in identities to get IDs
        print(f"✅ Master Identities Locked: Admin, Pilot, Merchant")

        print("📦 STOCKING THE MARKET...")
        
        # Assets belonging to the Merchant
        assets = [
            Listing(
                title="MacBook Pro M3 Max (16-inch)", 
                description="64GB RAM, 2TB SSD. Silicon Valley Grade. Pristine condition.", 
                price=1850000.0, section="declutter", category="Electronics", 
                condition="Brand New", state="Lagos", city="Ikeja", user_id=buyer.id
            ),
            Listing(
                title="Lekki Phase 1 Luxury Shortlet", 
                description="2-Bedroom fully serviced apartment. 24/7 Power & Security.", 
                price=120000.0, section="shortlet", category="Real Estate", 
                condition="Refurbished", state="Lagos", city="Lekki", user_id=buyer.id
            ),
            Listing(
                title="Rolex Submariner (Date)", 
                description="2024 Card. Box and Papers included. Investment grade.", 
                price=14500000.0, section="declutter", category="Watches", 
                condition="Brand New", state="Lagos", city="Victoria Island", user_id=buyer.id
            )
        ]
        
        for asset in assets:
            db.session.add(asset)
        
        db.session.commit()
        print(f"🚀 GENESIS COMPLETE. 3 Nodes & {len(assets)} Market Assets Live.")

if __name__ == '__main__':
    run_genesis()