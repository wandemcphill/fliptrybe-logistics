import os
from app import create_app, db
from app.models import User, Listing, Order, Transaction, Notification, PriceHistory
from werkzeug.security import generate_password_hash

def rebuild_grid():
    """
    The Genesis Protocol: Wipes the current database and re-initializes 
    all tables to match the synchronized 10-Build architecture.
    """
    app, _ = create_app()
    
    with app.app_context():
        print("🛰️  SIGNAL RECEIVED: Initializing Grid Rebuild...")
        
        # --- 🛡️ STEP 1: DESTRUCTIVE SYNC ---
        # Wipes all tables. Use only in development or for total system reset.
        db.drop_all()
        print("🗑️  VAULT CLEARED: All existing tables dropped.")
        
        # --- 🧬 STEP 2: STRUCTURAL INITIALIZATION ---
        db.create_all()
        print("🏗️  INFRASTRUCTURE SYNC: Tables re-created from master models.")
        
        # --- 👤 STEP 3: SEED ADMIN NODE (Build #7) ---
        admin_pass = "admin123" # CHANGE THIS IN PRODUCTION
        admin_node = User(
            name="Grid Overseer",
            email="admin@fliptrybe.com",
            phone="2348000000001",
            password_hash=generate_password_hash(admin_pass),
            is_admin=True,
            is_verified=True,
            wallet_balance=0.0
        )
        db.session.add(admin_node)
        print(f"🛡️  ADMIN NODE DEPLOYED: Login: admin@fliptrybe.com | Pass: {admin_pass}")

        # --- 📦 STEP 4: SEED MERCHANT NODE (Build #1) ---
        merchant_pass = "merchant123"
        merchant_node = User(
            name="Genesis Merchant",
            email="merchant@fliptrybe.com",
            phone="2348000000002",
            password_hash=generate_password_hash(merchant_pass),
            is_verified=True,
            merchant_tier="Novice",
            wallet_balance=50000.0 # Seeded with starting liquidity
        )
        db.session.add(merchant_node)
        db.session.flush() # Secure the ID for listing creation

        # --- 📈 STEP 5: SEED INITIAL ASSET (Build #3) ---
        genesis_listing = Listing(
            title="Industrial Power Grid Node",
            description="High-frequency liquidity asset for genesis testing.",
            price=25000.0,
            category="electronics",
            state="Lagos",
            status="Available",
            user_id=merchant_node.id
        )
        db.session.add(genesis_listing)
        db.session.flush()

        # --- 📝 STEP 6: SEED PRICE HISTORY (Build #3 FOMO) ---
        # Creating a fake history to trigger a 20% price drop signal instantly
        old_price = PriceHistory(price=31250.0, listing_id=genesis_listing.id)
        new_price = PriceHistory(price=25000.0, listing_id=genesis_listing.id)
        db.session.add_all([old_price, new_price])

        # --- 🏁 STEP 7: COMMIT & LOCK ---
        db.session.commit()
        print("✅ GRID REBUILT: Handshake protocols active. Price FOMO signals primed.")

if __name__ == "__main__":
    rebuild_grid()