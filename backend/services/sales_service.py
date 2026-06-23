from sqlalchemy import select, func
from backend.database import SessionLocal
from backend.models.product import Product

class SalesService:
    @staticmethod
    def get_paginated_products(page: int, per_page: int):
        """Fetches a paginated slice of records along with total counts."""
        db = SessionLocal()
        try:
            offset = (page - 1) * per_page
            
            # 1. Total row count query
            total_count = db.execute(select(func.count(Product.id))).scalar() or 0
            
            # 2. Paginated data rows query
            stmt = select(Product).offset(offset).limit(per_page)
            products = db.execute(stmt).scalars().all()
            
            return {
                "items": [
                    {
                        "id": p.id,
                        "sku": p.sku,
                        "name": p.name,
                        "price": p.price,
                        "stock_quantity": p.stock_quantity
                    } for p in products
                ],
                "total": total_count,
                "page": page,
                "per_page": per_page
            }
        finally:
            SessionLocal.remove()