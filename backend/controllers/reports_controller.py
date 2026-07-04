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