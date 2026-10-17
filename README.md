# The Great British Bake Off Dataset

A comprehensive tidy dataset and AI training corpus for the television series **The Great British Bake Off** (**GBBO**), broadcast as *The Great British Baking Show* in North America.

## Tech Stack
* **Language:** Python 3.12+
* **Dependency Management:** [`uv`](https://docs.astral.sh/uv/)
* **Task Runner:** [`go-task`](https://taskfile.dev/) (`Taskfile.yml`)
* **Libraries:** `beautifulsoup4`, `lxml`, `pandas`, `pydantic`, `requests`
* **Data Formats:** JSON and CSV (in `data/processed/`)

## Project Structure
```text
the-great-british-bake-off/
├── .agents/
│   ├── rules/          # Workspace rules (RTK, Serena, GBBO terminology, etc.)
│   └── skills/         # Workspace skills (gbbo-scrape-wiki, gbbo-dataset-builder, etc.)
├── data/
│   ├── raw/            # Scraped Wikipedia series JSON files
│   └── processed/      # Validated master datasets (bakers, episodes, performances, seasons)
├── src/
│   └── gbbo_dataset/   # Core Python library and Typer CLI (gbbo)
│       ├── models.py       # Pydantic schemas (Baker, Episode, Performance, Season)
│       ├── scraper.py      # Wikipedia extraction and cleaner
│       ├── builder.py      # Data aggregation, validation, and export
│       ├── gap_auditor.py  # Completeness and null rate auditor
│       ├── importers/      # External dataset integrations (RayofData)
│       └── cli.py          # Unified CLI dispatcher (gbbo)
├── scripts/            # Backward-compatible script shims
├── tests/              # Pytest test suite
├── AGENTS.md           # Agent operating instructions
├── pyproject.toml      # Managed by uv
├── Taskfile.yml        # Task automation definitions
├── _typos.toml         # Spellchecker configuration
└── README.md
```

## Quick Start

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

# Or scrape multiple series
uv run gbbo scrape --start 1 --end 17
```

### 3. Build & Validate Datasets
```bash
task build
# Or via CLI
uv run gbbo build
```

This compiles raw files in `data/raw/` into validated tidy tables in `data/processed/`:
- `bakers.json` & `bakers.csv`
- `episodes.json` & `episodes.csv`
- `performances.json` & `performances.csv`

### 4. Enrich Dataset (Demographics, Handshakes, Streaming)
```bash
task enrich:ray
# Or via CLI
uv run gbbo enrich
```

### 5. Inspect Dataset Stats
```bash
task stats
# Or via CLI
uv run gbbo stats
```

### 6. Run Quality Checks & Tests
```bash
# Run pytest test suite
task test

# Run complete quality suite (formatting, linting, spellcheck, tests)
task check
```

## Data Schemas

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

---

## :clap: Acknowledgments & Credits

Special credit and gratitude to:
- **[RayofData](https://github.com/RayofData)** for the [The-Great-British-Bake-Off-Dashboard](https://github.com/RayofData/The-Great-British-Bake-Off-Dashboard) repository and data curation (based on the Tableau Public sample dataset). This project utilizes its curated metadata to enrich baker demographics (gender, headshot image URLs), confirm Hollywood Handshake occurrences, challenge duration times, and streaming distribution mappings across Seasons 1–14.
- **Wikipedia contributors** for comprehensive season broadcast summaries, challenge tables, and BARB viewing figures.

---

## :balance_scale: License

[Apache License 2.0](LICENSE)

## :writing_hand: Author

This project was started in 2026 by [Nicholas Wilde](https://github.com/nicholaswilde/).
