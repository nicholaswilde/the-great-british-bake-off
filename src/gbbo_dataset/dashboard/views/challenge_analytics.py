"""Challenge Analytics view: Technical rank distributions, challenge time limits, and theme analytics."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


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
        st.subheader("⏱️ Average Challenge Time Limits")
        if not episodes.empty:
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

    # 2. Recipe & Flavor Search Engine
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
