"""Supporting-information figures S2 and S3: full mixing converges on the advective answer.

One Discussion sentence rests on them: as the cells and time steps get smaller, the numerical
dispersion shrinks, and full mixing approaches the advective answer. Fig. S2 refines the cells,
Fig. S3 the transport time steps.

SI Figure 2 (si_fig2_cell_size), cell size:

- (a-f) Problem A of the dispersion study (studies/dispersion/problems.py, AnalyticSpec: uniform
  regional flow to a pumping well in a confined aquifer, flow at 30 degrees to the grid rows),
  whose reference is the exact analytical capture zone (Javandel and Tsang 1986): the
  full-mixing fraction F to the well on square cells (DIS, a-c) and on smooth Voronoi cells
  (DISV from vorflow, d-f) of nominal size 50, 25 and 12.5 m, with the exact zone edge dashed
  and the cell edges drawn faintly (read from the study's binary grid files).
- (g, h) Against the mean cell size h, from the study's metric table: the width of the band
  where 0.1 < F < 0.9 and the relative difference of the F > 0.5 area from the exact zone, on
  DIS and DISV, with flow along the grid rows (solid) and at 30 degrees to them (dotted). The
  axis starts at 100 m; the 200 m grids, 10 cells across the 2 km domain, miss the zone by
  38 to 47 %.

SI Figure 3 (si_fig3_time_steps), one panel: the seasonal transient model of main-text Example D (30
years, one flow step per season), new recharge tracked forward to the supply well with 1, 4, 16
and 64 transport sub-steps per flow step; the share of new recharge in the well's water per flow
step over the first three years.

Fig. S2 is redrawn from studies/dispersion/output (nothing rerun); Fig. S3 builds and runs the
model under $TMPDIR and deletes it. Run from the repository root with the tutorials of the SFR stream
model (as studies/paper/synthetic_figures.py):

    PYTHONPATH=src:<sfr worktree>/tutorials python studies/paper/si_convergence_figure.py
"""

import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (style, palette, save)

sys.path.insert(0, str(mfig.DISPERSION_DIR))

import analysis as an  # noqa: E402  (dispersion study: analytical divide)
import flopy  # noqa: E402
import gwsource as gs  # noqa: E402
import herebedragons as hbd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import problems as pb  # noqa: E402  (dispersion study: problem specs)

CELL_FIG_NAME = "si_fig2_cell_size"
STEP_FIG_NAME = "si_fig3_time_steps"
FULL_WIDTH = 17.15 / 2.54  # in, full page width
COLUMN_WIDTH = 8.5 / 2.54  # in, one column
OUT_DIR = mfig.REPO.parents[2] / "docs" / "paper" / "overleaf" / "si_2026-10-29" / "fig" / "si"
DISPERSION_OUT = mfig.DISPERSION_DIR / "output"
WORK_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "si_convergence_figure"
F_CMAP = "viridis"  # as the main-text F maps
MAP_ANGLE = 30.0  # degrees, flow direction of the maps (the harder case)
MAP_SIZES = (50.0, 25.0, 12.5)
SIZES = (100.0, 50.0, 25.0, 12.5)
GRIDS = {  # kind: (colour, marker, label)
    "DIS": (mfig.OKABE_ITO["blue"], "o", "square cells (DIS)"),
    "DISV": (mfig.OKABE_ITO["green"], "D", "Voronoi cells (DISV)"),
}
ANGLES = ((0.0, "-", "flow along rows"), (30.0, ":", "flow at 30° to rows"))
CELL_EDGE = dict(colors="#808080", linewidths=0.2, alpha=0.5)
DASH = (0, (3, 1.5))
AREA_LIM = 14.0  # %, y range of panel (h): DISV at 100 m and 30 degrees is -12.8 %
WELL = "supply_well"
POROSITY = 0.3
N_YEARS = 30
SUBSTEPS = (1, 4, 16, 64)
SUBSTEP_COLOURS = ("#fde725", "#35b779", "#31688e", "#440154")  # viridis, coarse to fine
T_MAX_YR = 3.0
YEAR = 365.25  # d


# ---------------------------------------------------------------- Fig. S3 model run


def track_new_recharge(work: Path, mf6: Path, substeps: tuple = SUBSTEPS,
                       n_years: int = N_YEARS, porosity: float = POROSITY,
                       well: str = WELL) -> tuple[pd.DataFrame, np.ndarray]:
    """Share of new recharge in the well's water per flow step for each number of sub-steps.

    Returns the shares (one column per sub-step count) and the flow-step edges in years.
    """
    run = hbd.build_transient(work / "transient", mf6, n_years=n_years, steps_per_season=1)
    reader = gs.open_model(run.ws, boundnames=True)
    pumped = well_volumes(reader, well)
    sinks = {well: {"boundnames": [well]}}
    shares = {}
    for m in substeps:
        config = gs.TrackingConfig(porosity=porosity, substeps=m, keep_series=True)
        fwd = gs.track_forward(reader, {"recharge": {"package": "RCH"}}, config, sinks=sinks)
        shares[m] = fwd.outflow_to[well]["recharge"] / pumped
    edges = np.concatenate([[0.0], fwd.totim]) / YEAR
    return pd.DataFrame(shares), edges


def well_volumes(reader, well: str) -> np.ndarray:
    """Return the volume pumped by the well in every flow step (m3)."""
    volumes = []
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        rate = -float(step.term_flow[gs.select(step, boundnames=[well]).terms].sum())
        volumes.append(rate * reader.step_length(kstpkper))
    return np.asarray(volumes)


# ---------------------------------------------------------------- maps


def grb_file(models_dir: Path, kind: str, h: float, angle: float = MAP_ANGLE) -> Path:
    """Return the binary grid file of one problem A run of the dispersion study."""
    return models_dir / f"a{angle:g}_{kind}_{h:g}" / f"a_{kind.lower()}.{kind.lower()}.grb"


def draw_cell_edges(ax: plt.Axes, grb: Path) -> None:
    """Draw the cell outlines of a model grid faintly."""
    modelgrid = flopy.mf6.utils.MfGrdFile(str(grb), verbose=False).modelgrid
    flopy.plot.PlotMapView(modelgrid=modelgrid, ax=ax).plot_grid(**CELL_EDGE)


def map_axes(ax: plt.Axes, spec: pb.AnalyticSpec) -> None:
    """Whole domain, equal aspect, km ticks and thin spines."""
    ax.set_xlim(0, spec.lx)
    ax.set_ylim(0, spec.ly)
    ax.set_aspect("equal", adjustable="box")
    ticks = (0, 1000, 2000)
    ax.set_xticks(ticks, [f"{t / 1000:g}" for t in ticks])
    ax.set_yticks(ticks, [f"{t / 1000:g}" for t in ticks])
    ax.tick_params(length=2, pad=1.5)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)


def draw_map(ax: plt.Axes, field: np.ndarray, grb: Path, spec: pb.AnalyticSpec):
    """One F map of problem A with cell edges, the exact capture-zone edge and the well."""
    image = ax.imshow(field, origin="lower", extent=(0, spec.lx, 0, spec.ly), cmap=F_CMAP,
                      vmin=0, vmax=1, interpolation="nearest")
    draw_cell_edges(ax, grb)
    ax.plot(*an.divide_line(spec), color="white", lw=1.0, ls=DASH)
    ax.plot(spec.well_x, spec.well_y, "o", ms=4, mfc="white", mec=mfig.INK, mew=0.6)
    map_axes(ax, spec)
    return image


def draw_maps(axes, maps: dict, models_dir: Path, sizes: tuple = MAP_SIZES,
              grids: dict = GRIDS, angle: float = MAP_ANGLE):
    """Panels (a-f): full mixing on square (top) and Voronoi (bottom) cells of each size."""
    spec = pb.AnalyticSpec(angle_deg=angle)
    letters = iter("abcdef")
    for row, (kind, (_, _, row_label)) in zip(axes, grids.items()):
        for ax, h in zip(row, sizes):
            image = draw_map(ax, maps[f"{angle:g}_{kind}_{h:g}_mixing"],
                             grb_file(models_dir, kind, h, angle), spec)
            ax.set_title(f"({next(letters)}) {h:g} m", loc="left")
        row[0].set_ylabel(f"{row_label}\ny (km)")
        for ax in row[1:]:
            ax.set_yticklabels([])
    for ax in axes[0]:
        ax.set_xticklabels([])
    for ax in axes[1]:
        ax.set_xlabel("x (km)")
    return image


# ---------------------------------------------------------------- line panels


def size_axis(ax: plt.Axes, sizes: tuple = SIZES) -> None:
    """Log cell-size axis, finest on the right."""
    ax.set_xscale("log")
    ax.set_xticks(sizes, [f"{s:g}" for s in sizes])
    ax.set_xticks([], minor=True)
    ax.set_xlim(sizes[0] * 1.3, sizes[-1] * 0.8)
    ax.set_xlabel("mean cell size h (m)")
    ax.grid(True, color=mfig.GRID, lw=0.5)
    ax.set_axisbelow(True)


def draw_metric(ax: plt.Axes, table: pd.DataFrame, column: str, scale: float = 1.0,
                grids: dict = GRIDS, angles: tuple = ANGLES, sizes: tuple = SIZES) -> None:
    """One full-mixing metric against the mean cell size per grid kind and flow direction."""
    rows = table[(table.method == "mixing") & (table.h <= max(sizes))]
    for kind, (colour, marker, _) in grids.items():
        for angle, ls, _ in angles:
            sel = rows[(rows.kind == kind) & (rows.angle == angle)].sort_values("mean_h")
            ax.plot(sel.mean_h, sel[column] * scale, color=colour, marker=marker, ms=3.5,
                    lw=1.4, ls=ls)
    size_axis(ax)


def draw_band(ax: plt.Axes, table: pd.DataFrame) -> None:
    """Panel (g): width of the 0.1 < F < 0.9 band, with an h^0.5 guide."""
    draw_metric(ax, table, "band_width")
    ax.set_yscale("log")
    h = np.array([100.0, 12.5])
    guide = 520.0 * (h / 100.0) ** 0.5
    ax.plot(h, guide, color="#999999", lw=0.9, ls=(0, (5, 2)))
    ax.text(h[-1], guide[-1] * 1.12, "$h^{0.5}$", color=mfig.MUTED, fontsize=7, ha="center",
            va="bottom")
    mfig.plain_log_ticks(ax, (100, 200, 500))
    ax.set_ylim(80, 700)
    ax.set_ylabel("band width (m)")
    ax.set_title("(g) 0.1 < F < 0.9 band", loc="left")


def draw_area(ax: plt.Axes, table: pd.DataFrame, lim: float = AREA_LIM) -> None:
    """Panel (h): relative difference of the F > 0.5 area from the exact zone (%)."""
    ax.axhspan(-5, 5, color="#eeeeee", zorder=0)
    ax.axhline(0.0, color=mfig.MUTED, lw=0.6)
    draw_metric(ax, table, "area_err_0.5", scale=100.0)
    ax.set_ylim(-lim, lim)
    ax.set_yticks(np.arange(-12, 13, 4))
    ax.set_ylabel("F > 0.5 area vs exact zone (%)")
    ax.set_title("(h) F > 0.5 area", loc="left")


def draw_steps(ax: plt.Axes, shares: pd.DataFrame, edges: np.ndarray,
               colours: tuple = SUBSTEP_COLOURS, t_max: float = T_MAX_YR) -> None:
    """Fig. S3: share of new recharge in the well's water per flow step."""
    for colour, m in zip(colours, shares.columns):
        ax.stairs(shares[m].to_numpy(), edges, color=colour, lw=1.4, label=f"{m}")
    in_window = edges[1:] <= t_max + 1e-9
    ax.set_xlim(0, t_max)
    ax.set_ylim(0, 1.1 * float(shares[in_window].to_numpy().max()))
    ax.set_xticks(np.arange(0, t_max + 0.1, 1.0))
    ax.grid(True, color=mfig.GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.set_xlabel("time (years)")
    ax.set_ylabel("new recharge in the well (-)")
    ax.legend(title="sub-steps per\n~91-day flow step", loc="upper left", handlelength=1.6,
              title_fontsize=7, borderaxespad=0.2)


def legend_handles(grids: dict = GRIDS, angles: tuple = ANGLES) -> list:
    """Shared legend of (g) and (h): grid kinds by colour and marker, flow direction by line."""
    handles = [plt.Line2D([], [], color=c, marker=m, ms=3.5, lw=1.4, label=f"full mixing, {lab}")
               for c, m, lab in grids.values()]
    handles += [plt.Line2D([], [], color=mfig.MUTED, ls=ls, lw=1.2, label=lab)
                for _, ls, lab in angles]
    return handles


def make_cell_size_figure(out_dir: Path, maps: dict, models_dir: Path,
                          table: pd.DataFrame) -> list[Path]:
    """Draw Fig. S2 (maps and metrics against cell size) and save PNG and PDF."""
    mfig.paper_style()
    fig = plt.figure(figsize=(FULL_WIDTH, 7.6), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(1.9, 1.15), hspace=0.03)
    map_axes_ = top.subplots(2, 3, gridspec_kw={"wspace": 0.03, "hspace": 0.03})
    image = draw_maps(map_axes_, maps, models_dir)
    top.colorbar(image, ax=map_axes_, shrink=0.6, aspect=22, pad=0.01, ticks=(0, 0.5, 1),
                 label="F (-)")
    ax_band, ax_area = bottom.subplots(1, 2, gridspec_kw={"wspace": 0.08})
    draw_band(ax_band, table)
    draw_area(ax_area, table)
    bottom.legend(handles=legend_handles(), loc="outside lower center", ncol=4,
                  handlelength=2.2)
    return mfig.save(fig, out_dir, CELL_FIG_NAME)


def make_time_step_figure(out_dir: Path, shares: pd.DataFrame, edges: np.ndarray,
                          width: float = COLUMN_WIDTH) -> list[Path]:
    """Draw Fig. S3 (one panel, time steps) and save PNG and PDF."""
    mfig.paper_style()
    fig, ax = plt.subplots(figsize=(width, 2.6), layout="constrained")
    draw_steps(ax, shares, edges)
    return mfig.save(fig, out_dir, STEP_FIG_NAME)


# ---------------------------------------------------------------- numbers and driver


def print_numbers(table: pd.DataFrame, steps: pd.DataFrame, edges: np.ndarray) -> None:
    """Print every number the caption or text could quote."""
    out = table[table.method == "mixing"].copy()
    out["area_err_0.5"] *= 100.0
    columns = ["kind", "angle", "h", "mean_h", "n_cells", "band_width", "area_err_0.5"]
    print(out[columns].round(2).to_string(index=False))
    lengths = np.diff(edges)[1:] * YEAR
    print(f"mean flow step {lengths.mean():.2f} d")
    print(steps.iloc[1:5].round(4).set_axis([f"step {n}" for n in range(1, 5)]))
    first = steps.iloc[1]
    print({f"m = {m} / m = {steps.columns[-1]}": round(first[m] / first.iloc[-1], 3)
           for m in steps.columns[:2]})


def main(out_dir: Path = OUT_DIR, dispersion_out: Path = DISPERSION_OUT,
         work: Path = WORK_DIR) -> list[Path]:
    """Track new recharge, print the numbers and draw Figs S2 and S3; delete the workspace."""
    maps = dict(np.load(dispersion_out / "a_maps.npz"))
    table = pd.read_csv(dispersion_out / "a_metrics.csv")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    steps, edges = track_new_recharge(work, mfig.find_mf6())
    shutil.rmtree(work, ignore_errors=True)
    print_numbers(table, steps, edges)
    return (make_cell_size_figure(out_dir, maps, dispersion_out / "models", table)
            + make_time_step_figure(out_dir, steps, edges))


if __name__ == "__main__":
    t0 = time.perf_counter()
    print(main())
    print(f"{time.perf_counter() - t0:.1f} s")
