from sqlalchemy import select
from backend.models.models import Product  # Adjust to point to your Product model file location
from backend.database import SessionLocal 

class ProductsService:
    @staticmethod
    def fetch_all_products() -> list[dict]:
        """Queries the underlying database records inside an isolated session context."""
        # Single responsibility: Context manage the SQLAlchemy connection & read rows
        with SessionLocal() as session:
            stmt = select(Product)
            result = session.scalars(stmt).all()
            
            # Direct mapping from relational rows to safe data dictionaries
            return [
                {
                    "id": prod.id,
                    "name": prod.name,
                    "category": prod.category,
                    "selling_price": float(prod.selling_price),
                    "stock_quantity": prod.stock_quantity
                }
                for prod in result
            ]