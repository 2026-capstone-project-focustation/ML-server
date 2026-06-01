"""
Run Linear Regression inference for FocuStation satisfaction prediction.

Examples:
    python3 model/linear_regression_v1/inference_linear_regression.py \
        --input model/linear_regression_v1/sample_input.json \
        --output predictions.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "outputs_linear_regression/models/linear_regression.joblib"
PREDICTION_COL = "predicted_satisfaction_score"


def load_model_bundle(model_path: Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            "Run `python3 export_linear_regression_model.py` first."
        )

    loaded = joblib.load(model_path)
    if isinstance(loaded, dict) and "model" in loaded and "feature_columns" in loaded:
        return loaded

    feature_columns = getattr(loaded, "feature_columns", None)
    if feature_columns is None:
        raise ValueError(
            "Model bundle must contain `model` and `feature_columns`. "
            "Re-export the model with `export_linear_regression_model.py`."
        )
    return {"model": loaded, "feature_columns": feature_columns}


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


def validate_input(df: pd.DataFrame, feature_columns: list[str]) -> None:
    missing_columns = [col for col in feature_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing feature columns: {missing_columns}")


def predict_dataframe(
    df: pd.DataFrame,
    model_path: Path = DEFAULT_MODEL_PATH,
    clip: bool = True,
) -> pd.DataFrame:
    bundle = load_model_bundle(model_path)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    validate_input(df, feature_columns)
    predictions = model.predict(df[feature_columns])
    if clip:
        predictions = predictions.clip(0, 100)

    result = df.copy()
    result[PREDICTION_COL] = predictions
    return result


def predict_satisfaction(
    record: dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
    clip: bool = True,
) -> float:
    result = predict_dataframe(pd.DataFrame([record]), model_path=model_path, clip=clip)
    return float(result.loc[0, PREDICTION_COL])


def save_predictions(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return
    if suffix == ".json":
        records = df.to_dict(orient="records")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return
    raise ValueError("Output file must be .csv or .json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run FocuStation Linear Regression satisfaction inference."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input .csv or .json file")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output .csv or .json file",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_PATH,
        type=Path,
        help=f"Model bundle path. Default: {DEFAULT_MODEL_PATH}",
    )
    parser.add_argument(
        "--no-clip",
        action="store_true",
        help="Do not clip predictions to the 0-100 score range.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_df = load_records(args.input)
    output_df = predict_dataframe(input_df, model_path=args.model, clip=not args.no_clip)
    save_predictions(output_df, args.output)
    print(f"Saved predictions to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
