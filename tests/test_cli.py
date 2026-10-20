"""Unit tests for gbbo CLI."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from gbbo_dataset import __version__
from gbbo_dataset.cli import app

runner = CliRunner()


def test_cli_version():
    """Verify --version returns version string."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_help():
    """Verify --help lists available commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scrape" in result.stdout
    assert "build" in result.stdout
    assert "enrich" in result.stdout
    assert "gaps" in result.stdout
    assert "stats" in result.stdout
    assert "export-sqlite" in result.stdout
    assert "export-arrow" in result.stdout
    assert "export-r" in result.stdout
    assert "predict" in result.stdout


def test_cli_stats():
    """Verify stats command runs and shows table summary."""
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "bakers" in result.stdout
    assert "episodes" in result.stdout
    assert "performances" in result.stdout
    assert "seasons" in result.stdout


def test_cli_gaps():
    """Verify gaps command executes audit."""
    result = runner.invoke(app, ["gaps"])
    assert result.exit_code == 0
    assert "Completeness" in result.stdout


def test_cli_exports(tmp_path):
    """Verify export-sqlite, export-arrow, and export-r CLI commands."""
    db_file = tmp_path / "cli_gbbo.db"
    res_sqlite = runner.invoke(
        app,
        [
            "export-sqlite",
            "--processed-dir",
            "data/processed",
            "--db-path",
            str(db_file),
        ],
    )
    assert res_sqlite.exit_code == 0
    assert db_file.exists()

    arrow_dir = tmp_path / "arrow"
    res_arrow = runner.invoke(
        app,
        [
            "export-arrow",
            "--processed-dir",
            "data/processed",
            "--arrow-dir",
            str(arrow_dir),
        ],
    )
    assert res_arrow.exit_code == 0
    assert (arrow_dir / "bakers.arrow").exists()

    r_dir = tmp_path / "r_out"
    pkg_dir = tmp_path / "r_pkg"
    res_r = runner.invoke(
        app,
        [
            "export-r",
            "--processed-dir",
            "data/processed",
            "--r-dir",
            str(r_dir),
            "--pkg-dir",
            str(pkg_dir),
        ],
    )
    assert res_r.exit_code == 0
    assert (r_dir / "bakers.rds").exists()
    assert (pkg_dir / "DESCRIPTION").exists()


def test_cli_ai_and_hf_commands(tmp_path):
    """Verify export-ai, eval-benchmark, and publish-hf CLI commands."""
    ai_dir = tmp_path / "ai_out"
    res_ai = runner.invoke(
        app,
        [
            "export-ai",
            "--processed-dir",
            "data/processed",
            "--ai-dir",
            str(ai_dir),
        ],
    )
    assert res_ai.exit_code == 0
    assert (ai_dir / "gbbo_qa_finetuning.jsonl").exists()
    assert (ai_dir / "gbbo_knowledge_corpus.jsonl").exists()
    assert (ai_dir / "gbbo_benchmark_suite.jsonl").exists()

    res_bench = runner.invoke(
        app,
        [
            "eval-benchmark",
            "--benchmark-file",
            str(ai_dir / "gbbo_benchmark_suite.jsonl"),
        ],
    )
    assert res_bench.exit_code == 0
    assert "Benchmark complete" in res_bench.stdout

    stage_dir = tmp_path / "hf_stage"
    res_hf = runner.invoke(
        app,
        [
            "publish-hf",
            "--dry-run",
            "--staging-dir",
            str(stage_dir),
        ],
    )
    assert res_hf.exit_code == 0
    assert "Dry-run complete" in res_hf.stdout
    assert (stage_dir / "README.md").exists()


def test_cli_validate_and_predict(tmp_path):
    """Verify validate, predict, and extract-flavors CLI commands."""
    res_val = runner.invoke(app, ["validate", "--processed-dir", "data/processed"])
    assert res_val.exit_code == 0
    assert "Validation Status: PASS" in res_val.stdout

    res_pred = runner.invoke(app, ["predict", "--series", "17"])
    assert res_pred.exit_code == 0
    assert "Series 17" in res_pred.stdout

    flavors_out = "test_flavors.json"
    res_flavors = runner.invoke(
        app,
        [
            "extract-flavors",
            "--processed-dir",
            "data/processed",
            "--output",
            flavors_out,
        ],
    )
    assert res_flavors.exit_code == 0
    test_out = Path("data/processed") / flavors_out
    if test_out.exists():
        test_out.unlink()
    test_csv = Path("data/processed") / "test_flavors.csv"
    if test_csv.exists():
        test_csv.unlink()


def test_cli_mocked_pipelines(tmp_path):
    """Verify scrape, build, enrich, scrape-fandom, and package CLI commands."""
    with patch("gbbo_dataset.cli.scrape_series") as mock_scrape:
        res = runner.invoke(
            app, ["scrape", "--series", "1", "--raw-dir", str(tmp_path / "raw")]
        )
        assert res.exit_code == 0
        mock_scrape.assert_called_once()

    with patch("gbbo_dataset.cli.build_datasets") as mock_build:
        mock_build.return_value = {
            "bakers": 10,
            "episodes": 5,
            "performances": 20,
            "errors": 0,
        }
        res = runner.invoke(
            app,
            [
                "build",
                "--raw-dir",
                str(tmp_path / "raw"),
                "--processed-dir",
                str(tmp_path / "proc"),
            ],
        )
        assert res.exit_code == 0
        mock_build.assert_called_once()

    with patch("gbbo_dataset.cli.run_enrichment") as mock_enrich:
        mock_enrich.return_value = {
            "bakers_enriched": 10,
            "episodes_enriched": 5,
            "handshakes_confirmed": 2,
            "seasons_created": 1,
        }
        res = runner.invoke(
            app,
            ["enrich", "--processed-dir", str(tmp_path / "proc")],
        )
        assert res.exit_code == 0
        mock_enrich.assert_called_once()

    with patch("gbbo_dataset.cli.scrape_all_fandom") as mock_fandom:
        mock_fandom.return_value = {"lore_count": 5, "recipe_count": 5}
        res = runner.invoke(
            app,
            ["scrape-fandom", "--offline", "--raw-dir", str(tmp_path / "raw_fandom")],
        )
        assert res.exit_code == 0
        mock_fandom.assert_called_once()

    with patch("gbbo_dataset.cli.scrape_all_reddit") as mock_reddit:
        mock_reddit.return_value = {"discussion_count": 10}
        res = runner.invoke(
            app,
            ["scrape-reddit", "--offline", "--raw-dir", str(tmp_path / "raw_reddit")],
        )
        assert res.exit_code == 0
        mock_reddit.assert_called_once()

    res_pkg = runner.invoke(
        app,
        ["package", "--component", "csv", "--output-dir", str(tmp_path / "dist")],
    )
    assert res_pkg.exit_code == 0
    assert len(list((tmp_path / "dist").glob("gbbo-dataset-csv-*.zip"))) == 1


def test_cli_scrape_ranges_and_errors(tmp_path):
    """Verify scrape range logic and error exit codes."""
    with patch("gbbo_dataset.cli.scrape_series") as mock_scrape:
        mock_scrape.return_value = {"bakers": 10, "episodes": 5, "performances": 20}
        res_range = runner.invoke(
            app,
            [
                "scrape",
                "--start",
                "1",
                "--end",
                "2",
                "--raw-dir",
                str(tmp_path / "raw"),
            ],
        )
        assert res_range.exit_code == 0
        assert mock_scrape.call_count == 2

    with patch("gbbo_dataset.cli.scrape_series") as mock_scrape:
        mock_scrape.side_effect = RuntimeError("Failed scrape")
        res_err = runner.invoke(
            app, ["scrape", "--series", "1", "--raw-dir", str(tmp_path / "raw")]
        )
        assert res_err.exit_code == 1

    with patch("gbbo_dataset.cli.scrape_series") as mock_scrape:
        mock_scrape.side_effect = [RuntimeError("Failed s1"), {"bakers": 10}]
        res_range_fail = runner.invoke(
            app,
            [
                "scrape",
                "--start",
                "1",
                "--end",
                "2",
                "--raw-dir",
                str(tmp_path / "raw"),
            ],
        )
        assert res_range_fail.exit_code == 0
        assert "skipped/failed" in res_range_fail.stdout


def test_cli_fandom_and_reddit_errors(tmp_path):
    """Verify scrape-fandom and scrape-reddit error exit codes."""
    with patch("gbbo_dataset.cli.scrape_fandom_series") as mock_f:
        mock_f.side_effect = RuntimeError("Fandom error")
        res_f = runner.invoke(
            app, ["scrape-fandom", "--series", "1", "--raw-dir", str(tmp_path / "raw")]
        )
        assert res_f.exit_code == 1

    with patch("gbbo_dataset.cli.scrape_reddit_series") as mock_r:
        mock_r.side_effect = RuntimeError("Reddit error")
        res_r = runner.invoke(
            app, ["scrape-reddit", "--series", "1", "--raw-dir", str(tmp_path / "raw")]
        )
        assert res_r.exit_code == 1


def test_cli_validate_failure(tmp_path):
    """Verify validate command exits with 1 on invalid or missing data."""
    res = runner.invoke(app, ["validate", "--processed-dir", str(tmp_path / "empty")])
    assert res.exit_code == 1
    assert "FAIL" in res.stdout


def test_cli_gaps_detail_and_export(tmp_path):
    """Verify gaps command with --detail and --export-md options."""
    md_file = tmp_path / "gaps.md"
    res = runner.invoke(app, ["gaps", "--detail", "--export-md", str(md_file)])
    assert res.exit_code == 0
    assert md_file.exists()


def test_cli_package_components_and_invalid(tmp_path):
    """Verify package command options and invalid component handling."""
    dist_dir = tmp_path / "dist_comp"

    # Valid component
    res_parquet = runner.invoke(
        app,
        ["package", "--component", "parquet", "--output-dir", str(dist_dir)],
    )
    assert res_parquet.exit_code == 0

    # Invalid component
    res_inv = runner.invoke(
        app,
        ["package", "--component", "unknown_comp", "--output-dir", str(dist_dir)],
    )
    assert res_inv.exit_code == 1
    assert "Unknown component" in res_inv.stdout


def test_cli_dashboard_mocked():
    """Verify dashboard CLI invokes streamlit subprocess and handles interrupt."""
    with patch("subprocess.run") as mock_sub:
        res = runner.invoke(app, ["dashboard", "--no-browser", "--port", "8502"])
        assert res.exit_code == 0
        mock_sub.assert_called_once()

    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        res_int = runner.invoke(app, ["dashboard", "--browser", "--port", "8502"])
        assert res_int.exit_code == 0
        assert "Dashboard stopped" in res_int.stdout
