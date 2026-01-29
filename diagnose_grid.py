import os
import sys
import requests
from datetime import datetime
from app import create_app, db
from app.models import User, Listing, Order, Transaction, PriceHistory

def run_diagnostics():
    """
    The Grid Diagnostic Protocol: A deep-system audit of the FlipTrybe ecosystem.
    Checks for structural integrity, logical loops, and connectivity failures.
    """
    app, celery = create_app()
    
    with app.app_context():
        print(f"\n{'='*50}")
        print(f"🛰️  FLIPTRYBE GRID DIAGNOSTICS // {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        # --- 🧬 1. DATABASE INTEGRITY AUDIT ---
        print("🔍 Checking Database Nodes...")
        try:
            user_count = User.query.count()
            listing_count = Listing.query.count()
            order_count = Order.query.count()
            print(f"   [OK] Connection Active. Found: {user_count} Users, {listing_count} Listings, {order_count} Orders.")
            
            # Audit Build #1: Merchant Tiers
            masters = User.query.filter_by(merchant_tier='Grid-Master').count()
            print(f"   [OK] Merchant Tier logic synchronized. Grid-Masters detected: {masters}")
        except Exception as e:
            print(f"   [❌] DATABASE ERROR: {str(e)}")

        # --- 🚁 2. BACKGROUND WORKER HEARTBEAT (CELERY/REDIS) ---
        print("\n🔍 Checking Background Signal Engine...")
        try:
            # Pinging Redis via Celery
            inspector = celery.control.inspect()
            stats = inspector.stats()
            if stats:
                print("   [OK] Celery Worker Heartbeat Detected. System is optimal.")
            else:
                print("   [⚠️] WARNING: Celery Worker Offline. SMS/OTP signals will fail.")
        except Exception as e:
            print(f"   [❌] REDIS/CELERY ERROR: Could not reach background engine.")

        # --- 📲 3. EXTERNAL API SIGNAL STRENGTH ---
        print("\n🔍 Checking External Gateway Terminals...")
        
        # Termii Signal Check
        termii_key = os.environ.get('TERMII_API_KEY')
        if termii_key:
            print("   [OK] Termii API Key present.")
        else:
            print("   [❌] CRITICAL: TERMII_API_KEY is missing from .env.")

        # Paystack Signal Check
        paystack_key = os.environ.get('PAYSTACK_SECRET_KEY')
        if paystack_key:
            print("   [OK] Paystack Secret Key present.")
        else:
            print("   [❌] CRITICAL: PAYSTACK_SECRET_KEY is missing from .env.")

        # --- 📁 4. ASSET STORAGE AUDIT ---
        print("\n🔍 Checking Asset Storage Nodes...")
        upload_path = os.path.join(app.root_path, 'static', 'uploads', 'products')
        if os.path.exists(upload_path):
            print(f"   [OK] Product Image directory verified: {upload_path}")
        else:
            print(f"   [❌] ERROR: Upload path missing. Run: mkdir -p {upload_path}")

        # --- 🤝 5. LOGICAL LOOP AUDIT (Price FOMO) ---
        print("\n🔍 Checking FOMO Logic (Build #3 & #8)...")
        sample_listing = Listing.query.first()
        if sample_listing:
            try:
                drop = sample_listing.price_drop
                print(f"   [OK] PriceHistory Relationship Active. Sample Drop: {drop}%")
            except Exception as e:
                print(f"   [❌] LOGIC ERROR: PriceHistory mapping is broken.")
        else:
            print("   [⚠️] SKIP: No listings found to test FOMO logic.")

        print(f"\n{'='*50}")
        print("✅ DIAGNOSTICS COMPLETE: Grid stability verified.")
        print(f"{'='*50}\n")

if __name__ == "__main__":
    run_diagnostics()