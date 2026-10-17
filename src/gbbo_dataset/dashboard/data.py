"""Data loading and caching layer for the GBBO Streamlit dashboard."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import streamlit as st

    cache_data = st.cache_data
except ImportError:

    def cache_data(func: Any) -> Any:
        """Fallback decorator when streamlit is not installed."""
        return func


def _get_data_dir() -> Path:
    """Resolve the directory containing processed tables."""
    env_dir = os.environ.get("GBBO_DATA_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    # 1. Project root / data/processed
    candidates = [
        Path("data/processed"),
        Path("../data/processed"),
        Path("../../data/processed"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed",
    ]
    for c in candidates:
        if c.exists() and (c / "seasons.parquet").exists():
            return c
        if c.exists() and (c / "seasons.csv").exists():
            return c

    return Path("data/processed")


@cache_data
def load_table(table_name: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    """Load a processed table from Parquet or CSV with caching."""
    dir_path = Path(data_dir) if data_dir else _get_data_dir()
    parquet_path = dir_path / f"{table_name}.parquet"
    csv_path = dir_path / f"{table_name}.csv"

    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            # Normalize array columns to comma-separated strings for Streamlit display
            for col in df.columns:
                if df[col].dtype == object and len(df) > 0:
                    first_val = (
                        df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    )
                    if isinstance(first_val, (list, tuple)) or (
                        hasattr(first_val, "__iter__")
                        and not isinstance(first_val, (str, bytes))
                    ):
                        df[col] = df[col].apply(
                            lambda x: (
                                ", ".join(str(i) for i in x)
                                if hasattr(x, "__iter__")
                                and not isinstance(x, (str, bytes))
                                else str(x)
                            )
                        )
            return df
        except Exception as err:
            logger.debug("Failed to read parquet table %s: %s", parquet_path, err)

    if csv_path.exists():
        try:
            return pd.read_csv(csv_path)
        except Exception as err:
            logger.debug("Failed to read csv table %s: %s", csv_path, err)

    return pd.DataFrame()


@cache_data
def load_all_datasets(data_dir: Path | str | None = None) -> dict[str, pd.DataFrame]:
    """Load all 4 core tables into memory."""
    tables = ["seasons", "bakers", "episodes", "performances"]
    return {tbl: load_table(tbl, data_dir=data_dir) for tbl in tables}
