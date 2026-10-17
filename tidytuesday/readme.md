# The Great British Bake Off (Series 1–17)

Welcome to **The Great British Bake Off (GBBO)** dataset curated for the [R for Data Science (R4DS) TidyTuesday](https://github.com/rfordatascience/tidytuesday) community!

Broadcast in North America as *The Great British Baking Show*, GBBO is a beloved television competition where amateur bakers compete in weekly themed tournaments (Cake, Bread, Biscuit, Pastry, Desserts, Patisserie). In each episode, contestants tackle three distinct culinary challenges:
1. **The Signature Challenge**: A tried-and-tested personal recipe reflecting the baker's personality.
2. **The Technical Challenge**: A blind test of fundamental baking knowledge where all bakers receive identical, intentionally minimal instructions and identical ingredients, ranked from worst to best by the judges.
3. **The Showstopper Challenge**: An ambitious, visually spectacular centerpiece designed to test professional-level culinary artistry, flavor harmony, and architectural stability.

Each week, the judges award one outstanding contestant the title of **Star Baker**, while eliminating the weakest performer. In the season finale, three finalists bake across three final challenges to determine the ultimate series champion.

---

## The Data

The dataset comprises 4 clean relational tables available as tidy CSV files:

| Table | File | Description | Rows |
| :--- | :--- | :--- | :---: |
| `seasons` | `seasons.csv` | Series-level metadata, broadcast years, champions, hosts, judges, and networks | 17 |
| `bakers` | `bakers.csv` | Contestant demographic profiles, age, gender, occupation, hometown, and final placement | 204 |
| `episodes` | `episodes.csv` | Episode broadcast schedule, weekly baking themes, air dates, and challenge time limits | 158 |
| `performances` | `performances.csv` | Challenge dishes, technical ranks, Star Bakers, eliminations, and Hollywood Handshakes | 1,203 |

### How to Read the Data in R

```r
# Option 1: Load directly from GitHub raw CSV
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-great-british-bake-off/main/data/processed/"

seasons      <- readr::read_csv(paste0(base_url, "seasons.csv"))
bakers       <- readr::read_csv(paste0(base_url, "bakers.csv"))
episodes     <- readr::read_csv(paste0(base_url, "episodes.csv"))
performances <- readr::read_csv(paste0(base_url, "performances.csv"))

# Option 2: Install and load via companion R package
# remotes::install_github("nicholaswilde/the-great-british-bake-off", subdir = "r")
# library(gbbo)
# data(seasons)
# data(bakers)
# data(performances)
```

---

## Game Mechanics & Cultural Glossary

Understanding the rules and cultural nuances of the tent helps frame compelling visual and statistical hypotheses:

- **Star Baker**: Introduced in Series 2, this title honors the contestant who performed best across all three challenges in an individual episode. Multi-time Star Baker recipients frequently reach the finale, but winning the most Star Bakers does not guarantee winning the series (e.g. Richard Burr won 5 Star Bakers in Series 5, but Nancy Birtwhistle won the series).
- **The Hollywood Handshake**: An impromptu gesture of supreme approval from veteran judge Paul Hollywood. Rare in early BBC series, handshakes became an iconic television ritual during the Channel 4 era.
- **The Technical Challenge Ranking**: Scored completely blind without knowing which baker made which dish. A score of `1` indicates the top-ranked bake of the challenge.
- **Soggy Bottom**: A dreaded baking flaw in tarts, pies, and pastries where the base fails to bake through crisply.
- **The Final (Top 3)**: Each series culminates in a 3-person finale with no Star Baker awarded—only the announcement of the champion and two runners-up.

---

## Data Dictionary

### `seasons.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `series_number` | integer | Series / Season sequence number (1 to 17) |
| `year` | integer | Broadcast year |
| `winner` | character | Name of the series champion |
| `hosts` | character | Series hosts |
| `judges` | character | Series judges |
| `network` | character | UK broadcast channel (BBC Two, BBC One, Channel 4) |
| `pbs_season` | integer | US PBS season number |
| `netflix_collection` | integer | US Netflix collection number |
| `roku_season` | integer | US The Roku Channel season number |
| `location` | character | Filming location / estate |

### `bakers.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `baker_id` | character | Unique ID formatted as `s{series:02d}_{first_name}` |
| `series_number` | integer | Series number |
| `name` | character | Full name |
| `age` | integer | Baker age during series broadcast |
| `gender` | character | Gender identity (`M`, `F`, `NB`) |
| `occupation` | character | Profession / job |
| `hometown` | character | Residence / hometown |
| `latitude` | numeric | Hometown latitude coordinate (WGS84) |
| `longitude` | numeric | Hometown longitude coordinate (WGS84) |
| `country` | character | Constituent country or nation |
| `county_region` | character | County or administrative region |
| `overall_placement` | integer | Final placement rank (`1` = Winner) |
| `image_url` | character | Headshot photo URL |

### `episodes.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `episode_id` | character | Unique ID formatted as `s{series:02d}e{episode:02d}` |
| `series_number` | integer | Series number |
| `episode_number` | integer | Episode index within series |
| `theme` | character | Episode theme (e.g. "Cake Week") |
| `air_date` | date | Original UK broadcast date |
| `signature_time_min` | integer | Signature challenge duration in minutes |
| `technical_time_min` | integer | Technical challenge duration in minutes |
| `showstopper_time_min` | integer | Showstopper challenge duration in minutes |

### `performances.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `performance_id` | character | Unique ID formatted as `{episode_id}_{baker_id}` |
| `baker_id` | character | Foreign key to `bakers` |
| `episode_id` | character | Foreign key to `episodes` |
| `signature_dish` | character | Description/title of Signature challenge dish |
| `technical_rank` | integer | Finishing rank in blind Technical challenge (1 = best) |
| `showstopper_dish` | character | Description/title of Showstopper challenge dish |
| `result` | character | Episode outcome (`SAFE`, `STAR_BAKER`, `ELIMINATED`, `WINNER`, etc.) |
| `hollywood_handshake` | logical | Whether baker received a Hollywood Handshake |
| `did_well` | logical | Whether baker was called out as doing well |
| `at_risk` | logical | Whether baker was called out as in the bottom |
| `absent` | logical | Whether baker missed the episode due to illness |

---

## Starter Exploration Ideas

1. **The Handshake Inflation**: Has Paul Hollywood become more generous with Hollywood Handshakes over the years?
2. **Technical Mastery vs. Star Baker**: Does winning the blind technical challenge predict who wins Star Baker, or does the Showstopper outweigh it?
3. **Age & Placement**: Does baking experience (older age) translate to deeper tournament survival, or do younger bakers prevail?
4. **Theme Difficulty**: Which challenge themes (e.g., Bread Week, Pastry Week) produce the highest elimination turnover or bottom judging callouts?
