"""Steady forward fractions against MF6 GWT unit concentrations run to equilibrium.

Gross accounting is how transport treats sinks: a sink removes water at the concentration of its
cell, whatever share of the cell's outflow it takes. The steady forward fraction G
(`source_fraction`) must therefore equal the equilibrium concentration C of advection-only
transport with concentration 1 on the source and 0 on every other inflow.

GWT setup (tests/models/gwt.py): a separate simulation reads the steady flows through FMI with
FLOW_IMBALANCE_CORRECTION (each cell's residual leaves at the cell concentration, so the cell
equation is normalised by its inflow, as in forward mode). ADV UPSTREAM is the transport scheme
that matches full mixing: each face carries the concentration of the cell the water leaves, and
a cell is one mixed volume. No DSP, MST porosity 0.3 (porosity sets only how fast equilibrium is
reached), initial concentration 0. One transport period of EQUILIBRIUM_DAYS in 60 steps growing
by 1.2 (first step 35 d, last 1.7e6 d); FMI reuses the single saved flow step for every transport
step. Equilibrium criterion: the largest concentration change over the last step is below
EQUILIBRIUM_TOL.

Models: 1 (recharge, and river leakage from the losing reaches; the 11 gaining river cells are
partly capturing sinks: 1.5 to 54 % of their outflow goes to the river, the rest to neighbours),
2 (three layers, recharge and the inflowing CHD edge; a weak well in the bottom layer takes a
small share of its cell's outflow) and 7 with SFR reaches as nodes and MVR edges (GWT with SFT
and MVT; recharge and the stream inflow).

Agreement reached (GWT outer/inner DVCLOSE 1e-12/1e-13, RCLOSE 1e-9): max |C - G| <= 3e-11 on
models 1 and 2 (1e-3, 1e-5, 1e-8 after 1e5, 2e5, 4e5 days for model 1 recharge), about 1e-8 on
model 7 with the test model's flow solver settings. On model 7 the limit is the flow solve: the
reach budgets close only to the flow solver tolerance, and SFT reads the SFR budget's side of
the aquifer exchange while the network takes the GWF side; with the flow model solved 100 times
tighter, max |C - G| falls to 3e-11. Net accounting is the control
that fails: at model 2's weak well it is 14 times the transport result.
"""

import flopy
import numpy as np
import pytest
from models.gwt import GWT_IMS, build_gwt_fmi
from models.mover import build_mover_dis

import gwsource as gs

POROSITY = 0.3
EQUILIBRIUM_DAYS = 1.0e7
SHORT_RUNS_DAYS = (1.0e5, 2.0e5, 4.0e5)
N_STEPS, STEP_MULT = 60, 1.2
EQUILIBRIUM_TOL = 1e-12  # max |dC| over the last transport step
GWT_ATOL = 1e-10  # max |C - G| at equilibrium
NETWORK_ATOL = 1e-7  # model 7 with the test model's flow solver settings (see module docstring)
# With the default GWT_IMS (RCLOSE 1e-12) the GWT run of model 1 stops converging after about
# 2000 days: the residual asked for is near the round-off of mass rates up to ~1e3 m3/d.
EQUILIBRIUM_IMS = {**GWT_IMS, "outer_dvclose": 1e-12, "inner_dvclose": 1e-13, "rcloserecord": 1e-9}
TIGHT_FLOW_IMS = {"outer_dvclose": 1e-11, "inner_dvclose": 1e-12, "rcloserecord": 1e-10}

CELL_CASES = {  # name: (model, GWF pname tagged in GWT, gwsource selection of the same source)
    "m1_rch": ("m1_dis", "rch", {"package": "RCH"}),
    "m1_riv": ("m1_dis", "riv", {"package": "RIV"}),
    "m2_rch": ("m2_dis3lay", "rch", {"package": "RCH"}),
    "m2_chd": ("m2_dis3lay", "chd", {"package": "CHD"}),
}
NETWORK_CASES = {  # name: (GWF pnames tagged, SFT inflow concentration, gwsource selection)
    "rch": (("rch",), 0.0, {"package": "RCH"}),
    "stream_inflow": ((), 1.0, {"package": "SFR", "term": "EXT-INFLOW"}),
}


def transport_periods(n_flow_periods: int, days: float) -> list[tuple]:
    """Return GWT periods: 1-day copies of the earlier flow periods, then one long period."""
    return [(1.0, 1, 1.0)] * (n_flow_periods - 1) + [(days, N_STEPS, STEP_MULT)]


def last_two_steps(ucn_file) -> tuple[np.ndarray, np.ndarray]:
    """Return the concentrations of the last two saved steps (flattened)."""
    data = flopy.utils.HeadFile(str(ucn_file), text="CONCENTRATION").get_alldata()
    data = data.reshape(len(data), -1)
    return data[-1], data[-2]


def steady_fraction(step: gs.FlowStep, selection: dict) -> np.ndarray:
    """Return the steady forward fraction of one source group."""
    return gs.forward(step, {"g": gs.select(step, **selection)}).source_fraction["g"]


def run_to_equilibrium(run, ws, exe, tagged, days: float, sft_inflow=None):
    """Run GWT on the saved flows for `days`; return the last and previous concentrations."""
    nper = run.sim.tdis.nper.get_data()
    ucn = build_gwt_fmi(
        run, ws, exe, POROSITY, tagged, sft_inflow=sft_inflow,
        perioddata=transport_periods(nper, days), ims=EQUILIBRIUM_IMS,
    )
    return last_two_steps(ucn)


@pytest.mark.parametrize("case", CELL_CASES)
def test_steady_forward_equals_gwt_equilibrium(case, model_run, tmp_path, mf6_exe):
    """G of one source equals the equilibrium GWT concentration in every active cell."""
    key, pname, selection = CELL_CASES[case]
    run = model_run(key)
    reader = gs.open_model(run.ws)
    step = reader.read(reader.steps[0])
    fraction = steady_fraction(step, selection)
    conc, previous = run_to_equilibrium(run, tmp_path, mf6_exe, (pname,), EQUILIBRIUM_DAYS)
    active = step.active
    change = np.abs(conc - previous)[active].max()
    error = np.abs(conc - fraction)[active]
    assert change < EQUILIBRIUM_TOL, f"{case}: not at equilibrium, last |dC| = {change:.1e}"
    assert error.max() < GWT_ATOL, f"{case}: max |C - G| = {error.max():.2e}"
    assert fraction[active].max() > 0.4  # every case tags a large share of some cell's water


def test_partial_sinks_are_exercised(model_run):
    """Models 1 and 2 have cells whose sinks take only part of the outflow (the gross case).

    Model 1: the gaining river cells, which also pass water on; model 2: the weak well.
    """
    reader = gs.open_model(model_run("m1_dis").ws)
    budget = gs.cell_budget(reader.read(reader.steps[0]))
    assert np.count_nonzero((budget.sink > 0.0) & (budget.edge_out > 0.0)) >= 5
    run = model_run("m2_dis3lay")
    reader = gs.open_model(run.ws)
    budget = gs.cell_budget(reader.read(reader.steps[0]))
    node = run.notes["weak_well_node"]
    share = budget.sink[node] / budget.outflow[node]
    assert 0.0 < share < 0.1, share


def test_net_accounting_does_not_match_gwt(model_run, tmp_path, mf6_exe):
    """Control: net accounting (fraction fixed at 1 in the source cells) does not match transport.

    At model 2's weak well (bottom layer) the recharge fraction is C = G = 6.0e-4; net mode,
    which counts every top-layer cell as wholly recharge water, gives 8.4e-3.
    """
    key, pname, selection = CELL_CASES["m2_rch"]
    run = model_run(key)
    reader = gs.open_model(run.ws)
    step = reader.read(reader.steps[0])
    groups = {"g": gs.select(step, **selection)}
    net = gs.forward(step, groups, gs.TraceConfig(accounting="net")).source_fraction["g"]
    conc, _ = run_to_equilibrium(run, tmp_path, mf6_exe, (pname,), EQUILIBRIUM_DAYS)
    node = run.notes["weak_well_node"]
    assert abs(conc[node] - steady_fraction(step, selection)[node]) < GWT_ATOL
    assert abs(conc[node] - net[node]) > 1e-3


@pytest.mark.parametrize("case", ["m1_rch", "m2_chd"])
def test_gwt_difference_shrinks_with_run_length(case, model_run, tmp_path, mf6_exe):
    """max |C - G| falls with the transport run length down to the solver level."""
    key, pname, selection = CELL_CASES[case]
    run = model_run(key)
    reader = gs.open_model(run.ws)
    step = reader.read(reader.steps[0])
    fraction = steady_fraction(step, selection)
    errors = []
    for days in (*SHORT_RUNS_DAYS, EQUILIBRIUM_DAYS):
        conc, _ = run_to_equilibrium(run, tmp_path / f"{days:g}", mf6_exe, (pname,), days)
        errors.append(np.abs(conc - fraction)[step.active].max())
    assert errors[0] > 1e-6 and errors[-1] < GWT_ATOL, errors
    assert all(a > b for a, b in zip(errors[:-2], errors[1:-1])), errors


def network_errors(run, ws, exe, case: str) -> tuple[float, float]:
    """Return max |C - G| over the active cells and over the reaches of model 7 (SFR nodes)."""
    tagged, inflow, selection = NETWORK_CASES[case]
    reader = gs.open_simulation(run.ws, package_nodes=("SFR",))
    step = reader.read(reader.steps[-1])
    fraction = steady_fraction(step, selection)
    conc, previous = run_to_equilibrium(run, ws, exe, tagged, EQUILIBRIUM_DAYS, sft_inflow=inflow)
    reach_conc, _ = last_two_steps(ws / "gwt.sft.ucn")
    cells, reaches = step.blocks[0], step.block("SFR")
    active = step.active[cells.nodes]
    assert np.abs(conc - previous)[active].max() < EQUILIBRIUM_TOL
    assert fraction[cells.nodes].max() > 0.5 and fraction[reaches.nodes].max() > 0.3
    cell_error = np.abs(conc - fraction[cells.nodes])[active].max()
    return cell_error, np.abs(reach_conc - fraction[reaches.nodes]).max()


@pytest.fixture(scope="module")
def m7_tight(tmp_path_factory, mf6_exe):
    """Model 7 with its flow model solved about 100 times tighter than the test default."""
    return build_mover_dis(tmp_path_factory.mktemp("m7_tight"), mf6_exe, ims_kwargs=TIGHT_FLOW_IMS)


@pytest.mark.parametrize("case", NETWORK_CASES)
def test_network_forward_equals_gwt_sft_equilibrium(case, model_run, m7_tight, tmp_path, mf6_exe):
    """Model 7 (SFR nodes, MVR) vs GWT with SFT and MVT at equilibrium: cells and reaches.

    The difference follows the flow solver tolerance: below NETWORK_ATOL with the test model's
    settings, and below GWT_ATOL (and at least 100 times smaller) with the tighter flow solve.
    """
    default = network_errors(model_run("m7_mover"), tmp_path / "default", mf6_exe, case)
    tight = network_errors(m7_tight, tmp_path / "tight", mf6_exe, case)
    assert max(default) < NETWORK_ATOL, default
    assert max(tight) < GWT_ATOL, tight
    assert max(tight) < 0.01 * max(default), (default, tight)
