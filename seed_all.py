from app import create_app, db, bcrypt
from app.models import User, Listing
import os

app = create_app()

with app.app_context():
    print("\n🧹 TERMINATING EXISTING SIGNALS (Dropping Tables)...")
    db.drop_all()
    
    print("🏗️  RECONSTRUCTING TRIBE ARCHITECTURE (Creating Tables)...")
    db.create_all()
    
    print("🚀 INITIALIZING GENESIS USERS...")

    # 1. 👑 THE OVERSEER (Admin)
    admin_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
    admin = User(
        name="Opeyemi Admin",
        username="admin_op",
        email="admin@fliptrybe.com", 
        password=admin_pw, 
        role="admin",
        is_admin=True,
        image_file="default.jpg"
    )
    db.session.add(admin)

    # 2. 🏠 THE PROPERTY MOGUL (Agent)
    agent_pw = bcrypt.generate_password_hash("agent123").decode('utf-8')
    agent = User(
        name="Agent Chidi",
        username="chidi_realty",
        email="agent@fliptrybe.com", 
        password=agent_pw, 
        phone="+2348011223344", 
        role="agent", 
        is_agent=True, 
        state="Lagos",
        city="Lekki",
        wallet_balance=5000.0,
        image_file="default.jpg"
    )
    db.session.add(agent)

    # 3. 🚐 THE LOGISTICS PILOT (Driver)
    driver_pw = bcrypt.generate_password_hash("driver123").decode('utf-8')
    driver = User(
        name="Musa Driver",
        username="musa_wheels",
        email="driver@fliptrybe.com",
        password=driver_pw,
        phone="+2349055667788",
        role="driver",
        is_driver=True,
        state="Lagos",
        city="Ikeja",
        # Logistics Specs
        vehicle_type="Toyota Hiace",
        vehicle_year="2018",
        vehicle_color="Silver",
        license_plate="LAG-504-KD",
        rating=4.9,
        image_file="default.jpg"
    )
    db.session.add(driver)

    # 4. 🛒 THE ALPHA BUYER
    buyer_pw = bcrypt.generate_password_hash("buyer123").decode('utf-8')
    buyer = User(
        name="Lekan Buyer", 
        username="lekan_b",
        email="buyer@fliptrybe.com", 
        password=buyer_pw, 
        phone="+2347011122233", 
        role="user",
        state="Lagos",
        city="Victoria Island",
        wallet_balance=2500000.0, # ₦2.5M for the MacBook!
        image_file="default.jpg"
    )
    db.session.add(buyer)

    db.session.commit()
    print("✅ IDENTITY NODES SYNCED.")

    # 5. 🛰️ DEPLOYING INITIAL ASSETS
    print("📡 DEPLOYING MARKET SIGNALS...")
    
    # Asset 1: Premium Real Estate
    shortlet = Listing(
        title="Luxury Lekki Ocean-View Shortlet", 
        description="High-fidelity 2-bedroom apartment. Includes 24/7 Power, Starlink Internet, and Private Security. Perfect for digital nomads.", 
        price=85000.0, 
        section="shortlet",
        category="Real Estate", 
        specifications="2-Bedroom / Ocean View",
        condition="New",
        state="Lagos", 
        city="Lekki Phase 1", 
        seller_id=agent.id,
        status="Available"
    )
    db.session.add(shortlet)

    # Asset 2: High-Value Declutter
    laptop = Listing(
        title="MacBook Pro M3 Max (2024)", 
        description="Unopened box. 32GB RAM, 1TB SSD. Liquid Retina XDR display. Selling due to corporate upgrade.", 
        price=1850000.0, 
        section="declutter",
        category="Electronics", 
        brand="Apple",
        specifications="14-inch / M3 Max",
        condition="New",
        state="Lagos", 
        city="Ikeja", 
        seller_id=buyer.id, # The buyer is acting as a seller here
        status="Available"
    )
    db.session.add(laptop)

    db.session.commit()
    print("✅ ASSETS DEPLOYED TO GRID.")

    print("\n🔥 GENESIS COMPLETE.")
    print("👉 Terminal Access: admin@fliptrybe.com / admin123")
    print("👉 Driver Unit: driver@fliptrybe.com / driver123")
    print("👉 Market Entry: buyer@fliptrybe.com / buyer123")
    print("\nRun 'python run.py' to initialize the terminal.")