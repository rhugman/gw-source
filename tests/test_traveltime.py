"""Eulerian mean travel time and mean age: identities, analytic cases, grid equivalence, transient.

Identities (derived in gwsource.traveltime), with r the per-cell residual, V the water volume,
m and n the fraction-weighted times, x the exit-cell residence term, d the destination sinks:
    backward:   sum(Src m) - sum(r m) = sum(V F)
    exit cell:  sum(Src (m - x)) - sum(r (m - x)) = sum(V F) - sum(tau d)
    forward:    sum(Snk n) + sum(r n) = sum(V G)
They must hold to 1e-10 relative on every steady test model (models 1-5).
"""

import numpy as np
import pytest

import gwsource as gs
from gwsource.traveltime import exit_cell_closure, travel_time_closure

STEADY = ("m1_dis", "m2_dis3lay", "m3_disv", "m4_disu_vert", "m4_disu_novert", "m5_xt3d")
POROSITY = 0.3
RTOL = 1e-10


def _assert_identity(check) -> None:
    """Assert an identity holds to RTOL relative to its right-hand side."""
    assert abs(check.error) <= RTOL * max(abs(check.rhs), 1.0), check


@pytest.mark.parametrize("key", STEADY)
def test_identities_on_steady_models(key, model_run):
    """The travel-time and age identities hold to 1e-10 for every package group."""
    step = gs.read_step(model_run(key).ws)
    assert step.notes["thickness_from"] == "DATA-SAT"
    groups = gs.groups_by_package(step)
    back, fwd = gs.backward(step, groups), gs.forward(step, groups)
    tt_back = gs.travel_time(step, back, POROSITY)
    tt_fwd = gs.travel_time(step, fwd, POROSITY)
    for name in groups:
        _assert_identity(travel_time_closure(step, back, tt_back, name))
        _assert_identity(exit_cell_closure(step, back, tt_back, name))
        _assert_identity(travel_time_closure(step, fwd, tt_fwd, name))
        if tt_back.group_inflow[name] > 0:
            ratio = tt_back.flux_weighted_time[name] / tt_back.mean_transit_time[name]
            assert ratio == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("key", STEADY)
def test_times_positive_where_captured(key, model_run):
    """Mean travel times to the well are finite and positive wherever F exceeds the threshold."""
    step = gs.read_step(model_run(key).ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    tt = gs.travel_time(step, res, POROSITY)
    f = res.fraction_through["wel"]
    captured = f > tt.fraction_threshold
    assert captured.sum() > 10
    for values in (tt.mean_time["wel"], tt.mean_time_to_exit_cell["wel"]):
        assert np.all(np.isfinite(values[captured]))
        assert np.all(np.isnan(values[~captured]))
    assert np.all(tt.mean_time["wel"][captured] > 0.0)
    assert np.all(tt.mean_time_to_exit_cell["wel"][captured] >= -1e-9)


@pytest.mark.parametrize("disu_key", ["m4_disu_vert", "m4_disu_novert"])
def test_dis_and_disu_identical(disu_key, model_run):
    """Travel times and ages of the DIS and DISU builds of model 1 agree to machine precision."""
    out = {}
    for key in ("m1_dis", disu_key):
        step = gs.read_step(model_run(key).ws)
        groups = gs.groups_by_package(step)
        out[key] = (
            gs.travel_time(step, gs.backward(step, groups), POROSITY),
            gs.travel_time(step, gs.forward(step, groups), POROSITY),
        )
    for dis, disu in zip(out["m1_dis"], out[disu_key]):
        np.testing.assert_allclose(disu.water_volume, dis.water_volume, rtol=1e-12)
        for g in dis.groups:
            for name in ("weighted_time", "mean_time"):
                np.testing.assert_allclose(
                    getattr(disu, name)[g], getattr(dis, name)[g], rtol=1e-11, equal_nan=True
                )
            assert disu.mean_transit_time[g] == pytest.approx(
                dis.mean_transit_time[g], rel=1e-12, nan_ok=True
            )


def _chain_step(split: float = 0.0) -> gs.FlowStep:
    """Recharge 10 into cell 0, flowing 0 -> 1 -> 2 -> well; cell 1 optionally loses split."""
    rch, wel, drn = gs.Package("RCH", "RCH"), gs.Package("WEL", "WEL"), gs.Package("DRN", "DRN")
    q12 = 10.0 - split
    return gs.from_edges(
        3,
        src=[0, 1],
        dst=[1, 2],
        q=[10.0, q12],
        term_cell=[0, 2, 1],
        term_flow=[10.0, -q12, -split],
        term_package=[0, 1, 2],
        packages=[rch, wel, drn],
        area=np.array([1.0, 2.0, 4.0]),
        saturated_thickness=np.array([10.0, 10.0, 10.0]),
    )


def test_chain_analytic():
    """On a chain, the mean time is the sum of V / Q of the cells passed, ending cell included."""
    step = _chain_step()
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    tt = gs.travel_time(step, res, 0.5)
    v = 0.5 * 10.0 * np.array([1.0, 2.0, 4.0])
    tau = v / 10.0
    np.testing.assert_allclose(tt.residence_time, tau)
    np.testing.assert_allclose(tt.mean_time["wel"], np.cumsum(tau[::-1])[::-1])
    np.testing.assert_allclose(tt.mean_time_to_exit_cell["wel"], [tau[0] + tau[1], tau[1], 0.0])
    assert tt.mean_transit_time["wel"] == pytest.approx(v.sum() / 10.0)
    fwd = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    age = gs.travel_time(step, fwd, 0.5)
    np.testing.assert_allclose(age.mean_time["rch"], np.cumsum(tau))


def test_weak_sink_does_not_change_conditional_time():
    """A weak sink upstream removes water but, under full mixing, not the time of what passes on."""
    step = _chain_step(split=4.0)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    tt = gs.travel_time(step, res, 0.5)
    v = 0.5 * 10.0 * np.array([1.0, 2.0, 4.0])
    tau = v / np.array([10.0, 10.0, 6.0])
    np.testing.assert_allclose(res.fraction_through["wel"], [0.6, 0.6, 1.0])
    np.testing.assert_allclose(tt.mean_time["wel"], [tau.sum(), tau[1:].sum(), tau[2]])
    # flux-weighted over the recharge: sum(V F) / Q_D
    assert tt.mean_transit_time["wel"] == pytest.approx((v[0] * 0.6 + v[1] * 0.6 + v[2]) / 6.0)


def test_factor_is_reused_or_rebuilt(model_run):
    """Travel times are the same with the stored factorisation and with a rebuilt one."""
    step = gs.read_step(model_run("m5_xt3d").ws)
    res = gs.backward(step, gs.groups_by_package(step))
    assert res.factor is not None and res.factor.kind == "block"
    stored = gs.travel_time(step, res, POROSITY)
    res.factor = None
    rebuilt = gs.travel_time(step, res, POROSITY)
    for g in stored.groups:
        np.testing.assert_allclose(rebuilt.weighted_time[g], stored.weighted_time[g], atol=1e-9)


def test_heads_fallback_matches_saturation(model_run):
    """Without DATA-SAT the saturated thickness from heads equals DATA-SAT x (top - bot)."""
    for key in ("m1_dis", "m2_dis3lay"):
        run = model_run(key)
        reader = gs.open_model(run.ws)
        step = reader.read((0, 0))
        from_heads, source = reader.thickness((0, 0), None, step.active)
        assert source == "heads"
        np.testing.assert_allclose(from_heads, step.saturated_thickness, atol=1e-8)


def test_clear_errors(model_run):
    """Net mode, missing areas and missing thickness are refused with a message."""
    run = model_run("m4_disu_novert")
    files = gs.find_model_files(run.ws)
    no_area = gs.read_step_files(files.grb_file, files.budget_file)
    res = gs.backward(no_area, {"wel": gs.select(no_area, package="WEL")})
    with pytest.raises(AssertionError, match="areas"):
        gs.travel_time(no_area, res, POROSITY)
    step = gs.read_step(model_run("m1_dis").ws)
    net = gs.backward(step, {"wel": gs.select(step, package="WEL")}, gs.TraceConfig("net"))
    with pytest.raises(AssertionError, match="gross"):
        gs.travel_time(step, net, POROSITY)
    step.saturated_thickness = None
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    with pytest.raises(AssertionError, match="saturated thickness"):
        gs.travel_time(step, res, POROSITY)


def test_per_cell_porosity(model_run):
    """Doubling the porosity everywhere doubles every time; a per-cell array is accepted."""
    step = gs.read_step(model_run("m1_dis").ws)
    res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
    base = gs.travel_time(step, res, 0.2)
    double = gs.travel_time(step, res, np.full(step.n_cells, 0.4))
    np.testing.assert_allclose(double.mean_time["wel"], 2.0 * base.mean_time["wel"], rtol=1e-12)


def test_transient_snapshot_travel_time(model_run):
    """trace_transient with porosity matches per-step travel_time on model 6 (time-weighted mean)."""
    run = model_run("m6_transient")
    reader = gs.open_model(run.ws)
    config = gs.TransientConfig(porosity=POROSITY, outputs=("mean_time", "fraction_through"))
    res = gs.trace_transient(reader, {"wel": {"package": "WEL"}}, config=config)
    stack, transit, weights = [], [], []
    for kstpkper in reader.steps:
        step = gs.read_step(run.ws, kstpkper=kstpkper)
        back = gs.backward(step, {"wel": gs.select(step, package="WEL")})
        tt = gs.travel_time(step, back, POROSITY)
        stack.append(tt.mean_time["wel"])
        transit.append(tt.mean_transit_time["wel"])
        weights.append(step.notes["delt"])
    stack, w = np.array(stack), np.array(weights)[:, None]
    valid = np.isfinite(stack)
    with np.errstate(invalid="ignore"):
        mean = (np.where(valid, stack, 0.0) * w).sum(axis=0) / (valid * w).sum(axis=0)
    np.testing.assert_allclose(res.stats["mean"]["mean_time"]["wel"], mean, rtol=1e-12)
    top = np.where(valid, stack, -np.inf).max(axis=0)
    expected_max = np.where(valid.any(axis=0), top, np.nan)
    np.testing.assert_allclose(res.stats["max"]["mean_time"]["wel"], expected_max)
    np.testing.assert_allclose(res.group_mean_transit_time["wel"], transit, rtol=1e-12)
