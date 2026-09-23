"""
NetGuard AI — Dashboard API Blueprint
GET /api/dashboard
"""
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func

from ...models.activity import NetworkActivity
from ...models.alert import Alert
from ...models.ml_model_record import MLModelRecord
from ...services.ml_service import get_active_model

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """
    Returns real-time dashboard statistics from the database.
    No hardcoded values.
    """
    try:
        # ── Counts ──────────────────────────────────────────────
        total_analyses = NetworkActivity.query.count()
        total_attacks = NetworkActivity.query.filter_by(is_attack=True).count()
        open_alerts = Alert.query.filter_by(status="open").count()
        total_alerts = Alert.query.count()

        # ── Active model metrics ─────────────────────────────────
        active_model = get_active_model()
        model_accuracy = active_model.accuracy if active_model else None
        model_version = active_model.version if active_model else None

        # ── 24h activity breakdown ───────────────────────────────
        since_24h = datetime.utcnow() - timedelta(hours=24)
        recent_total = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since_24h
        ).count()
        recent_attacks = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since_24h,
            NetworkActivity.is_attack == True,
        ).count()

        # ── Attack type distribution (all time) ──────────────────
        attack_dist = (
            NetworkActivity.query
            .filter_by(is_attack=True)
            .with_entities(NetworkActivity.prediction, func.count(NetworkActivity.id).label("count"))
            .group_by(NetworkActivity.prediction)
            .order_by(func.count(NetworkActivity.id).desc())
            .limit(10)
            .all()
        )
        attack_distribution = [{"type": r.prediction, "count": r.count} for r in attack_dist]

        # ── Threat trend (last 7 days, daily buckets) ────────────
        trend = []
        for days_ago in range(6, -1, -1):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
            day_end = day_start + timedelta(days=1)
            day_total = NetworkActivity.query.filter(
                NetworkActivity.timestamp >= day_start,
                NetworkActivity.timestamp < day_end,
            ).count()
            day_attacks = NetworkActivity.query.filter(
                NetworkActivity.timestamp >= day_start,
                NetworkActivity.timestamp < day_end,
                NetworkActivity.is_attack == True,
            ).count()
            trend.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total": day_total,
                "attacks": day_attacks,
            })

        # ── Recent activities (last 10) ──────────────────────────
        recent_activities = (
            NetworkActivity.query
            .order_by(NetworkActivity.timestamp.desc())
            .limit(10)
            .all()
        )

        # ── Average risk score ───────────────────────────────────
        avg_risk = (
            NetworkActivity.query
            .with_entities(func.avg(NetworkActivity.risk_score))
            .scalar()
        )

        return jsonify({
            "success": True,
            "data": {
                "stats": {
                    "total_analyses": total_analyses,
                    "total_attacks": total_attacks,
                    "attack_rate": round(total_attacks / total_total * 100, 2) if (total_total := total_analyses) > 0 else 0,
                    "open_alerts": open_alerts,
                    "total_alerts": total_alerts,
                    "model_accuracy": round(model_accuracy * 100, 2) if model_accuracy is not None else None,
                    "model_version": model_version,
                    "recent_24h_total": recent_total,
                    "recent_24h_attacks": recent_attacks,
                    "avg_risk_score": round(float(avg_risk), 2) if avg_risk else 0.0,
                },
                "attack_distribution": attack_distribution,
                "threat_trend": trend,
                "recent_activities": [a.to_dict() for a in recent_activities],
                "model_info": active_model.to_dict() if active_model else None,
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": {"code": "DASHBOARD_ERROR", "message": str(e)}}), 500
