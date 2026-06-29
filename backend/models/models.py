# backend/models/models.py
from decimal import Decimal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, Boolean, DateTime, JSON, CheckConstraint, ForeignKey
from datetime import datetime, timedelta
import uuid

class Base(DeclarativeBase):
    """Defines the base class for SQLAlchemy models"""
    pass

class Product(Base):
    """Defines the Product models"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_quantity: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncQueue(Base):
    """Defines the SyncQueue model"""
    __tablename__ = "sync_queue"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(unique=True)  # FK
    device_id: Mapped[str] = mapped_column()  # FK
    entity_type: Mapped[str] = mapped_column(String(20))
    operation: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    retry_count: Mapped[int] = mapped_column(default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'synced', 'failed', 'conflict')", name="valid_status"),
        CheckConstraint("entity_type IN ('sale', 'product', 'user')", name="valid_entity_type"),
        CheckConstraint("operation IN ('CREATE', 'UPDATE', 'DELETE')", name="valid_operation"),
    )

class User(Base):
    """Defines the User model"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column()
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(20), default="employee")
    phone_or_email: Mapped[str] = mapped_column(String(50))
    account_name: Mapped[str | None] = mapped_column(String(50))
    bank_name: Mapped[str | None] = mapped_column(String(50))
    account_number: Mapped[str | None] = mapped_column(String(10))
    pin_hash: Mapped[str | None] = mapped_column(String(60))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'manager', 'employee')", name="valid_role"),
    )

class Device(Base):
    """Defines the Device model"""
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey(User.id))
    device_name: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class Sale(Base):
    """Defines the Sale model"""
    __tablename__ = "sales"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_number: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey(User.id))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    profit_at_sale: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[DateTime] = mapped_column(default=datetime.utcnow)
    editable_until: Mapped[DateTime] = mapped_column(default=lambda: datetime.utcnow + timedelta(minutes=20))
    
    __table_args__ = (
        CheckConstraint("payment_method IN ('cash', 'transfer', 'pos')", name="valid_payment_method"),
        CheckConstraint("status IN ('completed', 'edited', 'cancelled')", name="valid_status")
    )