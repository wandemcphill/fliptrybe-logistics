from app import create_app, db, bcrypt
from app.models import User, Listing
import os

app = create_app()

def run_genesis():
    with app.app_context():
        print("🧹 CLEARING GRID...")
        db.drop_all()
        db.create_all()

        print("🚀 INITIALIZING GENESIS NODES...")
        
        # Master Admin
        pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = User(name="Overseer", username="admin_hq", email="admin@fliptrybe.com", 
                     password_hash=pw, role="admin", is_admin=True, is_verified=True)
        db.session.add(admin)

        # Pilot Alpha
        p_pw = bcrypt.generate_password_hash("driver123").decode('utf-8')
        pilot = User(name="Musa Driver", username="pilot_alpha", email="driver@fliptrybe.com", 
                     password_hash=p_pw, role="driver", is_driver=True, is_verified=True,
                     state="Lagos", vehicle_type="Toyota Hiace", license_plate="LAG-504-FT")
        db.session.add(pilot)

        # Merchant
        m_pw = bcrypt.generate_password_hash("buyer123").decode('utf-8')
        buyer = User(name="Lekan Merchant", username="lekan_m", email="buyer@fliptrybe.com", 
                     password_hash=m_pw, role="user", wallet_balance=2500000.0)
        db.session.add(buyer)

        db.session.commit()

        # Asset Deployment
        item = Listing(title="MacBook Pro M3 Max", description="Silicon Valley Level Hardware.", 
                       price=1850000.0, section="declutter", category="Electronics", 
                       state="Lagos", city="Ikeja", user_id=buyer.id)
        db.session.add(item)
        
        db.session.commit()
        print("✅ GENESIS COMPLETE.")

if __name__ == '__main__':
    run_genesis()