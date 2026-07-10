from flask import Blueprint
<<<<<<< HEAD
from backend.middleware.auth_middleware import require_auth, require_role
from backend.controllers.reports_controller import ReportsController

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")
reports_controller = ReportsController()


@reports_bp.route("/daily", methods=["GET"])
@require_auth
@require_role("admin", "manager")
def get_daily_report():
    return reports_controller.get_daily_report()


@reports_bp.route("/monthly", methods=["GET"])
@require_auth
@require_role("admin", "manager")
def get_monthly_report():
    return reports_controller.get_monthly_report()


@reports_bp.route("/yearly", methods=["GET"])
@require_auth
@require_role("admin", "manager")
def get_yearly_report():
    return reports_controller.get_yearly_report()


@reports_bp.route("/employee/<user_id>", methods=["GET"])
@require_auth
@require_role("admin", "manager")
def get_employee_report(user_id):
    return reports_controller.get_employee_report(user_id)
=======
from backend.controllers.reports_controller import ReportsController
from backend.utils.auth_middleware import require_auth, require_role

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

reports_bp.route("/daily", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_daily_report)))
reports_bp.route("/monthly", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_monthly_report)))
reports_bp.route("/yearly", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_yearly_report)))
reports_bp.route("/employee/<string:user_id>", methods=["GET"])(require_auth(require_role("admin", "manager")(ReportsController.get_employee_report)))
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
