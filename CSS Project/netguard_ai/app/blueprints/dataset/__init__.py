"""
NetGuard AI — Dataset & Training API Blueprint
POST /api/dataset/upload
POST /api/dataset/inspect
POST /api/dataset/train
"""
import os
import json
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from ...ml.trainer import inspect_dataset, validate_training_request, train_model
from ...services.ml_service import register_trained_model

dataset_bp = Blueprint("dataset", __name__)

ALLOWED_EXTENSIONS = {"csv"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@dataset_bp.route("/dataset/upload", methods=["POST"])
def upload_dataset():
    """
    Upload a CSV dataset file.
    Returns: file metadata and basic inspection results.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": {"code": "NO_FILE", "message": "No file provided."}}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": {"code": "EMPTY_FILENAME", "message": "No file selected."}}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only CSV files are supported."}
        }), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(upload_folder, unique_name)

    try:
        file.save(file_path)
        current_app.logger.info(f"Dataset uploaded: {unique_name}")
    except Exception as e:
        return jsonify({"success": False, "error": {"code": "SAVE_FAILED", "message": str(e)}}), 500

    # Inspect the file
    inspection = inspect_dataset(file_path)

    if "error" in inspection:
        os.remove(file_path)
        return jsonify({
            "success": False,
            "error": {"code": "INSPECTION_FAILED", "message": inspection["error"]}
        }), 422

    return jsonify({
        "success": True,
        "data": {
            "file_path": file_path,
            "original_name": filename,
            "saved_as": unique_name,
            "inspection": inspection,
        }
    })


@dataset_bp.route("/dataset/inspect", methods=["POST"])
def inspect_file():
    """
    Inspect an already-uploaded file path.
    Body: {"file_path": "..."}
    """
    data = request.get_json(silent=True) or {}
    file_path = data.get("file_path")

    if not file_path or not os.path.isfile(file_path):
        return jsonify({"success": False, "error": {"code": "INVALID_PATH", "message": "File not found."}}), 400

    # Security: ensure path is within uploads folder
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": "Invalid file path."}}), 403

    inspection = inspect_dataset(file_path)
    return jsonify({"success": True, "data": inspection})


@dataset_bp.route("/dataset/train", methods=["POST"])
def train():
    """
    Train the Random Forest model on an uploaded dataset.
    Body:
    {
        "file_path": str,
        "target_column": str,
        "feature_columns": list[str],   # optional — if empty, all non-target columns used
        "n_estimators": int,            # optional, default 100
        "max_depth": int | null,        # optional
        "test_size": float,             # optional, default 0.2
        "random_state": int             # optional, default 42
    }
    """
    data = request.get_json(silent=True) or {}

    file_path = data.get("file_path")
    target_column = data.get("target_column")
    feature_columns = data.get("feature_columns", [])

    # Validate required fields
    if not file_path:
        return jsonify({"success": False, "error": {"code": "MISSING_FILE", "message": "file_path is required."}}), 400
    if not target_column:
        return jsonify({"success": False, "error": {"code": "MISSING_TARGET", "message": "target_column is required."}}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": "Invalid file path."}}), 403

    if not os.path.isfile(file_path):
        return jsonify({"success": False, "error": {"code": "FILE_NOT_FOUND", "message": "Uploaded file not found."}}), 400

    # Inspect to auto-fill feature columns if not provided
    inspection = inspect_dataset(file_path)
    if "error" in inspection:
        return jsonify({"success": False, "error": {"code": "DATASET_ERROR", "message": inspection["error"]}}), 422

    if not feature_columns:
        feature_columns = [c for c in inspection["column_names"] if c != target_column]

    # Validate the request
    validation = validate_training_request(inspection, target_column, feature_columns)
    if not validation["valid"]:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_FAILED", "message": "; ".join(validation["errors"])},
            "warnings": validation["warnings"],
        }), 422

    # Training configuration
    config = {
        "target_column": target_column,
        "feature_columns": feature_columns,
        "n_estimators": int(data.get("n_estimators", 100)),
        "max_depth": data.get("max_depth"),
        "test_size": float(data.get("test_size", 0.2)),
        "random_state": int(data.get("random_state", 42)),
    }

    models_store = current_app.config["MODELS_STORE"]
    dataset_name = os.path.basename(file_path)

    current_app.logger.info(f"Training started: dataset={dataset_name}, target={target_column}")

    result = train_model(
        file_path=file_path,
        target_column=target_column,
        feature_columns=feature_columns,
        models_store=models_store,
        **{k: v for k, v in config.items() if k not in ("target_column", "feature_columns")},
    )

    if not result["success"]:
        current_app.logger.error(f"Training failed: {result.get('error')}")
        return jsonify({
            "success": False,
            "error": {"code": "TRAINING_FAILED", "message": result.get("error", "Training failed.")},
        }), 500

    # Register in DB and activate
    model_record = register_trained_model(result, dataset_name, config)
    current_app.logger.info(f"Training complete: version={result['version']}, accuracy={result['accuracy']:.4f}")

    return jsonify({
        "success": True,
        "message": f"Model {result['version']} trained and activated successfully.",
        "data": {
            "version": result["version"],
            "accuracy": result["accuracy"],
            "precision_macro": result["precision_macro"],
            "recall_macro": result["recall_macro"],
            "f1_macro": result["f1_macro"],
            "classes": result["classes"],
            "n_samples": result["n_samples"],
            "n_features": result["n_features"],
            "warnings": validation.get("warnings", []),
        }
    })
