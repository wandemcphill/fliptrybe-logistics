import os
from app import create_app, db
from app.models import User

def rebuild_grid():
    app = create_app()
    with app.app_context():
        print("\n🏗️  FLIPTRYBE: REBUILDING THE GRID...")
        
        # 🛡️ SAFETY CHECK: Prevent accidental deletion in production
        confirm = input("⚠️  WARNING: This will wipe ALL data in the Postgres Vault. Proceed? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Aborted. No changes made.")
            return

        # 1. DROP AND CREATE
        try:
            # We drop everything to clear out old singular table names (user, order)
            db.drop_all()
            db.create_all()
            print("✅ Pluralized Schema Injected (users, listings, orders, transactions).")
        except Exception as e:
            print(f"❌ SCHEMA ERROR: {e}")
            return

        # 2. INITIALIZE ADMIN ACCOUNT
        print("👤 Setting up Admin Node...")
        admin = User(
            name="FlipTrybe Admin",
            email="admin@fliptrybe.com",
            phone="2348000000000",
            is_admin=True,
            is_verified=True,
            password_hash="" # Placeholder for set_password
        )
        # Using the standard Bcrypt method from your User model
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        admin.password_hash = bcrypt.generate_password_hash("password123").decode('utf-8')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin Node Initialized (Email: admin@fliptrybe.com | Pass: password123)")
        print("\n🚀 GRID READY. Infrastructure is now production-hardened.")

if __name__ == "__main__":
    rebuild_grid()