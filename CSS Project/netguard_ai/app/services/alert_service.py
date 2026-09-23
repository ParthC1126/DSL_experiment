"""
NetGuard AI — Alert Service
Creates alerts based on actual prediction/risk results.
"""
import logging
from datetime import datetime

from ..extensions import db
from ..models.alert import Alert
from .risk_service import determine_alert_severity, should_create_alert

logger = logging.getLogger(__name__)


def maybe_create_alert(activity) -> Alert | None:
    """
    Evaluate a NetworkActivity and create an Alert if warranted.
    Returns the created Alert or None.
    """
    if not should_create_alert(activity.is_attack, activity.risk_score or 0):
        return None

    severity = determine_alert_severity(activity.risk_score or 0)

    if activity.is_attack:
        message = (
            f"Attack detected: {activity.prediction}. "
            f"Risk score: {activity.risk_score:.1f}/100. "
            f"Confidence: {(activity.confidence * 100):.1f}% "
            if activity.confidence is not None
            else f"Attack detected: {activity.prediction}. Risk score: {activity.risk_score:.1f}/100. Confidence unavailable."
        )
        if activity.confidence is not None:
            message = (
                f"Attack detected: {activity.prediction}. "
                f"Risk score: {activity.risk_score:.1f}/100. "
                f"Confidence: {(activity.confidence * 100):.1f}%."
            )
    else:
        message = (
            f"Suspicious activity flagged with risk score {activity.risk_score:.1f}/100. "
            f"Prediction: {activity.prediction}."
        )

    alert = Alert(
        activity_id=activity.id,
        severity=severity,
        status="open",
        message=message,
        attack_type=activity.prediction if activity.is_attack else None,
        risk_score=activity.risk_score,
    )
    db.session.add(alert)
    db.session.commit()
    logger.info(f"Alert created: severity={severity}, activity_id={activity.id}")
    return alert


def acknowledge_alert(alert_id: int) -> Alert | None:
    alert = Alert.query.get(alert_id)
    if not alert:
        return None
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return alert


def resolve_alert(alert_id: int) -> Alert | None:
    alert = Alert.query.get(alert_id)
    if not alert:
        return None
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.session.commit()
    return alert


def get_alerts(status: str = None, severity: str = None, limit: int = 100) -> list:
    q = Alert.query
    if status:
        q = q.filter_by(status=status)
    if severity:
        q = q.filter_by(severity=severity)
    alerts = q.order_by(Alert.created_at.desc()).limit(limit).all()
    return [a.to_dict() for a in alerts]
