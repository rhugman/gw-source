"""Strong sinks (TraceConfig.strong_sinks): sink cells that pass no water on, as MODPATH 7 "stop".

A strong-sink cell is absorbing. Gross accounting gives it F = d / Snk, its destination share of
its sink outflow; net accounting keeps the destination cells at 1 and sets the other strong-sink
cells to 0. The closure check gains the strong-sink term A (gwsource.diagnostics).
"""

import numpy as np
import pytest

import gwsource as gs
from gwsource.diagnostics import backward_closure, budget_error
from test_assemble import SRC, graph, weak_sink_step
from test_closure_duality import STEADY, _assert_check

WEL, DRN, CHD = gs.Package("WEL", "WEL"), gs.Package("DRN", "DRN"), gs.Package("CHD", "CHD")


def two_sink_step() -> gs.FlowStep:
    """Source 10 at cell 0 -> cell 1 (well 1, drain 3) -> 6 on to cell 2 (constant head 6)."""
    terms = [(0, 10.0, 0), (1, -1.0, 1), (1, -3.0, 2), (2, -6.0, 3)]
    return graph(3, [(0, 1, 10.0), (1, 2, 6.0)], terms, (SRC, WEL, DRN, CHD))


def test_strong_cell_split_by_its_sink_flows():
    """The well-and-drain cell keeps all its water: 1/4 to the well, 3/4 to the drain, 0 on."""
    step = two_sink_step()
    groups = gs.groups_by_package(step)
    mixed = gs.backward(step, groups)
    np.testing.assert_allclose(mixed.fraction_through["WEL"], [0.1, 0.1, 0.0])
    strong = gs.backward(step, groups, gs.TraceConfig(strong_sinks=("WEL",)))
    np.testing.assert_allclose(strong.fraction_through["WEL"], [0.25, 0.25, 0.0])
    np.testing.assert_allclose(strong.fraction_through["DRN"], [0.75, 0.75, 0.0])
    np.testing.assert_allclose(strong.fraction_through["CHD"], [0.0, 0.0, 1.0])
    assert strong.volume_from["WEL"].sum() == pytest.approx(2.5)
    for name in ("WEL", "DRN", "CHD"):
        check = backward_closure(step, strong, name)
        assert abs(check.error) < 1e-13
    # the 6 handed on from cell 1 counts with F_1 instead of F_2: A = 6 (1/4 - 0)
    assert backward_closure(step, strong, "WEL").strong_sink_term == pytest.approx(1.5)
    assert backward_closure(step, strong, "CHD").strong_sink_term == pytest.approx(-6.0)


def test_weak_sink_becomes_absorbing():
    """Tutorial-style weak well: strong, the whole cell (and the source upstream) counts."""
    step = weak_sink_step()
    config = gs.TraceConfig(strong_sinks=["wel"])
    res = gs.backward(step, {"well": gs.select(step, package="WEL")}, config)
    np.testing.assert_allclose(res.fraction_through["well"], [1.0, 1.0, 0.0])
    assert res.destination_inflow["well"] == pytest.approx(1.0)
    assert res.volume_from["well"].sum() == pytest.approx(10.0)
    check = backward_closure(step, res, "well")
    assert check.strong_sink_term == pytest.approx(9.0) and abs(check.error) < 1e-13


def net_step() -> gs.FlowStep:
    """Source 10 at cell 0 splits 4 to cell 1 (drain 2, passes 2 on) and 6 to well cell 2 (8)."""
    edges = [(0, 1, 4.0), (0, 2, 6.0), (1, 2, 2.0)]
    terms = [(0, 10.0, 0), (1, -2.0, 2), (2, -8.0, 1)]
    return graph(3, edges, terms, (SRC, WEL, DRN))


@pytest.mark.parametrize("accounting", ["gross", "net"])
def test_other_strong_cell_gives_nothing_on(accounting):
    """A strong drain cell with no well water sends none of its inflow to the well."""
    step = net_step()
    groups = {"well": gs.select(step, package="WEL")}
    mixed = gs.backward(step, groups, gs.TraceConfig(accounting=accounting))
    np.testing.assert_allclose(mixed.fraction_through["well"], [0.8, 0.5, 1.0])
    config = gs.TraceConfig(accounting=accounting, strong_sinks="all")
    res = gs.backward(step, groups, config)
    np.testing.assert_allclose(res.fraction_through["well"], [0.6, 0.0, 1.0])
    check = backward_closure(step, res, "well")
    assert check.strong_sink_term == pytest.approx(-2.0) and abs(check.error) < 1e-13


def test_net_destination_stays_fixed():
    """In net mode a strong cell of the destination keeps f = 1, not its share d / Snk."""
    step = two_sink_step()
    config = gs.TraceConfig(accounting="net", strong_sinks="all")
    res = gs.backward(step, {"well": gs.select(step, package="WEL")}, config)
    np.testing.assert_allclose(res.fraction_through["well"], [1.0, 1.0, 0.0])
    assert not res.absorbing[1, 0] and res.absorbing[2, 0]


def check_all_strong(step: gs.FlowStep) -> None:
    """With every sink strong: sink cells get d / Snk, boundary control sums to 1, closure holds."""
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    res = gs.backward(step, groups, gs.TraceConfig(strong_sinks="all"))
    budget = gs.cell_budget(step)
    sink_cells = budget.sink > 0.0
    total = np.sum([res.fraction_through[g] for g in groups], axis=0)
    drains = budget.outflow > 0.0
    np.testing.assert_allclose(total[drains], 1.0, atol=1e-12)
    np.testing.assert_array_equal(total[~drains], 0.0)
    for g, sel in groups.items():
        d = np.bincount(step.term_cell[sel.terms], -step.term_flow[sel.terms], step.n_cells)
        expected = d[sink_cells] / budget.sink[sink_cells]
        np.testing.assert_allclose(res.fraction_through[g][sink_cells], expected, atol=1e-14)
    abs_residual = budget_error(step)["abs_residual"]
    for g in groups:
        _assert_check(backward_closure(step, res, g), abs_residual)


def test_all_strong_hand_built():
    """'all' on the two-sink graph: every sink cell absorbing."""
    check_all_strong(two_sink_step())


@pytest.mark.parametrize("key", STEADY)
def test_all_strong_steady_models(key, model_run):
    """'all' on every steady test model: shares, boundary control and closure."""
    check_all_strong(gs.read_step(model_run(key).ws))


def test_no_strong_cells_is_bitwise_default(model_run):
    """Strong sinks that match no sink cell give exactly the default trace."""
    step = gs.read_step(model_run("m1_dis").ws)
    groups = gs.groups_by_package(step)
    default = gs.backward(step, groups)
    assert default.absorbing is None
    none_strong = gs.backward(step, groups, gs.TraceConfig(strong_sinks=("RCH",)))
    assert not none_strong.absorbing.any()
    for g in groups:
        assert np.array_equal(default.fraction_through[g], none_strong.fraction_through[g])
        assert backward_closure(step, none_strong, g) == backward_closure(step, default, g)


def test_unsupported_combinations():
    """Forward traces, travel times and unknown packages are refused clearly."""
    step = two_sink_step()
    config = gs.TraceConfig(strong_sinks="all")
    with pytest.raises(AssertionError, match="backward traces only"):
        gs.forward(step, {"rch": gs.select(step, package="RCH")}, config)
    res = gs.backward(step, {"well": gs.select(step, package="WEL")}, config)
    with pytest.raises(AssertionError, match="strong sinks"):
        gs.travel_time(step, res, porosity=0.3)
    with pytest.raises(AssertionError, match="no package matches"):
        gs.backward(step, res.selections, gs.TraceConfig(strong_sinks=["MAW"]))
    with pytest.raises(AssertionError, match="strong_sinks must be"):
        gs.TraceConfig(strong_sinks="WEL")
