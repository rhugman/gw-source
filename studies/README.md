# Reproducing the paper

Three commands rebuild every figure of the paper into `output/paper/` (PNG at 300 dpi, and PDF).
Each study also writes its result tables to an `output/` folder of its own, for example
`studies/neversink/output/`. Git ignores every `output/` folder. The figure scripts check the
numbers they draw with `assert` statements, so a figure is written only if the results match.

## Three commands

Run them from the repository root on Linux, macOS or Windows, in any shell. With conda or mamba,
write `conda` or `mamba` in place of `micromamba`.

```
micromamba env create -f studies/environment.yml
micromamba activate gw-source-paper
python studies/setup_tools.py
python studies/reproduce.py
```

- `studies/environment.yml` pins every package the results were made with.
- `setup_tools.py` puts MODFLOW 6 6.8.1 into `bin/` and makes FloPy's MODFLOW 6 classes from
  the 6.8.1 input definitions. It also fetches the USGS Neversink/Rondout model (about 1 GB, needs
  `git`). It skips what is already done. Use `--no-neversink` to skip the data.
- `reproduce.py` runs the studies in order, then draws the figures, and prints a summary. It skips
  steps whose outputs exist, so after an interruption, rerun it to resume. Options:
  `--quick` (Figs 1 to 5 and SI Fig. 3, a few minutes, no Neversink data needed), `--list` (steps,
  what each needs, rough runtimes), `--steps a,b` (a subset) and `--force` (redo).

On Linux, Gmsh (used for the Voronoi grids) also needs some system libraries, for example on
Ubuntu: `sudo apt-get install libglu1-mesa libxrender1 libxcursor1 libxft2 libxinerama1`.

## Runtime and disk

The full run takes a few hours on a 16-core laptop. Most of it is the comparison study (about
9 CPU hours in up to 8 processes), the Neversink ensemble (about 75 minutes in 6 processes) and
the refined Neversink window (about 40 minutes). Plan for about 1 GB of Neversink data and a few
GB of study output. Model workspaces are mostly deleted once their results are read.

## Figures and the scripts that make them

| Figure | Content | Script (`studies/...`) | Step in `reproduce.py` |
| --- | --- | --- | --- |
| Fig. 1 | Method sketch | `paper/gallery_figure.py` | `method` |
| Figs 2 to 5 | Synthetic examples A to D | `paper/synthetic_figures.py` | `synthetic` |
| Graphical abstract | Contributing area, mean travel time, sources of water and seasonal contribution of the example well | `paper/graphical_abstract.py` | `graphical_abstract` |
| Fig. 6 | Full mixing against particles, synthetic aquifer | `comparison/paper_figures.py` | `comparison_figures` |
| Fig. 7 | Neversink: F and the published contributing area | `neversink/paper_figures.py` | `neversink_figures` |
| Fig. 8 | Neversink: full mixing against particles, refined window | `comparison/paper_figures.py` | `comparison_figures` |
| SI Fig. 1 | Neversink: mean F over the ensemble | `neversink/paper_figures.py` | `neversink_figures` |
| SI Fig. 2 | Full mixing against cell size | `paper/si_convergence_figure.py` | `si_cell_size` |
| SI Fig. 3 | New recharge against transport sub-steps | `paper/si_convergence_figure.py` | `si_time_steps` |

`python studies/reproduce.py --list` shows the study steps behind each figure. Some steps
(`net_and_envelope`, `strong_sinks`, `prt_many_particles`, `diagnostics`, `mc_masks`) give
numbers quoted in the text and draw no paper figure.

## Running a single study

Each script runs alone as `python studies/<study>/<script>.py`, with no `PYTHONPATH` needed. Its
`main(...)` has keyword gates that switch its parts on and off. The module docstring says what
the script reads and writes. Set the gates in `__main__` to rerun a part.
