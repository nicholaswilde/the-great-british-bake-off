---
name: gbbo-dataset-builder
description: >-
  Use this skill to aggregate, validate through Pydantic schemas, and export raw GBBO series files
  into master JSON and CSV tidy tables in data/processed/.
---

# Build & Validate GBBO Datasets

This skill compiles raw scraped files in `data/raw/` into validated tidy datasets using `task build` or `uv run python scripts/build.py`.

## Usage

```bash
# Using Taskfile
task build

# Or directly via uv
uv run python scripts/build.py
```

## Validation & Export

The builder validates each record against Pydantic models in `scripts/models.py`:
- `Baker`: `baker_id`, `series_number`, `name`, `age`, `occupation`, `hometown`, `overall_placement`.
- `Episode`: `episode_id`, `series_number`, `episode_number`, `theme`, `air_date`.
- `Performance`: `performance_id`, `baker_id`, `episode_id`, `signature_dish`, `technical_rank`, `showstopper_dish`, `result`, `hollywood_handshake`.

## Output Files

Master tidy tables in `data/processed/`:
- `bakers.json` and `bakers.csv`
- `episodes.json` and `episodes.csv`
- `performances.json` and `performances.csv`

## Verification

Run verification checks after building:
```bash
task check
```
