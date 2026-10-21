"""Challenge Analytics view: Technical rank distributions, challenge time limits, and theme analytics."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from gbbo_dataset.dashboard.data import compute_time_pressure_metrics
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

    # 3. Recipe & Flavor Search Engine
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
