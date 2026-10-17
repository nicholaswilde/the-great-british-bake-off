"""Tests for Apache Arrow IPC and Parquet exporter."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pyarrow import feather

from gbbo_dataset.exports.arrow_export import ArrowExporter, export_arrow


def test_arrow_exporter_basic(tmp_path: Path):
    """Test exporting tables to both Parquet and Arrow IPC formats."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    arrow_dir = tmp_path / "arrow"

    # Create dummy tables
    for tbl in ["seasons", "bakers", "episodes", "performances"]:
        df = pd.DataFrame([{"id": 1, "col": "val"}])
        df.to_csv(proc_dir / f"{tbl}.csv", index=False)

    exporter = ArrowExporter(processed_dir=proc_dir, arrow_dir=arrow_dir)
    results = exporter.export_all()

    parquet_files = results["parquet"]
    arrow_files = results["arrow"]

    assert len(parquet_files) == 4
    assert len(arrow_files) == 4

    for tbl in ["seasons", "bakers", "episodes", "performances"]:
        pq_path = parquet_files[tbl]
        assert pq_path.exists()
        df_pq = pd.read_parquet(pq_path)
        assert len(df_pq) == 1

        ar_path = arrow_files[tbl]
        assert ar_path.exists()
        tbl_ar = feather.read_table(ar_path)
        assert len(tbl_ar) == 1


def test_arrow_export_helper(tmp_path: Path):
    """Test export_arrow helper function."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    for tbl in ["seasons", "bakers", "episodes", "performances"]:
        df = pd.DataFrame([{"series_number": 1}])
        df.to_csv(proc_dir / f"{tbl}.csv", index=False)

    results = export_arrow(processed_dir=proc_dir, arrow_dir=tmp_path / "arrow")
    assert len(results["arrow"]) == 4
    assert len(results["parquet"]) == 4
