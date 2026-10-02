"""Ensemble driver on five realisations of model 1 with random K fields, against brute force.

The brute force traces every realisation on its own (gs.read_step, gs.backward,
gs.travel_time), stores all outputs in a float64 stack and computes every statistic with numpy.
Exact quantiles keep a float32 stack, so they match to float32 rounding; histogram quantiles
must lie within one bin width of the exact ones.
"""

import dataclasses
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pytest

import gwsource as gs
from models import BaseSpec, build_base_dis

N_REAL = 5
POROSITY = 0.3
GROUPS = {"wel": {"package": "WEL"}, "riv": {"package": "RIV"}}
OUTPUTS = ("fraction_through", "volume_from", "mean_time")
THRESHOLDS = (0.0, 0.1, 0.5)
QUANTILES = (0.0, 0.1, 0.5, 0.9, 1.0)
TIME_RANGE = (0.0, 1.0e5)


@pytest.fixture(scope="module")
def realisations(tmp_path_factory, mf6_exe):
    """Build and run five model-1 realisations with log-normal K; return their folders."""
    root = tmp_path_factory.mktemp("ensemble")
    spec = BaseSpec()
    rng = np.random.default_rng(42)
    for i in range(N_REAL):
        k = spec.k * np.exp(rng.normal(0.0, 0.7, size=(1, spec.nrow, spec.ncol)))
        build_base_dis(root / f"real_{i:03d}", mf6_exe, dataclasses.replace(spec, k=k))
    return gs.list_realisations(root, "real_*")


def brute_force(workspaces) -> dict[tuple[str, str], np.ndarray]:
    """Return stack[(output, group)] -> (n_real, n_cells) float64, traced one by one."""
    stack = {}
    for ws in workspaces:
        step = gs.read_step(ws)
        res = gs.backward(step, {g: gs.select(step, **kw) for g, kw in GROUPS.items()})
        tt = gs.travel_time(step, res, POROSITY)
        for output in OUTPUTS:
            source = tt if output == "mean_time" else res
            for group, values in getattr(source, output).items():
                stack.setdefault((output, group), []).append(values)
    return {k: np.array(v) for k, v in stack.items()}


def _config(**kwargs) -> gs.EnsembleConfig:
    """Return the ensemble configuration of these tests (overridable)."""
    base = {
        "outputs": OUTPUTS,
        "thresholds": THRESHOLDS,
        "quantiles": QUANTILES,
        "porosity": POROSITY,
        "histogram_range": {"mean_time": TIME_RANGE, "volume_from": (0.0, 50.0)},
        "histogram_bins": 400,
    }
    base.update(kwargs)
    return gs.EnsembleConfig(**base)


def expected(values: np.ndarray) -> dict:
    """Return min, max, mean, count, exceedance and quantiles of a stack (NaN = undefined)."""
    valid = np.isfinite(values)
    count = valid.sum(axis=0)
    v = np.where(valid, values, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = {
            "min": np.where(count > 0, np.where(valid, values, np.inf).min(axis=0), np.nan),
            "max": np.where(count > 0, np.where(valid, values, -np.inf).max(axis=0), np.nan),
            "mean": np.where(count > 0, v.sum(axis=0) / count, np.nan),
            "count": count,
            "exceedance": {
                t: np.where(count > 0, (valid & (v > t)).sum(axis=0) / count, np.nan)
                for t in THRESHOLDS
            },
        }
    quant = np.full((len(QUANTILES), values.shape[1]), np.nan)
    has = count > 0
    quant[:, has] = np.nanquantile(values[:, has], QUANTILES, axis=0)
    out["quantiles"] = {q: quant[i] for i, q in enumerate(QUANTILES)}
    return out


def check_against_brute_force(result: gs.EnsembleResult, stack: dict, quantile_atol) -> None:
    """Assert every statistic equals the brute-force value (quantiles within quantile_atol)."""
    for (output, group), values in stack.items():
        want = expected(values)
        for name in ("min", "max", "mean"):
            np.testing.assert_allclose(
                result.stats[name][output][group],
                want[name],
                rtol=1e-12,
                atol=1e-12,
                equal_nan=True,
                err_msg=f"{name} {output} {group}",
            )
        np.testing.assert_array_equal(result.stats["count"][output][group], want["count"])
        for t in THRESHOLDS:
            np.testing.assert_allclose(
                result.exceedance[t][output][group], want["exceedance"][t], equal_nan=True
            )
        for q in QUANTILES:
            got, ref = result.quantiles[q][output][group], want["quantiles"][q]
            np.testing.assert_array_equal(np.isnan(got), np.isnan(ref))
            ok = ~np.isnan(ref)
            tol = quantile_atol(output, ref[ok])
            assert np.all(np.abs(got[ok] - ref[ok]) <= tol), (output, group, q)


def test_exact_quantiles_match_brute_force(realisations):
    """With the stack in memory every statistic matches brute force (quantiles to float32)."""
    result = gs.run_ensemble(realisations, GROUPS, _config())
    assert result.quantile_method == "exact"
    assert len(result.realisations) == N_REAL and result.groups == ["wel", "riv"]
    stack = brute_force(realisations)
    check_against_brute_force(result, stack, lambda output, ref: 1e-6 * np.abs(ref) + 1e-9)
    capture = result.exceedance[0.0]["fraction_through"]["wel"]
    assert 0.0 < capture.max() <= 1.0 and np.any((capture > 0) & (capture < 1))
    assert result.mean_transit_time["wel"].shape == (N_REAL,)


def test_histogram_quantiles_within_one_bin(realisations):
    """Below the memory budget the quantiles come from histograms, within one bin width."""
    result = gs.run_ensemble(realisations, GROUPS, _config(memory_budget=0))
    assert result.quantile_method == "histogram"
    width = result.bin_width
    assert width["fraction_through"] == pytest.approx(1.0 / 400)
    stack = brute_force(realisations)
    check_against_brute_force(result, stack, lambda output, ref: width[output] * (1 + 1e-9))


def process_pool_available() -> bool:
    """Return False where the OS refuses process pools (e.g. a sandbox without semaphores)."""
    try:
        ProcessPoolExecutor(max_workers=1).shutdown()
    except (PermissionError, NotImplementedError):  # raised by the system-limits check
        return False
    return True


def test_serial_and_parallel_identical(realisations):
    """Two worker processes give bit-identical statistics to the serial run."""
    if not process_pool_available():
        pytest.skip("process pools are not permitted in this environment")
    serial = gs.run_ensemble(realisations, GROUPS, _config())
    parallel = gs.run_ensemble(realisations, GROUPS, _config(max_workers=2))
    for name, by_output in serial.stats.items():
        for output, by_group in by_output.items():
            for group, values in by_group.items():
                np.testing.assert_array_equal(parallel.stats[name][output][group], values)
    for q in QUANTILES:
        for output in OUTPUTS:
            for group in GROUPS:
                np.testing.assert_array_equal(
                    parallel.quantiles[q][output][group], serial.quantiles[q][output][group]
                )
    np.testing.assert_array_equal(parallel.group_inflow["wel"], serial.group_inflow["wel"])


def test_grid_mismatch_refused(realisations, model_run):
    """A realisation with different connectivity is refused."""
    other = model_run("m2_dis3lay").ws
    config = gs.EnsembleConfig(outputs=("fraction_through",))
    with pytest.raises(AssertionError, match="IA/JA"):
        gs.run_ensemble([realisations[0], other], {"wel": {"package": "WEL"}}, config)


def test_travel_time_outputs_need_porosity():
    """Asking for travel-time outputs without porosity is refused at configuration."""
    with pytest.raises(AssertionError, match="porosity"):
        gs.EnsembleConfig(outputs=("mean_time",)).resolved_outputs()


def test_groups_by_boundname(model_run):
    """With boundnames=True, a realisation's groups can be selected by boundname."""
    ws = model_run("m7_mover").ws
    groups = {"east": {"boundnames": ["well_east"]}}
    config = gs.EnsembleConfig(outputs=("fraction_through",), boundnames=True)
    result = gs.run_ensemble([ws, ws], groups, config)
    step = gs.read_step(ws, boundnames=True)
    direct = gs.backward(step, {"east": gs.select(step, boundnames=["well_east"])})
    np.testing.assert_allclose(
        result.stats["mean"]["fraction_through"]["east"], direct.fraction_through["east"], atol=1e-12
    )
    assert result.group_inflow["east"][0] == pytest.approx(800.0, rel=1e-6)
