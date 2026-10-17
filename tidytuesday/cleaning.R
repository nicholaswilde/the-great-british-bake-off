# ------------------------------------------------------------------------------
# TidyTuesday: The Great British Bake Off (Series 1–17)
# Data Cleaning & Preparation Script
# ------------------------------------------------------------------------------
# This script loads, validates, and cleans the relational tidy tables comprising
# The Great British Bake Off dataset for R4DS TidyTuesday.
# ------------------------------------------------------------------------------

library(tidyverse)

# Base raw repository URL
base_raw_url <- "https://raw.githubusercontent.com/nicholaswilde/the-great-british-bake-off/main/data/processed/"

# Helper to load either from local directory if available, or fall back to GitHub raw
load_table <- function(name) {
  local_path <- file.path("data", "processed", paste0(name, ".csv"))
  if (file.exists(local_path)) {
    message("Loading local: ", local_path)
    read_csv(local_path, show_col_types = FALSE)
  } else {
    remote_url <- paste0(base_raw_url, name, ".csv")
    message("Fetching remote: ", remote_url)
    read_csv(remote_url, show_col_types = FALSE)
  }
}

# 1. Load Raw Tables
message("--- Loading raw tables ---")
raw_seasons      <- load_table("seasons")
raw_bakers       <- load_table("bakers")
raw_episodes     <- load_table("episodes")
raw_performances <- load_table("performances")

# 2. Clean Seasons Table
message("--- Cleaning seasons ---")
seasons <- raw_seasons |>
  mutate(
    series_number = as.integer(series_number),
    year = as.integer(year),
    winner = as.character(winner),
    network = as.character(network),
    pbs_season = as.integer(pbs_season),
    netflix_collection = as.integer(netflix_collection),
    roku_season = as.integer(roku_season),
    location = as.character(location)
  ) |>
  arrange(series_number)

# 3. Clean Bakers Table
message("--- Cleaning bakers ---")
bakers <- raw_bakers |>
  mutate(
    baker_id = as.character(baker_id),
    series_number = as.integer(series_number),
    name = as.character(name),
    age = as.integer(age),
    gender = as.character(gender),
    occupation = as.character(occupation),
    hometown = as.character(hometown),
    overall_placement = as.integer(overall_placement)
  ) |>
  arrange(series_number, overall_placement, name)

# 4. Clean Episodes Table
message("--- Cleaning episodes ---")
episodes <- raw_episodes |>
  mutate(
    episode_id = as.character(episode_id),
    series_number = as.integer(series_number),
    episode_number = as.integer(episode_number),
    theme = as.character(theme),
    air_date = as.Date(air_date),
    signature_time_min = as.integer(signature_time_min),
    technical_time_min = as.integer(technical_time_min),
    showstopper_time_min = as.integer(showstopper_time_min)
  ) |>
  arrange(series_number, episode_number)

# 5. Clean Performances Table
message("--- Cleaning performances ---")
performances <- raw_performances |>
  mutate(
    performance_id = as.character(performance_id),
    baker_id = as.character(baker_id),
    episode_id = as.character(episode_id),
    signature_dish = as.character(signature_dish),
    technical_rank = as.integer(technical_rank),
    showstopper_dish = as.character(showstopper_dish),
    result = as.character(result),
    hollywood_handshake = as.logical(replace_na(hollywood_handshake, FALSE)),
    did_well = as.logical(replace_na(did_well, FALSE)),
    at_risk = as.logical(replace_na(at_risk, FALSE)),
    absent = as.logical(replace_na(absent, FALSE))
  )

message("--- Cleaned dataset summary ---")
message("Seasons:      ", nrow(seasons))
message("Bakers:       ", nrow(bakers))
message("Episodes:     ", nrow(episodes))
message("Performances: ", nrow(performances))
