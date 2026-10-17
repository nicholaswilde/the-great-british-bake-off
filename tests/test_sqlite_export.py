"""Tests for SQLite database export."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from gbbo_dataset.exports.sqlite_export import SQLiteExporter, export_to_sqlite


@pytest.fixture
def mock_processed_dir(tmp_path: Path) -> Path:
    """Create a temporary processed directory with sample tables."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    df_seasons = pd.DataFrame(
        [
            {
                "series_number": 1,
                "year": 2010,
                "winner": "Edd Kimber",
                "hosts": "['Mel Giedroyc', 'Sue Perkins']",
                "judges": "['Mary Berry', 'Paul Hollywood']",
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
                "performance_id": "s01e01_s01_edd",
                "baker_id": "s01_edd",  # Legacy alias should be normalized
                "episode_id": "s01e01",
                "signature_dish": "Victoria Sponge",
                "technical_rank": 1.0,
                "showstopper_dish": "Chocolate Celebration Cake",
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


def test_sqlite_exporter_basic(mock_processed_dir: Path, tmp_path: Path):
    """Test exporting sample tables into SQLite database."""
    db_path = tmp_path / "test_gbbo.db"
    exporter = SQLiteExporter(processed_dir=mock_processed_dir, db_path=db_path)
    out = exporter.export()

    assert out.exists()
    assert out == db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify tables exist
    tables = {
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"seasons", "bakers", "episodes", "performances"}.issubset(tables)

    # Verify foreign key check passes
    cursor.execute("PRAGMA foreign_key_check;")
    assert cursor.fetchall() == []

    # Verify rows count
    assert cursor.execute("SELECT COUNT(*) FROM seasons;").fetchone()[0] == 1
    assert cursor.execute("SELECT COUNT(*) FROM bakers;").fetchone()[0] == 1
    assert cursor.execute("SELECT COUNT(*) FROM episodes;").fetchone()[0] == 1
    assert cursor.execute("SELECT COUNT(*) FROM performances;").fetchone()[0] == 1

    # Verify baker alias was normalized so JOIN works seamlessly
    res = cursor.execute(
        """
        SELECT b.name, p.signature_dish, e.theme
        FROM performances p
        JOIN bakers b ON p.baker_id = b.baker_id
        JOIN episodes e ON p.episode_id = e.episode_id
        """
    ).fetchall()
    assert len(res) == 1
    assert res[0][0] == "Edward 'Edd' Kimber"
    assert res[0][1] == "Victoria Sponge"
    assert res[0][2] == "Cake"

    # Verify indexes
    indexes = {
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    assert "idx_bakers_series" in indexes
    assert "idx_episodes_series" in indexes
    assert "idx_performances_baker" in indexes
    assert "idx_performances_episode" in indexes

    conn.close()


def test_sqlite_export_foreign_key_violation(tmp_path: Path):
    """Test that SQLiteExporter raises RuntimeError on foreign key integrity violation."""
    proc_dir = tmp_path / "broken_proc"
    proc_dir.mkdir(parents=True, exist_ok=True)

    df_seasons = pd.DataFrame([{"series_number": 1, "year": 2010}])
    df_bakers = pd.DataFrame(
        [{"baker_id": "s01_alice", "series_number": 1, "name": "Alice"}]
    )
    df_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
            }
        ]
    )
    # Performance references unknown baker
    df_performances = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_unknown",
                "baker_id": "s99_unknown_baker",
                "episode_id": "s01e01",
                "result": "SAFE",
            }
        ]
    )

    df_seasons.to_csv(proc_dir / "seasons.csv", index=False)
    df_bakers.to_csv(proc_dir / "bakers.csv", index=False)
    df_episodes.to_csv(proc_dir / "episodes.csv", index=False)
    df_performances.to_csv(proc_dir / "performances.csv", index=False)

    exporter = SQLiteExporter(processed_dir=proc_dir, db_path=tmp_path / "broken.db")
    with pytest.raises((sqlite3.IntegrityError, RuntimeError, pd.errors.DatabaseError)):
        exporter.export()


def test_export_to_sqlite_helper(mock_processed_dir: Path, tmp_path: Path):
    """Test export_to_sqlite convenience function."""
    db_path = tmp_path / "helper_gbbo.db"
    out = export_to_sqlite(processed_dir=mock_processed_dir, db_path=db_path)
    assert out.exists()
    assert out == db_path
