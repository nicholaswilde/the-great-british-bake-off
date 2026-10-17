"""Unit tests for Reddit community discussion importer and models."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from gbbo_dataset.cli import app
from gbbo_dataset.importers.reddit import (
    scrape_all_reddit,
    scrape_reddit_series,
)
from gbbo_dataset.models import RedditComment, RedditDiscussion

runner = CliRunner()


def test_reddit_models():
    """Verify RedditDiscussion and RedditComment models."""
    comment = RedditComment(
        comment_id="c_test1",
        author="tent_baker",
        score=45,
        body="Super proud of the winner this season!",
    )
    assert comment.score == 45
    assert comment.author == "tent_baker"

    disc = RedditDiscussion(
        thread_id="t3_s15e01",
        subreddit="GreatBritishBakeOff",
        series_number=15,
        episode_number=1,
        title="[Episode Discussion] Series 15 Episode 1: Cake Week",
        author="mod_user",
        score=350,
        upvote_ratio=0.99,
        num_comments=120,
        permalink="https://reddit.com/r/GreatBritishBakeOff/comments/s15e01/",
        top_comments=[comment],
        sentiment_label="Positive",
    )
    assert disc.series_number == 15
    assert len(disc.top_comments) == 1
    assert disc.sentiment_label == "Positive"


def test_scrape_reddit_series(tmp_path: Path):
    """Test extracting series discussion threads in offline mode."""
    raw_dir = tmp_path / "raw_reddit"
    res = scrape_reddit_series(
        series_number=5,
        subreddit="GreatBritishBakeOff",
        raw_dir=raw_dir,
        offline=True,
    )
    assert res["series_number"] == 5
    assert len(res["discussions"]) >= 1

    out_file = raw_dir / "series_05_reddit.json"
    assert out_file.exists()
    with open(out_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["series_number"] == 5
    assert any("Bingate" in d["title"] for d in data["discussions"])


def test_scrape_all_reddit(tmp_path: Path):
    """Test aggregating Reddit discussions across series."""
    raw_dir = tmp_path / "raw"
    proc_dir = tmp_path / "proc"
    summary = scrape_all_reddit(
        raw_dir=raw_dir,
        processed_dir=proc_dir,
        series_range=(1, 2),
        subreddit="GreatBritishBakeOff",
        offline=True,
    )
    assert summary["discussion_count"] >= 2
    assert (proc_dir / "reddit_discussions.json").exists()
    assert (proc_dir / "reddit_discussions.csv").exists()


def test_cli_scrape_reddit(tmp_path: Path):
    """Test gbbo scrape-reddit CLI command."""
    raw_dir = tmp_path / "reddit_cli_raw"
    proc_dir = tmp_path / "reddit_cli_proc"
    result = runner.invoke(
        app,
        [
            "scrape-reddit",
            "--series",
            "1",
            "--raw-dir",
            str(raw_dir),
            "--processed-dir",
            str(proc_dir),
            "--offline",
        ],
    )
    assert result.exit_code == 0
    assert "Series 01" in result.output
    assert (raw_dir / "series_01_reddit.json").exists()
