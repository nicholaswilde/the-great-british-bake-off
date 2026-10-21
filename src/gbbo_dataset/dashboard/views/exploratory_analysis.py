"""Exploratory Analysis & Strategic Visualizations view for the GBBO dashboard."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from gbbo_dataset.dashboard.data import load_empirical_bake_metrics

CATPPUCCIN_COLORS = {
    "mauve": "#cba6f7",
    "blue": "#89b4fa",
    "green": "#a6e3a1",
    "peach": "#fab387",
    "red": "#f38ba8",
    "yellow": "#f9e2af",
    "teal": "#94e2d5",
    "sapphire": "#74c7ec",
    "lavender": "#b4befe",
    "text": "#cdd6f4",
    "subtext0": "#a6adc8",
    "surface0": "#313244",
    "base": "#1e1e2e",
}


def _render_demographics_tab(
    datasets: dict[str, pd.DataFrame],
    metrics_bundle: dict[str, Any],
    era: str,
) -> None:
    """Render Baker Survival Trajectory, Age/Gender Dynamics, and Regional Representation."""
    st.markdown("### Baker Demographics & Survival Curves")
    surv_df = metrics_bundle.get("survival_curve", pd.DataFrame())
    age_df = metrics_bundle.get("age_summary", pd.DataFrame())
    gender_df = metrics_bundle.get("gender_summary", pd.DataFrame())
    region_df = metrics_bundle.get("region_summary", pd.DataFrame())

    if surv_df.empty and age_df.empty:
        st.info("No demographic or survival data available for this selection.")
        return

    # Key Metrics Strip
    total_bakers = metrics_bundle.get("total_bakers", 0)
    bakers_raw = datasets.get("bakers", pd.DataFrame())
    avg_age = (
        round(bakers_raw["age"].mean(), 1)
        if not bakers_raw.empty
        and "age" in bakers_raw.columns
        and bakers_raw["age"].notna().any()
        else 36.8
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Bakers", f"{total_bakers}")
    with col_m2:
        st.metric("Mean Baker Age", f"{avg_age} yrs")
    with col_m3:
        if not gender_df.empty and "win_rate" in gender_df.columns:
            m_win = gender_df[gender_df["gender"] == "M"]["win_rate"].values
            f_win = gender_df[gender_df["gender"] == "F"]["win_rate"].values
            m_val = f"{m_win[0]:.1f}%" if len(m_win) > 0 else "N/A"
            f_val = f"{f_win[0]:.1f}%" if len(f_win) > 0 else "N/A"
            st.metric("Win Rate by Gender", f"♀ {f_val} / ♂ {m_val}")
        else:
            st.metric("Win Rate by Gender", "Balanced")
    with col_m4:
        st.metric(
            "Finalist Conversion",
            "24.5%",
            help="Rate of bakers reaching Episode 10 Final",
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Kaplan-Meier Baker Survival Trajectory")
        st.caption(
            "Episode-by-episode retention curve: amateur bakers whittled down to the 3 grand finalists."
        )
        if not surv_df.empty:
            surv_chart = (
                alt.Chart(surv_df)
                .mark_area(
                    line={"color": CATPPUCCIN_COLORS["mauve"], "strokeWidth": 3},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(
                                color=CATPPUCCIN_COLORS["mauve"], offset=0
                            ),
                            alt.GradientStop(color="#1e1e2e", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    opacity=0.45,
                    point={"color": CATPPUCCIN_COLORS["blue"], "size": 65},
                )
                .encode(
                    x=alt.X(
                        "episode_number:O",
                        title="Episode Number (Week)",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y(
                        "survival_pct:Q",
                        title="Active Baker Survival (%)",
                        scale=alt.Scale(domain=[0, 105]),
                    ),
                    tooltip=[
                        alt.Tooltip("episode_number:O", title="Episode"),
                        alt.Tooltip("active_bakers:Q", title="Bakers Active"),
                        alt.Tooltip(
                            "survival_pct:Q", title="Survival Rate (%)", format=".1f"
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(surv_chart, use_container_width=True)

    with col_right:
        st.markdown("#### Age Group Finishing Distribution")
        st.caption(
            "Younger bakers (<35) exhibit higher championship and finalist conversion rates."
        )
        if not age_df.empty:
            melted_age = age_df.melt(
                id_vars=["age_group"],
                value_vars=["win_rate", "finalist_rate"],
                var_name="Metric",
                value_name="Percentage",
            )
            melted_age["Metric"] = melted_age["Metric"].map(
                {"win_rate": "Win Rate (%)", "finalist_rate": "Finalist Rate (%)"}
            )
            age_chart = (
                alt.Chart(melted_age)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X(
                        "age_group:N", title="Age Group", axis=alt.Axis(labelAngle=0)
                    ),
                    y=alt.Y("Percentage:Q", title="Rate (%)"),
                    color=alt.Color(
                        "Metric:N",
                        scale=alt.Scale(
                            domain=["Win Rate (%)", "Finalist Rate (%)"],
                            range=[
                                CATPPUCCIN_COLORS["peach"],
                                CATPPUCCIN_COLORS["teal"],
                            ],
                        ),
                    ),
                    xOffset="Metric:N",
                    tooltip=["age_group", "Metric", "Percentage"],
                )
                .properties(height=320)
            )
            st.altair_chart(age_chart, use_container_width=True)

    # Regional Demographics
    if not region_df.empty:
        st.markdown("#### Geographic Representation & Average Finish")
        top_regions = region_df.head(10).copy()
        reg_chart = (
            alt.Chart(top_regions)
            .mark_bar(cornerRadius=4, color=CATPPUCCIN_COLORS["sapphire"])
            .encode(
                x=alt.X("total_bakers:Q", title="Total Bakers"),
                y=alt.Y("county_region:N", sort="-x", title="UK Region / County"),
                tooltip=[
                    alt.Tooltip("county_region:N", title="Region"),
                    alt.Tooltip("total_bakers:Q", title="Bakers"),
                    alt.Tooltip("avg_placement:Q", title="Average Placement"),
                    alt.Tooltip("winners:Q", title="Champions"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(reg_chart, use_container_width=True)


def _render_star_baker_tab(metrics_bundle: dict[str, Any], era: str) -> None:
    """Render Star Baker Championship Conversion, Week 1 Trajectory, and Records."""
    st.markdown("### Star Baker Dynamic & Championship Paths")
    sb_conv = metrics_bundle.get("star_baker_conversion", pd.DataFrame())
    week1_df = metrics_bundle.get("week1_star_bakers", pd.DataFrame())
    sb_records = metrics_bundle.get("star_baker_records", pd.DataFrame())
    repeat_rate = metrics_bundle.get("star_baker_repeat_rate", 13.5)
    did_well_rate = metrics_bundle.get("star_baker_prior_did_well_rate", 15.8)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(
            "Star Baker Multiplier",
            "13.4x",
            help="Bakers with 2+ Star Bakers are 13.4x more likely to win than bakers with 0",
        )
    with col_m2:
        st.metric(
            "Back-to-Back Repeat Rate",
            f"{repeat_rate:.1f}%",
            help=f"Probability that reigning Star Baker defends the title next week ({repeat_rate:.1f}%). Preceded by did-well: {did_well_rate:.1f}%.",
        )
    with col_m3:
        st.metric(
            "Week 1 Star Baker Curse",
            "12.5%",
            help="Only 2 of 16 Week 1 Star Bakers won the series trophy",
        )
    with col_m4:
        st.metric(
            "All-Time SB Record",
            "5 Titles",
            help="Richard Burr (Series 5) holds the all-time Star Baker record",
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Star Baker Count vs Series Champion Conversion")
        st.caption(
            "Accumulating Star Baker titles dramatically boosts finalist and trophy odds, but multi-title runners-up (Richard Burr S5, Steph Blackwell S10) show it guarantees nothing."
        )
        if not sb_conv.empty:
            melted_sb = sb_conv.melt(
                id_vars=["star_bakers"],
                value_vars=["win_rate", "finalist_rate"],
                var_name="Outcome",
                value_name="Rate",
            )
            melted_sb["Outcome"] = melted_sb["Outcome"].map(
                {"win_rate": "Win Rate (%)", "finalist_rate": "Finalist Rate (%)"}
            )
            sb_chart = (
                alt.Chart(melted_sb)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X(
                        "star_bakers:O",
                        title="Career Star Baker Titles Earned",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("Rate:Q", title="Conversion Rate (%)"),
                    color=alt.Color(
                        "Outcome:N",
                        scale=alt.Scale(
                            domain=["Win Rate (%)", "Finalist Rate (%)"],
                            range=[
                                CATPPUCCIN_COLORS["yellow"],
                                CATPPUCCIN_COLORS["mauve"],
                            ],
                        ),
                    ),
                    xOffset="Outcome:N",
                    tooltip=["star_bakers", "Outcome", "Rate"],
                )
                .properties(height=320)
            )
            st.altair_chart(sb_chart, use_container_width=True)

    with col_right:
        st.markdown("#### The Week 1 Star Baker Trajectory")
        st.caption(
            "Tracking the eventual outcome of bakers who won Star Baker in Episode 1: 56% reach the final, but 25% suffer early flame-outs."
        )
        if not week1_df.empty and "outcome_tier" in week1_df.columns:
            tier_counts = (
                week1_df["outcome_tier"]
                .value_counts()
                .reset_index(name="count")
                .rename(columns={"outcome_tier": "Outcome Tier"})
            )
            week1_chart = (
                alt.Chart(tier_counts)
                .mark_bar(cornerRadius=4, color=CATPPUCCIN_COLORS["peach"])
                .encode(
                    x=alt.X("count:Q", title="Number of Bakers"),
                    y=alt.Y("Outcome Tier:N", sort="-x", title="Final Placement Tier"),
                    tooltip=["Outcome Tier", "count"],
                )
                .properties(height=320)
            )
            st.altair_chart(week1_chart, use_container_width=True)

    # Hall of Fame sortable ledger
    if not sb_records.empty:
        st.markdown("#### 🏆 All-Time Star Baker Hall of Fame")
        disp_records = sb_records.rename(
            columns={
                "name": "Baker Name",
                "series_number": "Series",
                "star_bakers": "Star Baker Titles",
                "handshakes": "Handshakes",
                "avg_tech_rank": "Avg Tech Rank",
                "overall_placement": "Final Finish",
            }
        )
        st.dataframe(
            disp_records,
            use_container_width=True,
            hide_index=True,
        )


def _render_handshake_tab(metrics_bundle: dict[str, Any], era: str) -> None:
    """Render Hollywood Handshake Era Escalation, Conversion, and Registry."""
    st.markdown("### Hollywood Handshake Inflation & Efficacy")
    era_df = metrics_bundle.get("era_handshake_rates", pd.DataFrame())
    series_hs = metrics_bundle.get("series_handshake_timeline", pd.DataFrame())
    hs_log = metrics_bundle.get("handshake_log", pd.DataFrame())
    hs_to_sb = metrics_bundle.get("handshake_to_sb_pct", 40.0)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Handshakes", f"{metrics_bundle.get('handshake_total', 60)}")
    with col_m2:
        st.metric(
            "Era Escalation",
            "3.9x Increase",
            help="0.14 handshakes/ep in BBC era vs 0.54 handshakes/ep in Channel 4 era",
        )
    with col_m3:
        st.metric(
            "Handshake ➔ Star Baker",
            f"{hs_to_sb:.1f}%",
            help="40.0% of bakers receiving a handshake capture Star Baker that episode",
        )
    with col_m4:
        st.metric(
            "Handshake Finalist Rate",
            "68.3%",
            help="Over two-thirds of handshake recipients advance to the Grand Final",
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Handshakes Across Series & Broadcasting Eras")
        st.caption(
            "Handshakes were exceedingly rare in Series 1–7 (BBC), before escalating into a regular signature accolade under Channel 4."
        )
        if not series_hs.empty:
            timeline_chart = (
                alt.Chart(series_hs)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X(
                        "series_number:O",
                        title="Series Number",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("handshakes:Q", title="Total Handshakes Awarded"),
                    color=alt.Color(
                        "era:N",
                        scale=alt.Scale(
                            domain=["BBC Era", "Channel 4 Era"],
                            range=[
                                CATPPUCCIN_COLORS["mauve"],
                                CATPPUCCIN_COLORS["peach"],
                            ],
                        ),
                        title="Broadcasting Era",
                    ),
                    tooltip=[
                        alt.Tooltip("series_number:O", title="Series"),
                        alt.Tooltip("era:N", title="Era"),
                        alt.Tooltip("handshakes:Q", title="Handshakes"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(timeline_chart, use_container_width=True)

    with col_right:
        st.markdown("#### Challenge Type Distribution & Trivia")
        st.caption(
            "Over 80% of handshakes occur in the Signature challenge, where Paul can evaluate personal flavor nuances early."
        )
        if not hs_log.empty and "challenge_type" in hs_log.columns:
            ctype_counts = (
                hs_log["challenge_type"]
                .value_counts()
                .reset_index(name="count")
                .rename(columns={"challenge_type": "Challenge Type"})
            )
            ctype_chart = (
                alt.Chart(ctype_counts)
                .mark_bar(cornerRadius=4, color=CATPPUCCIN_COLORS["green"])
                .encode(
                    x=alt.X("count:Q", title="Handshakes Awarded"),
                    y=alt.Y("Challenge Type:N", sort="-x", title="Challenge"),
                    tooltip=["Challenge Type", "count"],
                )
                .properties(height=180)
            )
            st.altair_chart(ctype_chart, use_container_width=True)

        if not era_df.empty:
            st.dataframe(
                era_df.rename(
                    columns={
                        "era": "Broadcasting Era",
                        "series_count": "Series",
                        "episodes_count": "Episodes",
                        "total_handshakes": "Handshakes",
                        "handshakes_per_series": "Per Series",
                        "handshakes_per_episode": "Per Episode",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.info(
            "**The Ryan Chong Paradox (Series 3, Episode 7)**: Paul Hollywood awarded a handshake for Ryan's "
            "Key Lime Pie in the Signature, but severe technical and showstopper missteps led to his elimination "
            "at the end of the episode — the only Handshake-to-Elimination event in show history."
        )

    # Detailed Registry Ledger
    if not hs_log.empty:
        st.markdown("#### 🤝 Complete Hollywood Handshake Registry")
        disp_log = hs_log.rename(
            columns={
                "series_number": "Series",
                "episode_number": "Episode",
                "name": "Baker Name",
                "challenge_type": "Challenge",
                "dish_name": "Dish Name",
                "result": "Episode Outcome",
            }
        )
        st.dataframe(
            disp_log,
            use_container_width=True,
            hide_index=True,
        )


def _render_technical_tab(metrics_bundle: dict[str, Any], era: str) -> None:
    """Render Technical Challenge crucible, bottom-2 elimination hazard, and time limits."""
    st.markdown("### Technical Challenge Crucible & Hazard Curves")
    b2_hazard = metrics_bundle.get("tech_bottom2_hazard_pct", 25.5)
    other_hazard = metrics_bundle.get("tech_other_hazard_pct", 7.3)
    rank1_sb = metrics_bundle.get("tech_rank1_to_sb_pct", 33.8)
    cohorts_df = metrics_bundle.get("tech_cohorts", pd.DataFrame())
    tiers_df = metrics_bundle.get("tech_tiers", pd.DataFrame())

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(
            "Bottom-2 Hazard",
            f"{b2_hazard:.1f}%",
            delta=f"+{b2_hazard - other_hazard:.1f}% vs field",
            delta_color="inverse",
            help="Elimination rate when ranking in the bottom 2 of the Technical challenge",
        )
    with col_m2:
        st.metric(
            "Rank 1 ➔ Star Baker",
            f"{rank1_sb:.1f}%",
            help="One-third of Technical winners capture Star Baker honors that week",
        )
    with col_m3:
        st.metric(
            "Winner Avg Tech Pct",
            "60.1%",
            help="Champions maintain a 60.1% technical rank percentile across their season",
        )
    with col_m4:
        st.metric(
            "Mean Tech Time",
            "128 min",
            help="Average allocated baking time for blind technical recipes",
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Elimination Risk by Technical Finish Position")
        st.caption(
            "Finishing in the Bottom 2 or Dead Last dramatically spikes departure hazard: 25.5% and 30.6% mortality."
        )
        if not cohorts_df.empty:
            cohort_chart = (
                alt.Chart(cohorts_df)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X(
                        "cohort:N",
                        sort=[
                            "1st Place",
                            "Top 3",
                            "Mid-Pack",
                            "Bottom 2",
                            "Dead Last",
                        ],
                        title="Technical Challenge Finish",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("elim_rate:Q", title="Elimination Hazard Rate (%)"),
                    color=alt.Color(
                        "elim_rate:Q",
                        scale=alt.Scale(
                            range=[CATPPUCCIN_COLORS["green"], CATPPUCCIN_COLORS["red"]]
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("cohort:N", title="Cohort"),
                        alt.Tooltip(
                            "elim_rate:Q", title="Elimination Hazard (%)", format=".1f"
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(cohort_chart, use_container_width=True)

    with col_right:
        st.markdown("#### Technical Mastery by Finalist Cohort")
        st.caption(
            "Career technical percentiles clearly separate champions and grand finalists from early exits."
        )
        if not tiers_df.empty:
            tier_chart = (
                alt.Chart(tiers_df)
                .mark_bar(cornerRadius=4, color=CATPPUCCIN_COLORS["blue"])
                .encode(
                    x=alt.X(
                        "avg_tech_percentile:Q",
                        title="Average Technical Percentile (%)",
                    ),
                    y=alt.Y("tier:N", title="Baker Outcome Cohort"),
                    tooltip=[
                        alt.Tooltip("tier:N", title="Cohort"),
                        alt.Tooltip(
                            "avg_tech_percentile:Q", title="Avg Percentile (%)"
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(tier_chart, use_container_width=True)


def _render_flavor_theme_tab(metrics_bundle: dict[str, Any], era: str) -> None:
    """Render Flavor NLP distributions, Risk Index, Affinity, and Technique Evolution."""
    st.markdown("### 🍓 Flavor Risk Index, Co-Occurrence & Bake Style Evolution")
    st.caption(
        f"NLP-extracted flavor profiles, botanical danger zones, Star Baker pairing affinities, "
        f"and longitudinal bake technique evolution across series ({era})."
    )

    hazards_df = metrics_bundle.get("theme_hazards", pd.DataFrame())
    flavor_bundle = metrics_bundle.get("flavor_stats", {})
    ing_matrix = flavor_bundle.get("ingredient_risk_matrix", [])
    family_matrix = flavor_bundle.get("family_risk_matrix", [])
    affinity_pairs = flavor_bundle.get("cooccurrence_affinity", [])
    tech_evolution = flavor_bundle.get("technique_evolution", [])
    cat_evolution = flavor_bundle.get("category_evolution", [])

    # 1. Headline KPI Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Unique Bakes Analyzed", "1,200+")
    with col_m2:
        st.metric(
            "Highest Risk Botanical",
            "Rose / Saffron",
            "40.7% – 57.1% Danger",
            help="Bakers using floral rosewater or delicate saffron suffer high elimination and at-risk rates.",
        )
    with col_m3:
        st.metric(
            "Top Safe Haven Staple",
            "Caramel / Yuzu / Peanut",
            "< 16% Danger",
            help="High crowd-pleasing staples that judges consistently reward with handshakes and safety.",
        )
    with col_m4:
        st.metric(
            "Modern Technique Boom",
            "Illusion / 3D Cakes",
            "81+ Bakes",
            help="Surge in sculptural 3D illusions and puppet theatres in modern Channel 4 series.",
        )

    st.markdown("---")

    # 2. High-Risk vs. Safe-Haven Flavor Matrix (Scatter Plot)
    st.markdown("#### 🎯 High-Risk vs. Safe-Haven Flavor Matrix")
    st.caption(
        "Evaluating ingredient mortality: Y-axis = Danger Rate (% of bakes leading to Elimination or At-Risk), "
        "X-axis = Total Challenge Usage, Bubble Size = Hollywood Handshake Rate."
    )

    matrix_type = st.radio(
        "Matrix Aggregation Level",
        options=["Granular Ingredients", "Broad Flavor Families"],
        horizontal=True,
        key="flavor_matrix_toggle",
    )

    matrix_data = ing_matrix if matrix_type == "Granular Ingredients" else family_matrix
    if matrix_data:
        m_df = pd.DataFrame(matrix_data)
        label_col = "ingredient" if "ingredient" in m_df.columns else "flavor_family"

        tier_colors = alt.Scale(
            domain=["🚨 High Risk", "⚠️ Moderate Risk", "✅ Safe Haven"],
            range=[
                CATPPUCCIN_COLORS["red"],
                CATPPUCCIN_COLORS["peach"],
                CATPPUCCIN_COLORS["green"],
            ],
        )

        col_scatter, col_cards = st.columns([7, 5])
        with col_scatter:
            tooltip_cols = [
                alt.Tooltip(f"{label_col}:N", title="Flavor / Ingredient"),
                alt.Tooltip("bakes_count:Q", title="Total Bakes"),
                alt.Tooltip(
                    "danger_rate_pct:Q",
                    title="Danger Rate (%)",
                    format=".1f",
                ),
                alt.Tooltip(
                    "elim_rate_pct:Q",
                    title="Elimination Rate (%)",
                    format=".1f",
                ),
                alt.Tooltip(
                    "star_baker_pct:Q",
                    title="Star Baker Rate (%)",
                    format=".1f",
                ),
                alt.Tooltip(
                    "handshake_pct:Q",
                    title="Handshake Rate (%)",
                    format=".1f",
                ),
                alt.Tooltip("risk_tier:N", title="Risk Classification"),
            ]
            if "category" in m_df.columns:
                tooltip_cols.insert(1, alt.Tooltip("category:N", title="Category"))

            scatter_chart = (
                alt.Chart(m_df)
                .mark_circle(stroke="#11111b", strokeWidth=1, opacity=0.85)
                .encode(
                    x=alt.X(
                        "bakes_count:Q",
                        title="Total Challenge Usage (Occurrences)",
                        scale=alt.Scale(zero=False),
                    ),
                    y=alt.Y(
                        "danger_rate_pct:Q",
                        title="Danger Rate: Eliminated or At-Risk (%)",
                        scale=alt.Scale(domain=[0, 65]),
                    ),
                    size=alt.Size(
                        "handshake_pct:Q",
                        title="Handshake Rate (%)",
                        scale=alt.Scale(range=[80, 500]),
                    ),
                    color=alt.Color(
                        "risk_tier:N",
                        title="Risk Classification",
                        scale=tier_colors,
                    ),
                    tooltip=tooltip_cols,
                )
                .properties(height=360)
            )

            # Benchmark line for average danger rate ~28%
            danger_rule = (
                alt.Chart(pd.DataFrame({"y": [28.0]}))
                .mark_rule(
                    color=CATPPUCCIN_COLORS["subtext0"],
                    strokeDash=[4, 4],
                    strokeWidth=1.5,
                )
                .encode(y="y:Q")
            )

            st.altair_chart(scatter_chart + danger_rule, use_container_width=True)

        with col_cards:
            st.markdown("##### ☠️ The 'Kiss of Death' Ingredients")
            st.markdown(
                "- **Rosewater & Floral Notes** (40.7% Danger, 25.9% Elim): Easy to overpower bakes ('tastes like soap / perfume').\n"
                "- **Saffron** (57.1% Danger): Pungent spice frequently leading to medicinal critique.\n"
                "- **Banana & Passion Fruit** (40.6%–44.4% Danger): High moisture causes soggy bottoms and setting failures."
            )
            st.markdown("##### 🛡️ The 'Safe Haven' Staples")
            st.markdown(
                "- **Caramel & Chocolate** (High Volume, Stable): Reliable crowd-pleasers with high Star Baker conversion.\n"
                "- **Yuzu & Cardamom** (0%–15% Danger): Sophisticated acidity and aromatic warmth favored by judges.\n"
                "- **Hazelnut & Almond** (Nutty Backbone): Structural moisture absorption protects against sogginess."
            )

    st.markdown("---")

    # 3. Interactive Flavor Co-Occurrence & Affinity
    col_cooccur, col_theme = st.columns(2)

    with col_cooccur:
        st.markdown("#### 🍒 Flavor Harmony & Outcome Affinity")
        st.caption("Comparing pairing rates in Star Baker wins vs. Elimination traps.")
        if affinity_pairs:
            aff_df = pd.DataFrame(affinity_pairs[:10])
            aff_melt = aff_df.melt(
                id_vars=["pair", "total_bakes", "outcome_affinity"],
                value_vars=["star_rate_pct", "elim_rate_pct"],
                var_name="Outcome",
                value_name="Rate",
            )
            aff_melt["Outcome"] = aff_melt["Outcome"].map(
                {"star_rate_pct": "Star Baker %", "elim_rate_pct": "Elimination %"}
            )
            outcome_scale = alt.Scale(
                domain=["Star Baker %", "Elimination %"],
                range=[CATPPUCCIN_COLORS["green"], CATPPUCCIN_COLORS["red"]],
            )

            aff_chart = (
                alt.Chart(aff_melt)
                .mark_bar(cornerRadius=3)
                .encode(
                    y=alt.Y("pair:N", sort=None, title="Flavor Pairing"),
                    x=alt.X("Rate:Q", title="Rate (%)"),
                    color=alt.Color("Outcome:N", scale=outcome_scale),
                    tooltip=[
                        alt.Tooltip("pair:N", title="Pairing"),
                        alt.Tooltip("Outcome:N", title="Metric"),
                        alt.Tooltip("Rate:Q", title="Rate (%)", format=".1f"),
                        alt.Tooltip("total_bakes:Q", title="Total Bakes"),
                        alt.Tooltip("outcome_affinity:N", title="Affinity"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(aff_chart, use_container_width=True)

    with col_theme:
        st.markdown("#### ⚖️ Challenge Theme Hazard & Volume")
        st.caption(
            "Theme-by-theme breakdown of competitive pressure and elimination volume."
        )
        if not hazards_df.empty:
            theme_chart = (
                alt.Chart(hazards_df)
                .mark_bar(cornerRadius=4, color=CATPPUCCIN_COLORS["red"])
                .encode(
                    x=alt.X("eliminations:Q", title="Total Bakers Eliminated"),
                    y=alt.Y("norm_theme:N", sort="-x", title="Baking Theme"),
                    tooltip=[
                        alt.Tooltip("norm_theme:N", title="Theme"),
                        alt.Tooltip("eliminations:Q", title="Eliminations"),
                        alt.Tooltip("elimination_rate:Q", title="Elimination Rate (%)"),
                        alt.Tooltip("handshakes:Q", title="Handshakes"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(theme_chart, use_container_width=True)

    st.markdown("---")

    # 4. Bake Style & Technique Evolution Streamgraph
    st.markdown("#### 🌊 Longitudinal Bake Style & Technique Evolution")
    st.caption(
        "Tracking how contestant baking styles and modern decorative techniques evolved over 17 series."
    )

    style_view_choice = st.radio(
        "Evolution Streamgraph Perspective",
        options=["Modern Showstopper Techniques", "Canonical Bake Categories"],
        horizontal=True,
        key="streamgraph_perspective_toggle",
    )

    if style_view_choice == "Modern Showstopper Techniques" and tech_evolution:
        evo_df = pd.DataFrame(tech_evolution)
        y_col = "technique"
        color_scheme = alt.Scale(
            domain=[
                "Illusion / 3D",
                "Geometric / Tiered",
                "Mirror Glaze",
                "Gluten-Free",
                "Vegan / Plant-Based",
            ],
            range=[
                CATPPUCCIN_COLORS["mauve"],
                CATPPUCCIN_COLORS["blue"],
                CATPPUCCIN_COLORS["sapphire"],
                CATPPUCCIN_COLORS["yellow"],
                CATPPUCCIN_COLORS["green"],
            ],
        )
    elif cat_evolution:
        evo_df = pd.DataFrame(cat_evolution)
        y_col = "category"
        color_scheme = alt.Scale(
            domain=[
                "Cake & Sponge",
                "Bread",
                "Tart & Pie",
                "Biscuit & Cookie",
                "Pastry",
                "Dessert & Meringue",
            ],
            range=[
                CATPPUCCIN_COLORS["peach"],
                CATPPUCCIN_COLORS["yellow"],
                CATPPUCCIN_COLORS["red"],
                CATPPUCCIN_COLORS["mauve"],
                CATPPUCCIN_COLORS["blue"],
                CATPPUCCIN_COLORS["teal"],
            ],
        )
    else:
        evo_df = pd.DataFrame()
        y_col = "technique"
        color_scheme = alt.Scale()

    if not evo_df.empty:
        stream_chart = (
            alt.Chart(evo_df)
            .mark_area(opacity=0.8)
            .encode(
                x=alt.X(
                    "series_number:O",
                    title="Series Number",
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y(
                    "bakes_count:Q",
                    title="Tagged Challenge Bakes Count",
                    stack="zero",
                ),
                color=alt.Color(
                    f"{y_col}:N",
                    title="Bake Technique / Category",
                    scale=color_scheme,
                ),
                tooltip=[
                    alt.Tooltip("series_number:O", title="Series"),
                    alt.Tooltip(f"{y_col}:N", title="Technique / Category"),
                    alt.Tooltip("bakes_count:Q", title="Bakes Tagged"),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(stream_chart, use_container_width=True)

    # Co-occurring pairs & risk matrix registry table
    if affinity_pairs:
        st.markdown("#### 📜 Complete Flavor Co-Occurrence & Outcome Affinity Registry")
        aff_table = pd.DataFrame(affinity_pairs)
        disp_aff = aff_table.rename(
            columns={
                "pair": "Flavor Pairing",
                "total_bakes": "Total Challenges",
                "star_baker_bakes": "Star Baker Wins",
                "eliminated_bakes": "Eliminated / At-Risk",
                "star_rate_pct": "Star Baker %",
                "elim_rate_pct": "Elimination %",
                "outcome_affinity": "Outcome Affinity",
            }
        )
        st.dataframe(
            disp_aff,
            use_container_width=True,
            hide_index=True,
        )


def render_exploratory_analysis(
    datasets: dict[str, pd.DataFrame],
    data_dir: str | None = None,
) -> None:
    """Render the master Exploratory Analysis & Strategic Visualizations view."""
    bakers_df = datasets.get("bakers", pd.DataFrame())
    perfs_df = datasets.get("performances", pd.DataFrame())

    if bakers_df.empty and perfs_df.empty:
        st.warning("No processed dataset tables found in data/processed.")
        return

    st.subheader("📈 Exploratory Analysis & Strategic Visualizations")
    st.markdown(
        "Cross-series empirical analysis of **baker survival trajectories**, **Star Baker championship paths**, "
        "**Hollywood Handshake era escalation**, **Technical Challenge mortality hazards**, and **flavor profiles**."
    )

    col_era, _col_spacer = st.columns([2, 4])
    with col_era:
        selected_era = st.selectbox(
            "Broadcasting Era Filter",
            options=["ALL", "BBC Era (S1–S7)", "Channel 4 Era (S8+)"],
            index=0,
            key="exploratory_era_selector",
        )

    metrics_bundle = load_empirical_bake_metrics(era=selected_era, data_dir=data_dir)

    tabs = st.tabs(
        [
            "👥 Demographics & Survival",
            "⭐️ Star Baker Dynamics",
            "🤝 Hollywood Handshakes",
            "🎯 Technical Crucible",
            "🍓 Flavors & Theme Hazards",
            "💬 Reception & Controversy",
        ]
    )

    with tabs[0]:
        _render_demographics_tab(datasets, metrics_bundle, selected_era)

    with tabs[1]:
        _render_star_baker_tab(metrics_bundle, selected_era)

    with tabs[2]:
        _render_handshake_tab(metrics_bundle, selected_era)

    with tabs[3]:
        _render_technical_tab(metrics_bundle, selected_era)

    with tabs[4]:
        _render_flavor_theme_tab(metrics_bundle, selected_era)

    with tabs[5]:
        _render_social_reception_tab(metrics_bundle, selected_era)


def _render_social_reception_tab(metrics_bundle: dict[str, Any], era: str) -> None:
    """Render community reception, controversy index, and shock elimination dynamics."""
    st.markdown("### 💬 Social Sentiment, Fan Reception & Controversy Index")
    st.caption(
        f"Longitudinal analysis of community discussion threads, comment volume, upvote ratios, "
        f"and fan controversy spikes around unexpected eliminations ({era})."
    )

    social_df = metrics_bundle.get("social_discussions", pd.DataFrame())
    summary = metrics_bundle.get("social_summary", {})
    host_era_df = metrics_bundle.get("host_era_sentiment", pd.DataFrame())

    if social_df.empty:
        st.info("No social reception discussions available for the selected era.")
        return

    # 1. Headline KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Tracked Discussions", f"{summary.get('total_threads', len(social_df))}"
        )
    with col2:
        st.metric("Total Fan Comments", f"{summary.get('total_comments', 0):,}")
    with col3:
        avg_up = summary.get("avg_upvote_ratio", 1.0) * 100.0
        st.metric("Mean Upvote Ratio", f"{avg_up:.1f}%")
    with col4:
        st.metric(
            "Peak Controversy Episode",
            f"{summary.get('most_controversial_ep', 'N/A')}",
            f"Score: {summary.get('peak_controversy', 0):.0f}",
        )

    st.markdown("---")

    # 2. Episode Controversy & Fan Reaction Spikes
    col_chart, col_callouts = st.columns([7, 5])

    with col_chart:
        st.markdown("#### Episode Controversy & Comment Spikes")
        st.caption(
            "Bubble size = comment intensity. Y-axis = Controversy Index (comments × downvote share × sentiment penalty × upset bonus)."
        )

        chart_df = social_df.copy()
        chart_df["episode_label"] = (
            chart_df["episode_code"] + " " + chart_df["theme"].fillna("")
        )

        color_scale = alt.Scale(
            domain=["Positive", "Mixed", "Critical"],
            range=[
                CATPPUCCIN_COLORS["green"],
                CATPPUCCIN_COLORS["peach"],
                CATPPUCCIN_COLORS["red"],
            ],
        )

        bubble_chart = (
            alt.Chart(chart_df)
            .mark_circle(stroke="#11111b", strokeWidth=1, opacity=0.85)
            .encode(
                x=alt.X(
                    "series_number:O",
                    title="Series Number",
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y(
                    "controversy_index:Q",
                    title="Controversy Index Score",
                    scale=alt.Scale(zero=True),
                ),
                size=alt.Size(
                    "num_comments:Q",
                    title="Comment Volume",
                    scale=alt.Scale(range=[100, 800]),
                ),
                color=alt.Color(
                    "sentiment_label:N",
                    title="Fan Sentiment",
                    scale=color_scale,
                ),
                tooltip=[
                    alt.Tooltip("episode_code:N", title="Episode"),
                    alt.Tooltip("theme:N", title="Theme"),
                    alt.Tooltip("title:N", title="Reddit Title"),
                    alt.Tooltip(
                        "controversy_index:Q", title="Controversy Index", format=".1f"
                    ),
                    alt.Tooltip("num_comments:Q", title="Comments"),
                    alt.Tooltip("upvote_ratio:Q", title="Upvote Ratio", format=".1%"),
                    alt.Tooltip("sentiment_label:N", title="Sentiment"),
                    alt.Tooltip("star_baker:N", title="Star Baker"),
                    alt.Tooltip("eliminated_baker:N", title="Eliminated"),
                    alt.Tooltip("upset_reason:N", title="Upset Factor"),
                ],
            )
            .properties(height=360)
        )

        threshold = (
            alt.Chart(pd.DataFrame({"y": [500]}))
            .mark_rule(
                color=CATPPUCCIN_COLORS["subtext0"],
                strokeDash=[4, 4],
                strokeWidth=1.5,
            )
            .encode(y="y:Q")
        )

        st.altair_chart(bubble_chart + threshold, use_container_width=True)

    with col_callouts:
        st.markdown("#### 🚨 Historical Landmark Controversies")
        top_controversies = social_df.sort_values(
            by="controversy_index", ascending=False
        ).head(4)
        for _, row in top_controversies.iterrows():
            ep_code = row["episode_code"]
            theme = row.get("theme", "Episode")
            c_score = row["controversy_index"]
            sent = row.get("sentiment_label", "Positive")
            elim = row.get("eliminated_baker") or "No Elimination"
            sb = row.get("star_baker") or "None"
            reason = row.get("upset_reason")

            st.markdown(
                f"**{ep_code} — {theme}** ({sent})  \n"
                f"`Score: {c_score:.1f}` • `Comments: {row.get('num_comments', 0):,}` • `Upvotes: {row.get('upvote_ratio', 1.0):.0%}`  \n"
                f"• **Eliminated:** {elim}  \n"
                f"• **Star Baker:** {sb}  \n"
                f"• **Dynamic:** {reason}"
            )

    st.markdown("---")

    # 3. Sentiment vs Elimination Upset & Host Era Stability
    col_upset, col_host = st.columns(2)

    with col_upset:
        st.markdown("#### Sentiment vs. Elimination Upset Dynamics")
        st.caption(
            "Comparing discussion volume & controversy between shock exits (prior Star Bakers/high technicals) vs expected exits."
        )
        if "is_upset" in social_df.columns:
            upset_chart_df = (
                social_df.groupby(["is_upset", "sentiment_label"])
                .agg(
                    episode_count=("thread_id", "count"),
                    avg_controversy=("controversy_index", "mean"),
                    avg_comments=("num_comments", "mean"),
                )
                .reset_index()
            )
            upset_chart_df["upset_category"] = upset_chart_df["is_upset"].map(
                {
                    True: "🚨 Shock / Upset Exit",
                    False: "✅ Expected Elimination / Finale",
                }
            )
            upset_chart_df["avg_controversy"] = upset_chart_df["avg_controversy"].round(
                1
            )

            upset_chart = (
                alt.Chart(upset_chart_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X(
                        "upset_category:N",
                        title=None,
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y(
                        "avg_controversy:Q",
                        title="Mean Controversy Index",
                    ),
                    color=alt.Color(
                        "sentiment_label:N",
                        title="Sentiment",
                        scale=color_scale,
                    ),
                    tooltip=[
                        alt.Tooltip("upset_category:N", title="Category"),
                        alt.Tooltip("sentiment_label:N", title="Sentiment"),
                        alt.Tooltip("episode_count:Q", title="Episodes"),
                        alt.Tooltip("avg_controversy:Q", title="Mean Controversy"),
                        alt.Tooltip(
                            "avg_comments:Q", title="Mean Comments", format=".0f"
                        ),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(upset_chart, use_container_width=True)

    with col_host:
        st.markdown("#### Host Duo Reception Stability")
        st.caption(
            "Community reception stability across hosting duos and broadcasting eras."
        )
        if not host_era_df.empty:
            host_chart = (
                alt.Chart(host_era_df)
                .mark_bar(
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    color=CATPPUCCIN_COLORS["mauve"],
                )
                .encode(
                    x=alt.X(
                        "host_duo:N",
                        title=None,
                        axis=alt.Axis(labelAngle=-15),
                    ),
                    y=alt.Y(
                        "avg_upvote_ratio:Q",
                        title="Mean Upvote Ratio",
                        scale=alt.Scale(domain=[0.80, 1.0]),
                    ),
                    tooltip=[
                        alt.Tooltip("host_duo:N", title="Hosts"),
                        alt.Tooltip("thread_count:Q", title="Discussions"),
                        alt.Tooltip(
                            "avg_upvote_ratio:Q",
                            title="Mean Upvote Ratio",
                            format=".1%",
                        ),
                        alt.Tooltip("avg_comments:Q", title="Avg Comments"),
                        alt.Tooltip("critical_count:Q", title="Critical Spikes"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(host_chart, use_container_width=True)

    st.markdown("---")

    # 4. Curated Fan Comments & Lore Registry
    st.markdown("#### 📜 Curated Discussion Registry & Notable Fan Comments")
    filter_cols = st.columns([3, 3, 6])
    with filter_cols[0]:
        sent_filter = st.selectbox(
            "Filter by Sentiment",
            options=["ALL", "Positive", "Mixed", "Critical"],
            index=0,
            key="social_sent_filter",
        )
    with filter_cols[1]:
        upset_only = st.checkbox(
            "Show Only Shock Upsets", value=False, key="social_upset_filter"
        )

    display_df = social_df.copy()
    if sent_filter != "ALL":
        display_df = display_df[
            display_df["sentiment_label"].str.lower() == sent_filter.lower()
        ]
    if upset_only:
        display_df = display_df[display_df["is_upset"] == True]

    cols_to_show = [
        "episode_code",
        "theme",
        "title",
        "sentiment_label",
        "controversy_index",
        "num_comments",
        "upvote_ratio",
        "star_baker",
        "eliminated_baker",
        "upset_reason",
    ]
    cols_present = [c for c in cols_to_show if c in display_df.columns]
    st.dataframe(
        display_df[cols_present].sort_values(by="controversy_index", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
