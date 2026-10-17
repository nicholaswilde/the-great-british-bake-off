---
name: gbbo-predict
description: >-
  Run empirical predictive engine to forecast Star Baker candidates, elimination risks, and series winner trajectories for in-progress GBBO series.
---

# GBBO Empirical Predictive Modeling Engine Guide

This skill guides running and updating the data-driven forecasting engine for The Great British Bake Off. It calculates real-time probabilities for upcoming Star Bakers, weekly elimination risks, and overall series winning trajectories for in-progress series (such as Series 17).

## Execution Commands

### 1. Run Predictions for In-Progress Series

```bash
task predict
# Or directly via CLI:
uv run gbbo predict
# Or via script shim:
uv run python scripts/predict.py
```

### 2. Update Documentation and Snapshots

Update `docs/predictions.md`, `README.md`, and generate episode historical snapshots in `data/predictions/`:

```bash
task predict:update
# Or directly via CLI:
uv run gbbo predict --update-docs
```

### 3. Advanced Options

```bash
# Predict specific series (e.g. Series 17) with detailed factor breakdown
uv run gbbo predict --series 17 --detail

# Limit top displayed rankings
uv run gbbo predict --series 17 --top 5

# Export prediction results to custom JSON file
uv run gbbo predict --series 17 --output data/predictions/series_17/latest.json
```

## Model Factors & Baselines

Calibrated across 16 historical GBBO series (16 winners, 200+ bakers):
1. **Cumulative Technical Percentile (30%)**: Normalized ranking across challenges ($P_{tech} = \frac{N - r}{N - 1}$).
2. **Recent Technical Form (25%)**: Performance in immediately preceding episode.
3. **Star Baker Momentum & Callouts (20%)**: Historical awards and judging callouts (`did_well` vs `at_risk`).
4. **Hollywood Handshakes (15%)**: Rare high-recognition momentum indicators.
5. **Peak Winner Age (5%)**: Gaussian likelihood centered at $32.5 \pm 9.9$ years.
