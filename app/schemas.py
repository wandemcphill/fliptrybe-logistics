from pydantic import BaseModel
from typing import Optional

class PaymentInitiate(BaseModel):
    item_id: int
    buyer_id: int
    distance_km: float
    buyer_email: Optional[str] = None
    vehicle_type: str = "Bike"  # 👈 This is the new field

class PaymentResponse(BaseModel):
    success: bool
    flip_ref: str
    payment_mode: str
    amount: float