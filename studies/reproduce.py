"""Run every study of the paper in order and draw every figure into output/paper/.

A thin driver: each step calls the main(...) of one script with the gates the paper uses, in a
fresh Python process. A step whose outputs already exist is skipped, so an interrupted run
resumes where it stopped. Study tables go to output/ folders inside each study (git-ignored).

Run from anywhere, with the gw-source-paper environment active and studies/setup_tools.py done:

    python studies/reproduce.py                  # everything (a few hours)
    python studies/reproduce.py --quick          # figures that need no long study (minutes)
    python studies/reproduce.py --list           # steps, what they need, rough runtimes
    python studies/reproduce.py --steps dispersion,si_cell_size
    python studies/reproduce.py --force          # redo steps whose outputs exist

The synthetic example figures need the SFR stream of the shared model (add_sfr in
tutorials/herebedragons.py); without it that step is skipped with a message.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIG_DIR = REPO / "output" / "paper"
NEVERSINK = "studies/neversink/output"
NEVERSINK_DATA = REPO / "studies" / "neversink" / "external" / "neversink_workflow"
QUICK = ("method", "synthetic", "graphical_abstract", "si_time_steps")
# Imports a script as a module in a fresh process and calls its main with JSON keyword arguments.
RUNNER = (
    "import importlib, json, sys; from pathlib import Path; path = Path(sys.argv[1]); "
    "sys.path.insert(0, str(path.parent)); "
    "importlib.import_module(path.stem).main(**json.loads(sys.argv[2]))"
)


@dataclass(frozen=True)
class Step:
    """One script call: what it runs, what it writes, what it needs first."""

    name: str
    script: str  # relative to the repository root
    about: str
    runtime: str
    outputs: tuple[str, ...]  # relative to the repository root; all exist = step done
    needs: tuple[str, ...] = ()  # names of earlier steps
    kwargs: dict = field(default_factory=dict)
    neversink_data: bool = False
    sfr: bool = False


def figures(*names: str) -> tuple[str, ...]:
    """Return the output/paper PNG paths of the named figures."""
    return tuple(f"output/paper/{n}.png" for n in names)


STEPS = (
    Step("method", "studies/paper/gallery_figure.py", "Fig. 1, method sketch", "< 1 min",
         figures("fig_method_single")),
    Step("synthetic", "studies/paper/synthetic_figures.py", "Figs 2-5, synthetic examples A-D",
         "few min", figures("fig_example_a", "fig_example_b", "fig_example_c", "fig_example_d"),
         sfr=True),
    Step("graphical_abstract", "studies/paper/graphical_abstract.py",
         "graphical abstract (Table of Contents image)", "< 1 min",
         figures("graphical_abstract"), sfr=True),
    Step("si_time_steps", "studies/paper/si_convergence_figure.py",
         "SI Fig. 3, transport sub-steps", "< 1 min", figures("si_fig3_time_steps"),
         kwargs={"cell_size": False}),
    Step("dispersion", "studies/dispersion/workflow.py", "dispersion study", "~ 3 min",
         ("studies/dispersion/output/a_maps.npz", "studies/dispersion/output/a_metrics.csv")),
    Step("si_cell_size", "studies/paper/si_convergence_figure.py", "SI Fig. 2, cell size",
         "< 1 min", figures("si_fig2_cell_size"), needs=("dispersion",),
         kwargs={"time_steps": False}),
    Step("neversink", "studies/neversink/workflow.py", "Neversink base model, F against MODPATH",
         "~ 30 min", (f"{NEVERSINK}/fractions_cells.npz", f"{NEVERSINK}/fractions_sfr_network.npz",
                      f"{NEVERSINK}/mp7_comparison.csv", f"{NEVERSINK}/prt_volume_thin1"),
         neversink_data=True),
    Step("net_and_envelope", "studies/neversink/net_and_envelope.py", "gross against net (numbers)",
         "~ 5 min", (f"{NEVERSINK}/net_vs_gross_mp7.csv", f"{NEVERSINK}/envelope_prt.csv"),
         needs=("neversink",), neversink_data=True),
    Step("strong_sinks", "studies/neversink/strong_sinks.py", "every sink strong (numbers)",
         "~ 2 min", (f"{NEVERSINK}/strong_sinks_mp7.csv",), needs=("neversink",),
         neversink_data=True),
    Step("prt_many_particles", "studies/neversink/prt_many_particles.py",
         "27 PRT particles per cell (numbers)", "~ 5 min",
         (f"{NEVERSINK}/prt_many_particles_cells.csv",), needs=("neversink",),
         neversink_data=True),
    Step("diagnostics", "studies/neversink/diagnostics.py", "why F and particles differ (numbers)",
         "~ 10 min", (f"{NEVERSINK}/diagnostics/path_loss_by_position.csv",),
         needs=("prt_many_particles",), neversink_data=True),
    Step("window", "studies/neversink/window.py", "refined Neversink window", "~ 40 min",
         (f"{NEVERSINK}/window/run_log.json", f"{NEVERSINK}/window/refinement.csv",
          f"{NEVERSINK}/window/start_cells.csv.gz"), needs=("neversink",), neversink_data=True),
    Step("pest_rebuild", "studies/neversink/pest_rebuild.py", "rebuild the 358-member ensemble",
         "~ 15 min",
         (f"{NEVERSINK}/pest/mask_index.csv", f"{NEVERSINK}/pest/check_observations.csv"),
         neversink_data=True),
    Step("ensemble", "studies/neversink/ensemble_run.py", "run and trace the ensemble", "~ 75 min",
         (f"{NEVERSINK}/ensemble/probability_maps.npz", f"{NEVERSINK}/ensemble/summary.csv"),
         needs=("neversink", "pest_rebuild"), neversink_data=True,
         kwargs={"run_scenarios": False, "analyse_scenarios": False, "make_figures": False}),
    Step("mc_masks", "studies/neversink/mc_masks.py", "published mask offsets (numbers)", "~ 2 min",
         (f"{NEVERSINK}/mc_masks/mask_offsets.csv",), needs=("pest_rebuild",),
         neversink_data=True, kwargs={"compare": False, "run_multiplier": False}),
    Step("neversink_figures", "studies/neversink/paper_figures.py",
         "Fig. 7 and SI Fig. 1, Neversink maps", "~ 1 min",
         figures("fig_neversink_maps", "figS1_neversink_ensemble"), needs=("neversink", "ensemble"),
         neversink_data=True),
    Step("comparison", "studies/comparison/workflow.py", "full mixing against particles, 3D",
         "~ 9 CPU h", ("studies/comparison/output/tables/scores.csv",
                       "studies/comparison/output/tables/coarse_runs.csv")),
    Step("comparison_figures", "studies/comparison/paper_figures.py",
         "Figs 6 and 8, comparison", "~ 1 min",
         figures("fig_comparison_synthetic", "fig_neversink_window"),
         needs=("comparison", "window")),
)


def is_done(step: Step, repo: Path = REPO) -> bool:
    """Return True if every output of step exists."""
    return all((repo / p).exists() for p in step.outputs)


def has_sfr(repo: Path = REPO) -> bool:
    """Return True if the shared synthetic model has its SFR stream."""
    text = (repo / "tutorials" / "herebedragons.py").read_text(encoding="utf-8")
    return "\ndef add_sfr(" in text


def missing_inputs(step: Step, by_name: dict[str, Step], repo: Path = REPO) -> list[str]:
    """Return what step needs but does not find, as messages."""
    missing = [f"step {n} (run it first)" for n in step.needs if not is_done(by_name[n], repo)]
    if step.neversink_data and not NEVERSINK_DATA.is_dir():
        missing.append("the Neversink data (python studies/setup_tools.py)")
    return missing


def run_step(step: Step, repo: Path = REPO) -> None:
    """Call the step's main(**kwargs) in a fresh Python process; raise if it fails."""
    env = {**os.environ, "MPLBACKEND": os.environ.get("MPLBACKEND", "Agg"),
           "PYTHONUTF8": "1"}
    cmd = [sys.executable, "-c", RUNNER, str(repo / step.script), json.dumps(step.kwargs)]
    subprocess.run(cmd, check=True, cwd=repo, env=env)


def print_steps(steps: tuple[Step, ...], repo: Path = REPO) -> None:
    """Print the steps with what they need, rough runtimes and whether they are done."""
    print(f"{'step':<20}{'runtime':<12}{'done':<6}{'needs':<34}content")
    for s in steps:
        needs = ", ".join(s.needs + (("data",) if s.neversink_data else ()))
        print(f"{s.name:<20}{s.runtime:<12}{'yes' if is_done(s, repo) else '-':<6}"
              f"{needs or '-':<34}{s.about}")
    print(f"\nquick: {', '.join(QUICK)}. Runtimes are rough, on a 16-core laptop.")


def summarise(ran: list[str], skipped: list[str], start: float, fig_dir: Path = FIG_DIR) -> None:
    """Print the steps run and skipped, the figures written in this run, and the total time."""
    made = sorted(p.name for p in fig_dir.glob("*.png") if p.stat().st_mtime >= start)
    print("\n" + "=" * 60)
    print(f"steps run: {', '.join(ran) or 'none'}")
    for line in skipped:
        print(f"skipped: {line}")
    print(f"{len(made)} figures written to {fig_dir}: {', '.join(made) or '-'}")
    print(f"total time: {(time.time() - start) / 60:.1f} min")


def main(names: tuple[str, ...], force: bool = False, steps: tuple[Step, ...] = STEPS,
         repo: Path = REPO) -> None:
    """Run the named steps in their fixed order; skip those already done unless force."""
    by_name = {s.name: s for s in steps}
    unknown = set(names) - set(by_name)
    assert not unknown, f"unknown steps {sorted(unknown)}; see --list"
    start = time.time()
    ran, skipped = [], []
    for step in (s for s in steps if s.name in names):
        if is_done(step, repo) and not force:
            skipped.append(f"{step.name} (outputs exist; --force to redo)")
            continue
        if step.sfr and not has_sfr(repo):
            skipped.append(f"{step.name} (tutorials/herebedragons.py has no add_sfr: the "
                           "synthetic model's SFR stream is not on this branch yet)")
            print(f"\n--- {step.name}: SKIPPED, no SFR stream in the synthetic model")
            continue
        missing = missing_inputs(step, by_name, repo)
        assert not missing, f"step {step.name} needs: {'; '.join(missing)}"
        print(f"\n--- {step.name}: {step.about} ({step.runtime}) ---", flush=True)
        t0 = time.time()
        try:
            run_step(step, repo)
        except subprocess.CalledProcessError:
            sys.exit(f"\nstep {step.name} failed (see above). Rerun to resume; finished steps "
                     "are skipped.")
        print(f"--- {step.name}: done in {(time.time() - t0) / 60:.1f} min", flush=True)
        ran.append(step.name)
    summarise(ran, skipped, start, repo / "output" / "paper")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reproduce the paper's studies and figures.")
    parser.add_argument("--list", action="store_true", help="print the steps and exit")
    parser.add_argument("--quick", action="store_true",
                        help=f"only the steps that need no long study: {', '.join(QUICK)}")
    parser.add_argument("--steps", help="comma-separated step names to run (see --list)")
    parser.add_argument("--force", action="store_true", help="redo steps whose outputs exist")
    args = parser.parse_args()
    if args.list:
        print_steps(STEPS)
    else:
        chosen = QUICK if args.quick else tuple(s.name for s in STEPS)
        if args.steps:
            chosen = tuple(n.strip() for n in args.steps.split(","))
        main(chosen, force=args.force)
