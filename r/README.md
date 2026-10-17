# gbbo

<!-- badges: start -->
[![R-universe](https://nicholaswilde.r-universe.dev/badges/gbbo)](https://nicholaswilde.r-universe.dev)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
<!-- badges: end -->

A comprehensive, tidy dataset and companion R package for the hit television series **The Great British Bake Off** (**GBBO**), broadcast as *The Great British Baking Show* in North America.

## Installation

Install the development version of **gbbo** directly from GitHub:

```r
# install.packages("remotes")
remotes::install_github("nicholaswilde/the-great-british-bake-off/r")
```

Or install via R-universe:

```r
install.packages("gbbo", repos = "https://nicholaswilde.r-universe.dev")
```

## Datasets Included

The package exports 4 clean, relational data frames:

| Dataset | Description |
| :--- | :--- |
| `seasons` | Season broadcast years, winners, hosts, judges, networks, and streaming links |
| `bakers` | Baker demographics, ages, hometowns, occupations, and overall finish placements |
| `episodes` | Episode air dates, themes, and challenge duration time limits |
| `performances` | Challenge bakes, technical ranks, Hollywood Handshakes, and results |

## Quickstart

```r
library(gbbo)
library(dplyr)
library(ggplot2)

# Inspect seasons overview
head(seasons)

# Hollywood Handshake distribution across series
performances |>
  filter(hollywood_handshake) |>
  count(episode_id, sort = TRUE)

# Star Baker frequencies
performances |>
  filter(result == "STAR_BAKER") |>
  count(baker_id, sort = TRUE)
```

## Direct Parquet / Arrow Usage

For users who prefer high-performance columnar reads without loading package `.rda` objects, read the pre-compiled Parquet tables directly using the `{arrow}` package:

```r
library(arrow)

seasons <- read_parquet("https://github.com/nicholaswilde/the-great-british-bake-off/raw/main/data/processed/seasons.parquet")
bakers <- read_parquet("https://github.com/nicholaswilde/the-great-british-bake-off/raw/main/data/processed/bakers.parquet")
```

## License

This package is licensed under the Apache License 2.0.
