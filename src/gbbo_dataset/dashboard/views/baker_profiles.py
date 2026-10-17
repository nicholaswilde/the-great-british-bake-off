"""Baker Profiles view: Baker headshot, demographics, dish catalog, and challenge history."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_baker_profiles(data: dict[str, pd.DataFrame]) -> None:
    """Render the baker profile and challenge catalog page."""
    st.title("👩‍🍳 Baker Profiles & Challenge History")
    st.markdown(
        "Inspect individual baker biographies, official portraits, signature recipes, "
        "blind technical rankings, showstopper centerpieces, and episode-by-episode outcomes."
    )

    bakers = data.get("bakers", pd.DataFrame())
    performances = data.get("performances", pd.DataFrame())
    episodes = data.get("episodes", pd.DataFrame())

    if bakers.empty:
        st.warning("No baker demographic data available.")
        return

    # 1. Filters (Series & Baker Selection)
    col_s, col_b = st.columns([1, 2])
    with col_s:
        series_list = sorted(bakers["series_number"].unique().tolist())
        selected_series = st.selectbox("Filter by Series", options=series_list)

    filtered_bakers = bakers[bakers["series_number"] == selected_series].sort_values(
        by="name"
    )
    with col_b:
        baker_names = filtered_bakers["name"].tolist()
        selected_name = st.selectbox("Select Baker", options=baker_names)

    selected_baker_row = filtered_bakers[filtered_bakers["name"] == selected_name]
    if selected_baker_row.empty:
        return
    baker_info = selected_baker_row.iloc[0]
    baker_id = str(baker_info["baker_id"])

    # 2. Baker Profile Header & Metrics
    st.divider()
    col_img, col_demo = st.columns([1, 2])

    with col_img:
        img_url = baker_info.get("image_url")
        if (
            pd.notna(img_url)
            and str(img_url).strip()
            and str(img_url).startswith("http")
        ):
            st.image(img_url, caption=f"{baker_info['name']}", use_container_width=True)
        else:
            st.markdown(
                f"<div style='background-color:#313244;padding:40px;border-radius:12px;text-align:center;font-size:48px;'>"
                f"🧁<br><span style='font-size:18px;'>{baker_info['name']}</span></div>",
                unsafe_allow_html=True,
            )

    # Compute Accolades from performances
    b_perfs = (
        performances[performances["baker_id"] == baker_id]
        if not performances.empty
        else pd.DataFrame()
    )
    sb_count = (
        int((b_perfs["result"] == "STAR_BAKER").sum()) if not b_perfs.empty else 0
    )
    hs_count = (
        int(b_perfs["hollywood_handshake"].sum())
        if not b_perfs.empty and "hollywood_handshake" in b_perfs.columns
        else 0
    )
    tech_wins = (
        int((b_perfs["technical_rank"] == 1).sum())
        if not b_perfs.empty and "technical_rank" in b_perfs.columns
        else 0
    )

    with col_demo:
        st.subheader(f"{baker_info['name']}")
        place = baker_info.get("overall_placement")
        place_str = f"#{int(place)}" if pd.notna(place) else "Competitor"
        if place == 1:
            place_str = "🏆 Winner (1st Place)"

        st.markdown(f"**Series**: `Series {baker_info['series_number']}`")
        st.markdown(f"**Overall Placement**: `{place_str}`")
        st.markdown(
            f"**Age**: `{int(baker_info['age']) if pd.notna(baker_info.get('age')) else 'N/A'}`"
        )
        st.markdown(f"**Occupation**: `{baker_info.get('occupation', 'N/A')}`")
        st.markdown(f"**Hometown**: `{baker_info.get('hometown', 'N/A')}`")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("⭐ Star Bakers", sb_count)
        with m2:
            st.metric("🤝 Handshakes", hs_count)
        with m3:
            st.metric("🥇 Technical Wins", tech_wins)

    # 3. Technical Ranking Trajectory
    if not b_perfs.empty and not episodes.empty:
        merged = b_perfs.merge(episodes, on="episode_id", how="left").sort_values(
            by="episode_number"
        )
        has_tech = (
            "technical_rank" in merged.columns
            and merged["technical_rank"].notna().any()
        )

        if has_tech:
            st.divider()
            st.subheader("📈 Technical Challenge Ranking Trajectory")
            st.caption("Lower rank is better (1st place is top of challenge).")

            valid_tech = merged.dropna(subset=["technical_rank"]).copy()
            valid_tech["Episode"] = (
                "Ep "
                + valid_tech["episode_number"].astype(str)
                + " ("
                + valid_tech["theme"].fillna("")
                + ")"
            )

            chart = (
                alt.Chart(valid_tech)
                .mark_line(
                    point=alt.OverlayMarkDef(filled=True, size=100),
                    color="#cba6f7",
                    strokeWidth=3,
                )
                .encode(
                    x=alt.X("Episode:N", sort=None),
                    y=alt.Y(
                        "technical_rank:Q",
                        scale=alt.Scale(reverse=True, zero=False),
                        title="Technical Rank (1st = Best)",
                    ),
                    tooltip=[
                        "Episode",
                        "technical_rank",
                        "signature_dish",
                        "showstopper_dish",
                    ],
                )
                .properties(height=240)
            )
            st.altair_chart(chart, use_container_width=True)

        # 4. Challenge Bake Catalog
        st.divider()
        st.subheader("🥣 Challenge Bake Catalog")
        display_rows = []
        for _, row in merged.iterrows():
            ep_num = row.get("episode_number", "?")
            theme = row.get("theme", "Episode")
            sig = row.get("signature_dish", "-")
            tech = (
                f"#{int(row['technical_rank'])}"
                if pd.notna(row.get("technical_rank"))
                else "-"
            )
            show = row.get("showstopper_dish", "-")
            res = row.get("result", "SAFE")
            hs = "🤝 Yes" if bool(row.get("hollywood_handshake", False)) else "No"

            display_rows.append(
                {
                    "Episode": f"Ep {ep_num}: {theme}",
                    "Signature Bake": sig,
                    "Technical Rank": tech,
                    "Showstopper Bake": show,
                    "Result": res,
                    "Handshake": hs,
                }
            )

        if display_rows:
            st.dataframe(
                pd.DataFrame(display_rows), use_container_width=True, hide_index=True
            )
