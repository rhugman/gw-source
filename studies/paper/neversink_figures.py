"""Shared style, loaders and map helpers of the Neversink figures.

Imported by studies/neversink/paper_figures.py and by the Neversink study scripts (diagnostics.py,
window.py). Everything is read from existing outputs of the study (studies/neversink/output and
the USGS sparse checkout in studies/neversink/external, both git-ignored); nothing is rerun.

Map conventions and colours follow studies/neversink/figures.py: F in classes (edges 0.01, 0.1,
0.25, 0.5, 0.75, 1), the SFR reaches as a network, the priority wells by cluster, coordinates in
km from the grid origin. Fonts 7 to 8 pt; figures are saved as PNG (300 dpi) and PDF.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEVERSINK = REPO / "studies" / "neversink"
sys.path.insert(0, str(NEVERSINK))

import figures as nf  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402  (figures sets the Agg backend)
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

OUT = NEVERSINK / "output"

DOUBLE = 7.0  # in, full page width
DPI = 300
INK, MUTED, GRID, SURFACE = nf.INK, nf.MUTED, nf.GRID, nf.SURFACE
COLORS = {
    "published": INK,
    "cells": "#2a78d6",  # palette slot 1, blue
    "prt": "#eb6834",  # slot 2, orange
    "network": "#1baf7a",  # slot 3, aqua
    "pumping": "#9a9994",
}
ACTIVE_FILL = "#e9e8e4"
STREAM = "#3987e5"
MAX_SEGMENT_KM = 0.25  # longest drawn connection between SFR reaches
CLUSTERS = {  # as studies/neversink/growth_mechanisms.CLUSTERS
    "U": ("U_917", "U__55", "U___7", "U___8"),
    "SV_W": ("SV_193", "SV_227", "SV_407"),
    "SV_S": ("SV_487",),
}
WINDOW_ASPECT = 1.3  # width / height of every map panel
WINDOW_NAMES = {"U": "U", "SV north": "SV_W", "SV south": "SV_S"}  # nf.cluster_windows keys
F_EDGES = (0.01, 0.1, 0.25, 0.5, 0.75, 1.0)  # colour classes of F; below 0.01: grey
F_COLORMAP = "viridis_r"  # perceptual; light for low F, dark for high F


# ---------------------------------------------------------------- style and output


def paper_style() -> None:
    """Set the light style of studies/neversink/figures.py at journal font sizes."""
    nf._style()
    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "pdf.fonttype": 42,
            "axes.grid": False,
        }
    )


def save(fig: plt.Figure, fig_dir: Path, name: str) -> Path:
    """Save a figure as PNG (DPI) and PDF; return the PNG path."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / f"{name}.png"
    fig.savefig(path, dpi=DPI)
    fig.savefig(fig_dir / f"{name}.pdf")
    plt.close(fig)
    return path


def grid_km(i: np.ndarray, j: np.ndarray, nrow: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the cell centres (x, y) in km from the grid origin (lower-left corner)."""
    return (np.asarray(j) + 0.5) * nf.CELL_KM, (nrow - np.asarray(i) - 0.5) * nf.CELL_KM


def well_ij(wells: dict, shape: tuple) -> dict:
    """Return {well: (row, column)} from the 0-based nodes of the wells."""
    nrow, ncol = shape
    return {name: ((n % (nrow * ncol)) // ncol, n % ncol) for name, n in wells.items()}


# ---------------------------------------------------------------- streams and scale bar


def sfr_reaches(packagedata: Path) -> pd.DataFrame:
    """Return reach number and 0-based (layer, row, column) of every SFR reach."""
    table = pd.read_csv(
        packagedata,
        sep=r"\s+",
        comment="#",
        header=None,
        usecols=[0, 1, 2, 3],
        names=["rno", "k", "i", "j"],
    )
    table[["k", "i", "j"]] -= 1
    return table.set_index("rno")


def sfr_downstream(sfr_file: Path) -> list[tuple[int, int]]:
    """Return (reach, downstream reach) pairs of CONNECTIONDATA (negative = downstream)."""
    pairs, inside = [], False
    for line in sfr_file.read_text().splitlines():
        word = line.strip().upper()
        if word.startswith("BEGIN CONNECTIONDATA"):
            inside = True
        elif word.startswith("END CONNECTIONDATA"):
            break
        elif inside and word and not word.startswith("#"):
            numbers = [int(v) for v in line.split()]
            pairs += [(numbers[0], -v) for v in numbers[1:] if v < 0]
    return pairs


def stream_segments(
    reaches: pd.DataFrame, pairs: list, nrow: int, max_km: float = MAX_SEGMENT_KM
) -> np.ndarray:
    """Return line segments (n, 2, 2) in km from each reach to its downstream reach.

    Connections longer than max_km (routing between distant reaches, 4 of 12,310) are dropped.
    """
    x, y = grid_km(reaches["i"].to_numpy(), reaches["j"].to_numpy(), nrow)
    xy = pd.DataFrame({"x": x, "y": y}, index=reaches.index)
    up = xy.loc[[a for a, _ in pairs]].to_numpy()
    down = xy.loc[[b for _, b in pairs]].to_numpy()
    keep = np.hypot(*(down - up).T) <= max_km
    return np.stack([up[keep], down[keep]], axis=1)


def model_segments(model_dir: Path, nrow: int) -> np.ndarray:
    """Return the SFR reach-to-downstream-reach segments (km) of the model in model_dir."""
    return stream_segments(
        sfr_reaches(model_dir / "neversink_packagedata.dat"),
        sfr_downstream(model_dir / "neversink.sfr"),
        nrow,
    )


def scale_bar(ax: plt.Axes, x0: float, y0: float, length_km: float = 5.0) -> None:
    """Draw a black-and-white scale bar of length_km starting at (x0, y0) in km."""
    half = length_km / 2
    for k, color in enumerate((INK, SURFACE)):
        ax.add_patch(
            plt.Rectangle((x0 + k * half, y0), half, 0.35, facecolor=color, edgecolor=INK, lw=0.6)
        )
    for x, label in ((x0, "0"), (x0 + length_km, f"{length_km:g} km")):
        ax.text(x, y0 + 0.6, label, ha="center", va="bottom", fontsize=7)


# ---------------------------------------------------------------- map windows and classes


def fit_aspect(window: tuple, shape: tuple, aspect: float = WINDOW_ASPECT) -> tuple:
    """Return the window (row0, row1, col0, col1) widened about its centre to aspect."""
    r0, r1, c0, c1 = window
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if width < aspect * height:
        c0, c1 = _widen(c0, c1, int(round(aspect * height)), shape[1])
    else:
        r0, r1 = _widen(r0, r1, int(round(width / aspect)), shape[0])
    return r0, r1, c0, c1


def _widen(lo: int, hi: int, size: int, n: int) -> tuple[int, int]:
    """Return a range of size cells centred on [lo, hi], shifted to stay within 0 to n - 1."""
    lo = max((lo + hi) // 2 - size // 2, 0)
    hi = min(lo + size - 1, n - 1)
    return max(hi - size + 1, 0), hi


def ordered_windows(wells: dict, ncol: int, extent: np.ndarray) -> dict:
    """Return the cluster windows of nf.cluster_windows, renamed, ordered U, SV_W, SV_S and
    widened to a common aspect ratio so that the panels tile."""
    windows = nf.cluster_windows(wells, ncol, extent)
    named = {WINDOW_NAMES[k]: fit_aspect(v, extent.shape) for k, v in windows.items()}
    return {name: named[name] for name in CLUSTERS}


def map_windows(fields: dict, outline: np.ndarray, wells: dict) -> dict:
    """Return the cluster windows around the outline and the cells where any field is above 0.1."""
    extent = outline | np.any([np.nan_to_num(f) > 0.1 for f in fields.values()], axis=0)
    return ordered_windows(wells, outline.shape[1], extent)


def capture_fields(idomain: np.ndarray, out: Path = OUT) -> dict:
    """Return F of the uppermost active cell with streams as cells and as a stream network."""
    top = nf.top_active(idomain)
    return {
        "streams as cells": nf.top_map(np.load(out / "fractions_cells.npz")["priority"], top),
        "stream network": nf.top_map(np.load(out / "fractions_sfr_network.npz")["priority"], top),
    }


def capture_windows(idomain: np.ndarray, wells: dict, mask: np.ndarray, out: Path = OUT) -> dict:
    """Return the cluster windows around the F > 0.1 areas and the published cells."""
    return map_windows(capture_fields(idomain, out), mask, wells)


def window_extent(window: tuple, nrow: int) -> tuple:
    """Return the (x0, x1, y0, y1) extent in km of a (row0, row1, col0, col1) window."""
    r0, r1, c0, c1 = window
    x0, x1 = c0 * nf.CELL_KM, (c1 + 1) * nf.CELL_KM
    return x0, x1, (nrow - r1 - 1) * nf.CELL_KM, (nrow - r0) * nf.CELL_KM


def f_classes(
    edges: tuple = F_EDGES, colormap: str = F_COLORMAP
) -> tuple[ListedColormap, BoundaryNorm]:
    """Return a discrete colour map of F with one colour per class between edges; F below the
    first edge is grey (active fill) and inactive cells are the surface colour."""
    colors = plt.get_cmap(colormap)(np.linspace(0.0, 1.0, len(edges) - 1))
    cmap = ListedColormap(colors).with_extremes(under=ACTIVE_FILL, bad=SURFACE)
    return cmap, BoundaryNorm(edges, cmap.N)


# ---------------------------------------------------------------- loaders


def published_mask(shape: tuple, out: Path = OUT) -> np.ndarray:
    """Return the published contributing cells of the calibrated model as a (row, column) grid."""
    mp7 = np.load(out / "mp7_priority.npz")
    return nf.mp7_grid(mp7["node0"], mp7["captured"], shape)
