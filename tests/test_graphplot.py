"""Graph-view data (gwsource.graphplot) on a hand-built split and a single-model MF6 step."""

import numpy as np
import pytest

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


def test_single_model_step_layers_and_positions(model_run):
    """A plain read_step (no blocks) is one model: layer zones, node layers and cell centres."""
    from gwsource.export import cell_centres

    run = model_run("m2_dis3lay")
    step = gs.read_step(run.ws)
    nlay = step.grid_shape[0]
    per_layer = step.n_cells // nlay
    zones, names = gp.layer_zones(step)
    assert names == [f"layer {k + 1}" for k in range(nlay)]
    np.testing.assert_array_equal(zones, np.arange(step.n_cells) // per_layer)
    np.testing.assert_array_equal(gp.node_layers(step), zones)
    np.testing.assert_allclose(gp.node_positions(step), cell_centres(run.grb_file))
    graph = gp.zone_graph(step, zones, names)
    assert graph.flow.shape == (nlay, nlay) and graph.flow.sum() > 0.0


def test_alluvial_shows_the_lowest_band():
    """The y-limit sits one gap below the bottom of the longer stack, sources or groups."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    gap = 0.02
    matrix = np.array([[1.0, 8.0], [5.0, 0.5], [0.5, 9.0]])
    for m in (matrix, matrix.T):
        fig, ax = plt.subplots()
        labels, groups = [f"s{i}" for i in range(m.shape[0])], [f"g{j}" for j in range(m.shape[1])]
        gp.plot_alluvial(labels, groups, m, ax, colors=["C0", "C1", "C2"], gap=gap)
        # the bands are scaled so that the longer stack, with its gaps, runs from 1 down to 0
        assert ax.get_ylim()[0] == pytest.approx(-gap)
        plt.close(fig)
