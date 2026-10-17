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
from gbbo_dataset.exports import (
    BenchmarkSuite,
    export_ai,
    export_arrow,
    export_to_r,
    export_to_sqlite,
    publish_to_hf,
)
from gbbo_dataset.exports.packaging import ReleasePackager
from gbbo_dataset.gap_auditor import DatasetGapAuditor
from gbbo_dataset.geocoding import export_bakers_geojson
from gbbo_dataset.importers.rayofdata import (
    DEFAULT_RAY_DATA_DIR,
    run_enrichment,
)
from gbbo_dataset.predictor import run_predict_cli
from gbbo_dataset.scraper import scrape_series
from gbbo_dataset.validator import DatasetValidator

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


@app.command("export-sqlite")
def export_sqlite_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        "-p",
        help="Directory with processed Parquet/CSV tables",
    ),
    db_path: Path = typer.Option(
        Path("data/processed/gbbo.db"),
        "--db-path",
        "-d",
        help="Path to write SQLite database",
    ),
) -> None:
    """Export processed tables into a unified SQLite database with foreign keys."""
    console.print(f"[bold blue]Exporting tables to SQLite ({db_path})...[/bold blue]")
    out = export_to_sqlite(processed_dir=processed_dir, db_path=db_path)
    console.print(f"[green]✓ Successfully exported SQLite database to {out}[/green]")


@app.command("export-geojson")
def export_geojson_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        "-p",
        help="Directory with processed tables",
    ),
    output_file: Path = typer.Option(
        Path("data/processed/bakers.geojson"),
        "--output-file",
        "-o",
        help="Path to output GeoJSON file",
    ),
) -> None:
    """Export baker hometown coordinates to standard GeoJSON."""
    console.print(
        "[bold blue]Exporting GBBO baker hometown coordinates to GeoJSON...[/bold blue]"
    )
    bakers_path = processed_dir / "bakers.json"
    out = export_bakers_geojson(output_path=output_file, bakers_json_path=bakers_path)
    console.print(f"[green]✓ Exported GeoJSON dataset to {out}[/green]")


@app.command("export-arrow")
def export_arrow_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        "-p",
        help="Processed tables directory",
    ),
    arrow_dir: Path = typer.Option(
        Path("data/processed/arrow"),
        "--arrow-dir",
        "-a",
        help="Arrow IPC output directory",
    ),
) -> None:
    """Export tables to Apache Arrow IPC files and Parquet tables."""
    console.print(
        "[bold blue]Exporting Apache Arrow IPC & Parquet datasets...[/bold blue]"
    )
    results = export_arrow(processed_dir=processed_dir, arrow_dir=arrow_dir)
    parquet_tables = results.get("parquet", {})
    arrow_tables = results.get("arrow", {})
    console.print(
        f"[green]✓ Exported {len(parquet_tables)} tables to Parquet (.parquet)[/green]"
    )
    console.print(
        f"[green]✓ Exported {len(arrow_tables)} tables to Apache Arrow IPC (.arrow)[/green]"
    )


@app.command("export-r")
def export_r_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        "-p",
        help="Processed tables directory",
    ),
    r_dir: Path = typer.Option(
        Path("data/processed/r"),
        "--r-dir",
        "-r",
        help="Directory to output .rds and .rda files",
    ),
    pkg_dir: Path = typer.Option(
        Path("r"),
        "--pkg-dir",
        help="Companion R package directory",
    ),
) -> None:
    """Export processed tables to native R formats (.rds, .rda) and scaffold companion R package."""
    console.print(
        "[bold blue]Exporting GBBO datasets to R formats and companion package...[/bold blue]"
    )
    results = export_to_r(
        processed_dir=processed_dir,
        r_output_dir=r_dir,
        r_pkg_dir=pkg_dir,
    )
    rds_tables = results.get("rds", {})
    rda_tables = results.get("rda", {})

    console.print(f"[green]✓ Exported {len(rds_tables)} RDS tables to {r_dir}[/green]")
    console.print(
        f"[green]✓ Exported {len(rda_tables)} RDA package tables to {Path(pkg_dir) / 'data'}[/green]"
    )
    console.print(
        f"[green]✓ Scaffolding and roxygen2 docs complete in {pkg_dir}/[/green]"
    )


@app.command("export-ai")
def export_ai_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        "-p",
        help="Directory with processed tables",
    ),
    ai_dir: Path = typer.Option(
        Path("data/ai"),
        "--ai-dir",
        "-a",
        help="Target AI export directory",
    ),
) -> None:
    """Export processed datasets into AI training formats (Chat SFT JSONL, RAG corpus, and benchmark suite)."""
    console.print(
        f"[bold blue]Exporting AI fine-tuning datasets and RAG corpus to {ai_dir}...[/bold blue]"
    )
    results = export_ai(processed_dir=processed_dir, ai_dir=ai_dir)
    for name, path in results.items():
        console.print(f"  [green]✓ {name}: {path}[/green]")
    console.print("[bold green]✓ AI training corpora export complete.[/bold green]")


@app.command("eval-benchmark")
def eval_benchmark_cmd(
    benchmark_file: Path = typer.Option(
        Path("data/ai/gbbo_benchmark_suite.jsonl"),
        "--benchmark-file",
        "-b",
        help="Path to benchmark JSONL file",
    ),
) -> None:
    """Run evaluation benchmark against ground truth rubrics and print score summary."""
    console.print(
        f"[bold blue]Evaluating GBBO benchmark suite ({benchmark_file})...[/bold blue]"
    )
    suite = BenchmarkSuite(benchmark_file=benchmark_file)
    summary = suite.evaluate_benchmark()
    suite.render_summary(summary)
    console.print(
        f"[bold green]✓ Benchmark complete: {summary['total_passed']}/{summary['total_questions']} "
        f"passed ({summary['pass_rate'] * 100:.1f}%), avg score: {summary['average_score'] * 100:.1f}%[/bold green]"
    )


@app.command("publish-hf")
def publish_hf_cmd(
    repo_id: str | None = typer.Option(
        None,
        "--repo-id",
        "-r",
        help="Hugging Face repository ID (e.g. user/the-great-british-bake-off)",
    ),
    token: str | None = typer.Option(
        None, "--token", "-t", help="Hugging Face API token"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Stage files locally without uploading to Hugging Face Hub",
    ),
    staging_dir: Path | None = typer.Option(
        None, "--staging-dir", "-s", help="Custom staging directory"
    ),
) -> None:
    """Publish and synchronize datasets and AI corpora to the Hugging Face Hub."""
    console.print("[bold blue]Preparing Hugging Face dataset release...[/bold blue]")
    try:
        res = publish_to_hf(
            repo_id=repo_id,
            token=token,
            dry_run=dry_run,
            staging_dir=staging_dir,
        )
        if dry_run:
            console.print(
                f"[green]✓ Dry-run complete: staged {res.get('files_count', 0)} files in {res.get('staging_dir')}[/green]"
            )
        else:
            console.print(
                f"[bold green]✓ Successfully published {res.get('files_count', 0)} files to {res.get('url')}[/bold green]"
            )
    except Exception as e:
        console.print(f"[red]✗ Hugging Face publishing failed: {e}[/red]")
        raise typer.Exit(code=1) from e


@app.command("predict")
def predict(
    series: int = typer.Option(
        17, "--series", "-s", help="Series number to predict (e.g. 17)."
    ),
    top: int = typer.Option(12, "--top", "-t", help="Number of top bakers to display."),
    detail: bool = typer.Option(
        False, "--detail", "-d", help="Display detailed factor metrics."
    ),
    output_json: Path | None = typer.Option(
        None, "--output", "-o", help="Optional path to export predictions JSON."
    ),
    update_docs: bool = typer.Option(
        False,
        "--update-docs",
        help="Update prediction documentation in README.md and docs/predictions.md.",
    ),
) -> None:
    """Predict Star Baker candidates, elimination risks, and series winner trajectories."""
    code = run_predict_cli(
        series=series,
        top=top,
        detail=detail,
        output_json=output_json,
        update_docs=update_docs,
        console=console,
    )
    if code != 0:
        raise typer.Exit(code=code)


@app.command("dashboard")
def dashboard(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run Streamlit on"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host interface to bind"),
    browser: bool = typer.Option(
        True, "--browser/--no-browser", help="Open browser on launch"
    ),
) -> None:
    """Launch interactive Streamlit web dashboard for GBBO series, bakers, and challenges."""
    import subprocess
    import sys

    try:
        import streamlit  # noqa: F401
    except ImportError:
        console.print(
            "[bold red]Streamlit is not installed.[/bold red]\n"
            "Please install dashboard dependencies via:\n"
            "  [cyan]uv add streamlit altair[/cyan]"
        )
        raise typer.Exit(code=1)

    app_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.address",
        host,
    ]
    if not browser:
        cmd.extend(["--server.headless", "true"])

    console.print(
        f"[bold green]Starting The Great British Bake Off Dashboard on http://{host}:{port}...[/bold green]"
    )
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")


@app.command("validate")
def validate_cmd(
    processed_dir: Path = typer.Option(
        Path("data/processed"),
        "--processed-dir",
        help="Directory with processed tables",
    ),
) -> None:
    """Run data integrity, relational constraints, and quality checks."""
    console.print("[bold blue]Running GBBO data validation checks...[/bold blue]")
    validator = DatasetValidator(processed_dir=processed_dir)
    report = validator.validate()

    color = (
        "green"
        if report["status"] == "PASS"
        else ("yellow" if report["status"] == "WARNING" else "red")
    )
    console.print(f"Validation Status: [{color}]{report['status']}[/{color}]")

    table = Table(title="Processed GBBO Tables Summary")
    table.add_column("Table", style="cyan")
    table.add_column("Row Count", style="magenta")

    for tbl, count in report.get("row_counts", {}).items():
        table.add_row(tbl, str(count))
    console.print(table)

    if report.get("issues"):
        console.print("[bold red]Issues / Warnings found:[/bold red]")
        for issue in report["issues"]:
            console.print(f"  - {issue}")
    if report["status"] == "FAIL":
        raise typer.Exit(code=1)


@app.command("package")
def package_cmd(
    output_dir: Path = typer.Option(
        Path("dist/release"),
        "--output-dir",
        "-o",
        help="Target directory for release bundles and checksums",
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Release version string (e.g. 0.1.0 or v0.1.0; defaults to pyproject.toml)",
    ),
    component: str = typer.Option(
        "all",
        "--component",
        "-c",
        help="Component to package: all, csv, parquet, ai, sqlite, r, python, tidytuesday, manifest, checksums",
    ),
) -> None:
    """Package segmented release archives for CSV, Parquet, AI JSONL, R, Python, and generate checksums."""
    console.print(
        f"[bold blue]Packaging release distribution assets (version: {version or 'auto'})...[/bold blue]"
    )
    packager = ReleasePackager(output_dir=output_dir, version=version)

    comp = component.lower()
    if comp == "all":
        results = packager.package_all()
    elif comp == "csv":
        results = {
            "csv": packager.package_csv(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "parquet":
        results = {
            "parquet": packager.package_parquet(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "ai":
        results = {
            "ai": packager.package_ai(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "sqlite":
        pkg = packager.package_sqlite()
        results = ({"sqlite": pkg} if pkg else {}) | {
            "checksums": packager.generate_checksums()
        }
    elif comp == "r":
        results = {
            "r": packager.package_r(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "python":
        results = {
            "python": packager.package_python(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "tidytuesday":
        results = {
            "tidytuesday": packager.package_tidytuesday(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "manifest":
        results = {
            "manifest": packager.generate_manifest(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "checksums":
        results = {"checksums": packager.generate_checksums()}
    else:
        console.print(
            f"[bold red]Unknown component '{component}'.[/bold red] Choose from: all, csv, parquet, ai, sqlite, r, python, tidytuesday, manifest, checksums."
        )
        raise typer.Exit(code=1)

    table = Table(title=f"Release Distribution Assets ({packager.tag_version})")
    table.add_column("Category", style="bold cyan")
    table.add_column("Asset File", style="bold white")
    table.add_column("Size", justify="right", style="green")

    for cat, item in results.items():
        if item is None:
            continue
        items_list = item if isinstance(item, list) else [item]
        for p in items_list:
            if isinstance(p, Path) and p.exists():
                size_kb = p.stat().st_size / 1024
                size_str = (
                    f"{size_kb / 1024:.2f} MB"
                    if size_kb >= 1024
                    else f"{size_kb:.1f} KB"
                )
                table.add_row(cat, p.name, size_str)

    console.print(table)
    console.print(
        f"[bold green]✓ Successfully packaged assets in {output_dir}[/bold green]"
    )


if __name__ == "__main__":
    app()
