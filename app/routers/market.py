from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db  # Ensure this is imported!
from app.models import Item, User, Order, ItemStatus, OrderStatus
from app.notifications import notify_parties_of_sale

router = APIRouter()

# --- INPUT SCHEMAS ---
class ItemCreate(BaseModel):
    title: str
    description: str
    price: float
    category: str
    pickup_address: str
    pickup_days: str
    pickup_contact_name: str
    pickup_contact_phone: str
    seller_id: int 

class PurchaseRequest(BaseModel):
    buyer_id: int
    item_id: int
    delivery_required: bool
    delivery_address: Optional[str] = None

# --- API ROUTES ---

# 👇 THIS WAS THE MISSING PART
@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    """Fetch all available items for the feed."""
    # We filter by status so sold items disappear from the feed
    return db.query(Item).filter(Item.status == ItemStatus.AVAILABLE).all()

@router.post("/list-item")
def list_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Seller lists an item."""
    new_item = Item(
        title=item.title,
        description=item.description,
        price=item.price,
        category=item.category,
        pickup_address=item.pickup_address,
        pickup_days=item.pickup_days,
        pickup_contact_name=item.pickup_contact_name,
        pickup_contact_phone=item.pickup_contact_phone,
        seller_id=item.seller_id,
        status=ItemStatus.AVAILABLE
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"status": "success", "item_id": new_item.id}

@router.post("/buy-item")
def buy_item(request: PurchaseRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Buyer purchases item."""
    
    # 1. Check Item
    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item or item.status != ItemStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Item is no longer available.")
    
    # 2. Get Buyer
    buyer = db.query(User).filter(User.id == request.buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
        
    # 3. Create Order
    new_order = Order(
        buyer_id=buyer.id,
        item_id=item.id,
        amount_paid=item.price,
        status=OrderStatus.PAID,
        delivery_required=request.delivery_required,
        delivery_address=request.delivery_address if request.delivery_required else buyer.address
    )
    
    # 4. Mark Item Sold
    item.status = ItemStatus.SOLD
    
    db.add(new_order)
    db.commit()
    
    # 5. Notify
    pickup_data = {
        "contact_name": item.pickup_contact_name,
        "contact_phone": item.pickup_contact_phone,
        "address": item.pickup_address,
        "days": item.pickup_days
    }
    
    background_tasks.add_task(
        notify_parties_of_sale,
        buyer_phone=buyer.phone,
        buyer_name=buyer.full_name,
        seller_phone=item.pickup_contact_phone,
        seller_name=item.pickup_contact_name,
        item_title=item.title,
        pickup_details=pickup_data
    )
    
    return {"status": "success", "message": "Payment confirmed."}