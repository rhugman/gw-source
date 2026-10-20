"""Dispersion study: how much does full mixing spread capture zones, and how much of it
does face-to-face routing remove? Tutorial 11 (tutorials/11_numerical_dispersion) walks through
the same two test problems.

Run from anywhere with the project environment (MF6 and triangle are taken from <repo>/bin):

    python studies/dispersion/workflow.py

Edit the gates in __main__ to rerun parts. Models and tables go to studies/dispersion/output/
(git-ignored); figures to studies/dispersion/output/figures/. The transient part reads the particle arrivals saved
by the problem B part. Runtime on a 16-core laptop: about 6 minutes, most of it the MF6 PRT run
on the finest grid of problem B (about 94,000 particles).
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import figures  # noqa: E402
import runs  # noqa: E402

OUT = HERE / "output"
FIG_DIR = OUT / "figures"
BIN = REPO / "bin"


def study_config(out: Path = OUT, bin_dir: Path = BIN) -> runs.StudyConfig:
    """Return the study configuration with the executables in bin_dir."""
    suffix = ".exe" if sys.platform.startswith("win") else ""
    mf6, triangle = bin_dir / f"mf6{suffix}", bin_dir / f"triangle{suffix}"
    assert mf6.is_file() and triangle.is_file(), "run scripts/setup_env.sh to fetch mf6, triangle"
    return runs.StudyConfig(out=out, mf6_exe=mf6, triangle_exe=triangle)


def save_maps(path: Path, maps: dict) -> None:
    """Save raster maps as float32 (booleans as 0/1)."""
    np.savez_compressed(path, **{k: np.asarray(v, dtype=np.float32) for k, v in maps.items()})


def main(
    run_analytic: bool = True,
    run_model1: bool = True,
    run_transient: bool = True,
    make_figures: bool = True,
) -> None:
    """Run the selected parts of the study and record their runtimes."""
    config = study_config()
    OUT.mkdir(parents=True, exist_ok=True)
    timing_file = OUT / "timing.json"
    timing = json.loads(timing_file.read_text()) if timing_file.is_file() else {}
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
    timing_file.write_text(json.dumps(timing, indent=2))
    print(pd.Series(timing).round(1).to_string())


if __name__ == "__main__":
    main()
