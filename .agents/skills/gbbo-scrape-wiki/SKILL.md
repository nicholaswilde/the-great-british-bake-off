---
name: gbbo-scrape-wiki
description: >-
  Use this skill to scrape and extract The Great British Bake Off (GBBO) series summaries, baker
  demographics, episode themes, challenge bakes, technical rankings, star bakers, and eliminations from Wikipedia.
---

# Scrape Wikipedia for The Great British Bake Off

This skill provides step-by-step instructions to scrape structured data from Wikipedia using `uv run python scripts/scrape.py` or `task scrape`.

## Usage

### 1. Scrape a Specific Series

```bash
# Using Taskfile
task scrape -- --series 1

# Or directly via uv
uv run python scripts/scrape.py --series 1
```

### 2. Scrape a Range of Series

```bash
uv run python scripts/scrape.py --start 1 --end 15
```

## Raw Output Files

- `data/raw/series_{series}_bakers.json`
- `data/raw/series_{series}_episodes.json`
- `data/raw/series_{series}_performances.json`

## Next Steps

After scraping, build the validated tidy datasets using `task build` (or the `gbbo-dataset-builder` skill).
