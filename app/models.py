from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class PaymentMethodEnum(str, enum.Enum):
    MANUAL = "MANUAL"
    GATEWAY = "GATEWAY"

class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    flip_ref = Column(String, unique=True, index=True)
    amount = Column(Float)
    payment_method = Column(Enum(PaymentMethodEnum))
    status = Column(String, default="PENDING")
    product_type = Column(String, default="Bike") # 👈 NEW: Remembers "Bike" or "Van"

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    vehicle_type = Column(String) 
    status = Column(String, default="AVAILABLE") 

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True, index=True)
    transaction_ref = Column(String, ForeignKey("transactions.flip_ref"))
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    pickup_address = Column(String, default="Lagos")
    delivery_status = Column(String, default="ASSIGNED") 
    driver = relationship("Driver")