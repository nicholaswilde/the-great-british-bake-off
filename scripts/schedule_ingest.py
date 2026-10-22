#!/usr/bin/env -S uv run python
"""Automated scheduled ingestion and series tracking workflow script for GBBO.

Periodically checks for new broadcast episodes and series of The Great British Bake Off,
scrapes updated tables from Wikipedia, executes data rebuilds and predictive models,
and opens a Pull Request if fresh data is detected.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("schedule_ingest")


def run_cmd(cmd: list[str] | str, check: bool = True, capture: bool = True) -> str:
    """Run shell command and return decoded stdout."""
    if isinstance(cmd, str):
        res = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture,
            text=True,
        )
    else:
        res = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
        )
    return res.stdout.strip() if capture else ""


def get_highest_ingested_series(
    raw_dir: Path = Path("data/raw"),
    processed_dir: Path = Path("data/processed"),
) -> int:
    """Determine highest series number currently ingested."""
    seasons_csv = processed_dir / "seasons.csv"
    if seasons_csv.exists():
        try:
            import pandas as pd

            df = pd.read_csv(seasons_csv)
            if not df.empty and "series_number" in df.columns:
                return int(df["series_number"].max())
        except Exception as e:
            logger.warning("Error reading seasons.csv: %s", e)

    pattern = re.compile(r"series_(\d+)_bakers\.json")
    highest = 0
    if raw_dir.exists():
        for f in raw_dir.glob("series_*_bakers.json"):
            m = pattern.match(f.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest or 17


def run_pipeline() -> bool:
    """Execute the data processing, export pipeline, and prediction update."""
    task_bin = shutil.which("task")
    if task_bin:
        logger.info("Executing `task pipeline` and `task predict:update`...")
        res = subprocess.run([task_bin, "pipeline"], check=False)
        if res.returncode != 0:
            return False
        subprocess.run([task_bin, "predict:update"], check=False)
        return True

    # Fallback via uv run gbbo CLI
    try:
        run_cmd(["uv", "run", "gbbo", "build"])
        run_cmd(["uv", "run", "gbbo", "export-sqlite"])
        run_cmd(["uv", "run", "gbbo", "export-arrow"])
        run_cmd(["uv", "run", "gbbo", "export-r"])
        run_cmd(["uv", "run", "gbbo", "export-ai"])
        run_cmd(["uv", "run", "gbbo", "eval-benchmark"])
        run_cmd(["uv", "run", "gbbo", "validate"])
        run_cmd(["uv", "run", "gbbo", "predict", "--update-docs"])
        return True
    except Exception as e:
        logger.error("Error executing pipeline: %s", e)
        return False


def create_pr_or_commit(series: int, open_pr: bool = True) -> bool:
    """Commit changes and optionally open a Pull Request."""
    status = run_cmd("git status --porcelain data/ docs/ README.md", check=False)
    if not status:
        logger.info(
            "No git changes detected in data/, docs/, or README.md; skipping commit/PR."
        )
        return False

    branch_name = f"data/ingest-series-{series:02d}"
    commit_msg = (
        f"data(ingest): import Series {series} updates and refresh data pipeline"
    )

    logger.info("Creating git commit for Series %d ingestion...", series)
    try:
        run_cmd("git config user.name 'github-actions[bot]' || true", check=False)
        run_cmd(
            "git config user.email 'github-actions[bot]@users.noreply.github.com' || true",
            check=False,
        )

        if open_pr:
            run_cmd(f"git checkout -B {branch_name}", check=True)
            run_cmd("git add data/ docs/ README.md", check=True)
            run_cmd(["git", "commit", "-m", commit_msg], check=True)
            run_cmd(f"git push -u origin {branch_name} --force", check=True)

            pr_title = f"data(ingest): update Series {series} data and predictions"
            pr_body = (
                f"## Automated Series Ingestion\n\n"
                f"- Scraped latest episode bakes and challenge results for **Series {series}** from Wikipedia.\n"
                f"- Rebuilt tidy relational datasets, SQLite, Arrow IPC, Parquet, R package, and AI corpora.\n"
                f"- Recalibrated empirical predictive forecasts in `docs/predictions.md` and `README.md`.\n"
            )
            res = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    pr_title,
                    "--body",
                    pr_body,
                    "--base",
                    "main",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                logger.info("Opened Pull Request for %s", branch_name)
            elif "already exists" in res.stderr.lower():
                logger.info(
                    "Pull request for %s already exists and was updated.", branch_name
                )
            else:
                logger.warning("Could not create PR: %s", res.stderr.strip())
        else:
            run_cmd("git add data/ docs/ README.md", check=True)
            run_cmd(["git", "commit", "-m", commit_msg], check=True)
            run_cmd("git push origin HEAD", check=True)
            logger.info("Pushed commit directly to current branch.")
        return True
    except Exception as e:
        logger.error("Error creating PR/commit: %s", e)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check and ingest new episodes/series of The Great British Bake Off."
    )
    parser.add_argument(
        "--series",
        type=int,
        default=None,
        help="Specific series number to ingest (defaults to latest series)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check without scraping or building",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scraping and rebuilding even if no changes detected",
    )
    parser.add_argument(
        "--open-pr",
        action="store_true",
        default=True,
        help="Open a Pull Request if new data is ingested",
    )

    args = parser.parse_args()
    target_series = args.series or get_highest_ingested_series()

    logger.info("Targeting Series %d for ingestion check...", target_series)
    if args.check_only:
        logger.info("Check-only mode completed.")
        return 0

    # Execute scrape
    logger.info("Scraping Wikipedia for Series %d...", target_series)
    try:
        from gbbo_dataset.scraper import scrape_series

        scrape_series(target_series, raw_dir=Path("data/raw"))
    except Exception as e:
        logger.error("Failed scraping Series %d: %s", target_series, e)
        if not args.force:
            return 1

    # Run data pipeline and update predictions
    success = run_pipeline()
    if not success:
        logger.error("Pipeline run failed.")
        return 1

    # Commit and create PR if changes exist
    create_pr_or_commit(target_series, open_pr=args.open_pr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
