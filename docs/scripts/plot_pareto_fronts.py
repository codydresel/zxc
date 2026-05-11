#!/usr/bin/env python3
r"""
Generate "Pareto Fronts" academic small-multiples chart.

Four panels in a 2×2 grid, one per CPU. Each panel plots every codec on
the (compressed size, decompression speed) plane — the canonical "ZXC
identity" tradeoff. Pareto-optimal codecs are drawn with filled markers
and connected by the frontier line; dominated codecs are grayed out.

ZXC variants are always rendered in red (with the level number inline)
so the family stays visible whether on the frontier or not.

Usage:
    python3 plot_pareto_fronts.py [--output PATH] [--format webp|png|svg]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _research_data import (
    CPUS, CPU_META, DATA,
    codec_family, pareto_optimal_mask,
    apply_academic_style, style_axes,
)


USE_TEX = False

FAMILY_MARKERS = {
    "zxc":    "o",
    "lz4":    "^",
    "zstd":   "s",
    "memcpy": "*",
    "other":  "D",
}

ZXC_COLOR        = "#F02020"      # punchy red (matches the arm64 chart)
OPT_COLOR        = "#1D7AE0"      # vivid blue for non-ZXC Pareto-optimal codecs
DOMINATED_COLOR  = "#9CA3AF"      # cool gray for dominated codecs
FRONTIER_COLOR   = "#F9A826"      # warm gold for the Pareto frontier line
ZONE_COLOR       = "#FDF3D4"      # light gold tint for the champions zone


# Label offsets per codec (dx, dy in points). Tuned to avoid overlaps in the
# canonical M2 layout; close enough on the other CPUs since the layouts are
# topologically similar.
LABEL_OFFSETS = {
    "zxc -1":          ( 6,   4),
    "zxc -2":          ( 6,   4),
    "zxc -3":          ( 6,   4),
    "zxc -4":          ( 6,  -8),
    "zxc -5":          ( 6,   4),
    "zxc -6":          ( 6,   4),
    "lz4":             ( 7,  -4),
    "lz4 --fast -17":  (-8,  -12),
    "lz4hc -9":        ( 7,  -4),
    "lzav -1":         ( 7,  -4),
    "snappy":          ( 7,  -4),
    "zstd --fast -1":  ( 7,  -4),
    "zstd -1":         ( 7,  -4),
    "zlib -1":         ( 7,  -4),
}


def _panel(ax, cpu: str, xlim, ylim):
    names, xs, ys = [], [], []
    for name, (_, dec, ratio) in DATA[cpu].items():
        if name == "memcpy":
            continue
        names.append(name)
        xs.append(ratio)
        ys.append(dec)

    # Pareto direction: lower ratio better, higher decode better.
    mask = pareto_optimal_mask(xs, ys, "min", "max")

    # Plot dominated codecs first (gray, hollow).
    for i, name in enumerate(names):
        if mask[i] or codec_family(name) == "zxc":
            continue
        fam = codec_family(name)
        marker = FAMILY_MARKERS.get(fam, "D")
        ax.scatter(xs[i], ys[i],
                   s=55, marker=marker,
                   facecolor="white", edgecolor=DOMINATED_COLOR,
                   linewidth=1.0, alpha=0.85, zorder=3)
        dx, dy = LABEL_OFFSETS.get(name, (6, 4))
        ax.annotate(name, (xs[i], ys[i]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=8, color=DOMINATED_COLOR, zorder=4)

    # Pareto frontier line: connect all Pareto-optimal points, sorted by x.
    opt = [(xs[i], ys[i], names[i]) for i in range(len(names)) if mask[i]]
    opt.sort(key=lambda t: t[0])
    ax.plot([t[0] for t in opt], [t[1] for t in opt],
            color=FRONTIER_COLOR, linewidth=2.6, alpha=0.95,
            zorder=4, linestyle="-",
            solid_capstyle="round",
            label="Pareto frontier")

    # Plot Pareto-optimal non-ZXC codecs (filled dark slate).
    for i, name in enumerate(names):
        if not mask[i] or codec_family(name) == "zxc":
            continue
        fam = codec_family(name)
        marker = FAMILY_MARKERS.get(fam, "D")
        ax.scatter(xs[i], ys[i],
                   s=110, marker=marker,
                   facecolor=OPT_COLOR, edgecolor="white",
                   linewidth=1.4, zorder=6)
        dx, dy = LABEL_OFFSETS.get(name, (6, 4))
        ax.annotate(name, (xs[i], ys[i]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=9, fontweight="bold", color=OPT_COLOR, zorder=7)

    # Plot ZXC last so it always sits on top — pareto-optimal or not.
    for i, name in enumerate(names):
        if codec_family(name) != "zxc":
            continue
        size = 130 if mask[i] else 90
        ax.scatter(xs[i], ys[i],
                   s=size, marker="o",
                   facecolor=ZXC_COLOR, edgecolor="white",
                   linewidth=1.5, zorder=8)
        dx, dy = LABEL_OFFSETS.get(name, (6, 4))
        lvl = name.split()[-1]
        ax.annotate(f"zxc {lvl}", (xs[i], ys[i]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=9, fontweight="bold", color=ZXC_COLOR, zorder=9)

    # Shade the Pareto-dominated region (below + right of the frontier) in a
    # light gold tint so the "champions zone" pops without overwhelming.
    front_xs = [t[0] for t in opt]
    front_ys = [t[1] for t in opt]
    if front_xs:
        x_pts = [xlim[0]] + front_xs + [xlim[1], xlim[1], xlim[0]]
        y_pts = [front_ys[0]] + front_ys + [front_ys[-1], 0, 0]
        ax.fill(x_pts, y_pts, color=ZONE_COLOR, alpha=0.55, zorder=1)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_title(
        f"{cpu}   ({CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz)",
        fontsize=12.5, pad=10, loc="left",
    )

    style_axes(ax)


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)

    # Compute shared axis ranges so that the 4 panels are directly comparable.
    all_ratios = [r for cpu in CPUS for (_, _, r) in DATA[cpu].values()
                  if r < 100.0]
    all_decs   = [d for cpu in CPUS for (_, d, r) in DATA[cpu].values()
                  if r < 100.0]
    xlim = (min(all_ratios) - 2, max(all_ratios) + 2)
    ylim = (0, max(all_decs) * 1.08)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10.5), dpi=160,
                             sharex=True, sharey=True)

    for ax, cpu in zip(axes.flatten(), CPUS):
        _panel(ax, cpu, xlim, ylim)

    # Shared axis labels (placed on the figure edge, not per-axis, to avoid
    # repetition). Y positions set explicitly so the bold supxlabel never
    # collides with the italic footer caption.
    fig.supxlabel(
        r"Compressed size (% of original)   [Lower $\leftarrow$ Better]",
        fontsize=12, fontweight="bold", y=0.055,
    )
    fig.supylabel(
        r"Decompression speed (MB/s)   [Better $\uparrow$ Higher]",
        fontsize=12, fontweight="bold", x=0.012,
    )

    # Global legend explaining the visual encoding.
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", markersize=11,
               markerfacecolor=ZXC_COLOR, markeredgecolor="white",
               linewidth=0,
               label="ZXC family"),
        Line2D([0], [0], marker="^", markersize=10,
               markerfacecolor=OPT_COLOR, markeredgecolor="white",
               linewidth=0,
               label="Pareto-optimal competitor"),
        Line2D([0], [0], marker="^", markersize=8,
               markerfacecolor="white", markeredgecolor=DOMINATED_COLOR,
               linewidth=0,
               label="Dominated competitor"),
        Line2D([0], [0], color=FRONTIER_COLOR, linewidth=2.0, alpha=0.7,
               label="Pareto frontier"),
    ]
    leg = fig.legend(handles=handles, loc="upper center",
                     bbox_to_anchor=(0.5, 0.965),
                     ncol=4, frameon=True, fontsize=10,
                     edgecolor="#222222", facecolor="white",
                     framealpha=1.0, fancybox=False)
    leg.get_frame().set_linewidth(0.8)

    fig.suptitle(
        "Pareto Fronts — Decode speed vs Compressed size, one panel per CPU",
        fontsize=14, fontweight="bold", y=0.998,
    )

    fig.text(
        0.5, 0.015,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded  |  "
        "memcpy excluded (no compression)",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.10,
                        hspace=0.22, wspace=0.08)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-pareto-fronts-0.11.0.webp"

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
