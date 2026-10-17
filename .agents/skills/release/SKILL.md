---
name: release
description: Automates version calculation, pre-release validation, version bumping (pyproject.toml, r/DESCRIPTION, CITATION.cff), git tagging, and atomic push using scripts/release.sh.
---
# /release [patch|minor|major|<version>]

Automates the versioning, tagging, and deployment process for The Great British Bake Off dataset project.

## Description
This skill handles the release process by executing the `scripts/release.sh` utility. The script will automatically:
1. Determine the target version (default: next patch, or increments minor/major, or accepts an explicit version).
2. Run pre-release validation suite (`task check` running linting, formatting, test suite, and dataset schema validation).
3. Bump version numbers in `pyproject.toml`, `r/DESCRIPTION`, and `CITATION.cff`.
4. Commit the version bump (`chore(release): bump version to vX.Y.Z`).
5. Create an annotated git tag (`vX.Y.Z`).
6. Atomically push commit and tag to the remote repository (`git push --atomic origin <branch> vX.Y.Z`).
7. Trigger the tag-based GitHub Actions release workflow (`.github/workflows/release.yml`) to compile segmented dataset bundles (CSV, Parquet, AI, SQLite, R, Python) and create a release draft.

## Rules & Version Bumping
- **Always bump the git version tag**: Every release invocation must increment the version tag (`vX.Y.Z`). Never reuse, overwrite, force-move, or re-tag an existing release tag.
- By default, executing `./scripts/release.sh` or `task release` automatically bumps to the next patch version (`vX.Y.(Z+1)`). Use `minor` for features or newly ingested series, and `major` for breaking schema changes.

## Protocol

1. Run the release script or Taskfile command:
   ```bash
   # Release next patch version (e.g. 0.1.0 -> 0.1.1)
   ./scripts/release.sh
   # or
   task release

   # Release minor version (e.g. 0.1.0 -> 0.2.0)
   ./scripts/release.sh minor
   # or
   task release -- minor

   # Release major or specific version
   ./scripts/release.sh major
   ./scripts/release.sh 1.0.0
   ```
2. Once pushed, verify the GitHub Actions release workflow completes and generates the release assets and notes.
