"""Data validation utilities for numpy arrays and pandas DataFrames."""

from __future__ import annotations

from typing import Any

from ml_core.exceptions import ValidationError


def validate_array(arr: Any, *, name: str = "array", allow_empty: bool = False) -> Any:
    """Validate a numpy-like array for NaN/Inf/empty."""
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("numpy is required for validate_array") from exc

    if not isinstance(arr, np.ndarray):
        raise ValidationError(
            f"{name} must be a numpy ndarray, got {type(arr).__name__}"
        )
    if not allow_empty and arr.size == 0:
        raise ValidationError(f"{name} is empty")
    if np.any(np.isnan(arr)):
        raise ValidationError(f"{name} contains NaN values")
    if np.any(np.isinf(arr)):
        raise ValidationError(f"{name} contains Inf values")
    return arr


def validate_dataframe(
    df: Any, *, required_columns: list[str] | None = None, name: str = "dataframe"
) -> Any:
    """Validate a pandas DataFrame for nulls, required columns, and non-emptiness."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required for validate_dataframe") from exc

    if not isinstance(df, pd.DataFrame):
        raise ValidationError(
            f"{name} must be a pandas DataFrame, got {type(df).__name__}"
        )
    if df.empty:
        raise ValidationError(f"{name} is empty")
    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise ValidationError(f"{name} is missing required columns: {missing}")
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if not cols_with_nulls.empty:
        raise ValidationError(
            f"{name} contains null values in columns: {cols_with_nulls.to_dict()}"
        )
    return df
