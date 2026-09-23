"""
NetGuard AI — Centralized Prediction Logic
Loads the active model and its exact preprocessing pipeline for inference.
"""
import json
import logging
import os

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Module-level cache to avoid reloading from disk on every request
_cache = {
    "version": None,
    "clf": None,
    "preprocessor": None,
    "le": None,
    "metadata": None,
}


def _load_artifacts(model_record) -> bool:
    """Load model artifacts from disk into cache. Returns True on success."""
    global _cache
    try:
        clf = joblib.load(model_record.model_path)
        preprocessor = joblib.load(model_record.preprocessor_path)
        le_path = model_record.model_path.replace("model.joblib", "label_encoder.joblib")
        le = joblib.load(le_path)
        meta_path = model_record.metadata_path
        with open(meta_path) as f:
            metadata = json.load(f)

        _cache["version"] = model_record.version
        _cache["clf"] = clf
        _cache["preprocessor"] = preprocessor
        _cache["le"] = le
        _cache["metadata"] = metadata
        logger.info(f"Predictor loaded model version {model_record.version}")
        return True
    except Exception as e:
        logger.error(f"Failed to load model artifacts: {e}")
        return False


def predict(features_dict: dict, model_record) -> dict:
    """
    Run inference using the active model.

    Args:
        features_dict: dict of {feature_name: value}
        model_record: MLModelRecord ORM object

    Returns:
        {
          "success": bool,
          "prediction": str,
          "is_attack": bool,
          "confidence": float | None,
          "probabilities": dict | None,
          "error": str (if failed)
        }
    """
    # (Re)load if version changed
    if _cache["version"] != model_record.version:
        ok = _load_artifacts(model_record)
        if not ok:
            return {"success": False, "error": "Failed to load model artifacts."}

    clf = _cache["clf"]
    preprocessor = _cache["preprocessor"]
    le = _cache["le"]
    metadata = _cache["metadata"]

    feature_columns = metadata.get("feature_columns", [])

    # Build DataFrame with exact feature columns
    try:
        row = {col: features_dict.get(col, np.nan) for col in feature_columns}
        X = pd.DataFrame([row])
    except Exception as e:
        return {"success": False, "error": f"Feature construction error: {str(e)}"}

    # Preprocess using the saved pipeline (no re-fitting)
    try:
        X_proc = preprocessor.transform(X)
    except Exception as e:
        return {"success": False, "error": f"Preprocessing error: {str(e)}"}

    # Predict
    try:
        y_pred_enc = clf.predict(X_proc)
        y_pred_label = le.inverse_transform(y_pred_enc)[0]

        # Confidence from predict_proba if available
        confidence = None
        probabilities = None
        if hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X_proc)[0]
            confidence = float(np.max(proba))
            probabilities = {
                str(le.classes_[i]): float(proba[i])
                for i in range(len(le.classes_))
            }

        # Determine if attack (everything that isn't NORMAL/normal/benign/Benign)
        NORMAL_LABELS = {"normal", "benign", "legitimate", "safe"}
        is_attack = str(y_pred_label).strip().lower() not in NORMAL_LABELS

        return {
            "success": True,
            "prediction": str(y_pred_label),
            "is_attack": is_attack,
            "confidence": confidence,
            "probabilities": probabilities,
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"success": False, "error": f"Prediction failed: {str(e)}"}


def get_feature_importances(model_record) -> dict:
    """Return feature importances from the Random Forest model."""
    if _cache["version"] != model_record.version:
        ok = _load_artifacts(model_record)
        if not ok:
            return {"success": False, "error": "Failed to load model."}

    clf = _cache["clf"]
    metadata = _cache["metadata"]
    feature_columns = metadata.get("feature_columns", [])

    if not hasattr(clf, "feature_importances_"):
        return {"success": False, "error": "Model does not expose feature importances."}

    importances = clf.feature_importances_

    # The preprocessor may expand feature count (one-hot); use raw feature names where possible
    importance_list = []
    for i, imp in enumerate(importances):
        name = feature_columns[i] if i < len(feature_columns) else f"feature_{i}"
        importance_list.append({"feature": name, "importance": float(imp)})

    importance_list.sort(key=lambda x: x["importance"], reverse=True)
    return {"success": True, "importances": importance_list[:20]}
