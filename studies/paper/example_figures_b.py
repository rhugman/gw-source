"""Example figures of the paper, Sections 4.6 to 4.10 (Figs 7, 8, 10 and 11).

Captions: docs/paper/draft/display/E2.md (Figs 7, 8, 11) and E3.md (Fig. 10); text:
docs/paper/draft/sections/04b, 04c and 04d. Each figure rebuilds its model with the builders of
the worked examples (tutorials/herebedragons.py and the helpers.py next to each notebook), so the
figures show the notebooks' numbers. The numbers the captions and text quote are asserted before
plotting, so a figure stops if they drift.

- Fig. 7 (Section 4.6), travel time. (a) Mean travel time to the well inside the F > 0.5 area,
  with the 5-year and 25-year time-of-travel zones. (b) Mean travel time per release cell, PRT
  weight-losing particles against full mixing, both to the well cell, coloured by F.
- Fig. 8 (Section 4.7), a stream fed by drains through the water mover. (a) F on the aquifer cells
  alone; (b) F with the stream reaches and the mover traced; (c) F of each reach. A multi-aquifer
  well (MAW) in a three-layer model, section through the MAW's row: (d) F on the aquifer cells
  alone; (e) F with the MAW borehole traced as a node.
- Fig. 10 (Supporting Information Fig. S3, file figS3_ensembles), history matching with PEST++
  IES on the model with the SFR stream. Prior and posterior probability of contribution (the share
  of realisations with F > 0.5) with the true F > 0.5 outline, and the stream share of each
  realisation. PEST++ runs serially here (N_WORKERS = 0 in the notebook):
  its local TCP workers need ports. The posterior does not
  depend on the number of workers, so the serial run gives the notebook's numbers.
- Fig. 11 (Section 4.10), the unit-concentration example of Bedekar et al. (2024). (a) Tracked
  shares of the pumped water against the read-offs of their Figure 2. (b-e) Backward tracking in
  time, layer 2: fraction of each cell's water at the start that the well pumps within 1, 5, 10 and
  25 years. (f) Steady F of the year-25 flows.

Style from studies/paper/method_figures.py (7 in wide, 7 to 8 pt type, PNG at 300 dpi and PDF).
F maps use viridis from 0 to 1 with white F = 0.1 (dashed) and F = 0.5 (solid) contours, as the
other example figures. Run from the repository root (workspaces in studies/paper/output,
git-ignored):

    PYTHONPATH=src:tutorials python studies/paper/example_figures_b.py
"""

import importlib.util
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (style, palette, save, find_mf6)

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.colors import ListedColormap, LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

TUTORIAL_DIR = mfig.TUTORIAL_DIR
WORK_DIR = mfig.WORK_DIR / "example_figures_b"
WELL = "supply_well"
YEAR = 365.25  # days
F_CMAP = "viridis"
CONTOUR_COLOUR = "white"
RIVER_COLOUR = mfig.OKABE_ITO["blue"]
WELL_STYLE = {"marker": "*", "ms": 8, "color": mfig.OKABE_ITO["vermillion"], "mec": "black",
              "mew": 0.5, "ls": "none", "zorder": 6}
DRAIN_STYLE = {"marker": "v", "ms": 4.5, "color": "white", "mec": "black", "mew": 0.6,
               "ls": "none", "zorder": 6}

# Fig. 7: tutorial 06 settings
POROSITY = 0.3
PRT_SUBDIVISIONS = 2
CAPTURE_F = 0.5
ZONE_YEARS = (5, 25)
TRAVEL_NORM = (0.1, 100.0)  # years, colour scale of the travel-time map
SCATTER_LIMITS = (0.1, 3000.0)  # years: every release cell with both times
ZOOM_Y = (0.4, 1.6)  # km, rows of the travel-time map (the F > 0.5 area lies within)
ZONE_LABEL_XY = {5: (1.3, 0.86), 25: (0.86, 1.0)}  # km, contour label positions
ZONE_COLOUR = "tab:cyan"

# Fig. 8: tutorial 07
REACH_COLOURS = {"losing": "tab:blue", "gaining": "tab:orange"}
MAW_GROUP = "MAW pumping"
SECTION_X = (0.5, 1.7)  # km, columns of the MAW cross-section (MAW and supply well within)
BORE_STYLE = {"color": "white", "lw": 1.8, "solid_capstyle": "butt", "zorder": 5,
              "path_effects": [patheffects.withStroke(linewidth=3.2, foreground="black")]}
LAYER_NAMES = ("layer 1", "layer 2 (aquitard)", "layer 3")
LAYER_NAME_COLOURS = ("white", "black", "black")  # readable on the F colours of panel (d)
FIG8_HEIGHT = 4.6  # in: the maps of (a) and (b) fill their columns, so (d) and (e) align below

# Fig. 10: tutorial 09 settings (one pilot-point ensemble: the prior of section 1, the posterior of section 9)
SIGMA_LNK = 0.8
CORRELATION_LENGTH = 400.0  # m: ln K correlated as exp(-(r / CORRELATION_LENGTH)^2)
TRUTH_SEED = 2024
N_OBS = 40
OBS_SEED = 11
NOISE_SD = 0.05
NOISE_SEED = 12
PP_SPACING = 4
NUGGET = 1e-4
N_REAL = 50
PRIOR_SEED = 3
N_ITER = 3
N_WORKERS = 0  # serial PEST++: the sandbox blocks the workers' local ports
PROB_CMAP = "YlGnBu"
PROB_LEVELS = (0.1, 0.5, 0.9)
PROB_LABEL_XY = {  # km, label positions of the P = 0.1, 0.5 and 0.9 contours
    "prior": ((0.8, 1.52), (0.5, 0.62), (0.7, 1.1)),
    "posterior": ((1.0, 1.3), (0.15, 1.33), (0.75, 1.14)),
}
TRUTH_COLOUR = "tab:red"
SHARE_COLOUR = "tab:blue"

# Fig. 11: tutorial 10 settings
BEDEKAR_POROSITY = 0.1
BEDEKAR_YEARS = 25
BEDEKAR_NSTP = 300
BEDEKAR_SOURCES = {"lateral inflow": {"package": "INFLOW"}, "recharge": {"package": "RCH"},
                   "stream": {"package": "RIV"}}
BEDEKAR_INITIAL = {"storage": "all"}
BEDEKAR_GROUPS = ["storage", "lateral inflow", "recharge", "stream"]
BEDEKAR_PACKAGES = {"INFLOW": "lateral inflow", "RCH": "recharge", "RIV": "stream",
                    "STO-SS": "storage", "STO-SY": "storage"}
BEDEKAR_WINDOWS = (1, 5, 10, 25)  # years
BEDEKAR_COLOURS = {"storage": "0.5", "recharge": "tab:green", "stream": "tab:blue",
                   "lateral inflow": "tab:orange"}  # as in Bedekar et al. (2024), Fig. 2
BEDEKAR_LABELS = {"storage": "stored water", "lateral inflow": "lateral inflow",
                  "recharge": "recharge", "stream": "stream"}
PAPER_YEARS = (0.5, 1, 1.5, 2, 3, 5, 7.5, 10, 11, 12, 13, 15, 17.5, 20, 25)
PAPER_FIG2 = pd.DataFrame(  # percent, read off Bedekar et al. (2024), Fig. 2 (tutorial 10)
    {
        "lateral inflow": [0, 0, 0, 0, 0, 0, 0, 7.7, 16.6, 25.9, 33.0, 40.9, 45.4, 47.2, 48.1],
        "recharge": [1.7, 3.3, 4.9, 6.3, 9.1, 13.9, 19.4, 24.3, 25.7, 26.8, 27.6, 28.3, 28.8, 29.0,
                     29.2],
        "stream": [0.9, 8.0, 15.7, 19.0, 21.3, 22.2, 22.4, 22.5, 22.4, 22.5, 22.5, 22.5, 22.4, 22.5,
                   22.5],
    },
    index=pd.Index(PAPER_YEARS, name="time (yr)"),
) / 100.0

# Quoted numbers: {name: (value, tolerance)}; the computed value must lie within the tolerance.
QUOTED_FIG7 = {
    "zone 5 yr (km2)": (0.098, 5e-4),
    "zone 25 yr (km2)": (0.455, 5e-4),
    "zone 5 yr (cells)": (39, 0),
    "zone 25 yr (cells)": (182, 0),
    "mean time, all water (yr)": (46.0, 0.05),
    "mean time, river (yr)": (2.2, 0.05),
    "mean time, recharge (yr)": (41.7, 0.05),
    "mean time, west edge (yr)": (108.4, 0.05),
    "residence time, well cell (d)": (32.2, 0.05),
    "particles": (18208, 0),
    "captured particle flow (m3/d)": (799.9, 0.05),
    "PRT mean (yr)": (45.7, 0.05),
    "full mixing to the well cell (yr)": (45.9, 0.05),
    "PRT vs full mixing (%)": (-0.5, 0.05),
    "core cells": (456, 0),
    "core median ratio": (0.96, 0.005),
    "edge cells": (676, 0),
    "edge median ratio": (5.72, 0.005),
    "PRT zone 5 yr (km2)": (0.122, 5e-4),
    "PRT zone 25 yr (km2)": (0.465, 5e-4),
}
QUOTED_FIG8 = {
    "SFR share, cells only": (0.319, 5e-4),
    "SFR, cells only (m3/d)": (255.2, 0.05),
    "stream inflow to the well (m3/d)": (129.4, 0.05),
    "extra recharge (m3/d)": (125.8, 0.05),
    "through the mover (m3/d)": (188.3, 0.05),
    "F drain a": (0.345, 5e-4),
    "F drain b": (0.431, 5e-4),
    "F reach 1": (0.43, 5e-3),
    "last feeding reach": (21, 0),
    "F reach 21": (0.014, 5e-4),
    "flow loop nodes": (711, 0),
    "MAW pumping (m3/d)": (10.0, 0.05),
    "borehole inflow, layers 1-2 (m3/d)": (24.3, 0.05),
    "borehole outflow, layer 3 (m3/d)": (14.3, 0.05),
    "MAW water to the well, cells only (m3/d)": (14.3, 0.05),
    "extra recharge with the borehole (m3/d)": (14.3, 0.05),
    "F MAW cell layer 1, cells only": (0.06, 5e-3),
    "F MAW cell layer 1, borehole traced": (0.53, 5e-3),
}
QUOTED_FIG10 = {  # tutorial 09 sections 9.1 to 9.4, model with the SFR stream (serial PEST++)
    "truth area F > 0.5 (km2)": (0.998, 5e-4),
    "truth stream share": (0.092, 5e-4),
    "prior area P >= 0.9 (km2)": (0.560, 5e-4),
    "posterior area P >= 0.9 (km2)": (0.965, 5e-4),
    "prior band 0.1 < P < 0.9 (km2)": (1.083, 5e-4),
    "posterior band 0.1 < P < 0.9 (km2)": (0.360, 5e-4),
    "prior stream share 5 %": (0.000, 5e-4),
    "prior stream share 95 %": (0.326, 5e-4),
    "posterior stream share 5 %": (0.044, 5e-4),
    "posterior stream share 95 %": (0.133, 5e-4),
    "prior true zone with P >= 0.5 (%)": (78.4, 0.05),
    "posterior true zone with P >= 0.5 (%)": (94.0, 0.05),
    "prior mean phi": (3673.5, 0.5),
    "posterior mean phi": (55.8, 0.05),
    "prior P >= 0.9 inside the true zone (%)": (85.3, 0.05),
    "posterior P >= 0.9 inside the true zone (%)": (87.6, 0.05),
}
QUOTED_FIG11 = {
    "lateral inflow at 25 yr": (0.482, 5e-4),
    "recharge at 25 yr": (0.292, 5e-4),
    "stream at 25 yr": (0.225, 5e-4),
    "stream at 1 yr": (0.080, 5e-4),
    "lateral inflow at 10 yr": (0.090, 5e-4),
    "stream at 0.5 yr (%)": (1.1, 0.05),
    "largest difference from the read-offs (points)": (1.3, 0.05),
    "year of the largest difference": (10.0, 0),
    "first year with lateral inflow > 0.1 %": (7.0, 1.0),
    "cells w > 0.5, layer 2, 1 yr": (841, 0),
    "cells w > 0.5, layer 2, 25 yr": (6825, 0),
    "steady cells F > 0.5, layer 1": (6817, 0),
    "steady cells F > 0.5, layer 2": (6829, 0),
    "steady cells F > 0.5, layer 3": (6831, 0),
    "steady lateral inflow share": (0.483, 5e-4),
    "steady recharge share": (0.292, 5e-4),
    "steady stream share": (0.225, 5e-4),
    "lateral inflow (m3/d)": (454.5, 0.05),
    "recharge (m3/d)": (306.0, 0.05),
}


# ---------------------------------------------------------------- shared helpers


def tutorial_modules(tutorial: str, tutorial_dir: Path = TUTORIAL_DIR):
    """Import herebedragons and one tutorial's helpers.py (under a unique name); return both."""
    if str(tutorial_dir) not in sys.path:
        sys.path.insert(0, str(tutorial_dir))
    import herebedragons as hbd

    name = f"helpers_{tutorial.split('_')[0]}"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, tutorial_dir / tutorial / "helpers.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return hbd, sys.modules[name]


def clean_dir(path: Path) -> Path:
    """Remove and recreate a workspace folder of this script."""
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def check_quoted(computed: dict, quoted: dict, figure: str) -> None:
    """Assert that every quoted number matches the computed one within its tolerance."""
    for name, (value, tolerance) in quoted.items():
        got = computed[name]
        assert abs(got - value) <= tolerance + 1e-12, f"{figure}, {name}: computed {got}, quoted {value}"
    print(f"{figure}: {len(quoted)} quoted numbers match")


def map_extent(spec) -> tuple[float, float, float, float]:
    """Return the map extent (km) of a regular tutorial grid."""
    return (0.0, spec.lx / 1000.0, 0.0, spec.ly / 1000.0)


def cell_centres_km(spec) -> tuple[np.ndarray, np.ndarray]:
    """Return the x and y (km) of the cell centres of a regular tutorial grid."""
    x = (np.arange(spec.ncol) + 0.5) * spec.delr / 1000.0
    y = (spec.ly - (np.arange(spec.nrow) + 0.5) * spec.delc) / 1000.0
    return x, y


def draw_field(ax, grid: np.ndarray, spec, **kwargs):
    """Draw one layer of per-cell values (row 0 north) as an image in km."""
    image = ax.imshow(grid, extent=map_extent(spec), origin="upper", interpolation="nearest",
                      **kwargs)
    ax.set_aspect("equal")
    return image


def draw_contours(ax, grid: np.ndarray, spec, levels: tuple, colours=CONTOUR_COLOUR,
                  linestyles=("--", "-"), linewidth: float = 0.9):
    """Draw contours of one layer of per-cell values at the cell centres."""
    x, y = cell_centres_km(spec)
    return ax.contour(x, y, np.ma.masked_invalid(grid), levels=list(levels), colors=colours,
                      linestyles=list(linestyles), linewidths=linewidth)


def fill_cells(ax, spec, rows: np.ndarray, cols: np.ndarray, colour: str = RIVER_COLOUR) -> None:
    """Fill the given cells of a regular grid with one colour."""
    mask = np.full((spec.nrow, spec.ncol), np.nan)
    mask[rows, cols] = 1.0
    draw_field(ax, mask, spec, cmap=ListedColormap([colour]), vmin=0.0, vmax=2.0, zorder=3)


def mark_cell(ax, spec, rc: tuple[int, int], style: dict) -> None:
    """Mark the centre of cell (row, col) with a marker style."""
    x, y = spec.xy(rc)
    ax.plot(x / 1000.0, y / 1000.0, **style)


def node_rc(node: int, spec) -> tuple[int, int]:
    """Return the (row, col) of a node of a DIS grid (any layer)."""
    return divmod(int(node) % (spec.nrow * spec.ncol), spec.ncol)


def map_axes(ax, spec, ticks: tuple, ylabel: bool = True) -> None:
    """Set km ticks and axis labels on a map."""
    ax.set_xlim(0.0, spec.lx / 1000.0)
    ax.set_ylim(0.0, spec.ly / 1000.0)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xlabel("x (km)")
    if ylabel:
        ax.set_ylabel("y (km)")
    else:
        ax.set_yticklabels([])


def title(ax, text: str) -> None:
    """Write a bold panel title at the left, as in the other paper figures."""
    ax.set_title(text, loc="left", fontweight="bold")


def colour_bar(fig, image, ax, label: str, **kwargs):
    """Add a thin colour bar to one or more axes."""
    bar = fig.colorbar(image, ax=ax, **kwargs)
    bar.set_label(label)
    bar.outline.set_linewidth(0.5)
    return bar


# ---------------------------------------------------------------- Fig. 7: travel time


def compute_fig7(work: Path, mf6: Path) -> dict:
    """Build tutorial 06's model, trace it, compute travel times and run the PRT comparison."""
    hbd, h06 = tutorial_modules("06_travel_time")
    run = hbd.build_quickstart(clean_dir(work / "fig7") / "model", mf6)
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=[WELL])
    res = gs.backward(step, {WELL: well})
    tt = gs.travel_time(step, res, POROSITY)
    prt = gs.track_particles(run.ws, step, res, WELL,
                             gs.PrtConfig(porosity=POROSITY, subdivisions=PRT_SUBDIVISIONS), mf6,
                             work / "fig7" / "prt")
    return {"run": run, "step": step, "res": res, "tt": tt, "prt": prt,
            "well_cell": int(np.flatnonzero(well.cells)[0]),
            "means": h06.eulerian_means(step, res, tt, WELL), "zone_area": h06.zone_area}


def fig7_values(data: dict) -> dict:
    """Return the numbers Section 4.6 quotes, from the Fig. 7 data."""
    step, tt, prt = data["step"], data["tt"], data["prt"]
    f = data["res"].fraction_through[WELL]
    t_well, t_exit = tt.mean_time[WELL], tt.mean_time_to_exit_cell[WELL]
    assert np.array_equal(f >= CAPTURE_F, f > CAPTURE_F), "F >= 0.5 and F > 0.5 select other cells"
    zone_area = data["zone_area"]
    out = {}
    for years in ZONE_YEARS:
        out[f"zone {years} yr (km2)"] = zone_area(step.area, t_well, f, years * YEAR) / 1e6
        out[f"zone {years} yr (cells)"] = zone_area(np.ones(step.n_cells), t_well, f, years * YEAR)
        prt_f = np.nan_to_num(prt.cell_capture_fraction)
        in_prt = (prt_f >= CAPTURE_F) & np.isfinite(prt.cell_mean_arrival) & (
            prt.cell_mean_arrival <= years * YEAR)
        out[f"PRT zone {years} yr (km2)"] = step.area[in_prt].sum() / 1e6
    means = data["means"]
    out["mean time, all water (yr)"] = means["all sources"]["to the well"] / YEAR
    out["mean time, river (yr)"] = means["RIV"]["to the well"] / YEAR
    out["mean time, recharge (yr)"] = means["RCH"]["to the well"] / YEAR
    out["mean time, west edge (yr)"] = means["CHD"]["to the well"] / YEAR
    out["residence time, well cell (d)"] = tt.residence_time[data["well_cell"]]
    out["particles"] = prt.release.n
    out["captured particle flow (m3/d)"] = prt.captured_flow
    out["PRT mean (yr)"] = prt.mean_arrival / YEAR
    out["full mixing to the well cell (yr)"] = means["all sources"]["to the well cell"] / YEAR
    out["PRT vs full mixing (%)"] = 100.0 * (prt.mean_arrival
                                            / means["all sources"]["to the well cell"] - 1.0)
    both = np.isfinite(prt.cell_mean_arrival) & np.isfinite(t_exit) & (t_exit > 0)
    ratio = prt.cell_mean_arrival[both] / t_exit[both]
    core = f[both] >= CAPTURE_F
    out["core cells"], out["core median ratio"] = int(core.sum()), float(np.median(ratio[core]))
    out["edge cells"], out["edge median ratio"] = int((~core).sum()), float(np.median(ratio[~core]))
    return out


def make_fig7(out_dir: Path, data: dict) -> list[Path]:
    """Fig. 7: travel-time map with time-of-travel zones, and PRT against full mixing per cell."""
    step, tt, prt, spec = data["step"], data["tt"], data["prt"], data["run"].spec
    f = data["res"].fraction_through[WELL]
    t_zone = np.where(f > CAPTURE_F, tt.mean_time[WELL], np.nan) / YEAR
    grid = gs.export.to_grid(step, t_zone)[0]
    closed = np.where(np.isfinite(grid), grid, 10.0 * TRAVEL_NORM[1])  # zones end at F = 0.5

    fig, axes = plt.subplots(1, 2, figsize=(mfig.FULL_WIDTH, 2.45), layout="constrained",
                             gridspec_kw={"width_ratios": [1.4, 1.0], "wspace": 0.12})
    ax = axes[0]
    image = draw_field(ax, grid, spec, cmap="magma_r", norm=LogNorm(*TRAVEL_NORM))
    lines = draw_contours(ax, closed, spec, ZONE_YEARS, colours=ZONE_COLOUR, linestyles=("-", "-"),
                          linewidth=1.1)
    ax.clabel(lines, fmt={y: f"{y} yr" for y in ZONE_YEARS}, fontsize=7, inline_spacing=2,
              manual=[ZONE_LABEL_XY[y] for y in ZONE_YEARS])
    fill_cells(ax, spec, np.arange(spec.nrow), np.full(spec.nrow, spec.riv_col))
    mark_cell(ax, spec, spec.wells[0][1], WELL_STYLE)
    map_axes(ax, spec, (0, 0.5, 1, 1.5, 2))
    ax.set_ylim(*ZOOM_Y)
    ax.set_yticks((0.5, 1.0, 1.5))
    title(ax, "(a) Mean travel time to the well, F > 0.5")
    ax.set_anchor("N")  # top level with panel (b)
    colour_bar(fig, image, None, "mean travel time (years)", cax=ax.inset_axes((1.03, 0.0, 0.04, 1.0)))

    ax = axes[1]
    t_exit = tt.mean_time_to_exit_cell[WELL]
    both = np.isfinite(prt.cell_mean_arrival) & np.isfinite(t_exit) & (t_exit > 0)
    order = np.argsort(f[both])[::-1]  # draw the edge cells (small F) on top
    points = ax.scatter(t_exit[both][order] / YEAR, prt.cell_mean_arrival[both][order] / YEAR,
                        c=f[both][order], s=4, linewidths=0, cmap=F_CMAP, vmin=0.0, vmax=1.0)
    ax.plot(SCATTER_LIMITS, SCATTER_LIMITS, color=mfig.INK, ls="--", lw=0.9, label="equal times")
    ax.set(xscale="log", yscale="log", xlim=SCATTER_LIMITS, ylim=SCATTER_LIMITS)
    ax.set_box_aspect(1.0)
    ax.set_xlabel("full mixing (years)")
    ax.set_ylabel("PRT particles (years)")
    ax.legend(loc="upper left")
    title(ax, "(b) Time per release cell")
    ax.set_anchor("N")
    colour_bar(fig, points, None, "F in the release cell (-)", cax=ax.inset_axes((1.04, 0.0, 0.04, 1.0)))
    return mfig.save(fig, out_dir, "fig7_travel_time")


# ---------------------------------------------------------------- Fig. 8: networks


def compute_fig8(work: Path, mf6: Path) -> dict:
    """Build tutorial 07's stream and MAW models; trace each on the cells and with its nodes."""
    hbd, h07 = tutorial_modules("07_networks_multimodel")
    stream = hbd.build_stream_mover(clean_dir(work / "fig8") / "stream", mf6)
    cells_only = gs.read_step(stream.ws, boundnames=True)
    back_off = gs.backward(cells_only, {WELL: gs.select(cells_only, boundnames=[WELL])})
    network = gs.open_simulation(stream.ws, package_nodes=("SFR",), boundnames=True).read((0, 0))
    back_on = gs.backward(network, {WELL: gs.select(network, boundnames=[WELL])})
    reaches = network.block("SFR").nodes
    exchange = h07.reach_exchange(network, "SFR")
    drain_nodes = stream.info["drain_nodes"]
    mover = h07.edges_between(network, list(drain_nodes.values()), reaches)
    for name, result, step in (("cells only", back_off, cells_only), ("reaches", back_on, network)):
        check = gs.diagnostics.backward_closure(step, result, WELL)
        assert check.relative_error < 1e-8, (name, check)
    return {"stream": stream, "cells_only": cells_only, "back_off": back_off, "network": network,
            "back_on": back_on, "reaches": reaches, "exchange": exchange,
            "drain_nodes": drain_nodes, "mover": mover, "hbd": hbd,
            "n_cells": network.block(stream.name).n,
            **compute_maw(work / "fig8" / "maw", mf6, hbd, h07)}


def compute_maw(ws: Path, mf6: Path, hbd, h07) -> dict:
    """Build tutorial 07's MAW model; trace it on the cells and with the borehole as a node."""
    maw = hbd.build_maw(ws, mf6)
    maw_cells = maw.info["maw_nodes"]  # the MAW's cell in layers 1, 2 and 3
    maw_step = gs.read_step(maw.ws, boundnames=True)
    maw_off = gs.backward(maw_step, {WELL: gs.select(maw_step, boundnames=[WELL])})
    maw_net = gs.read_network(maw.ws, package_nodes=("MAW",), boundnames=True)
    bore = int(maw_net.block("MAW").nodes[0])  # the one MAW well is one node
    maw_on = gs.backward(maw_net, {MAW_GROUP: gs.select(maw_net, package="MAW", term="RATE"),
                                   WELL: gs.select(maw_net, boundnames=[WELL])})
    for name, result, step in (("MAW cells only", maw_off, maw_step), ("MAW node", maw_on, maw_net)):
        check = gs.diagnostics.backward_closure(step, result, WELL)
        assert check.relative_error < 1e-8, (name, check)
    return {"maw": maw, "maw_off": maw_off, "maw_on": maw_on, "maw_cells": maw_cells,
            "bore_in": h07.edges_between(maw_net, maw_cells, [bore]),
            "bore_out": h07.edges_between(maw_net, [bore], maw_cells)}


def fig8_values(data: dict) -> dict:
    """Return the numbers Section 4.7 quotes, from the Fig. 8 data (stream, then MAW)."""
    hbd = data["hbd"]
    f_on = data["back_on"].fraction_through[WELL]
    off = hbd.volume_from_table(data["back_off"], WELL)
    on = hbd.volume_from_table(data["back_on"], WELL)
    f_reach = pd.Series(f_on[data["reaches"]], index=np.arange(1, len(data["reaches"]) + 1))
    last = int(f_reach[f_reach > 0.0].index.max())
    assert (f_reach.loc[:last] > 0.0).all() and (f_reach.loc[last + 1:] == 0.0).all()
    gaining = list(f_reach.index[gaining_reaches(data["exchange"])])
    assert gaining == [2, *range(22, 41)], f"gaining reaches {gaining}"
    via_mover = float((data["mover"]["q"] * f_on[data["mover"]["dst"]]).sum())
    drains = data["drain_nodes"]
    stream_values = {
        "SFR share, cells only": float(off.loc["SFR", "share"]),
        "SFR, cells only (m3/d)": float(off.loc["SFR", "volume_from"]),
        "stream inflow to the well (m3/d)": float(on.loc["SFR:EXT-INFLOW", "volume_from"]),
        "extra recharge (m3/d)": float(on.loc["RCH", "volume_from"] - off.loc["RCH", "volume_from"]),
        "through the mover (m3/d)": via_mover,
        "F drain a": float(f_on[drains["drain_a"]]),
        "F drain b": float(f_on[drains["drain_b"]]),
        "F reach 1": float(f_reach.loc[1]),
        "last feeding reach": last,
        "F reach 21": float(f_reach.loc[21]),
        "flow loop nodes": max(c.cells.size for c in data["back_on"].cycles),
    }
    return {**stream_values, **maw_values(data)}


def maw_values(data: dict) -> dict:
    """Return the numbers of the MAW example: borehole flows, sources and F of the MAW cells."""
    hbd, maw_cells = data["hbd"], data["maw_cells"]
    bore_in, bore_out = data["bore_in"], data["bore_out"]
    assert sorted(maw_cells.index(n) for n in bore_in["src"]) == [0, 1], "inflow from layers 1, 2"
    assert [maw_cells.index(n) for n in bore_out["dst"]] == [2], "outflow to layer 3"
    off = hbd.volume_from_table(data["maw_off"], WELL)
    on = hbd.volume_from_table(data["maw_on"], WELL)
    return {
        "MAW pumping (m3/d)": -float(data["maw"].info["maw_rate"]),
        "borehole inflow, layers 1-2 (m3/d)": float(bore_in["q"].sum()),
        "borehole outflow, layer 3 (m3/d)": float(bore_out["q"].sum()),
        "MAW water to the well, cells only (m3/d)": float(off.loc["MAW", "volume_from"]),
        "extra recharge with the borehole (m3/d)":
            float(on.loc["RCH", "volume_from"] - off.loc["RCH", "volume_from"]),
        "F MAW cell layer 1, cells only": float(data["maw_off"].fraction_through[WELL][maw_cells[0]]),
        "F MAW cell layer 1, borehole traced":
            float(data["maw_on"].fraction_through[WELL][maw_cells[0]]),
    }


def gaining_reaches(exchange: pd.DataFrame) -> np.ndarray:
    """Return a mask of the reaches that gain water from the aquifer."""
    return exchange["to_cells"].to_numpy() <= exchange["from_cells"].to_numpy()


def make_fig8(out_dir: Path, data: dict) -> list[Path]:
    """Fig. 8: the stream example (a-c) above the MAW cross-sections (d, e); one F colour bar."""
    fig, axes = plt.subplot_mosaic(
        [["a", "b", "c"], ["d", "e", "key"]], figsize=(mfig.FULL_WIDTH, FIG8_HEIGHT),
        layout="constrained", width_ratios=[1.0, 1.0, 0.55], height_ratios=[1.0, 0.66],
    )
    image = draw_stream_panels(axes, data)
    draw_maw_panels(axes, data)
    colour_bar(fig, image, [axes[k] for k in "abde"], "F (-)", shrink=0.9, pad=0.02)
    return mfig.save(fig, out_dir, "fig8_networks")


def draw_stream_panels(axes: dict, data: dict):
    """Draw panels (a) to (c): F maps of the stream model and F of each reach; return the image."""
    stream, step, n_cells = data["stream"], data["cells_only"], data["n_cells"]
    spec = stream.spec
    f_maps = {"a": ("(a) Aquifer cells only", data["back_off"].fraction_through[WELL][:n_cells]),
              "b": ("(b) Stream reaches and mover traced",
                    data["back_on"].fraction_through[WELL][:n_cells])}
    for key, (text, values) in f_maps.items():
        ax = axes[key]
        grid = gs.export.to_grid(step, values)[0]
        image = draw_field(ax, grid, spec, cmap=F_CMAP, vmin=0.0, vmax=1.0)
        draw_contours(ax, grid, spec, (0.1, 0.5))
        fill_cells(ax, spec, np.arange(spec.nrow), np.full(spec.nrow, spec.riv_col))
        for node in data["drain_nodes"].values():
            mark_cell(ax, spec, node_rc(node, spec), DRAIN_STYLE)
        mark_cell(ax, spec, spec.wells[0][1], WELL_STYLE)
        map_axes(ax, spec, (0, 1, 2), ylabel=key == "a")
        title(ax, text)

    ax = axes["c"]
    f_reach = data["back_on"].fraction_through[WELL][data["reaches"]]
    y_reach = cell_centres_km(spec)[1]  # one reach per row, north to south
    gaining = gaining_reaches(data["exchange"])
    ax.plot(f_reach, y_reach, color=mfig.MUTED, lw=0.8)
    ax.plot(f_reach[~gaining], y_reach[~gaining], "o", ms=3, color=REACH_COLOURS["losing"],
            label="losing reach")
    ax.plot(f_reach[gaining], y_reach[gaining], "o", ms=3, color=REACH_COLOURS["gaining"],
            label="gaining reach")
    ax.set_ylim(0.0, spec.ly / 1000.0)
    ax.set_yticks((0, 1, 2))
    ax.set_xlim(-0.02, 0.5)
    ax.set_xlabel("F of the reach (-)")
    ax.set_ylabel("y of the reach (km)")
    ax.legend(loc="lower right", handletextpad=0.2, borderaxespad=0.2)
    title(ax, "(c) F of each reach")
    return image


def draw_maw_panels(axes: dict, data: dict) -> None:
    """Draw panels (d) and (e): F along the MAW's row, cells only and with the borehole traced."""
    maw = data["maw"]
    spec, botm = maw.spec, data["hbd"].LAYER_BOTM
    z_edges = np.array([spec.top, *botm])
    shape = (len(botm), spec.nrow, spec.ncol)
    row, col = maw.info["maw_cell"]
    layer, well_row, well_col = maw_supply_cell(data)
    assert well_row == row, "the supply well lies in the MAW's row"
    sections = {"d": ("(d) Aquifer cells only", data["maw_off"].fraction_through[WELL]),
                "e": ("(e) MAW borehole traced", data["maw_on"].fraction_through[WELL])}
    for key, (text, values) in sections.items():
        ax = axes[key]
        draw_section(ax, values[: np.prod(shape)].reshape(shape)[:, row, :], spec, z_edges)
        fill_section_cell(ax, spec, z_edges, 0, spec.riv_col, RIVER_COLOUR)
        x_bore = (col + 0.5) * spec.delr / 1000.0
        ax.plot([x_bore, x_bore], z_edges[[0, -1]], **BORE_STYLE)
        ax.plot((well_col + 0.5) * spec.delr / 1000.0, z_edges[layer:layer + 2].mean(),
                **WELL_STYLE)
        ax.set_xlim(*SECTION_X)
        ax.set_ylim(z_edges[-1], z_edges[0])
        ax.set_yticks(z_edges)
        ax.set_xlabel("x (km)")
        if key == "d":
            ax.set_ylabel("elevation (m)")
            z_mids = (z_edges[:-1] + z_edges[1:]) / 2.0
            for name, z_mid, colour in zip(LAYER_NAMES, z_mids, LAYER_NAME_COLOURS):
                ax.text(SECTION_X[0] + 0.02, z_mid, name, color=colour, ha="left", va="center",
                        fontsize=7, zorder=6)
        else:
            ax.set_yticklabels([])
        title(ax, text)

    ax = axes["key"]
    ax.axis("off")
    handles = [Line2D([], [], **BORE_STYLE, label="MAW borehole"),
               Line2D([], [], **WELL_STYLE, label="supply well"),
               Line2D([], [], color=RIVER_COLOUR, ls="none", marker="s", ms=5, label="river")]
    ax.legend(handles=handles, loc="center left", borderaxespad=0.0)


def maw_supply_cell(data: dict) -> tuple[int, int, int]:
    """Return the (layer, row, col) of the supply well of the MAW model."""
    maw = data["maw"]
    shape = (len(data["hbd"].LAYER_BOTM), maw.spec.nrow, maw.spec.ncol)
    return tuple(int(i) for i in np.unravel_index(maw.info["well_nodes"][WELL], shape))


def draw_section(ax, values: np.ndarray, spec, z_edges: np.ndarray):
    """Draw one row of per-cell values (nlay, ncol) as a cross-section in km and m."""
    x = np.arange(spec.ncol + 1) * spec.delr / 1000.0
    mesh = ax.pcolormesh(x, z_edges[::-1], values[::-1], shading="flat", cmap=F_CMAP, vmin=0.0,
                         vmax=1.0)
    for depth in z_edges[1:-1]:
        ax.axhline(depth, color="white", lw=0.5)
    return mesh


def fill_section_cell(ax, spec, z_edges: np.ndarray, layer: int, col: int, colour: str) -> None:
    """Fill one cell of a cross-section with one colour."""
    x0 = col * spec.delr / 1000.0
    ax.fill_between([x0, x0 + spec.delr / 1000.0], z_edges[layer + 1], z_edges[layer],
                    color=colour, lw=0, zorder=3)


# ---------------------------------------------------------------- Fig. 10: history matching


def setup_history_match(ws: Path, mf6: Path, h09, hbd) -> dict:
    """Build the truth, observations, pilot points, prior and PEST++ template of tutorial 09."""
    base = hbd.build_quickstart(clean_dir(ws / "base"), mf6)
    base_step = gs.read_step(base.ws, boundnames=True)
    group = {WELL: {"boundnames": [WELL]}}
    smoothing_cells = CORRELATION_LENGTH / (2 * base.spec.delr)  # Gaussian width s: length 2 s
    truth = hbd.build_realisation(clean_dir(ws / "truth"), mf6, TRUTH_SEED, sigma_lnk=SIGMA_LNK,
                                  correlation_cells=smoothing_cells)
    truth_step = gs.read_step(truth.ws, boundnames=True)
    truth_res = gs.backward(truth_step, {WELL: gs.select(truth_step, **group[WELL])})
    spec = base.spec
    obs_cells = h09.observation_cells(spec, N_OBS, OBS_SEED)
    observed = h09.observed_heads(truth.head_file, [spec.node(rc) for rc in obs_cells], NOISE_SD,
                                  NOISE_SEED)
    pp_cells = h09.pilot_point_cells(spec, PP_SPACING)
    pp_cov = h09.pilot_point_covariance(spec, pp_cells, CORRELATION_LENGTH, NUGGET)
    weights = h09.kriging_weights(spec, pp_cells, CORRELATION_LENGTH, NUGGET)
    mean_k = float(spec.k)
    prior_values = h09.draw_prior(pp_cov, mean_k, SIGMA_LNK, N_REAL, PRIOR_SEED)
    template = h09.build_pest_template(clean_dir(ws / "template"), mf6, spec, pp_cells, weights,
                                       obs_cells, mean_k)
    h09.write_prior(template, prior_values)
    k_bounds = (mean_k * np.exp(-4 * SIGMA_LNK), mean_k * np.exp(4 * SIGMA_LNK))
    options = {"ies_parameter_ensemble": "prior.csv", "ies_num_reals": N_REAL,
               "ies_include_base": False}
    h09.build_pst(template, observed, NOISE_SD, mean_k, k_bounds, options, noptmax=N_ITER)
    return {"base": base, "base_step": base_step, "group": group, "truth_step": truth_step,
            "truth_res": truth_res, "obs_cells": obs_cells, "template": template,
            "mean_k": mean_k, "spec": spec, "prior_values": prior_values}


def compute_fig10(work: Path, mf6: Path, pestpp: Path, run_ies: bool = True,
                  n_workers: int = N_WORKERS, tutorial_dir: Path = TUTORIAL_DIR) -> dict:
    """Run tutorial 09's history match (or reuse its PEST++ output) and trace prior and posterior.

    The prior is the drawn pilot-point ensemble itself, as in section 1 of the notebook. PEST++ IES
    starts from it (prior.csv); its iteration-0 file holds the same values to six digits.
    """
    hbd, h09 = tutorial_modules("09_ensembles", tutorial_dir)
    ws = work / "fig10"
    data = setup_history_match(ws, mf6, h09, hbd)
    master = ws / "master"
    if run_ies or not (master / "case.phi.actual.csv").is_file():
        start = time.perf_counter()
        h09.run_ies(data["template"], pestpp, "case.pst", n_workers, master)
        print(f"PEST++ IES with {n_workers} workers: {time.perf_counter() - start:.0f} s")
    config = gs.EnsembleConfig(outputs=("fraction_through",), thresholds=(0.5,), boundnames=True)
    area = data["base_step"].area
    f_truth = data["truth_res"].fraction_through[WELL]
    np.testing.assert_allclose(h09.read_par_ensemble(master, 0).to_numpy(), data["prior_values"],
                               rtol=1e-5)  # PEST++ writes six significant digits
    parameters = {
        "prior": h09.prior_frame(data["prior_values"]),
        "posterior": h09.read_par_ensemble(master, h09.last_iteration(master)),
    }
    ensembles = {}
    for label, pe in parameters.items():
        folders = h09.run_parameter_ensemble(data["template"], clean_dir(ws / label), pe, mf6,
                                             data["mean_k"])
        ens = gs.run_ensemble(folders, data["group"], config)
        table = h09.summarise_realisations(folders, WELL, data["group"][WELL], (0.5,))
        prob = ens.exceedance[0.5]["fraction_through"][WELL]
        ensembles[label] = {
            "prob": prob, "table": table,
            "summary": {**h09.capture_probability_summary(ens, table, area, WELL),
                        **h09.truth_overlap(prob, f_truth, area)},
        }
    data.update({"ensembles": ensembles, "phi": h09.read_phi(master),
                 "truth": h09.capture_summary(data["truth_step"], data["truth_res"], WELL)})
    return data


def fig10_values(data: dict) -> dict:
    """Return the numbers Section 4.9 quotes, from the Fig. 10 data."""
    out = {"truth area F > 0.5 (km2)": data["truth"]["area F > 0.5 (km2)"],
           "truth stream share": data["truth"]["stream share"],
           "prior mean phi": float(data["phi"]["mean"].iloc[0]),
           "posterior mean phi": float(data["phi"]["mean"].iloc[-1])}
    for label, item in data["ensembles"].items():
        summary = item["summary"]
        out[f"{label} area P >= 0.9 (km2)"] = summary["area P >= 0.9 (km2)"]
        out[f"{label} band 0.1 < P < 0.9 (km2)"] = summary["band 0.1 < P < 0.9 (km2)"]
        out[f"{label} stream share 5 %"] = summary["stream share 5 %"]
        out[f"{label} stream share 95 %"] = summary["stream share 95 %"]
        out[f"{label} true zone with P >= 0.5 (%)"] = summary["true zone with P >= 0.5 (%)"]
        out[f"{label} P >= 0.9 inside the true zone (%)"] = summary[
            "area P >= 0.9 inside the true zone (%)"]
    return out


def stream_shares(table: pd.DataFrame) -> pd.Series:
    """Return the stream share of each realisation (0 where the stream gives no water)."""
    return table["share SFR"] if "share SFR" in table else pd.Series(0.0, index=table.index)


def draw_share_spread(ax, shares: dict, truth: float) -> None:
    """Box plot (25 to 75 %, whiskers 5 to 95 %) and jittered dots of the stream share."""
    labels = list(shares)
    stats = []
    for label in labels:  # whiskers at the 5 and 95 % quantiles themselves, as the text quotes
        values = np.asarray(shares[label])
        low, q1, median, q3, high = np.quantile(values, (0.05, 0.25, 0.5, 0.75, 0.95))
        stats.append({"whislo": low, "q1": q1, "med": median, "q3": q3, "whishi": high,
                      "fliers": []})
    ax.bxp(stats, positions=range(len(labels)), widths=0.5, showfliers=False,
           medianprops={"color": mfig.INK, "lw": 0.9}, boxprops={"lw": 0.7},
           whiskerprops={"lw": 0.7}, capprops={"lw": 0.7})
    rng = np.random.default_rng(0)
    for i, label in enumerate(labels):
        values = np.asarray(shares[label])
        ax.plot(i + rng.uniform(-0.13, 0.13, values.size), values, "o", ms=2.4, alpha=0.7,
                color=SHARE_COLOUR, mew=0, zorder=3)
    ax.axhline(truth, color=TRUTH_COLOUR, ls="--", lw=1.0, label="true model")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(0.0, None)


def make_fig10(out_dir: Path, data: dict) -> list[Path]:
    """Fig. 10: prior and posterior probability of contribution (share of realisations with
    F > 0.5) with the true zone, and the stream-share spread."""
    spec, step = data["spec"], data["base_step"]
    truth_grid = gs.export.to_grid(step, data["truth_res"].fraction_through[WELL])[0]
    fig, axes = plt.subplots(1, 3, figsize=(mfig.FULL_WIDTH, 2.75), layout="constrained",
                             gridspec_kw={"width_ratios": [1.0, 1.0, 0.55]})
    titles = {"prior": "(a) prior", "posterior": "(b) posterior"}
    obs_rows, obs_cols = np.array(data["obs_cells"]).T
    x, y = cell_centres_km(spec)
    for i, (ax, (label, text)) in enumerate(zip(axes[:2], titles.items())):
        grid = gs.export.to_grid(step, data["ensembles"][label]["prob"])[0]
        image = draw_field(ax, grid, spec, cmap=PROB_CMAP, vmin=0.0, vmax=1.0)
        lines = draw_contours(ax, grid, spec, PROB_LEVELS, colours=mfig.INK,
                              linestyles=("-",) * 3, linewidth=0.7)
        ax.clabel(lines, fmt="%.1f", fontsize=7, inline_spacing=1, manual=PROB_LABEL_XY[label])
        draw_contours(ax, truth_grid, spec, (0.5,), colours=TRUTH_COLOUR, linestyles=("--",),
                      linewidth=1.1)
        ax.plot(x[obs_cols], y[obs_rows], "o", ms=2.6, mfc="white", mec=mfig.INK, mew=0.4,
                ls="none", zorder=5)
        fill_cells(ax, spec, np.arange(spec.nrow), np.full(spec.nrow, spec.stream_col),
                   colour=mfig.STREAM_COLOUR)
        mark_cell(ax, spec, spec.wells[0][1], WELL_STYLE)
        map_axes(ax, spec, (0, 1, 2), ylabel=i == 0)
        title(ax, text)
    colour_bar(fig, image, axes[:2],
               "probability of contribution\n(the share of realisations with F > 0.5)",
               shrink=0.9, pad=0.02)

    ax = axes[2]
    shares = {label: stream_shares(data["ensembles"][label]["table"]).to_numpy() for label in titles}
    draw_share_spread(ax, shares, data["truth"]["stream share"])
    ax.set_ylabel("stream share of the pumped water (-)")
    ax.legend(loc="upper right")
    title(ax, "(c) stream share")
    return mfig.save(fig, out_dir, "figS3_ensembles")


# ---------------------------------------------------------------- Fig. 11: unit concentration


def compute_fig11(work: Path, mf6: Path) -> dict:
    """Build the Bedekar et al. (2024) model of tutorial 10; track forward and backward in time."""
    hbd, h10 = tutorial_modules("10_unit_concentration")
    run = h10.build_bedekar(clean_dir(work / "fig11") / "model", mf6, n_years=BEDEKAR_YEARS,
                            nstp=BEDEKAR_NSTP)
    reader = gs.open_model(run.ws, boundnames=True)
    start = reader.step_length(reader.steps[0])  # pumping starts after the 1-day steady period
    first, last = reader.read(reader.steps[0]), reader.read(reader.steps[-1])
    destinations = {h10.WELL: {"boundnames": [h10.WELL]}}
    config = gs.TrackingConfig(porosity=BEDEKAR_POROSITY, initial_water=BEDEKAR_INITIAL,
                               volume_mode="gwt")
    fwd = gs.track_forward(reader, BEDEKAR_SOURCES, config, sinks=destinations)
    pumped = h10.sink_volumes(reader, h10.WELL)
    shares = h10.well_shares(fwd.outflow_to[h10.WELL], pumped, fwd.totim, start)[BEDEKAR_GROUPS]
    windows = {}
    for years in BEDEKAR_WINDOWS:
        config_w = gs.TrackingConfig(porosity=BEDEKAR_POROSITY, initial_water=BEDEKAR_INITIAL,
                                     volume_mode="gwt", keep_series=False)
        bwd = gs.track_backward(h10.window(reader, start + years * YEAR), destinations, config_w,
                                sources=BEDEKAR_SOURCES)
        windows[years] = bwd.fraction_through[h10.WELL][0]
    steady = gs.backward(last, {h10.WELL: gs.select(last, boundnames=[h10.WELL])})
    return {"run": run, "spec": h10.SPEC, "first": first, "last": last, "shares": shares,
            "windows": windows, "steady": steady.fraction_through[h10.WELL],
            "budget": h10.package_budget(first), "h10": h10,
            "well_node": run.info["well_node"]}


def fig11_values(data: dict) -> dict:
    """Return the numbers Section 4.10 quotes, from the Fig. 11 data."""
    h10, shares = data["h10"], data["shares"]
    at = h10.series_at_years(shares, PAPER_YEARS)
    paper = PAPER_FIG2.copy()
    paper.insert(0, "storage", 1.0 - paper.sum(axis=1))
    difference = (100.0 * (at - paper)).abs()
    worst = difference.max().idxmax()
    steady_shares = h10.steady_shares(data["last"], h10.WELL, BEDEKAR_PACKAGES)
    lateral = shares["lateral inflow"]
    nlay = 3
    out = {
        "lateral inflow at 25 yr": float(shares["lateral inflow"].iloc[-1]),
        "recharge at 25 yr": float(shares["recharge"].iloc[-1]),
        "stream at 25 yr": float(shares["stream"].iloc[-1]),
        "stream at 1 yr": float(at.loc[1, "stream"]),
        "lateral inflow at 10 yr": float(at.loc[10, "lateral inflow"]),
        "stream at 0.5 yr (%)": 100.0 * float(at.loc[0.5, "stream"]),
        "largest difference from the read-offs (points)": float(difference.to_numpy().max()),
        "year of the largest difference": float(difference[worst].idxmax()),
        "first year with lateral inflow > 0.1 %": float(lateral[lateral > 1e-3].index[0]),
        "steady lateral inflow share": float(steady_shares["lateral inflow"]),
        "steady recharge share": float(steady_shares["recharge"]),
        "steady stream share": float(steady_shares["stream"]),
        "lateral inflow (m3/d)": float(data["budget"].loc["INFLOW", "in"]),
        "recharge (m3/d)": float(data["budget"].loc["RCH", "in"]),
    }
    for years in (1, 25):
        layer2 = data["windows"][years].reshape(nlay, -1)[1]
        out[f"cells w > 0.5, layer 2, {years} yr"] = int((layer2 > 0.5).sum())
    steady = data["steady"].reshape(nlay, -1)
    for k in range(nlay):
        out[f"steady cells F > 0.5, layer {k + 1}"] = int((steady[k] > 0.5).sum())
    return out


def make_fig11(out_dir: Path, data: dict) -> list[Path]:
    """Fig. 11: tracked shares against Bedekar et al. (2024) Fig. 2, and layer-2 backward maps."""
    spec, first, shares = data["spec"], data["first"], data["shares"]
    paper = PAPER_FIG2.copy()
    paper.insert(0, "storage", 1.0 - paper.sum(axis=1))
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 4.3))
    top = fig.add_gridspec(1, 1, left=0.09, right=0.985, top=0.945, bottom=0.6)
    ax = fig.add_subplot(top[0])
    for group in BEDEKAR_GROUPS:
        ax.plot(shares.index, shares[group], color=BEDEKAR_COLOURS[group],
                label=BEDEKAR_LABELS[group])
        ax.plot(paper.index, paper[group], "o", color=BEDEKAR_COLOURS[group], ms=3.5, mfc="none",
                mew=0.8)
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], marker="o", color=mfig.INK, ms=3.5, mfc="none", ls="none"))
    labels.append("Bedekar et al. (2024), Fig. 2")
    ax.legend(handles, labels, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.0),
              handlelength=1.5, columnspacing=1.2)
    ax.set_xlim(0.0, BEDEKAR_YEARS)
    ax.set_ylim(0.0, 1.12)
    ax.set_yticks((0.0, 0.25, 0.5, 0.75, 1.0))
    ax.set_xlabel("time since pumping started (years)")
    ax.set_ylabel("share of the\npumped water (-)")
    title(ax, "(a) Share of the pumped water by source")

    bottom = fig.add_gridspec(1, 5, left=0.09, right=0.9, top=0.44, bottom=0.08, wspace=0.12)
    panels = [(data["windows"][years], f"({'bcde'[i]}) {years} year{'s' * (years > 1)}")
              for i, years in enumerate(BEDEKAR_WINDOWS)]
    panels.append((data["steady"], "(f) steady F"))
    well_rc = node_rc(data["well_node"], spec)
    for i, (values, text) in enumerate(panels):
        ax = fig.add_subplot(bottom[0, i])
        grid = gs.export.to_grid(first, values)[1]  # layer 2
        image = draw_field(ax, grid, spec, cmap=F_CMAP, vmin=0.0, vmax=1.0)
        mark_cell(ax, spec, well_rc, WELL_STYLE)
        map_axes(ax, spec, (0, 0.5, 1), ylabel=i == 0)
        ax.set_xticklabels(["0", "0.5", "1"])
        if i == 0:
            ax.set_yticklabels(["0", "0.5", "1"])
        title(ax, text)
    cax = fig.add_axes((0.915, 0.08, 0.012, 0.3))
    bar = fig.colorbar(image, cax=cax)
    bar.set_label("fraction to the well (-)")
    bar.outline.set_linewidth(0.5)
    return mfig.save(fig, out_dir, "fig11_unit_concentration")


# ---------------------------------------------------------------- driver


def report(values: dict) -> None:
    """Print computed values, rounded for reading."""
    for key, value in values.items():
        print(f"  {key}: {value:.4g}" if isinstance(value, float) else f"  {key}: {value}")


def main(
    out_dir: Path = mfig.FIG_DIR,
    work: Path = WORK_DIR,
    fig7: bool = True,
    fig8: bool = True,
    fig10: bool = True,
    fig11: bool = True,
    run_ies: bool = True,
    tutorial_dir: Path = TUTORIAL_DIR,
    bin_dir: Path = mfig.REPO / "bin",
) -> None:
    """Make Figs 7, 8, 10 and 11; each gate can be switched off. run_ies=False reuses PEST++ output."""
    mfig.paper_style()
    mf6 = mfig.find_mf6(bin_dir)
    start = time.perf_counter()
    gates = (
        (fig7, compute_fig7, fig7_values, QUOTED_FIG7, make_fig7, "Fig. 7"),
        (fig8, compute_fig8, fig8_values, QUOTED_FIG8, make_fig8, "Fig. 8"),
        (fig11, compute_fig11, fig11_values, QUOTED_FIG11, make_fig11, "Fig. 11"),
    )
    for gate, compute, values, quoted, make, name in gates:
        if gate:
            data = compute(work, mf6)
            computed = values(data)
            report(computed)
            check_quoted(computed, quoted, name)
            print("wrote", make(out_dir, data))
    if fig10:
        pestpp = mf6.parent / "pestpp-ies"
        data = compute_fig10(work, mf6, pestpp, run_ies=run_ies, tutorial_dir=tutorial_dir)
        computed = fig10_values(data)
        report(computed)
        check_quoted(computed, QUOTED_FIG10, "Fig. 10")
        print("wrote", make_fig10(out_dir, data))
    print(f"done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
