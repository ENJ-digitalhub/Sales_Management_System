<<<<<<< HEAD
import uuid
from datetime import datetime
from sqlalchemy import (
    
    Column, String, DateTime, Numeric, Integer, ForeignKey,
    CheckConstraint, UniqueConstraint, JSON)

from sqlalchemy.orm import relationship
from backend.database import Base



class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'manager', 'employee')", name='valid_role'),
        UniqueConstraint('username', name='uq_user_username'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    username = Column(String(80), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='employee')
    phone_or_email = Column(String(50), nullable=False)
    account_name = Column(String(50), nullable=True)
    bank_name = Column(String(50), nullable=True)
    account_number = Column(String(10), nullable=True)
    pin_hash = Column(String(60), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    sales = relationship('Sale', back_populates='user', foreign_keys='Sale.user_id')
    audit_logs = relationship('AuditLog', back_populates='user', foreign_keys='AuditLog.user_id')
    purchases_created = relationship('Purchase', back_populates='creator', foreign_keys='Purchase.created_by')
    purchases_approved = relationship('Purchase', back_populates='approver', foreign_keys='Purchase.approved_by')
    devices = relationship('Device', back_populates='user', foreign_keys='Device.user_id')


class Device(Base):
    __tablename__ = 'devices'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    last_seen_at = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='devices', foreign_keys=[user_id])


class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (
        UniqueConstraint('sku', name='uq_product_sku'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False)
    sku = Column(String(50), nullable=False)
    category = Column(String(50), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    selling_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    stock_quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale_items = relationship('SaleItem', back_populates='product')
    inventory_logs = relationship('InventoryLog', back_populates='product')
    purchase_items = relationship('PurchaseItem', back_populates='product')

=======

from decimal import Decimal
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Boolean, JSON, CheckConstraint, ForeignKey, Integer, DateTime, Text
from datetime import datetime, timedelta
from backend.utils.time import now_utc
import json
import uuid

class Base(DeclarativeBase):
    """Defines the base class for SQLAlchemy models"""
    pass

class User(Base):
    """Defines the User model"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="employee")
    phone_or_email: Mapped[str | None] = mapped_column(String(100))
    account_name: Mapped[str | None] = mapped_column(String(100))
    bank_name: Mapped[str | None] = mapped_column(String(100))
    account_number: Mapped[str | None] = mapped_column(String(20))
    pin_hash: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    devices: Mapped[list["Device"]] = relationship("Device", back_populates="user")
    sales: Mapped[list["Sale"]] = relationship("Sale", back_populates="user")
    purchases: Mapped[list["Purchase"]] = relationship("Purchase", back_populates="creator", foreign_keys="[Purchase.created_by]")
    approved_purchases: Mapped[list["Purchase"]] = relationship("Purchase", back_populates="approver", foreign_keys="[Purchase.approved_by]")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN (\'admin\', \'manager\', \'employee\')", name="valid_role"),
        CheckConstraint("is_active IN (0, 1)", name="valid_user_is_active"),
    )

class Product(Base):
    """Defines the Product model"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)

    sale_items: Mapped[list["SaleItem"]] = relationship("SaleItem", back_populates="product")
    purchase_items: Mapped[list["PurchaseItem"]] = relationship("PurchaseItem", back_populates="product")
    inventory_logs: Mapped[list["InventoryLog"]] = relationship("InventoryLog", back_populates="product")

    __table_args__ = (
        CheckConstraint("selling_price >= 0", name="selling_price_positive"),
        CheckConstraint("cost_price >= 0", name="cost_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="stock_quantity_non_negative"),
        CheckConstraint("is_active IN (0, 1)", name="valid_product_is_active"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "selling_price": float(self.selling_price) if isinstance(self.selling_price, Decimal) else self.selling_price,
            "cost_price": float(self.cost_price) if isinstance(self.cost_price, Decimal) else self.cost_price,
            "stock_quantity": self.stock_quantity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

class Sale(Base):
    __tablename__ = 'sales'

<<<<<<< HEAD

    __table_args__ = (

        CheckConstraint(
            "payment_method IN ('cash', 'transfer', 'pos')",
            name='valid_payment_method'
        ),
        CheckConstraint("status IN ('completed', 'edited', 'cancelled')", name='valid_sale_status'),
        UniqueConstraint('client_transaction_id', name='uq_sale_client_txn'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_transaction_id = Column(String(36), nullable=False)
    device_id = Column(String(36), nullable=False)
    receipt_number = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    profit_at_sale = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='completed')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    editable_until = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='sales', foreign_keys=[user_id])
    items = relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')


class SaleItem(Base):
    __tablename__ = 'sale_items'
=======
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey(User.id))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    profit_at_sale: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    editable_until: Mapped[datetime] = mapped_column(DateTime, default=lambda: now_utc() + timedelta(minutes=20))

    user: Mapped["User"] = relationship("User", back_populates="sales")
    items: Mapped[list["SaleItem"]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="total_amount_positive"),
        CheckConstraint("profit_at_sale >= 0", name="profit_at_sale_positive"),
        CheckConstraint("payment_method IN (\'cash\', \'transfer\', \'pos\')", name="valid_payment_method"),
        CheckConstraint("status IN (\'completed\', \'edited\', \'cancelled\')", name="valid_sale_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "receipt_number": self.receipt_number,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount) if isinstance(self.total_amount, Decimal) else self.total_amount,
            "profit_at_sale": float(self.profit_at_sale) if isinstance(self.profit_at_sale, Decimal) else self.profit_at_sale,
            "payment_method": self.payment_method,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "editable_until": self.editable_until.isoformat() if self.editable_until else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }

class SaleItem(Base):
    """Defines the SaleItem model"""
    __tablename__ = "sale_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id: Mapped[str] = mapped_column(ForeignKey(Sale.id, ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id, ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost_price_at_sale: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="sale_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_positive"),
        CheckConstraint("cost_price_at_sale >= 0", name="cost_price_at_sale_positive"),
        CheckConstraint("total_price >= 0", name="total_price_positive"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if isinstance(self.unit_price, Decimal) else self.unit_price,
            "cost_price_at_sale": float(self.cost_price_at_sale) if isinstance(self.cost_price_at_sale, Decimal) else self.cost_price_at_sale,
            "total_price": float(self.total_price) if isinstance(self.total_price, Decimal) else self.total_price,
        }

class InventoryLog(Base):
    """Defines the InventoryLog model"""
    __tablename__ = "inventory_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id, ondelete="RESTRICT"))
    change_type: Mapped[str] = mapped_column(String(20))
    quantity_change: Mapped[int] = mapped_column(Integer)
    reference_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    product: Mapped["Product"] = relationship("Product", back_populates="inventory_logs")
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = Column(String, ForeignKey('sales.id'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price_at_sale = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

<<<<<<< HEAD
    sale = relationship('Sale', back_populates='items')
    product = relationship('Product', back_populates='sale_items')

=======
class AuditLog(Base):
    """Defines the AuditLog model"""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"))
    action_type: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[str | None] = mapped_column(String(255))
    log_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

class InventoryLog(Base):
    __tablename__ = 'inventory_logs'
    __table_args__ = (
<<<<<<< HEAD
        CheckConstraint(
            "change_type IN ('sale', 'cancellation', 'restock', 'adjustment', 'sale_edit')",
            name='valid_change_type'
        ),
=======
        CheckConstraint("action_type IN ('create_sale', 'edit_sale', 'cancel_sale', 'delete_sale', 'create_product', 'edit_product', 'delete_product', 'create_user', 'edit_user', 'deactivate_user', 'login', 'logout', 'approve_purchase', 'create_purchase', 'sync_push', 'sync_conflict')", name="valid_action_type"),
        CheckConstraint("entity_type IN ('sale', 'product', 'user', 'purchase', 'system')", name="valid_entity_type"),
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey('products.id'), nullable=False, index=True)
    change_type = Column(String(20), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reference_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    product = relationship('Product', back_populates='inventory_logs')
    

class SyncQueue(Base):
    __tablename__ = 'sync_queue'
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'synced', 'failed', 'conflict')",
            name='valid_sync_status'
        ),
        CheckConstraint(
            "conflict_type IS NULL OR conflict_type IN ('stock', 'deleted_product', 'duplicate')",
            name='valid_conflict_type'
        ),
    )

    id = Column(String, primary_key=True)  # client-supplied transaction_id
    device_id = Column(String(36), nullable=False, index=True)
    submitted_by = Column(String, ForeignKey('users.id'), nullable=True)  # who originally pushed this transaction
    entity_type = Column(String(30), nullable=False)
    operation = Column(String(20), nullable=False, default='CREATE')
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    conflict_type = Column(String(30), nullable=True)  # set only when status == 'conflict'
    retry_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    result_message = Column(String(255), nullable=True)
    server_sale_id = Column(String(36), nullable=True)
    resolved_by = Column(String, ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    action_type = Column(String(30), nullable=False)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)
    log_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship('User', back_populates='audit_logs', foreign_keys=[user_id])


class Purchase(Base):
<<<<<<< HEAD
    __tablename__ = 'purchases'
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'received')", name='valid_purchase_status'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    supplier = Column(String, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    total_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_by = Column(String, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    creator = relationship('User', back_populates='purchases_created', foreign_keys=[created_by])
    approver = relationship('User', back_populates='purchases_approved', foreign_keys=[approved_by])
    items = relationship('PurchaseItem', back_populates='purchase', cascade='all, delete-orphan')


class PurchaseItem(Base):
    __tablename__ = 'purchase_items'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id = Column(String, ForeignKey('purchases.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    purchase = relationship('Purchase', back_populates='items')
    product = relationship('Product', back_populates='purchase_items')
=======
    """Defines the Purchase model"""
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by: Mapped[str] = mapped_column(ForeignKey(User.id, ondelete="RESTRICT"))
    supplier: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)

    creator: Mapped["User"] = relationship("User", back_populates="purchases", foreign_keys="[Purchase.created_by]")
    approver: Mapped["User"] = relationship("User", back_populates="approved_purchases", foreign_keys="[Purchase.approved_by]")
    items: Mapped[list["PurchaseItem"]] = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_cost >= 0", name="total_cost_positive"),
        CheckConstraint("status IN (\'pending\', \'approved\', \'rejected\')", name="valid_purchase_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "created_by": self.created_by,
            "supplier": self.supplier,
            "status": self.status,
            "total_cost": float(self.total_cost) if isinstance(self.total_cost, Decimal) else self.total_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "items": [item.to_dict() for item in self.items] if self.items else []
        }

class PurchaseItem(Base):
    """Defines the PurchaseItem model"""
    __tablename__ = "purchase_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id: Mapped[str] = mapped_column(ForeignKey(Purchase.id, ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(ForeignKey(Product.id, ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="purchase_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="purchase_quantity_positive"),
        CheckConstraint("cost_price >= 0", name="purchase_cost_price_positive"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "purchase_id": self.purchase_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "cost_price": float(self.cost_price) if isinstance(self.cost_price, Decimal) else self.cost_price,
        }

class Device(Base):
    """Defines the Device model"""
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    device_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)

    user: Mapped["User"] = relationship("User", back_populates="devices")

    __table_args__ = (
        CheckConstraint("is_active IN (0, 1)", name="valid_device_is_active"),
    )

class SyncQueue(Base):
    """Defines the SyncQueue model"""
    __tablename__ = "sync_queue"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(255), unique=True) # Globally unique ID for idempotency
    device_id: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))
    operation: Mapped[str] = mapped_column(String(10))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    conflict_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'synced', 'failed', 'conflict')", name="valid_sync_status"),
        CheckConstraint("entity_type IN ('sale', 'product', 'user', 'purchase', 'device')", name="valid_sync_entity_type"),
        CheckConstraint("operation IN ('CREATE', 'UPDATE', 'DELETE')", name="valid_sync_operation"),
        CheckConstraint("conflict_type IN ('stock', 'deleted_product', 'duplicate') OR conflict_type IS NULL", name="valid_sync_conflict_type"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "device_id": self.device_id,
            "entity_type": self.entity_type,
            "operation": self.operation,
            "payload": json.loads(self.payload) if isinstance(self.payload, str) else self.payload,
            "status": self.status,
            "retry_count": self.retry_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "created_at": self.created_at.isoformat()
        }
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
