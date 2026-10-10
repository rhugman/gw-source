"""Public entry points: backward (capture) and forward (fate) tracing of one FlowStep."""

from dataclasses import dataclass

import numpy as np

from .assemble import (
    Edges,
    absorbing_edges,
    cell_budget,
    flow_edges,
    gross_backward_system,
    gross_forward_system,
    group_term_flows,
    net_balance,
    net_double_count,
    net_system,
)
from .config import TraceConfig
from .flowstep import FlowStep
from .metrics import (
    BackwardResult,
    ForwardResult,
    backward_metrics,
    forward_metrics,
    per_cell_by_package,
)
from .selectors import Selection
from .solve import (
    Factor,
    dependency_graph,
    factorize,
    find_cycles,
    isolate_closed_loops,
    remove_cycle_edges,
)


def _check_groups(step: FlowStep, groups: dict[str, Selection]) -> None:
    """Assert that groups is a non-empty dict of Selections sized for this step."""
    assert isinstance(groups, dict) and groups, "groups must be a non-empty dict {name: Selection}"
    for name, sel in groups.items():
        assert len(sel.terms) == step.n_terms and len(sel.cells) == step.n_cells, (
            f"group {name!r} was selected on a different FlowStep"
        )


def backward(
    step: FlowStep, groups: dict[str, Selection], config: TraceConfig | None = None
) -> BackwardResult:
    """Trace backward from each destination group: fraction and volume of water reaching it."""
    config = TraceConfig() if config is None else config
    _check_groups(step, groups)
    edges = flow_edges(step)
    if config.accounting == "net":
        result = _net_backward(step, groups, edges, config)
    else:
        result = _gross_backward(step, groups, edges, config)
    result.cycles = find_cycles(step.n_cells, edges)
    return result


def forward(
    step: FlowStep, groups: dict[str, Selection], config: TraceConfig | None = None
) -> ForwardResult:
    """Trace forward from each source group: fraction of water in each cell that came from it."""
    config = TraceConfig() if config is None else config
    _check_groups(step, groups)
    edges = flow_edges(step)
    if config.accounting == "net":
        result = _net_forward(step, groups, edges, config)
    else:
        result = _gross_forward(step, groups, edges, config)
    result.cycles = find_cycles(step.n_cells, edges)
    return result


def _solve(matrix, rhs: np.ndarray, config: TraceConfig) -> tuple[np.ndarray, Factor, list]:
    """Isolate closed recirculation loops, factorise and solve; return (X, factor, loops)."""
    graph = None if config.solver == "lu" else dependency_graph(matrix)
    matrix, rhs, loops = isolate_closed_loops(matrix, rhs, config.closed_loop_tol, graph)
    graph = None if loops else graph  # isolating loops changes the components
    factor = factorize(matrix, config.solver, graph)
    if loops:
        factor.zero_rows = np.concatenate(loops)
    return factor.solve(rhs), factor, loops


def _gross_backward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> BackwardResult:
    """Gross-accounting backward trace: one solve with a column per group."""
    budget = cell_budget(step, edges)
    matrix, rhs = gross_backward_system(step, edges, budget, groups)
    fraction, factor, loops = _solve(matrix, rhs, config)
    destination = group_term_flows(step, groups, sign=-1).sum(axis=0)
    by_package = per_cell_by_package(step, sign=+1)
    result = backward_metrics(
        step, groups, fraction, budget.outflow, budget.source, by_package, destination, "gross"
    )
    result.solver_used = [factor.kind]
    result.closed_loops = loops
    result.factor = factor
    return result


def _gross_forward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> ForwardResult:
    """Gross-accounting forward trace: one solve with a column per group."""
    budget = cell_budget(step, edges)
    matrix, rhs = gross_forward_system(step, edges, budget, groups)
    fraction, factor, loops = _solve(matrix, rhs, config)
    source = group_term_flows(step, groups, sign=+1).sum(axis=0)
    by_package = per_cell_by_package(step, sign=-1)
    result = forward_metrics(
        step, groups, fraction, budget.inflow, budget.sink, by_package, source, "gross"
    )
    result.solver_used = [factor.kind]
    result.closed_loops = loops
    result.factor = factor
    return result


def _net_edges(
    n: int, edges: Edges, fixed: np.ndarray, backward: bool, remove_cycles: bool
) -> Edges:
    """Return the edges used in net mode, after optional min-edge cycle removal.

    Cycles are searched with the fixed cells absorbing (their out-edges, or in-edges in forward
    mode, cut), as in the reference method; the removed edges are then dropped from the graph.
    """
    if not remove_cycles:
        return edges
    cut = fixed[edges.src] if backward else fixed[edges.dst]
    candidates = np.flatnonzero(~cut)
    keep_sub = remove_cycle_edges(n, absorbing_edges(edges, fixed, backward))
    keep = np.ones(len(edges.q), dtype=bool)
    keep[candidates[~keep_sub]] = False
    return edges.subset(keep)


def net_fixed_cells(step: FlowStep, sel: Selection, sign: int) -> np.ndarray:
    """Return the cells fixed at 1: sel.cells, or the cells where selected terms flow with sign.

    A pure cell or zone selection keeps its cells. A selection with term criteria fixes a cell
    if any selected entry in it flows in the traced direction: sign -1 (a sink) backward, +1 (a
    source) forward, as term_flow is positive into the cell. A cell with selected entries of
    both signs is fixed in both directions; a group with no such entry fixes no cell.
    """
    assert sign in (-1, 1), "sign must be -1 (backward, sinks) or +1 (forward, sources)"
    if not sel.term_criteria:
        return sel.cells
    fixed = np.zeros(step.n_cells, dtype=bool)
    fixed[step.term_cell[sel.terms & (sign * step.term_flow > 0.0)]] = True
    return fixed


@dataclass
class NetSolution:
    """Net-mode fractions, per-cell s and T and fixed cells (cells, groups), edges per group."""

    fraction: np.ndarray
    s: np.ndarray
    throughflow: np.ndarray
    fixed: np.ndarray
    used: list[Edges]
    solvers: list[str]
    loops: list[np.ndarray]


def _net_solve(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig, backward: bool
) -> NetSolution:
    """Solve net mode group by group, with each group's cells fixed by net_fixed_cells."""
    n, n_groups = step.n_cells, len(groups)
    fraction, s_all, t_all = (np.zeros((n, n_groups)) for _ in range(3))
    fixed_all = np.zeros((n, n_groups), dtype=bool)
    used_all, solvers, closed = [], [], np.zeros(n, dtype=bool)
    sign = -1 if backward else +1
    for g, sel in enumerate(groups.values()):
        fixed = net_fixed_cells(step, sel, sign)
        used = _net_edges(n, edges, fixed, backward, config.remove_cycles)
        s, throughflow = net_balance(n, used)
        matrix, rhs = net_system(n, used, fixed, throughflow, backward)
        fraction[:, g], factor, loops = _solve(matrix, rhs, config)
        s_all[:, g], t_all[:, g], fixed_all[:, g] = s, throughflow, fixed
        used_all.append(used)
        solvers.append(factor.kind)
        for cells in loops:
            closed[cells] = True
    loops = _loops_from_mask(n, edges, closed)
    return NetSolution(fraction, s_all, t_all, fixed_all, used_all, solvers, loops)


def _net_group_inflow(
    used: list[Edges],
    fixed: np.ndarray,
    fraction: np.ndarray,
    throughflow: np.ndarray,
    backward: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Return per group (inflow with each passage counted once, the fixed cells' T sum)."""
    t_sum = (throughflow * fixed).sum(axis=0)
    double = np.array(
        [
            net_double_count(used[g], fixed[:, g], fraction[:, g], backward)
            for g in range(fixed.shape[1])
        ]
    )
    return t_sum - double[:, 0] - double[:, 1], t_sum


def _loops_from_mask(n: int, edges: Edges, closed: np.ndarray) -> list[np.ndarray]:
    """Split a mask of closed-loop cells into its strongly connected sets."""
    if not closed.any():
        return []
    cycles = find_cycles(n, edges)
    return [c.cells for c in cycles if closed[c.cells].all()]


def _net_backward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> BackwardResult:
    """Net-mode backward trace (reference method): destination cells absorbing with f = 1.

    The destination cells are net_fixed_cells(sign=-1): the group's cells, or for a group
    selected by term criteria the cells where a selected entry is a sink.

    destination_inflow is the destination cells' throughflow sum less the water it counts twice
    (net_double_count); destination_throughflow keeps the throughflow sum.
    """
    sol = _net_solve(step, groups, edges, config, backward=True)
    inflow, t_sum = _net_group_inflow(sol.used, sol.fixed, sol.fraction, sol.throughflow, True)
    result = backward_metrics(
        step, groups, sol.fraction, sol.throughflow, np.maximum(sol.s, 0.0), {}, inflow, "net"
    )
    result.destination_throughflow = {g: float(v) for g, v in zip(groups, t_sum)}
    result.solver_used = sol.solvers
    result.closed_loops = sol.loops
    return result


def _net_forward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> ForwardResult:
    """Net-mode forward trace: source cells fixed at g = 1 on the reversed graph.

    The source cells are net_fixed_cells(sign=+1): the group's cells, or for a group selected by
    term criteria the cells where a selected entry is a source.

    source_inflow is the source cells' throughflow sum less the water it counts twice
    (net_double_count); source_throughflow keeps the throughflow sum.
    """
    sol = _net_solve(step, groups, edges, config, backward=False)
    inflow, t_sum = _net_group_inflow(sol.used, sol.fixed, sol.fraction, sol.throughflow, False)
    result = forward_metrics(
        step, groups, sol.fraction, sol.throughflow, np.maximum(-sol.s, 0.0), {}, inflow, "net"
    )
    result.source_throughflow = {g: float(v) for g, v in zip(groups, t_sum)}
    result.solver_used = sol.solvers
    result.closed_loops = sol.loops
    return result
