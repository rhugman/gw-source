"""Verification table of the paper (Table 2, Fig. 2): the exact checks over the synthetic test models.

The test suite asserts each check against a tolerance; this collector records the error that is
actually reached, per model and check, so the paper can quote it. It builds and runs the test
models with the builders in tests/models (MF6 from <repo>/bin) and reuses the helpers of the
tests that compute the compared quantities.

Checks and error measures (one row per model and check in the CSV):

- backward_closure, forward_closure, duality: the gross identities of gwsource.diagnostics with
  the residual term, one group per package; error |lhs - residual term - rhs| / max(|rhs|, 1 m3/d),
  the largest over all groups (closure) or all destination/source pairs (duality) and all steps.
  Tolerance 1e-10 (tests/test_closure_duality.py).
- boundary_control: one group per sink term; max |sum_g F_g - 1| over cells with outflow.
  Tolerance 1e-12.
- dis_vs_disu: every backward and forward output of model 4 (DISU, with and without vertices)
  against model 1 (DIS); max |a - b| / max |a| per output, largest over outputs. Tolerance 1e-12.
- split_vs_single: models 1, 3 and 6 split into 2 to 4 models (Mf6Splitter, GWF-GWF exchanges)
  against the single model, every output and travel time; same measure as above, largest over
  outputs (and the four transient steps of model 6). Tolerance 1e-8 (the two runs agree only to
  the MF6 solver tolerance; tests/test_multimodel.py).
- tracking_vs_gwt: transient tracking (volume_mode "gwt") against MF6 GWT unit concentrations;
  max |c - C| over all steps and active cells (and SFR reaches on model 7), largest over the
  tagging cases of tests/test_tracking_mf6.py. Tolerance 1e-8.
- prt_capture: captured flow-weighted PRT particle flow against the destination inflow,
  |captured / inflow - 1|. Tolerance 0.01 (models 1, 3) and 0.02 (model 2), as in tests/test_prt.py;
  the error is quadrature (release points), not round-off.
- reference_example: net accounting on the 3x3 example of [FB13]; max |value - published| over
  fraction, volume through and volume from. Tolerance 1e-14 (tests/test_fb13_example.py).

- steady_g_vs_gwt: steady forward fraction G against MF6 GWT unit concentrations run to
  equilibrium (1e7 d, ADV upstream, no dispersion, FLOW_IMBALANCE_CORRECTION) on the steady
  flows of models 1, 2 and 7 (SFR nodes + MVR vs SFT + MVT); max |C - G| over active cells (and
  reaches), the largest over the tagging cases of tests/test_gwt_equilibrium.py. Tolerance
  1e-10 (models 1, 2) and 1e-7 (model 7 with the test model's flow solver settings; the note
  gives the value with the flow model solved about 100 times tighter).

Transient tracking checks (tests/test_tracking_mf6.py, tests/test_tracking.py). The collectors
call the tests' own helpers, which assert the test tolerances, and record() refuses an "ok"
row whose error exceeds its tolerance:

- tracking_vs_gwt (above).

- tracking_duality: forward tracking against backward tracking in time, |tagged outflow
  forward - adjoint inner product| / forward outflow, the largest over both volume options, all
  source (and initial-water) and destination pairs, on models 6 (1 and 5 transport sub-steps),
  6 split into 4 models, 7 (SFR + MVR) and 9 (LAK + UZF, transient period). Tolerance 1e-10.
- water_balance: "flow" volumes on models 6 and 9; each cell's water balance error relative to
  that cell's water volume, max_i |V^new - V^old - dt (I - O - r)| / max(V^old, V^new), the
  largest over cells and steps. Tolerance 1e-10.
- tagged_balance: "flow" volumes on models 6 and 9; for each tagged group (initial water
  included), the model-wide balance of tagged water in every step (change in tagged storage
  against tagged inflow minus outflow), its largest error relative to the group's largest
  balance term. Tolerance 1e-10.
- steady_limit_g, steady_limit_f: model 10 (model 1's flows held 4e5 d in 120 equal steps);
  max |c - G| at the end and max |w - F| at the start over active cells and groups. Tolerances
  1e-11 and 1e-8.
- substeps: m = 3 transport sub-steps against a flow model with 3 times more steps of the same
  flows (hand-built 15-cell network with flow loops and no storage, not an MF6 model, 6
  steps); every fraction, outflow and volume, max |a - b| / max |b| per output. The test
  itself asserts elementwise (rtol 1e-12, atol 1e-14). Tolerance 1e-12.

Models 7 to 9 are read as package networks (SFR; MAW; LAK and UZF nodes) and every saved step
is checked; model 6 is checked on every time step with storage as source and sink terms.
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.diagnostics import backward_closure, duality, forward_closure

REPO = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO / "tests"
POROSITY = 0.3

IDENTITY_MODELS = (
    "m1_dis", "m2_dis3lay", "m3_disv", "m4_disu_vert", "m4_disu_novert", "m5_xt3d",
    "m6_transient", "m7_mover", "m8_maw", "m9_lak_uzf",
)
NETWORKS = {"m7_mover": ("SFR",), "m8_maw": ("MAW",), "m9_lak_uzf": ("LAK", "UZF")}
DISU_MODELS = ("m4_disu_vert", "m4_disu_novert")
SPLIT_MODELS = {"m1_dis": ((0, 0),), "m3_disv": ((0, 0),),
                "m6_transient": ((0, 0), (3, 1), (0, 2), (3, 3))}
PRT_MODELS = {  # key: (PrtConfig keywords, tolerance)
    "m1_dis": ({}, 0.01),
    "m3_disv": ({}, 0.01),
    "m2_dis3lay": ({"subdivisions": 3, "z_levels": 2}, 0.02),
}
TOLERANCES = {
    "backward_closure": 1e-10,
    "forward_closure": 1e-10,
    "duality": 1e-10,
    "boundary_control": 1e-12,
    "dis_vs_disu": 1e-12,
    "split_vs_single": 1e-8,
    "tracking_vs_gwt": 1e-8,
    "reference_example": 1e-14,
    "tracking_duality": 1e-10,
    "water_balance": 1e-10,
    "tagged_balance": 1e-10,
    "steady_limit_g": 1e-11,
    "steady_limit_f": 1e-8,
    "substeps": 1e-12,
    "steady_g_vs_gwt": 1e-10,
}
MEASURES = {
    "backward_closure": "relative to destination inflow (absolute in m³/d below 1 m³/d)",
    "forward_closure": "relative to source inflow (absolute in m³/d below 1 m³/d)",
    "duality": "relative to forward source-to-destination flow (absolute in m³/d below 1 m³/d)",
    "steady_g_vs_gwt": "absolute (fraction)",
    "boundary_control": "absolute (fraction)",
    "dis_vs_disu": "relative to output maximum",
    "split_vs_single": "relative to output maximum",
    "tracking_vs_gwt": "absolute (fraction)",
    "prt_capture": "relative to destination inflow",
    "reference_example": "absolute (published values)",
    "tracking_duality": "relative to forward source-to-destination volume (absolute when zero)",
    "water_balance": "relative to the cell's water volume",
    "tagged_balance": "relative to largest term of the tagged-water balance",
    "steady_limit_g": "absolute (fraction)",
    "steady_limit_f": "absolute (fraction)",
    "substeps": "relative to output maximum",
}
CHECK_GROUPS = {  # Table 2 parts and Fig. 2 blocks, in table order
    "steady and snapshot checks": (
        "backward_closure", "forward_closure", "duality", "boundary_control", "steady_g_vs_gwt",
        "dis_vs_disu", "split_vs_single", "prt_capture", "reference_example",
    ),
    "transient tracking checks": (
        "tracking_vs_gwt", "tracking_duality", "water_balance", "tagged_balance",
        "steady_limit_g", "steady_limit_f", "substeps",
    ),
}
CHECK_ORDER = tuple(c for checks in CHECK_GROUPS.values() for c in checks)
assert sorted(CHECK_ORDER) == sorted(MEASURES), "every check belongs to exactly one group"
SUBSTEPS = 3  # transport sub-steps of the sub-step check (tests/test_tracking.py)


@dataclass
class Exes:
    """Paths of the executables the test models need (None if missing)."""

    mf6: Path | None
    triangle: Path | None


def find_exes(bin_dir: Path = REPO / "bin") -> Exes:
    """Return the mf6 and triangle executables in bin_dir, None for any that is missing."""
    suffix = ".exe" if sys.platform.startswith("win") else ""
    paths = [bin_dir / f"{name}{suffix}" for name in ("mf6", "triangle")]
    return Exes(*[p if p.is_file() else None for p in paths])


def add_tests_to_path(tests_dir: Path = TESTS_DIR) -> None:
    """Make the test-model builders and the test helpers importable."""
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))


class ModelCache:
    """Build and run each test model once, in its own folder under work."""

    def __init__(self, work: Path, exes: Exes):
        self.work = Path(work)
        self.exes = exes
        self.runs = {}
        self.splits = {}

    def get(self, key: str):
        """Return the ModelRun of a test model, building it on first use."""
        from models import build_model

        if key not in self.runs:
            ws = self.work / key
            ws.mkdir(parents=True, exist_ok=True)
            self.runs[key] = build_model(key, ws, self.exes.mf6, self.exes.triangle)
        return self.runs[key]

    def split(self, key: str):
        """Return (workspace, splitter) of a test model split with Mf6Splitter, run once."""
        from test_multimodel import split_and_run

        if key not in self.splits:
            ws = self.work / f"{key}_split"
            ws.mkdir(parents=True, exist_ok=True)
            self.splits[key] = (ws, split_and_run(self.get(key), key, ws, self.exes.mf6))
        return self.splits[key]


def record(model: str, check: str, error: float, n: int, seconds: float, tol=None,
           status: str = "ok", note: str = "") -> dict:
    """Return one row of the verification table; an "ok" row must be within its tolerance."""
    tol = TOLERANCES.get(check) if tol is None else tol
    assert not (status == "ok" and error > tol), f"{model} {check}: {error:.2e} > {tol:.0e}"
    return {"model": model, "check": check, "error": error, "tolerance": tol,
            "measure": MEASURES[check], "n_compared": n, "status": status, "seconds": seconds,
            "note": note}


def not_run(model: str, check: str, reason: str) -> dict:
    """Return a table row for a check that was not run."""
    return record(model, check, np.nan, 0, 0.0, status="not run", note=reason)


# ---------------------------------------------------------------- identities


def model_steps(run, key: str) -> list[gs.FlowStep]:
    """Return every saved step of a test model (package networks read with their nodes)."""
    if key in NETWORKS:
        reader = gs.open_simulation(run.ws, package_nodes=NETWORKS[key], boundnames=True)
    else:
        reader = gs.open_model(run.ws)
    return [reader.read(ks) for ks in reader.steps]


def scaled_error(check) -> float:
    """Return |error| / max(|rhs|, 1), the measure the tests bound by 1e-10."""
    return abs(check.error) / max(abs(check.rhs), 1.0)


def identity_errors(step: gs.FlowStep) -> dict[str, tuple[float, int]]:
    """Return (largest error, number of checks) of closure and duality on one step."""
    groups = gs.groups_by_package(step)
    back, fwd = gs.backward(step, groups), gs.forward(step, groups)
    bwd_close = [scaled_error(backward_closure(step, back, g)) for g in groups]
    fwd_close = [scaled_error(forward_closure(step, fwd, g)) for g in groups]
    dual = [scaled_error(duality(step, back, d, fwd, s)) for d in groups for s in groups]
    return {
        "backward_closure": (max(bwd_close), len(bwd_close)),
        "forward_closure": (max(fwd_close), len(fwd_close)),
        "duality": (max(dual), len(dual)),
    }


def boundary_control_error(step: gs.FlowStep) -> tuple[float, int]:
    """Return max |sum of F over all sink terms - 1| over cells with outflow, and their number."""
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    res = gs.backward(step, groups)
    total = np.sum([res.fraction_through[g] for g in groups], axis=0)
    drains = cell_budget(step, flow_edges(step)).outflow > 0.0
    return float(np.abs(total[drains] - 1.0).max()), int(drains.sum())


def identity_rows(key: str, cache: ModelCache) -> list[dict]:
    """Return the closure, duality and boundary-control rows of one model (all steps)."""
    start = time.perf_counter()
    steps = model_steps(cache.get(key), key)
    worst = {name: [0.0, 0] for name in ("backward_closure", "forward_closure", "duality",
                                         "boundary_control")}
    for step in steps:
        values = identity_errors(step)
        values["boundary_control"] = boundary_control_error(step)
        for name, (error, n) in values.items():
            worst[name][0] = max(worst[name][0], error)
            worst[name][1] += n
    seconds = time.perf_counter() - start
    note = f"{len(steps)} step(s)" + (", package network" if key in NETWORKS else "")
    return [record(key, name, err, n, seconds, note=note) for name, (err, n) in worst.items()]


# ---------------------------------------------------------------- grid and split agreement


def output_error(ref: np.ndarray, other: np.ndarray) -> float:
    """Return max |other - ref| / max |ref| over the finite entries (NaN pattern must match)."""
    ref, other = np.asarray(ref, float), np.asarray(other, float)
    assert np.array_equal(np.isfinite(ref), np.isfinite(other)), "NaN patterns differ"
    finite = np.isfinite(ref)
    scale = max(float(np.abs(ref[finite]).max(initial=0.0)), 1e-300)
    return float(np.abs(other[finite] - ref[finite]).max(initial=0.0)) / scale


def disu_rows(cache: ModelCache) -> list[dict]:
    """Return the DIS vs DISU rows: every output of model 4 against model 1."""
    from test_mf6_integration import all_outputs

    _, dis = all_outputs(cache.get("m1_dis").ws)
    rows = []
    for key in DISU_MODELS:
        start = time.perf_counter()
        _, disu = all_outputs(cache.get(key).ws)
        assert dis.keys() == disu.keys(), key
        error = max(output_error(dis[name], disu[name]) for name in dis)
        rows.append(record(key, "dis_vs_disu", error, len(dis), time.perf_counter() - start,
                           note="vs model 1 (DIS)"))
    return rows


def split_rows(cache: ModelCache) -> list[dict]:
    """Return the split vs single-model rows (Mf6Splitter, every output and travel time)."""
    from test_multimodel import achieved_agreement

    rows = []
    for key, steps in SPLIT_MODELS.items():
        start = time.perf_counter()
        run = cache.get(key)
        ws, splitter = cache.split(key)
        errors = []
        for ks in steps:
            single = gs.read_step(run.ws, kstpkper=ks)
            net = gs.read_network(ws, kstpkper=ks)
            errors.extend(achieved_agreement(single, net, splitter).values())
        n_models = len(gs.read_network(ws, kstpkper=steps[0]).model_names)
        rows.append(record(key, "split_vs_single", max(errors), len(errors),
                           time.perf_counter() - start,
                           note=f"{n_models} models, {len(steps)} step(s)"))
    return rows


# ---------------------------------------------------------------- transient tracking vs GWT


def gwt_error_model6(run, work: Path, exe: Path) -> tuple[float, int]:
    """Return the largest |c - C_gwt| over the GWT tagging cases of model 6, and their number."""
    from models.gwt import build_gwt_fmi
    from test_tracking_mf6 import GWT_CASES, gwt_concentrations

    from gwsource import tracking as tr

    worst = 0.0
    for case, (tagged, strt, correction) in GWT_CASES.items():
        ucn = build_gwt_fmi(run, work / f"gwt_{case}", exe, POROSITY, tagged, strt, correction)
        reader = gs.open_model(run.ws)
        sources = {"tagged": {"package": [p.upper() for p in tagged]}} if tagged else None
        config = tr.TrackingConfig(porosity=POROSITY, volume_mode="gwt",
                                   flow_error_correction=correction,
                                   initial_water={"initial": "all"} if strt else None)
        result = tr.track_forward(reader, sources, config)
        c = sum(result.source_fraction[g] for g in result.groups)
        active = reader.grid.idomain.ravel() > 0
        conc = gwt_concentrations(ucn, result.steps)
        worst = max(worst, float(np.abs(conc[:, active] - c[:, active]).max()))
    return worst, len(GWT_CASES)


def gwt_error_model7(run, work: Path, exe: Path) -> tuple[float, int]:
    """Return the largest |c - C| over cells and reaches of model 7 (SFT + MVT), two tags."""
    import flopy
    from models.gwt import build_gwt_fmi
    from test_tracking_mf6 import gwt_concentrations

    from gwsource import tracking as tr

    worst = 0.0
    for tag in ("rch", "stream_inflow"):
        ws = work / f"gwt_m7_{tag}"
        tagged, inflow = (("rch",), 0.0) if tag == "rch" else ((), 1.0)
        ucn = build_gwt_fmi(run, ws, exe, POROSITY, tagged, sft_inflow=inflow)
        reader = gs.open_simulation(run.ws, package_nodes=("SFR",))
        source = ({"package": "RCH"} if tag == "rch"
                  else {"package": "SFR", "term": "EXT-INFLOW"})
        config = tr.TrackingConfig(porosity=POROSITY, volume_mode="gwt")
        result = tr.track_forward(reader, {"t": source}, config)
        step = reader.read(reader.steps[-1])
        cells, reaches = step.blocks[0], step.block("SFR")
        active = step.active[cells.nodes]
        conc = gwt_concentrations(ucn, result.steps)
        sft = flopy.utils.HeadFile(str(ws / "gwt.sft.ucn"), text="CONCENTRATION")
        for n, ks in enumerate(result.steps):
            c = result.source_fraction["t"][n]
            reach_conc = np.asarray(sft.get_data(kstpkper=ks), float).ravel()
            worst = max(worst, float(np.abs(conc[n][active] - c[cells.nodes][active]).max()),
                        float(np.abs(reach_conc - c[reaches.nodes]).max()))
    return worst, 2


def gwt_rows(cache: ModelCache) -> list[dict]:
    """Return the transient tracking vs MF6 GWT rows (model 6; model 7 with SFT and MVT)."""
    rows = []
    for key, func, note in (("m6_transient", gwt_error_model6, "5 tagging cases"),
                            ("m7_mover", gwt_error_model7, "SFR nodes + MVR vs SFT + MVT")):
        start = time.perf_counter()
        error, n = func(cache.get(key), cache.work, cache.exes.mf6)
        rows.append(record(key, "tracking_vs_gwt", error, n, time.perf_counter() - start,
                           note=note))
    return rows


# ---------------------------------------------------------------- transient tracking checks


def tracking_readers(cache: ModelCache) -> dict:
    """Return (reader, sources, destinations, sub-step counts) per model of the duality check."""
    import test_tracking_mf6 as ttm

    m6 = (ttm.MODEL6_SOURCES, ttm.MODEL6_DESTINATIONS)
    net = (ttm.NETWORK_SOURCES, ttm.NETWORK_DESTINATIONS)
    mover = (ttm.MOVER_SOURCES, ttm.MOVER_DESTINATIONS)
    return {
        "m6_transient": (gs.open_model(cache.get("m6_transient").ws), *m6, (1, 5)),
        "m6_split": (gs.open_simulation(cache.split("m6_transient")[0]), *m6, (1,)),
        "m7_mover": (gs.open_simulation(cache.get("m7_mover").ws, package_nodes=("SFR",),
                                        boundnames=True), *mover, (1,)),
        "m9_lak_uzf": (gs.open_simulation(cache.get("m9_lak_uzf").ws,
                                          package_nodes=("LAK", "UZF")), *net, (1,)),
    }


def tracking_duality_rows(cache: ModelCache) -> list[dict]:
    """Return the transient forward-backward rows (both volume options, all source pairs)."""
    from test_tracking_mf6 import check_duality

    rows = []
    for key, (reader, sources, destinations, substeps) in tracking_readers(cache).items():
        start = time.perf_counter()
        results = [check_duality(reader, sources, destinations, m) for m in substeps]
        error = max(r["duality"] for r in results)
        n = sum(r["n_duality"] for r in results)
        note = f"{len(reader.steps)} steps, both volume options"
        if len(substeps) > 1:
            note += ", 1 and 5 transport sub-steps"
        rows.append(record(key, "tracking_duality", error, n, time.perf_counter() - start,
                           note=note))
    return rows


def balance_rows(cache: ModelCache) -> list[dict]:
    """Return the water and tagged-water balance rows of "flow" volumes (models 6 and 9)."""
    import test_tracking_mf6 as ttm

    from gwsource import tracking as tr

    cases = {
        "m6_transient": (gs.open_model(cache.get("m6_transient").ws),
                         ttm.MODEL6_SOURCES, ttm.MODEL6_DESTINATIONS),
        "m9_lak_uzf": (gs.open_simulation(cache.get("m9_lak_uzf").ws,
                                          package_nodes=("LAK", "UZF")),
                       ttm.NETWORK_SOURCES, ttm.NETWORK_DESTINATIONS),
    }
    rows = []
    for key, (reader, sources, destinations) in cases.items():
        start = time.perf_counter()
        fwd = ttm.check_flow_mode(reader, sources, destinations)["flow"][0]
        water = float(ttm.cell_water_balance_errors(reader, fwd.config).max())
        seconds = time.perf_counter() - start
        tagged = max(tr.forward_balance_error(fwd, g) for g in fwd.groups)
        note = f"{len(fwd.steps)} steps"
        rows.append(record(key, "water_balance", water, len(fwd.steps), seconds, note=note))
        rows.append(record(key, "tagged_balance", tagged, len(fwd.groups), seconds,
                           note=note + f", {len(fwd.groups)} tagged groups incl. initial water"))
    return rows


def steady_limit_rows(cache: ModelCache) -> list[dict]:
    """Return model 10's steady-limit rows: c at the end against G, w at the start against F."""
    from test_tracking_mf6 import steady_limit_errors

    start = time.perf_counter()
    reader = gs.open_model(cache.get("m10_constant").ws)
    errors = steady_limit_errors(reader)
    seconds = time.perf_counter() - start
    n, groups = len(reader.steps), errors["n_groups"]
    return [
        record("m10_constant", "steady_limit_g", errors["g_end"], groups, seconds,
               note=f"{n} steps; c vs G at the end (at the start: at least "
                    f"{errors['g_start']:.2f})"),
        record("m10_constant", "steady_limit_f", errors["f_start"], groups, seconds,
               note=f"{n} steps; w vs F at the start (at the end: at least "
                    f"{errors['f_end']:.2f})"),
    ]


def substep_rows(m: int = SUBSTEPS) -> list[dict]:
    """Return the sub-step row: m sub-steps against m times more flow steps of the same flows."""
    from test_tracking import substep_refinement_pairs

    start = time.perf_counter()
    pairs = substep_refinement_pairs(m)
    error = max(output_error(fine, coarse) for _, coarse, fine, _ in pairs)
    return [record("substep_network", "substeps", error, len(pairs),
                   time.perf_counter() - start,
                   note=f"{m} sub-steps vs {m}x flow steps, {len(pairs)} outputs")]


# ---------------------------------------------------------------- steady G vs GWT at equilibrium


def gwt_equilibrium_cell_rows(cache: ModelCache) -> list[dict]:
    """Return max |C - G| at equilibrium per model over the cell cases (models 1 and 2)."""
    import test_gwt_equilibrium as teq

    by_model = {}
    for case, (key, pname, selection) in teq.CELL_CASES.items():
        start = time.perf_counter()
        run = cache.get(key)
        step = gs.read_step(run.ws)
        fraction = teq.steady_fraction(step, selection)
        conc, previous = teq.run_to_equilibrium(run, cache.work / f"gwt_eq_{case}",
                                                cache.exes.mf6, (pname,), teq.EQUILIBRIUM_DAYS)
        change = float(np.abs(conc - previous)[step.active].max())
        assert change < teq.EQUILIBRIUM_TOL, f"{case}: not at equilibrium ({change:.1e})"
        error = float(np.abs(conc - fraction)[step.active].max())
        worst, cases, seconds = by_model.get(key, (0.0, [], 0.0))
        by_model[key] = (max(worst, error), [*cases, f"{case} {error:.1e}"],
                         seconds + time.perf_counter() - start)
    return [record(key, "steady_g_vs_gwt", worst, len(cases), seconds, tol=teq.GWT_ATOL,
                   note="; ".join(cases))
            for key, (worst, cases, seconds) in by_model.items()]


def gwt_equilibrium_network_row(cache: ModelCache) -> dict:
    """Return max |C - G| at equilibrium on model 7 (cells and reaches), default and tight flow."""
    import test_gwt_equilibrium as teq
    from models.mover import build_mover_dis

    start = time.perf_counter()
    ws = cache.work / "m7_tight"
    ws.mkdir(parents=True, exist_ok=True)
    tight_run = build_mover_dis(ws, cache.exes.mf6, ims_kwargs=teq.TIGHT_FLOW_IMS)
    default, tight = 0.0, 0.0
    for case in teq.NETWORK_CASES:
        default = max(default, *teq.network_errors(cache.get("m7_mover"),
                                                   cache.work / f"gwt_eq_m7_{case}",
                                                   cache.exes.mf6, case))
        tight = max(tight, *teq.network_errors(tight_run, cache.work / f"gwt_eq_m7t_{case}",
                                               cache.exes.mf6, case))
    assert tight < teq.GWT_ATOL, tight
    return record("m7_mover", "steady_g_vs_gwt", default, 2 * len(teq.NETWORK_CASES),
                  time.perf_counter() - start, tol=teq.NETWORK_ATOL,
                  note=f"cells and reaches; flow model solved about 100 times tighter: "
                       f"{tight:.1e}")


def gwt_equilibrium_rows(cache: ModelCache) -> list[dict]:
    """Return the steady G vs GWT at equilibrium rows (models 1, 2 and 7)."""
    return [*gwt_equilibrium_cell_rows(cache), gwt_equilibrium_network_row(cache)]


# ---------------------------------------------------------------- particles and worked example


def prt_rows(cache: ModelCache) -> list[dict]:
    """Return captured PRT particle flow against the well inflow (models 1, 3 and 2)."""
    from gwsource.prt import PrtConfig, track_particles

    rows = []
    for key, (kwargs, tol) in PRT_MODELS.items():
        start = time.perf_counter()
        run = cache.get(key)
        step = gs.read_step(run.ws)
        res = gs.backward(step, {"wel": gs.select(step, package="WEL")})
        config = PrtConfig(porosity=POROSITY, **kwargs)
        prt = track_particles(run.ws, step, res, "wel", config, cache.exes.mf6,
                              cache.work / f"{key}_prt")
        inflow = res.destination_inflow["wel"]
        rows.append(record(key, "prt_capture", abs(prt.captured_flow / inflow - 1.0),
                           len(prt.release.package), time.perf_counter() - start, tol=tol,
                           note=f"{prt.captured_flow:.1f} of {inflow:.1f} m3/d"))
    return rows


def reference_example_row() -> dict:
    """Return the largest difference from the published numbers of the [FB13] worked example."""
    import test_fb13_example as fb

    start = time.perf_counter()
    step = fb.fb13_step()
    res = gs.backward(step, {"A": gs.select_cells(step, [0])}, gs.TraceConfig(accounting="net"))
    errors = []
    for got, expected in ((res.fraction_through["A"], fb.EXPECTED_F),
                          (res.volume_through["A"], fb.EXPECTED_V_THROUGH),
                          (res.volume_from["A"], fb.EXPECTED_V_FROM)):
        errors += [abs(float(got[fb.LABELS.index(k)]) - v) for k, v in expected.items()]
    return record("fb13_example", "reference_example", max(errors), len(errors),
                  time.perf_counter() - start, note="net accounting, 9 cells x 3 outputs")


# ---------------------------------------------------------------- collection and tables


def collect(work: Path, exes: Exes, run_identities: bool = True, run_disu: bool = True,
            run_split: bool = True, run_gwt: bool = True, run_prt: bool = True,
            run_tracking: bool = True, run_gwt_equilibrium: bool = True) -> pd.DataFrame:
    """Run every selected check and return the long table (one row per model and check)."""
    add_tests_to_path()
    rows = [reference_example_row()]
    if exes.mf6 is None or exes.triangle is None:
        reason = "mf6 or triangle missing from bin/"
        rows += [not_run(k, c, reason) for k in IDENTITY_MODELS
                 for c in ("backward_closure", "forward_closure", "duality", "boundary_control")]
        return pd.DataFrame(rows)
    cache = ModelCache(work, exes)
    gates = (
        (run_identities, lambda: [r for k in IDENTITY_MODELS for r in identity_rows(k, cache)],
         [(k, c) for k in IDENTITY_MODELS for c in ("backward_closure", "forward_closure",
                                                     "duality", "boundary_control")]),
        (run_disu, lambda: disu_rows(cache), [(k, "dis_vs_disu") for k in DISU_MODELS]),
        (run_split, lambda: split_rows(cache), [(k, "split_vs_single") for k in SPLIT_MODELS]),
        (run_gwt, lambda: gwt_rows(cache),
         [("m6_transient", "tracking_vs_gwt"), ("m7_mover", "tracking_vs_gwt")]),
        (run_prt, lambda: prt_rows(cache), [(k, "prt_capture") for k in PRT_MODELS]),
        (run_tracking,
         lambda: (tracking_duality_rows(cache) + balance_rows(cache) + steady_limit_rows(cache)
                  + substep_rows()),
         [(k, "tracking_duality") for k in ("m6_transient", "m6_split", "m7_mover",
                                            "m9_lak_uzf")]
         + [(k, c) for k in ("m6_transient", "m9_lak_uzf")
            for c in ("water_balance", "tagged_balance")]
         + [("m10_constant", "steady_limit_g"), ("m10_constant", "steady_limit_f"),
            ("substep_network", "substeps")]),
        (run_gwt_equilibrium, lambda: gwt_equilibrium_rows(cache),
         [(k, "steady_g_vs_gwt") for k in ("m1_dis", "m2_dis3lay", "m7_mover")]),
    )
    for enabled, func, keys in gates:
        rows += func() if enabled else [not_run(k, c, "switched off") for k, c in keys]
    return pd.DataFrame(rows)


MODEL_LABELS = {
    "fb13_example": "[FB13] worked example, net accounting",
    "m1_dis": "1 DIS",
    "m2_dis3lay": "2 DIS, 3 layers, weak sink",
    "m3_disv": "3 DISV Voronoi",
    "m4_disu_vert": "4 DISU (vertices)",
    "m4_disu_novert": "4 DISU (no vertices)",
    "m5_xt3d": "5 XT3D, cycles",
    "m6_transient": "6 transient (STO)",
    "m6_split": "6 transient, split into 4 models",
    "m7_mover": "7 SFR + MVR network",
    "m8_maw": "8 MAW network",
    "m9_lak_uzf": "9 LAK + UZF + MVR network",
    "m10_constant": "10 model 1 flows, held 4 × 10⁵ d",
    "substep_network": "hand-built 15-cell network (not MF6)",
}
CHECK_LABELS = {
    "backward_closure": "backward closure",
    "forward_closure": "forward closure",
    "duality": "forward–backward",
    "boundary_control": "boundary control",
    "dis_vs_disu": "DISU vs DIS",
    "split_vs_single": "split vs single",
    "tracking_vs_gwt": "tracking vs GWT",
    "prt_capture": "PRT flow to the well",
    "reference_example": "[FB13] example",
    "tracking_duality": "transient forward–backward",
    "water_balance": "water balance (\"flow\")",
    "tagged_balance": "tagged-water balance (\"flow\")",
    "steady_limit_g": "steady limit, c to G",
    "steady_limit_f": "steady limit, w to F",
    "substeps": "sub-steps vs refined steps",
    "steady_g_vs_gwt": "steady G vs GWT at equilibrium",
}


def format_error(error: float, status: str) -> str:
    """Return an error for the markdown table: '0', '3.1e-16', 'not run' or blank."""
    if status != "ok":
        return status
    if np.isnan(error):
        return ""
    return "0" if error == 0.0 else f"{error:.1e}"


def pivot_markdown(table: pd.DataFrame, check_order: tuple = CHECK_ORDER) -> str:
    """Return the table as markdown: models as rows, checks as columns, plus tolerances."""
    checks = [c for c in check_order if c in set(table.check)]
    models = [m for m in MODEL_LABELS if m in set(table[table.check.isin(checks)].model)]
    lines = ["| model | " + " | ".join(CHECK_LABELS[c] for c in checks) + " |",
             "|---|" + "---|" * len(checks)]
    for model in models:
        cells = []
        for check in checks:
            row = table[(table.model == model) & (table.check == check)]
            cells.append("–" if row.empty else format_error(row.error.iloc[0],
                                                            row.status.iloc[0]))
        lines.append(f"| {MODEL_LABELS[model]} | " + " | ".join(cells) + " |")
    tols = []
    for check in checks:
        values = sorted(set(table[table.check == check].tolerance.dropna()))
        tols.append(" / ".join(f"{v:.0e}" for v in values) or "–")
    lines.append("| *test tolerance* | " + " | ".join(tols) + " |")
    measures = " ".join(f"**{CHECK_LABELS[c]}**: {MEASURES[c]}." for c in checks)
    return "\n".join(lines) + "\n\nError measures. " + measures + "\n"


def summary_by_check(table: pd.DataFrame) -> pd.DataFrame:
    """Return the largest error per check, with the model where it occurs."""
    ok = table[table.status == "ok"]
    rows = []
    for check in [c for c in CHECK_ORDER if c in set(ok.check)]:
        sel = ok[ok.check == check]
        worst = sel.loc[sel.error.idxmax()]
        rows.append({"check": check, "largest_error": worst.error, "model": worst.model,
                     "tolerance": worst.tolerance, "n_models": len(sel)})
    return pd.DataFrame(rows)


def write_tables(table: pd.DataFrame, out_dir: Path) -> tuple[Path, Path]:
    """Write verification_table.csv and verification_table.md; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = out_dir / "verification_table.csv"
    table.to_csv(csv, index=False, float_format="%.3e")
    worst = summary_by_check(table)
    lines = [f"| {CHECK_LABELS[r.check]} | {format_error(r.largest_error, 'ok')} | "
             f"{MODEL_LABELS[r.model]} | "
             f"{r.tolerance:.0e} |" for r in worst.itertuples()]
    parts = "".join(
        f"\n## {name.capitalize()}\n\n" + pivot_markdown(table, checks)
        for name, checks in CHECK_GROUPS.items()
    )
    text = (
        "# Table 2. Verification checks on the synthetic test models\n\n"
        "Generated by `studies/paper/method_figures.py` (`studies/paper/verification.py`); "
        "errors are the largest over groups, group pairs and time steps of each model. "
        "'–': check not applicable to the model.\n"
        + parts
        + "\n## Largest error per check\n\n| check | largest error | model | tolerance |\n"
        "|---|---|---|---|\n" + "\n".join(lines) + "\n"
    )
    md = out_dir / "verification_table.md"
    md.write_text(text)
    return csv, md
