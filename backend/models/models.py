import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Numeric, Integer, ForeignKey,
    CheckConstraint, UniqueConstraint, JSON
)
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


class Sale(Base):
    __tablename__ = 'sales'
    __table_args__ = (
        # Keep this list in sync with ALLOWED_PAYMENT_METHODS in
        # backend/utils/validators.py — this is intentionally duplicated
        # as a DB-level backstop, not the primary validation layer.
        CheckConstraint(
            "payment_method IN ("
            "'cash','card','contactless','bank_transfer','ussd','qr_payment',"
            "'pos_terminal','digital_wallet','store_wallet','credit_sale',"
            "'installment','gift_card','loyalty_points','split_payment',"
            "'trexave_pay','other')",
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
    payment_method = Column(String(30), nullable=False)
    payment_provider = Column(String(30), nullable=True)
    payment_details = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default='completed')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    editable_until = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='sales', foreign_keys=[user_id])
    items = relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')


class SaleItem(Base):
    __tablename__ = 'sale_items'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = Column(String, ForeignKey('sales.id'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price_at_sale = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    sale = relationship('Sale', back_populates='items')
    product = relationship('Product', back_populates='sale_items')


class InventoryLog(Base):
    __tablename__ = 'inventory_logs'
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('sale', 'cancellation', 'restock', 'adjustment', 'sale_edit')",
            name='valid_change_type'
        ),
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
            "status IN ('pending', 'synced', 'failed')",
            name='valid_sync_status'
        ),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(30), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    retry_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
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