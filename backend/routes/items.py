
from flask import Blueprint
from backend.controllers.items_controller import ItemController
from backend.utils.auth_middleware import require_auth, require_role

items_bp = Blueprint("items", __name__, url_prefix="/items")

items_bp.route("/", methods=["POST"])(require_auth(require_role("admin", "manager")(ItemController.create_item)))
items_bp.route("/<string:item_id>", methods=["GET"])(require_auth(ItemController.get_item))
items_bp.route("/", methods=["GET"])(require_auth(ItemController.get_all_items))
items_bp.route("/<string:item_id>", methods=["PATCH"])(require_auth(require_role("admin", "manager")(ItemController.update_item)))
items_bp.route("/<string:item_id>", methods=["DELETE"])(require_auth(require_role("admin", "manager")(ItemController.delete_item)))