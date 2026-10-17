#!/usr/bin/env python3
"""Backward-compatibility wrapper forwarding to gbbo_dataset.scraper."""

from gbbo_dataset.scraper import (
    clean_text,
    extract_air_dates,
    extract_bakers,
    extract_episodes_and_performances,
    extract_placements_from_matrix,
    fetch_series_html,
    find_bakers_table,
    find_elimination_matrix,
    main,
    parse_placement,
    resolve_baker_id,
    scrape_series,
)

__all__ = [
    "clean_text",
    "extract_air_dates",
    "extract_bakers",
    "extract_episodes_and_performances",
    "extract_placements_from_matrix",
    "fetch_series_html",
    "find_bakers_table",
    "find_elimination_matrix",
    "main",
    "parse_placement",
    "resolve_baker_id",
    "scrape_series",
]

if __name__ == "__main__":
    main()
