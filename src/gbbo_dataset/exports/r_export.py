"""Native R language dataset export and companion R data package scaffolding.

Exports processed The Great British Bake Off datasets into compressed .rds and .rda formats
and maintains the companion R data package structure in r/.
"""

from __future__ import annotations

import gzip
import logging
import lzma
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadr

logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "bakers",
    "episodes",
    "performances",
]

BAKER_ID_ALIASES = {
    "s01_edd": "s01_edward",
    "s02_jo": "s02_joanne",
    "s07_val": "s07_valerie",
    "s08_yan": "s08_chuenyan",
    "s12_jairzeno": "s12_jairzinho",
}

INTEGER_COLUMNS = {
    "seasons": ["series_number", "year"],
    "bakers": ["series_number", "age"],
    "episodes": ["series_number", "episode_number"],
}

BOOLEAN_COLUMNS = {
    "performances": [
        "hollywood_handshake",
        "did_well",
        "at_risk",
        "absent",
    ],
}

FLOAT_COLUMNS = {
    "seasons": ["pbs_season", "netflix_collection", "roku_season"],
    "bakers": ["overall_placement"],
    "episodes": [
        "signature_time_min",
        "technical_time_min",
        "showstopper_time_min",
    ],
    "performances": ["technical_rank"],
}

TABLE_DOCUMENTATION = {
    "seasons": {
        "title": "Seasons in The Great British Bake Off",
        "description": "Season-level metadata, broadcast years, winners, hosts, judges, networks, streaming collections, and filming locations.",
        "columns": {
            "series_number": "Series / Season number (integer)",
            "year": "Broadcast premiere year (integer)",
            "winner": "Series champion baker name",
            "hosts": "Series presenter(s) / host(s)",
            "judges": "Series judge(s)",
            "network": "Broadcasting network (e.g. BBC Two, BBC One, Channel 4)",
            "pbs_season": "PBS broadcast season number in the US",
            "netflix_collection": "Netflix Collection number in the US",
            "roku_season": "The Roku Channel season number",
            "location": "Filming tent location",
        },
    },
    "bakers": {
        "title": "Bakers in The Great British Bake Off",
        "description": "Contestant demographics, ages, hometowns, occupations, overall finish placements, and headshot URLs.",
        "columns": {
            "baker_id": "Unique alphanumeric baker identifier (format: s{series}_{first_name})",
            "series_number": "Series number (integer)",
            "name": "Full name of the baker",
            "age": "Age of the baker during series filming (integer)",
            "gender": "Gender of the baker ('M', 'F', 'NB')",
            "occupation": "Stated occupation of the baker",
            "hometown": "City and region of permanent residence",
            "latitude": "Geographic latitude coordinate of baker hometown (decimal degrees)",
            "longitude": "Geographic longitude coordinate of baker hometown (decimal degrees)",
            "country": "Constituent country or sovereign nation of baker hometown",
            "county_region": "Administrative county or geographic region of baker hometown",
            "overall_placement": "Final rank in the series (1 = Winner)",
            "image_url": "URL link to official baker headshot photo",
        },
    },
    "episodes": {
        "title": "Episodes in The Great British Bake Off",
        "description": "Episode-level broadcast metadata, themes, air dates, and challenge time limits.",
        "columns": {
            "episode_id": "Unique episode identifier (format: s{series}e{episode})",
            "series_number": "Series number (integer)",
            "episode_number": "Episode number within the series (integer)",
            "theme": "Weekly episode theme (e.g. Cake Week, Bread Week)",
            "air_date": "Original UK television broadcast date (YYYY-MM-DD)",
            "signature_time_min": "Time limit allocated for Signature challenge in minutes",
            "technical_time_min": "Time limit allocated for Technical challenge in minutes",
            "showstopper_time_min": "Time limit allocated for Showstopper challenge in minutes",
        },
    },
    "performances": {
        "title": "Baker Episode Performances in The Great British Bake Off",
        "description": "Individual baker challenge bakes, technical rankings, judges' evaluations, Hollywood Handshakes, and weekly outcomes.",
        "columns": {
            "performance_id": "Unique performance identifier (format: s{series}e{episode}_{baker_id})",
            "baker_id": "Foreign key reference to baker identifier",
            "episode_id": "Foreign key reference to episode identifier",
            "signature_dish": "Description or title of Signature challenge bake",
            "technical_rank": "Rank achieved in blind Technical challenge (1 = First Place)",
            "showstopper_dish": "Description or title of Showstopper challenge bake",
            "result": "Episode outcome ('STAR_BAKER', 'SAFE', 'ELIMINATED', 'WINNER', 'RUNNER_UP', 'WITHDREW')",
            "hollywood_handshake": "Logical flag indicating if baker received a Hollywood Handshake",
            "did_well": "Logical flag indicating if judges commended baker among top of the week",
            "at_risk": "Logical flag indicating if baker was evaluated as in the bottom / at risk",
            "absent": "Logical flag indicating if baker was absent due to illness",
        },
    },
}


def _to_ascii(text: str) -> str:
    """Normalize and transliterate text to pure ASCII for CRAN compliance."""
    if not isinstance(text, str):
        return text
    text = (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u02bb", "'")
        .replace("\u2192", "->")
    )
    decomposed = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in decomposed if not unicodedata.combining(c))
    return cleaned.encode("ascii", "ignore").decode("ascii")


def _clean_str(val: Any) -> Any:
    """Sanitize string values to ASCII while preserving None for missing entries."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) or (
        hasattr(val, "__iter__") and not isinstance(val, (str, bytes))
    ):
        val = ", ".join(str(x) for x in val)
    else:
        try:
            if pd.isna(val):
                return None
        except ValueError:
            pass
    return _to_ascii(str(val))


def _write_deterministic_rds(path: Path, df: pd.DataFrame) -> None:
    """Write an RDS file with deterministic gzip compression (mtime=0)."""
    with tempfile.NamedTemporaryFile(suffix=".rds", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        pyreadr.write_rds(tmp_path, df)
        raw_bytes = tmp_path.read_bytes()
        compressed = gzip.compress(raw_bytes, compresslevel=9, mtime=0)
        path.write_bytes(compressed)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _write_deterministic_rdata(
    path: Path, df: pd.DataFrame, df_name: str, compress: str = "xz"
) -> None:
    """Write an RDA file with deterministic xz (or gzip) compression."""
    with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        pyreadr.write_rdata(tmp_path, df, df_name=df_name)
        raw_bytes = tmp_path.read_bytes()
        if compress == "xz":
            compressed = lzma.compress(raw_bytes, preset=9)
        else:
            compressed = gzip.compress(raw_bytes, compresslevel=9, mtime=0)
        path.write_bytes(compressed)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


class RExporter:
    """Exports processed GBBO datasets into .rds and .rda files and maintains companion R package."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        r_output_dir: Path | str = "data/processed/r",
        r_pkg_dir: Path | str = "r",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.r_output_dir = Path(r_output_dir)
        self.r_pkg_dir = Path(r_pkg_dir)

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a processed table from Parquet (or fallback to CSV) and format types for R."""
        parquet_file = self.processed_dir / f"{table_name}.parquet"
        csv_file = self.processed_dir / f"{table_name}.csv"

        if parquet_file.exists():
            df = pd.read_parquet(parquet_file)
        elif csv_file.exists():
            df = pd.read_csv(csv_file)
        else:
            raise FileNotFoundError(
                f"Table '{table_name}' not found in {self.processed_dir} (.parquet or .csv)"
            )

        if table_name == "performances":
            if "baker_id" in df.columns:
                df["baker_id"] = df["baker_id"].replace(BAKER_ID_ALIASES)
            if "episode_id" in df.columns and "baker_id" in df.columns:
                df["performance_id"] = df["episode_id"] + "_" + df["baker_id"]

        # Cast integer columns to Int32 (R-compatible 32-bit nullable integer)
        int_cols = INTEGER_COLUMNS.get(table_name, [])
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int32")

        # Cast boolean columns to bool
        bool_cols = BOOLEAN_COLUMNS.get(table_name, [])
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        # Cast float columns
        float_cols = FLOAT_COLUMNS.get(table_name, [])
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

        # Ensure strings and sanitize to pure ASCII for CRAN portability
        for col in df.columns:
            if col not in int_cols and col not in bool_cols and col not in float_cols:
                df[col] = df[col].map(_clean_str)

        return df

    def export_rds(self) -> dict[str, Path]:
        """Export each processed table as a gzip-compressed .rds file."""
        self.r_output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)
            out_path = self.r_output_dir / f"{table_name}.rds"
            _write_deterministic_rds(out_path, df)
            results[table_name] = out_path
            logger.info("Exported RDS table: %s (%d rows)", out_path, len(df))

        return results

    def export_rda(self) -> dict[str, Path]:
        """Export each table as a compressed .rda file into the R package data directory."""
        pkg_data_dir = self.r_pkg_dir / "data"
        pkg_data_dir.mkdir(parents=True, exist_ok=True)
        self.r_output_dir.mkdir(parents=True, exist_ok=True)

        results: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)

            # Export to R package data directory
            pkg_out = pkg_data_dir / f"{table_name}.rda"
            _write_deterministic_rdata(pkg_out, df, df_name=table_name)

            # Mirror into data/processed/r/
            mirror_out = self.r_output_dir / f"{table_name}.rda"
            _write_deterministic_rdata(mirror_out, df, df_name=table_name)

            results[table_name] = pkg_out
            logger.info("Exported RDA table: %s (%d rows)", pkg_out, len(df))

        return results

    def generate_roxygen_docs(self) -> Path:
        """Generate R/data.R roxygen2 documentation for all datasets."""
        r_dir = self.r_pkg_dir / "R"
        r_dir.mkdir(parents=True, exist_ok=True)
        data_r_path = r_dir / "data.R"

        chunks: list[str] = [
            "# Auto-generated documentation for gbbo datasets",
            "# Generated from models.py and processed tables. Do not edit by hand.",
            "",
        ]

        for table_name in TABLES:
            doc_meta = TABLE_DOCUMENTATION.get(table_name, {})
            title = doc_meta.get(
                "title", f"{table_name.capitalize()} in The Great British Bake Off"
            )
            desc = doc_meta.get("description", f"Tidy dataset of {table_name}.")
            columns = doc_meta.get("columns", {})

            parquet_file = self.processed_dir / f"{table_name}.parquet"
            csv_file = self.processed_dir / f"{table_name}.csv"
            if parquet_file.exists():
                df = pd.read_parquet(parquet_file)
                n_rows = len(df)
                n_cols = len(df.columns)
            elif csv_file.exists():
                df = pd.read_csv(csv_file)
                n_rows = len(df)
                n_cols = len(df.columns)
            else:
                n_rows = 0
                n_cols = len(columns)

            chunks.append(f"#' {title}")
            chunks.append("#'")
            chunks.append(f"#' {desc}")
            chunks.append("#'")
            chunks.append(
                f"#' @format A data frame with {n_rows} rows and {n_cols} variables:"
            )
            chunks.append("#' \\describe{")
            for col_name, col_desc in columns.items():
                chunks.append(f"#'   \\item{{{col_name}}}{{{col_desc}}}")
            chunks.append("#' }")
            chunks.append(
                "#' @source \\url{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}"
            )
            chunks.append(f'"{table_name}"')
            chunks.append("")

        data_r_path.write_text("\n".join(chunks), encoding="utf-8")
        logger.info("Generated roxygen documentation in %s", data_r_path)
        return data_r_path

    def generate_rd_docs(self) -> dict[str, Path]:
        """Generate man/*.Rd documentation files for all datasets."""
        man_dir = self.r_pkg_dir / "man"
        man_dir.mkdir(parents=True, exist_ok=True)
        created: dict[str, Path] = {}

        for table_name in TABLES:
            doc_meta = TABLE_DOCUMENTATION.get(table_name, {})
            title = doc_meta.get(
                "title", f"{table_name.capitalize()} in The Great British Bake Off"
            )
            desc = doc_meta.get("description", f"Tidy dataset of {table_name}.")
            columns = doc_meta.get("columns", {})

            parquet_file = self.processed_dir / f"{table_name}.parquet"
            csv_file = self.processed_dir / f"{table_name}.csv"
            if parquet_file.exists():
                df = pd.read_parquet(parquet_file)
                n_rows = len(df)
                n_cols = len(df.columns)
            elif csv_file.exists():
                df = pd.read_csv(csv_file)
                n_rows = len(df)
                n_cols = len(df.columns)
            else:
                n_rows = 0
                n_cols = len(columns)

            items_str = "\n".join(
                f"  \\item{{{col}}}{{{col_desc}}}" for col, col_desc in columns.items()
            )

            rd_content = f"""% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/data.R
\\docType{{data}}
\\name{{{table_name}}}
\\alias{{{table_name}}}
\\title{{{title}}}
\\format{{
A data frame with {n_rows} rows and {n_cols} variables:
\\describe{{
{items_str}
}}
}}
\\source{{
\\url{{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}}
}}
\\usage{{
{table_name}
}}
\\description{{
{desc}
}}
\\keyword{{datasets}}
"""
            rd_path = man_dir / f"{table_name}.Rd"
            rd_path.write_text(rd_content, encoding="utf-8")
            created[table_name] = rd_path

        logger.info("Generated %d Rd documentation files in %s", len(created), man_dir)
        return created

    def scaffold_package(self) -> dict[str, Path]:
        """Scaffold companion R package metadata, vignettes, tests, and documentation."""
        self.r_pkg_dir.mkdir(parents=True, exist_ok=True)
        created_files: dict[str, Path] = {}

        # 1. DESCRIPTION
        desc_path = self.r_pkg_dir / "DESCRIPTION"
        version = "0.1.0"
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            m_ver = re.search(
                r'version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8")
            )
            if m_ver:
                version = m_ver.group(1)
        elif desc_path.exists():
            m_ver = re.search(
                r"Version:\s*([^\n\r]+)", desc_path.read_text(encoding="utf-8")
            )
            if m_ver:
                version = m_ver.group(1).strip()

        desc_content = f"""Package: gbbo
Title: The Great British Bake Off Tidy Datasets
Version: {version}
Authors@R: person("Nicholas", "Wilde", email = "nicholas@nicholaswilde.io", role = c("aut", "cre"))
Description: Comprehensive tidy datasets for the television series The
    Great British Bake Off (broadcast as The Great British Baking Show in
    North America). Contains clean tabular data on seasons, bakers,
    episodes, and challenge performances for exploratory data analysis,
    statistical modeling, baking text analytics, and game show survival
    analysis.
License: Apache License (== 2.0)
URL: https://github.com/nicholaswilde/the-great-british-bake-off
BugReports: https://github.com/nicholaswilde/the-great-british-bake-off/issues
Depends:
    R (>= 3.5.0)
LazyData: true
LazyDataCompression: xz
ByteCompile: true
RoxygenNote: 7.3.1
Suggests:
    dplyr,
    ggplot2,
    knitr,
    rmarkdown,
    testthat (>= 3.0.0),
    tibble
VignetteBuilder: knitr
Encoding: UTF-8
"""
        desc_path.write_text(desc_content, encoding="utf-8")
        created_files["DESCRIPTION"] = desc_path

        # 2. NAMESPACE
        namespace_path = self.r_pkg_dir / "NAMESPACE"
        namespace_content = "# Generated by roxygen2: do not edit by hand\n"
        namespace_path.write_text(namespace_content, encoding="utf-8")
        created_files["NAMESPACE"] = namespace_path

        # 3. .Rbuildignore
        buildignore_path = self.r_pkg_dir / ".Rbuildignore"
        buildignore_content = """^.*\\.Rproj$
^\\.Rproj\\.user$
^tests/testthat/_snaps$
^LICENSE$
"""
        buildignore_path.write_text(buildignore_content, encoding="utf-8")
        created_files[".Rbuildignore"] = buildignore_path

        # 4. README.md
        readme_path = self.r_pkg_dir / "README.md"
        readme_content = """# gbbo

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
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        created_files["README.md"] = readme_path

        # 5. Vignette: vignettes/introduction.Rmd
        vignettes_dir = self.r_pkg_dir / "vignettes"
        vignettes_dir.mkdir(parents=True, exist_ok=True)
        vignette_path = vignettes_dir / "introduction.Rmd"
        vignette_content = """---
title: "Introduction to gbbo"
output: rmarkdown::html_vignette
vignette: >
  %\\VignetteIndexEntry{Introduction to gbbo}
  %\\VignetteEngine{knitr::rmarkdown}
  %\\VignetteEncoding{UTF-8}
---

```{r, include = FALSE}
knitr::opts_chunk$set(
  collapse = TRUE,
  comment = "#>"
)
```

## Overview

The `gbbo` package provides comprehensive tidy datasets for **The Great British Bake Off** (broadcast in the US as *The Great British Baking Show*).

The data is structured into four relational tables:
1. `seasons`: Series summaries, broadcast years, hosts, judges, and winners.
2. `bakers`: Contestant demographics, ages, hometowns, occupations, and placements.
3. `episodes`: Weekly episode themes, air dates, and challenge time allocations.
4. `performances`: Individual baker challenge bakes, technical ranks, Hollywood Handshakes, and outcomes.

## Setup and Data Inspection

```{r setup, eval = FALSE}
library(gbbo)
library(dplyr)
library(ggplot2)

data(seasons)
data(bakers)
data(episodes)
data(performances)
```

## Analysis 1: Hollywood Handshakes Over Time

```{r handshakes, eval = FALSE}
handshake_counts <- performances |>
  filter(hollywood_handshake) |>
  count(episode_id, sort = TRUE)

head(handshake_counts)
```

## Analysis 2: Technical Challenge Rankings vs Final Outcome

```{r technical-analysis, eval = FALSE}
performances |>
  filter(!is.na(technical_rank)) |>
  group_by(result) |>
  summarize(avg_tech_rank = mean(technical_rank, na.rm = TRUE))
```
"""
        vignette_path.write_text(vignette_content, encoding="utf-8")
        created_files["vignettes/introduction.Rmd"] = vignette_path

        # 6. Tests: tests/testthat.R and tests/testthat/test-datasets.R
        tests_dir = self.r_pkg_dir / "tests" / "testthat"
        tests_dir.mkdir(parents=True, exist_ok=True)

        testthat_runner = self.r_pkg_dir / "tests" / "testthat.R"
        testthat_runner.write_text(
            'library(testthat)\nlibrary(gbbo)\n\ntest_check("gbbo")\n',
            encoding="utf-8",
        )
        created_files["tests/testthat.R"] = testthat_runner

        test_datasets = tests_dir / "test-datasets.R"
        test_datasets_content = """test_that("all 4 datasets exist and have expected structure", {
  expect_true(exists("seasons"))
  expect_true(exists("bakers"))
  expect_true(exists("episodes"))
  expect_true(exists("performances"))

  tables <- list(
    seasons = seasons,
    bakers = bakers,
    episodes = episodes,
    performances = performances
  )

  for (name in names(tables)) {
    df <- tables[[name]]
    expect_s3_class(df, "data.frame")
    expect_gt(nrow(df), 0)
    expect_gt(ncol(df), 0)
  }
})

test_that("seasons table has series_number integer column", {
  expect_true(is.integer(seasons$series_number))
})

test_that("performances table has boolean flag columns", {
  expect_true(is.logical(performances$hollywood_handshake))
  expect_true(is.logical(performances$did_well))
})
"""
        test_datasets.write_text(test_datasets_content, encoding="utf-8")
        created_files["tests/testthat/test-datasets.R"] = test_datasets

        return created_files

    def export_all(self) -> dict[str, Any]:
        """Perform full R export: RDS files, RDA package data, roxygen docs, and package scaffolding."""
        rds_results = self.export_rds()
        rda_results = self.export_rda()
        roxygen_file = self.generate_roxygen_docs()
        rd_files = self.generate_rd_docs()
        scaffold_files = self.scaffold_package()

        return {
            "rds": rds_results,
            "rda": rda_results,
            "roxygen": roxygen_file,
            "rd": rd_files,
            "scaffold": scaffold_files,
        }


def export_to_r(
    processed_dir: Path | str = "data/processed",
    r_output_dir: Path | str = "data/processed/r",
    r_pkg_dir: Path | str = "r",
) -> dict[str, Any]:
    """Helper function to run the full R export pipeline."""
    exporter = RExporter(
        processed_dir=processed_dir,
        r_output_dir=r_output_dir,
        r_pkg_dir=r_pkg_dir,
    )
    return exporter.export_all()
