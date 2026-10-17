#!/usr/bin/env python3
"""Backward-compatibility wrapper forwarding to gbbo_dataset.gap_auditor."""

from gbbo_dataset.gap_auditor import (
    ColumnGap,
    DatasetGapAuditor,
    main,
)

__all__ = [
    "ColumnGap",
    "DatasetGapAuditor",
    "main",
]

if __name__ == "__main__":
    main()
