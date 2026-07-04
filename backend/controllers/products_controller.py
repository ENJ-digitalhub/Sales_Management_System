from flask import request, jsonify, g
from backend.database import get_db
from backend.services.products_service import ProductsService
from backend.utils.validators import validate_product_payload


class ProductsController:
    def get_products(self):
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"
        session = get_db()
        try:
            products = ProductsService.get_all_products(session, include_inactive=include_inactive)
            return jsonify({"success": True, "products": products}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to fetch products", "detail": str(e)}), 500

    def create_product(self, current_user):
        data = request.get_json(silent=True) or {}
        validation = validate_product_payload(data, partial=False)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            product = ProductsService.create_product(session, current_user["id"], validation["fields"])
            session.commit()
            return jsonify({"success": True, "product": product}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to create product", "detail": str(e)}), 500

    def edit_product(self, product_id, current_user):
        data = request.get_json(silent=True) or {}
        validation = validate_product_payload(data, partial=True)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            product = ProductsService.edit_product(session, current_user["id"], product_id, validation["fields"])
            if product is None:
                return jsonify({"success": False, "message": "Product not found"}), 404
            session.commit()
            return jsonify({"success": True, "product": product}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to edit product", "detail": str(e)}), 500

    def deactivate_product(self, product_id, current_user):
        session = get_db()
        try:
            product = ProductsService.deactivate_product(session, current_user["id"], product_id)
            if product is None:
                return jsonify({"success": False, "message": "Product not found"}), 404
            session.commit()
            return jsonify({"success": True, "message": "Product deactivated"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to deactivate product", "detail": str(e)}), 500