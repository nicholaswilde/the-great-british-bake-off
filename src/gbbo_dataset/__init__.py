"""The Great British Bake Off (GBBO) Dataset and AI Training Corpus."""

from gbbo_dataset.models import Baker, Episode, Performance, ResultEnum, Season
from gbbo_dataset.predictor import SeriesPredictor

__version__ = "0.1.0"
__all__ = [
    "Baker",
    "Episode",
    "Performance",
    "ResultEnum",
    "Season",
    "SeriesPredictor",
]
