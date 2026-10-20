"""Neversink case study, pumping-scenario follow-up: why the contributing area of thinned PRT
particles can grow with pumping at a different rate than the area under full mixing.

The areas compared are sums over the published start cells (one particle per cell at its
centre, local z 0.5) of the captured weight of that particle (gwsource.prt gross accounting), or
of F of the start cell under full mixing. The cell value is not conserved, but the water is: with
flux-weighted releases from every source, the thinned particles deliver the wells' inflow, but
can split it between recharge and stream leakage differently from full mixing. Since every
start cell is a recharge cell, an area is close to the captured recharge divided by the
recharge per contributing cell, so a different source split moves the area.

Per case (realisation, scenario) the flow field is rebuilt as in growth_mechanisms (RCH and SFR
with an IFLOWFACE column) and two flux-weighted PRT runs are made from every source term of the
cells with F > FRACTION_THRESHOLD (gwsource.prt.release_points: SUBDIVISIONS, Z_LEVELS):
- distributed: every boundary flow distributed over its cell (the R3 convention of
  growth_mechanisms; budget copy with IFLOWFACE 0), thinned at every sink (weak_sink_survival).
  A recharge term is then released at 4 plan points x Z_LEVELS heights of its cell, an
  equal-volume release over the start cell, the dense counterpart of the single start particle.
- top_face: RCH and SFR on the top face where it is open (R2), thinned at the distributed sinks
  (growth_mechanisms.distributed_survival). Recharge is released on the top face (4 points).
Starts in a cell wet by a film (saturation < growth_mechanisms.FILM_SAT) are left out.

Per case the particle captures and F of every cell are saved; analyse() combines them with the
single-particle results of the same cases in growth_mechanisms' mechanisms60 output (same
realisations, same flows) into:
- areas, area_growth: F of the start cells, the dense recharge release over the start cells
  (capture of the recharge released in the start's recharge cell), the single particle
  (r3_thinned, r2_thinned), and the recharge of the start columns captured under each;
- decomposition: per realisation, the growth of the single-particle area over that of F split
  into method (dense / F) and quadrature (single / dense); method into captured recharge and
  area per unit captured recharge;
- source_growth: the recharge and stream water reaching the wells under mixing and along paths;
- by_f_class, reaches: per class of F of the start cell or of the losing SFR cell, the areas,
  leakage and captured parts; partial_reaches: the losing cells captured in part (PARTIAL_F) at
  base pumping, followed to the other rates;
- single_ratios, single_f_classes, single_by_place: the single-particle areas of all
  realisations of mechanisms60 against F, by F class, layer, region and distance to the wells.
Two checks: quadrature (FINE_K plan subdivisions on the base realisation) and through
(run_through_check: the share of the water released in, or carried by particles into, the
partially captured reach cells that reaches the wells along the paths, against F).

The tables answer three questions: whether the single particle is a good quadrature of the
dense distributed release (decomposition, the quadrature check), whether the dense release
converges to F (areas), and which source cells carry any difference in the source split
(source_growth, reaches, partial_reaches, the through check). Tables go to OUT_DIR and FINE_DIR
(git-ignored).

Run from anywhere with the project environment; the cases run in N_WORKERS processes (this
needs a process pool; some restricted environments forbid one):

    python studies/neversink/advective_growth.py

A case takes 3 to 6 min (MF6 15 to 30 s; distributed 210,000 to 480,000 particles, 2 to 5
min; top face a quarter of that); the 18 cases ran in about 25 min on four processes, the two
finer cases (1.2 and 1.8 million particles) in 15 and 19 min, and the through check in about
8 min per case on one process. Resumable: a case with a summary file is skipped. The track
files (up to a few GB) are deleted once read.
"""

import copy
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import growth_mechanisms as gm  # noqa: E402
import mp7_convention as mp7  # noqa: E402
import pest_rebuild as pr  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

OUT_DIR = wf.OUT / "scenarios" / "advective_growth"
MECH_DIR = wf.OUT / "scenarios" / "mechanisms60"  # single-particle results of the same cases
# The base realisation and five of mechanisms60 spread over its range of growth ratios
# (r3_thinned growth / F growth)
REALS = ("base", "231", "353", "101", "196", "0")
QRATS = gm.QRATS  # baserat, 0.5rat, maxrat
CONVENTIONS = ("distributed", "top_face")
SINGLE = {"distributed": "r3_thinned", "top_face": "r2_thinned"}  # matching mechanisms60 column
SUBDIVISIONS = 1
Z_LEVELS = 4
FRACTION_THRESHOLD = 1e-4
PACKAGES = ("RCHA", "SFR_0")
GROUP = gm.GROUP
F_CLASSES = (0.0, 1e-4, 0.01, 0.1, 0.5, 0.9, 0.999, 1.01)
N_WORKERS = 4
# Quadrature check: the base realisation again with 16 plan points per cell (k = 2)
FINE_DIR = OUT_DIR.with_name("advective_growth_k2")
FINE_REALS = ("base",)
FINE_K = 2
FINE_QRATS = ("baserat", "maxrat")
# Losing reach cells captured in part at base pumping (F in PARTIAL_F); the through-flow check
# reruns THROUGH_REALS keeping the particle paths
PARTIAL_F = (0.5, 0.9)
THROUGH_REALS = ("base",)
THREADS_PER_WORKER = 2

_WORKER = {}  # per-process state set by the pool initializer


# ---------------------------------------------------------------- PRT runs


def distributed_step(step: gs.FlowStep) -> gs.FlowStep:
    """Return a shallow copy of a step with every boundary flow distributed (IFLOWFACE 0)."""
    out = copy.copy(step)
    out.term_iflowface = np.zeros(step.n_terms, dtype=np.int64)
    return out


def subset_release(release: gs.prt.ReleasePoints, keep: np.ndarray) -> gs.prt.ReleasePoints:
    """Return the release points where keep is True."""
    names = ("cell", "x", "y", "z", "weight", "package")
    return gs.prt.ReleasePoints(**{n: getattr(release, n)[keep] for n in names})


def source_release(
    step: gs.FlowStep, grid: gs.prt.PrtGrid, f: np.ndarray, sat: np.ndarray,
    threshold: float = FRACTION_THRESHOLD, k: int = SUBDIVISIONS, z_levels: int = Z_LEVELS,
    min_sat: float = gm.FILM_SAT,
) -> tuple[gs.prt.ReleasePoints, int]:
    """Return the flux-weighted release points of the cells with F > threshold (films left out)
    and the number of points left out."""
    local_z = (np.arange(z_levels) + 0.5) / z_levels
    release = gs.prt.release_points(step, grid, f > threshold, None, k, local_z)
    s = sat[release.cell]
    keep = (s == 0.0) | (s >= min_sat)
    return subset_release(release, keep), int(np.sum(~keep))


def release_frame(release: gs.prt.ReleasePoints) -> pd.DataFrame:
    """Return release points as the start table of mp7_convention.write_mp7_prt."""
    return pd.DataFrame(
        {"node0": release.cell, "x0": release.x, "y0": release.y, "zloc0": release.z}
    )


def read_visits(track_csv: Path) -> dict[str, np.ndarray]:
    """Return the cell visits of a PRT track file (pandas reader; the file is deleted)."""
    cols = gs.prt.TRACK_COLUMNS
    table = pd.read_csv(track_csv, usecols=list(cols))
    track_csv.unlink()
    dtype = [(n, "f8" if n in ("trelease", "t") else "i8") for n in cols]
    tracks = np.empty(len(table), dtype=dtype)
    for name in cols:
        tracks[name] = table[name].to_numpy()
    del table
    return gs.prt.cell_visits(tracks)


def convention_inputs(
    ws: Path, step: gs.FlowStep, convention: str
) -> tuple[gs.FlowStep, Path, np.ndarray]:
    """Return the step to seed from, the budget file PRT reads and the thinning survival."""
    budget = ws / f"{wf.MODEL}.cbc"
    if convention == "distributed":
        flat = ws / "distributed.cbc"
        mp7.write_distributed_budget(budget, flat, gm.FACE_TEXTS)
        return distributed_step(step), flat, gs.prt.weak_sink_survival(step)
    assert convention == "top_face", f"unknown convention {convention}"
    return step, budget, gm.distributed_survival(step)


def track_convention(
    ws: Path, step: gs.FlowStep, result: gs.BackwardResult, sat: np.ndarray, exe: Path,
    convention: str, k: int = SUBDIVISIONS, z_levels: int = Z_LEVELS,
) -> tuple[gs.prt.ReleasePoints, dict[str, np.ndarray], np.ndarray, int]:
    """Run one flux-weighted PRT release; return the release points, cell visits, the thinning
    survival used and the number of points left out for a film."""
    seed_step, budget, survival = convention_inputs(ws, step, convention)
    grid = gs.prt.load_prt_grid(ws, wf.MODEL, "DIS")
    f = result.fraction_through[GROUP]
    release, films = source_release(seed_step, grid, f, sat, k=k, z_levels=z_levels)
    prt_ws = ws / f"prt_{convention}"
    options = {"stop_at_weak_sink": False, "tracks": True}
    sim = mp7.write_mp7_prt(prt_ws, ws, budget, release_frame(release), exe, **options)
    visits = read_visits(gs.prt.run_prt(sim))
    shutil.rmtree(prt_ws)
    return release, visits, survival, films


def run_convention(
    ws: Path, step: gs.FlowStep, result: gs.BackwardResult, sat: np.ndarray, exe: Path,
    convention: str, k: int = SUBDIVISIONS, z_levels: int = Z_LEVELS,
) -> tuple[dict[str, np.ndarray], dict]:
    """Run one flux-weighted PRT release; return the per-particle capture and a summary row."""
    t0 = time.perf_counter()
    tracked = track_convention(ws, step, result, sat, exe, convention, k, z_levels)
    release, visits, survival, films = tracked
    share = gs.prt.destination_share(step, result.selections[GROUP])
    captured = gs.prt.capture_along_paths(visits, release.n, share, survival)[0]
    particles = {
        "cell": release.cell.astype(np.int32),
        "package": release.package.astype(str),
        "z": release.z.astype(np.float32),
        "weight": release.weight,
        "captured": captured.astype(np.float32),
    }
    row = {f"{convention}:particles": release.n, f"{convention}:film_points": films}
    for pkg in PACKAGES:
        is_pkg = release.package == pkg
        row[f"{convention}:released:{pkg}"] = float(release.weight[is_pkg].sum())
        row[f"{convention}:captured:{pkg}"] = float(np.sum(release.weight * captured * is_pkg))
    row[f"{convention}:seconds"] = time.perf_counter() - t0
    return particles, row


# ---------------------------------------------------------------- one case and the pool


def init_worker(pest_dir: Path) -> None:
    """Load the interface and the executable once per worker process."""
    _WORKER["iface"] = pr.load_interface(pest_dir)
    _WORKER["exe"] = wf.mf6_exe()


def run_case(
    real: str, qrat: str, out: Path, conventions: tuple[str, ...] = CONVENTIONS,
    k: int = SUBDIVISIONS, z_levels: int = Z_LEVELS,
) -> dict:
    """Write, run, trace and track one case with the conventions; save; delete the workspace."""
    iface, exe = _WORKER["iface"], _WORKER["exe"]
    name = gm.case_name(real, qrat)
    ws = out / "ws" / name
    gm.write_case(real, qrat, ws, iface)
    row = {"real": real, "qrat": qrat, "mf6_seconds": wf.run_mf6(ws, exe)}
    step, result, _ = wf.trace_wells(ws)
    row["inflow"] = result.destination_inflow[GROUP]
    for pkg in PACKAGES:
        row[f"mixing:{pkg}"] = float(result.volume_from_by_term[GROUP][pkg].sum())
    sat = mp7.cell_saturation(ws / f"{wf.MODEL}.cbc", step.n_cells)
    f = result.fraction_through[GROUP][: step.n_cells].astype(np.float32)
    np.savez_compressed(out / "cells" / f"{name}.npz", f=f)
    for convention in conventions:
        particles, prt_row = run_convention(ws, step, result, sat, exe, convention, k, z_levels)
        np.savez_compressed(out / "particles" / f"{name}_{convention}.npz", **particles)
        row.update(prt_row)
    (out / "summary" / f"{name}.json").write_text(json.dumps(row))
    shutil.rmtree(ws)
    return row


def run_cases(
    out: Path, reals: tuple[str, ...], qrats: tuple[str, ...], n_workers: int = N_WORKERS,
    threads: int = THREADS_PER_WORKER, **case_options,
) -> None:
    """Run the pending cases in a process pool; failures are logged and stay pending.

    case_options go to run_case (conventions, k, z_levels).
    """
    for sub in ("ws", "summary", "cells", "particles"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    cases = gm.pending_cases(out, list(reals), qrats)
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = str(threads)  # inherited by the workers before they import numpy
    t0 = time.perf_counter()
    with ProcessPoolExecutor(n_workers, initializer=init_worker, initargs=(pr.PEST_DIR,)) as pool:
        jobs = {pool.submit(run_case, r, q, out, **case_options): (r, q) for r, q in cases}
        for k, job in enumerate(as_completed(jobs), start=1):
            try:
                job.result()
            except Exception as err:  # keep the pool running; the case stays pending
                with (out / "failures.log").open("a") as f:
                    f.write(f"{gm.case_name(*jobs[job])}: {type(err).__name__}: {err}\n")
            minutes = (time.perf_counter() - t0) / 60
            name = gm.case_name(*jobs[job])
            print(f"{k}/{len(cases)} done ({name}), {minutes:.1f} min", flush=True)


# ---------------------------------------------------------------- through-flow check


def partial_cells(
    out: Path, real: str, f_range: tuple[float, float] = PARTIAL_F, convention: str = "distributed"
) -> np.ndarray:
    """Return the losing SFR cells whose F at base pumping lies in f_range (saved case)."""
    name = gm.case_name(real, "baserat")
    f = np.load(out / "cells" / f"{name}.npz")["f"].astype(float)
    particles = dict(np.load(out / "particles" / f"{name}_{convention}.npz"))
    leak = cell_capture(particles, len(f), "SFR_0")[0]
    return np.flatnonzero((leak > 0) & (f >= f_range[0]) & (f < f_range[1]))


def visit_gains(
    visits: dict[str, np.ndarray], share: np.ndarray, survival: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return per visit the particle's remaining weight on entry, the share captured there and
    the share captured on the earlier visits (as gwsource.prt.capture_along_paths)."""
    p = visits["particle"]
    log_f = np.log(np.maximum(survival[visits["cell"]], 1e-300))
    cum = np.cumsum(log_f)
    start = np.r_[0, np.flatnonzero(p[1:] != p[:-1]) + 1]
    counts = np.diff(np.r_[start, len(p)])
    remaining = np.exp(cum - log_f - np.repeat(cum[start] - log_f[start], counts))
    gain = remaining * share[visits["cell"]]
    cum_gain = np.cumsum(gain)
    before = cum_gain - gain - np.repeat(cum_gain[start] - gain[start], counts)
    return remaining, gain, before


def through_capture(
    visits: dict[str, np.ndarray], release: gs.prt.ReleasePoints, share: np.ndarray,
    survival: np.ndarray, cells: np.ndarray, f: np.ndarray,
) -> pd.DataFrame:
    """Return, for the water released in a set of cells and the water entering them from
    elsewhere (by source package), the flow, the part of it captured from there on along the
    paths (P) and under full mixing (F of the cell it is in or enters)."""
    remaining, gain, before = visit_gains(visits, share, survival)
    p, c = visits["particle"], visits["cell"]
    total = np.bincount(p, weights=gain, minlength=release.n)
    idx = np.flatnonzero(np.isin(c, cells))
    particles, first = np.unique(p[idx], return_index=True)
    e = idx[first]  # each particle's first visit to the set (visits are in time order)
    released_here = np.r_[True, p[1:] != p[:-1]][e]
    flow = release.weight[particles] * remaining[e]
    table = pd.DataFrame(
        {
            "origin": np.where(released_here, "released in the cells", "entering them"),
            "package": release.package[particles],
            "flow": flow,
            "prt": release.weight[particles] * (total[particles] - before[e]),
            "mixing": flow * f[c[e]],
        }
    )
    out = table.groupby(["origin", "package"])[["flow", "prt", "mixing"]].sum().reset_index()
    out["P"], out["F"] = out["prt"] / out["flow"], out["mixing"] / out["flow"]
    return out


def run_through_check(real: str, qrat: str, cells: np.ndarray, out: Path) -> pd.DataFrame:
    """Rebuild and track one case (distributed release) and return through_capture() for cells."""
    iface, exe = pr.load_interface(pr.PEST_DIR), wf.mf6_exe()
    ws = out / "ws" / f"through_{gm.case_name(real, qrat)}"
    gm.write_case(real, qrat, ws, iface)
    wf.run_mf6(ws, exe)
    step, result, _ = wf.trace_wells(ws)
    sat = mp7.cell_saturation(ws / f"{wf.MODEL}.cbc", step.n_cells)
    release, visits, survival, _ = track_convention(ws, step, result, sat, exe, "distributed")
    share = gs.prt.destination_share(step, result.selections[GROUP])
    f = result.fraction_through[GROUP]
    table = through_capture(visits, release, share, survival, cells, f)
    shutil.rmtree(ws)
    return table.assign(real=real, qrat=qrat, cells=len(cells))


def through_checks(
    out: Path, reals: tuple[str, ...] = THROUGH_REALS, qrats: tuple[str, ...] = QRATS
) -> pd.DataFrame:
    """Return the through-flow check of the partially captured reach cells of each realisation
    (selected at base pumping) at every scenario; cases run one after the other."""
    frames = []
    for real in reals:
        cells = partial_cells(out, real)
        frames += [run_through_check(real, qrat, cells, out) for qrat in qrats]
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- analysis: per case


def cell_capture(particles: dict, n_cells: int, package: str = "RCHA") -> tuple[np.ndarray, ...]:
    """Return per cell the flow released from one package and its captured part."""
    w = np.where(particles["package"] == package, particles["weight"], 0.0)
    released = np.bincount(particles["cell"], weights=w, minlength=n_cells)
    captured = np.bincount(particles["cell"], weights=w * particles["captured"], minlength=n_cells)
    return released, captured


def start_recharge_cells(released: np.ndarray, starts: np.ndarray, ncpl: int) -> np.ndarray:
    """Return, per start, the cell of its column that receives recharge (-1: none released).

    Recharge enters one cell per column (IRCH); columns without released recharge (F below the
    threshold) get -1.
    """
    cells = np.flatnonzero(released > 0)
    column = np.full(ncpl, -1, dtype=np.int64)
    column[cells % ncpl] = cells
    return column[starts % ncpl]


def case_starts(
    out: Path, real: str, qrat: str, convention: str, starts: np.ndarray, ncpl: int
) -> dict:
    """Return per start F, the dense recharge capture, the single particle, and the recharge."""
    name = gm.case_name(real, qrat)
    f = np.load(out / "cells" / f"{name}.npz")["f"].astype(float)
    particles = dict(np.load(out / "particles" / f"{name}_{convention}.npz"))
    released, captured = cell_capture(particles, len(f))
    rch_cell = start_recharge_cells(released, starts, ncpl)
    has = rch_cell >= 0
    rch = np.where(has, released[rch_cell], 0.0)
    dense = np.where(has, captured[rch_cell] / np.where(rch > 0, rch, 1.0), 0.0)
    mech = np.load(MECH_DIR / "starts" / f"{name}.npz")
    return {
        "f_start": f[starts],
        "f_mech": mech["f_start"].astype(float),
        "f_rch": np.where(has, f[rch_cell], 0.0),
        "dense": dense,
        "single": mech[SINGLE[convention]].astype(float),
        "rch": rch,
        "rch_elsewhere": has & (rch_cell != starts),
    }


def area_row(per_start: dict) -> dict:
    """Return the areas (sums over the starts) and the recharge-weighted sums of one case."""
    r = per_start["rch"]
    row = {f"area:{k}": float(per_start[k].sum()) for k in ("f_start", "f_rch", "dense", "single")}
    row["rch_mix_starts"] = float(np.sum(r * per_start["f_rch"]))
    row["rch_prt_starts"] = float(np.sum(r * per_start["dense"]))
    row["max_f_diff_mech"] = float(np.abs(per_start["f_start"] - per_start["f_mech"]).max())
    row["starts_rch_elsewhere"] = int(np.sum(per_start["rch_elsewhere"]))
    return row


def f_class_rows(per_start: dict, bins: tuple = F_CLASSES) -> list[dict]:
    """Return per class of F of the start cell the starts, the three areas and the captured
    recharge of the start columns (mixing and dense release)."""
    b = np.digitize(per_start["f_start"], bins) - 1
    rows = []
    for k in range(len(bins) - 1):
        m = b == k
        row = {"f_from": bins[k], "f_to": bins[k + 1], "starts": int(m.sum())}
        for v in ("f_start", "dense", "single"):
            row[f"area:{v}"] = float(per_start[v][m].sum())
        row["rch_mix"] = float(np.sum((per_start["rch"] * per_start["f_rch"])[m]))
        row["rch_prt"] = float(np.sum((per_start["rch"] * per_start["dense"])[m]))
        rows.append(row)
    return rows


def reach_rows(out: Path, real: str, qrat: str, convention: str, bins: tuple = F_CLASSES) -> list:
    """Return per class of F of the losing SFR cells the leakage and its captured part.

    SFR particles are released in the reach cells; F is the reach cell's, PRT the captured share
    of the released leakage (both summed over the reaches in the class).
    """
    name = gm.case_name(real, qrat)
    f = np.load(out / "cells" / f"{name}.npz")["f"].astype(float)
    particles = dict(np.load(out / "particles" / f"{name}_{convention}.npz"))
    released, captured = cell_capture(particles, len(f), "SFR_0")
    cells = np.flatnonzero(released > 0)
    b = np.digitize(f[cells], bins) - 1
    rows = []
    for k in range(len(bins) - 1):
        c = cells[b == k]
        rows.append(
            {"f_from": bins[k], "f_to": bins[k + 1], "cells": len(c),
             "leakage": released[c].sum(), "mixing": float(np.sum(released[c] * f[c])),
             "prt": captured[c].sum()}
        )
    return rows


# ---------------------------------------------------------------- analysis: tables


def collect(out: Path) -> pd.DataFrame:
    """Return the summary rows of every finished case with the stream shares."""
    rows = [json.loads(p.read_text()) for p in sorted((out / "summary").glob("*.json"))]
    table = pd.DataFrame(rows)
    present = [c for c in CONVENTIONS if f"{c}:particles" in table.columns]
    for method in ("mixing", *present):
        prefix = method if method == "mixing" else f"{method}:captured"
        total = sum(table[f"{prefix}:{pkg}"] for pkg in PACKAGES)
        table[f"{method}:total"] = total
        table[f"{method}:stream_share"] = table[f"{prefix}:SFR_0"] / total
    return table


def case_tables(
    out: Path, reals: tuple[str, ...], qrats: tuple[str, ...]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return the per-case areas, the F-class table and the reach table of every case."""
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)["node0"].to_numpy()
    ncpl = int(np.prod(wf.grid_idomain(wf.OUT / "optimal").shape[1:]))
    areas, classes, reaches = [], [], []
    for real in reals:
        for qrat in qrats:
            for convention in CONVENTIONS:
                key = {"real": real, "qrat": qrat, "convention": convention}
                per_start = case_starts(out, real, qrat, convention, starts, ncpl)
                areas.append({**key, **area_row(per_start)})
                classes += [{**key, **r} for r in f_class_rows(per_start)]
                reaches += [{**key, **r} for r in reach_rows(out, real, qrat, convention)]
    return pd.DataFrame(areas), pd.DataFrame(classes), pd.DataFrame(reaches)


def growth(
    table: pd.DataFrame, columns: list[str], keys: tuple = ("real", "convention")
) -> pd.DataFrame:
    """Return per key the base and maxrat values of the columns and their ratio."""
    base = table[table["qrat"] == "baserat"].set_index(list(keys))[columns]
    other = table[table["qrat"] == "maxrat"].set_index(list(keys))[columns]
    out = base.add_suffix(":base").join(other.add_suffix(":max"))
    for c in columns:
        out[f"{c}:growth"] = out[f"{c}:max"] / out[f"{c}:base"]
    return out.reset_index()


def decomposition(area_growth: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Return per realisation and convention the growth of the single-particle area over that of
    full mixing, split into method (dense release over F) and quadrature (single over dense),
    the method part split into captured recharge and recharge per unit area, and the stream
    shares under mixing and along the paths at both rates."""
    g = area_growth.set_index(["real", "convention"])
    out = pd.DataFrame(index=g.index)
    out["total"] = g["area:single:growth"] / g["area:f_start:growth"]
    out["method"] = g["area:dense:growth"] / g["area:f_start:growth"]
    out["quadrature"] = g["area:single:growth"] / g["area:dense:growth"]
    out["recharge"] = g["rch_prt_starts:growth"] / g["rch_mix_starts:growth"]
    out["per_area"] = out["method"] / out["recharge"]
    shares = summary.set_index(["real", "qrat"])
    for (real, convention) in out.index:
        for qrat, tag in (("baserat", "base"), ("maxrat", "max")):
            out.loc[(real, convention), f"mixing_share:{tag}"] = shares.loc[
                (real, qrat), "mixing:stream_share"
            ]
            out.loc[(real, convention), f"prt_share:{tag}"] = shares.loc[
                (real, qrat), f"{convention}:stream_share"
            ]
    return out.reset_index()


def single_ratios(mech_dir: Path = MECH_DIR) -> pd.DataFrame:
    """Return per realisation and scenario of growth_mechanisms the single-particle areas over
    the full-mixing area, with the mixing stream share."""
    table = pd.read_csv(mech_dir / "summary.csv", dtype={"real": str})
    out = table[["real", "qrat", "area:f_start", "area:r3_thinned", "area:r2_thinned"]].copy()
    out["stream_share"] = table["stream_share"]
    for key in SINGLE.values():
        out[f"{key}/f"] = out[f"area:{key}"] / out["area:f_start"]
    return out


def single_f_classes(
    mech_dir: Path = MECH_DIR, qrats: tuple[str, ...] = gm.QRATS, bins: tuple = F_CLASSES
) -> pd.DataFrame:
    """Return per scenario and class of F of the start cell the mean (over the realisations of
    growth_mechanisms) number of starts, areas and absolute single-particle difference."""
    rows = []
    for qrat in qrats:
        for path in sorted((mech_dir / "starts").glob(f"{qrat}_*.npz")):
            data = np.load(path)
            f = data["f_start"].astype(float)
            b = np.digitize(f, bins) - 1
            for k in range(len(bins) - 1):
                m = b == k
                row = {"qrat": qrat, "real": path.stem.split("_", 1)[1], "f_from": bins[k]}
                row.update(f_to=bins[k + 1], starts=int(m.sum()), f_start=float(f[m].sum()))
                for key in SINGLE.values():
                    single = data[key].astype(float)[m]
                    row[key] = float(single.sum())
                    row[f"abs_{key}_minus_f"] = float(np.abs(single - f[m]).sum())
                rows.append(row)
    table = pd.DataFrame(rows)
    return table.groupby(["qrat", "f_from", "f_to"]).mean(numeric_only=True).reset_index()


def quadrature_table(
    out: Path = OUT_DIR, fine: Path = FINE_DIR, reals: tuple[str, ...] = FINE_REALS,
    qrats: tuple[str, ...] = FINE_QRATS,
) -> pd.DataFrame:
    """Return the distributed dense-release areas and captured water of the default and the
    finer release (FINE_K) of the same cases."""
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)["node0"].to_numpy()
    ncpl = int(np.prod(wf.grid_idomain(wf.OUT / "optimal").shape[1:]))
    summaries = {label: collect(d).set_index(["real", "qrat"]) for label, d in
                 (("default", out), ("fine", fine))}
    rows = []
    for real in reals:
        for qrat in qrats:
            for label, d in (("default", out), ("fine", fine)):
                per_start = case_starts(d, real, qrat, "distributed", starts, ncpl)
                summary = summaries[label].loc[(real, qrat)]
                row = {"real": real, "qrat": qrat, "release": label, **area_row(per_start)}
                for key in ("particles", "captured:RCHA", "captured:SFR_0", "stream_share"):
                    row[key] = summary[f"distributed:{key}"]
                rows.append(row)
    return pd.DataFrame(rows)


def reach_cell_info(reaches: pd.DataFrame) -> pd.DataFrame:
    """Return per SFR cell its layer (1-based), open top, nearest cluster and plan distance."""
    info = reaches.drop_duplicates("cell").set_index("cell")
    dist = info[[f"d_{c}" for c in gm.CLUSTERS]]
    return info.assign(d=dist.min(axis=1), cluster=dist.idxmin(axis=1).str[2:])


def partial_reaches(
    out: Path, reals: tuple[str, ...], qrats: tuple[str, ...] = QRATS,
    f_range: tuple[float, float] = PARTIAL_F, convention: str = "distributed",
) -> pd.DataFrame:
    """Return, per realisation and scenario, the leakage of the losing SFR cells whose F at base
    pumping lies in f_range, and the share of it reaching the wells under mixing (F) and along
    the paths (P), with where these cells lie."""
    info = reach_cell_info(gm.reach_table())
    rows = []
    for real in reals:
        cells = partial_cells(out, real, f_range, convention)
        where = info.loc[cells]
        for qrat in qrats:
            name = gm.case_name(real, qrat)
            f = np.load(out / "cells" / f"{name}.npz")["f"].astype(float)
            particles = dict(np.load(out / "particles" / f"{name}_{convention}.npz"))
            leak, captured = cell_capture(particles, len(f), "SFR_0")
            rows.append(
                {"real": real, "qrat": qrat, "cells": len(cells), "leakage": leak[cells].sum(),
                 "F": float(np.sum(leak[cells] * f[cells]) / leak[cells].sum()),
                 "P": float(captured[cells].sum() / leak[cells].sum()),
                 "prt_minus_mixing": float(np.sum(captured[cells] - leak[cells] * f[cells])),
                 "d_min": where["d"].min(), "d_max": where["d"].max(),
                 "clusters": ",".join(sorted(set(where["cluster"]))),
                 "layers": ",".join(map(str, sorted(set(where["layer"]))))}
            )
    return pd.DataFrame(rows)


def start_places(starts: pd.DataFrame, ncpl: int, bins: tuple = gm.DISTANCE_BINS) -> pd.DataFrame:
    """Return per start its MODPATH region and plan distance class to the nearest priority well."""
    plan = starts["node0"].to_numpy() % ncpl
    x, y = gm.cell_centres()
    wells = np.array([node % ncpl for node in wf.PRIORITY_WELLS.values()])
    d = np.hypot(x[plan][:, None] - x[wells], y[plan][:, None] - y[wells]).min(axis=1)
    labels = [f"{a:g}-{b:g} m" for a, b in zip(bins[:-1], bins[1:])]
    return pd.DataFrame({"region": starts["region"].to_numpy(),
                         "distance": np.array(labels)[np.digitize(d, bins) - 1]})


def single_by_place(mech_dir: Path = MECH_DIR, qrats: tuple[str, ...] = gm.QRATS) -> pd.DataFrame:
    """Return per scenario, and per layer (of the draped start), region or distance class to the
    nearest well, the mean (over growth_mechanisms' realisations) F and single-particle areas."""
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)
    ncpl = int(np.prod(wf.grid_idomain(wf.OUT / "optimal").shape[1:]))
    places = start_places(starts, ncpl)
    rows = []
    for qrat in qrats:
        paths = sorted((mech_dir / "starts").glob(f"{qrat}_*.npz"))
        for path in paths:
            data = np.load(path)
            values = pd.DataFrame({k: data[k].astype(float) for k in ("f_start", *SINGLE.values())})
            values = values.assign(layer=data["draped_node"] // ncpl + 1, **places)
            for key in ("layer", "region", "distance"):
                sums = values.groupby(key)[["f_start", *SINGLE.values()]].sum() / len(paths)
                for place, row in sums.iterrows():
                    rows.append({"qrat": qrat, "by": key, "place": str(place), **row.to_dict()})
    return pd.DataFrame(rows).groupby(["qrat", "by", "place"], sort=False).sum().reset_index()


def analyse(
    out: Path = OUT_DIR, reals: tuple[str, ...] = REALS, qrats: tuple[str, ...] = QRATS
) -> None:
    """Write the area, source, F-class and reach tables of the finished cases, and the
    single-particle ratios and F classes of growth_mechanisms' sample."""
    single_ratios().to_csv(out / "single_ratios.csv", index=False)
    single_f_classes().to_csv(out / "single_f_classes.csv", index=False)
    single_by_place().to_csv(out / "single_by_place.csv", index=False)
    summary = collect(out)
    summary.to_csv(out / "summary.csv", index=False)
    areas, classes, reaches = case_tables(out, reals, qrats)
    areas.to_csv(out / "areas.csv", index=False)
    classes.to_csv(out / "by_f_class.csv", index=False)
    reaches.to_csv(out / "reaches.csv", index=False)
    partial_reaches(out, reals, qrats).to_csv(out / "partial_reaches.csv", index=False)
    cols = ["area:f_start", "area:dense", "area:single", "rch_mix_starts", "rch_prt_starts"]
    area_growth = growth(areas, cols)
    area_growth.to_csv(out / "area_growth.csv", index=False)
    decomposition(area_growth, summary).to_csv(out / "decomposition.csv", index=False)
    sources = [c for c in summary.columns if ":captured:" in c or c.startswith("mixing:")]
    sources += [c for c in summary.columns if c.endswith(":stream_share") or c.endswith(":total")]
    growth(summary.assign(convention="-"), sorted(set(sources))).to_csv(
        out / "source_growth.csv", index=False
    )


def main(
    run: bool = True,
    run_fine: bool = True,
    run_through: bool = True,
    analyse_runs: bool = True,
    out: Path = OUT_DIR,
    fine: Path = FINE_DIR,
    reals: tuple[str, ...] = REALS,
    qrats: tuple[str, ...] = QRATS,
    n_workers: int = N_WORKERS,
) -> None:
    """Run the cases and analyse them."""
    if run:
        run_cases(out, reals, qrats, n_workers)
    if run_fine:
        options = {"conventions": ("distributed",), "k": FINE_K}
        run_cases(fine, FINE_REALS, FINE_QRATS, min(n_workers, len(FINE_QRATS)), **options)
    if run_through:
        through_checks(out).to_csv(out / "through.csv", index=False)
    if analyse_runs:
        analyse(out, reals, qrats)
        quadrature_table(out, fine).to_csv(out / "quadrature.csv", index=False)


if __name__ == "__main__":
    main()
