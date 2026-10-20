"""Forward particle tracking with MF6 PRT against the Eulerian mean travel time (models 1 and 3).

Both the Eulerian and the advective flux-weighted mean travel time of all water reaching the
well equal (water volume that ends at the well) / (well rate); they differ only through the
capture-zone edge, which full mixing smears over about one cell width h. For a capture zone of
plan size L = sqrt(sum F x area) the expected relative difference is therefore O(h / L), and
that is the tolerance (h = 50 m, L ~ 840 m, so ~6 %). The comparison uses the Eulerian time
to the exit cell, because PRT stops particles on entering the well cell. The particle-count
error is checked separately: the captured particle flow must match the well rate to 1 %
(release points are a midpoint quadrature of the uniform areal sources).

Observed (porosity 0.3, 16 points per DIS cell, MF6 nightly, 2026-10-02):
- model 1 (DIS): PRT 9590 d, Eulerian to exit cell 9574 d (+0.17 %), mean_time 9607 d;
  captured flow 800.4 of 800 m3/d; by source: recharge 10433 vs 10379 d, river 2605 vs 2909 d.
- model 3 (DISV): PRT 9475 d vs 9421 d (+0.6 %); captured flow 800.4 of 800 m3/d.
Per cell (release cells with PRT arrivals): correlation of the mean arrival with the Eulerian
time to the exit cell 0.98 (DIS) and 0.95 (DISV), median PRT / Eulerian - 1 of -6 % (DIS) and
-7 % (DISV); mean absolute difference of the capture fraction 0.04 (DIS) and 0.06 (DISV),
largest on the capture-zone edge, where full mixing and advection legitimately differ cell by
cell. Only the correlation is asserted, loosely (> 0.9).
"""

from dataclasses import replace

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.prt import (
    IFLOWFACE_BOTTOM,
    IFLOWFACE_TOP,
    PrtConfig,
    _dis_polygons,
    fan_points,
    term_points,
    track_particles,
)

POROSITY = 0.3


def eulerian_to_exit_cell(step: gs.FlowStep, res, tt) -> float:
    """Return the Eulerian flux-weighted mean time to the exit cell over all source inflow."""
    source = cell_budget(step, flow_edges(step)).source
    f = res.fraction_through["wel"]
    to_exit = tt.weighted_time["wel"] - tt.exit_cell_time["wel"]
    return float(source @ to_exit / (source @ f))


def per_cell_report(res, tt, prt) -> dict[str, float]:
    """Return per-cell comparison statistics (correlation, mean abs capture-fraction difference)."""
    euler = tt.mean_time_to_exit_cell["wel"]
    both = np.isfinite(prt.cell_mean_arrival) & np.isfinite(euler) & (euler > 0)
    released = np.isfinite(prt.cell_capture_fraction)
    diff = prt.cell_capture_fraction[released] - res.fraction_through["wel"][released]
    return {
        "n_cells": int(both.sum()),
        "correlation": float(np.corrcoef(prt.cell_mean_arrival[both], euler[both])[0, 1]),
        "median_rel_diff": float(np.median(prt.cell_mean_arrival[both] / euler[both] - 1.0)),
        "capture_fraction_mae": float(np.abs(diff).mean()),
    }


@pytest.mark.parametrize("key", ["m1_dis", "m3_disv"])
def test_prt_mean_arrival_matches_eulerian(key, model_run, mf6_exe, tmp_path):
    """Flux-weighted PRT arrival at the well agrees with the Eulerian mean within h / L."""
    run = model_run(key)
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    tt = gs.travel_time(step, res, POROSITY)
    prt = track_particles(
        run.ws, step, res, "wel", PrtConfig(porosity=POROSITY), mf6_exe, tmp_path / "prt"
    )
    q = tt.group_inflow["wel"]
    assert prt.captured_flow == pytest.approx(q, rel=0.01)
    h = run.notes["spec"].delr
    capture_size = np.sqrt(np.sum(res.fraction_through["wel"] * step.area))
    tol = h / capture_size
    euler = eulerian_to_exit_cell(step, res, tt)
    assert abs(prt.mean_arrival / euler - 1.0) < tol, (prt.mean_arrival, euler, tol)
    assert abs(prt.mean_arrival / tt.mean_transit_time["wel"] - 1.0) < tol
    report = per_cell_report(res, tt, prt)
    print(key, prt.mean_arrival, euler, tt.mean_transit_time["wel"], prt.captured_flow, report)
    assert report["correlation"] > 0.9


def test_fan_points_cover_polygon():
    """Release points are area-weighted: weights sum to 1 and their centroid is the polygon's."""
    polygon = np.array([[0.0, 0.0], [4.0, 0.0], [5.0, 3.0], [1.0, 4.0]])
    points, weights = fan_points(polygon, 3)
    assert len(points) == 4 * 9
    assert weights.sum() == pytest.approx(1.0)
    x, y = polygon[:, 0], polygon[:, 1]
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    cross = x * yn - xn * y
    centroid = np.array([((x + xn) * cross).sum(), ((y + yn) * cross).sum()]) / (3.0 * cross.sum())
    np.testing.assert_allclose(weights @ points, centroid, rtol=1e-12)


def test_prt_refuses_disu(model_run, mf6_exe, tmp_path):
    """PRT supports DIS and DISV only: a DISU model is refused with a clear message."""
    run = model_run("m4_disu_vert")
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    with pytest.raises(AssertionError, match="DIS and DISV"):
        track_particles(run.ws, step, res, "wel", PrtConfig(POROSITY), mf6_exe, tmp_path)


def test_without_thinning_weak_sinks_overcount(model_run, mf6_exe, tmp_path):
    """Passing other weak sinks unthinned over-counts the well flow (observed 851 of 800 m3/d)."""
    run = model_run("m1_dis")
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    config = PrtConfig(porosity=POROSITY, subdivisions=1, thin_weak_sinks=False)
    prt = track_particles(run.ws, step, res, "wel", config, mf6_exe, tmp_path / "prt")
    assert prt.captured_flow > 1.02 * res.destination_inflow["wel"]
    print("unthinned captured flow", prt.captured_flow)


def test_layered_capture_matches_inflow(model_run, mf6_exe, tmp_path):
    """Layered model, wells in the bottom layer: the captured particle flow closes on the inflow.

    It guards against two ways of under-counting the capture: releasing all points at the water
    table (top-layer particles stay there, as the top face carries no flow) and stopping
    particles in the first well cell, which drops the weight the weak well passes on to the
    strong one. Observed 402.6 of 405 m3/d.
    """
    run = model_run("m2_dis3lay")
    step = gs.read_step(run.ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    config = PrtConfig(porosity=POROSITY, subdivisions=3, z_levels=2)
    prt = track_particles(run.ws, step, res, "wel", config, mf6_exe, tmp_path / "prt")
    print("layered captured flow", prt.captured_flow, "of", res.destination_inflow["wel"])
    assert prt.captured_flow == pytest.approx(res.destination_inflow["wel"], rel=0.02)
    weak = run.notes["weak_well_node"]
    assert res.fraction_through["wel"][weak] > 0.9  # the weak well's cell drains to the strong well


def test_term_points_follow_iflowface():
    """IFLOWFACE 0 fills the volume, -1 / -2 the top / bottom face, i > 0 lateral edge i."""
    polygon = _dis_polygons(np.array([10.0]), np.array([4.0]))[0]  # SW, NW, NE, SE
    local_z = np.array([0.25, 0.75])
    xy, z, share = term_points(polygon, 0, 2, local_z)
    assert len(z) == 16 * 2 and set(z) == {0.25, 0.75}
    for face, height in ((IFLOWFACE_TOP, 1.0), (IFLOWFACE_BOTTOM, 0.0)):
        xy, z, share = term_points(polygon, face, 2, local_z)
        assert len(z) == 16 and np.all(z == height)
    edges = {1: (0, None), 2: (None, 4.0), 3: (10.0, None), 4: (None, 0.0)}  # W, N, E, S
    for face, (x, y) in edges.items():
        xy, z, share = term_points(polygon, face, 2, local_z)
        assert len(z) == 16 * 2 and share.sum() == pytest.approx(1.0)
        if x is not None:
            np.testing.assert_allclose(xy[:, 0], x)
        if y is not None:
            np.testing.assert_allclose(xy[:, 1], y)
    with pytest.raises(AssertionError, match="not a face"):
        term_points(polygon, 5, 2, local_z)


def test_top_face_recharge_is_released_on_the_top_face(model_run, mf6_exe, tmp_path):
    """Recharge assigned to the top face (IFLOWFACE = -1) is released there and closes the budget.

    Model 2 with RCH AUXILIARY IFLOWFACE = -1 (same GWF flows). PRT then brings the recharge in
    through the top face: it is the uppermost water, stays above the regional CHD inflow and
    leaves at the east edge, so no recharge particle reaches the bottom-layer wells. Observed
    (k = 3, 2 levels): released on the top face 405.8 of 405 m3/d, recharge 0; seeded over the
    cell volume instead (as if IFLOWFACE were 0) 412.7, of which 6.9 recharge, released below
    the top where PRT's velocity field carries no recharge water. The CHD particles are the
    same in both runs, so the difference is the recharge alone.
    """
    run = model_run("m2_dis3lay_top")
    step = gs.read_step(run.ws)
    rch = step.package_names.index("RCH")
    assert np.all(step.term_iflowface[step.term_package == rch] == IFLOWFACE_TOP)
    assert np.all(step.term_iflowface[step.term_package != rch] == 0)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    config = PrtConfig(porosity=POROSITY, subdivisions=3, z_levels=2)
    prt = track_particles(run.ws, step, res, "wel", config, mf6_exe, tmp_path / "face")
    volume_step = replace(step, term_iflowface=None)
    volume = track_particles(run.ws, volume_step, res, "wel", config, mf6_exe, tmp_path / "vol")
    face_rch, vol_rch = (p.release.package == "RCH" for p in (prt, volume))
    q = res.destination_inflow["wel"]
    print("top-face recharge: captured", prt.captured_flow, "volume seeding", volume.captured_flow,
          "recharge", prt.captured_weight[face_rch].sum(), volume.captured_weight[vol_rch].sum())
    assert np.all(prt.release.z[face_rch] == 1.0)
    assert prt.captured_flow == pytest.approx(q, rel=0.02)
    assert prt.captured_weight[face_rch].sum() < 0.5
    assert volume.captured_weight[vol_rch].sum() > 5.0  # spurious recharge capture
    excess = volume.captured_flow - prt.captured_flow
    assert excess == pytest.approx(volume.captured_weight[vol_rch].sum(), abs=0.5)


def test_capture_along_paths_follows_weight_past_partial_sinks():
    """A particle passing a partial destination cell keeps the rest of its weight downstream."""
    from gwsource.prt import capture_along_paths

    visits = {
        "particle": np.array([0, 0, 0, 1]),
        "cell": np.array([0, 1, 2, 2]),
        "time": np.array([0.0, 10.0, 30.0, 0.0]),
    }
    share = np.array([0.0, 0.4, 1.0])
    survival = np.array([0.5, 0.6, 0.0])  # cell 0 loses half to another sink
    captured, mean_time = capture_along_paths(visits, 2, share, survival)
    np.testing.assert_allclose(captured, [0.5 * 0.4 + 0.5 * 0.6 * 1.0, 1.0])
    np.testing.assert_allclose(mean_time, [(0.2 * 10.0 + 0.3 * 30.0) / 0.5, 0.0])


def test_prt_needs_a_single_steady_period(model_run, mf6_exe, tmp_path):
    """Model 6 has four periods: tracking any of its steps is refused before PRT runs."""
    run = model_run("m6_transient")
    for kstpkper in ((0, 0), (0, 1)):
        step = gs.read_step(run.ws, kstpkper=kstpkper)
        res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
        with pytest.raises(AssertionError, match="single steady stress period"):
            track_particles(run.ws, step, res, "wel", PrtConfig(POROSITY), mf6_exe, tmp_path)


def period_block(iper: int, keyword: str) -> str:
    """Return an STO PERIOD block holding one keyword."""
    return f"BEGIN period {iper}\n  {keyword}\nEND period\n"


def test_sto_period_one_transient(tmp_path):
    """STO without a PERIOD block is transient in MF6; STEADY-STATE in period 1 makes it steady."""
    from gwsource.prt import _sto_period_one_transient

    texts = {
        "BEGIN griddata\n  ss\n    CONSTANT 1e-5\nEND griddata\n": True,
        period_block(1, "STEADY-STATE") + period_block(2, "TRANSIENT"): False,
        period_block(1, "TRANSIENT"): True,
        period_block(2, "STEADY-STATE"): True,
    }
    for i, (text, transient) in enumerate(texts.items()):
        sto_file = tmp_path / f"m{i}.sto"
        sto_file.write_text(text)
        assert _sto_period_one_transient(sto_file) is transient, text


def test_unterminated_particles_are_refused():
    """A particle without a termination record fails the check, with its share of the weight."""
    from gwsource.prt import ReleasePoints, assert_terminated

    release = ReleasePoints(*(np.zeros(3) for _ in range(4)), np.array([1.0, 2.0, 3.0]),
                            np.full(3, "RCH", dtype=object))
    ends = {"cell": np.array([4, -1, 7]), "status": np.array([1, -1, 1]), "time": np.ones(3)}
    with pytest.raises(AssertionError, match=r"1 of 3 particles did not terminate \(flow weight 2"):
        assert_terminated(ends, release)
    assert_terminated({**ends, "cell": np.array([4, 5, 7]), "status": np.array([1, 2, 1])}, release)


def test_write_prt_options(model_run, mf6_exe, tmp_path):
    """write_prt options: STOP_AT_WEAK_SINK, termination records only, scalar porosity, clear_ws."""
    from gwsource.prt import load_prt_grid, release_points, write_prt

    run = model_run("m1_dis")
    step = gs.read_step(run.ws)
    grid = load_prt_grid(run.ws, run.name, "DIS")
    release = release_points(step, grid, np.ones(step.n_cells, bool), None, 1, np.array([0.5]))
    prt_ws = tmp_path / "prt"
    prt_ws.mkdir()
    (prt_ws / "stale.txt").write_text("left over")
    config = PrtConfig(porosity=POROSITY)
    write_prt(prt_ws, run.ws, grid, release, config, mf6_exe, budget_file=run.budget_file,
              stop_at_weak_sink=True, track_release=False, track_exit=False, clear_ws=True)
    assert not (prt_ws / "stale.txt").exists()
    prp = (prt_ws / "prt.prp").read_text().upper()
    oc = (prt_ws / "prt.oc").read_text().upper()
    mip = (prt_ws / "prt.mip").read_text().upper()
    assert "STOP_AT_WEAK_SINK" in prp and "EXTEND_TRACKING" in prp
    assert "TRACK_TERMINATE" in oc and "TRACK_RELEASE" not in oc and "TRACK_EXIT" not in oc
    assert "CONSTANT" in mip
