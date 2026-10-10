"""Transient tracking on MF6 models: GWT agreement, volume modes, duality, limit and exports.

GWT check: a separate GWT simulation reads model 6's head and budget files through FMI (ADV
UPSTREAM, no DSP, MST porosity POROSITY, SSM concentration 1 on the tagged packages through SPC
files, FLOW_IMBALANCE_CORRECTION on unless stated). With volume_mode="gwt" the tracked fractions
must equal the GWT concentrations at every saved step (agreement reached: about 2e-15).
"""

import numpy as np
import pytest
from models.gwt import build_gwt_fmi
from test_multimodel import map_back, split_and_run

import gwsource as gs
from gwsource import tracking as tr

POROSITY = 0.3
GWT_ATOL = 1e-8
EXACT = 1e-10

GWT_CASES = {  # name: (tagged GWF packages, GWT initial concentration, flow-error correction)
    "rch": (("rch",), 0.0, True),
    "chd_riv": (("chd", "riv"), 0.0, True),
    "initial": ((), 1.0, True),
    "rch_initial": (("rch",), 1.0, True),
    "rch_no_correction": (("rch",), 0.0, False),
}


def gwt_concentrations(ucn_file, steps) -> np.ndarray:
    """Return the GWT concentration of every saved step, (n_steps, n_cells)."""
    import flopy

    ucn = flopy.utils.HeadFile(str(ucn_file), text="CONCENTRATION")
    return np.array([np.asarray(ucn.get_data(kstpkper=ks), float).ravel() for ks in steps])


@pytest.mark.parametrize("case", GWT_CASES)
def test_forward_matches_gwt(case, model_run, tmp_path, mf6_exe):
    """volume_mode='gwt': c equals the MF6 GWT unit concentration at every step."""
    tagged, strt, correction = GWT_CASES[case]
    run = model_run("m6_transient")
    ucn = build_gwt_fmi(run, tmp_path, mf6_exe, POROSITY, tagged, strt, correction)
    reader = gs.open_model(run.ws)
    sources = {"tagged": {"package": [p.upper() for p in tagged]}} if tagged else None
    config = tr.TrackingConfig(
        porosity=POROSITY,
        volume_mode="gwt",
        flow_error_correction=correction,
        initial_water={"initial": "all"} if strt else None,
    )
    result = tr.track_forward(reader, sources, config)
    c = sum(result.source_fraction[g] for g in result.groups)
    active = reader.grid.idomain.ravel() > 0
    conc = gwt_concentrations(ucn, result.steps)
    error = np.abs(conc[:, active] - c[:, active]).max()
    assert error < GWT_ATOL, f"{case}: max |c - C_gwt| = {error:.2e}"
    assert c[:, active].max() > 0.01  # 301 days of a model with a ~9000-day turnover


@pytest.mark.parametrize("tag", ["rch", "stream_inflow"])
def test_package_network_matches_gwt_sft_mvt(tag, model_run, tmp_path, mf6_exe):
    """Model 7 with SFR nodes and MVR edges vs GWT with SFT and MVT: cells and reaches agree.

    Drain water is moved to the first reach, which loses it back to the aquifer; the SFR
    storage flow is 0, so SFT carries the reach volume from the previous step (gwt mode copies
    this rule).
    """
    import flopy

    run = model_run("m7_mover")
    tagged, inflow = (("rch",), 0.0) if tag == "rch" else ((), 1.0)
    ucn = build_gwt_fmi(run, tmp_path, mf6_exe, POROSITY, tagged, sft_inflow=inflow)
    reader = gs.open_simulation(run.ws, package_nodes=("SFR",))
    source = {"package": "RCH"} if tag == "rch" else {"package": "SFR", "term": "EXT-INFLOW"}
    config = tr.TrackingConfig(porosity=POROSITY, volume_mode="gwt")
    result = tr.track_forward(reader, {"t": source}, config)
    step = reader.read(reader.steps[-1])
    cells, reaches = step.blocks[0], step.block("SFR")
    active = step.active[cells.nodes]
    conc = gwt_concentrations(ucn, result.steps)
    sft = flopy.utils.HeadFile(str(tmp_path / "gwt.sft.ucn"), text="CONCENTRATION")
    for n, kstpkper in enumerate(result.steps):
        c = result.source_fraction["t"][n]
        assert np.abs(conc[n][active] - c[cells.nodes][active]).max() < GWT_ATOL
        reach_conc = np.asarray(sft.get_data(kstpkper=kstpkper), float).ravel()
        assert np.abs(reach_conc - c[reaches.nodes]).max() < GWT_ATOL
    assert result.source_fraction["t"][-1].max() > 1e-5


def cell_water_balance_errors(reader, config: tr.TrackingConfig) -> np.ndarray:
    """Return, per step, max over cells of |V^new - V^old - dt (I - O - r)| / max(V^old, V^new).

    The volumes are those of the tracker (tracking.step_volumes, carried from step to step);
    cells without water are left out. r is included when the flow-error correction is on.
    """
    previous, errors = None, []
    for kstpkper in reader.steps:
        step, delt = reader.read(kstpkper), reader.step_length(kstpkper)
        flows = tr.step_flows(step, config.storage_texts)
        volumes = tr.step_volumes(step, flows, config, delt, previous)
        residual = flows.residual if config.flow_error_correction else 0.0
        error = np.abs(volumes.new - volumes.old - delt * (flows.inflow - flows.outflow - residual))
        scale = np.maximum(volumes.old, volumes.new)
        wet = scale > 0.0
        errors.append(float((error[wet] / scale[wet]).max(initial=0.0)))
        previous = volumes.new
    return np.asarray(errors)


def check_flow_mode(reader, sources: dict, destinations: dict) -> tuple:
    """Run both volume modes; assert flow-mode water and tagged balances; return both runs."""
    runs = {}
    for mode in tr.VOLUME_MODES:
        config = tr.TrackingConfig(porosity=POROSITY, volume_mode=mode,
                                   initial_water={"init": "all"})
        fwd = tr.track_forward(reader, sources, config)
        bwd = tr.track_backward(reader, destinations, config)
        runs[mode] = (fwd, bwd)
    fwd, bwd = runs["flow"]
    assert cell_water_balance_errors(reader, fwd.config).max() < EXACT
    assert np.all(fwd.volume_jump == 0.0)
    for g in fwd.groups:
        assert tr.forward_balance_error(fwd, g) < EXACT
        assert np.all(fwd.balance[g]["volume_adjustment"] == 0.0)
    every = tr.track_forward(reader, lambda step: {"all": gs.select(step)}, fwd.config)
    total = every.source_fraction["all"] + every.source_fraction["init"]
    assert np.allclose(total[:, bwd.active[-1]], 1.0, atol=1e-9)
    assert np.nanmax(np.abs(bwd.fraction_unaccounted)) < 1e-8  # flow residual only
    gwt_fwd, gwt_bwd = runs["gwt"]
    assert gwt_fwd.volume_jump.max() > 0.0
    assert np.nanmax(np.abs(gwt_bwd.fraction_unaccounted)) > 1e-4
    return runs


MODEL6_SOURCES = {"rch": {"package": "RCH"}, "riv": {"package": "RIV"}}
MODEL6_DESTINATIONS = {"wel": {"package": "WEL"}, "riv": {"package": "RIV"}}


def test_flow_mode_exact_balances_model6(model_run):
    """Model 6, flow mode: exact water and tagged balances; differs from gwt mode (porosity 0.3
    vs specific yield 0.2) by a few per cent of the fraction at most."""
    reader = gs.open_model(model_run("m6_transient").ws)
    runs = check_flow_mode(reader, MODEL6_SOURCES, MODEL6_DESTINATIONS)
    flow, gwt = runs["flow"][0], runs["gwt"][0]
    diff = max(np.abs(flow.source_fraction[g] - gwt.source_fraction[g]).max() for g in flow.groups)
    assert 1e-6 < diff < 0.05, diff


NETWORK_SOURCES = {
    "rch": {"package": "RCH"},
    "rain": {"package": "LAK", "term": "RAINFALL"},
    "uzf": {"package": "UZF", "term": "INFILTRATION"},
}
NETWORK_DESTINATIONS = {
    "wel": {"package": "WEL"},
    "lake_out": {"package": "LAK", "term": "EXT-OUTFLOW"},
}


def test_flow_mode_exact_balances_package_network(model_run):
    """Model 9 with LAK and UZF nodes (transient period), flow mode: exact balances."""
    reader = gs.open_simulation(model_run("m9_lak_uzf").ws, package_nodes=("LAK", "UZF"))
    check_flow_mode(reader, NETWORK_SOURCES, NETWORK_DESTINATIONS)


def check_duality(reader, sources: dict, destinations: dict,
                  substeps: int = 1) -> dict[str, float]:
    """Assert the forward/adjoint duality and the backward closure in both volume modes.

    The closure needs volumes consistent with the storage flows, which the SFT rule of gwt
    mode breaks for SFR reaches; it is then checked in flow mode only. Returns the largest
    relative errors reached ("duality", "closure") and the number of duality pairs checked
    ("n_duality").
    """
    has_sfr = tr.sfr_nodes(reader.read(reader.steps[0])).any()
    worst = {"duality": 0.0, "closure": 0.0, "n_duality": 0}
    for mode in tr.VOLUME_MODES:
        config = tr.TrackingConfig(porosity=POROSITY, volume_mode=mode,
                                   initial_water={"init": "all"}, substeps=substeps)
        fwd = tr.track_forward(reader, sources, config, sinks=destinations)
        bwd = tr.track_backward(reader, destinations, config, sources=sources)
        for d in destinations:
            if mode == "flow" or not has_sfr:
                closure = tr.backward_closure(bwd, d).relative_error
                assert closure < EXACT
                worst["closure"] = max(worst["closure"], closure)
            for s in [*sources, "init"]:
                check = tr.tracking_duality(fwd, s, bwd, d)
                assert check.relative_error < EXACT, (mode, s, d, check)
                worst["duality"] = max(worst["duality"], check.relative_error)
                worst["n_duality"] += 1
            assert tr.tracking_duality(fwd, "init", bwd, d).rhs > 0.0
    return worst


def test_duality_model6(model_run):
    """Model 6: forward tagged outflow equals the adjoint inner product."""
    reader = gs.open_model(model_run("m6_transient").ws)
    check_duality(reader, MODEL6_SOURCES, MODEL6_DESTINATIONS)


def test_duality_model6_substeps(model_run):
    """Model 6 with 5 transport sub-steps per flow step: duality and closure still exact."""
    reader = gs.open_model(model_run("m6_transient").ws)
    check_duality(reader, MODEL6_SOURCES, MODEL6_DESTINATIONS, substeps=5)


@pytest.fixture(scope="module")
def split_model6(model_run, tmp_path_factory, mf6_exe):
    """Model 6 split into four models (GWF-GWF exchanges), run once."""
    run = model_run("m6_transient")
    ws = tmp_path_factory.mktemp("m6_tracking_split")
    return run, ws, split_and_run(run, "m6_transient", ws, mf6_exe)


def test_duality_split_model6(split_model6):
    """Model 6 split into four models: duality, and the same fractions as the single model."""
    run, ws, splitter = split_model6
    reader = gs.open_simulation(ws)
    check_duality(reader, MODEL6_SOURCES, MODEL6_DESTINATIONS)
    config = tr.TrackingConfig(porosity=POROSITY)
    split = tr.track_forward(reader, MODEL6_SOURCES, config)
    single = tr.track_forward(gs.open_model(run.ws), MODEL6_SOURCES, config)
    step = reader.read(reader.steps[-1])
    active = gs.open_model(run.ws).grid.idomain.ravel() > 0
    for g in MODEL6_SOURCES:
        for n in (0, 4, len(split.steps) - 1):
            mapped = map_back(splitter, step, split.source_fraction[g][n])
            assert np.allclose(mapped[active], single.source_fraction[g][n][active], atol=1e-8)


def test_duality_package_network_transient(model_run):
    """Model 9 with LAK and UZF nodes, steady then transient period: duality and closure."""
    reader = gs.open_simulation(model_run("m9_lak_uzf").ws, package_nodes=("LAK", "UZF"))
    check_duality(reader, NETWORK_SOURCES, NETWORK_DESTINATIONS)


MOVER_SOURCES = {"rch": {"package": "RCH"}, "stream": {"package": "SFR", "term": "EXT-INFLOW"}}
MOVER_DESTINATIONS = {
    "east": {"boundnames": ["well_east"]},
    "outlet": {"package": "SFR", "term": "EXT-OUTFLOW"},
}


def test_duality_mover_network(model_run):
    """Model 7 with SFR nodes and MVR edges (two steady periods, the well list changes)."""
    reader = gs.open_simulation(model_run("m7_mover").ws, package_nodes=("SFR",), boundnames=True)
    check_duality(reader, MOVER_SOURCES, MOVER_DESTINATIONS)


def group_errors(series: dict, steady: dict, index: int, active: np.ndarray) -> list[float]:
    """Return max |series[g][index] - steady[g]| over the active cells, one value per group."""
    return [float(np.abs(series[g][index] - steady[g])[active].max()) for g in series]


def steady_limit_errors(reader) -> dict[str, float]:
    """Return max |transient - steady| over active cells for model 10: forward c at the end and
    adjoint f at the start (largest over groups), and forward c at the start and adjoint f at
    the end (smallest over groups), against the steady source_fraction and fraction_through."""
    step = reader.read(reader.steps[-1])
    sources = {"rch": {"package": "RCH"}, "riv": {"package": "RIV"}}
    destinations = {"wel": {"package": "WEL"}, "riv": {"package": "RIV"}}
    steady_fwd = gs.forward(step, {g: gs.select(step, **kw) for g, kw in sources.items()})
    steady_bwd = gs.backward(step, {g: gs.select(step, **kw) for g, kw in destinations.items()})
    config = tr.TrackingConfig(porosity=POROSITY)
    fwd = tr.track_forward(reader, sources, config)
    bwd = tr.track_backward(reader, destinations, config)
    c, g = fwd.source_fraction, steady_fwd.source_fraction
    w, f = bwd.fraction_through, steady_bwd.fraction_through
    return {
        "g_end": max(group_errors(c, g, -1, step.active)),
        "g_start": min(group_errors(c, g, 0, step.active)),
        "f_start": max(group_errors(w, f, 0, step.active)),
        "f_end": min(group_errors(w, f, -1, step.active)),
        "n_groups": len(c) + len(w),
    }


STEADY_G_ATOL = 1e-11  # reached: 1e-13 (time stepping and round-off)
STEADY_F_ATOL = 1e-8  # reached: 7e-10, the size of the cell budget errors of the flow solve


def test_constant_flows_converge_to_steady_snapshot(model_run):
    """Model 10 (model 1's flows held for 4e5 days in 120 equal steps): forward c tends to the
    steady source_fraction at the end, adjoint f at the start to the steady fraction_through.

    The G error is what is left of the time-stepping tail (water still in the model from the
    last steps); the F error is limited by the cell budget errors of the MF6 solution (about
    the water the flow-error correction removes, 7e-10). The tolerances leave a factor of 100
    and 15 for other MF6 versions and platforms. At the other end of the run both errors are
    large (c at the start, f at the end), so the test cannot pass trivially.
    """
    errors = steady_limit_errors(gs.open_model(model_run("m10_constant").ws))
    assert errors["g_end"] < STEADY_G_ATOL and errors["g_start"] > 0.1
    assert errors["f_start"] < STEADY_F_ATOL and errors["f_end"] > 0.1


def test_tracking_exports(model_run, tmp_path):
    """netCDF with a time dimension (forward and backward) and one npz per step."""
    pytest.importorskip("xarray")
    import xarray as xr

    reader = gs.open_model(model_run("m6_transient").ws)
    config = tr.TrackingConfig(porosity=POROSITY, initial_water={"init": "all"})
    fwd = tr.track_forward(reader, MODEL6_SOURCES, config)
    bwd = tr.track_backward(reader, MODEL6_DESTINATIONS, config)
    ds = gs.export.tracking_dataset(fwd)
    assert ds["tracked_source_fraction"].dims == ("time", "group", "layer", "row", "col")
    assert ds.sizes["time"] == len(fwd.steps)
    path = tmp_path / "fwd.nc"
    ds.to_netcdf(path)
    back = xr.open_dataset(path)
    values = back["tracked_source_fraction"].sel(group="rch").values[-1].ravel()
    assert np.allclose(values[reader.grid.idomain.ravel() > 0],
                       fwd.source_fraction["rch"][-1][reader.grid.idomain.ravel() > 0])
    back.close()
    ds_b = gs.export.tracking_dataset(bwd)
    assert np.allclose(ds_b["time"].values, bwd.totim - bwd.delt)
    assert "fraction_in_storage_at_end" in ds_b and "destination_outflow" in ds_b
    files = gs.export.save_tracking_npz(tmp_path / "npz", bwd, prefix="bwd")
    assert len(files) == len(bwd.steps)
    with np.load(files[3]) as data:
        assert data["fraction_through__wel"].shape == (1, 20, 30)
        assert np.allclose(np.nan_to_num(data["fraction_through__wel"]).ravel(),
                           bwd.fraction_through["wel"][3])


def test_network_npz_export(model_run, tmp_path):
    """A network tracking result is saved over all global nodes (package nodes included)."""
    reader = gs.open_simulation(model_run("m9_lak_uzf").ws, package_nodes=("LAK", "UZF"))
    fwd = tr.track_forward(reader, NETWORK_SOURCES, tr.TrackingConfig(porosity=POROSITY))
    files = gs.export.save_tracking_npz(tmp_path, fwd)
    with np.load(files[-1]) as data:
        assert data["source_fraction__rain"].shape == (fwd.template.n_cells,)
    ds = gs.export.tracking_dataset(fwd)
    assert ds["tracked_source_fraction"].dims[:2] == ("time", "group")
