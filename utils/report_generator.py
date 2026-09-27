"""Dataset metrics, suggestions, and plain-text reporting."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from pandas.api.types import is_object_dtype

from cleaner.text_cleaning import clean_column_name
from cleaner.validator import detect_invalid_values


def dataset_metrics(df: pd.DataFrame) -> dict[str, int]:
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
    }


def cleaning_suggestions(df: pd.DataFrame) -> list[str]:
    suggestions: list[str] = []
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        suggestions.append(f"Remove or review {duplicate_count} duplicate row(s).")
    for column in df.columns:
        missing = float(df[column].isna().mean())
        if missing:
            method = "median" if pd.api.types.is_numeric_dtype(df[column]) else "mode or Unknown"
            suggestions.append(f"'{column}' is {missing:.1%} missing; consider {method}.")
        if clean_column_name(column) != column:
            suggestions.append(f"Standardize the column name '{column}'.")
        if is_object_dtype(df[column]) and df[column].notna().any():
            values = df[column].dropna().astype(str)
            if values.str.contains(r"^\s|\s$|\s{2,}", regex=True).any():
                suggestions.append(f"Trim or collapse whitespace in '{column}'.")
            numeric_rate = pd.to_numeric(values, errors="coerce").notna().mean()
            if numeric_rate >= 0.8:
                suggestions.append(f"'{column}' looks numeric; consider converting its type.")
    for column, result in detect_invalid_values(df).items():
        if result["count"]:
            suggestions.append(
                f"Review {result['count']} invalid value(s) in '{column}' ({result['rule']} rule)."
            )
    return suggestions or ["No common data-quality issues were detected."]


def generate_report(
    filename: str,
    before: pd.DataFrame,
    after: pd.DataFrame,
    history: list[str],
) -> str:
    original = dataset_metrics(before)
    cleaned = dataset_metrics(after)
    actions = "\n".join(f"{index}. {action}" for index, action in enumerate(history, 1))
    return f"""CSV DATA CLEANING REPORT
Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}
File: {filename}

BEFORE CLEANING
Rows: {original['rows']}
Columns: {original['columns']}
Missing values: {original['missing']}
Duplicate rows: {original['duplicates']}

AFTER CLEANING
Rows: {cleaned['rows']}
Columns: {cleaned['columns']}
Missing values: {cleaned['missing']}
Duplicate rows: {cleaned['duplicates']}

CLEANING HISTORY
{actions or 'No cleaning actions were applied.'}
"""
