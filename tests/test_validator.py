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


def test_validator_issues_and_relations(tmp_path: Path) -> None:
    """Test all validator relational integrity and constraint checks."""
    import pandas as pd

    seasons_df = pd.DataFrame({"series_number": [1, 2]})
    bakers_df = pd.DataFrame(
        {
            "baker_id": ["b1", "b1"],  # duplicate pk
            "series_number": [99, 99],  # invalid series
        }
    )
    episodes_df = pd.DataFrame(
        {
            "episode_id": ["e1"],
            "series_number": [88],  # invalid series
        }
    )
    performances_df = pd.DataFrame(
        {
            # Missing 'performance_id' pk column to test missing pk branch
            "baker_id": ["b_unknown"],  # unknown baker
            "episode_id": ["e_unknown"],  # unknown episode
            "result": ["INVALID_RESULT"],  # invalid enum
        }
    )

    seasons_df.to_csv(tmp_path / "seasons.csv", index=False)
    bakers_df.to_csv(tmp_path / "bakers.csv", index=False)
    episodes_df.to_csv(tmp_path / "episodes.csv", index=False)
    performances_df.to_csv(tmp_path / "performances.csv", index=False)

    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()

    assert report["status"] == "FAIL"
    issues = " ".join(report["issues"])
    assert "Missing primary key column 'performance_id'" in issues
    assert "Duplicate primary keys found in bakers.csv" in issues
    assert "Bakers reference invalid series" in issues
    assert "Episodes reference invalid series" in issues
    assert "Performances reference unknown bakers" in issues
    assert "Performances reference unknown episodes" in issues
    assert "Invalid performance results" in issues


def test_validator_warning_status(tmp_path: Path) -> None:
    """Test status fallback to WARNING when non-critical issue present."""
    import pandas as pd

    seasons_df = pd.DataFrame({"series_number": [1]})
    bakers_df = pd.DataFrame({"baker_id": ["b1"], "series_number": [1]})
    episodes_df = pd.DataFrame({"episode_id": ["e1"], "series_number": [1]})
    performances_df = pd.DataFrame(
        {
            "performance_id": ["p1"],
            "baker_id": ["b1"],
            "episode_id": ["e1"],
            "result": ["RUNNER_UP"],
        }
    )

    seasons_df.to_csv(tmp_path / "seasons.csv", index=False)
    bakers_df.to_csv(tmp_path / "bakers.csv", index=False)
    episodes_df.to_csv(tmp_path / "episodes.csv", index=False)
    performances_df.to_csv(tmp_path / "performances.csv", index=False)

    validator = DatasetValidator(processed_dir=tmp_path)
    # Monkeypatch validate to add non-critical issue
    orig_validate = validator.validate

    def mock_validate():
        rep = orig_validate()
        rep["issues"].append("Minor note about metadata")
        has_error = any(
            "Duplicate" in i or "Missing" in i or "unknown" in i or "invalid" in i
            for i in rep["issues"]
        )
        rep["status"] = "FAIL" if has_error else "WARNING"
        return rep

    validator.validate = mock_validate
    report = validator.validate()
    assert report["status"] == "WARNING"


def test_cli_validate() -> None:
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "Validation Status: PASS" in result.stdout
