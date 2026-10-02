"""Transient snapshot loop on model 6: streaming statistics against a brute-force calculation.

The brute force reads and traces every step independently (gs.read_step), stores all of them,
and computes each statistic with numpy over the stored stack. Step lengths for time weighting
are computed here from the TDIS period data, independently of the budget-file headers.
"""

import numpy as np
import pytest

import gwsource as gs
from gwsource import mf6io

GROUPS = {
    "wel": {"package": "WEL"},
    "riv": {"package": "RIV"},
    "sto": {"package": ["STO-SS", "STO-SY"]},
}
OUTPUTS = ("fraction_through", "volume_from", "fraction_from_cell_input")
THRESHOLD = 0.05
VALUE_RANGE = (0.02, 0.5)


def tdis_step_lengths(perioddata) -> dict[tuple[int, int], float]:
    """Return {(kstp, kper): DELT} from (perlen, nstp, tsmult) period data."""
    lengths = {}
    for kper, (perlen, nstp, tsmult) in enumerate(perioddata):
        if tsmult == 1.0:
            first = perlen / nstp
        else:
            first = perlen * (tsmult - 1.0) / (tsmult**nstp - 1.0)
        for kstp in range(nstp):
            lengths[(kstp, kper)] = first * tsmult**kstp
    return lengths


def brute_force(run, steps, mode: str, outputs) -> dict[str, dict[str, np.ndarray]]:
    """Return stack[output][group] -> (n_steps, n_cells) by tracing each step on its own."""
    trace = gs.backward if mode == "backward" else gs.forward
    stack = {o: {g: [] for g in GROUPS} for o in outputs}
    for kstpkper in steps:
        step = gs.read_step(run.ws, kstpkper=kstpkper)
        res = trace(step, {g: gs.select(step, **kw) for g, kw in GROUPS.items()})
        for o in outputs:
            for g in GROUPS:
                stack[o][g].append(getattr(res, o)[g])
    return {o: {g: np.array(v) for g, v in by_g.items()} for o, by_g in stack.items()}


def expected_stats(values: np.ndarray, weights: np.ndarray) -> dict[str, np.ndarray]:
    """Return every statistic of a (steps, cells) stack with NaN = undefined, by plain numpy."""
    valid = np.isfinite(values)
    w = weights[:, None] * valid
    v = np.where(valid, values, 0.0)
    n_valid = valid.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = (w * v).sum(axis=0) / w.sum(axis=0)
        exceed = (valid & (v > THRESHOLD)).sum(axis=0)
        inside = valid & (v >= VALUE_RANGE[0]) & (v <= VALUE_RANGE[1])
        prob = (w * inside).sum(axis=0) / w.sum(axis=0)
    asn = np.select([n_valid == 0, exceed == 0, exceed == n_valid], [np.nan, 0.0, 1.0], 0.5)
    return {
        "min": _nan_reduce(values, valid, np.min),
        "max": _nan_reduce(values, valid, np.max),
        "mean": mean,
        "asn": asn,
        "exceedance_count": exceed,
        "probability_in_range": prob,
    }


def _nan_reduce(values: np.ndarray, valid: np.ndarray, reduce) -> np.ndarray:
    """Return reduce over steps of the valid values per cell, NaN where none is valid."""
    out = np.full(values.shape[1], np.nan)
    for c in np.flatnonzero(valid.any(axis=0)):
        out[c] = reduce(values[valid[:, c], c])
    return out


@pytest.mark.parametrize("weighting", ["time", "equal"])
def test_backward_stats_match_brute_force(weighting, model_run):
    """Every statistic of every output and group matches the brute force, for both weightings."""
    run = model_run("m6_transient")
    reader = gs.open_model(run.ws)
    config = gs.TransientConfig(
        outputs=OUTPUTS, weighting=weighting, threshold=THRESHOLD, value_range=VALUE_RANGE
    )
    res = gs.trace_transient(reader, GROUPS, "backward", config)
    assert len(res.steps) == 13 and res.groups == list(GROUPS)
    lengths = tdis_step_lengths(run.sim.tdis.perioddata.array)
    expected_w = [lengths[ks] if weighting == "time" else 1.0 for ks in res.steps]
    np.testing.assert_allclose(res.weights, expected_w, rtol=1e-6)
    weights = res.weights  # checked against TDIS above; the sums below are then exact
    stack = brute_force(run, res.steps, "backward", OUTPUTS)
    for output in OUTPUTS:
        for group in GROUPS:
            values = stack[output][group]
            exp = expected_stats(values, weights)
            stats = ("min", "max", "mean")
            if output == OUTPUTS[0]:
                stats += ("asn", "exceedance_count", "probability_in_range")
            for stat in stats:
                got = res.stats[stat][output][group]
                np.testing.assert_allclose(
                    got,
                    exp[stat],
                    rtol=1e-12,
                    atol=1e-13,
                    equal_nan=True,
                    err_msg=f"{stat} {output} {group}",
                )
    assert set(res.stats["asn"]) == {OUTPUTS[0]}
    asn = res.stats["asn"]["fraction_through"]["wel"]
    assert set(np.unique(asn[np.isfinite(asn)])) <= {0.0, 0.5, 1.0}
    assert {0.0, 0.5}.issubset(set(np.unique(asn)))


def test_time_weighting_changes_the_mean(model_run):
    """Time weighting and equal weighting give different means on unequal steps."""
    reader = gs.open_model(model_run("m6_transient").ws)
    timed = gs.trace_transient(reader, GROUPS, config=gs.TransientConfig(weighting="time"))
    equal = gs.trace_transient(reader, GROUPS, config=gs.TransientConfig(weighting="equal"))
    diff = (
        timed.stats["mean"]["fraction_through"]["wel"]
        - equal.stats["mean"]["fraction_through"]["wel"]
    )
    assert np.abs(diff).max() > 1e-3


def test_forward_series_and_step_selection(model_run):
    """Forward mode with a period list keeps a series whose stats match the stored steps."""
    run = model_run("m6_transient")
    reader = gs.open_model(run.ws)
    groups = {"rch": {"package": "RCH"}, "riv": {"package": "RIV"}}
    config = gs.TransientConfig(steps=[1, 3], keep_series=True, weighting="equal")
    res = gs.trace_transient(reader, groups, "forward", config)
    assert res.steps == [(k, p) for p in (1, 3) for k in range(4)]
    series = res.series["source_fraction"]["rch"]
    assert series.shape == (8, reader.grid.ia.size - 1)
    np.testing.assert_allclose(res.stats["mean"]["source_fraction"]["rch"], series.mean(axis=0))
    step = gs.read_step(run.ws, kstpkper=(2, 3))
    single = gs.forward(step, {g: gs.select(step, **kw) for g, kw in groups.items()})
    np.testing.assert_array_equal(series[6], single.source_fraction["rch"])
    explicit = gs.TransientConfig(steps=[(0, 1), (3, 3)])
    assert gs.trace_transient(reader, groups, "forward", explicit).steps == [(0, 1), (3, 3)]
    with pytest.raises(AssertionError, match="not in the budget file"):
        gs.trace_transient(reader, groups, "forward", gs.TransientConfig(steps=[(9, 9)]))


def test_reader_opens_files_once(model_run, monkeypatch):
    """The loop reuses the open grid and budget files: no grid re-read, shared IA/JA arrays."""
    reader = gs.open_model(model_run("m6_transient").ws)

    def fail(*args, **kwargs):
        raise AssertionError("grid file read again")

    monkeypatch.setattr(mf6io, "read_grid", fail)
    monkeypatch.setattr(mf6io.flopy.utils, "CellBudgetFile", fail)
    seen = []
    res = gs.trace_transient(
        reader, lambda step: seen.append(step) or {"wel": gs.select(step, package="WEL")}
    )
    assert len(seen) == 13 and all(s.ia is seen[0].ia for s in seen)
    assert res.solver_used == ["topological"] * 13
    np.testing.assert_allclose(
        res.group_inflow["wel"],
        [800, 1200, 1200, 1200, 1200, 400, 400, 400, 400, 1000, 1000, 1000, 1000],
    )


def test_transient_npz_export(model_run, tmp_path):
    """Transient statistics round-trip through .npz with the step table."""
    reader = gs.open_model(model_run("m6_transient").ws)
    res = gs.trace_transient(reader, GROUPS, config=gs.TransientConfig(threshold=0.1))
    path = gs.export.save_transient_npz(tmp_path / "stats.npz", res)
    with np.load(path) as data:
        np.testing.assert_array_equal(
            data["fraction_through_mean__wel"],
            gs.export.to_grid(res.template, res.stats["mean"]["fraction_through"]["wel"]),
        )
        assert data["kstpkper"].shape == (13, 2) and "fraction_through_asn__sto" in data.files
