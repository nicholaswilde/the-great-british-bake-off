"""Test dataset gap auditor logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from gbbo_dataset.gap_auditor import ColumnGap, DatasetGapAuditor, main


def test_gap_auditor_runs():
    """Verify DatasetGapAuditor runs and identifies table metrics."""
    auditor = DatasetGapAuditor(processed_dir="data/processed")
    results = auditor.audit_all()

    assert "bakers" in results
    assert "episodes" in results
    assert "performances" in results

    bakers_gaps = {g.column_name: g for g in results["bakers"]}
    assert bakers_gaps["baker_id"].missing_count == 0
    assert bakers_gaps["baker_id"].severity == "OK"


def test_column_gap_properties():
    """Verify ColumnGap severity calculations and dictionary export."""
    gap_ok = ColumnGap(
        table_name="bakers",
        column_name="baker_id",
        total_rows=100,
        missing_count=0,
        affected_series={},
        sample_keys=[],
    )
    assert gap_ok.severity == "OK"
    assert not gap_ok.is_conditional
    assert gap_ok.to_dict()["severity"] == "OK"

    gap_cond = ColumnGap(
        table_name="performances",
        column_name="signature_dish",
        total_rows=100,
        missing_count=50,
        affected_series={1: 50},
        sample_keys=["s01e01_s01_edd"],
    )
    assert gap_cond.is_conditional
    assert gap_cond.severity == "CONDITIONAL"

    gap_low = ColumnGap(
        table_name="bakers",
        column_name="name",
        total_rows=100,
        missing_count=2,
        affected_series={1: 2},
        sample_keys=["s01_edd"],
    )
    assert gap_low.severity == "LOW"

    gap_med = ColumnGap(
        table_name="bakers",
        column_name="name",
        total_rows=100,
        missing_count=15,
        affected_series={1: 15},
        sample_keys=["s01_edd"],
    )
    assert gap_med.severity == "MEDIUM"

    gap_high = ColumnGap(
        table_name="bakers",
        column_name="name",
        total_rows=100,
        missing_count=50,
        affected_series={1: 50},
        sample_keys=["s01_edd"],
    )
    assert gap_high.severity == "HIGH"


def test_gap_auditor_print_and_nonexistent_table():
    """Verify print_summary and missing table handling."""
    auditor = DatasetGapAuditor(processed_dir="data/processed")
    assert auditor.audit_table("non_existent_table") == []

    results = auditor.audit_all()
    # Print without detail
    auditor.print_summary(results, detail=False)
    # Print with detail
    auditor.print_summary(results, detail=True)


def test_gap_auditor_markdown_export(tmp_path: Path):
    """Verify Markdown report export."""
    auditor = DatasetGapAuditor(processed_dir="data/processed")
    results = auditor.audit_all()
    md_path = tmp_path / "gap_report.md"
    auditor.export_markdown(results, md_path)

    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "Great British Bake Off" in content
    assert "`bakers`" in content


def test_gap_auditor_main_cli(tmp_path: Path):
    """Verify gap auditor CLI main entrypoint."""
    md_out = tmp_path / "report.md"
    with patch(
        "sys.argv",
        [
            "gbbo-gap-audit",
            "--processed-dir",
            "data/processed",
            "--table",
            "bakers",
            "--detail",
            "--export-md",
            str(md_out),
        ],
    ):
        main()
        assert md_out.exists()
