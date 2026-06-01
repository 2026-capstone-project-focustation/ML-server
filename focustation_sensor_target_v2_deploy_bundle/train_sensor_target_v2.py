"""
Train FocuStation sensor-aware satisfaction models.

Run from the folder containing focustation_synthetic_3000_sensor_target_v2.csv:
    python3 train_sensor_target_v2.py

Main target:
    satisfaction_score_sensor_v2

Recommended model bundle:
    outputs_sensor_target_v2/models/ridge_sensor_target_v2.joblib
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA_PATH = Path("focustation_synthetic_3000_sensor_target_v2.csv")
OUTPUT_DIR = Path("outputs_sensor_target_v2")
MODELS_DIR = OUTPUT_DIR / "models"
METRICS_DIR = OUTPUT_DIR / "metrics"
TARGET_COL = "satisfaction_score_sensor_v2"
SPLIT_COL = "split"

EXCLUDE_COLUMNS = [
    "interaction_id", "user_id", "place_id", "place_name", "source", "split",
    "satisfaction_score", "satisfaction_binary", "satisfaction_score_sensor_v2",
    "sensor_environment_score", "sensor_penalty_total", "sensor_adjustment",
]
SENSOR_MEAN_COLUMNS = ["noise_mean_db", "light_mean_lux", "vibration_mean"]
SENSOR_STAT_COLUMNS = [
    "noise_mean_db", "noise_std_db", "noise_max_db", "noise_p90_db", "noise_spike_count", "quiet_ratio",
    "light_mean_lux", "light_std_lux", "light_min_lux", "light_max_lux", "light_range_lux", "too_dark_ratio", "too_bright_ratio",
    "vibration_mean", "vibration_std", "vibration_max", "vibration_p95", "vibration_spike_count", "stillness_ratio",
    "measurement_duration_sec", "sample_count", "valid_sample_ratio", "phone_movement_ratio",
    "noise_level_norm", "light_deviation_norm", "vibration_level_norm", "sensor_quality_score",
]
INTERACTION_COLUMNS = [
    "pref_quiet_x_noise", "pref_quiet_x_noise_p90", "pref_light_x_light_deviation",
    "pref_comfort_x_vibration", "pref_comfort_x_vibration_spike",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    required = {TARGET_COL, SPLIT_COL}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def base_feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = set(EXCLUDE_COLUMNS)
    return [
        col for col in df.columns
        if col not in excluded and col not in SENSOR_STAT_COLUMNS and col not in INTERACTION_COLUMNS
    ]


def build_preprocessor(X_train: pd.DataFrame) -> ColumnTransformer:
    numeric_features = X_train.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = X_train.select_dtypes(exclude=["number"]).columns.tolist()
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]), categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_model(X_train: pd.DataFrame, kind: str) -> Pipeline:
    estimator = LinearRegression() if kind == "linear_regression" else Ridge(alpha=1.0)
    return Pipeline([("preprocessor", build_preprocessor(X_train)), ("model", estimator)])


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(y_true, y_pred)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "MSE": float(mse),
        "RMSE": float(np.sqrt(mse)),
        "R2": float(r2_score(y_true, y_pred)),
    }


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    base_cols = base_feature_columns(df)
    feature_sets = {
        "A_base_only_v2_target": base_cols,
        "B_base_plus_sensor_means_v2_target": base_cols + SENSOR_MEAN_COLUMNS,
        "C_base_plus_sensor_stats_v2_target": base_cols + SENSOR_STAT_COLUMNS,
        "D_base_plus_sensor_stats_interactions_v2_target": base_cols + SENSOR_STAT_COLUMNS + INTERACTION_COLUMNS,
    }
    splits = {name: df[df[SPLIT_COL] == name].copy() for name in ["train", "valid", "test"]}
    if any(split_df.empty for split_df in splits.values()):
        raise ValueError("Missing train/valid/test split rows")

    all_metrics: dict[str, Any] = {"target": TARGET_COL, "models": {}}
    for model_kind in ["linear_regression", "ridge"]:
        all_metrics["models"][model_kind] = {}
        for experiment_name, feature_columns in feature_sets.items():
            X_train = splits["train"][feature_columns]
            y_train = splits["train"][TARGET_COL]
            model = build_model(X_train, model_kind)
            model.fit(X_train, y_train)

            experiment_metrics: dict[str, Any] = {
                "feature_count": len(feature_columns),
                "feature_columns": feature_columns,
                "splits": {},
            }
            for split_name, split_df in splits.items():
                X_split = split_df[feature_columns]
                y_split = split_df[TARGET_COL]
                experiment_metrics["splits"][split_name] = regression_metrics(y_split, model.predict(X_split))
            all_metrics["models"][model_kind][experiment_name] = experiment_metrics

            if experiment_name == "D_base_plus_sensor_stats_interactions_v2_target":
                bundle = {
                    "model": model,
                    "model_name": f"{model_kind}_sensor_target_v2",
                    "target_column": TARGET_COL,
                    "feature_columns": feature_columns,
                }
                joblib.dump(bundle, MODELS_DIR / f"{model_kind}_sensor_target_v2.joblib")

    metrics_path = METRICS_DIR / "sensor_target_v2_metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2, default=json_default)
    print(f"Saved metrics to: {metrics_path.resolve()}")
    print(json.dumps(all_metrics["models"]["ridge"]["D_base_plus_sensor_stats_interactions_v2_target"]["splits"]["test"], indent=2))


if __name__ == "__main__":
    main()
