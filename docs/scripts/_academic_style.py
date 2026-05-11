"""Shared academic LaTeX-style helpers for the 0.11.0 benchmark charts."""

import matplotlib.pyplot as plt


def apply_rcparams() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "STIXGeneral", "Times New Roman"],
            "mathtext.fontset": "cm",
            "axes.edgecolor": "#222222",
            "axes.linewidth": 0.9,
        }
    )


def apply_axes_style(ax) -> None:
    """Boxed plot, dashed major + dotted minor grid, ticks inward."""
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)

    ax.grid(
        True,
        which="major",
        linestyle="--",
        color="#8a8a8a",
        linewidth=0.7,
        alpha=0.6,
        zorder=0,
    )
    ax.grid(
        True,
        which="minor",
        linestyle=":",
        color="#b0b0b0",
        linewidth=0.5,
        alpha=0.4,
        zorder=0,
    )
    ax.minorticks_on()
    ax.set_axisbelow(True)
    ax.tick_params(
        axis="both", which="major", direction="in", length=5, colors="#222222"
    )
    ax.tick_params(
        axis="both", which="minor", direction="in", length=2.5, colors="#222222"
    )


def style_legend(legend) -> None:
    legend.get_frame().set_linewidth(0.8)


# Per-platform clock rates (GHz) and color codes used by both charts.
PLATFORMS = {
    "M2": {
        "label": "Apple M2 (ARM64 @ 3.5 GHz)",
        "clock_ghz": 3.5,
        "color": "#3D9CF4",
    },
    "Axion": {
        "label": "Google Axion (ARM64 @ 2.6 GHz)",
        "clock_ghz": 2.6,
        "color": "#67C038",
    },
    "9B45": {
        "label": "AMD EPYC 9B45 (x86_64 @ 2.1 GHz)",
        "clock_ghz": 2.1,
        "color": "#E5302D",
    },
}

PLATFORM_ORDER = ["M2", "Axion", "9B45"]


# Per-codec measurements (Silesia, lzbench 2.2.1, single-threaded, -march=native).
# Decode in MB/s (decimal MB, the lzbench convention).
# Ratio in % of original size; None means "not applicable" (memcpy).
CODEC_DATA = {
    "memcpy": {"ratio": None, "decode": {"M2": 52887, "Axion": 24134, "9B45": 23292}},
    "zxc -1": {"ratio": 61.50, "decode": {"M2": 12530, "Axion": 9067, "9B45": 10844}},
    "zxc -2": {"ratio": 53.61, "decode": {"M2": 10360, "Axion": 7524, "9B45": 9597}},
    "zxc -3": {"ratio": 45.79, "decode": {"M2": 7049, "Axion": 5297, "9B45": 5955}},
    "zxc -4": {"ratio": 42.65, "decode": {"M2": 6697, "Axion": 5025, "9B45": 5589}},
    "zxc -5": {"ratio": 40.27, "decode": {"M2": 6267, "Axion": 4685, "9B45": 5259}},
    "zxc -6": {"ratio": 36.28, "decode": {"M2": 5620, "Axion": 4205, "9B45": 4695}},
    "lz4": {"ratio": 47.60, "decode": {"M2": 4783, "Axion": 4259, "9B45": 5013}},
    "lz4 --fast -17": {
        "ratio": 62.15,
        "decode": {"M2": 5623, "Axion": 4951, "9B45": 5301},
    },
    "lz4hc -9": {"ratio": 36.75, "decode": {"M2": 4528, "Axion": 3849, "9B45": 4841}},
    "lzav -1": {"ratio": 39.94, "decode": {"M2": 3877, "Axion": 2757, "9B45": 3628}},
    "zstd -1": {"ratio": 34.53, "decode": {"M2": 1806, "Axion": 1645, "9B45": 1868}},
    "zstd --fast -1": {
        "ratio": 41.01,
        "decode": {"M2": 2538, "Axion": 2295, "9B45": 2407},
    },
    "snappy": {"ratio": 47.85, "decode": {"M2": 3264, "Axion": 2313, "9B45": 2118}},
}


def is_zxc(codec: str) -> bool:
    return codec.startswith("zxc")
