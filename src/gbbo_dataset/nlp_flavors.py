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

# Modern structural and technique taxonomy
TECHNIQUE_STYLE_TAXONOMY: dict[str, list[str]] = {
    "Illusion / 3D": [
        r"\billusion\b",
        r"\b(?:sculpted|sculpture|sculpt)\b",
        r"\b3d\b",
        r"\blandscape\b",
        r"\bportrait\b",
        r"\bbust\b",
        r"\bpuppet\b",
        r"\btheatre\b",
    ],
    "Geometric / Tiered": [
        r"\bgeometric\b",
        r"\btower\b",
        r"\btiered\b",
        r"\btiers\b",
        r"\bconstruction\b",
        r"\barchitectur(?:e|al)\b",
    ],
    "Mirror Glaze": [
        r"\bmirror\s*glaze\b",
        r"\bglac[eé]\b",
    ],
    "Gluten-Free": [
        r"\bgluten-?free\b",
        r"\bwheat-?free\b",
        r"\bflourless\b",
    ],
    "Vegan / Plant-Based": [
        r"\bvegan\b",
        r"\bplant-?based\b",
        r"\bdairy-?free\b",
        r"\begg-?free\b",
        r"\baquafaba\b",
    ],
}

# Granular ingredient keywords and categories for risk indexing
INGREDIENT_KEYWORD_TAXONOMY: dict[str, tuple[str, str]] = {
    "Rose": (r"\brose(?:water)?\b", "Botanical & Floral"),
    "Lavender": (r"\blavender\b", "Botanical & Floral"),
    "Matcha": (r"\bmatcha\b", "Tea & Botanical"),
    "Elderflower": (r"\belderflower\b", "Botanical & Floral"),
    "Orange Blossom": (r"\borange blossom\b", "Botanical & Floral"),
    "Lemon": (r"\blemon\b", "Citrus"),
    "Lime": (r"\blime\b", "Citrus"),
    "Orange": (r"\borange\b", "Citrus"),
    "Grapefruit": (r"\bgrapefruit\b", "Citrus"),
    "Yuzu": (r"\byuzu\b", "Citrus"),
    "Raspberry": (r"\braspberr(?:y|ies)\b", "Berry"),
    "Strawberry": (r"\bstrawberr(?:y|ies)\b", "Berry"),
    "Blackberry": (r"\bblackberr(?:y|ies)\b", "Berry"),
    "Blueberry": (r"\bblueberr(?:y|ies)\b", "Berry"),
    "Blackcurrant": (r"\bblackcurrant\b", "Berry"),
    "Cardamom": (r"\bcardamom\b", "Warm Spice"),
    "Cinnamon": (r"\bcinnamon\b", "Warm Spice"),
    "Ginger": (r"\bginger\b", "Warm Spice"),
    "Nutmeg": (r"\bnutmeg\b", "Warm Spice"),
    "Saffron": (r"\bsaffron\b", "Warm Spice"),
    "Chilli": (r"\bchilli?\b", "Spice"),
    "Chocolate": (r"\bchocolate|cocoa|cacao|ganache\b", "Staple Sweet"),
    "Caramel": (r"\bcaramel(?:i[sz]ed)?|toffee|butterscotch\b", "Staple Sweet"),
    "Vanilla": (r"\bvanilla\b", "Staple Sweet"),
    "Coffee": (r"\bcoffee|espresso|mocha\b", "Coffee & Tea"),
    "Pistachio": (r"\bpistachio\b", "Nutty"),
    "Almond": (r"\balmond|frangipane\b", "Nutty"),
    "Hazelnut": (r"\bhazelnut|praline\b", "Nutty"),
    "Pecan": (r"\bpecan\b", "Nutty"),
    "Walnut": (r"\bwalnut\b", "Nutty"),
    "Peanut Butter": (r"\bpeanut\b", "Nutty"),
    "Passion Fruit": (r"\bpassion\s*fruit\b", "Tropical Fruit"),
    "Mango": (r"\bmango\b", "Tropical Fruit"),
    "Coconut": (r"\bcoconut\b", "Tropical Fruit"),
    "Banana": (r"\bbanana\b", "Fruit"),
    "Apple": (r"\bapple\b", "Orchard Fruit"),
    "Pear": (r"\bpear\b", "Orchard Fruit"),
    "Cherry": (r"\bcherr(?:y|ies)\b", "Orchard Fruit"),
    "Fig": (r"\bfig\b", "Fruit"),
    "Cheese": (r"\bcheese|cheddar|parmesan|feta|gouda\b", "Savory"),
    "Bacon & Pork": (r"\bbacon|pork|pancetta|prosciutto|sausage\b", "Savory"),
    "Rum": (r"\brum\b", "Alcohol"),
    "Gin": (r"\bgin\b", "Alcohol"),
    "Kirsch & Liqueur": (r"\bkirsch|amaretto|cointreau|liqueur\b", "Alcohol"),
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


def extract_techniques(text: str | None) -> list[str]:
    """Extract modern bake techniques (illusion, mirror glaze, geometric, vegan, etc.)."""
    if not text or not isinstance(text, str):
        return []
    t_lower = text.lower()
    detected = []
    for tech, patterns in TECHNIQUE_STYLE_TAXONOMY.items():
        if any(re.search(pat, t_lower) for pat in patterns):
            detected.append(tech)
    return sorted(detected)


def calculate_ingredient_risk_matrix(
    performances: pd.DataFrame, min_bakes: int = 3
) -> list[dict[str, Any]]:
    """Compute risk matrix for individual key ingredients."""
    if performances.empty:
        return []

    records: list[dict[str, Any]] = []
    sig_col = performances.get("signature_dish", pd.Series(dtype=str)).fillna("")
    show_col = performances.get("showstopper_dish", pd.Series(dtype=str)).fillna("")

    res_col = performances.get("result", pd.Series(dtype=str)).astype(str).str.upper()
    at_risk_col = (
        performances.get("at_risk", pd.Series(dtype=bool)).fillna(False).astype(bool)
    )
    hs_col = (
        performances.get("hollywood_handshake", pd.Series(dtype=bool))
        .fillna(False)
        .astype(bool)
    )

    is_danger = res_col.isin(["ELIMINATED", "WITHDREW"]) | at_risk_col
    is_elim = res_col.isin(["ELIMINATED", "WITHDREW"])
    is_star = res_col.isin(["STAR_BAKER", "WINNER"])

    for ing, (pat, cat) in INGREDIENT_KEYWORD_TAXONOMY.items():
        regex = re.compile(pat, re.IGNORECASE)
        mask = sig_col.str.contains(regex) | show_col.str.contains(regex)
        tot = int(mask.sum())
        if tot >= min_bakes:
            danger_cnt = int((mask & is_danger).sum())
            elim_cnt = int((mask & is_elim).sum())
            star_cnt = int((mask & is_star).sum())
            hs_cnt = int((mask & hs_col).sum())

            danger_rate = round(danger_cnt / tot * 100, 1)
            tier = (
                "🚨 High Risk"
                if danger_rate >= 35.0
                else ("⚠️ Moderate Risk" if danger_rate >= 25.0 else "✅ Safe Haven")
            )
            records.append(
                {
                    "ingredient": ing,
                    "category": cat,
                    "bakes_count": tot,
                    "danger_count": danger_cnt,
                    "danger_rate_pct": danger_rate,
                    "elim_rate_pct": round(elim_cnt / tot * 100, 1),
                    "star_baker_pct": round(star_cnt / tot * 100, 1),
                    "handshake_pct": round(hs_cnt / tot * 100, 1),
                    "risk_tier": tier,
                }
            )

    return sorted(records, key=lambda x: x["danger_rate_pct"], reverse=True)


def calculate_family_risk_matrix(
    performances: pd.DataFrame, min_bakes: int = 5
) -> list[dict[str, Any]]:
    """Compute risk matrix for broad flavor families."""
    if performances.empty:
        return []

    records: list[dict[str, Any]] = []
    res_col = performances.get("result", pd.Series(dtype=str)).astype(str).str.upper()
    at_risk_col = (
        performances.get("at_risk", pd.Series(dtype=bool)).fillna(False).astype(bool)
    )
    hs_col = (
        performances.get("hollywood_handshake", pd.Series(dtype=bool))
        .fillna(False)
        .astype(bool)
    )

    is_danger = res_col.isin(["ELIMINATED", "WITHDREW"]) | at_risk_col
    is_elim = res_col.isin(["ELIMINATED", "WITHDREW"])
    is_star = res_col.isin(["STAR_BAKER", "WINNER"])

    all_flavors_per_row = [
        set(extract_flavors(sig) + extract_flavors(show))
        for sig, show in zip(
            performances.get("signature_dish", []),
            performances.get("showstopper_dish", []),
            strict=False,
        )
    ]

    for fam in FLAVOR_TAXONOMY:
        mask = pd.Series(
            [fam in flvs for flvs in all_flavors_per_row], index=performances.index
        )
        tot = int(mask.sum())
        if tot >= min_bakes:
            danger_cnt = int((mask & is_danger).sum())
            elim_cnt = int((mask & is_elim).sum())
            star_cnt = int((mask & is_star).sum())
            hs_cnt = int((mask & hs_col).sum())

            danger_rate = round(danger_cnt / tot * 100, 1)
            tier = (
                "🚨 High Risk"
                if danger_rate >= 32.0
                else ("⚠️ Moderate Risk" if danger_rate >= 27.0 else "✅ Safe Haven")
            )
            records.append(
                {
                    "flavor_family": fam.capitalize(),
                    "bakes_count": tot,
                    "danger_count": danger_cnt,
                    "danger_rate_pct": danger_rate,
                    "elim_rate_pct": round(elim_cnt / tot * 100, 1),
                    "star_baker_pct": round(star_cnt / tot * 100, 1),
                    "handshake_pct": round(hs_cnt / tot * 100, 1),
                    "risk_tier": tier,
                }
            )

    return sorted(records, key=lambda x: x["danger_rate_pct"], reverse=True)


def calculate_cooccurrence_affinity(
    performances: pd.DataFrame, min_pairs: int = 5
) -> list[dict[str, Any]]:
    """Compute co-occurrence pairing affinity comparing Star Baker vs Eliminated outcomes."""
    if performances.empty:
        return []

    star_pairs: Counter[tuple[str, str]] = Counter()
    elim_pairs: Counter[tuple[str, str]] = Counter()
    all_pairs: Counter[tuple[str, str]] = Counter()

    for _, row in performances.iterrows():
        sig = row.get("signature_dish")
        show = row.get("showstopper_dish")
        flavors = sorted(set(extract_flavors(sig) + extract_flavors(show)))
        if len(flavors) >= 2:
            pairs = list(itertools.combinations(flavors, 2))
            res = str(row.get("result", "")).upper()
            is_star = res in ("STAR_BAKER", "WINNER")
            is_elim = res in ("ELIMINATED", "WITHDREW") or bool(
                row.get("at_risk", False)
            )
            for p in pairs:
                all_pairs[p] += 1
                if is_star:
                    star_pairs[p] += 1
                if is_elim:
                    elim_pairs[p] += 1

    records: list[dict[str, Any]] = []
    for p, total in all_pairs.items():
        if total >= min_pairs:
            s_count = star_pairs[p]
            e_count = elim_pairs[p]
            affinity = (
                "⭐️ Star Baker Favored"
                if s_count > e_count
                else (
                    "🚨 Elimination Trap" if e_count > s_count else "⚖️ Balanced Harmony"
                )
            )
            records.append(
                {
                    "pair": f"{p[0].capitalize()} + {p[1].capitalize()}",
                    "total_bakes": total,
                    "star_baker_bakes": s_count,
                    "eliminated_bakes": e_count,
                    "star_rate_pct": round(s_count / total * 100, 1),
                    "elim_rate_pct": round(e_count / total * 100, 1),
                    "outcome_affinity": affinity,
                }
            )

    return sorted(records, key=lambda x: x["total_bakes"], reverse=True)


def calculate_technique_evolution(
    performances: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Calculate longitudinal time series of modern baking techniques across series."""
    if performances.empty:
        return []

    df = performances.copy()
    if "episode_id" in df.columns:
        series_s = df["episode_id"].astype(str).str.extract(r"s(\d+)e")[0]
        df["series_number"] = (
            pd.to_numeric(series_s, errors="coerce").fillna(1).astype(int)
        )
    elif "series_number" not in df.columns:
        return []

    sig_col = df.get("signature_dish", pd.Series(dtype=str)).fillna("")
    show_col = df.get("showstopper_dish", pd.Series(dtype=str)).fillna("")

    records: list[dict[str, Any]] = []
    for s_num in sorted(df["series_number"].unique()):
        s_mask = df["series_number"] == s_num
        s_sig = sig_col[s_mask]
        s_show = show_col[s_mask]
        for tech, pats in TECHNIQUE_STYLE_TAXONOMY.items():
            pat = "|".join(pats)
            regex = re.compile(pat, re.IGNORECASE)
            count = int((s_sig.str.contains(regex) | s_show.str.contains(regex)).sum())
            records.append(
                {
                    "series_number": int(s_num),
                    "series_label": f"Series {int(s_num)}",
                    "technique": tech,
                    "bakes_count": count,
                }
            )

    return records


def calculate_category_evolution(
    performances: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Calculate longitudinal time series of canonical bake styles across series."""
    if performances.empty:
        return []

    df = performances.copy()
    if "episode_id" in df.columns:
        series_s = df["episode_id"].astype(str).str.extract(r"s(\d+)e")[0]
        df["series_number"] = (
            pd.to_numeric(series_s, errors="coerce").fillna(1).astype(int)
        )
    elif "series_number" not in df.columns:
        return []

    records: list[dict[str, Any]] = []
    for s_num in sorted(df["series_number"].unique()):
        s_df = df[df["series_number"] == s_num]
        style_counts: Counter[str] = Counter()
        for _, row in s_df.iterrows():
            styles = set(
                extract_bake_styles(row.get("signature_dish"))
                + extract_bake_styles(row.get("showstopper_dish"))
            )
            for st in styles:
                style_counts[st] += 1

        for cat, display_name in [
            ("cake_sponge", "Cake & Sponge"),
            ("bread", "Bread"),
            ("tart_pie", "Tart & Pie"),
            ("biscuit_cookie", "Biscuit & Cookie"),
            ("pastry", "Pastry"),
            ("dessert_meringue", "Dessert & Meringue"),
        ]:
            records.append(
                {
                    "series_number": int(s_num),
                    "series_label": f"Series {int(s_num)}",
                    "category": display_name,
                    "bakes_count": style_counts.get(cat, 0),
                }
            )

    return records


def calculate_flavor_statistics(performances: pd.DataFrame) -> dict[str, Any]:
    """Calculate frequency, co-occurrence, and outcome correlations for flavors."""
    if performances.empty:
        return {
            "flavor_counts": {},
            "style_counts": {},
            "handshake_rates": {},
            "star_baker_rates": {},
            "co_occurring_pairs": [],
            "ingredient_risk_matrix": [],
            "family_risk_matrix": [],
            "cooccurrence_affinity": [],
            "technique_evolution": [],
            "category_evolution": [],
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
        "ingredient_risk_matrix": calculate_ingredient_risk_matrix(performances),
        "family_risk_matrix": calculate_family_risk_matrix(performances),
        "cooccurrence_affinity": calculate_cooccurrence_affinity(performances),
        "technique_evolution": calculate_technique_evolution(performances),
        "category_evolution": calculate_category_evolution(performances),
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
