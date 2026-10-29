"""Dispersion study: how much does full mixing spread capture zones, and how much of it
does face-to-face routing remove? Tutorial 11 (tutorials/11_numerical_dispersion) walks through
the same two test problems.

Run from anywhere with the project environment (MF6 is taken from <repo>/bin, Voronoi grids
come from vorflow):

    python studies/dispersion/workflow.py

Edit the gates in __main__ to rerun parts. Models and tables go to studies/dispersion/output/
(git-ignored); figures to studies/dispersion/output/figures/. The transient part reads the
particle arrivals saved by the problem B part. The rerun_disv_a gate reruns only problem A on
the Voronoi (DISV) grids, replaces their rows and maps in the saved outputs and adds the maps of
the finest DIS grid. Runtime on a 16-core laptop: about 6 minutes,
most of it the MF6 PRT run on the finest grid of problem B (about 94,000 particles).
"""

import json
import shutil
import sys
from dataclasses import replace
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMPORT_DIRS = (HERE, REPO / "studies" / "paper", REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import figures  # noqa: E402
import runs  # noqa: E402

OUT = HERE / "output"
FIG_DIR = OUT / "figures"
BIN = REPO / "bin"


def study_config(out: Path = OUT, bin_dir: Path = BIN) -> runs.StudyConfig:
    """Return the study configuration with the executables in bin_dir."""
    suffix = ".exe" if sys.platform.startswith("win") else ""
    mf6 = bin_dir / f"mf6{suffix}"
    assert mf6.is_file(), f"{mf6} not found; run python studies/setup_tools.py"
    return runs.StudyConfig(out=out, mf6_exe=mf6)


def save_maps(path: Path, maps: dict) -> None:
    """Save raster maps as float32 (booleans as 0/1)."""
    np.savez_compressed(path, **{k: np.asarray(v, dtype=np.float32) for k, v in maps.items()})


def replace_rows(path: Path, new: pd.DataFrame, kind: str = "DISV") -> None:
    """Replace the rows of one grid kind in a saved table with new rows (same columns)."""
    old = pd.read_csv(path)
    assert set(new.kind) == {kind}, f"new rows must all be {kind}"
    pd.concat([old[old.kind != kind], new[old.columns]], ignore_index=True).to_csv(path, index=False)


def replace_maps(path: Path, new: dict, kind: str = "DISV") -> None:
    """Replace the maps whose key holds kind + '_' in a saved map file with new ones."""
    tag = f"{kind}_"
    maps = {k: v for k, v in np.load(path).items() if tag not in k}
    maps.update({k: v for k, v in new.items() if tag in k})
    save_maps(path, maps)


def rerun_analytic_disv(config: runs.StudyConfig, out: Path = OUT) -> None:
    """Rerun problem A on the DISV grids and replace their rows and maps in the outputs."""
    for folder in (out / "models").glob("a*_DISV_*"):
        shutil.rmtree(folder)
    table, maps = runs.run_analytic(replace(config, kinds=("DISV",)))
    replace_rows(out / "a_metrics.csv", table)
    replace_maps(out / "a_maps.npz", maps)


def add_finest_dis_maps(config: runs.StudyConfig, out: Path = OUT) -> None:
    """Add the problem A maps of the finest DIS grid to the outputs.

    The grid is rerun in a scratch folder for its maps only: its metrics must match the saved
    ones, and the folder is deleted.
    """
    h = min(config.sizes_a)
    scratch = out / "scratch"
    table, maps = runs.run_analytic(replace(config, out=scratch, kinds=("DIS",), sizes_a=(h,)))
    shutil.rmtree(scratch)
    saved = pd.read_csv(out / "a_metrics.csv")
    saved = saved[(saved.kind == "DIS") & (saved.h == h)]
    key = ["angle", "method"]
    numeric = [c for c in table.columns if c not in (*key, "kind", "seconds")]
    diff = (table.set_index(key)[numeric] - saved.set_index(key)[numeric]).abs().max().max()
    assert diff < 1e-9, f"DIS h={h:g} metrics changed by {diff:.1e}"
    print(f"DIS h={h:g} metrics unchanged (max difference {diff:.1e})")
    replace_maps(out / "a_maps.npz", maps, kind=f"DIS_{h:g}")


def main(
    run_analytic: bool = True,
    run_model1: bool = True,
    run_transient: bool = True,
    make_figures: bool = True,
    rerun_disv_a: bool = False,
) -> None:
    """Run the selected parts of the study and record their runtimes."""
    config = study_config()
    OUT.mkdir(parents=True, exist_ok=True)
    timing_file = OUT / "timing.json"
    timing = json.loads(timing_file.read_text(encoding="utf-8")) if timing_file.is_file() else {}
    if rerun_disv_a:
        t0 = time.perf_counter()
        rerun_analytic_disv(config)
        add_finest_dis_maps(config)
        timing["analytic_disv"] = time.perf_counter() - t0
    if run_analytic:
        t0 = time.perf_counter()
        table, maps = runs.run_analytic(config)
        table.to_csv(OUT / "a_metrics.csv", index=False)
        save_maps(OUT / "a_maps.npz", maps)
        timing["analytic"] = time.perf_counter() - t0
    if run_model1:
        t0 = time.perf_counter()
        table, shares, maps, arrivals = runs.run_model1(config)
        table.to_csv(OUT / "b_metrics.csv", index=False)
        shares.to_csv(OUT / "b_shares.csv", index=False)
        save_maps(OUT / "b_maps.npz", maps)
        np.savez_compressed(OUT / "b_arrivals.npz", **arrivals)
        timing["model1"] = time.perf_counter() - t0
    if run_transient:
        t0 = time.perf_counter()
        arrivals = dict(np.load(OUT / "b_arrivals.npz"))
        runs.run_transient(config, arrivals).to_csv(OUT / "t_curves.csv", index=False)
        timing["transient"] = time.perf_counter() - t0
    if make_figures:
        t0 = time.perf_counter()
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        figures.make_all(OUT, FIG_DIR, config)
        figures.write_tables(OUT, config)
        timing["figures"] = time.perf_counter() - t0
    timing_file.write_text(json.dumps(timing, indent=2), encoding="utf-8")
    print(pd.Series(timing).round(1).to_string())


if __name__ == "__main__":
    main()
