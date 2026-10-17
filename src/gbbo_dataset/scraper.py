"""Scrape Great British Bake Off (GBBO) series tables from Wikipedia."""

import argparse
import io
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from gbbo_dataset.models import Baker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = (
    "GBBODataset/0.1.0 (https://github.com/nicholaswilde/the-great-british-bake-off)"
)


def clean_text(val: Any) -> str:
    """Clean Wikipedia text: remove citations [1], extra whitespace, newlines."""
    if val is None or pd.isna(val):
        return ""
    text = str(val)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_placement(placement_str: str) -> int | None:
    """Extract integer placement rank from strings like '1st', 'Winner', '9th (tie)'."""
    text = placement_str.lower()
    if "winner" in text or text.startswith("1st"):
        return 1
    if "runner" in text or text.startswith("2nd"):
        return 2
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def fetch_series_html(series: int) -> str:
    """Fetch HTML for a given GBBO series from Wikipedia."""
    headers = {"User-Agent": USER_AGENT}
    candidate_urls = [
        f"https://en.wikipedia.org/wiki/The_Great_British_Bake_Off_(series_{series})",
        f"https://en.wikipedia.org/wiki/The_Great_British_Bake_Off_series_{series}",
    ]
    for url in candidate_urls:
        logger.info("Fetching %s", url)
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.text
        if resp.status_code != 404:
            resp.raise_for_status()

    raise FileNotFoundError(f"Series {series} not found on Wikipedia (404)")


def find_bakers_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    """Identify the 'The Bakers' DataFrame from Wikipedia tables."""
    for df in tables:
        # Normalize column names
        cleaned_cols = [clean_text(c).lower() for c in df.columns]
        has_baker = any(k in cleaned_cols for k in ["baker", "contestant", "name"])
        has_age = any("age" in k for k in cleaned_cols)
        if has_baker and has_age:
            return df


def find_elimination_matrix(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    """Identify the Elimination Matrix DataFrame."""
    for df in tables:
        cols = [clean_text(c).lower() for c in df.columns]
        has_baker = any(c in ["baker", "contestant"] for c in cols)
        has_nums = any(re.match(r"^\d+$", str(c).strip()) for c in df.columns)
        if has_baker and has_nums:
            return df
    return None


def extract_placements_from_matrix(df: pd.DataFrame) -> dict[str, int]:
    """Derive overall placement from elimination matrix."""
    placements: dict[str, int] = {}
    for idx, row in df.iterrows():
        baker_name = clean_text(row.iloc[0])
        if not baker_name or baker_name.lower() in ["baker", "contestant"]:
            continue
        first_name = re.sub(r"[^a-z0-9]", "", baker_name.split()[0].lower())
        last_val = ""
        for col_idx in range(len(row) - 1, 0, -1):
            val = clean_text(row.iloc[col_idx])
            if val and val.lower() not in ["nan", "none", ""]:
                last_val = val.lower()
                break
        if "winner" in last_val:
            rank = 1
        elif "runner" in last_val:
            rank = 2
        else:
            rank = idx + 1
        placements[first_name] = rank
        placements[baker_name.lower()] = rank
    return placements


def extract_bakers(
    series: int, df: pd.DataFrame, matrix_placements: dict[str, int] | None = None
) -> list[dict[str, Any]]:
    """Clean and structure the Bakers table into raw records."""
    df_clean = df.copy()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
    )
    logger.info("Extracting bakers from table...")

    # Flatten multi-level columns if present
    if isinstance(df_clean.columns, pd.MultiIndex):
        df_clean.columns = [
            clean_text("_".join(map(str, col))) for col in df_clean.columns
        ]
    else:
        df_clean.columns = [clean_text(c) for c in df_clean.columns]

    cols_lower = {col: col.lower() for col in df_clean.columns}

    baker_col = next(
        (
            c
            for c, l in cols_lower.items()
            if any(k in l for k in ["baker", "contestant", "name"])
        ),
        None,
    )
    age_col = next((c for c, l in cols_lower.items() if "age" in l), None)
    occ_col = next(
        (c for c, l in cols_lower.items() if "occupation" in l or "job" in l), None
    )
    town_col = next(
        (
            c
            for c, l in cols_lower.items()
            if "hometown" in l or "town" in l or "home" in l
        ),
        None,
    )
    # Prefer explicit 'place' column over 'finish' column
    place_col = next((c for c, l in cols_lower.items() if "place" in l), None) or next(
        (c for c, l in cols_lower.items() if any(k in l for k in ["finish", "result"])),
        None,
    )

    if not baker_col:
        raise ValueError("Could not find baker / contestant column in table")

    bakers: list[dict[str, Any]] = []
    for _, row in df_clean.iterrows():
        raw_name = clean_text(row.get(baker_col, ""))
        if not raw_name or raw_name.lower() in ["contestant", "baker", "total"]:
            continue

        raw_age = clean_text(row.get(age_col, "")) if age_col else None
        age = None
        if raw_age:
            try:
                age = int(float(raw_age))
            except (ValueError, TypeError):
                age = None

        occ = clean_text(row.get(occ_col, "")) if occ_col else None
        town = clean_text(row.get(town_col, "")) if town_col else None
        place_str = clean_text(row.get(place_col, "")) if place_col else ""
        placement = parse_placement(place_str) if place_str else None

        baker_id = Baker.generate_baker_id(series, raw_name)
        clean_first = baker_id.split("_", 1)[1]

        if placement is None and matrix_placements:
            placement = matrix_placements.get(clean_first) or next(
                (v for k, v in matrix_placements.items() if k in raw_name.lower()),
                None,
            )

        bakers.append(
            {
                "baker_id": baker_id,
                "series_number": series,
                "name": raw_name,
                "age": age,
                "occupation": occ or None,
                "hometown": town or None,
                "overall_placement": placement,
                "raw_placement_text": place_str or None,
            }
        )
    return bakers


def extract_air_dates(soup: BeautifulSoup) -> dict[int, str]:
    """Extract air dates by episode number from Wikipedia Ratings table."""
    air_dates: dict[int, str] = {}
    ratings_h = soup.find(
        lambda t: t.name in ["h2", "h3"] and "ratings" in t.text.lower()
    )
    table = ratings_h.find_next("table") if ratings_h else None
    if table:
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]
            ep_col = next(
                (c for c in df.columns if "episode" in clean_text(c).lower()), None
            )
            date_col = next(
                (
                    c
                    for c in df.columns
                    if "air" in clean_text(c).lower() or "date" in clean_text(c).lower()
                ),
                None,
            )
            if ep_col and date_col:
                for _, row in df.iterrows():
                    raw_ep = clean_text(row.get(ep_col, ""))
                    raw_date = clean_text(row.get(date_col, ""))
                    ep_match = re.search(r"(\d+)", raw_ep)
                    if ep_match and raw_date:
                        ep_num = int(ep_match.group(1))
                        try:
                            dt = pd.to_datetime(raw_date, dayfirst=True)
                            air_dates[ep_num] = dt.strftime("%Y-%m-%d")
                        except Exception:
                            air_dates[ep_num] = raw_date
        except Exception as e:
            logger.warning("Could not parse ratings table for air dates: %s", e)

    if not air_dates:
        infobox = soup.select_one(".infobox")
        if infobox:
            for tr in infobox.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if th and td and "release" in th.get_text().lower():
                    date_match = re.search(
                        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})", td.get_text()
                    )
                    if date_match:
                        try:
                            start_dt = pd.to_datetime(
                                date_match.group(1), dayfirst=True
                            )
                            for ep_i in range(1, 11):
                                ep_dt = start_dt + pd.Timedelta(weeks=ep_i - 1)
                                air_dates[ep_i] = ep_dt.strftime("%Y-%m-%d")
                        except Exception as err:
                            logger.warning(
                                "Could not compute air dates from infobox: %s", err
                            )
                    break

    return air_dates


def resolve_baker_id(
    series: int, table_baker_name: str, bakers: list[dict[str, Any]] | None = None
) -> str:
    """Resolve baker name from challenge table to canonical baker_id."""
    clean_first = re.sub(r"[^a-z0-9]", "", table_baker_name.split()[0].lower())
    default_id = f"s{series:02d}_{clean_first}"
    if not bakers:
        return default_id

    cand = table_baker_name.strip().lower()
    # 1. Exact baker_id match
    for b in bakers:
        if b.get("baker_id") == f"s{series:02d}_{cand}":
            return b["baker_id"]
    # 2. Nickname in quotes in name (e.g. quoted aliases like Rebs, Maxy, Sandro)
    for b in bakers:
        b_name = b.get("name", "").lower()
        if f"'{cand}'" in b_name or f'"{cand}"' in b_name:
            return b["baker_id"]
    # 3. Word match in full name
    for b in bakers:
        words = [re.sub(r"[^a-z0-9]", "", w) for w in b.get("name", "").lower().split()]
        if cand in words:
            return b["baker_id"]
    # 4. Substring match
    for b in bakers:
        if cand in b.get("name", "").lower():
            return b["baker_id"]
    return default_id


def extract_episodes_and_performances(
    series: int,
    soup: BeautifulSoup,
    tables: list[pd.DataFrame],
    bakers: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract episode themes and challenge performances from Wikipedia tables."""
    episodes: list[dict[str, Any]] = []
    performances: list[dict[str, Any]] = []

    air_dates = extract_air_dates(soup)

    # Search for headings mentioning Episode
    episode_headings = soup.find_all(re.compile(r"^h[2-4]$"))
    ep_num = 1
    seen_eps: set[int] = set()

    for head in episode_headings:
        text = clean_text(head.get_text())
        if any(
            k in text.lower()
            for k in ["masterclass", "special", "celebrity", "extras", "controversy"]
        ):
            break
        ep_match = re.search(r"Episode\s+(\d+)[:\s]*(.*)", text, re.IGNORECASE)
        if ep_match:
            ep_idx = int(ep_match.group(1))
            if ep_idx in seen_eps:
                break
            seen_eps.add(ep_idx)
            theme = ep_match.group(2).strip() or None
            episode_id = f"s{series:02d}e{ep_idx:02d}"
            episodes.append(
                {
                    "episode_id": episode_id,
                    "series_number": series,
                    "episode_number": ep_idx,
                    "theme": theme,
                    "air_date": air_dates.get(ep_idx),
                }
            )

    # Search for challenge tables (tables with Signature, Technical, or Showstopper)
    for table_idx, df in enumerate(tables):
        if episodes and ep_num > len(episodes):
            break
        cols = [clean_text(c).lower() for c in df.columns]
        is_challenge_table = any("signature" in c for c in cols) or any(
            "showstopper" in c for c in cols
        )
        if not is_challenge_table:
            continue

        baker_col = next(
            (c for c in df.columns if clean_text(c).lower() in ["baker", "contestant"]),
            None,
        )
        if not baker_col:
            continue

        sig_col = next(
            (c for c in df.columns if "signature" in clean_text(c).lower()), None
        )
        tech_col = next(
            (c for c in df.columns if "technical" in clean_text(c).lower()), None
        )
        show_col = next(
            (c for c in df.columns if "showstopper" in clean_text(c).lower()), None
        )
        res_col = next(
            (c for c in df.columns if "result" in clean_text(c).lower()), None
        )

        current_ep = min(ep_num, len(episodes)) if episodes else ep_num
        episode_id = f"s{series:02d}e{current_ep:02d}"

        for _, row in df.iterrows():
            name = clean_text(row.get(baker_col, ""))
            if not name or name.lower() in ["baker", "contestant"]:
                continue

            baker_id = resolve_baker_id(series, name, bakers)

            sig_text = clean_text(row.get(sig_col, "")) if sig_col else None
            tech_raw = clean_text(row.get(tech_col, "")) if tech_col else None
            tech_rank = None
            if tech_raw:
                rank_match = re.search(r"(\d+)", tech_raw)
                if rank_match:
                    tech_rank = int(rank_match.group(1))

            show_text = clean_text(row.get(show_col, "")) if show_col else None
            res_text = clean_text(row.get(res_col, "")) if res_col else ""

            # Standardize outcome
            res_upper = res_text.upper()
            if "STAR BAKER" in res_upper:
                result = "STAR_BAKER"
            elif "ELIMINATED" in res_upper or "OUT" in res_upper:
                result = "ELIMINATED"
            elif "WINNER" in res_upper:
                result = "WINNER"
            elif "RUNNER" in res_upper:
                result = "RUNNER_UP"
            elif "WITHDREW" in res_upper:
                result = "WITHDREW"
            else:
                result = "SAFE"

            # Detect Hollywood Handshake mention in any challenge text
            all_bakes_text = f"{sig_text or ''} {show_text or ''}".lower()
            handshake = (
                "handshake" in all_bakes_text or "hollywood handshake" in all_bakes_text
            )

            performance_id = f"{episode_id}_{baker_id}"
            performances.append(
                {
                    "performance_id": performance_id,
                    "baker_id": baker_id,
                    "episode_id": episode_id,
                    "signature_dish": sig_text or None,
                    "technical_rank": tech_rank,
                    "showstopper_dish": show_text or None,
                    "result": result,
                    "hollywood_handshake": handshake,
                }
            )
        ep_num += 1

    return episodes, performances


def scrape_series(series: int, raw_dir: Path) -> dict[str, Any]:
    """Execute scraping pipeline for one series and write raw JSON output."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    html = fetch_series_html(series)
    soup = BeautifulSoup(html, "html.parser")
    tables = pd.read_html(io.StringIO(html))

    bakers_df = find_bakers_table(tables)
    if bakers_df is None:
        raise ValueError(f"Could not locate The Bakers table for Series {series}")

    matrix_df = find_elimination_matrix(tables)
    matrix_placements = (
        extract_placements_from_matrix(matrix_df) if matrix_df is not None else {}
    )

    bakers = extract_bakers(series, bakers_df, matrix_placements)
    episodes, performances = extract_episodes_and_performances(
        series, soup, tables, bakers=bakers
    )

    # Save raw extracted bakers JSON
    bakers_file = raw_dir / f"series_{series}_bakers.json"
    with open(bakers_file, "w", encoding="utf-8") as f:
        json.dump(bakers, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d bakers to %s", len(bakers), bakers_file)

    # Save raw extracted episodes & performances
    if episodes:
        episodes_file = raw_dir / f"series_{series}_episodes.json"
        with open(episodes_file, "w", encoding="utf-8") as f:
            json.dump(episodes, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d episodes to %s", len(episodes), episodes_file)

    if performances:
        perf_file = raw_dir / f"series_{series}_performances.json"
        with open(perf_file, "w", encoding="utf-8") as f:
            json.dump(performances, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d performances to %s", len(performances), perf_file)

    return {
        "series": series,
        "bakers": bakers,
        "episodes": episodes,
        "performances": performances,
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape GBBO data from Wikipedia.")
    parser.add_argument(
        "--series", "-s", type=int, default=1, help="Series number (e.g. 1)"
    )
    parser.add_argument(
        "--start", type=int, default=None, help="Start series number for range"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="End series number for range"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("data/raw"),
        help="Output directory",
    )

    args = parser.parse_args()

    if args.start is not None and args.end is not None:
        series_range = range(args.start, args.end + 1)
    else:
        series_range = [args.series]

    for s in series_range:
        try:
            logger.info("Scraping Series %d...", s)
            scrape_series(s, args.output_dir)
        except Exception as e:
            logger.error("Failed to scrape Series %d: %s", s, e)
            if len(series_range) == 1:
                sys.exit(1)


if __name__ == "__main__":
    main()
