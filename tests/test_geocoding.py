"""Unit tests for baker geocoding and GeoJSON export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.geocoding import (
    enrich_bakers,
    export_bakers_geojson,
    lookup_hometown,
)

runner = CliRunner()


def test_lookup_hometown_known_locations():
    """Test looking up known UK and overseas hometowns."""
    # England location
    geo_bradford = lookup_hometown("Bradford")
    assert geo_bradford["country"] == "England"
    assert geo_bradford["county_region"] == "West Yorkshire"
    assert isinstance(geo_bradford["latitude"], float)
    assert isinstance(geo_bradford["longitude"], float)

    # Scotland location
    geo_edin = lookup_hometown("Edinburgh, Scotland")
    assert geo_edin["country"] == "Scotland"
    assert geo_edin["county_region"] == "Edinburgh"
    assert geo_edin["latitude"] > 55.0

    # Wales location
    geo_cardiff = lookup_hometown("Cardiff, Wales")
    assert geo_cardiff["country"] == "Wales"
    assert geo_cardiff["county_region"] == "Cardiff"

    # Northern Ireland location
    geo_belfast = lookup_hometown("Belfast, Northern Ireland")
    assert geo_belfast["country"] == "Northern Ireland"
    assert geo_belfast["county_region"] == "Belfast"


def test_lookup_hometown_empty_and_unknown():
    """Test handling of empty, None, and unknown locations."""
    assert lookup_hometown(None)["latitude"] is None
    assert lookup_hometown("")["latitude"] is None
    assert lookup_hometown("   ")["latitude"] is None

    unknown = lookup_hometown("Nowhere In The World 99999")
    assert unknown["latitude"] is None
    assert unknown["country"] == "Unknown"


def test_enrich_bakers_dict_and_dataframe():
    """Test enriching baker records in list and DataFrame forms."""
    sample_bakers = [
        {
            "baker_id": "s01_edward",
            "name": "Edward Kimber",
            "series_number": 1,
            "hometown": "Bradford",
        },
        {
            "baker_id": "s03_john",
            "name": "John Whaite",
            "series_number": 3,
            "hometown": "Manchester",
        },
    ]

    # Test list enrichment
    enriched_list = enrich_bakers(sample_bakers)
    assert len(enriched_list) == 2
    assert enriched_list[0]["country"] == "England"
    assert enriched_list[0]["county_region"] == "West Yorkshire"
    assert enriched_list[1]["county_region"] == "Greater Manchester"

    # Test DataFrame enrichment
    df = pd.DataFrame(sample_bakers)
    enriched_df = enrich_bakers(df)
    assert "latitude" in enriched_df.columns
    assert "longitude" in enriched_df.columns
    assert "country" in enriched_df.columns
    assert "county_region" in enriched_df.columns
    assert enriched_df["country"].iloc[0] == "England"


def test_export_bakers_geojson(tmp_path: Path):
    """Test generating GeoJSON FeatureCollection with Point features."""
    sample_bakers = [
        {
            "baker_id": "s01_edward",
            "name": "Edward Kimber",
            "series_number": 1,
            "age": 24,
            "gender": "M",
            "occupation": "Debt collector",
            "hometown": "Bradford",
            "overall_placement": 1,
            "image_url": "https://example.com/edd.jpg",
        },
        {
            "baker_id": "s01_miranda",
            "name": "Miranda Gore Browne",
            "series_number": 1,
            "age": 37,
            "gender": "F",
            "occupation": "Food buyer",
            "hometown": "Midhurst",
            "overall_placement": 2,
            "image_url": None,
        },
    ]

    out_file = tmp_path / "test_bakers.geojson"
    result_path = export_bakers_geojson(bakers_data=sample_bakers, output_path=out_file)
    assert result_path.exists()

    with open(result_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["type"] == "FeatureCollection"
    assert data["name"] == "gbbo_bakers"
    assert len(data["features"]) == 2

    feat = data["features"][0]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "Point"
    # GeoJSON coordinates order: [lon, lat]
    coords = feat["geometry"]["coordinates"]
    assert len(coords) == 2
    assert coords[0] < 0  # UK longitude is negative / western
    assert coords[1] > 50  # UK latitude > 50° N

    props = feat["properties"]
    assert props["baker_id"] == "s01_edward"
    assert props["name"] == "Edward Kimber"
    assert props["is_winner"] is True
    assert props["county_region"] == "West Yorkshire"


def test_cli_export_geojson(tmp_path: Path):
    """Test CLI export-geojson command."""
    out_file = tmp_path / "cli_bakers.geojson"
    result = runner.invoke(app, ["export-geojson", "--output-file", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    assert "Exported GeoJSON dataset" in result.stdout
