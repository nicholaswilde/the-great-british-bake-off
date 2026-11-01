---
name: gbbo-ingest
description: >-
  Automates checking for new broadcast episodes and series of The Great British Bake Off,
  executing the data pipeline, updating empirical predictions, and opening pull requests.
---

# Ingest and Track The Great British Bake Off Broadcast Series

This skill automates checking for newly aired episodes, scraping fresh broadcast data from Wikipedia, executing the data compilation pipeline, updating predictions, and opening a Pull Request or committing changes.

## Protocol & Workflows

### 1. Check for New Broadcast Episodes or Series (Lightweight)

Check if new episode or series data is available without executing the full build pipeline:

```bash
task ingest:check
# Or directly via script:
./scripts/schedule_ingest.py --check-only
```

### 2. Run Scheduled Ingestion & Pipeline Sync

To fetch new episodes, execute the compilation pipeline, update empirical forecasts, and open a Pull Request:

```bash
task ingest:run
# Or with explicit arguments:
./scripts/schedule_ingest.py --series <N> --open-pr
```

### 3. Force Re-ingestion for In-Progress Series

To force re-scraping and rebuilding regardless of cache status:

```bash
./scripts/schedule_ingest.py --force --series <N>
```

### 4. Manual Series Ingestion Steps

If running individual steps manually:

1. **Scrape Wikipedia & Multi-source Data**:
   ```bash
   uv run gbbo scrape --series <N>
   uv run gbbo scrape-fandom --series <N>
   uv run gbbo scrape-reddit --series <N>
   ```

2. **Rebuild Pipeline Tables**:
   ```bash
   task pipeline
   # Or directly via CLI:
   uv run gbbo build
   task export:all
   ```

3. **Update Empirical Predictions**:
   ```bash
   task predict:update
   # Or directly via CLI:
   uv run gbbo predict --update-docs
   ```

4. **Verify Relational & Schema Integrity**:
   ```bash
   task check
   ```
