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

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.prt import PrtConfig, fan_points, track_particles

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
