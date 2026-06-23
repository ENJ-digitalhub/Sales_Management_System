from flask import jsonify, request
from backend.services.inventory_service import InventoryService

class InventoryController:
    @staticmethod
    def list_products():
        products = InventoryService.get_all_products()
        serialized = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock_quantity": p.stock_quantity
            } for p in products
        ]
        return jsonify(serialized), 200

    @staticmethod
    def patch_product(product_id):
        data = request.get_json() or {}
        updated_product = InventoryService.update_product(product_id, data)
        
        if not updated_product:
            return jsonify({"error": f"Product with ID {product_id} not found"}), 404
            
        return jsonify(updated_product), 200