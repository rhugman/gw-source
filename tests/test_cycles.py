"""Closed recirculation loops (no exit) and the cycle report, on hand-built graphs and model 5."""

import csv

import numpy as np
import pytest
import scipy.sparse as sp

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges, gross_backward_system
from gwsource.solve import isolate_closed_loops, solve_lu

PACKAGES = [gs.Package("RCH", "RCH"), gs.Package("WEL", "WEL")]


def loop_step(feed: float = 0.0, exit_q: float = 0.0) -> gs.FlowStep:
    """Return loop 0 -> 1 -> 2 -> 0 (q = 1) beside chain 3 -> 4 (q = 2, RCH at 3, WEL at 4).

    feed adds an edge 3 -> 0 (water enters the loop and cannot leave); exit_q adds a sink in
    cell 2 (a weak exit from the loop).
    """
    src, dst, q = [0, 1, 2, 3], [1, 2, 0, 4], [1.0, 1.0, 1.0, 2.0]
    if feed:
        src, dst, q = src + [3], dst + [0], q + [feed]
    cells, flows, pkgs = [3, 4], [2.0 + feed, -2.0], [0, 1]
    if exit_q:
        cells, flows, pkgs = cells + [2], flows + [-exit_q], pkgs + [1]
    return gs.from_edges(5, src, dst, q, cells, flows, pkgs, packages=list(PACKAGES))


def test_closed_loop_makes_lu_singular_and_is_isolated():
    """The pure loop is singular; it is detected before the solve and gets fraction 0."""
    step = loop_step()
    groups = {"wel": gs.select(step, package="WEL")}
    edges = flow_edges(step)
    matrix, rhs = gross_backward_system(step, edges, cell_budget(step, edges), groups)
    with pytest.raises(RuntimeError, match="singular"):
        solve_lu(matrix, rhs)
    _, _, loops = isolate_closed_loops(matrix, rhs)
    assert [c.tolist() for c in loops] == [[0, 1, 2]]
    for solver in ("auto", "block", "lu"):
        res = gs.backward(step, groups, gs.TraceConfig(solver=solver))
        np.testing.assert_array_equal(res.fraction_through["wel"], [0, 0, 0, 1, 1])
        assert [c.tolist() for c in res.closed_loops] == [[0, 1, 2]]
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    np.testing.assert_array_equal(fwd.source_fraction["rch"], [0, 0, 0, 1, 1])
    assert [c.tolist() for c in fwd.closed_loops] == [[0, 1, 2]]


def test_loop_fed_but_without_exit():
    """Backward: water sent into a loop with no exit never arrives (F = 2/3 upstream).

    Forward: the same loop has an entry, so it is not closed, and its water is all recharge.
    """
    step = loop_step(feed=1.0)
    back = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    np.testing.assert_allclose(back.fraction_through["wel"], [0, 0, 0, 2.0 / 3.0, 1], atol=1e-15)
    assert len(back.closed_loops) == 1
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    np.testing.assert_allclose(fwd.source_fraction["rch"], 1.0, rtol=1e-13)
    assert fwd.closed_loops == []


def test_loop_with_real_exit_is_not_closed():
    """A loop whose only exit is a weak sink sends all its water there (F = 1), not 0."""
    step = loop_step(feed=1.0, exit_q=1.0)
    res = gs.backward(step, {"exit": gs.select(step, package="WEL", cells=[2])})
    assert res.closed_loops == []
    np.testing.assert_allclose(res.fraction_through["exit"][:3], 1.0, rtol=1e-12)
    tiny = loop_step(exit_q=1e-14)
    assert len(gs.backward(tiny, {"w": gs.select(tiny, package="WEL")}).closed_loops) == 1


def test_net_mode_closed_loop():
    """Net mode isolates the same loop."""
    step = loop_step()
    res = gs.backward(step, {"c4": gs.select_cells(step, [4])}, gs.TraceConfig(accounting="net"))
    np.testing.assert_array_equal(res.fraction_through["c4"], [0, 0, 0, 1, 1])
    assert [c.tolist() for c in res.closed_loops] == [[0, 1, 2]]


def test_cycle_report_hand_built():
    """Circulation by cycle cancelling: one 2-cell cycle, and a figure-of-eight of two cycles."""
    # 0 -> 1 (10); 1 <-> 2 (12 forward, 5 back); sinks 3 at cell 1, 7 at cell 2
    step = gs.from_edges(
        3, [0, 1, 2], [1, 2, 1], [10.0, 12.0, 5.0], [0, 1, 2], [10.0, -3.0, -7.0], [0, 1, 1],
        packages=list(PACKAGES),
    )  # fmt: skip
    (cycle,) = gs.diagnostics.cycle_report(step)
    assert cycle.cells.tolist() == [1, 2] and cycle.internal_flow == 17.0
    assert cycle.circulation == 5.0 and cycle.circulating_throughflow == 10.0
    assert cycle.throughflow_share == pytest.approx(10.0 / 37.0)  # O = 10 + 15 + 12
    # 0 <-> 1 (3 out, 2 back) and 0 <-> 2 (4 out, 1 back), fed by 5 at 0, sinks at 1 and 2
    eight = gs.from_edges(
        3, [0, 1, 0, 2], [1, 0, 2, 0], [3.0, 2.0, 4.0, 1.0], [0, 1, 2], [5.0, -1.0, -3.0],
        [0, 1, 1], packages=list(PACKAGES),
    )  # fmt: skip
    (cycle,) = gs.diagnostics.cycle_report(eight)
    assert cycle.n_cells == 3 and cycle.circulation == 3.0 and cycle.circulating_throughflow == 6.0


def test_cycle_report_model5_and_export(model_run, tmp_path):
    """On the XT3D model the report is consistent and exports to CSV and per-cell ids."""
    step = gs.read_step(model_run("m5_xt3d").ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    cycles = gs.diagnostics.cycle_report(step, res)
    assert cycles and all(0 < c.circulation <= c.internal_flow for c in cycles)
    assert all(c.circulating_throughflow <= c.internal_flow + 1e-9 for c in cycles)
    assert all(not c.closed for c in cycles)
    shares = [c.throughflow_share for c in cycles]
    assert 0 < sum(shares) < 1
    assert [c.circulation for c in cycles] == sorted((c.circulation for c in cycles), reverse=True)
    path = gs.export.save_cycle_report(tmp_path / "cycles.csv", cycles)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(cycles)
    assert [int(n) for n in rows[0]["cells"].split()] == cycles[0].cells.tolist()
    assert float(rows[0]["circulation"]) == pytest.approx(cycles[0].circulation)
    ids = gs.diagnostics.cycle_ids(step.n_cells, cycles)
    assert np.all(ids[cycles[0].cells] == 0) and (ids >= 0).sum() == sum(c.n_cells for c in cycles)
    with np.load(gs.export.save_npz(tmp_path / "r.npz", step, res)) as data:
        assert (data["cycle_id"] >= 0).sum() == (ids >= 0).sum()


def test_isolation_keeps_other_rows():
    """Rows outside closed loops are untouched by the isolation."""
    matrix = sp.csr_matrix(
        [[1.0, -1.0, 0.0, 0.0], [-1.0, 1.0, 0.0, 0.0], [0.0, -0.5, 1.0, 0.0], [0, 0, 0, 1.0]]
    )
    fixed, rhs, loops = isolate_closed_loops(matrix, np.ones((4, 1)))
    assert [c.tolist() for c in loops] == [[0, 1]]
    np.testing.assert_array_equal(fixed.toarray()[2:], matrix.toarray()[2:])
    np.testing.assert_array_equal(fixed.toarray()[:2], np.eye(4)[:2])
    np.testing.assert_array_equal(rhs.ravel(), [0, 0, 1, 1])
