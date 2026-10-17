"""NLP Flavor Profile and Bake Style Extraction Engine.

Extracts structured flavor taxonomy, ingredient keywords, and bake style classifications
from natural language dish descriptions across 1,200+ GBBO challenge bakes.
"""

from __future__ import annotations

import itertools
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Structured flavor taxonomy with matching keyword regex patterns
FLAVOR_TAXONOMY: dict[str, list[str]] = {
    "citrus": [
        r"\blemon\b",
        r"\blime\b",
        r"\borange\b",
        r"\byuzu\b",
        r"\bgrapefruit\b",
        r"\bbergamot\b",
        r"\bclementine\b",
        r"\bmandarin\b",
        r"\bkumquat\b",
        r"\bcalamansi\b",
    ],
    "berry": [
        r"\braspberr(?:y|ies)\b",
        r"\bstrawberr(?:y|ies)\b",
        r"\bblackberr(?:y|ies)\b",
        r"\bblueberr(?:y|ies)\b",
        r"\bblackcurrant\b",
        r"\bredcurrant\b",
        r"\bcranberr(?:y|ies)\b",
        r"\belderberr(?:y|ies)\b",
        r"\bgooseberr(?:y|ies)\b",
        r"\blingonberr(?:y|ies)\b",
        r"\bboysenberr(?:y|ies)\b",
    ],
    "chocolate": [
        r"\bchocolate\b",
        r"\bcocoa\b",
        r"\bcacao\b",
        r"\bganache\b",
        r"\bbrownie\b",
        r"\bfudge\b",
        r"\bgianduja\b",
    ],
    "spice": [
        r"\bcinnamon\b",
        r"\bcardamom\b",
        r"\bginger\b",
        r"\bnutmeg\b",
        r"\bclove\b",
        r"\bstar anise\b",
        r"\ballspice\b",
        r"\bsaffron\b",
        r"\bchai\b",
        r"\bchili\b",
        r"\bchilli\b",
        r"\bpepper\b",
        r"\bpaprika\b",
        r"\bturmeric\b",
        r"\bfenugreek\b",
    ],
    "floral": [
        r"\brose(?:water)?\b",
        r"\blavender\b",
        r"\bviolet\b",
        r"\belderflower\b",
        r"\borange blossom\b",
        r"\bhibiscus\b",
        r"\bchamomile\b",
        r"\bjasmine\b",
    ],
    "caramel": [
        r"\bcaramel(?:i[sz]ed)?\b",
        r"\btoffee\b",
        r"\bbutterscotch\b",
        r"\bdulce de leche\b",
        r"\bpraline\b",
        r"\bhoneycomb\b",
        r"\btreacle\b",
        r"\bmaple\b",
        r"\bmolasses\b",
    ],
    "nutty": [
        r"\balmond\b",
        r"\bhazelnut\b",
        r"\bpistachio\b",
        r"\bpecan\b",
        r"\bwalnut\b",
        r"\bpeanut\b",
        r"\bchestnut\b",
        r"\bmacadamia\b",
        r"\bcashew\b",
        r"\bsesame\b",
        r"\btahini\b",
        r"\bmarzipan\b",
        r"\bfrangipane\b",
    ],
    "orchard_fruit": [
        r"\bapple\b",
        r"\bpear\b",
        r"\bpeach\b",
        r"\bplum\b",
        r"\bcherr(?:y|ies)\b",
        r"\bapricot\b",
        r"\bfig\b",
        r"\bquince\b",
        r"\bnectarine\b",
        r"\bdate\b",
        r"\bdates\b",
    ],
    "tropical": [
        r"\bmango\b",
        r"\bpassion\s*fruit\b",
        r"\bcoconut\b",
        r"\bpineapple\b",
        r"\bbanana\b",
        r"\bguava\b",
        r"\bpapaya\b",
        r"\bkiwi\b",
        r"\blychee\b",
        r"\btamarind\b",
    ],
    "coffee_tea": [
        r"\bcoffee\b",
        r"\bespresso\b",
        r"\bmocha\b",
        r"\bmatcha\b",
        r"\bearl grey\b",
        r"\bblack tea\b",
        r"\bgreen tea\b",
    ],
    "savory": [
        r"\bcheese\b",
        r"\bcheddar\b",
        r"\bparmesan\b",
        r"\bfeta\b",
        r"\bgouda\b",
        r"\bbacon\b",
        r"\bham\b",
        r"\bprosciutto\b",
        r"\bgarlic\b",
        r"\bonion\b",
        r"\brosemary\b",
        r"\bthyme\b",
        r"\bbasil\b",
        r"\bsage\b",
        r"\bolive\b",
        r"\btomato\b",
        r"\bmushroom\b",
        r"\bsausage\b",
        r"\bchorizo\b",
        r"\bmarmite\b",
    ],
    "vanilla_dairy": [
        r"\bvanilla\b",
        r"\bcustard\b",
        r"\bclotted cream\b",
        r"\bmascarpone\b",
        r"\bricotta\b",
        r"\bbuttermilk\b",
        r"\byog(?:h)?urt\b",
        r"\bcr[eè]me patissi[eè]re\b",
    ],
    "alcohol": [
        r"\brum\b",
        r"\bbrandy\b",
        r"\bwhisky\b",
        r"\bwhiskey\b",
        r"\bbourbon\b",
        r"\bgin\b",
        r"\bliqueur\b",
        r"\bamaretto\b",
        r"\bprosecco\b",
        r"\bchampagne\b",
        r"\bsherry\b",
        r"\bport\b",
        r"\bcointreau\b",
        r"\bkirsch\b",
        r"\bbaileys\b",
    ],
}

# Structured bake category taxonomy
BAKE_STYLE_TAXONOMY: dict[str, list[str]] = {
    "bread": [
        r"\bsourdough\b",
        r"\bbrioche\b",
        r"\bfocaccia\b",
        r"\bciabatta\b",
        r"\bbagels?\b",
        r"\brye\b",
        r"\bpita\b",
        r"\bchallah\b",
        r"\bbaguettes?\b",
        r"\bflatbreads?\b",
        r"\bnaans?\b",
        r"\brolls?\b",
        r"\bloa(?:f|ves)\b",
        r"\bbuns?\b",
        r"\bbread\b",
    ],
    "pastry": [
        r"\bchoux\b",
        r"\bpuff\s*pastry\b",
        r"\brough\s*puff\b",
        r"\bshortcrust\b",
        r"\bfilo\b",
        r"\bphyllo\b",
        r"\bdanish\b",
        r"\bcroissants?\b",
        r"\bmille-?feuilles?\b",
        r"\beclairs?\b",
        r"\bgoug[eè]res?\b",
        r"\bprofiteroles?\b",
        r"\bpastry\b",
    ],
    "tart_pie": [
        r"\btart(?:let)?s?\b",
        r"\bpies?\b",
        r"\bgalettes?\b",
        r"\bquiches?\b",
        r"\bpast(?:y|ies)\b",
        r"\btourtes?\b",
    ],
    "cake_sponge": [
        r"\bsponges?\b",
        r"\bg[eé]noises?\b",
        r"\bchiffons?\b",
        r"\bangel\s*food\b",
        r"\bvictoria\s*sponge\b",
        r"\bbundts?\b",
        r"\bg[aâ]teaux?\b",
        r"\broulades?\b",
        r"\bentremets?\b",
        r"\bcupcakes?\b",
        r"\bcakes?\b",
    ],
    "biscuit_cookie": [
        r"\bbiscuits?\b",
        r"\bcookies?\b",
        r"\bshortbread\b",
        r"\bgingerbread\b",
        r"\bmacarons?\b",
        r"\bbiscotti\b",
        r"\btuiles?\b",
        r"\bwafers?\b",
        r"\bsabl[eé]s?\b",
    ],
    "dessert_meringue": [
        r"\bmeringues?\b",
        r"\bpavlovas?\b",
        r"\bmousses?\b",
        r"\bpanna\s*cottas?\b",
        r"\bcheesecakes?\b",
        r"\bparfaits?\b",
        r"\bsouffl[eé]s?\b",
        r"\bpuddings?\b",
        r"\btrifles?\b",
        r"\btiramisu\b",
    ],
}


def extract_flavors(text: str | None) -> list[str]:
    """Extract canonical flavor families from dish description text."""
    if not text or not isinstance(text, str):
        return []

    t_lower = text.lower()
    detected = []
    for flavor_family, patterns in FLAVOR_TAXONOMY.items():
        if any(re.search(pat, t_lower) for pat in patterns):
            detected.append(flavor_family)

    return sorted(detected)


def extract_bake_styles(text: str | None) -> list[str]:
    """Extract canonical bake categories from dish description text."""
    if not text or not isinstance(text, str):
        return []

    t_lower = text.lower()
    detected = []
    for style, patterns in BAKE_STYLE_TAXONOMY.items():
        if any(re.search(pat, t_lower) for pat in patterns):
            detected.append(style)

    return sorted(detected)


def enrich_performances_with_nlp(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich performances DataFrame with extracted flavor and style tags."""
    enriched = df.copy()

    sig_col = "signature_dish" if "signature_dish" in enriched.columns else None
    show_col = "showstopper_dish" if "showstopper_dish" in enriched.columns else None

    sig_flavors = (
        enriched[sig_col].apply(extract_flavors)
        if sig_col
        else [[] for _ in range(len(enriched))]
    )
    sig_styles = (
        enriched[sig_col].apply(extract_bake_styles)
        if sig_col
        else [[] for _ in range(len(enriched))]
    )

    show_flavors = (
        enriched[show_col].apply(extract_flavors)
        if show_col
        else [[] for _ in range(len(enriched))]
    )
    show_styles = (
        enriched[show_col].apply(extract_bake_styles)
        if show_col
        else [[] for _ in range(len(enriched))]
    )

    all_flavors = [
        sorted(set(sf + shf))
        for sf, shf in zip(sig_flavors, show_flavors, strict=False)
    ]
    all_styles = [
        sorted(set(sig_s + show_s))
        for sig_s, show_s in zip(sig_styles, show_styles, strict=False)
    ]

    enriched["signature_flavors"] = [", ".join(f) for f in sig_flavors]
    enriched["signature_styles"] = [", ".join(s) for s in sig_styles]
    enriched["showstopper_flavors"] = [", ".join(f) for f in show_flavors]
    enriched["showstopper_styles"] = [", ".join(s) for s in show_styles]
    enriched["all_flavors"] = [", ".join(f) for f in all_flavors]
    enriched["all_styles"] = [", ".join(s) for s in all_styles]

    return enriched


def calculate_flavor_statistics(performances: pd.DataFrame) -> dict[str, Any]:
    """Calculate frequency, co-occurrence, and outcome correlations for flavors."""
    if performances.empty:
        return {
            "flavor_counts": {},
            "style_counts": {},
            "handshake_rates": {},
            "star_baker_rates": {},
            "co_occurring_pairs": [],
        }

    flavor_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    handshake_counter: Counter[str] = Counter()
    star_baker_counter: Counter[str] = Counter()
    pair_counter: Counter[tuple[str, str]] = Counter()

    for _, row in performances.iterrows():
        sig = row.get("signature_dish")
        show = row.get("showstopper_dish")
        hs = bool(row.get("hollywood_handshake", False))
        res = str(row.get("result", "")).upper()
        is_star = res in ("STAR_BAKER", "WINNER")

        flavors = set(extract_flavors(sig) + extract_flavors(show))
        styles = set(extract_bake_styles(sig) + extract_bake_styles(show))

        for f in flavors:
            flavor_counter[f] += 1
            if hs:
                handshake_counter[f] += 1
            if is_star:
                star_baker_counter[f] += 1

        for s in styles:
            style_counter[s] += 1

        # Co-occurrence of flavors
        if len(flavors) >= 2:
            for p1, p2 in itertools.combinations(sorted(flavors), 2):
                pair_counter[(p1, p2)] += 1

    handshake_rates = {
        f: round(handshake_counter[f] / count * 100, 1)
        for f, count in flavor_counter.items()
        if count >= 10
    }
    star_baker_rates = {
        f: round(star_baker_counter[f] / count * 100, 1)
        for f, count in flavor_counter.items()
        if count >= 10
    }

    top_pairs = [
        {"pair": f"{p[0]} + {p[1]}", "count": count}
        for p, count in pair_counter.most_common(15)
    ]

    return {
        "flavor_counts": dict(flavor_counter.most_common()),
        "style_counts": dict(style_counter.most_common()),
        "handshake_rates": dict(
            sorted(handshake_rates.items(), key=lambda x: x[1], reverse=True)
        ),
        "star_baker_rates": dict(
            sorted(star_baker_rates.items(), key=lambda x: x[1], reverse=True)
        ),
        "co_occurring_pairs": top_pairs,
    }


def run_nlp_flavor_pipeline(
    processed_dir: Path = Path("data/processed"),
    output_file: str = "bakes_nlp.json",
) -> dict[str, Any]:
    """Execute end-to-end NLP flavor and style tagging over processed performances."""
    parquet_path = processed_dir / "performances.parquet"
    csv_path = processed_dir / "performances.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Performances table not found in {processed_dir}")

    enriched = enrich_performances_with_nlp(df)
    stats = calculate_flavor_statistics(df)

    out_json = processed_dir / output_file
    out_csv = processed_dir / (Path(output_file).stem + ".csv")
    stats_json = processed_dir / "flavor_analytics.json"

    # Export records
    records = enriched.to_dict(orient="records")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    enriched.to_csv(out_csv, index=False)

    with open(stats_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    logger.info(
        "Successfully exported NLP tagged bakes to %s and %s", out_json, out_csv
    )
    return {
        "bakes_tagged": len(enriched),
        "unique_flavors": len(stats["flavor_counts"]),
        "unique_styles": len(stats["style_counts"]),
        "stats": stats,
    }
