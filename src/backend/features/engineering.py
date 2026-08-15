"""Feature engineering shared by model training and inference."""

from collections.abc import Iterable

import pandas as pd

FEATURE_COLUMNS = [
    "return_1",
    "close_lag_1",
    "close_lag_5",
    "volatility_5",
]
TARGET_COLUMN = "target_close"
REQUIRED_COLUMNS = {"timestamp", "close"}


def build_feature_frame(
    data: pd.DataFrame | Iterable[object],
    horizon: int = 1,
    include_target: bool = True,
) -> pd.DataFrame:
    """Build the same lag and rolling features for training or prediction."""

    if horizon < 1:
        raise ValueError("horizon must be at least 1")

    # Normalize input records into a sorted numeric frame.
    frame = _to_frame(data)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    frame = frame.sort_values("timestamp").reset_index(drop=True).copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame["close"].isna().all():
        raise ValueError("close must contain at least one numeric value")

    # Build lag, return, and rolling-volatility inputs.
    frame["return_1"] = frame["close"].pct_change()
    frame["close_lag_1"] = frame["close"].shift(1)
    frame["close_lag_5"] = frame["close"].shift(5)
    frame["volatility_5"] = frame["return_1"].rolling(window=5).std()

    # Add the future close only when preparing training data.
    if include_target:
        frame[TARGET_COLUMN] = frame["close"].shift(-horizon)

    columns = ["timestamp", *FEATURE_COLUMNS]
    if include_target:
        columns.append(TARGET_COLUMN)
    # Remove rows that cannot produce complete features.
    return frame.dropna(subset=columns).loc[:, columns]


def _to_frame(data: pd.DataFrame | Iterable[object]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data

    rows = []
    for observation in data:
        rows.append(
            {
                "timestamp": observation.timestamp,
                "close": observation.close,
            }
        )
    return pd.DataFrame(rows)