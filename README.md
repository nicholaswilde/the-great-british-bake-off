# :cake: The Great British Bake Off Dataset & AI Training Corpus :pie:

[![Task](https://img.shields.io/badge/Task-Enabled-brightgreen?style=for-the-badge&logo=task&logoColor=white)](https://taskfile.dev/#/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Managed-purple?style=for-the-badge&logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge&logo=apache)](LICENSE)

A comprehensive tidy dataset and AI training corpus for the television series **[The Great British Bake Off](https://en.wikipedia.org/wiki/The_Great_British_Bake_Off)** (**GBBO**), broadcast as *The Great British Baking Show* in North America.

> [!WARNING]
> This project is currently in a `v0.X.X` development stage. Features and configurations are subject to change, and breaking changes may be introduced at any time.

---

## :sparkles: Features

- **Tidy Relational Tables:** Master tables for `seasons`, `bakers`, `episodes`, and `performances` validated against Pydantic schemas.
- **Rich Demographics & Metadata:** Enriched with headshot photos, age, hometown, occupation, challenge timings, and Hollywood Handshakes.
- **Multi-Format Serialization:** Exportable to JSON, CSV, Apache Parquet, Apache Arrow IPC, unified SQLite (`gbbo.db`), and native R formats (`.rds`, `.rda`).
- **AI Training Corpora:** Pre-formatted conversational instruction tuning datasets (Chat SFT JSONL), RAG knowledge corpus, and evaluation benchmark suite.
- **Empirical Predictive Modeling:** Data-driven probabilistic forecasts for weekly Star Baker contenders, elimination risks, and overall series winners calibrated across 16 historical series.
- **Interactive Web Dashboard:** Streamlit application for exploratory data analysis, contestant trajectory tracking, and challenge analytics.

---

## :hammer_and_wrench: Tech Stack

- **Language:** Python 3.12+
- **Dependency Management:** [`uv`](https://docs.astral.sh/uv/)
- **Task Runner:** [`go-task`](https://taskfile.dev/) (`Taskfile.yml`)
- **Libraries:** `beautifulsoup4`, `lxml`, `pandas`, `pydantic`, `pyarrow`, `requests`, `rich`, `streamlit`, `typer`
- **Data Formats:** JSON, CSV, Parquet, Arrow IPC, SQLite, RDS/RDA

---

## :file_folder: Project Structure

```text
the-great-british-bake-off/
├── .agents/
│   ├── rules/          # Workspace rules (RTK, Serena, GBBO terminology, etc.)
│   └── skills/         # Workspace skills (gbbo-scrape-wiki, gbbo-dataset-builder, gbbo-predict, etc.)
├── data/
│   ├── raw/            # Scraped Wikipedia series JSON files
│   ├── processed/      # Validated master datasets (bakers, episodes, performances, seasons)
│   └── predictions/    # Weekly series forecasting snapshots
├── src/
│   └── gbbo_dataset/   # Core Python library and Typer CLI (gbbo)
│       ├── models.py       # Pydantic schemas (Baker, Episode, Performance, Season)
│       ├── scraper.py      # Wikipedia extraction and cleaner
│       ├── builder.py      # Data aggregation, validation, and export
│       ├── predictor.py    # Empirical predictive modeling engine
│       ├── gap_auditor.py  # Completeness and null rate auditor
│       ├── exports.py      # Multi-format serialization & AI corpora exports
│       ├── importers/      # External dataset integrations (RayofData)
│       └── cli.py          # Unified CLI dispatcher (gbbo)
├── notebooks/          # Exploratory Jupyter starter notebooks
├── tidytuesday/        # R4DS TidyTuesday data cleaning & exploration kit
├── scripts/            # Backward-compatible script shims
├── tests/              # Pytest test suite
├── docs/               # Data dictionary, gap reports, and predictions ledger
├── AGENTS.md           # Agent operating instructions
├── pyproject.toml      # Managed by uv
├── Taskfile.yml        # Task automation definitions
├── _typos.toml         # Spellchecker configuration
├── CITATION.cff        # Citation File Format specification
├── .zenodo.json        # Zenodo archival DOI configuration
└── README.md
```

---

## :rocket: Quick Start

### 1. Setup Environment

```bash
task setup
```

### 2. Scrape Wikipedia Data

```bash
# Scrape Series 1
task scrape -- --series 1

# Or directly via CLI
uv run gbbo scrape --series 1

# Scrape multiple series (1 to 17)
uv run gbbo scrape --start 1 --end 17
```

### 3. Build & Validate Datasets

```bash
task build
# Or via CLI
uv run gbbo build
```

Compiles raw files in `data/raw/` into validated tidy tables in `data/processed/`:
- `bakers.json` & `bakers.csv`
- `episodes.json` & `episodes.csv`
- `performances.json` & `performances.csv`

### 4. Enrich Dataset (Demographics, Handshakes, Streaming)

```bash
task enrich:ray
# Or via CLI
uv run gbbo enrich
```

### 5. Run Empirical Predictive Engine

```bash
# Run real-time predictions for in-progress series (Series 17)
task predict

# Update predictions documentation and ledger snapshots
task predict:update
# Or via CLI
uv run gbbo predict --update-docs
```

### 6. Inspect Dataset Stats & Gaps

```bash
# Row count statistics
task stats

# Completeness & gap audit
task gaps
task gaps:detail
task gaps:report
```

### 7. Export Multi-Format Datasets & AI Corpora

```bash
# Export all formats (SQLite, Arrow IPC, Parquet, R, AI corpora)
task export:all

# Or individual formats:
task export:sqlite
task export:arrow
task export:r
task export:ai
```

### 8. Interactive Streamlit Dashboard

```bash
task dashboard
```

### 9. Run Quality Checks & Tests

```bash
# Run pytest test suite
task test

# Run complete verification suite (formatting, linting, spellcheck, tests)
task check
```

---

## :card_index_dividers: Data Schemas

### Season
- `series_number` (int): Series number (1–17+)
- `year` (int): Broadcast year
- `winner` (str): Series winner name
- `hosts` (list[str]): Series hosts
- `judges` (list[str]): Series judges
- `network` (str): Original UK broadcaster (BBC Two, BBC One, Channel 4)
- `pbs_season` (int | None): US PBS season number
- `netflix_collection` (int | None): US Netflix collection number
- `roku_season` (int | None): US Roku Channel season number
- `location` (str | None): Primary filming location

### Baker
- `baker_id` (str): Primary key, format `s{series_number:02d}_{first_name}` (e.g. `s01_edward`)
- `series_number` (int): Series number
- `name` (str): Full name
- `age` (int): Age during series
- `gender` (str | None): Baker gender (`M`, `F`, `NB`)
- `occupation` (str): Occupation
- `hometown` (str): Hometown
- `overall_placement` (int): Final placement rank (1 = Winner)
- `image_url` (str | None): Official headshot photograph URL

### Episode
- `episode_id` (str): Primary key, format `s{series:02d}e{episode:02d}` (e.g. `s01e01`)
- `series_number` (int): Series number
- `episode_number` (int): Episode number within series
- `theme` (str): Episode theme (e.g. "Cake Week")
- `air_date` (str): Broadcast air date (YYYY-MM-DD)
- `signature_time_min` (int | None): Signature challenge time limit in minutes
- `technical_time_min` (int | None): Technical challenge time limit in minutes
- `showstopper_time_min` (int | None): Showstopper challenge time limit in minutes

### Performance
- `performance_id` (str): Primary key, format `s{series}e{episode}_{baker_id}`
- `baker_id` (str): Foreign key to Baker
- `episode_id` (str): Foreign key to Episode
- `signature_dish` (str | None): Signature challenge bake
- `technical_rank` (int | None): Rank in technical challenge
- `showstopper_dish` (str | None): Showstopper challenge bake
- `result` (str): `SAFE`, `STAR_BAKER`, `ELIMINATED`, `WINNER`, `RUNNER_UP`, `WITHDREW`
- `hollywood_handshake` (bool): Whether baker received a Hollywood Handshake
- `did_well` (bool): Whether baker was called out as doing well in the episode
- `at_risk` (bool): Whether baker was in the bottom / at risk of elimination
- `absent` (bool): Whether baker was absent from episode due to illness

> [!NOTE]
> **Comprehensive Documentation**: See the [Data Dictionary & Relational Schema](docs/data_dictionary.md) for full column specifications, data types, nullability, primary/foreign keys, and Entity-Relationship diagrams across all 4 tables.
>
> **Exploratory Notebook**: Check out [`notebooks/gbbo_exploration.ipynb`](notebooks/gbbo_exploration.ipynb) for a starter Jupyter notebook covering statistical analysis, Hollywood Handshake frequencies, technical rank correlations, and SQL querying.
>
> **TidyTuesday Community Kit**: See [`tidytuesday/`](tidytuesday/) for R data cleaning scripts, exploratory visualizations, and submission templates.

---

## :crystal_ball: Empirical Series Predictions

<!-- GBBO_PREDICTIONS_START -->
### :trophy: Live Empirical Predictions (Series 17 - After Episode 4)

Probabilistic forecasts computed via multi-factor empirical modeling calibrated against 16 historical GBBO series. See [docs/predictions.md](docs/predictions.md) for full weekly trajectory ledgers and outcome accuracy tracking.

| Rank | Baker | Age | Avg Tech % | Handshakes | Star Bakers | Next Star Baker | Next Elim Risk | Win Prob | Finale Prob |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Tom Whittaker** | 25 | 71.1% | 0 | 2 | **26.7%** | 4.4% | **30.6%** | **87.7%** |
| 2 | **Mo Mahir** | 21 | 72.8% | 0 | 1 | **11.7%** | 8.4% | **15.7%** | **52.2%** |
| 3 | **Clara Satchell-Silva** | 24 | 55.5% | 0 | 1 | **14.4%** | 7.1% | **14.1%** | **44.9%** |
| 4 | **Moyin Odeniran** | 22 | 58.8% | 1 | 0 | **12.2%** | 8.5% | **11.0%** | **38.2%** |
| 5 | **Gabe Capes** | 32 | 84.1% | 0 | 0 | **15.6%** | 8.5% | **10.5%** | **42.0%** |
| 6 | **Elizabeth 'Connie' Lewis** | 63 | 63.6% | 0 | 0 | **8.7%** | 13.9% | **6.8%** | **29.0%** |
| 7 | **Dr. Yannis Ali** | 28 | 28.6% | 0 | 0 | **5.9%** | 23.8% | **6.3%** | **20.8%** |
| 8 | **Gary Harding** | 67 | 30.2% | 0 | 0 | **4.9%** | 25.4% | **5.1%** | **18.3%** |

> [!NOTE]
> Predictions update automatically after each broadcast episode via `task predict:update` or `uv run gbbo predict --update-docs`. See [docs/predictions.md](docs/predictions.md) for all historical episode snapshots.
<!-- GBBO_PREDICTIONS_END -->

---

## :clap: Acknowledgments & Credits

Special credit and gratitude to:
- **[RayofData](https://github.com/RayofData)** for the [The-Great-British-Bake-Off-Dashboard](https://github.com/RayofData/The-Great-British-Bake-Off-Dashboard) repository and data curation (based on the Tableau Public sample dataset). This project utilizes its curated metadata to enrich baker demographics (gender, headshot image URLs), confirm Hollywood Handshake occurrences, challenge duration times, and streaming distribution mappings across Seasons 1–14.
- **Wikipedia contributors** for comprehensive season broadcast summaries, challenge tables, and BARB viewing figures.

---

## :handshake: Contributing

Contributions, bug reports, and suggestions are welcome! Please open an issue or pull request.

---

## :bookmark: Citation

If you use this dataset, companion R package, or AI training corpus in your research or coursework, please cite it as:

```bibtex
@misc{wilde_gbbo_2026,
  author       = {Nicholas Wilde},
  title        = {The Great British Bake Off Dataset & AI Training Corpus},
  year         = {2026},
  version      = {0.1.0},
  url          = {https://github.com/nicholaswilde/the-great-british-bake-off}
}
```

Or see [`CITATION.cff`](CITATION.cff) and [`.zenodo.json`](.zenodo.json).

---

## :balance_scale: License

​[Apache License 2.0](LICENSE)

## :writing_hand: Author

​This project was started in 2026 by [Nicholas Wilde][2].

[2]: <https://github.com/nicholaswilde/>
