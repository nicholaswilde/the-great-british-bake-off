#!/usr/bin/env python3
"""Backward-compatibility wrapper forwarding to gbbo_dataset.predictor."""

from gbbo_dataset.predictor import (
    DEFAULT_HISTORICAL_BASELINES,
    SeriesPredictor,
    main,
)

__all__ = [
    "DEFAULT_HISTORICAL_BASELINES",
    "SeriesPredictor",
    "main",
]

if __name__ == "__main__":
    main()
