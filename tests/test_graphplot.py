"""Graph-view data (gwsource.graphplot) on a hand-built split: edges, zone graph, sources."""

import numpy as np

import gwsource as gs
from gwsource import graphplot as gp

SRC, SNK = gs.Package("SRC", "RCH"), gs.Package("SNK", "WEL")


def split_step() -> gs.FlowStep:
    """Cell 0 (source 10) splits 6 to cell 1 (well) and 4 to cell 2 (drain-like sink)."""
    return gs.from_edges(
        3, [0, 0], [1, 2], [6.0, 4.0], [0, 1, 2], [10.0, -6.0, -4.0], [0, 1, 1],
        packages=[SRC, SNK],
    )


def test_edge_list():
    """edge_list returns each positive edge once, from src to dst."""
    src, dst, q = gp.edge_list(split_step())
    order = np.argsort(dst)
    assert list(src[order]) == [0, 0]
    assert list(dst[order]) == [1, 2]
    np.testing.assert_allclose(q[order], [6.0, 4.0])


def test_zone_graph_all_and_carried():
    """The zone graph keeps every flow; weighted by F it closes on the group's inflow."""
    step = split_step()
    groups = {"well": gs.select_cells(step, [1])}
    result = gs.backward(step, groups)
    zones, names = np.array([0, 1, 1]), ["up", "down"]
    full = gp.zone_graph(step, zones, names)
    np.testing.assert_allclose(full.flow, [[0.0, 10.0], [0.0, 0.0]])
    np.testing.assert_allclose(full.term_in["SRC"], [10.0, 0.0])
    np.testing.assert_allclose(full.term_out["SNK"], [0.0, 10.0])
    dst = gp.edge_list(step)[1]
    carried = gp.zone_graph(
        step, zones, names, edge_weight=result.fraction_through["well"][dst],
        term_weight=gp.term_weights(step, result, "well"),
    )
    np.testing.assert_allclose(carried.flow[0, 1], 6.0)
    np.testing.assert_allclose(carried.term_in["SRC"].sum(), result.destination_inflow["well"])
    np.testing.assert_allclose(carried.term_out["SNK"], [0.0, 6.0])


def test_source_matrix_and_neighbourhood():
    """source_matrix sums volume_from by package; neighbourhood follows edges both ways."""
    step = split_step()
    result = gs.backward(step, {"well": gs.select_cells(step, [1])})
    labels, matrix = gp.source_matrix(step, result, ["well"])
    assert labels == ["SRC"]
    np.testing.assert_allclose(matrix, [[6.0]])
    assert list(gp.neighbourhood(step, [1], hops=1)) == [0, 1]
    assert list(gp.neighbourhood(step, [1], hops=2)) == [0, 1, 2]
