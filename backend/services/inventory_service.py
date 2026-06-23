from backend.database import SessionLocal
from backend.models.models import Product

class InventoryService:
    @staticmethod
    def get_all_products():
        with SessionLocal() as session:
            return session.query(Product).filter(Product.is_active == True).all()

    @staticmethod
    def update_product(product_id, update_data):
        with SessionLocal() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None
            
            # Dynamically patch allowed tracking fields safely
            for key, value in update_data.items():
                if hasattr(product, key) and key != "id":
                    setattr(product, key, value)
            
            session.commit()
            session.refresh(product)
            
            # Detach model from session scope to pass data safely across layers
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "is_active": product.is_active
            }