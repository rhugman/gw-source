"""Public entry points: backward (capture) and forward (fate) tracing of one FlowStep."""

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


def _net_solve(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig, backward: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[np.ndarray]]:
    """Solve net mode group by group; return (fractions, s, T, solvers, closed loops)."""
    n, n_groups = step.n_cells, len(groups)
    fraction, s_all, t_all = (np.zeros((n, n_groups)) for _ in range(3))
    solvers, closed = [], np.zeros(n, dtype=bool)
    for g, sel in enumerate(groups.values()):
        used = _net_edges(n, edges, sel.cells, backward, config.remove_cycles)
        s, throughflow = net_balance(n, used)
        matrix, rhs = net_system(n, used, sel.cells, throughflow, backward)
        fraction[:, g], factor, loops = _solve(matrix, rhs, config)
        s_all[:, g], t_all[:, g] = s, throughflow
        solvers.append(factor.kind)
        for cells in loops:
            closed[cells] = True
    return fraction, s_all, t_all, solvers, _loops_from_mask(n, edges, closed)


def _loops_from_mask(n: int, edges: Edges, closed: np.ndarray) -> list[np.ndarray]:
    """Split a mask of closed-loop cells into its strongly connected sets."""
    if not closed.any():
        return []
    cycles = find_cycles(n, edges)
    return [c.cells for c in cycles if closed[c.cells].all()]


def _net_backward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> BackwardResult:
    """Net-mode backward trace (reference method): destination cells absorbing with f = 1."""
    fraction, s, throughflow, solvers, loops = _net_solve(
        step, groups, edges, config, backward=True
    )
    cells = np.column_stack([sel.cells for sel in groups.values()])
    destination = (throughflow * cells).sum(axis=0)
    result = backward_metrics(
        step, groups, fraction, throughflow, np.maximum(s, 0.0), {}, destination, "net"
    )
    result.solver_used = solvers
    result.closed_loops = loops
    return result


def _net_forward(
    step: FlowStep, groups: dict, edges: Edges, config: TraceConfig
) -> ForwardResult:
    """Net-mode forward trace: source cells fixed at g = 1 on the reversed graph."""
    fraction, s, throughflow, solvers, loops = _net_solve(
        step, groups, edges, config, backward=False
    )
    cells = np.column_stack([sel.cells for sel in groups.values()])
    source = (throughflow * cells).sum(axis=0)
    result = forward_metrics(
        step, groups, fraction, throughflow, np.maximum(-s, 0.0), {}, source, "net"
    )
    result.solver_used = solvers
    result.closed_loops = loops
    return result
