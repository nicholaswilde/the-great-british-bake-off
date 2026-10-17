"""Enrich GBBO processed dataset with demographics, handshakes, challenge times, and streaming metadata from RayofData/Tableau GBBO dataset."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from gbbo_dataset.models import Baker, Episode, Performance, Season

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)

DEFAULT_RAY_DATA_DIR = Path(
    "/home/nicholas/git/RayofData/The-Great-British-Bake-Off-Dashboard/data"
)


RAY_BAKER_ALIASES: dict[tuple[int, str], str] = {
    (12, "jairzeno"): "s12_jairzinho",
}

SERIES_15_BAKER_ENRICHMENT: dict[str, dict[str, str]] = {
    "s15_andy": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-andy-450x450-1.jpg",
    },
    "s15_christiaan": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-christiaan-450x450-1.jpg",
    },
    "s15_dylan": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-dylan-450x450-1.jpg",
    },
    "s15_georgie": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-georgie-450x450-1.jpg",
    },
    "s15_gill": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-gill-450x450-1.jpg",
    },
    "s15_hazel": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-hazel-450x450-1.jpg",
    },
    "s15_illiyin": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-illiyin-450x450-1.jpg",
    },
    "s15_jeff": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-jeff-450x450-1.jpg",
    },
    "s15_john": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-john-450x450-1.jpg",
    },
    "s15_mike": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-mike-450x450-1.jpg",
    },
    "s15_nelly": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-nelly-450x450-1.jpg",
    },
    "s15_sumayah": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2024/09/s15-sumayah-450x450-1.jpg",
    },
}

SERIES_15_HANDSHAKES: set[str] = {
    "s15e01_s15_illiyin",
    "s15e03_s15_dylan",
    "s15e06_s15_sumayah",
    "s15e07_s15_dylan",
    "s15e08_s15_dylan",
    "s15e08_s15_christiaan",
}

SERIES_16_BAKER_ENRICHMENT: dict[str, dict[str, str]] = {
    "s16_aaron": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Aa.jpg",
    },
    "s16_carol": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Pui.jpg",
    },
    "s16_hassan": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Ha.jpg",
    },
    "s16_iain": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Ia.jpg",
    },
    "s16_jasmine": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Ja.jpg",
    },
    "s16_jessika": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Je.jpg",
    },
    "s16_leighton": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Lei.jpg",
    },
    "s16_lesley": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Les.jpg",
    },
    "s16_nadia": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Nad.jpg",
    },
    "s16_nataliia": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Nat.jpg",
    },
    "s16_thomas": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Tom.jpg",
    },
    "s16_toby": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2025/08/78357_S16_Tob.jpg",
    },
}

SERIES_16_HANDSHAKES: set[str] = {
    "s16e02_s16_thomas",
    "s16e05_s16_jasmine",
}

SERIES_17_BAKER_ENRICHMENT: dict[str, dict[str, str]] = {
    "s17_clara": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/CLARA-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_danni": {
        "gender": "NB",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/DANNI-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_elizabeth": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/CONNIE-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_gabe": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/GABE-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_gary": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/GARY-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_mo": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/MO-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_molly": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/MOLLY-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_moyin": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/MOYIN-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_nikki": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/NIKKI-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_shannon": {
        "gender": "F",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/SHANNON-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_tom": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/TOM-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
    "s17_yannis": {
        "gender": "M",
        "image_url": "https://thegreatbritishbakeoff.co.uk/wp-content/uploads/2026/09/YANNIS-Anno-CLEAN_GBBO_S17_PreTX_1x1.jpg",
    },
}

SERIES_17_HANDSHAKES: set[str] = {
    "s17e03_s17_moyin",
}


def match_baker_id(
    season: int, ray_name: str, bakers_list: list[dict[str, Any]]
) -> str | None:
    """Resolve RayofData baker name (e.g. DavidC, Edd, Jo) to canonical baker_id."""
    s_bakers = [b for b in bakers_list if b.get("series_number") == season]
    base = (
        re.sub(r"(?<=[a-z])[A-Z]+$", "", str(ray_name)).strip().lower()
        or str(ray_name).strip().lower()
    )

    alias_id = RAY_BAKER_ALIASES.get((season, base))
    if alias_id:
        return alias_id

    # 1. Direct ID match
    for b in s_bakers:
        if b["baker_id"] == f"s{season:02d}_{base}":
            return b["baker_id"]

    # 2. Match word or substring in full name
    for b in s_bakers:
        name_lower = b.get("name", "").lower()
        if (
            base in name_lower.split()
            or f"'{base}'" in name_lower
            or f'"{base}"' in name_lower
            or name_lower.startswith(base)
        ):
            return b["baker_id"]

    # 3. Substring match
    for b in s_bakers:
        if base in b.get("name", "").lower():
            return b["baker_id"]

    return None


def enrich_bakers(
    bakers_path: Path, ray_bakers_path: Path
) -> tuple[list[dict[str, Any]], int]:
    """Enrich bakers with gender and headshot image URL."""
    if not bakers_path.exists() or not ray_bakers_path.exists():
        logger.warning("Bakers file or RayofData Bakers.csv missing, skipping")
        return [], 0

    with open(bakers_path, encoding="utf-8") as f:
        bakers = json.load(f)

    ray_df = pd.read_csv(ray_bakers_path)
    enriched_count = 0

    for _, row in ray_df.iterrows():
        season = int(row["Season"])
        ray_name = str(row["Baker"])
        baker_id = match_baker_id(season, ray_name, bakers)
        if not baker_id:
            continue

        gender = str(row["Gender"]).strip() if pd.notna(row.get("Gender")) else None
        image_url = (
            str(row["Image Link"]).strip() if pd.notna(row.get("Image Link")) else None
        )

        for b in bakers:
            if b["baker_id"] == baker_id:
                if gender:
                    b["gender"] = gender
                if image_url:
                    b["image_url"] = image_url
                enriched_count += 1

    for b in bakers:
        if b["baker_id"] in SERIES_15_BAKER_ENRICHMENT:
            meta = SERIES_15_BAKER_ENRICHMENT[b["baker_id"]]
            b["gender"] = meta["gender"]
            b["image_url"] = meta["image_url"]
            enriched_count += 1
        elif b["baker_id"] in SERIES_16_BAKER_ENRICHMENT:
            meta = SERIES_16_BAKER_ENRICHMENT[b["baker_id"]]
            b["gender"] = meta["gender"]
            b["image_url"] = meta["image_url"]
            enriched_count += 1
        elif b["baker_id"] in SERIES_17_BAKER_ENRICHMENT:
            meta = SERIES_17_BAKER_ENRICHMENT[b["baker_id"]]
            b["gender"] = meta["gender"]
            b["image_url"] = meta["image_url"]
            enriched_count += 1

    return bakers, enriched_count


def enrich_episodes(
    episodes_path: Path, ray_episodes_path: Path
) -> tuple[list[dict[str, Any]], int]:
    """Enrich episodes with challenge duration times."""
    if not episodes_path.exists() or not ray_episodes_path.exists():
        logger.warning("Episodes file or RayofData Episodes.csv missing, skipping")
        return [], 0

    with open(episodes_path, encoding="utf-8") as f:
        episodes = json.load(f)

    ray_df = pd.read_csv(ray_episodes_path)
    enriched_count = 0

    for _, row in ray_df.iterrows():
        season = int(row["Season"])
        ep_num = int(row["Episode"])
        episode_id = f"s{season:02d}e{ep_num:02d}"

        sig_time = (
            int(row["Signature Time (min)"])
            if pd.notna(row.get("Signature Time (min)"))
            else None
        )
        tech_time = (
            int(row["Technical Time (min)"])
            if pd.notna(row.get("Technical Time (min)"))
            else None
        )
        show_time = (
            int(row["Showstopper Time (min)"])
            if pd.notna(row.get("Showstopper Time (min)"))
            else None
        )

        for ep in episodes:
            if ep["episode_id"] == episode_id:
                if sig_time is not None:
                    ep["signature_time_min"] = sig_time
                if tech_time is not None:
                    ep["technical_time_min"] = tech_time
                if show_time is not None:
                    ep["showstopper_time_min"] = show_time
                enriched_count += 1

    return episodes, enriched_count


def enrich_performances(
    performances_path: Path, ray_outcomes_path: Path, bakers_list: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """Enrich performances with confirmed Hollywood Handshakes, did_well, and at_risk flags."""
    if not performances_path.exists() or not ray_outcomes_path.exists():
        logger.warning("Performances file or RayofData Outcomes.csv missing, skipping")
        return [], 0

    with open(performances_path, encoding="utf-8") as f:
        performances = json.load(f)

    ray_df = pd.read_csv(ray_outcomes_path)
    handshakes_added = 0

    for _, row in ray_df.iterrows():
        se_str = str(row["SeasonEpisode"]).strip().lower()
        match = re.match(r"s(\d+)e(\d+)", se_str)
        if not match:
            continue
        season = int(match.group(1))
        ep_num = int(match.group(2))
        episode_id = f"s{season:02d}e{ep_num:02d}"

        ray_baker = str(row["Baker"]).strip()
        baker_id = match_baker_id(season, ray_baker, bakers_list)
        if not baker_id:
            continue

        performance_id = f"{episode_id}_{baker_id}"
        has_handshake = bool(row.get("Handshake") == 1)
        did_well = bool(row.get("Did well") == 1)
        at_risk = bool(row.get("At risk") == 1)
        absent = bool(row.get("Absent") == 1)

        for p in performances:
            if p["performance_id"] == performance_id:
                if has_handshake and not p.get("hollywood_handshake"):
                    p["hollywood_handshake"] = True
                    handshakes_added += 1
                p["did_well"] = did_well
                p["at_risk"] = at_risk
                p["absent"] = absent

    for p in performances:
        if (
            p["performance_id"] in SERIES_15_HANDSHAKES
            or p["performance_id"] in SERIES_16_HANDSHAKES
            or p["performance_id"] in SERIES_17_HANDSHAKES
        ) and not p.get("hollywood_handshake"):
            p["hollywood_handshake"] = True
            handshakes_added += 1

    return performances, handshakes_added


def build_seasons(ray_seasons_path: Path) -> list[dict[str, Any]]:
    """Build Season models from RayofData Seasons.csv."""
    if not ray_seasons_path.exists():
        return []

    ray_df = pd.read_csv(ray_seasons_path)
    seasons: list[dict[str, Any]] = []

    for season_num, group in ray_df.groupby("Season"):
        s_num = int(season_num)
        hosts = sorted(set(group["Hosts"].dropna().astype(str).str.strip().unique()))
        judges = sorted(set(group["Judges"].dropna().astype(str).str.strip().unique()))
        winner = (
            str(group["Winner"].iloc[0]).strip()
            if pd.notna(group["Winner"].iloc[0])
            else None
        )
        year = int(group["Year"].iloc[0]) if pd.notna(group["Year"].iloc[0]) else None
        network = (
            str(group["Network"].iloc[0]).strip()
            if pd.notna(group["Network"].iloc[0])
            else None
        )

        pbs = (
            int(group["PBS Season"].iloc[0])
            if pd.notna(group["PBS Season"].iloc[0])
            else None
        )
        netflix = (
            int(group["Netflix Collection"].iloc[0])
            if pd.notna(group["Netflix Collection"].iloc[0])
            else None
        )
        roku = (
            int(group["Roku Season"].iloc[0])
            if pd.notna(group["Roku Season"].iloc[0])
            else None
        )
        location = (
            str(group["Location"].iloc[0]).strip()
            if pd.notna(group["Location"].iloc[0])
            else None
        )

        season_obj = Season(
            series_number=s_num,
            year=year,
            winner=winner,
            hosts=hosts,
            judges=judges,
            network=network,
            pbs_season=pbs,
            netflix_collection=netflix,
            roku_season=roku,
            location=location,
        )
        seasons.append(season_obj.model_dump())

    if not any(s["series_number"] == 15 for s in seasons):
        s15 = Season(
            series_number=15,
            year=2024,
            winner="Georgie Grasso",
            hosts=["Alison Hammond", "Noel Fielding"],
            judges=["Paul Hollywood", "Prue Leith"],
            network="Channel 4",
            pbs_season=None,
            netflix_collection=12,
            roku_season=None,
            location="Welford Park, Berkshire",
        )
        seasons.append(s15.model_dump())

    if not any(s["series_number"] == 16 for s in seasons):
        s16 = Season(
            series_number=16,
            year=2025,
            winner="Jasmine Mitchell",
            hosts=["Alison Hammond", "Noel Fielding"],
            judges=["Paul Hollywood", "Prue Leith"],
            network="Channel 4",
            pbs_season=None,
            netflix_collection=13,
            roku_season=None,
            location="Welford Park, Berkshire",
        )
        seasons.append(s16.model_dump())

    if not any(s["series_number"] == 17 for s in seasons):
        s17 = Season(
            series_number=17,
            year=2026,
            winner=None,
            hosts=["Alison Hammond", "Noel Fielding"],
            judges=["Nigella Lawson", "Paul Hollywood"],
            network="Channel 4",
            pbs_season=None,
            netflix_collection=None,
            roku_season=None,
            location="Welford Park, Berkshire",
        )
        seasons.append(s17.model_dump())

    seasons.sort(key=lambda x: x["series_number"])
    return seasons


def run_enrichment(
    processed_dir: Path = Path("data/processed"),
    ray_dir: Path = DEFAULT_RAY_DATA_DIR,
) -> dict[str, Any]:
    """Execute complete enrichment pipeline."""
    logger.info("Enriching processed tables from %s", ray_dir)

    bakers_path = processed_dir / "bakers.json"
    episodes_path = processed_dir / "episodes.json"
    performances_path = processed_dir / "performances.json"

    # 1. Bakers
    bakers, b_count = enrich_bakers(bakers_path, ray_dir / "Bakers.csv")
    if bakers:
        # Re-validate with Pydantic
        validated_bakers = [Baker.model_validate(b).model_dump() for b in bakers]
        with open(bakers_path, "w", encoding="utf-8") as f:
            json.dump(validated_bakers, f, indent=2, ensure_ascii=False)
        df_bakers = pd.DataFrame(validated_bakers)
        df_bakers.to_csv(processed_dir / "bakers.csv", index=False)
        df_bakers.to_parquet(processed_dir / "bakers.parquet", index=False)
        logger.info("Enriched %d bakers with demographics & photos", b_count)

    # 2. Episodes
    episodes, ep_count = enrich_episodes(episodes_path, ray_dir / "Episodes.csv")
    if episodes:
        validated_episodes = [Episode.model_validate(e).model_dump() for e in episodes]
        with open(episodes_path, "w", encoding="utf-8") as f:
            json.dump(validated_episodes, f, indent=2, ensure_ascii=False)
        df_episodes = pd.DataFrame(validated_episodes)
        df_episodes.to_csv(processed_dir / "episodes.csv", index=False)
        df_episodes.to_parquet(processed_dir / "episodes.parquet", index=False)
        logger.info("Enriched %d episodes with challenge durations", ep_count)

    # 3. Performances
    performances, hs_count = enrich_performances(
        performances_path, ray_dir / "Outcomes.csv", bakers
    )
    if performances:
        validated_performances = [
            Performance.model_validate(p).model_dump(mode="json") for p in performances
        ]
        with open(performances_path, "w", encoding="utf-8") as f:
            json.dump(validated_performances, f, indent=2, ensure_ascii=False)
        df_perf = pd.DataFrame(validated_performances)
        df_perf.to_csv(processed_dir / "performances.csv", index=False)
        df_perf.to_parquet(processed_dir / "performances.parquet", index=False)
        logger.info("Enriched performances (%d handshakes confirmed)", hs_count)

    # 4. Seasons Table
    seasons = build_seasons(ray_dir / "Seasons.csv")
    if seasons:
        seasons_path = processed_dir / "seasons.json"
        with open(seasons_path, "w", encoding="utf-8") as f:
            json.dump(seasons, f, indent=2, ensure_ascii=False)
        df_seasons = pd.DataFrame(seasons)
        df_seasons.to_csv(processed_dir / "seasons.csv", index=False)
        df_seasons.to_parquet(processed_dir / "seasons.parquet", index=False)
        logger.info(
            "Exported %d seasons with streaming & filming locations to %s",
            len(seasons),
            seasons_path,
        )

    return {
        "bakers_enriched": b_count,
        "episodes_enriched": ep_count,
        "handshakes_confirmed": hs_count,
        "seasons_created": len(seasons),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Enrich GBBO dataset with RayofData data."
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Processed data directory",
    )
    parser.add_argument(
        "--ray-dir",
        type=Path,
        default=DEFAULT_RAY_DATA_DIR,
        help="RayofData dataset directory",
    )

    args = parser.parse_args()
    results = run_enrichment(processed_dir=args.processed_dir, ray_dir=args.ray_dir)
    logger.info("Enrichment summary: %s", results)


if __name__ == "__main__":
    main()
