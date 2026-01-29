import os
from app import create_app, db, bcrypt # 🟢 Use bcrypt from app
from app.models import User, Listing, Order, Transaction, Withdrawal, Dispute, Notification, PriceHistory, Favorite

app = create_app()

def rebuild():
    with app.app_context():
        print("🏗️  REBUILDING THE GRID...")
        
        # Reset DB
        db.drop_all()
        db.create_all()
        print("✅ Schema Injected.")

        # 🔐 Hash using Bcrypt to match auth.py
        hashed_password = bcrypt.generate_password_hash("password123").decode('utf-8')

        # Seed Admin
        admin = User(
            name="Chief Engineer",
            email="admin@fliptrybe.com",
            phone="08000000001",
            password_hash=hashed_password,
            is_admin=True,
            is_verified=True,
            wallet_balance=1000000.0
        )
        
        db.session.add(admin)
        db.session.commit()
        print("👤 Admin Node Initialized with Bcrypt hash.")
        print("\n🚀 GRID READY. Run 'python run.py'.")

if __name__ == "__main__":
    rebuild()