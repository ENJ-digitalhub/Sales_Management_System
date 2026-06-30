# backend/services/sales_service.py
from sqlalchemy import select, func
from backend.models.models import Product


class SalesService:
    @staticmethod
    def get_paginated_products(session, page: int, per_page: int):
        """Fetches a paginated slice of records along with total counts."""
        db = session
        offset = (page - 1) * per_page

        # 1. Total row count query
        total_count = db.execute(select(func.count(Product.id)).where(Product.is_active == True)).scalar() or 0

        # 2. Paginated data rows query
        stmt = select(Product).where(Product.is_active == True).offset(offset).limit(per_page)
        products = db.execute(stmt).scalars().all()

        return {
            "items": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "selling_price": p.selling_price,
                    "cost_price": p.cost_price,
                    "stock_quantity": p.stock_quantity
                } for p in products
            ],
            "total": total_count,
            "page": page,
            "per_page": per_page
        }

    @staticmethod
    def update_product(session, product_id: str, updates: dict):
        """Applies a partial update to a single product and returns the updated record."""
        allowed_fields = {"name", "category", "cost_price", "selling_price", "stock_quantity", "is_active"}

        product = session.get(Product, product_id)
        if not product:
            return None

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(product, field, value)

        session.flush()

        return {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "selling_price": product.selling_price,
            "cost_price": product.cost_price,
            "stock_quantity": product.stock_quantity
        }