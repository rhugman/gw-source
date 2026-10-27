"""Method and verification figures of the paper (Figs 1 to 3, Table S1); outline in docs/paper/outline.md.

- Fig. 1, method schematic, one idea per panel and no tutorial names in the figure. (a) One
  cell with intercell flows, recharge and a well, and the definitions of total inflow I, total
  outflow O and residual r. (b) An eight-cell graph in plan view with the backward fraction F
  to a well, computed by gwsource on a hand-built FlowStep (gross accounting); every arrow is
  numbered by its flow in m3/d, read from the FlowStep (F = 6/11 in the well cell). (c) The
  water credited to a weak-sink well under gross and net accounting (5.0 vs 33.7 m3/d),
  recomputed by building and tracing the layered model of tutorial 02. (d) A snapshot treats
  storage release as a source term of unknown origin; transient tracking carries the cell's
  stored water from the end of one step into the next (symbolic, no numbers). The quoted
  numbers are asserted in check_fig1_numbers().
- Table S1 (supporting information) and Fig. 2, verification. studies/paper/verification.py
  runs the exact checks over the synthetic test models 1 to 10 (and the hand-built network of
  the sub-step test) and records the error reached per model and check; Fig. 2 plots them on
  a log scale with machine precision and the test tolerances, in two blocks: steady and
  snapshot checks, transient tracking checks.
- Fig. 3, numerical dispersion. The two convergence figures of docs/dispersion_study.md
  (problem A, analytical reference; problem B, PRT reference) are merged into one figure of two
  rows: the band width carries the h^0.5 message, the F > 0.1 area error the "conservative
  but too large" message and the F > 0.5 area error the "within 5 % for h <= 50 m" message.
  It is redrawn from the study's metric tables (studies/dispersion/output) with the study's
  own axis helper and labels.

Sizes follow Groundwater: double column 7 in, fonts 7 pt or larger, PNG at 300 dpi and PDF.
Colours are the Okabe-Ito set (colour-blind safe), with markers as a second cue. Run as
`python studies/paper/method_figures.py` from the repository root; model workspaces go to
studies/paper/output (git-ignored).
"""

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

import gwsource as gs  # noqa: E402

PAPER_DIR = Path(__file__).resolve().parent
REPO = PAPER_DIR.parents[1]
FIG_DIR = REPO / "docs" / "paper" / "figures"
WORK_DIR = PAPER_DIR / "output"
DISPERSION_DIR = REPO / "studies" / "dispersion"
TUTORIAL_DIR = REPO / "tutorials"

FULL_WIDTH = 7.0  # in, Groundwater double column
DPI = 300
INK, MUTED, GRID = "#000000", "#555555", "#dddddd"
OKABE_ITO = {
    "black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73",
    "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7",
}
F_CMAP = LinearSegmentedColormap.from_list(
    "f_blues", ["#ffffff", "#d6e6f4", "#8fbfe0", "#4a90c8", "#0072B2", "#08306b"]
)
MACHINE_EPS = float(np.finfo(float).eps)


def paper_style() -> None:
    """Set a plain journal style: white background, 8 pt text, 7 pt ticks and legends."""
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "legend.fontsize": 7, "axes.edgecolor": MUTED,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "lines.linewidth": 1.4, "mathtext.fontset": "dejavusans", "pdf.fonttype": 42,
    })


def save(fig, out_dir: Path, name: str) -> list[Path]:
    """Save a figure as PNG (300 dpi) and PDF; return the paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{name}.png", out_dir / f"{name}.pdf"]
    for path in paths:
        fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return paths


def panel_label(ax, text: str, x: float = 0.0, y: float = 1.0) -> None:
    """Write a bold panel label such as '(a)' at the top left of an axes."""
    ax.text(x, y, text, transform=ax.transAxes, fontweight="bold", ha="left", va="top")


# ---------------------------------------------------------------- Fig. 1: hand-built graph

GRAPH_SHAPE = (2, 4)  # rows, columns of the panel (b) graph; cell id = row * 4 + col
GRAPH_EDGES = (  # (from, to, flow): water moves east to a well (cell 6) and a river (column 3)
    (0, 1, 4.0), (0, 4, 1.0), (4, 5, 6.0), (1, 2, 3.0), (1, 5, 2.0), (5, 6, 9.0),
    (2, 3, 3.0), (2, 6, 1.0), (6, 7, 5.0),
)
GRAPH_TERMS = (  # (cell, package, flow): + into the cell, - out of it
    (0, "CHD", 4.0), (4, "CHD", 4.0),
    *((c, "RCH", 1.0) for c in range(8)),
    (6, "WEL", -6.0), (3, "RIV", -4.0), (7, "RIV", -6.0),
)


def graph_step(edges: tuple = GRAPH_EDGES, terms: tuple = GRAPH_TERMS,
               n_cells: int = 8) -> gs.FlowStep:
    """Return the panel (b) graph as a FlowStep with intercell edges and external terms."""
    names = list(dict.fromkeys(pkg for _, pkg, _ in terms))
    packages = [gs.Package(name, name) for name in names]
    src, dst, q = zip(*edges)
    cells, pkgs, flows = zip(*terms)
    return gs.from_edges(
        n_cells, src, dst, q, term_cell=cells, term_flow=flows,
        term_package=[names.index(p) for p in pkgs], packages=packages,
    )


def graph_fractions(step: gs.FlowStep) -> tuple[np.ndarray, float, float]:
    """Return F to the well (gross), the well inflow and the closure error on the graph."""
    res = gs.backward(step, {"well": gs.select(step, package="WEL")})
    check = gs.diagnostics.backward_closure(step, res, "well")
    assert abs(check.error) < 1e-12, check
    return res.fraction_through["well"], res.destination_inflow["well"], check.error


# ---------------------------------------------------------------- Fig. 1: tutorial 02 numbers


def weak_sink_numbers(work: Path, mf6_exe: Path) -> dict[str, float]:
    """Build tutorial 02's layered model and return the weak well's gross and net accounting."""
    if str(TUTORIAL_DIR) not in sys.path:
        sys.path.insert(0, str(TUTORIAL_DIR))
    import herebedragons as hbd

    run = hbd.build_layered(work / "tutorial02_layered", mf6_exe)
    step = gs.read_step(run.ws, boundnames=True)
    cell = run.info["weak_well_node"]
    wells = {"weak": gs.select(step, boundnames=["weak_well"])}
    gross = gs.backward(step, wells)
    net = gs.backward(step, wells, gs.TraceConfig(accounting="net"))
    budget = gs.cell_budget(step)
    return {
        "pumping": float(-step.term_flow[wells["weak"].terms].sum()),
        "cell_inflow": float(budget.inflow[cell]),
        "passed_on": float(budget.edge_out[cell]),
        "f_gross": float(gross.fraction_through["weak"][cell]),
        "f_net": float(net.fraction_through["weak"][cell]),
        "attributed_gross": float(gross.volume_from["weak"].sum()),
        "attributed_net": float(net.volume_from["weak"].sum()),
    }


# ---------------------------------------------------------------- Fig. 1: drawing


def arrow(ax, start, end, colour: str = INK, width: float = 1.2, style: str = "-|>",
          **kwargs) -> None:
    """Draw a straight arrow in data coordinates."""
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=9, color=colour,
                                 linewidth=width, shrinkA=0, shrinkB=0, **kwargs))


def cell_box(ax, xy: tuple[float, float], size: float, face: str = "white", **kwargs) -> None:
    """Draw a square cell centred on xy."""
    ax.add_patch(Rectangle((xy[0] - size / 2, xy[1] - size / 2), size, size, facecolor=face,
                           edgecolor=INK, linewidth=1.0, **kwargs))


def blank_axes(ax, xlim: tuple, ylim: tuple) -> None:
    """Set equal-aspect limits and hide the axes frame."""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_single_cell(ax) -> None:
    """Panel (a): cell i with intercell in- and outflows, a source and a sink term."""
    blue, red = OKABE_ITO["blue"], OKABE_ITO["vermillion"]
    for xy, name in (((-1.6, 0.0), "$j$"), ((1.6, 0.0), "$k$")):
        cell_box(ax, xy, 0.8, face="#f2f2f2", linestyle="--")
        ax.text(*xy, name, ha="center", va="center", fontsize=9)
    cell_box(ax, (0.0, 0.0), 1.2)
    ax.text(0.0, -0.05, "$i$", ha="center", va="center", fontsize=10)
    arrow(ax, (-1.2, -0.05), (-0.6, -0.05), INK)
    ax.text(-0.9, 0.05, "$q_{ji}$", ha="center", va="bottom", fontsize=7)
    arrow(ax, (0.6, -0.05), (1.2, -0.05), INK)
    ax.text(0.9, 0.05, "$q_{ik}$", ha="center", va="bottom", fontsize=7)
    arrow(ax, (-0.3, 1.25), (-0.3, 0.6), blue, width=1.4)
    ax.text(-0.42, 0.95, "recharge", ha="right", va="center", fontsize=7, color=blue)
    arrow(ax, (0.3, 0.6), (0.3, 1.25), red, width=1.4)
    ax.text(0.42, 0.95, "well $d_i$", ha="left", va="center", fontsize=7, color=red)
    lines = ("$I_i = \\Sigma_j\\, q_{ji}$ + sources",
             "$O_i = \\Sigma_k\\, q_{ik}$ + sinks",
             "$r_i = I_i - O_i$")
    for n, line in enumerate(lines):
        ax.text(-1.95, -1.0 - 0.42 * n, line, ha="left", va="center", fontsize=7.5)
    blank_axes(ax, (-2.05, 2.05), (-2.05, 1.6))


def graph_positions(shape: tuple[int, int] = GRAPH_SHAPE, spacing: float = 1.5) -> np.ndarray:
    """Return (x, y) of each graph cell; row 0 on top."""
    rows, cols = np.divmod(np.arange(shape[0] * shape[1]), shape[1])
    return np.column_stack([cols * spacing, -rows * spacing])


def term_cells(terms: tuple, package: str) -> list[int]:
    """Return the cells of the graph terms of one package, in order."""
    return [cell for cell, pkg, _ in terms if pkg == package]


def step_edges(step: gs.FlowStep) -> tuple:
    """Return the intercell flows of a FlowStep as (from, to, flow) with flow > 0."""
    rows = np.repeat(np.arange(step.n_cells), np.diff(step.ia))
    out = step.flowja < 0.0  # negative flowja: out of the row cell
    return tuple(zip(rows[out].tolist(), step.ja[out].tolist(), (-step.flowja[out]).tolist()))


def step_terms(step: gs.FlowStep) -> tuple:
    """Return the external terms of a FlowStep as (cell, package, flow), + into the cell."""
    names = step.package_names
    return tuple(zip(step.term_cell.tolist(), [names[p] for p in step.term_package],
                     step.term_flow.tolist()))


def flow_width(q: float) -> float:
    """Line width of a graph arrow carrying flow q."""
    return 0.5 + 0.18 * abs(q)


def draw_graph(ax, step: gs.FlowStep, f: np.ndarray, value_size: float = 6.5) -> None:
    """Plan view of the graph: cells shaded and labelled by F, every arrow numbered by its flow."""
    xy = graph_positions()
    half = 0.45
    for i, (x, y) in enumerate(xy):
        cell_box(ax, (x, y), 2 * half, face=F_CMAP(f[i]))
        colour = "white" if f[i] > 0.55 else INK
        ax.text(x, y, f"{f[i]:.2f}", ha="center", va="center", fontsize=7.5, color=colour)
    for a, b, q in step_edges(step):
        unit = (xy[b] - xy[a]) / np.linalg.norm(xy[b] - xy[a])
        start, end = xy[a] + half * unit, xy[b] - half * unit
        arrow(ax, start, end, MUTED, width=flow_width(q))
        side = np.array([unit[1], -unit[0]]) * (1 if unit[0] else -1)  # below or east
        mid = 0.5 * (start + end) + 0.17 * side
        ax.text(*mid, f"{q:g}", ha="center", va="center", fontsize=value_size, color=INK)
    draw_graph_terms(ax, xy, half, step_terms(step), value_size)
    blank_axes(ax, (-1.35, 5.5), (-2.75, 0.95))


def draw_graph_terms(ax, xy: np.ndarray, half: float, terms: tuple,
                     value_size: float = 6.5) -> None:
    """Draw and number the CHD inflows on the west, the recharge, the well and the river sinks."""
    blue, red, green = OKABE_ITO["blue"], OKABE_ITO["vermillion"], OKABE_ITO["green"]
    for cell, pkg, q in terms:
        x, y = xy[cell]
        if pkg == "CHD":
            arrow(ax, (x - half - 0.45, y), (x - half, y), green, width=flow_width(q))
            ax.text(x - half - 0.22, y + 0.15, f"{q:g}", ha="center", va="center",
                    fontsize=value_size, color=green)
        elif pkg == "RCH":
            arrow(ax, (x - 0.22, y + half + 0.22), (x - 0.22, y + half - 0.08), blue, width=0.7)
            ax.text(x - 0.33, y + half + 0.13, f"{q:g}", ha="right", va="center",
                    fontsize=value_size, color=blue)
        elif pkg == "WEL":
            arrow(ax, (x, y - half), (x, y - half - 0.4), red, width=flow_width(q))
        elif pkg == "RIV":
            arrow(ax, (x + half, y), (x + half + 0.4, y), red, width=flow_width(q))
            ax.text(x + half + 0.2, y + 0.15, f"{-q:g}", ha="center", va="center",
                    fontsize=value_size, color=red)


def draw_graph_labels(ax, inflow: float, terms: tuple = GRAPH_TERMS) -> None:
    """Name the boundary inflow, the river, the recharge and the well, and state view and units."""
    blue, red, green = OKABE_ITO["blue"], OKABE_ITO["vermillion"], OKABE_ITO["green"]
    xy = graph_positions()
    half = 0.45
    x_in, y_in = xy[term_cells(terms, "CHD")].mean(axis=0)  # between the two inflow arrows
    ax.text(x_in - half - 0.4, y_in, "inflow", ha="center", va="center", fontsize=7,
            color=green)
    x_riv, y_riv = xy[term_cells(terms, "RIV")].mean(axis=0)
    ax.text(x_riv + half + 0.2, y_riv, "river", ha="center", va="center", fontsize=7,
            color=red)
    x_well, y_well = xy[term_cells(terms, "WEL")[0]]
    ax.text(x_well, y_well - half - 0.45, f"well {inflow:g}", ha="center", va="top",
            fontsize=7, color=red)
    x_rch, y_rch = xy[term_cells(terms, "RCH")[0]]
    ax.text(x_rch - half - 0.85, y_rch + half + 0.4, "recharge", ha="left", va="center",
            fontsize=7, color=blue)
    ax.text(xy[0][0] - half, y_well - half - 0.1, "plan view, flows in m³/d", ha="left",
            va="top", fontsize=7, color=INK)


def draw_gross_net(ax, numbers: dict[str, float]) -> None:
    """Panel (c): the weak well's cell, and the water credited to the well in each accounting.
    The gross bar takes the well's colour (its pumping), the net bar the inflow's (the cell's
    throughflow)."""
    red = OKABE_ITO["vermillion"]
    cell_box(ax, (0.0, 1.45), 0.9)
    ax.plot(0.0, 1.45, marker="v", color=red, ms=6)
    arrow(ax, (-1.3, 1.45), (-0.45, 1.45), MUTED, width=2.2)
    ax.text(-0.88, 1.56, f"{numbers['cell_inflow']:.1f}", ha="center", va="bottom", fontsize=7)
    arrow(ax, (0.45, 1.45), (1.3, 1.45), MUTED, width=2.0)
    ax.text(0.88, 1.56, f"{numbers['passed_on']:.1f}", ha="center", va="bottom", fontsize=7)
    arrow(ax, (0.0, 1.0), (0.0, 0.55), red, width=1.0)
    ax.text(0.12, 0.75, f"well {numbers['pumping']:.1f}", ha="left", va="center", fontsize=7,
            color=red)
    ax.text(0.0, 2.05, "weak-sink cell (m³/d)", ha="center", va="bottom", fontsize=7)
    ax.text(0.0, 0.1, "credited to the well (m³/d)", ha="center", va="center", fontsize=7)
    bars = (("gross", numbers["attributed_gross"], red),
            ("net", numbers["attributed_net"], MUTED))
    x0, scale = -0.85, 2.05 / numbers["attributed_net"]
    for row, (name, value, colour) in enumerate(bars):
        y = -0.35 - 0.55 * row
        ax.add_patch(Rectangle((x0, y - 0.18), value * scale, 0.36, color=colour, lw=0))
        ax.text(x0 - 0.08, y, name, ha="right", va="center", fontsize=7)
        ax.text(x0 + 0.05 + value * scale, y, f"{value:.1f}", ha="left", va="center",
                fontsize=7)
    blank_axes(ax, (-1.9, 1.9), (-1.2, 2.45))


def water_cell(ax, xy: tuple[float, float], size: float, level: float, shade: float,
               text: str = "") -> None:
    """Draw a cell partly filled with water; the fill colour darkens with the tagged fraction."""
    x0, y0 = xy[0] - size / 2, xy[1] - size / 2
    ax.add_patch(Rectangle((x0, y0), size, level * size, facecolor=F_CMAP(shade), lw=0))
    cell_box(ax, xy, size, face="none")
    ax.text(xy[0], y0 + 0.6 * level * size, text, ha="center", va="center", fontsize=7)


def cell_terms(ax, x: float, y: float, h: float, inflow_y: float,
               flow_colour: str = INK) -> None:
    """Draw a cell's intercell in- and outflow, its recharge and its well, unlabelled."""
    blue, red = OKABE_ITO["blue"], OKABE_ITO["vermillion"]
    arrow(ax, (x - h - 0.6, inflow_y), (x - h, inflow_y), flow_colour)
    arrow(ax, (x + h, inflow_y), (x + h + 0.6, inflow_y), flow_colour)
    arrow(ax, (x - 0.25, y + h + 0.55), (x - 0.25, y + h), blue, width=1.4)
    arrow(ax, (x + 0.25, y + h), (x + 0.25, y + h + 0.55), red, width=1.4)


def draw_snapshot_cell(ax, xy: tuple[float, float] = (2.4, 1.7), size: float = 1.0,
                       flow_colour: str = INK) -> None:
    """Panel (d), left: one step traced on its own flows, storage release as a source term."""
    blue, red = OKABE_ITO["blue"], OKABE_ITO["vermillion"]
    x, y, h = xy[0], xy[1], size / 2
    cell_box(ax, xy, size)
    ax.text(x, y, "$i$", ha="center", va="center", fontsize=9)
    cell_terms(ax, x, y, h, y, flow_colour)
    ax.text(x - 0.37, y + h + 0.3, "recharge", ha="right", va="center", fontsize=7, color=blue)
    ax.text(x + 0.37, y + h + 0.3, "well", ha="left", va="center", fontsize=7, color=red)
    arrow(ax, (x, y - h - 0.65), (x, y - h), MUTED, width=2.2)
    ax.text(x + 0.15, y - h - 0.35, "storage release,\norigin unknown", ha="left",
            va="center", fontsize=7, color=MUTED)


def draw_tracking_cells(ax, x0: float = 7.0, y: float = 1.7, size: float = 1.0,
                        gap: float = 2.4, flow_colour: str = INK) -> None:
    """Panel (d), right: the same cell i at three times. The water stored at the end of step n
    is mixed with the inflows of step n+1; outflows and the water stored at the end of step n+1
    carry the mixture."""
    xa, xb, xc, h = x0, x0 + gap, x0 + 2 * gap, size / 2
    water_cell(ax, (xa, y), size, 0.6, 0.25)
    water_cell(ax, (xb, y), size, 0.55, 0.42, "mixed")
    water_cell(ax, (xc, y), size, 0.5, 0.42)
    cell_terms(ax, xb, y, h, y + 0.3, flow_colour)
    low = y - h + 0.15
    for x_from, x_to in ((xa + h, xb - h), (xb + h, xc - h)):
        arrow(ax, (x_from, low), (x_to, low), MUTED, width=2.2)
    ax.text(0.5 * (xa + xb), low + 0.07, "stored\nwater", ha="center", va="bottom", fontsize=7,
            color=MUTED)
    time_y = y - h - 0.12
    arrow(ax, (xa - h, time_y), (xc + h + 0.6, time_y), MUTED, width=0.6)
    ax.text(xc + h + 0.65, time_y, "time", ha="left", va="center", fontsize=7, color=MUTED)
    for x, text in ((xa, "end of step $n$\n$V_i^{n},\\ c_i^{n}$"),
                    (xb, "step $n$+1"),
                    (xc, "end of step $n$+1\n$V_i^{n+1},\\ c_i^{n+1}$")):
        ax.text(x, y - h - 0.25, text, ha="center", va="top", fontsize=7)


def draw_transient(ax) -> None:
    """Panel (d): a snapshot of one step against transient tracking from step n to n+1."""
    draw_snapshot_cell(ax)
    ax.plot([5.0, 5.0], [0.3, 3.3], color=GRID, lw=0.8)
    ax.text(0.2, 3.3, "snapshot", ha="left", va="top", fontsize=7.5)
    ax.text(5.3, 3.3, "transient tracking", ha="left", va="top", fontsize=7.5)
    draw_tracking_cells(ax)
    blank_axes(ax, (0.0, 14.0), (0.3, 3.35))


def check_fig1_numbers(f: np.ndarray, inflow: float, numbers: dict[str, float],
                       terms: tuple = GRAPH_TERMS) -> None:
    """Assert the Fig. 1 numbers quoted in the text: F = 6/11 in (b), 5.0 vs 33.7 m³/d in (c)."""
    well = term_cells(terms, "WEL")[0]
    assert inflow == 6.0 and abs(f[well] - 6 / 11) < 1e-12, (inflow, f[well])
    assert round(numbers["pumping"], 1) == 5.0, numbers
    assert round(numbers["attributed_gross"], 1) == 5.0, numbers
    assert round(numbers["attributed_net"], 1) == 33.7, numbers
    assert round(numbers["f_gross"], 2) == 0.15, numbers


def make_fig1(out_dir: Path, numbers: dict[str, float]) -> list[Path]:
    """Fig. 1: method schematic, three panels in the top row and the transient panel below."""
    step = graph_step()
    f, inflow, _ = graph_fractions(step)
    check_fig1_numbers(f, inflow, numbers)
    fig = plt.figure(figsize=(FULL_WIDTH, 3.9))
    outer = fig.add_gridspec(2, 1, height_ratios=(2.0, 1.55), hspace=0.14, left=0.01,
                             right=0.99, top=0.94, bottom=0.01)
    top = outer[0].subgridspec(1, 3, width_ratios=(1.0, 1.65, 1.05), wspace=0.08)
    axes = [fig.add_subplot(top[0, i]) for i in range(3)] + [fig.add_subplot(outer[1])]
    draw_single_cell(axes[0])
    draw_graph(axes[1], step, f)
    draw_graph_labels(axes[1], inflow)
    draw_gross_net(axes[2], numbers)
    draw_transient(axes[3])
    titles = ("(a) one fully mixed cell", "(b) backward fraction F to a well",
              "(c) gross vs net accounting", "(d) snapshot vs transient tracking")
    for ax, title in zip(axes, titles):
        ax.apply_aspect()
        box = ax.get_position()
        y, va = (0.99, "top") if ax is not axes[3] else (box.y1 + 0.012, "bottom")
        fig.text(box.x0 + 0.005, y, title, ha="left", va=va, fontsize=8, fontweight="bold")
    return save(fig, out_dir, "fig1_method_schematic")


# ---------------------------------------------------------------- Fig. 2: verification

MODEL_STYLES = {  # model: (colour, marker)
    "m1_dis": (OKABE_ITO["blue"], "o"),
    "m2_dis3lay": (OKABE_ITO["blue"], "s"),
    "m3_disv": (OKABE_ITO["green"], "o"),
    "m4_disu_vert": (OKABE_ITO["green"], "s"),
    "m4_disu_novert": (OKABE_ITO["green"], "D"),
    "m5_xt3d": (OKABE_ITO["sky"], "^"),
    "m6_transient": (OKABE_ITO["orange"], "v"),
    "m6_split": (OKABE_ITO["orange"], "^"),
    "m7_mover": (OKABE_ITO["vermillion"], "o"),
    "m8_maw": (OKABE_ITO["vermillion"], "s"),
    "m9_lak_uzf": (OKABE_ITO["vermillion"], "D"),
    "m10_constant": (OKABE_ITO["blue"], "P"),
    "substep_network": (OKABE_ITO["purple"], "X"),
    "fb13_example": (INK, "*"),
}
ZERO_AT = 1e-18  # where exact zeros are drawn on the log axis
MARKER_SIZE = 4.5  # pt, model markers in Fig. 2 and its legend
MARKER_SCALE = {"*": 1.5, "P": 1.15, "X": 1.15, "D": 0.9}  # same apparent size as a circle
TOLERANCE_GREY = "#9a9a9a"
ROW_GRID = "#ececec"
FIG2_MODEL_LABELS = {  # reader-facing legend labels that differ from verification.MODEL_LABELS
    "fb13_example": "Foley and Black (2013)\nexample, net accounting",
    "m5_xt3d": "5 flow loops (XT3D)",
    "substep_network": "hand-built 15-cell\nnetwork (not MF6)",
}
FIG2_CHECK_LABELS = {"reference_example": "Foley and Black (2013) example"}


def model_offsets(models: list[str], spread: float = 0.32) -> dict[str, float]:
    """Return a vertical offset per model within a check's row (one model: centred)."""
    if len(models) == 1:
        return {models[0]: 0.0}
    return dict(zip(models, np.linspace(-spread, spread, len(models))))


def check_rows(check_groups: dict, checks: list[str]) -> tuple[dict, list]:
    """Return the y row of each check and the (row, heading) of each group, top to bottom."""
    rows, headings, y = {}, [], 0
    for name, group in check_groups.items():
        present = [c for c in group if c in checks]
        if not present:
            continue
        headings.append((y, name))
        y += 1
        for check in present:
            rows[check] = y
            y += 1
    return rows, headings


def draw_tolerances(ax, table: pd.DataFrame, rows: dict, colour: str = TOLERANCE_GREY) -> None:
    """Mark each check's test tolerance(s) as a short grey bar across its row."""
    for check, row in rows.items():
        for tol in sorted(set(table[table.check == check].tolerance.dropna())):
            ax.plot([tol, tol], [row - 0.4, row + 0.4], color=colour, lw=2.2,
                    solid_capstyle="butt", zorder=2)


def draw_errors(ax, table: pd.DataFrame, rows: dict, labels: dict,
                ms: float = MARKER_SIZE) -> list:
    """Plot each model's error per check (exact zeros at ZERO_AT); return legend handles."""
    ok = table[table.status == "ok"]
    offsets = {}
    for check in rows:
        present = [m for m in MODEL_STYLES if m in set(ok[ok.check == check].model)]
        offsets.update({(m, check): o for m, o in model_offsets(present).items()})
    handles = []
    for model in [m for m in MODEL_STYLES if m in set(ok.model)]:
        colour, marker = MODEL_STYLES[model]
        sel = ok[ok.model == model]
        y = [rows[c] + offsets[(model, c)] for c in sel.check]
        x = np.where(sel.error.to_numpy() == 0.0, ZERO_AT, sel.error.to_numpy())
        size = ms * MARKER_SCALE.get(marker, 1.0)
        handles.append(ax.plot(x, y, ls="none", marker=marker, color=colour, ms=size,
                               mec="white", mew=0.4, zorder=4, label=labels[model])[0])
    return handles


def axis_break(ax, x: float = 1.7e-17) -> None:
    """Mark the break in the x axis between the 'exact' slot and the first decade.

    x sits halfway (on the log axis) between the grey 'exact' band and 1e-16; the white box
    behind the mark is kept small so it cuts the axis line but not the band.
    """
    ax.text(x, 0.0, "//", transform=ax.get_xaxis_transform(), ha="center", va="center",
            fontsize=7, color=MUTED, zorder=5, clip_on=False,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3})


def x_ticks(ax, decades: tuple = (-16, -12, -8, -4, 0)) -> None:
    """Label the 'exact' slot and every fourth decade; mark the decades between unlabelled."""
    ticks = [ZERO_AT] + [10.0 ** d for d in decades]
    ax.set_xticks(ticks, ["exact"] + [f"$10^{{{d}}}$" for d in decades])
    minor = [10.0 ** d for d in range(decades[0], decades[-1], 2) if d not in decades]
    ax.set_xticks(minor, [""] * len(minor), minor=True)
    ax.tick_params(axis="x", which="minor", length=2.0)


def fig2_legends(fig, handles: list) -> None:
    """Put the model key top right and the reference key (precision, tolerance) below it."""
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.72, 0.985),
               title="model", title_fontsize=7, alignment="left", handletextpad=0.3,
               labelspacing=0.45)
    eps = plt.Line2D([], [], color=INK, ls="--", lw=0.9, label="machine precision")
    tol = plt.Line2D([], [], color=TOLERANCE_GREY, ls="none", marker="|", ms=9, mew=2.2,
                     label="test tolerance")
    fig.legend(handles=[eps, tol], loc="lower left", bbox_to_anchor=(0.72, 0.085),
               handletextpad=0.3, labelspacing=0.45)


def make_fig2(out_dir: Path, table: pd.DataFrame, model_labels: dict,
              check_labels: dict, check_order: tuple, check_groups: dict,
              xlabel: str = "error reached (measure per check in Table S1)",
              file_name: str = "fig2_verification") -> list[Path]:
    """Fig. 2: error per check and model on a log axis, with machine precision and tolerances.
    The reduced draft's SI figure (figS21_verification) names the measures in its caption."""
    checks = [c for c in check_order if c in set(table.check)]
    rows, headings = check_rows(check_groups, checks)
    n_rows = len(rows) + len(headings)
    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 5.0))
    fig.subplots_adjust(left=0.235, right=0.71, top=0.985, bottom=0.085)
    ax.axvspan(3e-19, 3e-18, color="#f2f2f2", zorder=0)
    ax.axvline(MACHINE_EPS, color=INK, ls="--", lw=0.9, zorder=1)
    draw_tolerances(ax, table, rows)
    handles = draw_errors(ax, table, rows, model_labels)
    ax.set_xscale("log")
    ax.set_xlim(3e-19, 1.0)
    axis_break(ax)
    x_ticks(ax)
    ax.set_yticks(list(rows.values()), [check_labels[c] for c in rows])
    ax.set_ylim(n_rows - 0.5, -0.5)
    for row in range(1, n_rows):
        ax.axhline(row - 0.5, color=ROW_GRID, lw=0.5, zorder=0)
    for row, name in headings:
        ax.axhspan(row - 0.5, row + 0.5, color="white", zorder=3)
        ax.text(0.01, row, name, transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=7.5, fontweight="bold", zorder=4)
        if row > 0:
            ax.axhline(row - 0.5, color=MUTED, lw=0.8, zorder=3)
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)
    fig2_legends(fig, handles)
    return save(fig, out_dir, file_name)


# ---------------------------------------------------------------- Fig. 3: numerical dispersion

DISPERSION_SERIES = {  # (grid, method): (colour, marker, label)
    ("DIS", "mixing"): (OKABE_ITO["blue"], "o", "full mixing, DIS"),
    ("DIS", "routing"): (OKABE_ITO["vermillion"], "s", "face routing, DIS"),
    ("DISV", "mixing"): (OKABE_ITO["green"], "D", "full mixing, DISV"),
    ("DIS", "cell_average"): (OKABE_ITO["purple"], "", "cell-averaged exact zone (A)"),
    ("DIS", "particles"): (INK, "^", "PRT particles, DIS (B)"),
}


def import_dispersion_figures(study_dir: Path = DISPERSION_DIR):
    """Import the dispersion study's figure module (its axis helper and labels)."""
    if str(study_dir) not in sys.path:
        sys.path.insert(0, str(study_dir))
    import figures as dispersion_figures

    return dispersion_figures


def dispersion_series(ax, table: pd.DataFrame, key: tuple, column: str, angle=None,
                      ls: str = "-") -> None:
    """Plot one metric against the mean cell size for one grid kind and method."""
    colour, marker, _ = DISPERSION_SERIES[key]
    sel = (table.kind == key[0]) & (table.method == key[1])
    if angle is not None:
        sel &= table.angle == angle
    rows = table[sel].sort_values("mean_h")
    ax.plot(rows.mean_h, rows[column], color=colour, marker=marker, ms=3.2, ls=ls,
            lw=1.0 if key[1] == "cell_average" else 1.4)


def slope_guide(ax, h: np.ndarray, anchor: tuple[float, float], power: float, text: str) -> None:
    """Draw a reference line y ~ h^power through anchor (h, y) with a label."""
    y = anchor[1] * (h / anchor[0]) ** power
    ax.plot(h, y, color="#999999", lw=0.9, ls=(0, (5, 2)))
    ax.text(h[-1] * 0.92, y[-1], text, fontsize=7, color=MUTED, ha="left", va="center")


def plain_log_ticks(ax, ticks: tuple[float, ...]) -> None:
    """Label a log y axis with plain numbers at the given ticks."""
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_yticks([], minor=True)


def dispersion_row(axes, table: pd.DataFrame, keys: list, angles: tuple, size_axis,
                   sizes: tuple) -> None:
    """Draw band width, area error F > 0.1 and area error F > 0.5 for one problem."""
    columns = ("band_width", "area_err_0.1", "area_err_0.5")
    for ax, column in zip(axes, columns):
        for key in keys:
            for angle, ls in angles:
                dispersion_series(ax, table, key, column, angle, ls)
        size_axis(ax, sizes)
        ax.set_xlim(sizes[0] * 1.3, sizes[-1] * 0.8)
        ax.grid(True, color=GRID, lw=0.5)
    axes[0].set_yscale("log")
    axes[1].set_yscale("log")
    axes[2].axhspan(-0.05, 0.05, color="#eeeeee", zorder=0)
    axes[2].axhline(0.0, color=MUTED, lw=0.6)


def make_fig3(out_dir: Path, dispersion_out: Path) -> list[Path]:
    """Fig. 3: problems A and B against cell size (band width, area errors), one figure."""
    dfig = import_dispersion_figures()
    a = pd.read_csv(dispersion_out / "a_metrics.csv")
    b = pd.read_csv(dispersion_out / "b_metrics.csv")
    fig, axes = plt.subplots(2, 3, figsize=(FULL_WIDTH, 4.6), constrained_layout=True)
    keys_a = [("DIS", "mixing"), ("DIS", "routing"), ("DISV", "mixing"), ("DIS", "cell_average")]
    keys_b = [("DIS", "mixing"), ("DIS", "routing"), ("DISV", "mixing"), ("DIS", "particles")]
    dispersion_row(axes[0], a, keys_a, ((0.0, "-"), (30.0, ":")), dfig._size_axis,
                   (200, 100, 50, 25, 12.5))
    dispersion_row(axes[1], b, keys_b, ((None, "-"),), dfig._size_axis, (100, 50, 25, 12.5))
    slope_guide(axes[0, 0], np.array([200.0, 12.5]), (200.0, 900.0), 0.5, "$h^{0.5}$")
    slope_guide(axes[1, 0], np.array([100.0, 12.5]), (100.0, 230.0), 0.5, "$h^{0.5}$")
    plain_log_ticks(axes[0, 0], (10, 30, 100, 300, 1000))
    plain_log_ticks(axes[1, 0], (10, 30, 100, 300))
    plain_log_ticks(axes[0, 1], (0.03, 0.1, 0.3, 1, 3))
    plain_log_ticks(axes[1, 1], (0.02, 0.05, 0.1, 0.2, 0.5))
    titles = ("width of the 0.1 < F < 0.9 band (m)", "relative area error, F > 0.1",
              "relative area error, F > 0.5")
    for row, problem in enumerate(("A: analytical reference", "B: PRT reference")):
        for col, title in enumerate(titles):
            ax = axes[row, col]
            ax.set_title(f"({'abcdef'[3 * row + col]}) {title}", loc="left")
            if row == 0:
                ax.set_xlabel("")
        axes[row, 0].set_ylabel(f"problem {problem}")
    axes[0, 2].set_ylim(-0.55, 0.5)
    axes[1, 2].set_ylim(-0.06, 0.06)
    handles = [plt.Line2D([], [], color=c, marker=m, ms=3.2, lw=1.4, label=lab)
               for c, m, lab in DISPERSION_SERIES.values()]
    handles += [plt.Line2D([], [], color=MUTED, ls=ls, lw=1.2, label=lab)
                for ls, lab in (("-", "A: flow along the rows"), (":", "A: flow at 30°"))]
    fig.legend(handles=handles, loc="outside lower center", ncol=4)
    return save(fig, out_dir, "fig3_numerical_dispersion")


# ---------------------------------------------------------------- driver


def find_mf6(bin_dir: Path = REPO / "bin") -> Path:
    """Return the mf6 executable in bin_dir."""
    exe = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    assert exe.is_file(), f"{exe} not found; run scripts/setup_env.sh"
    return exe


def run_verification(out_dir: Path, work: Path) -> pd.DataFrame:
    """Run the verification checks and write Table S1 (CSV and markdown)."""
    import verification as ver

    table = ver.collect(work / "verification", ver.find_exes())
    ver.write_tables(table, out_dir)
    return table


def main(
    out_dir: Path = FIG_DIR,
    work: Path = WORK_DIR,
    dispersion_out: Path = DISPERSION_DIR / "output",
    fig1: bool = True,
    verification: bool = True,
    fig2: bool = True,
    fig3: bool = True,
) -> None:
    """Make the method and verification figures; each gate can be switched off."""
    if str(PAPER_DIR) not in sys.path:
        sys.path.insert(0, str(PAPER_DIR))
    import verification as ver

    paper_style()
    start = time.perf_counter()
    if fig1:
        numbers = weak_sink_numbers(work, find_mf6())
        print("Fig. 1 weak sink:", {k: round(v, 3) for k, v in numbers.items()})
        print("wrote", make_fig1(out_dir, numbers))
    if verification:
        table = run_verification(out_dir, work)
        print(ver.summary_by_check(table).to_string(index=False))
    if fig2:
        table = pd.read_csv(out_dir / "verification_table.csv")
        model_labels = {**ver.MODEL_LABELS, **FIG2_MODEL_LABELS}
        check_labels = {**ver.CHECK_LABELS, **FIG2_CHECK_LABELS}
        print("wrote", make_fig2(out_dir, table, model_labels, check_labels, ver.CHECK_ORDER,
                                 ver.CHECK_GROUPS))
    if fig3:
        print("wrote", make_fig3(out_dir, dispersion_out))
    print(f"done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
