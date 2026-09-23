"""
NetGuard AI — Activities API Blueprint
GET /api/activities
GET /api/activities/<id>
"""
import json
from flask import Blueprint, request, jsonify
from ...models.activity import NetworkActivity
from ...services.explanation_service import parse_explanation

activities_bp = Blueprint("activities", __name__)


@activities_bp.route("/activities", methods=["GET"])
def get_activities():
    """
    Return paginated list of network activities.
    Query params: page, per_page, is_attack, prediction, search
    """
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)
        is_attack_filter = request.args.get("is_attack")
        prediction_filter = request.args.get("prediction")

        q = NetworkActivity.query

        if is_attack_filter is not None:
            is_attack_bool = is_attack_filter.lower() in ("true", "1", "yes")
            q = q.filter_by(is_attack=is_attack_bool)

        if prediction_filter:
            q = q.filter(NetworkActivity.prediction.ilike(f"%{prediction_filter}%"))

        q = q.order_by(NetworkActivity.timestamp.desc())
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "success": True,
            "data": {
                "activities": [a.to_dict() for a in pagination.items],
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
        return jsonify({"success": False, "error": {"code": "ACTIVITIES_ERROR", "message": str(e)}}), 500


@activities_bp.route("/activities/<int:activity_id>", methods=["GET"])
def get_activity(activity_id: int):
    """Return a single activity with full detail including parsed explanation."""
    activity = NetworkActivity.query.get(activity_id)
    if not activity:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Activity not found."}}), 404

    data = activity.to_dict()
    data["explanation_parsed"] = parse_explanation(activity.explanation)

    # Include raw features if available
    if activity.raw_features:
        try:
            data["raw_features"] = json.loads(activity.raw_features)
        except Exception:
            data["raw_features"] = {}

    return jsonify({"success": True, "data": data})
