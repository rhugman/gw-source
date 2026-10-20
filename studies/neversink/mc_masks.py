"""Neversink case study: which flow fields the published Monte Carlo masks come from.

The 6 x 357 published masks (output/modpath_mc/{qrat}.zip, {qrat}_real{k}.dat) do not line up
with the rebuilt realisations when mask k is taken to be realisation k on its stored grid. This
script tests two bookkeeping steps of the published pipeline that would explain it, keeping the
rebuilt flow fields as they are.

1. Row offset. scripts/get_endpoints.py converts the start coordinates of the captured
   particles to rows with i = nrow - (y0 - 25) / 50, which is the 1-based row of a cell centre;
   a mask grid indexed with it as a 0-based row is shifted one row south. mask_offsets and
   calibrated_offsets test this: whether row 0 is empty in every mask (a 1-based row is never
   0), how many published cells lie on a start cell for each trial offset, and which offset
   makes the published mask of the calibrated model (from its end-point files) agree best with
   the Monte Carlo masks.
2. Pairing. scripts/modpath_mc_varq.py zips run r (row r of the scenario's parameter table,
   modpath_par_ens.csv order) as mp_results_{r}_{qrat}.zip. If the masks are numbered in the
   order of those names sorted as text, where '_' sorts after the digits ('100_' before '10_'),
   mask k is run pest_rebuild.mask_run_order()[k]. Runs 0..356 have masks; run 357, the base
   realisation, has none. The postprocessing that wrote the .dat files is not archived, so the
   order is tested against the R1 matches below rather than read from code.

Both corrections live in ensemble_run: read_mask returns a mask moved back onto its cells
(corrected=False: as stored, used here for the offset test) and mask_indices / run_indices give
the pairing (pest_rebuild.mask_run_order). r1_matches and pairing_check compare the R1 masks of
growth_mechanisms (PRT with the published conventions on the rebuilt flow fields, 60
realisations) with every published mask, to check that each matches its paired mask best. The
per-realisation comparisons of full mixing with its own mask are here (paired_comparison,
region_areas); probability_comparison sets the published probability from the masks as stored
against the corrected one.

Scenario well multipliers. run_multiplier_test reruns six paired realisations with R1 only,
with the realisation's own priority-well multiplier kept and replaced; multiplier_table gives
each case's Jaccard index with its paired mask and with the best mask. Kept,
q = m (q_base + f (q_max - q_base)), is the default of scenarios.scenario_pars.

Run with the project environment; run_multiplier_test needs a process pool (some restricted
environments forbid one):

    python studies/neversink/mc_masks.py

Output goes to studies/neversink/output/mc_masks/ (git-ignored).
"""

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

import ensemble_run as er  # noqa: E402
import figures  # noqa: E402
import growth_mechanisms as gm  # noqa: E402
import mp7_convention as mp7  # noqa: E402
import pest_rebuild as pr  # noqa: E402
import scenarios as sc  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

OUT_DIR = wf.OUT / "mc_masks"
MECH_DIR = wf.OUT / "scenarios" / "mechanisms60"
N_RUNS = pr.N_MASKS  # runs with a published mask (rows 0..356 of modpath_par_ens.csv)
NROW, NCOL = 680, 619
OFFSETS = tuple((di, dj) for di in (-1, 0, 1, 2) for dj in (-1, 0, 1))
MULT_REALS = ("8", "130", "241", "324", "412", "498")  # spread over the masks; in mechanisms60
MULT_QRATS = ("baserat", "maxrat")
N_WORKERS = 6
THREADS_PER_WORKER = 2
GROUP = er.GROUP

_WORKER = {}  # per-process state set by the pool initializer


# ---------------------------------------------------------------- masks and pairing


def shift_grid(grid: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Return a (..., nrow, ncol) grid moved by rows (south) and cols (east), without wrapping."""
    moved = er.shift_rows(grid, rows)
    return np.swapaxes(er.shift_rows(np.swapaxes(moved, -1, -2), cols), -1, -2)


def raw_masks(qrat: str, n_masks: int = N_RUNS) -> np.ndarray:
    """Return all published masks of a scenario as stored, (n_masks, nrow, ncol) boolean."""
    return np.array([er.read_mask(i, qrat, corrected=False) for i in range(n_masks)])


def mask_pairing(pest_dir: Path = pr.PEST_DIR) -> pd.DataFrame:
    """Return per published mask (in mask order) its run index and realisation name."""
    table = er.mask_table(pest_dir)
    table = table[table["mask_index"] >= 0].sort_values("mask_index").reset_index(drop=True)
    return table[["mask_index", "run_index", "real_name"]]


def mask_of_real(pairing: pd.DataFrame) -> dict[str, int]:
    """Return {realisation name: published mask index} from a pairing table."""
    return dict(zip(pairing["real_name"], pairing["mask_index"]))


# ---------------------------------------------------------------- evidence for the offset


def start_support(starts: pd.DataFrame, nrow: int = NROW, ncol: int = NCOL) -> np.ndarray:
    """Return the (nrow, ncol) cells where a published particle starts."""
    grid = np.zeros(nrow * ncol, dtype=bool)
    grid[starts["node0"].to_numpy() % (nrow * ncol)] = True
    return grid.reshape(nrow, ncol)


def calibrated_grid(starts: pd.DataFrame, nrow: int = NROW, ncol: int = NCOL) -> np.ndarray:
    """Return the published mask of the calibrated model (its end-point files) as a grid."""
    captured = wf.mp7_mask(starts, list(wf.PRIORITY_WELLS.values()))
    grid = np.zeros(nrow * ncol, dtype=bool)
    grid[starts["node0"].to_numpy()[captured] % (nrow * ncol)] = True
    return grid.reshape(nrow, ncol)


def grid_jaccards(masks: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Return the Jaccard index of every mask of (n, nrow, ncol) with one grid."""
    union = (masks | grid).sum(axis=(1, 2))
    return (masks & grid).sum(axis=(1, 2)) / np.maximum(union, 1)


def mask_offsets(qrat: str, masks: np.ndarray, support: np.ndarray, offsets=OFFSETS) -> pd.DataFrame:
    """Return per offset of the start cells the number of published cells off them."""
    rows = []
    for di, dj in offsets:
        off = masks & ~shift_grid(support, di, dj)[None]
        rows.append(
            {"qrat": qrat, "rows_south": di, "cols_east": dj, "cells_off_starts": int(off.sum()),
             "masks_with_cells_off": int(off.any(axis=(1, 2)).sum()),
             "cells_in_row_0": int(masks[:, 0].sum())}
        )
    return pd.DataFrame(rows)


def calibrated_offsets(masks: np.ndarray, calibrated: np.ndarray, offsets=OFFSETS) -> pd.DataFrame:
    """Return per offset of the calibrated mask its best and median Jaccard with the masks."""
    rows = []
    for di, dj in offsets:
        jac = grid_jaccards(masks, shift_grid(calibrated, di, dj))
        rows.append(
            {"rows_south": di, "cols_east": dj, "best_jaccard": float(jac.max()),
             "best_mask": int(jac.argmax()), "median_jaccard": float(np.median(jac))}
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- R1 against the masks


def corrected_matrix(qrat: str, plan: np.ndarray, n_masks: int = N_RUNS) -> np.ndarray:
    """Return the corrected masks of a scenario on the start cells, (n_masks, n_starts)."""
    return np.array([er.read_mask(i, qrat).ravel()[plan] for i in range(n_masks)])


def match_row(r1: np.ndarray, masks: np.ndarray, paired: int) -> dict:
    """Return the best, second and paired Jaccard of one R1 mask against a mask matrix."""
    union = (masks | r1).sum(axis=1)
    jac = (masks & r1).sum(axis=1) / np.maximum(union, 1)
    order = np.argsort(-jac)
    row = {"r1_cells": int(r1.sum()), "best_mask": int(order[0]), "best_jaccard": float(jac[order[0]])}
    row.update(second_jaccard=float(jac[order[1]]), median_jaccard=float(np.median(jac)))
    row.update(paired_mask=paired, paired_jaccard=float(jac[paired]) if paired >= 0 else np.nan)
    return row


def r1_matches(
    reals: list[str], qrats: tuple[str, ...], pairing: pd.DataFrame, plan: np.ndarray,
    mech_dir: Path = MECH_DIR,
) -> pd.DataFrame:
    """Return per growth_mechanisms case the best corrected mask and the paired one."""
    paired = mask_of_real(pairing)
    rows = []
    for qrat in qrats:
        masks = corrected_matrix(qrat, plan)
        for real in reals:
            r1 = np.load(mech_dir / "starts" / f"{gm.case_name(real, qrat)}.npz")["r1"]
            row = {"real": real, "qrat": qrat, **match_row(r1, masks, paired.get(real, -1))}
            rows.append(row)
    return pd.DataFrame(rows)


def pairing_check(matches: pd.DataFrame) -> pd.DataFrame:
    """Return per scenario how many best matches are the paired mask, and the Jaccard spread."""
    paired = matches[matches["paired_mask"] >= 0]
    return paired.groupby("qrat").apply(
        lambda g: pd.Series(
            {"cases": len(g), "best_is_paired": int((g["best_mask"] == g["paired_mask"]).sum()),
             "paired_min": g["paired_jaccard"].min(), "paired_median": g["paired_jaccard"].median(),
             "second_median": g["second_jaccard"].median(), "second_max": g["second_jaccard"].max()}
        ),
        include_groups=False,
    ).reset_index()


# ---------------------------------------------------------------- full mixing, paired


def fraction_matrix(ens_dir: Path, reals: list[str], plan: np.ndarray, label: str = "cells") -> np.ndarray:
    """Return F (uppermost active layer) of the realisations on the start cells, (n, n_starts)."""
    return np.array(
        [np.nan_to_num(np.load(ens_dir / "fractions" / f"{r}.npz")[label]).ravel()[plan] for r in reals]
    )


def area_matched_jaccard(f: np.ndarray, mask: np.ndarray) -> float:
    """Return the Jaccard index of a mask with the same number of cells of highest F."""
    top = np.zeros(len(f), dtype=bool)
    top[np.argsort(-f, kind="stable")[: mask.sum()]] = True
    return wf.jaccard(mask, top)


def correlation_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return the Pearson correlation of every row of a with every row of b."""
    za = (a - a.mean(axis=1, keepdims=True)) / a.std(axis=1, keepdims=True)
    zb = (b - b.mean(axis=1, keepdims=True)) / b.std(axis=1, keepdims=True)
    return za @ zb.T / a.shape[1]


def paired_comparison(
    qrat: str, pairing: pd.DataFrame, starts: pd.DataFrame, plan: np.ndarray, ens_dir: Path
) -> tuple[pd.DataFrame, dict]:
    """Compare every corrected mask with F of its own realisation and of the others.

    Per mask: area-matched Jaccard with its own F and with the F of the next mask's realisation
    (a neighbour test), and the rank of its own realisation among all 357 by
    correlation. Summary: those counts and, per region, the correlation over the masks of the
    published area with the sum of F of the paired realisation.
    """
    masks = corrected_matrix(qrat, plan).astype(np.float32)
    f = fraction_matrix(ens_dir, list(pairing["real_name"]), plan).astype(np.float32)
    corr = correlation_matrix(masks, f)
    own = np.diag(corr)
    rank = (corr > own[:, None]).sum(axis=1) + 1
    nxt = np.roll(np.arange(len(masks)), -1)
    rows = []
    for k in range(len(masks)):
        m = masks[k] > 0.5
        rows.append(
            {"mask_index": k, "real_name": pairing["real_name"].iloc[k], "corr_own": float(own[k]),
             "corr_rank": int(rank[k]), "jaccard_own": area_matched_jaccard(f[k], m),
             "jaccard_next": area_matched_jaccard(f[nxt[k]], m)}
        )
    table = pd.DataFrame(rows)
    summary = {
        "qrat": qrat,
        "own_better_than_next": int((table["jaccard_own"] > table["jaccard_next"]).sum()),
        "jaccard_own_median": float(table["jaccard_own"].median()),
        "jaccard_next_median": float(table["jaccard_next"].median()),
        "corr_rank_1": int((table["corr_rank"] == 1).sum()),
        "corr_rank_median": float(table["corr_rank"].median()),
    }
    region = starts["region"].to_numpy()
    for name in np.unique(region):
        sel = region == name
        summary[f"area_corr_{name}"] = float(
            np.corrcoef(masks[:, sel].sum(axis=1), f[:, sel].sum(axis=1))[0, 1]
        )
    return table, summary


def region_areas(
    qrats: tuple[str, ...], pairing: pd.DataFrame, starts: pd.DataFrame, plan: np.ndarray,
    mech_dir: Path = MECH_DIR,
) -> pd.DataFrame:
    """Return per scenario and region the spread of the paired published areas and their
    correlation with the R1 area and the sum of F of the same realisation (growth_mechanisms)."""
    paired = mask_of_real(pairing)
    reals = [r for r in gm.sample_realisations(60) if r in paired]
    region = starts["region"].to_numpy()
    rows = []
    for qrat in qrats:
        masks = corrected_matrix(qrat, plan)
        cases = [np.load(mech_dir / "starts" / f"{gm.case_name(r, qrat)}.npz") for r in reals]
        for name in np.unique(region):
            sel = region == name
            pub = np.array([masks[paired[r]][sel].sum() for r in reals], dtype=float)
            r1 = np.array([c["r1"][sel].sum() for c in cases], dtype=float)
            f = np.array([c["f_start"][sel].sum() for c in cases], dtype=float)
            rows.append(
                {"qrat": qrat, "region": name, "cases": len(reals), "published_cv": pub.std() / pub.mean(),
                 "corr_published_r1": np.corrcoef(pub, r1)[0, 1], "corr_published_f": np.corrcoef(pub, f)[0, 1]}
            )
    return pd.DataFrame(rows)


def probability_comparison(qrat: str, maps_dir: Path, plan: np.ndarray) -> pd.DataFrame:
    """Repeat ensemble_run.compare_probability with the masks as stored and corrected.

    The gwsource maps are the saved ones of ensemble_run.analyse (all realisations run).
    """
    maps = dict(np.load(maps_dir / "probability_maps.npz"))
    rows = []
    for label, corrected in (("as stored", False), ("corrected", True)):
        published = er.published_probability(qrat, corrected=corrected)
        table = er.compare_probability({**maps, "mp7": published}, plan)
        rows.append(table.assign(qrat=qrat, published=label))
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- well multiplier test (R1 only)


def multiplier_pars(real: str, qrat: str, keep: bool, run_index: int) -> pd.Series:
    """Return a realisation's parameters under a scenario with its priority-well multiplier
    kept (keep=True) or replaced; at baserat, replaced means a multiplier of 1."""
    pars = pr.realisation_pars(real)
    fractions = np.zeros(len(sc.priority_well_table())) if qrat == "baserat" else None
    if qrat == "baserat" and keep:
        return pars
    return sc.scenario_pars(pars, qrat, run_index, fractions=fractions, keep_multiplier=keep)


def run_r1(ws: Path, starts: pd.DataFrame, exe: Path) -> np.ndarray:
    """Trace the priority wells and track the published starts with R1; return capture per start."""
    step = gs.read_step(ws, boundnames=True)
    result = gs.backward(step, wf.well_groups(step))
    budget = ws / f"{wf.MODEL}.cbc"
    draped, seed, _ = gm.seeded_starts(ws, budget, starts, result.fraction_through[GROUP])
    sim = mp7.write_mp7_prt(ws / "prt_r1", ws, budget, draped[seed].reset_index(drop=True), exe)
    ends = mp7.run_endpoints(sim, np.ones(int(seed.sum()), dtype=bool))
    captured = np.zeros(len(starts), dtype=bool)
    captured[seed] = np.isin(ends["cell"], np.flatnonzero(result.selections[GROUP].cells))
    return captured


def init_worker(pest_dir: Path) -> None:
    """Load the interface, executable and published starts once per worker process."""
    _WORKER["iface"] = pr.load_interface(pest_dir)
    _WORKER["exe"] = wf.mf6_exe()
    _WORKER["starts"] = wf.read_endpoints(columns=mp7.START_COLUMNS)


def multiplier_case(real: str, qrat: str, keep: bool, run_index: int, out: Path) -> dict:
    """Write, run and track one case of the multiplier test; save its R1 capture."""
    iface, exe, starts = (_WORKER[k] for k in ("iface", "exe", "starts"))
    name = f"{qrat}_{real}_{'kept' if keep else 'replaced'}"
    ws = out / "ws" / name
    pars = multiplier_pars(real, qrat, keep, run_index)
    pr.write_realisation(real, ws, pars=pars, iface=iface)
    mp7.add_iflowface(ws)
    row = {"real": real, "qrat": qrat, "multiplier": "kept" if keep else "replaced"}
    row["pumping"] = float(sc.scenario_rates(pars).sum())
    row["mf6_seconds"] = wf.run_mf6(ws, exe)
    t0 = time.perf_counter()
    np.save(out / "r1" / f"{name}.npy", run_r1(ws, starts, exe))
    row["r1_seconds"] = time.perf_counter() - t0
    (out / "summary" / f"{name}.json").write_text(json.dumps(row))
    shutil.rmtree(ws)
    return row


def run_multiplier_test(
    out: Path, reals: tuple[str, ...], qrats: tuple[str, ...], pairing: pd.DataFrame,
    n_workers: int = N_WORKERS, threads: int = THREADS_PER_WORKER,
) -> None:
    """Run the pending multiplier cases in a process pool; failures are logged."""
    for sub in ("ws", "r1", "summary"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    run_of = dict(zip(pairing["real_name"], pairing["run_index"]))
    cases = [(r, q, k) for q in qrats for r in reals for k in (False, True)]
    done = {p.stem for p in (out / "summary").glob("*.json")}
    cases = [c for c in cases if f"{c[1]}_{c[0]}_{'kept' if c[2] else 'replaced'}" not in done]
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = str(threads)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(n_workers, initializer=init_worker, initargs=(pr.PEST_DIR,)) as pool:
        jobs = {pool.submit(multiplier_case, r, q, k, run_of[r], out): (r, q, k) for r, q, k in cases}
        for n, job in enumerate(as_completed(jobs), start=1):
            try:
                job.result()
            except Exception as err:  # keep the pool running; the case stays pending
                with (out / "failures.log").open("a") as f:
                    f.write(f"{jobs[job]}: {type(err).__name__}: {err}\n")
            print(f"{n}/{len(cases)} done {jobs[job]}, {(time.perf_counter() - t0) / 60:.1f} min", flush=True)


def multiplier_table(out: Path, pairing: pd.DataFrame, plan: np.ndarray) -> pd.DataFrame:
    """Return per multiplier case the Jaccard index with its paired mask and the best mask."""
    paired = mask_of_real(pairing)
    rows = [json.loads(p.read_text()) for p in sorted((out / "summary").glob("*.json"))]
    masks = {}
    for row in rows:
        qrat = row["qrat"]
        if qrat not in masks:
            masks[qrat] = corrected_matrix(qrat, plan)
        r1 = np.load(out / "r1" / f"{qrat}_{row['real']}_{row['multiplier']}.npy")
        row.update(match_row(r1, masks[qrat], paired[row["real"]]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main


def evidence(out: Path, starts: pd.DataFrame, qrats: tuple[str, ...] = sc.QRATS) -> None:
    """Write the offset evidence: start-cell support per scenario and the calibrated mask."""
    support = start_support(starts)
    tables = [mask_offsets(q, raw_masks(q), support) for q in qrats]
    pd.concat(tables, ignore_index=True).to_csv(out / "mask_offsets.csv", index=False)
    cal = calibrated_offsets(raw_masks("baserat"), calibrated_grid(starts))
    cal.to_csv(out / "calibrated_offsets.csv", index=False)


def comparisons(
    out: Path, starts: pd.DataFrame, pairing: pd.DataFrame, plan: np.ndarray,
    mech_dir: Path = MECH_DIR, ens_dir: Path = er.ENS_DIR, base_maps: Path | None = None,
    scenario_dir: Path = er.SCENARIO_DIR,
) -> None:
    """Write the R1 matches, the paired full-mixing comparison and the probability tables.

    ens_dir and scenario_dir hold the base-rate ensemble and the scenario runs; base_maps (default ens_dir) the
    base-rate probability maps.
    """
    reals = gm.sample_realisations(60)
    matches = r1_matches(reals, gm.QRATS, pairing, plan, mech_dir)
    matches.to_csv(out / "r1_matches.csv", index=False)
    pairing_check(matches).to_csv(out / "pairing_check.csv", index=False)
    region_areas(gm.QRATS, pairing, starts, plan, mech_dir).to_csv(out / "region_areas.csv", index=False)
    summaries, probs = [], []
    for qrat in sc.QRATS:
        runs = er.scenario_dir_of(qrat, ens_dir, scenario_dir)
        table, summary = paired_comparison(qrat, pairing, starts, plan, runs)
        table.to_csv(out / f"paired_{qrat}.csv", index=False)
        summaries.append(summary)
        maps_dir = (base_maps or ens_dir) if qrat == "baserat" else runs
        probs.append(probability_comparison(qrat, maps_dir, plan))
    pd.DataFrame(summaries).to_csv(out / "paired_summary.csv", index=False)
    pd.concat(probs, ignore_index=True).to_csv(out / "probability_comparison.csv", index=False)


def main(
    write_evidence: bool = True,
    compare: bool = True,
    run_multiplier: bool = True,
    out: Path = OUT_DIR,
    mult_reals: tuple[str, ...] = MULT_REALS,
    mult_qrats: tuple[str, ...] = MULT_QRATS,
    mech_dir: Path = MECH_DIR,
    ens_dir: Path = er.ENS_DIR,
    base_maps: Path | None = None,
    scenario_dir: Path = er.SCENARIO_DIR,
) -> None:
    """Write the pairing, the offset evidence, the comparisons and the multiplier test."""
    out.mkdir(parents=True, exist_ok=True)
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)
    plan = starts["node0"].to_numpy() % (NROW * NCOL)
    pairing = mask_pairing()
    pairing.to_csv(out / "mask_pairing.csv", index=False)
    if write_evidence:
        evidence(out, starts)
    if compare:
        comparisons(out, starts, pairing, plan, mech_dir, ens_dir, base_maps, scenario_dir)
    if run_multiplier:
        run_multiplier_test(out, mult_reals, mult_qrats, pairing)
        multiplier_table(out, pairing, plan).to_csv(out / "multiplier_test.csv", index=False)


if __name__ == "__main__":
    main()
