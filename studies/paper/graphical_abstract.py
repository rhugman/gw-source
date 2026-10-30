"""Graphical abstract (Table of Contents image) of the paper.

Groundwater asks for a square image of 5.5 in at 300 dpi, as TIFF, PDF or JPG. The image shows
what gwsource returns for the supply well of the synthetic example model
(tutorials/herebedragons.py), in four panels of one size: its contributing area (F, viridis with
the F = 0.1 dashed and F = 0.5 solid contours), the mean travel time to the well where F > 0.5
(log scale, magma_r), the well's water by source, and the well's water by source in every season
of two years of the seasonal model (each step traced as a snapshot, so water released from
storage is a source; tutorials/08_transient_tracking, helpers.step_summary). The maps reuse the
drawing helpers of gallery_figure.py and example_figures.py; the travel time is computed as in
synthetic_figures.compute_travel_time.

The model workspace goes in the system temporary folder and is deleted at the end; the image goes
to output/paper/ in the repository root (git-ignored) as PNG, TIFF and PDF.

    python studies/paper/graphical_abstract.py
"""

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
REPO = PAPER_DIR.parents[1]
IMPORT_DIRS = (PAPER_DIR, REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import example_figures as ef  # noqa: E402
import example_figures_b as efb  # noqa: E402
import gallery_figure as gf  # noqa: E402
import method_figures as mfig  # noqa: E402
import synthetic_figures as sf  # noqa: E402

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm, Normalize  # noqa: E402

NAME = "graphical_abstract"
SIZE = 5.5  # in, square
WORK_DIR = Path(tempfile.gettempdir()) / NAME
TITLE_SIZE = 14
LABEL_SIZE = 11
SOURCES = {"recharge": "recharge", "stream": "stream", "west edge": "boundary"}  # name: label
SERIES = {"snapshot RCH": "recharge", "snapshot SFR": "stream", "snapshot CHD": "west edge",
          "snapshot storage": "storage"}  # step_summary column: source
STORAGE_COLOUR = sf.INITIAL_COLOUR


def compute(work: Path, mf6: Path) -> dict:
    """F to the well, mean travel time where F > 0.5 (years), the well's water by source, and
    by source in every season."""
    run = sf.hbd.build_quickstart(work / "quickstart", mf6)
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=[sf.WELL])
    res = gs.backward(step, {sf.WELL: well})
    f = res.fraction_through[sf.WELL]
    mean_time = gs.travel_time(step, res, sf.POROSITY).mean_time[sf.WELL]
    years = np.where(f > efb.CAPTURE_F, mean_time, np.nan) / sf.YEAR
    volumes = sf.by_source(res)
    well_cells = np.flatnonzero(well.cells)
    return {"area": sf.map_layer(run.grb_file, step, f, well_cells),
            "time": sf.map_layer(run.grb_file, step, years, well_cells),
            "shares": volumes / volumes.sum(),
            "seasons": seasonal(work, mf6)}


def seasonal(work: Path, mf6: Path, n_years: int = 2) -> pd.DataFrame:
    """The well's water by source in every step of the seasonal model, each step a snapshot."""
    run = sf.hbd.build_transient(work / "seasonal", mf6, n_years=n_years, steps_per_season=1)
    reader = gs.open_model(run.ws, boundnames=True)
    return efb.tutorial_modules("08_transient_tracking")[1].step_summary(reader, sf.WELL)


def map_axes(ax) -> None:
    """Bare square map: no ticks, a thin frame."""
    ax.set_xlim(0.0, sf.EXTENT)
    ax.set_ylim(0.0, sf.EXTENT)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.6)


def colour_bar(fig, image, cax, ticks: tuple, labels: tuple, label: str) -> None:
    """Slim vertical colour bar beside a map, its label above it."""
    bar = fig.colorbar(image, cax=cax, ticks=ticks)
    bar.ax.set_yticklabels(labels)
    bar.ax.minorticks_off()
    bar.ax.tick_params(labelsize=LABEL_SIZE, length=2, pad=2)
    bar.ax.text(0.0, 1.03, label, transform=bar.ax.transAxes, ha="left", va="bottom",
                fontsize=LABEL_SIZE)
    bar.outline.set_linewidth(0.5)


def draw_area(ax, layer: dict):
    """Contributing area: F with its contours, the stream and the well."""
    image = gf.draw_layer(ax, layer, ef.F_CMAP, Normalize(0.0, 1.0))
    ef.draw_f_contours(ax, layer["grb"], layer["step"], layer["values"])
    ef.draw_well(ax, layer["grb"], layer["well"], size=220.0)
    map_axes(ax)
    return image


def draw_time(ax, layer: dict):
    """Mean travel time to the well where F > 0.5 (years), the stream and the well."""
    image = gf.draw_layer(ax, layer, "magma_r", LogNorm(*gf.TRAVEL_NORM))
    ef.draw_well(ax, layer["grb"], layer["well"], size=220.0)
    map_axes(ax)
    return image


def draw_sources(ax, shares, names: dict = SOURCES) -> None:
    """The well's water by source: one bar each, the share printed on top."""
    values = [100.0 * float(shares[n]) for n in names]
    ax.bar(range(len(names)), values, width=0.6, color=[sf.COLOURS[n] for n in names])
    for x, value in enumerate(values):
        ax.text(x, value + 2.0, f"{value:.0f} %", ha="center", va="bottom", fontsize=LABEL_SIZE)
    ax.set_xticks(range(len(names)), list(names.values()), fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", length=0)
    ax.set_yticks([])
    ax.set_ylim(0.0, 100.0)
    ax.spines[["left", "top", "right"]].set_visible(False)


def draw_series(ax, summary, series: dict = SERIES, labels: dict = SOURCES,
                y_max: float = 140.0) -> None:
    """The well's water by source in every season of the seasonal model (%), one line each; the
    legend above 100 %."""
    years = summary["time (yr)"].to_numpy()
    shares = [100.0 * summary[c].to_numpy() for c in series]
    colours = [sf.COLOURS.get(n, STORAGE_COLOUR) for n in series.values()]
    for share, colour, name in zip(shares, colours, series.values()):
        ax.plot(years, share, color=colour, lw=2.0, marker="o", ms=3.5,
                label=labels.get(name, name))
    ax.legend(loc="upper center", ncol=2, fontsize=LABEL_SIZE - 1, frameon=False,
              handlelength=1.2, columnspacing=1.0, labelspacing=0.2, borderaxespad=0.1)
    ax.set_xlim(0.0, years[-1])
    ax.set_ylim(0.0, y_max)
    ax.spines["left"].set_bounds(0.0, 100.0)
    ax.set_xticks((0, 1, 2))
    ax.set_yticks((0, 50, 100))
    ax.tick_params(labelsize=LABEL_SIZE - 1, length=2, pad=1)
    ax.set_xlabel("years", fontsize=LABEL_SIZE, labelpad=1)
    ax.set_ylabel("%", fontsize=LABEL_SIZE, labelpad=2)


def make_figure(data: dict, out_dir: Path, size: float = SIZE, name: str = NAME) -> list[Path]:
    """Square image of four panels of one size: contributing area and mean travel time maps
    above, the well's water by source and by source in every season below."""
    fig = plt.figure(figsize=(size, size))
    side, column, top, gap = 2.1, 2.72, 0.38, 0.45  # in: panel, column width, top and row gaps
    x0 = (0.06, 0.06 + column)
    y0 = (size - top - side, size - top - 2 * side - gap)
    assert y0[1] >= 0.45, "no room for the axis labels of the lower panels"
    ax_area, ax_time, ax_src, ax_series = (sf.axes_in(fig, (size, size), (x, y, side, side))
                                           for y in y0 for x in x0)
    bars = ((ax_area, draw_area(ax_area, data["area"]), (0.0, 0.5, 1.0), ("0", "0.5", "1"),
             "F"),
            (ax_time, draw_time(ax_time, data["time"]), (1.0, 10.0, 100.0), ("1", "10", "100"),
             "years"))
    for ax, image, ticks, labels, label in bars:
        box = ax.get_position()
        cax = sf.axes_in(fig, (size, size), (box.x1 * size + 0.08, box.y0 * size, 0.08, side))
        colour_bar(fig, image, cax, ticks, labels, label)
    draw_sources(ax_src, data["shares"])
    draw_series(ax_series, data["seasons"])
    for ax, title in ((ax_area, "contributing area"), (ax_time, "mean travel time"),
                      (ax_src, "sources of water"), (ax_series, "seasonal contribution")):
        ax.set_title(title, fontsize=TITLE_SIZE, pad=9)
    out_dir.mkdir(parents=True, exist_ok=True)
    tiff = out_dir / f"{name}.tif"
    fig.savefig(tiff, dpi=mfig.DPI, pil_kwargs={"compression": "tiff_lzw"})
    return [tiff, *mfig.save(fig, out_dir, name)]


def main(out_dir: Path = mfig.FIG_DIR, work: Path = WORK_DIR, keep_work: bool = False) -> None:
    """Build and trace the example model and draw the graphical abstract."""
    mfig.paper_style()
    data = compute(sf.clean_dir(work), mfig.find_mf6())
    print("shares of the well's water:", data["shares"].round(3).to_dict())
    print("wrote", make_figure(data, out_dir))
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
