"""Data loading and caching layer for the GBBO Streamlit dashboard."""

from __future__ import annotations

import logging
import os
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

    return {
        "era": era,
        "total_bakers": len(b),
        "total_episodes": len(e),
        "total_performances": len(p),
        "survival_curve": surv_df,
        "age_summary": age_summary,
        "gender_summary": gender_summary,
        "region_summary": region_summary,
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
    }
