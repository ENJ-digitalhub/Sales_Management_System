<<<<<<< HEAD
from flask import request, jsonify
from backend.database import get_db
from backend.services.reports_service import ReportsService
from backend.utils.validators import (
    validate_daily_report_params,
    validate_monthly_report_params,
    validate_yearly_report_params,
    validate_employee_report_params,
)


class ReportsController:
    def get_daily_report(self):
        validation = validate_daily_report_params(request.args.get("date"))
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            report = ReportsService.get_daily_report(session, validation["date"])
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to generate daily report", "detail": str(e)}), 500

    def get_monthly_report(self):
        validation = validate_monthly_report_params(request.args.get("month"))
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            report = ReportsService.get_monthly_report(session, validation["year"], validation["month"])
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to generate monthly report", "detail": str(e)}), 500

    def get_yearly_report(self):
        validation = validate_yearly_report_params(request.args.get("year"))
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            report = ReportsService.get_yearly_report(session, validation["year"])
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to generate yearly report", "detail": str(e)}), 500

    def get_employee_report(self, user_id):
        validation = validate_employee_report_params(
            request.args.get("from"), request.args.get("to")
        )
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            report = ReportsService.get_employee_report(
                session, user_id, validation["from_date"], validation["to_date"]
            )
            if report is None:
                return jsonify({"success": False, "message": "Employee not found"}), 404
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to generate employee report", "detail": str(e)}), 500
=======
from flask import request, jsonify, g
from backend.services.reports_service import ReportsService
from backend.database import get_db
from backend.utils.auth_middleware import require_auth, require_role
from datetime import datetime

class ReportsController:
    @staticmethod
    @require_auth
    @require_role("admin", "manager")
    def get_daily_report():
        date_str = request.args.get("date")
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400

        session = get_db()
        try:
            report, error = ReportsService.get_daily_report(session, report_date)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    @require_role("admin", "manager")
    def get_monthly_report():
        month = request.args.get("month")
        try:
            year_month = datetime.strptime(month, "%Y-%m").date() if month else None
        except ValueError:
            return jsonify({"success": False, "message": "Invalid month format. Use YYYY-MM."}), 400

        session = get_db()
        try:
            report, error = ReportsService.get_monthly_report(session, year_month)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    @require_role("admin", "manager")
    def get_yearly_report():
        year = request.args.get("year")
        try:
            report_year = int(year) if year else None
        except ValueError:
            return jsonify({"success": False, "message": "Invalid year format. Use YYYY."}), 400

        session = get_db()
        try:
            report, error = ReportsService.get_yearly_report(session, report_year)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    @require_role("admin", "manager")
    def get_employee_report(user_id):
        from_date = request.args.get("from")
        to_date = request.args.get("to")
        try:
            from_date_parsed = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
            to_date_parsed = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400

        session = get_db()
        try:
            report, error = ReportsService.get_employee_report(session, user_id, from_date_parsed, to_date_parsed)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "report": report}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
