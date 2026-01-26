from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# --- ENUMS ---
class UserRole(str, enum.Enum):
    USER = "USER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"

class ItemCategory(str, enum.Enum):
    DECLUTTER = "DECLUTTER"
    SHORTLET = "SHORTLET"

class OrderStatus(str, enum.Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CANCELLED_BY_SELLER = "CANCELLED_BY_SELLER"
    COMPLETED = "COMPLETED"

class WithdrawalStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"

# --- USERS ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # 📍 LOCATION & RANK
    state = Column(String, default="Lagos")
    city = Column(String, default="Ikeja")
    rating = Column(Float, default=3.0)
    
    # 💰 WALLET (The Agent's Bank)
    wallet_balance = Column(Float, default=0.0)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    
    items = relationship("Item", back_populates="lister")
    orders = relationship("Order", back_populates="buyer")
    withdrawals = relationship("Withdrawal", back_populates="agent")

# --- WITHDRAWALS (New) ---
class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"))
    
    amount_requested = Column(Float) # e.g. 100,000
    fee_platform = Column(Float)     # 5% = 5,000
    amount_net = Column(Float)       # Sent = 95,000
    
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    agent = relationship("User", back_populates="withdrawals")

# --- ITEMS ---
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ItemCategory), default=ItemCategory.DECLUTTER)
    title = Column(String, index=True)
    description = Text()
    price = Column(Float)
    
    # Location
    region = Column(String, index=True)
    city = Column(String, index=True)
    pickup_address = Column(String)
    
    # Client Data
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_pickup_time = Column(String, nullable=True)
    
    # Financials
    commission_agent = Column(Float, default=0.0) # This goes to Wallet
    commission_platform = Column(Float, default=0.0)
    payout_amount = Column(Float, default=0.0)
    
    is_sold = Column(Boolean, default=False)
    lister_id = Column(Integer, ForeignKey("users.id"))
    lister = relationship("User", back_populates="items")

# --- ORDERS ---
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    amount_paid = Column(Float)
    refund_account_details = Column(String)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_CONFIRMATION)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    buyer = relationship("User", back_populates="orders")
    item = relationship("Item")

# --- UTILS ---
class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
class SystemSetting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)