"""Neversink case study, stage 3 follow-up: where the stream water reaching the wells changes
with pumping, and why the published contributing area grows more slowly than full mixing.

Sample. SAMPLE_N realisations at rows of modpath_par_ens.csv evenly spread over the 357 runs
with a published mask (ensemble_run.scenario_subset) plus the base (calibrated) realisation, each
at base, half and maximum pumping (QRATS). Stage 3 kept only package totals per run; here every
run is rebuilt as ensemble_run.run_realisation does (same parameters and scenario rule, the
realisation's own priority-well multiplier kept), with the RCH and SFR
flows given an IFLOWFACE auxiliary (top face where it is open, as in mp7_convention). The aux
column does not change the flow solution, so one MF6 run serves both full mixing and PRT.

Question 1, where. Per SFR reach: the aquifer exchange q from the GWF budget (positive into the
aquifer, i.e. a losing reach) and, under full mixing with streams as cells, the part of its
leakage that reaches each well cluster, F_cluster(cell) x max(q, 0) (the reach's share of the SFR
term of volume_from). analyse() tabulates it by cluster and plan distance from the cluster's
nearest well, by reach state (losing or gaining at both rates, or switching), by stream segment
(SFR line_id), and splits the change of each reach into more leakage (F_base x dq), a larger
share of the same leakage (dF x q_base) and their product (dF x dq).

Question 2, why. The same flow fields are tracked with MF6 PRT from the published start positions
(one particle per cell of the uppermost active layer, dry starts draped; mp7_convention), seeded
only where F > 0 at the (draped) start, since no other start has a flow path to the wells. Three
PRT runs per flow field:
- R1, the published conventions: RCH and SFR flows on the top face where it is open,
  STOP_AT_WEAK_SINK, termination records only (mp7_convention.reproduce).
- R2, as R1 without STOP_AT_WEAK_SINK, with tracks.
- R3, as R2 with every boundary flow distributed over the cell (MF6's default; IFLOWFACE set to
  0 in a copy of the budget file), with tracks.
Stopping rules are applied to the tracks afterwards (first_stop_capture): a particle counts if
the first cell of the stop set that it visits is a priority-well cell. The stop sets are the
well cells only, plus the stream weak sinks, plus every weak sink (which should repeat R1). A
weak sink is a cell with a sink that PRT spreads over the cell (IFLOWFACE 0); a stream flow put
on an open top face instead ends the particle there (it leaves the model). Thinned particles
carry the gross accounting of gwsource.prt instead (capture_along_paths): in R3 every sink
thins, in R2 only the distributed ones; a stop is a survival of 0. The area of a variant is the
sum over the start cells of the count or captured weight; its growth is the scenario's area over
the baserat area. VARIANTS orders them from full mixing to the published convention, one change
at a time. stream_stops() locates the stream cells where the stop removes weight. The R1 masks
are compared with the published masks of the same scenario (moved back onto their cells,
ensemble_run.read_mask): in distribution, by best match and with the realisation's own mask
(mask_matches, mask_similarity).

Run from anywhere with the project environment, outside the Claude Code sandbox (process pool):

    python studies/neversink/growth_mechanisms.py

About 80 s per case on one process (MF6 15 s, both traces 3 s, the three PRT runs 60 s); the
33 cases of the default sample take 10 min on six processes. main(sample_n=60,
out=OUT_DIR.with_name("mechanisms60")) repeats it on 61 realisations (183 cases) as a check of
the growth decomposition. Resumable: a case with a summary file is skipped. Output goes to
OUT_DIR (git-ignored): summary/, reaches/, starts/ per case (<qrat>_<real>) and the tables of
analyse().
"""

import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import flopy
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ensemble_run as er  # noqa: E402
import figures  # noqa: E402
import mp7_convention as mp7  # noqa: E402
import pest_rebuild as pr  # noqa: E402
import scenarios as sc  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

OUT_DIR = wf.OUT / "scenarios" / "mechanisms"
SAMPLE_N = 10
QRATS = ("baserat", "0.5rat", "maxrat")
BASE_REAL = "base"
N_WORKERS = 6
THREADS_PER_WORKER = 2
GROUP = er.GROUP
CLUSTERS = {
    "U": ("U_917", "U__55", "U___7", "U___8"),
    "SV_W": ("SV_193", "SV_227", "SV_407"),
    "SV_S": ("SV_487",),
}
DISTANCE_BINS = (0.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, np.inf)
SFR_TEXT = "SFR"
FACE_TEXTS = ("RCHA", "SFR")  # the budget records that carry IFLOWFACE
# Starts in cells wet only by a film are left out (MF6 6.9.0.dev0 PRT aborts at their release;
# mp7_convention.MIN_SAT). In realisation 443 at maxrat films of 1.3e-15 to 1.3e-13 occur.
FILM_SAT = 1e-10
# Area variants, from full mixing to the published convention: (column, description)
VARIANTS = (
    ("f_start", "full mixing, F of the start cell"),
    ("f_draped", "full mixing, F of the draped start cell"),
    ("r3_thinned", "PRT, flows distributed, thinned at every sink"),
    ("r2_thinned", "PRT, top face where open, thinned at distributed sinks"),
    ("r2_streams_thinned", "PRT, top face where open, stop at stream weak sinks, else thinned"),
    ("r2_wells", "PRT, top face where open, stop in the well cells only"),
    ("r2_streams", "PRT, top face where open, stop also at stream weak sinks"),
    ("r2_all", "PRT, top face where open, stop at every weak sink"),
    ("r1", "PRT, published conventions (STOP_AT_WEAK_SINK)"),
    ("r3_wells", "PRT, flows distributed, stop in the well cells only"),
    ("r3_all", "PRT, flows distributed, stop at every weak sink"),
)

_WORKER = {}  # per-process state set by the pool initializer


# ---------------------------------------------------------------- cases


def sample_realisations(n: int = SAMPLE_N) -> list[str]:
    """Return the sample: n realisations evenly spread over the runs with a mask, and the base."""
    return [*er.scenario_subset(n), BASE_REAL]


def case_name(real: str, qrat: str) -> str:
    """Return the file stem of a case."""
    return f"{qrat}_{real}"


def case_pars(real: str, qrat: str) -> pd.Series | None:
    """Return the parameters of a realisation under a scenario (None: the ensemble row)."""
    if qrat == "baserat":
        return None
    return sc.scenario_pars(pr.realisation_pars(real), qrat, er.run_indices()[real])


def write_case(real: str, qrat: str, ws: Path, iface) -> dict:
    """Write a realisation under a scenario with SPDIS, saturation and IFLOWFACE for PRT."""
    pr.write_realisation(real, ws, pars=case_pars(real, qrat), iface=iface)
    return mp7.add_iflowface(ws)


# ---------------------------------------------------------------- full mixing


def term_text(step: gs.FlowStep) -> np.ndarray:
    """Return the budget text of every term entry."""
    return np.array([p.text for p in step.packages], dtype=object)[step.term_package]


def cluster_fractions(result: gs.BackwardResult, n_cells: int) -> dict[str, np.ndarray]:
    """Return F per cell of every well cluster and of the priority group (sums of well F)."""
    f = result.fraction_through
    out = {name: sum(f[w][:n_cells] for w in wells) for name, wells in CLUSTERS.items()}
    out[GROUP] = result.fraction_through[GROUP][:n_cells]
    return out


def reach_flows(step: gs.FlowStep, result: gs.BackwardResult) -> dict[str, np.ndarray]:
    """Return per SFR reach (1-based order) its cell, exchange q (+ into the aquifer) and F."""
    sfr = term_text(step) == SFR_TEXT
    reach = step.term_bound[sfr]
    order = np.argsort(reach)
    assert np.array_equal(reach[order], np.arange(1, sfr.sum() + 1)), "one term per SFR reach"
    cell = step.term_cell[sfr][order]
    out = {"cell": cell, "q": step.term_flow[sfr][order]}
    for name, f in cluster_fractions(result, step.n_cells).items():
        out[f"f_{name}"] = f[cell].astype(np.float32)
    return out


def coverage(
    result: gs.BackwardResult, start_nodes: dict[str, np.ndarray], top: np.ndarray
) -> dict:
    """Return the share of the wells' inflow that enters in the start cells and the top layer."""
    vf = result.volume_from[GROUP]
    total = vf.sum()
    row = {f"coverage_{k}": float(vf[np.unique(v)].sum() / total) for k, v in start_nodes.items()}
    row["coverage_top_layer"] = float(vf[top[top >= 0]].sum() / total)
    return row


# ---------------------------------------------------------------- PRT


def sink_cells(step: gs.FlowStep, terms: np.ndarray) -> np.ndarray:
    """Return, per cell, whether one of the selected term entries removes water there."""
    out = np.where(terms, np.maximum(-step.term_flow, 0.0), 0.0)
    return np.bincount(step.term_cell, weights=out, minlength=step.n_cells) > 0


def stop_sets(step: gs.FlowStep) -> dict[str, np.ndarray]:
    """Return the cells with stream weak sinks and with any weak sink of the two face conventions.

    face_*: with RCH and SFR on the top face where it is open (IFLOWFACE -1), only the sinks
    left distributed (IFLOWFACE 0) make a weak sink. dist_all: every sink is distributed.
    """
    assert step.term_iflowface is not None, "the budget has no IFLOWFACE column"
    is_sfr = term_text(step) == SFR_TEXT
    distributed = step.term_iflowface == 0
    every = np.ones(step.n_terms, dtype=bool)
    return {
        "face_streams": sink_cells(step, is_sfr & distributed),
        "face_all": sink_cells(step, distributed),
        "dist_all": sink_cells(step, every),
    }


def distributed_survival(step: gs.FlowStep) -> np.ndarray:
    """Return 1 - Snk0 / O per cell, Snk0 the sinks that PRT spreads over the cell (IFLOWFACE 0)."""
    budget = gs.cell_budget(step, gs.flow_edges(step))
    out = np.where(step.term_iflowface == 0, np.maximum(-step.term_flow, 0.0), 0.0)
    sink0 = np.bincount(step.term_cell, weights=out, minlength=step.n_cells)
    removed = np.divide(sink0, budget.outflow, out=np.zeros(step.n_cells), where=budget.outflow > 0)
    return 1.0 - removed


def first_stop_capture(
    visits: dict[str, np.ndarray], n: int, stop: np.ndarray, dest: np.ndarray
) -> np.ndarray:
    """Return, per particle, whether the first stop or destination cell it visits is a well cell."""
    p, c = visits["particle"], visits["cell"]
    idx = np.flatnonzero(stop[c] | dest[c])
    particles, first = np.unique(p[idx], return_index=True)  # visits are in time order
    captured = np.zeros(n, dtype=bool)
    captured[particles] = dest[c[idx[first]]]
    return captured


def run_visits(sim) -> dict[str, np.ndarray]:
    """Run a PRT simulation with tracks and return its cell visits (the track file is deleted)."""
    track_csv = gs.prt.run_prt(sim)
    visits = gs.prt.cell_visits(gs.prt.read_tracks(track_csv))
    track_csv.unlink()
    return visits


def seeded_starts(
    ws: Path, budget: Path, starts: pd.DataFrame, f: np.ndarray, min_sat: float = FILM_SAT
) -> tuple[pd.DataFrame, np.ndarray, int]:
    """Return the draped starts, which of them to track (F > 0 at either cell, not in a film)
    and the number left out for a film."""
    idomain = wf.grid_idomain(ws)
    sat = mp7.cell_saturation(budget, idomain.size)
    draped = mp7.drape_dry_starts(starts, idomain, sat)
    reach = (f[starts["node0"].to_numpy()] > 0) | (f[draped["node0"].to_numpy()] > 0)
    trackable = mp7.trackable(draped, sat, min_sat)
    return draped, trackable & reach, int(np.sum(reach & ~trackable))


def prt_variants(
    ws: Path, step: gs.FlowStep, result: gs.BackwardResult, starts: pd.DataFrame, exe: Path
) -> tuple[dict[str, np.ndarray], dict]:
    """Run R1 to R3 on one flow field; return per start the capture of every variant and a row."""
    budget = ws / f"{wf.MODEL}.cbc"
    f = result.fraction_through[GROUP]
    draped, seed, films = seeded_starts(ws, budget, starts, f)
    tracked = draped[seed].reset_index(drop=True)
    n = len(tracked)
    dest = result.selections[GROUP].cells
    share = gs.prt.destination_share(step, result.selections[GROUP])
    stops = stop_sets(step)
    timing = {}
    t0 = time.perf_counter()
    sim = mp7.write_mp7_prt(ws / "prt_r1", ws, budget, tracked, exe)
    r1 = mp7.run_endpoints(sim, np.ones(n, dtype=bool))
    timing["r1_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    options = {"stop_at_weak_sink": False, "tracks": True}
    sim = mp7.write_mp7_prt(ws / "prt_r2", ws, budget, tracked, exe, **options)
    v2 = run_visits(sim)
    timing["r2_seconds"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    budget3 = ws / "distributed.cbc"
    mp7.write_distributed_budget(budget, budget3, FACE_TEXTS)
    sim = mp7.write_mp7_prt(ws / "prt_r3", ws, budget3, tracked, exe, **options)
    v3 = run_visits(sim)
    budget3.unlink()
    timing["r3_seconds"] = time.perf_counter() - t0
    none = np.zeros(step.n_cells, dtype=bool)
    survival2 = distributed_survival(step)
    seeded = {
        "r1": np.isin(r1["cell"], np.flatnonzero(dest)),
        "r2_thinned": gs.prt.capture_along_paths(v2, n, share, survival2)[0],
        "r2_streams_thinned": gs.prt.capture_along_paths(
            v2, n, share, np.where(stops["face_streams"], 0.0, survival2)
        )[0],
        "r2_wells": first_stop_capture(v2, n, none, dest),
        "r2_streams": first_stop_capture(v2, n, stops["face_streams"], dest),
        "r2_all": first_stop_capture(v2, n, stops["face_all"], dest),
        "r3_thinned": gs.prt.capture_along_paths(v3, n, share, gs.prt.weak_sink_survival(step))[0],
        "r3_wells": first_stop_capture(v3, n, none, dest),
        "r3_all": first_stop_capture(v3, n, stops["dist_all"], dest),
    }
    per_start = {
        "f_start": f[starts["node0"].to_numpy()].astype(np.float32),
        "f_draped": f[draped["node0"].to_numpy()].astype(np.float32),
        "seeded": seed,
        "draped_node": draped["node0"].to_numpy(),
        "r1_status": np.where(seed, 0, -1),
        "r1_end": np.full(len(starts), -1, dtype=np.int64),
    }
    for key, values in seeded.items():
        full = np.zeros(len(starts), dtype=np.float32 if values.dtype.kind == "f" else bool)
        full[seed] = values
        per_start[key] = full
    per_start["r1_status"][seed] = r1["status"]
    per_start["r1_end"][seed] = r1["cell"]
    row = {
        **timing,
        "particles": n,
        "film_starts": films,
        "dry_starts": int(np.sum(draped["node0"].to_numpy() != starts["node0"].to_numpy())),
        "r1_equals_r2_all": float(np.mean(seeded["r1"] == seeded["r2_all"])),
        "r1_not_tracked": int(np.sum(r1["cell"] < 0)),
    }
    return per_start, row


# ---------------------------------------------------------------- one case and the pool


def init_worker(pest_dir: Path) -> None:
    """Load the interface, executable, grid and published starts once per worker process."""
    idomain = wf.grid_idomain(wf.OUT / "optimal")
    _WORKER["iface"] = pr.load_interface(pest_dir)
    _WORKER["exe"] = wf.mf6_exe()
    _WORKER["top"] = figures.top_active(idomain)
    _WORKER["starts"] = wf.read_endpoints(columns=mp7.START_COLUMNS)


def run_case(real: str, qrat: str, out: Path) -> dict:
    """Write, run, trace and track one case; save its tables; delete the workspace."""
    iface, exe, top, starts = (_WORKER[k] for k in ("iface", "exe", "top", "starts"))
    name = case_name(real, qrat)
    ws = out / "ws" / name
    t0 = time.perf_counter()
    faces = write_case(real, qrat, ws, iface)
    row = {"real": real, "qrat": qrat, "write_seconds": time.perf_counter() - t0, **faces}
    row["mf6_seconds"] = wf.run_mf6(ws, exe)
    t0 = time.perf_counter()
    traces = er.trace_pair(ws)
    step, result = traces["cells"]
    row.update(trace_seconds=time.perf_counter() - t0, **er.trace_row(traces))
    maps = er.trace_maps(traces, top)
    per_start, prt_row = prt_variants(ws, step, result, starts, exe)
    row.update(prt_row)
    nodes = {"start": starts["node0"].to_numpy(), "draped": per_start["draped_node"]}
    row.update(coverage(result, nodes, top))
    row.update({f"area:{k}": float(per_start[k].sum()) for k, _ in VARIANTS})
    network = maps["network"].ravel()[er.start_cells(*top.shape)]
    row["area:network"] = float(np.nan_to_num(network).sum())
    np.savez_compressed(out / "reaches" / f"{name}.npz", **reach_flows(step, result))
    np.savez_compressed(out / "starts" / f"{name}.npz", **per_start)
    (out / "summary" / f"{name}.json").write_text(json.dumps(row))
    shutil.rmtree(ws)
    return row


def pending_cases(out: Path, reals: list[str], qrats: tuple[str, ...]) -> list[tuple[str, str]]:
    """Return the (real, qrat) cases without a summary file."""
    cases = [(r, q) for q in qrats for r in reals]
    return [c for c in cases if not (out / "summary" / f"{case_name(*c)}.json").is_file()]


def run_cases(
    out: Path, reals: list[str], qrats: tuple[str, ...], n_workers: int = N_WORKERS,
    threads: int = THREADS_PER_WORKER,
) -> None:
    """Run the pending cases in a process pool; failures are logged and stay pending."""
    for sub in ("ws", "summary", "reaches", "starts"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    cases = pending_cases(out, reals, qrats)
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = str(threads)  # inherited by the workers before they import numpy
    t0 = time.perf_counter()
    with ProcessPoolExecutor(n_workers, initializer=init_worker, initargs=(pr.PEST_DIR,)) as pool:
        jobs = {pool.submit(run_case, r, q, out): (r, q) for r, q in cases}
        for k, job in enumerate(as_completed(jobs), start=1):
            try:
                job.result()
            except Exception as err:  # keep the pool running; the case stays pending
                with (out / "failures.log").open("a") as f:
                    f.write(f"{case_name(*jobs[job])}: {type(err).__name__}: {err}\n")
            minutes = (time.perf_counter() - t0) / 60
            print(f"{k}/{len(cases)} done ({case_name(*jobs[job])}), {minutes:.1f} min", flush=True)


# ---------------------------------------------------------------- analysis: sample check


def collect(out: Path) -> pd.DataFrame:
    """Return the summary rows of every finished case."""
    rows = [json.loads(p.read_text()) for p in sorted((out / "summary").glob("*.json"))]
    table = pd.DataFrame(rows)
    table["stream_share"] = table["cells:SFR_0"] / table["inflow"]
    return table


def stage3_summary(
    qrat: str, ens_dir: Path = er.ENS_DIR, scenario_dir: Path = er.SCENARIO_DIR
) -> pd.DataFrame:
    """Return the stage-2/3 summary rows of a scenario (all realisations run there)."""
    summary = er.collect_summary(er.scenario_dir_of(qrat, ens_dir, scenario_dir))
    summary["stream_share"] = summary["cells:SFR_0"] / summary["inflow"]
    return summary.rename(columns={"cells:expected_cells": "area:f_start"})


def sample_check(
    table: pd.DataFrame, qrats: tuple[str, ...] = QRATS, ens_dir: Path = er.ENS_DIR,
    scenario_dir: Path = er.SCENARIO_DIR,
) -> pd.DataFrame:
    """Return medians of the sample against stage 3 (same realisations, and all of them).

    rerun_max_diff is the largest relative difference of the rerun to stage 3 per realisation.
    """
    cols = ("inflow", "stream_share", "cells:RCHA", "area:f_start")
    rows = []
    for qrat in qrats:
        mine = table[table["qrat"] == qrat].set_index("real")
        old = stage3_summary(qrat, ens_dir, scenario_dir).set_index("real")
        same = old.loc[old.index.intersection(mine.index)]
        for col in cols:
            diff = (mine.loc[same.index, col] - same[col]).abs() / same[col].abs()
            rows.append(
                {
                    "qrat": qrat,
                    "quantity": col,
                    "sample_median": mine[col].median(),
                    "sample_median_without_base": mine.drop(index=BASE_REAL)[col].median(),
                    "stage3_same_reals": same[col].median(),
                    "stage3_all": old[col].median(),
                    "rerun_max_diff": float(diff.max()),
                    "n_sample": len(mine),
                    "n_stage3": len(old),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- analysis: reaches


def cell_centres(
    ws: Path = wf.OUT / "optimal", model: str = wf.MODEL
) -> tuple[np.ndarray, np.ndarray]:
    """Return x and y of every plan cell centre (row-major, y down from the first row)."""
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{model}.dis.grb")
    delr, delc = np.asarray(grb.delr), np.asarray(grb.delc)
    x, y = np.cumsum(delr) - delr / 2, np.cumsum(delc) - delc / 2
    xx, yy = np.meshgrid(x, y)
    return xx.ravel(), yy.ravel()


def reach_table(packagedata: Path = pr.BASE_MODEL / f"{wf.MODEL}_packagedata.dat") -> pd.DataFrame:
    """Return per SFR reach its cell, segment (line_id) and plan distance to each cluster [m]."""
    cells = mp7.sfr_reach_cells(packagedata)
    line_id = np.loadtxt(packagedata, comments="#", usecols=(-1,), dtype=np.int64)
    idomain = wf.grid_idomain(wf.OUT / "optimal")
    nrow, ncol = idomain.shape[1:]
    ncpl = nrow * ncol
    plan = cells[:, 1] * ncol + cells[:, 2]
    x, y = cell_centres()
    table = pd.DataFrame(
        {
            "reach": np.arange(1, len(cells) + 1),
            "layer": cells[:, 0] + 1,
            "cell": cells[:, 0] * ncpl + plan,
            "top_open": mp7.top_face_open(idomain)[tuple(cells.T)],
            "line_id": line_id,
        }
    )
    for name, wells in CLUSTERS.items():
        well_plan = np.array([wf.PRIORITY_WELLS[w] % ncpl for w in wells])
        d = np.hypot(x[plan][:, None] - x[well_plan], y[plan][:, None] - y[well_plan])
        table[f"d_{name}"] = d.min(axis=1)
    return table


def reach_long(out: Path, reals: list[str], qrats: tuple[str, ...] = QRATS) -> pd.DataFrame:
    """Return one row per realisation and reach with q and the volume to each cluster per qrat."""
    frames = []
    for real in reals:
        cols = {}
        for qrat in qrats:
            data = np.load(out / "reaches" / f"{case_name(real, qrat)}.npz")
            cols[f"q_{qrat}"] = data["q"]
            for name in (*CLUSTERS, GROUP):
                f = data[f"f_{name}"].astype(float)
                cols[f"f_{name}_{qrat}"] = f
                cols[f"v_{name}_{qrat}"] = f * np.maximum(data["q"], 0.0)
        frames.append(pd.DataFrame(cols).assign(real=real, reach=np.arange(1, len(data["q"]) + 1)))
    return pd.concat(frames, ignore_index=True)


def reach_state(q0: np.ndarray, q1: np.ndarray, tol: float = 1e-6) -> np.ndarray:
    """Return the state of each reach from base to the other rate: losing (L) or gaining (G)."""
    def label(q):
        return np.where(q > tol, "L", np.where(q < -tol, "G", "0"))

    return np.char.add(np.char.add(label(q0), "->"), label(q1))


def change_split(
    long: pd.DataFrame, name: str, q0: str = "baserat", q1: str = "maxrat"
) -> pd.DataFrame:
    """Return the change of a cluster's stream water split into leakage, share and product terms."""
    l0, l1 = np.maximum(long[f"q_{q0}"], 0.0), np.maximum(long[f"q_{q1}"], 0.0)
    f0, f1 = long[f"f_{name}_{q0}"], long[f"f_{name}_{q1}"]
    return pd.DataFrame(
        {
            "v_base": f0 * l0,
            "v_max": f1 * l1,
            "more_leakage": f0 * (l1 - l0),
            "larger_share": (f1 - f0) * l0,
            "product": (f1 - f0) * (l1 - l0),
            "leak_base": l0,
            "leak_max": l1,
        }
    )


def stream_by_distance(
    long: pd.DataFrame, reaches: pd.DataFrame, bins: tuple = DISTANCE_BINS
) -> pd.DataFrame:
    """Return per cluster and distance class the mean (over realisations) stream water to it."""
    n_reals = long["real"].nunique()
    rows = []
    for name in CLUSTERS:
        d = reaches.set_index("reach").loc[long["reach"], f"d_{name}"].to_numpy()
        split = change_split(long, name).assign(bin=np.digitize(d, bins) - 1)
        sums = split.groupby("bin").sum() / n_reals
        for b, values in sums.iterrows():
            row = {"cluster": name, "from_m": bins[b], "to_m": bins[b + 1]}
            rows.append({**row, **values.to_dict()})
    table = pd.DataFrame(rows)
    table["change"] = table["v_max"] - table["v_base"]
    return table


def stream_by_state(long: pd.DataFrame, reaches: pd.DataFrame) -> pd.DataFrame:
    """Return per reach state (L/G at base -> maxrat) the reaches, leakage and water to the wells.

    near_2km: the reach lies within 2 km (plan) of a priority well.
    """
    n_reals = long["real"].nunique()
    state = reach_state(long["q_baserat"].to_numpy(), long["q_maxrat"].to_numpy())
    split = change_split(long, GROUP).assign(state=state)
    d = reaches.set_index("reach")[[f"d_{c}" for c in CLUSTERS]].min(axis=1)
    split["near_2km"] = d.loc[long["reach"]].to_numpy() <= 2000.0
    split["reaches"] = 1.0
    table = split.groupby(["state", "near_2km"]).sum() / n_reals
    table["change"] = table["v_max"] - table["v_base"]
    return table.reset_index()


def stream_by_segment(long: pd.DataFrame, reaches: pd.DataFrame, n_top: int = 25) -> pd.DataFrame:
    """Return the segments (SFR line_id) with the largest mean change of the water to the wells."""
    n_reals = long["real"].nunique()
    info = reaches.set_index("reach")
    split = change_split(long, GROUP)
    split["line_id"] = info.loc[long["reach"], "line_id"].to_numpy()
    for c in CLUSTERS:
        split[f"d_{c}"] = info.loc[long["reach"], f"d_{c}"].to_numpy()
    sums = split.groupby("line_id")[["v_base", "v_max", "leak_base", "leak_max"]].sum() / n_reals
    dist = split.groupby("line_id")[[f"d_{c}" for c in CLUSTERS]].min()
    counts = info.groupby("line_id").size().rename("reaches")
    is_losing = long[["q_baserat", "q_maxrat"]].gt(1e-6).astype(float)
    is_losing.columns = ["losing_baserat", "losing_maxrat"]
    losing = is_losing.groupby(split["line_id"].to_numpy()).mean()
    table = sums.join(dist).join(counts).join(losing)
    table["change"] = table["v_max"] - table["v_base"]
    table["nearest_cluster"] = table[[f"d_{c}" for c in CLUSTERS]].idxmin(axis=1).str[2:]
    return table.sort_values("change", ascending=False).head(n_top).reset_index()


# ---------------------------------------------------------------- analysis: area growth


def published_mask_matrix(
    qrat: str, starts: pd.DataFrame, ncpl: int, n_masks: int = 357
) -> np.ndarray:
    """Return the published masks of a scenario on the start cells, (n_masks, n_starts) boolean."""
    plan = starts["node0"].to_numpy() % ncpl
    return np.array([er.read_mask(i, qrat).ravel()[plan] for i in range(n_masks)])


def growth_row(a0: np.ndarray, a1: np.ndarray) -> dict:
    """Return the median areas, the ratio of the medians and the median ratio of two scenarios."""
    ratio = np.asarray(a1, dtype=float) / np.asarray(a0, dtype=float)
    return {
        "area_baserat": float(np.median(a0)),
        "area_scenario": float(np.median(a1)),
        "growth_of_medians": float(np.median(a1) / np.median(a0)),
        "median_growth": float(np.median(ratio)),
        "min_growth": float(ratio.min()),
        "max_growth": float(ratio.max()),
    }


def growth_table(table: pd.DataFrame, published: dict[str, np.ndarray]) -> pd.DataFrame:
    """Return per scenario and area variant the growth over base pumping (sample medians).

    The published row uses all 357 masks of each scenario, paired by index (the index order is
    the same in every scenario).
    """
    base = table[table["qrat"] == "baserat"].set_index("real")
    rows = []
    for qrat in [q for q in published if q != "baserat"]:
        other = table[table["qrat"] == qrat].set_index("real").loc[base.index]
        for key, text in (*VARIANTS, ("network", "full mixing, stream network")):
            row = growth_row(base[f"area:{key}"].to_numpy(), other[f"area:{key}"].to_numpy())
            rows.append({"qrat": qrat, "variant": key, "description": text, **row})
        p0, p1 = published["baserat"].sum(axis=1), published[qrat].sum(axis=1)
        text = "published masks (357, paired by index)"
        row = {"qrat": qrat, "variant": "published", "description": text}
        rows.append({**row, **growth_row(p0, p1)})
    return pd.DataFrame(rows)


def mask_matches(
    out: Path, reals: list[str], published: dict[str, np.ndarray], calibrated: np.ndarray
) -> pd.DataFrame:
    """Return per case the published mask R1 matches best (Jaccard), its own mask and the base check.

    calibrated is the published mask of the calibrated model (workflow.mp7_mask), the reference
    for the base realisation at base pumping (it has no Monte Carlo mask).
    """
    paired = er.mask_indices()
    rows = []
    for real in reals:
        for qrat, masks in published.items():
            r1 = np.load(out / "starts" / f"{case_name(real, qrat)}.npz")["r1"]
            union = (masks | r1).sum(axis=1)
            jac = (masks & r1).sum(axis=1) / np.maximum(union, 1)
            best = int(np.argmax(jac))
            row = {"real": real, "qrat": qrat, "r1_cells": int(r1.sum()), "best_mask": best}
            row.update(best_jaccard=float(jac[best]), second_jaccard=float(np.sort(jac)[-2]))
            row["median_jaccard"] = float(np.median(jac))
            row["mask_index"] = paired.get(real, -1)
            row["paired_jaccard"] = float(jac[paired[real]]) if real in paired else np.nan
            if real == BASE_REAL and qrat == "baserat":
                row["jaccard_calibrated"] = wf.jaccard(r1, calibrated)
            rows.append(row)
    return pd.DataFrame(rows)


def stream_stops(
    out: Path, reals: list[str], reaches: pd.DataFrame, qrats: tuple[str, ...] = QRATS,
    bins: tuple = DISTANCE_BINS,
) -> pd.DataFrame:
    """Return where stopping at stream weak sinks removes particle weight (mean over the sample).

    lost is r2_thinned - r2_streams_thinned per start: the captured weight that stopping at the
    stream weak sinks (SFR cells with an active cell above) removes. It is assigned to the cell
    where the R1 particle ends, classed by layer, nearest well cluster and plan distance to that
    cluster's nearest well; 'elsewhere' collects particles that do not end in such a cell.
    """
    buried = reaches[~reaches["top_open"]].drop_duplicates("cell").set_index("cell")
    dist = buried[[f"d_{c}" for c in CLUSTERS]]
    buried = buried.assign(d=dist.min(axis=1), cluster=dist.idxmin(axis=1).str[2:])
    rows = []
    for qrat in qrats:
        frames = []
        for real in reals:
            data = np.load(out / "starts" / f"{case_name(real, qrat)}.npz")
            lost = data["r2_thinned"] - data["r2_streams_thinned"]
            end = pd.Series(data["r1_end"])
            in_stream = end.isin(buried.index).to_numpy()
            d = np.where(in_stream, buried["d"].reindex(end).to_numpy(), np.nan)
            layer = np.where(in_stream, buried["layer"].reindex(end).to_numpy(), 0)
            cluster = np.where(in_stream, buried["cluster"].reindex(end).to_numpy(), "")
            b = np.where(in_stream, np.digitize(np.nan_to_num(d), bins) - 1, -1)
            frames.append(
                pd.DataFrame(
                    {"lost": lost, "particles": (lost > 0.01).astype(float), "bin": b,
                     "layer": layer, "cluster": cluster}
                )
            )
        both = pd.concat(frames)
        keys = ["cluster", "layer", "bin"]
        sums = both.groupby(keys)[["lost", "particles"]].sum() / len(reals)
        for (cluster, layer, b), values in sums.iterrows():
            where = "elsewhere" if b < 0 else f"{bins[b]:g}-{bins[b + 1]:g} m"
            rows.append(
                {"qrat": qrat, "end_cluster": cluster, "end_layer": layer, "end_distance": where,
                 **values.to_dict()}
            )
    return pd.DataFrame(rows)


def pair_jaccards(masks: np.ndarray) -> np.ndarray:
    """Return the Jaccard index of every pair of rows of a boolean (n, n_starts) array."""
    m = masks.astype(np.float32)
    both = m @ m.T
    size = m.sum(axis=1)
    union = size[:, None] + size[None, :] - both
    i, j = np.triu_indices(len(m), k=1)
    return both[i, j] / np.maximum(union[i, j], 1.0)


def mask_similarity(out: Path, reals: list[str], published: dict[str, np.ndarray]) -> pd.DataFrame:
    """Return per scenario the Jaccard index between published masks and between R1 masks."""
    rows = []
    for qrat, masks in published.items():
        r1 = np.array([np.load(out / "starts" / f"{case_name(r, qrat)}.npz")["r1"] for r in reals])
        for label, jac in (("published", pair_jaccards(masks)), ("r1_sample", pair_jaccards(r1))):
            rows.append(
                {
                    "qrat": qrat,
                    "masks": label,
                    "pairs": len(jac),
                    "median_jaccard": float(np.median(jac)),
                    "min_jaccard": float(jac.min()),
                    "max_jaccard": float(jac.max()),
                }
            )
    return pd.DataFrame(rows)


def analyse(
    out: Path, reals: list[str], qrats: tuple[str, ...] = QRATS, ens_dir: Path = er.ENS_DIR,
    scenario_dir: Path = er.SCENARIO_DIR,
) -> None:
    """Write the sample check, the reach tables (base to maxrat) and the growth decomposition.

    ens_dir and scenario_dir hold the stage-2 and stage-3 runs the sample is checked against.
    """
    table = collect(out)
    table.to_csv(out / "summary.csv", index=False)
    sample_check(table, qrats, ens_dir, scenario_dir).to_csv(out / "sample_check.csv", index=False)
    reaches = reach_table()
    long = reach_long(out, reals, qrats)
    stream_by_distance(long, reaches).to_csv(out / "stream_by_distance.csv", index=False)
    stream_by_state(long, reaches).to_csv(out / "stream_by_state.csv", index=False)
    stream_by_segment(long, reaches).to_csv(out / "stream_by_segment.csv", index=False)
    stream_stops(out, reals, reaches, qrats).to_csv(out / "stream_stops.csv", index=False)
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)
    ncpl = int(np.prod(wf.grid_idomain(wf.OUT / "optimal").shape[1:]))
    published = {q: published_mask_matrix(q, starts, ncpl) for q in qrats}
    growth_table(table, published).to_csv(out / "growth_decomposition.csv", index=False)
    calibrated = wf.mp7_mask(starts, list(wf.PRIORITY_WELLS.values()))
    mask_matches(out, reals, published, calibrated).to_csv(out / "mask_matches.csv", index=False)
    mask_similarity(out, reals, published).to_csv(out / "mask_similarity.csv", index=False)


def main(
    run: bool = True,
    analyse_runs: bool = True,
    out: Path = OUT_DIR,
    sample_n: int = SAMPLE_N,
    qrats: tuple[str, ...] = QRATS,
    n_workers: int = N_WORKERS,
    ens_dir: Path = er.ENS_DIR,
    scenario_dir: Path = er.SCENARIO_DIR,
) -> None:
    """Run the sample at the scenarios and analyse it against the stage-2 and stage-3 runs."""
    reals = sample_realisations(sample_n)
    if run:
        run_cases(out, reals, qrats, n_workers)
    if analyse_runs:
        analyse(out, reals, qrats, ens_dir, scenario_dir)


if __name__ == "__main__":
    main()
