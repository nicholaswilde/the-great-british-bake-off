"""Unit and integration tests for GBBO SeriesPredictor and predictive CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.predictor import (
    DEFAULT_HISTORICAL_BASELINES,
    SeriesPredictor,
)

runner = CliRunner()


def test_default_historical_baselines():
    """Verify default historical baselines exist and have valid values."""
    assert "winner_mean_age" in DEFAULT_HISTORICAL_BASELINES
    assert 20.0 < DEFAULT_HISTORICAL_BASELINES["winner_mean_age"] < 45.0
    assert 0.0 < DEFAULT_HISTORICAL_BASELINES["winner_avg_tech_pct"] < 1.0
    assert DEFAULT_HISTORICAL_BASELINES["winner_avg_star_bakers"] > 0.5


def test_series_predictor_baselines_fallback(tmp_path: Path):
    """Verify predictor falls back to defaults when processed dir is empty."""
    predictor = SeriesPredictor(processed_dir=tmp_path, raw_dir=tmp_path)
    assert (
        predictor.baselines["winner_mean_age"]
        == DEFAULT_HISTORICAL_BASELINES["winner_mean_age"]
    )
    assert (
        predictor.baselines["winner_avg_tech_pct"]
        == DEFAULT_HISTORICAL_BASELINES["winner_avg_tech_pct"]
    )


def test_score_baker_eliminated():
    """Verify scoring logic for an eliminated baker."""
    predictor = SeriesPredictor()
    res = predictor.score_baker(
        baker_id="s17_danni",
        name="Danni",
        age=25,
        performances=[
            {"episode_id": "s17e01", "technical_rank": 11, "result": "SAFE"},
            {"episode_id": "s17e02", "technical_rank": 11, "result": "ELIMINATED"},
        ],
        ep_tech_max={"s17e01": 12.0, "s17e02": 12.0},
        is_eliminated=True,
    )
    assert res["status"] == "Eliminated"
    assert res["is_active"] is False
    assert res["is_eliminated"] is True
    assert res["episodes_competed"] == 2
    assert res["avg_technical_pct"] < 0.20


def test_score_baker_withdrew():
    """Verify scoring logic for a withdrawn baker."""
    predictor = SeriesPredictor()
    res = predictor.score_baker(
        baker_id="s17_nikki",
        name="Nikki",
        age=50,
        performances=[
            {"episode_id": "s17e01", "technical_rank": 5, "result": "SAFE"},
            {"episode_id": "s17e02", "technical_rank": 9, "result": "SAFE"},
            {"episode_id": "s17e03", "technical_rank": 4, "result": "SAFE"},
            {"episode_id": "s17e04", "technical_rank": None, "result": "WITHDREW"},
        ],
        ep_tech_max={"s17e01": 12.0, "s17e02": 12.0, "s17e03": 11.0, "s17e04": 9.0},
        is_withdrew=True,
    )
    assert res["status"] == "Withdrew"
    assert res["is_active"] is False
    assert res["is_withdrew"] is True


def test_score_baker_active():
    """Verify scoring logic for an active contender."""
    predictor = SeriesPredictor()
    res = predictor.score_baker(
        baker_id="s17_tom",
        name="Tom Whittaker",
        age=25,
        performances=[
            {"episode_id": "s17e01", "technical_rank": 1, "result": "SAFE"},
            {"episode_id": "s17e02", "technical_rank": 3, "result": "STAR_BAKER"},
            {"episode_id": "s17e03", "technical_rank": 7, "result": "SAFE"},
            {"episode_id": "s17e04", "technical_rank": 4, "result": "STAR_BAKER"},
        ],
        ep_tech_max={"s17e01": 12.0, "s17e02": 12.0, "s17e03": 11.0, "s17e04": 9.0},
        is_eliminated=False,
    )
    assert res["status"] == "Active"
    assert res["is_active"] is True
    assert res["star_baker_count"] == 2
    assert res["last_star_baker"] is True
    assert res["avg_technical_pct"] > 0.60
    assert res["star_baker_raw"] > 0.50
    assert res["win_raw"] > 0.50


def test_score_baker_empty_performances():
    """Verify scoring logic for baker with no completed performances."""
    predictor = SeriesPredictor()
    res = predictor.score_baker(
        baker_id="s17_new",
        name="New Baker",
        age=30,
        performances=[],
        ep_tech_max={},
    )
    assert res["is_active"] is True
    assert res["episodes_competed"] == 0
    assert res["star_baker_count"] == 0


def test_predict_series_17():
    """Verify prediction pipeline on Series 17."""
    predictor = SeriesPredictor()
    results = predictor.predict_series(series=17)

    assert results["series"] == 17
    assert results["current_episode"] == 4
    assert results["next_episode"] == 5
    assert results["total_bakers"] == 12
    assert results["active_bakers_count"] == 8
    assert results["eliminated_bakers_count"] == 4

    rankings = results["rankings"]
    active = [b for b in rankings if b["is_active"]]
    inactive = [b for b in rankings if not b["is_active"]]

    assert len(active) == 8
    assert len(inactive) == 4

    # Win probabilities across active bakers should sum to ~100%
    active_win_sum = sum(b["win_probability"] for b in active)
    assert pytest.approx(active_win_sum, abs=1.0) == 100.0

    # Star baker probabilities across active bakers should sum to ~100%
    active_sb_sum = sum(b["star_baker_prob"] for b in active)
    assert pytest.approx(active_sb_sum, abs=1.0) == 100.0

    # Elimination risks across active bakers should sum to ~100%
    active_elim_sum = sum(b["elimination_risk"] for b in active)
    assert pytest.approx(active_elim_sum, abs=1.0) == 100.0

    # Inactive bakers must have 0.0% probabilities
    for b in inactive:
        assert b["win_probability"] == 0.0
        assert b["star_baker_prob"] == 0.0
        assert b["elimination_risk"] == 0.0
        assert b["top3_probability"] == 0.0


def test_predict_series_as_of_episode():
    """Verify retroactive predictions as of a specific past episode."""
    predictor = SeriesPredictor()
    res_ep1 = predictor.predict_series(series=17, as_of_episode=1)
    assert res_ep1["current_episode"] == 1
    assert res_ep1["next_episode"] == 2
    assert res_ep1["active_bakers_count"] == 12

    res_ep2 = predictor.predict_series(series=17, as_of_episode=2)
    assert res_ep2["current_episode"] == 2
    assert res_ep2["next_episode"] == 3
    assert res_ep2["active_bakers_count"] == 11


def test_predict_series_invalid():
    """Verify ValueError is raised for nonexistent series."""
    predictor = SeriesPredictor()
    with pytest.raises(ValueError, match="No baker records found"):
        predictor.predict_series(series=999)


def test_update_predictions_docs(tmp_path: Path):
    """Verify document generation and README updates in isolated paths."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "# Test GBBO\n\n## :clap: Acknowledgments & Credits\n\nThanks!\n",
        encoding="utf-8",
    )
    docs_path = tmp_path / "docs" / "predictions.md"
    data_dir = tmp_path / "data" / "predictions"

    predictor = SeriesPredictor()
    out = predictor.update_predictions_docs(
        series=17,
        readme_path=readme_path,
        docs_path=docs_path,
        data_dir=data_dir,
    )

    assert Path(out["docs_file"]).exists()
    assert Path(out["snapshot_file"]).exists()

    docs_content = docs_path.read_text(encoding="utf-8")
    assert "Series 17 Empirical Predictions & Accuracy Ledger" in docs_content
    assert "Latest Contender Rankings" in docs_content
    assert "Weekly Win Probability Trajectory" in docs_content
    assert "Prediction Accuracy vs Actual Broadcast Outcomes" in docs_content
    assert "Tom Whittaker" in docs_content

    readme_content = readme_path.read_text(encoding="utf-8")
    assert "<!-- GBBO_PREDICTIONS_START -->" in readme_content
    assert "<!-- GBBO_PREDICTIONS_END -->" in readme_content
    assert "Live Empirical Predictions (Series 17" in readme_content


def test_cli_predict():
    """Verify gbbo predict command executes cleanly."""
    res = runner.invoke(app, ["predict", "--series", "17", "--top", "6"])
    assert res.exit_code == 0
    assert "Series 17 Contender Rankings" in res.stdout
    assert "Tom" in res.stdout


def test_cli_predict_detail(tmp_path: Path):
    """Verify gbbo predict with --detail and --output flags."""
    out_json = tmp_path / "test_predict.json"
    res = runner.invoke(
        app,
        [
            "predict",
            "--series",
            "17",
            "--detail",
            "--output",
            str(out_json),
        ],
    )
    assert res.exit_code == 0
    assert "Series 17 Factor Breakdown" in res.stdout
    assert out_json.exists()

    with open(out_json, encoding="utf-8") as f:
        data = json.load(f)
    assert data["series"] == 17
    assert len(data["rankings"]) == 12


def test_cli_predict_error():
    """Verify gbbo predict returns exit code 1 for invalid series."""
    res = runner.invoke(app, ["predict", "--series", "999"])
    assert res.exit_code == 1
    assert "Prediction error:" in res.stdout


def test_helper_edge_cases():
    """Verify helper functions handle edge cases."""
    assert SeriesPredictor._extract_episode_number("s01e05") == 5
    assert SeriesPredictor._extract_episode_number("invalid") == 0
    assert SeriesPredictor._softmax([]) == []
    assert SeriesPredictor._softmax([5.0]) == [100.0]
    softmax_res = SeriesPredictor._softmax([1.0, 2.0, 3.0])
    assert pytest.approx(sum(softmax_res), abs=0.5) == 100.0


def test_predictor_app_direct():
    """Verify predictor.py app can be run directly via CliRunner."""
    from gbbo_dataset.predictor import app as pred_app

    res = runner.invoke(pred_app, ["--series", "17", "--top", "3"])
    assert res.exit_code == 0
    assert "Series 17 Contender Rankings" in res.stdout


def test_readme_existing_markers_update(tmp_path: Path):
    """Verify update_predictions_docs cleanly replaces existing markers."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "# GBBO\n\n<!-- GBBO_PREDICTIONS_START -->old table<!-- GBBO_PREDICTIONS_END -->\n",
        encoding="utf-8",
    )
    docs_path = tmp_path / "docs" / "predictions.md"
    data_dir = tmp_path / "data" / "predictions"

    predictor = SeriesPredictor()
    predictor.update_predictions_docs(
        series=17,
        readme_path=readme_path,
        docs_path=docs_path,
        data_dir=data_dir,
    )

    content = readme_path.read_text(encoding="utf-8")
    assert "old table" not in content
    assert "Live Empirical Predictions (Series 17" in content


def test_top3_few_active_bakers(tmp_path: Path):
    """Verify finale probability is 100% when 3 or fewer active bakers remain."""
    bakers = [
        {"baker_id": "s01_a", "series_number": 99, "name": "Baker A", "age": 30},
        {"baker_id": "s01_b", "series_number": 99, "name": "Baker B", "age": 28},
    ]
    perfs = [
        {
            "baker_id": "s01_a",
            "episode_id": "s99e01",
            "technical_rank": 1,
            "result": "SAFE",
        },
        {
            "baker_id": "s01_b",
            "episode_id": "s99e01",
            "technical_rank": 2,
            "result": "SAFE",
        },
    ]
    (tmp_path / "bakers.json").write_text(json.dumps(bakers), encoding="utf-8")
    (tmp_path / "performances.json").write_text(json.dumps(perfs), encoding="utf-8")

    predictor = SeriesPredictor(processed_dir=tmp_path)
    res = predictor.predict_series(series=99)
    for b in res["rankings"]:
        assert b["top3_probability"] == 100.0
