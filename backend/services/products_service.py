from backend.models.database import get_session
from backend.models.product import Product


class ProductsService:
    @staticmethod
    def get_all_products() -> list[dict]:
        """Returns all active products as plain dictionaries."""
        with get_session() as session:
            products = session.query(Product).all()
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "category": p.category,
                    "cost_price": float(p.cost_price),
                    "selling_price": float(p.selling_price),
                    "stock_quantity": p.stock_quantity,
                    "is_active": p.is_active,
                }
                for p in products
            ]

    @staticmethod
    def update_product(product_id: int, updates: dict) -> dict:
        """Applies a partial update to a single product and returns the updated record."""
        allowed_fields = {
            "name", "category", "cost_price", "selling_price",
            "stock_quantity", "is_active"
        }

        with get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()

            if not product:
                raise ValueError("Product not found")

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(product, field, value)

            session.flush()

            return {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "cost_price": float(product.cost_price),
                "selling_price": float(product.selling_price),
                "stock_quantity": product.stock_quantity,
                "is_active": product.is_active,
            }