"""Duplicate-row operations."""

from __future__ import annotations

import pandas as pd


def count_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> int:
    """Return the number of duplicate rows, optionally based on selected columns."""
    return int(df.duplicated(subset=subset).sum())


def remove_duplicates(
    df: pd.DataFrame, subset: list[str] | None = None, keep: str | bool = "first"
) -> tuple[pd.DataFrame, int]:
    """Return a copy with duplicate rows removed and the number removed."""
    before = len(df)
    cleaned = df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
    return cleaned, before - len(cleaned)
