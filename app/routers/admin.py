from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Order, Item, UserRole, OrderStatus, Driver

router = APIRouter()

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    The Brain of the Admin Panel. 
    Calculates Real-Time Financials and Operations data.
    """
    
    # 1. FINANCIALS (The Money)
    # Sum of all CONFIRMED orders
    total_sales = db.query(func.sum(Order.amount_paid)).filter(Order.status == OrderStatus.CONFIRMED).scalar() or 0.0
    
    # Revenue Split
    platform_revenue = total_sales * 0.05  # Your 5%
    agent_payouts = total_sales * 0.10     # Their 10%
    client_payouts = total_sales * 0.85    # Owner's 85%
    
    # 2. OPERATIONAL HEALTH
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING_CONFIRMATION).count()
    active_listings = db.query(Item).filter(Item.is_sold == False).count()
    
    # 3. AGENT NETWORK
    total_agents = db.query(User).filter(User.role == UserRole.AGENT).count()
    
    # 4. RECENT ACTIVITY FEED (Last 5 Orders)
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    
    # Format the feed for the UI
    activity_feed = []
    for o in recent_orders:
        activity_feed.append({
            "id": o.id,
            "item": o.item.title,
            "amount": o.amount_paid,
            "status": o.status,
            "buyer": o.buyer.full_name,
            "date": o.created_at.strftime("%H:%M %d/%m")
        })

    return {
        "financials": {
            "gross_volume": total_sales,
            "net_revenue": platform_revenue,
            "agent_commissions": agent_payouts,
            "pending_payouts": client_payouts
        },
        "operations": {
            "pending_orders": pending_orders,
            "active_listings": active_listings,
            "total_agents": total_agents
        },
        "feed": activity_feed
    }

# --- LEGACY DRIVER MANAGEMENT (Kept as a utility) ---
@router.get("/drivers")
def get_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).all()

@router.get("/seed-market-users")
def seed_market_users(db: Session = Depends(get_db)):
    """Quick tool to create test accounts if database was wiped."""
    if not db.query(User).filter(User.email == "agent@fliptrybe.com").first():
        agent = User(full_name="Agent Chidi", phone="080AGENT001", role=UserRole.AGENT, email="agent@fliptrybe.com")
        buyer = User(full_name="Tunde Buyer", phone="080BUYER001", role=UserRole.USER, email="buyer@fliptry