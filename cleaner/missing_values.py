"""Missing-value inspection and treatment."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missing counts and percentages for every column."""
    counts = df.isna().sum()
    return pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": counts.to_numpy(),
            "missing_percent": (counts.to_numpy() / max(len(df), 1) * 100).round(2),
        }
    )


def fill_missing(
    df: pd.DataFrame,
    column: str,
    method: str,
    custom_value: Any | None = None,
) -> tuple[pd.DataFrame, int]:
    """Apply one missing-value strategy to one column and return change count."""
    if column not in df.columns:
        raise KeyError(f"Unknown column: {column}")

    cleaned = df.copy()
    count = int(cleaned[column].isna().sum())
    if count == 0:
        return cleaned, 0

    if method == "drop rows":
        cleaned = cleaned.dropna(subset=[column]).reset_index(drop=True)
        return cleaned, count
    if method in {"mean", "median"}:
        if not is_numeric_dtype(cleaned[column]):
            raise TypeError(f"{method.title()} is only valid for numeric columns")
        value = getattr(cleaned[column], method)()
    elif method == "mode":
        modes = cleaned[column].mode(dropna=True)
        if modes.empty:
            raise ValueError(f"Column '{column}' has no non-missing mode")
        value = modes.iloc[0]
    elif method == "unknown":
        value = "Unknown"
    elif method == "custom":
        value = custom_value
        if is_numeric_dtype(cleaned[column]) and custom_value is not None:
            converted = pd.to_numeric(pd.Series([custom_value]), errors="coerce").iloc[0]
            if pd.isna(converted):
                raise ValueError(f"Custom value for numeric column '{column}' must be numeric")
            value = converted
    else:
        raise ValueError(f"Unsupported missing-value method: {method}")

    cleaned[column] = cleaned[column].fillna(value)
    return cleaned, count
