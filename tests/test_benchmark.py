"""Unit tests for GBBO benchmark suite and evaluation harness."""

from __future__ import annotations

from pathlib import Path

from gbbo_dataset.exports.benchmark import BENCHMARK_ITEMS, BenchmarkSuite


def test_benchmark_suite_items_count_and_categories():
    """Verify curated benchmark suite meets issue criteria."""
    assert len(BENCHMARK_ITEMS) >= 40

    categories = {item["category"] for item in BENCHMARK_ITEMS}
    assert "trivia" in categories
    assert "challenge_reasoning" in categories
    assert "baking_rules" in categories
    assert "handshakes_and_accolades" in categories

    for item in BENCHMARK_ITEMS:
        assert "id" in item
        assert "question" in item
        assert "reference_answer" in item
        assert "key_facts" in item
        assert len(item["key_facts"]) > 0


def test_benchmark_suite_save_and_load(tmp_path: Path):
    """Test saving benchmark items to disk and reloading."""
    bench_file = tmp_path / "test_benchmark.jsonl"
    suite = BenchmarkSuite(benchmark_file=bench_file)

    saved_path = suite.save_default_suite()
    assert saved_path.exists()
    assert saved_path.stat().st_size > 0

    loaded = suite.load_suite()
    assert len(loaded) == len(BENCHMARK_ITEMS)
    assert loaded[0]["id"] == BENCHMARK_ITEMS[0]["id"]


def test_benchmark_scoring_rubric():
    """Test scoring responses against key facts."""
    item = {
        "id": "test-item-001",
        "question": "Who won Series 1?",
        "key_facts": ["Edd", "Kimber"],
    }

    # Full match
    score_full = BenchmarkSuite.score_response(item, "Edd Kimber won Series 1.")
    assert score_full["passed"] is True
    assert score_full["score"] == 1.0
    assert "Edd" in score_full["matched_facts"]
    assert "Kimber" in score_full["matched_facts"]

    # Partial match (1 of 2 = 0.5 -> passing threshold)
    score_partial = BenchmarkSuite.score_response(item, "Edd won Series 1.")
    assert score_partial["passed"] is True
    assert score_partial["score"] == 0.5
    assert "Edd" in score_partial["matched_facts"]
    assert "Kimber" in score_partial["missing_facts"]

    # No match
    score_zero = BenchmarkSuite.score_response(item, "John Doe won Series 1.")
    assert score_zero["passed"] is False
    assert score_zero["score"] == 0.0

    # Item without key facts
    empty_item = {"id": "test-empty", "key_facts": []}
    assert BenchmarkSuite.score_response(empty_item, "any answer")["passed"] is True


def test_benchmark_evaluation_runner(tmp_path: Path):
    """Test running evaluation harness and rendering summary."""
    bench_file = tmp_path / "bench.jsonl"
    suite = BenchmarkSuite(benchmark_file=bench_file)

    # Self-evaluation using reference answers
    summary = suite.evaluate_benchmark()
    assert summary["total_questions"] == len(BENCHMARK_ITEMS)
    assert summary["total_passed"] == len(BENCHMARK_ITEMS)
    assert summary["pass_rate"] == 1.0
    assert summary["average_score"] > 0.9

    # Test custom evaluation function
    def custom_eval(prompt: str) -> str:
        return "I do not know the answer."

    summary_custom = suite.evaluate_benchmark(eval_fn=custom_eval)
    assert summary_custom["pass_rate"] == 0.0

    # Render summary with Rich
    suite.render_summary(summary)
