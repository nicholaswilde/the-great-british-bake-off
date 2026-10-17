"""Build and aggregate raw GBBO data into validated processed datasets."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from gbbo_dataset.models import Baker, Episode, Performance

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


BAKER_ID_ALIASES: dict[str, str] = {
    "s01_edd": "s01_edward",
    "s02_jo": "s02_joanne",
    "s07_val": "s07_valerie",
    "s08_yan": "s08_chuenyan",
    "s12_jairzeno": "s12_jairzinho",
}


def load_json(filepath: Path) -> list[dict[str, Any]]:
    """Safely load JSON list from file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error("Error loading %s: %s", filepath, e)
        return []


def build_datasets(
    raw_dir: Path = Path("data/raw"), processed_dir: Path = Path("data/processed")
) -> dict[str, int]:
    """Validate raw records against Pydantic models and export master datasets."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    bakers_map: dict[str, Baker] = {}
    episodes_map: dict[str, Episode] = {}
    performances_map: dict[str, Performance] = {}

    validation_errors = 0

    # Load existing processed files to preserve enriched attributes (e.g. RayofData demographics, times, handshakes)
    existing_bakers: dict[str, dict[str, Any]] = {}
    bakers_json_path = processed_dir / "bakers.json"
    if bakers_json_path.exists():
        for b in load_json(bakers_json_path):
            if isinstance(b, dict) and "baker_id" in b:
                existing_bakers[b["baker_id"]] = b

    existing_episodes: dict[str, dict[str, Any]] = {}
    episodes_json_path = processed_dir / "episodes.json"
    if episodes_json_path.exists():
        for ep in load_json(episodes_json_path):
            if isinstance(ep, dict) and "episode_id" in ep:
                existing_episodes[ep["episode_id"]] = ep

    existing_performances: dict[str, dict[str, Any]] = {}
    performances_json_path = processed_dir / "performances.json"
    if performances_json_path.exists():
        for perf in load_json(performances_json_path):
            if isinstance(perf, dict) and "performance_id" in perf:
                existing_performances[perf["performance_id"]] = perf

    # 1. Process Bakers
    baker_files = sorted(raw_dir.glob("series_*_bakers.json"))
    logger.info("Found %d baker file(s) in %s", len(baker_files), raw_dir)
    for bf in baker_files:
        items = load_json(bf)
        for raw in items:
            b_id = raw.get("baker_id", "")
            if b_id in existing_bakers:
                for k in ["gender", "image_url"]:
                    if raw.get(k) is None and existing_bakers[b_id].get(k) is not None:
                        raw[k] = existing_bakers[b_id][k]
            try:
                baker = Baker.model_validate(raw)
                bakers_map[baker.baker_id] = baker
            except ValidationError as err:
                validation_errors += 1
                logger.warning("Validation failed for baker in %s: %s", bf.name, err)

    # 2. Process Episodes
    episode_files = sorted(raw_dir.glob("series_*_episodes.json"))
    logger.info("Found %d episode file(s) in %s", len(episode_files), raw_dir)
    for ef in episode_files:
        items = load_json(ef)
        for raw in items:
            e_id = raw.get("episode_id", "")
            if e_id in existing_episodes:
                for k in [
                    "signature_time_min",
                    "technical_time_min",
                    "showstopper_time_min",
                ]:
                    if (
                        raw.get(k) is None
                        and existing_episodes[e_id].get(k) is not None
                    ):
                        raw[k] = existing_episodes[e_id][k]
            try:
                ep = Episode.model_validate(raw)
                episodes_map[ep.episode_id] = ep
            except ValidationError as err:
                validation_errors += 1
                logger.warning("Validation failed for episode in %s: %s", ef.name, err)

    # 3. Process Performances
    perf_files = sorted(raw_dir.glob("series_*_performances.json"))
    logger.info("Found %d performance file(s) in %s", len(perf_files), raw_dir)
    for pf in perf_files:
        items = load_json(pf)
        for raw in items:
            baker_id = raw.get("baker_id", "")
            if baker_id in BAKER_ID_ALIASES:
                raw["baker_id"] = BAKER_ID_ALIASES[baker_id]
                raw["performance_id"] = f"{raw.get('episode_id')}_{raw['baker_id']}"
            p_id = raw.get("performance_id", "")
            if p_id in existing_performances:
                if not raw.get("hollywood_handshake") and existing_performances[
                    p_id
                ].get("hollywood_handshake"):
                    raw["hollywood_handshake"] = True
                if not raw.get("did_well") and existing_performances[p_id].get(
                    "did_well"
                ):
                    raw["did_well"] = True
                if not raw.get("at_risk") and existing_performances[p_id].get(
                    "at_risk"
                ):
                    raw["at_risk"] = True
                if not raw.get("absent") and existing_performances[p_id].get("absent"):
                    raw["absent"] = True
            try:
                perf = Performance.model_validate(raw)
                performances_map[perf.performance_id] = perf
            except ValidationError as err:
                validation_errors += 1
                logger.warning(
                    "Validation failed for performance in %s: %s", pf.name, err
                )

    # Convert to dictionaries for export
    bakers_list = [b.model_dump() for b in bakers_map.values()]
    episodes_list = [e.model_dump() for e in episodes_map.values()]
    performances_list = [p.model_dump(mode="json") for p in performances_map.values()]

    # Sort records
    bakers_list.sort(
        key=lambda x: (x["series_number"], x["overall_placement"] or 99, x["name"])
    )
    episodes_list.sort(key=lambda x: (x["series_number"], x["episode_number"]))
    performances_list.sort(key=lambda x: (x["episode_id"], x["baker_id"]))

    # Write JSON files
    bakers_json_path = processed_dir / "bakers.json"
    with open(bakers_json_path, "w", encoding="utf-8") as f:
        json.dump(bakers_list, f, indent=2, ensure_ascii=False)

    episodes_json_path = processed_dir / "episodes.json"
    with open(episodes_json_path, "w", encoding="utf-8") as f:
        json.dump(episodes_list, f, indent=2, ensure_ascii=False)

    performances_json_path = processed_dir / "performances.json"
    with open(performances_json_path, "w", encoding="utf-8") as f:
        json.dump(performances_list, f, indent=2, ensure_ascii=False)

    # Write CSV & Parquet files
    if bakers_list:
        df_bakers = pd.DataFrame(bakers_list)
        df_bakers.to_csv(processed_dir / "bakers.csv", index=False)
        df_bakers.to_parquet(processed_dir / "bakers.parquet", index=False)
    if episodes_list:
        df_episodes = pd.DataFrame(episodes_list)
        df_episodes.to_csv(processed_dir / "episodes.csv", index=False)
        df_episodes.to_parquet(processed_dir / "episodes.parquet", index=False)
    if performances_list:
        df_performances = pd.DataFrame(performances_list)
        df_performances.to_csv(processed_dir / "performances.csv", index=False)
        df_performances.to_parquet(processed_dir / "performances.parquet", index=False)

    seasons_json = processed_dir / "seasons.json"
    seasons_csv = processed_dir / "seasons.csv"
    if seasons_json.exists():
        s_list = load_json(seasons_json)
        if s_list:
            pd.DataFrame(s_list).to_parquet(
                processed_dir / "seasons.parquet", index=False
            )
    elif seasons_csv.exists():
        pd.read_csv(seasons_csv).to_parquet(
            processed_dir / "seasons.parquet", index=False
        )

    logger.info(
        "Build complete: %d bakers, %d episodes, %d performances written to %s (Errors: %d)",
        len(bakers_list),
        len(episodes_list),
        len(performances_list),
        processed_dir,
        validation_errors,
    )

    return {
        "bakers": len(bakers_list),
        "episodes": len(episodes_list),
        "performances": len(performances_list),
        "errors": validation_errors,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate and validate raw GBBO data."
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=Path("data/raw"), help="Raw data directory"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Processed data directory",
    )

    args = parser.parse_args()
    results = build_datasets(raw_dir=args.raw_dir, processed_dir=args.processed_dir)
    if results["errors"] > 0:
        logger.warning(
            "Build completed with %d validation warnings/errors", results["errors"]
        )


if __name__ == "__main__":
    main()
