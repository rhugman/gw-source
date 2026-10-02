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
"""

from dataclasses import dataclass

import numpy as np

from .assemble import cell_budget, flow_edges
from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult
from .solve import Cycle, find_cycles


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


def cycle_report(step: FlowStep) -> list[Cycle]:
    """Return the flow cycles of a step, largest internal flow first."""
    cycles = find_cycles(step.n_cells, flow_edges(step))
    return sorted(cycles, key=lambda c: -c.internal_flow)
