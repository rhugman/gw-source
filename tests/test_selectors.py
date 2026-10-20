"""Selectors by boundname (per stress period), by zone array on DIS, DISV and DISU grids, by term."""

from dataclasses import replace

import numpy as np
import pytest

import gwsource as gs


@pytest.mark.parametrize("kstpkper", [(0, 0), (0, 1)])
def test_boundnames_follow_the_stress_period_list(kstpkper, model_run):
    """A named well is found by name although its bound number changes between periods."""
    run = model_run("m7_mover")
    step = gs.read_step(run.ws, kstpkper=kstpkper, boundnames=True)
    spec = run.notes["spec"]
    wells = run.notes["wells"][kstpkper[1]]
    for bound, (name, (row, col), rate) in enumerate(wells, start=1):
        sel = gs.select(step, boundnames=[name])
        assert step.term_bound[sel.terms].tolist() == [bound]
        assert step.term_cell[sel.terms].tolist() == [row * spec.ncol + col]
        assert step.term_flow[sel.terms].tolist() == [rate]
        assert np.flatnonzero(sel.cells).tolist() == [row * spec.ncol + col]


def test_boundnames_of_mover_records_and_sfr_reaches(model_run):
    """DRN-TO-MVR records take their package's names; SFR reaches are named from PACKAGEDATA."""
    step = gs.read_step(model_run("m7_mover").ws, boundnames=True)
    drn_a = gs.select(step, boundnames=["DRN_A"])  # names match in any case
    texts = sorted(step.packages[p].text for p in step.term_package[drn_a.terms])
    assert texts == ["DRN", "DRN-TO-MVR"]
    reach = gs.select(step, package="SFR", boundnames=["reach_3"])
    assert step.term_bound[reach.terms].tolist() == [3]
    assert set(gs.groups_by_boundname(step, package="WEL")) == {"well_east", "well_west"}


def test_absent_boundname_selects_nothing(model_run):
    """well_north only exists in period 2: in period 1 it selects nothing, and traces to zero."""
    step = gs.read_step(model_run("m7_mover").ws, kstpkper=(0, 0), boundnames=True)
    sel = gs.select(step, boundnames=["well_north"])
    assert not sel.terms.any() and not sel.cells.any()
    res = gs.backward(step, {"north": sel})
    assert res.destination_inflow["north"] == 0.0
    assert np.all(res.fraction_through["north"] == 0.0)


def test_boundnames_need_reading(model_run):
    """Without boundnames=True the step has none and the selector says so."""
    step = gs.read_step(model_run("m7_mover").ws)
    assert step.term_boundname is None
    with pytest.raises(AssertionError, match="boundnames"):
        gs.select(step, boundnames=["well_east"])


@pytest.mark.parametrize("key", ["m1_dis", "m3_disv", "m4_disu_vert"])
def test_zone_selection_any_grid(key, model_run):
    """A zone array (grid-shaped or flat) selects its cells; with package= only their terms."""
    step = gs.read_step(model_run(key).ws)
    rng = np.random.default_rng(3)
    zones = rng.integers(0, 3, size=step.n_cells).reshape(step.grid_shape)
    sel = gs.select_zone(step, zones, 2)
    np.testing.assert_array_equal(sel.cells, zones.ravel() == 2)
    np.testing.assert_array_equal(sel.terms, zones.ravel()[step.term_cell] == 2)
    rch = gs.select_zone(step, zones.ravel(), [1, 2], package="RCH")
    expected = np.isin(zones.ravel()[step.term_cell], [1, 2]) & gs.select(step, package="RCH").terms
    np.testing.assert_array_equal(rch.terms, expected)
    groups = gs.groups_by_zone(step, zones, package="RCH")
    assert list(groups) == ["zone_1", "zone_2"]
    fwd = gs.forward(step, groups)
    for value in (1, 2):
        in_zone = gs.select_zone(step, zones, value, package="RCH").terms
        expected = step.term_flow[in_zone].sum()
        assert expected > 0.0
        assert fwd.source_inflow[f"zone_{value}"] == pytest.approx(expected, rel=1e-12)


def test_zone_array_must_match_grid(model_run):
    """A zone array of the wrong size is refused."""
    step = gs.read_step(model_run("m1_dis").ws)
    with pytest.raises(AssertionError, match="zone array"):
        gs.select_zone(step, np.zeros(10), 1)


def test_groups_by_term_keeps_entries_sharing_a_bound():
    """Two cells connected to lake 1 both get a group, and the boundary control rows sum to 1."""
    packages = [gs.Package("RCH", "RCH"), gs.Package("LAK-1", "LAK"), gs.Package("WEL", "WEL")]
    step = gs.from_edges(
        3, [0, 0], [1, 2], [4.0, 6.0], [0, 1, 2, 2], [10.0, -4.0, -5.0, -1.0], [0, 1, 1, 2],
        packages=packages,
    )
    step = replace(step, term_bound=np.array([1, 1, 1, 1]))
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    assert list(groups) == ["LAK-1:1:1", "LAK-1:1:2", "WEL:1"]
    assert [int(np.flatnonzero(g.terms)[0]) for g in groups.values()] == [1, 2, 3]
    res = gs.backward(step, groups)
    assert res.destination_inflow["LAK-1:1:1"] == pytest.approx(4.0)
    np.testing.assert_allclose(sum(res.fraction_through[g] for g in groups), 1.0, atol=1e-14)
