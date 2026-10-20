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


def test_flowja_must_be_antisymmetric():
    """A FlowStep whose flow and reverse flow disagree is refused; a solver-level difference not."""
    step = graph(3, [(0, 1, 2.0), (1, 2, 3.0)], [(0, 2.0, 0), (1, 1.0, 0), (2, -3.0, 1)])
    fields = {k: getattr(step, k) for k in ("ia", "ja", "term_cell", "term_flow", "term_package",
                                            "term_bound", "packages")}
    flowja = step.flowja.copy()
    flowja[1] = -2.5  # 0 -> 1 is 2.0 in row 1, 2.5 in row 0
    with pytest.raises(AssertionError, match="not antisymmetric"):
        gs.FlowStep(flowja=flowja, **fields)
    flowja[1] = -2.0 * (1.0 + 1e-12)
    gs.FlowStep(flowja=flowja, **fields)


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


def test_net_two_cell_group_closure():
    """A group of two well cells, one feeding the other directly and through a third cell.

    Source 10 -> well cell 1 (pumps 4), which sends 3 to well cell 3 and 3 to cell 2; cell 2
    sends 2 to cell 3 (pumps 5) and 1 to cell 4 (other sink). Net mode gives f = (1, 1, 2/3, 1, 0).
    The throughflow sum (10 + 5) counts the 3 passing 1 -> 3 twice and the 2 passing 1 -> 2 -> 3
    twice; the volume from (10) does not: sum f s+ = sum T_D - q(D->D) - sum q(D->not D) f.
    destination_inflow is the 10, destination_throughflow the 15.
    """
    edges = [(0, 1, 10.0), (1, 3, 3.0), (1, 2, 3.0), (2, 3, 2.0), (2, 4, 1.0)]
    terms = [(0, 10.0, 0), (1, -4.0, 1), (3, -5.0, 1), (4, -1.0, 1)]
    step = graph(5, edges, terms)
    groups = {"wells": gs.select_cells(step, [1, 3])}
    net = gs.backward(step, groups, gs.TraceConfig(accounting="net"))
    f = net.fraction_through["wells"]
    np.testing.assert_allclose(f, [1.0, 1.0, 2.0 / 3.0, 1.0, 0.0], rtol=1e-14)
    assert net.destination_inflow["wells"] == pytest.approx(10.0, rel=1e-14)
    assert net.destination_throughflow["wells"] == pytest.approx(15.0, rel=1e-14)
    assert net.volume_from["wells"].sum() == pytest.approx(10.0)
    e = gs.flow_edges(step)
    dest = groups["wells"].cells
    dest_to_dest = e.q[dest[e.src] & dest[e.dst]].sum()
    onward = dest[e.src] & ~dest[e.dst]
    dest_onward = np.sum(e.q[onward] * f[e.dst[onward]])
    assert (dest_to_dest, dest_onward) == pytest.approx((3.0, 2.0))
    rhs = net.destination_throughflow["wells"] - dest_to_dest - dest_onward
    assert net.volume_from["wells"].sum() == pytest.approx(rhs, rel=1e-14)
    check = backward_closure(step, net, "wells")
    assert check.residual_term == 0.0 and abs(check.error) < 1e-13
    gross = gs.backward(step, {"wells": gs.select(step, package="WEL", cells=[1, 3])})
    assert gross.volume_from["wells"].sum() == pytest.approx(9.0)


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
    assert cut.destination_inflow["c3"] == pytest.approx(cut.volume_from["c3"].sum(), rel=1e-14)
    assert abs(backward_closure(step, cut, "c3").error) < 1e-13


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


def test_net_destination_inflow_return_flow():
    """Net destination inflow of one cell less the water that leaves it and comes back.

    cycle_step, group cell 2: T_2 = 12, of which 5 leaves for cell 1 (f = 0.8) and comes back, so
    the inflow is 12 - 5 x 0.8 = 8 = the net volume from (10 x 0.8).
    """
    step = cycle_step()
    res = gs.backward(step, {"c2": gs.select_cells(step, [2])}, gs.TraceConfig(accounting="net"))
    np.testing.assert_allclose(res.fraction_through["c2"], [0.8, 0.8, 1.0], rtol=1e-14)
    assert res.destination_inflow["c2"] == pytest.approx(8.0, rel=1e-14)
    assert res.destination_throughflow["c2"] == pytest.approx(12.0, rel=1e-14)
    check = backward_closure(step, res, "c2")
    assert check.residual_term == 0.0 and abs(check.error) < 1e-13


def test_net_source_inflow_return_flow():
    """Net source inflow of one cell less the water that leaves it and comes back.

    cycle_step forward, source cell 1: T_1 = 15, of which 5 comes back from cell 2 (g = 1) and
    10 enters from cell 0 (g = 0), so the inflow is 15 - 5 x 1 = 10 = the net volume to (3 + 7).
    """
    step = cycle_step()
    res = gs.forward(step, {"c1": gs.select_cells(step, [1])}, gs.TraceConfig(accounting="net"))
    np.testing.assert_allclose(res.source_fraction["c1"], [0.0, 1.0, 1.0], rtol=1e-14)
    assert res.source_inflow["c1"] == pytest.approx(10.0, rel=1e-14)
    assert res.source_throughflow["c1"] == pytest.approx(15.0, rel=1e-14)
    check = forward_closure(step, res, "c1")
    assert check.residual_term == 0.0 and abs(check.error) < 1e-13


def test_net_two_cell_source_group_closure():
    """Forward twin of test_net_two_cell_group_closure: the same graph reversed, cells 1 and 3 as
    the source group. The source throughflow sum (10 + 5) counts the 3 passing 3 -> 1 and the 2
    passing 3 -> 2 -> 1 twice; the source inflow is 15 - 3 - 3 x 2/3 = 10 = the net volume to.
    """
    edges = [(1, 0, 10.0), (3, 1, 3.0), (2, 1, 3.0), (3, 2, 2.0), (4, 2, 1.0)]
    terms = [(0, -10.0, 1), (1, 4.0, 0), (3, 5.0, 0), (4, 1.0, 0)]
    step = graph(5, edges, terms)
    groups = {"wells": gs.select_cells(step, [1, 3])}
    net = gs.forward(step, groups, gs.TraceConfig(accounting="net"))
    g = net.source_fraction["wells"]
    np.testing.assert_allclose(g, [1.0, 1.0, 2.0 / 3.0, 1.0, 0.0], rtol=1e-14)
    assert net.source_inflow["wells"] == pytest.approx(10.0, rel=1e-14)
    assert net.source_throughflow["wells"] == pytest.approx(15.0, rel=1e-14)
    assert net.volume_to["wells"].sum() == pytest.approx(10.0, rel=1e-14)
    within, returning = gs.assemble.net_double_count(
        gs.flow_edges(step), groups["wells"].cells, g, backward=False
    )
    assert (within, returning) == pytest.approx((3.0, 2.0), rel=1e-14)
    check = forward_closure(step, net, "wells")
    assert check.residual_term == 0.0 and abs(check.error) < 1e-13


def test_net_several_groups_match_single_runs():
    """Groups traced in one net call give the same inflow and fractions as one call per group."""
    step = cycle_step()
    cells = {"c1": [1], "c2": [2], "both": [1, 2]}
    config = gs.TraceConfig(accounting="net")
    together = gs.backward(step, {g: gs.select_cells(step, c) for g, c in cells.items()}, config)
    for name, c in cells.items():
        alone = gs.backward(step, {name: gs.select_cells(step, c)}, config)
        assert together.destination_inflow[name] == alone.destination_inflow[name]
        assert together.destination_throughflow[name] == alone.destination_throughflow[name]
        f_together, f_alone = together.fraction_through[name], alone.fraction_through[name]
        np.testing.assert_array_equal(f_together, f_alone)
        assert abs(backward_closure(step, together, name).error) < 1e-13
    assert together.destination_inflow["both"] == pytest.approx(10.0, rel=1e-14)
    assert together.destination_throughflow["both"] == pytest.approx(27.0, rel=1e-14)


def test_net_destination_in_closed_loop():
    """A destination cell on a loop with no way out: nothing enters the loop, so the inflow is 0.

    Loop 0 -> 1 -> 2 -> 0 (q = 1) beside chain 3 -> 4; cell 2 has a negligible sink. The
    throughflow sum is 1, all of it water that leaves cell 2 and comes back (f = 1 on the loop).
    """
    edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 0, 1.0), (3, 4, 2.0)]
    terms = [(3, 2.0, 0), (4, -2.0, 1), (2, -1e-14, 1)]
    step = graph(5, edges, terms)
    res = gs.backward(step, {"c2": gs.select_cells(step, [2])}, gs.TraceConfig(accounting="net"))
    assert res.destination_inflow["c2"] == pytest.approx(0.0, abs=1e-14)
    assert res.destination_throughflow["c2"] == pytest.approx(1.0, rel=1e-14)
    assert abs(backward_closure(step, res, "c2").error) < 1e-13


def zero_recharge_step() -> gs.FlowStep:
    """Chain 0 -> 1 -> 2: recharge 10 at cell 0 and 0.0 at cell 1, CHD inflow 5 at cell 1."""
    packages = [gs.Package("RCH", "RCH"), gs.Package("CHD", "CHD"), gs.Package("WEL", "WEL")]
    terms = [(0, 10.0, 0), (1, 0.0, 0), (1, 5.0, 1), (2, -15.0, 2)]
    return graph(3, [(0, 1, 10.0), (1, 2, 15.0)], terms, packages)


def test_net_forward_skips_zero_flow_source_cells():
    """A recharge entry at 0.0 does not fix its cell: g_1 = q01 / T1 = 10 / 15, not 1."""
    step = zero_recharge_step()
    rch = {"rch": gs.select(step, package="RCH")}
    res = gs.forward(step, rch, gs.TraceConfig(accounting="net"))
    np.testing.assert_allclose(res.source_fraction["rch"], [1.0, 2.0 / 3.0, 2.0 / 3.0], rtol=1e-14)
    assert res.source_inflow["rch"] == pytest.approx(10.0, rel=1e-14)
    assert abs(forward_closure(step, res, "rch").error) < 1e-13


def test_net_fixed_cells_follow_the_traced_direction():
    """Term selections fix the cells whose selected entries flow in the traced direction only."""
    step = zero_recharge_step()
    both = gs.select(step, package=["RCH", "WEL"])
    assert both.cells.tolist() == [True, True, True]
    assert gs.trace.net_fixed_cells(step, both, +1).tolist() == [True, False, False]
    assert gs.trace.net_fixed_cells(step, both, -1).tolist() == [False, False, True]
    by_cell = gs.select_cells(step, [1])
    for sign in (-1, +1):
        assert gs.trace.net_fixed_cells(step, by_cell, sign).tolist() == [False, True, False]
    cells_and_package = gs.select(step, package="RCH", cells=[0, 1])
    assert by_cell.term_criteria is False and cells_and_package.term_criteria is True
    assert gs.trace.net_fixed_cells(step, cells_and_package, +1).tolist() == [True, False, False]
    with pytest.raises(AssertionError, match="sign"):
        gs.trace.net_fixed_cells(step, both, 0)
    # any selected entry flowing in the traced direction fixes the cell: +3 and -4 fix it both ways
    packages = [gs.Package("RIV", "RIV"), gs.Package("WEL", "WEL")]
    mixed = graph(2, [(1, 0, 1.0)], [(0, 3.0, 0), (0, -4.0, 1), (1, 1.0, 0)], packages)
    sel = gs.select(mixed, term_mask=mixed.term_cell == 0)
    for sign in (-1, +1):
        assert gs.trace.net_fixed_cells(mixed, sel, sign).tolist() == [True, False]


def zero_drain_step() -> gs.FlowStep:
    """Source 10 at cell 0 -> cell 1, which splits 6 to a drain at cell 2 and 4 to a well at 3.

    Cell 1 also has a drain entry at 0.0 (a drain above the water table).
    """
    packages = [SRC, gs.Package("DRN", "DRN"), gs.Package("WEL", "WEL")]
    terms = [(0, 10.0, 0), (1, 0.0, 1), (2, -6.0, 1), (3, -4.0, 2)]
    return graph(4, [(0, 1, 10.0), (1, 2, 6.0), (1, 3, 4.0)], terms, packages)


def test_net_backward_skips_zero_flow_destination_cells():
    """A drain entry at 0.0 leaves its cell non-absorbing; the inflow is the flowing drain's."""
    step = zero_drain_step()
    config = gs.TraceConfig(accounting="net")
    res = gs.backward(step, {"drn": gs.select(step, package="DRN")}, config)
    np.testing.assert_allclose(res.fraction_through["drn"], [0.6, 0.6, 1.0, 0.0], rtol=1e-14)
    alone = gs.backward(step, {"c2": gs.select_cells(step, [2])}, config)
    assert res.destination_inflow["drn"] == alone.destination_inflow["c2"] == pytest.approx(6.0)
    assert abs(backward_closure(step, res, "drn").error) < 1e-13


def test_net_group_with_no_flowing_entry_fixes_nothing():
    """A group whose selected entries are all at 0.0 fixes no cell: every value is 0, no NaN."""
    step = zero_drain_step()
    idle = gs.select(step, package="DRN", term_mask=step.term_flow == 0.0)
    res = gs.backward(step, {"idle": idle}, gs.TraceConfig(accounting="net"))
    np.testing.assert_array_equal(res.fraction_through["idle"], 0.0)
    assert res.destination_inflow["idle"] == 0.0
    assert res.destination_throughflow["idle"] == 0.0
    assert backward_closure(step, res, "idle").error == 0.0
    assert not np.isnan(res.fraction_from_total["idle"]).any()


def test_net_cell_selection_keeps_its_cells():
    """select_cells still fixes every selected cell, whether or not a term flows there."""
    step = zero_drain_step()
    groups = {"c12": gs.select_cells(step, [1, 2])}
    res = gs.backward(step, groups, gs.TraceConfig(accounting="net"))
    np.testing.assert_allclose(res.fraction_through["c12"], [1.0, 1.0, 1.0, 0.0], rtol=1e-14)
    assert res.destination_inflow["c12"] == pytest.approx(10.0, rel=1e-14)


def test_gross_results_have_no_throughflow_sums():
    """destination_throughflow and source_throughflow are net-only and empty in gross results."""
    step = cycle_step()
    back = gs.backward(step, {"c2": gs.select(step, package="WEL", bounds=[2])})
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    assert back.destination_throughflow == {} and fwd.source_throughflow == {}


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
