import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import (
    User, Listing, Order, Transaction, 
    PriceHistory, Notification, Withdrawal
)

def seed_grid():
    """
    The Pulse Generator: Seeds the grid with a complete 
    biosphere of Admins, Merchants, Pilots, and Assets.
    """
    app, _ = create_app()
    
    with app.app_context():
        print("🛰️  SIGNAL RECEIVED: Starting Deep Grid Population...")
        
        # --- 🛡️ CLEAN SWEEP (Safety Check) ---
        # This seed script assumes a fresh or migrated DB.
        # It does not drop tables, but wipes data to prevent PK conflicts.
        db.session.query(PriceHistory).delete()
        db.session.query(Transaction).delete()
        db.session.query(Order).delete()
        db.session.query(Listing).delete()
        db.session.query(Notification).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("🧹 GRID PURIFIED: Legacy nodes cleared.")

        # --- 👤 IDENTITY NODES (Build #1, #4, #7) ---
        password = generate_password_hash('flip1234')

        # 1. Admin Node (The Overseer)
        admin = User(
            name="FlipTrybe Admin",
            email="admin@fliptrybe.com",
            phone="2348000000001",
            password_hash=password,
            is_admin=True,
            is_verified=True
        )

        # 2. Merchant Node (The Alpha Seller)
        merchant = User(
            name="Genesis Merchant",
            email="merchant@fliptrybe.com",
            phone="2348000000002",
            password_hash=password,
            is_verified=True,
            merchant_tier="Grid-Master", # Build #1
            wallet_balance=150000.0
        )

        # 3. Pilot Node (The Logistics Asset)
        pilot = User(
            name="Skyline Pilot",
            email="pilot@fliptrybe.com",
            phone="2348000000003",
            password_hash=password,
            is_driver=True,
            is_verified=True,
            pilot_rating_sum=45, # 4.5 average (Build #4)
            pilot_rating_count=10
        )

        db.session.add_all([admin, merchant, pilot])
        db.session.flush() # Secure IDs for foreign key mapping
        print("👥 IDENTITY NODES: Admin, Merchant, and Pilot online.")

        # --- 📦 ASSET NODES (Build #3 & #8) ---
        
        # Asset 1: The "Deal of the Day" Candidate
        listing_1 = Listing(
            title="MacBook Pro M3 Max",
            description="Ultra-high performance node. 64GB RAM. Space Black.",
            price=1800000.0,
            category="electronics",
            state="Lagos",
            user_id=merchant.id,
            status="Available"
        )

        # Asset 2: Standard Inventory
        listing_2 = Listing(
            title="Vintage Leather Jacket",
            description="Classic edge-case fashion. Grade A hide.",
            price=45000.0,
            category="fashion",
            state="Abuja",
            user_id=merchant.id,
            status="Available"
        )

        db.session.add_all([listing_1, listing_2])
        db.session.flush()

        # --- 📈 PRICE HISTORY NODES (FOMO Trigger) ---
        # We seed a price drop for Listing 1 to trigger the Marquee instantly
        ph1 = PriceHistory(price=2200000.0, listing_id=listing_1.id, timestamp=datetime.utcnow() - timedelta(days=1))
        ph2 = PriceHistory(price=1800000.0, listing_id=listing_1.id, timestamp=datetime.utcnow())
        
        db.session.add_all([ph1, ph2])
        print("📈 FOMO SIGNALS: Price drop history synchronized.")

        # --- 🤝 TRANSACTIONAL NODES (Handshake Pulse) ---
        
        # Creating a completed order to establish Merchant reputation
        order = Order(
            handshake_id="HS-GENESIS",
            total_price=50000.0,
            status="Completed",
            buyer_id=admin.id, # Admin bought for testing
            listing_id=listing_1.id,
            driver_id=pilot.id
        )
        db.session.add(order)
        db.session.flush()

        # Corresponding Transaction Ledger
        tx = Transaction(
            amount=50000.0,
            type="Credit",
            reference="RELEASE-HS-GENESIS",
            user_id=merchant.id
        )
        db.session.add(tx)

        # --- 🏁 FINAL COMMIT ---
        db.session.commit()
        print("✅ GRID SEEDED: 10 Build-Bundles are now active and synchronized.")
        print(f"👉 Access: merchant@fliptrybe.com / flip1234")

if __name__ == "__main__":
    seed_grid()