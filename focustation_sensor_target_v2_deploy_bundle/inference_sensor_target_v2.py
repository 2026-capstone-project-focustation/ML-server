"""
FocuStation sensor-aware satisfaction inference.

Recommended model:
    outputs_sensor_target_v2/models/ridge_sensor_target_v2.joblib

Usage:
    python3 inference_sensor_target_v2.py --input sample.json --output predictions.json
    python3 inference_sensor_target_v2.py --input sample.csv --output predictions.csv

Design:
    Android sends existing base inputs + minimal sensor summary primitives.
    This file derives match features, normalized sensor features, interaction features,
    then runs the Ridge sensor-target-v2 model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

DEFAULT_MODEL_PATH = Path("outputs_sensor_target_v2/models/ridge_sensor_target_v2.joblib")
PREDICTION_COL = "predicted_satisfaction_score_sensor_v2"
IDEAL_LUX = 550.0

# Android/server request should contain these primitive sensor summaries.
# All other sensor-derived columns below can be computed on the ML server.
SENSOR_PRIMITIVE_COLUMNS = [
    "noise_mean_db",
    "noise_std_db",
    "noise_max_db",
    "noise_p90_db",
    "noise_spike_count",
    "light_mean_lux",
    "light_std_lux",
    "light_min_lux",
    "light_max_lux",
    "vibration_mean",
    "vibration_std",
    "vibration_max",
    "vibration_p95",
    "vibration_spike_count",
    "measurement_duration_sec",
]

# Optional columns. If Android does not send them, this file uses safe defaults.
OPTIONAL_MEASUREMENT_COLUMNS = {
    "valid_sample_ratio": 0.95,
    "phone_movement_ratio": 0.05,
}

TASK_DEEPWORK_WEIGHT = {
    "deep_study": 1.00,
    "coding": 0.90,
    "report_writing": 0.85,
    "online_class": 0.65,
    "light_reading": 0.45,
    "team_project": 0.25,
    "meeting": 0.20,
}
DEEPWORK_TASKS = {"deep_study", "coding", "report_writing"}
ADJACENT_TIME_PAIRS = {
    frozenset(("early_morning", "morning")),
    frozenset(("morning", "afternoon")),
    frozenset(("afternoon", "evening")),
    frozenset(("evening", "late_night")),
}


def _clip(value: Any, lo: float, hi: float) -> Any:
    return np.minimum(np.maximum(value, lo), hi)


def _sigmoid(value: Any) -> Any:
    return 1 / (1 + np.exp(-value))


def load_model_bundle(model_path: Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict) or "model" not in bundle or "feature_columns" not in bundle:
        raise ValueError("Model bundle must contain `model` and `feature_columns`.")
    return bundle


def load_records(input_path: Path) -> pd.DataFrame:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(input_path, encoding="utf-8-sig")
    if suffix == ".json":
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        return pd.DataFrame(data)
    raise ValueError("Input file must be .csv or .json")


def _require_columns(df: pd.DataFrame, columns: list[str], context: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing {context} columns: {missing}")


def add_base_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive old match features on the ML server when Android does not send them."""
    out = df.copy()
    pairwise_matches = {
        "quiet_match": ("pref_quiet", "place_quiet"),
        "light_match": ("pref_light", "place_light"),
        "crowd_match": ("pref_low_crowd", "place_low_crowd"),
        "privacy_match": ("pref_privacy", "place_low_visual_distraction"),
        "outlet_match": ("pref_outlet", "place_outlet"),
        "thermal_air_match": ("pref_thermal_air", "place_temperature_air"),
        "control_match": ("pref_control", "place_control"),
        "comfort_match": ("pref_comfort", "place_comfort"),
    }
    for target, (left, right) in pairwise_matches.items():
        if target not in out.columns and left in out.columns and right in out.columns:
            out[target] = pd.to_numeric(out[left]) * pd.to_numeric(out[right])

    if "distance_penalty" not in out.columns and {"distance_minutes", "pref_distance"}.issubset(out.columns):
        out["distance_penalty"] = (pd.to_numeric(out["distance_minutes"]) * pd.to_numeric(out["pref_distance"]) / 8).round(1)

    if "deepwork_task_match" not in out.columns and {"pref_deepwork", "task_type"}.issubset(out.columns):
        weights = out["task_type"].map(TASK_DEEPWORK_WEIGHT).fillna(0.50)
        out["deepwork_task_match"] = (pd.to_numeric(out["pref_deepwork"]) * weights).round(1)

    if "task_place_fit_match" not in out.columns and {"place_task_fit", "pref_deepwork", "task_type"}.issubset(out.columns):
        # Deep-work-like tasks use the user's deepwork preference as multiplier.
        # Other collaborative/light tasks use neutral multiplier 3.
        multiplier = np.where(out["task_type"].isin(DEEPWORK_TASKS), pd.to_numeric(out["pref_deepwork"]), 3)
        out["task_place_fit_match"] = pd.to_numeric(out["place_task_fit"]) * multiplier

    if "time_match" not in out.columns and {"general_time_slot", "time_slot"}.issubset(out.columns):
        def calc_time_match(row: pd.Series) -> float:
            preferred = row["general_time_slot"]
            actual = row["time_slot"]
            if preferred == actual:
                return 1.0
            if frozenset((preferred, actual)) in ADJACENT_TIME_PAIRS:
                return 0.5
            return 0.0
        out["time_match"] = out.apply(calc_time_match, axis=1)

    return out


def add_sensor_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive sensor ratios, normalized risks, quality score, and interaction features."""
    out = df.copy()
    _require_columns(out, SENSOR_PRIMITIVE_COLUMNS, "sensor primitive")

    for col in SENSOR_PRIMITIVE_COLUMNS:
        out[col] = pd.to_numeric(out[col])
    for col, default in OPTIONAL_MEASUREMENT_COLUMNS.items():
        if col not in out.columns:
            out[col] = default
        out[col] = pd.to_numeric(out[col])

    if "quiet_ratio" not in out.columns:
        out["quiet_ratio"] = _clip(
            1 / (1 + np.exp((out["noise_mean_db"] - 48) / 5)) - out["noise_spike_count"] * 0.015,
            0.02,
            0.98,
        )

    if "light_range_lux" not in out.columns:
        out["light_range_lux"] = out["light_max_lux"] - out["light_min_lux"]
    if "too_dark_ratio" not in out.columns:
        out["too_dark_ratio"] = _clip(
            1 / (1 + np.exp((out["light_mean_lux"] - 250) / 90)) + (out["light_std_lux"] > 250).astype(float) * 0.04,
            0,
            0.95,
        )
    if "too_bright_ratio" not in out.columns:
        out["too_bright_ratio"] = _clip(
            1 / (1 + np.exp((900 - out["light_mean_lux"]) / 180)) + (out["light_std_lux"] > 300).astype(float) * 0.05,
            0,
            0.95,
        )

    if "stillness_ratio" not in out.columns:
        out["stillness_ratio"] = _clip(
            1 / (1 + np.exp((out["vibration_mean"] - 0.055) / 0.018)) - out["vibration_spike_count"] * 0.015,
            0.01,
            0.99,
        )

    if "sample_count" not in out.columns:
        out["sample_count"] = np.rint(out["measurement_duration_sec"] * out["valid_sample_ratio"]).astype(int)

    if "sensor_quality_score" not in out.columns:
        out["sensor_quality_score"] = _clip(
            100 * out["valid_sample_ratio"]
            - 18 * out["phone_movement_ratio"]
            + (out["measurement_duration_sec"] - 600) / 1200 * 3,
            70,
            100,
        )

    out["noise_level_norm"] = _clip((out["noise_p90_db"] - 38) / 42 * 5, 0, 5)
    noise_spike_norm = _clip(out["noise_spike_count"] / 12 * 5, 0, 5)
    out["light_deviation_norm"] = _clip(
        np.abs(np.log((out["light_mean_lux"] + 1) / IDEAL_LUX)) * 2.0
        + (out["light_std_lux"] / 500)
        + out["too_dark_ratio"] * 1.5
        + out["too_bright_ratio"] * 1.2,
        0,
        5,
    )
    out["vibration_level_norm"] = _clip((out["vibration_p95"] - 0.03) / 0.27 * 5, 0, 5)
    vibration_spike_norm = _clip(out["vibration_spike_count"] / 10 * 5, 0, 5)

    _require_columns(out, ["pref_quiet", "pref_light", "pref_comfort"], "preference")
    out["pref_quiet_x_noise"] = pd.to_numeric(out["pref_quiet"]) * out["noise_level_norm"]
    out["pref_quiet_x_noise_p90"] = pd.to_numeric(out["pref_quiet"]) * _clip((out["noise_p90_db"] - 35) / 45 * 5, 0, 5)
    out["pref_light_x_light_deviation"] = pd.to_numeric(out["pref_light"]) * out["light_deviation_norm"]
    out["pref_comfort_x_vibration"] = pd.to_numeric(out["pref_comfort"]) * out["vibration_level_norm"]
    out["pref_comfort_x_vibration_spike"] = pd.to_numeric(out["pref_comfort"]) * vibration_spike_norm

    return out


def preprocess_for_model(df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    out = add_base_derived_features(df)
    out = add_sensor_derived_features(out)
    missing = [col for col in feature_columns if col not in out.columns]
    if missing:
        raise ValueError(f"Missing model feature columns after preprocessing: {missing}")
    return out


def predict_dataframe(
    df: pd.DataFrame,
    model_path: Path = DEFAULT_MODEL_PATH,
    clip: bool = True,
) -> pd.DataFrame:
    bundle = load_model_bundle(model_path)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    processed = preprocess_for_model(df, feature_columns)
    predictions = model.predict(processed[feature_columns])
    if clip:
        predictions = predictions.clip(0, 100)
    result = processed.copy()
    result[PREDICTION_COL] = predictions
    return result


def predict_satisfaction(record: dict[str, Any], model_path: Path = DEFAULT_MODEL_PATH, clip: bool = True) -> float:
    result = predict_dataframe(pd.DataFrame([record]), model_path=model_path, clip=clip)
    return float(result.loc[0, PREDICTION_COL])


def save_predictions(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return
    if suffix == ".json":
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        return
    raise ValueError("Output file must be .csv or .json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FocuStation sensor-target-v2 inference.")
    parser.add_argument("--input", required=True, type=Path, help="Input .csv or .json file")
    parser.add_argument("--output", required=True, type=Path, help="Output .csv or .json file")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, type=Path, help=f"Model path. Default: {DEFAULT_MODEL_PATH}")
    parser.add_argument("--no-clip", action="store_true", help="Do not clip predictions to 0-100")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_df = load_records(args.input)
    output_df = predict_dataframe(input_df, model_path=args.model, clip=not args.no_clip)
    save_predictions(output_df, args.output)
    print(f"Saved predictions to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
