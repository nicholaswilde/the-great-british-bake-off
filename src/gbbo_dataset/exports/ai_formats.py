"""Exports processed GBBO datasets into AI training formats (JSONL for fine-tuning, RAG, and benchmark evaluation)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from gbbo_dataset.exports.benchmark import BenchmarkSuite

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert encyclopedia and baking analyst for the television competition series "
    "The Great British Bake Off (broadcast as The Great British Baking Show in North America). "
    "You possess comprehensive knowledge of every series, baker, theme, signature bake, "
    "technical challenge, showstopper, Star Baker award, Hollywood Handshake, and elimination."
)


def format_list_or_str(val: Any) -> str:
    """Format string or list/ndarray of strings into human-readable text."""
    if val is None:
        return ""
    if isinstance(val, (list, tuple)) or (
        hasattr(val, "__iter__") and not isinstance(val, (str, bytes))
    ):
        items = [
            str(x).strip()
            for x in val
            if x is not None
            and str(x).strip()
            and str(x).lower() not in ("nan", "none")
        ]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return f"{', '.join(items[:-1])}, and {items[-1]}"
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("nan", "none") else s


def is_valid_val(val: Any) -> bool:
    """Check if value is present and non-empty, supporting arrays/lists."""
    if val is None:
        return False
    if isinstance(val, (list, tuple)) or (
        hasattr(val, "__iter__") and not isinstance(val, (str, bytes))
    ):
        return len(val) > 0
    return bool(
        pd.notna(val)
        and str(val).strip() != ""
        and str(val).strip().lower() not in ("nan", "none")
    )


class AIExportBuilder:
    """Builds LLM-ready datasets: Chat SFT fine-tuning JSONL and RAG knowledge corpus."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.ai_dir = Path(ai_dir)
        self.ai_dir.mkdir(parents=True, exist_ok=True)

    def load_table(self, name: str) -> pd.DataFrame:
        """Load a processed CSV or Parquet table."""
        parquet_path = self.processed_dir / f"{name}.parquet"
        csv_path = self.processed_dir / f"{name}.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def generate_qa_pairs(self) -> list[dict[str, Any]]:
        """Generate verified instruction fine-tuning QA pairs across all series, bakers, and episodes."""
        seasons = self.load_table("seasons")
        bakers = self.load_table("bakers")
        episodes = self.load_table("episodes")
        performances = self.load_table("performances")

        qa_records: list[dict[str, Any]] = []

        def add_qa(
            user_prompt: str,
            assistant_response: str,
            category: str,
            series: int | None = None,
            baker_id: str | None = None,
            episode_id: str | None = None,
        ) -> None:
            metadata: dict[str, Any] = {"category": category}
            if series is not None:
                metadata["series_number"] = int(series)
            if baker_id is not None:
                metadata["baker_id"] = baker_id
            if episode_id is not None:
                metadata["episode_id"] = episode_id

            qa_records.append(
                {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_response},
                    ],
                    "metadata": metadata,
                }
            )

        # 1. Season Winners, Judges, Hosts, Networks
        if not seasons.empty:
            for _, s in seasons.iterrows():
                s_num = int(s["series_number"])
                year = s.get("year")
                winner = format_list_or_str(s.get("winner"))
                judges = format_list_or_str(s.get("judges"))
                hosts = format_list_or_str(s.get("hosts"))
                network = format_list_or_str(s.get("network"))
                loc = format_list_or_str(s.get("location"))

                if winner:
                    add_qa(
                        f"Who won Series {s_num} of The Great British Bake Off?",
                        f"The winner of Series {s_num} of The Great British Bake Off ({year}) was {winner}.",
                        "winners",
                        series=s_num,
                    )
                if judges and hosts:
                    add_qa(
                        f"Who were the judges and presenters for Series {s_num} of The Great British Bake Off?",
                        f"In Series {s_num} ({year}), the judges were {judges} and the presenters were {hosts}.",
                        "judges_and_hosts",
                        series=s_num,
                    )
                if loc:
                    add_qa(
                        f"Where was Series {s_num} of The Great British Bake Off filmed?",
                        f"Series {s_num} was filmed on location at {loc}.",
                        "filming_locations",
                        series=s_num,
                    )
                if network:
                    add_qa(
                        f"Which television network originally broadcast Series {s_num} of The Great British Bake Off?",
                        f"Series {s_num} was originally broadcast in the United Kingdom on {network}.",
                        "broadcast_network",
                        series=s_num,
                    )

        # 2. Baker Demographics, Hometown, and Placement
        baker_map: dict[str, dict[str, Any]] = {}
        if not bakers.empty:
            for _, b in bakers.iterrows():
                b_id = str(b["baker_id"])
                baker_map[b_id] = b.to_dict()
                s_num = int(b["series_number"])
                name = b["name"]
                age = b.get("age")
                occ = b.get("occupation")
                town = b.get("hometown")
                placement = b.get("overall_placement")

                age_str = f"{int(age)}-year-old " if pd.notna(age) else ""
                occ_str = f"{occ} " if pd.notna(occ) and str(occ).strip() else "baker "
                town_str = (
                    f"from {town}" if pd.notna(town) and str(town).strip() else ""
                )
                place_str = (
                    f"finished in position {int(placement)}"
                    if pd.notna(placement)
                    else "competed"
                )

                add_qa(
                    f"What is the background and final placement of {name} in Series {s_num} of The Great British Bake Off?",
                    f"{name} was a {age_str}{occ_str}{town_str} who {place_str} in Series {s_num} of The Great British Bake Off.",
                    "baker_demographics",
                    series=s_num,
                    baker_id=b_id,
                )

        # 3. Episode Themes, Star Bakers, and Eliminations
        ep_map: dict[str, dict[str, Any]] = {}
        if not episodes.empty:
            for _, ep in episodes.iterrows():
                ep_id = str(ep["episode_id"])
                ep_map[ep_id] = ep.to_dict()
                s_num = int(ep["series_number"])
                ep_num = int(ep["episode_number"])
                theme = ep.get("theme", "Baking")
                air_date = ep.get("air_date")

                air_str = (
                    f" (originally aired {air_date})" if pd.notna(air_date) else ""
                )
                add_qa(
                    f"What was the theme of Series {s_num}, Episode {ep_num} of The Great British Bake Off?",
                    f"The theme for Series {s_num}, Episode {ep_num}{air_str} was {theme} Week.",
                    "episode_themes",
                    series=s_num,
                    episode_id=ep_id,
                )

        # 4. Individual Performance & Challenge Bakes
        if not performances.empty:
            # Group by episode for star baker & eliminations
            by_episode = performances.groupby("episode_id")
            for ep_id, group in by_episode:
                ep_info = ep_map.get(str(ep_id), {})
                s_num = ep_info.get("series_number")
                ep_num = ep_info.get("episode_number")
                theme = ep_info.get("theme", "Baking")

                star_bakers = group[group["result"] == "STAR_BAKER"]
                eliminated = group[group["result"] == "ELIMINATED"]

                if not star_bakers.empty and s_num is not None:
                    sb_names = [
                        baker_map.get(b_id, {}).get("name", b_id)
                        for b_id in star_bakers["baker_id"]
                    ]
                    sb_str = ", ".join(sb_names)
                    add_qa(
                        f"Who was awarded Star Baker in Series {s_num}, Episode {ep_num} ({theme} Week)?",
                        f"In Series {s_num}, Episode {ep_num} ({theme} Week), {sb_str} was named Star Baker.",
                        "star_bakers",
                        series=s_num,
                        episode_id=str(ep_id),
                    )

                if not eliminated.empty and s_num is not None:
                    elim_names = [
                        baker_map.get(b_id, {}).get("name", b_id)
                        for b_id in eliminated["baker_id"]
                    ]
                    elim_str = ", ".join(elim_names)
                    add_qa(
                        f"Who was eliminated in Series {s_num}, Episode {ep_num} ({theme} Week)?",
                        f"In Series {s_num}, Episode {ep_num} ({theme} Week), {elim_str} was eliminated from the competition.",
                        "eliminations",
                        series=s_num,
                        episode_id=str(ep_id),
                    )

            # Individual bakes and handshakes
            for _, p in performances.iterrows():
                b_id = str(p["baker_id"])
                ep_id = str(p["episode_id"])
                b_info = baker_map.get(b_id, {})
                ep_info = ep_map.get(ep_id, {})
                b_name = b_info.get("name", b_id)
                s_num = ep_info.get("series_number")
                ep_num = ep_info.get("episode_number")
                theme = ep_info.get("theme", "Baking")

                sig = p.get("signature_dish")
                show = p.get("showstopper_dish")
                tech_rank = p.get("technical_rank")
                res = p.get("result")
                hs = bool(p.get("hollywood_handshake", False))

                bakes_parts = []
                if pd.notna(sig) and str(sig).strip():
                    bakes_parts.append(f"Signature: {sig}")
                if pd.notna(tech_rank):
                    bakes_parts.append(f"Technical ranking: {int(tech_rank)}")
                if pd.notna(show) and str(show).strip():
                    bakes_parts.append(f"Showstopper: {show}")

                if bakes_parts and s_num is not None:
                    bake_summary = "; ".join(bakes_parts)
                    add_qa(
                        f"What dishes did {b_name} bake in Series {s_num}, Episode {ep_num} ({theme} Week)?",
                        f"In Series {s_num}, Episode {ep_num} ({theme} Week), {b_name} made: {bake_summary}. Result: {res}.",
                        "challenge_descriptions",
                        series=s_num,
                        baker_id=b_id,
                        episode_id=ep_id,
                    )

                if hs and s_num is not None:
                    add_qa(
                        f"Did {b_name} receive a Hollywood Handshake in Series {s_num}, Episode {ep_num} ({theme} Week)?",
                        f"Yes! {b_name} received a Hollywood Handshake from Paul Hollywood in Series {s_num}, Episode {ep_num} ({theme} Week).",
                        "hollywood_handshakes",
                        series=s_num,
                        baker_id=b_id,
                        episode_id=ep_id,
                    )

        # 5. Domain Specific Multi-Hop Reasoning & Hall of Fame Trivia
        add_qa(
            "Which baker received a Hollywood Handshake and was eliminated in the very same episode?",
            "Ryan Chong received a Hollywood Handshake from Paul Hollywood for his Key Lime Pie in the Signature challenge of Series 3, Episode 7 (Sweet Dough Week), but was eliminated at the end of the episode.",
            "multi_hop_reasoning",
            series=3,
            baker_id="s03_ryan",
            episode_id="s03e07",
        )
        add_qa(
            "Which baker won The Great British Bake Off without ever winning Star Baker during any regular episode?",
            "David Atherton won Series 10 of The Great British Bake Off without winning the Star Baker title in any of the nine prior episodes, before clinching victory in the final.",
            "multi_hop_reasoning",
            series=10,
            baker_id="s10_david",
        )
        add_qa(
            "Who holds the record for winning Star Baker the most times in a single series of The Great British Bake Off?",
            "Richard Burr holds the all-time record, winning Star Baker 5 times during Series 5 (Bread, Desserts, Pies and Tarts, Advanced Dough, and Patisserie Weeks).",
            "multi_hop_reasoning",
            series=5,
            baker_id="s05_richard",
        )
        add_qa(
            "Who was the youngest baker to win The Great British Bake Off?",
            "Peter Sawkins became the youngest winner in GBBO history at age 20 when he won Series 11 in 2020.",
            "multi_hop_reasoning",
            series=11,
            baker_id="s11_peter",
        )
        add_qa(
            "Who was the oldest baker to win The Great British Bake Off?",
            "Nancy Birtwhistle became the oldest winner in GBBO history at age 60 when she won Series 5 in 2014.",
            "multi_hop_reasoning",
            series=5,
            baker_id="s05_nancy",
        )

        return qa_records

    def generate_knowledge_corpus(self) -> list[dict[str, Any]]:
        """Generate chunked narrative knowledge documents for RAG and semantic vector search."""
        seasons = self.load_table("seasons")
        bakers = self.load_table("bakers")
        episodes = self.load_table("episodes")
        performances = self.load_table("performances")

        corpus: list[dict[str, Any]] = []

        # 1. Series Overview Documents
        if not seasons.empty:
            for _, s in seasons.iterrows():
                s_num = int(s["series_number"])
                year = s.get("year", "N/A")
                winner = format_list_or_str(s.get("winner")) or "Unknown"
                judges = format_list_or_str(s.get("judges")) or "Unknown"
                hosts = format_list_or_str(s.get("hosts")) or "Unknown"
                network = format_list_or_str(s.get("network")) or "Unknown"
                loc = format_list_or_str(s.get("location")) or "Unknown"
                pbs = s.get("pbs_season")
                netflix = s.get("netflix_collection")
                roku = s.get("roku_season")

                streaming_lines = []
                if pd.notna(pbs) and str(pbs).strip():
                    streaming_lines.append(f"- PBS Broadcast: Season {pbs}")
                if pd.notna(netflix) and str(netflix).strip():
                    streaming_lines.append(f"- Netflix Collection: {netflix}")
                if pd.notna(roku) and str(roku).strip():
                    streaming_lines.append(f"- The Roku Channel: Season {roku}")
                streaming_block = (
                    "\n".join(streaming_lines)
                    if streaming_lines
                    else "Standard UK terrestrial broadcast."
                )

                s_bakers = (
                    bakers[bakers["series_number"] == s_num]
                    if not bakers.empty
                    else pd.DataFrame()
                )
                baker_names = (
                    ", ".join(s_bakers["name"].tolist())
                    if not s_bakers.empty
                    else "N/A"
                )

                text = (
                    f"# The Great British Bake Off: Series {s_num} ({year})\n\n"
                    f"**Winner**: {winner}\n"
                    f"**Judges**: {judges}\n"
                    f"**Presenters/Hosts**: {hosts}\n"
                    f"**Original UK Network**: {network}\n"
                    f"**Filming Location**: {loc}\n\n"
                    f"## North American & Streaming Distribution\n"
                    f"{streaming_block}\n\n"
                    f"## Competing Bakers ({len(s_bakers)})\n"
                    f"{baker_names}\n"
                )

                corpus.append(
                    {
                        "id": f"series_{s_num:02d}_overview",
                        "title": f"The Great British Bake Off — Series {s_num} Overview",
                        "text": text,
                        "metadata": {
                            "type": "series_overview",
                            "series_number": s_num,
                            "year": year,
                            "winner": winner,
                            "network": network,
                        },
                    }
                )

        # 2. Episode Narrative Documents
        if not episodes.empty:
            for _, ep in episodes.iterrows():
                ep_id = str(ep["episode_id"])
                s_num = int(ep["series_number"])
                ep_num = int(ep["episode_number"])
                theme = ep.get("theme", "Baking")
                air_date = ep.get("air_date", "N/A")
                sig_t = ep.get("signature_time_min")
                tech_t = ep.get("technical_time_min")
                show_t = ep.get("showstopper_time_min")

                time_parts = []
                if pd.notna(sig_t):
                    time_parts.append(f"Signature: {int(sig_t)} mins")
                if pd.notna(tech_t):
                    time_parts.append(f"Technical: {int(tech_t)} mins")
                if pd.notna(show_t):
                    time_parts.append(f"Showstopper: {int(show_t)} mins")
                time_str = ", ".join(time_parts) if time_parts else "Standard limits"

                ep_perfs = (
                    performances[performances["episode_id"] == ep_id]
                    if not performances.empty
                    else pd.DataFrame()
                )

                perf_lines = []
                star_bakers = []
                eliminations = []
                handshakes = []

                if not ep_perfs.empty and not bakers.empty:
                    merged = ep_perfs.merge(bakers, on="baker_id", how="left")
                    for _, p in merged.iterrows():
                        name = p.get("name", p["baker_id"])
                        res = p.get("result", "SAFE")
                        sig = p.get("signature_dish")
                        tech = p.get("technical_rank")
                        show = p.get("showstopper_dish")
                        hs = bool(p.get("hollywood_handshake", False))

                        if res == "STAR_BAKER":
                            star_bakers.append(name)
                        elif res == "ELIMINATED":
                            eliminations.append(name)
                        if hs:
                            handshakes.append(name)

                        dish_desc = []
                        if pd.notna(sig) and str(sig).strip():
                            dish_desc.append(f"Sig: {sig}")
                        if pd.notna(tech):
                            dish_desc.append(f"Tech: {int(tech)}")
                        if pd.notna(show) and str(show).strip():
                            dish_desc.append(f"Show: {show}")
                        line = f"- **{name}** ({res}): {'; '.join(dish_desc)}"
                        if hs:
                            line += " 🤝 *[Hollywood Handshake]*"
                        perf_lines.append(line)

                sb_str = ", ".join(star_bakers) if star_bakers else "None"
                elim_str = ", ".join(eliminations) if eliminations else "None"
                hs_str = ", ".join(handshakes) if handshakes else "None awarded"
                bakes_block = (
                    "\n".join(perf_lines) if perf_lines else "No detailed bake records."
                )

                text = (
                    f"# Series {s_num}, Episode {ep_num}: {theme} Week\n\n"
                    f"**Broadcast Air Date**: {air_date}\n"
                    f"**Allocated Times**: {time_str}\n"
                    f"**Star Baker**: {sb_str}\n"
                    f"**Eliminated**: {elim_str}\n"
                    f"**Hollywood Handshakes**: {hs_str}\n\n"
                    f"## Baker Bakes & Challenge Outcomes\n"
                    f"{bakes_block}\n"
                )

                corpus.append(
                    {
                        "id": f"episode_{ep_id}",
                        "title": f"GBBO Series {s_num} Episode {ep_num} — {theme} Week",
                        "text": text,
                        "metadata": {
                            "type": "episode_narrative",
                            "episode_id": ep_id,
                            "series_number": s_num,
                            "episode_number": ep_num,
                            "theme": theme,
                        },
                    }
                )

        # 3. Baker Profile Documents
        if not bakers.empty:
            for _, b in bakers.iterrows():
                b_id = str(b["baker_id"])
                s_num = int(b["series_number"])
                name = b["name"]
                age = b.get("age", "N/A")
                occ = b.get("occupation", "N/A")
                town = b.get("hometown", "N/A")
                placement = b.get("overall_placement", "N/A")

                b_perfs = (
                    performances[performances["baker_id"] == b_id]
                    if not performances.empty
                    else pd.DataFrame()
                )

                sb_count = (
                    (b_perfs["result"] == "STAR_BAKER").sum()
                    if not b_perfs.empty
                    else 0
                )
                hs_count = (
                    b_perfs["hollywood_handshake"].sum() if not b_perfs.empty else 0
                )

                bakes_lines = []
                if not b_perfs.empty and not episodes.empty:
                    merged_b = b_perfs.merge(episodes, on="episode_id", how="left")
                    for _, p in merged_b.iterrows():
                        ep_num = p.get("episode_number", "?")
                        theme = p.get("theme", "Episode")
                        sig = p.get("signature_dish")
                        tech = p.get("technical_rank")
                        show = p.get("showstopper_dish")
                        res = p.get("result", "SAFE")
                        hs = bool(p.get("hollywood_handshake", False))

                        items = []
                        if pd.notna(sig) and str(sig).strip():
                            items.append(f"Signature: {sig}")
                        if pd.notna(tech):
                            items.append(f"Technical #{int(tech)}")
                        if pd.notna(show) and str(show).strip():
                            items.append(f"Showstopper: {show}")
                        hs_note = " [Handshake]" if hs else ""
                        bakes_lines.append(
                            f"- Ep {ep_num} ({theme} - {res}{hs_note}): {'; '.join(items)}"
                        )

                history_block = (
                    "\n".join(bakes_lines) if bakes_lines else "No recorded bakes."
                )

                text = (
                    f"# Baker Profile: {name} (Series {s_num})\n\n"
                    f"**Age**: {age}\n"
                    f"**Occupation**: {occ}\n"
                    f"**Hometown**: {town}\n"
                    f"**Final Placement**: Position {placement}\n"
                    f"**Star Baker Awards**: {sb_count}\n"
                    f"**Hollywood Handshakes**: {hs_count}\n\n"
                    f"## Challenge Bake History\n"
                    f"{history_block}\n"
                )

                corpus.append(
                    {
                        "id": f"baker_{b_id}",
                        "title": f"Baker Profile: {name} (GBBO Series {s_num})",
                        "text": text,
                        "metadata": {
                            "type": "baker_profile",
                            "baker_id": b_id,
                            "name": name,
                            "series_number": s_num,
                            "placement": placement,
                        },
                    }
                )

        return corpus

    def export_all(self) -> dict[str, Path]:
        """Export Chat SFT dataset, RAG knowledge corpus, and evaluation benchmark suite."""
        self.ai_dir.mkdir(parents=True, exist_ok=True)

        qa_pairs = self.generate_qa_pairs()
        qa_file = self.ai_dir / "gbbo_qa_finetuning.jsonl"
        with open(qa_file, "w", encoding="utf-8") as f:
            f.writelines(
                json.dumps(pair, ensure_ascii=False) + "\n" for pair in qa_pairs
            )
        logger.info("Exported %d QA pairs -> %s", len(qa_pairs), qa_file)

        corpus = self.generate_knowledge_corpus()
        corpus_file = self.ai_dir / "gbbo_knowledge_corpus.jsonl"
        with open(corpus_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(doc, ensure_ascii=False) + "\n" for doc in corpus)
        logger.info("Exported %d RAG documents -> %s", len(corpus), corpus_file)

        bench_suite = BenchmarkSuite(
            benchmark_file=self.ai_dir / "gbbo_benchmark_suite.jsonl"
        )
        bench_file = bench_suite.save_default_suite()

        return {
            "qa_finetuning": qa_file,
            "knowledge_corpus": corpus_file,
            "benchmark_suite": bench_file,
        }


def export_ai(
    processed_dir: Path | str = "data/processed",
    ai_dir: Path | str = "data/ai",
) -> dict[str, Path]:
    """Helper function to build and export all AI corpora."""
    builder = AIExportBuilder(processed_dir=processed_dir, ai_dir=ai_dir)
    return builder.export_all()
