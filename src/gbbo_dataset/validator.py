"""Data integrity and relational constraint validation for The Great British Bake Off dataset."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from gbbo_dataset.models import ResultEnum

logger = logging.getLogger(__name__)

TABLES = ["seasons", "bakers", "episodes", "performances"]


class DatasetValidator:
    """Validates relational integrity, primary/foreign keys, and domain rules across tables."""

    def __init__(self, processed_dir: Path | str = "data/processed") -> None:
        self.processed_dir = Path(processed_dir)

    def validate(self) -> dict[str, Any]:
        """Run all validation checks and return summary report."""
        report: dict[str, Any] = {
            "tables_found": [],
            "row_counts": {},
            "issues": [],
            "status": "PASS",
        }

        dfs: dict[str, pd.DataFrame] = {}

        for t in TABLES:
            csv_file = self.processed_dir / f"{t}.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                dfs[t] = df
                report["tables_found"].append(t)
                report["row_counts"][t] = len(df)
            else:
                report["issues"].append(f"Missing required table: {t}.csv")

        if len(dfs) < len(TABLES):
            report["status"] = "FAIL"
            return report

        # 1. Primary key uniqueness checks
        pk_map = {
            "seasons": "series_number",
            "bakers": "baker_id",
            "episodes": "episode_id",
            "performances": "performance_id",
        }
        for t, pk in pk_map.items():
            if t in dfs:
                df = dfs[t]
                if pk not in df.columns:
                    report["issues"].append(
                        f"Missing primary key column '{pk}' in {t}.csv"
                    )
                elif df[pk].duplicated().any():
                    dups = df[df[pk].duplicated()][pk].tolist()
                    report["issues"].append(
                        f"Duplicate primary keys found in {t}.csv: {dups[:5]}"
                    )

        # 2. Foreign key relational checks
        if "seasons" in dfs and "bakers" in dfs:
            valid_series = set(dfs["seasons"]["series_number"].unique())
            baker_series = set(dfs["bakers"]["series_number"].unique())
            orphaned = baker_series - valid_series
            if orphaned:
                report["issues"].append(f"Bakers reference invalid series: {orphaned}")

        if "seasons" in dfs and "episodes" in dfs:
            valid_series = set(dfs["seasons"]["series_number"].unique())
            ep_series = set(dfs["episodes"]["series_number"].unique())
            orphaned = ep_series - valid_series
            if orphaned:
                report["issues"].append(
                    f"Episodes reference invalid series: {orphaned}"
                )

        if "bakers" in dfs and "performances" in dfs:
            valid_bakers = set(dfs["bakers"]["baker_id"].unique())
            perf_bakers = set(dfs["performances"]["baker_id"].unique())
            orphaned = perf_bakers - valid_bakers
            if orphaned:
                report["issues"].append(
                    f"Performances reference unknown bakers: {orphaned}"
                )

        if "episodes" in dfs and "performances" in dfs:
            valid_eps = set(dfs["episodes"]["episode_id"].unique())
            perf_eps = set(dfs["performances"]["episode_id"].unique())
            orphaned = perf_eps - valid_eps
            if orphaned:
                report["issues"].append(
                    f"Performances reference unknown episodes: {orphaned}"
                )

        # 3. Domain rules: ResultEnum values
        if "performances" in dfs:
            perf_df = dfs["performances"]
            valid_results = {r.value for r in ResultEnum}
            actual_results = set(perf_df["result"].dropna().unique())
            invalid_results = actual_results - valid_results
            if invalid_results:
                report["issues"].append(
                    f"Invalid performance results: {invalid_results}"
                )

        # Determine overall status
        if report["issues"]:
            has_error = any(
                "Duplicate" in i or "Missing" in i or "unknown" in i or "invalid" in i
                for i in report["issues"]
            )
            report["status"] = "FAIL" if has_error else "WARNING"

        return report
