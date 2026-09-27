"""IQR-based outlier detection. Detection never deletes data."""

from __future__ import annotations

import pandas as pd


def iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        raise ValueError("IQR bounds require at least one numeric value")
    q1, q3 = numeric.quantile([0.25, 0.75])
    spread = q3 - q1
    return float(q1 - multiplier * spread), float(q3 + multiplier * spread)


def detect_iqr_outliers(
    df: pd.DataFrame, column: str, multiplier: float = 1.5
) -> tuple[pd.DataFrame, tuple[float, float]]:
    lower, upper = iqr_bounds(df[column], multiplier)
    numeric = pd.to_numeric(df[column], errors="coerce")
    return df.loc[(numeric < lower) | (numeric > upper)].copy(), (lower, upper)
