from flask import Blueprint
from backend.controllers.inventory_controller import InventoryController
from backend.utils.auth import secure  # Using your verified middleware file

inventory_bp = Blueprint("inventory", __name__)

# Open endpoint: Anyone logged in can browse inventory catalogs
@inventory_bp.route("/products", methods=["GET"])
@secure()
def get_products(current_user):
    return InventoryController.list_products()

# Restricted patch: Only administrators or managers should modify quantities/pricing
@inventory_bp.route("/products/<int:product_id>", methods=["PATCH"])
@secure(allowed_roles=["admin", "manager"])
def patch_product(current_user, product_id):
    return InventoryController.patch_product(product_id)