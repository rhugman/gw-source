"""Plots of the flow graph: the package network on a map, a zone graph and a local zoom.

The full graph of a model is mostly cell-to-cell flows and is better shown as maps of per-cell
values (gwsource.export). The views here draw the parts of the graph that a node-link drawing
does show well:

- package network: the package nodes (SFR reaches, lakes, MAW wells, UZF cells) at the mean
  centre of the cells they exchange water with, their links to each other (package FLOW-JA-FACE,
  lake outlets, MVR) as lines, line width the flow on the link;
- zone graph: the graph condensed to a few zones (for example the model layers and each package),
  with the flow between zones and the source and sink terms of each zone;
- local zoom: a handful of nodes (a cycle, the neighbourhood of a well) with every edge between
  them drawn as an arrow, in plan with each layer shifted so that vertical flows show.

Water that reaches a group. In a backward result, F_j is the share of the water passing through
node j that reaches the group (fraction_through). The water on an edge i -> j that reaches the
group is q_ij F_j, and the water from a source term of node i that reaches it is s_i F_i. Summed
over the source terms this is the group's volume_from. Every view takes these weights in place
of the plain flows, so the same drawing shows where all the water goes or only the water that
reaches the group.

Data functions return numpy arrays and need only numpy; the plot functions import matplotlib.
"""

from dataclasses import dataclass

import numpy as np

from .flowstep import FlowStep
from .metrics import BackwardResult


@dataclass
class ZoneGraph:
    """The flow graph condensed to zones.

    flow[a, b] is the flow from zone a to zone b; term_in[name][a] and term_out[name][a] are the
    source and sink terms of zone a by package (both positive).
    """

    names: list[str]
    flow: np.ndarray
    term_in: dict[str, np.ndarray]
    term_out: dict[str, np.ndarray]


# ---------------------------------------------------------------- graph data


def edge_list(step: FlowStep) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (src, dst, q), one entry per directed edge with flow q > 0 from src to dst."""
    row = np.repeat(np.arange(len(step.ia) - 1), np.diff(step.ia))
    into = (step.flowja > 0) & (row != step.ja)
    return step.ja[into], row[into], step.flowja[into]


def carried_flow(
    result: BackwardResult, group: str, dst: np.ndarray, q: np.ndarray
) -> np.ndarray:
    """Return q F_dst, the part of each edge flow that reaches the group."""
    return q * result.fraction_through[group][dst]


def term_weights(step: FlowStep, result: BackwardResult, group: str) -> np.ndarray:
    """Return per term the part of its flow that reaches the group (sources F, sinks selected)."""
    f = result.fraction_through[group][step.term_cell]
    selected = result.selections[group].terms
    return np.where(step.term_flow > 0, f, selected.astype(float))


def zone_graph(
    step: FlowStep,
    zones: np.ndarray,
    names: list[str],
    edge_weight: np.ndarray | None = None,
    term_weight: np.ndarray | None = None,
) -> ZoneGraph:
    """Condense the graph to zones (zones[node] in 0..len(names)-1, -1 to leave a node out).

    edge_weight scales each edge of edge_list(step) and term_weight each term; give both from
    carried_flow and term_weights for the water that reaches a group.
    """
    zones = np.asarray(zones)
    assert len(zones) == len(step.ia) - 1, "zones needs one entry per node"
    n = len(names)
    src, dst, q = edge_list(step)
    if edge_weight is not None:
        q = q * edge_weight
    a, b = zones[src], zones[dst]
    keep = (a >= 0) & (b >= 0) & (a != b)
    flow = np.zeros((n, n))
    np.add.at(flow, (a[keep], b[keep]), q[keep])
    tq = step.term_flow if term_weight is None else step.term_flow * term_weight
    tz = zones[step.term_cell]
    term_in, term_out = {}, {}
    for p, package in enumerate(step.packages):
        mask = (step.term_package == p) & (tz >= 0)
        term_in[package.name] = np.bincount(tz[mask], np.maximum(tq[mask], 0.0), minlength=n)
        term_out[package.name] = np.bincount(tz[mask], np.maximum(-tq[mask], 0.0), minlength=n)
    return ZoneGraph(list(names), flow, term_in, term_out)


def layer_zones(step: FlowStep) -> tuple[np.ndarray, list[str]]:
    """Return zones and names: one zone per layer of each DIS/DISV model and one per package."""
    zones = np.full(len(step.ia) - 1, -1)
    names = []
    for block in step.blocks:
        local = np.arange(block.n)
        if block.kind == "model" and block.grid_type in ("DIS", "DISV"):
            per_layer = block.n // block.grid_shape[0]
            zones[block.offset + local] = len(names) + local // per_layer
            prefix = f"{block.name} " if len(step.model_names) > 1 else ""
            names += [f"{prefix}layer {k + 1}" for k in range(block.grid_shape[0])]
        else:
            zones[block.offset + local] = len(names)
            names.append(block.name.split("/")[-1])
    return zones, names


def source_matrix(
    step: FlowStep,
    result: BackwardResult,
    groups: list[str],
    zones: np.ndarray | None = None,
    zone_names: list[str] | None = None,
) -> tuple[list[str], np.ndarray]:
    """Return (labels, V): V[s, g] the water from source s reaching group g [L3/T].

    A source is a term package (volume_from_by_term) or, with zones, a package in a zone of
    entry ('<package> | <zone>'). Sources that give no water to any group are left out.
    """
    labels, rows = [], []
    for package in result.volume_from_by_term[groups[0]]:
        per_group = np.array([result.volume_from_by_term[g][package] for g in groups])
        if zones is None:
            labels.append(package)
            rows.append(per_group.sum(axis=1))
            continue
        for z, name in enumerate(zone_names):
            labels.append(f"{package} | {name}")
            rows.append(per_group[:, zones == z].sum(axis=1))
    matrix = np.array(rows)
    keep = matrix.sum(axis=1) > 0
    return [lab for lab, k in zip(labels, keep) if k], matrix[keep]


def neighbourhood(step: FlowStep, nodes, hops: int = 1) -> np.ndarray:
    """Return the nodes within hops edges of nodes (either direction), sorted."""
    current = np.unique(np.asarray(nodes))
    for _ in range(hops):
        rows = [step.ja[step.ia[n] : step.ia[n + 1]] for n in current]
        current = np.unique(np.concatenate([current, *rows]))
    return current


def subgraph_edges(step: FlowStep, nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (src, dst, q) of the edges with both ends in nodes."""
    src, dst, q = edge_list(step)
    keep = np.isin(src, nodes) & np.isin(dst, nodes)
    return src[keep], dst[keep], q[keep]


def node_layers(step: FlowStep) -> np.ndarray:
    """Return the 0-based layer of each DIS/DISV cell; -1 for package nodes and DISU cells."""
    layers = np.full(len(step.ia) - 1, -1)
    for block in step.blocks:
        if block.kind == "model" and block.grid_type in ("DIS", "DISV"):
            per_layer = block.n // block.grid_shape[0]
            layers[block.offset : block.offset + block.n] = np.arange(block.n) // per_layer
    return layers


def node_positions(step: FlowStep) -> np.ndarray:
    """Return (x, y) of every node: cell centres and package points (NaN where unknown)."""
    from .export import cell_centres, package_points

    xy = np.full((len(step.ia) - 1, 2), np.nan)
    for block in step.blocks:
        grb_file = step.notes.get("model_notes", {}).get(block.model, {}).get("grb_file")
        if block.kind == "model" and grb_file is not None:
            xy[block.offset : block.offset + block.n] = cell_centres(grb_file)
    for node, point in package_points(step).items():
        xy[node] = point
    return xy


def shifted_positions(step: FlowStep, xy: np.ndarray, shift: tuple[float, float]) -> np.ndarray:
    """Return xy with layer k moved by k * shift and package nodes by -1 * shift."""
    layers = node_layers(step)
    return xy + np.outer(layers, shift)


def package_block(step: FlowStep, name: str):
    """Return the package NodeBlock whose label or name ends with name (e.g. 'SFR_0')."""
    blocks = [b for b in step.blocks if b.kind == "package" and b.label.endswith(name)]
    assert len(blocks) == 1, f"expected one package block matching {name!r}, found {len(blocks)}"
    return blocks[0]


def package_net_exchange(step: FlowStep, block) -> np.ndarray:
    """Return per package node the net flow from the aquifer into it (positive: gaining node)."""
    assert block.kind == "package", "block must be a package block"
    src, dst, q = edge_list(step)
    lo, hi = block.offset, block.offset + block.n
    is_cell = np.zeros(len(step.ia) - 1, dtype=bool)
    for b in step.blocks:
        if b.kind == "model":
            is_cell[b.offset : b.offset + b.n] = True
    net = np.zeros(block.n)
    into = (dst >= lo) & (dst < hi) & is_cell[src]
    out = (src >= lo) & (src < hi) & is_cell[dst]
    np.add.at(net, dst[into] - lo, q[into])
    np.subtract.at(net, src[out] - lo, q[out])
    return net


# ---------------------------------------------------------------- plots


def _widths(q: np.ndarray, qmax: float, wmax: float, wmin: float = 0.15) -> np.ndarray:
    """Return line widths scaled with the square root of q (wmin at q -> 0, wmax at qmax)."""
    return wmin + (wmax - wmin) * np.sqrt(np.clip(q / qmax, 0.0, 1.0))


def plot_package_network(
    step: FlowStep,
    block,
    xy: np.ndarray,
    ax,
    q: np.ndarray | None = None,
    color: np.ndarray | None = None,
    wmax: float = 3.0,
    wmin: float = 0.15,
    qmax: float | None = None,
    **kwargs,
):
    """Draw the links between the nodes of one package block; return the LineCollection.

    q gives one value per link of package_links(step, block) (default: the link flows); color, if
    given, one value per link for the colormap (kwargs go to LineCollection: cmap, norm, ...).
    """
    from matplotlib.collections import LineCollection

    src, dst, flow = package_links(step, block)
    q = flow if q is None else q
    qmax = q.max() if qmax is None else qmax
    segments = np.stack([xy[src], xy[dst]], axis=1)
    widths = _widths(q, qmax, wmax, wmin)
    lines = LineCollection(segments, linewidths=widths, capstyle="round", **kwargs)
    if color is not None:
        lines.set_array(color)
    ax.add_collection(lines)
    ax.autoscale_view()
    ax.set_aspect("equal")
    return lines


def package_links(step: FlowStep, block) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (src, dst, q) of the edges between nodes of one package block (incl. MVR)."""
    src, dst, q = edge_list(step)
    lo, hi = block.offset, block.offset + block.n
    keep = (src >= lo) & (src < hi) & (dst >= lo) & (dst < hi)
    return src[keep], dst[keep], q[keep]


def ring_layout(names: list[str], radius: float = 2.0) -> dict[str, np.ndarray]:
    """Return zone positions on a circle, the first at the top and the rest clockwise."""
    angles = 0.5 * np.pi - 2.0 * np.pi * np.arange(len(names)) / len(names)
    return {name: radius * np.array([np.cos(a), np.sin(a)]) for name, a in zip(names, angles)}


def plot_zone_graph(
    graph: ZoneGraph,
    ax,
    pos: dict[str, np.ndarray] | None = None,
    qmax: float | None = None,
    wmax: float = 14.0,
    min_share: float = 0.005,
    term_length: float = 1.5,
    color: str = "#2a78d6",
    ink: str = "#0b0b0b",
    muted: str = "#52514e",
    fmt: str = "{:,.0f}",
) -> None:
    """Draw a zone graph: net flows between zones as straight arrows, terms pointing outwards.

    pos defaults to ring_layout(graph.names). Flows below min_share of the largest flow are
    left out. Each zone's source terms come in, and its sink terms leave, along the direction
    away from the centre of the layout, sources turned to one side and sinks to the other.
    """
    from matplotlib.patches import FancyArrowPatch

    pos = ring_layout(graph.names) if pos is None else pos
    points = np.array([pos[name] for name in graph.names], dtype=float)
    centre = points.mean(axis=0)
    net = graph.flow - graph.flow.T
    largest = max(net.max(), *(v.max() for v in graph.term_in.values()),
                  *(v.max() for v in graph.term_out.values()))
    qmax = largest if qmax is None else qmax
    cut = min_share * qmax

    def arrow(p0, p1, q, shrink_a=20, shrink_b=20):
        width = _widths(np.array([q]), qmax, wmax, 0.6)[0]
        ax.add_patch(FancyArrowPatch(
            p0, p1, linewidth=width, color=color, alpha=0.85, shrinkA=shrink_a,
            shrinkB=shrink_b, zorder=2,
            arrowstyle=f"-|>,head_length={0.3 + 0.05 * width},head_width={0.15 + 0.04 * width}",
            mutation_scale=10,
        ))

    def label(xy, text, **kwargs):
        ax.annotate(text, xy, fontsize=7.5, color=muted, zorder=4, **kwargs)

    for a, b in zip(*np.nonzero(net > cut)):
        arrow(points[a], points[b], net[a, b])
        label(0.5 * (points[a] + points[b]), fmt.format(net[a, b]), ha="center", va="center",
              bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85})
    for z, zone in enumerate(graph.names):
        p = points[z]
        out = p - centre
        base = np.arctan2(out[1], out[0]) if np.hypot(*out) > 0 else 0.0
        ins = [(n, v[z]) for n, v in graph.term_in.items() if v[z] > cut]
        outs = [(n, v[z]) for n, v in graph.term_out.items() if v[z] > cut]
        for side, items in ((1, ins), (-1, outs)):
            for i, (name, q) in enumerate(items):
                angle = base + side * (0.3 + 0.3 * i)
                far = p + term_length * np.array([np.cos(angle), np.sin(angle)])
                if side > 0:
                    arrow(far, p, q, shrink_a=2)
                else:
                    arrow(p, far, q, shrink_b=2)
                label(far, f"{name.split(':')[-1]} {fmt.format(q)}", **_alignment(angle))
        ax.annotate(zone, p, ha="center", va="center", fontsize=8.5, color=ink, zorder=5,
                    bbox={"boxstyle": "round,pad=0.4", "fc": "white", "ec": muted, "lw": 0.8})
    reach = term_length + 1.2
    ax.set_xlim(points[:, 0].min() - reach, points[:, 0].max() + reach)
    ax.set_ylim(points[:, 1].min() - reach, points[:, 1].max() + reach)
    ax.set_aspect("equal")
    ax.set_axis_off()


def _alignment(angle: float) -> dict[str, str]:
    """Return ha, va that put a label beyond the end of an arrow pointing at angle."""
    c, s = np.cos(angle), np.sin(angle)
    ha = "left" if c > 0.2 else "right" if c < -0.2 else "center"
    va = "bottom" if s > 0.2 else "top" if s < -0.2 else "center"
    return {"ha": ha, "va": va}


def plot_alluvial(
    labels: list[str],
    groups: list[str],
    matrix: np.ndarray,
    ax,
    colors: list[str],
    gap: float = 0.02,
    ink: str = "#0b0b0b",
    muted: str = "#52514e",
    fmt: str = "{:,.0f}",
) -> None:
    """Draw sources (left) to groups (right) as bands of width V[s, g]; colors one per source."""
    from matplotlib.patches import Rectangle

    total = matrix.sum()
    scale = (1.0 - gap * (max(len(labels), len(groups)) - 1)) / total
    t = np.linspace(0.0, 1.0, 60)
    ease = 0.5 - 0.5 * np.cos(np.pi * t)

    def stacks(sizes):
        tops, y = [], 1.0
        for s in sizes:
            tops.append(y)
            y -= s * scale + gap
        return tops

    left, right = stacks(matrix.sum(axis=1)), stacks(matrix.sum(axis=0))
    right_fill = list(right)
    for s, label in enumerate(labels):
        y_left = left[s]
        for g in range(len(groups)):
            h = matrix[s, g] * scale
            if h <= 0:
                continue
            top = y_left + (right_fill[g] - y_left) * ease
            ax.fill_between(0.06 + 0.88 * t, top - h, top, color=colors[s], alpha=0.55, lw=0)
            y_left -= h
            right_fill[g] -= h
        h = matrix[s].sum() * scale
        ax.add_patch(Rectangle((0.0, left[s] - h), 0.06, h, color=colors[s], lw=0))
        ax.annotate(f"{label}  {fmt.format(matrix[s].sum())}", (0.0, left[s] - h / 2),
                    xytext=(-4, 0), textcoords="offset points", ha="right", va="center",
                    fontsize=8, color=ink)
    for g, group in enumerate(groups):
        h = matrix[:, g].sum() * scale
        ax.add_patch(Rectangle((0.94, right[g] - h), 0.06, h, color=muted, lw=0))
        ax.annotate(f"{group}  {fmt.format(matrix[:, g].sum())}", (1.0, right[g] - h / 2),
                    xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=8, color=ink)
    ax.set_xlim(0, 1)
    ax.set_ylim(min(left[-1], right[-1]) - matrix.max() * scale - gap, 1.0 + gap)
    ax.set_axis_off()


def plot_subgraph(
    step: FlowStep,
    nodes: np.ndarray,
    xy: np.ndarray,
    ax,
    q: np.ndarray | None = None,
    node_values: np.ndarray | None = None,
    wmax: float = 4.0,
    edge_color: str = "#2a78d6",
    ink: str = "#0b0b0b",
    package_color: str = "white",
    **scatter_kwargs,
):
    """Draw the edges among nodes as arrows (width from q, default the flows); return the scatter.

    q, if given, has one value per edge of subgraph_edges(step, nodes). Cells are circles,
    coloured by node_values (kwargs go to scatter: cmap, vmin, vmax, ...); package nodes are
    squares in package_color.
    """
    from matplotlib.patches import FancyArrowPatch

    src, dst, flow = subgraph_edges(step, nodes)
    q = flow if q is None else q
    qmax = max(q.max(), 1e-30)
    for s, d, w in zip(src, dst, _widths(q, qmax, wmax, 0.3)):
        ax.add_patch(FancyArrowPatch(
            xy[s], xy[d], arrowstyle="-|>", mutation_scale=6 + 2 * w, linewidth=w,
            color=edge_color, alpha=0.8, shrinkA=5, shrinkB=5, zorder=2,
        ))
    cells = node_layers(step)[nodes] >= 0
    points = ax.scatter(xy[nodes[cells], 0], xy[nodes[cells], 1],
                        c=None if node_values is None else node_values[cells], s=30,
                        edgecolors=ink, linewidths=0.5, zorder=3, **scatter_kwargs)
    ax.scatter(xy[nodes[~cells], 0], xy[nodes[~cells], 1], marker="s", s=30, c=package_color,
               edgecolors=ink, linewidths=0.5, zorder=3)
    ax.set_aspect("equal")
    return points
