#!/usr/bin/env python3
"""Dataset Gap Auditor for The Great British Bake Off (GBBO) dataset.

Identifies missing cells, null rates, series-level data gaps,
and completeness metrics across all processed tables.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "bakers",
    "episodes",
    "performances",
]

DIAGNOSIS_HINTS: dict[tuple[str, str], str] = {
    ("episodes", "air_date"): (
        "Episode air dates recorded in Wikipedia 'Ratings' section; requires parsing ratings table."
    ),
    ("performances", "technical_rank"): (
        "Some series finals (e.g. Series 1) omitted technical challenges, or judges only ranked top/bottom bakers."
    ),
    ("bakers", "age"): (
        "Baker age at time of competition occasionally unlisted in early source summaries."
    ),
    ("bakers", "occupation"): ("Baker occupation unlisted or retired."),
    ("bakers", "hometown"): ("Hometown unrecorded or broad region specified."),
}

# Columns conditionally populated by design (not considered data quality defects)
CONDITIONAL_COLUMNS: set[tuple[str, str]] = {
    ("performances", "technical_rank"),
    ("performances", "signature_dish"),
    ("performances", "showstopper_dish"),
    ("episodes", "technical_time_min"),
    ("episodes", "showstopper_time_min"),
    ("seasons", "pbs_season"),
    ("seasons", "netflix_collection"),
    ("seasons", "roku_season"),
}


class ColumnGap:
    """Missing data metrics for a single column."""

    def __init__(
        self,
        table_name: str,
        column_name: str,
        total_rows: int,
        missing_count: int,
        affected_series: dict[int, int],
        sample_keys: list[str],
        diagnosis_hint: str = "",
    ) -> None:
        self.table_name = table_name
        self.column_name = column_name
        self.total_rows = total_rows
        self.missing_count = missing_count
        self.missing_pct = (missing_count / total_rows * 100) if total_rows else 0.0
        self.affected_series = affected_series
        self.sample_keys = sample_keys
        self.diagnosis_hint = diagnosis_hint

    @property
    def is_conditional(self) -> bool:
        return (self.table_name, self.column_name) in CONDITIONAL_COLUMNS

    @property
    def severity(self) -> str:
        if self.missing_pct == 0:
            return "OK"
        if self.is_conditional:
            return "CONDITIONAL"
        if self.missing_pct < 5.0:
            return "LOW"
        if self.missing_pct < 20.0:
            return "MEDIUM"
        return "HIGH"

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table_name,
            "column": self.column_name,
            "total_rows": self.total_rows,
            "missing_count": self.missing_count,
            "missing_pct": round(self.missing_pct, 2),
            "severity": self.severity,
            "is_conditional": self.is_conditional,
            "affected_series": self.affected_series,
            "sample_keys": self.sample_keys,
            "diagnosis_hint": self.diagnosis_hint,
        }


class DatasetGapAuditor:
    """Audits processed GBBO tables for completeness and schema gaps."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        series: int | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.series = series

    def load_table(self, name: str) -> pd.DataFrame:
        """Load JSON or CSV table."""
        json_path = self.processed_dir / f"{name}.json"
        if json_path.exists():
            df = pd.read_json(json_path)
        else:
            csv_path = self.processed_dir / f"{name}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
            else:
                return pd.DataFrame()

        if self.series is not None:
            if "series_number" in df.columns:
                df = df[df["series_number"] == self.series]
            elif "episode_id" in df.columns:
                prefix = f"s{self.series:02d}"
                df = df[
                    df["episode_id"].astype(str).str.startswith(prefix)
                    | df["episode_id"].astype(str).str.startswith(f"s{self.series}e")
                ]
        return df

    def audit_column(
        self, table_name: str, column_name: str, df: pd.DataFrame
    ) -> ColumnGap:
        """Analyze missingness and series distribution for a column."""
        col = df[column_name]
        is_missing = col.isna() | (
            col.astype(str).str.strip().isin(["", "nan", "None"])
        )
        missing_count = int(is_missing.sum())
        total_rows = len(df)

        affected_series: dict[int, int] = {}
        sample_keys: list[str] = []

        if missing_count > 0:
            missing_rows = df[is_missing]
            if "series_number" in df.columns:
                series_counts = missing_rows["series_number"].value_counts().to_dict()
                affected_series = {
                    int(s): int(cnt) for s, cnt in sorted(series_counts.items())
                }

            for _, row in missing_rows.head(3).iterrows():
                key_id = str(
                    row.get("baker_id")
                    or row.get("episode_id")
                    or row.get("performance_id")
                    or row.name
                )
                sample_keys.append(key_id)

        hint = DIAGNOSIS_HINTS.get((table_name, column_name), "")

        return ColumnGap(
            table_name=table_name,
            column_name=column_name,
            total_rows=total_rows,
            missing_count=missing_count,
            affected_series=affected_series,
            sample_keys=sample_keys,
            diagnosis_hint=hint,
        )

    def audit_table(self, table_name: str) -> list[ColumnGap]:
        """Audit all columns in a table."""
        df = self.load_table(table_name)
        if df.empty:
            return []
        return [self.audit_column(table_name, col, df) for col in df.columns]

    def audit_all(self) -> dict[str, list[ColumnGap]]:
        """Audit all tables in dataset."""
        results: dict[str, list[ColumnGap]] = {}
        for t in TABLES:
            gaps = self.audit_table(t)
            if gaps:
                results[t] = gaps
        return results

    def print_summary(
        self, results: dict[str, list[ColumnGap]], detail: bool = False
    ) -> None:
        """Print rich console report."""
        console = Console()

        console.print(
            Panel.fit(
                "[bold cyan]The Great British Bake Off — Dataset Gap Audit[/bold cyan]\n"
                "[dim]Complete cell missingness and schema health overview[/dim]",
                border_style="cyan",
            )
        )

        # Overview Table
        summary_table = Table(
            title="Table-Level Completeness Summary",
            show_header=True,
            header_style="bold magenta",
        )
        summary_table.add_column("Table", style="cyan")
        summary_table.add_column("Rows", justify="right")
        summary_table.add_column("Columns", justify="right")
        summary_table.add_column("Total Cells", justify="right")
        summary_table.add_column("Missing Cells", justify="right")
        summary_table.add_column("Completeness", justify="right")
        summary_table.add_column("Status", justify="center")

        total_cells_all = 0
        total_missing_all = 0

        for table_name, gaps in results.items():
            if not gaps:
                continue
            rows = gaps[0].total_rows
            cols = len(gaps)
            table_cells = rows * cols
            table_missing = sum(g.missing_count for g in gaps if not g.is_conditional)
            table_comp = 100.0 - (
                (table_missing / table_cells * 100) if table_cells else 0.0
            )

            total_cells_all += table_cells
            total_missing_all += table_missing

            status_style = (
                "green" if table_comp >= 95 else "yellow" if table_comp >= 80 else "red"
            )
            status_text = (
                "PASS" if table_comp >= 95 else "WARN" if table_comp >= 80 else "CRIT"
            )

            summary_table.add_row(
                table_name,
                str(rows),
                str(cols),
                str(table_cells),
                str(table_missing),
                f"[{status_style}]{table_comp:.1f}%[/{status_style}]",
                f"[{status_style}]{status_text}[/{status_style}]",
            )

        console.print(summary_table)

        # Detailed breakdown
        if detail:
            for table_name, gaps in results.items():
                detail_table = Table(
                    title=f"Column Detail: {table_name}",
                    show_header=True,
                    header_style="bold yellow",
                )
                detail_table.add_column("Column", style="bold")
                detail_table.add_column("Missing", justify="right")
                detail_table.add_column("% Missing", justify="right")
                detail_table.add_column("Severity", justify="center")
                detail_table.add_column("Diagnosis / Sample Keys")

                for g in gaps:
                    sev_style = {
                        "OK": "green",
                        "LOW": "blue",
                        "MEDIUM": "yellow",
                        "HIGH": "red bold",
                        "CONDITIONAL": "dim cyan",
                    }.get(g.severity, "white")

                    notes = g.diagnosis_hint
                    if g.sample_keys:
                        notes += f" | Samples: {', '.join(g.sample_keys[:2])}"

                    detail_table.add_row(
                        g.column_name,
                        str(g.missing_count),
                        f"{g.missing_pct:.1f}%",
                        f"[{sev_style}]{g.severity}[/{sev_style}]",
                        notes.strip(),
                    )
                console.print(detail_table)

    def export_markdown(
        self, results: dict[str, list[ColumnGap]], output_path: Path
    ) -> None:
        """Export gap audit report as GitHub-flavored Markdown."""
        lines = [
            "# Great British Bake Off — Dataset Gap Audit Report\n",
            "## Summary Table\n",
            "| Table | Rows | Columns | Missing Cells | Completeness | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for table_name, gaps in results.items():
            if not gaps:
                continue
            rows = gaps[0].total_rows
            cols = len(gaps)
            cells = rows * cols
            missing = sum(g.missing_count for g in gaps if not g.is_conditional)
            comp = 100.0 - ((missing / cells * 100) if cells else 0.0)
            status = "PASS" if comp >= 95 else "WARN" if comp >= 80 else "CRIT"
            lines.append(
                f"| `{table_name}` | {rows} | {cols} | {missing} | {comp:.1f}% | **{status}** |"
            )

        lines.append("\n## Column Gaps Detail\n")
        for table_name, gaps in results.items():
            lines.append(f"### Table: `{table_name}`\n")
            lines.append("| Column | Missing | % Missing | Severity | Notes |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for g in gaps:
                notes = g.diagnosis_hint or (
                    "Conditional challenge by design"
                    if g.is_conditional
                    else "Complete"
                )
                lines.append(
                    f"| `{g.column_name}` | {g.missing_count} | {g.missing_pct:.1f}% | {g.severity} | {notes} |"
                )
            lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("Exported gap audit markdown report to %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Audit GBBO dataset for gaps and missing data."
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Processed data directory",
    )
    parser.add_argument(
        "--table", "-t", type=str, default=None, help="Filter to specific table"
    )
    parser.add_argument(
        "--series", "-s", type=int, default=None, help="Filter to specific series"
    )
    parser.add_argument(
        "--detail", "-d", action="store_true", help="Print column-level details"
    )
    parser.add_argument(
        "--export-md", type=Path, default=None, help="Export Markdown report to path"
    )

    args = parser.parse_args()

    auditor = DatasetGapAuditor(processed_dir=args.processed_dir, series=args.series)
    if args.table:
        gaps = auditor.audit_table(args.table)
        results = {args.table: gaps} if gaps else {}
    else:
        results = auditor.audit_all()

    auditor.print_summary(results, detail=args.detail)

    if args.export_md:
        auditor.export_markdown(results, args.export_md)


if __name__ == "__main__":
    main()
