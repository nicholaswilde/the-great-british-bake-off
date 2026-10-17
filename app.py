"""Streamlit entrypoint for The Great British Bake Off Analytics Dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path for direct repository deployment
repo_root = Path(__file__).resolve().parent
src_dir = repo_root / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from gbbo_dataset.dashboard.app import main

if __name__ == "__main__":
    main()
