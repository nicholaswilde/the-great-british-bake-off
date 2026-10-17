"""Test dataset gap auditor logic."""

from pathlib import Path

from gbbo_dataset.gap_auditor import DatasetGapAuditor


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
