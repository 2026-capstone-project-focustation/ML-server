from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "model"
    / "outputs_linear_regression"
    / "models"
    / "linear_regression.joblib"
)
PREDICTION_COL = "predicted_satisfaction_score"


def _validate_model(model: Any) -> Any:
    predict = getattr(model, "predict", None)
    if not callable(predict):
        raise ValueError("Model bundle validation failed: `model.predict` must be callable.")
    return model


def _validate_feature_columns(feature_columns: Any) -> list[str]:
    if isinstance(feature_columns, (str, bytes)) or not isinstance(feature_columns, Iterable):
        raise ValueError(
            "Model bundle validation failed: `feature_columns` must be a non-empty iterable of strings."
        )

    columns = list(feature_columns)
    if not columns:
        raise ValueError(
            "Model bundle validation failed: `feature_columns` must not be empty."
        )

    if not all(isinstance(column, str) for column in columns):
        raise ValueError(
            "Model bundle validation failed: every `feature_columns` item must be a string."
        )

    return columns


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}. "
            "Export or copy the linear regression bundle before starting the server."
        )

    loaded = joblib.load(MODEL_PATH)
    if isinstance(loaded, dict):
        if "model" not in loaded:
            raise ValueError("Model bundle validation failed: missing `model` key.")
        if "feature_columns" not in loaded:
            raise ValueError("Model bundle validation failed: missing `feature_columns` key.")

        return {
            "model": _validate_model(loaded["model"]),
            "feature_columns": _validate_feature_columns(loaded["feature_columns"]),
        }

    feature_columns = getattr(loaded, "feature_columns", None)
    if feature_columns is None:
        raise ValueError(
            "Model bundle must contain `model` and `feature_columns`. "
            "Re-export the model bundle."
        )

    return {
        "model": _validate_model(loaded),
        "feature_columns": _validate_feature_columns(feature_columns),
    }


def predict_satisfaction(record: dict[str, Any], clip: bool = True) -> float:
    bundle = load_model_bundle()
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    df = pd.DataFrame([record])

    missing_columns = [col for col in feature_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing feature columns: {missing_columns}")

    predictions = model.predict(df[feature_columns])
    if clip:
        predictions = predictions.clip(0, 100)

    return float(predictions[0])
