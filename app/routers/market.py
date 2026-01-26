from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Item, User, Order, ItemCategory, OrderStatus, UserRole
from app.notifications import send_whatsapp

router = APIRouter()

# --- INPUT SCHEMAS ---
class UnifiedListing(BaseModel):
    title: str
    description: str
    price: float
    type: ItemCategory
    lister_id: int
    # Location (Optional for User, Required for Agent)
    state: Optional[str] = None 
    city: Optional[str] = None
    # Client Data (For Agents)
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_pickup_address: Optional[str] = None

class PurchaseRequest(BaseModel):
    buyer_id: int
    item_id: int
    refund_account: str

# --- ROUTES ---

@router.get("/feed")
def get_smart_feed(
    user_state: str = "Lagos", 
    user_city: str = "Ikeja", 
    view_mode: str = "LOCAL", # LOCAL or NATIONWIDE
    db: Session = Depends(get_db)
):
    """
    THE SMART ALGORITHM:
    1. Filter by 'Sold' status.
    2. If LOCAL mode: Filter strictly by State.
    3. Sort by: Exact City Match (Ikorodu first) -> Agent Rating (High rank) -> Price (Low).
    """
    query = db.query(Item).join(User).filter(Item.is_sold == False)
    
    if view_mode == "LOCAL":
        query = query.filter(Item.region == user_state)
    
    # Fetch all items to sort in Python (easier for MVP complex sorting)
    items = query.all()
    
    # 🧠 SORTING LOGIC
    # +1000 points if City matches User City.
    # +100 points * Agent Rating (5.0 rating = +500 points).
    # -Price/1000 (Cheaper items score higher).
    
    def calculate_score(item):
        score = 0
        if item.city and item.city.lower() == user_city.lower():
            score += 1000
        if item.lister.rating:
            score += (item.lister.rating * 100) # Boost High Ranked Agents
        
        # Price penalty (Higher price = Lower score)
        score -= (item.price / 10000) 
        return score

    # Sort DESC (Highest score first)
    sorted_items = sorted(items, key=calculate_score, reverse=True)
    
    return sorted_items

@router.post("/list-item")
def unified_list_item(data: UnifiedListing, db: Session = Depends(get_db)):
    """
    ONE BUTTON LISTING:
    Checks if user is Agent or Regular and applies rules automatically.
    """
    user = db.query(User).filter(User.id == data.lister_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    # DEFAULTS
    final_region = user.state
    final_city = user.city
    final_address = f"Registered Address in {user.city}"
    
    # AGENT OVERRIDES
    if user.role == UserRole.AGENT:
        if not data.state or not data.city:
            # For MVP simplicity, if they forgot, default to their profile
            final_region = data.state or user.state
            final_city = data.city or user.city
            
        final_region = data.state or user.state
        final_city = data.city or user.city
        final_address = data.client_pickup_address or "Agent Office"
        
        # COMMISSION CALC (10% Agent, 5% Platform, 85% Client)
        comm_agent = data.price * 0.10
        comm_platform = data.price * 0.05
        payout = data.price * 0.85
    else:
        # USER CALC (0% Agent, 5% Platform, 95% User)
        comm_agent = 0.0
        comm_platform = data.price * 0.05
        payout = data.price * 0.95

    new_item = Item(
        type=data.type,
        title=data.title,
        description=data.description,
        price=data.price,
        region=final_region,
        city=final_city,
        pickup_address=final_address,
        
        # Financials
        commission_agent=comm_agent,
        commission_platform=comm_platform,
        payout_amount=payout,
        
        # Agent Details (Only if Agent)
        client_name=data.client_name if user.role == UserRole.AGENT else user.full_name,
        client_phone=data.client_phone if user.role == UserRole.AGENT else user.phone,
        client_pickup_time="9am - 5pm", 
        
        lister_id=data.lister_id
    )
    db.add(new_item)
    db.commit()
    return {"status": "success", "msg": f"Listed in {final_city}, {final_region}"}

@router.post("/buy-item")
def request_purchase(req: PurchaseRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Step 1: Buyer Pays -> Money Held -> Verification Link Sent to Agent/Seller
    """
    item = db.query(Item).filter(Item.id == req.item_id).first()
    if not item or item.is_sold:
        raise HTTPException(status_code=400, detail="Item unavailable")

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
    
    # Send Magic Link to Lister
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
        
        # 💰 CREDIT AGENT WALLET
        if lister.role == UserRole.AGENT:
            lister.wallet_balance += item.commission_agent

        # Notify Buyer
        buyer_msg = (
            f"✅ Order Confirmed! '{item.title}' is yours.\n"
            f"Pickup Address: {item.pickup_address}\n"
            f"Contact Name: {item.client_name}\n"
            f"Phone: {item.client_phone}"
        )
        bg_tasks.add_task(send_whatsapp, buyer.phone, buyer_msg)
        
    elif action == "cancel":
        # --- SCENARIO B: SOLD ELSEWHERE (NO) ---
        order.status = OrderStatus.CANCELLED_BY_SELLER
        buyer_msg = f"❌ Update on '{item.title}': The seller sold this locally. Refund processing to: {order.refund_account_details}."
        bg_tasks.add_task(send_whatsapp, buyer.phone, buyer_msg)
        
    db.commit()
    return {"status": "success", "action": action}