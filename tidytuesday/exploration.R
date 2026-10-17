# ==============================================================================
# TidyTuesday Starter Exploration: The Great British Bake Off (GBBO)
# ==============================================================================
# Visualizing Hollywood Handshakes, Technical Challenge Rank Distributions,
# Star Baker Momentum, and Age Demographics.
#
# Packages required:
#   install.packages(c("tidyverse", "scales"))
# ==============================================================================

library(tidyverse)
library(scales)

# ------------------------------------------------------------------------------
# 1. Load Datasets
# ------------------------------------------------------------------------------
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-great-british-bake-off/main/data/processed/"

load_gbbo_table <- function(filename) {
  local_path <- file.path("data", "processed", filename)
  if (file.exists(local_path)) {
    read_csv(local_path, show_col_types = FALSE)
  } else {
    read_csv(paste0(base_url, filename), show_col_types = FALSE)
  }
}

seasons      <- load_gbbo_table("seasons.csv")
bakers       <- load_gbbo_table("bakers.csv")
episodes     <- load_gbbo_table("episodes.csv")
performances <- load_gbbo_table("performances.csv")

# ------------------------------------------------------------------------------
# 2. Exploration 1: The Hollywood Handshake Era
# ------------------------------------------------------------------------------
# How frequently has Paul Hollywood awarded handshakes across series?
performances_with_series <- performances |>
  mutate(series_number = as.integer(str_extract(episode_id, "(?<=s)\\d+")))

handshakes_per_series <- performances_with_series |>
  filter(hollywood_handshake == TRUE) |>
  count(series_number, name = "handshakes")

plot_handshakes <- handshakes_per_series |>
  ggplot(aes(x = factor(series_number), y = handshakes)) +
  geom_col(fill = "#D35400", width = 0.7) +
  geom_text(aes(label = handshakes), vjust = -0.5, fontface = "bold") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = "The Rise of the Hollywood Handshake",
    subtitle = "Number of handshakes awarded by Paul Hollywood per series",
    x = "GBBO Series",
    y = "Handshakes Awarded",
    caption = "Source: The Great British Bake Off Tidy Dataset (github.com/nicholaswilde/the-great-british-bake-off)"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    plot.title = element_text(face = "bold", size = 16),
    panel.grid.minor = element_blank()
  )

# ------------------------------------------------------------------------------
# 3. Exploration 2: Technical Challenge Percentile Rank vs. Final Placement
# ------------------------------------------------------------------------------
# Do series champions consistently excel at blind technical challenges?
baker_tech <- performances |>
  filter(!is.na(technical_rank)) |>
  group_by(episode_id) |>
  mutate(
    max_rank = max(technical_rank, na.rm = TRUE),
    tech_percentile = if_else(max_rank > 1, (max_rank - technical_rank) / (max_rank - 1), 1.0)
  ) |>
  ungroup() |>
  group_by(baker_id) |>
  summarise(
    avg_tech_percentile = mean(tech_percentile, na.rm = TRUE),
    n_challenges = n(),
    .groups = "drop"
  ) |>
  inner_join(bakers, by = "baker_id") |>
  mutate(
    placement_group = case_when(
      overall_placement == 1 ~ "Winner (1st)",
      overall_placement %in% c(2, 3) ~ "Runner-Up (2nd-3rd)",
      overall_placement %in% c(4, 5, 6) ~ "Middle Pack (4th-6th)",
      TRUE ~ "Early Elimination (7th+)"
    ),
    placement_group = factor(
      placement_group,
      levels = c("Winner (1st)", "Runner-Up (2nd-3rd)", "Middle Pack (4th-6th)", "Early Elimination (7th+)")
    )
  )

plot_tech <- baker_tech |>
  ggplot(aes(x = placement_group, y = avg_tech_percentile, fill = placement_group)) +
  geom_boxplot(alpha = 0.7, outlier.shape = 21, outlier.fill = "white") +
  scale_y_continuous(labels = percent_format()) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Technical Challenge Mastery by Final Tournament Placement",
    subtitle = "Average technical challenge percentile rank (100% = 1st place in all technicals)",
    x = NULL,
    y = "Average Technical Percentile",
    caption = "Source: The Great British Bake Off Tidy Dataset"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    legend.position = "none",
    plot.title = element_text(face = "bold", size = 16)
  )

# ------------------------------------------------------------------------------
# 4. Exploration 3: Multi-Time Star Baker Legends
# ------------------------------------------------------------------------------
star_baker_leaders <- performances |>
  filter(result == "STAR_BAKER") |>
  count(baker_id, name = "star_bakers") |>
  filter(star_bakers >= 3) |>
  inner_join(bakers, by = "baker_id") |>
  mutate(name = fct_reorder(paste0(name, " (S", series_number, ")"), star_bakers))

plot_star_bakers <- star_baker_leaders |>
  ggplot(aes(x = star_bakers, y = name, fill = factor(overall_placement == 1))) +
  geom_col(width = 0.6) +
  scale_fill_manual(
    values = c("TRUE" = "#27AE60", "FALSE" = "#2980B9"),
    labels = c("TRUE" = "Series Winner", "FALSE" = "Finalist / Runner-Up")
  ) +
  labs(
    title = "Most Dominant Contestants in Bake Off History",
    subtitle = "Bakers who earned 3 or more Star Baker titles in a single series",
    x = "Star Baker Titles Won",
    y = NULL,
    fill = "Final Result",
    caption = "Source: The Great British Bake Off Tidy Dataset"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    plot.title = element_text(face = "bold", size = 16),
    legend.position = "bottom"
  )

message("Starter plots configured successfully. Run interactive session or ggsave() to view.")
