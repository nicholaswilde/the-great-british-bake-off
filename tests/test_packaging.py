"""Unit and integration tests for release packaging and segmented dataset bundles."""

from __future__ import annotations

import zipfile
from pathlib import Path

from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.exports.packaging import (
    ReleasePackager,
    get_project_version,
    package_release,
)

runner = CliRunner()


def test_get_project_version(tmp_path: Path) -> None:
    # Test fallback
    assert get_project_version(tmp_path) == "0.1.0"

    # Test pyproject.toml detection
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    assert get_project_version(tmp_path) == "1.2.3"

    # Test r/DESCRIPTION detection
    tmp_path_r = tmp_path / "subdir"
    r_dir = tmp_path_r / "r"
    r_dir.mkdir(parents=True)
    (r_dir / "DESCRIPTION").write_text(
        "Package: test\nVersion: 2.3.4\n", encoding="utf-8"
    )
    assert get_project_version(tmp_path_r) == "2.3.4"


def test_release_packager_all(tmp_path: Path) -> None:
    out_dir = tmp_path / "dist" / "release"
    packager = ReleasePackager(output_dir=out_dir, version="0.2.0")

    assert packager.clean_version == "0.2.0"
    assert packager.tag_version == "v0.2.0"

    results = packager.package_all()

    # Check CSV bundle
    assert "csv" in results
    csv_zip = results["csv"]
    assert csv_zip.exists()
    with zipfile.ZipFile(csv_zip, "r") as zf:
        names = zf.namelist()
        assert "csv/seasons.csv" in names
        assert "csv/bakers.csv" in names
        assert "data_dictionary.md" in names
        assert "LICENSE" in names
        assert "README.md" in names

    # Check Parquet bundle
    assert "parquet" in results
    parquet_zip = results["parquet"]
    assert parquet_zip.exists()
    with zipfile.ZipFile(parquet_zip, "r") as zf:
        names = zf.namelist()
        assert "parquet/seasons.parquet" in names
        assert "parquet/bakers.parquet" in names
        assert "data_dictionary.md" in names

    # Check AI bundle
    assert "ai" in results
    ai_zip = results["ai"]
    assert ai_zip.exists()
    with zipfile.ZipFile(ai_zip, "r") as zf:
        names = zf.namelist()
        assert "ai/gbbo_qa_finetuning.jsonl" in names
        assert "README.md" in names
        assert "data_dictionary.md" in names

    # Check SQLite bundle
    if (Path("data/processed") / "gbbo.db").exists():
        assert "sqlite" in results
        assert results["sqlite"].exists()
        with zipfile.ZipFile(results["sqlite"], "r") as zf:
            names = zf.namelist()
            assert "gbbo.db" in names

    # Check TidyTuesday bundle
    assert "tidytuesday" in results
    assert results["tidytuesday"].exists()

    # Check R package tarball
    assert "r" in results
    assert results["r"].exists()
    assert results["r"].name == "gbbo_0.2.0.tar.gz"

    # Check manifest and checksums
    assert "manifest" in results
    assert results["manifest"].exists()
    assert "checksums" in results
    assert results["checksums"].exists()


def test_package_release_convenience(tmp_path: Path) -> None:
    out_dir = tmp_path / "convenience_release"
    results = package_release(output_dir=out_dir, version="0.1.0")
    assert "csv" in results
    assert (out_dir / "checksums.txt").exists()


def test_cli_package_components(tmp_path: Path) -> None:
    out_dir = tmp_path / "cli_release"
    result = runner.invoke(
        app,
        ["package", "--output-dir", str(out_dir), "--component", "csv"],
    )
    assert result.exit_code == 0
    assert (out_dir / "checksums.txt").exists()
