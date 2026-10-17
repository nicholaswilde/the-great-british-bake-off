"""Unit tests for AI training corpora exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gbbo_dataset.exports.ai_formats import (
    AIExportBuilder,
    export_ai,
    format_list_or_str,
    is_valid_val,
)


def test_format_helpers():
    """Test string and list formatting helper functions."""
    assert format_list_or_str(None) == ""
    assert format_list_or_str(float("nan")) == ""
    assert format_list_or_str("Nancy") == "Nancy"
    assert format_list_or_str(["Paul", "Mary"]) == "Paul and Mary"
    assert format_list_or_str(["Mel", "Sue", "Noel"]) == "Mel, Sue, and Noel"
    assert format_list_or_str(["Single"]) == "Single"

    assert is_valid_val(None) is False
    assert is_valid_val("") is False
    assert is_valid_val("nan") is False
    assert is_valid_val("Valid") is True
    assert is_valid_val(["Item"]) is True
    assert is_valid_val([]) is False


def test_ai_export_builder_qa_generation(tmp_path: Path):
    """Test generating Chat SFT fine-tuning conversation pairs."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    # Create mock seasons
    df_seasons = pd.DataFrame(
        [
            {
                "series_number": 1,
                "year": 2010,
                "winner": "Edd Kimber",
                "hosts": "Mel Giedroyc and Sue Perkins",
                "judges": "Mary Berry and Paul Hollywood",
                "network": "BBC Two",
                "location": "Various",
            }
        ]
    )
    df_seasons.to_csv(proc_dir / "seasons.csv", index=False)

    # Create mock bakers
    df_bakers = pd.DataFrame(
        [
            {
                "baker_id": "s01_edd",
                "series_number": 1,
                "name": "Edd Kimber",
                "age": 24,
                "occupation": "Debt collector",
                "hometown": "Bradford",
                "overall_placement": 1,
            }
        ]
    )
    df_bakers.to_csv(proc_dir / "bakers.csv", index=False)

    # Create mock episodes
    df_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cakes",
                "air_date": "2010-08-17",
            }
        ]
    )
    df_episodes.to_csv(proc_dir / "episodes.csv", index=False)

    # Create mock performances
    df_perfs = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_edd",
                "baker_id": "s01_edd",
                "episode_id": "s01e01",
                "signature_dish": "Cinnamon and Apple Cake",
                "technical_rank": 1,
                "showstopper_dish": "Tiered Celebration Cake",
                "result": "SAFE",
                "hollywood_handshake": True,
            }
        ]
    )
    df_perfs.to_csv(proc_dir / "performances.csv", index=False)

    builder = AIExportBuilder(processed_dir=proc_dir, ai_dir=tmp_path / "ai")
    qa_pairs = builder.generate_qa_pairs()

    assert len(qa_pairs) > 0
    for pair in qa_pairs:
        assert "messages" in pair
        assert len(pair["messages"]) == 3
        roles = [m["role"] for m in pair["messages"]]
        assert roles == ["system", "user", "assistant"]
        assert "metadata" in pair
        assert "category" in pair["metadata"]

    categories = {pair["metadata"]["category"] for pair in qa_pairs}
    assert "winners" in categories
    assert "judges_and_hosts" in categories
    assert "baker_demographics" in categories
    assert "episode_themes" in categories
    assert "challenge_descriptions" in categories
    assert "hollywood_handshakes" in categories


def test_ai_export_builder_knowledge_corpus(tmp_path: Path):
    """Test generating narrative RAG knowledge documents."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    df_seasons = pd.DataFrame(
        [
            {
                "series_number": 1,
                "year": 2010,
                "winner": "Edd Kimber",
                "hosts": "Mel and Sue",
                "judges": "Mary and Paul",
                "network": "BBC Two",
                "location": "Various",
            }
        ]
    )
    df_seasons.to_csv(proc_dir / "seasons.csv", index=False)

    df_bakers = pd.DataFrame(
        [
            {
                "baker_id": "s01_edd",
                "series_number": 1,
                "name": "Edd Kimber",
                "age": 24,
                "occupation": "Debt collector",
                "hometown": "Bradford",
                "overall_placement": 1,
            }
        ]
    )
    df_bakers.to_csv(proc_dir / "bakers.csv", index=False)

    df_episodes = pd.DataFrame(
        [
            {
                "episode_id": "s01e01",
                "series_number": 1,
                "episode_number": 1,
                "theme": "Cakes",
                "air_date": "2010-08-17",
            }
        ]
    )
    df_episodes.to_csv(proc_dir / "episodes.csv", index=False)

    df_perfs = pd.DataFrame(
        [
            {
                "performance_id": "s01e01_s01_edd",
                "baker_id": "s01_edd",
                "episode_id": "s01e01",
                "signature_dish": "Apple Cake",
                "technical_rank": 1,
                "showstopper_dish": "Celebration Cake",
                "result": "STAR_BAKER",
                "hollywood_handshake": False,
            }
        ]
    )
    df_perfs.to_csv(proc_dir / "performances.csv", index=False)

    builder = AIExportBuilder(processed_dir=proc_dir, ai_dir=tmp_path / "ai")
    corpus = builder.generate_knowledge_corpus()

    assert len(corpus) == 3  # 1 series + 1 episode + 1 baker
    types = {doc["metadata"]["type"] for doc in corpus}
    assert types == {"series_overview", "episode_narrative", "baker_profile"}

    for doc in corpus:
        assert "id" in doc
        assert "title" in doc
        assert "text" in doc
        assert len(doc["text"]) > 20


def test_export_all_creates_valid_jsonl(tmp_path: Path):
    """Test export_ai() writing complete valid JSONL datasets."""
    ai_dir = tmp_path / "ai"
    results = export_ai(processed_dir="data/processed", ai_dir=ai_dir)

    assert "qa_finetuning" in results
    assert "knowledge_corpus" in results
    assert "benchmark_suite" in results

    for path in results.values():
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                assert isinstance(item, dict)
