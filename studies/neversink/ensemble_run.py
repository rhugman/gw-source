"""Neversink case study, stage 2: the 358-realisation Monte Carlo ensemble at base pumping.

Every realisation of the rebuilt ensemble (pest_rebuild.py) is written, run with MF6 and traced
backward from the eight priority wells twice: with streams as cells, and with the SFR reaches
as package nodes. The published solver criterion is kept, so the stream network needs a looser
aquifer exchange tolerance than the default (AQUIFER_RTOL_NETWORK; see docs/neversink_study.md).
Per realisation the F of the uppermost active layer is kept (both traces) with a summary row;
the workspace is deleted.

The published masks baserat_real0..356 belong to rows 0..356 of modpath_par_ens.csv; the last
row ('base') has none. Each mask is compared with its realisation's F at the MODPATH start
cells, and the published probability (the share of the 357 masks in which a cell contributes)
with the share of realisations in which F exceeds a threshold, and with the mean F.

Run from anywhere with the project environment; the realisations run in N_WORKERS processes
(outside the Claude Code sandbox, which blocks process pools):

    python studies/neversink/ensemble_run.py

Edit the gates in __main__ to rerun parts. The run is resumable: a realisation with a summary
file is skipped. Output goes to studies/neversink/output/ensemble/ (git-ignored).
"""

import io
import json
import os
import shutil
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import figures  # noqa: E402
import pest_rebuild as pr  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

ENS_DIR = wf.OUT / "ensemble"
MASK_ZIP = wf.SOURCE / "output" / "modpath_mc" / "{qrat}.zip"
N_WORKERS = 6
THREADS_PER_WORKER = 2
AQUIFER_RTOL_NETWORK = 1e-3
THRESHOLDS = (0.1, 0.5)
GROUP = "priority"

_WORKER = {}  # per-process state set by the pool initializer (interface, exe, start cells)


def read_mask(index: int, qrat: str = "baserat") -> np.ndarray:
    """Return published mask number index of a scenario as a (nrow, ncol) boolean grid."""
    with zipfile.ZipFile(str(MASK_ZIP).format(qrat=qrat)) as z:
        with z.open(f"{qrat}/{qrat}_real{index}.dat") as f:
            return np.loadtxt(io.TextIOWrapper(f)) > 0.5


def mask_indices(pest_dir: Path = pr.PEST_DIR) -> dict[str, int]:
    """Return {realisation name: published mask index}."""
    table = pd.read_csv(pest_dir / "mask_index.csv", dtype={"real_name": str})
    return dict(zip(table["real_name"], table["mask_index"]))


def start_cells(nrow: int, ncol: int) -> np.ndarray:
    """Return the (row * ncol + col) cells where the published particles start."""
    return np.unique(wf.read_endpoints()["node0"].to_numpy() % (nrow * ncol))


def compare_one(f_top: np.ndarray, mask: np.ndarray, starts: np.ndarray) -> dict:
    """Compare one realisation's F (uppermost active layer) with its mask on the start cells."""
    f = np.nan_to_num(f_top.ravel()[starts])
    m = mask.ravel()[starts]
    top = np.zeros(len(f), dtype=bool)
    top[np.argsort(-f, kind="stable")[: m.sum()]] = True
    row = {"mp7_cells": int(m.sum()), "expected_cells": float(f.sum())}
    for t in THRESHOLDS:
        row[f"jaccard_F>{t}"] = wf.jaccard(m, f > t)
    row["jaccard_area_matched"] = wf.jaccard(m, top)
    return row


def trace_both(ws: Path, top: np.ndarray, aquifer_rtol: float = AQUIFER_RTOL_NETWORK) -> tuple:
    """Trace the priority wells with streams as cells and as nodes; return F maps and a row."""
    t0 = time.perf_counter()
    step = gs.read_step(ws, boundnames=True)
    res = gs.backward(step, wf.well_groups(step))
    net = gs.read_network(ws, package_nodes=("SFR",), boundnames=True, aquifer_rtol=aquifer_rtol)
    res_net = gs.backward(net, wf.well_groups(net))
    n = step.n_cells
    maps = {
        "cells": figures.top_map(res.fraction_through[GROUP][:n], top).astype(np.float32),
        "network": figures.top_map(res_net.fraction_through[GROUP][:n], top).astype(np.float32),
    }
    row = {"trace_seconds": time.perf_counter() - t0, "inflow": res.destination_inflow[GROUP]}
    for label, (s, r) in {"cells": (step, res), "network": (net, res_net)}.items():
        check = gs.diagnostics.backward_closure(s, r, GROUP)
        row[f"closure_{label}"] = check.error
        row[f"cycles_{label}"] = len(r.cycles)
        for pkg, v in r.volume_from_by_term[GROUP].items():
            row[f"{label}:{pkg}"] = float(v.sum())
    return maps, row


def run_realisation(real: str, ens_dir: Path, mask_index: int | None) -> dict:
    """Write, run and trace one realisation; save its F maps and summary; delete the workspace."""
    iface, exe, top, starts = (_WORKER[k] for k in ("iface", "exe", "top", "starts"))
    ws = ens_dir / "ws" / real
    t0 = time.perf_counter()
    pr.write_realisation(real, ws, iface=iface, npf_options=())
    row = {"real": real, "mask_index": mask_index, "write_seconds": time.perf_counter() - t0}
    row["mf6_seconds"] = wf.run_mf6(ws, exe)
    maps, trace_row = trace_both(ws, top)
    row.update(trace_row)
    if mask_index is not None:
        mask = read_mask(mask_index)
        for label, f_top in maps.items():
            row.update({f"{label}:{k}": v for k, v in compare_one(f_top, mask, starts).items()})
    np.savez_compressed(ens_dir / "fractions" / f"{real}.npz", **maps)
    (ens_dir / "summary" / f"{real}.json").write_text(json.dumps(row))
    shutil.rmtree(ws)
    return row


def init_worker(pest_dir: Path) -> None:
    """Load the interface, executable and grid once per worker process."""
    idomain = wf.grid_idomain(wf.OUT / "optimal")
    _WORKER["iface"] = pr.load_interface(pest_dir)
    _WORKER["exe"] = wf.mf6_exe()
    _WORKER["top"] = figures.top_active(idomain)
    _WORKER["starts"] = start_cells(*idomain.shape[1:])


def pending_realisations(ens_dir: Path, pest_dir: Path = pr.PEST_DIR) -> list[str]:
    """Return the realisations of modpath_par_ens.csv without a summary file, in table order."""
    names = pd.read_csv(pest_dir / "modpath_par_ens.csv", usecols=[0], dtype=str).iloc[:, 0]
    return [n for n in names if not (ens_dir / "summary" / f"{n}.json").is_file()]


def run_ensemble(
    ens_dir: Path = ENS_DIR,
    n_workers: int = N_WORKERS,
    threads: int = THREADS_PER_WORKER,
    reals: list[str] | None = None,
) -> None:
    """Run the pending realisations in a process pool; failures are logged, not raised."""
    for sub in ("ws", "fractions", "summary"):
        (ens_dir / sub).mkdir(parents=True, exist_ok=True)
    reals = pending_realisations(ens_dir) if reals is None else reals
    indices = mask_indices()
    log = ens_dir / "failures.log"
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = str(threads)  # inherited by the workers before they import numpy
    t0 = time.perf_counter()
    with ProcessPoolExecutor(n_workers, initializer=init_worker, initargs=(pr.PEST_DIR,)) as pool:
        jobs = {pool.submit(run_realisation, r, ens_dir, indices.get(r)): r for r in reals}
        for k, job in enumerate(as_completed(jobs), start=1):
            real = jobs[job]
            try:
                job.result()
            except Exception as err:  # keep the pool running; the realisation stays pending
                with log.open("a") as f:
                    f.write(f"{real}: {type(err).__name__}: {err}\n")
            minutes = (time.perf_counter() - t0) / 60
            print(f"{k}/{len(reals)} done ({real}), {minutes:.1f} min", flush=True)


def collect_summary(ens_dir: Path = ENS_DIR) -> pd.DataFrame:
    """Return the summary rows of every finished realisation."""
    rows = [json.loads(p.read_text()) for p in sorted((ens_dir / "summary").glob("*.json"))]
    return pd.DataFrame(rows)


def probability_maps(ens_dir: Path, summary: pd.DataFrame, shape: tuple) -> dict[str, np.ndarray]:
    """Return the published probability and gwsource's share of F > t and mean F (357 masks)."""
    reals = summary.dropna(subset=["mask_index"])
    maps = {"mp7": np.zeros(shape)}
    for label in ("cells", "network"):
        maps[f"{label}:mean_F"] = np.zeros(shape)
        for t in THRESHOLDS:
            maps[f"{label}:P(F>{t})"] = np.zeros(shape)
    for _, r in reals.iterrows():
        maps["mp7"] += read_mask(int(r["mask_index"]))
        fractions = np.load(ens_dir / "fractions" / f"{r['real']}.npz")
        for label in ("cells", "network"):
            f = np.nan_to_num(fractions[label])
            maps[f"{label}:mean_F"] += f
            for t in THRESHOLDS:
                maps[f"{label}:P(F>{t})"] += f > t
    return {k: v / len(reals) for k, v in maps.items()}


def compare_probability(maps: dict, starts: np.ndarray) -> pd.DataFrame:
    """Compare each gwsource probability map with the published one on the start cells."""
    p = maps["mp7"].ravel()[starts]
    rows = []
    for name, m in maps.items():
        if name == "mp7":
            continue
        q = m.ravel()[starts]
        rows.append(
            {
                "map": name,
                "mean_abs_diff": float(np.abs(q - p).mean()),
                "sum_ratio": float(q.sum() / p.sum()),
                "correlation": float(np.corrcoef(p, q)[0, 1]),
                "jaccard_P>0.5": wf.jaccard(p > 0.5, q > 0.5),
                "jaccard_P>0.1": wf.jaccard(p > 0.1, q > 0.1),
            }
        )
    return pd.DataFrame(rows)


def main(run: bool = True, analyse: bool = True, ens_dir: Path = ENS_DIR) -> None:
    """Run the ensemble, then compare it with the published Monte Carlo results."""
    if run:
        run_ensemble(ens_dir)
        if not pending_realisations(ens_dir):
            (ens_dir / "DONE").write_text("all realisations finished\n")
    if analyse:
        summary = collect_summary(ens_dir)
        summary.to_csv(ens_dir / "summary.csv", index=False)
        idomain = wf.grid_idomain(wf.OUT / "optimal")
        maps = probability_maps(ens_dir, summary, idomain.shape[1:])
        np.savez_compressed(ens_dir / "probability_maps.npz", **maps)
        starts = start_cells(*idomain.shape[1:])
        compare_probability(maps, starts).to_csv(ens_dir / "probability_comparison.csv", index=False)


if __name__ == "__main__":
    main()
