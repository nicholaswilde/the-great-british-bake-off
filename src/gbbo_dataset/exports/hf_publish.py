"""Hugging Face Hub publisher for The Great British Bake Off tidy datasets and AI training corpora."""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "bakers",
    "episodes",
    "performances",
]

AI_FILES = [
    ("gbbo_qa_finetuning.jsonl", "qa_finetuning.parquet"),
    ("gbbo_knowledge_corpus.jsonl", "knowledge_corpus.parquet"),
    ("gbbo_benchmark_suite.jsonl", "benchmark_suite.parquet"),
]


def get_project_version(repo_root: Path) -> str:
    """Extract project version from pyproject.toml."""
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.1.0"


def generate_dataset_card(version: str = "0.1.0") -> str:
    """Generate Hugging Face Dataset Card (README.md) with complete YAML frontmatter."""
    return f"""---
annotations_creators:
  - no-annotation
language_creators:
  - found
  - expert-generated
language:
  - en
license: apache-2.0
multilinguality:
  - monolingual
size_categories:
  - 1K<n<10K
source_datasets:
  - original
task_categories:
  - question-answering
  - text-generation
  - tabular-classification
  - tabular-regression
task_ids: []
pretty_name: The Great British Bake Off Dataset & AI Training Corpus
tags:
  - reality-tv
  - television
  - baking
  - tidy-data
  - tidytuesday
  - the-great-british-bake-off
  - tabular
  - gbbo
configs:
  - config_name: default
    data_files: "data/seasons.parquet"
  - config_name: seasons
    data_files: "data/seasons.parquet"
  - config_name: bakers
    data_files: "data/bakers.parquet"
  - config_name: episodes
    data_files: "data/episodes.parquet"
  - config_name: performances
    data_files: "data/performances.parquet"
  - config_name: qa_finetuning
    data_files: "data/qa_finetuning.parquet"
  - config_name: knowledge_corpus
    data_files: "data/knowledge_corpus.parquet"
  - config_name: benchmark_suite
    data_files: "data/benchmark_suite.parquet"
---

# 🍰 The Great British Bake Off Dataset & AI Training Corpus (v{version})

A comprehensive tidy relational dataset and AI instruction-tuning corpus for the television competition series **The Great British Bake Off** (broadcast in North America as *The Great British Baking Show*).

This dataset structures every series, baker, episode, signature bake, technical challenge, showstopper, Star Baker accolade, and Hollywood Handshake into normalized relational tables alongside curated Chat SFT instruction pairs, RAG knowledge corpora, and evaluation benchmarks.

- **GitHub Repository**: [nicholaswilde/the-great-british-bake-off](https://github.com/nicholaswilde/the-great-british-bake-off)
- **License**: Apache 2.0
- **Release Version**: {version}

---

## 🚀 Quick Start with `datasets`

Install the Hugging Face `datasets` library:
```bash
pip install datasets
```

### Loading Tabular Configurations

Each relational table is available as an independent configuration:

```python
from datasets import load_dataset

# Load seasons summary table
seasons = load_dataset("nicholaswilde/the-great-british-bake-off", "seasons", split="train")

# Load bakers demographic profile and placements
bakers = load_dataset("nicholaswilde/the-great-british-bake-off", "bakers", split="train")

# Load challenge-by-challenge performances and dishes
performances = load_dataset("nicholaswilde/the-great-british-bake-off", "performances", split="train")

# Convert to Pandas DataFrame
df_bakers = bakers.to_pandas()
print(df_bakers[["name", "series_number", "overall_placement", "hometown"]].head())
```

### Loading AI Fine-Tuning & Knowledge Corpora

```python
# Load multi-turn Chat SFT conversational pairs
qa_ds = load_dataset("nicholaswilde/the-great-british-bake-off", "qa_finetuning", split="train")
print(qa_ds[0]["messages"])

# Load narrative knowledge documents for RAG vector embeddings
knowledge_ds = load_dataset("nicholaswilde/the-great-british-bake-off", "knowledge_corpus", split="train")
print(knowledge_ds[0]["text"][:250])

# Load benchmark evaluation suite
bench_ds = load_dataset("nicholaswilde/the-great-british-bake-off", "benchmark_suite", split="train")
print(bench_ds[0]["question"])
```

---

## 📊 Dataset Configurations & Schema

The dataset provides 8 configurations:

| Config Name | File | Description |
| :--- | :--- | :--- |
| `seasons` | `data/seasons.parquet` | Series summary: winner, year, judges, presenters, original network, location, and streaming collection IDs. |
| `bakers` | `data/bakers.parquet` | Baker demographics: age, hometown, occupation, overall placement, and official portrait URLs. |
| `episodes` | `data/episodes.parquet` | Episode records: series number, episode number, theme, air date, and challenge time allocations. |
| `performances` | `data/performances.parquet` | Challenge outcomes: signature bake, technical rank, showstopper bake, episode result, and Hollywood Handshakes. |
| `qa_finetuning` | `data/gbbo_qa_finetuning.jsonl` | Multi-turn instruction fine-tuning dataset formatted for OpenAI / Gemini SFT. |
| `knowledge_corpus` | `data/gbbo_knowledge_corpus.jsonl` | Chunked narrative documents with metadata for vector search and RAG retrieval. |
| `benchmark_suite` | `data/gbbo_benchmark_suite.jsonl` | Curated evaluation questions with ground truth rubrics and keyword fact verification. |

---

## 📖 Citation

If you use this dataset in your research or applications, please cite:

```bibtex
@misc{{wilde_gbbo_2026,
  author       = {{Nicholas Wilde}},
  title        = {{The Great British Bake Off Dataset & AI Training Corpus}},
  year         = {{2026}},
  version      = {{{version}}},
  publisher    = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/datasets/nicholaswilde/the-great-british-bake-off}}}}
}}
```
"""


class HuggingFacePublisher:
    """Manages staging and synchronization of datasets and AI corpora to the Hugging Face Hub."""

    def __init__(
        self,
        repo_root: Path | str = ".",
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
        docs_dir: Path | str = "docs",
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.processed_dir = self.repo_root / processed_dir
        self.ai_dir = self.repo_root / ai_dir
        self.docs_dir = self.repo_root / docs_dir
        self.version = get_project_version(self.repo_root)

    def prepare_staging_directory(self, target_dir: Path | str) -> Path:
        """Stage all parquet tables, AI corpora, dataset card, and metadata into a directory."""
        stage_path = Path(target_dir).resolve()
        stage_path.mkdir(parents=True, exist_ok=True)
        data_dir = stage_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy Parquet files
        for table in TABLES:
            parquet_src = self.processed_dir / f"{table}.parquet"
            if parquet_src.exists():
                shutil.copy2(parquet_src, data_dir / f"{table}.parquet")
            else:
                logger.warning("Parquet table not found: %s", parquet_src)

            csv_src = self.processed_dir / f"{table}.csv"
            if csv_src.exists():
                shutil.copy2(csv_src, data_dir / f"{table}.csv")

        # 2. Copy AI JSONL files and convert to Parquet for native Hub loading
        for jsonl_name, parquet_name in AI_FILES:
            ai_src = self.ai_dir / jsonl_name
            if ai_src.exists():
                shutil.copy2(ai_src, data_dir / jsonl_name)
                try:
                    df = pd.read_json(ai_src, lines=True)
                    df.to_parquet(data_dir / parquet_name, engine="pyarrow")
                except Exception as e:
                    logger.warning("Could not convert %s to parquet: %s", jsonl_name, e)
            else:
                logger.warning("AI corpus file not found: %s", ai_src)

        # 3. Write Dataset Card (README.md)
        card_content = generate_dataset_card(version=self.version)
        (stage_path / "README.md").write_text(card_content, encoding="utf-8")

        # 4. Copy supporting documentation and manifests
        support_files = [
            (self.repo_root / "LICENSE", "LICENSE"),
            (self.repo_root / "llms.txt", "llms.txt"),
            (self.repo_root / "llms-full.txt", "llms-full.txt"),
        ]
        for src_path, dest_name in support_files:
            if src_path.exists():
                shutil.copy2(src_path, stage_path / dest_name)

        return stage_path

    def publish(
        self,
        repo_id: str | None = None,
        token: str | None = None,
        private: bool = False,
        commit_message: str | None = None,
        staging_dir: Path | str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Publish the staged dataset to Hugging Face Hub."""
        if staging_dir:
            stage_path = Path(staging_dir)
            self.prepare_staging_directory(stage_path)
        else:
            temp_dir = tempfile.mkdtemp(prefix="gbbo_hf_stage_")
            stage_path = Path(temp_dir)
            self.prepare_staging_directory(stage_path)

        staged_files = [
            str(p.relative_to(stage_path)) for p in stage_path.rglob("*") if p.is_file()
        ]

        if dry_run:
            logger.info(
                "Dry-run mode: staged %d files to %s without publishing",
                len(staged_files),
                stage_path,
            )
            return {
                "dry_run": True,
                "staging_dir": str(stage_path),
                "files_count": len(staged_files),
                "staged_files": staged_files,
                "version": self.version,
            }

        try:
            from huggingface_hub import HfApi
        except ImportError as err:
            raise ImportError(
                "huggingface_hub is required to publish to Hugging Face. "
                "Install it with `uv add huggingface_hub` or specify --dry-run."
            ) from err

        auth_token = (
            token
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )
        if not auth_token:
            try:
                from huggingface_hub import get_token

                auth_token = get_token()
            except Exception as e:
                logger.debug("Could not retrieve stored Hugging Face token: %s", e)

        if not auth_token:
            raise ValueError(
                "Hugging Face API token is required to publish to the Hub. "
                "Set the HF_TOKEN environment variable, pass --token, or specify --dry-run."
            )

        api = HfApi(token=auth_token)

        target_repo = repo_id or os.environ.get("HF_REPO_ID")
        if not target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/the-great-british-bake-off"
            except Exception as e:
                logger.warning("Could not auto-determine Hugging Face username: %s", e)
                target_repo = "nicholaswilde/the-great-british-bake-off"
        elif "/" not in target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/{target_repo}"
            except Exception as e:
                logger.debug("Could not prepend username to repository ID: %s", e)

        logger.info("Target Hugging Face repository: %s", target_repo)

        api.create_repo(
            repo_id=target_repo,
            repo_type="dataset",
            exist_ok=True,
            private=private,
        )

        msg = (
            commit_message or f"Sync The Great British Bake Off dataset v{self.version}"
        )

        api.upload_folder(
            folder_path=str(stage_path),
            repo_id=target_repo,
            repo_type="dataset",
            commit_message=msg,
        )

        if self.version:
            try:
                api.create_tag(
                    repo_id=target_repo,
                    repo_type="dataset",
                    tag=f"v{self.version}",
                    tag_message=f"Release v{self.version}",
                    exist_ok=True,
                )
            except Exception as e:
                logger.debug("Could not create tag on Hugging Face Hub: %s", e)

        dataset_url = f"https://huggingface.co/datasets/{target_repo}"
        logger.info("Successfully published dataset to %s", dataset_url)

        return {
            "repo_id": target_repo,
            "url": dataset_url,
            "version": self.version,
            "private": private,
            "files_count": len(staged_files),
        }


def publish_to_hf(
    repo_id: str | None = None,
    token: str | None = None,
    dry_run: bool = False,
    staging_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Helper function to publish dataset to Hugging Face Hub."""
    publisher = HuggingFacePublisher()
    return publisher.publish(
        repo_id=repo_id,
        token=token,
        dry_run=dry_run,
        staging_dir=staging_dir,
    )
