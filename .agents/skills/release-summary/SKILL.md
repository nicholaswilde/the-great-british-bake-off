---
name: release-summary
description: Generates a categorized, professional GitHub release summary based on git logs and updates the draft release using scripts/release_summary.py.
---
# /release-summary [range]

Generates a clean, professional GitHub release summary based on git logs.

## Description
This skill uses `scripts/release_summary.py` to retrieve git commit logs and format them into structured markdown categories:
- 🚀 **New Features**: New features, scrapers, predictive modeling, exporters, and CLI commands.
- 📊 **Dataset & Pipeline Updates**: Series ingestion, challenge tables, and schema additions.
- 🐛 **Bug Fixes**: Scraper fixes, schema corrections, and edge case fixes.
- ✨ **Improvements**: Refactoring, performance optimizations, and style improvements.
- 🔧 **Maintenance & Automation**: Taskfile, CI/CD, dependency updates, and packaging.
- 📝 **Documentation**: Documentation, README, and data dictionary updates.

It then updates the existing GitHub draft release with the formatted changelog using `gh release edit <tag> --draft -F <notes>`.

## Protocol

1. Execute the Python script or Taskfile command:
   ```bash
   # Automatically detect the latest release/tag range
   ./scripts/release_summary.py
   # or
   task release:summary

   # Or specify an explicit git revision range
   ./scripts/release_summary.py v0.1.0..v0.2.0
   task release:summary -- v0.1.0..v0.2.0
   ```
2. The script parses conventional commits, displays the formatted release notes in the terminal, and updates the corresponding draft release in-place on GitHub.
