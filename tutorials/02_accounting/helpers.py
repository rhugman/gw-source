"""Tutorial 02 helpers: the hand-built graph of the Foley & Black (2013) worked example and its figure.

The worked example is a 3 x 3 block of cells A-I (A B C / D E F / G H I) with destination A.
Two extra nodes stand for the area outside the picture: J sends 10 into C, and K receives the 5
that B sends out of the picture. Flows are in arbitrary volume-rate units.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

import gwsource as gs

FB13_LABELS = "ABCDEFGHIJK"
FB13_EDGES = (  # (from, to, flow)
    ("B", "A", 5.0), ("D", "A", 5.0), ("C", "B", 5.0), ("E", "B", 5.0), ("B", "K", 5.0),
    ("E", "D", 5.0), ("C", "F", 5.0), ("F", "E", 8.0), ("I", "F", 1.0), ("H", "E", 2.0),
    ("J", "C", 10.0),
)
FB13_POSITIONS = {  # (x, y) of each cell centre in the figure; J and K lie outside the block
    "A": (0, 2), "B": (1, 2), "C": (2, 2),
    "D": (0, 1), "E": (1, 1), "F": (2, 1),
    "G": (0, 0), "H": (1, 0), "I": (2, 0),
    "J": (3.3, 2), "K": (1, 3.3),
}
FB13_OUTSIDE = ("J", "K")


def fb13_edge_arrays(
    labels: str = FB13_LABELS, edges: tuple = FB13_EDGES
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the worked example's edges as 0-based (src, dst, q) arrays."""
    index = {label: i for i, label in enumerate(labels)}
    src = np.array([index[a] for a, _, _ in edges])
    dst = np.array([index[b] for _, b, _ in edges])
    q = np.array([flow for _, _, flow in edges])
    return src, dst, q


def fb13_step(labels: str = FB13_LABELS, edges: tuple = FB13_EDGES) -> gs.FlowStep:
    """Return the worked example as a FlowStep with intercell flows only (enough for net mode)."""
    src, dst, q = fb13_edge_arrays(labels, edges)
    return gs.from_edges(len(labels), src, dst, q)


def fb13_step_with_terms(
    sources: dict[str, float], sinks: dict[str, float], labels: str = FB13_LABELS,
    edges: tuple = FB13_EDGES,
) -> gs.FlowStep:
    """Return the worked example with explicit external terms: packages 'SRC' (in) and 'SNK' (out)."""
    src, dst, q = fb13_edge_arrays(labels, edges)
    index = {label: i for i, label in enumerate(labels)}
    cells = [index[c] for c in sources] + [index[c] for c in sinks]
    flows = list(sources.values()) + [-v for v in sinks.values()]
    package = [0] * len(sources) + [1] * len(sinks)
    packages = [gs.Package("SRC", "SRC"), gs.Package("SNK", "SNK")]
    return gs.from_edges(
        len(labels), src, dst, q, term_cell=cells, term_flow=flows, term_package=package,
        packages=packages,
    )


def _draw_cell(ax, xy: tuple[float, float], label: str, value: float, cmap, outside: bool) -> None:
    """Draw one cell as a coloured square with its label and value."""
    colour = "white" if outside else cmap(value)
    ax.add_patch(Rectangle(
        (xy[0] - 0.4, xy[1] - 0.4), 0.8, 0.8, facecolor=colour, edgecolor="0.3",
        linestyle="--" if outside else "-", linewidth=1.2, zorder=1,
    ))
    text_colour = "k" if outside or value > 0.45 else "w"
    ax.text(xy[0], xy[1] + 0.12, label, ha="center", va="center", fontsize=13,
            fontweight="bold", color=text_colour, zorder=3)
    ax.text(xy[0], xy[1] - 0.15, f"F = {value:.3g}", ha="center", va="center", fontsize=9,
            color=text_colour, zorder=3)


def _draw_edge(ax, start: tuple[float, float], end: tuple[float, float], q: float) -> None:
    """Draw an arrow from cell to cell with the flow written next to it."""
    start, end = np.asarray(start, float), np.asarray(end, float)
    unit = (end - start) / np.linalg.norm(end - start)
    a, b = start + 0.42 * unit, end - 0.42 * unit
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color="tab:red",
                                 linewidth=1.2 + 0.25 * q, zorder=2))
    mid = 0.5 * (a + b) + 0.13 * np.array([-unit[1], unit[0]])
    ax.text(mid[0], mid[1], f"{q:g}", ha="center", va="center", fontsize=9, color="tab:red",
            zorder=4, bbox={"boxstyle": "round,pad=0.1", "fc": "white", "ec": "none"})


def draw_cell_graph(
    values: np.ndarray,
    labels: str = FB13_LABELS,
    edges: tuple = FB13_EDGES,
    positions: dict | None = None,
    outside: tuple[str, ...] = FB13_OUTSIDE,
    ax=None,
    title: str = "",
):
    """Draw the worked-example graph: cells coloured by a fraction, arrows labelled with flows."""
    positions = FB13_POSITIONS if positions is None else positions
    if ax is None:
        _, ax = plt.subplots(figsize=(5.5, 5.5))
    cmap = plt.get_cmap("viridis")
    for i, label in enumerate(labels):
        _draw_cell(ax, positions[label], label, float(values[i]), cmap, label in outside)
    for a, b, q in edges:
        _draw_edge(ax, positions[a], positions[b], q)
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    ax.set_xlim(min(xs) - 0.6, max(xs) + 0.6)
    ax.set_ylim(min(ys) - 0.6, max(ys) + 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title)
    plt.colorbar(plt.cm.ScalarMappable(cmap=cmap), ax=ax, shrink=0.7, label="F (-)")
    return ax
