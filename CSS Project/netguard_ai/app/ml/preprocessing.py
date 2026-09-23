"""
NetGuard AI — ML Preprocessing Pipeline
Fit only on training data; reuse exact same pipeline for prediction.
"""
import joblib
import logging
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


def build_preprocessor(cat_features: list, num_features: list) -> ColumnTransformer:
    """
    Build a ColumnTransformer pipeline for numerical and categorical features.
    This must be fit ONLY on training data.
    """
    transformers = []

    if num_features:
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("num", num_pipeline, num_features))

    if cat_features:
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("cat", cat_pipeline, cat_features))

    if not transformers:
        raise ValueError("No features provided to preprocessor.")

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return preprocessor


def save_preprocessor(preprocessor, path: str):
    joblib.dump(preprocessor, path)
    logger.info(f"Preprocessor saved to {path}")


def load_preprocessor(path: str):
    preprocessor = joblib.load(path)
    logger.info(f"Preprocessor loaded from {path}")
    return preprocessor


def encode_labels(y_series):
    """
    Encode string class labels to integers.
    Returns (encoded_array, label_encoder).
    """
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_series.astype(str))
    return y_encoded, le


def save_label_encoder(le, path: str):
    joblib.dump(le, path)


def load_label_encoder(path: str):
    return joblib.load(path)
