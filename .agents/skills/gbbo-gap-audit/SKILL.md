---
name: gbbo-gap-audit
description: >-
  Audit dataset completeness, calculate missing cell rates, and backfill broadcast ratings or demographic gaps.
---

# Dataset Gap Auditor & Backfill Guide

This skill audits missing cells, null rates, and incomplete fields across all processed tables in The Great British Bake Off dataset, and guides backfilling broadcast air dates, ratings, and challenge gaps.

## Auditing Commands

### 1. High-Level Dataset Gap Summary

```bash
task gaps
# Or directly via python:
uv run python scripts/gap_auditor.py
```

### 2. Detailed Column-by-Column & Series Breakdown

```bash
task gaps:detail
# Or directly via python:
uv run python scripts/gap_auditor.py --detail
```

### 3. Filter by Specific Table or Series

```bash
# Check episode air date and theme gaps
uv run python scripts/gap_auditor.py --table episodes --detail

# Check specific series gaps
uv run python scripts/gap_auditor.py --series 1 --detail
```

### 4. Export Markdown Gap Report

Export the latest audit report to `docs/dataset_gaps.md`:

```bash
task gaps:report
# Or:
uv run python scripts/gap_auditor.py --export-md docs/dataset_gaps.md
```

## Backfill Protocol

1. **Air Dates & Viewership**:
   - Extract from the Wikipedia "Ratings" table for each series.
2. **Technical Ranks in Finals**:
   - Note conditional omissions (e.g. Series 1 Final had no technical challenge).
3. **Rebuild Dataset**:
   ```bash
   task build
   task check
   ```
