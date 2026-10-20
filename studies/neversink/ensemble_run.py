"""Neversink case study: the 358-realisation Monte Carlo ensemble and the pumping scenarios.

Every realisation of the rebuilt ensemble (pest_rebuild.py) is written, run with MF6 and traced
backward from the eight priority wells twice: with streams as cells, and with the SFR reaches
as package nodes. The published solver criterion is kept; under it the GWF and SFR budgets agree
on the aquifer exchange less closely than the default network check asks, so the stream network
is read with a looser tolerance (AQUIFER_RTOL_NETWORK).
Per realisation the F of the uppermost active layer is kept (both traces) with a summary row;
the workspace is deleted.

The published masks (output/modpath_mc/{qrat}.zip) are stored one row south of their cells, and
mask k belongs to run pest_rebuild.mask_run_order()[k], run r being row r of modpath_par_ens.csv
(mc_masks.py tests both). read_mask moves a mask back onto its cells and
mask_indices gives each realisation its own mask; every comparison here uses both. Per
realisation, F is compared with its own mask (the mask columns of the summaries, recomputed from
the saved F maps by analyse). Per ensemble, the published probability (the share of the 357
masks in which a cell contributes) is compared with the share of realisations in which F exceeds
a threshold and with the mean F, and the contributing areas (and the wells' source split) per
pumping scenario.

Run from anywhere with the project environment; the realisations run in N_WORKERS processes
(this needs a process pool; some restricted environments forbid one):

    python studies/neversink/ensemble_run.py

The scenario part runs the five other published pumping scenarios (scenarios.py, the realisation's own
priority-well multiplier kept) on N_SUBSET realisations at rows evenly spread over the 357 runs
with a mask (357: all of them), and compares each with its scenario's masks; the base-rate
results are also analysed on that subset.

Edit the gates in __main__ to rerun parts. The runs are resumable: a realisation with a summary
file is skipped. Output goes to studies/neversink/output/ensemble/ and .../scenarios/<qrat>/
(git-ignored; main takes other folders, and base_out sends the base-rate tables elsewhere
without rerunning the base ensemble).
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
import scenarios as sc  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

ENS_DIR = wf.OUT / "ensemble"
SCENARIO_DIR = wf.OUT / "scenarios"
SCENARIOS = ("0.25rat", "0.5rat", "0.75rat", "maxrat", "maxrange")
N_SUBSET = 357  # realisations per pumping scenario, rows evenly spread over the 357 runs (357: all)
MASK_ZIP = wf.SOURCE / "output" / "modpath_mc" / "{qrat}.zip"
MASK_ROW_OFFSET = 1  # the published masks are stored this many rows south of their cells
N_WORKERS = 6
THREADS_PER_WORKER = 2
AQUIFER_RTOL_NETWORK = 1e-3
THRESHOLDS = (0.1, 0.5)
GROUP = "priority"

_WORKER = {}  # per-process state set by the pool initializer (interface, exe, start cells)


def shift_rows(grid: np.ndarray, rows: int) -> np.ndarray:
    """Return a (..., nrow, ncol) grid moved by rows (positive: south), without wrapping."""
    out = np.zeros_like(grid)
    if rows >= 0:
        out[..., rows:, :] = grid[..., : grid.shape[-2] - rows, :]
    else:
        out[..., :rows, :] = grid[..., -rows:, :]
    return out


def read_mask(index: int, qrat: str = "baserat", corrected: bool = True) -> np.ndarray:
    """Return published mask number index of a scenario as a (nrow, ncol) boolean grid.

    corrected=True moves it MASK_ROW_OFFSET rows north onto its cells; False returns it as stored.
    """
    with zipfile.ZipFile(str(MASK_ZIP).format(qrat=qrat)) as z:
        with z.open(f"{qrat}/{qrat}_real{index}.dat") as f:
            raw = np.loadtxt(io.TextIOWrapper(f)) > 0.5
    if not corrected:
        return raw
    assert not raw[:MASK_ROW_OFFSET].any(), f"{qrat} mask {index} has cells in its first rows"
    return shift_rows(raw, -MASK_ROW_OFFSET)


def mask_table(pest_dir: Path = pr.PEST_DIR) -> pd.DataFrame:
    """Return per realisation its run index (row of modpath_par_ens.csv) and mask index (-1: none)."""
    return pr.mask_index_table(all_realisations(pest_dir))


def mask_indices(pest_dir: Path = pr.PEST_DIR) -> dict[str, int]:
    """Return {realisation name: its published mask index}; 'base' has no mask."""
    table = mask_table(pest_dir)
    table = table[table["mask_index"] >= 0]
    return dict(zip(table["real_name"], table["mask_index"].astype(int)))


def run_indices(pest_dir: Path = pr.PEST_DIR) -> dict[str, int]:
    """Return {realisation name: run index}, the row of modpath_par_ens.csv ('base' included)."""
    table = mask_table(pest_dir)
    return dict(zip(table["real_name"], table["run_index"].astype(int)))


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


def trace_pair(ws: Path, aquifer_rtol: float = AQUIFER_RTOL_NETWORK) -> dict[str, tuple]:
    """Trace the wells with streams as cells and as nodes: {label: (step, result)}."""
    step = gs.read_step(ws, boundnames=True)
    net = gs.read_network(ws, package_nodes=("SFR",), boundnames=True, aquifer_rtol=aquifer_rtol)
    return {
        "cells": (step, gs.backward(step, wf.well_groups(step))),
        "network": (net, gs.backward(net, wf.well_groups(net))),
    }


def trace_maps(traces: dict[str, tuple], top: np.ndarray) -> dict[str, np.ndarray]:
    """Return F of the uppermost active layer of both traces (float32)."""
    n = traces["cells"][0].n_cells
    return {
        label: figures.top_map(r.fraction_through[GROUP][:n], top).astype(np.float32)
        for label, (_, r) in traces.items()
    }


def trace_row(traces: dict[str, tuple]) -> dict:
    """Return the inflow, closure, cycles and volumes by source package of both traces."""
    row = {"inflow": traces["cells"][1].destination_inflow[GROUP]}
    for label, (s, r) in traces.items():
        check = gs.diagnostics.backward_closure(s, r, GROUP)
        row[f"closure_{label}"] = check.error
        row[f"cycles_{label}"] = len(r.cycles)
        for pkg, v in r.volume_from_by_term[GROUP].items():
            row[f"{label}:{pkg}"] = float(v.sum())
    return row


def trace_both(ws: Path, top: np.ndarray, aquifer_rtol: float = AQUIFER_RTOL_NETWORK) -> tuple:
    """Trace the priority wells with streams as cells and as nodes; return F maps and a row."""
    t0 = time.perf_counter()
    traces = trace_pair(ws, aquifer_rtol)
    maps = trace_maps(traces, top)
    row = {"trace_seconds": time.perf_counter() - t0, **trace_row(traces)}
    return maps, row


def realisation_pars(real: str, run_index: int, qrat: str) -> pd.Series | None:
    """Return the parameters of a realisation under a pumping scenario (None: as published).

    run_index (the row of modpath_par_ens.csv) seeds the maxrange draw.
    """
    if qrat == "baserat":
        return None
    return sc.scenario_pars(pr.realisation_pars(real), qrat, run_index)


def run_realisation(
    real: str, ens_dir: Path, run_index: int, mask_index: int | None, qrat: str = "baserat"
) -> dict:
    """Write, run and trace one realisation; save its F maps and summary; delete the workspace."""
    iface, exe, top, starts = (_WORKER[k] for k in ("iface", "exe", "top", "starts"))
    ws = ens_dir / "ws" / real
    t0 = time.perf_counter()
    pars = realisation_pars(real, run_index, qrat)
    pr.write_realisation(real, ws, pars=pars, iface=iface, npf_options=())
    row = {"real": real, "qrat": qrat, "run_index": run_index, "mask_index": mask_index}
    row["write_seconds"] = time.perf_counter() - t0
    row["mf6_seconds"] = wf.run_mf6(ws, exe)
    maps, trace_row = trace_both(ws, top)
    row.update(trace_row)
    if mask_index is not None:
        mask = read_mask(mask_index, qrat)
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


def all_realisations(pest_dir: Path = pr.PEST_DIR) -> list[str]:
    """Return the realisation names of modpath_par_ens.csv in table order."""
    return list(pd.read_csv(pest_dir / "modpath_par_ens.csv", usecols=[0], dtype=str).iloc[:, 0])


def scenario_subset(n: int = N_SUBSET, n_runs: int = pr.N_MASKS) -> list[str]:
    """Return n realisations at rows of modpath_par_ens.csv evenly spread over 0 .. n_runs - 1.

    Rows 0 .. 356 are the runs with a published mask (n = 357: all of them). The sample is
    defined by table row, not by mask index, so it does not depend on how the masks are paired
    with the realisations.
    """
    rows = np.unique(np.linspace(0, n_runs - 1, n).round().astype(int))
    names = all_realisations()
    return [names[i] for i in rows]


def pending_realisations(ens_dir: Path, reals: list[str] | None = None) -> list[str]:
    """Return the realisations (default: all) without a summary file, in the given order."""
    reals = all_realisations() if reals is None else reals
    return [n for n in reals if not (ens_dir / "summary" / f"{n}.json").is_file()]


def run_ensemble(
    ens_dir: Path = ENS_DIR,
    n_workers: int = N_WORKERS,
    threads: int = THREADS_PER_WORKER,
    reals: list[str] | None = None,
    qrat: str = "baserat",
) -> None:
    """Run the pending realisations (default: all) in a process pool; failures are logged."""
    for sub in ("ws", "fractions", "summary"):
        (ens_dir / sub).mkdir(parents=True, exist_ok=True)
    reals = pending_realisations(ens_dir, reals)
    runs, masks = run_indices(), mask_indices()
    log = ens_dir / "failures.log"
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = str(threads)  # inherited by the workers before they import numpy
    t0 = time.perf_counter()
    with ProcessPoolExecutor(n_workers, initializer=init_worker, initargs=(pr.PEST_DIR,)) as pool:
        jobs = {
            pool.submit(run_realisation, r, ens_dir, runs[r], masks.get(r), qrat): r for r in reals
        }
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


def published_probability(
    qrat: str = "baserat", n_masks: int = pr.N_MASKS, corrected: bool = True
) -> np.ndarray:
    """Return the published probability: the share of a scenario's masks in which a cell contributes."""
    total = sum(read_mask(i, qrat, corrected).astype(float) for i in range(n_masks))
    return total / n_masks


def published_areas(qrat: str, starts: np.ndarray, n_masks: int = pr.N_MASKS) -> np.ndarray:
    """Return the number of contributing start cells of every published mask of a scenario."""
    return np.array([read_mask(i, qrat).ravel()[starts].sum() for i in range(n_masks)])


def probability_maps(
    ens_dir: Path, summary: pd.DataFrame, shape: tuple, qrat: str = "baserat"
) -> dict[str, np.ndarray]:
    """Return the published probability (all masks) and gwsource's share of F > t and mean F.

    The published map uses all (corrected) masks of the scenario and the gwsource maps all
    realisations of summary.
    """
    maps = {"mp7": published_probability(qrat)}
    for label in ("cells", "network"):
        maps[f"{label}:mean_F"] = np.zeros(shape)
        for t in THRESHOLDS:
            maps[f"{label}:P(F>{t})"] = np.zeros(shape)
    for real in summary["real"]:
        fractions = np.load(ens_dir / "fractions" / f"{real}.npz")
        for label in ("cells", "network"):
            f = np.nan_to_num(fractions[label])
            maps[f"{label}:mean_F"] += f
            for t in THRESHOLDS:
                maps[f"{label}:P(F>{t})"] += f > t
    n = len(summary)
    return {k: (v if k == "mp7" else v / n) for k, v in maps.items()}


def scenario_dir_of(qrat: str, ens_dir: Path = ENS_DIR, scenario_dir: Path = SCENARIO_DIR) -> Path:
    """Return the folder of a scenario's runs: the base ensemble or scenario_dir / qrat."""
    return ens_dir if qrat == "baserat" else scenario_dir / qrat


def area_table(
    scenarios: tuple[str, ...] = ("baserat", *SCENARIOS),
    ens_dir: Path = ENS_DIR,
    scenario_dir: Path = SCENARIO_DIR,
) -> pd.DataFrame:
    """Return per scenario the median contributing area, published (all masks) and gwsource.

    The published area is the number of (corrected) mask cells on the start cells; gwsource's is
    the sum of F over the start cells (cells only and with the stream network); growth is
    relative to the base rate.
    """
    starts = start_cells(680, 619)
    rows = []
    for qrat in scenarios:
        summary = collect_summary(scenario_dir_of(qrat, ens_dir, scenario_dir))
        rows.append(
            {
                "qrat": qrat,
                "n_reals": len(summary),
                "inflow": summary["inflow"].median(),
                "published_cells": float(np.median(published_areas(qrat, starts))),
                "cells_expected": summary["cells:expected_cells"].median(),
                "network_expected": summary["network:expected_cells"].median(),
            }
        )
    table = pd.DataFrame(rows)
    for col in ("inflow", "published_cells", "cells_expected", "network_expected"):
        table[f"{col}_growth"] = table[col] / table.loc[0, col]
    return table


def source_table(
    scenarios: tuple[str, ...] = ("baserat", *SCENARIOS),
    ens_dir: Path = ENS_DIR,
    scenario_dir: Path = SCENARIO_DIR,
) -> pd.DataFrame:
    """Return per scenario the median source split of the wells' water, streams as cells.

    rch and sfr are the volumes from recharge and from stream leakage (m3/d); the stream share
    is sfr / inflow per realisation. area_per_rch is the sum of F over the start cells per m3/d
    of recharge. Growth is relative to the base rate.
    """
    rows = []
    for qrat in scenarios:
        summary = collect_summary(scenario_dir_of(qrat, ens_dir, scenario_dir))
        share = summary["cells:SFR_0"] / summary["inflow"]
        rows.append(
            {
                "qrat": qrat,
                "n_reals": len(summary),
                "inflow": summary["inflow"].median(),
                "rch": summary["cells:RCHA"].median(),
                "sfr": summary["cells:SFR_0"].median(),
                "stream_share": share.median(),
                "stream_share_min": share.min(),
                "stream_share_max": share.max(),
                "area_per_rch": (summary["cells:expected_cells"] / summary["cells:RCHA"]).median(),
            }
        )
    table = pd.DataFrame(rows)
    for col in ("inflow", "rch", "sfr"):
        table[f"{col}_growth"] = table[col] / table.loc[0, col]
    return table


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


def own_mask_columns(
    ens_dir: Path, summary: pd.DataFrame, qrat: str, starts: np.ndarray
) -> pd.DataFrame:
    """Return the summary with every realisation's F maps compared with its own corrected mask.

    The mask columns are recomputed from the saved F maps with read_mask and mask_indices, so
    they do not rely on the mask columns stored in the summary files. Realisations without a
    mask get NaN.
    """
    runs, masks = run_indices(), mask_indices()
    rows = []
    for real in summary["real"]:
        row = {"real": real, "run_index": runs[real], "mask_index": masks.get(real, -1)}
        if real in masks:
            mask = read_mask(masks[real], qrat)
            fractions = np.load(ens_dir / "fractions" / f"{real}.npz")
            for label in ("cells", "network"):
                compared = compare_one(fractions[label], mask, starts)
                row.update({f"{label}:{k}": v for k, v in compared.items()})
        rows.append(row)
    own = pd.DataFrame(rows).set_index("real")
    out = summary.set_index("real")
    out = out.drop(columns=[c for c in own.columns if c in out.columns])
    return out.join(own).reset_index()


def analyse(
    ens_dir: Path,
    qrat: str = "baserat",
    reals: list[str] | None = None,
    tag: str = "",
    out_dir: Path | None = None,
) -> None:
    """Write the summary, probability maps and their comparison for finished realisations.

    reals restricts the analysis (e.g. to the scenario subset); tag is added to the file names;
    the tables go to out_dir (default: ens_dir).
    """
    out_dir = ens_dir if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    idomain = wf.grid_idomain(wf.OUT / "optimal")
    starts = start_cells(*idomain.shape[1:])
    summary = collect_summary(ens_dir)
    if reals is not None:
        summary = summary[summary["real"].isin(reals)]
    summary = own_mask_columns(ens_dir, summary, qrat, starts)
    summary.to_csv(out_dir / f"summary{tag}.csv", index=False)
    maps = probability_maps(ens_dir, summary, idomain.shape[1:], qrat)
    np.savez_compressed(out_dir / f"probability_maps{tag}.npz", **maps)
    table = compare_probability(maps, starts).assign(qrat=qrat, n_reals=len(summary))
    table.to_csv(out_dir / f"probability_comparison{tag}.csv", index=False)


def main(
    run_base: bool = True,
    analyse_base: bool = True,
    run_scenarios: bool = True,
    analyse_scenarios: bool = True,
    make_figures: bool = True,
    scenarios: tuple[str, ...] = SCENARIOS,
    n_subset: int = N_SUBSET,
    ens_dir: Path = ENS_DIR,
    base_out: Path | None = None,
    scenario_dir: Path = SCENARIO_DIR,
    fig_dir: Path = wf.FIG_DIR,
) -> None:
    """Run and analyse the base-rate ensemble, then the pumping scenarios on a subset.

    ens_dir holds the base-rate runs; base_out (default ens_dir) receives their tables, so the
    base ensemble can be reanalysed into another folder without rerunning it.
    """
    subset = scenario_subset(n_subset)
    base_out = ens_dir if base_out is None else base_out
    if run_base:
        run_ensemble(ens_dir)
        if not pending_realisations(ens_dir):
            (ens_dir / "DONE").write_text("all realisations finished\n")
    if analyse_base:
        analyse(ens_dir, out_dir=base_out)
        analyse(ens_dir, reals=subset, tag="_subset", out_dir=base_out)
    for qrat in scenarios:
        if run_scenarios:
            run_ensemble(scenario_dir / qrat, reals=subset, qrat=qrat)
        if analyse_scenarios:
            analyse(scenario_dir / qrat, qrat)
    if analyse_scenarios:
        qrats = ("baserat", *scenarios)
        area_table(qrats, ens_dir, scenario_dir).to_csv(scenario_dir / "area_table.csv", index=False)
        source_table(qrats, ens_dir, scenario_dir).to_csv(scenario_dir / "source_table.csv", index=False)
    if make_figures:
        maps = dict(np.load(base_out / "probability_maps.npz"))
        idomain = wf.grid_idomain(wf.OUT / "optimal")
        fig_dir.mkdir(parents=True, exist_ok=True)
        figures.probability_maps(maps, fig_dir, idomain, wf.PRIORITY_WELLS)
        figures.area_growth(pd.read_csv(scenario_dir / "area_table.csv"), fig_dir)


if __name__ == "__main__":
    main()
