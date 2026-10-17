"""Overview view: Series summaries, broadcast history, judges, and winners."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_overview(data: dict[str, pd.DataFrame]) -> None:
    """Render the master overview page."""
    st.title("🍰 The Great British Bake Off — Series Overview")
    st.markdown(
        "Explore 15+ series of *The Great British Bake Off* (broadcast as *The Great British Baking Show* in North America). "
        "Select a series below to inspect broadcast history, judges, presenters, locations, and champions."
    )

    seasons = data.get("seasons", pd.DataFrame())
    bakers = data.get("bakers", pd.DataFrame())
    episodes = data.get("episodes", pd.DataFrame())
    performances = data.get("performances", pd.DataFrame())

    # 1. Key Metrics Strip
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Series", len(seasons) if not seasons.empty else 17)
    with col2:
        st.metric("Total Bakers", len(bakers) if not bakers.empty else 204)
    with col3:
        st.metric("Total Episodes", len(episodes) if not episodes.empty else 158)
    with col4:
        total_hs = (
            int(performances["hollywood_handshake"].sum())
            if not performances.empty and "hollywood_handshake" in performances.columns
            else 60
        )
        st.metric("Hollywood Handshakes", total_hs)

    st.divider()

    # 2. Series Inspector
    st.subheader("🔍 Series Inspector")
    if not seasons.empty:
        series_options = sorted(seasons["series_number"].unique().tolist())
        selected_series = st.selectbox(
            "Select Series",
            options=series_options,
            format_func=lambda s: (
                f"Series {s} ({seasons[seasons['series_number'] == s]['year'].iloc[0]})"
                if not seasons[seasons["series_number"] == s].empty
                else f"Series {s}"
            ),
            index=len(series_options) - 1 if series_options else 0,
        )

        s_row = seasons[seasons["series_number"] == selected_series]
        if not s_row.empty:
            s_data = s_row.iloc[0]

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Champion**: 🏆 `{s_data.get('winner', 'Unknown')}`")
                st.markdown(f"**Broadcast Year**: `{s_data.get('year', 'N/A')}`")
                st.markdown(f"**UK Network**: `{s_data.get('network', 'N/A')}`")
                st.markdown(f"**Filming Location**: `{s_data.get('location', 'N/A')}`")

            with col_b:
                st.markdown(f"**Judges**: `{s_data.get('judges', 'N/A')}`")
                st.markdown(f"**Presenters/Hosts**: `{s_data.get('hosts', 'N/A')}`")
                pbs = s_data.get("pbs_season")
                net = s_data.get("netflix_collection")
                roku = s_data.get("roku_season")
                streaming_info = []
                if pd.notna(pbs) and str(pbs).strip() and str(pbs).lower() != "nan":
                    streaming_info.append(f"PBS Season {int(float(pbs))}")
                if pd.notna(net) and str(net).strip() and str(net).lower() != "nan":
                    streaming_info.append(f"Netflix Collection {int(float(net))}")
                if pd.notna(roku) and str(roku).strip() and str(roku).lower() != "nan":
                    streaming_info.append(f"Roku Season {int(float(roku))}")
                st.markdown(
                    f"**Streaming Index**: `{', '.join(streaming_info) if streaming_info else 'Standard UK Broadcast'}`"
                )

            # Bakers in this series
            if not bakers.empty:
                s_bakers = bakers[
                    bakers["series_number"] == selected_series
                ].sort_values(by="overall_placement")
                if not s_bakers.empty:
                    st.markdown("#### Competing Bakers")
                    display_cols = [
                        c
                        for c in [
                            "overall_placement",
                            "name",
                            "age",
                            "occupation",
                            "hometown",
                        ]
                        if c in s_bakers.columns
                    ]
                    rename_cols = {
                        "overall_placement": "Placement",
                        "name": "Baker Name",
                        "age": "Age",
                        "occupation": "Occupation",
                        "hometown": "Hometown",
                    }
                    st.dataframe(
                        s_bakers[display_cols].rename(columns=rename_cols),
                        use_container_width=True,
                        hide_index=True,
                    )

    st.divider()

    # 3. All-Time Roll of Honor & Broadcaster Analytics
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🏆 Roll of Honor (Winners)")
        if not seasons.empty:
            winners_df = seasons[
                ["series_number", "year", "winner", "network", "location"]
            ].sort_values(by="series_number")
            st.dataframe(
                winners_df.rename(
                    columns={
                        "series_number": "Series",
                        "year": "Year",
                        "winner": "Winner",
                        "network": "Network",
                        "location": "Location",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    with col_right:
        st.subheader("📺 Broadcaster History")
        if not seasons.empty and "network" in seasons.columns:
            net_counts = (
                seasons["network"]
                .value_counts()
                .reset_index(name="count")
                .rename(columns={"network": "Broadcaster", "count": "Series Count"})
            )
            chart = (
                alt.Chart(net_counts)
                .mark_bar(cornerRadius=6)
                .encode(
                    x=alt.X("Broadcaster:N", sort="-y"),
                    y=alt.Y("Series Count:Q"),
                    color=alt.Color(
                        "Broadcaster:N",
                        scale=alt.Scale(scheme="purples"),
                        legend=None,
                    ),
                    tooltip=["Broadcaster", "Series Count"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)
