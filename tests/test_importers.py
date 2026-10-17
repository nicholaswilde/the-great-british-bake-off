"""Unit tests for RayofData importer and enrichment."""

from pathlib import Path

from gbbo_dataset.importers.rayofdata import (
    DEFAULT_RAY_DATA_DIR,
    build_seasons,
    match_baker_id,
    run_enrichment,
)


def test_match_baker_id():
    """Verify name matching resolves first names and disambiguated names."""
    sample_bakers = [
        {"baker_id": "s01_edward", "series_number": 1, "name": "Edward 'Edd' Kimber"},
        {"baker_id": "s01_david", "series_number": 1, "name": "David Chambers"},
        {"baker_id": "s02_joanne", "series_number": 2, "name": 'Joanne "Jo" Wheatley'},
    ]

    assert match_baker_id(1, "Edd", sample_bakers) == "s01_edward"
    assert match_baker_id(1, "DavidC", sample_bakers) == "s01_david"
    assert match_baker_id(2, "Jo", sample_bakers) == "s02_joanne"
    assert match_baker_id(1, "Nonexistent", sample_bakers) is None


def test_build_seasons():
    """Verify season metadata is parsed from Seasons.csv."""
    ray_seasons = DEFAULT_RAY_DATA_DIR / "Seasons.csv"
    if not ray_seasons.exists():
        return

    seasons = build_seasons(ray_seasons)
    assert len(seasons) == 17
    s1 = next(s for s in seasons if s["series_number"] == 1)
    assert "Mel Giedroyc" in s1["hosts"]
    assert "Paul Hollywood" in s1["judges"]
    assert s1["network"] == "BBC Two"


def test_run_enrichment(tmp_path: Path):
    """Verify end-to-end enrichment on processed datasets."""
    if not DEFAULT_RAY_DATA_DIR.exists():
        return

    res = run_enrichment(
        processed_dir=Path("data/processed"), ray_dir=DEFAULT_RAY_DATA_DIR
    )
    assert res["bakers_enriched"] >= 22
    assert res["episodes_enriched"] >= 14
    assert res["seasons_created"] == 17
