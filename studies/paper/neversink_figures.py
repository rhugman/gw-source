"""Paper Figure 12 and supporting-information Figs S3 and S5 to S9: the Neversink/Rondout case
study, at Groundwater sizes.

Every figure is drawn from existing outputs of the case study (studies/neversink/output, the
USGS sparse checkout in studies/neversink/external; both git-ignored); nothing is rerun. Git
worktrees do not share these untracked folders, so find_data_dir falls back to the study folder
of the main checkout when this checkout has no output folder.

- Fig. 12, one row in the U-cluster window: (a) F of the calibrated model with the published
  contributing cells outlined (as Fig. S6a), (b) the F > 0.1 area against the published cells
  (as Fig. S7a), (c) against the P > 0.5 area of the weight-losing PRT particles (as Fig. S7d),
  (d) ensemble mean F with the published probability 0.5 outlined (as Fig. S8d), and a locator
  map of the whole model with the window (in place of Fig. S5).
- Fig. S5, location map: active model area, SFR reaches as a network, the three MODPATH 7
  regions (start cells of the published runs), the published contributing cells of the
  calibrated model and the eight priority wells by cluster. Coordinates are km from the grid
  origin; the north arrow shows true north, computed from the model's EPSG:5070 grid.
- Fig. S6, F of the uppermost active cell in classes (viridis, edges 0.01, 0.1, 0.25, 0.5, 0.75,
  1) with streams as cells and as a network, the SFR reaches, the wells and the published
  contributing cells outlined; equal windows and one scale bar.
- Fig. S7, overlap maps in the windows and overlays of Fig. S6: the F > 0.1 area (gross, streams
  as cells) against the published contributing cells and against the area P > 0.5 of the
  weight-losing PRT particles released over the cell volume; three classes (in both, the other
  area only, F > 0.1 only) on the uppermost active cells.
- Fig. S8, published probability against ensemble mean F (paper-size version of
  docs/figures/neversink_probability_maps.png), in the classes, windows and overlays of Fig. S6.
- Fig. S9, median contributing area against pumping, relative to base.
- Fig. S3, growth mechanism: stream share of the wells' water against pumping, and, per
  realisation, the excess of area growth over pumping growth against the drop in stream share.

Map conventions, colours and helpers follow studies/neversink/figures.py. Categorical colours
are the first slots of the validated default palette (blue, orange, aqua) plus ink and grey,
with markers or line styles as a second encoding. Sizes: single column 3.5 in, double column
7 in; fonts 7 to 8 pt. Each figure is saved as PNG (300 dpi) and PDF. Numbers that the captions
quote are checked against docs/neversink_study.md and docs/paper/figures/README.md (DOC_*
constants) before plotting.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEVERSINK = REPO / "studies" / "neversink"
sys.path.insert(0, str(NEVERSINK))

import figures as nf  # noqa: E402
import workflow as wf  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402  (figures sets the Agg backend)
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.image import AxesImage  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

OUT = NEVERSINK / "output"
SCENARIO_DIR = OUT / "scenarios"
ENS_DIR = OUT / "ensemble"
MECH_DIR = SCENARIO_DIR / "mechanisms60"
MODEL_DIR = OUT / "optimal"
FIG_DIR = REPO / "docs" / "paper" / "figures"

SINGLE, DOUBLE = 3.5, 7.0  # Groundwater column widths (in)
DPI = 300
EPSG = 5070  # CRS of the model grid (neversink_full.yml of the source repository)
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
F_EDGES = (0.01, 0.1, 0.25, 0.5, 0.75, 1.0)  # Fig. S6 colour classes of F; below 0.01: grey
F_COLORMAP = "viridis_r"  # perceptual; light for low F, dark for high F
F6_BAR_KM = 2.0  # length of the one scale bar of Fig. S6
FIXED_QRATS = nf.QRAT_FRACTION  # baserat to maxrat and their pumping fraction f
PRT_RUN = "prt_volume_thin1"  # weight-losing particles over the cell volume (net_and_envelope)
F_ZONE, P_ZONE = 0.1, 0.5  # Fig. S7: the F > 0.1 area against the P > 0.5 area
# Fig. S7 overlap classes, codes 0 to 3: rest of the active area, in both, the other area only
# (published cells or P > 0.5), F > 0.1 only. Dark and light blue for the F > 0.1 area, orange
# for what it misses (as Fig. S2); every pair is at least 17 apart (OKLab x 100) under protan,
# deutan and tritan simulation.
OVERLAP_COLORS = (ACTIVE_FILL, "#1c5cab", COLORS["prt"], "#86b6ef")

# Values quoted in docs/neversink_study.md (Tables 5, 6, Section 7); each plotted value must
# round to these.
DOC_GROWTH = {"published": 3.60, "cells": 4.09, "network": 3.42, "pumping": 3.68, "prt": 3.62}
DOC_STREAM_SHARE = {"baserat": 0.42, "maxrat": 0.28}
DOC_EXCESS_R = 0.94
# NS Section 2 and Table 3a (envelope_prt.csv, all regions, P>0.5 against F>0.1)
DOC_OVERLAP = {
    "published": 980,
    "F > 0.1": 2139,
    "published inside F > 0.1": 711,
    "P > 0.5": 691,
    "P > 0.5 inside F > 0.1": 0.87,
}
# figures/README.md Figs S5 and S7, U window: published cells, and in both / other area only /
# F > 0.1 only against the published cells and against the P > 0.5 area
DOC_U_WINDOW = {
    "published": 688,
    "published classes": (538, 150, 1090),
    "P classes": (495, 86, 1133),
}
FIG12_WINDOW = "U"  # cluster window of Fig. 12


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


def assert_doc(value: float, doc: float, what: str) -> None:
    """Assert that a plotted value rounds to the number quoted in the study document."""
    digits = len(f"{doc}".split(".")[-1])
    assert abs(value - doc) <= 0.5 * 10.0**-digits + 1e-12, f"{what}: {value:.4f}, doc {doc}"


def grid_km(i: np.ndarray, j: np.ndarray, nrow: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the cell centres (x, y) in km from the grid origin (lower-left corner)."""
    return (np.asarray(j) + 0.5) * nf.CELL_KM, (nrow - np.asarray(i) - 0.5) * nf.CELL_KM


def well_ij(wells: dict, shape: tuple) -> dict:
    """Return {well: (row, column)} from the 0-based nodes of the wells."""
    nrow, ncol = shape
    return {name: ((n % (nrow * ncol)) // ncol, n % ncol) for name, n in wells.items()}


# ---------------------------------------------------------------- Fig. S5: location map


def read_dis_origin(dis_file: Path) -> tuple[float, float]:
    """Return XORIGIN and YORIGIN of the DIS file (m, EPSG:5070)."""
    values = {}
    for line in dis_file.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].upper() in ("XORIGIN", "YORIGIN"):
            values[parts[0].upper()] = float(parts[1])
    return values["XORIGIN"], values["YORIGIN"]


def true_north_angle(x: float, y: float, epsg: int = EPSG) -> float:
    """Return the angle (degrees, anticlockwise) of true north from grid north at (x, y)."""
    import pyproj

    to_geo = pyproj.Transformer.from_crs(epsg, 4326, always_xy=True)
    to_grid = pyproj.Transformer.from_crs(4326, epsg, always_xy=True)
    lon, lat = to_geo.transform(x, y)
    x2, y2 = to_grid.transform(lon, lat + 0.05)
    return float(np.degrees(np.arctan2(-(x2 - x), y2 - y)))


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


def region_grids(endpoints: pd.DataFrame, shape: tuple) -> dict:
    """Return {region: (row, column) grid of the start cells of its published particles}."""
    nrow, ncol = shape
    grids = {}
    for region, part in endpoints.groupby("region"):
        cell = part["node0"].to_numpy() % (nrow * ncol)
        grid = np.zeros(shape, dtype=bool)
        grid[cell // ncol, cell % ncol] = True
        grids[region] = grid
    return grids


def scale_bar(ax: plt.Axes, x0: float, y0: float, length_km: float = 5.0) -> None:
    """Draw a black-and-white scale bar of length_km starting at (x0, y0) in km."""
    half = length_km / 2
    for k, color in enumerate((INK, SURFACE)):
        ax.add_patch(
            plt.Rectangle((x0 + k * half, y0), half, 0.35, facecolor=color, edgecolor=INK, lw=0.6)
        )
    for x, label in ((x0, "0"), (x0 + length_km, f"{length_km:g} km")):
        ax.text(x, y0 + 0.6, label, ha="center", va="bottom", fontsize=7)


def north_arrow(ax: plt.Axes, x: float, y: float, angle: float, length: float = 2.5) -> None:
    """Draw an arrow to true north, rotated angle degrees anticlockwise from grid north."""
    dx = -length * np.sin(np.radians(angle))
    dy = length * np.cos(np.radians(angle))
    ax.annotate(
        "",
        xy=(x + dx, y + dy),
        xytext=(x, y),
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 0.9},
    )
    ax.text(
        x + 1.15 * dx, y + 1.15 * dy, "N", ha="center", va="bottom", fontsize=8, fontweight="bold"
    )


def label_clusters(ax: plt.Axes, wells_ij: dict, nrow: int, clusters: dict = CLUSTERS) -> None:
    """Draw the wells and one label per cluster with its number of wells."""
    offsets = {"U": (-3.2, 2.0), "SV_W": (-1.0, 2.2), "SV_S": (1.4, -1.6)}
    for name, members in clusters.items():
        ij = np.array([wells_ij[m] for m in members])
        x, y = grid_km(ij[:, 0], ij[:, 1], nrow)
        ax.plot(x, y, "o", ms=4.5, mfc=COLORS["prt"], mec=INK, mew=0.7, zorder=5)
        dx, dy = offsets.get(name, (1.2, 1.2))
        n = len(members)
        ax.annotate(
            f"{name} ({n} well{'s' if n > 1 else ''})",
            (x.mean(), y.mean()),
            xytext=(x.mean() + dx, y.mean() + dy),
            fontsize=7,
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.5},
            bbox={"boxstyle": "round,pad=0.15", "fc": SURFACE, "ec": "none"},
            zorder=6,
        )


def location_map(
    fig_dir: Path,
    idomain: np.ndarray,
    wells: dict,
    mask: np.ndarray,
    regions: dict,
    segments: np.ndarray,
    north: float,
) -> Path:
    """Fig. S5: active area, streams, MODPATH regions, published cells and the priority wells."""
    paper_style()
    nrow, ncol = idomain.shape[1:]
    extent = (0, ncol * nf.CELL_KM, 0, nrow * nf.CELL_KM)
    fig, ax = plt.subplots(figsize=(SINGLE, 4.35), constrained_layout=True)
    active = (idomain > 0).any(axis=0)
    ax.imshow(
        np.where(active, 1.0, np.nan),
        cmap=ListedColormap([ACTIVE_FILL]),
        extent=extent,
        interpolation="nearest",
    )
    ax.add_collection(LineCollection(segments, colors=STREAM, linewidths=0.45, zorder=2))
    yy, xx = np.mgrid[0:nrow, 0:ncol]
    xk, yk = grid_km(yy, xx, nrow)
    for name, grid in regions.items():
        ax.contour(xk, yk, grid, levels=[0.5], colors=MUTED, linewidths=0.7, linestyles="--")
        rows, cols = np.nonzero(grid)
        x, y = grid_km(rows.min(), cols[rows == rows.min()].min(), nrow)
        ax.text(
            x + 0.3,
            y - 0.3,
            f"{name} region",
            fontsize=7,
            color=MUTED,
            ha="left",
            va="top",
            bbox={"boxstyle": "square,pad=0.1", "fc": ACTIVE_FILL, "ec": "none"},
        )
    ax.imshow(
        np.where(mask, 1.0, np.nan),
        cmap=ListedColormap([INK]),
        extent=extent,
        interpolation="nearest",
        zorder=3,
    )
    label_clusters(ax, well_ij(wells, (nrow, ncol)), nrow)
    scale_bar(ax, 1.0, 1.0)
    north_arrow(ax, extent[1] - 2.0, extent[3] - 5.0, north)
    handles = [
        plt.Line2D([], [], color=STREAM, lw=1, label="SFR reaches"),
        plt.Line2D([], [], color=MUTED, lw=0.8, ls="--", label="MODPATH 7 regions"),
        plt.Line2D(
            [], [], ls="", marker="s", ms=4, mfc=INK, mec=INK, label="published contributing cells"
        ),
        plt.Line2D(
            [],
            [],
            ls="",
            marker="o",
            ms=4.5,
            mfc=COLORS["prt"],
            mec=INK,
            mew=0.7,
            label="priority wells",
        ),
        plt.Line2D(
            [],
            [],
            ls="",
            marker="s",
            ms=6,
            mfc=ACTIVE_FILL,
            mec=MUTED,
            mew=0.4,
            label="active model area",
        ),
    ]
    fig.legend(
        handles=handles, loc="outside lower center", ncol=2, handlelength=1.4, columnspacing=1.0
    )
    ax.set_xlim(extent[:2])
    ax.set_ylim(extent[2:])
    ax.set_aspect("equal")
    ax.set_xlabel("x from grid origin (km)")
    ax.set_ylabel("y from grid origin (km)")
    return save(fig, fig_dir, "figS5_location_map")


# ---------------------------------------------------------------- Figs S6 to S8: maps


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
    """Return the cluster windows of Fig. S2; Figs S6 to S8 enlarge them to one size."""
    return map_windows(capture_fields(idomain, out), mask, wells)


def equal_windows(windows: dict, shape: tuple) -> dict:
    """Return the windows enlarged about their centres to the size of the largest (in cells)."""
    rows = max(r1 - r0 + 1 for r0, r1, _, _ in windows.values())
    cols = max(c1 - c0 + 1 for _, _, c0, c1 in windows.values())
    return {
        name: (*_widen(r0, r1, rows, shape[0]), *_widen(c0, c1, cols, shape[1]))
        for name, (r0, r1, c0, c1) in windows.items()
    }


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


def class_panel(
    ax: plt.Axes,
    field: np.ndarray,
    outline: np.ndarray,
    wells_ij: list,
    window: tuple,
    segments: np.ndarray,
    f_map: tuple,
    title: str,
) -> AxesImage:
    """Draw one panel of Figs S6 and S8: classes, SFR reaches, outline (haloed) and wells."""
    r0, r1, c0, c1 = window
    nrow = field.shape[0]
    cmap, norm = f_map
    image = ax.imshow(
        field[r0 : r1 + 1, c0 : c1 + 1],
        cmap=cmap,
        norm=norm,
        extent=window_extent(window, nrow),
        interpolation="nearest",
    )
    yy, xx = np.mgrid[r0 : r1 + 1, c0 : c1 + 1]
    xk, yk = grid_km(yy, xx, nrow)
    outline_set = ax.contour(
        xk, yk, outline[r0 : r1 + 1, c0 : c1 + 1], levels=[0.5], colors=INK, linewidths=0.7
    )
    outline_set.set(path_effects=[patheffects.withStroke(linewidth=1.8, foreground=SURFACE)])
    outline_set.set_zorder(3)
    frame_panel(ax, window, nrow, wells_ij, segments, title)
    return image


def frame_panel(
    ax: plt.Axes, window: tuple, nrow: int, wells_ij: list, segments: np.ndarray, title: str
) -> None:
    """Draw the SFR reaches and the wells of a map panel (Figs S6 to S8) and fit it to window."""
    r0, r1, c0, c1 = window
    extent = window_extent(window, nrow)
    ax.add_collection(LineCollection(segments, colors=STREAM, linewidths=0.5, zorder=2))
    ij = np.array([(i, j) for i, j in wells_ij if r0 <= i <= r1 and c0 <= j <= c1])
    x, y = grid_km(ij[:, 0], ij[:, 1], nrow)
    ax.plot(x, y, "o", ms=4, mfc=COLORS["prt"], mec=INK, mew=0.7, zorder=5)
    ax.set_xlim(extent[:2])
    ax.set_ylim(extent[2:])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, loc="left")


def class_legend(fig: plt.Figure, outline_label: str) -> None:
    """Draw the legend of Figs S6 and S8 below the panels."""
    handles = [
        plt.Line2D(
            [], [], ls="", marker="o", ms=4, mfc=COLORS["prt"], mec=INK, mew=0.7, label="wells"
        ),
        plt.Line2D([], [], color=STREAM, lw=1, label="SFR reaches"),
        plt.Line2D([], [], color=INK, lw=0.8, label=outline_label),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=3, handlelength=1.6)


def class_maps(
    fields: dict,
    outline: np.ndarray,
    wells: dict,
    windows: dict,
    segments: np.ndarray,
    height: float,
    bar_label: str,
    outline_label: str,
    bar_km: float = F6_BAR_KM,
) -> plt.Figure:
    """Return a figure of class maps (Figs S6 and S8): one row per field, one column per cluster,
    equal windows, one scale bar in the first panel."""
    nrow, ncol = outline.shape
    wells_ij = list(well_ij(wells, (nrow, ncol)).values())
    windows = equal_windows(windows, (nrow, ncol))
    f_map = f_classes()
    fig, axes = plt.subplots(
        len(fields), len(windows), figsize=(DOUBLE, height), constrained_layout=True, squeeze=False
    )
    letters = iter("abcdefghijkl")
    for row, (label, field) in enumerate(fields.items()):
        for col, (name, window) in enumerate(windows.items()):
            title = f"({next(letters)}) {name}: {label}"
            image = class_panel(
                axes[row, col], field, outline, wells_ij, window, segments, f_map, title
            )
    x0, _, y0, _ = window_extent(windows[next(iter(windows))], nrow)
    scale_bar(axes[0, 0], x0 + 0.4, y0 + 0.4, bar_km)
    bar = fig.colorbar(
        image, ax=axes, shrink=0.75, aspect=25, extend="min", ticks=F_EDGES, spacing="uniform"
    )
    bar.set_label(bar_label)
    bar.ax.set_yticklabels([f"{edge:g}" for edge in F_EDGES])
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=7)
    class_legend(fig, outline_label)
    return fig


def capture_maps(
    fig_dir: Path,
    idomain: np.ndarray,
    wells: dict,
    mask: np.ndarray,
    windows: dict,
    segments: np.ndarray,
    out: Path = OUT,
) -> Path:
    """Fig. S6: F of the uppermost active cell in classes, streams as cells and as a network."""
    paper_style()
    fig = class_maps(
        capture_fields(idomain, out),
        mask,
        wells,
        windows,
        segments,
        3.9,
        "F, uppermost active cell (grey: below 0.01)",
        "published contributing cells (outline)",
    )
    return save(fig, fig_dir, "figS6_capture_maps")


# ---------------------------------------------------------------- Fig. S7: overlap maps

OVERLAP_ROWS = {"published": "published cells", "P": "particles, P > 0.5"}  # row titles
OVERLAP_LABELS = (  # codes 0 to 3, as OVERLAP_COLORS
    "rest of the active area",
    "in both",
    "published only (a–c), particles only (d–f)",
    "F > 0.1 only",
)


def overlap_zones(
    idomain: np.ndarray,
    mask: np.ndarray,
    out: Path = OUT,
    prt_run: str = PRT_RUN,
    f_zone: float = F_ZONE,
    p_zone: float = P_ZONE,
) -> dict:
    """Return the F > f_zone area (gross, streams as cells), the published cells and the
    P > p_zone area of the weight-losing particles as (row, column) grids of the uppermost
    active cells; cells without particles have P = 0."""
    top = nf.top_active(idomain)
    f = nf.top_map(np.load(out / "fractions_cells.npz")["priority"], top)
    p = nf.top_map(np.load(out / prt_run / "cell_capture_fraction.npy").astype(float), top)
    return {"F": np.nan_to_num(f) > f_zone, "published": mask, "P": np.nan_to_num(p) > p_zone}


def check_overlap(
    zones: dict,
    out: Path = OUT,
    f_zone: float = F_ZONE,
    p_zone: float = P_ZONE,
    doc: dict = DOC_OVERLAP,
) -> None:
    """Assert the cell counts of the zones against envelope_prt.csv and the quoted values."""
    env = pd.read_csv(out / "envelope_prt.csv").set_index(["region", "prt_zone", "f_zone"])
    row = env.loc[("all", f"P>{p_zone:g}", f"F>{f_zone:g}")]
    in_f, published, in_p = zones["F"], zones["published"], zones["P"]
    assert published.sum() == doc["published"], "published cells"
    assert in_f.sum() == row["f_cells"] == doc["F > 0.1"], "F > 0.1 cells"
    assert np.sum(published & in_f) == doc["published inside F > 0.1"], "published in F > 0.1"
    assert in_p.sum() == row["prt_cells"] == doc["P > 0.5"], "P > 0.5 cells"
    assert np.sum(in_p & ~in_f) == row["missed_cells"], "P > 0.5 cells outside F > 0.1"
    coverage = np.sum(in_p & in_f) / in_p.sum()
    assert np.isclose(coverage, row["coverage"], rtol=1e-12), "coverage"
    assert_doc(coverage, doc["P > 0.5 inside F > 0.1"], "P > 0.5 inside F > 0.1")


def overlap_codes(f_zone: np.ndarray, other: np.ndarray, active: np.ndarray) -> np.ndarray:
    """Return a code per (row, column): 0 rest of the active area, 1 in both areas, 2 in other
    only, 3 in f_zone only; NaN where no layer is active."""
    code = np.select([f_zone & other, other, f_zone], [1, 2, 3], 0)
    return np.where(active, code, np.nan)


def overlap_legend(
    fig: plt.Figure, colors: tuple = OVERLAP_COLORS, labels: tuple = OVERLAP_LABELS
) -> None:
    """Draw the legend of Fig. S7 below the panels: the classes, the wells and the SFR reaches."""
    handles = [Patch(facecolor=colors[k], edgecolor="none", label=labels[k]) for k in (1, 3, 2, 0)]
    handles += [
        plt.Line2D(
            [], [], ls="", marker="o", ms=4, mfc=COLORS["prt"], mec=INK, mew=0.7, label="wells"
        ),
        plt.Line2D([], [], color=STREAM, lw=1, label="SFR reaches"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=3, handlelength=1.6)


def overlap_maps(
    fig_dir: Path,
    idomain: np.ndarray,
    wells: dict,
    mask: np.ndarray,
    windows: dict,
    segments: np.ndarray,
    out: Path = OUT,
    rows: dict = OVERLAP_ROWS,
    bar_km: float = F6_BAR_KM,
) -> Path:
    """Fig. S7: the F > 0.1 area against (a-c) the published cells and (d-f) the P > 0.5 area of
    the weight-losing particles, in the windows of Fig. S6."""
    paper_style()
    zones = overlap_zones(idomain, mask, out)
    check_overlap(zones, out)
    active = nf.top_active(idomain) >= 0
    nrow, ncol = mask.shape
    wells_ij = list(well_ij(wells, (nrow, ncol)).values())
    windows = equal_windows(windows, (nrow, ncol))
    fig, axes = plt.subplots(2, len(windows), figsize=(DOUBLE, 4.05), constrained_layout=True)
    letters = iter("abcdef")
    for row, (key, label) in enumerate(rows.items()):
        codes = overlap_codes(zones["F"], zones[key], active)
        for col, (name, window) in enumerate(windows.items()):
            title = f"({next(letters)}) {name}: {label}"
            overlap_panel(axes[row, col], codes, window, wells_ij, segments, title)
    x0, _, y0, _ = window_extent(windows[next(iter(windows))], nrow)
    scale_bar(axes[0, 0], x0 + 0.4, y0 + 0.4, bar_km)
    overlap_legend(fig)
    return save(fig, fig_dir, "figS7_overlap_maps")


def probability_maps(
    fig_dir: Path,
    idomain: np.ndarray,
    wells: dict,
    windows: dict,
    segments: np.ndarray,
    maps_file: Path = ENS_DIR / "probability_maps.npz",
) -> Path:
    """Fig. S8: published probability against ensemble mean F, base pumping, in the classes and
    windows of Fig. S6."""
    paper_style()
    maps = np.load(maps_file)
    active = nf.top_active(idomain) >= 0
    fields = {
        "published probability": maps["mp7"],
        "mean F, cells": maps["cells:mean_F"],
        "mean F, network": maps["network:mean_F"],
    }
    fields = {label: np.where(active, field, np.nan) for label, field in fields.items()}
    fig = class_maps(
        fields,
        maps["mp7"] > 0.5,
        wells,
        windows,
        segments,
        5.6,
        "probability or mean F (grey: below 0.01)",
        "published probability 0.5 (outline)",
    )
    return save(fig, fig_dir, "figS8_probability_maps")


# ---------------------------------------------------------------- Fig. 12: one row, U window

FIG12_TITLES = (
    "(a) F",
    "(b) F > 0.1, published cells",
    "(c) F > 0.1, particles P > 0.5",
    "(d) ensemble mean F",
)
FIG12_OVERLAP_LABELS = (  # codes 0 to 3, as OVERLAP_COLORS
    "rest of the active area",
    "in both",
    "published only (b),\nparticles only (c)",
    "F > 0.1 only",
)


def window_counts(codes: np.ndarray, window: tuple) -> tuple[int, int, int]:
    """Return the cells in both areas, in the other area only and in F > 0.1 only in window."""
    r0, r1, c0, c1 = window
    part = codes[r0 : r1 + 1, c0 : c1 + 1]
    return tuple(int(np.sum(part == code)) for code in (1, 2, 3))


def row_maps(idomain: np.ndarray, mask: np.ndarray, out: Path, maps_file: Path) -> dict:
    """Return the fields, outlines and overlap codes of the four panels of Fig. 12."""
    zones = overlap_zones(idomain, mask, out)
    check_overlap(zones, out)
    active = nf.top_active(idomain) >= 0
    maps = np.load(maps_file)
    return {
        "F": capture_fields(idomain, out)["streams as cells"],
        "mean F": np.where(active, maps["cells:mean_F"], np.nan),
        "published": mask,
        "probability 0.5": maps["mp7"] > 0.5,
        "codes published": overlap_codes(zones["F"], zones["published"], active),
        "codes P": overlap_codes(zones["F"], zones["P"], active),
    }


def check_window(maps: dict, window: tuple, doc: dict = DOC_U_WINDOW) -> None:
    """Assert the published cells and the overlap classes in window against the quoted counts."""
    r0, r1, c0, c1 = window
    published = int(maps["published"][r0 : r1 + 1, c0 : c1 + 1].sum())
    assert published == doc["published"], f"published cells in window: {published}"
    for key in ("published", "P"):
        counts = window_counts(maps[f"codes {key}"], window)
        assert counts == doc[f"{key} classes"], f"classes against {key}: {counts}"


def overlap_panel(
    ax: plt.Axes,
    codes: np.ndarray,
    window: tuple,
    wells_ij: list,
    segments: np.ndarray,
    title: str,
    colors: tuple = OVERLAP_COLORS,
) -> None:
    """Draw one overlap map (Figs 12 and S7): the classes, SFR reaches and wells in window."""
    r0, r1, c0, c1 = window
    nrow = codes.shape[0]
    ax.imshow(
        codes[r0 : r1 + 1, c0 : c1 + 1],
        cmap=ListedColormap(colors).with_extremes(bad=SURFACE),
        vmin=-0.5,
        vmax=len(colors) - 0.5,
        extent=window_extent(window, nrow),
        interpolation="nearest",
    )
    frame_panel(ax, window, nrow, wells_ij, segments, title)


def locator_panel(
    ax: plt.Axes,
    idomain: np.ndarray,
    regions: dict,
    wells_ij: list,
    segments: np.ndarray,
    window: tuple,
) -> None:
    """Draw the locator map of Fig. 12: active area, SFR reaches, MODPATH 7 regions, wells and
    the window."""
    nrow, ncol = idomain.shape[1:]
    extent = (0, ncol * nf.CELL_KM, 0, nrow * nf.CELL_KM)
    active = (idomain > 0).any(axis=0)
    ax.imshow(
        np.where(active, 1.0, np.nan),
        cmap=ListedColormap([ACTIVE_FILL]),
        extent=extent,
        interpolation="nearest",
    )
    ax.add_collection(LineCollection(segments, colors=STREAM, linewidths=0.25, zorder=2))
    yy, xx = np.mgrid[0:nrow, 0:ncol]
    xk, yk = grid_km(yy, xx, nrow)
    for grid in regions.values():
        ax.contour(xk, yk, grid, levels=[0.5], colors=MUTED, linewidths=0.5, linestyles="--")
    ij = np.array(wells_ij)
    x, y = grid_km(ij[:, 0], ij[:, 1], nrow)
    ax.plot(x, y, "o", ms=2.2, mfc=COLORS["prt"], mec=INK, mew=0.4, zorder=5)
    x0, x1, y0, y1 = window_extent(window, nrow)
    ax.add_patch(
        plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=INK, lw=0.9, zorder=6)
    )
    ax.set_xlim(extent[:2])
    ax.set_ylim(extent[2:])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("inset: whole model", fontsize=7, labelpad=2)


def row_key(ax: plt.Axes, image: AxesImage, edges: tuple = F_EDGES) -> None:
    """Draw the horizontal colour bar of panels (a) and (d) in the upper part of ax."""
    ax.axis("off")
    cax = ax.inset_axes([0.04, 0.5, 0.92, 0.15])
    bar = plt.colorbar(
        image, cax=cax, orientation="horizontal", extend="min", ticks=edges, spacing="uniform"
    )
    bar.ax.set_xticklabels([f"{edge:g}" for edge in edges])
    bar.outline.set_visible(False)
    bar.ax.tick_params(labelsize=7)
    bar.ax.set_title("F (a), mean F (d); grey: below 0.01", fontsize=7, loc="left")


def row_legend(
    ax: plt.Axes, colors: tuple = OVERLAP_COLORS, labels: tuple = FIG12_OVERLAP_LABELS
) -> None:
    """Draw the legend of Fig. 12: the overlap classes of (b, c), then wells, SFR reaches,
    outlines and regions."""
    ax.axis("off")
    handles = [Patch(facecolor=colors[k], edgecolor="none", label=labels[k]) for k in (1, 3, 2, 0)]
    handles += [
        plt.Line2D(
            [], [], ls="", marker="o", ms=4, mfc=COLORS["prt"], mec=INK, mew=0.7, label="wells"
        ),
        plt.Line2D([], [], color=STREAM, lw=1, label="SFR reaches"),
        plt.Line2D(
            [], [], color=INK, lw=0.8, label="outline: published cells (a),\nprobability 0.5 (d)"
        ),
        plt.Line2D([], [], color=MUTED, lw=0.8, ls="--", label="MODPATH 7 regions (inset)"),
    ]
    ax.legend(
        handles=handles, loc="center", ncol=2, handlelength=1.6, frameon=False, columnspacing=1.2
    )


def neversink_row(
    fig_dir: Path,
    idomain: np.ndarray,
    wells: dict,
    maps: dict,
    window: tuple,
    segments: np.ndarray,
    regions: dict,
    titles: tuple = FIG12_TITLES,
    bar_km: float = F6_BAR_KM,
) -> Path:
    """Fig. 12: (a) F with the published cells, (b, c) the F > 0.1 area against the published
    cells and the P > 0.5 area, (d) ensemble mean F, in one window, and a locator map."""
    paper_style()
    nrow, ncol = idomain.shape[1:]
    wells_ij = list(well_ij(wells, (nrow, ncol)).values())
    f_map = f_classes()
    fig = plt.figure(figsize=(DOUBLE, 2.65), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(1.0, 0.62))
    axes = top.subplots(1, 4)
    image = class_panel(
        axes[0], maps["F"], maps["published"], wells_ij, window, segments, f_map, titles[0]
    )
    overlap_panel(axes[1], maps["codes published"], window, wells_ij, segments, titles[1])
    overlap_panel(axes[2], maps["codes P"], window, wells_ij, segments, titles[2])
    class_panel(
        axes[3],
        maps["mean F"],
        maps["probability 0.5"],
        wells_ij,
        window,
        segments,
        f_map,
        titles[3],
    )
    x0, _, y0, _ = window_extent(window, nrow)
    scale_bar(axes[0], x0 + 0.4, y0 + 0.4, bar_km)
    ax_key, ax_legend, ax_loc = bottom.subplots(1, 3, width_ratios=(1.25, 2.2, 0.9))
    row_key(ax_key, image)
    row_legend(ax_legend)
    locator_panel(ax_loc, idomain, regions, wells_ij, segments, window)
    return save(fig, fig_dir, "fig12_neversink")


# ---------------------------------------------------------------- Fig. S9: area growth


def growth_table(scenario_dir: Path = SCENARIO_DIR, mech_dir: Path = MECH_DIR) -> pd.DataFrame:
    """Return the area growth (growth of the medians) per pumping fraction f and series.

    published, cells, network and pumping from area_table.csv (357 or 358 realisations); prt is
    R1, PRT with the published conventions, from growth_decomposition.csv (61 realisations).
    """
    area = pd.read_csv(scenario_dir / "area_table.csv").set_index("qrat").loc[list(FIXED_QRATS)]
    table = pd.DataFrame(
        {
            "f": list(FIXED_QRATS.values()),
            "published": area["published_cells_growth"].to_numpy(),
            "cells": area["cells_expected_growth"].to_numpy(),
            "network": area["network_expected_growth"].to_numpy(),
            "pumping": area["inflow_growth"].to_numpy(),
        },
        index=list(FIXED_QRATS),
    )
    mech = pd.read_csv(mech_dir / "growth_decomposition.csv")
    r1 = mech[mech["variant"] == "r1"].set_index("qrat")["growth_of_medians"]
    table["prt"] = r1.reindex(table.index)
    table.loc["baserat", "prt"] = 1.0
    for key, doc in DOC_GROWTH.items():
        assert_doc(table.loc["maxrat", key], doc, f"growth {key}")
    return table


GROWTH_LABELS = {
    "published": "published MODPATH 7 (357 areas)",
    "prt": "PRT, published conventions (61)",
    "cells": "full mixing, streams as cells",
    "network": "full mixing, stream network",
    "pumping": "pumping of the priority wells",
}
GROWTH_MARKERS = {"cells": "o", "pumping": None, "prt": "D", "published": "s", "network": "^"}
LABEL_GAP = 0.15  # least spacing of the end labels (ratio units)


def spread_labels(values: pd.Series, gap: float = LABEL_GAP) -> pd.Series:
    """Return label heights near values, moved apart symmetrically to at least gap."""
    order = values.sort_values()
    heights = order.to_numpy().astype(float)
    for _ in range(50):
        moved = False
        for k in range(1, len(heights)):
            overlap = gap - (heights[k] - heights[k - 1])
            if overlap > 1e-9:
                heights[k - 1] -= overlap / 2
                heights[k] += overlap / 2
                moved = True
        if not moved:
            break
    return pd.Series(heights, index=order.index)


def growth_chart(fig_dir: Path, table: pd.DataFrame) -> Path:
    """Fig. S9: median contributing area relative to base pumping, with the pumping ratio dashed.

    The value at maximum pumping is written at the right, behind the series' own marker.
    """
    paper_style()
    fig, ax = plt.subplots(figsize=(SINGLE, 2.9), constrained_layout=True)
    ax.grid(True, color=GRID, lw=0.5)
    for key, mk in GROWTH_MARKERS.items():
        part = table[["f", key]].dropna()
        style = (
            {"ls": "--", "lw": 1.1}
            if mk is None
            else {"marker": mk, "ms": 4, "lw": 1.3, "mec": SURFACE, "mew": 0.6}
        )
        ax.plot(part["f"], part[key], color=COLORS[key], label=GROWTH_LABELS[key], **style)
    heights = spread_labels(table.loc["maxrat", list(GROWTH_MARKERS)])
    for key, y in heights.items():
        mk = GROWTH_MARKERS[key]
        if mk is None:
            ax.plot([1.04, 1.08], [y, y], ls="--", lw=1.1, color=COLORS[key])
        else:
            ax.plot(1.06, y, mk, ms=4, color=COLORS[key], mec=SURFACE, mew=0.6)
        ax.text(1.1, y, f"{table.loc['maxrat', key]:.2f}", va="center", fontsize=7)
    ax.set_xlim(-0.03, 1.27)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("pumping fraction f (0 = base, 1 = maximum)")
    ax.set_ylabel("median contributing area / base")
    ax.legend(loc="upper left", handlelength=2.2)
    return save(fig, fig_dir, "figS9_area_growth")


# ---------------------------------------------------------------- Fig. S3: growth mechanism


def realisation_summary(
    qrat: str, ens_dir: Path = ENS_DIR, scenario_dir: Path = SCENARIO_DIR
) -> pd.DataFrame:
    """Return per realisation the inflow, stream share and area (streams as cells) of a scenario."""
    folder = ens_dir if qrat == "baserat" else scenario_dir / qrat
    rows = [json.loads(p.read_text()) for p in sorted((folder / "summary").glob("*.json"))]
    table = pd.DataFrame(rows)
    table["real"] = table["real"].astype(str)
    table["stream_share"] = table["cells:SFR_0"] / table["inflow"]
    return table.set_index("real")[["inflow", "stream_share", "cells:expected_cells"]]


def share_bands(summaries: dict) -> pd.DataFrame:
    """Return per scenario the median and the 5 and 95 % quantiles of the stream share."""
    rows = []
    for qrat, table in summaries.items():
        share = table["stream_share"]
        rows.append(
            {
                "qrat": qrat,
                "f": FIXED_QRATS[qrat],
                "n": len(share),
                "median": share.median(),
                "q05": share.quantile(0.05),
                "q95": share.quantile(0.95),
            }
        )
    bands = pd.DataFrame(rows).set_index("qrat")
    for qrat, doc in DOC_STREAM_SHARE.items():
        assert_doc(bands.loc[qrat, "median"], doc, f"stream share {qrat}")
    return bands


def excess_table(base: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    """Return per realisation the stream-share drop and the area growth over pumping growth."""
    reals = top.index.intersection(base.index)
    table = pd.DataFrame(
        {
            "share_drop": base.loc[reals, "stream_share"] - top.loc[reals, "stream_share"],
            "area_growth": top.loc[reals, "cells:expected_cells"]
            / base.loc[reals, "cells:expected_cells"],
            "pumping_growth": top.loc[reals, "inflow"] / base.loc[reals, "inflow"],
        }
    )
    table["excess"] = table["area_growth"] - table["pumping_growth"]
    r = np.corrcoef(table["share_drop"], table["excess"])[0, 1]
    assert_doc(r, DOC_EXCESS_R, "r(excess, stream-share drop)")
    return table


def mechanism_chart(fig_dir: Path, bands: pd.DataFrame, excess: pd.DataFrame) -> Path:
    """Fig. S3: (a) stream share against pumping; (b) area-growth excess against share drop."""
    paper_style()
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(DOUBLE, 2.7), constrained_layout=True)
    blue = COLORS["cells"]
    ax_a.fill_between(
        bands["f"],
        100 * bands["q05"],
        100 * bands["q95"],
        color=blue,
        alpha=0.18,
        lw=0,
        label="5 to 95 % of realisations",
    )
    ax_a.plot(
        bands["f"],
        100 * bands["median"],
        marker="o",
        ms=4,
        lw=1.3,
        color=blue,
        mec=SURFACE,
        mew=0.6,
        label="median",
    )
    for qrat in ("baserat", "maxrat"):
        ax_a.annotate(
            f"{100 * bands.loc[qrat, 'median']:.0f} %",
            (bands.loc[qrat, "f"], 100 * bands.loc[qrat, "median"]),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            fontsize=7,
        )
    ax_a.set_xlabel("pumping fraction f (0 = base, 1 = maximum)")
    ax_a.set_ylabel("stream leakage in the wells' water (%)")
    ax_a.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_a.set_ylim(15, 50)
    ax_a.legend(loc="upper right")
    ax_a.set_title("(a) stream share, streams as cells", loc="left")
    x, y = 100 * excess["share_drop"], excess["excess"]
    slope, intercept = np.polyfit(x, y, 1)
    xs = np.array([x.min(), x.max()])
    ax_b.plot(x, y, "o", ms=3, color=blue, alpha=0.55, mec="none")
    ax_b.plot(xs, intercept + slope * xs, color=INK, lw=0.9)
    r = np.corrcoef(x, y)[0, 1]
    ax_b.text(
        0.04, 0.95, f"r = {r:.2f}, n = {len(x)}", transform=ax_b.transAxes, va="top", fontsize=7
    )
    ax_b.axhline(0, color=COLORS["pumping"], lw=0.8, ls="--")
    ax_b.set_xlabel("drop in stream share (percentage points)")
    ax_b.set_ylabel("area growth - pumping growth")
    ax_b.set_title("(b) per realisation, base to maximum pumping", loc="left")
    for ax in (ax_a, ax_b):
        ax.grid(True, color=GRID, lw=0.5)
    return save(fig, fig_dir, "figS3_growth_mechanism")


# ---------------------------------------------------------------- main


def find_data_dir(neversink: Path = NEVERSINK, repo: Path = REPO) -> Path:
    """Return the study folder that holds output/: this checkout's, else the main checkout's."""
    if (neversink / "output").is_dir():
        return neversink
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    main_dir = Path(common).parent / neversink.relative_to(repo)
    assert (main_dir / "output").is_dir(), f"no output folder in {neversink} or {main_dir}"
    return main_dir


def published_mask(shape: tuple, out: Path = OUT) -> np.ndarray:
    """Return the published contributing cells of the calibrated model as a (row, column) grid."""
    mp7 = np.load(out / "mp7_priority.npz")
    return nf.mp7_grid(mp7["node0"], mp7["captured"], shape)


def main(
    fig12: bool = True,
    figS5: bool = False,
    figS6: bool = False,
    figS7: bool = False,
    figS8: bool = False,
    figS9: bool = False,
    figS3: bool = False,
    fig_dir: Path = FIG_DIR,
    data_dir: Path | None = None,
) -> list[Path]:
    """Make the selected figures in fig_dir from the study folder data_dir (default:
    find_data_dir); return the PNG paths."""
    data_dir = find_data_dir() if data_dir is None else data_dir
    out = data_dir / "output"
    model_dir = out / "optimal"
    ens_dir = out / "ensemble"
    scenario_dir = out / "scenarios"
    mp_dir = (
        data_dir / "external" / "neversink_workflow" / "output" / "neversink_mp7_optimal_output"
    )
    paths = []
    idomain = wf.grid_idomain(model_dir)
    shape = idomain.shape[1:]
    wells = wf.PRIORITY_WELLS
    maps_needed = fig12 or figS5 or figS6 or figS7 or figS8
    if maps_needed:
        mask = published_mask(shape, out)
        windows = capture_windows(idomain, wells, mask, out)
        segments = model_segments(model_dir, shape[0])
    if fig12 or figS5:
        regions = region_grids(wf.read_endpoints(mp_dir, columns=("node0",)), shape)
    if fig12:
        window = equal_windows(windows, shape)[FIG12_WINDOW]
        maps = row_maps(idomain, mask, out, ens_dir / "probability_maps.npz")
        check_window(maps, window)
        paths.append(neversink_row(fig_dir, idomain, wells, maps, window, segments, regions))
    if figS5:
        x0, y0 = read_dis_origin(model_dir / "neversink.dis")
        north = true_north_angle(x0 + shape[1] * 25.0, y0 + shape[0] * 25.0)
        paths.append(location_map(fig_dir, idomain, wells, mask, regions, segments, north))
    if figS6:
        paths.append(capture_maps(fig_dir, idomain, wells, mask, windows, segments, out))
    if figS7:
        paths.append(overlap_maps(fig_dir, idomain, wells, mask, windows, segments, out))
    if figS8:
        maps_file = ens_dir / "probability_maps.npz"
        paths.append(probability_maps(fig_dir, idomain, wells, windows, segments, maps_file))
    if figS9:
        paths.append(
            growth_chart(fig_dir, growth_table(scenario_dir, scenario_dir / "mechanisms60"))
        )
    if figS3:
        summaries = {q: realisation_summary(q, ens_dir, scenario_dir) for q in FIXED_QRATS}
        excess = excess_table(summaries["baserat"], summaries["maxrat"])
        paths.append(mechanism_chart(fig_dir, share_bands(summaries), excess))
    return paths


if __name__ == "__main__":
    t0 = time.perf_counter()
    for p in main():
        print(p)
    print(f"{time.perf_counter() - t0:.1f} s")
