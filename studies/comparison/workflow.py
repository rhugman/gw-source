"""Particle tracking against full-mixing tracing: which gives the better contributing area,
and when. Synthetic part of the comparison study.

Run with the project environment (MF6 from <repo>/bin):

    python studies/comparison/workflow.py

Edit the gates in __main__ to rerun parts. Steps:
1. references: per physical case (screen x stream) the convergence series and R_adv (runs.py);
2. disp: the adjoint GWT validation and R_disp for alpha_T = 0.1, 1, 10 m, on 12.5 and 6.25 m;
3. coarse: 64 coarse grids (dx 100 ... 12.5 m, 1 ... 8 layers), gwsource F and four PRT runs;
4. score: every coarse field against R_adv and each R_disp (scoring.py);
5. figures.
Tables go to studies/comparison/output/tables/, figures to studies/comparison/output/figures/.
Model workspaces are deleted as each run finishes; only fields (npz) and tables are kept.
"""

import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMPORT_DIRS = (HERE, REPO / "studies" / "paper", REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import figures  # noqa: E402
import model as m  # noqa: E402
import runs  # noqa: E402
import scoring  # noqa: E402

OUT = HERE / "output"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
MAP_CASE = m.Case(25.0, 4, "lower", "near")
MAP_WINDOW = (0.0, 1600.0, 200.0, 1000.0)


def study_config(out: Path = OUT, bin_dir: Path = REPO / "bin") -> runs.StudyConfig:
    """Return the study configuration with the MF6 executable in bin_dir."""
    mf6 = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    assert mf6.is_file(), f"{mf6} not found; see studies/README.md (Environment)"
    return runs.StudyConfig(out=out, mf6_exe=mf6, design=m.Design())


def run_parallel(function, jobs: list, workers: int) -> list:
    """Run function(*job) for every job in a process pool; return the results in job order."""
    with Pool(processes=workers) as pool:  # concurrent.futures needs sysconf, blocked here
        return pool.starmap(function, jobs, chunksize=1)


def flatten(results: list[list[dict]]) -> pd.DataFrame:
    """Return the concatenated rows of several runs."""
    return pd.DataFrame([row for rows in results for row in rows])


def summary_table(scores: pd.DataFrame) -> pd.DataFrame:
    """Return the mean scores per reference, method and cell size (over layers and cases)."""
    columns = ["jaccard", "size_ratio", "rmse", "share_error_max", "closure"]
    return (scores.groupby(["reference", "method", "dx"])[columns].mean().reset_index()
            .sort_values(["reference", "method", "dx"]))


def make_figures(cfg: runs.StudyConfig) -> None:
    """Draw every figure from the saved tables and fields."""
    figures.style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    series = pd.read_csv(TABLES / "convergence.csv")
    scores = pd.read_csv(TABLES / "scores.csv")
    figures.convergence(series, runs.REF_NLAY, FIGURES / "convergence.png")
    figures.error_grid(scores, "dx", FIGURES / "error_vs_dx.png")
    figures.error_grid(scores, "nlay", FIGURES / "error_vs_layers.png")
    figures.error_vs_ratio(scores, FIGURES / "error_vs_ratio.png")
    draw_maps(cfg)


def draw_maps(cfg: runs.StudyConfig, case: m.Case = MAP_CASE) -> None:
    """Map the references and both methods on one mid-resolution grid."""
    d = cfg.design
    adv = np.load(cfg.refs / f"adv_{case.physical}.npz")["PRT 27 well"]
    disp_dx = runs.DISP_DX[-1]
    disp_name = f"disp_{case.physical}_dx{disp_dx:g}".replace(".", "p")
    disp = np.load(cfg.refs / f"{disp_name}.npz")["R_disp 1"]
    fields = np.load(cfg.fields / f"{case.label}.npz")
    panels = [
        ("R_adv, mapped", figures.mapped_reference(adv, runs.REF_DX, case.dx, d.rech), case.dx),
        ("R_disp ($\\alpha_T$ = 1 m), mapped",
         figures.mapped_reference(disp, disp_dx, case.dx, d.rech), case.dx),
        ("gwsource F", fields["F"], case.dx),
        ("PRT 27, P (pass)", fields["PRT 27 pass"], case.dx),
        ("PRT centre (pass)", fields["PRT centre pass"], case.dx),
    ]
    figures.map_panels(panels, (adv, runs.REF_DX), (d.well_x, d.well_y),
                       d.stream_x[case.stream], (d.lx, d.ly),
                       MAP_WINDOW, FIGURES / f"maps_{case.label}.png")


def main(
    run_references: bool = True,
    run_disp: bool = True,
    run_coarse: bool = True,
    score: bool = True,
    draw: bool = True,
    workers: int = max(1, min(8, (os.cpu_count() or 2) - 2)),
) -> None:
    """Run the selected steps of the study."""
    cfg = study_config()
    TABLES.mkdir(parents=True, exist_ok=True)
    physical = runs.physical_cases()
    if run_references:
        rows = run_parallel(runs.run_reference, [(cfg, s, t) for s, t in physical], workers)
        flatten(rows).to_csv(TABLES / "convergence.csv", index=False)
    if run_disp:
        jobs = [(cfg, s, t, dx) for s, t in physical for dx in runs.DISP_DX]
        flatten(run_parallel(runs.run_disp_reference, jobs, workers)).to_csv(
            TABLES / "disp_reference.csv", index=False)
    if run_coarse:
        jobs = [(cfg, case) for case in runs.coarse_cases()]
        flatten(run_parallel(runs.run_coarse, jobs, workers)).to_csv(
            TABLES / "coarse_runs.csv", index=False)
    if score:
        coarse = pd.read_csv(TABLES / "coarse_runs.csv")
        scores, floor = scoring.score_table(coarse, cfg.fields, cfg.refs, runs.DISP_DX[-1],
                                            cfg.design.rech)
        scores.to_csv(TABLES / "scores.csv", index=False)
        floor.to_csv(TABLES / "reference_floor.csv", index=False)
        summary_table(scores).to_csv(TABLES / "summary.csv", index=False)
    if draw:
        make_figures(cfg)
    print(json.dumps({"tables": str(TABLES), "figures": str(FIGURES)}))


if __name__ == "__main__":
    main()
