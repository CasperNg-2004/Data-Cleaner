"""Rule-based invalid-value detection."""

from __future__ import annotations

import re

import pandas as pd

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def infer_validation(column: str) -> str | None:
    name = column.lower()
    if "email" in name:
        return "email"
    if "age" in name:
        return "age"
    if any(token in name for token in ("salary", "price", "amount", "quantity", "qty")):
        return "non_negative"
    if "phone" in name or "mobile" in name:
        return "phone"
    return None


def invalid_mask(series: pd.Series, rule: str) -> pd.Series:
    present = series.notna()
    if rule == "email":
        return present & ~series.astype(str).str.match(EMAIL_PATTERN)
    if rule == "age":
        numeric = pd.to_numeric(series, errors="coerce")
        return present & (numeric.isna() | (numeric < 0) | (numeric > 120))
    if rule == "non_negative":
        numeric = pd.to_numeric(series, errors="coerce")
        return present & (numeric.isna() | (numeric < 0))
    if rule == "phone":
        digits = series.astype(str).str.replace(r"\D", "", regex=True)
        return present & ~digits.str.len().between(7, 15)
    raise ValueError(f"Unsupported validation rule: {rule}")


def detect_invalid_values(df: pd.DataFrame) -> dict[str, dict[str, object]]:
    """Apply inferred rules and return invalid row indexes and counts."""
    results: dict[str, dict[str, object]] = {}
    for column in df.columns:
        rule = infer_validation(column)
        if rule:
            mask = invalid_mask(df[column], rule)
            results[column] = {"rule": rule, "count": int(mask.sum()), "indexes": df.index[mask].tolist()}
    return results
