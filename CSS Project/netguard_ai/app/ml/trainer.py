"""
NetGuard AI — ML Trainer
Handles dataset inspection, training, evaluation, and model persistence.
No data leakage: split first, fit preprocessing only on training data.
"""
import json
import logging
import os
import uuid
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from .preprocessing import (
    build_preprocessor,
    encode_labels,
    save_label_encoder,
    save_preprocessor,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────── Dataset Inspection ──────────────────────────

def inspect_dataset(file_path: str) -> dict:
    """
    Load and inspect a CSV dataset.
    Returns column names, dtypes, sample counts, missing value counts, etc.
    """
    try:
        df = pd.read_csv(file_path, nrows=50000)  # Cap for inspection
    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}

    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_missing = int(df[col].isnull().sum())
        n_unique = int(df[col].nunique())
        sample_values = df[col].dropna().head(5).tolist()
        columns.append({
            "name": col,
            "dtype": dtype,
            "n_missing": n_missing,
            "n_unique": n_unique,
            "sample_values": [str(v) for v in sample_values],
            "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
        })

    return {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": columns,
        "column_names": df.columns.tolist(),
        "file_size_bytes": os.path.getsize(file_path),
    }


def validate_training_request(inspection: dict, target_column: str, feature_columns: list) -> dict:
    """
    Validate that the dataset and target/feature columns are compatible for training.
    Returns {"valid": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []

    if "error" in inspection:
        return {"valid": False, "errors": [inspection["error"]], "warnings": []}

    col_names = inspection.get("column_names", [])

    if target_column not in col_names:
        errors.append(f"Target column '{target_column}' not found in dataset.")

    missing_features = [f for f in feature_columns if f not in col_names]
    if missing_features:
        errors.append(f"Feature columns not found: {missing_features}")

    if target_column in feature_columns:
        errors.append("Target column must not be included in feature columns.")

    if inspection.get("n_rows", 0) < 20:
        errors.append("Dataset too small (need at least 20 rows).")

    if inspection.get("n_rows", 0) < 200:
        warnings.append("Dataset is small; model performance may be limited.")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


# ─────────────────────────────── Training ────────────────────────────────────

def train_model(
    file_path: str,
    target_column: str,
    feature_columns: list,
    models_store: str,
    n_estimators: int = 100,
    max_depth=None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Full training pipeline:
    1. Load dataset
    2. Split FIRST (no leakage)
    3. Fit preprocessor on train only
    4. Train Random Forest
    5. Evaluate on test set
    6. Save all artifacts
    Returns training result dict.
    """
    logger.info(f"Starting training on {file_path}, target={target_column}")

    # 1. Load dataset
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return {"success": False, "error": f"Failed to read dataset: {str(e)}"}

    # 2. Validate columns exist
    missing = [c for c in feature_columns + [target_column] if c not in df.columns]
    if missing:
        return {"success": False, "error": f"Columns not found: {missing}"}

    df = df[feature_columns + [target_column]].dropna(subset=[target_column])
    X = df[feature_columns]
    y = df[target_column]

    if len(df) < 20:
        return {"success": False, "error": "Not enough samples after cleaning."}

    # Identify numerical and categorical features
    num_features = [c for c in feature_columns if pd.api.types.is_numeric_dtype(X[c])]
    cat_features = [c for c in feature_columns if c not in num_features]

    # 3. Split FIRST — critical for no data leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=None
    )

    # 4. Build and fit preprocessor on train only
    preprocessor = build_preprocessor(cat_features, num_features)
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Encode labels
    y_train_enc, le = encode_labels(y_train)
    y_test_enc = le.transform(y_test.astype(str))

    # 5. Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )
    clf.fit(X_train_proc, y_train_enc)

    # 6. Evaluate
    y_pred = clf.predict(X_test_proc)
    acc = float(accuracy_score(y_test_enc, y_pred))
    prec = float(precision_score(y_test_enc, y_pred, average="macro", zero_division=0))
    rec = float(recall_score(y_test_enc, y_pred, average="macro", zero_division=0))
    f1 = float(f1_score(y_test_enc, y_pred, average="macro", zero_division=0))
    cm = confusion_matrix(y_test_enc, y_pred).tolist()
    cr = classification_report(
        y_test_enc, y_pred, target_names=le.classes_, output_dict=True, zero_division=0
    )

    # 7. Save artifacts
    version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    model_dir = os.path.join(models_store, version)
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "model.joblib")
    preprocessor_path = os.path.join(model_dir, "preprocessor.joblib")
    le_path = os.path.join(model_dir, "label_encoder.joblib")
    metadata_path = os.path.join(model_dir, "metadata.json")

    joblib.dump(clf, model_path)
    save_preprocessor(preprocessor, preprocessor_path)
    save_label_encoder(le, le_path)

    metadata = {
        "version": version,
        "dataset_name": os.path.basename(file_path),
        "target_column": target_column,
        "feature_columns": feature_columns,
        "num_features": num_features,
        "cat_features": cat_features,
        "classes": le.classes_.tolist(),
        "n_samples": len(df),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_features": len(feature_columns),
        "accuracy": acc,
        "precision_macro": prec,
        "recall_macro": rec,
        "f1_macro": f1,
        "confusion_matrix": cm,
        "classification_report": cr,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "test_size": test_size,
        "random_state": random_state,
        "trained_at": datetime.utcnow().isoformat(),
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
        "label_encoder_path": le_path,
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model {version} trained: acc={acc:.4f}, f1={f1:.4f}")

    return {
        "success": True,
        "version": version,
        "accuracy": acc,
        "precision_macro": prec,
        "recall_macro": rec,
        "f1_macro": f1,
        "confusion_matrix": cm,
        "classification_report": cr,
        "classes": le.classes_.tolist(),
        "n_samples": len(df),
        "n_features": len(feature_columns),
        "num_features": num_features,
        "cat_features": cat_features,
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
        "label_encoder_path": le_path,
        "metadata_path": metadata_path,
    }
