"""Backward-compatibility module forwarding to gbbo_dataset.models."""

from gbbo_dataset.models import (
    Baker,
    Episode,
    Performance,
    ResultEnum,
    Season,
)

__all__ = [
    "Baker",
    "Episode",
    "Performance",
    "ResultEnum",
    "Season",
]
