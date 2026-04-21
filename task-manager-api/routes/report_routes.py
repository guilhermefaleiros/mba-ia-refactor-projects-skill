from flask import Blueprint, jsonify

from controllers.report_controller import summary_report, user_report
from middleware.auth import require_admin, require_auth, require_self_or_admin


report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
@require_admin
def summary_report_route():
    return jsonify(summary_report()), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@require_auth
def user_report_route(user_id):
    require_self_or_admin(user_id)
    return jsonify(user_report(user_id)), 200
