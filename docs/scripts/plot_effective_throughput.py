#!/usr/bin/env python3
r"""
Generate "Effective Throughput vs LZ4" academic vertical-bar chart.

For each codec, plots one vertical bar per CPU showing the
ratio-normalised decode rate relative to the per-CPU lz4 baseline:

    effective(codec, cpu) = decode_MBps × 100 / ratio_pct
    score(codec, cpu)     = effective(codec, cpu) / effective(lz4, cpu)

Higher is better. The LZ4 baseline appears as a horizontal line at y = 1.00.
ZXC bars are hatched. Vivid platform palette keeps the four CPUs visually
distinct.

Usage:
    python3 plot_effective_throughput.py [--output PATH] [--format webp|png|svg]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _research_data import (
    CPUS, CPU_META, DATA,
    codec_family, apply_academic_style,
)


USE_TEX = False


# Codec order (left → right in the vertical chart, ZXC family first).
CODEC_ORDER = [
    "zxc -1", "zxc -2", "zxc -3", "zxc -4", "zxc -5", "zxc -6",
    "lz4 --fast -17", "lz4", "lz4hc -9",
    "lzav -1", "snappy",
    "zstd --fast -1", "zstd -1",
]


def _effective(codec: str, cpu: str) -> float:
    _, dec, ratio = DATA[cpu][codec]
    return dec * 100.0 / ratio


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)

    n_codecs = len(CODEC_ORDER)
    n_cpus   = len(CPUS)
    bar_w    = 0.20
    group_gap = 1.05

    # Per-CPU lz4 baselines.
    lz4_eff = {cpu: _effective("lz4", cpu) for cpu in CPUS}

    # Compute score matrix [codec, cpu].
    scores = np.zeros((n_codecs, n_cpus))
    for i, codec in enumerate(CODEC_ORDER):
        for j, cpu in enumerate(CPUS):
            scores[i, j] = _effective(codec, cpu) / lz4_eff[cpu]

    x_pos = np.arange(n_codecs) * group_gap

    fig, ax = plt.subplots(figsize=(16, 9), dpi=160)

    ymax = scores.max() * 1.18

    # LZ4 baseline horizontal line at y = 1.0.
    ax.axhline(1.0, color="#5b6470", linestyle="--", linewidth=1.1,
               alpha=0.85, zorder=2)
    ax.text(x_pos[-1] + 0.6, 1.03,
            r"LZ4 baseline ($= 1.00\,\times$)",
            fontsize=9.5, color="#5b6470", style="italic",
            ha="right", va="bottom")

    # Draw 4 bars per codec, horizontally offset per CPU.
    for j, cpu in enumerate(CPUS):
        offset = (j - (n_cpus - 1) / 2.0) * bar_w
        color  = CPU_META[cpu]["color"]
        label  = f"{cpu}  ({CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz)"

        for i, codec in enumerate(CODEC_ORDER):
            is_zxc = codec_family(codec) == "zxc"
            ax.bar(
                x_pos[i] + offset, scores[i, j], bar_w,
                color=color,
                edgecolor="#1A1A1A", linewidth=0.5,
                hatch="///" if is_zxc else None,
                zorder=3,
                label=label if i == 0 else None,
            )

    # Numeric multiplier above each bar.
    pad = ymax * 0.012
    for i in range(n_codecs):
        for j in range(n_cpus):
            offset = (j - (n_cpus - 1) / 2.0) * bar_w
            v = scores[i, j]
            is_zxc = codec_family(CODEC_ORDER[i]) == "zxc"
            ax.text(x_pos[i] + offset, v + pad,
                    f"{v:.2f}$\\times$",
                    ha="center", va="bottom",
                    fontsize=7.5,
                    fontweight="bold" if is_zxc else "normal",
                    color="#1a1a1a" if is_zxc else "#3a3a3a",
                    rotation=90)

    # X-axis: codec names. ZXC bold in red, others plain.
    ax.set_xticks(x_pos)
    ax.set_xticklabels(CODEC_ORDER, fontsize=10.5,
                       rotation=30, ha="right")
    for tick, codec in zip(ax.get_xticklabels(), CODEC_ORDER):
        if codec_family(codec) == "zxc":
            tick.set_color("#C8302E")
            tick.set_fontweight("bold")

    ax.set_ylim(0, ymax)
    ax.set_xlim(x_pos[0] - 0.7, x_pos[-1] + 0.7)

    ax.set_ylabel(
        r"Effective Throughput vs. LZ4   "
        r"(decode $\times$ 100 / ratio %)  /  LZ4 baseline   "
        r"[Higher is Better $\uparrow$]",
        fontsize=11.5,
    )

    ax.set_title(
        "Effective Throughput: Ratio-Normalised Decode vs. LZ4",
        fontsize=13.5, fontweight="bold", pad=12, loc="left",
    )

    # Custom legend: CPU colors + a hatch swatch for ZXC.
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=CPU_META[cpu]["color"], edgecolor="#1A1A1A",
              linewidth=0.5,
              label=f"{cpu}  ({CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz)")
        for cpu in CPUS
    ] + [
        Patch(facecolor="white", edgecolor="#1A1A1A",
              hatch="///", linewidth=0.5, label="ZXC 0.11.0"),
    ]
    leg = ax.legend(handles=legend_handles, loc="upper right",
                    frameon=True, fontsize=10,
                    edgecolor="#222222", facecolor="white",
                    framealpha=1.0, fancybox=False)
    leg.get_frame().set_linewidth(0.8)

    # Grid on the y-axis only (categorical x-axis).
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)
    ax.grid(True, which="major", axis="y", linestyle="--",
            color="#8a8a8a", linewidth=0.7, alpha=0.6, zorder=0)
    ax.grid(True, which="minor", axis="y", linestyle=":",
            color="#b0b0b0", linewidth=0.5, alpha=0.4, zorder=0)
    ax.minorticks_on()
    ax.xaxis.set_tick_params(which="minor", bottom=False)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", which="major", direction="in",
                   length=5, colors="#222222")
    ax.tick_params(axis="y", which="minor", direction="in",
                   length=2.5, colors="#222222")
    ax.tick_params(axis="x", length=0)

    fig.text(
        0.5, 0.015,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded   |   ZXC 0.11.0 vs lz4 1.10.0",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.075, right=0.985, top=0.93, bottom=0.16)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-effective-0.11.0.webp"

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
