"""Dashboard views for The Great British Bake Off explorer."""

from __future__ import annotations

from gbbo_dataset.dashboard.views.baker_profiles import render_baker_profiles
from gbbo_dataset.dashboard.views.challenge_analytics import render_challenge_analytics
from gbbo_dataset.dashboard.views.handshake_tracker import render_handshake_tracker
from gbbo_dataset.dashboard.views.overview import render_overview
from gbbo_dataset.dashboard.views.predictor_view import render_predictor_view

__all__ = [
    "render_baker_profiles",
    "render_challenge_analytics",
    "render_handshake_tracker",
    "render_overview",
    "render_predictor_view",
]
