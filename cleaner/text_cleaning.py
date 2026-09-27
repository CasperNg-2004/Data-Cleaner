"""Column-name and text-value normalization."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype


def clean_column_name(name: object) -> str:
    """Convert a label into a lowercase snake_case identifier."""
    value = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return value or "column"


def _unique_names(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        result.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return result


def clean_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Standardize names while preventing collisions."""
    cleaned = df.copy()
    new_names = _unique_names([clean_column_name(column) for column in df.columns])
    mapping = dict(zip(map(str, df.columns), new_names))
    cleaned.columns = new_names
    return cleaned, mapping


def text_columns(df: pd.DataFrame) -> list[str]:
    return [
        column
        for column in df.columns
        if is_object_dtype(df[column]) or is_string_dtype(df[column])
    ]


def clean_text_columns(
    df: pd.DataFrame, columns: list[str] | None = None
) -> tuple[pd.DataFrame, int]:
    """Trim text and collapse internal whitespace without changing missing values."""
    cleaned = df.copy()
    selected = columns if columns is not None else text_columns(cleaned)
    changed = 0
    for column in selected:
        before = cleaned[column].copy()
        mask = cleaned[column].notna()
        cleaned.loc[mask, column] = (
            cleaned.loc[mask, column].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        )
        changed += int((before.fillna("<NA>") != cleaned[column].fillna("<NA>")).sum())
    return cleaned, changed


def normalize_text(
    df: pd.DataFrame, columns: list[str], style: str = "title"
) -> tuple[pd.DataFrame, int]:
    """Normalize case for selected textual columns."""
    if style not in {"title", "lower", "upper"}:
        raise ValueError(f"Unsupported text style: {style}")
    cleaned = df.copy()
    changed = 0
    for column in columns:
        before = cleaned[column].copy()
        mask = cleaned[column].notna()
        cleaned.loc[mask, column] = getattr(cleaned.loc[mask, column].astype(str).str, style)()
        changed += int((before.fillna("<NA>") != cleaned[column].fillna("<NA>")).sum())
    return cleaned, changed
