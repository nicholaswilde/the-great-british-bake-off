<!-- rtk-begin -->
## RTK Command Guidelines
- **Git Operations**: Prefix `git` commands with `rtk` (e.g., `rtk git status`, `rtk git diff`, `rtk git log`, `rtk git commit`, `rtk git push`).
- **GitHub CLI**: Prefix `gh` commands with `rtk` and pipe to `cat` (e.g., `rtk gh issue list | cat`, `rtk gh pr status | cat`). Always pipe to bypass interactive pagers.
- **File & Directory Inspection**: Use `rtk ls`, `rtk tree`, `rtk find`, or `rtk read` when listing or reading files for token-optimized output.
- **Searching**: Use `rtk rg` or `rg` (ripgrep) for line search pattern matching to save tokens.
- **Build & Test Outputs**: Use `rtk err` or `rtk test` when running build/test commands to filter output to errors/failures only (e.g., `rtk test uv run pytest`).
- **Exceptions**: Inside `ctx_execute` / `ctx_batch_execute` sandbox code, skip `rtk` (only printed output enters context). Drop `rtk` when exact raw bytes or patch required (`git diff` patch).
<!-- rtk-end -->

<!-- context-mode-begin -->
## Context-Mode Routing Guidelines
- **Derive, Do Not Dump**: Do NOT use `ctx_execute_file` or `ctx_execute` to dump whole file or full config. Print only specific value, matches, count, or known line range needed.
- **Tool Call Surface**: When using MCP wrappers, call `call_mcp_tool` with `ServerName: "context-mode_context-mode"` (or `"context-mode"`) and `ToolName: "ctx_execute"`, `"ctx_execute_file"`, `"ctx_batch_execute"`, `"ctx_fetch_and_index"`, `"ctx_search"`, or `"ctx_index"`.
- **Mandatory Routing**:
  - For analyze/count/filter/compare/search/parse/transform tasks, write code with `ctx_execute` and print only final answer.
  - For analyzing/exploring inside file, use `ctx_execute_file`. Use native `read_file` only when editing requires exact bytes or small known range.
  - Use `ctx_batch_execute` for multi-command repository reconnaissance.
  - Use `ctx_execute` for shell commands whose output may exceed short fixed answer.
  - Use `ctx_fetch_and_index` for web content, then `ctx_search` to query it.
  - Return only derived answers, concise summaries, selected snippets, or file paths.
<!-- context-mode-end -->

<!-- ponytail-begin -->
## Ponytail (Lazy Senior Dev Mode) Guidelines
- **Stop at first rung that holds**:
  1. Need to build at all? (YAGNI)
  2. Already in codebase? Reuse existing helpers/utils/patterns.
  3. Stdlib does it? Use it.
  4. Native platform feature covers it? Use it.
  5. Installed dependency solves it? Use it.
  6. Can be one line? One line.
  7. Only then: write minimum working code.
- **Bug fix = root cause, not symptom**: Fix shared function/path rather than individual callers.
- **Rules**:
  - No unrequested abstractions, boilerplate, or avoidable dependencies.
  - Deletion over addition. Boring over clever. Fewest files possible.
  - Shortest working diff wins once problem understood.
  - Mark deliberate simplifications cutting real corner with `ponytail:` comment naming ceiling and upgrade path.
  - Ensure logic leaves behind ONE runnable check (assert-based demo/self-check or small test file). Trivial one-liners need none.
<!-- ponytail-end -->

<!-- caveman-begin -->
## Caveman Guidelines
Respond terse like smart caveman. All technical substance stay. Only fluff die.

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging.
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused. Resume after.

Boundaries: code/commits/PRs written normal.
<!-- caveman-end -->

<!-- codegraph-begin -->
## CodeGraph

In repositories indexed by CodeGraph (`.codegraph/` directory exists at repo root), reach for it BEFORE grep/find or reading files when exploring code:

- **MCP tool**: `codegraph_explore` answers source + call path + blast radius in one call. Dynamic-dispatch hops included. Name file or symbol in query to read current line-numbered source.
- **Shell**: `codegraph explore "<symbol names or question>"`.

If no `.codegraph/` directory exists, skip CodeGraph entirely.
<!-- codegraph-end -->

<!-- serena-begin -->
## Serena Semantic Navigation & LSP Integration
Use Serena (`serena`) MCP tools for semantic navigation, AST symbol inspection, LSP diagnostics, and project memories:
- **Mandatory Activation**: Before analyzing or editing Python code, agents MUST activate the project using `activate_project(project="the-great-british-bake-off")`.
1. **Map first**: Call `get_symbols_overview` on target file instead of reading entire file.
2. **Read target symbol only**: Call `find_symbol` with `include_body: true` for target function/class/method.
3. **Check callers**: Call `find_referencing_symbols` or `find_implementations` before signature or behavior changes.
4. **Edit by symbol**: Use `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, or `rename_symbol`. Use standard edit for small tweaks or non-code files.
5. **Verify diagnostics**: Call `get_diagnostics_for_file` after edits to catch LSP errors before full test run.
- **Rules Reference**: See [`.agents/rules/serena.md`](.agents/rules/serena.md) for tool mappings, refactoring protocols, and CodeGraph boundaries.
<!-- serena-end -->

<!-- headroom-begin -->
## Headroom MCP (Context Window Compression)
Use Headroom (`headroom`) MCP tools to manage context window consumption on large payloads:
- `headroom_compress`: Shrink large tool outputs or raw data.
- `headroom_retrieve`: Retrieve original content by hash if specific details needed.
- `headroom_stats`: Monitor headroom cache usage.
<!-- headroom-end -->

<!-- ripgrep-guidelines-begin -->
## Ripgrep Guidelines
- **Pattern Searching**: Always use `rg` (ripgrep) or `rtk rg` instead of standard `grep` to search text inside files quickly and save token output.
- **Scope**: Use `-t py` for Python files, `-l` for file listing, keep context small (`-C 1`).
<!-- ripgrep-guidelines-end -->

<!-- taplo-rules-begin -->
## Taplo TOML Rules
- **Format**: Run `taplo fmt` to format TOML files in-place (`pyproject.toml`).
- **Validation**: Run `taplo lint` to validate TOML syntax and schema.
<!-- taplo-rules-end -->

<!-- sensitive-information-protection-begin -->
## Sensitive Information & PII Protection
NEVER commit or stage sensitive personal, financial, or security data to repository:
1. **Secrets & Credentials**: Never commit `.env` files, API keys, bearer tokens, passwords, or private encryption keys.
2. **Explicit Staging**: Never use `git add .` when untracked secret files exist; stage explicitly by name.
<!-- sensitive-information-protection-end -->

<!-- issue-management-begin -->
## GitHub Issue Management
- **Commit Closing**: GitHub issues only close automatically when commits containing `Fixes #<number>` are pushed to remote repository.
<!-- issue-management-end -->

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
  - `rules/`: Workspace behavioral rules (`rtk-rules.md`, `serena.md`, `github-cli-rules.md`, `ripgrep-rules.md`, `no-secrets.md`, `caveman-rules.md`, `uv-rules.md`, `taplo-rules.md`, `domain-terminology-rules.md`).
  - `skills/`: On-demand agent runbooks (`gbbo-scrape-wiki`, `gbbo-dataset-builder`, `gbbo-gap-audit`, `gbbo-predict`, release and stack skills).
  - `skills_catalog.md`: Complete agent skills reference table.

## Available Workspace Skills
See [`.agents/skills_catalog.md`](.agents/skills_catalog.md) for full descriptions and commands.
- `gbbo-scrape-wiki`: Scrapes Wikipedia for series summaries, bakers, challenge bakes, technical ranks, and eliminations.
- `gbbo-dataset-builder`: Compiles raw data into validated tidy tables (`bakers.json`, `episodes.json`, `performances.json`) and CSVs.
- `gbbo-gap-audit`: Audits dataset completeness, calculates missing cell rates, and exports gap reports.
- `gbbo-predict`: Runs empirical predictive engine for Star Baker candidates, elimination risks, and series trajectories.
- `release`: Automates version calculation, pre-release validation (`task check`), version bumping, git tagging, and atomic push.
- `release-summary`: Generates categorized GitHub release notes based on conventional git logs and updates draft releases.
- `cavecrew`, `caveman`, `caveman-*`: Ultra-compressed communication and review modes.
- `ponytail`, `ponytail-*`: Minimalist, lazy senior dev and YAGNI discipline.
- `karpathy-guidelines`: AI engineer principles and practices.
