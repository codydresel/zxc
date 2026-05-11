#!/usr/bin/env python3
r"""
Generate "Pareto Efficiency" academic chart.

For each codec, count how many (CPU × tradeoff-plane) combinations it sits
on the Pareto frontier. There are 4 CPUs and 4 planes:

  decode-vs-ratio    compress-vs-ratio
  cycles/byte-vs-ratio   decode-vs-compress

giving 16 possible "wins" per codec. The chart is a horizontal stacked-bar
chart sorted by total wins descending; each segment colors the plane on
which the codec dominated. ZXC variants are highlighted with a hatched
overlay so they stand out from the rest of the field.

Usage:
    python3 plot_pareto_efficiency.py [--output PATH] [--format webp|png|svg]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _research_data import (
    CPUS, CPU_META, DATA,
    codec_family, cycles_per_byte_decode,
    pareto_optimal_mask, apply_academic_style, style_axes,
)


USE_TEX = False


PLANES = [
    ("Decode vs Ratio",        "dec_vs_ratio",  "min", "max", "#C8302E"),
    ("Compress vs Ratio",      "cmp_vs_ratio",  "min", "max", "#1F5BA8"),
    ("Cycles/byte vs Ratio",   "cyc_vs_ratio",  "min", "min", "#0a7d2a"),
    ("Decode vs Compress",     "dec_vs_cmp",    "max", "max", "#C77B0A"),
]


def _xy_for_plane(plane_id: str, cpu: str):
    """Return aligned (codec_names, xs, ys) for a CPU on a given plane.

    memcpy is excluded — it has no compression to speak of and would dominate
    every speed-vs-ratio plane trivially.
    """
    clock = CPU_META[cpu]["clock_ghz"]
    names, xs, ys = [], [], []
    for name, (comp, dec, ratio) in DATA[cpu].items():
        if name == "memcpy":
            continue
        names.append(name)
        if plane_id == "dec_vs_ratio":
            xs.append(ratio); ys.append(dec)
        elif plane_id == "cmp_vs_ratio":
            xs.append(ratio); ys.append(comp)
        elif plane_id == "cyc_vs_ratio":
            xs.append(ratio); ys.append(cycles_per_byte_decode(dec, clock))
        elif plane_id == "dec_vs_cmp":
            xs.append(comp);  ys.append(dec)
    return names, xs, ys


def _dominance_counts():
    """Return dict {codec_name: list_per_plane_of_count_of_CPUs (0-4)}.

    Each entry is a 4-vector (one entry per plane in PLANES order),
    counting on how many CPUs the codec was Pareto-optimal on that plane.
    """
    # Build canonical codec list (every codec present on every CPU).
    codec_list = [c for c in DATA[CPUS[0]].keys() if c != "memcpy"]
    counts = {c: [0, 0, 0, 0] for c in codec_list}

    for p_idx, (_, plane_id, x_better, y_better, _) in enumerate(PLANES):
        for cpu in CPUS:
            names, xs, ys = _xy_for_plane(plane_id, cpu)
            mask = pareto_optimal_mask(xs, ys, x_better, y_better)
            for name, optimal in zip(names, mask):
                if optimal:
                    counts[name][p_idx] += 1
    return counts


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)
    counts = _dominance_counts()

    # Sort codecs by total wins descending.
    order = sorted(counts.keys(), key=lambda c: (-sum(counts[c]), c))
    totals = [sum(counts[c]) for c in order]

    fig, ax = plt.subplots(figsize=(14, 10), dpi=160)

    y_pos = np.arange(len(order))
    bar_h = 0.62
    left  = np.zeros(len(order))

    for p_idx, (label, _, _, _, color) in enumerate(PLANES):
        widths = np.array([counts[c][p_idx] for c in order], dtype=float)
        bars = ax.barh(y_pos, widths, bar_h,
                       left=left, color=color, edgecolor="#1A1A1A",
                       linewidth=0.5, zorder=3, label=label)
        # Numeric label per segment (only if width > 0).
        for i, w in enumerate(widths):
            if w > 0:
                ax.text(left[i] + w / 2, y_pos[i],
                        f"{int(w)}",
                        ha="center", va="center",
                        fontsize=9, fontweight="bold", color="white")
        left += widths

    # Hatched overlay for ZXC bars.
    for i, c in enumerate(order):
        if codec_family(c) == "zxc":
            ax.barh(y_pos[i], totals[i], bar_h,
                    left=0, facecolor="none",
                    edgecolor="#1A1A1A", linewidth=0.5,
                    hatch="///", zorder=4)

    # Total count at the far right of each bar.
    for i, t in enumerate(totals):
        ax.text(t + 0.15, y_pos[i],
                f"$\\Sigma = {t}$ / 16",
                ha="left", va="center",
                fontsize=10, fontweight="bold", color="#1a1a1a")

    # Y axis: codec names. ZXC entries in bold red.
    ax.set_yticks(y_pos)
    labels = []
    for c in order:
        if codec_family(c) == "zxc":
            labels.append(c)
        else:
            labels.append(c)
    ax.set_yticklabels(labels, fontsize=10.5)
    for tick, c in zip(ax.get_yticklabels(), order):
        if codec_family(c) == "zxc":
            tick.set_color("#C8302E")
            tick.set_fontweight("bold")

    ax.invert_yaxis()
    ax.set_xlim(0, max(totals) * 1.18 + 1)
    ax.set_xlabel(
        r"Pareto-optimal wins across CPUs $\times$ tradeoff planes   (out of 16 = 4 CPUs $\times$ 4 planes)",
        fontsize=11.5,
    )
    ax.set_title(
        r"Pareto Efficiency: how often each codec sits on the frontier",
        fontsize=13, pad=12, loc="left", fontweight="bold",
    )

    style_axes(ax)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Hatch swatch for ZXC family + plane colors.
    from matplotlib.patches import Patch
    plane_handles = [
        Patch(facecolor=color, edgecolor="#1A1A1A", linewidth=0.5, label=label)
        for label, _, _, _, color in PLANES
    ]
    zxc_handle = Patch(facecolor="white", edgecolor="#1A1A1A", linewidth=0.5,
                       hatch="///", label="ZXC family (hatched)")
    leg = ax.legend(handles=plane_handles + [zxc_handle],
                    loc="lower right", frameon=True, fontsize=10,
                    edgecolor="#222222", facecolor="white",
                    framealpha=1.0, fancybox=False, ncol=1,
                    title="Tradeoff plane (color)", title_fontsize=10)
    leg.get_frame().set_linewidth(0.8)

    fig.text(
        0.5, 0.012,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded  |  "
        "memcpy excluded (no compression)",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.13, right=0.985, top=0.93, bottom=0.075)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-pareto-efficiency-0.11.0.webp"

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
