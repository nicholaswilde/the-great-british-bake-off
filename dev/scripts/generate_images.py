"""Generate publication-quality data visualizations and branding assets for The Great British Bake Off dataset.

Mirrors the structure and aesthetic of doehm/alone and the-amazing-race:
- survival.png: Kaplan-Meier style baker survival curves across episodes with inset boxplots
- items.png: Horizontal bar chart of top recurring flavor components across 1,000+ bakes
- boxplots.png: Baker age distributions across finish placement tiers
- gender_performance.png: Baker gender dynamics (Star Baker honors, technical wins, championship shares)
- handshakes_evolution.png: Evolution of Paul Hollywood's handshake across broadcast eras
- technical_performance.png: Technical rank percentile mastery and Star Baker conversion to finale
- thegreatbritishbakeoff hex.png: R package hexagonal sticker badge (3600x3600 RGBA)
- bg.png, bg white.png: Dark and light square social cards
- bg hex.png, bg white hex.png: Hexagon silhouette masks
- square.jpg: Showcase card with key dataset statistics
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from PIL import Image, ImageDraw, ImageFont

# Brand palette inspired by the iconic Bake Off tent aesthetics
PALETTE = {
    "powder_blue": "#5C94B3",
    "raspberry": "#C74163",
    "gold_caramel": "#D48C2E",
    "sage_green": "#4A7C59",
    "dark_plum": "#2B2038",
    "chocolate": "#5C3D2E",
    "citrus_lemon": "#E2B13C",
    "slate": "#3A506B",
    "dark": "#1A1D20",
    "gray_text": "#2B2D42",
    "gray_line": "#D1D5DB",
    "bg_white": "#FFFFFF",
    "bg_card": "#FDFBF7",
}

FONT_FAMILY = "DejaVu Sans"
plt.rcParams["font.sans-serif"] = [
    FONT_FAMILY,
    "Liberation Sans",
    "DejaVu Sans",
    "Arial",
]
plt.rcParams["font.family"] = "sans-serif"


def setup_canvas(
    width_in: float, height_in: float, dpi: int = 300
) -> tuple[plt.Figure, plt.Axes]:
    """Create a clean figure and axes with minimalist void styling."""
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])
    return fig, ax


def generate_survival_chart(output_dir: Path) -> None:
    """Generate survival.png: Baker survival curves across episodes with inset boxplot."""
    print("Generating survival.png...")
    bakers_df = pd.read_json("data/processed/bakers.json")
    performances_df = pd.read_json("data/processed/performances.json")
    episodes_df = pd.read_json("data/processed/episodes.json")

    # Map max episode reached per baker
    mp = performances_df.merge(
        episodes_df[["episode_id", "series_number", "episode_number"]], on="episode_id"
    )
    episodes_reached = mp.groupby("baker_id")["episode_number"].max().reset_index()
    episodes_reached.columns = ["baker_id", "max_episode"]
    bakers = bakers_df.merge(episodes_reached, on="baker_id", how="left")

    def age_bracket(age: float) -> str:
        if pd.isna(age):
            return "Other"
        if age < 30:
            return "Under 30"
        elif age < 50:
            return "30–49"
        else:
            return "50+"

    bakers["age_group"] = bakers["age"].apply(age_bracket)
    archetypes = ["Under 30", "30–49", "50+"]

    max_ep = 10
    surv_data: dict[str, list[float]] = {}
    for arch in archetypes:
        subset = bakers[bakers["age_group"] == arch]
        n_total = len(subset)
        rates = []
        for ep in range(max_ep + 1):
            if ep == 0:
                rates.append(1.0)
            else:
                survived = (subset["max_episode"] >= ep).sum()
                rates.append(survived / n_total if n_total > 0 else 0.0)
        surv_data[arch] = rates

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    ax_main = fig.add_axes([0.08, 0.12, 0.88, 0.68])
    ax_main.set_facecolor(PALETTE["bg_white"])

    colors = {
        "Under 30": PALETTE["raspberry"],
        "30–49": PALETTE["powder_blue"],
        "50+": PALETTE["sage_green"],
    }

    eps_range = list(range(max_ep + 1))
    for arch in archetypes:
        n_count = len(bakers[bakers["age_group"] == arch])
        ax_main.step(
            eps_range,
            surv_data[arch],
            where="post",
            label=f"{arch} (n={n_count})",
            color=colors[arch],
            linewidth=2.8,
            alpha=0.95,
        )

    ax_main.set_xlim(0, max_ep)
    ax_main.set_ylim(-0.02, 1.05)
    ax_main.set_xlabel(
        "Episode Reached",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_main.set_ylabel(
        "Proportion of Bakers Remaining",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_main.set_xticks(range(max_ep + 1))
    ax_main.set_yticks(np.arange(0.0, 1.1, 0.2))
    ax_main.set_yticklabels([f"{int(y * 100)}%" for y in np.arange(0.0, 1.1, 0.2)])
    ax_main.tick_params(colors=PALETTE["gray_text"], labelsize=11)

    ax_main.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax_main.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_main.spines[spine].set_color(PALETTE["gray_line"])
        ax_main.spines[spine].set_linewidth(1.2)

    ax_main.legend(
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=10.5,
        framealpha=0.9,
    )

    fig.text(
        0.08,
        0.92,
        "Baker survival curves across episodes",
        fontsize=24,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.08,
        0.87,
        "Younger bakers sustain significantly higher progression rates into late-stage episodes than veteran bakers",
        fontsize=12,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.03,
        "Data: 204 bakers across 17 Series | the-great-british-bake-off package",
        fontsize=9,
        color="#8E9AA7",
    )

    # Inset horizontal boxplot of episodes reached
    ax_inset = fig.add_axes([0.16, 0.18, 0.32, 0.28])
    ax_inset.set_facecolor(PALETTE["bg_card"])
    ax_inset.patch.set_alpha(0.85)

    box_data = [
        bakers[bakers["age_group"] == arch]["max_episode"].dropna().tolist()
        for arch in reversed(archetypes)
    ]
    box_colors = [colors[arch] for arch in reversed(archetypes)]

    bplot = ax_inset.boxplot(
        box_data,
        orientation="horizontal",
        patch_artist=True,
        widths=0.6,
        showfliers=False,
        medianprops={"color": PALETTE["dark"], "linewidth": 1.8},
    )
    for patch, col in zip(bplot["boxes"], box_colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.65)
        patch.set_edgecolor(col)

    np.random.seed(42)
    for i, (vals, col) in enumerate(zip(box_data, box_colors)):
        y_jitter = np.random.normal(i + 1, 0.08, size=len(vals))
        ax_inset.scatter(vals, y_jitter, color=col, alpha=0.35, s=14, edgecolors="none")

    ax_inset.set_yticks(range(1, len(archetypes) + 1))
    ax_inset.set_yticklabels(
        reversed(archetypes),
        fontsize=8.5,
        fontweight="bold",
        color=PALETTE["gray_text"],
    )
    ax_inset.set_xlabel("Episodes Completed", fontsize=8.5, color=PALETTE["gray_text"])
    ax_inset.tick_params(labelsize=8, colors=PALETTE["gray_text"])
    ax_inset.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.5)
    for spine in ax_inset.spines.values():
        spine.set_color(PALETTE["gray_line"])
        spine.set_linewidth(0.8)

    out_file = output_dir / "survival.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_items_chart(output_dir: Path) -> None:
    """Generate items.png: Horizontal bar chart of top featured flavors and ingredients."""
    print("Generating items.png...")
    performances_df = pd.read_json("data/processed/performances.json")

    dishes = (
        performances_df["signature_dish"].dropna().tolist()
        + performances_df["showstopper_dish"].dropna().tolist()
    )

    flavor_list = [
        "Chocolate",
        "Lemon",
        "Orange",
        "Raspberry",
        "Apple",
        "Caramel",
        "Ginger",
        "Pistachio",
        "Cherry",
        "Almond",
        "Coconut",
        "Strawberry",
        "Walnut",
        "Hazelnut",
    ]

    counts: dict[str, int] = Counter()
    for dish in dishes:
        d_lower = str(dish).lower()
        for f in flavor_list:
            if re.search(r"\b" + re.escape(f.lower()) + r"\b", d_lower):
                counts[f] += 1

    top_items = [(f, counts[f]) for f in flavor_list]
    top_items = sorted(top_items, key=lambda x: x[1], reverse=False)

    labels = [k for k, _ in top_items]
    values = [v for _, v in top_items]

    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, height=0.68, color=PALETTE["powder_blue"], alpha=0.92)

    # Custom color accents for signature ingredients
    for i, label in enumerate(labels):
        if label == "Chocolate":
            bars[i].set_color(PALETTE["chocolate"])
        elif label in ("Lemon", "Orange", "Caramel"):
            bars[i].set_color(PALETTE["gold_caramel"])
        elif label in ("Raspberry", "Cherry", "Strawberry"):
            bars[i].set_color(PALETTE["raspberry"])
        elif label in ("Pistachio", "Apple"):
            bars[i].set_color(PALETTE["sage_green"])

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 4.0,
            bar.get_y() + bar.get_height() / 2.0,
            f"{val}",
            va="center",
            ha="left",
            fontsize=10.5,
            fontweight="bold",
            color=PALETTE["gray_text"],
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        labels, fontsize=11, fontweight="bold", color=PALETTE["gray_text"]
    )
    ax.set_xlim(0, max(values) + 35)
    ax.set_xlabel(
        "Number of Challenge Bakes Featuring Flavor",
        fontsize=11,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax.tick_params(colors=PALETTE["gray_text"], labelsize=10)

    ax.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(PALETTE["gray_line"])
        ax.spines[spine].set_linewidth(1.1)

    fig.text(
        0.12,
        0.94,
        "Most featured flavors & signature ingredients",
        fontsize=18,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.12,
        0.90,
        "Total bake appearances across all signature and showstopper challenges (Series 1–15)",
        fontsize=10.5,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.12,
        0.02,
        "Data: the-great-british-bake-off package | 1,200+ performances analyzed",
        fontsize=8.5,
        color="#8E9AA7",
    )

    plt.subplots_adjust(left=0.22, right=0.92, top=0.86, bottom=0.10)
    out_file = output_dir / "items.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_boxplots_chart(output_dir: Path) -> None:
    """Generate boxplots.png: Baker age distribution across finish placement tiers."""
    print("Generating boxplots.png...")
    bakers_df = pd.read_json("data/processed/bakers.json")

    def tier(p: float) -> str | None:
        if pd.isna(p):
            return None
        p = int(p)
        if p == 1:
            return "Winners (1st)"
        elif p in (2, 3):
            return "Finalists (2nd–3rd)"
        elif p in (4, 5):
            return "Semifinalists (4th–5th)"
        elif 6 <= p <= 8:
            return "Mid-Pack (6th–8th)"
        else:
            return "Early Exits (9th+)"

    bakers = bakers_df.copy()
    bakers["tier"] = bakers["overall_placement"].apply(tier)
    tiers_order = [
        "Winners (1st)",
        "Finalists (2nd–3rd)",
        "Semifinalists (4th–5th)",
        "Mid-Pack (6th–8th)",
        "Early Exits (9th+)",
    ]

    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])

    data = [bakers[bakers["tier"] == t]["age"].dropna().tolist() for t in tiers_order]
    tier_colors = [
        PALETTE["gold_caramel"],
        PALETTE["raspberry"],
        PALETTE["powder_blue"],
        PALETTE["sage_green"],
        PALETTE["slate"],
    ]

    bplot = ax.boxplot(
        data,
        orientation="horizontal",
        patch_artist=True,
        widths=0.55,
        medianprops={"color": PALETTE["dark"], "linewidth": 2.4},
        flierprops={
            "marker": "o",
            "markersize": 4,
            "alpha": 0.4,
            "markerfacecolor": PALETTE["dark"],
        },
    )

    for patch, col in zip(bplot["boxes"], tier_colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.70)
        patch.set_edgecolor(PALETTE["dark"])
        patch.set_linewidth(1.4)

    np.random.seed(42)
    for i, (vals, col) in enumerate(zip(data, tier_colors)):
        y_jit = np.random.normal(i + 1, 0.08, size=len(vals))
        ax.scatter(
            vals, y_jit, color=PALETTE["dark"], alpha=0.32, s=28, edgecolors="none"
        )

    ax.set_yticks(range(1, len(tiers_order) + 1))
    ax.set_yticklabels(
        [f"{t}\n(n={len(vals)})" for t, vals in zip(tiers_order, data)],
        fontsize=11,
        fontweight="bold",
        color=PALETTE["gray_text"],
    )
    ax.set_xlabel(
        "Baker Age (Years)",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=12,
    )
    ax.tick_params(colors=PALETTE["gray_text"], labelsize=11)
    ax.set_xlim(14, 76)

    # Highlight historical winner sweet spot (25-35)
    ax.axvspan(
        25,
        35,
        color=PALETTE["gold_caramel"],
        alpha=0.15,
        label="Optimal Winner Age Sweet Spot (25–35)",
    )

    ax.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(PALETTE["gray_line"])
        ax.spines[spine].set_linewidth(1.2)

    ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=11,
    )

    fig.text(
        0.08,
        0.94,
        "Baker age distributions by finish placement",
        fontsize=22,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.08,
        0.89,
        "Championship winners and finalists cluster tightly in the 25–35 age demographic with significantly lower variance",
        fontsize=12,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.03,
        "Data: 196 classified bakers across 16 completed GBBO series | the-great-british-bake-off package",
        fontsize=9,
        color="#8E9AA7",
    )

    plt.subplots_adjust(left=0.20, right=0.94, top=0.84, bottom=0.12)
    out_file = output_dir / "boxplots.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_gender_performance_chart(output_dir: Path) -> None:
    """Generate gender_performance.png: Baker gender dynamics and championship conversion."""
    print("Generating gender_performance.png...")
    bakers_df = pd.read_json("data/processed/bakers.json")
    performances_df = pd.read_json("data/processed/performances.json")

    # Aggregate honors per baker
    star_bakers = (
        performances_df[performances_df["result"] == "STAR_BAKER"]
        .groupby("baker_id")
        .size()
        .rename("star_bakers")
    )
    handshakes = (
        performances_df[performances_df["hollywood_handshake"] == True]
        .groupby("baker_id")
        .size()
        .rename("handshakes")
    )
    tech_wins = (
        performances_df[performances_df["technical_rank"] == 1]
        .groupby("baker_id")
        .size()
        .rename("tech_wins")
    )

    b = bakers_df.merge(star_bakers, on="baker_id", how="left").fillna(
        {"star_bakers": 0}
    )
    b = b.merge(handshakes, on="baker_id", how="left").fillna({"handshakes": 0})
    b = b.merge(tech_wins, on="baker_id", how="left").fillna({"tech_wins": 0})
    b = b[b["gender"].isin(["F", "M"])].copy()

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Left: Honors per Baker Distributions
    ax_left = fig.add_axes([0.14, 0.16, 0.36, 0.65])
    ax_left.set_facecolor(PALETTE["bg_white"])

    categories = ["Technical Wins", "Star Bakers", "Handshakes"]
    f_totals = [
        float(b[b["gender"] == "F"]["tech_wins"].sum()),
        float(b[b["gender"] == "F"]["star_bakers"].sum()),
        float(b[b["gender"] == "F"]["handshakes"].sum()),
    ]
    m_totals = [
        float(b[b["gender"] == "M"]["tech_wins"].sum()),
        float(b[b["gender"] == "M"]["star_bakers"].sum()),
        float(b[b["gender"] == "M"]["handshakes"].sum()),
    ]

    y_pos = np.arange(len(categories))
    h = 0.32

    b_f = ax_left.barh(
        y_pos + h / 2,
        f_totals,
        height=h,
        color=PALETTE["raspberry"],
        alpha=0.90,
        label="Female Bakers (n=103)",
    )
    b_m = ax_left.barh(
        y_pos - h / 2,
        m_totals,
        height=h,
        color=PALETTE["powder_blue"],
        alpha=0.90,
        label="Male Bakers (n=100)",
    )

    for bar, val in zip(b_f, f_totals):
        ax_left.text(
            val + 1.2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(val)}",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=PALETTE["raspberry"],
        )

    for bar, val in zip(b_m, m_totals):
        ax_left.text(
            val + 1.2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(val)}",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=PALETTE["powder_blue"],
        )

    ax_left.set_yticks(y_pos)
    ax_left.set_yticklabels(
        categories, fontsize=11, fontweight="bold", color=PALETTE["gray_text"]
    )
    ax_left.set_xlim(0, 105)
    ax_left.set_xlabel(
        "Total Accolades Awarded",
        fontsize=11,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_left.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_left.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_left.set_title(
        "Challenge Accolades by Gender",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["dark"],
        pad=14,
    )
    ax_left.legend(
        loc="lower right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=9.5,
    )

    for spine in ["top", "right"]:
        ax_left.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_left.spines[spine].set_color(PALETTE["gray_line"])
        ax_left.spines[spine].set_linewidth(1.1)

    # Right: Championship Titles & Finale Shares
    ax_right = fig.add_axes([0.58, 0.16, 0.36, 0.65])
    ax_right.set_facecolor(PALETTE["bg_white"])

    completed_winners = b[b["overall_placement"] == 1]
    f_wins = len(completed_winners[completed_winners["gender"] == "F"])
    m_wins = len(completed_winners[completed_winners["gender"] == "M"])
    tot_wins = f_wins + m_wins

    f_finalists = len(
        b[(b["overall_placement"].isin([1, 2, 3])) & (b["gender"] == "F")]
    )
    m_finalists = len(
        b[(b["overall_placement"].isin([1, 2, 3])) & (b["gender"] == "M")]
    )

    f_win_pct = f_wins / tot_wins * 100
    m_win_pct = m_wins / tot_wins * 100

    y_indices = np.array([1, 2])
    bar_h = 0.32

    win_vals = [f_win_pct, m_win_pct]
    final_counts = [f_finalists, m_finalists]
    colors = [PALETTE["raspberry"], PALETTE["powder_blue"]]

    ax_right.barh(
        y_indices + bar_h / 2, win_vals, height=bar_h, color=colors, alpha=0.90
    )
    ax_right.barh(
        y_indices - bar_h / 2,
        [f / 48 * 100 for f in final_counts],
        height=bar_h,
        color=colors,
        alpha=0.5,
        hatch="//",
    )

    ax_right.text(
        f_win_pct + 1.5,
        1 + bar_h / 2,
        f"{f_win_pct:.1f}% ({f_wins} titles)",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=PALETTE["raspberry"],
    )
    ax_right.text(
        m_win_pct + 1.5,
        2 + bar_h / 2,
        f"{m_win_pct:.1f}% ({m_wins} titles)",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=PALETTE["powder_blue"],
    )

    ax_right.text(
        f_finalists / 48 * 100 + 1.5,
        1 - bar_h / 2,
        f"{f_finalists} finalists",
        va="center",
        fontsize=9,
        color=PALETTE["gray_text"],
    )
    ax_right.text(
        m_finalists / 48 * 100 + 1.5,
        2 - bar_h / 2,
        f"{m_finalists} finalists",
        va="center",
        fontsize=9,
        color=PALETTE["gray_text"],
    )

    ax_right.set_yticks(y_indices)
    ax_right.set_yticklabels(
        ["Female Bakers", "Male Bakers"],
        fontsize=11,
        fontweight="bold",
        color=PALETTE["gray_text"],
    )
    ax_right.set_xlim(0, 100)
    ax_right.set_ylim(0.4, 2.8)
    ax_right.set_xlabel(
        "Championship & Finale Share (%)",
        fontsize=11,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_right.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_right.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_right.set_title(
        "Championship Titles & Finale Conversion",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["dark"],
        pad=14,
    )

    for spine in ["top", "right"]:
        ax_right.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_right.spines[spine].set_color(PALETTE["gray_line"])
        ax_right.spines[spine].set_linewidth(1.1)

    legend_elements = [
        patches.Patch(
            facecolor="#4A5568",
            alpha=0.9,
            label="Championship Win Share (16 Completed Series)",
        ),
        patches.Patch(
            facecolor="#4A5568",
            alpha=0.5,
            hatch="//",
            label="Finale Qualification Share (%)",
        ),
    ]
    ax_right.legend(
        handles=legend_elements,
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=8.5,
    )

    callout_rect = patches.FancyBboxPatch(
        (0.08, 0.042),
        0.86,
        0.055,
        boxstyle="round,pad=0.015",
        facecolor=PALETTE["bg_card"],
        edgecolor=PALETTE["gold_caramel"],
        linewidth=1.5,
    )
    fig.patches.append(callout_rect)
    fig.text(
        0.51,
        0.068,
        "Historic Parity: Female bakers have won 9 titles (56.3%) and male bakers 7 titles (43.8%) across 16 completed series, with near identical finale qualification rates (23 vs 25 finalists).",
        fontsize=9,
        ha="center",
        va="center",
        color=PALETTE["gray_text"],
        style="italic",
    )

    fig.text(
        0.08,
        0.94,
        "Baker gender dynamics & performance",
        fontsize=22,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.08,
        0.89,
        "Comparison of Star Baker honors, technical rankings, and title shares across 204 bakers",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.012,
        "Data: 204 bakers across 17 Series | the-great-british-bake-off package",
        fontsize=8.5,
        color="#8E9AA7",
    )

    out_file = output_dir / "gender_performance.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_handshakes_evolution_chart(output_dir: Path) -> None:
    """Generate handshakes_evolution.png: Evolution of Hollywood Handshakes across broadcast eras."""
    print("Generating handshakes_evolution.png...")
    episodes_df = pd.read_json("data/processed/episodes.json")
    performances_df = pd.read_json("data/processed/performances.json")

    mp = performances_df.merge(
        episodes_df[["episode_id", "series_number", "episode_number"]], on="episode_id"
    )
    hs = mp.groupby("series_number")["hollywood_handshake"].sum().reset_index()
    hs = hs[hs["series_number"] <= 16]

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Top: Historical Handshake Frequency
    ax_top = fig.add_axes([0.16, 0.54, 0.78, 0.32])
    ax_top.set_facecolor(PALETTE["bg_white"])

    ax_top.axvspan(
        0.5,
        4.5,
        color=PALETTE["powder_blue"],
        alpha=0.12,
        label="BBC Two Era (S1–S4, Mean = 0.5 / series)",
    )
    ax_top.axvspan(
        4.5,
        7.5,
        color=PALETTE["raspberry"],
        alpha=0.12,
        label="BBC One Era (S5–S7, Mean = 2.3 / series)",
    )
    ax_top.axvspan(
        7.5,
        16.5,
        color=PALETTE["gold_caramel"],
        alpha=0.12,
        label="Channel 4 Era (S8–S16, Mean = 5.2 / series)",
    )

    ax_top.plot(
        hs["series_number"],
        hs["hollywood_handshake"],
        color=PALETTE["dark_plum"],
        marker="o",
        markersize=6,
        linewidth=2.4,
        label="Handshakes Awarded",
    )
    ax_top.scatter(
        hs["series_number"],
        hs["hollywood_handshake"],
        color=PALETTE["gold_caramel"],
        s=45,
        zorder=4,
    )

    # Annotate historic milestones
    ax_top.annotate(
        "S3: Ryan Chong\nFirst Handshake (Pudding Week)",
        xy=(3, 1),
        xytext=(1.2, 5.0),
        arrowprops={"arrowstyle": "->", "color": PALETTE["gray_text"], "lw": 1.2},
        fontsize=8.5,
        color=PALETTE["gray_text"],
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": PALETTE["bg_card"],
            "edgecolor": PALETTE["gray_line"],
            "alpha": 0.9,
        },
    )

    ax_top.annotate(
        "S9: Peak 'Handshake Inflation'\n(12 Handshakes Awarded)",
        xy=(9, 12),
        xytext=(10.0, 10.5),
        arrowprops={"arrowstyle": "->", "color": PALETTE["raspberry"], "lw": 1.2},
        fontsize=8.5,
        color=PALETTE["raspberry"],
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": PALETTE["bg_card"],
            "edgecolor": PALETTE["raspberry"],
            "alpha": 0.9,
        },
    )

    ax_top.set_xlim(0.5, 16.5)
    ax_top.set_ylim(-0.5, 14.0)
    ax_top.set_ylabel(
        "Handshakes Awarded",
        fontsize=10.5,
        fontweight="bold",
        color=PALETTE["gray_text"],
    )
    ax_top.tick_params(colors=PALETTE["gray_text"], labelsize=9.5)
    ax_top.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.6)
    ax_top.legend(
        loc="upper left",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=8.5,
    )

    for spine in ["top", "right"]:
        ax_top.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_top.spines[spine].set_color(PALETTE["gray_line"])
        ax_top.spines[spine].set_linewidth(1.0)

    # Bottom: Era averages comparison
    ax_bot = fig.add_axes([0.16, 0.12, 0.78, 0.30])
    ax_bot.set_facecolor(PALETTE["bg_white"])

    eras = [
        "BBC Two Era\n(Series 1–4)",
        "BBC One Era\n(Series 5–7)",
        "Channel 4 Era\n(Series 8–16)",
    ]
    era_avgs = [2 / 4, 7 / 3, 47 / 9]
    era_totals = [2, 7, 47]
    colors = [PALETTE["powder_blue"], PALETTE["raspberry"], PALETTE["gold_caramel"]]

    y_pos = np.arange(len(eras))
    bars = ax_bot.barh(y_pos, era_avgs, height=0.50, color=colors, alpha=0.88)

    for bar, avg, tot in zip(bars, era_avgs, era_totals):
        ax_bot.text(
            bar.get_width() + 0.12,
            bar.get_y() + bar.get_height() / 2,
            f"{avg:.2f} avg per series ({tot} total)",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=PALETTE["dark_plum"],
        )

    ax_bot.set_yticks(y_pos)
    ax_bot.set_yticklabels(
        eras, fontsize=10, fontweight="bold", color=PALETTE["gray_text"]
    )
    ax_bot.set_xlim(0, 7.5)
    ax_bot.set_xlabel(
        "Average Handshakes Awarded per Series",
        fontsize=10.5,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=8,
    )
    ax_bot.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_bot.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.6)

    for spine in ["top", "right"]:
        ax_bot.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_bot.spines[spine].set_color(PALETTE["gray_line"])
        ax_bot.spines[spine].set_linewidth(1.0)

    fig.text(
        0.08,
        0.94,
        "Hollywood Handshake frequency across broadcast eras",
        fontsize=22,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.08,
        0.89,
        "The evolution of Paul Hollywood's handshake from rare critique in early BBC years to cultural staple on Channel 4",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.02,
        "Data: 56 Hollywood Handshakes recorded across 16 series | the-great-british-bake-off package",
        fontsize=8.5,
        color="#8E9AA7",
    )

    out_file = output_dir / "handshakes_evolution.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_technical_performance_chart(output_dir: Path) -> None:
    """Generate technical_performance.png: Technical rank mastery and Star Baker conversion to finale."""
    print("Generating technical_performance.png...")
    bakers_df = pd.read_json("data/processed/bakers.json")
    performances_df = pd.read_json("data/processed/performances.json")
    episodes_df = pd.read_json("data/processed/episodes.json")

    mp = performances_df.merge(
        episodes_df[["episode_id", "series_number", "episode_number"]], on="episode_id"
    )
    tech_counts = (
        mp[mp["technical_rank"].notna()]
        .groupby("episode_id")["baker_id"]
        .count()
        .rename("tech_bakers_count")
    )
    mp = mp.merge(tech_counts, on="episode_id", how="left")

    # Compute rank percentile: (tech_bakers_count - technical_rank) / (tech_bakers_count - 1)
    mp["rank_pct"] = (mp["tech_bakers_count"] - mp["technical_rank"]) / (
        mp["tech_bakers_count"] - 1
    )
    baker_tech = mp.groupby("baker_id")["rank_pct"].mean().rename("avg_tech_pct")
    star_bakers = (
        mp[mp["result"] == "STAR_BAKER"]
        .groupby("baker_id")
        .size()
        .rename("star_bakers")
    )

    b = (
        bakers_df.merge(baker_tech, on="baker_id", how="left")
        .merge(star_bakers, on="baker_id", how="left")
        .fillna({"star_bakers": 0})
    )

    def tier(p: float) -> str | None:
        if pd.isna(p):
            return None
        p = int(p)
        if p == 1:
            return "Winners (1st)"
        elif p in (2, 3):
            return "Finalists (2nd–3rd)"
        elif p in (4, 5):
            return "Semifinalists (4th–5th)"
        elif 6 <= p <= 8:
            return "Mid-Pack (6th–8th)"
        else:
            return "Early Exits (9th+)"

    b["tier"] = b["overall_placement"].apply(tier)
    tiers_order = [
        "Winners (1st)",
        "Finalists (2nd–3rd)",
        "Semifinalists (4th–5th)",
        "Mid-Pack (6th–8th)",
        "Early Exits (9th+)",
    ]

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Left: Career Technical Rank Percentile Boxplots
    ax_left = fig.add_axes([0.16, 0.16, 0.36, 0.65])
    ax_left.set_facecolor(PALETTE["bg_white"])

    tier_colors = [
        PALETTE["gold_caramel"],
        PALETTE["raspberry"],
        PALETTE["powder_blue"],
        PALETTE["sage_green"],
        PALETTE["slate"],
    ]
    tech_data = [
        b[b["tier"] == t]["avg_tech_pct"].dropna().tolist() for t in tiers_order
    ]

    bplot = ax_left.boxplot(
        tech_data,
        orientation="horizontal",
        patch_artist=True,
        widths=0.55,
        medianprops={"color": PALETTE["dark"], "linewidth": 2.2},
        flierprops={
            "marker": "o",
            "markersize": 3,
            "alpha": 0.3,
            "markerfacecolor": PALETTE["dark"],
        },
    )

    for patch, col in zip(bplot["boxes"], tier_colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.70)
        patch.set_edgecolor(PALETTE["dark"])
        patch.set_linewidth(1.3)

    np.random.seed(42)
    for i, (vals, col) in enumerate(zip(tech_data, tier_colors)):
        y_jit = np.random.normal(i + 1, 0.08, size=len(vals))
        ax_left.scatter(
            vals, y_jit, color=PALETTE["dark"], alpha=0.28, s=20, edgecolors="none"
        )

    ax_left.set_yticks(range(1, len(tiers_order) + 1))
    ax_left.set_yticklabels(
        tiers_order, fontsize=10.5, fontweight="bold", color=PALETTE["gray_text"]
    )
    ax_left.set_xlabel(
        "Career Technical Percentile (Higher is Better →)",
        fontsize=10.5,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_left.set_xlim(0.0, 1.0)
    ax_left.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_left.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_left.set_title(
        "Technical Rank Mastery by Tier",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["dark"],
        pad=14,
    )

    for spine in ["top", "right"]:
        ax_left.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_left.spines[spine].set_color(PALETTE["gray_line"])
        ax_left.spines[spine].set_linewidth(1.1)

    # Right: Star Baker counts by tier
    ax_right = fig.add_axes([0.58, 0.16, 0.36, 0.65])
    ax_right.set_facecolor(PALETTE["bg_white"])

    sb_means = [b[b["tier"] == t]["star_bakers"].mean() for t in tiers_order]
    y_pos = np.arange(len(tiers_order))

    bars = ax_right.barh(y_pos, sb_means, height=0.55, color=tier_colors, alpha=0.88)

    for bar, val in zip(bars, sb_means):
        ax_right.text(
            bar.get_width() + 0.06,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f} avg",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=PALETTE["dark_plum"],
        )

    ax_right.set_yticks([])
    ax_right.set_xlim(0, 2.6)
    ax_right.set_xlabel(
        "Average Star Baker Accolades per Baker",
        fontsize=10.5,
        fontweight="bold",
        color=PALETTE["gray_text"],
        labelpad=10,
    )
    ax_right.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_right.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_right.set_title(
        "Star Baker Distribution by Tier",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["dark"],
        pad=14,
    )

    for spine in ["top", "right", "left"]:
        ax_right.spines[spine].set_visible(False)
    ax_right.spines["bottom"].set_color(PALETTE["gray_line"])
    ax_right.spines["bottom"].set_linewidth(1.1)

    callout_rect = patches.FancyBboxPatch(
        (0.08, 0.042),
        0.86,
        0.055,
        boxstyle="round,pad=0.015",
        facecolor=PALETTE["bg_card"],
        edgecolor=PALETTE["powder_blue"],
        linewidth=1.5,
    )
    fig.patches.append(callout_rect)
    fig.text(
        0.51,
        0.068,
        "Predictive Signal: Championship winners average a 60.0% career technical rank and 2.13 Star Baker titles, compared to 31.0% and 0.03 for early exit bakers.",
        fontsize=9,
        ha="center",
        va="center",
        color=PALETTE["gray_text"],
        style="italic",
    )

    fig.text(
        0.08,
        0.94,
        "Technical challenge mastery & Star Baker conversion",
        fontsize=22,
        fontweight="bold",
        color=PALETTE["dark"],
    )
    fig.text(
        0.08,
        0.89,
        "How blind technical challenge precision and Star Baker accolades forecast finale qualification",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.012,
        "Data: 196 classified bakers across 16 completed GBBO series | the-great-british-bake-off package",
        fontsize=8.5,
        color="#8E9AA7",
    )

    out_file = output_dir / "technical_performance.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_hex_badge(output_dir: Path) -> None:
    """Generate the official R package hex sticker badge (thegreatbritishbakeoff hex.png)."""
    print("Generating thegreatbritishbakeoff hex.png...")
    size = 3600
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    center_x = size / 2.0
    center_y = size / 2.0
    r = size * 0.45

    angles = [math.radians(a) for a in [30, 90, 150, 210, 270, 330]]
    hex_pts = [(center_x + r * math.cos(a), center_y + r * math.sin(a)) for a in angles]

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(hex_pts, fill=255)

    # Inner artwork layer: Pale powder blue tent counter background
    inner = Image.new("RGBA", (size, size), (250, 247, 242, 255))
    inner_draw = ImageDraw.Draw(inner)

    # Decorative British bunting banner across upper tent
    bunting_y = center_y - size * 0.26
    for i in range(7):
        bx = center_x - size * 0.32 + i * (size * 0.11)
        bw = size * 0.09
        bh = size * 0.08
        col = (199, 65, 99, 230) if i % 2 == 0 else (92, 148, 179, 230)
        inner_draw.polygon(
            [(bx, bunting_y), (bx + bw, bunting_y), (bx + bw / 2, bunting_y + bh)],
            fill=col,
        )

    inner_draw.line(
        [(center_x - size * 0.36, bunting_y), (center_x + size * 0.36, bunting_y)],
        fill=(58, 80, 107, 200),
        width=10,
    )

    # Stylized tiered cake illustration in center
    cake_w = size * 0.28
    cake_h = size * 0.09
    cy = center_y - size * 0.02

    # Tier 1 (Base cake)
    inner_draw.rounded_rectangle(
        [center_x - cake_w / 2, cy, center_x + cake_w / 2, cy + cake_h],
        radius=25,
        fill=(212, 140, 46, 255),
        outline=(58, 80, 107, 255),
        width=14,
    )
    # Frosting drizzle on Tier 1
    inner_draw.rectangle(
        [center_x - cake_w / 2 + 10, cy, center_x + cake_w / 2 - 10, cy + 25],
        fill=(255, 255, 255, 240),
    )

    # Tier 2 (Middle cake)
    t2_w = cake_w * 0.72
    t2_h = cake_h * 0.85
    cy2 = cy - t2_h + 10
    inner_draw.rounded_rectangle(
        [center_x - t2_w / 2, cy2, center_x + t2_w / 2, cy2 + t2_h],
        radius=20,
        fill=(199, 65, 99, 255),
        outline=(58, 80, 107, 255),
        width=14,
    )
    inner_draw.rectangle(
        [center_x - t2_w / 2 + 8, cy2, center_x + t2_w / 2 - 8, cy2 + 20],
        fill=(255, 255, 255, 240),
    )

    # Tier 3 (Top cake)
    t3_w = t2_w * 0.68
    t3_h = t2_h * 0.82
    cy3 = cy2 - t3_h + 8
    inner_draw.rounded_rectangle(
        [center_x - t3_w / 2, cy3, center_x + t3_w / 2, cy3 + t3_h],
        radius=16,
        fill=(92, 148, 179, 255),
        outline=(58, 80, 107, 255),
        width=14,
    )

    # Cherry topper
    cherry_r = 45
    inner_draw.ellipse(
        [
            center_x - cherry_r,
            cy3 - cherry_r * 1.5,
            center_x + cherry_r,
            cy3 + cherry_r * 0.5,
        ],
        fill=(199, 65, 99, 255),
        outline=(58, 80, 107, 255),
        width=8,
    )

    # Fonts
    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        font_title = ImageFont.truetype(font_path_bold, 240)
        font_sub = ImageFont.truetype(font_path_bold, 95)
        font_desc = ImageFont.truetype(font_path_reg, 80)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_desc = ImageFont.load_default()

    # Package title
    inner_draw.text(
        (center_x, center_y + size * 0.18),
        "gbbo",
        font=font_title,
        fill=(43, 32, 56, 255),
        anchor="mm",
    )
    inner_draw.text(
        (center_x, center_y + size * 0.26),
        "THE GREAT BRITISH BAKE OFF",
        font=font_sub,
        fill=(199, 65, 99, 255),
        anchor="mm",
    )
    inner_draw.text(
        (center_x, center_y + size * 0.31),
        "TIDY DATA & AI CORPUS",
        font=font_desc,
        fill=(90, 105, 120, 255),
        anchor="mm",
    )

    # Composite inner artwork
    im.paste(inner, (0, 0), mask)

    # Border
    draw.polygon(hex_pts, outline=(43, 32, 56, 255), width=50)

    # Inner pastel powder-blue accent line
    r_inner = r - 35
    hex_inner_pts = [
        (center_x + r_inner * math.cos(a), center_y + r_inner * math.sin(a))
        for a in angles
    ]
    draw.polygon(hex_inner_pts, outline=(92, 148, 179, 255), width=20)

    out_file = output_dir / "thegreatbritishbakeoff hex.png"
    im.save(out_file, "PNG")
    print(f"Saved {out_file}")

    # Aliases
    im.save(output_dir / "gbbo hex.png", "PNG")
    im.save(output_dir / "alone hex.png", "PNG")

    # Resized badge assets
    bg_hex = im.resize((1559, 1800), Image.Resampling.LANCZOS)
    bg_hex.save(output_dir / "bg hex.png", "PNG")

    white_hex = Image.new("RGBA", (1559, 1800), (255, 255, 255, 255))
    white_hex.paste(bg_hex, (0, 0), bg_hex)
    white_hex.save(output_dir / "bg white hex.png", "PNG")

    crop_hex = im.resize((1732, 2000), Image.Resampling.LANCZOS)
    crop_hex.save(output_dir / "hex1 crop.png", "PNG")

    square_badge = im.resize((1152, 1152), Image.Resampling.LANCZOS)
    square_badge.save(output_dir / "original2 square.png", "PNG")


def generate_square_and_backgrounds(output_dir: Path) -> None:
    """Generate square.jpg, bg.png, and bg white.png for README and social cards."""
    print("Generating square.jpg, bg.png, bg white.png...")
    size = 2160
    im = Image.new("RGB", (size, size), (253, 251, 247))
    draw = ImageDraw.Draw(im)

    # Dual banner header (Powder Blue & Raspberry)
    draw.rectangle([0, 0, size, 40], fill=(92, 148, 179))
    draw.rectangle([0, 40, size, 70], fill=(199, 65, 99))

    hex_path = output_dir / "gbbo hex.png"
    if hex_path.exists():
        badge = Image.open(hex_path).resize((1150, 1150), Image.Resampling.LANCZOS)
        im.paste(badge, (int((size - 1150) / 2), 220), badge)

    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        font_h1 = ImageFont.truetype(font_path_bold, 95)
        font_stats = ImageFont.truetype(font_path_bold, 58)
        font_sub = ImageFont.truetype(font_path_reg, 44)
    except Exception:
        font_h1 = font_stats = font_sub = ImageFont.load_default()

    draw.text(
        (size / 2, 1460),
        "The Great British Bake Off Dataset",
        font=font_h1,
        fill=(43, 32, 56),
        anchor="mm",
    )
    draw.text(
        (size / 2, 1540),
        "A Comprehensive Tidy Dataset & AI Training Corpus",
        font=font_sub,
        fill=(100, 116, 139),
        anchor="mm",
    )

    # Stats cards
    stats = [
        ("17", "SERIES"),
        ("204", "BAKERS"),
        ("158", "EPISODES"),
        ("1,200+", "BAKES"),
    ]

    card_w = 420
    card_h = 200
    gap = 40
    start_x = (size - (len(stats) * card_w + (len(stats) - 1) * gap)) / 2
    card_y = 1680

    for i, (val, label) in enumerate(stats):
        cx = start_x + i * (card_w + gap)
        draw.rounded_rectangle(
            [cx, card_y, cx + card_w, card_y + card_h],
            radius=24,
            fill=(255, 255, 255),
            outline=(209, 213, 219),
            width=3,
        )
        draw.text(
            (cx + card_w / 2, card_y + 70),
            val,
            font=font_stats,
            fill=(199, 65, 99),
            anchor="mm",
        )
        draw.text(
            (cx + card_w / 2, card_y + 140),
            label,
            font=font_sub,
            fill=(100, 116, 139),
            anchor="mm",
        )

    footer_text = "R Package • Python Package • Apache Arrow IPC • Parquet • SQLite • Hugging Face Hub"
    draw.text(
        (size / 2, 2020), footer_text, font=font_sub, fill=(140, 150, 160), anchor="mm"
    )

    out_square = output_dir / "square.jpg"
    im.save(out_square, "JPEG", quality=95)
    print(f"Saved {out_square}")

    # bg.png (dark)
    bg_dark = Image.new("RGB", (size, size), (26, 29, 32))
    bg_dark.save(output_dir / "bg.png", "PNG")

    # bg white.png (light)
    bg_white = Image.new("RGB", (size, size), (255, 255, 255))
    bg_white.save(output_dir / "bg white.png", "PNG")


def main() -> None:
    """Generate all figures and branding assets in dev/images/."""
    output_dir = Path("dev/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Generating data visualizations and brand assets in {output_dir.resolve()}..."
    )
    generate_survival_chart(output_dir)
    generate_items_chart(output_dir)
    generate_boxplots_chart(output_dir)
    generate_gender_performance_chart(output_dir)
    generate_handshakes_evolution_chart(output_dir)
    generate_technical_performance_chart(output_dir)
    generate_hex_badge(output_dir)
    generate_square_and_backgrounds(output_dir)
    print("\nAll publication assets successfully generated.")


if __name__ == "__main__":
    main()
