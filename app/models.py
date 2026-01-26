from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# --- ENUMS (Strict Choices) ---
class ItemStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    HIDDEN = "HIDDEN"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

# --- CORE USERS ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    address = Column(String, nullable=False) # Prerequisite for sellers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    items_for_sale = relationship("Item", back_populates="seller")
    orders = relationship("Order", back_populates="buyer")

# --- MARKETPLACE ITEMS ---
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, index=True)
    condition = Column(String)
    image_url = Column(String)
    
    # Pickup Logistics Data
    pickup_address = Column(String, nullable=False)
    pickup_days = Column(String) # e.g. "Mon-Fri 9am-5pm"
    pickup_contact_name = Column(String)
    pickup_contact_phone = Column(String)

    status = Column(Enum(ItemStatus), default=ItemStatus.AVAILABLE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    seller_id = Column(Integer, ForeignKey("users.id"))
    seller = relationship("User", back_populates="items_for_sale")

# --- TRANSACTIONS (The Order Ledger) ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    
    amount_paid = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Logistics Choice
    delivery_required = Column(Boolean, default=False)
    delivery_address = Column(String, nullable=True) # If different from user address
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("User", back_populates="orders")
    item = relationship("Item")

# --- LEGACY LOGISTICS (Keep for Toggle Feature) ---
class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    vehicle_type = Column(String)
    status = Column(String, default="AVAILABLE")

class SystemSetting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)