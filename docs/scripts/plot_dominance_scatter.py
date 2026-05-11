#!/usr/bin/env python3
r"""
Generate "ZXC vs LZ4 family — Dominance Scatter" academic chart.

Same matchups as plot_dominance_vs_lz4.py (Max Speed / Standard / Max
Density) but rendered as a 2-D scatter map:

    x-axis : decode speedup vs the matching LZ4-family competitor
    y-axis : compressed-size reduction vs the same competitor (% smaller)

LZ4 baseline sits at the origin (1.00×, 0%). The chart is split into
four quadrants by the (x=1, y=0) lines; the upper-right quadrant —
"Faster AND smaller" — is shaded green and contains every ZXC point
that strictly dominates its competitor.

Encoding:
    color  = CPU       (M2 blue / Axion green / 9B45 red / 7763 gold)
    marker = tier      (circle = Max Speed / triangle = Standard /
                         square = Max Density)

Usage:
    python3 plot_dominance_scatter.py [--output PATH] [--format webp|png|svg]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _research_data import (
    CPUS, CPU_META, DATA,
    apply_academic_style,
)


USE_TEX = False


# (tier_label, zxc_codec, competitor_codec, marker_symbol)
TIERS = [
    ("Max Speed",   "zxc -1", "lz4 --fast -17", "o"),
    ("Standard",    "zxc -3", "lz4",            "^"),
    ("Max Density", "zxc -6", "lz4hc -9",       "s"),
]


LZ4_BASELINE_COLOR = "#F9A826"
WIN_ZONE_COLOR     = "#D9F2D9"      # very light green — "better on both"
LOSE_ZONE_COLOR    = "#FCE0E0"      # very light red  — "worse on both"


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)

    # Compute all points.
    points = []   # list of dicts
    for tier_label, zxc_name, comp_name, marker in TIERS:
        ratio_zxc  = DATA["Apple M2"][zxc_name][2]
        ratio_comp = DATA["Apple M2"][comp_name][2]
        smaller_pct = (ratio_comp - ratio_zxc) / ratio_comp * 100.0
        for cpu in CPUS:
            _, zxc_dec, _ = DATA[cpu][zxc_name]
            _, comp_dec, _ = DATA[cpu][comp_name]
            speedup = zxc_dec / comp_dec
            points.append({
                "tier":     tier_label,
                "cpu":      cpu,
                "zxc":      zxc_name,
                "comp":     comp_name,
                "speedup":  speedup,
                "smaller":  smaller_pct,
                "marker":   marker,
                "color":    CPU_META[cpu]["color"],
            })

    speedups = [p["speedup"] for p in points]
    smallers = [p["smaller"] for p in points]

    xlim = (min(speedups) - 0.10, max(speedups) + 0.18)
    ylim = (-0.5, max(smallers) + 1.2)

    fig, ax = plt.subplots(figsize=(15, 10), dpi=160)

    # Quadrant shading.
    # Upper-right ("Faster AND smaller"): from (1, 0) to (xmax, ymax).
    ax.fill_between([1.0, xlim[1]], 0, ylim[1],
                    color=WIN_ZONE_COLOR, alpha=0.85, zorder=1)
    # Lower-left ("Slower AND larger"): from (xmin, ymin) to (1, 0).
    ax.fill_between([xlim[0], 1.0], ylim[0], 0,
                    color=LOSE_ZONE_COLOR, alpha=0.85, zorder=1)

    # Quadrant labels.
    ax.text(xlim[1] - 0.04, ylim[1] - 0.1,
            "Faster $\\bf{AND}$ smaller",
            ha="right", va="top",
            fontsize=12, fontweight="bold", color="#0a4d2a",
            style="italic", zorder=2)
    ax.text(xlim[0] + 0.05, ylim[1] - 0.1,
            "Slower / smaller",
            ha="left", va="top",
            fontsize=11, color="#8a6a0a", style="italic", zorder=2)
    ax.text(xlim[1] - 0.04, ylim[0] + 0.1,
            "Faster / larger",
            ha="right", va="bottom",
            fontsize=11, color="#8a6a0a", style="italic", zorder=2)

    # Axis lines for LZ4 baseline (x=1, y=0).
    ax.axvline(1.0, color=LZ4_BASELINE_COLOR, linestyle="--",
               linewidth=2.0, alpha=0.95, zorder=3)
    ax.axhline(0.0, color=LZ4_BASELINE_COLOR, linestyle="--",
               linewidth=2.0, alpha=0.95, zorder=3)

    # LZ4 origin marker.
    ax.scatter([1.0], [0.0], marker="X",
               s=320, color=LZ4_BASELINE_COLOR,
               edgecolor="#1A1A1A", linewidth=1.0, zorder=6)
    ax.annotate(
        "LZ4 family baseline\n(1.00×, 0%)",
        xy=(1.0, 0.0),
        xytext=(14, -22), textcoords="offset points",
        fontsize=10, fontweight="bold",
        color=LZ4_BASELINE_COLOR, style="italic",
        bbox=dict(boxstyle="round,pad=0.30", facecolor="white",
                  edgecolor=LZ4_BASELINE_COLOR, linewidth=0.9),
        zorder=8,
    )

    # Plot every ZXC point.
    for p in points:
        ax.scatter(
            p["speedup"], p["smaller"],
            marker=p["marker"], s=260,
            facecolor=p["color"], edgecolor="#1A1A1A",
            linewidth=1.3, alpha=0.95, zorder=5,
        )

    # Tier-line connecting the 4 CPUs within each tier (all share the same y).
    # Helps the eye see how the same ratio gain plays out across CPUs.
    for tier_label, zxc_name, comp_name, _ in TIERS:
        tier_points = [p for p in points if p["tier"] == tier_label]
        xs = sorted([p["speedup"] for p in tier_points])
        y  = tier_points[0]["smaller"]
        ax.plot(xs, [y] * len(xs),
                linestyle=":", color="#5A5A5A", linewidth=1.0,
                alpha=0.6, zorder=4)
        # Tier label at the LEFT edge of the tier's data range.
        ax.text(min(xs) - 0.06, y,
                f"{tier_label}\n($\\bf{{{zxc_name.split()[-1]}}}$ vs $\\bf{{{comp_name.split()[0]}\\,{comp_name.split()[-1] if ' ' in comp_name else ''}}}$)",
                ha="right", va="center",
                fontsize=9.5, fontweight="bold", color="#1a1a1a")

    # Annotate each point with its CPU short label.
    for p in points:
        cpu_short = p["cpu"].split()[-1]   # "M2", "Axion", "9B45", "7763"
        ax.annotate(
            cpu_short, (p["speedup"], p["smaller"]),
            xytext=(7, 6), textcoords="offset points",
            fontsize=8.5, fontweight="bold", color=p["color"], zorder=7,
        )

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    ax.set_xlabel(
        r"Decode speedup vs LZ4 family   $\bf{(higher \rightarrow better)}$",
        fontsize=12,
    )
    ax.set_ylabel(
        r"Compressed-size reduction vs LZ4 family (% smaller)   $\bf{(higher \uparrow better)}$",
        fontsize=12,
    )

    # Boxed plot with dashed grid.
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)
    ax.grid(True, which="major", linestyle="--",
            color="#8a8a8a", linewidth=0.7, alpha=0.5, zorder=0)
    ax.grid(True, which="minor", linestyle=":",
            color="#b0b0b0", linewidth=0.5, alpha=0.35, zorder=0)
    ax.minorticks_on()
    ax.set_axisbelow(False)   # gridlines drawn under shaded zones already
    ax.tick_params(axis="both", which="major", direction="in",
                   length=5, colors="#222222")
    ax.tick_params(axis="both", which="minor", direction="in",
                   length=2.5, colors="#222222")

    # Custom legend: CPU colors + tier markers.
    from matplotlib.lines import Line2D
    cpu_handles = [
        Line2D([0], [0], marker="o", color="white",
               markerfacecolor=CPU_META[cpu]["color"],
               markeredgecolor="#1A1A1A",
               markersize=11, linewidth=0,
               label=f"{cpu}  ({CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz)")
        for cpu in CPUS
    ]
    tier_handles = [
        Line2D([0], [0], marker=marker, color="white",
               markerfacecolor="#1A1A1A",
               markeredgecolor="#1A1A1A",
               markersize=11, linewidth=0,
               label=f"{tier_label}  ({zxc} vs {comp})")
        for tier_label, zxc, comp, marker in TIERS
    ]
    leg_cpu = ax.legend(handles=cpu_handles, loc="upper left",
                        bbox_to_anchor=(0.01, 0.99),
                        frameon=True, fontsize=9.5,
                        edgecolor="#222222", facecolor="white",
                        framealpha=0.95, fancybox=False,
                        title="CPU (color)", title_fontsize=10)
    leg_cpu.get_frame().set_linewidth(0.8)
    ax.add_artist(leg_cpu)
    leg_tier = ax.legend(handles=tier_handles, loc="lower right",
                         bbox_to_anchor=(0.99, 0.02),
                         frameon=True, fontsize=9.5,
                         edgecolor="#222222", facecolor="white",
                         framealpha=0.95, fancybox=False,
                         title="Tier (marker)", title_fontsize=10)
    leg_tier.get_frame().set_linewidth(0.8)

    fig.suptitle(
        "ZXC vs LZ4 family — Dominance Map across 4 CPUs",
        fontsize=15, fontweight="bold", y=0.98,
    )

    fig.text(
        0.5, 0.012,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded   |   "
        "ZXC 0.11.0 vs lz4 1.10.0   |   "
        "Upper-right quadrant = ZXC strictly dominates the LZ4-family competitor",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.075)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-dominance-scatter-0.11.0.webp"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default,
                        help=f"output path (default: {default.relative_to(repo_root)})")
    parser.add_argument("--format", choices=("webp", "png", "svg"), default=None,
                        help="override output format (otherwise inferred from extension)")
    args = parser.parse_args()

    out = args.output
    if args.format:
        out = out.with_suffix(f".{args.format}")
    plot(out)


if __name__ == "__main__":
    main()
