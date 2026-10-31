# Agent Skills Catalog

Catalog of Antigravity agent skills available in `the-great-british-bake-off`.

| Skill | Description | Task / Command |
|---|---|---|
| [`cavecrew`](skills/cavecrew/SKILL.md) | Decision guide for delegating to caveman-style subagents | `/cavecrew` / delegation |
| [`caveman`](skills/caveman/SKILL.md) | Ultra-compressed communication mode cutting output tokens 65% | `/caveman [lite\|full\|ultra\|wenyan]` |
| [`caveman-commit`](skills/caveman-commit/SKILL.md) | Ultra-compressed Conventional Commits message generator | `/caveman-commit` |
| [`caveman-compress`](skills/caveman-compress/SKILL.md) | Compress natural language memory files into caveman format | `/caveman-compress <file>` |
| [`caveman-help`](skills/caveman-help/SKILL.md) | Quick-reference card for all caveman modes, skills, and commands | `/caveman-help` |
| [`caveman-review`](skills/caveman-review/SKILL.md) | Ultra-compressed one-line code review comments | `/caveman-review` |
| [`caveman-stats`](skills/caveman-stats/SKILL.md) | Show real session token usage and estimated savings | `/caveman-stats` |
| [`gbbo-dataset-builder`](skills/gbbo-dataset-builder/SKILL.md) | Aggregate, validate through Pydantic schemas, and export raw GBBO series files into master tables | `task build` / `uv run gbbo build` |
| [`gbbo-gap-audit`](skills/gbbo-gap-audit/SKILL.md) | Audit dataset completeness, calculate missing cell rates, and backfill broadcast ratings or demographic gaps | `task audit:gaps` / `uv run python scripts/gap_audit.py` |
| [`gbbo-predict`](skills/gbbo-predict/SKILL.md) | Run empirical predictive engine to forecast Star Baker candidates, elimination risks, and winner trajectories | `task predict` / `uv run python scripts/predict.py` |
| [`gbbo-scrape-wiki`](skills/gbbo-scrape-wiki/SKILL.md) | Scrape and extract GBBO series summaries, baker demographics, challenge bakes, technical rankings, and eliminations | `task scrape` / `uv run gbbo scrape` |
| [`karpathy-guidelines`](skills/karpathy-guidelines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes | Guidelines reference |
| [`ponytail`](skills/ponytail/SKILL.md) | Switch ponytail intensity level (lazy senior dev mode, YAGNI ladder) | `/ponytail [lite\|full\|ultra\|off]` |
| [`ponytail-audit`](skills/ponytail-audit/SKILL.md) | Audit whole repo for over-engineering and removable complexity | `/ponytail-audit` |
| [`ponytail-debt`](skills/ponytail-debt/SKILL.md) | Harvest `ponytail:` comments into a tracked debt ledger | `/ponytail-debt` |
| [`ponytail-gain`](skills/ponytail-gain/SKILL.md) | Show ponytail measured impact scoreboard | `/ponytail-gain` |
| [`ponytail-help`](skills/ponytail-help/SKILL.md) | Quick reference for ponytail levels, skills, and commands | `/ponytail-help` |
| [`ponytail-review`](skills/ponytail-review/SKILL.md) | Review changes for over-engineering and dead complexity | `/ponytail-review` |
| [`release`](skills/release/SKILL.md) | Automate version calculation, pre-release validation, version bumping, git tagging, and atomic push | `scripts/release.sh` |
| [`release-summary`](skills/release-summary/SKILL.md) | Generate categorized, professional GitHub release summary based on git logs | `scripts/release_summary.py` |
