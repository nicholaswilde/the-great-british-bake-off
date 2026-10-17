- [x] This dataset has not already been used in TidyTuesday.
- [x] The dataset will (probably) be less than 20MB when saved as a tidy CSV.
- [x] I can imagine a data visualization related to this dataset.

- [x] **title:** The Great British Bake Off (Series 1–17)
- [x] **article:** An example of the dataset being used, such as a blog post or a README about the dataset.
  - [x] **title:** The Great British Bake Off Tidy Dataset & AI Training Corpus
  - [x] **url:** https://github.com/nicholaswilde/the-great-british-bake-off
- [x] **data_source:** A source where the dataset can be downloaded.
  - [x] **title:** The Great British Bake Off Processed Tidy CSV Tables
  - [x] **url:** https://github.com/nicholaswilde/the-great-british-bake-off/tree/main/data/processed
- [x] **images:** One or more images related to the dataset.
  - [x] **file:** https://raw.githubusercontent.com/nicholaswilde/the-great-british-bake-off/main/docs/predictions.md
  - [x] **alt:** Multi-factor empirical predictions ledger and historical accuracy tracking for The Great British Bake Off.

- [x] **cleaning_script:** A script to fetch and clean the data, resulting in one or more data.frames that can be saved as CSVs.

```r
library(tidyverse)

# Base URL for processed data in GitHub repository
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-great-british-bake-off/main/data/processed/"

# 1. Seasons summary
seasons <- read_csv(paste0(base_url, "seasons.csv"), show_col_types = FALSE) |>
  mutate(
    series_number = as.integer(series_number),
    year = as.integer(year),
    winner = as.character(winner),
    network = as.character(network),
    pbs_season = as.integer(pbs_season),
    netflix_collection = as.integer(netflix_collection),
    roku_season = as.integer(roku_season)
  )

# 2. Bakers demographics
bakers <- read_csv(paste0(base_url, "bakers.csv"), show_col_types = FALSE) |>
  mutate(
    series_number = as.integer(series_number),
    name = as.character(name),
    age = as.integer(age),
    gender = as.character(gender),
    overall_placement = as.integer(overall_placement)
  )

# 3. Episodes schedule and challenge limits
episodes <- read_csv(paste0(base_url, "episodes.csv"), show_col_types = FALSE) |>
  mutate(
    series_number = as.integer(series_number),
    episode_number = as.integer(episode_number),
    air_date = as.Date(air_date),
    signature_time_min = as.integer(signature_time_min),
    technical_time_min = as.integer(technical_time_min),
    showstopper_time_min = as.integer(showstopper_time_min)
  )

# 4. Challenge performances and judging outcomes
performances <- read_csv(paste0(base_url, "performances.csv"), show_col_types = FALSE) |>
  mutate(
    technical_rank = as.integer(technical_rank),
    result = as.character(result),
    hollywood_handshake = as.logical(replace_na(hollywood_handshake, FALSE)),
    did_well = as.logical(replace_na(did_well, FALSE)),
    at_risk = as.logical(replace_na(at_risk, FALSE)),
    absent = as.logical(replace_na(absent, FALSE))
  )
```

- [x] **data_dictionary:** A data dictionary for each table included in the dataset.

### `seasons.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `series_number` | integer | Series sequence number (1–17) |
| `year` | integer | Broadcast year |
| `winner` | character | Name of series champion |
| `hosts` | character | Series hosts |
| `judges` | character | Series judges |
| `network` | character | Broadcaster (BBC Two, BBC One, Channel 4) |
| `pbs_season` | integer | US PBS season number |
| `netflix_collection` | integer | US Netflix collection number |
| `roku_season` | integer | US Roku Channel season number |
| `location` | character | Filming location / estate |

### `bakers.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `baker_id` | character | Unique ID: `s{series:02d}_{first_name}` |
| `series_number` | integer | Series number |
| `name` | character | Full name |
| `age` | integer | Age during filming |
| `gender` | character | Gender identity (`M`, `F`, `NB`) |
| `occupation` | character | Occupation / profession |
| `hometown` | character | Hometown / residence |
| `overall_placement` | integer | Final placement rank (1 = Winner) |
| `image_url` | character | Headshot photo URL |

### `episodes.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `episode_id` | character | Unique ID: `s{series:02d}e{episode:02d}` |
| `series_number` | integer | Series number |
| `episode_number` | integer | Episode sequence index |
| `theme` | character | Weekly baking theme |
| `air_date` | date | Original UK broadcast date |
| `signature_time_min` | integer | Signature challenge time limit in minutes |
| `technical_time_min` | integer | Technical challenge time limit in minutes |
| `showstopper_time_min` | integer | Showstopper challenge time limit in minutes |

### `performances.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `performance_id` | character | Unique ID: `{episode_id}_{baker_id}` |
| `baker_id` | character | Foreign key reference to `bakers` |
| `episode_id` | character | Foreign key reference to `episodes` |
| `signature_dish` | character | Title/description of Signature challenge bake |
| `technical_rank` | integer | Finishing rank in blind Technical challenge (1 = best) |
| `showstopper_dish` | character | Title/description of Showstopper challenge bake |
| `result` | character | Episode outcome (`SAFE`, `STAR_BAKER`, `ELIMINATED`, `WINNER`, etc.) |
| `hollywood_handshake` | logical | Whether baker received a Hollywood Handshake |
| `did_well` | logical | Whether baker was called out as doing well |
| `at_risk` | logical | Whether baker was called out as in the bottom |
| `absent` | logical | Whether baker was absent from episode due to illness |
