"""Assemble the linear systems of backward and forward tracing from a FlowStep.

Gross accounting (default). For cell i, with q_ij >= 0 the intercell flow i→j and
q_k the external terms (positive into the cell):
    O_i = sum_j q_ij + sum_{k in i, q_k<0} |q_k|      (total outflow)
    I_i = sum_j q_ji + sum_{k in i, q_k>0} q_k        (total inflow)
    r_i = I_i - O_i                                   (budget residual, reported only)
Backward: F_i - sum_j (q_ij/O_i) F_j = sum_{k in D, q_k<0} |q_k| / O_i
Forward:  G_i - sum_j (q_ji/I_i) G_j = sum_{k in S, q_k>0} q_k / I_i
Cells with O_i = 0 (backward) or I_i = 0 (forward) get an identity row and zero right-hand side.

Net accounting (the reference method, Foley & Black 2013 [FB13]). Edges only:
    s_i = O^edges_i - I^edges_i,   T_i = I^edges_i + max(s_i, 0)
Destination cells are absorbing (f = 1, their out-edges ignored); elsewhere
    f_i = sum_j q_ij f_j / T_i.
Forward net mode is the same on the reversed graph with source cells fixed at g = 1.

Net group inflow. Summing the row equations T_i f_i = sum_j q_ij f_j over the cells outside the
destination group D gives, with s+ = max(s, 0),
    sum_i f_i s+_i = sum_{d in D} T_d - sum_{D->D} q - sum_{D->not D} q_ij f_j
and in forward mode, with S the source group and s- = max(-s, 0),
    sum_i g_i s-_i = sum_{s in S} T_s - sum_{S->S} q - sum_{not S->S} q_ji g_j.
The throughflow sum of the fixed cells counts twice the water passing from one fixed cell to
another and the water that leaves the group and comes back (with share f_j or g_j). The net
destination (source) inflow is the throughflow sum less these two terms (net_double_count), so
it counts each passage once and equals the net volume from (to). It depends on the solved
fractions just outside the group, not on the budget alone. With the solved fractions, volume
from (to) minus the net inflow is exactly the sum of the un-normalised row residuals over the
cells outside the group (gwsource.diagnostics).

Matrices are written in "dependency" form: row i of (I - P) refers to the cells whose values
cell i depends on (downstream cells in backward mode, upstream cells in forward mode).
"""

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from .flowstep import FlowStep, connection_rows
from .selectors import Selection


@dataclass
class Edges:
    """Directed intercell flows src→dst with q > 0."""

    src: np.ndarray
    dst: np.ndarray
    q: np.ndarray

    def subset(self, keep: np.ndarray) -> "Edges":
        """Return the edges where keep is True."""
        return Edges(self.src[keep], self.dst[keep], self.q[keep])


@dataclass
class CellBudget:
    """Per-cell gross flow totals (all non-negative except the residual)."""

    edge_out: np.ndarray
    edge_in: np.ndarray
    source: np.ndarray
    sink: np.ndarray

    @property
    def outflow(self) -> np.ndarray:
        """Total outflow O = intercell outflow + sink terms."""
        return self.edge_out + self.sink

    @property
    def inflow(self) -> np.ndarray:
        """Total inflow I = intercell inflow + source terms."""
        return self.edge_in + self.source

    @property
    def residual(self) -> np.ndarray:
        """Budget residual r = I - O."""
        return self.inflow - self.outflow


def flow_edges(step: FlowStep) -> Edges:
    """Return the directed positive-flow edges from the off-diagonal FLOW-JA-FACE entries."""
    rows = connection_rows(step.ia)
    out = (rows != step.ja) & (step.flowja < 0.0)  # negative flowja: flow out of row cell
    return Edges(src=rows[out], dst=step.ja[out], q=-step.flowja[out])


def term_totals(step: FlowStep, mask: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return per-cell (source, sink) totals of the external terms (optionally masked)."""
    flow = step.term_flow if mask is None else np.where(mask, step.term_flow, 0.0)
    n = step.n_cells
    source = np.bincount(step.term_cell, weights=np.maximum(flow, 0.0), minlength=n)
    sink = np.bincount(step.term_cell, weights=np.maximum(-flow, 0.0), minlength=n)
    return source, sink


def cell_budget(step: FlowStep, edges: Edges | None = None) -> CellBudget:
    """Return the per-cell gross budget of a FlowStep (edges from flow_edges(step) if not given)."""
    if edges is None:
        edges = flow_edges(step)
    n = step.n_cells
    source, sink = term_totals(step)
    return CellBudget(
        edge_out=np.bincount(edges.src, weights=edges.q, minlength=n),
        edge_in=np.bincount(edges.dst, weights=edges.q, minlength=n),
        source=source,
        sink=sink,
    )


def system_matrix(
    n: int, row: np.ndarray, col: np.ndarray, q: np.ndarray, norm: np.ndarray, fixed=None
) -> sp.csr_matrix:
    """Return I - P with P[row, col] = q / norm[row]; rows with norm 0, or fixed, are identity."""
    keep = norm[row] > 0.0
    if fixed is not None:
        keep &= ~fixed[row]
    p = sp.coo_matrix((q[keep] / norm[row[keep]], (row[keep], col[keep])), shape=(n, n))
    return (sp.identity(n, format="csr") - p.tocsr()).tocsr()


def _safe_divide(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """Return num/den where den > 0, else 0 (broadcast over trailing group columns)."""
    den = den.reshape(-1, *([1] * (num.ndim - 1)))
    return np.divide(num, den, out=np.zeros_like(num, dtype=float), where=den > 0.0)


def group_term_flows(step: FlowStep, groups: dict[str, Selection], sign: int) -> np.ndarray:
    """Return (cells, groups) totals of |q| over each group's selected terms of the given sign."""
    flow = np.maximum(sign * step.term_flow, 0.0)
    out = np.zeros((step.n_cells, len(groups)))
    for g, sel in enumerate(groups.values()):
        weights = np.where(sel.terms, flow, 0.0)
        out[:, g] = np.bincount(step.term_cell, weights=weights, minlength=step.n_cells)
    return out


# ---------------------------------------------------------------- gross accounting


def gross_backward_system(
    step: FlowStep, edges: Edges, budget: CellBudget, groups: dict[str, Selection]
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Return (I - P, S D) for gross backward tracing; one right-hand-side column per group."""
    outflow = budget.outflow
    matrix = system_matrix(step.n_cells, edges.src, edges.dst, edges.q, outflow)
    rhs = _safe_divide(group_term_flows(step, groups, sign=-1), outflow)
    return matrix, rhs


def gross_forward_system(
    step: FlowStep, edges: Edges, budget: CellBudget, groups: dict[str, Selection]
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Return (I - Q, R T) for gross forward tracing; one right-hand-side column per group."""
    inflow = budget.inflow
    matrix = system_matrix(step.n_cells, edges.dst, edges.src, edges.q, inflow)
    rhs = _safe_divide(group_term_flows(step, groups, sign=+1), inflow)
    return matrix, rhs


# ---------------------------------------------------------------- net accounting


def net_balance(n: int, edges: Edges) -> tuple[np.ndarray, np.ndarray]:
    """Return (s, T): net source s = O^edges - I^edges and throughflow T = I^edges + max(s, 0)."""
    edge_out = np.bincount(edges.src, weights=edges.q, minlength=n)
    edge_in = np.bincount(edges.dst, weights=edges.q, minlength=n)
    s = edge_out - edge_in
    return s, edge_in + np.maximum(s, 0.0)


def net_system(
    n: int, edges: Edges, fixed: np.ndarray, throughflow: np.ndarray, backward: bool
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Return (matrix, rhs) of net-mode tracing with the fixed cells set to 1."""
    row, col = (edges.src, edges.dst) if backward else (edges.dst, edges.src)
    matrix = system_matrix(n, row, col, edges.q, throughflow, fixed=fixed)
    return matrix, fixed.astype(float)


def net_double_count(
    edges: Edges, fixed: np.ndarray, fraction: np.ndarray, backward: bool = True
) -> tuple[float, float]:
    """Return the water the fixed cells' T sum counts twice: (inside, boundary x f) (module doc)."""
    near, far = (edges.src, edges.dst) if backward else (edges.dst, edges.src)
    inside = fixed[near] & fixed[far]
    leaving = fixed[near] & ~fixed[far]
    within = float(edges.q[inside].sum())
    returning = float(np.sum(edges.q[leaving] * fraction[far[leaving]]))
    return within, returning


def absorbing_edges(edges: Edges, fixed: np.ndarray, backward: bool) -> Edges:
    """Return the edges left once the fixed cells absorb (backward: drop their out-edges)."""
    cut = fixed[edges.src] if backward else fixed[edges.dst]
    return edges.subset(~cut)
