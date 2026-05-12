"""
Export a Linear Regression inference bundle for FocuStation satisfaction prediction.

Run:
    python3 export_linear_regression_model.py
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
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_PATH = Path("focustation_synthetic_3000.csv")
OUTPUT_DIR = Path("outputs_linear_regression")
MODELS_DIR = OUTPUT_DIR / "models"
METRICS_DIR = OUTPUT_DIR / "metrics"
MODEL_PATH = MODELS_DIR / "linear_regression.joblib"
METRICS_PATH = METRICS_DIR / "linear_regression_metrics.json"

TARGET_COL = "satisfaction_score"
SPLIT_COL = "split"
EXCLUDE_COLUMNS = [
    "interaction_id",
    "user_id",
    "place_id",
    "place_name",
    "source",
    "split",
    "satisfaction_score",
    "satisfaction_binary",
]


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    required_columns = {TARGET_COL, SPLIT_COL}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in EXCLUDE_COLUMNS]


def build_preprocessor(X_train: pd.DataFrame) -> ColumnTransformer:
    numeric_features = X_train.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = X_train.select_dtypes(exclude=["number"]).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_model(X_train: pd.DataFrame) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train)),
            ("model", LinearRegression()),
        ]
    )


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

    df = load_data(DATA_PATH)
    feature_columns = get_feature_columns(df)

    splits = {
        split_name: df[df[SPLIT_COL] == split_name].copy()
        for split_name in ["train", "valid", "test"]
    }
    missing_splits = [name for name, split_df in splits.items() if split_df.empty]
    if missing_splits:
        raise ValueError(f"Missing split rows: {missing_splits}")

    X_train = splits["train"][feature_columns]
    y_train = splits["train"][TARGET_COL]

    model = build_model(X_train)
    model.fit(X_train, y_train)

    metrics = {
        "model": "linear_regression",
        "target": TARGET_COL,
        "feature_columns": feature_columns,
        "splits": {},
    }
    for split_name, split_df in splits.items():
        X_split = split_df[feature_columns]
        y_split = split_df[TARGET_COL]
        metrics["splits"][split_name] = regression_metrics(y_split, model.predict(X_split))

    bundle = {
        "model": model,
        "model_name": "linear_regression",
        "target_column": TARGET_COL,
        "feature_columns": feature_columns,
    }
    joblib.dump(bundle, MODEL_PATH)

    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, default=json_default)

    print(f"Saved model bundle to: {MODEL_PATH.resolve()}")
    print(f"Saved metrics to: {METRICS_PATH.resolve()}")
    print(json.dumps(metrics["splits"]["test"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
