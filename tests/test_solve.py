"""Solver checks: topological substitution vs sparse LU, ordering, and cycle handling."""

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import Edges
from gwsource.solve import (
    _kahn_order,
    find_cycles,
    remove_cycle_edges,
    solve_system,
    topological_order,
)


def random_dag_step(n: int, seed: int) -> gs.FlowStep:
    """Return a random acyclic flow graph with recharge everywhere and wells in the last cells."""
    rng = np.random.default_rng(seed)
    src, dst = [], []
    for i in range(n - 5):
        for j in rng.choice(np.arange(i + 1, n), size=min(3, n - i - 1), replace=False):
            src.append(i)
            dst.append(int(j))
    q = rng.uniform(0.1, 10.0, size=len(src))
    inflow = np.bincount(dst, weights=q, minlength=n)
    outflow = np.bincount(src, weights=q, minlength=n)
    recharge = rng.uniform(0.5, 2.0, size=n)
    sink = inflow + recharge - outflow  # makes every cell balance exactly
    cells = np.concatenate([np.arange(n), np.arange(n)])
    flows = np.concatenate([recharge, np.minimum(-sink, 0.0)])
    pkg = np.concatenate([np.zeros(n, int), np.ones(n, int)])
    perm = rng.permutation(n)  # so the natural order is not already topological
    packages = [gs.Package("RCH", "RCH"), gs.Package("WEL", "WEL")]
    return gs.from_edges(n, perm[src], perm[dst], q, perm[cells], flows, pkg, packages=packages)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_topological_matches_lu(seed):
    """Both solvers give the same fractions to machine precision on acyclic graphs."""
    step = random_dag_step(200, seed)
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    for trace in (gs.backward, gs.forward):
        if trace is gs.forward:
            groups = {"rch": gs.select(step, package="RCH", cells=np.arange(50))}
        topo = trace(step, groups, gs.TraceConfig(solver="topological"))
        lu = trace(step, groups, gs.TraceConfig(solver="lu"))
        assert topo.solver_used == ["topological"] and lu.solver_used == ["lu"]
        name = "fraction_through" if trace is gs.backward else "source_fraction"
        for g in groups:
            np.testing.assert_allclose(getattr(topo, name)[g], getattr(lu, name)[g], rtol=1e-13, atol=1e-15)


def test_topological_order_is_valid_and_kahn_agrees():
    """The component-label order and Kahn's order both put every edge's tail first."""
    rng = np.random.default_rng(7)
    n = 300
    before = rng.integers(0, n - 1, size=900)
    after = before + rng.integers(1, 20, size=900)
    keep = after < n
    perm = rng.permutation(n)
    before, after = perm[before[keep]], perm[after[keep]]
    for order in (topological_order(n, before, after), _kahn_order(n, before, after)):
        position = np.empty(n, int)
        position[order] = np.arange(n)
        assert np.all(position[before] < position[after])


def test_cyclic_graph_has_no_topological_order():
    """A cycle makes both ordering routes return None."""
    before, after = np.array([0, 1, 2]), np.array([1, 2, 0])
    assert topological_order(3, before, after) is None
    assert _kahn_order(3, before, after) is None


def test_auto_solver_switches_to_lu_on_cycles():
    """The auto solver uses LU when the matrix dependency graph has a cycle."""
    import scipy.sparse as sp

    matrix = sp.csr_matrix(np.array([[1.0, -0.5, 0.0], [0.0, 1.0, -0.5], [-0.5, 0.0, 1.0]]))
    x, used = solve_system(matrix, np.ones((3, 2)), "auto")
    assert used == "lu"
    np.testing.assert_allclose(matrix @ x, 1.0)


def test_remove_cycle_edges_breaks_every_cycle():
    """Min-edge removal leaves an acyclic graph and removes the smallest edge of a simple cycle."""
    edges = Edges(
        src=np.array([0, 1, 2, 3, 4, 5]),
        dst=np.array([1, 2, 0, 4, 5, 3]),
        q=np.array([3.0, 1.0, 2.0, 5.0, 4.0, 6.0]),
    )
    keep = remove_cycle_edges(6, edges)
    assert list(np.flatnonzero(~keep)) == [1, 4]
    assert find_cycles(6, edges.subset(keep)) == []
    cycles = find_cycles(6, edges)
    assert sorted(c.internal_flow for c in cycles) == [6.0, 15.0]
