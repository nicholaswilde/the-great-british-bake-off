#!/usr/bin/env python3
"""Backward-compatibility wrapper forwarding to gbbo_dataset.importers.rayofdata."""

from gbbo_dataset.importers.rayofdata import (
    DEFAULT_RAY_DATA_DIR,
    RAY_BAKER_ALIASES,
    SERIES_15_BAKER_ENRICHMENT,
    SERIES_15_HANDSHAKES,
    SERIES_16_BAKER_ENRICHMENT,
    SERIES_16_HANDSHAKES,
    SERIES_17_BAKER_ENRICHMENT,
    SERIES_17_HANDSHAKES,
    build_seasons,
    enrich_bakers,
    enrich_episodes,
    enrich_performances,
    main,
    match_baker_id,
    run_enrichment,
)

__all__ = [
    "DEFAULT_RAY_DATA_DIR",
    "RAY_BAKER_ALIASES",
    "SERIES_15_BAKER_ENRICHMENT",
    "SERIES_15_HANDSHAKES",
    "SERIES_16_BAKER_ENRICHMENT",
    "SERIES_16_HANDSHAKES",
    "SERIES_17_BAKER_ENRICHMENT",
    "SERIES_17_HANDSHAKES",
    "build_seasons",
    "enrich_bakers",
    "enrich_episodes",
    "enrich_performances",
    "main",
    "match_baker_id",
    "run_enrichment",
]

if __name__ == "__main__":
    main()
