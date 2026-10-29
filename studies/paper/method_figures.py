"""Shared style, paths and drawing helpers of the paper figures.

- paper_style and save: plain journal style (7 to 8 pt type), PNG at 300 dpi and PDF.
- The method sketch: a hand-built eight-cell flow graph (a gwsource FlowStep) with the backward
  fraction F to a well, every arrow numbered by its flow, and the symbolic cells that set a
  snapshot against transient tracking. gallery_figure.make_method_single draws the figure.
- find_mf6 and the repository paths. FIG_DIR, the default output folder of every paper figure,
  is output/paper/ in the repository root (git-ignored).

Colours are the Okabe-Ito set (colour-blind safe).
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

import gwsource as gs  # noqa: E402

PAPER_DIR = Path(__file__).resolve().parent
REPO = PAPER_DIR.parents[1]
FIG_DIR = REPO / "output" / "paper"
DISPERSION_DIR = REPO / "studies" / "dispersion"
TUTORIAL_DIR = REPO / "tutorials"

DPI = 300
INK, MUTED, GRID = "#000000", "#555555", "#dddddd"
OKABE_ITO = {
    "black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73",
    "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7",
}
F_CMAP = LinearSegmentedColormap.from_list(
    "f_blues", ["#ffffff", "#d6e6f4", "#8fbfe0", "#4a90c8", "#0072B2", "#08306b"]
)


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


# ---------------------------------------------------------------- method sketch: hand-built graph

GRAPH_SHAPE = (2, 4)  # rows, columns of the method-sketch graph; cell id = row * 4 + col
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
    """Return the method-sketch graph as a FlowStep with intercell edges and external terms."""
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


# ---------------------------------------------------------------- method sketch: drawing


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


# ---------------------------------------------------------------- axes


def plain_log_ticks(ax, ticks: tuple[float, ...]) -> None:
    """Label a log y axis with plain numbers at the given ticks."""
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_yticks([], minor=True)


# ---------------------------------------------------------------- executables


def find_mf6(bin_dir: Path = REPO / "bin") -> Path:
    """Return the mf6 executable in bin_dir."""
    exe = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    assert exe.is_file(), f"{exe} not found; run python studies/setup_tools.py"
    return exe
