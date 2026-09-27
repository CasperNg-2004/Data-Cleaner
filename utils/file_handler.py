"""CSV parsing helpers with practical fallbacks."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def read_csv_safely(data: bytes) -> tuple[pd.DataFrame, str]:
    """Read CSV bytes using common encodings and delimiter auto-detection."""
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            frame = pd.read_csv(BytesIO(data), encoding=encoding, sep=None, engine="python")
            if frame.shape[1] == 0:
                raise ValueError("No columns found")
            return frame, encoding
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            errors.append(f"{encoding}: {exc}")
    raise ValueError("Could not parse the file as CSV. " + " | ".join(errors))
