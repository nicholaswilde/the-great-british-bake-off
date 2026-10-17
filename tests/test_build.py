"""Test dataset build and aggregation logic."""

from pathlib import Path

from gbbo_dataset.builder import build_datasets


def test_build_datasets_runs(tmp_path: Path):
    """Test build_datasets processes raw files and outputs expected files."""
    raw_dir = Path("data/raw")
    if not (raw_dir / "series_1_bakers.json").exists():
        return

    processed_dir = tmp_path / "processed"
    results = build_datasets(raw_dir=raw_dir, processed_dir=processed_dir)

    assert results["errors"] == 0
    assert results["bakers"] > 0
    assert (processed_dir / "bakers.json").exists()
    assert (processed_dir / "bakers.csv").exists()
    assert (processed_dir / "bakers.parquet").exists()
