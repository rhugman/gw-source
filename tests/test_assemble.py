"""Hand-built graphs with analytical answers: chain, split, merge, weak sink, cycle, residuals."""

import numpy as np
import pytest

import gwsource as gs
from gwsource.diagnostics import backward_closure, cell_residual, duality, forward_closure

SRC, SNK = gs.Package("SRC", "RCH"), gs.Package("SNK", "WEL")


def graph(n, edges, terms, packages=(SRC, SNK)) -> gs.FlowStep:
    """Build a FlowStep from (src, dst, q) edges and (cell, flow, package index) terms."""
    src, dst, q = (np.array(x) for x in zip(*edges)) if edges else ([], [], [])
    cell, flow, pkg = (np.array(x) for x in zip(*terms))
    return gs.from_edges(n, src, dst, q, cell, flow, pkg, packages=list(packages))


def test_from_edges_layout():
    """from_edges puts the diagonal first in each row and makes flowja antisymmetric."""
    step = graph(3, [(0, 1, 2.0), (1, 2, 3.0)], [(0, 2.0, 0), (1, 1.0, 0), (2, -3.0, 1)])
    assert list(step.ia) == [0, 2, 5, 7]
    assert list(step.ja) == [0, 1, 1, 0, 2, 2, 1]
    assert list(step.flowja) == [0.0, -2.0, 0.0, 2.0, -3.0, 0.0, 3.0]
    assert list(step.term_bound) == [1, 2, 1]


def test_chain():
    """Source -> pass-through -> sink: every fraction is 1 and volumes equal the throughflow."""
    step = graph(3, [(0, 1, 10.0), (1, 2, 10.0)], [(0, 10.0, 0), (2, -10.0, 1)])
    back = gs.backward(step, {"well": gs.select(step, package="WEL")})
    np.testing.assert_allclose(back.fraction_through["well"], 1.0)
    np.testing.assert_allclose(back.volume_through["well"], 10.0)
    np.testing.assert_allclose(back.volume_from["well"], [10.0, 0.0, 0.0])
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    np.testing.assert_allclose(fwd.source_fraction["rch"], 1.0)
    np.testing.assert_allclose(fwd.volume_to["rch"], [0.0, 0.0, 10.0])


def test_split():
    """A source cell splitting 3:7 to two sinks sends 30 % of its water to the first."""
    step = graph(3, [(0, 1, 3.0), (0, 2, 7.0)], [(0, 10.0, 0), (1, -3.0, 1), (2, -7.0, 1)])
    back = gs.backward(step, {"w1": gs.select(step, package="WEL", bounds=[1])})
    np.testing.assert_allclose(back.fraction_through["w1"], [0.3, 1.0, 0.0])
    np.testing.assert_allclose(back.volume_from_by_term["w1"]["SRC"], [3.0, 0.0, 0.0])


def test_merge():
    """Two sources merging 4:6 into a sink: the sink cell holds 40 % of the first source's water."""
    packages = [gs.Package("A", "RCH"), gs.Package("B", "RCH"), SNK]
    step = graph(3, [(0, 2, 4.0), (1, 2, 6.0)], [(0, 4.0, 0), (1, 6.0, 1), (2, -10.0, 2)], packages)
    fwd = gs.forward(step, {"a": gs.select(step, package="A")})
    np.testing.assert_allclose(fwd.source_fraction["a"], [1.0, 0.0, 0.4])
    np.testing.assert_allclose(fwd.volume_to["a"], [0.0, 0.0, 4.0])
    np.testing.assert_allclose(fwd.volume_to_by_term["a"]["SNK"], [0.0, 0.0, 4.0])


def weak_sink_step() -> gs.FlowStep:
    """Source 10 at cell 0; cell 1 has a weak well (1) and passes 9 on to a strong sink at cell 2."""
    packages = [SRC, gs.Package("WEL", "WEL"), gs.Package("CHD", "CHD")]
    terms = [(0, 10.0, 0), (1, -1.0, 1), (2, -9.0, 2)]
    return graph(3, [(0, 1, 10.0), (1, 2, 9.0)], terms, packages)


def test_weak_sink_gross_takes_proportional_share():
    """Gross accounting gives the weak well only its 10 % share of the cell's water."""
    step = weak_sink_step()
    res = gs.backward(step, {"well": gs.select(step, package="WEL")})
    np.testing.assert_allclose(res.fraction_through["well"], [0.1, 0.1, 0.0])
    assert res.destination_inflow["well"] == pytest.approx(1.0)
    assert res.volume_from["well"].sum() == pytest.approx(1.0)


def test_weak_sink_net_absorbs_whole_cell():
    """Net mode makes the well cell absorbing: everything passing through it counts."""
    step = weak_sink_step()
    config = gs.TraceConfig(accounting="net")
    res = gs.backward(step, {"well": gs.select(step, package="WEL")}, config)
    np.testing.assert_allclose(res.fraction_through["well"], [1.0, 1.0, 0.0])
    assert res.destination_inflow["well"] == pytest.approx(10.0)
    assert res.volume_from["well"].sum() == pytest.approx(10.0)


def cycle_step() -> gs.FlowStep:
    """Source 10 -> cell 1 <-> cell 2 (12 forward, 5 back); sinks 3 at cell 1 and 7 at cell 2."""
    edges = [(0, 1, 10.0), (1, 2, 12.0), (2, 1, 5.0)]
    terms = [(0, 10.0, 0), (1, -3.0, 1), (2, -7.0, 1)]
    return graph(3, edges, terms)


def test_cycle_block_lu_exact():
    """Under full mixing the cycle has the exact solution F = (0.7, 0.7, 7/8) for the cell-2 sink."""
    step = cycle_step()
    res = gs.backward(step, {"w2": gs.select(step, package="WEL", bounds=[2])})
    assert res.solver_used == ["block"]
    np.testing.assert_allclose(res.fraction_through["w2"], [0.7, 0.7, 7.0 / 8.0], rtol=1e-14)
    assert [c.n_cells for c in res.cycles] == [2]
    assert res.cycles[0].internal_flow == 17.0 and res.cycles[0].min_edge_flow == 5.0


def test_cycle_topological_refuses():
    """The topological solver refuses a cyclic graph."""
    step = cycle_step()
    with pytest.raises(AssertionError, match="cycles"):
        gs.backward(step, {"w2": gs.select(step, package="WEL")}, gs.TraceConfig(solver="topological"))


def test_cycle_net_mode_removes_min_edge():
    """Net mode solves the cycle exactly by LU, or deletes the 5-unit back edge if asked to."""
    edges = [(0, 1, 10.0), (1, 2, 12.0), (2, 1, 5.0), (2, 3, 7.0)]
    step = graph(4, edges, [(0, 10.0, 0), (3, -7.0, 1)])
    groups = {"c3": gs.select_cells(step, [3])}
    exact = gs.backward(step, groups, gs.TraceConfig(accounting="net"))
    assert exact.solver_used == ["block"]
    np.testing.assert_allclose(exact.fraction_through["c3"], [0.7, 0.7, 7.0 / 8.0, 1.0], rtol=1e-14)
    config = gs.TraceConfig(accounting="net", solver="topological", remove_cycles=True)
    cut = gs.backward(step, groups, config)
    assert cut.solver_used == ["topological"]
    np.testing.assert_allclose(cut.fraction_through["c3"], [7 / 12, 7 / 12, 7 / 12, 1.0], rtol=1e-14)
    # without the back edge cell 1 receives 10 and sends 12: a net source of 2
    np.testing.assert_allclose(cut.volume_from["c3"], [70 / 12, 14 / 12, 0.0, 0.0], rtol=1e-14)


def test_remove_cycles_needs_net_mode():
    """Cycle removal is not offered in gross mode."""
    with pytest.raises(AssertionError, match="net mode"):
        gs.TraceConfig(remove_cycles=True)


def test_boundary_control_rows_sum_to_one():
    """With one group per sink term, the fractions of every draining cell sum to 1."""
    step = cycle_step()
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    res = gs.backward(step, groups)
    total = sum(res.fraction_through[g] for g in groups)
    np.testing.assert_allclose(total, 1.0, atol=1e-14)


def test_zero_outflow_cell_gets_identity_row():
    """An isolated cell (no flows) has zero fraction and does not break the solve."""
    step = graph(3, [(0, 1, 5.0)], [(0, 5.0, 0), (1, -5.0, 1)])
    res = gs.backward(step, {"well": gs.select(step, package="WEL")})
    np.testing.assert_allclose(res.fraction_through["well"], [1.0, 1.0, 0.0])


def residual_step() -> gs.FlowStep:
    """A graph whose budgets do not close: residual -0.5 in cell 1 and +0.25 in cell 2."""
    edges = [(0, 1, 10.0), (1, 2, 6.0), (1, 3, 4.5), (2, 3, 1.0)]
    terms = [(0, 10.0, 0), (2, -4.75, 1), (3, -5.5, 1)]
    return graph(4, edges, terms)


def test_residual_identities_hold_exactly():
    """Closure and duality hold to round-off once the residual term is included."""
    step = residual_step()
    np.testing.assert_allclose(cell_residual(step), [0.0, -0.5, 0.25, 0.0], atol=1e-15)
    dest = {"w1": gs.select(step, bounds=[1], package="WEL"), "w2": gs.select(step, bounds=[2], package="WEL")}
    back = gs.backward(step, dest)
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    for name in dest:
        check = backward_closure(step, back, name)
        assert abs(check.error) < 1e-13 and abs(check.error_without_residual) > 1e-3
        dual = duality(step, back, name, fwd, "rch")
        assert abs(dual.error) < 1e-13
    assert abs(forward_closure(step, fwd, "rch").error) < 1e-13


def test_net_forward_on_reversed_graph():
    """Net forward mode fixes the source cell at 1 and dilutes by throughflow downstream."""
    step = graph(3, [(0, 2, 4.0), (1, 2, 6.0)], [(0, 4.0, 0), (1, 6.0, 0), (2, -10.0, 1)])
    res = gs.forward(step, {"c0": gs.select_cells(step, [0])}, gs.TraceConfig(accounting="net"))
    np.testing.assert_allclose(res.source_fraction["c0"], [1.0, 0.0, 0.4])
    np.testing.assert_allclose(res.volume_to["c0"], [0.0, 0.0, 4.0])


def test_selectors():
    """Package/type matching, bounds, cells and term masks combine as documented."""
    packages = [gs.Package("WEL-1", "WEL"), gs.Package("WEL-2", "WEL"), gs.Package("RIV", "RIV")]
    terms = [(0, -1.0, 0), (1, -2.0, 0), (2, -3.0, 1), (2, 1.0, 2)]
    step = graph(3, [(0, 1, 1.0)], terms, packages)
    assert list(gs.select(step, package="WEL").terms) == [True, True, True, False]
    assert list(gs.select(step, package="wel-1").terms) == [True, True, False, False]
    assert list(gs.select(step, package="WEL-1", bounds=[2]).terms) == [False, True, False, False]
    by_cell = gs.select_cells(step, [2])
    assert list(by_cell.terms) == [False, False, True, True]
    assert list(by_cell.cells) == [False, False, True]
    assert list(gs.select(step, package="RIV").cells) == [False, False, True]
    assert set(gs.groups_by_package(step)) == {"WEL-1", "WEL-2", "RIV"}
    with pytest.raises(AssertionError, match="no package"):
        gs.select(step, package="DRN")


def test_public_cell_budget_and_exports(model_run):
    """cell_budget(step) computes the edges itself; PRT and budget helpers are top-level names."""
    step = gs.read_step(model_run("m1_dis").ws)
    budget = gs.cell_budget(step)
    np.testing.assert_array_equal(budget.outflow, gs.cell_budget(step, gs.flow_edges(step)).outflow)
    for name in ("PrtConfig", "track_particles", "CellBudget", "Edges"):
        assert hasattr(gs, name)
