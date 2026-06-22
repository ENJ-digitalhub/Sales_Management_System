# backend/models/models.py
from decimal import Decimal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, Boolean, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_quantity: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.now , onupdate=datetime.now)
    pass