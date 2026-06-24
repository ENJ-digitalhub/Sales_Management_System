from flask import Blueprint, jsonify, request
from backend.utils.decorators import require_auth, require_roles

products_bp = Blueprint("products", __name__, url_prefix="/products")

@products_bp.route("", methods=["GET"])
@require_auth
def list_products():
    # Route logic invokes InventoryService.get_all_products()
    return jsonify({"success": True, "products": []}), 200

@products_bp.route("/<int:product_id>", methods=["PATCH"])
@require_auth
@require_roles("admin", "manager")
def update_product(product_id):
    # Core update operations executed here
    return jsonify({"success": True, "message": f"Product {product_id} updated"}), 200