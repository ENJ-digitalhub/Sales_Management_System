# backend/models/models.py
from decimal import Decimal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, Boolean, JSON, CheckConstraint, ForeignKey, Integer
from datetime import datetime, timedelta, timezone
import uuid

# wherever you call it
datetime.now(timezone.utc)

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncQueue(Base):
    """Defines the SyncQueue model"""
    __tablename__ = "sync_queue"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(unique=True)
    device_id: Mapped[str] = mapped_column()
    entity_type: Mapped[str] = mapped_column(String(20))
    operation: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    retry_count: Mapped[int] = mapped_column(default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'synced', 'failed', 'conflict')", name="valid_status"),
        CheckConstraint("entity_type IN ('sale', 'product', 'user', 'purchase')", name="valid_entity_type"),
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

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
    last_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    editable_until: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow() + timedelta(minutes=20))

    __table_args__ = (
        CheckConstraint("payment_method IN ('cash', 'transfer', 'pos')", name="valid_payment_method"),
        CheckConstraint("status IN ('completed', 'edited', 'cancelled')", name="valid_status"),
    )

class SalesItem(Base):
    """Defines the sale_items model"""
    __tablename__ = "sale_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id: Mapped[str] = mapped_column(ForeignKey(Sale.id))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price_at_sale: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

class InventoryLogs(Base):
    """Defines the inventory_log model"""
    __tablename__ = "inventory_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id))
    change_type: Mapped[str] = mapped_column(String(20))
    quantity_change: Mapped[int] = mapped_column(Integer)
    reference_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("change_type IN ('sale', 'restock', 'adjustment', 'cancellation')", name="valid_change_type"),
    )

class AuditLogs(Base):
    """Defines the audit_logs model"""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey(User.id))
    action_type: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[str] = mapped_column(String)
    log_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('create_sale', 'edit_sale', 'cancel_sale', 'delete_sale', "
            "'create_product', 'edit_product', 'delete_product', "
            "'create_user', 'edit_user', 'deactivate_user', "
            "'login', 'logout', 'approve_purchase', 'create_purchase', "
            "'sync_push', 'sync_conflict')",
            name="valid_action_type",
        ),
        CheckConstraint("entity_type IN ('sale', 'product', 'user', 'purchase', 'system')", name="valid_entity_type"),
    )

class Purchase(Base):
    """Defines the Purchase model"""
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by: Mapped[str] = mapped_column(ForeignKey(User.id))
    supplier: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey(User.id))
    approved_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="valid_status"),
    )

class PurchaseItem(Base):
    """Defines the PurchaseItems model"""
    __tablename__ = "purchase_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id: Mapped[str] = mapped_column(ForeignKey(Purchase.id))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id))
    quantity: Mapped[int] = mapped_column(Integer)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))