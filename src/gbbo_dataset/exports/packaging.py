"""Packaging module for creating segmented release assets and distribution bundles for GBBO."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TABLE_NAMES = [
    "seasons",
    "bakers",
    "episodes",
    "performances",
]


def get_project_version(root_dir: Path | str = ".") -> str:
    """Extract project version from pyproject.toml or r/DESCRIPTION."""
    root = Path(root_dir)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)

    r_desc = root / "r" / "DESCRIPTION"
    if r_desc.exists():
        content = r_desc.read_text(encoding="utf-8")
        match = re.search(r"Version:\s*([^\n\r]+)", content)
        if match:
            return match.group(1).strip()

    return "0.1.0"


class ReleasePackager:
    """Builds segmented release bundles for CSV, Parquet, AI JSONL, SQLite, R, and Python."""

    def __init__(
        self,
        output_dir: Path | str = "dist/release",
        version: str | None = None,
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
        r_dir: Path | str = "r",
        docs_dir: Path | str = "docs",
        repo_root: Path | str = ".",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.repo_root = Path(repo_root)
        self.processed_dir = Path(processed_dir)
        self.ai_dir = Path(ai_dir)
        self.r_dir = Path(r_dir)
        self.docs_dir = Path(docs_dir)

        # Resolve version: explicit arg -> GITHUB_REF_NAME -> pyproject.toml
        raw_version = (
            version
            or os.environ.get("RELEASE_VERSION")
            or os.environ.get("GITHUB_REF_NAME")
            or get_project_version(self.repo_root)
        )
        self.clean_version = raw_version.lstrip("v")
        self.tag_version = f"v{self.clean_version}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def package_csv(self) -> Path:
        """Package all tidy CSV tables and documentation into a zip bundle."""
        archive_name = f"gbbo-dataset-csv-{self.clean_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building CSV bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for table in TABLE_NAMES:
                csv_file = self.processed_dir / f"{table}.csv"
                if csv_file.exists():
                    zf.write(csv_file, arcname=f"csv/{csv_file.name}")

            for doc_file in [
                self.docs_dir / "data_dictionary.md",
                self.docs_dir / "dataset_gaps.md",
                self.repo_root / "LICENSE",
                self.repo_root / "CITATION.cff",
                self.repo_root / "README.md",
            ]:
                if doc_file.exists():
                    zf.write(doc_file, arcname=doc_file.name)

        return target_path

    def package_parquet(self) -> Path:
        """Package all Parquet tables and documentation into a zip bundle."""
        archive_name = f"gbbo-dataset-parquet-{self.clean_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building Parquet bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for table in TABLE_NAMES:
                parquet_file = self.processed_dir / f"{table}.parquet"
                if parquet_file.exists():
                    zf.write(parquet_file, arcname=f"parquet/{parquet_file.name}")

            for doc_file in [
                self.docs_dir / "data_dictionary.md",
                self.docs_dir / "dataset_gaps.md",
                self.repo_root / "LICENSE",
                self.repo_root / "CITATION.cff",
                self.repo_root / "README.md",
            ]:
                if doc_file.exists():
                    zf.write(doc_file, arcname=doc_file.name)

        return target_path

    def package_ai(self) -> Path:
        """Package AI fine-tuning datasets and knowledge corpora into a zip bundle."""
        archive_name = f"gbbo-dataset-ai-{self.clean_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building AI bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            ai_files = [
                "gbbo_qa_finetuning.jsonl",
                "gbbo_knowledge_corpus.jsonl",
                "gbbo_benchmark_suite.jsonl",
            ]
            for file_name in ai_files:
                f_path = self.ai_dir / file_name
                if f_path.exists():
                    zf.write(f_path, arcname=f"ai/{file_name}")

            for llm_file in ["llms.txt", "llms-full.txt"]:
                llm_path = self.repo_root / llm_file
                if llm_path.exists():
                    zf.write(llm_path, arcname=llm_file)

            for doc_file in [
                self.docs_dir / "data_dictionary.md",
                self.repo_root / "LICENSE",
                self.repo_root / "CITATION.cff",
                self.repo_root / "README.md",
            ]:
                if doc_file.exists():
                    zf.write(doc_file, arcname=doc_file.name)

        return target_path

    def package_sqlite(self) -> Path | None:
        """Package SQLite database into a zip bundle if it exists."""
        db_path = self.processed_dir / "gbbo.db"
        if not db_path.exists():
            return None

        archive_name = f"gbbo-dataset-sqlite-{self.clean_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building SQLite bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, arcname="gbbo.db")

            for doc_file in [
                self.docs_dir / "data_dictionary.md",
                self.repo_root / "LICENSE",
                self.repo_root / "CITATION.cff",
                self.repo_root / "README.md",
            ]:
                if doc_file.exists():
                    zf.write(doc_file, arcname=doc_file.name)

        return target_path

    def package_tidytuesday(self) -> Path:
        """Package TidyTuesday submission bundle (CSVs, scripts, and documentation)."""
        archive_name = f"gbbo-dataset-tidytuesday-{self.clean_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building TidyTuesday bundle: %s", target_path)

        tidytuesday_dir = self.repo_root / "tidytuesday"
        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for table in TABLE_NAMES:
                csv_file = self.processed_dir / f"{table}.csv"
                if csv_file.exists():
                    zf.write(csv_file, arcname=f"data/{csv_file.name}")

            for tt_file in [
                "readme.md",
                "cleaning.R",
                "exploration.R",
                "submission_issue.md",
            ]:
                p = tidytuesday_dir / tt_file
                if p.exists():
                    zf.write(p, arcname=tt_file)

            for doc_file in [
                self.docs_dir / "data_dictionary.md",
                self.repo_root / "LICENSE",
                self.repo_root / "CITATION.cff",
            ]:
                if doc_file.exists():
                    zf.write(doc_file, arcname=doc_file.name)

        return target_path

    def package_r(self) -> Path:
        """Build CRAN-compliant R source package tarball."""
        archive_name = f"gbbo_{self.clean_version}.tar.gz"
        target_path = self.output_dir / archive_name
        logger.info("Building R source package: %s", target_path)

        # Check if R CMD build is available
        r_bin = shutil.which("R")
        if r_bin:
            try:
                cmd = [
                    r_bin,
                    "CMD",
                    "build",
                    str(self.r_dir),
                    "--no-build-vignettes",
                    "--no-manual",
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    cwd=str(self.output_dir),
                    capture_output=True,
                    text=True,
                )
                built_tarball = self.output_dir / archive_name
                if built_tarball.exists():
                    return built_tarball
            except Exception as e:
                logger.warning(
                    "R CMD build failed (%s); falling back to pure Python packaging", e
                )

        # Pure Python fallback: create the package tarball
        pkg_name = "gbbo"
        excluded_patterns = {
            ".git",
            ".Rhistory",
            ".RData",
            ".DS_Store",
            "__pycache__",
        }

        with tarfile.open(target_path, "w:gz") as tf:
            for root, dirs, files in os.walk(self.r_dir):
                dirs[:] = [d for d in dirs if d not in excluded_patterns]
                rel_root = Path(root).relative_to(self.r_dir)

                for file in files:
                    if file in excluded_patterns or file.endswith("~"):
                        continue
                    file_path = Path(root) / file
                    arcname = Path(pkg_name) / rel_root / file
                    tf.add(file_path, arcname=str(arcname))

            license_file = self.repo_root / "LICENSE"
            if license_file.exists() and not (self.r_dir / "LICENSE").exists():
                tf.add(license_file, arcname=f"{pkg_name}/LICENSE")

        return target_path

    def package_python(self) -> list[Path]:
        """Build Python wheel and source distribution using uv build."""
        logger.info("Building Python distribution with uv build")
        built_files: list[Path] = []
        try:
            cmd = ["uv", "build", "--out-dir", str(self.output_dir)]
            subprocess.run(
                cmd,
                check=True,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
            )
            for f in self.output_dir.iterdir():
                if f.name.endswith((".whl", ".tar.gz")) and f.name.startswith(
                    "the_great_british_bake_off"
                ):
                    built_files.append(f)
        except Exception as e:
            logger.warning("uv build failed: %s", e)

        return built_files

    def generate_manifest(self) -> Path:
        """Generate manifest.json with asset metadata, sizes, and SHA-256 hashes."""
        manifest_file = self.output_dir / "manifest.json"
        files = sorted(
            [
                f
                for f in self.output_dir.iterdir()
                if f.is_file()
                and f.name not in ["checksums.txt", "manifest.json"]
                and not f.name.startswith(".")
            ]
        )
        assets = []
        for file_path in files:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            assets.append(
                {
                    "name": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "sha256": hasher.hexdigest(),
                }
            )

        data = {
            "version": self.clean_version,
            "tag": self.tag_version,
            "generated_at": datetime.now(UTC).isoformat(),
            "asset_count": len(assets),
            "assets": assets,
        }
        manifest_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        logger.info("Generated release manifest: %s", manifest_file)
        return manifest_file

    def generate_checksums(self) -> Path:
        """Generate SHA-256 checksums file for all release assets in output_dir."""
        checksum_file = self.output_dir / "checksums.txt"
        lines: list[str] = []

        files = sorted(
            [
                f
                for f in self.output_dir.iterdir()
                if f.is_file()
                and f.name != "checksums.txt"
                and not f.name.startswith(".")
            ]
        )

        for file_path in files:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            lines.append(f"{hasher.hexdigest()}  {file_path.name}")

        checksum_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("Generated checksums: %s", checksum_file)
        return checksum_file

    def package_all(self) -> dict[str, Any]:
        """Package all release assets, manifest, and checksums."""
        results: dict[str, Any] = {}
        results["csv"] = self.package_csv()
        results["parquet"] = self.package_parquet()
        results["ai"] = self.package_ai()
        sqlite_pkg = self.package_sqlite()
        if sqlite_pkg:
            results["sqlite"] = sqlite_pkg
        results["r"] = self.package_r()
        results["tidytuesday"] = self.package_tidytuesday()
        results["python"] = self.package_python()
        results["manifest"] = self.generate_manifest()
        results["checksums"] = self.generate_checksums()
        return results


def package_release(
    output_dir: Path | str = "dist/release",
    version: str | None = None,
) -> dict[str, Any]:
    """Convenience function to run full release packaging."""
    packager = ReleasePackager(output_dir=output_dir, version=version)
    return packager.package_all()
