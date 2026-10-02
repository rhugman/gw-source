"""End-to-end checks on the MF6 test models: grid-type equivalence, cycles, weak sinks, export."""

import numpy as np
import pytest

import gwsource as gs
from gwsource.export import result_arrays


def all_outputs(ws) -> tuple[gs.FlowStep, dict[str, np.ndarray]]:
    """Return a step and every backward and forward output (per package) as flat arrays."""
    step = gs.read_step(ws)
    groups = gs.groups_by_package(step)
    arrays = {}
    for prefix, res in (("back", gs.backward(step, groups)), ("fwd", gs.forward(step, groups))):
        for key, values in result_arrays(step, res).items():
            arrays[f"{prefix}:{key}"] = values.ravel()
    return step, arrays


@pytest.mark.parametrize("disu_key", ["m4_disu_vert", "m4_disu_novert"])
def test_dis_and_disu_identical(disu_key, model_run):
    """The DIS and DISU builds of model 1 give the same outputs to machine precision."""
    dis_step, dis = all_outputs(model_run("m1_dis").ws)
    disu_step, disu = all_outputs(model_run(disu_key).ws)
    assert disu_step.grid_shape == (dis_step.n_cells,)
    assert dis.keys() == disu.keys() and len(dis) > 20
    for key in dis:
        np.testing.assert_allclose(disu[key], dis[key], rtol=1e-12, atol=1e-12, equal_nan=True, err_msg=key)


def well_source_shares(ws) -> tuple[dict[str, float], float]:
    """Return the share of the WEL water from each source package and the capture-zone area."""
    step = gs.read_step(ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    by_term = {k: float(v.sum()) for k, v in res.volume_from_by_term["wel"].items()}
    total = sum(by_term.values())
    capture_area = float(np.sum(res.fraction_through["wel"] * step.area))
    return {k: v / total for k, v in by_term.items()}, capture_area


def test_disv_matches_dis_within_cell_size_tolerance(model_run):
    """DISV (Voronoi) and DIS versions of model 1 agree on integral capture quantities.

    Both grids have cells of about h = 50 m on a domain of L = 1500 m. Full mixing spreads the
    capture zone by about a cell either side, so the source shares of the well water and the
    capture-zone area (sum of F x cell area) are compared with a tolerance of h / L = 0.033
    (absolute for shares, relative for the area). Observed: shares differ by about 0.013,
    areas by about 1.5 %.
    """
    spec = model_run("m1_dis").notes["spec"]
    tol = spec.delr / (spec.ncol * spec.delr)
    dis_shares, dis_area = well_source_shares(model_run("m1_dis").ws)
    disv_shares, disv_area = well_source_shares(model_run("m3_disv").ws)
    assert set(dis_shares) == set(disv_shares) == {"RCH", "RIV"}
    for key in dis_shares:
        assert abs(disv_shares[key] - dis_shares[key]) < tol, (key, dis_shares, disv_shares)
    assert abs(disv_area / dis_area - 1.0) < tol


def test_xt3d_cycles_detected_and_solved_by_block_lu(model_run):
    """Model 5 has flow cycles: reported, solved by block LU (equal to plain LU); topological refuses."""
    step = gs.read_step(model_run("m5_xt3d").ws)
    cycles = gs.diagnostics.cycle_report(step)
    assert len(cycles) >= 1 and all(c.n_cells > 1 and c.min_edge_flow > 0.0 for c in cycles)
    groups = {"wel": gs.select(step, package="WEL")}
    res = gs.backward(step, groups)
    assert res.solver_used == ["block"] and len(res.cycles) == len(cycles)
    lu = gs.backward(step, groups, gs.TraceConfig(solver="lu"))
    np.testing.assert_allclose(res.fraction_through["wel"], lu.fraction_through["wel"], atol=1e-13)
    with pytest.raises(AssertionError, match="cycles"):
        gs.backward(step, groups, gs.TraceConfig(solver="topological"))
    net = gs.backward(step, groups, gs.TraceConfig(accounting="net", remove_cycles=True))
    assert net.solver_used == ["topological"]


def test_weak_sink_gross_vs_net(model_run):
    """Model 2's small well: gross captures only its 5 m3/d; net absorbs the cell's throughflow."""
    run = model_run("m2_dis3lay")
    step = gs.read_step(run.ws)
    weak = {"weak": gs.select(step, package="WEL", cells=[run.notes["weak_well_node"]])}
    gross = gs.backward(step, weak)
    net = gs.backward(step, weak, gs.TraceConfig(accounting="net"))
    assert gross.destination_inflow["weak"] == pytest.approx(5.0)
    assert gross.volume_from["weak"].sum() == pytest.approx(5.0, rel=1e-8)
    assert net.destination_inflow["weak"] > 10.0 * 5.0
    assert net.volume_from["weak"].sum() == pytest.approx(net.destination_inflow["weak"], rel=1e-8)
    assert np.all(gross.fraction_through["weak"] <= net.fraction_through["weak"] + 1e-12)


def test_export_grid_and_npz(model_run, tmp_path):
    """Gridded outputs have NaN in inactive cells and round-trip through .npz."""
    step = gs.read_step(model_run("m1_dis").ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    grid = gs.export.to_grid(step, res.fraction_through["wel"])
    assert grid.shape == (1, 20, 30)
    assert np.isnan(grid[0, 0, 27]) and not np.isnan(grid[0, 0, 26])
    path = gs.export.save_npz(tmp_path / "wel.npz", step, res)
    with np.load(path) as data:
        np.testing.assert_array_equal(data["fraction_through__wel"], grid)
        assert "volume_from_by_term__wel__RCH" in data.files
        assert data["active"].sum() == 594


def test_flux_outputs_need_area(model_run):
    """Flux outputs are volumes over cell area, and None when the step has no areas."""
    run = model_run("m4_disu_novert")
    files = gs.find_model_files(run.ws)
    no_area = gs.read_step_files(files.grb_file, files.budget_file)
    res = gs.backward(no_area, {"wel": gs.select(no_area, package="WEL")})
    assert res.flux_through is None and res.flux_from is None
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    np.testing.assert_allclose(res.flux_from["wel"] * 2500.0, res.volume_from["wel"])


def test_quicklook_map(model_run):
    """plot_map draws a FloPy map of a per-cell result."""
    import matplotlib

    matplotlib.use("Agg")
    run = model_run("m3_disv")
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    collection = gs.export.plot_map(run.grb_file, step, res.fraction_through["wel"])
    assert collection is not None
