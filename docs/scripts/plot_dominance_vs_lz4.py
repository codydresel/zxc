#!/usr/bin/env python3
r"""
Generate "ZXC vs LZ4 family — Dominance Map" hero chart for the README.

For each ZXC deployment tier, this chart shows the decompression speedup vs
the matching LZ4-family competitor on every benchmarked CPU, together with
the codec-level ratio improvement annotated per group.

Tier matchups:
    Max Speed     : zxc -1  vs  lz4 --fast -17
    Standard      : zxc -3  vs  lz4 (default)
    Max Density   : zxc -6  vs  lz4hc -9

Three stacked panels, four horizontal bars per panel (one per CPU). Bars
are colored by CPU; the LZ4 baseline appears as a vertical line at 1.00×.
Each bar is annotated with its speedup multiplier; the codec-property
ratio improvement (smaller compressed size) is shown once per tier.

Usage:
    python3 plot_dominance_vs_lz4.py [--output PATH] [--format webp|png|svg]
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


# (tier_label, zxc_codec, competitor_codec)
TIERS = [
    ("Max Speed",   "zxc -1", "lz4 --fast -17"),
    ("Standard",    "zxc -3", "lz4"),
    ("Max Density", "zxc -6", "lz4hc -9"),
]


LZ4_BASELINE_COLOR = "#F9A826"   # warm gold (matches Pareto-fronts frontier)


def _draw_tier_panel(ax, tier_label: str, zxc_name: str, comp_name: str,
                     xmax: float, is_top: bool, is_bottom: bool):
    """Render one tier panel with 4 horizontal bars (one per CPU)."""
    # Tier-invariant ratio improvement (codec property, identical across CPUs).
    ratio_zxc  = DATA["Apple M2"][zxc_name][2]
    ratio_comp = DATA["Apple M2"][comp_name][2]
    ratio_pct  = (ratio_comp - ratio_zxc) / ratio_comp * 100.0

    speedups = []
    for cpu in CPUS:
        _, zxc_dec, _ = DATA[cpu][zxc_name]
        _, comp_dec, _ = DATA[cpu][comp_name]
        speedups.append(zxc_dec / comp_dec)

    y_pos = np.arange(len(CPUS))[::-1]   # top → bottom: M2, Axion, 9B45, 7763
    bar_h = 0.62

    for i, cpu in enumerate(CPUS):
        color = CPU_META[cpu]["color"]
        speedup = speedups[i]
        # Above-baseline bars are filled solid; below-baseline get hatched to
        # honestly flag the trade-off (decode trails competitor here).
        if speedup >= 1.0:
            ax.barh(y_pos[i], speedup, bar_h,
                    color=color, edgecolor="#1A1A1A", linewidth=0.5,
                    zorder=3)
        else:
            ax.barh(y_pos[i], speedup, bar_h,
                    color=color, edgecolor="#1A1A1A", linewidth=0.5,
                    hatch="xxx", alpha=0.8, zorder=3)

        # Speedup annotation just past the bar tip.
        pad = xmax * 0.008
        sign = "Faster" if speedup >= 1.0 else "Slower"
        ax.text(speedup + pad, y_pos[i],
                f"{speedup:.2f}$\\times$  {sign}",
                ha="left", va="center",
                fontsize=11, fontweight="bold",
                color="#0a4d2a" if speedup >= 1.0 else "#8a0a0a")

    # LZ4 baseline vertical line at x = 1.0 + per-panel callout naming the
    # specific lz4 variant this tier is measured against.
    ax.axvline(1.0, color=LZ4_BASELINE_COLOR, linestyle="--", linewidth=2.0,
               alpha=0.95, zorder=2)
    ax.text(
        1.0, len(CPUS) - 0.10,
        f"{comp_name} baseline  (= 1.00×)",
        ha="center", va="bottom",
        fontsize=9.5, color=LZ4_BASELINE_COLOR,
        fontweight="bold", style="italic",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white",
                  edgecolor=LZ4_BASELINE_COLOR, linewidth=0.9),
        zorder=10,
    )

    # Y axis: CPU names with arch info.
    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        [f"{cpu}\n{CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz"
         for cpu in CPUS],
        fontsize=10,
    )

    ax.set_xlim(0, xmax)
    # Reserve a bit of top headroom in every panel for the per-panel
    # baseline callout (placed just above the topmost bar).
    ax.set_ylim(-0.55, len(CPUS) + 0.35)

    # Header inside the panel showing the matchup, raw ratios and gain.
    # Plain text (no mathtext) so we can safely embed the special characters.
    header = (
        f"{tier_label}   |   "
        f"{zxc_name} ({ratio_zxc:.2f}%)  vs  {comp_name} ({ratio_comp:.2f}%)   |   "
        f"compressed size: −{ratio_pct:.1f}% smaller"
    )
    ax.set_title(header, fontsize=12, pad=8, loc="left",
                 fontweight="bold")

    if is_bottom:
        ax.set_xlabel(
            r"Decode speedup vs LZ4 family  ($\bf{higher \rightarrow better}$)",
            fontsize=11.5,
        )
    else:
        ax.set_xticklabels([])

    # Boxed axes + x-grid only.
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)
    ax.grid(True, which="major", axis="x", linestyle="--",
            color="#8a8a8a", linewidth=0.7, alpha=0.6, zorder=0)
    ax.grid(True, which="minor", axis="x", linestyle=":",
            color="#b0b0b0", linewidth=0.5, alpha=0.4, zorder=0)
    ax.minorticks_on()
    ax.yaxis.set_tick_params(which="minor", left=False)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", which="major", direction="in",
                   length=5, colors="#222222")
    ax.tick_params(axis="x", which="minor", direction="in",
                   length=2.5, colors="#222222")
    ax.tick_params(axis="y", length=0)


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)

    # Global xmax so the 3 panels share the same scale and bars are
    # visually comparable across tiers.
    all_speedups = []
    for _, zxc_name, comp_name in TIERS:
        for cpu in CPUS:
            _, zxc_dec, _ = DATA[cpu][zxc_name]
            _, comp_dec, _ = DATA[cpu][comp_name]
            all_speedups.append(zxc_dec / comp_dec)
    xmax = max(all_speedups) * 1.18

    fig, axes = plt.subplots(3, 1, figsize=(15, 11.5), dpi=160,
                             sharex=True)
    for i, ((tier, zxc, comp), ax) in enumerate(zip(TIERS, axes)):
        _draw_tier_panel(
            ax, tier, zxc, comp,
            xmax=xmax,
            is_top=(i == 0),
            is_bottom=(i == len(TIERS) - 1),
        )

    fig.suptitle(
        "ZXC vs LZ4 family — Decode speedup and size reduction across 4 CPUs",
        fontsize=15, fontweight="bold", y=0.995,
    )

    fig.text(
        0.5, 0.012,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded   |   "
        "ZXC 0.11.0 vs lz4 1.10.0   |   "
        "Solid bars = faster than LZ4 family ; hatched bars = slower (within a few %)",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.13, right=0.985, top=0.93, bottom=0.075,
                        hspace=0.50)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-dominance-0.11.0.webp"

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
