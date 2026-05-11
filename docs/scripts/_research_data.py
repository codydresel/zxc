"""Shared benchmark dataset for the research-style charts.

Silesia corpus (211 947 520 bytes), lzbench 2.2.1, single-threaded,
-march=native. Numbers are the rows published in the README for each CPU.

Each codec entry is a tuple: (compress_MBps, decode_MBps, ratio_pct).
Clock speeds are reported in GHz (used to convert decode MB/s into
cycles per byte).
"""

CORPUS_BYTES = 211_947_520

CPUS = ["Apple M2", "Google Axion", "EPYC 9B45", "EPYC 7763"]

CPU_META = {
    "Apple M2":     {"clock_ghz": 3.5,  "arch": "ARM64",  "color": "#3D9CF4"},
    "Google Axion": {"clock_ghz": 2.6,  "arch": "ARM64",  "color": "#67C038"},
    "EPYC 9B45":    {"clock_ghz": 2.1,  "arch": "x86_64", "color": "#E5302D"},
    "EPYC 7763":    {"clock_ghz": 2.45, "arch": "x86_64", "color": "#FFB300"},
}


DATA = {
    "Apple M2": {
        "memcpy":           (52866, 52887, 100.00),
        "zxc -1":           (876,   12530,  61.50),
        "zxc -2":           (586,   10360,  53.61),
        "zxc -3":           (253,    7049,  45.79),
        "zxc -4":           (174,    6697,  42.65),
        "zxc -5":           (102,    6267,  40.27),
        "zxc -6":           (11.8,   5620,  36.28),
        "lz4":              (813,    4783,  47.60),
        "lz4 --fast -17":   (1350,   5623,  62.15),
        "lz4hc -9":         (48.2,   4528,  36.75),
        "lzav -1":          (665,    3877,  39.94),
        "snappy":           (880,    3264,  47.85),
        "zstd --fast -1":   (724,    2538,  41.01),
        "zstd -1":          (645,    1806,  34.53),
        "zlib -1":          (150,     410,  36.45),
    },
    "Google Axion": {
        "memcpy":           (24179, 24134, 100.00),
        "zxc -1":           (868,    9067,  61.50),
        "zxc -2":           (586,    7524,  53.61),
        "zxc -3":           (238,    5297,  45.79),
        "zxc -4":           (165,    5025,  42.65),
        "zxc -5":           (96.9,   4685,  40.27),
        "zxc -6":           (11.0,   4205,  36.28),
        "lz4":              (732,    4259,  47.60),
        "lz4 --fast -17":   (1280,   4951,  62.15),
        "lz4hc -9":         (43.4,   3849,  36.75),
        "lzav -1":          (562,    2757,  39.94),
        "snappy":           (757,    2313,  47.85),
        "zstd --fast -1":   (607,    2295,  41.01),
        "zstd -1":          (525,    1645,  34.53),
        "zlib -1":          (115,     390,  36.45),
    },
    "EPYC 9B45": {
        "memcpy":           (23351, 23292, 100.00),
        "zxc -1":           (859,   10844,  61.50),
        "zxc -2":           (584,    9597,  53.61),
        "zxc -3":           (238,    5955,  45.79),
        "zxc -4":           (163,    5589,  42.65),
        "zxc -5":           (97.0,   5259,  40.27),
        "zxc -6":           (11.7,   4695,  36.28),
        "lz4":              (767,    5013,  47.60),
        "lz4 --fast -17":   (1280,   5301,  62.15),
        "lz4hc -9":         (45.0,   4841,  36.75),
        "lzav -1":          (600,    3628,  39.94),
        "snappy":           (768,    2118,  47.89),
        "zstd --fast -1":   (656,    2407,  41.01),
        "zstd -1":          (597,    1868,  34.53),
        "zlib -1":          (133,     387,  36.45),
    },
    "EPYC 7763": {
        "memcpy":           (23023, 23087, 100.00),
        "zxc -1":           (640,    7077,  61.50),
        "zxc -2":           (431,    5907,  53.61),
        "zxc -3":           (185,    3922,  45.79),
        "zxc -4":           (128,    3775,  42.65),
        "zxc -5":           (76.5,   3624,  40.27),
        "zxc -6":           (8.85,   3196,  36.28),
        "lz4":              (580,    3546,  47.60),
        "lz4 --fast -17":   (1015,   4092,  62.15),
        "lz4hc -9":         (33.8,   3401,  36.75),
        "lzav -1":          (407,    2609,  39.94),
        "snappy":           (612,    1591,  47.89),
        "zstd --fast -1":   (443,    1626,  41.01),
        "zstd -1":          (400,    1221,  34.53),
        "zlib -1":          (98.1,    328,  36.45),
    },
}


# Codec families used to color / shape the markers.
ZXC_CODECS  = {"zxc -1", "zxc -2", "zxc -3", "zxc -4", "zxc -5", "zxc -6"}
LZ4_CODECS  = {"lz4", "lz4 --fast -17", "lz4hc -9"}
ZSTD_CODECS = {"zstd -1", "zstd --fast -1"}


def codec_family(name: str) -> str:
    if name in ZXC_CODECS:
        return "zxc"
    if name in LZ4_CODECS:
        return "lz4"
    if name in ZSTD_CODECS:
        return "zstd"
    if name == "memcpy":
        return "memcpy"
    return "other"


def cycles_per_byte_decode(decode_mbps: float, clock_ghz: float) -> float:
    """Convert decode MB/s to cycles/byte at the CPU's nominal clock."""
    return clock_ghz * 1000.0 / decode_mbps


def cycles_per_byte_compress(compress_mbps: float, clock_ghz: float) -> float:
    return clock_ghz * 1000.0 / compress_mbps


def pareto_optimal_mask(xs, ys, x_better, y_better):
    """Return a boolean array marking Pareto-optimal points among ``zip(xs, ys)``.

    ``x_better`` and ``y_better`` are either ``"max"`` or ``"min"`` to
    indicate the preferred direction for each axis. A point is Pareto-optimal
    if no other point dominates it strictly on both axes.
    """
    n = len(xs)
    mask = [True] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            x_dom = (xs[j] >= xs[i]) if x_better == "max" else (xs[j] <= xs[i])
            y_dom = (ys[j] >= ys[i]) if y_better == "max" else (ys[j] <= ys[i])
            x_strict = (xs[j] >  xs[i]) if x_better == "max" else (xs[j] <  xs[i])
            y_strict = (ys[j] >  ys[i]) if y_better == "max" else (ys[j] <  ys[i])
            if x_dom and y_dom and (x_strict or y_strict):
                mask[i] = False
                break
    return mask


def apply_academic_style(use_tex: bool = False) -> None:
    """Set serif body + Computer Modern math + heavier axes."""
    import matplotlib.pyplot as plt
    rc = {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "STIXGeneral", "Times New Roman", "CMU Serif"],
        "mathtext.fontset": "cm",
        "axes.edgecolor": "#222222",
        "axes.linewidth": 0.9,
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
    }
    if use_tex:
        rc.update({
            "text.usetex": True,
            "text.latex.preamble": r"\usepackage{lmodern}\usepackage{amsmath}",
        })
    plt.rcParams.update(rc)


def style_axes(ax) -> None:
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)
    ax.grid(True, which="major", linestyle="--",
            color="#8a8a8a", linewidth=0.7, alpha=0.6, zorder=0)
    ax.grid(True, which="minor", linestyle=":",
            color="#b0b0b0", linewidth=0.5, alpha=0.4, zorder=0)
    ax.minorticks_on()
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", which="major", direction="in",
                   length=5, colors="#222222")
    ax.tick_params(axis="both", which="minor", direction="in",
                   length=2.5, colors="#222222")
