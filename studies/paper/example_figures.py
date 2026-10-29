"""Map helpers for the example-model figures: F colours, contours, stream cells, well stars
and km axes on a FloPy grid, and the half-up rounding of the quoted-number checks.

F maps use viridis from 0 to 1 with white contours (dashed F = 0.1, solid F = 0.5); G maps use
YlOrRd. Imported by gallery_figure.py and synthetic_figures.py.
"""

import sys
from pathlib import Path

import numpy as np

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (palette)

import flopy  # noqa: E402
import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap, Normalize  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

THRESHOLDS = (0.1, 0.5)  # F contours: dashed, solid
FIELD_ROWS = (10, 16)  # 0-based [start, stop) rows of the recharge field
FIELD_COLS = (12, 18)

OKABE_ITO = mfig.OKABE_ITO
F_CMAP = plt.get_cmap("viridis")
G_CMAP = plt.get_cmap("YlOrRd")
F_CONTOUR = "white"
RIVER_COLOUR = OKABE_ITO["sky"]
STAR_COLOUR = "white"  # the well on maps


# ---------------------------------------------------------------- checks


def round_half_up(value: float, digits: int) -> float:
    """Round half up, as the notebooks print areas (1.1425 -> 1.143)."""
    scale = 10.0 ** digits
    return float(np.floor(value * scale + 0.5 + 1e-9) / scale)


# ---------------------------------------------------------------- map drawing


def model_grid(grb_file: Path):
    """Return the FloPy model grid of a binary grid file."""
    return flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False).modelgrid


def draw_values(ax, grb_file: Path, step: gs.FlowStep, values: np.ndarray, cmap, norm,
                layer: int = 0):
    """Colour every cell of one layer by a per-cell value; NaN cells stay blank."""
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(grb_file), layer=layer, ax=ax)
    gridded = np.ma.masked_invalid(gs.export.to_grid(step, values))
    return pmv.plot_array(gridded, cmap=cmap, norm=norm, edgecolor="face", linewidth=0.3)


def draw_contours(ax, grb_file: Path, step: gs.FlowStep, values: np.ndarray, levels: tuple,
                  colour: str, styles: tuple, layer: int = 0, width: float = 1.0):
    """Draw contours of a per-cell value at the given levels."""
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(grb_file), layer=layer, ax=ax)
    gridded = np.ma.masked_invalid(gs.export.to_grid(step, values))
    return pmv.contour_array(gridded, levels=list(levels), colors=colour,
                             linestyles=list(styles), linewidths=width)


def draw_f_contours(ax, grb_file: Path, step: gs.FlowStep, f: np.ndarray,
                    levels: tuple = THRESHOLDS, colour: str = F_CONTOUR, layer: int = 0):
    """Draw the F = 0.1 (dashed) and F = 0.5 (solid) contours."""
    styles = ("--", "-") if len(levels) == 2 else ("-",) * len(levels)
    return draw_contours(ax, grb_file, step, f, levels, colour, styles, layer)


def draw_cells(ax, grb_file: Path, step: gs.FlowStep, cells: np.ndarray, colour: str,
               layer: int = 0) -> None:
    """Fill the given cells with one colour."""
    values = np.full(step.n_cells, np.nan)
    values[cells] = 1.0
    draw_values(ax, grb_file, step, values, ListedColormap([colour]), Normalize(0.0, 2.0),
                layer)


def draw_well(ax, grb_file: Path, cells: np.ndarray, size: float = 70.0,
              colour: str = STAR_COLOUR) -> None:
    """Mark wells with a star."""
    xy = gs.export.cell_centres(grb_file)[np.atleast_1d(cells)]
    ax.scatter(xy[:, 0], xy[:, 1], marker="*", s=size, color=colour, edgecolor="black",
               linewidth=0.6, zorder=6)


def km_axes(ax, window: tuple | None = None, extent: float = 2000.0, step_km: float = 0.5,
            x_label: bool = True, y_label: bool = True) -> None:
    """Equal-aspect map axes in km with the given window (m) or the whole domain."""
    window = ((0.0, extent), (0.0, extent)) if window is None else window
    ax.set_xlim(*window[0])
    ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    km = FuncFormatter(lambda v, _: f"{v / 1000:g}")
    for axis, (lo, hi) in ((ax.xaxis, window[0]), (ax.yaxis, window[1])):
        ticks = np.arange(np.ceil(lo / (1000 * step_km)), np.floor(hi / (1000 * step_km)) + 1)
        axis.set_ticks(ticks * 1000 * step_km)
        axis.set_major_formatter(km)
    ax.set_xlabel("x (km)" if x_label else "")
    ax.set_ylabel("y (km)" if y_label else "")
    if not x_label:
        ax.tick_params(labelbottom=False)
    if not y_label:
        ax.tick_params(labelleft=False)
    ax.spines[["top", "right"]].set_visible(True)


# ---------------------------------------------------------------- field outline


def field_rectangle(ax, spec, rows: tuple = FIELD_ROWS, cols: tuple = FIELD_COLS) -> None:
    """Outline the field."""
    x0, y0 = cols[0] * spec.delr, spec.ly - rows[1] * spec.delc
    ax.add_patch(Rectangle((x0, y0), (cols[1] - cols[0]) * spec.delr,
                           (rows[1] - rows[0]) * spec.delc, fill=False, edgecolor="black",
                           linewidth=1.0, zorder=5))
