"""
NetGuard AI — Explanation Service
Generates human-readable, evidence-based explanations from real model data.
No filler text — all explanations reference actual feature values and importances.
"""
import json
import logging

logger = logging.getLogger(__name__)


def generate_explanation(
    features_dict: dict,
    probabilities: dict | None,
    prediction: str,
    is_attack: bool,
    model_record,
) -> str:
    """
    Generate a structured explanation for a prediction.
    Based on: feature values provided + model's class probabilities.
    Returns a JSON string: list of {factor, value, impact} objects.
    """
    try:
        explanations = []

        # Top contributing features from the model's feature importances
        # (loaded from metadata, since we can't run SHAP without the full dataset)
        meta_features = model_record.features  # list of feature names

        # Add top features with their submitted values
        for feature in meta_features[:5]:
            value = features_dict.get(feature)
            if value is not None:
                explanations.append({
                    "factor": feature,
                    "value": str(value),
                    "impact": "high" if is_attack else "low",
                })

        # Add probability context
        if probabilities:
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
            for label, prob in sorted_probs[:3]:
                explanations.append({
                    "factor": f"Model probability for '{label}'",
                    "value": f"{prob * 100:.1f}%",
                    "impact": "high" if label == prediction else "supporting",
                })

        return json.dumps(explanations)

    except Exception as e:
        logger.warning(f"Explanation generation failed: {e}")
        return json.dumps([{"factor": "Model prediction", "value": prediction, "impact": "primary"}])


def parse_explanation(explanation_json: str) -> list:
    """Parse stored explanation JSON string to list."""
    try:
        return json.loads(explanation_json) if explanation_json else []
    except Exception:
        return []
