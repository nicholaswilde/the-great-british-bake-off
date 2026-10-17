# Agent Guidelines: The Great British Bake Off Dataset

This repository creates a comprehensive tidy dataset and AI training corpus for the television series **The Great British Bake Off** (**GBBO**), broadcast as *The Great British Baking Show* in North America.

## Environment & Dependency Management
- **Tooling**: Use [`uv`](https://docs.astral.sh/uv/) and [`go-task`](https://taskfile.dev/) (`task`) to manage dependencies, run pipeline workflows, and execute commands.
  - Run tasks: `task <command>` (e.g., `task test`, `task check`, `task spellcheck`, `task spellcheck-file FILE=path/to/file`, `task scrape`, `task build`, `task sync`, `task stats`)
  - Run CLI directly: `uv run gbbo --help`, `uv run gbbo scrape --series 1`, `uv run gbbo build`, `uv run gbbo stats`
  - Run build: `task build` or `uv run gbbo build`
  - Run tests: `task test` or `uv run --extra dev pytest`
  - Manage packages: `uv add <package>`, `uv lock`, or `task sync`
  - Never run raw `pip install` or direct `python` without `uv run`.

## Directory Structure
- `src/gbbo_dataset/`:
  - `models.py`: Pydantic models for `Baker`, `Episode`, `Performance`, `Season`, and `ResultEnum`.
  - `scraper.py`: Wikipedia extraction logic and cleaner.
  - `builder.py`: Master dataset validator and exporter (JSON + CSV).
  - `gap_auditor.py`: Dataset completeness and null rate auditor.
  - `importers/rayofdata.py`: Demographics, handshakes, and streaming metadata enrichment.
  - `cli.py`: Typer CLI application (`gbbo`).
- `scripts/`: Backward-compatible wrappers forwarding to `gbbo_dataset`.
- `data/`:
  - `data/raw/`: Raw scraped series files (`series_{series}_bakers.json`, etc.).
  - `data/processed/`: Validated master tidy tables (`bakers.json`, `episodes.json`, `performances.json`, `seasons.json`, and CSVs).
- `tests/`: Pytest unit and integration test suite.
- `.agents/`:
  - `rules/`: Workspace behavioral rules (RTK, Caveman, Ponytail, CodeGraph, Context-Mode, GBBO terminology, Serena).
  - `skills/`: On-demand agent runbooks (`gbbo-scrape-wiki`, `gbbo-dataset-builder`, stack skills).

## Available Workspace Skills
Agents can invoke the following skills located in `.agents/skills/`:
- `gbbo-scrape-wiki`: Scrapes Wikipedia for series summaries, bakers, challenge bakes, technical ranks, and eliminations.
- `gbbo-dataset-builder`: Compiles raw data into validated tidy tables (`bakers.json`, `episodes.json`, `performances.json`) and CSVs.
- `gbbo-gap-audit`: Audits dataset completeness, calculates missing cell rates, and exports gap reports.
- `gbbo-predict`: Runs empirical predictive engine for Star Baker candidates, elimination risks, and series trajectories.
- `release`: Automates version calculation, pre-release validation (`task check`), version bumping, git tagging, and atomic push.
- `release-summary`: Generates categorized GitHub release notes based on conventional git logs and updates draft releases.
- `cavecrew`, `caveman`, `caveman-*`: Ultra-compressed communication and review modes.
- `ponytail`, `ponytail-*`: Minimalist, lazy senior dev and YAGNI discipline.
- `karpathy-guidelines`: AI engineer principles and practices.

## RTK Command Guidelines
- **Git Operations**: Prefix `git` commands with `rtk` (e.g., `rtk git status`, `rtk git diff`, `rtk git log`, `rtk git commit`, `rtk git push`).
- **GitHub CLI**: Prefix `gh` commands with `rtk` and always pipe to `cat` to bypass interactive prompts and terminal pagers (e.g., `rtk gh issue list | cat`, `rtk gh pr status | cat`).
- **File & Directory Inspection**: Use `rtk ls`, `rtk tree`, `rtk find`, or `rtk read` when listing or reading files to get token-optimized output.
- **Searching**: Use `rtk rg` (ripgrep) as the primary pattern and text search utility. Avoid raw `grep` or `find | xargs`. Leverage `-t py`, `-l`, and path scoping to conserve tokens.

## Serena Semantic Code Navigation & LSP
This project uses Serena for semantic Python development, AST manipulation, and LSP diagnostics.
- **Mandatory Activation**: Before analyzing or editing Python code, agents MUST activate the project using `activate_project(project="the-great-british-bake-off")`.
- **Rules Reference**: See [`.agents/rules/serena-rules.md`](.agents/rules/serena-rules.md) for tool mappings, refactoring protocols, and CodeGraph boundaries.
