"""Unit tests for the Wikipedia scraper module."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from gbbo_dataset.scraper import (
    clean_text,
    extract_air_dates,
    extract_bakers,
    extract_episodes_and_performances,
    extract_placements_from_matrix,
    fetch_series_html,
    find_bakers_table,
    find_elimination_matrix,
    main,
    parse_placement,
    resolve_baker_id,
    scrape_series,
)


def test_clean_text():
    """Test Wikipedia text cleaner handles edge cases."""
    assert clean_text(None) == ""
    assert clean_text(pd.NA) == ""
    assert clean_text("Jane Doe[1][a]") == "Jane Doe"
    assert clean_text("  Paul \n Hollywood \t ") == "Paul Hollywood"
    assert clean_text(123) == "123"


def test_parse_placement():
    """Test parsing ordinal and string placements into integers."""
    assert parse_placement("Winner") == 1
    assert parse_placement("1st place") == 1
    assert parse_placement("Runner-up") == 2
    assert parse_placement("2nd") == 2
    assert parse_placement("3rd") == 3
    assert parse_placement("10th (eliminated)") == 10
    assert parse_placement("Unknown") is None


def test_fetch_series_html():
    """Test fetching series HTML with mock response."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body>GBBO Series 1</body></html>"
        mock_get.return_value = mock_resp

        html = fetch_series_html(1)
        assert "GBBO Series 1" in html
        assert mock_get.called

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with pytest.raises(FileNotFoundError, match="not found on Wikipedia"):
            fetch_series_html(99)


def test_find_bakers_table():
    """Test identifying baker table from candidate DataFrames."""
    df_wrong = pd.DataFrame({"episodes": [1, 2], "views": [5.1, 6.2]})
    df_bakers = pd.DataFrame(
        {
            "Baker": ["Edd", "Ruth"],
            "Age": [24, 31],
            "Occupation": ["Debt collector", "Retail"],
            "Hometown": ["Bradford", "Poynton"],
        }
    )

    assert find_bakers_table([df_wrong]) is None
    found = find_bakers_table([df_wrong, df_bakers])
    assert found is not None
    assert "Baker" in found.columns


def test_find_elimination_matrix():
    """Test identifying elimination matrix table."""
    df_wrong = pd.DataFrame({"Baker": ["Edd"], "Age": [24]})
    df_matrix = pd.DataFrame(
        {
            "Baker": ["Edd", "Ruth"],
            "1": ["SAFE", "SAFE"],
            "2": ["STAR", "SAFE"],
            "3": ["WINNER", "RUNNER"],
        }
    )

    assert find_elimination_matrix([df_wrong]) is None
    found = find_elimination_matrix([df_wrong, df_matrix])
    assert found is not None
    assert "1" in found.columns


def test_extract_placements_from_matrix():
    """Test extracting placements dictionary from elimination matrix."""
    df_matrix = pd.DataFrame(
        {
            "Baker": ["Edd Kimber", "Ruth Clemens", "Lea Harris"],
            "1": ["SAFE", "SAFE", "OUT"],
            "2": ["SAFE", "SAFE", "None"],
            "3": ["WINNER", "RUNNER-UP", "None"],
        }
    )

    placements = extract_placements_from_matrix(df_matrix)
    assert placements.get("edd") == 1
    assert placements.get("ruth") == 2
    assert placements.get("lea") == 3


def test_extract_bakers_single_and_multiindex():
    """Test extracting baker dictionaries from single and multi-level tables."""
    df_single = pd.DataFrame(
        {
            "Baker": ["Edd Kimber", "Total"],
            "Age": ["24", ""],
            "Occupation": ["Debt collector", ""],
            "Hometown": ["Bradford", ""],
            "Finish": ["Winner", ""],
        }
    )

    bakers = extract_bakers(1, df_single)
    assert len(bakers) == 1
    assert bakers[0]["name"] == "Edd Kimber"
    assert bakers[0]["age"] == 24
    assert bakers[0]["overall_placement"] == 1

    # Missing baker column raises ValueError
    with pytest.raises(ValueError, match="Could not find baker"):
        extract_bakers(1, pd.DataFrame({"Foo": [1]}))

    # MultiIndex columns
    cols = pd.MultiIndex.from_tuples(
        [("Info", "Baker"), ("Info", "Age"), ("Info", "Town")]
    )
    df_multi = pd.DataFrame([["Nadiya Hussain", "30", "Leeds"]], columns=cols)
    bakers_multi = extract_bakers(6, df_multi, matrix_placements={"nadiya": 1})
    assert len(bakers_multi) == 1
    assert bakers_multi[0]["name"] == "Nadiya Hussain"
    assert bakers_multi[0]["overall_placement"] == 1


def test_extract_air_dates():
    """Test air dates extraction from ratings table or infobox."""
    ratings_html = """
    <div>
        <h3>Ratings</h3>
        <table>
            <tr><th>Episode</th><th>Air date</th></tr>
            <tr><td>1</td><td>17 August 2010</td></tr>
            <tr><td>2</td><td>24 August 2010</td></tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(ratings_html, "html.parser")
    dates = extract_air_dates(soup)
    assert dates.get(1) == "2010-08-17"
    assert dates.get(2) == "2010-08-24"

    # Infobox fallback
    infobox_html = """
    <table class="infobox">
        <tr><th>Original release</th><td>17 August 2010</td></tr>
    </table>
    """
    soup_info = BeautifulSoup(infobox_html, "html.parser")
    dates_info = extract_air_dates(soup_info)
    assert dates_info.get(1) == "2010-08-17"


def test_resolve_baker_id():
    """Test matching baker names to canonical baker_id."""
    bakers = [
        {"baker_id": "s01_edd", "name": "Edd Kimber"},
        {"baker_id": "s01_ruth", "name": "Ruth Clemens"},
    ]

    assert resolve_baker_id(1, "Edd", bakers) == "s01_edd"
    assert resolve_baker_id(1, "Edd Kimber", bakers) == "s01_edd"
    assert resolve_baker_id(1, "Ruth", bakers) == "s01_ruth"
    # Unmatched fallback
    assert resolve_baker_id(1, "Unknown Person", bakers) == "s01_unknown"


def test_extract_episodes_and_performances():
    """Test extracting episodes and performances from Wikipedia challenge tables."""
    page_html = """
    <div>
        <h3>Episode 1: Cakes</h3>
        <table>
            <tr>
                <th>Baker</th>
                <th>Signature</th>
                <th>Technical</th>
                <th>Showstopper</th>
                <th>Result</th>
            </tr>
            <tr>
                <td>Edd</td>
                <td>Carrot Cake</td>
                <td>1st</td>
                <td>Victoria Sponge</td>
                <td>Star Baker</td>
            </tr>
            <tr>
                <td>Ruth</td>
                <td>Lemon Cake</td>
                <td>2nd</td>
                <td>Chocolate Fudge</td>
                <td>Safe</td>
            </tr>
            <tr>
                <td>Lea</td>
                <td>Fruit Cake</td>
                <td>10th</td>
                <td>Dry Cake</td>
                <td>Eliminated</td>
            </tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(page_html, "html.parser")
    tables = pd.read_html(io.StringIO(page_html))
    bakers = [
        {"baker_id": "s01_edd", "name": "Edd"},
        {"baker_id": "s01_ruth", "name": "Ruth"},
        {"baker_id": "s01_lea", "name": "Lea"},
    ]

    episodes, perfs = extract_episodes_and_performances(1, soup, tables, bakers=bakers)
    assert len(episodes) == 1
    assert episodes[0]["episode_number"] == 1
    assert episodes[0]["theme"] == "Cakes"
    assert len(perfs) == 3

    edd_perf = next(p for p in perfs if p["baker_id"] == "s01_edd")
    assert edd_perf["technical_rank"] == 1
    assert edd_perf["result"] == "STAR_BAKER"

    lea_perf = next(p for p in perfs if p["baker_id"] == "s01_lea")
    assert lea_perf["technical_rank"] == 10
    assert lea_perf["result"] == "ELIMINATED"


def test_scrape_series_orchestration(tmp_path: Path):
    """Test scrape_series saves JSON raw files."""
    sample_html = """
    <html>
    <body>
        <table>
            <tr><th>Baker</th><th>Age</th><th>Occupation</th><th>Hometown</th><th>Result</th></tr>
            <tr><td>Edd Kimber</td><td>24</td><td>Debt collector</td><td>Bradford</td><td>Winner</td></tr>
        </table>
        <table>
            <tr><th>Baker</th><th>1</th></tr>
            <tr><td>Edd Kimber</td><td>WINNER</td></tr>
        </table>
        <h3>Episode 1: Cakes</h3>
        <table>
            <tr><th>Baker</th><th>Signature</th><th>Technical</th><th>Showstopper</th><th>Result</th></tr>
            <tr><td>Edd</td><td>Sponge</td><td>1st</td><td>Layer Cake</td><td>Winner</td></tr>
        </table>
    </body>
    </html>
    """
    with patch("gbbo_dataset.scraper.fetch_series_html", return_value=sample_html):
        result = scrape_series(1, raw_dir=tmp_path)
        assert result["series"] == 1
        assert len(result["bakers"]) == 1
        assert (tmp_path / "series_1_bakers.json").exists()
        assert (tmp_path / "series_1_episodes.json").exists()
        assert (tmp_path / "series_1_performances.json").exists()

        # Also test default raw_dir
        with patch("pathlib.Path.mkdir"), patch("builtins.open", mock_open()):
            res_default = scrape_series(1)
            assert res_default["series"] == 1


def test_scraper_main_cli(tmp_path: Path):
    """Test main function CLI arguments handling."""
    with (
        patch("sys.argv", ["gbbo-scrape", "--series", "1", "-o", str(tmp_path)]),
        patch("gbbo_dataset.scraper.scrape_series") as mock_scrape,
    ):
        main()
        mock_scrape.assert_called_once_with(1, tmp_path)

    with (
        patch(
            "sys.argv",
            [
                "gbbo-scrape",
                "--start",
                "1",
                "--end",
                "2",
                "-o",
                str(tmp_path),
            ],
        ),
        patch("gbbo_dataset.scraper.scrape_series") as mock_scrape,
    ):
        main()
        assert mock_scrape.call_count == 2
