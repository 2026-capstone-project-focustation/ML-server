from __future__ import annotations

from pathlib import Path
from typing import Any

from model.sensor_target_v2.inference_sensor_target_v2 import (
    PREDICTION_COL as SENSOR_TARGET_V2_PREDICTION_COL,
    load_model_bundle as load_sensor_target_v2_bundle,
    predict_satisfaction as predict_sensor_target_v2_satisfaction,
)


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "model"
    / "sensor_target_v2"
    / "outputs_sensor_target_v2"
    / "models"
    / "ridge_sensor_target_v2.joblib"
)
PREDICTION_COL = SENSOR_TARGET_V2_PREDICTION_COL


def load_model_bundle() -> dict[str, Any]:
    return load_sensor_target_v2_bundle(MODEL_PATH)


def predict_satisfaction(record: dict[str, Any], clip: bool = True) -> float:
    return predict_sensor_target_v2_satisfaction(record, model_path=MODEL_PATH, clip=clip)
