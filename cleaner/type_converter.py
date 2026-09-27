"""Safe data-type conversion helpers."""

from __future__ import annotations

import pandas as pd


def convert_column(
    df: pd.DataFrame, column: str, target_type: str
) -> tuple[pd.DataFrame, int]:
    """Convert a column, coercing invalid numeric/date values to missing."""
    if column not in df.columns:
        raise KeyError(f"Unknown column: {column}")
    cleaned = df.copy()
    before_missing = int(cleaned[column].isna().sum())

    if target_type == "numeric":
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    elif target_type == "date":
        cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")
    elif target_type == "text":
        cleaned[column] = cleaned[column].astype("string")
    elif target_type == "boolean":
        values = cleaned[column].astype("string").str.strip().str.lower()
        mapped = values.map(
            {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}
        )
        cleaned[column] = mapped.astype("boolean")
    else:
        raise ValueError(f"Unsupported target type: {target_type}")

    introduced_missing = max(0, int(cleaned[column].isna().sum()) - before_missing)
    return cleaned, introduced_missing
