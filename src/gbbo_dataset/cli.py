"""CLI for The Great British Bake Off (GBBO) Dataset and AI Training Corpus."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from gbbo_dataset import __version__
from gbbo_dataset.builder import build_datasets
from gbbo_dataset.gap_auditor import DatasetGapAuditor
from gbbo_dataset.importers.rayofdata import (
    DEFAULT_RAY_DATA_DIR,
    run_enrichment,
)
from gbbo_dataset.scraper import scrape_series

app = typer.Typer(
    name="gbbo",
    help="The Great British Bake Off (GBBO) dataset curation & AI training toolkit.",
    add_completion=False,
)
console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gbbo_dataset.cli")


def version_callback(value: bool) -> None:
    """Print package version and exit."""
    if value:
        console.print(
            f"[bold cyan]gbbo[/bold cyan] version [bold green]{__version__}[/bold green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """The Great British Bake Off dataset CLI."""


@app.command("scrape")
def scrape(
    series: int | None = typer.Option(
        None, "--series", "-s", help="Specific series number to scrape"
    ),
    start: int = typer.Option(1, "--start", help="Start of series range"),
    end: int = typer.Option(17, "--end", help="End of series range"),
    raw_dir: Path = typer.Option(
        Path("data/raw"), "--raw-dir", help="Target raw data directory"
    ),
) -> None:
    """Scrape Wikipedia series tables for bakers, episodes, and challenge bakes."""
    if series is not None:
        console.print(
            f"[bold blue]Scraping Wikipedia for GBBO Series {series}...[/bold blue]"
        )
        try:
            res = scrape_series(series, raw_dir=raw_dir)
            console.print(
                f"[green]✓ Series {series} scraped: {res.get('bakers', 0)} bakers, "
                f"{res.get('episodes', 0)} episodes, {res.get('performances', 0)} performances[/green]"
            )
        except Exception as e:
            console.print(f"[red]✗ Failed to scrape Series {series}: {e}[/red]")
            raise typer.Exit(code=1) from e
        return

    console.print(
        f"[bold blue]Scraping Wikipedia for GBBO Series {start} to {end}...[/bold blue]"
    )
    successes = 0
    failures = 0
    for s_idx in range(start, end + 1):
        try:
            res = scrape_series(s_idx, raw_dir=raw_dir)
            console.print(
                f"  [green]✓ Series {s_idx:02d}: {res.get('bakers', 0)} bakers, "
                f"{res.get('episodes', 0)} episodes, {res.get('performances', 0)} performances[/green]"
            )
            successes += 1
        except Exception as err:
            console.print(
                f"  [yellow]⚠ Series {s_idx:02d} skipped/failed: {err}[/yellow]"
            )
            failures += 1

    console.print(
        f"[bold green]Scraping complete: {successes} succeeded, {failures} skipped/failed.[/bold green]"
    )


@app.command("build")
def build(
    raw_dir: Path = typer.Option(
        Path("data/raw"), "--raw-dir", help="Directory containing raw JSON files"
    ),
    processed_dir: Path = typer.Option(
        Path("data/processed"), "--processed-dir", help="Target processed directory"
    ),
) -> None:
    """Aggregate raw series files and validate records against Pydantic schemas."""
    console.print(
        "[bold blue]Building and validating processed GBBO datasets...[/bold blue]"
    )
    results = build_datasets(raw_dir=raw_dir, processed_dir=processed_dir)
    if results["errors"] > 0:
        console.print(
            f"[yellow]Build completed with {results['errors']} validation errors/warnings.[/yellow]"
        )
    else:
        console.print(
            f"[green]✓ Build complete: {results['bakers']} bakers, {results['episodes']} episodes, "
            f"{results['performances']} performances written to {processed_dir}.[/green]"
        )


@app.command("enrich")
def enrich(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        help="Directory with processed tables",
    ),
    ray_dir: Path = typer.Option(
        DEFAULT_RAY_DATA_DIR, "--ray-dir", help="RayofData dataset directory"
    ),
) -> None:
    """Enrich datasets with demographics, handshakes, challenge times, and streaming metadata."""
    console.print(
        f"[bold blue]Enriching processed tables from {ray_dir}...[/bold blue]"
    )
    summary = run_enrichment(processed_dir=processed_dir, ray_dir=ray_dir)
    console.print(
        f"[green]✓ Enrichment complete: {summary['bakers_enriched']} bakers enriched, "
        f"{summary['episodes_enriched']} episodes timed, {summary['handshakes_confirmed']} handshakes, "
        f"{summary['seasons_created']} seasons exported.[/green]"
    )


@app.command("gaps")
def gaps(
    detail: bool = typer.Option(
        False, "--detail", "-d", help="Display column-level gap breakdown"
    ),
    export_md: Path | None = typer.Option(
        None, "--export-md", help="Export Markdown gap report to specified path"
    ),
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        help="Directory with processed tables",
    ),
) -> None:
    """Audit dataset completeness, column nullability, and schema health."""
    auditor = DatasetGapAuditor(processed_dir=processed_dir)
    results = auditor.audit_all()
    auditor.print_summary(results)

    if detail:
        auditor.print_detail(results)

    if export_md:
        auditor.export_markdown(results, export_md)
        console.print(
            f"[bold green]✓ Exported markdown gap report to {export_md}[/bold green]"
        )


@app.command("stats")
def stats(
    processed_dir: Path = typer.Option(
        Path("data/processed"), "--processed-dir", help="Processed data directory"
    ),
) -> None:
    """Display table row count and size statistics across all processed datasets."""
    tables = ["seasons", "bakers", "episodes", "performances"]
    t = Table(
        title="The Great British Bake Off — Processed Dataset Stats",
        header_style="bold magenta",
    )
    t.add_column("Table", style="bold cyan")
    t.add_column("Rows", justify="right")
    t.add_column("Columns", justify="right")
    t.add_column("JSON Size", justify="right")
    t.add_column("CSV Size", justify="right")

    for tbl in tables:
        json_file = processed_dir / f"{tbl}.json"
        csv_file = processed_dir / f"{tbl}.csv"
        rows = "-"
        cols = "-"
        json_size = "-"
        csv_size = "-"

        if json_file.exists():
            json_size = f"{json_file.stat().st_size / 1024:.1f} KB"
        if csv_file.exists():
            csv_size = f"{csv_file.stat().st_size / 1024:.1f} KB"
            try:
                df = pd.read_csv(csv_file)
                rows = f"{len(df):,}"
                cols = str(len(df.columns))
            except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
                rows = "-"
                cols = "-"

        t.add_row(tbl, rows, cols, json_size, csv_size)

    console.print(t)


if __name__ == "__main__":
    app()
