from flask import Blueprint, jsonify, request
from backend.database import get_db
from backend.models.models import Product

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def list_products():
    """Simple stub to list active products for validation testing."""
    session = get_db()
    products = session.query(Product).filter(Product.is_active == 1).all()
    return jsonify({
        "success": True, 
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "selling_price": float(p.selling_price),
                "stock_quantity": p.stock_quantity
            } for p in products
        ]
    }), 200