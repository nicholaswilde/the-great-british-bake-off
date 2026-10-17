"""Main entrypoint for The Great British Bake Off interactive Streamlit dashboard."""

from __future__ import annotations

import streamlit as st

from gbbo_dataset.dashboard.data import load_all_datasets
from gbbo_dataset.dashboard.views.baker_profiles import render_baker_profiles
from gbbo_dataset.dashboard.views.challenge_analytics import render_challenge_analytics
from gbbo_dataset.dashboard.views.handshake_tracker import render_handshake_tracker
from gbbo_dataset.dashboard.views.overview import render_overview
from gbbo_dataset.dashboard.views.predictor_view import render_predictor_view


def main() -> None:
    """Streamlit application entrypoint."""
    st.set_page_config(
        page_title="The Great British Bake Off Dashboard",
        page_icon="🍰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar Navigation & Branding
    st.sidebar.markdown(
        "<h2 style='text-align: center; color: #cba6f7;'>🍰 GBBO Explorer</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "*The Great British Bake Off Tidy Dataset & AI Training Corpus*"
    )
    st.sidebar.divider()

    view = st.sidebar.radio(
        "Navigation",
        [
            "Series Overview",
            "Baker Profiles",
            "Challenge Analytics",
            "Hollywood Handshakes",
            "Predictions & Forecasting",
        ],
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        "**Dataset Source**:\n"
        "- [GitHub Repository](https://github.com/nicholaswilde/the-great-british-bake-off)\n"
        "- License: Apache-2.0"
    )

    # Load data
    data = load_all_datasets()

    # Route view
    if view == "Series Overview":
        render_overview(data)
    elif view == "Baker Profiles":
        render_baker_profiles(data)
    elif view == "Challenge Analytics":
        render_challenge_analytics(data)
    elif view == "Hollywood Handshakes":
        render_handshake_tracker(data)
    elif view == "Predictions & Forecasting":
        render_predictor_view(data)


if __name__ == "__main__":
    main()
