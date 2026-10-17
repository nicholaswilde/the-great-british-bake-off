"""Geocoding coordinates, regional taxonomy, and GeoJSON export for GBBO bakers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Complete offline WGS84 coordinates (latitude, longitude), country, and county/region for GBBO hometowns
HOMETOWN_COORDINATES: dict[str, tuple[float, float, str, str]] = {
    "Aldershot, Hampshire": (51.2484, -0.7645, "England", "Hampshire"),
    "Alkington, Shropshire": (52.9167, -2.7167, "England", "Shropshire"),
    "Arlesey": (52.0167, -0.2667, "England", "Bedfordshire"),
    "Ascot, Berkshire": (51.4116, -0.6766, "England", "Berkshire"),
    "Ashton upon Mersey, Trafford": (53.4328, -2.3333, "England", "Greater Manchester"),
    "Auchterarder, Perthshire": (56.2974, -3.7088, "Scotland", "Perthshire"),
    "Aylesbury, England": (51.8167, -0.8125, "England", "Buckinghamshire"),
    "Barton-Le-Clay, England": (51.9667, -0.4286, "England", "Bedfordshire"),
    "Barton-upon-Humber, Lincolnshire": (53.6833, -0.4333, "England", "Lincolnshire"),
    "Beckenham, England": (51.4083, -0.0333, "England", "Greater London"),
    "Bedfordshire, England": (52.1386, -0.4667, "England", "Bedfordshire"),
    "Belfast, Northern Ireland": (54.5973, -5.9301, "Northern Ireland", "Belfast"),
    "Bewbush, England": (51.1042, -0.2222, "England", "West Sussex"),
    "Bexhill-on-Sea, England": (50.8444, 0.4686, "England", "East Sussex"),
    "Birmingham": (52.4862, -1.8904, "England", "West Midlands"),
    "Birmingham, England": (52.4862, -1.8904, "England", "West Midlands"),
    "Bolton, England": (53.5769, -2.4282, "England", "Greater Manchester"),
    "Bracknell, Berkshire": (51.4167, -0.7500, "England", "Berkshire"),
    "Bradford": (53.7960, -1.7594, "England", "West Yorkshire"),
    "Brentwood, England": (51.6206, 0.3056, "England", "Essex"),
    "Brighton, East Sussex": (50.8225, -0.1372, "England", "East Sussex"),
    "Brighton, England": (50.8225, -0.1372, "England", "East Sussex"),
    "Bristol, England": (51.4545, -2.5879, "England", "Bristol"),
    "Broadstairs, Kent": (51.3589, 1.4397, "England", "Kent"),
    "Brooke, England": (52.5333, 1.3667, "England", "Norfolk"),
    "Cambridgeshire, England": (52.2053, 0.1218, "England", "Cambridgeshire"),
    "Cardiff, Wales": (51.4816, -3.1791, "Wales", "Cardiff"),
    "Carmarthen, Wales": (51.8576, -4.3121, "Wales", "Carmarthenshire"),
    "Cheshire, England": (53.2326, -2.6103, "England", "Cheshire"),
    "Chester, England": (53.1905, -2.8917, "England", "Cheshire"),
    "County Antrim, Northern Ireland": (
        54.8636,
        -6.2085,
        "Northern Ireland",
        "County Antrim",
    ),
    "County Tyrone, Northern Ireland": (
        54.6042,
        -7.0944,
        "Northern Ireland",
        "County Tyrone",
    ),
    "Crawley, England": (51.1130, -0.1831, "England", "West Sussex"),
    "Croydon": (51.3762, -0.0982, "England", "Greater London"),
    "Cumbria, England": (54.5772, -2.7975, "England", "Cumbria"),
    "Didcot, Oxfordshire": (51.6061, -1.2422, "England", "Oxfordshire"),
    "Dorset, England": (50.7483, -2.3381, "England", "Dorset"),
    "Dunkeld, Perth and Kinross": (56.5647, -3.5855, "Scotland", "Perth and Kinross"),
    "Dunstable": (51.8860, -0.5210, "England", "Bedfordshire"),
    "Durham, England": (54.7761, -1.5733, "England", "County Durham"),
    "East Sussex, England": (50.9167, 0.2500, "England", "East Sussex"),
    "East Yorkshire, England": (
        53.8500,
        -0.4333,
        "England",
        "East Riding of Yorkshire",
    ),
    "Edinburgh, Scotland": (55.9533, -3.1883, "Scotland", "Edinburgh"),
    "Enfield": (51.6517, -0.0792, "England", "Greater London"),
    "Erith, England": (51.4819, 0.1772, "England", "Greater London"),
    "Essex": (51.7719, 0.4431, "England", "Essex"),
    "Essex, England": (51.7719, 0.4431, "England", "Essex"),
    "Formby": (53.5572, -3.0644, "England", "Merseyside"),
    "Gloucestershire, England": (51.8644, -2.2381, "England", "Gloucestershire"),
    "Gravesend, England": (51.4417, 0.3686, "England", "Kent"),
    "Great Wilbraham, Cambridgeshire": (52.1936, 0.2558, "England", "Cambridgeshire"),
    "Grimsby, Lincolnshire": (53.5667, -0.0833, "England", "Lincolnshire"),
    "Guildford, Surrey": (51.2362, -0.5704, "England", "Surrey"),
    "Halifax, England": (53.7258, -1.8631, "England", "West Yorkshire"),
    "Halifax, West Yorkshire, England": (53.7258, -1.8631, "England", "West Yorkshire"),
    "Hampshire, England": (51.0572, -1.3081, "England", "Hampshire"),
    "Herefordshire, England": (52.0564, -2.7156, "England", "Herefordshire"),
    "Hertfordshire, England": (51.8098, -0.2377, "England", "Hertfordshire"),
    "Hillswick, Scotland": (60.4764, -1.4925, "Scotland", "Shetland"),
    "Holywood, Northern Ireland": (54.6369, -5.8447, "Northern Ireland", "County Down"),
    "Kent, England": (51.2787, 0.5217, "England", "Kent"),
    "Kidderminster": (52.3885, -2.2490, "England", "Worcestershire"),
    "Lanarkshire, Scotland": (55.6731, -3.7837, "Scotland", "Lanarkshire"),
    "Lancashire, England": (53.8636, -2.6644, "England", "Lancashire"),
    "Leeds / Luton": (53.8008, -1.5491, "England", "West Yorkshire"),
    "Leeds, England": (53.8008, -1.5491, "England", "West Yorkshire"),
    "Leicester": (52.6369, -1.1398, "England", "Leicestershire"),
    "Leicester, England": (52.6369, -1.1398, "England", "Leicestershire"),
    "Leicestershire, England": (52.6369, -1.1398, "England", "Leicestershire"),
    "Lichfield, England": (52.6835, -1.8265, "England", "Staffordshire"),
    "Liverpool, England": (53.4084, -2.9916, "England", "Merseyside"),
    "London": (51.5074, -0.1278, "England", "Greater London"),
    "London, England": (51.5074, -0.1278, "England", "Greater London"),
    "London/Belfast": (51.5074, -0.1278, "England", "Greater London"),
    "Maidstone, England": (51.2720, 0.5290, "England", "Kent"),
    "Manchester": (53.4808, -2.2426, "England", "Greater Manchester"),
    "Manchester, England": (53.4808, -2.2426, "England", "Greater Manchester"),
    "Market Harborough, Leicestershire": (
        52.4776,
        -0.9213,
        "England",
        "Leicestershire",
    ),
    "Melbourn, Cambridgeshire": (52.0833, 0.0167, "England", "Cambridgeshire"),
    "Merseyside, England": (53.4084, -2.9916, "England", "Merseyside"),
    "Midhurst": (50.9856, -0.7397, "England", "West Sussex"),
    "Midlothian": (55.8450, -3.1000, "Scotland", "Midlothian"),
    "Mill Hill, London": (51.6167, -0.2333, "England", "Greater London"),
    "Milton Keynes": (52.0406, -0.7594, "England", "Buckinghamshire"),
    "Newport, Wales": (51.5842, -2.9977, "Wales", "Newport"),
    "Norfolk": (52.6309, 1.2974, "England", "Norfolk"),
    "Norfolk, England": (52.6309, 1.2974, "England", "Norfolk"),
    "North London, England": (51.5833, -0.1333, "England", "Greater London"),
    "Northampton": (52.2405, -0.9027, "England", "Northamptonshire"),
    "Nottinghamshire, England": (53.1000, -1.0000, "England", "Nottinghamshire"),
    "Ongar": (51.7067, 0.2450, "England", "Essex"),
    "Pease Pottage, England": (51.0850, -0.2036, "England", "West Sussex"),
    "Penwortham, Lancashire": (53.7486, -2.7247, "England", "Lancashire"),
    "Pershore, England": (52.1122, -2.0800, "England", "Worcestershire"),
    "Peterborough": (52.5726, -0.2427, "England", "Cambridgeshire"),
    "Pointon": (52.8711, -0.3478, "England", "Lincolnshire"),
    "Poole, England": (50.7161, -1.9858, "England", "Dorset"),
    "Portadown, Northern Ireland": (
        54.4206,
        -6.4444,
        "Northern Ireland",
        "County Armagh",
    ),
    "Portknockie, Moray": (57.7031, -2.8601, "Scotland", "Moray"),
    "Portsmouth, Hampshire": (50.8167, -1.0833, "England", "Hampshire"),
    "Poynton, Cheshire": (53.3486, -2.1228, "England", "Cheshire"),
    "Radlett, England": (51.6833, -0.3167, "England", "Hertfordshire"),
    "Rainham, England": (51.5167, 0.1833, "England", "Greater London"),
    "Reading, Berkshire": (51.4543, -0.9781, "England", "Berkshire"),
    "Rochdale, England": (53.6167, -2.1500, "England", "Greater Manchester"),
    "Romford, England": (51.5760, 0.1819, "England", "Greater London"),
    "Rotherham, England": (53.4300, -1.3570, "England", "South Yorkshire"),
    "Saltley, Birmingham": (52.4897, -1.8600, "England", "West Midlands"),
    "Scarborough, England": (54.2831, -0.4042, "England", "North Yorkshire"),
    "Sheffield": (53.3811, -1.4701, "England", "South Yorkshire"),
    "Sheffield, England": (53.3811, -1.4701, "England", "South Yorkshire"),
    "Shropshire, England": (52.6140, -2.7303, "England", "Shropshire"),
    "Sneinton, Nottingham": (52.9525, -1.1306, "England", "Nottinghamshire"),
    "Somerset, England": (51.1000, -3.0000, "England", "Somerset"),
    "South London, England": (51.4500, -0.1000, "England", "Greater London"),
    "South Wales": (51.6214, -3.9436, "Wales", "South Wales"),
    "Southend, England": (51.5459, 0.7077, "England", "Essex"),
    "Southend, Essex": (51.5459, 0.7077, "England", "Essex"),
    "St Albans": (51.7520, -0.3397, "England", "Hertfordshire"),
    "St Eval, England": (50.4800, -4.9814, "England", "Cornwall"),
    "Stoke-on-Trent, England": (53.0027, -2.1794, "England", "Staffordshire"),
    "Stratford-upon-Avon, England": (52.1917, -1.7083, "England", "Warwickshire"),
    "Surrey, England": (51.2500, -0.4167, "England", "Surrey"),
    "Sutton Coldfield, England": (52.5630, -1.8220, "England", "West Midlands"),
    "Swansea, Wales": (51.6214, -3.9436, "Wales", "Swansea"),
    "Tamworth, England": (52.6340, -1.6959, "England", "Staffordshire"),
    "Teignmouth, Devon": (50.5475, -3.4961, "England", "Devon"),
    "Tenby, Wales": (51.6720, -4.7040, "Wales", "Pembrokeshire"),
    "Wakefield, England": (53.6833, -1.4964, "England", "West Yorkshire"),
    "Warwickshire, England": (52.3000, -1.5833, "England", "Warwickshire"),
    "Waterlooville, England": (50.8800, -1.0300, "England", "Hampshire"),
    "Watford, England": (51.6565, -0.3903, "England", "Hertfordshire"),
    "West Kirby": (53.3725, -3.1839, "England", "Merseyside"),
    "West Midlands, England": (52.4862, -1.8904, "England", "West Midlands"),
    "West Molesey, England": (51.4000, -0.3667, "England", "Surrey"),
    "West Sussex, England": (50.9167, -0.5000, "England", "West Sussex"),
    "West Yorkshire, England": (53.7500, -1.7500, "England", "West Yorkshire"),
    "Whitby, England": (54.4858, -0.6206, "England", "North Yorkshire"),
    "Wigan, England": (53.5450, -2.6325, "England", "Greater Manchester"),
    "Wiltshire, England": (51.3500, -1.9167, "England", "Wiltshire"),
    "Windsor, England": (51.4839, -0.6044, "England", "Berkshire"),
    "Woodford, London / Vilkaviškis, Lithuania": (
        51.6044,
        0.0242,
        "England",
        "Greater London",
    ),
    "Yeadon, West Yorkshire": (53.8644, -1.6881, "England", "West Yorkshire"),
    "Yeovil, England": (50.9416, -2.6322, "England", "Somerset"),
}


def lookup_hometown(hometown: str | None) -> dict[str, Any]:
    """Look up geographic coordinates, country, and region for a hometown string.

    Returns dict with keys: latitude, longitude, country, county_region.
    """
    if not hometown or not str(hometown).strip():
        return {
            "latitude": None,
            "longitude": None,
            "country": None,
            "county_region": None,
        }

    clean_ht = str(hometown).strip()
    if clean_ht in HOMETOWN_COORDINATES:
        lat, lon, country, region = HOMETOWN_COORDINATES[clean_ht]
        return {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "country": country,
            "county_region": region,
        }

    # Partial / substring match fallback
    lower_ht = clean_ht.lower()
    for known_loc, (lat, lon, country, region) in HOMETOWN_COORDINATES.items():
        if known_loc.lower() in lower_ht or lower_ht in known_loc.lower():
            return {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "country": country,
                "county_region": region,
            }

    # Default fallback when unmapped
    return {
        "latitude": None,
        "longitude": None,
        "country": "Unknown",
        "county_region": None,
    }


def enrich_bakers(
    bakers_data: list[dict[str, Any]] | pd.DataFrame,
) -> list[dict[str, Any]] | pd.DataFrame:
    """Enrich baker records with latitude, longitude, country, and county_region."""
    if isinstance(bakers_data, pd.DataFrame):
        df = bakers_data.copy()
        lats, lons, countries, regions = [], [], [], []
        for _, row in df.iterrows():
            geo = lookup_hometown(row.get("hometown"))
            lats.append(geo["latitude"])
            lons.append(geo["longitude"])
            countries.append(geo["country"])
            regions.append(geo["county_region"])

        df["latitude"] = lats
        df["longitude"] = lons
        df["country"] = countries
        df["county_region"] = regions
        return df

    # List of dictionaries
    enriched_list: list[dict[str, Any]] = []
    for b in bakers_data:
        record = dict(b)
        geo = lookup_hometown(record.get("hometown"))
        record.update(geo)
        enriched_list.append(record)
    return enriched_list


def export_bakers_geojson(
    bakers_data: list[dict[str, Any]] | pd.DataFrame | None = None,
    output_path: Path | str = "data/processed/bakers.geojson",
    bakers_json_path: Path | str = "data/processed/bakers.json",
) -> Path:
    """Generate and write standard GeoJSON FeatureCollection of baker hometowns."""
    target_out = Path(output_path)
    target_out.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    if bakers_data is not None:
        if isinstance(bakers_data, pd.DataFrame):
            records = bakers_data.to_dict(orient="records")
        else:
            records = list(bakers_data)
    else:
        src_path = Path(bakers_json_path)
        if not src_path.exists():
            raise FileNotFoundError(f"Source bakers data not found at {src_path}")
        with open(src_path, encoding="utf-8") as f:
            records = json.load(f)

    # Ensure records are enriched with coordinates
    enriched = enrich_bakers(records)
    if isinstance(enriched, pd.DataFrame):
        enriched_records = enriched.to_dict(orient="records")
    else:
        enriched_records = enriched

    features: list[dict[str, Any]] = []
    for b in enriched_records:
        lat = b.get("latitude")
        lon = b.get("longitude")
        if lat is None or lon is None:
            continue

        placement = b.get("overall_placement")
        is_winner = placement == 1

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)],
            },
            "properties": {
                "baker_id": b.get("baker_id"),
                "name": b.get("name"),
                "series_number": b.get("series_number"),
                "age": b.get("age"),
                "gender": b.get("gender"),
                "occupation": b.get("occupation"),
                "hometown": b.get("hometown"),
                "country": b.get("country"),
                "county_region": b.get("county_region"),
                "overall_placement": placement,
                "is_winner": is_winner,
                "image_url": b.get("image_url"),
            },
        }
        features.append(feature)

    geojson_doc = {
        "type": "FeatureCollection",
        "name": "gbbo_bakers",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
    }

    with open(target_out, "w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2, ensure_ascii=False)

    logger.info("Exported %d baker GeoJSON features to %s", len(features), target_out)
    return target_out
