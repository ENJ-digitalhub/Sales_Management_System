# backend/models/models.py
from decimal import Decimal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, Boolean, DateTime, JSON, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    """Defines the base class for SQLAlchemy models"""
    pass

class Product(Base):
    """Defines the Product models"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_quantity: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.now , onupdate=datetime.now)
    pass

<<<<<<< HEAD
=======

>>>>>>> a42e0680ca5389a118a3e26d2010d39f54282c44
class SyncQueue(Base):
    """Defines the SyncQueue model"""
    __tablename__ = "sync_queue"

    id: Mapped[str] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"), unique=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"))
    entity_type: Mapped[str] = mapped_column(String(20))
    operation: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    retry_count: Mapped[int] = mapped_column(default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    pass

