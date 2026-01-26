from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Item, Order, Withdrawal, ItemCategory, OrderStatus, UserRole
from app.notifications import send_whatsapp

router = APIRouter()

class WithdrawalRequest(BaseModel):
    agent_id: int
    amount: float
    bank_name: str
    account_number: str

@router.get("/dashboard/{agent_id}")
def get_agent_dashboard(agent_id: int, db: Session = Depends(get_db)):
    """
    The Agent's Brain: Analytics, Wallet, and Listings.
    """
    agent = db.query(User).filter(User.id == agent_id, User.role == UserRole.AGENT).first()
    if not agent: raise HTTPException(status_code=404, detail="Agent not found")
    
    # 1. ANALYTICS
    total_listings = db.query(Item).filter(Item.lister_id == agent_id).count()
    sold_items = db.query(Item).filter(Item.lister_id == agent_id, Item.is_sold == True).count()
    total_earnings = db.query(func.sum(Item.commission_agent)).filter(Item.lister_id == agent_id, Item.is_sold == True).scalar() or 0.0
    
    # 2. SEPARATE LISTINGS (Declutter vs Shortlet)
    declutter_listings = db.query(Item).filter(Item.lister_id == agent_id, Item.type == ItemCategory.DECLUTTER).all()
    shortlet_listings = db.query(Item).filter(Item.lister_id == agent_id, Item.type == ItemCategory.SHORTLET).all()
    
    # 3. WALLET
    current_balance = agent.wallet_balance
    
    return {
        "stats": {
            "balance": current_balance,
            "total_earnings": total_earnings,
            "items_sold": sold_items,
            "active_listings": total_listings - sold_items
        },
        "listings": {
            "declutter": declutter_listings,
            "shortlet": shortlet_listings
        }
    }

@router.post("/withdraw")
def request_withdrawal(req: WithdrawalRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Process Withdrawal: Deduct 5% Fee.
    """
    agent = db.query(User).filter(User.id == req.agent_id).first()
    
    if req.amount > agent.wallet_balance:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # CALCULATION
    fee = req.amount * 0.05
    net_amount = req.amount - fee
    
    # DEDUCT BALANCE NOW (Optimistic)
    agent.wallet_balance -= req.amount
    
    # RECORD TRANSACTION
    txn = Withdrawal(
        agent_id=agent.id,
        amount_requested=req.amount,
        fee_platform=fee,
        amount_net=net_amount,
        status="PENDING" # Admin must approve actual transfer
    )
    db.add(txn)
    db.commit()
    
    # NOTIFY ADMIN (Simulated)
    msg = f"💸 Withdrawal Alert: {agent.full_name} wants ₦{net_amount:,.2f} (Fee: ₦{fee:,.2f})."
    bg_tasks.add_task(send_whatsapp, "080ADMIN", msg)
    
    return {"status": "success", "msg": f"Withdrawal queued. You will receive ₦{net_amount:,.2f}"}