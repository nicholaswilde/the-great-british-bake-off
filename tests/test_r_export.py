"""Tests for R dataset exporter and companion R package scaffolding."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadr
import pytest

from gbbo_dataset.exports.r_export import RExporter, export_to_r


@pytest.fixture
def sample_processed_dir(tmp_path: Path) -> Path:
    """Create sample processed directory for R testing."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    df_seasons = pd.DataFrame(
        [
            {
                "series_number": 1,
                "year": 2010,
                "winner": "Edd Kimber",
                "hosts": "Mel & Sue",
                "judges": "Mary & Paul",
                "network": "BBC Two",
                "pbs_season": None,
                "netflix_collection": None,
                "roku_season": 1.0,
                "location": "Various",
            }
        ]
    )
    df_bakers = pd.DataFrame(
        [
            {
                "baker_id": "s01_edward",
                "series_number": 1,
                "name": "Edward 'Edd' Kimber",
                "age": 24,
                "gender": "M",
                "occupation": "Debt collector",
                "hometown": "Bradford",
                "overall_placement": 1.0,
                "image_url": "https://example.com/edd.jpg",
            }
        ]
    )
    df_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
                "air_date": "2010-08-17",
                "signature_time_min": 120.0,
                "technical_time_min": 60.0,
                "showstopper_time_min": 240.0,
            }
        ]
    )
    df_performances = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_edward",
                "baker_id": "s01_edward",
                "episode_id": "s01e01",
                "signature_dish": "Victoria Sponge",
                "technical_rank": 1.0,
                "showstopper_dish": "Celebration Cake",
                "result": "SAFE",
                "hollywood_handshake": False,
                "did_well": True,
                "at_risk": False,
                "absent": False,
            }
        ]
    )

    df_seasons.to_csv(proc_dir / "seasons.csv", index=False)
    df_bakers.to_csv(proc_dir / "bakers.csv", index=False)
    df_episodes.to_csv(proc_dir / "episodes.csv", index=False)
    df_performances.to_csv(proc_dir / "performances.csv", index=False)

    return proc_dir


def test_r_exporter_pipeline(sample_processed_dir: Path, tmp_path: Path):
    """Test full R export pipeline including package scaffolding and pyreadr read back."""
    r_out = tmp_path / "r_out"
    pkg_dir = tmp_path / "r_pkg"

    exporter = RExporter(
        processed_dir=sample_processed_dir,
        r_output_dir=r_out,
        r_pkg_dir=pkg_dir,
    )
    results = exporter.export_all()

    # 1. Verify RDS
    rds_dict = results["rds"]
    assert len(rds_dict) == 4
    for tbl, path in rds_dict.items():
        assert path.exists()
        res = pyreadr.read_r(str(path))
        df_read = res[None]
        assert len(df_read) == 1

    # 2. Verify RDA
    rda_dict = results["rda"]
    assert len(rda_dict) == 4
    for tbl, path in rda_dict.items():
        assert path.exists()
        res = pyreadr.read_r(str(path))
        df_read = res[tbl]
        assert len(df_read) == 1

    # 3. Verify documentation files
    roxygen_file = results["roxygen"]
    assert roxygen_file.exists()
    roxygen_content = roxygen_file.read_text(encoding="utf-8")
    assert "Seasons in The Great British Bake Off" in roxygen_content
    assert '"performances"' in roxygen_content

    rd_files = results["rd"]
    assert len(rd_files) == 4
    for tbl, path in rd_files.items():
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert f"\\name{{{tbl}}}" in content

    # 4. Verify scaffolding files
    assert "DESCRIPTION" in results["scaffold"]
    assert (pkg_dir / "DESCRIPTION").exists()
    assert (pkg_dir / "NAMESPACE").exists()
    assert (pkg_dir / ".Rbuildignore").exists()
    assert (pkg_dir / "README.md").exists()
    assert (pkg_dir / "vignettes" / "introduction.Rmd").exists()
    assert (pkg_dir / "tests" / "testthat.R").exists()
    assert (pkg_dir / "tests" / "testthat" / "test-datasets.R").exists()


def test_export_to_r_helper(sample_processed_dir: Path, tmp_path: Path):
    """Test export_to_r helper function."""
    r_out = tmp_path / "r_out_helper"
    pkg_dir = tmp_path / "r_pkg_helper"

    results = export_to_r(
        processed_dir=sample_processed_dir,
        r_output_dir=r_out,
        r_pkg_dir=pkg_dir,
    )
    assert len(results["rds"]) == 4
    assert len(results["rda"]) == 4
