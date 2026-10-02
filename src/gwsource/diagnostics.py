"""Budget residuals, closure and forward/backward duality checks, and the cycle report.

Exact identities of gross accounting (they follow from summing the unnormalised row equations
O_i F_i - sum_j q_ij F_j = d_i and I_i G_i - sum_j q_ji G_j = b_i over all cells; rows with
O_i = 0 or I_i = 0 satisfy them trivially). With r_i = I_i - O_i, Src_i and Snk_i the cell's
source and sink totals, d the destination sink flows and b the selected source flows:

    backward closure:  sum_i F_i Src_i - sum_i F_i r_i = sum_{k in D} |q_k|
    forward closure:   sum_i G_i Snk_i + sum_i G_i r_i = sum_{k in S} q_k
    duality:           sum_{k in S} F_{c(k)} q_k - sum_{k in D} G_{c(k)} |q_k| = sum_i F_i G_i r_i

So with the residual term the checks hold to round-off; without it they hold to within the
model's budget error (|sum F r| <= sum |r|, since 0 <= F <= 1).

Cycle report: cycle_report() lists every strongly connected set of the flow graph with the flow
that goes round it (by cycle cancelling) and its share of the model throughflow; cycle_table()
and cycle_ids() turn it into rows and a per-cell array for export.
"""

from dataclasses import dataclass

import numpy as np

from .assemble import Edges, cell_budget, flow_edges
from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult
from .solve import Cycle, _walk_to_cycle, find_cycles, strong_components


@dataclass
class Check:
    """Both sides of an identity and its error, with and without the residual term."""

    lhs: float
    rhs: float
    residual_term: float

    @property
    def error(self) -> float:
        """lhs - residual_term - rhs (zero to round-off)."""
        return self.lhs - self.residual_term - self.rhs

    @property
    def error_without_residual(self) -> float:
        """lhs - rhs, i.e. the error if the budget residual is ignored."""
        return self.lhs - self.rhs

    @property
    def relative_error(self) -> float:
        """|error| relative to |rhs| (or 1 if rhs is zero)."""
        return abs(self.error) / abs(self.rhs) if self.rhs != 0.0 else abs(self.error)


def cell_residual(step: FlowStep) -> np.ndarray:
    """Return the per-cell budget residual r = I - O (positive: more water in than out)."""
    return cell_budget(step, flow_edges(step)).residual


def budget_error(step: FlowStep) -> dict[str, float]:
    """Return the total absolute residual, total throughflow and their ratio."""
    budget = cell_budget(step, flow_edges(step))
    abs_residual = float(np.abs(budget.residual).sum())
    throughflow = float(np.maximum(budget.inflow, budget.outflow).sum())
    return {
        "abs_residual": abs_residual,
        "throughflow": throughflow,
        "relative": abs_residual / throughflow if throughflow > 0 else 0.0,
    }


def backward_closure(step: FlowStep, result: BackwardResult, group: str) -> Check:
    """Return the closure check sum(volume from) - sum(F r) = destination inflow (gross only)."""
    assert result.accounting == "gross", "closure identity is for gross accounting"
    r = cell_residual(step)
    f = result.fraction_through[group]
    return Check(
        lhs=float(result.volume_from[group].sum()),
        rhs=result.destination_inflow[group],
        residual_term=float(np.dot(f, r)),
    )


def forward_closure(step: FlowStep, result: ForwardResult, group: str) -> Check:
    """Return the closure check sum(volume to) + sum(G r) = source inflow (gross only)."""
    assert result.accounting == "gross", "closure identity is for gross accounting"
    r = cell_residual(step)
    g = result.source_fraction[group]
    return Check(
        lhs=float(result.volume_to[group].sum()),
        rhs=result.source_inflow[group],
        residual_term=-float(np.dot(g, r)),
    )


def duality(
    step: FlowStep,
    back: BackwardResult,
    dest_group: str,
    fwd: ForwardResult,
    source_group: str,
) -> Check:
    """Return the flow from a source group to a destination group, computed both ways (gross)."""
    assert back.accounting == fwd.accounting == "gross", "duality identity is for gross accounting"
    f = back.fraction_through[dest_group]
    g = fwd.source_fraction[source_group]
    q = step.term_flow
    sources = fwd.selections[source_group].terms & (q > 0.0)
    sinks = back.selections[dest_group].terms & (q < 0.0)
    via_backward = float(np.dot(f[step.term_cell[sources]], q[sources]))
    via_forward = float(np.dot(g[step.term_cell[sinks]], -q[sinks]))
    residual_term = float(np.sum(f * g * cell_residual(step)))
    return Check(lhs=via_backward, rhs=via_forward, residual_term=residual_term)


def cancel_cycles(edges: Edges, max_cancellations: int = 100_000) -> tuple[float, float, bool]:
    """Decompose the circulation of a flow graph by cycle cancelling.

    Repeatedly find a directed cycle, subtract its smallest edge flow from every edge on it and
    drop the emptied edge, until no cycle is left. Returns (circulation, circulating edge flow,
    complete): circulation is the sum of the cancelled cycle flows; circulating edge flow is the
    sum over cancelled cycles of cycle flow x cycle length, i.e. the throughflow the cells of the
    set carry only because water goes round. The decomposition is not unique; it is a measure
    of how much flow goes round, not a unique quantity. complete is False if max_cancellations
    was reached first.
    """
    q = edges.q.astype(float).copy()
    nodes, local = np.unique(np.concatenate([edges.src, edges.dst]), return_inverse=True)
    src, dst = local[: len(q)], local[len(q) :]
    n, keep = len(nodes), q > 0.0
    circulation = carried = 0.0
    for _ in range(max_cancellations):
        _, labels = strong_components(n, src[keep], dst[keep])
        sizes = np.bincount(labels, minlength=n)
        if sizes.max(initial=0) <= 1:
            return circulation, carried, True
        for label in np.flatnonzero(sizes > 1):
            idx = np.flatnonzero(keep & (labels[src] == label) & (labels[dst] == label))
            out_edges: dict[int, list[int]] = {}
            for e in idx:
                out_edges.setdefault(int(src[e]), []).append(int(e))
            cycle = np.asarray(_walk_to_cycle(int(src[idx[0]]), out_edges, dst))
            flow = q[cycle].min()
            q[cycle] -= flow
            keep[cycle[np.argmin(q[cycle])]] = False
            keep[cycle[q[cycle] <= 0.0]] = False
            circulation += flow
            carried += flow * len(cycle)
    return circulation, carried, False


def cycle_report(
    step: FlowStep, result: BackwardResult | ForwardResult | None = None
) -> list[Cycle]:
    """Return the flow cycles of a step with their circulation, largest circulation first.

    For each strongly connected set: the cells, the flow on its internal edges, the circulation
    found by cycle cancelling, the circulating throughflow (circulation x cycle length) and its
    share of the total model throughflow (sum of cell outflows). Sets reported as closed loops
    by a trace result are flagged closed.
    """
    edges = flow_edges(step)
    total = float(cell_budget(step, edges).outflow.sum())
    closed = np.zeros(step.n_cells, dtype=bool)
    for cells in [] if result is None else result.closed_loops:
        closed[cells] = True
    cycles = find_cycles(step.n_cells, edges)
    for cycle in cycles:
        inside = np.zeros(step.n_cells, dtype=bool)
        inside[cycle.cells] = True
        internal = edges.subset(inside[edges.src] & inside[edges.dst])
        cycle.circulation, cycle.circulating_throughflow, _ = cancel_cycles(internal)
        cycle.throughflow_share = cycle.circulating_throughflow / total if total > 0 else 0.0
        cycle.closed = bool(closed[cycle.cells].all())
    return sorted(cycles, key=lambda c: -c.circulation)


def cycle_table(cycles: list[Cycle]) -> list[dict]:
    """Return one row (dict) per cycle: id, size, flows, share and the 0-based cells."""
    return [
        {
            "cycle": i,
            "n_cells": c.n_cells,
            "internal_flow": c.internal_flow,
            "min_edge_flow": c.min_edge_flow,
            "circulation": c.circulation,
            "circulating_throughflow": c.circulating_throughflow,
            "throughflow_share": c.throughflow_share,
            "closed": c.closed,
            "cells": " ".join(str(int(n)) for n in c.cells),
        }
        for i, c in enumerate(cycles)
    ]


def cycle_ids(n_cells: int, cycles: list[Cycle]) -> np.ndarray:
    """Return, per cell, the index of the cycle it belongs to, or -1."""
    ids = np.full(n_cells, -1, dtype=np.int64)
    for i, c in enumerate(cycles):
        ids[c.cells] = i
    return ids
