from flask import request, jsonify
from backend.database import get_db
from backend.services.purchases_service import (
    PurchasesService,
    ProductNotFoundError,
    PurchaseNotFoundError,
    PurchaseAlreadyProcessedError,
)
from backend.utils.validators import validate_purchase_payload


class PurchasesController:
    def create_purchase(self, current_user):
        data = request.get_json(silent=True) or {}
        validation = validate_purchase_payload(data)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            purchase = PurchasesService.create_purchase(
                session=session,
                user_id=current_user["id"],
                items=validation["items"],
                supplier=validation["supplier"],
            )
            session.commit()
            return jsonify({"success": True, "purchase": purchase}), 201

        except ProductNotFoundError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e), "product_id": e.product_id}), 400

        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to create purchase", "detail": str(e)}), 500

    def approve_purchase(self, purchase_id, current_user):
        session = get_db()
        try:
            result = PurchasesService.approve_purchase(
                session=session,
                purchase_id=purchase_id,
                admin_id=current_user["id"],
            )
            session.commit()
            return jsonify(result), 200

        except PurchaseNotFoundError:
            session.rollback()
            return jsonify({"success": False, "message": "Purchase not found"}), 404

        except PurchaseAlreadyProcessedError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

        except ProductNotFoundError as e:
            session.rollback()
            return jsonify({
                "success": False,
                "message": f"Cannot approve — product no longer exists: {e.product_id}",
                "product_id": e.product_id,
            }), 400

        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to approve purchase", "detail": str(e)}), 500

    def get_purchase(self, purchase_id):
        session = get_db()
        try:
            purchase = PurchasesService.get_purchase(session, purchase_id)
            if purchase is None:
                return jsonify({"success": False, "message": "Purchase not found"}), 404
            return jsonify({"success": True, "purchase": purchase}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to fetch purchase", "detail": str(e)}), 500

    def get_purchase_history(self):
        session = get_db()
        try:
            purchases = PurchasesService.get_purchase_history(session)
            return jsonify({"success": True, "purchases": purchases}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to fetch purchase history", "detail": str(e)}), 500