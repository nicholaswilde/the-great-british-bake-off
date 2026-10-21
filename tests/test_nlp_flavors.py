"""Unit tests for NLP flavor profile and bake style extraction engine."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.nlp_flavors import (
    calculate_category_evolution,
    calculate_cooccurrence_affinity,
    calculate_family_risk_matrix,
    calculate_flavor_statistics,
    calculate_ingredient_risk_matrix,
    calculate_technique_evolution,
    enrich_performances_with_nlp,
    extract_bake_styles,
    extract_flavors,
    extract_techniques,
    run_nlp_flavor_pipeline,
)

runner = CliRunner()


def test_extract_flavors():
    """Verify regex-based flavor taxonomy extraction on dish titles."""
    assert extract_flavors(None) == []
    assert extract_flavors("") == []
    assert extract_flavors("Plain White Loaf") == []

    # Complex multi-flavor dish
    dish = "Cardamom and Orange Blossom Brioche Bun"
    flavors = extract_flavors(dish)
    assert "spice" in flavors
    assert "floral" in flavors
    assert "citrus" in flavors

    # Chocolate and berry
    dish2 = "Dark Chocolate and Raspberry Tart"
    flavors2 = extract_flavors(dish2)
    assert "chocolate" in flavors2
    assert "berry" in flavors2

    # Savory quiche
    dish3 = "Bacon, Cheddar and Caramelised Onion Quiche"
    flavors3 = extract_flavors(dish3)
    assert "savory" in flavors3
    assert "caramel" in flavors3


def test_extract_bake_styles():
    """Verify bake category and style classification."""
    assert extract_bake_styles(None) == []
    assert extract_bake_styles("") == []

    dish = "Cardamom and Orange Blossom Brioche Bun"
    styles = extract_bake_styles(dish)
    assert "bread" in styles

    dish2 = "Passion Fruit Choux Buns and Macarons"
    styles2 = extract_bake_styles(dish2)
    assert "pastry" in styles2
    assert "biscuit_cookie" in styles2

    dish3 = "Lemon Meringue Pavlova"
    styles3 = extract_bake_styles(dish3)
    assert "dessert_meringue" in styles3


def test_enrich_performances_with_nlp():
    """Verify DataFrame enrichment with flavor and style columns."""
    sample_df = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_edward",
                "signature_dish": "Vanilla and Strawberry Victoria Sponge",
                "showstopper_dish": "Chocolate Fudge Gateau",
                "hollywood_handshake": True,
                "result": "STAR_BAKER",
            },
            {
                "performance_id": "s01e01_s01_david",
                "signature_dish": "Apple and Cinnamon Pie",
                "showstopper_dish": "Coffee and Hazelnut Cake",
                "hollywood_handshake": False,
                "result": "SAFE",
            },
        ]
    )

    enriched = enrich_performances_with_nlp(sample_df)
    assert "signature_flavors" in enriched.columns
    assert "signature_styles" in enriched.columns
    assert "showstopper_flavors" in enriched.columns
    assert "all_flavors" in enriched.columns

    row1 = enriched.iloc[0]
    assert "berry" in row1["signature_flavors"]
    assert "vanilla_dairy" in row1["signature_flavors"]
    assert "cake_sponge" in row1["signature_styles"]
    assert "chocolate" in row1["showstopper_flavors"]


def test_calculate_flavor_statistics():
    """Verify aggregation metrics, rates, and co-occurrence pairs."""
    sample_df = pd.DataFrame(
        [
            {
                "signature_dish": "Lemon and Rosemary Tart",
                "showstopper_dish": "Chocolate and Raspberry Cake",
                "hollywood_handshake": True,
                "result": "STAR_BAKER",
            }
            for _ in range(15)
        ]
    )

    stats = calculate_flavor_statistics(sample_df)
    assert "citrus" in stats["flavor_counts"]
    assert "chocolate" in stats["flavor_counts"]
    assert "savory" in stats["flavor_counts"]
    assert stats["flavor_counts"]["citrus"] == 15

    # Handshake and Star Baker rates (100% in this mock)
    assert stats["handshake_rates"].get("citrus") == 100.0
    assert stats["star_baker_rates"].get("chocolate") == 100.0
    assert len(stats["co_occurring_pairs"]) > 0


def test_run_nlp_flavor_pipeline(tmp_path: Path):
    """Test full end-to-end pipeline execution and file export."""
    sample_df = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_test",
                "signature_dish": "Lemon and Blueberry Scones",
                "showstopper_dish": "Triple Chocolate Mousse",
                "hollywood_handshake": False,
                "result": "SAFE",
            }
        ]
    )
    sample_df.to_parquet(tmp_path / "performances.parquet")

    res = run_nlp_flavor_pipeline(
        processed_dir=tmp_path, output_file="test_bakes_nlp.json"
    )
    assert res["bakes_tagged"] == 1
    assert (tmp_path / "test_bakes_nlp.json").exists()
    assert (tmp_path / "test_bakes_nlp.csv").exists()
    assert (tmp_path / "flavor_analytics.json").exists()

    with open(tmp_path / "test_bakes_nlp.json", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert "citrus" in data[0]["signature_flavors"]


def test_cli_extract_flavors(tmp_path: Path):
    """Test gbbo extract-flavors CLI command."""
    sample_df = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_test",
                "signature_dish": "Cardamom and Orange Brioche",
                "showstopper_dish": "Pistachio Entremet",
                "hollywood_handshake": True,
                "result": "STAR_BAKER",
            }
        ]
    )
    sample_df.to_parquet(tmp_path / "performances.parquet")

    result = runner.invoke(
        app,
        [
            "extract-flavors",
            "--processed-dir",
            str(tmp_path),
            "--output",
            "cli_bakes_nlp.json",
        ],
    )
    assert result.exit_code == 0
    assert "Top 10 Flavor Families" in result.output
    assert (tmp_path / "cli_bakes_nlp.json").exists()


def test_extract_techniques():
    """Verify detection of modern showstopper techniques."""
    assert extract_techniques(None) == []
    assert extract_techniques("") == []

    dish = "Mirror Glaze Triple Tiered Cake"
    techs = extract_techniques(dish)
    assert "Mirror Glaze" in techs
    assert "Geometric / Tiered" in techs

    dish2 = "Vegan and Gluten-Free Chocolate Illusion Bust"
    techs2 = extract_techniques(dish2)
    assert "Vegan / Plant-Based" in techs2
    assert "Gluten-Free" in techs2
    assert "Illusion / 3D" in techs2


def test_risk_matrices_and_evolutions():
    """Verify ingredient risk matrices, co-occurrence affinity, and evolutions."""
    # Test empty dataframe handling
    empty_df = pd.DataFrame()
    assert calculate_ingredient_risk_matrix(empty_df) == []
    assert calculate_family_risk_matrix(empty_df) == []
    assert calculate_cooccurrence_affinity(empty_df) == []
    assert calculate_technique_evolution(empty_df) == []
    assert calculate_category_evolution(empty_df) == []

    # Populated test dataset
    mock_df = pd.DataFrame(
        [
            {
                "episode_id": "s07e01",
                "signature_dish": "Rosewater and Raspberry Tart",
                "showstopper_dish": "Mirror Glaze Illusion Cake",
                "result": "ELIMINATED",
                "at_risk": True,
                "hollywood_handshake": False,
            },
            {
                "episode_id": "s07e01",
                "signature_dish": "Cardamom and Orange Brioche",
                "showstopper_dish": "Caramel and Hazelnut Entremet",
                "result": "STAR_BAKER",
                "at_risk": False,
                "hollywood_handshake": True,
            },
            {
                "episode_id": "s07e02",
                "signature_dish": "Rosewater Brioche",
                "showstopper_dish": "Strawberry Tart",
                "result": "ELIMINATED",
                "at_risk": True,
                "hollywood_handshake": False,
            },
            {
                "episode_id": "s07e02",
                "signature_dish": "Rosewater Bun",
                "showstopper_dish": "Pistachio Cake",
                "result": "SAFE",
                "at_risk": False,
                "hollywood_handshake": False,
            },
        ]
    )

    ing_matrix = calculate_ingredient_risk_matrix(mock_df, min_bakes=2)
    assert len(ing_matrix) >= 1
    rose_entry = next(item for item in ing_matrix if item["ingredient"] == "Rose")
    assert rose_entry["bakes_count"] == 3
    assert rose_entry["danger_count"] == 2
    assert rose_entry["risk_tier"] == "🚨 High Risk"

    fam_matrix = calculate_family_risk_matrix(mock_df, min_bakes=1)
    assert len(fam_matrix) >= 1

    affinity = calculate_cooccurrence_affinity(mock_df, min_pairs=1)
    assert len(affinity) >= 1

    tech_evo = calculate_technique_evolution(mock_df)
    assert len(tech_evo) >= 5
    mirror_glaze = next(t for t in tech_evo if t["technique"] == "Mirror Glaze")
    assert mirror_glaze["bakes_count"] == 1

    cat_evo = calculate_category_evolution(mock_df)
    assert len(cat_evo) >= 6
