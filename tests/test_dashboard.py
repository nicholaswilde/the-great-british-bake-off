"""Unit tests for the interactive Streamlit dashboard and its CLI integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.dashboard.data import (
    _get_data_dir,
    classify_occupation,
    compute_baker_skills,
    compute_champion_benchmark,
    compute_occupational_metrics,
    compute_recipe_difficulty_and_sentiment_metrics,
    compute_time_pressure_metrics,
    compute_underdog_and_upset_metrics,
    load_all_datasets,
    load_empirical_bake_metrics,
    load_table,
)
from gbbo_dataset.dashboard.views.baker_profiles import (
    _render_individual_baker,
    generate_radar_svg,
    render_baker_profiles,
)
from gbbo_dataset.dashboard.views.challenge_analytics import render_challenge_analytics
from gbbo_dataset.dashboard.views.exploratory_analysis import (
    _render_demographics_tab,
    _render_star_baker_tab,
    _render_technical_tab,
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
    assert "social_discussions" in metrics_all
    assert "social_summary" in metrics_all
    assert "host_era_sentiment" in metrics_all
    assert metrics_all["handshake_total"] == 60
    assert metrics_all["tech_bottom2_hazard_pct"] > 20.0
    assert metrics_all["social_summary"]["total_threads"] >= 16
    assert metrics_all["social_summary"]["peak_controversy"] > 500

    # Test BBC vs Channel 4 era filtering
    metrics_bbc = load_empirical_bake_metrics(era="BBC Era (S1–S7)")
    metrics_c4 = load_empirical_bake_metrics(era="Channel 4 Era (S8+)")
    assert metrics_bbc["handshake_total"] == 9
    assert metrics_c4["handshake_total"] == 51
    assert len(metrics_bbc["social_discussions"]) > 0
    assert len(metrics_c4["social_discussions"]) > 0

    # Test rendering with real datasets
    real_data = load_all_datasets()
    mock_tab = MagicMock()
    mock_tab.__enter__.return_value = mock_tab
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", return_value="ALL"),
        patch("streamlit.tabs", return_value=[mock_tab] * 6),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe") as mock_df,
    ):
        render_exploratory_analysis(real_data)
        assert mock_chart.call_count >= 6
        assert mock_df.call_count >= 1


def test_compute_social_sentiment_metrics_and_render_tab():
    """Verify compute_social_sentiment_metrics edge cases and _render_social_reception_tab."""
    from gbbo_dataset.dashboard.data import compute_social_sentiment_metrics
    from gbbo_dataset.dashboard.views.exploratory_analysis import (
        _render_social_reception_tab,
    )

    # Empty raw data
    res_empty = compute_social_sentiment_metrics({})
    assert res_empty["social_discussions"].empty
    assert res_empty["social_summary"]["total_threads"] == 0

    # Populated mock data
    mock_reddit = pd.DataFrame(
        [
            {
                "thread_id": "s05e04_disc",
                "subreddit": "GreatBritishBakeOff",
                "series_number": 5,
                "episode_number": 4,
                "title": "Bingate Discussion",
                "score": 1200,
                "upvote_ratio": 0.94,
                "num_comments": 500,
                "sentiment_label": "Critical",
            }
        ]
    )
    mock_seasons = pd.DataFrame(
        [
            {
                "series_number": 5,
                "hosts": "Mel Giedroyc, Sue Perkins",
                "judges": "Mary Berry, Paul Hollywood",
                "network": "BBC One",
                "year": 2014,
            }
        ]
    )
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s05e04",
                "series_number": 5,
                "episode_number": 4,
                "theme": "Desserts",
            }
        ]
    )
    mock_perf = pd.DataFrame(
        [
            {
                "performance_id": "s05e04_iain",
                "baker_id": "s05_iain",
                "episode_id": "s05e04",
                "result": "WITHDREW",
            }
        ]
    )
    mock_bakers = pd.DataFrame(
        [
            {
                "baker_id": "s05_iain",
                "name": "Iain Watters",
                "series_number": 5,
            }
        ]
    )
    raw = {
        "reddit_discussions": mock_reddit,
        "seasons": mock_seasons,
        "episodes": mock_episodes,
        "performances": mock_perf,
        "bakers": mock_bakers,
    }
    res = compute_social_sentiment_metrics(raw, era="ALL")
    assert not res["social_discussions"].empty
    assert res["social_summary"]["total_threads"] == 1
    assert res["social_summary"]["peak_controversy"] > 0
    assert "Mel Giedroyc & Sue Perkins" in res["host_era_sentiment"]["host_duo"].values

    # Test rendering tab with empty bundle
    with patch("streamlit.info") as mock_info:
        _render_social_reception_tab({}, era="ALL")
        mock_info.assert_called_once()

    # Test rendering tab with populated bundle
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe") as mock_df,
    ):
        _render_social_reception_tab(res, era="ALL")
        assert mock_chart.call_count >= 2
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


def test_occupational_classification_and_metrics():
    """Test occupation categorization and archetype performance calculations."""
    # Test classifier mappings
    assert classify_occupation("Aerospace Engineer") == "STEM & Engineering"
    assert classify_occupation("Software developer") == "STEM & Engineering"
    assert classify_occupation("Doctor") == "Healthcare & Medicine"
    assert classify_occupation("Veterinary surgeon") == "Healthcare & Medicine"
    assert classify_occupation("High school teacher") == "Education & Academia"
    assert classify_occupation("Accountant") == "Finance, Law & Corporate"
    assert classify_occupation("Graphic Designer") == "Creative, Arts & Media"
    assert classify_occupation("Builder") == "Public Service & Trades"
    assert classify_occupation("University student") == "Students & Homemakers"
    assert classify_occupation("Housewife") == "Students & Homemakers"
    assert classify_occupation(None) == "Other & Unclassified"
    assert classify_occupation("") == "Other & Unclassified"

    # Test empty inputs
    empty_res = compute_occupational_metrics(pd.DataFrame(), pd.DataFrame())
    assert empty_res.empty

    # Test mock dataframe calculation
    mock_bakers = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "name": "Alice STEM",
                "occupation": "Software Engineer",
                "overall_placement": 1,
            },
            {
                "baker_id": "b2",
                "name": "Bob STEM",
                "occupation": "Chemist",
                "overall_placement": 2,
            },
            {
                "baker_id": "b3",
                "name": "Charlie Arts",
                "occupation": "Artist",
                "overall_placement": 5,
            },
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "episode_id": "e1",
                "technical_rank": 1,
                "result": "STAR_BAKER",
                "hollywood_handshake": 1,
            },
            {
                "baker_id": "b2",
                "episode_id": "e1",
                "technical_rank": 2,
                "result": "SAFE",
                "hollywood_handshake": 0,
            },
            {
                "baker_id": "b3",
                "episode_id": "e1",
                "technical_rank": 4,
                "result": "SAFE",
                "hollywood_handshake": 0,
            },
        ]
    )
    occ_df = compute_occupational_metrics(mock_bakers, mock_perfs)
    assert not occ_df.empty
    assert "STEM & Engineering" in occ_df["cluster"].values
    stem_row = occ_df[occ_df["cluster"] == "STEM & Engineering"].iloc[0]
    assert stem_row["total_bakers"] == 2
    assert stem_row["champions"] == 1
    assert stem_row["win_rate"] == 50.0
    assert stem_row["finalists"] == 2
    assert stem_row["finalist_rate"] == 100.0
    assert stem_row["star_bakers"] == 1
    assert stem_row["handshakes"] == 1


def test_baker_skills_and_benchmark():
    """Test 5-axis baker skill calculation, champion benchmark, and SVG generator."""
    # Test fallback on empty data
    empty_skills = compute_baker_skills("unknown", pd.DataFrame())
    assert len(empty_skills) == 5
    assert empty_skills["Technical Mastery"] == 50.0

    # Test fallback benchmark
    empty_bench = compute_champion_benchmark(pd.DataFrame(), pd.DataFrame())
    assert len(empty_bench) == 5
    assert "Technical Mastery" in empty_bench

    # Test with mock performances
    mock_perfs = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "episode_id": "e1",
                "technical_rank": 1,
                "result": "STAR_BAKER",
                "hollywood_handshake": 1,
                "at_risk": False,
                "did_well": True,
            },
            {
                "baker_id": "b1",
                "episode_id": "e2",
                "technical_rank": 2,
                "result": "SAFE",
                "hollywood_handshake": 0,
                "at_risk": False,
                "did_well": False,
            },
            {
                "baker_id": "b1",
                "episode_id": "e3",
                "technical_rank": 3,
                "result": "SAFE",
                "hollywood_handshake": 1,
                "at_risk": False,
                "did_well": True,
            },
        ]
    )
    b1_skills = compute_baker_skills("b1", mock_perfs)
    assert 0.0 <= b1_skills["Technical Mastery"] <= 100.0
    assert 0.0 <= b1_skills["Star Baker Clout"] <= 100.0
    assert 0.0 <= b1_skills["Handshake Conversion"] <= 100.0
    assert 0.0 <= b1_skills["Risk Avoidance"] <= 100.0
    assert 0.0 <= b1_skills["Showstopper Consistency"] <= 100.0

    mock_bakers = pd.DataFrame(
        [
            {"baker_id": "b1", "overall_placement": 1},
        ]
    )
    bench = compute_champion_benchmark(mock_bakers, mock_perfs)
    assert len(bench) == 5

    # Test SVG generator
    svg = generate_radar_svg("Alice", b1_skills, bench)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Alice" in svg
    assert "Technical Mastery" in svg
    assert "Champion Avg" in svg


def test_occupational_views_rendering():
    """Test demographics occupational archetype section and individual baker radar rendering."""
    mock_bakers = pd.DataFrame(
        [
            {
                "baker_id": "s01_edd",
                "series_number": 1,
                "name": "Edd Kimber",
                "age": 24,
                "occupation": "Debt collector",
                "hometown": "Bradford",
                "overall_placement": 1,
            }
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "baker_id": "s01_edd",
                "episode_id": "s01e01",
                "signature_dish": "Lemon Tart",
                "showstopper_dish": "Chocolate Tier",
                "technical_rank": 1,
                "result": "STAR_BAKER",
                "hollywood_handshake": 1,
                "at_risk": False,
                "did_well": True,
            }
        ]
    )
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
            }
        ]
    )
    occ_df = compute_occupational_metrics(mock_bakers, mock_perfs)
    metrics_bundle = {
        "total_bakers": 1,
        "survival_curve": pd.DataFrame([{"episode_number": 1, "survival_pct": 100}]),
        "age_summary": pd.DataFrame(),
        "gender_summary": pd.DataFrame(),
        "region_summary": pd.DataFrame(),
        "occupation_summary": occ_df,
    }
    raw_datasets = {
        "bakers": mock_bakers,
        "performances": mock_perfs,
        "episodes": mock_episodes,
    }

    # Test _render_demographics_tab with populated occupational metrics
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe") as mock_df,
        patch("streamlit.info") as mock_info,
    ):
        _render_demographics_tab(raw_datasets, metrics_bundle, era="ALL")
        assert mock_chart.call_count >= 1
        assert mock_df.call_count >= 1
        assert mock_info.call_count >= 1

    # Test _render_individual_baker with radar chart
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.selectbox", side_effect=[1, "Edd Kimber"]),
        patch("streamlit.markdown") as mock_md,
        patch("streamlit.metric"),
    ):
        _render_individual_baker(mock_bakers, mock_perfs, mock_episodes)
        # Verify radar SVG was rendered via st.markdown(unsafe_allow_html=True)
        radar_rendered = any(
            "<svg" in str(call.args[0])
            for call in mock_md.call_args_list
            if call.args and isinstance(call.args[0], str)
        )
        assert radar_rendered


def test_time_pressure_metrics():
    """Test challenge duration squeeze and time pressure calculations."""
    # Test empty fallback
    empty_res = compute_time_pressure_metrics(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )
    assert empty_res["series_time_trajectory"].empty
    assert empty_res["era_time_comparison"].empty
    assert empty_res["time_summary"]["shortest_technical"] == "N/A"

    # Test with mock data
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
                "signature_time_min": 150.0,
                "technical_time_min": 90.0,
                "showstopper_time_min": 240.0,
            },
            {
                "episode_id": "s08e01",
                "series_number": 8,
                "episode_number": 1,
                "theme": "Cake",
                "signature_time_min": 120.0,
                "technical_time_min": 120.0,
                "showstopper_time_min": 240.0,
            },
        ]
    )
    mock_seasons = pd.DataFrame(
        [
            {"series_number": 1, "network": "BBC Two"},
            {"series_number": 8, "network": "Channel 4"},
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "episode_id": "s01e01",
                "technical_rank": 1,
                "result": "STAR_BAKER",
            },
            {
                "baker_id": "b2",
                "episode_id": "s01e01",
                "technical_rank": 2,
                "result": "ELIMINATED",
            },
            {
                "baker_id": "b3",
                "episode_id": "s08e01",
                "technical_rank": 1,
                "result": "SAFE",
            },
            {
                "baker_id": "b4",
                "episode_id": "s08e01",
                "technical_rank": 2,
                "result": "ELIMINATED",
            },
        ]
    )

    res = compute_time_pressure_metrics(mock_episodes, mock_perfs, mock_seasons)
    assert not res["series_time_trajectory"].empty
    assert not res["era_time_comparison"].empty
    assert len(res["era_time_comparison"]) == 2
    assert res["time_summary"]["shortest_technical"] == "Cake (90m, S01E01)"
    assert res["time_summary"]["longest_technical"] == "Cake (120m, S08E01)"
    assert res["time_summary"]["bbc_avg_total"] == 480.0
    assert res["time_summary"]["c4_avg_total"] == 480.0
    assert not res["tech_time_brackets"].empty


def test_time_pressure_views_rendering():
    """Test rendering of technical tab with time pressure and challenge analytics."""
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
                "signature_time_min": 150.0,
                "technical_time_min": 90.0,
                "showstopper_time_min": 240.0,
            }
        ]
    )
    mock_seasons = pd.DataFrame([{"series_number": 1, "network": "BBC Two"}])
    mock_perfs = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "episode_id": "s01e01",
                "signature_dish": "Lemon Tart",
                "showstopper_dish": "Chocolate Tier",
                "technical_rank": 1,
                "result": "STAR_BAKER",
            }
        ]
    )
    tp_res = compute_time_pressure_metrics(mock_episodes, mock_perfs, mock_seasons)
    metrics_bundle = {
        "tech_bottom2_hazard_pct": 25.0,
        "tech_other_hazard_pct": 5.0,
        "tech_rank1_to_sb_pct": 33.3,
        "tech_cohorts": pd.DataFrame([{"cohort": "1st Place", "elim_rate": 0.0}]),
        "tech_tiers": pd.DataFrame(
            [{"tier": "1. Champion", "avg_tech_percentile": 75.0}]
        ),
        "time_pressure": tp_res,
    }

    # Test _render_technical_tab with time pressure section
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe") as mock_df,
        patch("streamlit.info") as mock_info,
    ):
        _render_technical_tab(metrics_bundle, era="ALL")
        assert mock_chart.call_count >= 2
        assert mock_df.call_count >= 1
        assert mock_info.call_count >= 1

    # Test render_challenge_analytics with time pressure
    mock_datasets = {
        "episodes": mock_episodes,
        "performances": mock_perfs,
        "seasons": mock_seasons,
        "bakers": pd.DataFrame(
            [{"baker_id": "b1", "name": "Baker 1", "series_number": 1}]
        ),
    }
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
    ):
        render_challenge_analytics(mock_datasets)
        assert mock_chart.call_count >= 2


def test_underdog_and_upset_metrics():
    """Test underdog dynamics, zero-SB champions, and theme upset rates."""
    # Test empty fallback
    empty_res = compute_underdog_and_upset_metrics(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )
    assert empty_res["cohort_trajectories"].empty
    assert empty_res["multi_sb_losers"].empty
    assert empty_res["underdog_summary"]["zero_sb_champion"] == "N/A"

    # Test with populated mock data
    mock_bakers = pd.DataFrame(
        [
            {"baker_id": "b1", "name": "Underdog Winner", "overall_placement": 1},
            {"baker_id": "b2", "name": "Star Baker Runner-up", "overall_placement": 2},
            {"baker_id": "b3", "name": "Early Departed", "overall_placement": 8},
        ]
    )
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
            },
            {
                "episode_id": "s01e02",
                "series_number": 1,
                "episode_number": 2,
                "theme": "Pâtisserie",
            },
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "baker_id": "b1",
                "episode_id": "s01e01",
                "result": "SAFE",
                "technical_rank": 2,
            },
            {
                "performance_id": "p2",
                "baker_id": "b2",
                "episode_id": "s01e01",
                "result": "STAR_BAKER",
                "technical_rank": 1,
            },
            {
                "performance_id": "p3",
                "baker_id": "b3",
                "episode_id": "s01e01",
                "result": "SAFE",
                "technical_rank": 3,
            },
            {
                "performance_id": "p4",
                "baker_id": "b1",
                "episode_id": "s01e02",
                "result": "WINNER",
                "technical_rank": 1,
            },
            {
                "performance_id": "p5",
                "baker_id": "b2",
                "episode_id": "s01e02",
                "result": "RUNNER_UP",
                "technical_rank": 2,
            },
            {
                "performance_id": "p6",
                "baker_id": "b3",
                "episode_id": "s01e02",
                "result": "ELIMINATED",
                "technical_rank": 3,
            },
        ]
    )

    res = compute_underdog_and_upset_metrics(mock_bakers, mock_episodes, mock_perfs)
    assert not res["cohort_trajectories"].empty
    assert "1. Champions" in res["cohort_trajectories"]["cohort"].values
    assert not res["theme_upset_rates"].empty


def test_underdog_views_rendering():
    """Test rendering of underdog arc section in star baker tab and predictor view."""
    mock_bakers = pd.DataFrame(
        [
            {
                "baker_id": "b1",
                "name": "Baker 1",
                "series_number": 1,
                "overall_placement": 1,
                "age": 28,
            },
            {
                "baker_id": "b2",
                "name": "Baker 2",
                "series_number": 1,
                "overall_placement": 2,
                "age": 34,
            },
        ]
    )
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
            },
            {
                "episode_id": "s01e02",
                "series_number": 1,
                "episode_number": 2,
                "theme": "Pâtisserie",
            },
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "baker_id": "b1",
                "episode_id": "s01e01",
                "result": "SAFE",
                "technical_rank": 1,
                "signature_dish": "Cake 1",
                "showstopper_dish": "Cake 2",
            },
            {
                "performance_id": "p2",
                "baker_id": "b2",
                "episode_id": "s01e01",
                "result": "STAR_BAKER",
                "technical_rank": 2,
                "signature_dish": "Cake 3",
                "showstopper_dish": "Cake 4",
            },
            {
                "performance_id": "p3",
                "baker_id": "b1",
                "episode_id": "s01e02",
                "result": "WINNER",
                "technical_rank": 1,
                "signature_dish": "Tart 1",
                "showstopper_dish": "Tart 2",
            },
            {
                "performance_id": "p4",
                "baker_id": "b2",
                "episode_id": "s01e02",
                "result": "RUNNER_UP",
                "technical_rank": 2,
                "signature_dish": "Tart 3",
                "showstopper_dish": "Tart 4",
            },
        ]
    )
    mock_seasons = pd.DataFrame([{"series_number": 1, "network": "BBC Two"}])

    ud_metrics = compute_underdog_and_upset_metrics(
        mock_bakers, mock_episodes, mock_perfs, mock_seasons
    )
    metrics_bundle = {
        "star_baker_conversion": pd.DataFrame(
            [{"star_bakers": 1, "win_rate": 50.0, "finalist_rate": 100.0}]
        ),
        "week1_star_bakers": pd.DataFrame(),
        "star_baker_records": pd.DataFrame(),
        "underdog_metrics": ud_metrics,
    }

    # Test _render_star_baker_tab with underdog arc section
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe"),
        patch("streamlit.info") as mock_info,
    ):
        _render_star_baker_tab(metrics_bundle, era="ALL")
        assert mock_chart.call_count >= 1
        assert mock_info.call_count >= 1

    # Test render_predictor_view with theme upset risk
    mock_datasets = {
        "bakers": mock_bakers,
        "episodes": mock_episodes,
        "performances": mock_perfs,
        "seasons": mock_seasons,
    }
    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.radio", return_value="🏆 Series Forecast"),
        patch("streamlit.selectbox", return_value=1),
        patch("streamlit.dataframe"),
    ):
        render_predictor_view(mock_datasets)
        assert mock_chart.call_count >= 1


def test_recipe_difficulty_and_sentiment_metrics():
    """Test recipe difficulty, judging sentiment polarity, and ambition metrics."""
    # Test empty fallback
    empty_res = compute_recipe_difficulty_and_sentiment_metrics(pd.DataFrame())
    assert empty_res["difficulty_sentiment"].empty
    assert empty_res["difficulty_tier_summary"].empty
    assert empty_res["recipe_summary"]["most_difficult_recipe"] == "N/A"

    # Test with populated mock data
    mock_recipes = pd.DataFrame(
        [
            {
                "recipe_id": "r1",
                "series_number": 1,
                "episode_number": 1,
                "challenge_type": "Technical",
                "dish_name": "Scones",
                "difficulty": "Easy",
                "judging_notes": "Judged for golden crust, soft crumb, and height.",
                "recipe_url": "https://example.com/scones",
            },
            {
                "recipe_id": "r2",
                "series_number": 1,
                "episode_number": 2,
                "challenge_type": "Showstopper",
                "dish_name": "Baked Alaska",
                "difficulty": "Extreme",
                "judging_notes": "Completely melted and collapsed.",
                "recipe_url": "https://example.com/alaska",
            },
        ]
    )
    mock_lore = pd.DataFrame(
        [
            {
                "series_number": 1,
                "episode_number": 1,
                "famous_quotes": "['A good biscuit must have a clean snap.']",
            },
            {
                "series_number": 1,
                "episode_number": 2,
                "famous_quotes": "['No one likes a soggy bottom.']",
            },
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "baker_id": "b1",
                "signature_dish": "Apple Tart",
                "showstopper_dish": "Choux Macaron Entremet Tower",
                "result": "STAR_BAKER",
                "hollywood_handshake": True,
                "did_well": True,
                "at_risk": False,
            },
            {
                "performance_id": "p2",
                "baker_id": "b2",
                "signature_dish": "Simple Bread",
                "showstopper_dish": "Plain Cake",
                "result": "ELIMINATED",
                "hollywood_handshake": False,
                "did_well": False,
                "at_risk": True,
            },
        ]
    )
    mock_nlp = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "all_flavors": "apple, caramel, chocolate",
                "all_styles": "pastry_choux, entremet",
            },
            {
                "performance_id": "p2",
                "all_flavors": "vanilla",
                "all_styles": "cake_sponge",
            },
        ]
    )

    res = compute_recipe_difficulty_and_sentiment_metrics(
        recipes=mock_recipes,
        lore=mock_lore,
        performances=mock_perfs,
        bakes_nlp=mock_nlp,
    )

    assert not res["difficulty_sentiment"].empty
    assert len(res["difficulty_sentiment"]) == 2
    # Easy recipe should have positive sentiment
    easy_row = res["difficulty_sentiment"][
        res["difficulty_sentiment"]["difficulty"] == "Easy"
    ].iloc[0]
    assert easy_row["sentiment_score"] > 0
    assert easy_row["sentiment_label"] == "Positive"

    # Extreme recipe should have critical sentiment
    ext_row = res["difficulty_sentiment"][
        res["difficulty_sentiment"]["difficulty"] == "Extreme"
    ].iloc[0]
    assert ext_row["sentiment_score"] < 0
    assert ext_row["sentiment_label"] == "Critical"

    assert not res["difficulty_tier_summary"].empty
    assert not res["challenge_type_complexity"].empty
    assert not res["ambition_outcomes"].empty
    assert res["recipe_summary"]["most_difficult_recipe"] == "Baked Alaska"


def test_challenge_analytics_with_recipe_difficulty():
    """Test challenge analytics rendering with recipe difficulty and ambition sections."""
    mock_recipes = pd.DataFrame(
        [
            {
                "recipe_id": "r1",
                "series_number": 1,
                "episode_number": 1,
                "challenge_type": "Technical",
                "dish_name": "Scones",
                "difficulty": "Easy",
                "judging_notes": "Golden crust and soft crumb.",
                "recipe_url": "https://example.com/scones",
            },
            {
                "recipe_id": "r2",
                "series_number": 1,
                "episode_number": 2,
                "challenge_type": "Showstopper",
                "dish_name": "Baked Alaska",
                "difficulty": "Extreme",
                "judging_notes": "Soggy bottom and melted.",
                "recipe_url": "https://example.com/alaska",
            },
        ]
    )
    mock_lore = pd.DataFrame(
        [
            {
                "series_number": 1,
                "episode_number": 1,
                "famous_quotes": "['A good biscuit must have a clean snap.']",
            }
        ]
    )
    mock_perfs = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "baker_id": "b1",
                "episode_id": "s01e01",
                "signature_dish": "Choux Macaron Sculpture",
                "showstopper_dish": "Tiered Chocolate Entremet",
                "result": "STAR_BAKER",
                "hollywood_handshake": True,
                "did_well": True,
                "at_risk": False,
            }
        ]
    )
    mock_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cake",
                "signature_time_min": 120,
                "technical_time_min": 90,
                "showstopper_time_min": 240,
            }
        ]
    )
    mock_nlp = pd.DataFrame(
        [
            {
                "performance_id": "p1",
                "all_flavors": "chocolate, vanilla",
                "all_styles": "pastry_choux",
            }
        ]
    )

    data = {
        "fandom_recipes": mock_recipes,
        "fandom_lore": mock_lore,
        "performances": mock_perfs,
        "episodes": mock_episodes,
        "bakes_nlp": mock_nlp,
        "bakers": pd.DataFrame(),
        "seasons": pd.DataFrame(),
    }

    with (
        patch("streamlit.columns", side_effect=_mock_columns),
        patch("streamlit.altair_chart") as mock_chart,
        patch("streamlit.dataframe"),
        patch("streamlit.selectbox", return_value="All"),
        patch("streamlit.text_input", return_value="chocolate"),
        patch("streamlit.info"),
    ):
        render_challenge_analytics(data)
        assert mock_chart.call_count >= 2
