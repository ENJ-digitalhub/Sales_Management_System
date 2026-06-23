from flask import jsonify
from backend.services.products_service import ProductsService

def get_products_controller():
    """Handles the request/response lifecycle for retrieving inventory records."""
    products = ProductsService.fetch_all_products()
    return jsonify(products), 200