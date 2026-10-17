"""Unit tests for DatasetValidator."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.validator import DatasetValidator

runner = CliRunner()


def test_validator_pass() -> None:
    validator = DatasetValidator(processed_dir="data/processed")
    report = validator.validate()
    assert report["status"] == "PASS"
    assert "seasons" in report["tables_found"]
    assert "bakers" in report["tables_found"]
    assert "episodes" in report["tables_found"]
    assert "performances" in report["tables_found"]
    assert len(report["issues"]) == 0


def test_validator_missing_table(tmp_path: Path) -> None:
    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()
    assert report["status"] == "FAIL"
    assert len(report["issues"]) > 0


def test_cli_validate() -> None:
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "Validation Status: PASS" in result.stdout
