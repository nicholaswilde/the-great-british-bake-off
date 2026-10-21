"""Data loading and caching layer for the GBBO Streamlit dashboard."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import streamlit as st

    cache_data = st.cache_data
except ImportError:

    def cache_data(func: Any) -> Any:
        """Fallback decorator when streamlit is not installed."""
        return func


def _get_data_dir() -> Path:
    """Resolve the directory containing processed tables."""
    env_dir = os.environ.get("GBBO_DATA_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    # 1. Project root / data/processed
    candidates = [
        Path("data/processed"),
        Path("../data/processed"),
        Path("../../data/processed"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed",
    ]
    for c in candidates:
        if c.exists() and (c / "seasons.parquet").exists():
            return c
        if c.exists() and (c / "seasons.csv").exists():
            return c

    return Path("data/processed")


@cache_data
def load_table(table_name: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    """Load a processed table from Parquet or CSV with caching."""
    dir_path = Path(data_dir) if data_dir else _get_data_dir()
    parquet_path = dir_path / f"{table_name}.parquet"
    csv_path = dir_path / f"{table_name}.csv"

    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            # Normalize array columns to comma-separated strings for Streamlit display
            for col in df.columns:
                if df[col].dtype == object and len(df) > 0:
                    first_val = (
                        df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    )
                    if isinstance(first_val, (list, tuple)) or (
                        hasattr(first_val, "__iter__")
                        and not isinstance(first_val, (str, bytes))
                    ):
                        df[col] = df[col].apply(
                            lambda x: (
                                ", ".join(str(i) for i in x)
                                if hasattr(x, "__iter__")
                                and not isinstance(x, (str, bytes))
                                else str(x)
                            )
                        )
            return df
        except Exception as err:
            logger.debug("Failed to read parquet table %s: %s", parquet_path, err)

    if csv_path.exists():
        try:
            return pd.read_csv(csv_path)
        except Exception as err:
            logger.debug("Failed to read csv table %s: %s", csv_path, err)

    return pd.DataFrame()


@cache_data
def load_all_datasets(data_dir: Path | str | None = None) -> dict[str, pd.DataFrame]:
    """Load core tables and supplementary datasets into memory."""
    tables = [
        "seasons",
        "bakers",
        "episodes",
        "performances",
        "bakes_nlp",
        "fandom_recipes",
        "fandom_lore",
        "reddit_discussions",
    ]
    return {tbl: load_table(tbl, data_dir=data_dir) for tbl in tables}


@cache_data
def load_empirical_bake_metrics(
    era: str = "ALL",
    data_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Compute cross-series empirical analytics and strategic visualizations data."""
    from gbbo_dataset.nlp_flavors import calculate_flavor_statistics

    raw_data = load_all_datasets(data_dir=data_dir)
    seasons = raw_data.get("seasons", pd.DataFrame())
    bakers = raw_data.get("bakers", pd.DataFrame())
    episodes = raw_data.get("episodes", pd.DataFrame())
    performances = raw_data.get("performances", pd.DataFrame())
    nlp_df = raw_data.get("bakes_nlp", pd.DataFrame())

    # Filter seasons by era
    s = seasons.copy()
    era_clean = str(era).strip().upper()
    if not s.empty and "network" in s.columns:
        if "BBC" in era_clean:
            s = s[s["network"].str.contains("BBC", case=False, na=False)]
        elif "CHANNEL" in era_clean or "C4" in era_clean:
            s = s[s["network"].str.contains("Channel 4", case=False, na=False)]

    valid_series = set(s["series_number"].unique()) if not s.empty else set()
    b = (
        bakers[bakers["series_number"].isin(valid_series)].copy()
        if not bakers.empty and "series_number" in bakers.columns and valid_series
        else bakers.copy()
    )
    e = (
        episodes[episodes["series_number"].isin(valid_series)].copy()
        if not episodes.empty and "series_number" in episodes.columns and valid_series
        else episodes.copy()
    )
    p = performances.copy()

    if not p.empty and not e.empty and "episode_id" in p.columns:
        p = p.merge(
            e[["episode_id", "series_number", "episode_number", "theme"]],
            on="episode_id",
            how="left",
            suffixes=("", "_ep"),
        )
        if "series_number" not in p.columns and "series_number_ep" in p.columns:
            p["series_number"] = p["series_number_ep"]
        if "series_number" in p.columns and valid_series:
            p = p[p["series_number"].isin(valid_series)]

    if (
        not b.empty
        and not p.empty
        and "name" not in p.columns
        and "baker_id" in p.columns
    ):
        p = p.merge(b[["baker_id", "name"]], on="baker_id", how="left")

    # 1. Survival Curve
    survival_data = []
    if not p.empty and "episode_number" in p.columns:
        for ep_num in range(1, 11):
            ep_p = p[p["episode_number"] == ep_num]
            active = ep_p["baker_id"].nunique()
            if active > 0:
                survival_data.append(
                    {"episode_number": ep_num, "active_bakers": active}
                )
        surv_df = pd.DataFrame(survival_data)
        if not surv_df.empty:
            base_count = surv_df.iloc[0]["active_bakers"]
            surv_df["survival_pct"] = (
                surv_df["active_bakers"] / max(base_count, 1) * 100
            ).round(1)
    else:
        surv_df = pd.DataFrame(
            columns=["episode_number", "active_bakers", "survival_pct"]
        )

    # 2. Age & Demographics
    age_summary = pd.DataFrame()
    gender_summary = pd.DataFrame()
    region_summary = pd.DataFrame()
    if not b.empty and "overall_placement" in b.columns:
        valid_b = b.dropna(subset=["overall_placement"]).copy()
        valid_b["is_winner"] = valid_b["overall_placement"] == 1
        valid_b["is_finalist"] = valid_b["overall_placement"] <= 3

        if "age" in valid_b.columns and valid_b["age"].notna().any():

            def _age_group(age: float) -> str:
                if pd.isna(age):
                    return "Unknown"
                if age < 25:
                    return "<25"
                if age <= 35:
                    return "25–35"
                if age <= 50:
                    return "36–50"
                return "51+"

            valid_b["age_group"] = valid_b["age"].apply(_age_group)
            age_summary = (
                valid_b[valid_b["age_group"] != "Unknown"]
                .groupby("age_group")
                .agg(
                    total_bakers=("baker_id", "count"),
                    winners=("is_winner", "sum"),
                    finalists=("is_finalist", "sum"),
                    avg_placement=("overall_placement", "mean"),
                )
                .reset_index()
            )
            age_summary["win_rate"] = (
                age_summary["winners"] / age_summary["total_bakers"] * 100
            ).round(1)
            age_summary["finalist_rate"] = (
                age_summary["finalists"] / age_summary["total_bakers"] * 100
            ).round(1)
            age_summary["avg_placement"] = age_summary["avg_placement"].round(2)

        if "gender" in valid_b.columns and valid_b["gender"].notna().any():
            gender_summary = (
                valid_b.groupby("gender")
                .agg(
                    total_bakers=("baker_id", "count"),
                    winners=("is_winner", "sum"),
                    finalists=("is_finalist", "sum"),
                    avg_placement=("overall_placement", "mean"),
                )
                .reset_index()
            )
            gender_summary["win_rate"] = (
                gender_summary["winners"] / gender_summary["total_bakers"] * 100
            ).round(1)
            gender_summary["finalist_rate"] = (
                gender_summary["finalists"] / gender_summary["total_bakers"] * 100
            ).round(1)
            gender_summary["avg_placement"] = gender_summary["avg_placement"].round(2)

        if (
            "county_region" in valid_b.columns
            and valid_b["county_region"].notna().any()
        ):
            region_summary = (
                valid_b.groupby("county_region")
                .agg(
                    total_bakers=("baker_id", "count"),
                    winners=("is_winner", "sum"),
                    finalists=("is_finalist", "sum"),
                    avg_placement=("overall_placement", "mean"),
                )
                .reset_index()
                .sort_values(by="total_bakers", ascending=False)
            )
            region_summary["avg_placement"] = region_summary["avg_placement"].round(2)

    # 3. Star Baker Dynamics
    sb_summary = pd.DataFrame()
    sb_records = pd.DataFrame()
    week1_records: list[dict[str, Any]] = []
    repeat_rate = 0.0
    prior_did_well_rate = 0.0

    if not p.empty and not b.empty and "result" in p.columns:
        sb_counts = (
            p[p["result"] == "STAR_BAKER"]
            .groupby("baker_id")["performance_id"]
            .count()
            .rename("star_bakers")
        )
        hs_counts = (
            p[p["hollywood_handshake"] == True]
            .groupby("baker_id")["performance_id"]
            .count()
            .rename("handshakes")
            if "hollywood_handshake" in p.columns
            else pd.Series(dtype=int)
        )
        tech_means = (
            p.dropna(subset=["technical_rank"])
            .groupby("baker_id")["technical_rank"]
            .mean()
            .rename("avg_tech_rank")
            .round(2)
            if "technical_rank" in p.columns
            else pd.Series(dtype=float)
        )

        b_merged = (
            b.merge(sb_counts, on="baker_id", how="left")
            .merge(hs_counts, on="baker_id", how="left")
            .merge(tech_means, on="baker_id", how="left")
            .fillna({"star_bakers": 0, "handshakes": 0})
        )
        b_merged["star_bakers"] = b_merged["star_bakers"].astype(int)
        b_merged["handshakes"] = b_merged["handshakes"].astype(int)
        b_merged["is_winner"] = b_merged["overall_placement"] == 1
        b_merged["is_finalist"] = b_merged["overall_placement"] <= 3

        sb_summary = (
            b_merged.groupby("star_bakers")
            .agg(
                total_bakers=("baker_id", "count"),
                winners=("is_winner", "sum"),
                finalists=("is_finalist", "sum"),
                avg_placement=("overall_placement", "mean"),
            )
            .reset_index()
        )
        sb_summary["win_rate"] = (
            sb_summary["winners"] / sb_summary["total_bakers"] * 100
        ).round(1)
        sb_summary["finalist_rate"] = (
            sb_summary["finalists"] / sb_summary["total_bakers"] * 100
        ).round(1)
        sb_summary["avg_placement"] = sb_summary["avg_placement"].round(2)

        # Star Baker Hall of Fame
        cols_needed = [
            c
            for c in [
                "name",
                "series_number",
                "star_bakers",
                "handshakes",
                "avg_tech_rank",
                "overall_placement",
            ]
            if c in b_merged.columns
        ]
        sb_records = (
            b_merged[b_merged["star_bakers"] > 0][cols_needed].sort_values(
                by=["star_bakers", "overall_placement"], ascending=[False, True]
            )
            if "star_bakers" in b_merged.columns
            else pd.DataFrame()
        )

        # Episode 1 Star Bakers
        if "episode_number" in p.columns:
            ep1_p = p[(p["episode_number"] == 1) & (p["result"] == "STAR_BAKER")]
            if not ep1_p.empty:
                ep1_m = ep1_p.merge(b, on="baker_id", suffixes=("_perf", "_baker"))
                for _, r in ep1_m.iterrows():
                    placement = r.get("overall_placement")
                    tier = "Unknown"
                    if pd.notna(placement):
                        if placement == 1:
                            tier = "Winner"
                        elif placement <= 3:
                            tier = "Runner-Up / Finalist"
                        elif placement <= 7:
                            tier = "Mid-Pack (4th–7th)"
                        else:
                            tier = "Early Flame-Out (8th+)"
                    week1_records.append(
                        {
                            "series_number": int(
                                r.get("series_number_baker", r.get("series_number", 0))
                            ),
                            "baker_name": r.get("name_baker", r.get("name", "Unknown")),
                            "overall_placement": placement,
                            "outcome_tier": tier,
                        }
                    )

        # Momentum: Repeat rate & prior did_well
        if "episode_number" in p.columns and "baker_id" in p.columns:
            sorted_p = p.sort_values(by=["series_number", "baker_id", "episode_number"])
            sorted_p["prev_result"] = sorted_p.groupby(["series_number", "baker_id"])[
                "result"
            ].shift(1)
            sorted_p["prev_did_well"] = sorted_p.groupby(["series_number", "baker_id"])[
                "did_well"
            ].shift(1)

            sb_episodes = sorted_p[sorted_p["result"] == "STAR_BAKER"]
            if not sb_episodes.empty:
                repeat_rate = round(
                    (sb_episodes["prev_result"] == "STAR_BAKER").mean() * 100, 1
                )
                prior_did_well_rate = round(
                    (sb_episodes["prev_did_well"] == True).mean() * 100, 1
                )

    week1_df = pd.DataFrame(week1_records)

    # 4. Hollywood Handshakes
    hs_perfs = (
        p[p["hollywood_handshake"] == True].copy()
        if not p.empty and "hollywood_handshake" in p.columns
        else pd.DataFrame()
    )
    hs_total = len(hs_perfs)
    hs_to_sb = (
        (hs_perfs["result"] == "STAR_BAKER").mean() * 100
        if hs_total > 0 and "result" in hs_perfs.columns
        else 0.0
    )

    era_rows: list[dict[str, Any]] = []
    if not seasons.empty and not performances.empty and not episodes.empty:
        all_p = performances.merge(
            episodes[["episode_id", "series_number", "episode_number"]],
            on="episode_id",
            how="left",
        )
        all_p = all_p.merge(
            seasons[["series_number", "network"]], on="series_number", how="left"
        )
        if "network" in all_p.columns:
            all_p["era_label"] = all_p["network"].apply(
                lambda x: (
                    "BBC Era (S1–S7)" if "BBC" in str(x) else "Channel 4 Era (S8+)"
                )
            )
            for era_lbl, grp in all_p.groupby("era_label"):
                n_series = grp["series_number"].nunique()
                n_eps = grp["episode_id"].nunique()
                n_hs = (
                    (grp["hollywood_handshake"] == True).sum()
                    if "hollywood_handshake" in grp.columns
                    else 0
                )
                era_rows.append(
                    {
                        "era": era_lbl,
                        "series_count": n_series,
                        "episodes_count": n_eps,
                        "total_handshakes": int(n_hs),
                        "handshakes_per_series": round(n_hs / max(n_series, 1), 2),
                        "handshakes_per_episode": round(n_hs / max(n_eps, 1), 2),
                    }
                )
    era_hs_df = pd.DataFrame(era_rows)

    series_hs_df = pd.DataFrame()
    if (
        not p.empty
        and "series_number" in p.columns
        and "hollywood_handshake" in p.columns
    ):
        hs_by_series = (
            p[p["hollywood_handshake"] == True]
            .groupby("series_number")
            .size()
            .reset_index(name="handshakes")
        )
        if not s.empty and "series_number" in s.columns:
            cols_s = [c for c in ["series_number", "year", "network"] if c in s.columns]
            series_hs_df = (
                s[cols_s]
                .merge(hs_by_series, on="series_number", how="left")
                .fillna({"handshakes": 0})
            )
            series_hs_df["handshakes"] = series_hs_df["handshakes"].astype(int)
            if "network" in series_hs_df.columns:
                series_hs_df["era"] = series_hs_df["network"].apply(
                    lambda x: "BBC Era" if "BBC" in str(x) else "Channel 4 Era"
                )

    hs_log_df = pd.DataFrame()
    if not hs_perfs.empty:
        log_cols = [
            "series_number",
            "episode_number",
            "name",
            "signature_dish",
            "showstopper_dish",
            "result",
        ]
        present_cols = [c for c in log_cols if c in hs_perfs.columns]
        hs_log_df = hs_perfs[present_cols].copy()
        if "signature_dish" in hs_log_df.columns:
            hs_log_df["challenge_type"] = hs_log_df["signature_dish"].apply(
                lambda x: (
                    "Signature"
                    if pd.notna(x) and str(x).strip() != ""
                    else "Showstopper"
                )
            )
            hs_log_df["dish_name"] = hs_log_df.apply(
                lambda r: (
                    r["signature_dish"]
                    if pd.notna(r.get("signature_dish"))
                    and str(r.get("signature_dish")).strip() != ""
                    else r.get("showstopper_dish", "N/A")
                ),
                axis=1,
            )

    # 5. Technical Challenge Dynamics
    bottom2_hazard = 0.0
    other_hazard = 0.0
    rank1_sb = 0.0
    tech_tiers_df = pd.DataFrame()
    tech_cohorts_df = pd.DataFrame()

    tech_p = (
        p.dropna(subset=["technical_rank"]).copy()
        if not p.empty and "technical_rank" in p.columns
        else pd.DataFrame()
    )
    if not tech_p.empty and "episode_id" in tech_p.columns:
        max_t = tech_p.groupby("episode_id")["technical_rank"].max().rename("max_rank")
        tech_p = tech_p.merge(max_t, on="episode_id")
        tech_p["is_1st"] = tech_p["technical_rank"] == 1
        tech_p["is_top3"] = tech_p["technical_rank"] <= 3
        tech_p["is_last"] = tech_p["technical_rank"] == tech_p["max_rank"]
        tech_p["is_bottom2"] = tech_p["technical_rank"] >= (tech_p["max_rank"] - 1)
        tech_p["is_elim"] = tech_p["result"] == "ELIMINATED"
        tech_p["is_sb"] = tech_p["result"] == "STAR_BAKER"

        b2_grp = tech_p[tech_p["is_bottom2"]]
        o_grp = tech_p[~tech_p["is_bottom2"]]
        bottom2_hazard = (
            round(b2_grp["is_elim"].mean() * 100, 1) if not b2_grp.empty else 0.0
        )
        other_hazard = (
            round(o_grp["is_elim"].mean() * 100, 1) if not o_grp.empty else 0.0
        )
        rank1_sb = (
            round(tech_p[tech_p["is_1st"]]["is_sb"].mean() * 100, 1)
            if not tech_p.empty
            else 0.0
        )

        cohorts = [
            {
                "cohort": "1st Place",
                "elim_rate": round(tech_p[tech_p["is_1st"]]["is_elim"].mean() * 100, 1),
            },
            {
                "cohort": "Top 3",
                "elim_rate": round(
                    tech_p[tech_p["is_top3"]]["is_elim"].mean() * 100, 1
                ),
            },
            {
                "cohort": "Mid-Pack",
                "elim_rate": round(
                    tech_p[~tech_p["is_top3"] & ~tech_p["is_bottom2"]]["is_elim"].mean()
                    * 100,
                    1,
                ),
            },
            {"cohort": "Bottom 2", "elim_rate": bottom2_hazard},
            {
                "cohort": "Dead Last",
                "elim_rate": round(
                    tech_p[tech_p["is_last"]]["is_elim"].mean() * 100, 1
                ),
            },
        ]
        tech_cohorts_df = pd.DataFrame(cohorts)

        if (
            not b.empty
            and "baker_id" in tech_p.columns
            and "overall_placement" in b.columns
        ):
            tech_merged = tech_p.merge(
                b[["baker_id", "overall_placement"]], on="baker_id", how="left"
            )

            def _tier(plc: Any) -> str:
                if pd.isna(plc):
                    return "Unknown"
                if plc == 1:
                    return "1. Champion"
                if plc <= 3:
                    return "2. Finalist (2nd–3rd)"
                if plc <= 7:
                    return "3. Mid-Pack (4th–7th)"
                return "4. Early Eliminated (8th+)"

            tech_merged["tier"] = tech_merged["overall_placement"].apply(_tier)
            tech_merged["tech_pct"] = 1.0 - (tech_merged["technical_rank"] - 1) / (
                tech_merged["max_rank"] - 1
            ).clip(lower=1)
            tech_tiers_df = (
                tech_merged[tech_merged["tier"] != "Unknown"]
                .groupby("tier")["tech_pct"]
                .mean()
                .reset_index(name="avg_tech_percentile")
            )
            tech_tiers_df["avg_tech_percentile"] = (
                tech_tiers_df["avg_tech_percentile"] * 100
            ).round(1)

    # 6. Theme and Flavor Dynamics
    theme_hazards_df = pd.DataFrame()
    if not p.empty and "theme" in p.columns and "result" in p.columns:
        valid_themes = p.dropna(subset=["theme"]).copy()

        def _norm_theme(t: Any) -> str:
            val = str(t).strip().lower()
            if val.startswith("cake"):
                return "Cake"
            if val.startswith("biscuit"):
                return "Biscuits"
            if val.startswith("bread"):
                return "Bread"
            if val.startswith("dessert"):
                return "Desserts"
            if val.startswith("pastry"):
                return "Pastry"
            if "pâtisserie" in val or "patisserie" in val:
                return "Pâtisserie"
            return str(t).strip()

        valid_themes["norm_theme"] = valid_themes["theme"].apply(_norm_theme)
        theme_summary = (
            valid_themes.groupby("norm_theme")
            .agg(
                total_performances=("performance_id", "count"),
                eliminations=("result", lambda s: (s == "ELIMINATED").sum()),
                star_bakers=("result", lambda s: (s == "STAR_BAKER").sum()),
                handshakes=(
                    "hollywood_handshake",
                    lambda s: (
                        (s == True).sum()
                        if "hollywood_handshake" in valid_themes.columns
                        else 0
                    ),
                ),
            )
            .reset_index()
        )
        theme_summary["elimination_rate"] = (
            theme_summary["eliminations"] / theme_summary["total_performances"] * 100
        ).round(1)
        theme_hazards_df = theme_summary[
            theme_summary["total_performances"] >= 20
        ].sort_values(by="eliminations", ascending=False)

    flavor_bundle = calculate_flavor_statistics(nlp_df if not nlp_df.empty else p)
    social_bundle = compute_social_sentiment_metrics(raw_data=raw_data, era=era)
    occ_summary = compute_occupational_metrics(bakers=b, performances=p, era=era)
    time_pressure_bundle = compute_time_pressure_metrics(
        episodes=raw_data.get("episodes", pd.DataFrame()),
        performances=raw_data.get("performances", pd.DataFrame()),
        seasons=raw_data.get("seasons", pd.DataFrame()),
        era=era,
    )
    underdog_bundle = compute_underdog_and_upset_metrics(
        bakers=b,
        episodes=raw_data.get("episodes", pd.DataFrame()),
        performances=p,
        seasons=raw_data.get("seasons", pd.DataFrame()),
    )
    recipe_diff_bundle = compute_recipe_difficulty_and_sentiment_metrics(
        recipes=raw_data.get("fandom_recipes", pd.DataFrame()),
        lore=raw_data.get("fandom_lore", pd.DataFrame()),
        performances=p,
        bakes_nlp=nlp_df,
        episodes=raw_data.get("episodes", pd.DataFrame()),
    )

    return {
        "era": era,
        "total_bakers": len(b),
        "total_episodes": len(e),
        "total_performances": len(p),
        "survival_curve": surv_df,
        "age_summary": age_summary,
        "gender_summary": gender_summary,
        "region_summary": region_summary,
        "occupation_summary": occ_summary,
        "time_pressure": time_pressure_bundle,
        "underdog_metrics": underdog_bundle,
        "recipe_difficulty": recipe_diff_bundle,
        "star_baker_conversion": sb_summary,
        "star_baker_records": sb_records,
        "week1_star_bakers": week1_df,
        "star_baker_repeat_rate": repeat_rate,
        "star_baker_prior_did_well_rate": prior_did_well_rate,
        "handshake_total": hs_total,
        "handshake_to_sb_pct": round(hs_to_sb, 1),
        "era_handshake_rates": era_hs_df,
        "series_handshake_timeline": series_hs_df,
        "handshake_log": hs_log_df,
        "tech_bottom2_hazard_pct": bottom2_hazard,
        "tech_other_hazard_pct": other_hazard,
        "tech_rank1_to_sb_pct": rank1_sb,
        "tech_cohorts": tech_cohorts_df,
        "tech_tiers": tech_tiers_df,
        "theme_hazards": theme_hazards_df,
        "flavor_stats": flavor_bundle,
        "social_discussions": social_bundle["social_discussions"],
        "social_summary": social_bundle["social_summary"],
        "host_era_sentiment": social_bundle["host_era_sentiment"],
    }


def compute_social_sentiment_metrics(
    raw_data: dict[str, pd.DataFrame],
    era: str = "ALL",
) -> dict[str, Any]:
    """Compute Reddit reception, controversy index, and host/judge era metrics."""
    reddit = raw_data.get("reddit_discussions", pd.DataFrame())
    episodes = raw_data.get("episodes", pd.DataFrame())
    seasons = raw_data.get("seasons", pd.DataFrame())
    performances = raw_data.get("performances", pd.DataFrame())
    bakers = raw_data.get("bakers", pd.DataFrame())
    lore = raw_data.get("fandom_lore", pd.DataFrame())

    empty_res: dict[str, Any] = {
        "social_discussions": pd.DataFrame(),
        "social_summary": {
            "total_threads": 0,
            "total_comments": 0,
            "avg_upvote_ratio": 1.0,
            "peak_controversy": 0.0,
            "most_controversial_ep": "None",
            "upset_count": 0,
        },
        "host_era_sentiment": pd.DataFrame(),
    }

    if reddit is None or reddit.empty or not isinstance(reddit, pd.DataFrame):
        return empty_res

    m = reddit.copy()

    # Filter by era if applicable
    s = seasons.copy() if seasons is not None and not seasons.empty else pd.DataFrame()
    era_clean = str(era).strip().upper()
    if not s.empty and "network" in s.columns:
        if "BBC" in era_clean:
            s = s[s["network"].str.contains("BBC", case=False, na=False)]
        elif "CHANNEL" in era_clean or "C4" in era_clean:
            s = s[s["network"].str.contains("Channel 4", case=False, na=False)]

        valid_series = set(s["series_number"].unique())
        if valid_series and "series_number" in m.columns:
            m = m[m["series_number"].isin(valid_series)]

    if m.empty:
        return empty_res

    if not s.empty and "series_number" in s.columns:
        m = m.merge(
            s[["series_number", "hosts", "judges", "network", "year"]],
            on="series_number",
            how="left",
        )

    if (
        episodes is not None
        and not episodes.empty
        and {"series_number", "episode_number"}.issubset(episodes.columns)
    ):
        ep_cols = [
            c
            for c in ["series_number", "episode_number", "episode_id", "theme"]
            if c in episodes.columns
        ]
        m = m.merge(
            episodes[ep_cols], on=["series_number", "episode_number"], how="left"
        )

    if (
        performances is not None
        and not performances.empty
        and bakers is not None
        and not bakers.empty
        and "baker_id" in performances.columns
    ):
        perf_b = performances.merge(
            bakers[["baker_id", "name"]], on="baker_id", how="left"
        )
        if "result" in perf_b.columns and "episode_id" in perf_b.columns:
            sb_names = (
                perf_b[perf_b["result"] == "STAR_BAKER"]
                .groupby("episode_id")["name"]
                .apply(lambda x: ", ".join(x))
                .reset_index()
                .rename(columns={"name": "star_baker"})
            )
            elim_b = (
                perf_b[perf_b["result"].isin(["ELIMINATED", "WITHDREW"])]
                .groupby("episode_id")[["name", "baker_id"]]
                .agg({"name": lambda x: ", ".join(x), "baker_id": list})
                .reset_index()
                .rename(columns={"name": "eliminated_baker"})
            )
            m = m.merge(sb_names, on="episode_id", how="left")
            m = m.merge(elim_b, on="episode_id", how="left")

            def check_upset(row: Any) -> tuple[bool, str]:
                b_ids = row.get("baker_id")
                if not isinstance(b_ids, list) or not b_ids:
                    return False, "Normal elimination"
                ep_id = str(row.get("episode_id", ""))
                is_u = False
                reasons: list[str] = []
                for b_id in b_ids:
                    prior_p = perf_b[
                        (perf_b["baker_id"] == b_id) & (perf_b["episode_id"] < ep_id)
                    ]
                    p_sb = (prior_p["result"] == "STAR_BAKER").sum()
                    if p_sb > 0:
                        is_u = True
                        reasons.append(f"{p_sb} prior Star Baker(s)")
                    if "technical_rank" in prior_p.columns:
                        prior_tech = prior_p["technical_rank"].dropna()
                        if len(prior_tech) > 0 and prior_tech.mean() <= 2.5:
                            is_u = True
                            reasons.append(f"Avg Tech Rank {prior_tech.mean():.1f}")
                return is_u, "; ".join(reasons) if reasons else "Expected outcome"

            upsets = m.apply(check_upset, axis=1)
            m["is_upset"] = [u[0] for u in upsets]
            m["upset_reason"] = [u[1] for u in upsets]

    if "is_upset" not in m.columns:
        m["is_upset"] = False
        m["upset_reason"] = ""
    if "star_baker" not in m.columns:
        m["star_baker"] = ""
    if "eliminated_baker" not in m.columns:
        m["eliminated_baker"] = ""

    # Calculate Controversy Score
    def calc_controversy(row: Any) -> float:
        comments = row.get("num_comments", 0)
        ratio = row.get("upvote_ratio", 1.0)
        sent = str(row.get("sentiment_label", "")).lower()
        sent_mult = 1.6 if sent == "critical" else (1.25 if sent == "mixed" else 1.0)
        upset_mult = 1.3 if row.get("is_upset") else 1.0
        return round(
            comments * max(1.0 - ratio, 0.01) * 10.0 * sent_mult * upset_mult, 1
        )

    m["controversy_index"] = m.apply(calc_controversy, axis=1)

    if (
        lore is not None
        and not lore.empty
        and {"series_number", "episode_number"}.issubset(lore.columns)
    ):
        l_cols = [
            c
            for c in [
                "series_number",
                "episode_number",
                "notable_moments",
                "famous_quotes",
            ]
            if c in lore.columns
        ]
        m = m.merge(lore[l_cols], on=["series_number", "episode_number"], how="left")

    m["episode_code"] = m.apply(
        lambda r: f"S{int(r['series_number']):02d}E{int(r['episode_number']):02d}",
        axis=1,
    )

    # Host & era sentiment
    host_era_df = pd.DataFrame()
    if "hosts" in m.columns:

        def _clean_host(h: Any) -> str:
            h_str = str(h)
            if "Mel" in h_str:
                return "Mel Giedroyc & Sue Perkins"
            if "Sandi" in h_str:
                return "Noel Fielding & Sandi Toksvig"
            if "Lucas" in h_str:
                return "Noel Fielding & Matt Lucas"
            if "Alison" in h_str:
                return "Noel Fielding & Alison Hammond"
            return h_str

        m["host_duo"] = m["hosts"].apply(_clean_host)
        host_era_df = (
            m.groupby("host_duo")
            .agg(
                thread_count=("thread_id", "count"),
                avg_comments=("num_comments", "mean"),
                avg_upvote_ratio=("upvote_ratio", "mean"),
                mean_controversy=("controversy_index", "mean"),
                critical_count=(
                    "sentiment_label",
                    lambda s: (s.str.lower() == "critical").sum(),
                ),
            )
            .reset_index()
        )
        host_era_df["avg_comments"] = host_era_df["avg_comments"].round(1)
        host_era_df["avg_upvote_ratio"] = host_era_df["avg_upvote_ratio"].round(3)
        host_era_df["mean_controversy"] = host_era_df["mean_controversy"].round(1)

    most_controversial = (
        m.sort_values(by="controversy_index", ascending=False).iloc[0]
        if not m.empty
        else None
    )

    social_summary = {
        "total_threads": len(m),
        "total_comments": int(m["num_comments"].sum())
        if "num_comments" in m.columns
        else 0,
        "avg_upvote_ratio": float(m["upvote_ratio"].mean())
        if "upvote_ratio" in m.columns
        else 1.0,
        "peak_controversy": float(most_controversial["controversy_index"])
        if most_controversial is not None
        else 0.0,
        "most_controversial_ep": (
            f"{most_controversial['episode_code']} ({most_controversial.get('theme', 'Episode')})"
            if most_controversial is not None
            else "None"
        ),
        "upset_count": int(m["is_upset"].sum()) if "is_upset" in m.columns else 0,
    }

    return {
        "social_discussions": m,
        "social_summary": social_summary,
        "host_era_sentiment": host_era_df,
    }


OCCUPATION_CLUSTERS: dict[str, list[str]] = {
    "STEM & Engineering": [
        r"engineer",
        r"software",
        r"developer",
        r"scientist",
        r"research",
        r"chemist",
        r"physic",
        r"biolog",
        r"data",
        r"architect",
        r"technologist",
        r"technology",
        r"optometrist",
        r"programmer",
    ],
    "Healthcare & Medicine": [
        r"doctor",
        r"gp\b",
        r"nurse",
        r"midwife",
        r"vet",
        r"medic",
        r"radiograph",
        r"physio",
        r"paramedic",
        r"clinical",
        r"health",
        r"dental",
        r"dentist",
        r"pharmac",
        r"anaesthet",
        r"therapist",
        r"psycholog",
        r"palliative",
        r"nhs",
        r"hospital",
        r"retirement",
    ],
    "Education & Academia": [
        r"teacher",
        r"tutor",
        r"lecturer",
        r"professor",
        r"headteacher",
        r"teaching",
        r"school",
        r"academic",
        r"coach",
    ],
    "Finance, Law & Corporate": [
        r"accountant",
        r"finance",
        r"bank",
        r"lawyer",
        r"solicitor",
        r"consultant",
        r"manager",
        r"market",
        r"project manager",
        r"sales",
        r"analyst",
        r"debt",
        r"auditor",
        r"director",
        r"administrator",
        r"business",
        r"hr\b",
        r"executive",
        r"entrepreneur",
        r"buyer",
        r"broker",
        r"client",
        r"office",
        r"retail",
        r"cashier",
        r"shop",
        r"assistant",
        r"planner",
    ],
    "Creative, Arts & Media": [
        r"designer",
        r"photograph",
        r"artist",
        r"writer",
        r"author",
        r"illustrat",
        r"actor",
        r"theatre",
        r"music",
        r"fashion",
        r"producer",
        r"animat",
        r"graphic",
        r"sculpt",
        r"gallery",
        r"restorer",
    ],
    "Public Service & Trades": [
        r"builder",
        r"carpenter",
        r"mechanic",
        r"police",
        r"civil servant",
        r"gardener",
        r"landscape",
        r"driver",
        r"postal",
        r"courier",
        r"military",
        r"army",
        r"navy",
        r"raf\b",
        r"fire",
        r"chef",
        r"baker",
        r"hair",
        r"barber",
        r"security",
        r"council",
        r"prison",
        r"pastor",
        r"vicar",
        r"priest",
        r"officer",
        r"charity",
        r"fundrais",
        r"operative",
        r"horticultur",
        r"countryside",
        r"waiter",
        r"support worker",
        r"coordinator",
    ],
    "Students & Homemakers": [
        r"student",
        r"homemaker",
        r"retired",
        r"stay-at-home",
        r"mother",
        r"parent",
        r"unemployed",
        r"graduate",
        r"housewife",
        r"house husband",
        r"childminder",
        r"nanny",
        r"wife",
        r"women's institute",
    ],
}


def classify_occupation(occ: str | None) -> str:
    """Classify a baker's occupation into a standardized demographic archetype."""
    if not occ or pd.isna(occ):
        return "Other & Unclassified"
    text = str(occ).lower()
    for cat, patterns in OCCUPATION_CLUSTERS.items():
        if any(re.search(p, text) for p in patterns):
            return cat
    return "Other & Unclassified"


def compute_occupational_metrics(
    bakers: pd.DataFrame,
    performances: pd.DataFrame,
    era: str = "ALL",
) -> pd.DataFrame:
    """Compute empirical performance statistics aggregated by occupational archetype."""
    if bakers.empty or "occupation" not in bakers.columns:
        return pd.DataFrame()

    b_df = bakers.copy()
    b_df["cluster"] = b_df["occupation"].apply(classify_occupation)

    p_df = (
        performances.copy()
        if not performances.empty
        else pd.DataFrame(columns=["baker_id", "technical_rank", "result"])
    )

    merged = p_df.merge(
        b_df[["baker_id", "cluster", "overall_placement", "name"]],
        on="baker_id",
        how="left",
    )

    rows: list[dict[str, Any]] = []
    for cluster, grp in b_df.groupby("cluster"):
        c_perfs = (
            merged[merged["cluster"] == cluster] if not merged.empty else pd.DataFrame()
        )
        total_bakers = len(grp)
        champions = (
            int((grp["overall_placement"] == 1).sum())
            if "overall_placement" in grp.columns
            else 0
        )
        finalists = (
            int((grp["overall_placement"] <= 3).sum())
            if "overall_placement" in grp.columns
            else 0
        )
        win_rate = round(champions / total_bakers * 100, 1) if total_bakers > 0 else 0.0
        finalist_rate = (
            round(finalists / total_bakers * 100, 1) if total_bakers > 0 else 0.0
        )

        med_tech = 0.0
        mean_tech = 0.0
        if not c_perfs.empty and "technical_rank" in c_perfs.columns:
            valid_t = c_perfs["technical_rank"].dropna()
            if not valid_t.empty:
                med_tech = round(float(valid_t.median()), 1)
                mean_tech = round(float(valid_t.mean()), 2)

        avg_ep = 0.0
        if not c_perfs.empty and "episode_id" in c_perfs.columns:
            ep_counts = c_perfs.groupby("baker_id")["episode_id"].nunique()
            if not ep_counts.empty:
                avg_ep = round(float(ep_counts.mean()), 1)

        star_bakers = (
            int((c_perfs["result"] == "STAR_BAKER").sum())
            if not c_perfs.empty and "result" in c_perfs.columns
            else 0
        )
        handshakes = (
            int(c_perfs["hollywood_handshake"].sum())
            if not c_perfs.empty and "hollywood_handshake" in c_perfs.columns
            else 0
        )

        notable_names: list[str] = []
        if "overall_placement" in grp.columns and "name" in grp.columns:
            top_b = (
                grp.sort_values(by="overall_placement")
                .dropna(subset=["overall_placement"])
                .head(3)
            )
            notable_names = top_b["name"].tolist()

        rows.append(
            {
                "cluster": cluster,
                "total_bakers": total_bakers,
                "champions": champions,
                "win_rate": win_rate,
                "finalists": finalists,
                "finalist_rate": finalist_rate,
                "median_technical_rank": med_tech,
                "mean_technical_rank": mean_tech,
                "avg_episodes": avg_ep,
                "star_bakers": star_bakers,
                "handshakes": handshakes,
                "notable_bakers": (
                    ", ".join(notable_names) if notable_names else "N/A"
                ),
            }
        )

    if not rows:
        return pd.DataFrame()

    res_df = pd.DataFrame(rows).sort_values(
        by=["win_rate", "finalist_rate"], ascending=False
    )
    return res_df.reset_index(drop=True)


def compute_baker_skills(
    baker_id: str,
    performances: pd.DataFrame,
) -> dict[str, float]:
    """Calculate 5 normalized skill metrics (0-100) for a given baker."""
    default_skills = {
        "Technical Mastery": 50.0,
        "Star Baker Clout": 0.0,
        "Handshake Conversion": 0.0,
        "Risk Avoidance": 50.0,
        "Showstopper Consistency": 50.0,
    }
    if performances.empty or "baker_id" not in performances.columns:
        return default_skills

    bp = performances[performances["baker_id"] == baker_id]
    if bp.empty:
        return default_skills

    eps = len(bp)

    # 1. Technical Mastery (scale: rank 1 = 100, rank 6 = 50, rank 11 = 0)
    tech_ranks = (
        bp["technical_rank"].dropna()
        if "technical_rank" in bp.columns
        else pd.Series(dtype=float)
    )
    mean_tech = float(tech_ranks.mean()) if not tech_ranks.empty else 6.0
    tech_score = round(max(0.0, min(100.0, 110.0 - mean_tech * 10.0)), 1)

    # 2. Star Baker Clout (scaled such that 40% win rate = 100)
    sb_count = (
        int((bp["result"] == "STAR_BAKER").sum()) if "result" in bp.columns else 0
    )
    sb_score = round(min(100.0, (sb_count / eps) * 250.0), 1)

    # 3. Handshake Conversion (scale: 3+ handshakes = 100)
    hs_count = (
        int(bp["hollywood_handshake"].sum())
        if "hollywood_handshake" in bp.columns
        else 0
    )
    hs_score = round(min(100.0, hs_count * 35.0), 1)

    # 4. Risk Avoidance (percentage of episodes avoiding jeopardy or elimination)
    at_r = 0
    if "at_risk" in bp.columns and "result" in bp.columns:
        at_r = int(((bp["at_risk"] == True) | (bp["result"] == "ELIMINATED")).sum())
    elif "result" in bp.columns:
        at_r = int((bp["result"] == "ELIMINATED").sum())
    risk_score = round(max(0.0, 100.0 - (at_r / eps) * 100.0), 1)

    # 5. Showstopper Consistency (frequency of Star Baker, Did Well, or top honors)
    high_perf = 0
    if "result" in bp.columns and "did_well" in bp.columns:
        high_perf = int(
            ((bp["result"] == "STAR_BAKER") | (bp["did_well"] == True)).sum()
        )
    elif "result" in bp.columns:
        high_perf = int(
            (bp["result"].isin(["STAR_BAKER", "WINNER", "RUNNER_UP"])).sum()
        )
    showstopper_score = round(min(100.0, (high_perf / eps) * 125.0), 1)

    return {
        "Technical Mastery": tech_score,
        "Star Baker Clout": sb_score,
        "Handshake Conversion": hs_score,
        "Risk Avoidance": risk_score,
        "Showstopper Consistency": showstopper_score,
    }


def compute_champion_benchmark(
    bakers: pd.DataFrame,
    performances: pd.DataFrame,
) -> dict[str, float]:
    """Compute average 5-axis skill profile across all GBBO Series Champions."""
    default_benchmark = {
        "Technical Mastery": 74.2,
        "Star Baker Clout": 45.7,
        "Handshake Conversion": 28.1,
        "Risk Avoidance": 86.9,
        "Showstopper Consistency": 58.4,
    }
    if bakers.empty or performances.empty or "overall_placement" not in bakers.columns:
        return default_benchmark

    champs = bakers[bakers["overall_placement"] == 1]["baker_id"].dropna().tolist()
    if not champs:
        return default_benchmark

    profiles = [compute_baker_skills(cid, performances) for cid in champs]
    df = pd.DataFrame(profiles)
    return {col: round(float(df[col].mean()), 1) for col in df.columns}


def compute_time_pressure_metrics(
    episodes: pd.DataFrame,
    performances: pd.DataFrame,
    seasons: pd.DataFrame,
    era: str = "ALL",
) -> dict[str, Any]:
    """Analyze challenge time allotments, broadcasting era squeeze, and disaster rates."""
    empty_res: dict[str, Any] = {
        "series_time_trajectory": pd.DataFrame(),
        "era_time_comparison": pd.DataFrame(),
        "tech_time_brackets": pd.DataFrame(),
        "time_summary": {
            "bbc_avg_total": 0.0,
            "c4_avg_total": 0.0,
            "total_time_squeeze_min": 0.0,
            "shortest_technical": "N/A",
            "longest_technical": "N/A",
            "fast_bracket_hazard": 0.0,
        },
    }
    if episodes.empty or "signature_time_min" not in episodes.columns:
        return empty_res

    e = episodes.copy()
    s = seasons.copy() if seasons is not None and not seasons.empty else pd.DataFrame()
    p = (
        performances.copy()
        if performances is not None and not performances.empty
        else pd.DataFrame()
    )

    if not s.empty and "series_number" in s.columns:
        e = e.merge(s[["series_number", "network"]], on="series_number", how="left")
    else:
        e["network"] = "Unknown"

    e["broadcasting_era"] = e["network"].apply(
        lambda n: (
            "BBC Era"
            if "BBC" in str(n)
            else ("Channel 4 Era" if "Channel 4" in str(n) else "Unknown")
        )
    )

    e["total_bake_time_min"] = (
        e["signature_time_min"] + e["technical_time_min"] + e["showstopper_time_min"]
    )

    # Era comparison table across all valid episodes with total time
    era_comp = (
        e[
            e["broadcasting_era"].isin(["BBC Era", "Channel 4 Era"])
            & e["total_bake_time_min"].notna()
        ]
        .groupby("broadcasting_era")
        .agg(
            episodes=("episode_id", "count"),
            avg_signature=("signature_time_min", "mean"),
            avg_technical=("technical_time_min", "mean"),
            avg_showstopper=("showstopper_time_min", "mean"),
            avg_total=("total_bake_time_min", "mean"),
        )
        .reset_index()
        .round(1)
    )

    # Filter by era if requested
    era_clean = str(era).strip().upper()
    if "BBC" in era_clean:
        e_filtered = e[e["broadcasting_era"] == "BBC Era"]
    elif "CHANNEL" in era_clean or "C4" in era_clean:
        e_filtered = e[e["broadcasting_era"] == "Channel 4 Era"]
    else:
        e_filtered = e

    # Series longitudinal trajectory
    series_traj = (
        e_filtered.groupby(["series_number", "broadcasting_era"])
        .agg(
            signature_time=("signature_time_min", "mean"),
            technical_time=("technical_time_min", "mean"),
            showstopper_time=("showstopper_time_min", "mean"),
            total_time=("total_bake_time_min", "mean"),
            episodes=("episode_id", "count"),
        )
        .reset_index()
    )
    series_traj = series_traj.dropna(
        subset=["signature_time", "technical_time", "showstopper_time"]
    )
    series_traj = series_traj.round(1)

    # Technical brackets and hazard analysis
    brackets_df = pd.DataFrame()
    if not p.empty and "technical_rank" in p.columns:
        m = p.merge(e_filtered, on="episode_id", how="left")
        m_valid = m.dropna(subset=["technical_time_min", "technical_rank"]).copy()
        if not m_valid.empty:
            max_t = m_valid.groupby("episode_id")["technical_rank"].transform("max")
            m_valid["is_bottom2"] = m_valid["technical_rank"] >= (max_t - 1)
            m_valid["is_rank1"] = m_valid["technical_rank"] == 1
            m_valid["is_elim"] = m_valid["result"] == "ELIMINATED"
            m_valid["is_sb"] = m_valid["result"] == "STAR_BAKER"

            m_valid["bracket"] = pd.cut(
                m_valid["technical_time_min"],
                bins=[0, 90, 120, 150, 999],
                labels=[
                    "Ultra-Fast (≤90m)",
                    "Fast (91–120m)",
                    "Standard (121–150m)",
                    "Generous (>150m)",
                ],
            )

            bracket_rows = []
            for b_name, grp in m_valid.groupby("bracket", observed=False):
                eps_cnt = grp["episode_id"].nunique()
                mean_t = (
                    round(float(grp["technical_time_min"].mean()), 1)
                    if not grp.empty
                    else 0.0
                )
                b2_sub = grp[grp["is_bottom2"]]
                b2_hazard = (
                    round(float(b2_sub["is_elim"].mean() * 100), 1)
                    if not b2_sub.empty
                    else 0.0
                )
                r1_sub = grp[grp["is_rank1"]]
                r1_sb_conv = (
                    round(float(r1_sub["is_sb"].mean() * 100), 1)
                    if not r1_sub.empty
                    else 0.0
                )
                bracket_rows.append(
                    {
                        "bracket": str(b_name),
                        "episodes": eps_cnt,
                        "mean_time_min": mean_t,
                        "bottom2_hazard_pct": b2_hazard,
                        "rank1_to_sb_pct": r1_sb_conv,
                    }
                )
            brackets_df = pd.DataFrame(bracket_rows)

    shortest_tech = (
        e.dropna(subset=["technical_time_min"])
        .sort_values("technical_time_min")
        .iloc[0]
        if not e.dropna(subset=["technical_time_min"]).empty
        else None
    )
    longest_tech = (
        e.dropna(subset=["technical_time_min"])
        .sort_values("technical_time_min")
        .iloc[-1]
        if not e.dropna(subset=["technical_time_min"]).empty
        else None
    )

    bbc_total = (
        float(era_comp[era_comp["broadcasting_era"] == "BBC Era"]["avg_total"].iloc[0])
        if not era_comp.empty and "BBC Era" in era_comp["broadcasting_era"].values
        else 0.0
    )
    c4_total = (
        float(
            era_comp[era_comp["broadcasting_era"] == "Channel 4 Era"]["avg_total"].iloc[
                0
            ]
        )
        if not era_comp.empty and "Channel 4 Era" in era_comp["broadcasting_era"].values
        else 0.0
    )

    fast_hazard = (
        float(
            brackets_df[brackets_df["bracket"] == "Ultra-Fast (≤90m)"][
                "bottom2_hazard_pct"
            ].iloc[0]
        )
        if not brackets_df.empty
        and "Ultra-Fast (≤90m)" in brackets_df["bracket"].values
        else 0.0
    )

    time_summary = {
        "bbc_avg_total": bbc_total,
        "c4_avg_total": c4_total,
        "total_time_squeeze_min": round(bbc_total - c4_total, 1),
        "shortest_technical": (
            f"{shortest_tech['theme']} ({int(shortest_tech['technical_time_min'])}m, S{shortest_tech['series_number']:02d}E{shortest_tech['episode_number']:02d})"
            if shortest_tech is not None
            else "N/A"
        ),
        "longest_technical": (
            f"{longest_tech['theme']} ({int(longest_tech['technical_time_min'])}m, S{longest_tech['series_number']:02d}E{longest_tech['episode_number']:02d})"
            if longest_tech is not None
            else "N/A"
        ),
        "fast_bracket_hazard": fast_hazard,
    }

    return {
        "series_time_trajectory": series_traj,
        "era_time_comparison": era_comp,
        "tech_time_brackets": brackets_df,
        "time_summary": time_summary,
    }


def compute_underdog_and_upset_metrics(
    bakers: pd.DataFrame,
    episodes: pd.DataFrame,
    performances: pd.DataFrame,
    seasons: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Model non-linear momentum, zero-SB champions, and theme elimination hazard spikes."""
    empty_res: dict[str, Any] = {
        "cohort_trajectories": pd.DataFrame(),
        "multi_sb_losers": pd.DataFrame(),
        "theme_upset_rates": pd.DataFrame(),
        "iconic_underdog_comparisons": pd.DataFrame(),
        "underdog_summary": {
            "zero_sb_champion": "N/A",
            "multi_sb_curse_win_rate": 0.0,
            "top_upset_theme": "N/A",
            "total_upset_eliminations": 0,
        },
    }
    if (
        bakers.empty
        or performances.empty
        or episodes.empty
        or "baker_id" not in performances.columns
    ):
        return empty_res

    ep_cols = [
        c
        for c in ["series_number", "episode_number", "theme"]
        if c in episodes.columns and c not in performances.columns
    ]
    if ep_cols:
        m = performances.merge(
            episodes[["episode_id", *ep_cols]],
            on="episode_id",
            how="left",
        )
    else:
        m = performances.copy()

    b_cols = [
        c
        for c in ["name", "overall_placement"]
        if c in bakers.columns and c not in m.columns
    ]
    if b_cols:
        m = m.merge(
            bakers[["baker_id", *b_cols]],
            on="baker_id",
            how="left",
        )

    if (
        m.empty
        or "technical_rank" not in m.columns
        or "episode_number" not in m.columns
        or "overall_placement" not in m.columns
    ):
        return empty_res

    if "did_well" not in m.columns:
        m["did_well"] = False
    if "at_risk" not in m.columns:
        m["at_risk"] = False
    if "hollywood_handshake" not in m.columns:
        m["hollywood_handshake"] = 0

    max_t = m.groupby("episode_id")["technical_rank"].transform("max")
    m["is_bottom2"] = m["technical_rank"] >= (max_t - 1)
    m["is_last"] = m["technical_rank"] == max_t

    def calc_momentum(row: Any) -> float:
        score = 0.0
        r = row.get("result")
        if r == "STAR_BAKER":
            score += 3.0
        elif r == "WINNER":
            score += 4.0
        elif r == "RUNNER_UP":
            score += 2.0
        elif row.get("did_well") is True:
            score += 1.5
        elif r == "SAFE":
            score += 0.5
        elif r == "ELIMINATED":
            score -= 3.0

        if row.get("at_risk") is True:
            score -= 1.5
        if row.get("hollywood_handshake") == 1:
            score += 1.5

        tr = row.get("technical_rank")
        if pd.notna(tr):
            if tr == 1:
                score += 1.5
            elif tr <= 3:
                score += 0.5
            if row.get("is_bottom2"):
                score -= 1.0
            if row.get("is_last"):
                score -= 0.5
        return score

    m["ep_score"] = m.apply(calc_momentum, axis=1)
    m = m.sort_values(by=["baker_id", "episode_number"])
    m["cum_score"] = m.groupby("baker_id")["ep_score"].cumsum()

    # Cohort mapping
    def get_cohort(plc: Any) -> str:
        if pd.isna(plc):
            return "Unknown"
        if plc == 1:
            return "1. Champions"
        if plc <= 3:
            return "2. Finalists (2nd–3rd)"
        if plc <= 7:
            return "3. Mid-Pack (4th–7th)"
        return "4. Early Exits (8th+)"

    m["cohort"] = m["overall_placement"].apply(get_cohort)
    cohort_traj = (
        m[m["cohort"] != "Unknown"]
        .groupby(["cohort", "episode_number"])["cum_score"]
        .mean()
        .reset_index()
        .round(2)
    )

    # Multi-SB Losers
    sb_counts = (
        m[m["result"] == "STAR_BAKER"]
        .groupby(["series_number", "baker_id", "name", "overall_placement"])
        .size()
        .reset_index(name="star_bakers")
    )
    multi_sb_losers = (
        sb_counts[sb_counts["overall_placement"] > 1]
        .sort_values(by="star_bakers", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    # Theme upset casualties
    m["prior_sb"] = m.groupby("baker_id")["result"].transform(
        lambda s: (s == "STAR_BAKER").cumsum().shift(1, fill_value=0)
    )
    m["prior_did_well"] = m.groupby("baker_id")["did_well"].transform(
        lambda s: s.fillna(False).astype(bool).cumsum().shift(1, fill_value=0)
    )
    m["prior_hs"] = m.groupby("baker_id")["hollywood_handshake"].transform(
        lambda s: (s == 1).cumsum().shift(1, fill_value=0)
    )

    elims = m[m["result"] == "ELIMINATED"].copy()
    elims["is_upset"] = (
        (elims["prior_sb"] > 0)
        | (elims["prior_hs"] > 0)
        | (elims["prior_did_well"] >= 2)
    )

    def norm_theme(t: Any) -> str:
        if not t or pd.isna(t):
            return "Other"
        t_lower = str(t).lower()
        for cat in [
            "bread",
            "cake",
            "biscuit",
            "pastry",
            "dessert",
            "pâtisserie",
            "patisserie",
            "chocolate",
            "botanical",
            "caramel",
            "vegan",
            "pie",
            "pudding",
        ]:
            if cat in t_lower:
                return "Pâtisserie" if "patiss" in cat else cat.capitalize()
        return "Specialty / International"

    m["norm_theme"] = m["theme"].apply(norm_theme)
    elims["norm_theme"] = elims["theme"].apply(norm_theme)

    theme_stats = (
        m.groupby("norm_theme")
        .agg(
            total_performances=("performance_id", "count"),
            eliminations=("result", lambda s: (s == "ELIMINATED").sum()),
        )
        .reset_index()
    )

    upset_stats = (
        elims[elims["is_upset"]]
        .groupby("norm_theme")
        .size()
        .reset_index(name="upset_eliminations")
    )
    theme_stats = theme_stats.merge(upset_stats, on="norm_theme", how="left").fillna(
        {"upset_eliminations": 0}
    )
    theme_stats["elimination_rate"] = (
        theme_stats["eliminations"] / theme_stats["total_performances"] * 100
    ).round(1)
    theme_stats["upset_rate"] = (
        theme_stats["upset_eliminations"] / theme_stats["eliminations"] * 100
    ).round(1)
    min_bakes = 20 if len(m) >= 20 else 1
    theme_stats = (
        theme_stats[theme_stats["total_performances"] >= min_bakes]
        .sort_values(by=["upset_rate", "eliminations"], ascending=False)
        .reset_index(drop=True)
    )

    # Iconic Underdog Case Studies (David vs Steph S10 and Nancy vs Richard S05)
    case_studies: list[dict[str, Any]] = []
    cases = [
        ("s10_david", "David Atherton (S10 Winner, 0 SB)"),
        ("s10_steph", "Steph Blackwell (S10 Runner-up, 4 SB)"),
        ("s05_nancy", "Nancy Birtwhistle (S05 Winner, 1 SB)"),
        ("s05_richard", "Richard Burr (S05 Runner-up, 5 SB)"),
    ]
    for bid, label in cases:
        b_sub = m[m["baker_id"] == bid]
        for _, r in b_sub.iterrows():
            case_studies.append(
                {
                    "baker": label,
                    "series_number": int(r["series_number"]),
                    "episode_number": int(r["episode_number"]),
                    "theme": str(r.get("theme", "Episode")),
                    "cumulative_momentum": round(float(r["cum_score"]), 1),
                    "episode_score": round(float(r["ep_score"]), 1),
                    "result": str(r.get("result", "")),
                }
            )
    case_df = pd.DataFrame(case_studies)

    top_upset_row = theme_stats.iloc[0] if not theme_stats.empty else None
    underdog_summary = {
        "zero_sb_champion": "David Atherton (Series 10)",
        "multi_sb_curse_win_rate": 0.0,
        "top_upset_theme": (
            f"{top_upset_row['norm_theme']} ({top_upset_row['upset_rate']}% Upset Rate)"
            if top_upset_row is not None
            else "N/A"
        ),
        "total_upset_eliminations": int(elims["is_upset"].sum()),
    }

    return {
        "cohort_trajectories": cohort_traj,
        "multi_sb_losers": multi_sb_losers,
        "theme_upset_rates": theme_stats,
        "iconic_underdog_comparisons": case_df,
        "underdog_summary": underdog_summary,
    }


def compute_recipe_difficulty_and_sentiment_metrics(
    recipes: pd.DataFrame,
    lore: pd.DataFrame | None = None,
    performances: pd.DataFrame | None = None,
    bakes_nlp: pd.DataFrame | None = None,
    episodes: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Analyze recipe difficulty, judging sentiment polarity, and bake ambition outcomes."""
    empty_res: dict[str, Any] = {
        "difficulty_sentiment": pd.DataFrame(),
        "difficulty_tier_summary": pd.DataFrame(),
        "challenge_type_complexity": pd.DataFrame(),
        "ambition_outcomes": pd.DataFrame(),
        "recipe_summary": {
            "most_difficult_recipe": "N/A",
            "easiest_recipe": "N/A",
            "avg_sentiment_easy": 0.0,
            "avg_sentiment_extreme": 0.0,
            "high_ambition_star_baker_rate": 0.0,
            "high_ambition_elimination_rate": 0.0,
            "moderate_ambition_elimination_rate": 0.0,
        },
    }

    if recipes.empty or "difficulty" not in recipes.columns:
        return empty_res

    diff_map = {
        "Easy": 1,
        "Moderate": 2,
        "Hard": 3,
        "Very Hard": 4,
        "Extreme": 5,
    }

    pos_keywords = [
        "even rise",
        "light sponge",
        "golden crust",
        "soft crumb",
        "height",
        "clean snap",
        "immaculate",
        "glossy",
        "feather-light",
        "defies gravity",
        "pure",
        "handshake",
        "triumph",
        "star baker",
        "precision",
        "crunch",
        "character",
        "silky",
        "delicious",
        "perfection",
        "beautiful",
        "sublime",
        "stunning",
        "well baked",
        "light",
    ]

    neg_keywords = [
        "underproved",
        "overbaked",
        "soggy",
        "soggy bottom",
        "melted",
        "failed",
        "failure",
        "style over substance",
        "burnt",
        "clumsy",
        "raw",
        "dense",
        "curdled",
        "tough",
        "pale",
        "mess",
        "collapsed",
        "overworked",
        "bland",
        "rubbery",
        "flat",
    ]

    # Merge lore quotes if available
    r_df = recipes.copy()
    if (
        lore is not None
        and not lore.empty
        and "series_number" in lore.columns
        and "episode_number" in lore.columns
    ):
        l_cols = [
            c
            for c in ["series_number", "episode_number", "famous_quotes"]
            if c in lore.columns
        ]
        r_df = r_df.merge(
            lore[l_cols], on=["series_number", "episode_number"], how="left"
        )

    def parse_quotes(val: Any) -> list[str]:
        if not val or pd.isna(val):
            return []
        if isinstance(val, list):
            return [str(x) for x in val]
        import ast
        import contextlib

        with contextlib.suppress(ValueError, SyntaxError):
            res = ast.literal_eval(str(val))
            if isinstance(res, list):
                return [str(x) for x in res]
        return [str(val)]

    records: list[dict[str, Any]] = []
    for _, row in r_df.iterrows():
        notes = str(row.get("judging_notes", "")).strip()
        quotes = parse_quotes(row.get("famous_quotes"))
        critique = f"{notes} {' '.join(quotes)}".strip()
        c_lower = critique.lower()

        pos_hits = [k for k in pos_keywords if k in c_lower]
        neg_hits = [k for k in neg_keywords if k in c_lower]
        tot = len(pos_hits) + len(neg_hits)
        polarity = round((len(pos_hits) - len(neg_hits)) / tot, 2) if tot > 0 else 0.0
        label = (
            "Positive"
            if polarity > 0.15
            else ("Critical" if polarity < -0.15 else "Neutral")
        )

        diff_str = str(row.get("difficulty", "Moderate")).strip()
        diff_num = diff_map.get(diff_str, 2)

        records.append(
            {
                "recipe_id": str(row.get("recipe_id", "")),
                "series_number": int(row.get("series_number", 0)),
                "episode_number": int(row.get("episode_number", 0)),
                "challenge_type": str(row.get("challenge_type", "Technical")),
                "dish_name": str(row.get("dish_name", "Unknown")),
                "difficulty": diff_str,
                "difficulty_num": diff_num,
                "judging_notes": notes,
                "critique_text": critique,
                "sentiment_score": polarity,
                "sentiment_label": label,
                "positive_indicators": ", ".join(pos_hits) if pos_hits else "-",
                "critical_indicators": ", ".join(neg_hits) if neg_hits else "-",
                "recipe_url": str(row.get("recipe_url", "")),
            }
        )

    diff_sent_df = pd.DataFrame(records)

    # 1. Tier summary
    tier_summary = (
        diff_sent_df.groupby("difficulty")
        .agg(
            recipe_count=("recipe_id", "count"),
            avg_sentiment=("sentiment_score", "mean"),
            positive_count=("sentiment_label", lambda s: (s == "Positive").sum()),
            critical_count=("sentiment_label", lambda s: (s == "Critical").sum()),
        )
        .reset_index()
    )
    tier_summary["difficulty_num"] = (
        tier_summary["difficulty"].map(diff_map).fillna(2).astype(int)
    )
    tier_summary = tier_summary.sort_values(by="difficulty_num").reset_index(drop=True)
    tier_summary["avg_sentiment"] = tier_summary["avg_sentiment"].round(2)
    tier_summary["positive_share"] = (
        tier_summary["positive_count"] / tier_summary["recipe_count"] * 100
    ).round(1)
    tier_summary["critical_share"] = (
        tier_summary["critical_count"] / tier_summary["recipe_count"] * 100
    ).round(1)

    # 2. Challenge type complexity
    complexity_df = (
        diff_sent_df.groupby(["challenge_type", "difficulty"])
        .size()
        .reset_index(name="recipe_count")
    )
    complexity_df["difficulty_num"] = (
        complexity_df["difficulty"].map(diff_map).fillna(2).astype(int)
    )
    tot_recipes = len(diff_sent_df)
    complexity_df["share_pct"] = (
        complexity_df["recipe_count"] / max(tot_recipes, 1) * 100
    ).round(1)
    complexity_df = complexity_df.sort_values(
        by=["challenge_type", "difficulty_num"]
    ).reset_index(drop=True)

    # 3. Ambition vs Outcome
    technique_keywords = [
        "choux",
        "macaron",
        "mirror",
        "glaze",
        "sugar",
        "tempered",
        "chocolate",
        "croquembouche",
        "meringue",
        "puff",
        "laminated",
        "filo",
        "mousse",
        "entremet",
        "illusion",
        "caramel",
        "brioche",
        "sculpture",
        "tiered",
        "lattice",
        "praline",
        "ganache",
        "tuile",
        "fondant",
        "layered",
    ]

    ambition_outcomes = pd.DataFrame()
    if performances is not None and not performances.empty:
        p_df = performances.copy()
        if (
            bakes_nlp is not None
            and not bakes_nlp.empty
            and "performance_id" in bakes_nlp.columns
        ):
            cols = [
                c
                for c in ["performance_id", "all_flavors", "all_styles"]
                if c in bakes_nlp.columns
            ]
            p_df = p_df.merge(bakes_nlp[cols], on="performance_id", how="left")

        def calc_ambition(row: Any) -> int:
            score = 1
            dish_text = f"{row.get('signature_dish', '')} {row.get('showstopper_dish', '')}".lower()
            flavors = (
                str(row.get("all_flavors", "")).split(",")
                if pd.notna(row.get("all_flavors"))
                else []
            )
            flavors = [f.strip() for f in flavors if f.strip() and f.strip() != "nan"]
            score += min(len(flavors), 2)
            styles = (
                str(row.get("all_styles", "")).split(",")
                if pd.notna(row.get("all_styles"))
                else []
            )
            styles = [s.strip() for s in styles if s.strip() and s.strip() != "nan"]
            score += min(len(styles), 2)
            tech_hits = [k for k in technique_keywords if k in dish_text]
            score += min(len(tech_hits), 3)
            return score

        p_df["ambition_score"] = p_df.apply(calc_ambition, axis=1)

        def get_ambition_tier(s: int) -> str:
            if s <= 2:
                return "1. Low Ambition"
            elif s <= 4:
                return "2. Moderate Ambition"
            elif s <= 6:
                return "3. High Ambition"
            return "4. Extreme Ambition"

        p_df["ambition_tier"] = p_df["ambition_score"].apply(get_ambition_tier)

        amb_grouped = (
            p_df.groupby("ambition_tier")
            .agg(
                total_bakes=("performance_id", "count"),
                handshakes=(
                    "hollywood_handshake",
                    lambda s: (
                        (s == True).sum()
                        if "hollywood_handshake" in p_df.columns
                        else 0
                    ),
                ),
                star_bakers=(
                    "result",
                    lambda s: (
                        (s == "STAR_BAKER").sum() if "result" in p_df.columns else 0
                    ),
                ),
                eliminations=(
                    "result",
                    lambda s: (
                        (s == "ELIMINATED").sum() if "result" in p_df.columns else 0
                    ),
                ),
                at_risk=(
                    "at_risk",
                    lambda s: (s == True).sum() if "at_risk" in p_df.columns else 0,
                ),
                did_well=(
                    "did_well",
                    lambda s: (s == True).sum() if "did_well" in p_df.columns else 0,
                ),
            )
            .reset_index()
        )

        amb_grouped["handshake_rate"] = (
            amb_grouped["handshakes"] / amb_grouped["total_bakes"] * 100
        ).round(1)
        amb_grouped["star_baker_rate"] = (
            amb_grouped["star_bakers"] / amb_grouped["total_bakes"] * 100
        ).round(1)
        amb_grouped["elimination_rate"] = (
            amb_grouped["eliminations"] / amb_grouped["total_bakes"] * 100
        ).round(1)
        amb_grouped["at_risk_rate"] = (
            amb_grouped["at_risk"] / amb_grouped["total_bakes"] * 100
        ).round(1)
        amb_grouped["did_well_rate"] = (
            amb_grouped["did_well"] / amb_grouped["total_bakes"] * 100
        ).round(1)
        ambition_outcomes = amb_grouped

    easy_rows = diff_sent_df[diff_sent_df["difficulty"] == "Easy"]
    extreme_rows = diff_sent_df[diff_sent_df["difficulty"] == "Extreme"]
    most_diff = (
        extreme_rows.iloc[0]["dish_name"]
        if not extreme_rows.empty
        else (
            diff_sent_df.sort_values(by="difficulty_num", ascending=False).iloc[0][
                "dish_name"
            ]
            if not diff_sent_df.empty
            else "N/A"
        )
    )
    easiest = (
        easy_rows.iloc[0]["dish_name"]
        if not easy_rows.empty
        else (
            diff_sent_df.sort_values(by="difficulty_num").iloc[0]["dish_name"]
            if not diff_sent_df.empty
            else "N/A"
        )
    )

    recipe_summary = {
        "most_difficult_recipe": most_diff,
        "easiest_recipe": easiest,
        "avg_sentiment_easy": (
            round(float(easy_rows["sentiment_score"].mean()), 2)
            if not easy_rows.empty
            else 0.0
        ),
        "avg_sentiment_extreme": (
            round(float(extreme_rows["sentiment_score"].mean()), 2)
            if not extreme_rows.empty
            else 0.0
        ),
        "high_ambition_star_baker_rate": (
            float(
                ambition_outcomes[
                    ambition_outcomes["ambition_tier"].str.contains("Extreme")
                ]["star_baker_rate"].iloc[0]
            )
            if not ambition_outcomes.empty
            and any("Extreme" in str(x) for x in ambition_outcomes["ambition_tier"])
            else 0.0
        ),
        "high_ambition_elimination_rate": (
            float(
                ambition_outcomes[
                    ambition_outcomes["ambition_tier"].str.contains("Extreme")
                ]["elimination_rate"].iloc[0]
            )
            if not ambition_outcomes.empty
            and any("Extreme" in str(x) for x in ambition_outcomes["ambition_tier"])
            else 0.0
        ),
        "moderate_ambition_elimination_rate": (
            float(
                ambition_outcomes[
                    ambition_outcomes["ambition_tier"].str.contains("Moderate")
                ]["elimination_rate"].iloc[0]
            )
            if not ambition_outcomes.empty
            and any("Moderate" in str(x) for x in ambition_outcomes["ambition_tier"])
            else 0.0
        ),
    }

    return {
        "difficulty_sentiment": diff_sent_df,
        "difficulty_tier_summary": tier_summary,
        "challenge_type_complexity": complexity_df,
        "ambition_outcomes": ambition_outcomes,
        "recipe_summary": recipe_summary,
    }
