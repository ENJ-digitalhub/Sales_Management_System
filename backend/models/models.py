from sqlalchemy import Column, Integer, String, Float, Boolean
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  # <--- Add this line
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee")
    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}  # <--- Add this line

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)