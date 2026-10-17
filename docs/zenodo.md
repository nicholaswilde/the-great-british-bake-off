# Zenodo Integration & Academic Archiving Guide

This guide details the integration of **Zenodo** (operated by CERN) for persistent academic citation, digital object identifier (DOI) allocation, and automated release snapshot archiving for **The Great British Bake Off (GBBO) Dataset & AI Training Corpus**.

---

## 1. Concept DOI vs. Version DOI

Zenodo provides two complementary persistent identifiers for GitHub repositories:

1. **Concept DOI (`10.5281/zenodo.14000000`)**:
   - Persistently identifies the dataset across **all versions** and releases.
   - Automatically redirects citations and visitors to the most recent published release.
   - Ideal for inclusion in `README.md` badges, paper references, and syllabi.

2. **Version DOI (`10.5281/zenodo.<version_id>`)**:
   - Identifies an immutable snapshot of an exact release (e.g. `v0.1.0`).
   - Ensures strict reproducibility for academic benchmarks and empirical papers.

---

## 2. Setting Up Automated GitHub-Zenodo Archiving

Zenodo integrates natively with GitHub via OAuth webhooks to archive every release automatically:

1. **Sign in to Zenodo**:
   - Navigate to [https://zenodo.org](https://zenodo.org) and log in using your GitHub account (`nicholaswilde`).

2. **Authorize GitHub Application**:
   - Go to [Zenodo GitHub Settings](https://zenodo.org/account/settings/github/).
   - Ensure the Zenodo GitHub application has read access to your public repositories.

3. **Enable Repository Archiving**:
   - Locate `nicholaswilde/the-great-british-bake-off` in the repository list.
   - Toggle the switch to **ON**.
   - Zenodo will automatically configure a GitHub release webhook on the repository.

4. **Trigger Archiving**:
   - Each time a GitHub Release is published (e.g. via `task release`), GitHub triggers the Zenodo webhook.
   - Zenodo pulls the release tarball, parses `.zenodo.json`, assigns a new version DOI, updates the Concept DOI, and publishes the record.

---

## 3. Metadata Specification (`.zenodo.json`)

The `.zenodo.json` file in the repository root configures Zenodo record metadata:

- **`title`**: Dataset and corpus title.
- **`upload_type`**: Set to `"dataset"`.
- **`description`**: Rich HTML summary of the tidy tables, AI corpora, and R package.
- **`creators`**: Primary author information and affiliations.
- **`access_right`**: `"open"`.
- **`license`**: `"Apache-2.0"`.
- **`keywords`**: Topic tags for discoverability in academic search indexes.
- **`related_identifiers`**: Links to the upstream GitHub repository.

---

## 4. Citation Example

### BibTeX
```bibtex
@misc{wilde_gbbo_2026,
  author       = {Nicholas Wilde},
  title        = {The Great British Bake Off Dataset & AI Training Corpus},
  year         = {2026},
  version      = {0.1.0},
  doi          = {10.5281/zenodo.14000000},
  publisher    = {Zenodo},
  url          = {https://doi.org/10.5281/zenodo.14000000}
}
```

### APA
> Wilde, N. (2026). *The Great British Bake Off Dataset & AI Training Corpus* (Version 0.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.14000000
