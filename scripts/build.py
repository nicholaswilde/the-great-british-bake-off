#!/usr/bin/env python3
"""Backward-compatibility wrapper forwarding to gbbo_dataset.builder."""

from gbbo_dataset.builder import (
    build_datasets,
    load_json,
    main,
)

__all__ = [
    "build_datasets",
    "load_json",
    "main",
]

if __name__ == "__main__":
    main()
