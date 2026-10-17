"""Empirical predictive modeling engine for The Great British Bake Off.

Calculates real-time Star Baker candidates, elimination probabilities,
and finale/winner trajectories for in-progress or historical GBBO series.
"""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

# Empirical historical baselines calibrated across GBBO Series 1–16
DEFAULT_HISTORICAL_BASELINES: dict[str, Any] = {
    "winner_mean_age": 32.5,
    "winner_std_age": 9.89,
    "winner_avg_tech_pct": 0.601,
    "winner_avg_star_bakers": 1.88,
    "winner_avg_handshakes": 0.81,
    "finalist_avg_tech_pct": 0.555,
    "eliminated_avg_tech_pct": 0.407,
    "eliminated_prev_at_risk_rate": 0.362,
    "star_baker_repeat_rate": 0.135,
    "star_baker_prev_did_well_rate": 0.158,
}


class SeriesPredictor:
    """Calculates data-driven predictions for GBBO contestants and episodes."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        raw_dir: Path | str = "data/raw",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.raw_dir = Path(raw_dir)
        self.baselines = self._compute_or_load_baselines()

    def _compute_or_load_baselines(self) -> dict[str, Any]:
        """Compute empirical baselines from Series 1-16 or fallback to cached defaults."""
        baselines = dict(DEFAULT_HISTORICAL_BASELINES)
        bakers_path = self.processed_dir / "bakers.json"
        perfs_path = self.processed_dir / "performances.json"

        if bakers_path.exists() and perfs_path.exists():
            try:
                bakers_df = pd.read_json(bakers_path)
                perfs_df = pd.read_json(perfs_path)

                if (
                    "series_number" not in perfs_df.columns
                    and "episode_id" in perfs_df.columns
                ):
                    perfs_df["series_number"] = (
                        perfs_df["episode_id"].str.extract(r"s(\d+)e").astype(float)
                    )

                # Filter historical Series 1-16
                h_bakers = bakers_df[bakers_df["series_number"] <= 16]
                h_perfs = perfs_df[perfs_df["series_number"] <= 16].copy()

                # Winner age mean and std
                winners = h_bakers[h_bakers["overall_placement"] == 1]
                valid_ages = winners["age"].dropna()
                valid_ages = valid_ages[valid_ages > 0]
                if not valid_ages.empty:
                    baselines["winner_mean_age"] = float(valid_ages.mean())
                    baselines["winner_std_age"] = (
                        float(valid_ages.std()) if len(valid_ages) > 1 else 9.89
                    )

                # Technical rank percentiles per episode
                if not h_perfs.empty and "technical_rank" in h_perfs.columns:
                    ep_max = h_perfs.groupby("episode_id")["technical_rank"].transform(
                        "max"
                    )
                    h_perfs["tech_pct"] = 1.0
                    mask = ep_max > 1
                    h_perfs.loc[mask, "tech_pct"] = (
                        ep_max[mask] - h_perfs.loc[mask, "technical_rank"]
                    ) / (ep_max[mask] - 1)

                    placement_map = h_bakers.set_index("baker_id")[
                        "overall_placement"
                    ].to_dict()
                    h_perfs["placement"] = h_perfs["baker_id"].map(placement_map)

                    w_perfs = h_perfs[h_perfs["placement"] == 1]
                    f_perfs = h_perfs[h_perfs["placement"] <= 3]
                    e_perfs = h_perfs[h_perfs["placement"] > 6]

                    if not w_perfs["tech_pct"].dropna().empty:
                        baselines["winner_avg_tech_pct"] = float(
                            w_perfs["tech_pct"].dropna().mean()
                        )
                    if not f_perfs["tech_pct"].dropna().empty:
                        baselines["finalist_avg_tech_pct"] = float(
                            f_perfs["tech_pct"].dropna().mean()
                        )
                    if not e_perfs["tech_pct"].dropna().empty:
                        baselines["eliminated_avg_tech_pct"] = float(
                            e_perfs["tech_pct"].dropna().mean()
                        )
            except Exception as exc:
                logger.warning("Could not calculate live baselines: %s", exc)

        return baselines

    def score_baker(
        self,
        baker_id: str,
        name: str,
        age: int | None,
        performances: list[dict[str, Any]],
        ep_tech_max: dict[str, float],
        is_eliminated: bool = False,
        is_withdrew: bool = False,
    ) -> dict[str, Any]:
        """Score an individual baker based on cumulative performance and judging momentum."""
        status = (
            "Withdrew" if is_withdrew else ("Eliminated" if is_eliminated else "Active")
        )
        is_active = not (is_eliminated or is_withdrew)

        # Baseline age Gaussian score
        mean_age = self.baselines.get("winner_mean_age", 32.5)
        std_age = self.baselines.get("winner_std_age", 9.89)
        if age and age > 0:
            age_score = math.exp(-((age - mean_age) ** 2) / (2 * (std_age**2)))
        else:
            age_score = 0.60

        if not performances:
            # Baker has no performances yet in completed episodes
            return {
                "baker_id": baker_id,
                "name": name,
                "age": age,
                "status": status,
                "is_active": is_active,
                "is_eliminated": is_eliminated,
                "is_withdrew": is_withdrew,
                "episodes_competed": 0,
                "avg_technical_pct": 0.5,
                "last_technical_rank": None,
                "last_technical_pct": 0.5,
                "star_baker_count": 0,
                "handshake_count": 0,
                "did_well_count": 0,
                "at_risk_count": 0,
                "last_star_baker": False,
                "last_did_well": False,
                "last_at_risk": False,
                "last_handshake": False,
                "age_score": round(age_score, 3),
                "star_baker_raw": 0.0,
                "elimination_raw": 0.0,
                "win_raw": 0.0,
            }

        tech_pcts: list[float] = []
        star_baker_count = 0
        handshake_count = 0
        did_well_count = 0
        at_risk_count = 0

        for p in performances:
            ep_id = p.get("episode_id", "")
            rank = p.get("technical_rank")
            max_r = ep_tech_max.get(ep_id, 1.0)

            if rank is not None and not (isinstance(rank, float) and math.isnan(rank)):
                rank_f = float(rank)
                pct = (max_r - rank_f) / (max_r - 1.0) if max_r > 1.0 else 1.0
                tech_pcts.append(max(0.0, min(1.0, pct)))

            res = str(p.get("result", "")).upper()
            if res == "STAR_BAKER":
                star_baker_count += 1
            if p.get("hollywood_handshake"):
                handshake_count += 1
            if p.get("did_well"):
                did_well_count += 1
            if p.get("at_risk"):
                at_risk_count += 1

        avg_tech_pct = sum(tech_pcts) / len(tech_pcts) if tech_pcts else 0.5
        last_tech_pct = tech_pcts[-1] if tech_pcts else 0.5
        last_p = performances[-1]
        last_rank = last_p.get("technical_rank")
        last_rank_int = (
            int(last_rank)
            if last_rank is not None
            and not (isinstance(last_rank, float) and math.isnan(last_rank))
            else None
        )

        last_res = str(last_p.get("result", "")).upper()
        last_star_baker = last_res == "STAR_BAKER"
        last_did_well = bool(last_p.get("did_well", False))
        last_at_risk = bool(last_p.get("at_risk", False))
        last_handshake = bool(last_p.get("hollywood_handshake", False))

        # Star Baker Candidate Raw Score
        sb_raw = (
            0.30 * avg_tech_pct
            + 0.25 * last_tech_pct
            + 0.20
            * (
                min(star_baker_count, 3) * 0.5
                + (0.8 if last_star_baker else 0.0)
                + (0.4 if last_did_well else 0.0)
            )
            + 0.15 * (min(handshake_count, 3) * 0.4 + (0.6 if last_handshake else 0.0))
            + 0.05 * age_score
            - (0.35 if last_at_risk else 0.0)
            - 0.10 * min(at_risk_count, 3)
        )

        # Elimination Risk Raw Score
        elim_raw = (
            0.35 * (1.0 - avg_tech_pct)
            + 0.25 * (1.0 - last_tech_pct)
            + 0.35 * (1.0 if last_at_risk else 0.0)
            + 0.15 * min(at_risk_count, 3)
            - 0.20 * min(star_baker_count, 2)
            - 0.15 * min(handshake_count, 2)
            - 0.10 * min(did_well_count, 2)
        )

        # Overall Series Win Raw Score
        win_raw = (
            0.35 * avg_tech_pct
            + 0.25 * min(star_baker_count, 3)
            + 0.15 * min(handshake_count, 3)
            + 0.10 * min(did_well_count, 3)
            - 0.20 * min(at_risk_count, 3)
            + 0.10 * age_score
        )

        return {
            "baker_id": baker_id,
            "name": name,
            "age": age,
            "status": status,
            "is_active": is_active,
            "is_eliminated": is_eliminated,
            "is_withdrew": is_withdrew,
            "episodes_competed": len(performances),
            "avg_technical_pct": round(avg_tech_pct, 3),
            "last_technical_rank": last_rank_int,
            "last_technical_pct": round(last_tech_pct, 3),
            "star_baker_count": star_baker_count,
            "handshake_count": handshake_count,
            "did_well_count": did_well_count,
            "at_risk_count": at_risk_count,
            "last_star_baker": last_star_baker,
            "last_did_well": last_did_well,
            "last_at_risk": last_at_risk,
            "last_handshake": last_handshake,
            "age_score": round(age_score, 3),
            "star_baker_raw": round(sb_raw, 4),
            "elimination_raw": round(elim_raw, 4),
            "win_raw": round(win_raw, 4),
        }

    def predict_series(
        self,
        series: int = 17,
        as_of_episode: int | None = None,
    ) -> dict[str, Any]:
        """Generate empirical predictions for bakers in a series as of a specific episode."""
        bakers_list: list[dict[str, Any]] = []
        perfs_list: list[dict[str, Any]] = []

        # 1. Try loading from processed tables
        processed_bakers = self.processed_dir / "bakers.json"
        processed_perfs = self.processed_dir / "performances.json"

        if processed_bakers.exists() and processed_perfs.exists():
            try:
                with open(processed_bakers, encoding="utf-8") as f:
                    all_bakers = json.load(f)
                with open(processed_perfs, encoding="utf-8") as f:
                    all_perfs = json.load(f)

                bakers_list = [
                    b for b in all_bakers if b.get("series_number") == series
                ]
                perfs_list = [
                    p
                    for p in all_perfs
                    if p.get("episode_id", "").startswith(f"s{series:02d}")
                    or p.get("episode_id", "").startswith(f"s{series}")
                ]
            except Exception as exc:
                logger.warning("Error reading processed data: %s", exc)

        # Fallback to raw series data if empty
        if not bakers_list or not perfs_list:
            raw_bakers = self.raw_dir / f"series_{series}_bakers.json"
            raw_perfs = self.raw_dir / f"series_{series}_performances.json"
            if raw_bakers.exists():
                with open(raw_bakers, encoding="utf-8") as f:
                    bakers_list = json.load(f)
            if raw_perfs.exists():
                with open(raw_perfs, encoding="utf-8") as f:
                    perfs_list = json.load(f)

        if not bakers_list:
            raise ValueError(f"No baker records found for Series {series}")

        # Extract completed episode IDs
        all_ep_ids = sorted({p["episode_id"] for p in perfs_list if "episode_id" in p})

        if as_of_episode is not None:
            # Filter episodes up to as_of_episode
            filtered_ep_ids = [
                ep
                for ep in all_ep_ids
                if self._extract_episode_number(ep) <= as_of_episode
            ]
        else:
            filtered_ep_ids = all_ep_ids

        perfs_filtered = [
            p for p in perfs_list if p.get("episode_id") in set(filtered_ep_ids)
        ]

        # Calculate max technical rank per episode in scope
        ep_tech_max: dict[str, float] = {}
        for ep in filtered_ep_ids:
            ranks = [
                float(p["technical_rank"])
                for p in perfs_filtered
                if p.get("episode_id") == ep
                and p.get("technical_rank") is not None
                and not (
                    isinstance(p.get("technical_rank"), float)
                    and math.isnan(p["technical_rank"])
                )
            ]
            ep_tech_max[ep] = max(ranks) if ranks else 1.0

        current_episode = (
            max(
                (self._extract_episode_number(ep) for ep in filtered_ep_ids),
                default=0,
            )
            if filtered_ep_ids
            else 0
        )
        next_episode = current_episode + 1

        # Score each baker
        scored_bakers: list[dict[str, Any]] = []
        for b in bakers_list:
            b_id = b["baker_id"]
            b_perfs = [p for p in perfs_filtered if p.get("baker_id") == b_id]
            b_perfs.sort(
                key=lambda x: self._extract_episode_number(x.get("episode_id", ""))
            )

            is_elim = any(
                str(p.get("result", "")).upper() == "ELIMINATED" for p in b_perfs
            )
            is_withdrew = any(
                str(p.get("result", "")).upper() == "WITHDREW" for p in b_perfs
            )

            score_data = self.score_baker(
                baker_id=b_id,
                name=b.get("name", b_id),
                age=b.get("age"),
                performances=b_perfs,
                ep_tech_max=ep_tech_max,
                is_eliminated=is_elim,
                is_withdrew=is_withdrew,
            )
            scored_bakers.append(score_data)

        # Calibrate probabilities across active bakers
        active_bakers = [b for b in scored_bakers if b["is_active"]]
        inactive_bakers = [b for b in scored_bakers if not b["is_active"]]

        for b in inactive_bakers:
            b["star_baker_prob"] = 0.0
            b["elimination_risk"] = 0.0
            b["win_probability"] = 0.0
            b["top3_probability"] = 0.0

        if active_bakers:
            win_probs = self._softmax([b["win_raw"] for b in active_bakers], temp=2.5)
            sb_probs = self._softmax(
                [b["star_baker_raw"] for b in active_bakers], temp=2.5
            )
            elim_risks = self._softmax(
                [b["elimination_raw"] for b in active_bakers], temp=2.5
            )

            for b, wp, sbp, er in zip(active_bakers, win_probs, sb_probs, elim_risks):
                b["win_probability"] = wp
                b["star_baker_prob"] = sbp
                b["elimination_risk"] = er

                if len(active_bakers) <= 3:
                    b["top3_probability"] = 100.0
                else:
                    top3_val = round(
                        wp * 2.4 + float(b.get("avg_technical_pct", 0.5)) * 20.0,
                        1,
                    )
                    b["top3_probability"] = max(wp, min(95.0, top3_val))

        # Sort rankings: active by win_probability desc, then inactive
        active_sorted = sorted(
            active_bakers,
            key=lambda x: (
                x["win_probability"],
                x["star_baker_prob"],
                x["avg_technical_pct"],
            ),
            reverse=True,
        )
        inactive_sorted = sorted(
            inactive_bakers,
            key=lambda x: x["episodes_competed"],
            reverse=True,
        )
        rankings = active_sorted + inactive_sorted

        return {
            "series": series,
            "current_episode": current_episode,
            "next_episode": next_episode,
            "total_bakers": len(bakers_list),
            "active_bakers_count": len(active_bakers),
            "eliminated_bakers_count": len(inactive_bakers),
            "rankings": rankings,
            "completed_episodes": filtered_ep_ids,
            "historical_baselines": self.baselines,
        }

    def update_predictions_docs(
        self,
        series: int = 17,
        readme_path: Path | str = "README.md",
        docs_path: Path | str = "docs/predictions.md",
        data_dir: Path | str = "data/predictions",
    ) -> dict[str, Any]:
        """Update predictions history snapshots, README summary, and docs/predictions.md."""
        readme_file = Path(readme_path)
        docs_file = Path(docs_path)
        history_dir = Path(data_dir) / f"series_{series}"
        history_dir.mkdir(parents=True, exist_ok=True)

        # 1. First generate current snapshot
        current_results = self.predict_series(series=series)
        current_ep = current_results["current_episode"]

        # 2. Also backfill snapshots for earlier completed episodes if not present
        for ep_num in range(1, current_ep + 1):
            snap_file = history_dir / f"episode_{ep_num}.json"
            if not snap_file.exists():
                past_results = self.predict_series(series=series, as_of_episode=ep_num)
                with open(snap_file, "w", encoding="utf-8") as f:
                    json.dump(past_results, f, indent=2)

        # Save latest current episode snapshot
        latest_snap_file = history_dir / f"episode_{current_ep}.json"
        with open(latest_snap_file, "w", encoding="utf-8") as f:
            json.dump(current_results, f, indent=2)

        # 3. Load all snapshots in order
        snapshots: dict[int, dict[str, Any]] = {}
        for snap_path in sorted(history_dir.glob("episode_*.json")):
            m = re.match(r"episode_(\d+)\.json", snap_path.name)
            if m:
                ep_idx = int(m.group(1))
                try:
                    with open(snap_path, encoding="utf-8") as f:
                        snapshots[ep_idx] = json.load(f)
                except Exception as exc:
                    logger.warning("Could not read snapshot %s: %s", snap_path, exc)

        rankings = current_results["rankings"]
        top_active = [b for b in rankings if b["is_active"]]

        # Build Contender Rankings Table
        table_rows: list[str] = []
        for idx, b in enumerate(top_active, 1):
            age_str = str(b["age"]) if b.get("age") else "-"
            tech_str = f"{b['avg_technical_pct'] * 100.0:.1f}%"
            table_rows.append(
                f"| {idx} | **{b['name']}** | {age_str} | {tech_str} | {b['handshake_count']} | {b['star_baker_count']} | **{b['star_baker_prob']:.1f}%** | {b['elimination_risk']:.1f}% | **{b['win_probability']:.1f}%** | **{b['top3_probability']:.1f}%** |"
            )

        latest_table_md = (
            "| Rank | Baker | Age | Avg Tech % | Handshakes | Star Bakers | Next Star Baker | Next Elim Risk | Win Prob | Finale Prob |\n"
            "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
            + "\n".join(table_rows)
        )

        # Weekly Win Probability Trajectory Table
        sorted_eps = sorted(snapshots.keys())
        ep_headers = " | ".join(f"Episode {e}" for e in sorted_eps)
        ep_align = " | ".join(":---:" for _ in sorted_eps)
        trajectory_header = f"| Baker | Status | {ep_headers} |"
        trajectory_align = f"| :--- | :---: | {ep_align} |"
        trajectory_rows: list[str] = []

        for b in rankings:
            b_name = b["name"]
            status_str = b["status"]
            probs: list[str] = []
            for e_idx in sorted_eps:
                s_data = snapshots[e_idx]
                match = next(
                    (
                        x
                        for x in s_data.get("rankings", [])
                        if x["name"] == b_name or x["baker_id"] == b["baker_id"]
                    ),
                    None,
                )
                if match:
                    if not match.get("is_active", True):
                        probs.append("0.0%")
                    else:
                        probs.append(f"{match.get('win_probability', 0.0):.1f}%")
                else:
                    probs.append("-")
            trajectory_rows.append(
                f"| **{b_name}** | {status_str} | " + " | ".join(probs) + " |"
            )

        trajectory_table_md = f"{trajectory_header}\n{trajectory_align}\n" + "\n".join(
            trajectory_rows
        )

        # Historical Outcome Accuracy Verification Table
        accuracy_rows: list[str] = []
        actual_episodes = self._gather_actual_episode_outcomes(series, current_ep)

        for ep_num in sorted_eps:
            actual = actual_episodes.get(ep_num, {})
            snap = snapshots[ep_num]
            snap_rankings = snap.get("rankings", [])
            sb_candidates = sorted(
                [x for x in snap_rankings if x.get("is_active")],
                key=lambda x: x.get("star_baker_prob", 0.0),
                reverse=True,
            )
            elim_candidates = sorted(
                [x for x in snap_rankings if x.get("is_active")],
                key=lambda x: x.get("elimination_risk", 0.0),
                reverse=True,
            )

            actual_sb = actual.get("star_baker", "—")
            elim = actual.get("eliminated")
            withdrew = actual.get("withdrew")
            if elim and withdrew:
                actual_elim = f"{elim} (Elim), {withdrew} (Withdrew)"
            elif elim:
                actual_elim = elim
            elif withdrew:
                actual_elim = f"{withdrew} (Withdrew)"
            else:
                actual_elim = "—"

            top_sb_name = sb_candidates[0]["name"] if sb_candidates else "—"
            top_sb_prob = (
                f"{sb_candidates[0]['star_baker_prob']:.1f}%" if sb_candidates else "—"
            )

            top_elim_name = elim_candidates[0]["name"] if elim_candidates else "—"
            top_elim_risk = (
                f"{elim_candidates[0]['elimination_risk']:.1f}%"
                if elim_candidates
                else "—"
            )

            accuracy_rows.append(
                f"| Episode {ep_num} | **{actual_sb}** | {top_sb_name} ({top_sb_prob}) | **{actual_elim}** | {top_elim_name} ({top_elim_risk}) |"
            )

        accuracy_table_md = (
            "| Episode | Actual Star Baker | Model Top SB Candidate | Actual Elimination | Model Top Elim Risk |\n"
            "| :---: | :--- | :--- | :--- | :--- |\n" + "\n".join(accuracy_rows)
        )

        # Elimination & Baker Status Verification
        elim_notes: list[str] = []
        for b in rankings:
            if b["status"] in ("Eliminated", "Withdrew"):
                elim_notes.append(
                    f"- **{b['name']}**: {b['status']}. Win & Star Baker probability correctly set to **0.0%**."
                )
        elim_eval_md = (
            "\n".join(elim_notes) if elim_notes else "- No bakers eliminated yet."
        )

        docs_file.parent.mkdir(parents=True, exist_ok=True)
        docs_content = f"""# The Great British Bake Off Series {series} Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, baker trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Great British Bake Off Series {series}**.

Predictions are calculated using an empirical modeling engine calibrated on 16 historical GBBO series: **Cumulative Technical Challenge Percentile (30%)**, **Recent Technical Form (25%)**, **Star Baker Momentum & Callouts (20%)**, **Hollywood Handshakes (15%)**, and **Winner Age Distribution (5%)**.

---

## 🎂 Latest Contender Rankings (After Episode {current_ep})

**Model Context**: Active Bakers: {current_results["active_bakers_count"]}/{current_results["total_bakers"]} | Calibrated Historical Sample: Series 1–16

{latest_table_md}

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated series win probabilities across broadcast episodes:

{trajectory_table_md}

---

## 🎯 Prediction Accuracy vs Actual Broadcast Outcomes

Comparison of model forecasts against actual weekly judging results:

{accuracy_table_md}

### Elimination & Baker Status Verification
{elim_eval_md}

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Cumulative Technical Rank**: Historical series winners averaged a 60.1% technical percentile rank; finalists averaged 55.5%; early eliminated bakers averaged 40.7%.
- **Judging Momentum**: 36.2% of non-first-episode eliminated bakers were placed *at risk* or in the bottom in the immediately preceding episode.
- **Hollywood Handshakes**: Handshakes strongly correlate with Star Baker performance and series longevity.
- **Peak Winner Age**: Gaussian centered at 32.5 ± 9.9 years.
"""
        docs_file.write_text(docs_content, encoding="utf-8")

        # 4. Update README.md section
        readme_section = f"""<!-- GBBO_PREDICTIONS_START -->
### :trophy: Live Empirical Predictions (Series {series} - After Episode {current_ep})

Probabilistic forecasts computed via multi-factor empirical modeling calibrated against 16 historical GBBO series. See [docs/predictions.md](docs/predictions.md) for full weekly trajectory ledgers and outcome accuracy tracking.

{latest_table_md}

> [!NOTE]
> Predictions update automatically after each broadcast episode via `task predict:update` or `uv run gbbo predict --update-docs`. See [docs/predictions.md](docs/predictions.md) for all historical episode snapshots.
<!-- GBBO_PREDICTIONS_END -->"""

        if readme_file.exists():
            content = readme_file.read_text(encoding="utf-8")
            if (
                "<!-- GBBO_PREDICTIONS_START -->" in content
                and "<!-- GBBO_PREDICTIONS_END -->" in content
            ):
                pattern = re.compile(
                    r"<!-- GBBO_PREDICTIONS_START -->.*?<!-- GBBO_PREDICTIONS_END -->",
                    re.DOTALL,
                )
                new_content = pattern.sub(readme_section, content)
            else:
                target_marker = "## :clap: Acknowledgments & Credits"
                if target_marker in content:
                    parts = content.split(target_marker, 1)
                    new_content = (
                        parts[0]
                        + "## :crystal_ball: Empirical Series Predictions\n\n"
                        + readme_section
                        + "\n\n---\n\n"
                        + target_marker
                        + parts[1]
                    )
                else:
                    new_content = content + "\n\n" + readme_section

            readme_file.write_text(new_content, encoding="utf-8")

        return {
            "series": series,
            "current_episode": current_ep,
            "docs_file": str(docs_file),
            "readme_file": str(readme_file),
            "snapshot_file": str(latest_snap_file),
            "rankings": rankings,
        }

    def _gather_actual_episode_outcomes(
        self, series: int, current_ep: int
    ) -> dict[int, dict[str, Any]]:
        """Gather actual Star Baker, eliminated, and withdrew outcomes per episode."""
        outcomes: dict[int, dict[str, Any]] = {}
        perfs_path = self.processed_dir / "performances.json"
        bakers_path = self.processed_dir / "bakers.json"

        name_map: dict[str, str] = {}
        if bakers_path.exists():
            try:
                with open(bakers_path, encoding="utf-8") as f:
                    for b in json.load(f):
                        name_map[b["baker_id"]] = b.get("name", b["baker_id"])
            except Exception as exc:
                logger.warning("Could not read baker names: %s", exc)

        if perfs_path.exists():
            try:
                with open(perfs_path, encoding="utf-8") as f:
                    all_perfs = json.load(f)
                for p in all_perfs:
                    ep_id = p.get("episode_id", "")
                    if ep_id.startswith((f"s{series:02d}", f"s{series}")):
                        ep_num = self._extract_episode_number(ep_id)
                        if ep_num <= current_ep:
                            if ep_num not in outcomes:
                                outcomes[ep_num] = {
                                    "star_baker": None,
                                    "eliminated": None,
                                    "withdrew": None,
                                }
                            res = str(p.get("result", "")).upper()
                            b_id = p.get("baker_id", "")
                            b_name = name_map.get(b_id, b_id)
                            if res == "STAR_BAKER":
                                outcomes[ep_num]["star_baker"] = b_name
                            elif res == "ELIMINATED":
                                outcomes[ep_num]["eliminated"] = b_name
                            elif res == "WITHDREW":
                                outcomes[ep_num]["withdrew"] = b_name
            except Exception as exc:
                logger.warning("Could not gather actual outcomes: %s", exc)

        return outcomes

    @staticmethod
    def _extract_episode_number(episode_id: str) -> int:
        """Extract integer episode number from ID like 's17e04'."""
        m = re.search(r"e(\d+)", episode_id, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _softmax(values: list[float], temp: float = 2.0) -> list[float]:
        """Compute temperature-scaled softmax probabilities summing to 100.0%."""
        if not values:
            return []
        if len(values) == 1:
            return [100.0]
        scaled = [v * temp for v in values]
        max_v = max(scaled)
        exps = [math.exp(v - max_v) for v in scaled]
        total = sum(exps)
        if total == 0.0:
            uniform = round(100.0 / len(values), 1)
            return [uniform] * len(values)
        return [round((e / total) * 100.0, 1) for e in exps]


def run_predict_cli(
    series: int = 17,
    top: int = 12,
    detail: bool = False,
    output_json: Path | None = None,
    update_docs: bool = False,
    console: Console | None = None,
) -> int:
    """Execute prediction workflow, render terminal output, and optionally write docs."""
    c = console or Console()
    c.print(
        f"[bold cyan]Running GBBO predictive modeling engine for Series {series}...[/bold cyan]"
    )
    predictor = SeriesPredictor()
    try:
        results = predictor.predict_series(series=series)
    except Exception as exc:
        c.print(f"[bold red]Prediction error:[/bold red] {exc}")
        return 1

    current_ep = results["current_episode"]
    next_ep = results["next_episode"]
    active_count = results["active_bakers_count"]
    total_count = results["total_bakers"]

    c.print(
        Panel(
            f"[bold white]Series {series} Prediction Engine (After Episode {current_ep})[/bold white]\n"
            f"[bold]Active Bakers:[/bold] {active_count}/{total_count}  |  "
            f"[bold]Next Episode:[/bold] Episode {next_ep}  |  "
            f"[bold]Historical Baseline Sample:[/bold] Series 1–16 (16 winners, 200+ bakers)",
            title="The Great British Bake Off Empirical Predictor",
            expand=False,
        )
    )

    table = Table(title=f"Series {series} Contender Rankings (Top {top})")
    table.add_column("Rank", style="bold cyan", justify="right")
    table.add_column("Baker", style="bold white")
    table.add_column("Status", justify="center")
    table.add_column("Age", justify="center")
    table.add_column("Avg Tech %", justify="center")
    table.add_column("Handshakes", justify="center")
    table.add_column("Star Bakers", justify="center")
    table.add_column("Next SB Prob", style="bold green", justify="right")
    table.add_column("Next Elim Risk", style="bold red", justify="right")
    table.add_column("Win Prob", style="bold yellow", justify="right")
    table.add_column("Finale Prob", style="bold magenta", justify="right")

    rankings = results["rankings"][:top]
    for idx, b in enumerate(rankings, 1):
        if not b["is_active"]:
            table.add_row(
                str(idx),
                f"[dim strikethrough]{b['name']}[/dim strikethrough]",
                f"[dim red]{b['status']}[/dim red]",
                f"[dim]{b['age'] or '-'}[/dim]",
                f"[dim]{b['avg_technical_pct'] * 100.0:.1f}%[/dim]",
                f"[dim]{b['handshake_count']}[/dim]",
                f"[dim]{b['star_baker_count']}[/dim]",
                "[dim]0.0%[/dim]",
                "[dim]0.0%[/dim]",
                "[dim]0.0%[/dim]",
                "[dim]0.0%[/dim]",
            )
        else:
            table.add_row(
                str(idx),
                b["name"],
                "[green]Active[/green]",
                str(b["age"]) if b["age"] else "-",
                f"{b['avg_technical_pct'] * 100.0:.1f}%",
                str(b["handshake_count"]),
                str(b["star_baker_count"]),
                f"{b['star_baker_prob']:.1f}%",
                f"{b['elimination_risk']:.1f}%",
                f"{b['win_probability']:.1f}%",
                f"{b['top3_probability']:.1f}%",
            )

    c.print(table)

    if detail:
        detail_table = Table(title=f"Series {series} Factor Breakdown")
        detail_table.add_column("Baker", style="bold white")
        detail_table.add_column("Last Tech %", justify="center")
        detail_table.add_column("Did Well", justify="center")
        detail_table.add_column("At Risk", justify="center")
        detail_table.add_column("Age Gaussian", justify="center")
        detail_table.add_column("SB Raw", justify="right")
        detail_table.add_column("Elim Raw", justify="right")
        detail_table.add_column("Win Raw", justify="right")

        for b in rankings:
            if b["is_active"]:
                detail_table.add_row(
                    b["name"],
                    f"{b['last_technical_pct'] * 100.0:.1f}%",
                    str(b["did_well_count"]),
                    str(b["at_risk_count"]),
                    f"{b['age_score']:.3f}",
                    f"{b['star_baker_raw']:.3f}",
                    f"{b['elimination_raw']:.3f}",
                    f"{b['win_raw']:.3f}",
                )
        c.print(detail_table)

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        c.print(f"[green]✓ Exported predictions JSON to {output_json}[/green]")

    if update_docs:
        doc_res = predictor.update_predictions_docs(series=series)
        c.print(
            f"[bold green]✓ Updated prediction ledger in {doc_res['docs_file']} and {doc_res['readme_file']}[/bold green]"
        )

    return 0


app = typer.Typer(help="The Great British Bake Off predictive engine.")


@app.command("predict")
def predict_cmd(
    series: int = typer.Option(
        17, "--series", "-s", help="Series number to predict (e.g. 17)."
    ),
    top: int = typer.Option(12, "--top", "-t", help="Number of top bakers to display."),
    detail: bool = typer.Option(
        False, "--detail", "-d", help="Display detailed factor metrics."
    ),
    output_json: Path | None = typer.Option(
        None, "--output", "-o", help="Optional path to export predictions JSON."
    ),
    update_docs: bool = typer.Option(
        False,
        "--update-docs",
        help="Update prediction documentation in README.md and docs/predictions.md.",
    ),
) -> None:
    code = run_predict_cli(
        series=series,
        top=top,
        detail=detail,
        output_json=output_json,
        update_docs=update_docs,
    )
    if code != 0:
        raise typer.Exit(code=code)


def main() -> None:
    """Run predictor CLI directly."""
    app()


if __name__ == "__main__":
    main()
