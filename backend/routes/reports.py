from flask import Blueprint
from backend.controllers.reports_controller import ReportsController
from backend.utils.auth_middleware import require_auth, require_role

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

reports_bp.route("/daily", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_daily_report)))
reports_bp.route("/monthly", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_monthly_report)))
reports_bp.route("/yearly", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_yearly_report)))
reports_bp.route("/employee/<string:user_id>", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_employee_report)))
