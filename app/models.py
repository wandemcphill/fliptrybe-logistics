from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
import datetime

# --- ENUMS ---
class UserRole(str, enum.Enum):
    USER = "USER"          # Normal Buyer/Seller
    AGENT = "AGENT"        # Third-party lister
    ADMIN = "ADMIN"

class ItemCategory(str, enum.Enum):
    DECLUTTER = "DECLUTTER"
    SHORTLET = "SHORTLET"

class OrderStatus(str, enum.Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION" # Buyer paid, waiting for Seller/Agent Yes/No
    CONFIRMED = "CONFIRMED"                       # Seller said YES (Show details)
    CANCELLED_BY_SELLER = "CANCELLED_BY_SELLER"   # Seller said NO (Refund)
    REFUNDED_TIMEOUT = "REFUNDED_TIMEOUT"         # 10 hours passed (Auto Refund)
    COMPLETED = "COMPLETED"                       # Pickup done

# --- USERS ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # Financials (For Agent Payouts)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("Item", back_populates="lister")
    orders = relationship("Order", back_populates="buyer")

# --- ITEMS (Declutter & Shortlet) ---
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ItemCategory), default=ItemCategory.DECLUTTER) # Declutter or Shortlet
    title = Column(String, index=True)
    description = Text()
    price = Column(Float)
    
    # Visuals
    image_urls = Column(Text) # Comma separated URLs
    video_url = Column(String, nullable=True)
    
    # --- THE AGENT PROTOCOL FIELDS ---
    # If listed by an Agent, these fields store the REAL owner's info
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_pickup_address = Column(String, nullable=True)
    client_pickup_time = Column(String, nullable=True)
    client_account_details = Column(String, nullable=True) # Text blob for now
    
    # Financials
    commission_agent = Column(Float, default=0.0) # 10%
    commission_platform = Column(Float, default=0.0) # 5%
    payout_amount = Column(Float, default=0.0) # 85%
    
    is_sold = Column(Boolean, default=False)
    lister_id = Column(Integer, ForeignKey("users.id")) # The Agent or Direct Seller
    lister = relationship("User", back_populates="items")

# --- TRANSACTIONS (The Trust Layer) ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    
    amount_paid = Column(Float)
    refund_account_details = Column(String, nullable=False) # Buyer provides this at purchase
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_CONFIRMATION)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Logic: To check if 5 hours have passed
    def hours_since_creation(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - self.created_at
        return diff.total_seconds() / 3600

    buyer = relationship("User", back_populates="orders")
    item = relationship("Item")
    
# --- LOGISTICS (Legacy) ---
class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
class SystemSetting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)