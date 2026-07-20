
from flask import request, jsonify, g
from backend.services.items_service import ItemService
from backend.database import get_db
from backend.utils.auth_middleware import require_auth, require_role
from decimal import Decimal

class ItemController:
    @staticmethod
    @require_role("admin", "manager")
    def create_item():
        data = request.get_json()
        name = data.get("name")
        category = data.get("category")
        selling_price = data.get("selling_price")
        cost_price = data.get("cost_price")
        stock_quantity = data.get("stock_quantity")

        if not all([name, selling_price, cost_price, stock_quantity is not None]):
            return jsonify({"success": False, "message": "Name, selling price, cost price, and stock quantity are required"}), 400

        try:
            selling_price = Decimal(str(selling_price))
            cost_price = Decimal(str(cost_price))
        except Exception:
            return jsonify({"success": False, "message": "Selling price and cost price must be valid numbers"}), 400

        session = get_db()
        try:
            item, error = ItemService.create_item(session, g.user.id, name, category, selling_price, cost_price, stock_quantity)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "item": item.to_dict()}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_item(item_id):
        session = get_db()
        try:
            item, error = ItemService.get_item(session, item_id)
            if error:
                return jsonify({"success": False, "message": error}), 404
            return jsonify({"success": True, "item": item.to_dict()}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_all_items():
        session = get_db()
        try:
            items, error = ItemService.get_all_items(session)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "items": [p.to_dict() for p in items]}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_role("admin", "manager")
    def update_item(item_id):
        data = request.get_json()
        name = data.get("name")
        category = data.get("category")
        selling_price = data.get("selling_price")
        cost_price = data.get("cost_price")
        stock_quantity = data.get("stock_quantity")
        is_active = data.get("is_active")

        update_fields = {}
        if name is not None: update_fields["name"] = name
        if category is not None: update_fields["category"] = category
        if selling_price is not None: update_fields["selling_price"] = Decimal(str(selling_price))
        if cost_price is not None: update_fields["cost_price"] = Decimal(str(cost_price))
        if stock_quantity is not None: update_fields["stock_quantity"] = stock_quantity
        if is_active is not None: update_fields["is_active"] = is_active

        if not update_fields:
            return jsonify({"success": False, "message": "No fields provided for update"}), 400

        session = get_db()
        try:
            item, error = ItemService.update_item(session, item_id, g.user.id, **update_fields)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "item": item.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_role("admin", "manager")
    def delete_item(item_id):
        session = get_db()
        try:
            success, error = ItemService.delete_item(session, item_id, g.user.id)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Item deactivated successfully"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
