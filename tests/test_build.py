"""Test dataset build and aggregation logic."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from gbbo_dataset.builder import build_datasets, load_json, main


def test_load_json_error_handling(tmp_path: Path):
    """Test load_json with non-existent and malformed files."""
    missing = tmp_path / "missing.json"
    assert load_json(missing) == []

    malformed = tmp_path / "bad.json"
    malformed.write_text("{not-valid-json", encoding="utf-8")
    assert load_json(malformed) == []

    not_a_list = tmp_path / "dict.json"
    not_a_list.write_text(json.dumps({"key": "val"}), encoding="utf-8")
    assert load_json(not_a_list) == []


def test_build_datasets_runs(tmp_path: Path):
    """Test build_datasets processes raw files and outputs expected files."""
    raw_dir = Path("data/raw")
    if not (raw_dir / "series_1_bakers.json").exists():
        return

    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    if Path("data/processed/seasons.json").exists():
        (processed_dir / "seasons.json").write_text(
            Path("data/processed/seasons.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    results = build_datasets(raw_dir=raw_dir, processed_dir=processed_dir)

    assert results["errors"] == 0
    assert results["bakers"] > 0
    assert (processed_dir / "bakers.json").exists()
    assert (processed_dir / "bakers.csv").exists()
    assert (processed_dir / "bakers.parquet").exists()
    assert (processed_dir / "seasons.parquet").exists()


def test_build_datasets_with_validation_errors_and_enrichment(tmp_path: Path):
    """Test build_datasets handles validation errors and preserves enriched attributes."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Seed existing processed data for enrichment preservation
    (processed_dir / "bakers.json").write_text(
        json.dumps(
            [
                {
                    "baker_id": "s01_edd",
                    "gender": "M",
                    "country": "United Kingdom",
                    "county_region": "West Yorkshire",
                    "latitude": 53.79,
                    "longitude": -1.75,
                }
            ]
        ),
        encoding="utf-8",
    )
    (processed_dir / "episodes.json").write_text(
        json.dumps(
            [
                {
                    "episode_id": "s01e01",
                    "signature_time_min": 120.0,
                    "technical_time_min": 60.0,
                    "showstopper_time_min": 240.0,
                }
            ]
        ),
        encoding="utf-8",
    )
    (processed_dir / "performances.json").write_text(
        json.dumps(
            [
                {
                    "performance_id": "s01e01_s01_edd",
                    "hollywood_handshake": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    # Raw baker files: one valid with hometown, one invalid
    bakers_raw = [
        {
            "baker_id": "s01_edd",
            "series_number": 1,
            "name": "Edd Kimber",
            "age": 24,
            "hometown": "Bradford",
            "overall_placement": 1,
        },
        {
            "baker_id": "invalid_baker",
            "series_number": -5,  # Invalid series
        },
    ]
    (raw_dir / "series_1_bakers.json").write_text(
        json.dumps(bakers_raw), encoding="utf-8"
    )

    # Raw episode files: one valid, one invalid
    episodes_raw = [
        {
            "episode_id": "s01e01",
            "series_number": 1,
            "episode_number": 1,
            "theme": "Cakes",
            "air_date": "2010-08-17",
        },
        {
            "episode_id": "bad_ep",
            "series_number": -1,
        },
    ]
    (raw_dir / "series_1_episodes.json").write_text(
        json.dumps(episodes_raw), encoding="utf-8"
    )

    # Raw performances: one valid with alias, one invalid
    perfs_raw = [
        {
            "baker_id": "s09_antony",  # Alias in BAKER_ID_ALIASES
            "episode_id": "s01e01",
            "performance_id": "s01e01_s09_antony",
            "signature_dish": "Cake",
            "technical_rank": 1,
            "showstopper_dish": "Cake",
            "result": "STAR_BAKER",
        },
        {
            "performance_id": "bad_perf",
            "baker_id": "bad",
            "episode_id": "bad",
            "result": "INVALID_STATUS_RESULT",
        },
    ]
    (raw_dir / "series_1_performances.json").write_text(
        json.dumps(perfs_raw), encoding="utf-8"
    )

    results = build_datasets(raw_dir=raw_dir, processed_dir=processed_dir)
    assert results["errors"] == 3  # 1 baker error, 1 episode error, 1 perf error
    assert results["bakers"] == 1
    assert results["episodes"] == 1
    assert results["performances"] == 1


def test_builder_main_cli(tmp_path: Path):
    """Test builder main function with CLI arguments."""
    with (
        patch(
            "sys.argv",
            [
                "gbbo-build",
                "--raw-dir",
                str(tmp_path / "raw"),
                "--processed-dir",
                str(tmp_path / "processed"),
            ],
        ),
        patch("gbbo_dataset.builder.build_datasets") as mock_build,
    ):
        mock_build.return_value = {"bakers": 1, "errors": 0}
        main()
        mock_build.assert_called_once()
