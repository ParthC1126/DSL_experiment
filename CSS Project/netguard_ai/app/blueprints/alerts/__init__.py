"""
NetGuard AI — Alerts API Blueprint
GET /api/alerts
PATCH /api/alerts/<id>
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from ...models.alert import Alert
from ...services.alert_service import acknowledge_alert, resolve_alert
from ...extensions import db

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/alerts", methods=["GET"])
def get_alerts():
    """
    Return alerts list.
    Query params: status, severity, limit
    """
    try:
        status = request.args.get("status")
        severity = request.args.get("severity")
        limit = min(int(request.args.get("limit", 50)), 200)
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        q = Alert.query

        if status and status in Alert.STATUS_OPTIONS:
            q = q.filter_by(status=status)
        if severity and severity in Alert.SEVERITY_LEVELS:
            q = q.filter_by(severity=severity)

        q = q.order_by(Alert.created_at.desc())
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)

        # Summary counts by severity
        counts = {
            "open": Alert.query.filter_by(status="open").count(),
            "acknowledged": Alert.query.filter_by(status="acknowledged").count(),
            "resolved": Alert.query.filter_by(status="resolved").count(),
            "critical": Alert.query.filter_by(severity="critical", status="open").count(),
            "high": Alert.query.filter_by(severity="high", status="open").count(),
            "medium": Alert.query.filter_by(severity="medium", status="open").count(),
            "low": Alert.query.filter_by(severity="low", status="open").count(),
        }

        return jsonify({
            "success": True,
            "data": {
                "alerts": [a.to_dict() for a in pagination.items],
                "counts": counts,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": {"code": "ALERTS_ERROR", "message": str(e)}}), 500


@alerts_bp.route("/alerts/<int:alert_id>", methods=["PATCH"])
def update_alert(alert_id: int):
    """
    Update alert status.
    Body: {"status": "acknowledged" | "resolved"}
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status not in Alert.STATUS_OPTIONS:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_STATUS", "message": f"Status must be one of: {Alert.STATUS_OPTIONS}"}
        }), 400

    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Alert not found."}}), 404

    if new_status == "acknowledged":
        alert = acknowledge_alert(alert_id)
    elif new_status == "resolved":
        alert = resolve_alert(alert_id)

    return jsonify({"success": True, "data": alert.to_dict()})
