"""Baker Profiles view: Baker headshot, demographics, dish catalog, and geographic distribution."""

from __future__ import annotations

import math

import altair as alt
import pandas as pd
import streamlit as st

from gbbo_dataset.dashboard.data import (
    classify_occupation,
    compute_baker_skills,
    compute_champion_benchmark,
)


def render_baker_profiles(data: dict[str, pd.DataFrame]) -> None:
    """Render the baker profile, challenge catalog, and geographic distribution page."""
    st.title("👩‍🍳 Baker Profiles & Geography")
    st.markdown(
        "Inspect individual baker biographies, official portraits, signature recipes, "
        "blind technical rankings, showstopper centerpieces, and nationwide geographic distribution."
    )

    bakers = data.get("bakers", pd.DataFrame())
    performances = data.get("performances", pd.DataFrame())
    episodes = data.get("episodes", pd.DataFrame())

    if bakers.empty:
        st.warning("No baker demographic data available.")
        return

    view_mode = st.radio(
        "Profile View Mode",
        ["👤 Individual Baker Profile", "🗺️ Baker Geography & UK Map"],
        horizontal=True,
    )

    if view_mode == "👤 Individual Baker Profile":
        _render_individual_baker(bakers, performances, episodes)
    else:
        _render_baker_geography(bakers)


def generate_radar_svg(
    baker_name: str,
    baker_skills: dict[str, float],
    benchmark_skills: dict[str, float] | None = None,
    width: int = 460,
    height: int = 340,
) -> str:
    """Generate a responsive, theme-consistent SVG 5-axis radar chart."""
    cx, cy = width / 2, height / 2 + 10
    radius = 110.0
    dimensions = list(baker_skills.keys())
    n = len(dimensions)
    if n == 0:
        return ""

    angles = [i * (2 * math.pi / n) - math.pi / 2 for i in range(n)]

    # 4 concentric pentagonal rings (25%, 50%, 75%, 100%)
    rings = [0.25, 0.50, 0.75, 1.0]
    ring_paths = []
    for r_scale in rings:
        pts = [
            f"{cx + radius * r_scale * math.cos(a):.1f},{cy + radius * r_scale * math.sin(a):.1f}"
            for a in angles
        ]
        ring_paths.append(
            f'<polygon points="{" ".join(pts)}" fill="none" stroke="#313244" stroke-width="1" stroke-dasharray="3,3"/>'
        )

    # Spokes and labels
    spokes = []
    labels = []
    for a, dim in zip(angles, dimensions):
        x2 = cx + radius * math.cos(a)
        y2 = cy + radius * math.sin(a)
        spokes.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#45475a" stroke-width="1.2"/>'
        )

        lx = cx + (radius + 24) * math.cos(a)
        ly = cy + (radius + 18) * math.sin(a)
        anchor = "middle"
        if math.cos(a) > 0.3:
            anchor = "start"
        elif math.cos(a) < -0.3:
            anchor = "end"
        val = baker_skills[dim]
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#cdd6f4" font-size="11" font-family="sans-serif" text-anchor="{anchor}" font-weight="600">{dim}</text>'
            f'<text x="{lx:.1f}" y="{ly + 13:.1f}" fill="#fab387" font-size="10" font-family="sans-serif" text-anchor="{anchor}">{val:.0f}/100</text>'
        )

    # Benchmark polygon (All-time champions)
    bench_polygon = ""
    if benchmark_skills:
        b_pts = []
        for a, dim in zip(angles, dimensions):
            val = benchmark_skills.get(dim, 50.0)
            r = radius * (max(0.0, min(100.0, val)) / 100.0)
            b_pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
        bench_polygon = f'<polygon points="{" ".join(b_pts)}" fill="#a6adc8" fill-opacity="0.12" stroke="#a6adc8" stroke-width="1.8" stroke-dasharray="4,4"/>'

    # Baker polygon and data markers
    pts = []
    markers = []
    for a, dim in zip(angles, dimensions):
        val = baker_skills[dim]
        r = radius * (max(0.0, min(100.0, val)) / 100.0)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        pts.append(f"{x:.1f},{y:.1f}")
        markers.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#89b4fa" stroke="#11111b" stroke-width="1.5"/>'
        )

    baker_poly = f'<polygon points="{" ".join(pts)}" fill="#cba6f7" fill-opacity="0.32" stroke="#cba6f7" stroke-width="2.5"/>'

    legend = (
        f'<g transform="translate(16, 18)">'
        f'<rect width="10" height="10" fill="#cba6f7" fill-opacity="0.8" rx="2"/>'
        f'<text x="16" y="9" fill="#cdd6f4" font-size="10.5" font-family="sans-serif">{baker_name}</text>'
        f'<line x1="125" y1="5" x2="145" y2="5" stroke="#a6adc8" stroke-width="1.8" stroke-dasharray="3,3"/>'
        f'<text x="151" y="9" fill="#a6adc8" font-size="10.5" font-family="sans-serif">All-Time Champion Avg</text>'
        f"</g>"
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #181825; border-radius: 8px;">'
        f"{legend}"
        f"{' '.join(ring_paths)}"
        f"{' '.join(spokes)}"
        f"{bench_polygon}"
        f"{baker_poly}"
        f"{' '.join(markers)}"
        f"{' '.join(labels)}"
        f"</svg>"
    )


def _render_individual_baker(
    bakers: pd.DataFrame,
    performances: pd.DataFrame,
    episodes: pd.DataFrame,
) -> None:
    """Render single baker biographical breakdown and challenge trajectory."""
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

        # Regional & geographic details
        country = baker_info.get("country", "")
        region = baker_info.get("county_region", "")
        geo_str = f" ({region}, {country})" if region and country else ""
        st.markdown(f"**Hometown**: `{baker_info.get('hometown', 'N/A')}`{geo_str}")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("⭐ Star Bakers", sb_count)
        with m2:
            st.metric("🤝 Handshakes", hs_count)
        with m3:
            st.metric("🥇 Technical Wins", tech_wins)

    # 3. Baker Skill Radar & Archetype Profile
    st.divider()
    st.subheader("🎯 Baker Skill Radar & Archetype Profile")
    st.caption(
        "Empirical multi-axis skill matrix benchmarked against All-Time Series Champions across 5 core dimensions: "
        "Technical Mastery, Star Baker Clout, Handshake Conversion, Risk Avoidance, and Showstopper Consistency."
    )

    archetype = classify_occupation(baker_info.get("occupation"))
    skills = compute_baker_skills(baker_id, performances)
    benchmark = compute_champion_benchmark(bakers, performances)

    col_radar, col_skills = st.columns([1.3, 1.0])
    with col_radar:
        radar_svg = generate_radar_svg(
            baker_name=str(baker_info.get("name", "Baker")),
            baker_skills=skills,
            benchmark_skills=benchmark,
        )
        st.markdown(radar_svg, unsafe_allow_html=True)

    with col_skills:
        st.markdown(f"**Career Archetype**: `{archetype}`")
        st.markdown(
            f"**Series Record**: `{place_str}` in Series {baker_info.get('series_number')}"
        )
        st.markdown("#### Normalized Dimensions (0–100)")
        for dim, val in skills.items():
            bench_val = benchmark.get(dim, 50.0)
            diff = val - bench_val
            diff_str = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
            st.markdown(
                f"- **{dim}**: `{val:.1f}` / 100 *(vs Champ {bench_val:.1f}: `{diff_str}`)*"
            )

    # 4. Technical Ranking Trajectory
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

        # 5. Challenge Bake Catalog
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


def _render_baker_geography(bakers: pd.DataFrame) -> None:
    """Render interactive UK map and geographic demographics analytics."""
    st.subheader("🗺️ Great British Bake Off — Nationwide Baker Geography")
    st.markdown(
        "Explore the regional provenance of all 204 bakers across England, Scotland, "
        "Wales, and Northern Ireland. Filter by series or inspect aggregate regional representation."
    )

    # Coords check
    has_coords = (
        "latitude" in bakers.columns
        and "longitude" in bakers.columns
        and bakers["latitude"].notna().any()
    )

    if not has_coords:
        st.warning("No geographic coordinates found in baker records.")
        return

    geo_bakers = bakers.dropna(subset=["latitude", "longitude"]).copy()

    # Filter by series
    col1, _col2 = st.columns([2, 4])
    with col1:
        series_choices = ["All Series (1–17)"] + [
            f"Series {s}" for s in sorted(geo_bakers["series_number"].unique().tolist())
        ]
        chosen_series = st.selectbox("Filter Series Map", options=series_choices)

    if chosen_series != "All Series (1–17)":
        s_num = int(chosen_series.split()[1])
        display_df = geo_bakers[geo_bakers["series_number"] == s_num]
    else:
        display_df = geo_bakers

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Mapped Bakers", len(display_df))
    with m2:
        countries_count = (
            display_df["country"].nunique() if "country" in display_df.columns else 0
        )
        st.metric("Countries Represented", countries_count)
    with m3:
        top_region = (
            display_df["county_region"].value_counts().index[0]
            if "county_region" in display_df.columns
            and not display_df["county_region"].empty
            else "N/A"
        )
        st.metric("Top County / Region", top_region)
    with m4:
        champs = (
            int((display_df["overall_placement"] == 1).sum())
            if "overall_placement" in display_df.columns
            else 0
        )
        st.metric("Champions", champs)

    # Interactive Map
    st.markdown("##### 📍 Interactive Hometown Location Map")
    map_data = display_df[["latitude", "longitude"]].copy()
    st.map(map_data, zoom=5)

    st.divider()

    # Regional Distributions
    st.subheader("📊 Regional Provenance & Representation")
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("##### Bakers by Country")
        if "country" in display_df.columns:
            country_counts = (
                display_df["country"].value_counts().reset_index(name="Baker Count")
            )
            country_counts.columns = ["Country", "Baker Count"]

            c_chart = (
                alt.Chart(country_counts)
                .mark_bar()
                .encode(
                    x=alt.X("Baker Count:Q", title="Number of Bakers"),
                    y=alt.Y("Country:N", sort="-x", title=None),
                    color=alt.Color(
                        "Country:N",
                        scale=alt.Scale(
                            domain=[
                                "England",
                                "Scotland",
                                "Wales",
                                "Northern Ireland",
                                "Overseas",
                            ],
                            range=[
                                "#cba6f7",
                                "#89b4fa",
                                "#a6e3a1",
                                "#fab387",
                                "#f38ba8",
                            ],
                        ),
                        legend=None,
                    ),
                    tooltip=["Country", "Baker Count"],
                )
                .properties(height=260)
            )
            st.altair_chart(c_chart, use_container_width=True)

    with c_right:
        st.markdown("##### Top 10 Counties & Regions")
        if "county_region" in display_df.columns:
            region_counts = (
                display_df["county_region"]
                .value_counts()
                .head(10)
                .reset_index(name="Baker Count")
            )
            region_counts.columns = ["County / Region", "Baker Count"]

            r_chart = (
                alt.Chart(region_counts)
                .mark_bar(color="#89b4fa")
                .encode(
                    x=alt.X("Baker Count:Q", title="Number of Bakers"),
                    y=alt.Y("County / Region:N", sort="-x", title=None),
                    tooltip=["County / Region", "Baker Count"],
                )
                .properties(height=260)
            )
            st.altair_chart(r_chart, use_container_width=True)

    # Regional Table
    st.divider()
    st.markdown("##### 🏛️ County & Regional Breakdown Table")
    if "county_region" in display_df.columns:
        summary_rows = []
        for r_name, group in display_df.groupby("county_region"):
            c_name = group["country"].iloc[0] if "country" in group.columns else "UK"
            total = len(group)
            wins = (
                int((group["overall_placement"] == 1).sum())
                if "overall_placement" in group.columns
                else 0
            )
            finalists = (
                int((group["overall_placement"] <= 3).sum())
                if "overall_placement" in group.columns
                else 0
            )
            summary_rows.append(
                {
                    "County / Region": r_name,
                    "Country": c_name,
                    "Total Bakers": total,
                    "Finalists (Top 3)": finalists,
                    "Champions (1st)": wins,
                }
            )

        sum_df = pd.DataFrame(summary_rows).sort_values(
            by=["Total Bakers", "Champions (1st)"], ascending=[False, False]
        )

        st.dataframe(sum_df, use_container_width=True, hide_index=True)
