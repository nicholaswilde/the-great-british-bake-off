"""Hollywood Handshake Tracker view: Milestone counters, series distributions, and Star Baker correlations."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_handshake_tracker(data: dict[str, pd.DataFrame]) -> None:
    """Render the Hollywood Handshake tracker and accolade analytics."""
    st.title("🤝 Hollywood Handshake Tracker")
    st.markdown(
        "Track the legendary Paul Hollywood Handshake across Bake Off history. "
        "Analyze handshake frequency across series, top recipients, and examine the correlation between handshakes and Star Baker honors."
    )

    performances = data.get("performances", pd.DataFrame())
    bakers = data.get("bakers", pd.DataFrame())
    episodes = data.get("episodes", pd.DataFrame())

    if performances.empty or "hollywood_handshake" not in performances.columns:
        st.warning("No performance data available.")
        return

    hs_perfs = performances[performances["hollywood_handshake"] == True].copy()
    if not bakers.empty and "baker_id" in bakers.columns:
        hs_perfs = hs_perfs.merge(
            bakers[["baker_id", "name", "series_number"]], on="baker_id", how="left"
        )
    if not episodes.empty and "episode_id" in episodes.columns:
        hs_perfs = hs_perfs.merge(
            episodes[["episode_id", "theme", "episode_number"]],
            on="episode_id",
            how="left",
        )

    # 1. Milestone Counters & Conversion Rates
    total_hs = len(hs_perfs)
    sb_after_hs = (hs_perfs["result"] == "STAR_BAKER").sum()
    conversion_rate = (sb_after_hs / total_hs * 100) if total_hs else 0.0
    elim_after_hs = (hs_perfs["result"] == "ELIMINATED").sum()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Handshakes", total_hs)
    with m2:
        st.metric("Won Star Baker", f"{sb_after_hs} ({conversion_rate:.1f}%)")
    with m3:
        st.metric("Safe / Other", total_hs - sb_after_hs - elim_after_hs)
    with m4:
        st.metric("Eliminated Same Week", f"{elim_after_hs} (Ryan Chong)")

    st.divider()

    # 2. Charts: Handshakes per Series & Top Recipients
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Handshakes by Series")
        if "series_number" in hs_perfs.columns:
            s_counts = (
                hs_perfs["series_number"]
                .value_counts()
                .reset_index(name="Handshakes")
                .rename(columns={"series_number": "Series"})
                .sort_values(by="Series")
            )
            s_counts["Series"] = "Series " + s_counts["Series"].astype(str)

            chart_series = (
                alt.Chart(s_counts)
                .mark_bar(cornerRadius=6, color="#f38ba8")
                .encode(
                    x=alt.X("Series:N", sort=None),
                    y=alt.Y("Handshakes:Q"),
                    tooltip=["Series", "Handshakes"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_series, use_container_width=True)

    with col_right:
        st.subheader("🏅 Top Handshake Recipients")
        if "name" in hs_perfs.columns:
            leaderboard = (
                hs_perfs.groupby(["name", "series_number"])
                .size()
                .reset_index(name="Handshakes")
                .sort_values(by="Handshakes", ascending=False)
                .head(8)
            )
            leaderboard["Baker"] = (
                leaderboard["name"]
                + " (Series "
                + leaderboard["series_number"].astype(str)
                + ")"
            )

            chart_bakers = (
                alt.Chart(leaderboard)
                .mark_bar(cornerRadius=6, color="#a6e3a1")
                .encode(
                    x=alt.X("Handshakes:Q"),
                    y=alt.Y("Baker:N", sort="-x"),
                    tooltip=["Baker", "Handshakes"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_bakers, use_container_width=True)

    st.divider()

    # 3. Rare Trivia Callout
    st.subheader("🌟 Handshake Lore: The Ryan Chong Paradox")
    st.info(
        "**The Only Handshake & Elimination in Same Episode**:\n\n"
        "In **Series 3, Episode 7 (Sweet Dough Week)**, Paul Hollywood awarded a handshake to **Ryan Chong** "
        "for his Key Lime Pie in the Signature challenge. However, following struggles in the Technical and Showstopper, "
        "Ryan was eliminated at the end of the episode — making him the only baker in GBBO history to receive a Hollywood Handshake "
        "and get eliminated in the same week!"
    )

    # 4. Complete Handshake Historical Log
    st.subheader("📜 Complete Hollywood Handshake Registry")
    log_rows = []
    for _, row in hs_perfs.sort_values(
        by=["series_number", "episode_number"], ascending=[True, True]
    ).iterrows():
        log_rows.append(
            {
                "Series": f"Series {row.get('series_number', '?')}",
                "Episode": f"Ep {row.get('episode_number', '?')} ({row.get('theme', 'Bake')})",
                "Baker": row.get("name", row.get("baker_id")),
                "Signature Bake": row.get("signature_dish", "-"),
                "Showstopper Bake": row.get("showstopper_dish", "-"),
                "Outcome": row.get("result", "SAFE"),
            }
        )

    if log_rows:
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
