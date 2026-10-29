"""Neversink/Rondout figures: F maps with the published contributing area, and the ensemble
mean F.

neversink_maps, four map panels: (a) the whole model with the three cluster windows, (b) to (d)
the windows of cluster U, the north SV wells and the south SV well. Each shows F of the
uppermost active cell of the calibrated model (gross accounting, stream reaches as cells;
viridis classes, grey below 0.01), the F = 0.1 and F = 0.5 contours and the published MODPATH 7
area.

neversink_ensemble, the three cluster windows: mean F over the realisations of the ensemble
(stream reaches as cells) with the cells of published probability of contribution 0.5 or more
outlined (the published masks moved back onto their cells, ensemble_run.read_mask).

Reads stored outputs only, from studies/neversink/output (run workflow.py, and pest_rebuild.py
plus ensemble_run.py for the ensemble figure); nothing is rerun. Writes to output/paper/ in the
repository root (git-ignored).

    PYTHONPATH=src:studies/paper python studies/neversink/paper_figures.py
"""

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "studies" / "paper"))

import neversink_figures as nvf  # noqa: E402
import workflow as wf  # noqa: E402  (on the path through neversink_figures)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

OUT_DIR = REPO / "output" / "paper"
TEXT_WIDTH = 17.15 / 2.54  # in, full page width
F_LEVELS = (0.1, 0.5)  # contoured values of F
F_STYLES = {0.1: "--", 0.5: "-"}
F_LINE = "#ffffff"
PUBLISHED_LINE = "#eb6834"  # orange, the particle colour of the other paper figures
WINDOW_TITLES = {"U": "wells of cluster U", "SV_W": "north SV wells", "SV_S": "south SV well"}
TIGHT_PAD = 12  # cells kept around the areas in the cropped windows
CROPPED = ("SV_W", "SV_S")  # windows cropped to their areas
PUBLISHED_CELLS = 980  # published contributing cells of the calibrated model
N_REALISATIONS = 358  # realisations of the base ensemble behind the mean F
PROBABILITY = 0.5  # outlined published probability of contribution
ENSEMBLE_BAR_KM = {"U": 2.0, "SV_W": 1.0, "SV_S": 1.0}  # scale bars; 1 km labels touch in (a)


def f_colormap() -> tuple:
    """Return the viridis classes of F of the other paper figures (edges nvf.F_EDGES), with F
    below the first edge grey and inactive cells blank."""
    return nvf.f_classes(colormap="viridis")


def halo(width: float) -> list:
    """Return a dark stroke behind a line, so that light lines read on light colours."""
    return [patheffects.withStroke(linewidth=width, foreground=nvf.INK)]


def field_panel(
    ax: plt.Axes,
    f: np.ndarray,
    window: tuple,
    wells_ij: list,
    segments: np.ndarray,
    scale: float,
) -> plt.cm.ScalarMappable:
    """Draw the F classes, SFR reaches and wells inside window and fit the panel to it; scale
    sets line widths and marker sizes (1 in the cluster windows, less on the whole model)."""
    r0, r1, c0, c1 = window
    nrow = f.shape[0]
    cmap, norm = f_colormap()
    image = ax.imshow(
        f[r0 : r1 + 1, c0 : c1 + 1],
        cmap=cmap,
        norm=norm,
        extent=nvf.window_extent(window, nrow),
        interpolation="nearest",
    )
    ax.add_collection(
        LineCollection(segments, colors=nvf.STREAM, linewidths=0.4 * scale, zorder=2, alpha=0.8)
    )
    ij = np.array([(i, j) for i, j in wells_ij if r0 <= i <= r1 and c0 <= j <= c1])
    x, y = nvf.grid_km(ij[:, 0], ij[:, 1], nrow)
    ax.plot(x, y, "o", ms=3.5 * scale, mfc=nvf.SURFACE, mec=nvf.INK, mew=0.7 * scale, zorder=5)
    x0, x1, y0, y1 = aspect_limits(nvf.window_extent(window, nrow))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    return image


def window_grid(window: tuple, nrow: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the cell centres (x, y) in km of the cells of window, for contouring."""
    r0, r1, c0, c1 = window
    yy, xx = np.mgrid[r0 : r1 + 1, c0 : c1 + 1]
    return nvf.grid_km(yy, xx, nrow)


def map_panel(
    ax: plt.Axes,
    f: np.ndarray,
    published: np.ndarray,
    window: tuple,
    wells_ij: list,
    segments: np.ndarray,
    scale: float,
) -> plt.cm.ScalarMappable:
    """Draw a map panel: the F classes with their contours, the published area, SFR reaches
    and wells inside window."""
    r0, r1, c0, c1 = window
    image = field_panel(ax, f, window, wells_ij, segments, scale)
    part = f[r0 : r1 + 1, c0 : c1 + 1]
    xk, yk = window_grid(window, f.shape[0])
    for level in F_LEVELS:
        lines = ax.contour(
            xk, yk, np.nan_to_num(part), levels=[level], colors=F_LINE,
            linewidths=0.7 * scale, linestyles=F_STYLES[level],
        )
        lines.set(path_effects=halo(1.5 * scale), zorder=3)
    outline = ax.contour(
        xk, yk, published[r0 : r1 + 1, c0 : c1 + 1], levels=[0.5], colors=PUBLISHED_LINE,
        linewidths=0.9 * scale,
    )
    outline.set(path_effects=halo(1.8 * scale), zorder=4)
    return image


def aspect_limits(extent: tuple, aspect: float = nvf.WINDOW_ASPECT) -> tuple:
    """Return the (x0, x1, y0, y1) extent widened about its centre to width / height = aspect,
    so that every map panel has the same size."""
    x0, x1, y0, y1 = extent
    width, height = max(x1 - x0, aspect * (y1 - y0)), max(y1 - y0, (x1 - x0) / aspect)
    xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
    return xc - width / 2, xc + width / 2, yc - height / 2, yc + height / 2


def tight_window(
    f: np.ndarray, published: np.ndarray, window: tuple, pad: int = TIGHT_PAD
) -> tuple:
    """Return window cropped to the cells with F of at least the first class edge or in the
    published area, plus pad cells, and widened to the panel aspect ratio."""
    r0, r1, c0, c1 = window
    shown = (np.nan_to_num(f) >= nvf.F_EDGES[0]) | published
    rows, cols = np.nonzero(shown[r0 : r1 + 1, c0 : c1 + 1])
    nrow, ncol = f.shape
    cropped = (
        max(r0 + rows.min() - pad, 0),
        min(r0 + rows.max() + pad, nrow - 1),
        max(c0 + cols.min() - pad, 0),
        min(c0 + cols.max() + pad, ncol - 1),
    )
    return nvf.fit_aspect(cropped, f.shape)


def model_window(idomain: np.ndarray) -> tuple:
    """Return the (row0, row1, col0, col1) bounds of the active model area."""
    rows, cols = np.nonzero((idomain > 0).any(axis=0))
    return rows.min(), rows.max(), cols.min(), cols.max()


def legend(fig: plt.Figure, image: plt.cm.ScalarMappable) -> None:
    """Draw the colour bar of F and the line key below the panels."""
    cax = fig.add_axes((0.08, 0.075, 0.38, 0.022))
    bar = fig.colorbar(image, cax=cax, orientation="horizontal", extend="min")
    bar.set_ticks(nvf.F_EDGES, labels=[f"{edge:g}" for edge in nvf.F_EDGES])
    bar.set_label("F of the uppermost active cell (grey: below 0.01)", fontsize=7)
    bar.outline.set_linewidth(0.5)
    handles = [
        plt.Line2D([], [], color=PUBLISHED_LINE, lw=1.0, path_effects=halo(2.0),
                   label="published contributing area (particles)"),
        plt.Line2D([], [], color=F_LINE, lw=0.8, ls="-", path_effects=halo(1.8), label="F = 0.5"),
        plt.Line2D([], [], color=F_LINE, lw=0.8, ls="--", path_effects=halo(1.8), label="F = 0.1"),
        plt.Line2D([], [], color=nvf.STREAM, lw=1.0, label="SFR reaches"),
        plt.Line2D([], [], ls="", marker="o", ms=3.5, mfc=nvf.SURFACE, mec=nvf.INK, mew=0.7,
                   label="priority wells"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.53, 0.012), ncols=2,
               frameon=False, handlelength=2.2, columnspacing=1.2)


def scale_bar(ax: plt.Axes, window: tuple, nrow: int, length_km: float) -> None:
    """Draw a black-and-white scale bar in the lower left of a panel, sized to its window."""
    x0, x1, y0, y1 = nvf.window_extent(window, nrow)
    height = 0.02 * (y1 - y0)
    left, base = x0 + 0.04 * (x1 - x0), y0 + 0.04 * (y1 - y0)
    for k, color in enumerate((nvf.INK, nvf.SURFACE)):
        ax.add_patch(plt.Rectangle((left + k * length_km / 2, base), length_km / 2, height,
                                   facecolor=color, edgecolor=nvf.INK, lw=0.6, zorder=6))
    for x, label in ((left, "0"), (left + length_km, f"{length_km:g} km")):
        ax.text(x, base + 1.8 * height, label, ha="center", va="bottom", fontsize=7, zorder=6)


def window_boxes(ax: plt.Axes, windows: dict, nrow: int) -> None:
    """Outline and letter the cluster windows on the whole-model panel."""
    for letter, window in zip("bcd", windows.values()):
        x0, x1, y0, y1 = nvf.window_extent(window, nrow)
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=nvf.INK,
                                   lw=0.8, zorder=6))
        ax.text(x1 + 0.4, y1, letter, ha="left", va="top", fontsize=7, fontweight="bold",
                zorder=6)


def neversink_maps(
    fig_dir: Path, idomain: np.ndarray, f: np.ndarray, published: np.ndarray, windows: dict,
    segments: np.ndarray,
) -> Path:
    """Draw the whole model and three cluster windows in a 2 by 2 grid."""
    nvf.paper_style()
    nrow, ncol = idomain.shape[1:]
    wells_ij = list(nvf.well_ij(wf.PRIORITY_WELLS, (nrow, ncol)).values())
    fig, axes = plt.subplots(2, 2, figsize=(nvf.DOUBLE, 6.1))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.14, wspace=0.04, hspace=0.1)
    whole = model_window(idomain)
    image = map_panel(axes[0, 0], f, published, whole, wells_ij, segments, scale=0.6)
    window_boxes(axes[0, 0], windows, nrow)
    scale_bar(axes[0, 0], whole, nrow, 10.0)
    axes[0, 0].set_title("(a) whole model", loc="left")
    for ax, letter, (name, window) in zip(axes.flat[1:], "bcd", windows.items()):
        map_panel(ax, f, published, window, wells_ij, segments, scale=1.0)
        ax.set_title(f"({letter}) {WINDOW_TITLES[name]}", loc="left")
        scale_bar(ax, window, nrow, 1.0)
    legend(fig, image)
    return nvf.save(fig, fig_dir, "fig_neversink_maps")


def ensemble_panel(
    ax: plt.Axes,
    mean_f: np.ndarray,
    probable: np.ndarray,
    window: tuple,
    wells_ij: list,
    segments: np.ndarray,
) -> plt.cm.ScalarMappable:
    """Draw an ensemble panel: the mean F classes, the outline of the cells of high published
    probability (black, white halo), SFR reaches and wells inside window."""
    r0, r1, c0, c1 = window
    image = field_panel(ax, mean_f, window, wells_ij, segments, scale=1.0)
    xk, yk = window_grid(window, mean_f.shape[0])
    outline = ax.contour(
        xk, yk, probable[r0 : r1 + 1, c0 : c1 + 1], levels=[0.5], colors=nvf.INK, linewidths=0.9
    )
    outline.set(path_effects=[patheffects.withStroke(linewidth=2.0, foreground=nvf.SURFACE)],
                zorder=4)
    return image


def ensemble_legend(fig: plt.Figure, image: plt.cm.ScalarMappable) -> None:
    """Draw the colour bar of mean F and the line key of the ensemble figure below the panels."""
    cax = fig.add_axes((0.06, 0.15, 0.38, 0.045))
    bar = fig.colorbar(image, cax=cax, orientation="horizontal", extend="min")
    bar.set_ticks(nvf.F_EDGES, labels=[f"{edge:g}" for edge in nvf.F_EDGES])
    bar.set_label("mean F of the uppermost active cell (grey: below 0.01)", fontsize=7)
    bar.outline.set_linewidth(0.5)
    handles = [
        plt.Line2D([], [], color=nvf.INK, lw=1.0,
                   path_effects=[patheffects.withStroke(linewidth=2.2, foreground=nvf.SURFACE)],
                   label=f"published probability \u2265 {PROBABILITY:g}"),
        plt.Line2D([], [], color=nvf.STREAM, lw=1.0, label="SFR reaches"),
        plt.Line2D([], [], ls="", marker="o", ms=3.5, mfc=nvf.SURFACE, mec=nvf.INK, mew=0.7,
                   label="priority wells"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.53, 0.03), ncols=2,
               frameon=False, handlelength=2.2, columnspacing=1.2)


def neversink_ensemble(
    fig_dir: Path, idomain: np.ndarray, mean_f: np.ndarray, probable: np.ndarray, windows: dict,
    segments: np.ndarray, width: float = TEXT_WIDTH, bar_km: dict = ENSEMBLE_BAR_KM,
) -> Path:
    """Draw the ensemble mean F in the three cluster windows of the map figure."""
    nvf.paper_style()
    nrow, ncol = idomain.shape[1:]
    wells_ij = list(nvf.well_ij(wf.PRIORITY_WELLS, (nrow, ncol)).values())
    fig, axes = plt.subplots(1, 3, figsize=(width, 2.55))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.3, wspace=0.04)
    for ax, letter, (name, window) in zip(axes, "abc", windows.items()):
        image = ensemble_panel(ax, mean_f, probable, window, wells_ij, segments)
        ax.set_title(f"({letter}) {WINDOW_TITLES[name]}", loc="left")
        scale_bar(ax, window, nrow, bar_km[name])
    ensemble_legend(fig, image)
    return nvf.save(fig, fig_dir, "figS1_neversink_ensemble")


def cluster_windows(idomain: np.ndarray, f: np.ndarray, published: np.ndarray, out: Path) -> dict:
    """Return the cluster windows (U, SV_W, SV_S); the SV windows cropped to F of the calibrated
    model and the published area."""
    windows = nvf.capture_windows(idomain, wf.PRIORITY_WELLS, published, out)
    for name in CROPPED:
        windows[name] = tight_window(f, published, windows[name])
    return windows


def ensemble_fields(idomain: np.ndarray, maps_file: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return the ensemble mean F (stream reaches as cells) on the active cells and the cells of
    published probability of contribution PROBABILITY or more."""
    maps = np.load(maps_file)
    active = (idomain > 0).any(axis=0)
    return np.where(active, maps["cells:mean_F"], np.nan), maps["mp7"] >= PROBABILITY


def main(maps: bool = True, ensemble: bool = True, out_dir: Path = OUT_DIR,
         data_dir: Path = nvf.OUT) -> list[Path]:
    """Draw the map and ensemble figures from the stored outputs of the Neversink study; return
    the PNG paths."""
    model_dir = data_dir / "optimal"
    idomain = wf.grid_idomain(model_dir)
    shape = idomain.shape[1:]
    published = nvf.published_mask(shape, data_dir)
    assert int(published.sum()) == PUBLISHED_CELLS, f"published cells: {published.sum()}"
    f = nvf.capture_fields(idomain, data_dir)["streams as cells"]
    windows = cluster_windows(idomain, f, published, data_dir)
    segments = nvf.model_segments(model_dir, shape[0])
    paths = []
    if maps:
        paths.append(neversink_maps(out_dir, idomain, f, published, windows, segments))
    if ensemble:
        n = len(list((data_dir / "ensemble" / "fractions").glob("*.npz")))
        assert n == N_REALISATIONS, f"ensemble realisations: {n}"
        mean_f, probable = ensemble_fields(idomain,
                                           data_dir / "ensemble" / "probability_maps.npz")
        paths.append(neversink_ensemble(out_dir, idomain, mean_f, probable, windows, segments))
    return paths


if __name__ == "__main__":
    t0 = time.perf_counter()
    for p in main():
        print(p)
    print(f"{time.perf_counter() - t0:.1f} s")
