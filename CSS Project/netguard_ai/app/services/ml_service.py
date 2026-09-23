"""
NetGuard AI — ML Service
Handles active model lookup and model versioning operations.
"""
import json
import logging
from ..models.ml_model_record import MLModelRecord
from ..extensions import db

logger = logging.getLogger(__name__)


def get_active_model() -> MLModelRecord | None:
    """Return the currently active ML model record, or None."""
    return MLModelRecord.query.filter_by(is_active=True).first()


def activate_model(version: str) -> bool:
    """Set a specific model version as active, deactivating all others."""
    try:
        MLModelRecord.query.update({MLModelRecord.is_active: False})
        record = MLModelRecord.query.filter_by(version=version).first()
        if not record:
            return False
        record.is_active = True
        db.session.commit()
        logger.info(f"Model {version} activated.")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to activate model {version}: {e}")
        return False


def register_trained_model(training_result: dict, dataset_name: str, config: dict) -> MLModelRecord:
    """
    Persist a newly trained model's metadata to the database.
    Deactivates the previous active model and activates this one.
    """
    import json

    # Deactivate all existing models
    MLModelRecord.query.update({MLModelRecord.is_active: False})

    record = MLModelRecord(
        version=training_result["version"],
        dataset_name=dataset_name,
        is_active=True,
        target_column=config.get("target_column"),
        n_samples=training_result["n_samples"],
        n_features=training_result["n_features"],
        features_json=json.dumps(training_result.get("feature_columns", config.get("feature_columns", []))),
        classes_json=json.dumps(training_result["classes"]),
        cat_features_json=json.dumps(training_result.get("cat_features", [])),
        num_features_json=json.dumps(training_result.get("num_features", [])),
        accuracy=training_result["accuracy"],
        precision_macro=training_result["precision_macro"],
        recall_macro=training_result["recall_macro"],
        f1_macro=training_result["f1_macro"],
        confusion_matrix_json=json.dumps(training_result["confusion_matrix"]),
        classification_report_json=json.dumps(training_result.get("classification_report", {})),
        model_path=training_result["model_path"],
        preprocessor_path=training_result["preprocessor_path"],
        metadata_path=training_result["metadata_path"],
        n_estimators=config.get("n_estimators", 100),
        max_depth=config.get("max_depth"),
        test_size=config.get("test_size", 0.2),
        random_state=config.get("random_state", 42),
    )
    db.session.add(record)
    db.session.commit()
    logger.info(f"Model {record.version} registered in database.")
    return record


def list_model_versions() -> list:
    """Return all model versions ordered by training date."""
    records = MLModelRecord.query.order_by(MLModelRecord.trained_at.desc()).all()
    return [r.to_dict() for r in records]
