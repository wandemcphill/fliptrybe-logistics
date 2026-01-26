from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Item, User, Order, ItemCategory, OrderStatus, UserRole
from app.notifications import send_whatsapp

router = APIRouter()

# --- INPUT SCHEMAS ---
class AgentListing(BaseModel):
    title: str
    description: str
    price: float
    type: ItemCategory # DECLUTTER or SHORTLET
    lister_id: int
    # Client Info (Required for Agents)
    client_name: str
    client_phone: str
    client_pickup_address: str
    client_pickup_time: str
    client_account_details: str

class PurchaseRequest(BaseModel):
    buyer_id: int
    item_id: int
    refund_account: str # Buyer MUST provide this

# --- ROUTES ---

@router.post("/agent-list-item")
def agent_list_item(data: AgentListing, db: Session = Depends(get_db)):
    """
    Agents list items here. 
    System automatically calculates the 15% commission split.
    """
    # 1. Calculate Split
    platform_cut = data.price * 0.05
    agent_cut = data.price * 0.10
    owner_payout = data.price * 0.85
    
    new_item = Item(
        type=data.type,
        title=data.title,
        description=data.description,
        price=data.price,
        
        # Financials
        commission_platform=platform_cut,
        commission_agent=agent_cut,
        payout_amount=owner_payout,
        
        # The Secret Client Data (Hidden from public)
        client_name=data.client_name,
        client_phone=data.client_phone,
        client_pickup_address=data.client_pickup_address,
        client_pickup_time=data.client_pickup_time,
        client_account_details=data.client_account_details,
        
        lister_id=data.lister_id,
        is_sold=False
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"status": "success", "item_id": new_item.id, "msg": "Item Listed. 85% Payout calculated."}

@router.post("/buy-item")
def request_purchase(req: PurchaseRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Step 1: Buyer Pays -> Money Held -> Verification Link Sent to Agent/Seller
    """
    item = db.query(Item).filter(Item.id == req.item_id).first()
    if not item or item.is_sold:
        raise HTTPException(status_code=400, detail="Item unavailable")

    # Create 'Pending' Order
    order = Order(
        buyer_id=req.buyer_id,
        item_id=item.id,
        amount_paid=item.price,
        refund_account_details=req.refund_account,
        status=OrderStatus.PENDING_CONFIRMATION
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # --- TRIGGER VERIFICATION MESSAGE ---
    # We send a "Magic Link" to the Agent/Lister
    lister = db.query(User).filter(User.id == item.lister_id).first()
    
    verify_link_yes = f"https://fliptrybe-app.onrender.com/api/market/verify/{order.id}/confirm"
    verify_link_no = f"https://fliptrybe-app.onrender.com/api/market/verify/{order.id}/cancel"
    
    msg = (
        f"🚨 Flip Trybe Alert: Someone paid for '{item.title}'.\n"
        f"Is it still available?\n\n"
        f"YES (Accept Sale): {verify_link_yes}\n\n"
        f"NO (Refund Buyer): {verify_link_no}\n\n"
        f"⚠️ You have 10 hours to reply before auto-refund."
    )
    
    bg_tasks.add_task(send_whatsapp, lister.phone, msg)
    
    return {"status": "pending", "message": "Payment received. Waiting for Seller confirmation."}

@router.get("/verify/{order_id}/{action}")
def verify_availability(order_id: int, action: str, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Step 2: The Agent/Seller clicks the link.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != OrderStatus.PENDING_CONFIRMATION:
        return {"msg": "Link expired or already processed."}
    
    item = order.item
    buyer = order.buyer
    lister = item.lister
    
    if action == "confirm":
        # --- SCENARIO A: AVAILABLE (YES) ---
        order.status = OrderStatus.CONFIRMED
        item.is_sold = True
        
        # 1. Send Pickup Details to Buyer
        buyer_msg = (
            f"✅ Order Confirmed! '{item.title}' is yours.\n"
            f"Pickup Address: {item.client_pickup_address}\n"
            f"Contact Name: {item.client_name}\n"
            f"Phone: {item.client_phone}\n"
            f"Time: {item.client_pickup_time}"
        )
        bg_tasks.add_task(send_whatsapp, buyer.phone, buyer_msg)
        
        # 2. Send Buyer Details to Client (Seller)
        client_msg = (
            f"💰 Flip Trybe Sale: Your item '{item.title}' sold!\n"
            f"Buyer: {buyer.full_name} ({buyer.phone})\n"
            f"Please allow pickup. Payout processes after pickup."
        )
        bg_tasks.add_task(send_whatsapp, item.client_phone, client_msg)
        
        # 3. Notify Agent
        agent_msg = f"👍 Good job. Your client's item '{item.title}' was sold. Commission pending."
        bg_tasks.add_task(send_whatsapp, lister.phone, agent_msg)
        
    elif action == "cancel":
        # --- SCENARIO B: SOLD ELSEWHERE (NO) ---
        order.status = OrderStatus.CANCELLED_BY_SELLER
        # Refund Logic Here (Mocked)
        buyer_msg = (
            f"❌ Update on '{item.title}': The seller just sold this item locally.\n"
            f"We are processing a full refund to your account: {order.refund_account_details}."
        )
        bg_tasks.add_task(send_whatsapp, buyer.phone, buyer_msg)
        
    db.commit()
    return {"status": "success", "action": action}

@router.post("/buyer-refund/{order_id}")
def buyer_trigger_refund(order_id: int, db: Session = Depends(get_db)):
    """
    Step 3: The 5-Hour Rule. Buyer can cancel if Seller is ghosting.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    # Check Logic
    hours_passed = order.hours_since_creation() # Need to implement this in model or here
    
    if hours_passed < 5:
        raise HTTPException(status_code=400, detail=f"Please wait. Refund button available in {5 - int(hours_passed)} hours.")
        
    if order.status == OrderStatus.PENDING_CONFIRMATION:
        order.status = OrderStatus.CANCELLED_BY_SELLER
        db.commit()
        return {"msg": "Refund processed. Sorry for the delay."}
        
    return {"msg": "Cannot refund at this stage."}