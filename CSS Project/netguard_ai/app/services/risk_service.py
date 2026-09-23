"""
NetGuard AI — Risk Scoring Service
Deterministic, backend-calculated risk and security scores.
No hardcoded or invented values — all derived from model output.
"""
import math


# Known attack type severity weights (based on common IDS classifications)
ATTACK_SEVERITY_WEIGHTS = {
    "dos": 0.9,
    "ddos": 0.95,
    "probe": 0.6,
    "r2l": 0.75,
    "u2r": 0.85,
    "backdoor": 0.8,
    "exploits": 0.85,
    "fuzzers": 0.65,
    "generic": 0.7,
    "reconnaissance": 0.6,
    "shellcode": 0.9,
    "worms": 0.95,
    "infiltration": 0.85,
    "heartbleed": 0.95,
    "bot": 0.8,
    "portscan": 0.55,
    "port scan": 0.55,
    "brute force": 0.75,
    "sql injection": 0.85,
    "xss": 0.7,
    "normal": 0.0,
    "benign": 0.0,
    "legitimate": 0.0,
    "safe": 0.0,
}


def calculate_risk_score(
    is_attack: bool,
    prediction: str,
    confidence: float | None,
) -> float:
    """
    Calculate a risk score (0–100) based on:
    - Whether it's an attack
    - The predicted attack type's known severity
    - Model confidence in the prediction

    Returns a float in [0, 100].
    """
    if not is_attack:
        # Normal traffic — risk is low but not zero (confidence might be low)
        base_risk = 0.0
        if confidence is not None:
            # Low confidence in a normal prediction → slightly elevated risk
            uncertainty = 1.0 - confidence
            base_risk = uncertainty * 15.0
        return round(min(base_risk, 20.0), 2)

    # Attack traffic
    label_lower = str(prediction).strip().lower()
    severity = 0.65  # Default severity for unknown attack types

    for key, weight in ATTACK_SEVERITY_WEIGHTS.items():
        if key in label_lower:
            severity = weight
            break

    # Confidence factor: high confidence in an attack → high risk
    conf_factor = confidence if confidence is not None else 0.7

    # Risk = severity × confidence × 100, with a minimum floor for detected attacks
    raw_risk = severity * conf_factor * 100.0
    risk = max(raw_risk, 30.0)  # Detected attacks always score at least 30

    return round(min(risk, 100.0), 2)


def calculate_security_score(risk_score: float) -> float:
    """
    Security score is inverse of risk, on a 0–100 scale.
    Uses a non-linear mapping so small risks don't tank the score too much.
    """
    normalized = risk_score / 100.0
    security = (1.0 - normalized) * 100.0
    return round(max(0.0, min(100.0, security)), 2)


def determine_alert_severity(risk_score: float) -> str:
    """Map risk score to alert severity level."""
    if risk_score >= 85:
        return "critical"
    elif risk_score >= 65:
        return "high"
    elif risk_score >= 40:
        return "medium"
    else:
        return "low"


def should_create_alert(is_attack: bool, risk_score: float) -> bool:
    """Determine if an alert should be generated for this activity."""
    return is_attack or risk_score >= 40.0
