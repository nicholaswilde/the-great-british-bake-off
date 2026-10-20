"""Unit tests for the interactive Streamlit dashboard and its CLI integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.dashboard.data import (
    _get_data_dir,
    load_all_datasets,
    load_empirical_bake_metrics,
    load_table,
)
from gbbo_dataset.dashboard.views.baker_profiles import render_baker_profiles
from gbbo_dataset.dashboard.views.challenge_analytics import render_challenge_analytics
from gbbo_dataset.dashboard.views.exploratory_analysis import (
    render_exploratory_analysis,
)
from gbbo_dataset.dashboard.views.handshake_tracker import render_handshake_tracker
from gbbo_dataset.dashboard.views.overview import render_overview
from gbbo_dataset.dashboard.views.predictor_view import render_predictor_view

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
        patch("streamlit.radio", return_value="👤 Individual Baker Profile"),
        patch("streamlit.selectbox", side_effect=[1, "Edd Kimber"]),
    ):
        render_baker_profiles(mock_data)


def test_render_baker_profiles_geography_view():
    """Test baker profiles geography and map view."""
    mock_data = _get_mock_datasets()
    mock_data["bakers"]["latitude"] = [53.7960]
    mock_data["bakers"]["longitude"] = [-1.7594]
    mock_data["bakers"]["country"] = ["England"]
    mock_data["bakers"]["county_region"] = ["West Yorkshire"]
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🗺️ Baker Geography & UK Map"),
        patch("streamlit.selectbox", return_value="All Series (1–17)"),
        patch("streamlit.map") as mock_map,
    ):
        render_baker_profiles(mock_data)
        mock_map.assert_called_once()


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


def test_render_predictor_view_series_forecast():
    """Test predictor view renders series forecast mode."""
    mock_data = _get_mock_datasets()
    # Mark winner as None to exercise in-progress formatting branch
    mock_data["seasons"].loc[0, "winner"] = None
    mock_pred_results = {
        "series": 1,
        "current_episode": 1,
        "next_episode": 2,
        "total_bakers": 1,
        "active_bakers_count": 1,
        "eliminated_bakers_count": 0,
        "rankings": [
            {
                "baker_id": "s01_edd",
                "name": "Edd Kimber",
                "age": 24,
                "status": "Active",
                "is_active": True,
                "is_eliminated": False,
                "is_withdrew": False,
                "episodes_competed": 1,
                "avg_technical_pct": 1.0,
                "last_technical_rank": 1,
                "last_technical_pct": 1.0,
                "star_baker_count": 1,
                "handshake_count": 1,
                "did_well_count": 0,
                "at_risk_count": 0,
                "last_star_baker": True,
                "last_did_well": False,
                "last_at_risk": False,
                "last_handshake": True,
                "age_score": 0.95,
                "star_baker_prob": 75.0,
                "elimination_risk": 5.0,
                "win_probability": 65.0,
                "top3_probability": 95.0,
            }
        ],
        "completed_episodes": ["s01e01"],
        "historical_baselines": {},
    }
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", return_value=1),
        patch(
            "gbbo_dataset.dashboard.views.predictor_view.SeriesPredictor"
        ) as mock_predictor_cls,
    ):
        mock_predictor = MagicMock()
        mock_predictor.predict_series.return_value = mock_pred_results
        mock_predictor_cls.return_value = mock_predictor
        render_predictor_view(mock_data)


def test_predictor_diagnostics_and_empty():
    """Verify _compute_diagnostics extracts strengths and risks across branches."""
    from gbbo_dataset.dashboard.views.predictor_view import _compute_diagnostics

    # Strengths heavy baker
    strong_baker = {
        "star_baker_count": 2,
        "handshake_count": 2,
        "avg_technical_pct": 0.85,
        "last_star_baker": True,
        "last_handshake": True,
        "age": 28,
        "age_score": 0.9,
        "episodes_competed": 4,
        "at_risk_count": 0,
        "did_well_count": 3,
    }
    strengths, risks = _compute_diagnostics(strong_baker)
    assert len(strengths) >= 6
    assert len(risks) == 0

    # Risk heavy baker
    risky_baker = {
        "star_baker_count": 0,
        "handshake_count": 0,
        "avg_technical_pct": 0.25,
        "last_star_baker": False,
        "last_handshake": False,
        "last_at_risk": True,
        "episodes_competed": 5,
        "at_risk_count": 3,
        "did_well_count": 0,
    }
    strengths, risks = _compute_diagnostics(risky_baker)
    assert len(strengths) == 0
    assert len(risks) >= 5

    # Empty seasons branch
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", return_value=1),
    ):
        render_predictor_view({})


def test_render_predictor_view_branches():
    """Test predictor view error branches, slider time-travel, and empty rankings."""
    # 1. Prediction throws error
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", return_value=1),
        patch("streamlit.error") as mock_err,
        patch(
            "gbbo_dataset.dashboard.views.predictor_view.SeriesPredictor"
        ) as mock_cls,
    ):
        mock_cls.return_value.predict_series.side_effect = RuntimeError(
            "Prediction fail"
        )
        render_predictor_view({})
        mock_err.assert_called_once()

    # 2. Rankings empty
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", return_value=1),
        patch("streamlit.warning") as mock_warn,
        patch(
            "gbbo_dataset.dashboard.views.predictor_view.SeriesPredictor"
        ) as mock_cls,
    ):
        mock_cls.return_value.predict_series.return_value = {
            "current_episode": 1,
            "rankings": [],
        }
        render_predictor_view({})
        mock_warn.assert_called_once()

    # 3. Slider time-travel (selected_ep != max_ep) and baker diagnostics
    dummy_rankings = [
        {
            "name": "Baker A",
            "age": 30,
            "win_probability": 0.45,
            "star_baker_prob": 0.50,
            "elimination_risk": 0.05,
            "predicted_rank": 1,
            "momentum_score": 12.5,
            "status": "Active",
            "star_baker_count": 2,
            "handshake_count": 1,
            "avg_technical_pct": 0.85,
            "last_star_baker": True,
            "last_handshake": False,
            "last_at_risk": False,
            "episodes_competed": 4,
            "at_risk_count": 0,
            "did_well_count": 3,
        }
    ]
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", side_effect=[1, "Baker A"]),
        patch("streamlit.slider", return_value=2),
        patch("streamlit.tabs", return_value=[MagicMock(), MagicMock(), MagicMock()]),
        patch(
            "gbbo_dataset.dashboard.views.predictor_view.SeriesPredictor"
        ) as mock_cls,
    ):
        mock_inst = MagicMock()
        mock_inst.predict_series.side_effect = [
            {"current_episode": 4, "total_bakers": 12, "rankings": dummy_rankings},
            {"current_episode": 2, "total_bakers": 12, "rankings": dummy_rankings},
        ]
        mock_cls.return_value = mock_inst
        render_predictor_view({})
        assert mock_inst.predict_series.call_count == 2


def test_render_predictor_view_custom_simulator():
    """Test predictor view renders custom what-if simulator mode."""
    mock_data = _get_mock_datasets()
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.radio", return_value="🧪 Custom Baker 'What-If' Simulator"),
        patch("streamlit.slider", side_effect=[30, 4, 0.65]),
        patch("streamlit.number_input", side_effect=[1, 1, 0, 1]),
        patch("streamlit.checkbox", return_value=False),
        patch(
            "gbbo_dataset.dashboard.views.predictor_view.SeriesPredictor"
        ) as mock_predictor_cls,
    ):
        mock_predictor = MagicMock()
        mock_predictor.baselines = {"winner_mean_age": 32.5, "winner_std_age": 9.89}
        mock_predictor_cls.return_value = mock_predictor
        render_predictor_view(mock_data)


def test_dashboard_main_router():
    """Test main router function renders views with emoji-prefixed and plain names."""
    from gbbo_dataset.dashboard.app import main

    mock_data = _get_mock_datasets()
    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="🍰 Series Overview"),
        patch("gbbo_dataset.dashboard.app.render_overview") as mock_overview,
    ):
        main()
        mock_overview.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="👤 Baker Profiles"),
        patch("gbbo_dataset.dashboard.app.render_baker_profiles") as mock_bakers,
    ):
        main()
        mock_bakers.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="⚖️ Challenge Analytics"),
        patch(
            "gbbo_dataset.dashboard.app.render_challenge_analytics"
        ) as mock_challenges,
    ):
        main()
        mock_challenges.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="🤝 Hollywood Handshakes"),
        patch("gbbo_dataset.dashboard.app.render_handshake_tracker") as mock_handshakes,
    ):
        main()
        mock_handshakes.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="🔮 Predictions & Forecasting"),
        patch(
            "gbbo_dataset.dashboard.app.render_predictor_view"
        ) as mock_predictor_view,
    ):
        main()
        mock_predictor_view.assert_called_once_with(mock_data)

    with (
        patch("gbbo_dataset.dashboard.app.load_all_datasets", return_value=mock_data),
        patch("streamlit.sidebar.radio", return_value="📈 Exploratory Analysis"),
        patch(
            "gbbo_dataset.dashboard.app.render_exploratory_analysis"
        ) as mock_exploratory,
    ):
        main()
        mock_exploratory.assert_called_once_with(mock_data)


def test_render_exploratory_analysis_view():
    """Test Exploratory Analysis view rendering, metrics computation, and empty handling."""
    with patch("streamlit.warning") as mock_warning:
        render_exploratory_analysis({})
        mock_warning.assert_called_once()

    # Test empirical bake metrics computation
    metrics_all = load_empirical_bake_metrics(era="ALL")
    assert "survival_curve" in metrics_all
    assert "age_summary" in metrics_all
    assert "star_baker_conversion" in metrics_all
    assert "week1_star_bakers" in metrics_all
    assert "handshake_total" in metrics_all
    assert "tech_bottom2_hazard_pct" in metrics_all
    assert "theme_hazards" in metrics_all
    assert metrics_all["handshake_total"] == 60
    assert metrics_all["tech_bottom2_hazard_pct"] > 20.0

    # Test BBC vs Channel 4 era filtering
    metrics_bbc = load_empirical_bake_metrics(era="BBC Era (S1–S7)")
    metrics_c4 = load_empirical_bake_metrics(era="Channel 4 Era (S8+)")
    assert metrics_bbc["handshake_total"] == 9
    assert metrics_c4["handshake_total"] == 51

    # Test rendering with real datasets
    real_data = load_all_datasets()
    mock_tab = MagicMock()
    mock_tab.__enter__.return_value = mock_tab
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", return_value="ALL"),
        patch("streamlit.tabs", return_value=[mock_tab] * 5),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe") as mock_df,
    ):
        render_exploratory_analysis(real_data)
        assert mock_chart.call_count >= 5
        assert mock_df.call_count >= 1


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
