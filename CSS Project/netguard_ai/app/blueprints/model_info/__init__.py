"""
NetGuard AI — Model Info API Blueprint
GET /api/model/info
GET /api/model/performance
GET /api/model/versions
PATCH /api/model/activate/<version>
"""
from flask import Blueprint, request, jsonify
from ...models.ml_model_record import MLModelRecord
from ...services.ml_service import get_active_model, list_model_versions, activate_model
from ...ml.predictor import get_feature_importances

model_info_bp = Blueprint("model_info", __name__)


@model_info_bp.route("/model/info", methods=["GET"])
def get_model_info():
    """Return active model metadata."""
    active = get_active_model()
    if not active:
        return jsonify({
            "success": True,
            "data": None,
            "message": "No active model. Please train a model first.",
        })
    return jsonify({"success": True, "data": active.to_dict()})


@model_info_bp.route("/model/performance", methods=["GET"])
def get_model_performance():
    """Return active model performance metrics including feature importances."""
    active = get_active_model()
    if not active:
        return jsonify({
            "success": True,
            "data": None,
            "message": "No active model.",
        })

    try:
        importances_result = get_feature_importances(active)
    except Exception as e:
        importances_result = {"success": False, "error": str(e)}

    import json
    cr_raw = active.classification_report_json
    classification_report = json.loads(cr_raw) if cr_raw else {}

    return jsonify({
        "success": True,
        "data": {
            "version": active.version,
            "accuracy": active.accuracy,
            "precision_macro": active.precision_macro,
            "recall_macro": active.recall_macro,
            "f1_macro": active.f1_macro,
            "confusion_matrix": active.confusion_matrix,
            "classes": active.classes,
            "classification_report": classification_report,
            "feature_importances": importances_result.get("importances", []) if importances_result.get("success") else [],
            "n_samples": active.n_samples,
            "n_features": active.n_features,
            "n_estimators": active.n_estimators,
            "max_depth": active.max_depth,
            "test_size": active.test_size,
        }
    })


@model_info_bp.route("/model/versions", methods=["GET"])
def get_model_versions():
    """Return all trained model versions."""
    versions = list_model_versions()
    return jsonify({"success": True, "data": versions})


@model_info_bp.route("/model/activate/<string:version>", methods=["PATCH"])
def set_active_model(version: str):
    """Activate a specific model version."""
    ok = activate_model(version)
    if not ok:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": f"Model version '{version}' not found."}
        }), 404
    return jsonify({"success": True, "message": f"Model {version} is now active."})
