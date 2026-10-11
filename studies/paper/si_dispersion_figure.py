"""Supporting-information figure S1 of the paper: numerical dispersion maps and time steps.

Main-text Fig. 3 gives the dispersion metrics against cell size; this figure shows the maps
behind them and the time-step test, redrawn from the dispersion study's outputs
(studies/dispersion/output: a_maps.npz, b_maps.npz, t_curves.csv; docs/dispersion_study.md
Figs 1, 3 and 5). Nothing is rerun.

- (a-h) Problem A, uniform flow to a well, 50 m cells, flow along the grid rows (a-d) and at 30
  degrees to them (e-h): the analytical capture zone averaged over the cells (the best any
  cell-based method can do on that grid), then full mixing on DIS, face routing on DIS and full
  mixing on DISV, with the analytical capture-zone edge dashed.
- (i-l) Problem B, recharge to a well beside a gaining river: PRT particles on the 12.5 m grid
  (the reference), then the three methods on 50 m cells, with the reference F = 0.5 edge
  dashed. Only the area west of the river (x < 1.1 km) enters the metrics.
- (m-n) Problem B's steady flows held for 2,000-day flow steps, all water entering after t = 0
  tagged: the share of that new water in the well per flow step on the 12.5 m grid with 1, 4, 16
  and 64 transport sub-steps per flow step and with PRT (m), and the difference to PRT (n).

The numbers the SI text quotes are in QUOTED and asserted before plotting. Sizes follow
studies/paper/method_figures.py: double column 7 in, fonts 7 to 8 pt, PNG at 300 dpi and PDF.
Run from the repository root:

    PYTHONPATH=src python studies/paper/si_dispersion_figure.py
"""

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
import matplotlib.pyplot as plt  # noqa: E402
import problems as pb  # noqa: E402  (dispersion study: problem specs)

FIG_NAME = "figS1_numerical_dispersion"
H_MAP = 50.0  # cell size of the method maps (m)
H_STEPS = 12.5  # grid of the time-step panels (m)
SUBSTEPS = (1, 4, 16, 64)
STEP_D = 2000.0  # flow step of the time-step test (d)
T_MAX_D = 20000.0  # plotted time window (d)
B_X0 = 500.0  # problem B maps start at x = 500 m, as in the study
A_METHODS = (  # (map key suffix, panel title)
    ("DIS_{h:g}_cell_average", "exact, cell-averaged"),
    ("DIS_{h:g}_mixing", "full mixing, DIS"),
    ("DIS_{h:g}_routing", "face routing, DIS"),
    ("DISV_{h:g}_mixing", "full mixing, DISV"),
)
B_METHODS = (
    ("ref", "PRT, 12.5 m cells"),
    ("DIS_{h:g}_mixing", "full mixing, DIS"),
    ("DIS_{h:g}_routing", "face routing, DIS"),
    ("DISV_{h:g}_mixing", "full mixing, DISV"),
)
SUBSTEP_COLORS = ("#9ecae1", "#4a90c8", "#0072B2", "#08306b")
# Values the SI text quotes (DS §3); the plot must round to them. The difference is the mean
# absolute difference to PRT over all 30 flow steps.
QUOTED = {"share 1 sub-step": 0.18, "share PRT": 0.09, "mean diff 16 sub-steps": 0.001}


def check_quoted(curves: pd.DataFrame, quoted: dict = QUOTED) -> None:
    """Assert the first-step shares and the 16-sub-step difference against the SI text."""
    prt = curves[curves.method == "particles"].fraction.to_numpy()
    one = curves[curves.method == "substeps_1"].fraction.to_numpy()
    sixteen = curves[curves.method == "substeps_16"].fraction.to_numpy()
    assert_quoted(one[0], quoted["share 1 sub-step"], "share 1 sub-step")
    assert_quoted(prt[0], quoted["share PRT"], "share PRT")
    assert_quoted(np.abs(sixteen - prt).mean(), quoted["mean diff 16 sub-steps"],
                "mean diff 16 sub-steps")


def assert_quoted(value: float, doc: float, what: str) -> None:
    """Assert that a value rounds to the quoted number (to the quoted decimals)."""
    digits = len(f"{doc}".split(".")[-1])
    assert abs(value - doc) <= 0.5 * 10.0**-digits + 1e-12, f"{what}: {value:.4f}, quoted {doc}"


def map_axes(ax: plt.Axes, xlim: tuple, ylim: tuple, xticks: tuple, yticks: tuple, left: bool,
             bottom: bool) -> None:
    """Set km ticks on a map; tick labels only on the left column and the bottom row."""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(xticks, [f"{t / 1000:g}" for t in xticks] if bottom else [])
    ax.set_yticks(yticks, [f"{t / 1000:g}" for t in yticks] if left else [])
    ax.tick_params(length=2, pad=1.5)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)


def draw_fraction(ax: plt.Axes, field: np.ndarray, extent: tuple):
    """Draw one fraction map (raster, row 0 at y = 0)."""
    return ax.imshow(field, origin="lower", extent=extent, cmap=mfig.F_CMAP, vmin=0, vmax=1,
                     interpolation="nearest")


def draw_problem_a(axes, maps: dict, angle: float, letters: str, h: float = H_MAP,
                   bottom: bool = False):
    """One row of problem A maps for one flow direction, with the analytical zone edge."""
    spec = pb.AnalyticSpec(angle_deg=angle)
    extent = (0, spec.lx, 0, spec.ly)
    dx, dy = an.divide_line(spec)
    for n, (ax, letter, (key, title)) in enumerate(zip(axes, letters, A_METHODS)):
        image = draw_fraction(ax, maps[f"{angle:g}_" + key.format(h=h)], extent)
        ax.plot(dx, dy, color=mfig.INK, lw=0.8, ls=(0, (3, 1.5)))
        ax.plot(spec.well_x, spec.well_y, "o", ms=2.5, color=mfig.INK)
        map_axes(ax, (0, spec.lx), (0, spec.ly), (0, 1000, 2000), (0, 1000, 2000), n == 0,
                 bottom)
        ax.set_title(f"({letter}) {title}", loc="left")
    return image


def draw_problem_b(axes, maps: dict, letters: str, h: float = H_MAP, x0: float = B_X0):
    """The row of problem B maps: PRT reference and the methods, reference F = 0.5 edge."""
    spec = pb.Model1Spec()
    extent = (0, spec.lx, 0, spec.ly)
    ref = maps["ref"]
    x = np.linspace(0, spec.lx, ref.shape[1] + 1)
    y = np.linspace(0, spec.ly, ref.shape[0] + 1)
    xc, yc = 0.5 * (x[1:] + x[:-1]), 0.5 * (y[1:] + y[:-1])
    for n, (ax, letter, (key, title)) in enumerate(zip(axes, letters, B_METHODS)):
        draw_fraction(ax, maps[key.format(h=h)], extent)
        ax.contour(xc, yc, ref, levels=[0.5], colors=mfig.INK, linewidths=0.8,
                   linestyles=[(0, (3, 1.5))])
        ax.axvline(spec.riv_x, color=mfig.MUTED, lw=1.0)
        ax.plot(spec.well_x, spec.well_y, "o", ms=2.5, color=mfig.INK)
        map_axes(ax, (x0, spec.lx), (0, spec.ly), (500, 1000, 1500), (0, 500, 1000), n == 0,
                 True)
        ax.set_title(f"({letter}) {title}", loc="left")
        ax.set_xlabel("x (km)")


def step_edges(curves: pd.DataFrame) -> np.ndarray:
    """Return the flow-step edges in 1000 d, starting at 0."""
    ends = curves[curves.method == "particles"].t.to_numpy() / 1000
    return np.concatenate([[0.0], ends])


def draw_steps(ax_share: plt.Axes, ax_diff: plt.Axes, curves: pd.DataFrame,
               substeps: tuple = SUBSTEPS, colors: tuple = SUBSTEP_COLORS,
               step_d: float = STEP_D, t_max: float = T_MAX_D) -> None:
    """(m) share of new water in the well per flow step; (n) its difference to PRT."""
    edges = step_edges(curves)
    prt = curves[curves.method == "particles"].fraction.to_numpy()
    for color, n_sub in zip(colors, substeps):
        f = curves[curves.method == f"substeps_{n_sub}"].fraction.to_numpy()
        label = (f"{n_sub} sub-steps of {step_d / n_sub:,.0f} d" if n_sub > 1
                 else f"1 step per flow step ({step_d:,.0f} d)")
        ax_share.stairs(f, edges, color=color, lw=1.4, label=label)
        ax_diff.stairs(f - prt, edges, color=color, lw=1.4)
    ax_share.stairs(prt, edges, color=mfig.INK, ls=(0, (3, 1.5)), lw=1.0, label="PRT particles")
    ax_diff.axhline(0.0, color=mfig.INK, ls=(0, (3, 1.5)), lw=0.8)
    for ax in (ax_share, ax_diff):
        ax.set_xlim(0, t_max / 1000)
        ax.set_xticks(np.arange(0, t_max / 1000 + 1, 4))
        ax.grid(True, color=mfig.GRID, lw=0.5)
        ax.set_axisbelow(True)
        ax.set_xlabel("time since tagging started (1,000 d)")
    ax_share.set_ylim(0, 1)
    ax_share.set_ylabel("share of new water\nin the well's water")
    ax_diff.set_ylabel("difference to PRT")
    ax_share.set_title(f"(m) new water in the well, {H_STEPS:g} m cells", loc="left")
    ax_diff.set_title("(n) difference to PRT", loc="left")


def make_figS1(fig_dir: Path, a_maps: dict, b_maps: dict, curves: pd.DataFrame) -> list[Path]:
    """Fig. S1: problem A and B maps at 50 m, and the transport time-step test."""
    mfig.paper_style()
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 7.5), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(2.85, 1.05), hspace=0.02)
    axes = top.subplots(3, 4, gridspec_kw={"hspace": 0.02, "wspace": 0.02})
    image = draw_problem_a(axes[0], a_maps, 0.0, "abcd")
    draw_problem_a(axes[1], a_maps, 30.0, "efgh", bottom=True)
    draw_problem_b(axes[2], b_maps, "ijkl")
    labels = ("problem A, flow along\nthe rows: y (km)", "problem A, flow at 30°\nto the rows: y (km)",
              "problem B: y (km)")
    for ax, label in zip(axes[:, 0], labels):
        ax.set_ylabel(label)
    top.colorbar(image, ax=axes, shrink=0.5, aspect=25, pad=0.01,
                 label="F, fraction of the water in the cell that reaches the well")
    ax_share, ax_diff = bottom.subplots(1, 2)
    draw_steps(ax_share, ax_diff, curves)
    handles, names = ax_share.get_legend_handles_labels()
    ax_diff.legend(handles, names, loc="upper right", handlelength=1.8, borderaxespad=0.2)
    return mfig.save(fig, fig_dir, FIG_NAME)


def main(fig_dir: Path = mfig.FIG_DIR, dispersion_out: Path = mfig.DISPERSION_DIR / "output",
         h_steps: float = H_STEPS) -> list[Path]:
    """Make Fig. S1 in fig_dir from the dispersion study's outputs; return the paths."""
    a_maps = dict(np.load(dispersion_out / "a_maps.npz"))
    b_maps = dict(np.load(dispersion_out / "b_maps.npz"))
    curves = pd.read_csv(dispersion_out / "t_curves.csv")
    curves = curves[curves.h == h_steps]
    check_quoted(curves)
    return make_figS1(fig_dir, a_maps, b_maps, curves)


if __name__ == "__main__":
    t0 = time.perf_counter()
    print(main())
    print(f"{time.perf_counter() - t0:.1f} s")
