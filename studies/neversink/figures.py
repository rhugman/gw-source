"""Figures (PNG, light theme) of the Neversink stage-1 comparison.

Maps show the backward fraction F of the uppermost active cell to the eight priority wells on a
single-hue blue ramp (0 to 1), the published MODPATH 7 contributing cells as an ink outline and
the wells as white-ringed ink dots. Colours and style follow studies/dispersion/figures.py.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SURFACE = "#fcfcfb"
BLUES = LinearSegmentedColormap.from_list(
    "blues", [SURFACE, "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)
CELL_KM = 0.05
PAD = 25  # cells around the window of each cluster


def _style() -> None:
    """Set a light, recessive matplotlib style."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
        "ytick.color": MUTED, "text.color": INK, "axes.grid": False, "font.size": 9,
        "axes.titlesize": 9.5, "legend.frameon": False,
    })


def top_active(idomain: np.ndarray) -> np.ndarray:
    """Return, per (row, column), the 0-based node of the uppermost active cell, or -1."""
    nlay, nrow, ncol = idomain.shape
    active = idomain > 0
    k = np.argmax(active, axis=0)
    node = k * nrow * ncol + np.arange(nrow * ncol).reshape(nrow, ncol)
    return np.where(active.any(axis=0), node, -1)


def top_map(values: np.ndarray, top: np.ndarray) -> np.ndarray:
    """Return a per-cell array on the uppermost active layer (NaN where none is active)."""
    return np.where(top >= 0, values[np.maximum(top, 0)], np.nan)


def mp7_grid(node0: np.ndarray, captured: np.ndarray, shape: tuple) -> np.ndarray:
    """Return the published contributing cells as a (row, column) boolean grid."""
    nrow, ncol = shape
    grid = np.zeros(shape, dtype=bool)
    cell = node0[captured] % (nrow * ncol)
    grid[cell // ncol, cell % ncol] = True
    return grid


def cluster_windows(wells: dict, ncol: int, mask: np.ndarray, pad: int = PAD) -> dict:
    """Return {cluster: (row0, row1, col0, col1)} around the wells and the mask cells near them."""
    clusters = {"SV north": ["SV_193", "SV_227", "SV_407"], "SV south": ["SV_487"],
                "U": ["U_917", "U__55", "U___7", "U___8"]}
    rows, cols = np.nonzero(mask)
    windows = {}
    for name, members in clusters.items():
        cells = [(wells[m] % (mask.size)) for m in members]
        wi = np.array([c // ncol for c in cells])
        wj = np.array([c % ncol for c in cells])
        near = (np.abs(rows[:, None] - wi).min(axis=1) < 120) & (
            np.abs(cols[:, None] - wj).min(axis=1) < 120
        )
        r = np.concatenate([wi, rows[near]])
        c = np.concatenate([wj, cols[near]])
        nrow = mask.shape[0]
        windows[name] = (
            max(r.min() - pad, 0), min(r.max() + pad, nrow - 1),
            max(c.min() - pad, 0), min(c.max() + pad, ncol - 1),
        )
    return windows


def _panel(ax, field, mask, wells_ij, window, title):
    """Draw one zoomed F map with the MODPATH outline and the wells (y up from the grid origin)."""
    r0, r1, c0, c1 = window
    nrow = field.shape[0]
    extent = (c0 * CELL_KM, (c1 + 1) * CELL_KM, (nrow - r1 - 1) * CELL_KM, (nrow - r0) * CELL_KM)
    image = ax.imshow(field[r0 : r1 + 1, c0 : c1 + 1], cmap=BLUES, vmin=0, vmax=1,
                      extent=extent, interpolation="nearest")
    yy, xx = np.mgrid[r0 : r1 + 1, c0 : c1 + 1]
    ax.contour((xx + 0.5) * CELL_KM, (nrow - yy - 0.5) * CELL_KM, mask[r0 : r1 + 1, c0 : c1 + 1],
               levels=[0.5], colors=INK, linewidths=0.9)
    for i, j in wells_ij:
        if r0 <= i <= r1 and c0 <= j <= c1:
            ax.plot((j + 0.5) * CELL_KM, (nrow - i - 0.5) * CELL_KM, "o", ms=5, mfc=INK,
                    mec=SURFACE, mew=1.2)
    ax.set_title(title, loc="left")
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7.5)
    return image


def capture_maps(out: Path, fig_dir: Path, idomain: np.ndarray, wells: dict) -> Path:
    """Map F (cells only, and with SFR reaches as nodes) against the MODPATH 7 cells."""
    _style()
    shape = idomain.shape[1:]
    top = top_active(idomain)
    mp7 = np.load(out / "mp7_priority.npz")
    mask = mp7_grid(mp7["node0"], mp7["captured"], shape)
    fields = {
        "stream as cells": top_map(np.load(out / "fractions_cells.npz")["priority"], top),
        "stream as network": top_map(np.load(out / "fractions_sfr_network.npz")["priority"], top),
    }
    ncol = shape[1]
    wells_ij = [((n % mask.size) // ncol, n % ncol) for n in wells.values()]
    extent = mask | np.any([np.nan_to_num(f) > 0.1 for f in fields.values()], axis=0)
    windows = cluster_windows(wells, ncol, extent)
    fig, axes = plt.subplots(2, len(windows), figsize=(10, 6.6), constrained_layout=True)
    for row, (label, field) in enumerate(fields.items()):
        for col, (name, window) in enumerate(windows.items()):
            image = _panel(axes[row, col], field, mask, wells_ij, window, f"{name} wells, {label}")
    for ax in axes[-1]:
        ax.set_xlabel("x from grid origin [km]")
    for ax in axes[:, 0]:
        ax.set_ylabel("y from grid origin [km]")
    bar = fig.colorbar(image, ax=axes, shrink=0.6, label="F, uppermost active cell")
    bar.outline.set_visible(False)
    fig.suptitle("Backward fraction F to the eight priority wells; outline: published MODPATH 7 "
                 "contributing cells", x=0.01, ha="left", fontsize=10)
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / "neversink_capture_maps.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def jaccard_table(out: Path) -> pd.DataFrame:
    """Return the agreement of each method with the published MODPATH 7 cells (priority)."""
    mp7 = pd.read_csv(out / "mp7_comparison.csv").set_index("group").loc["priority"]
    rows = [
        {"method": "full mixing, F > 0.1", "jaccard": mp7["jaccard_F>0.1"]},
        {"method": "full mixing, F > 0.5", "jaccard": mp7["jaccard_F>0.5"]},
        {"method": "full mixing, area-matched", "jaccard": mp7["jaccard_area_matched"]},
    ]
    prt = pd.read_csv(out / "prt_comparison.csv")
    for _, r in prt.iterrows():
        thin = "thinned" if r["thin_weak_sinks"] else "plain"
        rows.append({"method": f"PRT {r['release']}, {thin}, P > 0.5",
                     "jaccard": r["jaccard_mp7_prt>0.5"]})
    return pd.DataFrame(rows)


SERIES = {"published": "#0b0b0b", "cells": "#2a78d6", "network": "#1baf7a", "pumping": "#9a9994"}
SERIES_LABELS = {
    "published": "published MODPATH 7 (all masks)",
    "cells": "full mixing, streams as cells",
    "network": "full mixing, stream network",
    "pumping": "pumping of the priority wells",
}
QRAT_FRACTION = {"baserat": 0.0, "0.25rat": 0.25, "0.5rat": 0.5, "0.75rat": 0.75, "maxrat": 1.0}


def probability_maps(maps: dict, fig_dir: Path, idomain: np.ndarray, wells: dict) -> Path:
    """Map the published probability against gwsource's ensemble mean F (base pumping)."""
    _style()
    shape = idomain.shape[1:]
    ncol = shape[1]
    fields = {
        "published probability": maps["mp7"],
        "mean F, streams as cells": maps["cells:mean_F"],
        "mean F, stream network": maps["network:mean_F"],
    }
    outline = maps["mp7"] > 0.5
    wells_ij = [((n % outline.size) // ncol, n % ncol) for n in wells.values()]
    extent = np.any([f > 0.1 for f in fields.values()], axis=0)
    windows = cluster_windows(wells, ncol, extent)
    fig, axes = plt.subplots(len(fields), len(windows), figsize=(10, 9.6), constrained_layout=True)
    for row, (label, field) in enumerate(fields.items()):
        for col, (name, window) in enumerate(windows.items()):
            image = _panel(axes[row, col], field, outline, wells_ij, window, f"{name} wells: {label}")
    for ax in axes[-1]:
        ax.set_xlabel("x from grid origin [km]")
    for ax in axes[:, 0]:
        ax.set_ylabel("y from grid origin [km]")
    bar = fig.colorbar(image, ax=axes, shrink=0.5, label="probability or mean F")
    bar.outline.set_visible(False)
    fig.suptitle("Base pumping, 357 published masks and 358 realisations; outline: published "
                 "probability 0.5", x=0.01, ha="left", fontsize=10)
    path = fig_dir / "neversink_probability_maps.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def area_growth(table: pd.DataFrame, fig_dir: Path) -> Path:
    """Plot the median contributing area against the pumping scenario, relative to base."""
    _style()
    plt.rcParams.update({"axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6})
    fixed = table[table["qrat"].isin(QRAT_FRACTION)].copy()
    fixed["f"] = fixed["qrat"].map(QRAT_FRACTION)
    fixed = fixed.sort_values("f")
    columns = {
        "published": "published_cells_growth",
        "cells": "cells_expected_growth",
        "network": "network_expected_growth",
        "pumping": "inflow_growth",
    }
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    for key, col in columns.items():
        style = {"ls": "--", "lw": 1.5} if key == "pumping" else {"lw": 2, "marker": "o", "ms": 6}
        ax.plot(fixed["f"], fixed[col], color=SERIES[key], label=SERIES_LABELS[key], **style)
        if key != "pumping":  # the reference line is read off the legend
            ax.annotate(f"{fixed[col].iloc[-1]:.2f}", (1.0, fixed[col].iloc[-1]), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK)
    ax.set_xlabel("pumping scenario f  (q = q_base + f (q_max - q_base))")
    ax.set_ylabel("median contributing area / base")
    ax.set_xlim(-0.03, 1.12)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title("Contributing area of the eight priority wells against pumping", loc="left")
    path = fig_dir / "neversink_area_growth.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
