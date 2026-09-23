"""
NetGuard AI — Analytics API Blueprint
GET /api/analytics
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from ...models.activity import NetworkActivity
from ...models.alert import Alert
from ...models.ml_model_record import MLModelRecord
from ...services.ml_service import get_active_model

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def get_analytics():
    """
    Comprehensive analytics from the database.
    Query params: days (default 30)
    """
    try:
        days = int(request.args.get("days", 30))
        since = datetime.utcnow() - timedelta(days=days)

        # ── Overall stats ────────────────────────────────────────
        total = NetworkActivity.query.filter(NetworkActivity.timestamp >= since).count()
        attacks = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since,
            NetworkActivity.is_attack == True
        ).count()
        normal = total - attacks

        # ── Attack type breakdown ────────────────────────────────
        attack_types = (
            NetworkActivity.query
            .filter(NetworkActivity.timestamp >= since, NetworkActivity.is_attack == True)
            .with_entities(NetworkActivity.prediction, func.count(NetworkActivity.id).label("count"))
            .group_by(NetworkActivity.prediction)
            .order_by(func.count(NetworkActivity.id).desc())
            .all()
        )
        attack_type_data = [{"type": r.prediction or "Unknown", "count": r.count} for r in attack_types]

        # ── Daily trend ──────────────────────────────────────────
        daily_trend = []
        for d in range(days - 1, -1, -1):
            day_start = (datetime.utcnow() - timedelta(days=d)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
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
            daily_trend.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total": day_total,
                "attacks": day_attacks,
                "normal": day_total - day_attacks,
            })

        # ── Risk score distribution ──────────────────────────────
        risk_buckets = {
            "low (0-30)": NetworkActivity.query.filter(
                NetworkActivity.timestamp >= since,
                NetworkActivity.risk_score <= 30
            ).count(),
            "medium (31-60)": NetworkActivity.query.filter(
                NetworkActivity.timestamp >= since,
                NetworkActivity.risk_score > 30,
                NetworkActivity.risk_score <= 60
            ).count(),
            "high (61-85)": NetworkActivity.query.filter(
                NetworkActivity.timestamp >= since,
                NetworkActivity.risk_score > 60,
                NetworkActivity.risk_score <= 85
            ).count(),
            "critical (86-100)": NetworkActivity.query.filter(
                NetworkActivity.timestamp >= since,
                NetworkActivity.risk_score > 85
            ).count(),
        }

        # ── Protocol breakdown ───────────────────────────────────
        protocol_data = (
            NetworkActivity.query
            .filter(NetworkActivity.timestamp >= since, NetworkActivity.protocol.isnot(None))
            .with_entities(NetworkActivity.protocol, func.count(NetworkActivity.id).label("count"))
            .group_by(NetworkActivity.protocol)
            .order_by(func.count(NetworkActivity.id).desc())
            .limit(10)
            .all()
        )
        protocol_breakdown = [{"protocol": r.protocol, "count": r.count} for r in protocol_data]

        # ── Alert stats ──────────────────────────────────────────
        alert_counts = {
            "total": Alert.query.filter(Alert.created_at >= since).count(),
            "open": Alert.query.filter(Alert.created_at >= since, Alert.status == "open").count(),
            "critical": Alert.query.filter(Alert.created_at >= since, Alert.severity == "critical").count(),
            "high": Alert.query.filter(Alert.created_at >= since, Alert.severity == "high").count(),
        }

        # ── Active model performance ─────────────────────────────
        active_model = get_active_model()
        model_metrics = None
        if active_model:
            model_metrics = {
                "version": active_model.version,
                "accuracy": active_model.accuracy,
                "precision_macro": active_model.precision_macro,
                "recall_macro": active_model.recall_macro,
                "f1_macro": active_model.f1_macro,
                "classes": active_model.classes,
                "confusion_matrix": active_model.confusion_matrix,
            }

        # ── Avg risk & confidence ─────────────────────────────────
        avg_risk = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since
        ).with_entities(func.avg(NetworkActivity.risk_score)).scalar()

        avg_confidence = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since,
            NetworkActivity.confidence.isnot(None)
        ).with_entities(func.avg(NetworkActivity.confidence)).scalar()

        return jsonify({
            "success": True,
            "data": {
                "period_days": days,
                "summary": {
                    "total_analyses": total,
                    "total_attacks": attacks,
                    "normal_traffic": normal,
                    "attack_rate": round(attacks / total * 100, 2) if total > 0 else 0,
                    "avg_risk_score": round(float(avg_risk), 2) if avg_risk else 0.0,
                    "avg_confidence": round(float(avg_confidence), 4) if avg_confidence else None,
                },
                "attack_type_distribution": attack_type_data,
                "daily_trend": daily_trend,
                "risk_distribution": risk_buckets,
                "protocol_breakdown": protocol_breakdown,
                "alert_stats": alert_counts,
                "model_performance": model_metrics,
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": {"code": "ANALYTICS_ERROR", "message": str(e)}}), 500
