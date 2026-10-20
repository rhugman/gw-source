"""Figures (PNG, light theme) of the Neversink flow graph with the stream reaches as nodes.

The network step is the one of workflow.py (output/optimal_tight, package_nodes=("SFR",)), traced
backward from the eight priority wells. Four views of the graph (gwsource.graphplot):

- stream network: every reach-to-reach link of SFR at the reach's cell, line width the
  streamflow, colour whether the reach gains water from the aquifer or loses it; beside it the
  same links with width the streamflow that later reaches the priority wells (q F_dst);
- zone graph: the graph condensed to the four layers and the stream on a ring, all the water
  and only the water that reaches the priority wells;
- sources: the recharge that reaches each well, split by the plan distance of the recharge cell
  from the nearest priority well;
- local zoom: the cells and reaches of two flow cycles and of the neighbourhood of well U_917,
  each layer shifted down and right so that vertical flows show.

Run with the project environment after workflow.py:

    python studies/neversink/network_figures.py

Figures go to studies/neversink/output/figures/.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402
from gwsource import graphplot as gp  # noqa: E402

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)
# Losing (stream to aquifer) orange, gaining (aquifer to stream) blue, grey midpoint
EXCHANGE = LinearSegmentedColormap.from_list("exchange", ["#d4541f", "#c9c8c3", "#1c5cab"])
ORDINAL = ["#0d366b", "#1c5cab", "#3987e5", "#86b6ef"]
LAYERS = ["#0d366b", "#3987e5", "#86b6ef", "#cde2fb"]
DISTANCE_BANDS = (0.0, 250.0, 1000.0, 2000.0, np.inf)
LAYER_SHIFT = (14.0, -24.0)
SFR = "neversink/SFR_0"
WELL_ZOOM = "U_917"
CYCLES_SHOWN = (2, 5)


def _style() -> None:
    """Set a light, recessive matplotlib style."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
        "ytick.color": MUTED, "text.color": INK, "axes.grid": False, "font.size": 9,
        "axes.titlesize": 9.5, "legend.frameon": False,
    })


def well_points(step: gs.FlowStep, result: gs.BackwardResult, xy: np.ndarray) -> dict:
    """Return {well: (x, y)} of each priority well's cell."""
    return {
        g: xy[np.flatnonzero(result.selections[g].cells)].mean(axis=0)
        for g in wf.PRIORITY_WELLS
    }


def _wells(ax, points: dict, labels: bool = False) -> None:
    """Mark the wells as white-ringed ink dots."""
    xy = np.array(list(points.values()))
    ax.scatter(xy[:, 0], xy[:, 1], s=26, c=INK, edgecolors="white", linewidths=1.0, zorder=5)
    if labels:
        for names, (x, y) in well_clusters(points):
            ax.annotate("\n".join(names), (x, y), xytext=(6, 0), textcoords="offset points",
                        fontsize=7, color=INK, va="center")


def well_clusters(points: dict, radius: float = 1500.0) -> list[tuple[list[str], np.ndarray]]:
    """Return the wells joined into clusters of neighbours within radius, with their centre."""
    clusters = []
    for name, xy in points.items():
        for names, members in clusters:
            if np.hypot(*(np.mean(members, axis=0) - xy)) < radius:
                names.append(name)
                members.append(xy)
                break
        else:
            clusters.append(([name], [xy]))
    return [(names, np.mean(members, axis=0)) for names, members in clusters]


def _km_axes(ax) -> None:
    """Label a map axis in km."""
    ax.xaxis.set_major_formatter(lambda v, _: f"{v / 1000:g}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:g}")
    ax.set_xlabel("x [km]")
    ax.set_ylabel("y [km]")


def stream_network(step, result, xy, wells, fig_dir: Path) -> Path:
    """Draw the SFR links: streamflow and exchange, and the streamflow that reaches the wells."""
    block = gp.package_block(step, "SFR_0")
    src, dst, q = gp.package_links(step, block)
    exchange = gp.package_net_exchange(step, block)[dst - block.offset]
    carried = gp.carried_flow(result, "priority", dst, q)
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2), sharex=True, sharey=True,
                             constrained_layout=True)
    limit = np.percentile(np.abs(exchange), 98)
    lines = gp.plot_package_network(step, block, xy, axes[0], cmap=EXCHANGE, color=exchange,
                                    norm=TwoSlopeNorm(0.0, -limit, limit))
    fig.colorbar(lines, ax=axes[0], shrink=0.5, extend="both",
                 label="net flow aquifer → reach [m³/d]\n(> 0 gaining, < 0 losing)")
    axes[0].set_title("a) stream network: width streamflow, colour exchange with aquifer")
    gp.plot_package_network(step, block, xy, axes[1], wmax=0.6, colors=GRID)
    gp.plot_package_network(step, block, xy, axes[1], q=carried, wmax=3.5, wmin=0.0, colors=BLUE)
    axes[1].set_title("b) streamflow that reaches the priority wells (q F)")
    for ax in axes:
        _wells(ax, wells, labels=ax is axes[1])
        _km_axes(ax)
    path = fig_dir / "neversink_network_sfr.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def zone_graphs(step, result, fig_dir: Path) -> Path:
    """Draw the layer-and-stream zone graph: all water, and the water reaching the wells."""
    zones, names = gp.layer_zones(step)
    dst = gp.edge_list(step)[1]
    graphs = {
        "a) all water [m³/d]": gp.zone_graph(step, zones, names),
        "b) water that reaches the priority wells [m³/d]": gp.zone_graph(
            step, zones, names, edge_weight=result.fraction_through["priority"][dst],
            term_weight=gp.term_weights(step, result, "priority"),
        ),
    }
    pos = gp.ring_layout(names[-1:] + names[:-1])
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), constrained_layout=True)
    for ax, (title, graph) in zip(axes, graphs.items()):
        gp.plot_zone_graph(graph, ax, pos, color=BLUE, ink=INK, muted=MUTED, min_share=0.002)
        ax.set_title(title)
    path = fig_dir / "neversink_network_zones.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def distance_zones(xy: np.ndarray, wells: dict, bands=DISTANCE_BANDS) -> tuple:
    """Return zones by plan distance to the nearest priority well, and their names."""
    points = np.array(list(wells.values()))
    distance = np.full(len(xy), np.inf)
    for p in points:
        distance = np.minimum(distance, np.hypot(*(xy - p).T))
    zones = np.digitize(distance, bands[1:-1])
    zones[np.isnan(xy[:, 0])] = -1
    names = [f"< {bands[1]:g} m"]
    names += [f"{lo / 1000:g}–{hi / 1000:g} km" for lo, hi in zip(bands[1:-2], bands[2:-1])]
    names += [f"> {bands[-2] / 1000:g} km"]
    return zones, names


def sources(step, result, xy, wells, fig_dir: Path) -> Path:
    """Draw recharge by distance band to each priority well as an alluvial plot."""
    zones, names = distance_zones(xy, wells)
    groups = list(wf.PRIORITY_WELLS)
    labels, matrix = gp.source_matrix(step, result, groups, zones, names)
    labels = [lab.replace("RCHA | ", "recharge ") for lab in labels]
    fig, ax = plt.subplots(figsize=(7.5, 5.2), constrained_layout=True)
    gp.plot_alluvial(labels, groups, matrix, ax, ORDINAL[: len(labels)], ink=INK, muted=MUTED)
    ax.set_title("Water reaching each priority well by distance of its recharge from the nearest "
                 "priority well [m³/d]", fontsize=9)
    path = fig_dir / "neversink_network_sources.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _zoom_panel(ax, step, result, nodes, xy, title, carried: bool) -> None:
    """Draw one local subgraph, cells coloured by layer, stream reaches as white squares."""
    src, dst, q = gp.subgraph_edges(step, nodes)
    weights = gp.carried_flow(result, "priority", dst, q) if carried else None
    layers = gp.node_layers(step)[nodes]
    colours = [LAYERS[k] for k in layers if k >= 0]
    gp.plot_subgraph(step, nodes, xy, ax, q=weights, edge_color=BLUE, ink=INK, color=colours)
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])


def local_zooms(step, result, xy, fig_dir: Path) -> Path:
    """Draw two cycles and the neighbourhood of one well, layers shifted so vertical flow shows."""
    shifted = gp.shifted_positions(step, xy, LAYER_SHIFT)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), constrained_layout=True)
    for ax, c in zip(axes[:2], CYCLES_SHOWN):
        cycle = result.cycles[c]
        nodes = cycle.cells
        _zoom_panel(ax, step, result, nodes, shifted,
                    f"cycle {c + 1}: {len(nodes)} nodes, {cycle.internal_flow:,.0f} m³/d inside",
                    carried=False)
    well = np.flatnonzero(result.selections[WELL_ZOOM].cells)
    nodes = gp.neighbourhood(step, well, hops=2)
    _zoom_panel(axes[2], step, result, nodes, shifted,
                f"{WELL_ZOOM}, two links out: width q F", carried=True)
    axes[2].scatter(*shifted[well].T, s=90, facecolors="none", edgecolors=INK, lw=1.4, zorder=4)
    handles = [plt.Line2D([], [], ls="", marker="o", mfc=c, mec=INK, mew=0.5) for c in LAYERS]
    handles.append(plt.Line2D([], [], ls="", marker="s", mfc="white", mec=INK, mew=0.5))
    fig.legend(handles, [f"layer {k + 1}" for k in range(4)] + ["stream reach"], loc="lower center",
               ncol=5, bbox_to_anchor=(0.5, -0.06))
    path = fig_dir / "neversink_network_zoom.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def main(out: Path = wf.OUT, fig_dir: Path = wf.FIG_DIR) -> list[Path]:
    """Trace the SFR network step and write the four figures."""
    _style()
    fig_dir.mkdir(parents=True, exist_ok=True)
    step, result, _ = wf.trace_wells(out / "optimal_tight", package_nodes=("SFR",))
    xy = gp.node_positions(step)
    wells = well_points(step, result, xy)
    return [
        stream_network(step, result, xy, wells, fig_dir),
        zone_graphs(step, result, fig_dir),
        sources(step, result, xy, wells, fig_dir),
        local_zooms(step, result, xy, fig_dir),
    ]


if __name__ == "__main__":
    for p in main():
        print(p)
