"""Unit tests for gbbo CLI."""

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
