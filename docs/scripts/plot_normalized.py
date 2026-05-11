#!/usr/bin/env python3
r"""
Generate "Normalized Decode vs Compressed Size" academic chart.

Two panels stacked vertically:

    Top    panel : ARM64    — Apple M2 + Google Axion
    Bottom panel : x86_64   — AMD EPYC 9B45 + AMD EPYC 7763

Both axes are normalised to **LZ4 default** of the same CPU, so the four
CPUs can be overlaid on a shared frame without bias:

    x = ratio_pct(codec) / ratio_pct(lz4)    × 100      (LZ4 default = 100)
    y = decode(codec)   / decode(lz4)                   (LZ4 default = 1.00x)

Every benchmarked codec is plotted. ZXC variants are connected by a thick
solid line; the lz4 family is connected with a dashed line; zstd with a
dotted line; lzav, snappy, zlib appear as standalone markers.

LZ4 default sits at the origin (100, 1.00x). The upper-left quadrant —
"Faster AND smaller" — is shaded green.

Usage:
    python3 plot_normalized.py [--output PATH] [--format webp|png|svg]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _research_data import (
    CPUS, CPU_META, DATA,
    codec_family, apply_academic_style, style_axes,
)


USE_TEX = False


# (codec_list, marker, linestyle) — rendered as a connected curve.
ZXC_GROUP   = (["zxc -1", "zxc -2", "zxc -3", "zxc -4", "zxc -5", "zxc -6"],
               "o", "-")
LZ4_GROUP   = (["lz4 --fast -17", "lz4", "lz4hc -9"],
               "^", "--")
ZSTD_GROUP  = (["zstd --fast -1", "zstd -1"],
               "s", ":")

# (codec, marker) — standalone codecs (no connecting line).
SINGLES = [
    ("lzav -1",  "D"),
    ("snappy",   "P"),
    ("zlib -1",  "h"),
]


WIN_ZONE_COLOR = "#D9F2D9"      # very light green — "Faster AND smaller"


def _xy_for_codec(cpu: str, codec: str):
    """Return (ratio_index, speedup) normalised to LZ4 default on this CPU."""
    _, dec, ratio = DATA[cpu][codec]
    _, lz4_dec, lz4_ratio = DATA[cpu]["lz4"]
    return (ratio / lz4_ratio * 100.0, dec / lz4_dec)


def _draw_codec_curve(ax, cpu: str, color: str, codecs, marker, linestyle,
                      base_zorder: int, label_codecs: bool = False):
    """Plot a codec family as a connected line + markers for one CPU.

    If ``label_codecs`` is True, the codec name is annotated below each
    marker (used for the lz4 family so each point is identifiable).
    """
    xs, ys = [], []
    for c in codecs:
        x, y = _xy_for_codec(cpu, c)
        xs.append(x); ys.append(y)
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    xs_s = [xs[i] for i in order]
    ys_s = [ys[i] for i in order]
    codecs_s = [codecs[i] for i in order]

    is_zxc = codec_family(codecs[0]) == "zxc"
    lw    = 2.0 if is_zxc else 1.3
    alpha = 0.95 if is_zxc else 0.75
    size  = 130 if is_zxc else 75

    ax.plot(xs_s, ys_s, color=color, linestyle=linestyle,
            linewidth=lw, alpha=alpha, zorder=base_zorder)
    ax.scatter(xs_s, ys_s, marker=marker, s=size,
               facecolor=color, edgecolor="#1A1A1A",
               linewidth=1.0 if is_zxc else 0.7,
               zorder=base_zorder + 1)

    if is_zxc:
        for c, x, y in zip(codecs_s, xs_s, ys_s):
            lvl = c.split()[-1]
            ax.annotate(lvl, (x, y),
                        xytext=(7, 5), textcoords="offset points",
                        fontsize=8, fontweight="bold",
                        color=color, zorder=base_zorder + 2)
    elif label_codecs:
        # Annotate each codec name BELOW its marker, in the codec's CPU color
        # but at small fontsize to keep the plot uncluttered.
        for c, x, y in zip(codecs_s, xs_s, ys_s):
            ax.annotate(c, (x, y),
                        xytext=(0, -13), textcoords="offset points",
                        ha="center", va="top",
                        fontsize=7.5, color=color,
                        fontweight="bold",
                        zorder=base_zorder + 2)


def _draw_panel(ax, label: str, cpus_in_panel, xlim, ylim):
    # LZ4 baseline cross-hairs (no quadrant shading per user request).
    ax.axvline(100, color="#5b6470", linestyle="--",
               linewidth=1.0, alpha=0.85, zorder=2)
    ax.axhline(1.0, color="#5b6470", linestyle="--",
               linewidth=1.0, alpha=0.85, zorder=2)

    # Each CPU's codec curves.
    for cpu in cpus_in_panel:
        color = CPU_META[cpu]["color"]
        _draw_codec_curve(ax, cpu, color, ZXC_GROUP[0],
                          ZXC_GROUP[1], ZXC_GROUP[2], base_zorder=8)
        _draw_codec_curve(ax, cpu, color, LZ4_GROUP[0],
                          LZ4_GROUP[1], LZ4_GROUP[2], base_zorder=5,
                          label_codecs=True)
        _draw_codec_curve(ax, cpu, color, ZSTD_GROUP[0],
                          ZSTD_GROUP[1], ZSTD_GROUP[2], base_zorder=4)
        for codec, marker in SINGLES:
            x, y = _xy_for_codec(cpu, codec)
            ax.scatter(x, y, marker=marker, s=70,
                       facecolor=color, edgecolor="#1A1A1A",
                       linewidth=0.7, alpha=0.75, zorder=4)

    # LZ4 default reference at (100, 1.0).
    ax.scatter([100], [1.0], marker="X",
               s=240, color="#1F2937",
               edgecolor="white", linewidth=1.2, zorder=10)
    ax.annotate(
        "LZ4 default\n(100, 1.00×)",
        xy=(100, 1.0),
        xytext=(8, -28), textcoords="offset points",
        fontsize=9.5, fontweight="bold",
        color="#1F2937", style="italic",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                  edgecolor="#1F2937", linewidth=0.8),
        zorder=11,
    )

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    ax.set_title(label, fontsize=13, fontweight="bold", pad=10, loc="left")
    style_axes(ax)


def plot(output: Path) -> None:
    apply_academic_style(USE_TEX)

    # Shared axis ranges across both panels.
    all_xs, all_ys = [], []
    for cpu in CPUS:
        for codec in DATA[cpu]:
            if codec == "memcpy":
                continue
            x, y = _xy_for_codec(cpu, codec)
            all_xs.append(x); all_ys.append(y)
    xlim = (min(all_xs) - 6, max(all_xs) + 6)
    ylim = (0, max(all_ys) * 1.12)

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(15, 13), dpi=160,
                                          sharex=True)

    _draw_panel(ax_top, "ARM64   |   Apple M2 + Google Axion",
                ["Apple M2", "Google Axion"], xlim, ylim)
    _draw_panel(ax_bot, "x86_64   |   AMD EPYC 9B45 + AMD EPYC 7763",
                ["EPYC 9B45", "EPYC 7763"], xlim, ylim)

    ax_bot.set_xlabel(
        r"Compressed size  (% of LZ4 default ;  LZ4 = 100)   "
        r"$\bf{[Lower \leftarrow Better]}$",
        fontsize=12,
    )
    fig.supylabel(
        r"Decompression speed  ($\times$ LZ4 default ;  LZ4 = 1.00$\times$)   "
        r"$\bf{[Better \uparrow Higher]}$",
        fontsize=12, x=0.015,
    )

    # Per-panel legends.
    from matplotlib.lines import Line2D

    def _make_legend(ax, cpus_in_panel):
        cpu_handles = [
            Line2D([0], [0], marker="o", color="white",
                   markerfacecolor=CPU_META[cpu]["color"],
                   markeredgecolor=CPU_META[cpu]["color"],
                   markersize=11, linewidth=0,
                   label=f"{cpu}  ({CPU_META[cpu]['arch']} @ {CPU_META[cpu]['clock_ghz']} GHz)")
            for cpu in cpus_in_panel
        ]
        codec_handles = [
            Line2D([0], [0], marker=ZXC_GROUP[1], color="#1A1A1A",
                   linestyle=ZXC_GROUP[2], linewidth=2.0,
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=10, label="ZXC family (1 → 6)"),
            Line2D([0], [0], marker=LZ4_GROUP[1], color="#1A1A1A",
                   linestyle=LZ4_GROUP[2], linewidth=1.3,
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=9, label="lz4 family (--fast / default / hc -9)"),
            Line2D([0], [0], marker=ZSTD_GROUP[1], color="#1A1A1A",
                   linestyle=ZSTD_GROUP[2], linewidth=1.3,
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=9, label="zstd"),
            Line2D([0], [0], marker="D", color="white",
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=8, linewidth=0, label="lzav -1"),
            Line2D([0], [0], marker="P", color="white",
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=9, linewidth=0, label="snappy"),
            Line2D([0], [0], marker="h", color="white",
                   markerfacecolor="#1A1A1A", markeredgecolor="#1A1A1A",
                   markersize=9, linewidth=0, label="zlib -1"),
        ]
        # CPU legend on the LEFT.
        leg1 = ax.legend(handles=cpu_handles, loc="upper left",
                         bbox_to_anchor=(0.01, 0.99),
                         frameon=True, fontsize=9.5,
                         edgecolor="#222222", facecolor="white",
                         framealpha=0.95, fancybox=False,
                         title="CPU (color)", title_fontsize=10)
        leg1.get_frame().set_linewidth(0.8)
        ax.add_artist(leg1)
        # Codec legend on the BOTTOM-RIGHT.
        leg2 = ax.legend(handles=codec_handles, loc="lower right",
                         bbox_to_anchor=(0.99, 0.02),
                         frameon=True, fontsize=9,
                         edgecolor="#222222", facecolor="white",
                         framealpha=0.95, fancybox=False,
                         title="Codec (marker / line)", title_fontsize=10)
        leg2.get_frame().set_linewidth(0.8)

    _make_legend(ax_top, ["Apple M2", "Google Axion"])
    _make_legend(ax_bot, ["EPYC 9B45", "EPYC 7763"])

    fig.suptitle(
        "ZXC vs the rest — Normalized decode speed and compressed size  (LZ4 default = origin)",
        fontsize=14, fontweight="bold", y=0.995,
    )

    fig.text(
        0.5, 0.012,
        "Silesia corpus  |  lzbench 2.2.1  |  -march=native  |  single-threaded   |   "
        "Both axes normalized to LZ4 default of the same CPU   |   "
        "Upper-left quadrant = faster AND smaller than LZ4 default",
        ha="center", fontsize=9.5, color="#3a3a3a", style="italic",
    )

    plt.subplots_adjust(left=0.07, right=0.985, top=0.94, bottom=0.06,
                        hspace=0.20)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    print(f"wrote {output}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default = repo_root / "docs" / "images" / "bench-normalized-0.11.0.webp"

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
