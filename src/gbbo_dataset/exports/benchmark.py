"""RAG & AI Benchmark Suite for The Great British Bake Off.

Curates an evaluation benchmark prompt set and scoring harness to evaluate LLMs on:
1. GBBO Trivia
2. Challenge & Multi-Hop Reasoning
3. Baking Rules & Show Mechanics
4. Hollywood Handshakes & Accolades
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

BENCHMARK_ITEMS: list[dict[str, Any]] = [
    # ==========================
    # CATEGORY: TRIVIA
    # ==========================
    {
        "id": "bench-trivia-001",
        "category": "trivia",
        "difficulty": "easy",
        "series": 1,
        "question": "Who won the very first series of The Great British Bake Off?",
        "reference_answer": "Edd Kimber (Edward Kimber) won Series 1 of The Great British Bake Off in 2010.",
        "key_facts": ["Edd", "Kimber"],
        "context_docs": ["series_01_overview"],
    },
    {
        "id": "bench-trivia-002",
        "category": "trivia",
        "difficulty": "easy",
        "series": 6,
        "question": "Who won Series 6 of The Great British Bake Off and became one of the UK's most acclaimed culinary authors and TV personalities?",
        "reference_answer": "Nadiya Hussain won Series 6 in 2015.",
        "key_facts": ["Nadiya", "Hussain"],
        "context_docs": ["series_06_overview"],
    },
    {
        "id": "bench-trivia-003",
        "category": "trivia",
        "difficulty": "medium",
        "series": 11,
        "question": "Who was the youngest baker in history to win The Great British Bake Off?",
        "reference_answer": "Peter Sawkins won Series 11 at the age of 20.",
        "key_facts": ["Peter", "Sawkins", "20"],
        "context_docs": ["series_11_overview"],
    },
    {
        "id": "bench-trivia-004",
        "category": "trivia",
        "difficulty": "medium",
        "series": 5,
        "question": "Who was the oldest baker to win The Great British Bake Off?",
        "reference_answer": "Nancy Birtwhistle won Series 5 at the age of 60.",
        "key_facts": ["Nancy", "Birtwhistle", "60"],
        "context_docs": ["series_05_overview"],
    },
    {
        "id": "bench-trivia-005",
        "category": "trivia",
        "difficulty": "easy",
        "series": 3,
        "question": "Who won Series 3 of The Great British Bake Off in 2012?",
        "reference_answer": "John Whaite won Series 3.",
        "key_facts": ["John", "Whaite"],
        "context_docs": ["series_03_overview"],
    },
    {
        "id": "bench-trivia-006",
        "category": "trivia",
        "difficulty": "easy",
        "series": 4,
        "question": "Who won Series 4 of The Great British Bake Off in 2013 with imaginative architectural bakes?",
        "reference_answer": "Frances Quinn won Series 4.",
        "key_facts": ["Frances", "Quinn"],
        "context_docs": ["series_04_overview"],
    },
    {
        "id": "bench-trivia-007",
        "category": "trivia",
        "difficulty": "medium",
        "series": 7,
        "question": "Who won Series 7, the final series broadcast on the BBC before the series moved to Channel 4?",
        "reference_answer": "Candice Brown won Series 7 in 2016.",
        "key_facts": ["Candice", "Brown"],
        "context_docs": ["series_07_overview"],
    },
    {
        "id": "bench-trivia-008",
        "category": "trivia",
        "difficulty": "medium",
        "series": 8,
        "question": "Who won Series 8, the inaugural series broadcast on Channel 4?",
        "reference_answer": "Sophie Faldo won Series 8 in 2017.",
        "key_facts": ["Sophie", "Faldo"],
        "context_docs": ["series_08_overview"],
    },
    {
        "id": "bench-trivia-009",
        "category": "trivia",
        "difficulty": "easy",
        "series": 9,
        "question": "Which research scientist won Series 9 of The Great British Bake Off in 2018?",
        "reference_answer": "Rahul Mandal won Series 9.",
        "key_facts": ["Rahul", "Mandal"],
        "context_docs": ["series_09_overview"],
    },
    {
        "id": "bench-trivia-010",
        "category": "trivia",
        "difficulty": "medium",
        "series": 12,
        "question": "Who won Series 12 of The Great British Bake Off in 2021 as the show's first Italian winner?",
        "reference_answer": "Giuseppe Dell'Anno won Series 12.",
        "key_facts": ["Giuseppe", "Dell'Anno"],
        "context_docs": ["series_12_overview"],
    },
    {
        "id": "bench-trivia-011",
        "category": "trivia",
        "difficulty": "medium",
        "series": 13,
        "question": "Which cardiovascular research scientist won Series 13 of The Great British Bake Off in 2022?",
        "reference_answer": "Syabira Yusoff won Series 13.",
        "key_facts": ["Syabira", "Yusoff"],
        "context_docs": ["series_13_overview"],
    },
    {
        "id": "bench-trivia-012",
        "category": "trivia",
        "difficulty": "easy",
        "series": 14,
        "question": "Which physical education teacher won Series 14 of The Great British Bake Off in 2023?",
        "reference_answer": "Matty Edgell won Series 14.",
        "key_facts": ["Matty", "Edgell"],
        "context_docs": ["series_14_overview"],
    },
    {
        "id": "bench-trivia-013",
        "category": "trivia",
        "difficulty": "medium",
        "series": 2,
        "question": "Who won Series 2 of The Great British Bake Off in 2011?",
        "reference_answer": "Joanne Wheatley (Jo Wheatley) won Series 2.",
        "key_facts": ["Joanne", "Wheatley"],
        "context_docs": ["series_02_overview"],
    },
    {
        "id": "bench-trivia-014",
        "category": "trivia",
        "difficulty": "easy",
        "series": None,
        "question": "Which original UK television network aired Series 1 through 7 of The Great British Bake Off?",
        "reference_answer": "The BBC (BBC Two for Series 1-4, moving to BBC One for Series 5-7).",
        "key_facts": ["BBC"],
        "context_docs": ["series_01_overview"],
    },
    {
        "id": "bench-trivia-015",
        "category": "trivia",
        "difficulty": "easy",
        "series": None,
        "question": "Who replaced Mary Berry as a judge alongside Paul Hollywood when Bake Off moved to Channel 4?",
        "reference_answer": "Prue Leith joined Paul Hollywood as a judge starting in Series 8.",
        "key_facts": ["Prue", "Leith"],
        "context_docs": ["series_08_overview"],
    },
    {
        "id": "bench-trivia-016",
        "category": "trivia",
        "difficulty": "easy",
        "series": None,
        "question": "Who were the beloved comedic duo who originally presented The Great British Bake Off for Series 1 through 7?",
        "reference_answer": "Mel Giedroyc and Sue Perkins (Mel and Sue).",
        "key_facts": ["Mel", "Sue"],
        "context_docs": ["series_01_overview"],
    },
    {
        "id": "bench-trivia-017",
        "category": "trivia",
        "difficulty": "medium",
        "series": None,
        "question": "Who served as co-presenter alongside Noel Fielding for Series 8 through 10?",
        "reference_answer": "Sandi Toksvig presented alongside Noel Fielding.",
        "key_facts": ["Sandi", "Toksvig"],
        "context_docs": ["series_08_overview"],
    },
    {
        "id": "bench-trivia-018",
        "category": "trivia",
        "difficulty": "medium",
        "series": None,
        "question": "Who succeeded Matt Lucas as co-host alongside Noel Fielding beginning in Series 14?",
        "reference_answer": "Alison Hammond joined Noel Fielding as co-host in Series 14.",
        "key_facts": ["Alison", "Hammond"],
        "context_docs": ["series_14_overview"],
    },
    {
        "id": "bench-trivia-019",
        "category": "trivia",
        "difficulty": "medium",
        "series": 5,
        "question": "What historic estate in Berkshire served as the filming location for the Bake Off marquee tent for most seasons?",
        "reference_answer": "Welford Park in Berkshire.",
        "key_facts": ["Welford", "Park"],
        "context_docs": ["series_05_overview"],
    },
    # ==========================
    # CATEGORY: CHALLENGE REASONING
    # ==========================
    {
        "id": "bench-reasoning-001",
        "category": "challenge_reasoning",
        "difficulty": "hard",
        "series": 3,
        "question": "Which baker received a Hollywood Handshake and was eliminated in the exact same episode?",
        "reference_answer": "Ryan Chong received a Hollywood Handshake for his Key Lime Pie in the Signature challenge of Series 3, Episode 7 (Sweet Dough Week), but was eliminated at the end of the episode.",
        "key_facts": ["Ryan", "Chong", "Sweet Dough"],
        "context_docs": ["episode_s03e07"],
    },
    {
        "id": "bench-reasoning-002",
        "category": "challenge_reasoning",
        "difficulty": "hard",
        "series": 10,
        "question": "Which baker won The Great British Bake Off despite never winning Star Baker during any regular episode of their series?",
        "reference_answer": "David Atherton won Series 10 without winning a single Star Baker title in the preceding nine episodes.",
        "key_facts": ["David", "Atherton", "Series 10"],
        "context_docs": ["baker_s10_david"],
    },
    {
        "id": "bench-reasoning-003",
        "category": "challenge_reasoning",
        "difficulty": "medium",
        "series": 5,
        "question": "Which builder holds the record for winning Star Baker 5 times in a single series?",
        "reference_answer": "Richard Burr won Star Baker 5 times in Series 5.",
        "key_facts": ["Richard", "Burr", "5"],
        "context_docs": ["baker_s05_richard"],
    },
    {
        "id": "bench-reasoning-004",
        "category": "challenge_reasoning",
        "difficulty": "medium",
        "series": 10,
        "question": "Which baker won Star Baker 4 times in Series 10 before finishing as runner-up in the final?",
        "reference_answer": "Steph Blackwell won Star Baker 4 times in Series 10.",
        "key_facts": ["Steph", "Blackwell", "4"],
        "context_docs": ["baker_s10_steph"],
    },
    {
        "id": "bench-reasoning-005",
        "category": "challenge_reasoning",
        "difficulty": "hard",
        "series": 12,
        "question": "Which German baker won 3 Star Baker titles in Series 12 but was eliminated in the semi-final (Patisserie Week)?",
        "reference_answer": "Jürgen Krauss won 3 Star Baker awards in Series 12 before his shock elimination in the semi-final.",
        "key_facts": ["Jürgen", "Krauss"],
        "context_docs": ["baker_s12_jurgen"],
    },
    {
        "id": "bench-reasoning-006",
        "category": "challenge_reasoning",
        "difficulty": "medium",
        "series": 5,
        "question": "In Series 5 Episode 4 (Desserts Week), what famous controversy occurred when Ian Watters' Baked Alaska melted and was thrown into the bin?",
        "reference_answer": "The controversy is known as 'Bingate', where Ian Watters' Baked Alaska melted after being removed from the freezer and he threw it into the bin.",
        "key_facts": ["Bingate", "Baked Alaska", "Ian"],
        "context_docs": ["episode_s05e04"],
    },
    {
        "id": "bench-reasoning-007",
        "category": "challenge_reasoning",
        "difficulty": "hard",
        "series": 5,
        "question": "Which contestant withdrew from the competition due to illness the week following the 'Bingate' incident in Series 5?",
        "reference_answer": "Diana Beard withdrew from the competition in Episode 5 of Series 5.",
        "key_facts": ["Diana", "Beard"],
        "context_docs": ["episode_s05e05"],
    },
    {
        "id": "bench-reasoning-008",
        "category": "challenge_reasoning",
        "difficulty": "medium",
        "series": 6,
        "question": "What personal centerpiece did Nadiya Hussain bake for her winning final Showstopper in Series 6?",
        "reference_answer": "Nadiya baked 'My Big Fat British Wedding Cake' (a tiered lemon drizzle cake decorated with jewels and sari fabric) because she never had a traditional wedding cake at her marriage.",
        "key_facts": ["wedding cake", "lemon drizzle"],
        "context_docs": ["episode_s06e10"],
    },
    {
        "id": "bench-reasoning-009",
        "category": "challenge_reasoning",
        "difficulty": "hard",
        "series": 9,
        "question": "Which series of The Great British Bake Off featured the highest frequency of Hollywood Handshakes, including 3 each to Rahul Mandal and Dan Beasley-Harling?",
        "reference_answer": "Series 9 (2018) featured a record number of Hollywood Handshakes.",
        "key_facts": ["Series 9", "2018"],
        "context_docs": ["series_09_overview"],
    },
    {
        "id": "bench-reasoning-010",
        "category": "challenge_reasoning",
        "difficulty": "medium",
        "series": 11,
        "question": "Who was the first Scottish contestant to ever win The Great British Bake Off?",
        "reference_answer": "Peter Sawkins, from Edinburgh, was the first Scottish winner.",
        "key_facts": ["Peter", "Sawkins", "Scottish"],
        "context_docs": ["series_11_overview"],
    },
    # ==========================
    # CATEGORY: BAKING RULES & SHOW MECHANICS
    # ==========================
    {
        "id": "bench-rules-001",
        "category": "baking_rules",
        "difficulty": "easy",
        "series": None,
        "question": "What are the three distinct baking challenges featured in every standard episode of The Great British Bake Off?",
        "reference_answer": "The Signature Challenge, the Technical Challenge, and the Showstopper Challenge.",
        "key_facts": ["Signature", "Technical", "Showstopper"],
        "context_docs": ["rules_challenges"],
    },
    {
        "id": "bench-rules-002",
        "category": "baking_rules",
        "difficulty": "easy",
        "series": None,
        "question": "How is the Technical Challenge judged in The Great British Bake Off?",
        "reference_answer": "The Technical Challenge is judged blind. The judges leave the tent during preparation and taste the bakes without knowing which baker made which item.",
        "key_facts": ["blind", "without knowing"],
        "context_docs": ["rules_technical"],
    },
    {
        "id": "bench-rules-003",
        "category": "baking_rules",
        "difficulty": "easy",
        "series": None,
        "question": "What honor is awarded at the conclusion of each episode to the baker who performed best overall across the three challenges?",
        "reference_answer": "The title of Star Baker.",
        "key_facts": ["Star Baker"],
        "context_docs": ["rules_star_baker"],
    },
    {
        "id": "bench-rules-004",
        "category": "baking_rules",
        "difficulty": "easy",
        "series": None,
        "question": "What catchphrase is uttered by the presenters to officially start the baking timer for every challenge?",
        "reference_answer": "'On your marks, get set, bake!'",
        "key_facts": ["On your marks", "get set", "bake"],
        "context_docs": ["rules_catchphrase"],
    },
    {
        "id": "bench-rules-005",
        "category": "baking_rules",
        "difficulty": "easy",
        "series": None,
        "question": "How many finalist bakers typically compete in the Grand Finale episode of a GBBO series?",
        "reference_answer": "Three finalists compete in the Grand Finale.",
        "key_facts": ["Three", "3"],
        "context_docs": ["rules_finale"],
    },
    {
        "id": "bench-rules-006",
        "category": "baking_rules",
        "difficulty": "medium",
        "series": None,
        "question": "Under what broadcast title is The Great British Bake Off known in the United States and Canada?",
        "reference_answer": "The Great British Baking Show (due to the trademark on 'Bake-Off' owned by Pillsbury).",
        "key_facts": ["The Great British Baking Show"],
        "context_docs": ["rules_us_title"],
    },
    {
        "id": "bench-rules-007",
        "category": "baking_rules",
        "difficulty": "medium",
        "series": None,
        "question": "What purpose does the Signature Challenge serve in the episode structure?",
        "reference_answer": "The Signature challenge allows bakers to showcase their tried-and-tested personal home recipes that reflect their individual baking style.",
        "key_facts": ["home recipes", "style"],
        "context_docs": ["rules_signature"],
    },
    {
        "id": "bench-rules-008",
        "category": "baking_rules",
        "difficulty": "medium",
        "series": None,
        "question": "What happens when bakers prepare the Technical Challenge regarding their recipe instructions?",
        "reference_answer": "Bakers receive an identical surprise recipe with intentionally sparse, minimal instructions that test their foundational baking instincts.",
        "key_facts": ["minimal", "instructions", "recipe"],
        "context_docs": ["rules_technical"],
    },
    {
        "id": "bench-rules-009",
        "category": "baking_rules",
        "difficulty": "medium",
        "series": None,
        "question": "What is the primary evaluation focus of the Showstopper Challenge?",
        "reference_answer": "The Showstopper is designed to test technical skill and artistic presentation, demanding a professional, visually spectacular centerpiece with exquisite flavor.",
        "key_facts": ["artistic", "presentation", "flavor"],
        "context_docs": ["rules_showstopper"],
    },
    {
        "id": "bench-rules-010",
        "category": "baking_rules",
        "difficulty": "hard",
        "series": None,
        "question": "What prize or cash award do the winners of The Great British Bake Off receive upon winning the finale?",
        "reference_answer": "Winners do not receive any monetary cash prize; they receive an engraved glass cake stand trophy and a bouquet of flowers.",
        "key_facts": ["cake stand", "no", "cash prize"],
        "context_docs": ["rules_prizes"],
    },
    # ==========================
    # CATEGORY: HANDSHAKES & ACCOLADES
    # ==========================
    {
        "id": "bench-handshakes-001",
        "category": "handshakes_and_accolades",
        "difficulty": "easy",
        "series": None,
        "question": "What spontaneous gesture does judge Paul Hollywood bestow upon a baker for an extraordinary, near-flawless bake?",
        "reference_answer": "The Hollywood Handshake (or Paul Hollywood Handshake).",
        "key_facts": ["Hollywood Handshake", "Paul"],
        "context_docs": ["rules_handshake"],
    },
    {
        "id": "bench-handshakes-002",
        "category": "handshakes_and_accolades",
        "difficulty": "medium",
        "series": 9,
        "question": "Who were the two bakers in Series 9 who received 3 Hollywood Handshakes each during their series run?",
        "reference_answer": "Rahul Mandal and Dan Beasley-Harling each received 3 Hollywood Handshakes in Series 9.",
        "key_facts": ["Rahul", "Dan"],
        "context_docs": ["series_09_overview"],
    },
    {
        "id": "bench-handshakes-003",
        "category": "handshakes_and_accolades",
        "difficulty": "hard",
        "series": 15,
        "question": "Which young baker in Series 15 received 3 Hollywood Handshakes during the competition?",
        "reference_answer": "Dylan Bachelet received 3 Hollywood Handshakes in Series 15.",
        "key_facts": ["Dylan", "Bachelet"],
        "context_docs": ["baker_s15_dylan"],
    },
    {
        "id": "bench-handshakes-004",
        "category": "handshakes_and_accolades",
        "difficulty": "medium",
        "series": 3,
        "question": "In what series was the very first Hollywood Handshake famously given to Ryan Chong for his Key Lime Pie?",
        "reference_answer": "Series 3 (2012) in Episode 7.",
        "key_facts": ["Series 3", "2012"],
        "context_docs": ["episode_s03e07"],
    },
    {
        "id": "bench-handshakes-005",
        "category": "handshakes_and_accolades",
        "difficulty": "medium",
        "series": 12,
        "question": "Which Italian baker and eventual Series 12 winner received 2 Hollywood Handshakes during his run?",
        "reference_answer": "Giuseppe Dell'Anno received 2 Hollywood Handshakes in Series 12.",
        "key_facts": ["Giuseppe", "Dell'Anno"],
        "context_docs": ["baker_s12_giuseppe"],
    },
    {
        "id": "bench-handshakes-006",
        "category": "handshakes_and_accolades",
        "difficulty": "hard",
        "series": 8,
        "question": "Which baker in Series 8 received 2 Hollywood Handshakes and won Star Baker 3 times before reaching the final?",
        "reference_answer": "Steven Carter-Bailey received 2 handshakes and 3 Star Baker titles in Series 8.",
        "key_facts": ["Steven", "Carter-Bailey"],
        "context_docs": ["baker_s08_steven"],
    },
]


class BenchmarkSuite:
    """Manages GBBO AI evaluation benchmark prompts and scoring harness."""

    def __init__(
        self,
        benchmark_file: Path | str = "data/ai/gbbo_benchmark_suite.jsonl",
    ) -> None:
        self.benchmark_file = Path(benchmark_file)

    def save_default_suite(self) -> Path:
        """Save the default curated benchmark items to disk."""
        self.benchmark_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.benchmark_file, "w", encoding="utf-8") as f:
            f.writelines(
                json.dumps(item, ensure_ascii=False) + "\n" for item in BENCHMARK_ITEMS
            )
        logger.info(
            "Saved %d benchmark test items to %s",
            len(BENCHMARK_ITEMS),
            self.benchmark_file,
        )
        return self.benchmark_file

    def load_suite(self) -> list[dict[str, Any]]:
        """Load benchmark suite from file or fallback to built-in items."""
        if not self.benchmark_file.exists():
            self.save_default_suite()

        items = []
        with open(self.benchmark_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    @staticmethod
    def score_response(item: dict[str, Any], response: str) -> dict[str, Any]:
        """Score an LLM response against key facts and rubric criteria."""
        response_lower = response.lower()
        key_facts = item.get("key_facts", [])

        if not key_facts:
            return {
                "score": 1.0,
                "passed": True,
                "matched_facts": [],
                "missing_facts": [],
            }

        matched = [fact for fact in key_facts if fact.lower() in response_lower]
        missing = [fact for fact in key_facts if fact.lower() not in response_lower]

        score = len(matched) / len(key_facts)
        passed = score >= 0.5

        return {
            "score": round(score, 3),
            "passed": passed,
            "matched_facts": matched,
            "missing_facts": missing,
        }

    def evaluate_benchmark(
        self,
        eval_fn: Callable[[str], str] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a model or run self-evaluation using reference ground truth answers."""
        suite = self.load_suite()

        results_by_cat: dict[str, list[dict[str, Any]]] = {
            "trivia": [],
            "challenge_reasoning": [],
            "baking_rules": [],
            "handshakes_and_accolades": [],
        }

        total_score = 0.0
        total_passed = 0

        for item in suite:
            cat = item.get("category", "trivia")
            question = item.get("question", "")

            response = (
                eval_fn(question) if eval_fn else item.get("reference_answer", "")
            )
            eval_result = self.score_response(item, response)

            result_entry = {
                "id": item.get("id"),
                "question": question,
                "score": eval_result["score"],
                "passed": eval_result["passed"],
                "matched_facts": eval_result["matched_facts"],
                "missing_facts": eval_result["missing_facts"],
            }
            results_by_cat.setdefault(cat, []).append(result_entry)

            total_score += eval_result["score"]
            if eval_result["passed"]:
                total_passed += 1

        total_questions = len(suite)
        avg_score = total_score / total_questions if total_questions else 0.0

        summary = {
            "total_questions": total_questions,
            "total_passed": total_passed,
            "pass_rate": round(total_passed / total_questions, 3)
            if total_questions
            else 0.0,
            "average_score": round(avg_score, 3),
            "categories": {},
        }

        for cat, items in results_by_cat.items():
            cat_count = len(items)
            cat_passed = sum(1 for i in items if i["passed"])
            cat_score = sum(i["score"] for i in items) / cat_count if cat_count else 0.0
            summary["categories"][cat] = {
                "count": cat_count,
                "passed": cat_passed,
                "pass_rate": round(cat_passed / cat_count, 3) if cat_count else 0.0,
                "avg_score": round(cat_score, 3),
            }

        return summary

    def render_summary(self, summary: dict[str, Any]) -> None:
        """Render evaluation summary table using Rich."""
        console = Console()
        table = Table(
            title="The Great British Bake Off AI Benchmark Results", show_lines=True
        )
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Evaluated", style="magenta", justify="right")
        table.add_column("Passed", style="green", justify="right")
        table.add_column("Pass Rate", style="yellow", justify="right")
        table.add_column("Average Score", style="bold green", justify="right")

        for cat, data in summary.get("categories", {}).items():
            table.add_row(
                cat.replace("_", " ").title(),
                str(data["count"]),
                str(data["passed"]),
                f"{data['pass_rate'] * 100:.1f}%",
                f"{data['avg_score'] * 100:.1f}%",
            )

        table.add_row(
            "[bold]Total / Overall[/bold]",
            f"[bold]{summary['total_questions']}[/bold]",
            f"[bold]{summary['total_passed']}[/bold]",
            f"[bold]{summary['pass_rate'] * 100:.1f}%[/bold]",
            f"[bold]{summary['average_score'] * 100:.1f}%[/bold]",
        )
        console.print(table)
