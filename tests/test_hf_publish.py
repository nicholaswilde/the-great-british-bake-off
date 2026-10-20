"""Unit tests for Hugging Face Hub publication and staging."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from gbbo_dataset.exports.hf_publish import (
    HuggingFacePublisher,
    generate_dataset_card,
    get_project_version,
    publish_to_hf,
)


def test_generate_dataset_card():
    """Verify Hugging Face dataset card contains valid frontmatter and sections."""
    card = generate_dataset_card(version="0.1.0")
    assert card.startswith("---")
    assert (
        "pretty_name: The Great British Bake Off Dataset & AI Training Corpus" in card
    )
    assert "license: apache-2.0" in card
    assert "config_name: default" in card
    assert "config_name: seasons" in card
    assert "config_name: bakers" in card
    assert "config_name: episodes" in card
    assert "config_name: performances" in card
    assert "config_name: qa_finetuning" in card
    assert "config_name: knowledge_corpus" in card
    assert "config_name: benchmark_suite" in card
    assert "load_dataset" in card
    assert "@misc{" in card


def test_get_project_version(tmp_path: Path):
    """Test reading project version from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    assert get_project_version(tmp_path) == "1.2.3"

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert get_project_version(empty_dir) == "0.1.0"


def test_prepare_staging_directory(tmp_path: Path):
    """Test staging directory assembly with Parquet and converted AI files."""
    proc_dir = tmp_path / "processed"
    ai_dir = tmp_path / "ai"
    stage_dir = tmp_path / "staging"
    proc_dir.mkdir(parents=True, exist_ok=True)
    ai_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy parquet & csv
    df = pd.DataFrame([{"id": 1, "name": "Bake"}])
    for tbl in ["seasons", "bakers", "episodes", "performances"]:
        df.to_parquet(proc_dir / f"{tbl}.parquet")
        df.to_csv(proc_dir / f"{tbl}.csv", index=False)

    # Create dummy AI jsonl
    for f in [
        "gbbo_qa_finetuning.jsonl",
        "gbbo_knowledge_corpus.jsonl",
        "gbbo_benchmark_suite.jsonl",
    ]:
        (ai_dir / f).write_text('{"text": "Sample"}\n', encoding="utf-8")

    publisher = HuggingFacePublisher(
        repo_root=".",
        processed_dir=proc_dir,
        ai_dir=ai_dir,
    )
    staged = publisher.prepare_staging_directory(stage_dir)

    assert staged.exists()
    assert (stage_dir / "README.md").exists()
    assert (stage_dir / "data" / "seasons.parquet").exists()
    assert (stage_dir / "data" / "bakers.parquet").exists()
    assert (stage_dir / "data" / "episodes.parquet").exists()
    assert (stage_dir / "data" / "performances.parquet").exists()
    assert (stage_dir / "data" / "qa_finetuning.parquet").exists()
    assert (stage_dir / "data" / "knowledge_corpus.parquet").exists()
    assert (stage_dir / "data" / "benchmark_suite.parquet").exists()


def test_publish_dry_run(tmp_path: Path):
    """Test dry-run publishing returns file list and does not make network calls."""
    stage_dir = tmp_path / "stage_test"
    res = publish_to_hf(
        dry_run=True,
        staging_dir=stage_dir,
    )
    assert res["dry_run"] is True
    assert res["files_count"] > 0
    assert "README.md" in res["staged_files"]


def test_publish_missing_token_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify ValueError is raised when publishing without an auth token."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    monkeypatch.delenv("HF_REPO_ID", raising=False)

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "get_token", lambda: None)

    publisher = HuggingFacePublisher(repo_root=tmp_path)
    stage_dir = tmp_path / "stage_missing_token"

    with pytest.raises(ValueError, match="Hugging Face API token is required"):
        publisher.publish(dry_run=False, staging_dir=stage_dir, token=None)


def test_publish_dry_run_tempdir(monkeypatch: pytest.MonkeyPatch):
    """Test publish with dry_run and no explicit staging_dir creates tempdir."""
    res = publish_to_hf(dry_run=True, staging_dir=None)
    assert res["dry_run"] is True
    assert "gbbo_hf_stage_" in res["staging_dir"]


def test_prepare_staging_jsonl_corrupt(tmp_path: Path):
    """Test handling of corrupt JSONL file during parquet conversion."""
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir()
    (ai_dir / "gbbo_qa_finetuning.jsonl").write_text(
        "NOT VALID JSON\n", encoding="utf-8"
    )

    publisher = HuggingFacePublisher(
        repo_root=".",
        processed_dir=tmp_path / "proc",
        ai_dir=ai_dir,
    )
    stage_dir = tmp_path / "stage_corrupt"
    staged = publisher.prepare_staging_directory(stage_dir)
    assert staged.exists()
    assert not (stage_dir / "data" / "qa_finetuning.parquet").exists()


def test_publish_full_workflow_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test full Hugging Face publishing workflow with mocked HfApi."""
    import huggingface_hub

    calls = []

    class MockHfApi:
        def __init__(self, token=None):
            self.token = token

        def whoami(self, token=None):
            return {"name": "testbaker"}

        def create_repo(self, repo_id, repo_type, exist_ok, private):
            calls.append(("create_repo", repo_id, repo_type, exist_ok, private))

        def upload_folder(self, folder_path, repo_id, repo_type, commit_message):
            calls.append(("upload_folder", folder_path, repo_id, commit_message))

        def create_tag(self, repo_id, repo_type, tag, tag_message, exist_ok):
            calls.append(("create_tag", repo_id, tag))

    monkeypatch.setattr(huggingface_hub, "HfApi", MockHfApi)

    publisher = HuggingFacePublisher(repo_root=tmp_path)
    stage_dir = tmp_path / "stage_publish"

    # 1. With full repo_id
    res1 = publisher.publish(
        repo_id="custom_user/custom_repo",
        token="hf_secret_123",
        staging_dir=stage_dir,
        private=True,
        commit_message="Initial dataset release",
    )
    assert res1["repo_id"] == "custom_user/custom_repo"
    assert res1["private"] is True
    assert "https://huggingface.co/datasets/custom_user/custom_repo" in res1["url"]

    # 2. With partial repo_id (prepends whoami username)
    res2 = publisher.publish(
        repo_id="only-name",
        token="hf_secret_123",
        staging_dir=stage_dir,
    )
    assert res2["repo_id"] == "testbaker/only-name"

    # 3. With no repo_id (defaults to username/the-great-british-bake-off)
    res3 = publisher.publish(
        repo_id=None,
        token="hf_secret_123",
        staging_dir=stage_dir,
    )
    assert res3["repo_id"] == "testbaker/the-great-british-bake-off"


def test_publish_hf_exceptions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test whoami failure fallback and tag failure handling."""
    import huggingface_hub

    class FailingHfApi:
        def __init__(self, token=None):
            pass

        def whoami(self, token=None):
            raise RuntimeError("network failure")

        def create_repo(self, **kwargs):
            pass

        def upload_folder(self, **kwargs):
            pass

        def create_tag(self, **kwargs):
            raise RuntimeError("tag already exists")

    monkeypatch.setattr(huggingface_hub, "HfApi", FailingHfApi)

    publisher = HuggingFacePublisher(repo_root=tmp_path)
    stage_dir = tmp_path / "stage_err"

    res = publisher.publish(
        repo_id=None,
        token="token123",
        staging_dir=stage_dir,
    )
    assert res["repo_id"] == "nicholaswilde/the-great-british-bake-off"
