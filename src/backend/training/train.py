"""Train and evaluate baseline stock-price regressors."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import MarketObservation, Symbol
from ..features import FEATURE_COLUMNS, TARGET_COLUMN, build_feature_frame

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"


@dataclass(frozen=True)
class TrainingResult:
    """Summary of a completed training run."""

    symbol: str
    best_model: str
    model_path: Path
    metrics: dict[str, dict[str, float]]
    sample_count: int


def train_symbol(
    db: Session,
    symbol: str,
    model_dir: Path = DEFAULT_MODEL_DIR,
    test_size: float = 0.2,
    horizon: int = 1,
    min_samples: int = 20,
) -> TrainingResult:
    """Train baseline models for a symbol using a chronological split."""

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    ticker = symbol.strip().upper()
    if not ticker:
        raise ValueError("symbol must not be empty")

    # Load one company's observations in chronological order.
    observations = db.scalars(
        select(MarketObservation)
        .join(Symbol)
        .where(Symbol.ticker == ticker)
        .order_by(MarketObservation.timestamp)
    ).all()
    if not observations:
        raise ValueError(f"No observations found for {ticker}")

    feature_frame = build_feature_frame(observations, horizon=horizon)
    if len(feature_frame) < min_samples:
        raise ValueError(
            f"Not enough training samples for {ticker}: "
            f"need {min_samples}, found {len(feature_frame)}"
        )

    # Keep later observations isolated for an honest test.
    split_index = int(len(feature_frame) * (1 - test_size))
    if split_index < 1 or split_index >= len(feature_frame):
        raise ValueError("test_size leaves no training or test samples")

    train_frame = feature_frame.iloc[:split_index]
    test_frame = feature_frame.iloc[split_index:]
    train_features = train_frame[FEATURE_COLUMNS]
    test_features = test_frame[FEATURE_COLUMNS]
    train_target = train_frame[TARGET_COLUMN]
    test_target = test_frame[TARGET_COLUMN]

    # Compare simple baseline regressors.
    candidates = {
        "linear_regression": Pipeline(
            [("scaler", StandardScaler()), ("model", LinearRegression())]
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=200, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(random_state=42),
    }
    # Fit each candidate and score its test predictions.
    metrics: dict[str, dict[str, float]] = {}
    fitted_models = {}
    for name, model in candidates.items():
        model.fit(train_features, train_target)
        predictions = model.predict(test_features)
        fitted_models[name] = model
        metrics[name] = _metrics(test_target, predictions)

    # Compare against predicting the previous close unchanged.
    naive_predictions = test_frame["close_lag_1"]
    metrics["naive_previous_close"] = _metrics(test_target, naive_predictions)
    best_model = min(
        candidates,
        key=lambda name: (metrics[name]["rmse"], metrics[name]["mae"]),
    )

    # Save the winner and its metadata for the API.
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{ticker}_{best_model}.joblib"
    joblib.dump(fitted_models[best_model], model_path)
    metadata = {
        "symbol": ticker,
        "best_model": best_model,
        "model_file": model_path.name,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "horizon": horizon,
        "sample_count": len(feature_frame),
        "train_samples": len(train_frame),
        "test_samples": len(test_frame),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    (model_dir / f"{ticker}_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    _update_latest_pointer(model_dir, ticker, metadata)

    return TrainingResult(
        symbol=ticker,
        best_model=best_model,
        model_path=model_path,
        metrics=metrics,
        sample_count=len(feature_frame),
    )


def _metrics(target: pd.Series, predictions: object) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(target, predictions)),
        "rmse": float(mean_squared_error(target, predictions) ** 0.5),
        "r2": float(r2_score(target, predictions)),
    }


def _update_latest_pointer(
    model_dir: Path, ticker: str, metadata: dict[str, object]
) -> None:
    latest_path = model_dir / "latest.json"
    latest: dict[str, object] = {}
    if latest_path.exists():
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
    latest[ticker] = metadata
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")