from app import create_app
from app.models import db, User, Listing
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("🧹 Cleaning out the old Tribe (Dropping Tables)...")
    db.drop_all()
    
    print("🏗️ Building the new Tribe Schema with Logistics columns...")
    db.create_all()
    
    print("🚀 Populating the Tribe...")
    
    # 1. ADMIN
    admin = User(name="Opeyemi Admin", email="admin@fliptrybe.com", password=generate_password_hash("admin123"), is_admin=True)
    db.session.add(admin)

    # 2. AGENT
    agent = User(name="Agent Chidi", email="agent@fliptrybe.com", password=generate_password_hash("agent123"), phone="+2348011223344", is_agent=True, wallet_balance=5000.0)
    db.session.add(agent)

    # 3. PREMIUM DRIVER (With full vehicle info)
    driver = User(
        name="Musa Driver",
        email="driver@fliptrybe.com",
        password=generate_password_hash("driver123"),
        phone="+2349055667788",
        vehicle_type="Toyota Hiace",
        vehicle_year="2018",
        vehicle_color="Silver",
        license_plate="LAG-504-KD",
        rating=4.9,
        is_driver=True
    )
    db.session.add(driver)

    # 4. TEST BUYER
    buyer = User(name="Lekan Buyer", email="buyer@fliptrybe.com", password=generate_password_hash("buyer123"), phone="+2347011122233", wallet_balance=200000.0)
    db.session.add(buyer)

    db.session.commit()

    # 5. TEST LISTING
    agent_user = User.query.filter_by(is_agent=True).first()
    if agent_user:
        listing = Listing(title="Luxury Lekki Shortlet", description="Premium apartment with ocean view.", price=75000.0, category="Shortlet", state="Lagos", city="Lekki", agent_id=agent_user.id)
        db.session.add(listing)
        db.session.commit()

    print("\n🔥 THE TRIBE IS READY. Run 'python run.py' now!")