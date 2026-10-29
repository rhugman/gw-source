"""Method figure (make_method_single) and the map helpers that synthetic_figures.py reuses.

The method figure is one column wide. Panel (a) is backward fraction F to a well on a hand-built
eight-cell flow graph (method_figures.draw_graph), every arrow numbered by its flow. Panel (b)
sets a snapshot, where stored water released in a step is a source of unknown origin, against
transient tracking, which carries the stored water from one step into the next
(method_figures.draw_snapshot_cell and draw_tracking_cells). The figure needs no model run.

The map helpers draw a per-cell value on the 2 km x 2 km example model with sky-blue stream
cells and a white well star, in model metres with km ticks.

    PYTHONPATH=src:tutorials:studies/paper python studies/paper/gallery_figure.py

Output: output/paper/ in the repository root (git-ignored).
"""

import sys
from pathlib import Path

import numpy as np

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import example_figures as ef  # noqa: E402
import method_figures as mfig  # noqa: E402

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

METHOD_NAME = "fig_method_single"
EXTENT = 2000.0  # m, every map
SINGLE_WIDTH = 8.25 / 2.54  # in
TRAVEL_NORM = (0.1, 100.0)  # years
ZONE_YEARS = (5, 25)
ZONE_COLOUR = "tab:cyan"
G_LEVELS = (1e-3, 1.0)  # log range of G


# ---------------------------------------------------------------- drawing helpers


def draw_layer(ax, layer: dict, cmap, norm, values: np.ndarray | None = None):
    """Colour the cells of a map layer, fill the river cells and mark the well."""
    image = ef.draw_values(ax, layer["grb"], layer["step"],
                           layer["values"] if values is None else values, cmap, norm)
    ef.draw_cells(ax, layer["grb"], layer["step"], layer["river"], ef.RIVER_COLOUR)
    ef.draw_well(ax, layer["grb"], layer["well"], size=55.0)
    return image


def map_axes(ax, left: bool, bottom: bool, extent: float = EXTENT) -> None:
    """Square 2 km map axes; km ticks only on the outer panels."""
    ef.km_axes(ax, extent=extent, step_km=1.0, x_label=bottom, y_label=left)
    if not left:
        ax.tick_params(axis="y", length=0)
    if not bottom:
        ax.tick_params(axis="x", length=0)
    ax.xaxis.labelpad = 1
    ax.yaxis.labelpad = 1


def draw_fate(ax, layer: dict, levels: tuple = G_LEVELS):
    """G of the recharge on a field (log scale), the field outlined."""
    norm = LogNorm(*levels)
    image = draw_layer(ax, layer, ef.G_CMAP, norm, np.maximum(layer["values"], levels[0]))
    ef.field_rectangle(ax, layer["spec"])
    return image


def draw_travel_time(ax, layer: dict, label_xy: dict, norm: tuple = TRAVEL_NORM,
                     zone_years: tuple = ZONE_YEARS):
    """Mean travel time inside F > 0.5 (log, magma_r), the zone contours labelled inline."""
    image = draw_layer(ax, layer, "magma_r", LogNorm(*norm))
    years = layer["values"]
    closed = np.where(np.isfinite(years), years, 10.0 * norm[1])  # zones close at F = 0.5
    lines = ef.draw_contours(ax, layer["grb"], layer["step"], closed, zone_years, ZONE_COLOUR,
                             ("-",) * len(zone_years), width=1.0)
    ax.clabel(lines, levels=list(label_xy), fmt={y: f"{y} yr" for y in label_xy}, fontsize=7,
              inline_spacing=1, manual=list(label_xy.values()))
    return image


# ---------------------------------------------------------------- method figure


def draw_transient_rows(ax, x_cell: float = 4.2, y_snapshot: float = 4.6,
                        y_tracking: float = 1.7) -> None:
    """Panel (b): the snapshot cell above, the same cell under transient tracking below."""
    mfig.draw_snapshot_cell(ax, (x_cell, y_snapshot), flow_colour=mfig.MUTED)
    mfig.draw_tracking_cells(ax, x0=0.95, y=y_tracking, flow_colour=mfig.MUTED)
    ax.plot([-0.1, 7.6], [3.3, 3.3], color=mfig.GRID, lw=0.8)
    ax.text(-0.1, y_snapshot + 1.05, "snapshot", ha="left", va="top", fontsize=7.5)
    ax.text(-0.1, 3.2, "transient tracking", ha="left", va="top", fontsize=7.5)
    mfig.blank_axes(ax, (-0.15, 7.65), (0.25, 5.7))


def make_method_single(out_dir: Path, height: float = 4.6,
                       fig_name: str = METHOD_NAME, split: float = 0.435) -> list[Path]:
    """Method figure, one column wide: (a) F on the eight-cell graph, (b) snapshot against tracking."""
    step = mfig.graph_step()
    f, inflow, _ = mfig.graph_fractions(step)
    assert inflow == 6.0 and abs(f[6] - 6 / 11) < 1e-12, (inflow, f[6])
    # Net accounting uses only the cell-to-cell flows, so the well cell's own 1 m3/d of
    # recharge is left out and the well gets 10, not 11, m3/d.
    net = gs.backward(step, {"well": gs.select(step, package="WEL")},
                      gs.TraceConfig(accounting="net")).destination_inflow["well"]
    assert abs(net - 10.0) < 1e-12, net
    # Panel (a) numbers every arrow with the step's own flows; they are the graph's inputs and
    # every cell balances (inflow = outflow, m3/d).
    assert sorted(mfig.step_edges(step)) == sorted(mfig.GRAPH_EDGES), mfig.step_edges(step)
    assert sorted(mfig.step_terms(step)) == sorted(mfig.GRAPH_TERMS), mfig.step_terms(step)
    budget = gs.cell_budget(step)
    assert np.abs(budget.inflow - budget.outflow).max() < 1e-12, budget
    fig = plt.figure(figsize=(SINGLE_WIDTH, height))
    title_h = 0.24 / height  # figure fraction of a panel title
    ax_a = fig.add_axes((0.0, 1.0 - split, 1.0, split - title_h))
    mfig.draw_graph(ax_a, step, f)
    mfig.draw_graph_labels(ax_a, inflow)
    ax_b = fig.add_axes((0.0, 0.0, 1.0, 1.0 - split - title_h - 0.01))
    draw_transient_rows(ax_b)
    for y, text in ((0.995, "(a) Backward fraction F to a well"),
                    (1.0 - split - 0.005, "(b) Snapshot against transient tracking")):
        fig.text(0.02, y, text, ha="left", va="top", fontsize=8, fontweight="bold")
    return mfig.save(fig, out_dir, fig_name)


# ---------------------------------------------------------------- driver


def main(out_dir: Path = mfig.FIG_DIR) -> None:
    """Draw the method figure."""
    mfig.paper_style()
    print("wrote", make_method_single(out_dir))


if __name__ == "__main__":
    main()
