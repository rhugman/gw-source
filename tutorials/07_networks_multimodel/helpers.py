"""Plotting and table helpers local to tutorial 07 (package networks and multi-model simulations).

The shared builders and map helpers live in tutorials/herebedragons.py; this module adds a
box-and-arrow route diagram, a layered cross-section and a few small tables built from the
global node graph (gwsource.assemble.flow_edges).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch

import gwsource as gs
from gwsource.assemble import flow_edges


def edges_between(step: gs.FlowStep, sources, targets) -> pd.DataFrame:
    """Return the graph edges from any node in sources to any node in targets (src, dst, q)."""
    edges = flow_edges(step)
    hit = np.isin(edges.src, np.asarray(sources)) & np.isin(edges.dst, np.asarray(targets))
    return pd.DataFrame({"src": edges.src[hit], "dst": edges.dst[hit], "q": edges.q[hit]})


def reach_exchange(step: gs.FlowStep, block_label: str) -> pd.DataFrame:
    """Return, per package node of a block, its inflow from cells and outflow to cells [m3/d]."""
    nodes = step.block(block_label).nodes
    cells = np.arange(nodes[0])  # model cells come first in the global numbering
    into = edges_between(step, cells, nodes).groupby("dst")["q"].sum()
    out = edges_between(step, nodes, cells).groupby("src")["q"].sum()
    frame = pd.DataFrame(
        {"from_cells": into.reindex(nodes, fill_value=0.0).to_numpy(),
         "to_cells": out.reindex(nodes, fill_value=0.0).to_numpy()},
        index=pd.Index(np.arange(1, nodes.size + 1), name="id"),
    )
    return frame


def _box_edge(x0: float, y0: float, x1: float, y1: float, half: tuple[float, float]):
    """Return the point where the segment from (x0, y0) towards (x1, y1) leaves a box at x0, y0."""
    dx, dy = x1 - x0, y1 - y0
    scale = min(half[0] / abs(dx) if dx else np.inf, half[1] / abs(dy) if dy else np.inf)
    return x0 + scale * dx, y0 + scale * dy


def route_diagram(
    ax, boxes: dict, arrows: list, title: str = "", half: tuple[float, float] = (0.065, 0.11)
) -> None:
    """Draw labelled boxes {key: (x, y, text, colour)} joined by arrows [(from, to, text)].

    Coordinates are axes fractions; half is the half width and height of a box.
    """
    for x, y, text, colour in boxes.values():
        ax.add_patch(FancyBboxPatch(
            (x - half[0], y - half[1]), 2 * half[0], 2 * half[1], boxstyle="round,pad=0.005",
            facecolor=colour, edgecolor="0.2",
        ))
        ax.text(x, y, text, ha="center", va="center", fontsize=8.5)
    for start, end, text in arrows:
        (x0, y0), (x1, y1) = boxes[start][:2], boxes[end][:2]
        tail = _box_edge(x0, y0, x1, y1, half)
        head = _box_edge(x1, y1, x0, y0, half)
        ax.annotate("", xy=head, xytext=tail,
                    arrowprops={"arrowstyle": "-|>", "color": "0.25", "lw": 1.4})
        x_mid, y_mid = (tail[0] + head[0]) / 2, (tail[1] + head[1]) / 2
        if abs(head[0] - tail[0]) >= abs(head[1] - tail[1]):  # mostly horizontal: label above
            ax.text(x_mid, y_mid + 0.04, text, ha="center", va="bottom", fontsize=8.5)
        else:  # mostly vertical: label to the right
            ax.text(x_mid + 0.01, y_mid, text, ha="left", va="center", fontsize=8.5)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.set_title(title)


def cross_section(
    ax, values: np.ndarray, row: int, z_edges, delr: float, label: str = "", **kwargs
):
    """Draw one row of a (nlay, nrow, ncol) array as a cross-section with true layer depths."""
    ncol = values.shape[2]
    x = np.arange(ncol + 1) * delr
    z = np.asarray(z_edges, float)
    mesh = ax.pcolormesh(x, z[::-1], values[::-1, row, :], shading="flat", **kwargs)
    for depth in z[1:-1]:
        ax.axhline(depth, color="0.4", lw=0.6)
    plt.colorbar(mesh, ax=ax, shrink=0.9, label=label)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("elevation (m)")
    return mesh


def model_boundaries(ax, labels: np.ndarray, delr: float, delc: float) -> None:
    """Outline the parts of a (nrow, ncol) splitter label array on a map (row 0 is north)."""
    nrow = labels.shape[0]
    segments = []
    for r, c in zip(*np.nonzero(labels[:, 1:] != labels[:, :-1])):  # west-east neighbours
        x = (c + 1) * delr
        segments.append([(x, (nrow - r) * delc), (x, (nrow - r - 1) * delc)])
    for r, c in zip(*np.nonzero(labels[1:, :] != labels[:-1, :])):  # north-south neighbours
        y = (nrow - r - 1) * delc
        segments.append([(c * delr, y), ((c + 1) * delr, y)])
    ax.add_collection(LineCollection(segments, colors="k", linewidths=2.5, zorder=6))
