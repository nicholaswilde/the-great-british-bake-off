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
