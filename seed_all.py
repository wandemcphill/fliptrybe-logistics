from app import create_app, db, bcrypt
from app.models import (
    User, Listing, Order, Transaction, Dispute, 
    Withdrawal, Notification, PriceHistory, Favorite
)
from datetime import datetime, timedelta
import random

# Initialize the App Context
app = create_app()

def seed_database():
    with app.app_context():
        print("🛑 Wiping Grid Data...")
        db.drop_all()
        print("🏗️  Rebuilding Database Architecture...")
        db.create_all()

        print("👥 Seeding Identity Nodes (Users)...")
        # 1. THE OVERSEER (Admin)
        admin = User(
            name="FlipTrybe HQ",
            email="admin@fliptrybe.com",
            phone="2348000000000",
            password_hash=bcrypt.generate_password_hash("trybe_hq_2026").decode('utf-8'),
            is_admin=True,
            is_verified=True,
            wallet_balance=1000000.00
        )

        # 2. THE MERCHANT (Seller)
        merchant = User(
            name="Emeka Ventures",
            email="merchant@test.com",
            phone="2348011111111",
            password_hash=bcrypt.generate_password_hash("password").decode('utf-8'),
            is_verified=True,
            wallet_balance=45000.00
        )

        # 3. THE PILOT (Logistics)
        pilot = User(
            name="Musa Logistics",
            email="pilot@test.com",
            phone="2348022222222",
            password_hash=bcrypt.generate_password_hash("password").decode('utf-8'),
            is_driver=True,
            is_verified=True,
            wallet_balance=5000.00
        )

        # 4. THE BUYER (Consumer)
        buyer = User(
            name="Tola Customer",
            email="buyer@test.com",
            phone="2348033333333",
            password_hash=bcrypt.generate_password_hash("password").decode('utf-8'),
            is_verified=True,
            wallet_balance=250000.00
        )

        db.session.add_all([admin, merchant, pilot, buyer])
        db.session.commit()

        print("📦 Seeding Asset Manifest (Listings)...")
        # Merchant Assets
        l1 = Listing(
            title="iPhone 15 Pro Max",
            description="UK Used, 256GB, Battery Health 95%. Clean condition.",
            price=850000.00,
            category="Electronics",
            section="market",
            state="Lagos",
            image_filename="default.jpg",
            seller=merchant,
            status="Available"
        )

        l2 = Listing(
            title="Lekki 2-Bed Shortlet",
            description="Luxury apartment with 24/7 power and swimming pool.",
            price=150000.00,
            category="Real Estate",
            section="shortlet",
            state="Lagos",
            image_filename="default.jpg",
            seller=merchant,
            status="Available"
        )

        l3 = Listing(
            title="Toyota Camry 2018",
            description="Direct Belgium. Low mileage. Buy and drive.",
            price=4500000.00,
            category="Vehicles",
            section="market",
            state="Abuja",
            image_filename="default.jpg",
            seller=merchant,
            status="Available"
        )
        
        l4 = Listing(
            title="Vintage Denim Jacket",
            description="Size XL. Barely used. Decluttering my wardrobe.",
            price=15000.00,
            category="Fashion",
            section="declutter",
            state="Rivers",
            image_filename="default.jpg",
            seller=buyer, # Buyer listing an item (Declutter mode)
            status="Available"
        )

        db.session.add_all([l1, l2, l3, l4])
        db.session.commit()
        
        # Add Price History
        for item in [l1, l2, l3, l4]:
            ph = PriceHistory(listing_id=item.id, price=item.price)
            db.session.add(ph)
        db.session.commit()

        print("🤝 Seeding Handshake Protocols (Orders)...")
        # 1. An Active Escrow Order (Buyer buys iPhone)
        # We assume Buyer bought a PREVIOUS iPhone that is now 'Sold'
        sold_item = Listing(
            title="MacBook Pro M1",
            description="Sold item example.",
            price=600000.00,
            category="Electronics",
            section="market",
            state="Lagos",
            image_filename="default.jpg",
            seller=merchant,
            status="Sold"
        )
        db.session.add(sold_item)
        db.session.commit()

        order1 = Order(
            total_price=sold_item.price,
            status="Escrowed",
            delivery_status="In Transit",
            buyer=buyer,
            listing=sold_item,
            driver=pilot # Assigned to Musa
        )
        
        # 2. A Completed Order (History)
        completed_item = Listing(
            title="PS5 Console",
            description="Sold item example.",
            price=450000.00,
            category="Electronics",
            section="market",
            state="Lagos",
            image_filename="default.jpg",
            seller=merchant,
            status="Sold"
        )
        db.session.add(completed_item)
        db.session.commit()

        order2 = Order(
            total_price=completed_item.price,
            status="Released",
            delivery_status="Completed",
            buyer=buyer,
            listing=completed_item,
            driver=pilot
        )

        db.session.add_all([order1, order2])
        db.session.commit()

        print("💸 Seeding Financial Audit Trail...")
        # Transaction History for Buyer
        t1 = Transaction(amount=500000.00, type="Credit", reference="TOP-INIT-001", user=buyer)
        t2 = Transaction(amount=600000.00, type="Debit", reference="PURCHASE-HS-001", user=buyer)
        
        # Withdrawal Request for Merchant
        w1 = Withdrawal(
            amount=50000.00,
            bank_name="GTBank",
            account_number="0123456789",
            account_name="Emeka Ventures",
            status="Pending",
            user=merchant
        )
        
        db.session.add_all([t1, t2, w1])
        db.session.commit()

        print("🔔 Seeding Notification Signals...")
        n1 = Notification(
            user_id=buyer.id,
            title="Welcome to Grid 2026",
            message="Your node identity has been verified. Welcome to the future of commerce.",
            category="success"
        )
        n2 = Notification(
            user_id=merchant.id,
            title="Inventory Alert",
            message="Your 'MacBook Pro M1' has been secured in Escrow. Pilot Assigned.",
            category="info"
        )
        n3 = Notification(
            user_id=pilot.id,
            title="Mission Assigned",
            message="New logistics mission: Pickup at Ikeja. Deliver to Lekki.",
            category="warning"
        )
        
        db.session.add_all([n1, n2, n3])
        db.session.commit()

        print("✅ GRID INITIALIZATION COMPLETE.")
        print("------------------------------------------------")
        print(f"🔑 Admin Login:    admin@fliptrybe.com / trybe_hq_2026")
        print(f"🔑 Merchant Login: merchant@test.com / password")
        print(f"🔑 Pilot Login:    pilot@test.com    / password")
        print(f"🔑 Buyer Login:    buyer@test.com    / password")
        print("------------------------------------------------")

if __name__ == '__main__':
    seed_database()