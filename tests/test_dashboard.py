"""Unit tests for the interactive Streamlit dashboard and its CLI integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.dashboard.data import _get_data_dir, load_all_datasets, load_table
from gbbo_dataset.dashboard.views.baker_profiles import render_baker_profiles
from gbbo_dataset.dashboard.views.challenge_analytics import render_challenge_analytics
from gbbo_dataset.dashboard.views.handshake_tracker import render_handshake_tracker
from gbbo_dataset.dashboard.views.overview import render_overview

runner = CliRunner()


def test_dashboard_data_loading(tmp_path: Path):
    """Test loading tables from Parquet or CSV."""
    df_empty = load_table("nonexistent_table", data_dir=tmp_path)
    assert df_empty.empty

    # Test loading parquet
    sample_df = pd.DataFrame([{"series_number": 1, "winner": "Edd"}])
    parquet_path = tmp_path / "seasons.parquet"
    sample_df.to_parquet(parquet_path)

    loaded = load_table("seasons", data_dir=tmp_path)
    assert not loaded.empty
    assert len(loaded) == 1
    assert loaded["series_number"].iloc[0] == 1

    # Test loading csv fallback
    csv_df = pd.DataFrame([{"baker_id": "s01_edd", "name": "Edd Kimber"}])
    csv_path = tmp_path / "bakers.csv"
    csv_df.to_csv(csv_path, index=False)

    loaded_csv = load_table("bakers", data_dir=tmp_path)
    assert not loaded_csv.empty
    assert loaded_csv["name"].iloc[0] == "Edd Kimber"

    # Test load_all_datasets
    all_dfs = load_all_datasets(data_dir=tmp_path)
    assert "seasons" in all_dfs
    assert "bakers" in all_dfs
    assert "episodes" in all_dfs
    assert "performances" in all_dfs


def test_get_data_dir(tmp_path: Path, monkeypatch):
    """Test resolving data directory with fallback and env var."""
    monkeypatch.setenv("GBBO_DATA_DIR", str(tmp_path))
    assert _get_data_dir() == tmp_path

    monkeypatch.delenv("GBBO_DATA_DIR", raising=False)
    resolved = _get_data_dir()
    assert isinstance(resolved, Path)


def _get_mock_datasets() -> dict[str, pd.DataFrame]:
    """Provide minimal mock datasets for view testing."""
    seasons = pd.DataFrame(
        [
            {
                "series_number": 1,
                "year": 2010,
                "winner": "Edd Kimber",
                "hosts": "Mel and Sue",
                "judges": "Mary and Paul",
                "network": "BBC Two",
                "location": "Various",
                "pbs_season": 1,
                "netflix_collection": 1,
                "roku_season": 1,
            }
        ]
    )
    bakers = pd.DataFrame(
        [
            {
                "baker_id": "s01_edd",
                "series_number": 1,
                "name": "Edd Kimber",
                "age": 24,
                "occupation": "Debt collector",
                "hometown": "Bradford",
                "overall_placement": 1,
                "image_url": "https://example.com/edd.jpg",
            }
        ]
    )
    episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cakes",
                "air_date": "2010-08-17",
                "signature_time_min": 120.0,
                "technical_time_min": 60.0,
                "showstopper_time_min": 240.0,
            }
        ]
    )
    performances = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_edd",
                "baker_id": "s01_edd",
                "episode_id": "s01e01",
                "signature_dish": "Chocolate Cake",
                "technical_rank": 1,
                "showstopper_dish": "Celebration Cake",
                "result": "STAR_BAKER",
                "hollywood_handshake": True,
            }
        ]
    )
    return {
        "seasons": seasons,
        "bakers": bakers,
        "episodes": episodes,
        "performances": performances,
    }


def _mock_columns(spec):
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]


def test_render_overview_view():
    """Test overview page renders without errors."""
    mock_data = _get_mock_datasets()
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", return_value=1),
    ):
        render_overview(mock_data)


def test_render_baker_profiles_view():
    """Test baker profiles page renders without errors."""
    mock_data = _get_mock_datasets()
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", side_effect=[1, "Edd Kimber"]),
    ):
        render_baker_profiles(mock_data)


def test_render_challenge_analytics_view():
    """Test challenge analytics page renders without errors."""
    mock_data = _get_mock_datasets()
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.text_input", return_value="chocolate"),
    ):
        render_challenge_analytics(mock_data)


def test_render_handshake_tracker_view():
    """Test Hollywood Handshake tracker page renders without errors."""
    mock_data = _get_mock_datasets()
    with patch("streamlit.columns", side_effect=_mock_columns):
        render_handshake_tracker(mock_data)


def test_dashboard_main_router():
    """Test main router function renders views."""
    from gbbo_dataset.dashboard.app import main

    mock_data = _get_mock_datasets()
    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="Series Overview"),
        patch("gbbo_dataset.dashboard.app.render_overview") as mock_overview,
    ):
        main()
        mock_overview.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="Baker Profiles"),
        patch("gbbo_dataset.dashboard.app.render_baker_profiles") as mock_bakers,
    ):
        main()
        mock_bakers.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="Challenge Analytics"),
        patch(
            "gbbo_dataset.dashboard.app.render_challenge_analytics"
        ) as mock_challenges,
    ):
        main()
        mock_challenges.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="Hollywood Handshakes"),
        patch("gbbo_dataset.dashboard.app.render_handshake_tracker") as mock_handshakes,
    ):
        main()
        mock_handshakes.assert_called_once_with(mock_data)


def test_cli_dashboard_command():
    """Test launching dashboard CLI command."""
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(
            app, ["dashboard", "--no-browser", "--port", "8502", "--host", "127.0.0.1"]
        )
        assert result.exit_code == 0
        assert mock_run.called
        args = mock_run.call_args[0][0]
        assert "streamlit" in args
        assert "--server.port" in args
        assert "8502" in args
        assert "--server.address" in args
        assert "127.0.0.1" in args
        assert "--server.headless" in args
