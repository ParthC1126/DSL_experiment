"""
NetGuard AI — Activity Analyzer API Blueprint
POST /api/analyze
"""
import json
from flask import Blueprint, request, jsonify, current_app

from ...extensions import db
from ...models.activity import NetworkActivity
from ...services.ml_service import get_active_model
from ...services.risk_service import calculate_risk_score, calculate_security_score
from ...services.alert_service import maybe_create_alert
from ...services.explanation_service import generate_explanation
from ...ml.predictor import predict

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
def analyze_activity():
    """
    Analyze a network activity using the active ML model.
    Accepts: JSON body with feature key-value pairs + optional network metadata.
    Returns: prediction, confidence, risk score, explanation.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": {"code": "NO_DATA", "message": "Request body must be JSON."}}), 400

    # Check active model
    model_record = get_active_model()
    if not model_record:
        return jsonify({
            "success": False,
            "error": {
                "code": "NO_MODEL",
                "message": "No trained model is active. Please upload a dataset and train a model first.",
            }
        }), 422

    # Extract known network metadata from the payload (optional display fields)
    meta_fields = ["src_ip", "dst_ip", "protocol", "src_port", "dst_port",
                   "duration", "packet_size", "bytes_sent", "bytes_received", "flags"]
    meta = {k: data.get(k) for k in meta_fields}

    # All remaining fields are treated as ML features
    features_dict = {k: v for k, v in data.items() if k not in meta_fields}

    if not features_dict:
        # If no separate feature fields, try using the full payload as features
        features_dict = data

    # Run prediction
    result = predict(features_dict, model_record)

    if not result["success"]:
        return jsonify({
            "success": False,
            "error": {"code": "PREDICTION_FAILED", "message": result.get("error", "Prediction failed.")},
        }), 500

    prediction = result["prediction"]
    is_attack = result["is_attack"]
    confidence = result["confidence"]
    probabilities = result.get("probabilities")

    # Calculate risk
    risk_score = calculate_risk_score(is_attack, prediction, confidence)
    security_score = calculate_security_score(risk_score)

    # Generate explanation
    explanation = generate_explanation(
        features_dict=features_dict,
        probabilities=probabilities,
        prediction=prediction,
        is_attack=is_attack,
        model_record=model_record,
    )

    # Persist to database
    activity = NetworkActivity(
        src_ip=meta.get("src_ip"),
        dst_ip=meta.get("dst_ip"),
        protocol=meta.get("protocol"),
        src_port=_safe_int(meta.get("src_port")),
        dst_port=_safe_int(meta.get("dst_port")),
        duration=_safe_float(meta.get("duration")),
        packet_size=_safe_int(meta.get("packet_size")),
        bytes_sent=_safe_int(meta.get("bytes_sent")),
        bytes_received=_safe_int(meta.get("bytes_received")),
        flags=meta.get("flags"),
        raw_features=json.dumps(features_dict),
        prediction=prediction,
        is_attack=is_attack,
        confidence=confidence,
        risk_score=risk_score,
        security_score=security_score,
        explanation=explanation,
        model_version=model_record.version,
    )
    db.session.add(activity)
    db.session.commit()

    # Trigger alert if needed
    alert = maybe_create_alert(activity)

    current_app.logger.info(
        f"Analysis complete: prediction={prediction}, risk={risk_score}, activity_id={activity.id}"
    )

    return jsonify({
        "success": True,
        "data": {
            "activity_id": activity.id,
            "prediction": prediction,
            "is_attack": is_attack,
            "confidence": confidence,
            "confidence_display": f"{confidence * 100:.1f}%" if confidence is not None else "Confidence unavailable",
            "risk_score": risk_score,
            "security_score": security_score,
            "explanation": json.loads(explanation) if explanation else [],
            "probabilities": probabilities,
            "alert_created": alert is not None,
            "alert_id": alert.id if alert else None,
            "model_version": model_record.version,
        }
    })


def _safe_int(v):
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _safe_float(v):
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None
