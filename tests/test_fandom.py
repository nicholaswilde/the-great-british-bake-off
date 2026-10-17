"""Unit tests for Bake Off Fandom wiki importer and models."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.importers.fandom import (
    parse_fandom_quotes,
    scrape_all_fandom,
    scrape_fandom_series,
)
from gbbo_dataset.models import FandomLore, FandomRecipe

runner = CliRunner()


def test_fandom_models():
    """Verify FandomLore and FandomRecipe models and ID generation."""
    recipe_id = FandomRecipe.generate_recipe_id(15, 1, "Battenberg Cake")
    assert recipe_id == "s15e01_battenberg_cake"

    recipe = FandomRecipe(
        recipe_id=recipe_id,
        series_number=15,
        episode_number=1,
        challenge_type="Technical",
        dish_name="Battenberg Cake",
        difficulty="Moderate",
    )
    assert recipe.dish_name == "Battenberg Cake"
    assert recipe.challenge_type == "Technical"

    lore_id = FandomLore.generate_lore_id(5, 4)
    assert lore_id == "s05e04_lore"

    lore = FandomLore(
        lore_id=lore_id,
        series_number=5,
        episode_number=4,
        theme="Desserts",
        famous_quotes=["No one likes a soggy bottom."],
        notable_moments=["Baked Alaska incident (Bingate)."],
    )
    assert len(lore.famous_quotes) == 1
    assert "Bingate" in lore.notable_moments[0]


def test_parse_fandom_quotes():
    """Test extracting quotes from wikitext."""
    sample_wikitext = (
        'Paul commented "No one likes a soggy bottom" during the technical.'
    )
    quotes = parse_fandom_quotes(sample_wikitext)
    assert len(quotes) == 1
    assert "soggy bottom" in quotes[0]


def test_scrape_fandom_series(tmp_path: Path):
    """Test extracting series lore and recipes in offline mode."""
    raw_dir = tmp_path / "raw_fandom"
    res = scrape_fandom_series(series_number=5, raw_dir=raw_dir, offline=True)
    assert res["series_number"] == 5
    assert len(res["lore"]) >= 1
    assert len(res["recipes"]) >= 1

    out_file = raw_dir / "series_05_fandom.json"
    assert out_file.exists()
    with open(out_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["series_number"] == 5
    assert any(r["dish_name"] == "Baked Alaska" for r in data["recipes"])


def test_scrape_all_fandom(tmp_path: Path):
    """Test aggregating Fandom datasets across series range."""
    raw_dir = tmp_path / "raw"
    proc_dir = tmp_path / "proc"
    summary = scrape_all_fandom(
        raw_dir=raw_dir,
        processed_dir=proc_dir,
        series_range=(1, 2),
        offline=True,
    )
    assert summary["lore_count"] >= 2
    assert summary["recipe_count"] >= 2

    assert (proc_dir / "fandom_lore.json").exists()
    assert (proc_dir / "fandom_recipes.json").exists()
    assert (proc_dir / "fandom_lore.csv").exists()
    assert (proc_dir / "fandom_recipes.csv").exists()


def test_cli_scrape_fandom(tmp_path: Path):
    """Test gbbo scrape-fandom CLI command."""
    raw_dir = tmp_path / "fandom_cli_raw"
    proc_dir = tmp_path / "fandom_cli_proc"
    result = runner.invoke(
        app,
        [
            "scrape-fandom",
            "--series",
            "1",
            "--raw-dir",
            str(raw_dir),
            "--processed-dir",
            str(proc_dir),
            "--offline",
        ],
    )
    assert result.exit_code == 0
    assert "Series 01" in result.output
    assert (raw_dir / "series_01_fandom.json").exists()
