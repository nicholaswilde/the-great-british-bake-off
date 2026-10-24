# Great British Bake Off — Dataset Gap Audit Report

## Summary Table

| Table | Rows | Columns | Missing Cells | Completeness | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seasons` | 17 | 10 | 1 | 99.4% | **PASS** |
| `bakers` | 204 | 13 | 7 | 99.7% | **PASS** |
| `episodes` | 160 | 8 | 36 | 97.2% | **PASS** |
| `performances` | 1218 | 11 | 0 | 100.0% | **PASS** |

## Column Gaps Detail

### Table: `seasons`

| Column | Missing | % Missing | Severity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `series_number` | 0 | 0.0% | OK | Complete |
| `year` | 0 | 0.0% | OK | Complete |
| `winner` | 1 | 5.9% | MEDIUM | Complete |
| `hosts` | 0 | 0.0% | OK | Complete |
| `judges` | 0 | 0.0% | OK | Complete |
| `network` | 0 | 0.0% | OK | Complete |
| `pbs_season` | 12 | 70.6% | CONDITIONAL | Conditional challenge by design |
| `netflix_collection` | 8 | 47.1% | CONDITIONAL | Conditional challenge by design |
| `roku_season` | 10 | 58.8% | CONDITIONAL | Conditional challenge by design |
| `location` | 0 | 0.0% | OK | Complete |

### Table: `bakers`

| Column | Missing | % Missing | Severity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `baker_id` | 0 | 0.0% | OK | Complete |
| `series_number` | 0 | 0.0% | OK | Complete |
| `name` | 0 | 0.0% | OK | Complete |
| `age` | 0 | 0.0% | OK | Baker age at time of competition occasionally unlisted in early source summaries. |
| `gender` | 0 | 0.0% | OK | Complete |
| `occupation` | 0 | 0.0% | OK | Baker occupation unlisted or retired. |
| `hometown` | 0 | 0.0% | OK | Hometown unrecorded or broad region specified. |
| `overall_placement` | 7 | 3.4% | LOW | Complete |
| `image_url` | 0 | 0.0% | OK | Complete |
| `latitude` | 0 | 0.0% | OK | Complete |
| `longitude` | 0 | 0.0% | OK | Complete |
| `country` | 0 | 0.0% | OK | Complete |
| `county_region` | 0 | 0.0% | OK | Complete |

### Table: `episodes`

| Column | Missing | % Missing | Severity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `episode_id` | 0 | 0.0% | OK | Complete |
| `series_number` | 0 | 0.0% | OK | Complete |
| `episode_number` | 0 | 0.0% | OK | Complete |
| `theme` | 0 | 0.0% | OK | Complete |
| `air_date` | 0 | 0.0% | OK | Episode air dates recorded in Wikipedia 'Ratings' section; requires parsing ratings table. |
| `signature_time_min` | 36 | 22.5% | HIGH | Complete |
| `technical_time_min` | 38 | 23.8% | CONDITIONAL | Conditional challenge by design |
| `showstopper_time_min` | 43 | 26.9% | CONDITIONAL | Conditional challenge by design |

### Table: `performances`

| Column | Missing | % Missing | Severity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `performance_id` | 0 | 0.0% | OK | Complete |
| `baker_id` | 0 | 0.0% | OK | Complete |
| `episode_id` | 0 | 0.0% | OK | Complete |
| `signature_dish` | 7 | 0.6% | CONDITIONAL | Conditional challenge by design |
| `technical_rank` | 22 | 1.8% | CONDITIONAL | Some series finals (e.g. Series 1) omitted technical challenges, or judges only ranked top/bottom bakers. |
| `showstopper_dish` | 7 | 0.6% | CONDITIONAL | Conditional challenge by design |
| `result` | 0 | 0.0% | OK | Complete |
| `hollywood_handshake` | 0 | 0.0% | OK | Complete |
| `did_well` | 0 | 0.0% | OK | Complete |
| `at_risk` | 0 | 0.0% | OK | Complete |
| `absent` | 0 | 0.0% | OK | Complete |
