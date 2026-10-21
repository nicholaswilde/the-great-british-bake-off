"""Interactive Predictor view for the GBBO Streamlit dashboard."""

from __future__ import annotations

import math
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from gbbo_dataset.dashboard.data import compute_underdog_and_upset_metrics
from gbbo_dataset.predictor import SeriesPredictor


def _compute_diagnostics(baker: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Compute empirical strengths and risk factors for an individual baker."""
    strengths: list[str] = []
    risks: list[str] = []

    sb = baker.get("star_baker_count", 0)
    if sb > 0:
        strengths.append(f"⭐️ {sb} Star Baker title(s) earned")

    hs = baker.get("handshake_count", 0)
    if hs > 0:
        strengths.append(f"🤝 {hs} Hollywood Handshake(s) received")

    tech_pct = float(baker.get("avg_technical_pct", 0.5))
    if tech_pct >= 0.65:
        strengths.append(
            f"🎯 Elite technical challenge mastery ({tech_pct * 100:.1f}% percentile)"
        )

    if baker.get("last_star_baker"):
        strengths.append("🔥 Reigning Star Baker (peak positive momentum)")

    if baker.get("last_handshake"):
        strengths.append("✨ Received Hollywood Handshake in most recent episode")

    age = baker.get("age")
    age_score = float(baker.get("age_score", 0.6))
    if age and age_score >= 0.85:
        strengths.append(f"📊 Prime champion age demographic ({age} years old)")

    ep_comp = baker.get("episodes_competed", 0)
    if baker.get("at_risk_count", 0) == 0 and ep_comp >= 2:
        strengths.append("🛡️ Zero bottom / at-risk callouts by judges")

    if baker.get("did_well_count", 0) >= 2:
        strengths.append(
            f"👏 Called out as doing well {baker.get('did_well_count')} times"
        )

    # Risk factors
    ar = baker.get("at_risk_count", 0)
    if ar >= 2:
        risks.append(f"⚠️ {ar} bottom / at-risk judge callouts")

    if baker.get("last_at_risk"):
        risks.append("🚨 Finished in danger zone / at risk in the most recent episode")

    if tech_pct < 0.45:
        risks.append(
            f"📉 Vulnerable technical ranking average ({tech_pct * 100:.1f}% percentile)"
        )

    if sb == 0 and ep_comp >= 4:
        risks.append("⏳ Zero Star Baker honors through 4+ episodes")

    if hs == 0 and ep_comp >= 5:
        risks.append("🤝 No Hollywood Handshakes received through 5+ episodes")

    return strengths, risks


def render_predictor_view(datasets: dict[str, pd.DataFrame]) -> None:
    """Render the Interactive Season & Baker Predictor view."""
    st.title("🔮 Empirical Outcome & Elimination Risk Predictor")
    st.markdown(
        "Leverage empirical multi-factor modeling calibrated across 16 historical series "
        "(200+ bakers, 16 champions) to evaluate Star Baker odds, elimination hazard rates, "
        "and series finale trajectories."
    )

    pred_mode = st.radio(
        "Prediction Mode",
        ["🏆 Series Forecast", "🧪 Custom Baker 'What-If' Simulator"],
        horizontal=True,
    )

    if pred_mode == "🏆 Series Forecast":
        _render_series_forecast(datasets)
    else:
        _render_custom_baker_simulator()


def _render_series_forecast(datasets: dict[str, pd.DataFrame]) -> None:
    """Render full series forecast interface."""
    seasons_df = datasets.get("seasons", pd.DataFrame())
    if not seasons_df.empty and "series_number" in seasons_df.columns:
        available_series = sorted(
            seasons_df["series_number"].dropna().unique().astype(int).tolist()
        )
    else:
        available_series = list(range(1, 18))

    def _format_pred_series(s: int) -> str:
        row = (
            seasons_df[seasons_df["series_number"] == s]
            if not seasons_df.empty
            else pd.DataFrame()
        )
        if not row.empty:
            w = row.iloc[0].get("winner")
            if not w or str(w).strip().lower() in ("none", "nan", "tbd", ""):
                return f"Series {s} 🔴 (In Progress)"
        return f"Series {s}"

    col1, col2 = st.columns([2, 3])
    with col1:
        target_series = st.selectbox(
            "Target Series",
            options=available_series,
            index=len(available_series) - 1 if available_series else 0,
            format_func=_format_pred_series,
            key="pred_series_select",
        )

    predictor = SeriesPredictor()

    with st.spinner(f"Computing empirical predictions for Series {target_series}..."):
        try:
            initial_results = predictor.predict_series(series=int(target_series))
        except Exception as e:
            st.error(f"Error predicting Series {target_series}: {e}")
            return

    max_ep = initial_results.get("current_episode", 0)

    with col2:
        if max_ep > 1:
            selected_ep = st.slider(
                "Forecast As of Completed Episode",
                min_value=1,
                max_value=max_ep,
                value=max_ep,
                help="Simulate historical odds at an earlier point in the series.",
            )
            if selected_ep != max_ep:
                try:
                    results = predictor.predict_series(
                        series=int(target_series), as_of_episode=selected_ep
                    )
                except Exception as e:
                    st.error(f"Error computing as of episode {selected_ep}: {e}")
                    results = initial_results
            else:
                results = initial_results
        else:
            results = initial_results

    rankings = results.get("rankings", [])
    if not rankings:
        st.warning(f"No baker performance records found for Series {target_series}.")
        return

    # Key Metrics Strip
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Bakers", results.get("total_bakers", 0))
    with m2:
        st.metric("Active Contenders", results.get("active_bakers_count", 0))
    with m3:
        st.metric("Eliminated Bakers", results.get("eliminated_bakers_count", 0))
    with m4:
        curr_ep = results.get("current_episode", 0)
        next_ep = results.get("next_episode", 1)
        st.metric("Stage", f"Ep {curr_ep} (Predicting Ep {next_ep})")

    st.divider()

    # Contender Probabilities & Rankings Table
    st.subheader("📋 Contender Probabilities & Cumulative Stats")
    rows = []
    for rank, baker in enumerate(rankings, 1):
        rows.append(
            {
                "Rank": rank,
                "Baker": baker["name"],
                "Status": baker["status"],
                "Age": baker["age"] if baker["age"] else "N/A",
                "Star Bakers": baker.get("star_baker_count", 0),
                "Handshakes": baker.get("handshake_count", 0),
                "Tech Mastery": f"{float(baker.get('avg_technical_pct', 0.5)) * 100:.1f}%",
                "Win Prob (%)": baker.get("win_probability", 0.0),
                "Top 3 Prob (%)": baker.get("top3_probability", 0.0),
                "Next Star Baker (%)": baker.get("star_baker_prob", 0.0),
                "Next Elim Risk (%)": baker.get("elimination_risk", 0.0),
            }
        )
    rankings_df = pd.DataFrame(rows)
    st.dataframe(rankings_df, use_container_width=True, hide_index=True)

    # Probability Distribution Charts
    active_bakers = [b for b in rankings if b.get("is_active")]
    if active_bakers:
        st.subheader("📊 Probability Visualizations (Active Contenders)")
        c1, c2 = st.columns(2)

        # Chart 1: Win & Finale Odds
        with c1:
            st.markdown("##### 🏆 Series Win & Finale (Top 3) Odds")
            chart1_data = []
            for b in active_bakers:
                chart1_data.append(
                    {
                        "Baker": b["name"],
                        "Metric": "Win Prob (%)",
                        "Probability": b.get("win_probability", 0.0),
                    }
                )
                chart1_data.append(
                    {
                        "Baker": b["name"],
                        "Metric": "Top 3 Prob (%)",
                        "Probability": b.get("top3_probability", 0.0),
                    }
                )
            df1 = pd.DataFrame(chart1_data)
            bar1 = (
                alt.Chart(df1)
                .mark_bar()
                .encode(
                    x=alt.X("Probability:Q", title="Probability (%)"),
                    y=alt.Y("Baker:N", sort="-x", title=None),
                    color=alt.Color(
                        "Metric:N",
                        scale=alt.Scale(
                            domain=["Win Prob (%)", "Top 3 Prob (%)"],
                            range=["#cba6f7", "#89b4fa"],
                        ),
                        legend=alt.Legend(orient="bottom", title=None),
                    ),
                    tooltip=["Baker", "Metric", "Probability"],
                )
                .properties(height=320)
            )
            st.altair_chart(bar1, use_container_width=True)

        # Chart 2: Next Episode Outlook
        with c2:
            st.markdown(f"##### 🎯 Episode {results.get('next_episode', 1)} Outlook")
            chart2_data = []
            for b in active_bakers:
                chart2_data.append(
                    {
                        "Baker": b["name"],
                        "Metric": "Star Baker Odds (%)",
                        "Probability": b.get("star_baker_prob", 0.0),
                    }
                )
                chart2_data.append(
                    {
                        "Baker": b["name"],
                        "Metric": "Elimination Hazard (%)",
                        "Probability": b.get("elimination_risk", 0.0),
                    }
                )
            df2 = pd.DataFrame(chart2_data)
            bar2 = (
                alt.Chart(df2)
                .mark_bar()
                .encode(
                    x=alt.X("Probability:Q", title="Probability (%)"),
                    y=alt.Y("Baker:N", sort="-x", title=None),
                    color=alt.Color(
                        "Metric:N",
                        scale=alt.Scale(
                            domain=["Star Baker Odds (%)", "Elimination Hazard (%)"],
                            range=["#a6e3a1", "#f38ba8"],
                        ),
                        legend=alt.Legend(orient="bottom", title=None),
                    ),
                    tooltip=["Baker", "Metric", "Probability"],
                )
                .properties(height=320)
            )
            st.altair_chart(bar2, use_container_width=True)

        st.divider()

        # Baker Diagnostics
        st.subheader("🔍 Baker Analytical Profile & Factor Diagnostics")
        active_names = [b["name"] for b in active_bakers]
        selected_baker_name = st.selectbox(
            "Select Baker to Inspect Diagnostics:", options=active_names
        )
        selected_baker = next(
            (b for b in active_bakers if b["name"] == selected_baker_name), None
        )
        if selected_baker:
            strengths, risks = _compute_diagnostics(selected_baker)
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("##### ✅ Analytical Strengths")
                if strengths:
                    for s in strengths:
                        st.success(s)
                else:
                    st.info("No significant statistical advantages identified.")
            with d2:
                st.markdown("##### ⚠️ Risk Factors")
                if risks:
                    for r in risks:
                        st.error(r)
                else:
                    st.info("No significant statistical risk penalties identified.")

        st.divider()

        # Theme Week Casualty & Upset Risk Heatmap
        st.subheader("🌪️ Theme Week Casualty Spikes & Upset Risk Heatmap")
        st.caption(
            "Historical casualty rates and frontrunner upset probabilities across GBBO challenge themes. "
            "High-volatility themes (such as Pâtisserie and Pastry) feature high shock departure rates where decorated favorites stumble."
        )

        bakers_df = datasets.get("bakers", pd.DataFrame())
        episodes_df = datasets.get("episodes", pd.DataFrame())
        perf_df = datasets.get("performances", pd.DataFrame())

        underdog_data = compute_underdog_and_upset_metrics(
            bakers_df, episodes_df, perf_df, seasons_df
        )
        theme_upsets = underdog_data.get("theme_upset_rates", pd.DataFrame())

        if not theme_upsets.empty:
            c_th1, c_th2 = st.columns([1.2, 1.0])
            with c_th1:
                theme_chart = (
                    alt.Chart(theme_upsets)
                    .mark_bar(cornerRadius=4)
                    .encode(
                        x=alt.X("upset_rate:Q", title="Upset Elimination Rate (%)"),
                        y=alt.Y("norm_theme:N", sort="-x", title="Challenge Theme"),
                        color=alt.Color(
                            "upset_rate:Q",
                            scale=alt.Scale(range=["#89b4fa", "#f38ba8"]),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("norm_theme:N", title="Theme"),
                            alt.Tooltip(
                                "upset_rate:Q", title="Upset Rate (%)", format=".1f"
                            ),
                            alt.Tooltip(
                                "upset_eliminations:Q",
                                title="Decorated Bakers Eliminated",
                            ),
                            alt.Tooltip("eliminations:Q", title="Total Eliminations"),
                        ],
                    )
                    .properties(height=280)
                )
                st.altair_chart(theme_chart, use_container_width=True)

            with c_th2:
                st.dataframe(
                    theme_upsets.rename(
                        columns={
                            "norm_theme": "Theme",
                            "total_performances": "Bakes",
                            "eliminations": "Eliminations",
                            "upset_eliminations": "Upsets",
                            "elimination_rate": "Elim Rate (%)",
                            "upset_rate": "Upset Rate (%)",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.info(
                    "🚨 **Predictive Takeaway**: Pâtisserie week features a **92.9% upset rate** — 13 of 14 eliminated bakers were decorated frontrunners. When forecasting semifinals or pastry themes, discount early regular season momentum."
                )


def _render_custom_baker_simulator() -> None:
    """Render interactive what-if baker evaluator."""
    st.subheader("🧪 Custom Baker Evaluator & 'What-If' Simulator")
    st.markdown(
        "Configure hypothetical baker demographics, technical challenge execution, "
        "and judging callouts to evaluate their empirical momentum and win log-odds "
        "calibrated against Series 1–16 champions."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        baker_name = st.text_input("Baker Name", value="Hypothetical Star")
        age = st.slider("Age", min_value=17, max_value=75, value=31)

    with c2:
        episodes_competed = st.slider(
            "Episodes Competed So Far", min_value=1, max_value=10, value=4
        )
        tech_pct = st.slider(
            "Average Technical Rank Percentile",
            min_value=0.0,
            max_value=1.0,
            value=0.65,
            step=0.05,
            help="1.0 = consistently 1st place in technicals, 0.0 = consistently last.",
        )

    with c3:
        star_bakers = st.number_input(
            "Star Baker Honors", min_value=0, max_value=5, value=1, step=1
        )
        handshakes = st.number_input(
            "Hollywood Handshakes", min_value=0, max_value=4, value=1, step=1
        )
        at_risk = st.number_input(
            "Times at Risk / In Bottom", min_value=0, max_value=4, value=0, step=1
        )
        did_well = st.number_input(
            "Times Called Out Doing Well", min_value=0, max_value=5, value=1, step=1
        )

    st.markdown("##### Recent Episode Momentum (Episode N)")
    f1, f2, f3 = st.columns(3)
    with f1:
        last_sb = st.checkbox("Was Star Baker in Last Episode", value=False)
    with f2:
        last_hs = st.checkbox("Received Handshake in Last Episode", value=False)
    with f3:
        last_ar = st.checkbox("Was At Risk in Last Episode", value=False)

    predictor = SeriesPredictor()
    baselines = predictor.baselines

    mean_age = float(baselines.get("winner_mean_age", 32.5))
    std_age = float(baselines.get("winner_std_age", 9.89))
    age_score = math.exp(-((age - mean_age) ** 2) / (2 * (std_age**2)))
    has_dw = did_well > 0
    sb_raw = (
        0.30 * tech_pct
        + 0.25 * tech_pct
        + 0.20
        * (
            min(star_bakers, 3) * 0.5
            + (0.8 if last_sb else 0.0)
            + (0.4 if has_dw else 0.0)
        )
        + 0.15 * (min(handshakes, 3) * 0.4 + (0.6 if last_hs else 0.0))
        + 0.05 * age_score
        - (0.35 if last_ar else 0.0)
        - 0.10 * min(at_risk, 3)
    )

    elim_raw = (
        0.35 * (1.0 - tech_pct)
        + 0.25 * (1.0 - tech_pct)
        + 0.35 * (1.0 if last_ar else 0.0)
        + 0.15 * min(at_risk, 3)
        - 0.20 * min(star_bakers, 2)
        - 0.15 * min(handshakes, 2)
        - 0.10 * min(did_well, 2)
    )

    win_raw = (
        0.35 * tech_pct
        + 0.25 * min(star_bakers, 3)
        + 0.15 * min(handshakes, 3)
        + 0.10 * min(did_well, 3)
        - 0.20 * min(at_risk, 3)
        + 0.10 * age_score
    )

    st.divider()
    st.markdown(f"#### 📈 Evaluation Results for **{baker_name}**")

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Win Log-Odds Score", f"{win_raw:.3f}")
    with r2:
        st.metric("Star Baker Momentum", f"{sb_raw:.3f}")
    with r3:
        st.metric("Elimination Hazard", f"{elim_raw:.3f}")
    with r4:
        st.metric("Champion Age Match", f"{age_score * 100:.1f}%")

    st.markdown("##### 🏛️ Comparison with Historical GBBO Champions")
    c_base1, c_base2, c_base3 = st.columns(3)
    with c_base1:
        st.info(
            f"**Technical Mastery**: {tech_pct * 100:.1f}%\n\n"
            f"*GBBO Champion Benchmark: {float(baselines.get('winner_avg_tech_pct', 0.601)) * 100:.1f}%*"
        )
    with c_base2:
        st.info(
            f"**Star Baker Accolades**: {star_bakers}\n\n"
            f"*GBBO Champion Benchmark: {float(baselines.get('winner_avg_star_bakers', 1.88)):.2f} titles*"
        )
    with c_base3:
        st.info(
            f"**Hollywood Handshakes**: {handshakes}\n\n"
            f"*GBBO Champion Benchmark: {float(baselines.get('winner_avg_handshakes', 0.81)):.2f} handshakes*"
        )

    # Synthetic diagnostics
    custom_dict: dict[str, Any] = {
        "star_baker_count": star_bakers,
        "handshake_count": handshakes,
        "avg_technical_pct": tech_pct,
        "last_star_baker": last_sb,
        "last_handshake": last_hs,
        "last_at_risk": last_ar,
        "age": age,
        "age_score": age_score,
        "episodes_competed": episodes_competed,
        "at_risk_count": at_risk,
        "did_well_count": did_well,
    }
    s_list, r_list = _compute_diagnostics(custom_dict)
    sd1, sd2 = st.columns(2)
    with sd1:
        st.markdown("##### ✅ Evaluated Strengths")
        if s_list:
            for s in s_list:
                st.success(s)
        else:
            st.info("No significant statistical advantages detected.")
    with sd2:
        st.markdown("##### ⚠️ Evaluated Risks")
        if r_list:
            for r in r_list:
                st.error(r)
        else:
            st.info("No significant statistical risk penalties detected.")
