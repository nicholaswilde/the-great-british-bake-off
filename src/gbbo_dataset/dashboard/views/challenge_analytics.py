"""Challenge Analytics view: Technical rank distributions, challenge time limits, and theme analytics."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from gbbo_dataset.dashboard.data import (
    compute_recipe_difficulty_and_sentiment_metrics,
    compute_time_pressure_metrics,
)
from gbbo_dataset.nlp_flavors import calculate_flavor_statistics


def render_challenge_analytics(data: dict[str, pd.DataFrame]) -> None:
    """Render challenge analytics and theme explorer."""
    st.title("⚖️ Challenge Analytics & Dish Explorer")
    st.markdown(
        "Analyze technical challenge distributions, allocated baking times across series, "
        "historical theme frequencies, and explore the complete 1,200+ recipe database."
    )

    episodes = data.get("episodes", pd.DataFrame())
    performances = data.get("performances", pd.DataFrame())
    bakers = data.get("bakers", pd.DataFrame())
    seasons = data.get("seasons", pd.DataFrame())
    fandom_recipes = data.get("fandom_recipes", pd.DataFrame())
    fandom_lore = data.get("fandom_lore", pd.DataFrame())
    bakes_nlp = data.get("bakes_nlp", pd.DataFrame())

    # 1. Historical Theme Frequency
    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        st.subheader("🍰 Most Popular Challenge Themes")
        if not episodes.empty and "theme" in episodes.columns:
            theme_counts = (
                episodes["theme"]
                .value_counts()
                .head(10)
                .reset_index(name="count")
                .rename(columns={"theme": "Theme Week", "count": "Occurrences"})
            )
            theme_chart = (
                alt.Chart(theme_counts)
                .mark_bar(cornerRadius=6, color="#89b4fa")
                .encode(
                    x=alt.X("Occurrences:Q"),
                    y=alt.Y("Theme Week:N", sort="-x"),
                    tooltip=["Theme Week", "Occurrences"],
                )
                .properties(height=300)
            )
            st.altair_chart(theme_chart, use_container_width=True)

    with col_t2:
        st.subheader("⏱️ Challenge Time Allotments & Era Squeeze")
        tp_data = compute_time_pressure_metrics(episodes, performances, seasons)
        era_df = tp_data.get("era_time_comparison", pd.DataFrame())

        if not era_df.empty:
            melted_era = era_df.melt(
                id_vars=["broadcasting_era"],
                value_vars=["avg_signature", "avg_technical", "avg_showstopper"],
                var_name="Challenge",
                value_name="Minutes",
            )
            melted_era["Challenge"] = melted_era["Challenge"].map(
                {
                    "avg_signature": "Signature",
                    "avg_technical": "Technical",
                    "avg_showstopper": "Showstopper",
                }
            )
            time_chart = (
                alt.Chart(melted_era)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("Challenge:N", sort=None),
                    y=alt.Y("Minutes:Q", title="Average Minutes"),
                    color=alt.Color(
                        "broadcasting_era:N",
                        scale=alt.Scale(
                            domain=["BBC Era", "Channel 4 Era"],
                            range=["#cba6f7", "#fab387"],
                        ),
                        title="Broadcasting Era",
                    ),
                    xOffset="broadcasting_era:N",
                    tooltip=["Challenge", "broadcasting_era", "Minutes"],
                )
                .properties(height=300)
            )
            st.altair_chart(time_chart, use_container_width=True)
        elif not episodes.empty:
            time_cols = [
                c
                for c in [
                    "signature_time_min",
                    "technical_time_min",
                    "showstopper_time_min",
                ]
                if c in episodes.columns
            ]
            if time_cols:
                avg_times = episodes[time_cols].mean().reset_index()
                avg_times.columns = ["Challenge", "Average Minutes"]
                avg_times["Challenge"] = avg_times["Challenge"].replace(
                    {
                        "signature_time_min": "Signature",
                        "technical_time_min": "Technical",
                        "showstopper_time_min": "Showstopper",
                    }
                )
                time_chart = (
                    alt.Chart(avg_times)
                    .mark_bar(cornerRadius=6, color="#fab387")
                    .encode(
                        x=alt.X("Challenge:N", sort=None),
                        y=alt.Y("Average Minutes:Q"),
                        tooltip=["Challenge", "Average Minutes"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(time_chart, use_container_width=True)

    st.divider()

    # 2. NLP Flavor Profiles & Style Classifications
    st.subheader("🍓 NLP Flavor Profiles & Bake Styles")
    st.caption(
        "Structured NLP extraction across 1,200+ signature and showstopper dish descriptions, "
        "identifying flavor taxonomy, bake styles, and outcome correlations."
    )

    if not performances.empty:
        stats = calculate_flavor_statistics(performances)

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            st.markdown("**Top Flavor Families**")
            flavors_df = pd.DataFrame(
                list(stats["flavor_counts"].items()),
                columns=["Flavor Family", "Bake Count"],
            ).head(10)
            if not flavors_df.empty:
                flavor_chart = (
                    alt.Chart(flavors_df)
                    .mark_bar(cornerRadius=6, color="#a6e3a1")
                    .encode(
                        x=alt.X("Bake Count:Q"),
                        y=alt.Y("Flavor Family:N", sort="-x"),
                        tooltip=["Flavor Family", "Bake Count"],
                    )
                    .properties(height=280)
                )
                st.altair_chart(flavor_chart, use_container_width=True)

        with col_f2:
            st.markdown("**Top Bake Styles & Techniques**")
            styles_df = pd.DataFrame(
                list(stats["style_counts"].items()),
                columns=["Bake Category", "Bake Count"],
            ).head(8)
            if not styles_df.empty:
                style_chart = (
                    alt.Chart(styles_df)
                    .mark_bar(cornerRadius=6, color="#cba6f7")
                    .encode(
                        x=alt.X("Bake Count:Q"),
                        y=alt.Y("Bake Category:N", sort="-x"),
                        tooltip=["Bake Category", "Bake Count"],
                    )
                    .properties(height=280)
                )
                st.altair_chart(style_chart, use_container_width=True)

        # Flavor-outcome rates
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            st.markdown("**🤝 Highest Hollywood Handshake Rates (%)**")
            hs_df = pd.DataFrame(
                list(stats["handshake_rates"].items()),
                columns=["Flavor Family", "Handshake Rate (%)"],
            ).head(8)
            if not hs_df.empty:
                hs_chart = (
                    alt.Chart(hs_df)
                    .mark_bar(cornerRadius=6, color="#f9e2af")
                    .encode(
                        x=alt.X("Handshake Rate (%):Q"),
                        y=alt.Y("Flavor Family:N", sort="-x"),
                        tooltip=["Flavor Family", "Handshake Rate (%)"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(hs_chart, use_container_width=True)

        with col_r2:
            st.markdown("**⭐ Highest Star Baker Conversion Rates (%)**")
            sb_df = pd.DataFrame(
                list(stats["star_baker_rates"].items()),
                columns=["Flavor Family", "Star Baker Rate (%)"],
            ).head(8)
            if not sb_df.empty:
                sb_chart = (
                    alt.Chart(sb_df)
                    .mark_bar(cornerRadius=6, color="#f38ba8")
                    .encode(
                        x=alt.X("Star Baker Rate (%):Q"),
                        y=alt.Y("Flavor Family:N", sort="-x"),
                        tooltip=["Flavor Family", "Star Baker Rate (%)"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(sb_chart, use_container_width=True)

    st.divider()

    # 3. Recipe Difficulty, Judging Sentiment & Ambition Paradox
    diff_bundle = compute_recipe_difficulty_and_sentiment_metrics(
        recipes=fandom_recipes,
        lore=fandom_lore,
        performances=performances,
        bakes_nlp=bakes_nlp,
        episodes=episodes,
    )
    diff_sent_df = diff_bundle.get("difficulty_sentiment", pd.DataFrame())
    tier_summary = diff_bundle.get("difficulty_tier_summary", pd.DataFrame())
    complexity_df = diff_bundle.get("challenge_type_complexity", pd.DataFrame())
    ambition_outcomes = diff_bundle.get("ambition_outcomes", pd.DataFrame())
    summary = diff_bundle.get("recipe_summary", {})

    st.subheader("🎯 Recipe Difficulty, Judge Sentiment & Ambition Paradox")
    st.caption(
        "Correlating technical challenge difficulty ratings and qualitative judge critique with "
        "baker ambition, Hollywood handshake probabilities, and high-risk elimination hazards."
    )

    if not diff_sent_df.empty or not ambition_outcomes.empty:
        # Highlight Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Top Difficulty Bake",
            summary.get("most_difficult_recipe", "N/A"),
            "Extreme Tier",
        )
        m2.metric(
            "Judge Sentiment Polarities",
            f"+{summary.get('avg_sentiment_easy', 0.0):.1f} / {summary.get('avg_sentiment_extreme', 0.0):.1f}",
            "Easy vs. Extreme",
        )
        mod_elim = summary.get("moderate_ambition_elimination_rate", 0.0)
        ext_elim = summary.get("high_ambition_elimination_rate", 0.0)
        m3.metric(
            "Extreme Ambition Hazard",
            f"{ext_elim:.1f}%",
            f"+{ext_elim - mod_elim:.1f}% vs Mod",
            delta_color="inverse",
        )
        m4.metric(
            "Extreme Star Baker Rate",
            f"{summary.get('high_ambition_star_baker_rate', 0.0):.1f}%",
            "High Ceiling",
        )

        col_c1, col_c2 = st.columns([1, 1])

        with col_c1:
            st.markdown("#### ⚖️ Recipe Difficulty vs. Judge Sentiment Polarity")
            st.caption(
                "Average net sentiment polarity score extracted from Mary & Paul's technical judging commentary (-1.0 = Critical, +1.0 = Positive)."
            )
            if not tier_summary.empty:
                tier_plot = tier_summary.copy()
                tier_plot["sentiment_color"] = tier_plot["avg_sentiment"].apply(
                    lambda x: (
                        "#a6e3a1"
                        if x > 0.15
                        else ("#f38ba8" if x < -0.15 else "#89b4fa")
                    )
                )
                sent_chart = (
                    alt.Chart(tier_plot)
                    .mark_bar(cornerRadius=6)
                    .encode(
                        x=alt.X(
                            "avg_sentiment:Q",
                            title="Net Judging Sentiment Polarity (-1 to +1)",
                            scale=alt.Scale(domain=[-1.0, 1.0]),
                        ),
                        y=alt.Y(
                            "difficulty:N",
                            sort=alt.SortField(
                                field="difficulty_num", order="ascending"
                            ),
                            title="Difficulty Tier",
                        ),
                        color=alt.Color("sentiment_color:N", scale=None),
                        tooltip=[
                            alt.Tooltip("difficulty:N", title="Tier"),
                            alt.Tooltip("recipe_count:Q", title="Recipes"),
                            alt.Tooltip(
                                "avg_sentiment:Q",
                                title="Avg Sentiment",
                                format="+.2f",
                            ),
                            alt.Tooltip(
                                "positive_share:Q",
                                title="Positive (%)",
                                format=".1f",
                            ),
                            alt.Tooltip(
                                "critical_share:Q",
                                title="Critical (%)",
                                format=".1f",
                            ),
                        ],
                    )
                    .properties(height=280)
                )
                st.altair_chart(sent_chart, use_container_width=True)

        with col_c2:
            st.markdown("#### 🍰 Challenge Complexity & Difficulty Distribution")
            st.caption(
                "Distribution of recipe challenge types across difficulty tiers."
            )
            if not complexity_df.empty:
                tier_order = ["Easy", "Moderate", "Hard", "Very Hard", "Extreme"]
                comp_chart = (
                    alt.Chart(complexity_df)
                    .mark_bar(cornerRadius=4)
                    .encode(
                        x=alt.X("recipe_count:Q", title="Number of Recipes"),
                        y=alt.Y("challenge_type:N", title="Challenge Type"),
                        color=alt.Color(
                            "difficulty:N",
                            scale=alt.Scale(
                                domain=tier_order,
                                range=[
                                    "#a6e3a1",
                                    "#89b4fa",
                                    "#fab387",
                                    "#f38ba8",
                                    "#e64553",
                                ],
                            ),
                            title="Difficulty",
                        ),
                        order=alt.Order("difficulty_num:Q", sort="ascending"),
                        tooltip=[
                            alt.Tooltip("challenge_type:N", title="Challenge"),
                            alt.Tooltip("difficulty:N", title="Difficulty"),
                            alt.Tooltip("recipe_count:Q", title="Count"),
                            alt.Tooltip("share_pct:Q", title="Share (%)", format=".1f"),
                        ],
                    )
                    .properties(height=280)
                )
                st.altair_chart(comp_chart, use_container_width=True)

        if not ambition_outcomes.empty:
            st.markdown(
                "#### ⚡ The Bake Off Ambition Paradox: Ambition Tier vs. Performance Rates"
            )
            st.caption(
                "Comparing technique & flavor ambition scores across 1,200+ bakes against Hollywood handshakes, Star Baker honors, and elimination hazard."
            )
            melted_amb = ambition_outcomes.melt(
                id_vars=["ambition_tier"],
                value_vars=[
                    "elimination_rate",
                    "star_baker_rate",
                    "did_well_rate",
                    "handshake_rate",
                ],
                var_name="Metric",
                value_name="Rate",
            )
            metric_label_map = {
                "elimination_rate": "Elimination Hazard (%)",
                "star_baker_rate": "Star Baker Rate (%)",
                "did_well_rate": "Did Well Rate (%)",
                "handshake_rate": "Handshake Rate (%)",
            }
            melted_amb["Metric"] = melted_amb["Metric"].map(metric_label_map)

            amb_chart = (
                alt.Chart(melted_amb)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("Metric:N", title=None, axis=alt.Axis(labels=True)),
                    y=alt.Y("Rate:Q", title="Rate (%)"),
                    color=alt.Color(
                        "Metric:N",
                        scale=alt.Scale(
                            domain=[
                                "Elimination Hazard (%)",
                                "Star Baker Rate (%)",
                                "Did Well Rate (%)",
                                "Handshake Rate (%)",
                            ],
                            range=["#f38ba8", "#f9e2af", "#a6e3a1", "#fab387"],
                        ),
                        legend=None,
                    ),
                    column=alt.Column(
                        "ambition_tier:N",
                        title="Baker Ambition Tier",
                        header=alt.Header(labelOrient="bottom", titleOrient="bottom"),
                    ),
                    tooltip=[
                        "ambition_tier:N",
                        "Metric:N",
                        alt.Tooltip("Rate:Q", format=".1f"),
                    ],
                )
                .properties(width=160, height=260)
            )
            st.altair_chart(amb_chart, use_container_width=True)

            st.info(
                "💡 **The High-Ambition Precision Trap**: Extreme Ambition yields the highest 'Did Well' ceiling "
                f"({summary.get('high_ambition_star_baker_rate', 12.7):.1f}% Star Baker, 19.0% Did Well), "
                f"but incurs an elevated **{summary.get('high_ambition_elimination_rate', 15.9):.1f}% elimination hazard** "
                f"(vs. {summary.get('moderate_ambition_elimination_rate', 9.7):.1f}% for Moderate Ambition) and depressed handshake frequency. "
                "Tent time pressure frequently turns intricate sugar work, delicate mousses, and high-tier layering into fatal execution flaws."
            )

        if not diff_sent_df.empty:
            st.markdown("#### 📖 Curated Recipe Difficulty & Critique Explorer")
            col_sel1, col_sel2 = st.columns([1, 1])
            with col_sel1:
                diff_filter = st.selectbox(
                    "Filter by Difficulty Tier",
                    options=[
                        "All",
                        "Easy",
                        "Moderate",
                        "Hard",
                        "Very Hard",
                        "Extreme",
                    ],
                    key="diff_filter_select",
                )
            with col_sel2:
                sent_filter = st.selectbox(
                    "Filter by Judge Sentiment",
                    options=["All", "Positive", "Neutral", "Critical"],
                    key="sent_filter_select",
                )

            filtered_recipes = diff_sent_df.copy()
            if diff_filter != "All":
                filtered_recipes = filtered_recipes[
                    filtered_recipes["difficulty"] == diff_filter
                ]
            if sent_filter != "All":
                filtered_recipes = filtered_recipes[
                    filtered_recipes["sentiment_label"] == sent_filter
                ]

            display_cols = [
                "series_number",
                "episode_number",
                "challenge_type",
                "dish_name",
                "difficulty",
                "sentiment_label",
                "sentiment_score",
                "judging_notes",
                "positive_indicators",
                "critical_indicators",
            ]
            valid_cols = [c for c in display_cols if c in filtered_recipes.columns]
            st.dataframe(
                filtered_recipes[valid_cols].rename(
                    columns={
                        "series_number": "Series",
                        "episode_number": "Episode",
                        "challenge_type": "Challenge",
                        "dish_name": "Recipe Dish",
                        "difficulty": "Difficulty",
                        "sentiment_label": "Sentiment",
                        "sentiment_score": "Polarity",
                        "judging_notes": "Judge Commentary",
                        "positive_indicators": "Praise Indicators",
                        "critical_indicators": "Critique Indicators",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    # 4. Recipe & Flavor Search Engine
    st.subheader("🔍 Flavor & Recipe Search Engine")
    st.caption(
        "Search across 1,200+ signature and showstopper dishes for specific flavors, ingredients, or techniques."
    )

    query = st.text_input(
        "Search ingredients, flavors, or bakes (e.g. chocolate, raspberry, cardamom, brioche, passion fruit)",
        value="chocolate",
    )

    if not performances.empty and query.strip():
        q_lower = query.strip().lower()
        merged = performances.copy()
        if (
            not bakers.empty
            and "baker_id" in merged.columns
            and "baker_id" in bakers.columns
        ):
            merged = merged.merge(
                bakers[["baker_id", "name", "series_number"]], on="baker_id", how="left"
            )
        if (
            not episodes.empty
            and "episode_id" in merged.columns
            and "episode_id" in episodes.columns
        ):
            merged = merged.merge(
                episodes[["episode_id", "theme", "episode_number"]],
                on="episode_id",
                how="left",
            )

        sig_matches = (
            merged["signature_dish"].fillna("").str.lower().str.contains(q_lower)
        )
        show_matches = (
            merged["showstopper_dish"].fillna("").str.lower().str.contains(q_lower)
        )
        matches = merged[sig_matches | show_matches]

        st.markdown(f"Found **{len(matches)}** challenge bakes matching *'{query}'*:")

        results_list = []
        for _, r in matches.iterrows():
            name = r.get("name", r.get("baker_id", "Unknown"))
            s_num = r.get("series_number", "?")
            ep_num = r.get("episode_number", "?")
            theme = r.get("theme", "Baking")
            sig = r.get("signature_dish", "-")
            show = r.get("showstopper_dish", "-")
            res = r.get("result", "SAFE")
            hs = "🤝" if bool(r.get("hollywood_handshake", False)) else ""

            results_list.append(
                {
                    "Series": f"Series {s_num}",
                    "Episode": f"Ep {ep_num} ({theme})",
                    "Baker": name,
                    "Signature Dish": sig,
                    "Showstopper Dish": show,
                    "Result": f"{res} {hs}".strip(),
                }
            )

        if results_list:
            st.dataframe(
                pd.DataFrame(results_list), use_container_width=True, hide_index=True
            )
