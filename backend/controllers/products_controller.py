from flask import request, jsonify
from backend.services.products_service import ProductsService


class ProductsController:

    @staticmethod
    def list_products():
        """Handles GET /products."""
        products = ProductsService.get_all_products()
        return jsonify({"success": True, "products": products}), 200

    @staticmethod
    def update_product(product_id):
        """Handles PATCH /products/{id}."""
        updates = request.get_json() or {}

        if not updates:
            return jsonify({"success": False, "error": "No fields provided to update"}), 400

        try:
            product = ProductsService.update_product(product_id, updates)
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 404

        return jsonify({"success": True, "product": product}), 200