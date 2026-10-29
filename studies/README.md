# Reproducing the paper

This folder holds the analysis behind the paper. Each subfolder is one study:

- `comparison/`: full mixing against particle tracking on a 3D synthetic aquifer.
- `dispersion/`: numerical dispersion against cell size, on test problems with a known answer.
- `neversink/`: the USGS Neversink/Rondout model and its published particle tracking.
- `paper/`: figure scripts, and shared plotting helpers.

A study script runs models and writes result tables. A figure script reads those tables, or builds
a small model itself, and draws one or more paper figures. The figure scripts check the numbers
they draw with `assert` statements, so a figure is only written if the results match.

## Environment

Set up the `gw-source` environment once from the repository root:

```bash
scripts/setup_env.sh
conda activate gw-source        # or prefix each command with: mamba run -n gw-source
```

This installs `gwsource` (editable), FloPy, pyemu and vorflow, and puts MODFLOW 6 (`mf6`) and
PEST++ into `bin/`. The scripts take `mf6` from `bin/`.

Run every command below from the repository root, with this search path:

```bash
export PYTHONPATH=src:tutorials:tests:studies/paper
```

`tutorials` provides the shared synthetic model (`tutorials/herebedragons.py`). `studies/paper`
provides the plotting helpers that several studies import.

One extra need:

- **Neversink data.** See the Neversink study below.

The Voronoi grids of the dispersion study come from `vorflow` (from PyPI, in `environment.yml`), which meshes with Gmsh.

## Where outputs go

Model output and result tables go to `output/` folders inside each study, for example
`studies/neversink/output/`. Git ignores every `output/` folder, so results stay on your disk.
Most model workspaces are deleted once their results are read.

Every figure script writes its figures to `output/paper/` at the repository root (also
git-ignored). To write elsewhere, pass `out_dir` to the script's `main`. Each figure is written
as PNG (300 dpi) and PDF, except the two comparison figures, which are PNG only.

## Run order

Steps 1 to 4 are independent of each other, except that Fig. 8 (step 4) also needs the
Neversink window of step 3.

1. Method and synthetic figures: no study runs needed.
2. Dispersion study, then the SI convergence figures.
3. Neversink study, then the Neversink figures.
4. Comparison study, then the comparison figures.

## Figures and the scripts that make them

| Figure | Content | Script and function | Needs first | File written |
| --- | --- | --- | --- | --- |
| Fig. 1 | Method sketch: F on an eight-cell example; snapshot against transient tracing | `paper/gallery_figure.py`, `make_method_single` | nothing | `fig_method_single` |
| Fig. 2 | Example A: backward fraction F to the supply well | `paper/synthetic_figures.py`, `make_example_a` | nothing | `fig_example_a` |
| Fig. 3 | Example B: mean travel time; forward fraction G of a field | `paper/synthetic_figures.py`, `make_example_b` | nothing | `fig_example_b` |
| Fig. 4 | Example C: F with drains, without and with flow routed along the stream | `paper/synthetic_figures.py`, `make_example_c` | nothing | `fig_example_c` |
| Fig. 5 | Example D: transient tracing of the well's water | `paper/synthetic_figures.py`, `make_example_d` | nothing | `fig_example_d` |
| Fig. 6 | Full mixing against particle tracking in the synthetic aquifer | `comparison/paper_figures.py`, `fig_synthetic` | `comparison/workflow.py` | `fig_comparison_synthetic.png` |
| Fig. 7 | Neversink: F and the published contributing area, whole model and three windows | `neversink/paper_figures.py`, `neversink_maps` | `neversink/workflow.py` | `fig_neversink_maps` |
| Fig. 8 | Neversink: full mixing against particles in a refined window | `comparison/paper_figures.py`, `fig_neversink` | `neversink/workflow.py`, `neversink/window.py` | `fig_neversink_window.png` |
| SI Fig. 1 | Neversink: mean F over the 358-member ensemble | `neversink/paper_figures.py`, `neversink_ensemble` | `neversink/pest_rebuild.py`, `neversink/ensemble_run.py` | `figS1_neversink_ensemble` |
| SI Fig. 2 | Full mixing against cell size, well in uniform flow | `paper/si_convergence_figure.py`, `make_cell_size_figure` | `dispersion/workflow.py` | `si_fig2_cell_size` |
| SI Fig. 3 | New recharge at the well against the number of transport sub-steps | `paper/si_convergence_figure.py`, `make_time_step_figure` | nothing (builds its own model) | `si_fig3_time_steps` |

Figure numbers may still change.

## 1. Method and synthetic figures

Fig. 1 is drawn from a hand-built eight-cell example. It runs in seconds.

```bash
python studies/paper/gallery_figure.py
```

Figs 2 to 5 come from one script. It builds the shared synthetic model (40 × 40 cells of 50 m,
one layer, an SFR stream and a supply well) and its variants: forward and travel-time traces,
two drains with the water mover, and a 30-year transient run. Workspaces go under `$TMPDIR` and
are deleted at the end.

```bash
python studies/paper/synthetic_figures.py
```

The script prints every number it checks before it draws.

## 2. Dispersion study and SI Figs 2 and 3

The dispersion study runs two test problems on square (DIS) and Voronoi (DISV) grids of several
cell sizes, with Voronoi grids from vorflow. It takes about 3 minutes on a 16-core laptop.

```bash
python studies/dispersion/workflow.py
```

Tables, maps and grids go to `studies/dispersion/output/`. Edit the gates in `__main__` to rerun
parts.

Then draw SI Figs 2 and 3. SI Fig. 2 is redrawn from the dispersion output. SI Fig. 3 builds the
transient model of example D and tracks new recharge with 1, 4, 16 and 64 sub-steps.

```bash
python studies/paper/si_convergence_figure.py
```

## 3. Neversink study

### Data

The model is the USGS Neversink/Rondout MODFLOW 6 model (Fienen and others 2021; Corson-Dosch and
others 2021), public domain. Its calibrated input, the published MODPATH 7 results and the
PEST++ ensemble files are in the USGS repository `usgs/neversink_workflow`. The scripts read a
sparse checkout of it in `studies/neversink/external/neversink_workflow/` (git-ignored). Make it
once, without the large folders the study does not use:

```bash
git clone --filter=blob:none --no-checkout https://github.com/usgs/neversink_workflow.git \
    studies/neversink/external/neversink_workflow
cd studies/neversink/external/neversink_workflow
git sparse-checkout set --no-cone '/*' '!/*/' /neversink_optimal/ /neversink_mf6/ \
    /processed_data/ /output/neversink_mf6_optimal_output/ /output/neversink_mp7_optimal_output/ \
    /output/modpath_mc/ /output/parallel/ /scripts/ /notebooks_workflow_complete/ \
    /supplementary_tables/ /python_packages_static/
git checkout 6e4a5fb4c87f54d875675906380d0a0029fadd6c
cd -
```

The study was run on that commit. The checkout takes about 1 GB.

### Steps

Each script has gates (keyword arguments of `main`) that switch its parts on and off. All
results go to `studies/neversink/output/`.

| Step | Command | What it does | Main outputs |
| --- | --- | --- | --- |
| a | `python studies/neversink/workflow.py` | Copies and runs the calibrated model with MF6, traces the eight priority wells, compares F with the published MODPATH 7 area, runs PRT checks | `optimal/` (model), `mp7_comparison.csv`, `mp7_coverage.csv`, `checks_cells.csv`, `fractions_cells.npz` |
| b | `python studies/neversink/net_and_envelope.py` | Gross against net accounting on the same flows | `net_vs_gross_wells.csv`, `net_vs_gross_mp7.csv`, `envelope_prt.csv` |
| c | `python studies/neversink/strong_sinks.py` | Full mixing with every sink strong, against the published area | `strong_sinks_*.csv` |
| d | `python studies/neversink/prt_many_particles.py` | 27 PRT particles per start cell against F | `prt_many_particles/endpoints.npz`, `prt_many_particles_cells.csv` |
| e | `python studies/neversink/diagnostics.py` | Where and why full mixing and the published particles differ | `diagnostics/` |
| f | `python studies/neversink/window.py` | Refined window around the cluster U wells: MF6, gwsource and PRT on 50, 25 and 12.5 m cells with 4 to 32 layers | `window/` (`refinement.csv`, `metrics.csv`, `runs.csv`, `start_cells.csv.gz`) |
| g | `python studies/neversink/pest_rebuild.py` | Rebuilds the PEST interface and the 358-member parameter ensemble, and checks it against the published files | `pest/` (`modpath_par_ens.csv`, `mask_index.csv`) |
| h | see below | Runs and traces every realisation of the ensemble | `ensemble/` (`probability_maps.npz`, `probability_comparison.csv`, `summary.csv`) |
| i | see below | Checks the row offset and pairing of the published per-realisation masks | `mc_masks/` (`mask_offsets.csv`, `calibrated_offsets.csv`) |

Steps b to f need only step a. Steps c to f need `TraceConfig(strong_sinks=...)`, which is in
`gwsource`. Step f takes about 40 minutes of model, PRT and scoring time. Steps d and e give
supporting results only. No figure reads them.

Step h runs only the base pumping rate. The other pumping scenarios of `ensemble_run.py` are not
used in the paper:

```bash
PYTHONPATH=studies/neversink:$PYTHONPATH python -c "import ensemble_run as e; \
e.main(run_scenarios=False, analyse_scenarios=False)"
```

It runs six processes (`N_WORKERS`) and took about 75 minutes. It can be resumed: a realisation
that already has a summary file is skipped.

Step i needs only the published masks and end points, not the runs of step h:

```bash
PYTHONPATH=studies/neversink:$PYTHONPATH python -c "import mc_masks as m; \
m.main(compare=False, run_multiplier=False)"
```

### Figures

Fig. 7 and SI Fig. 1 read stored outputs only:

```bash
python studies/neversink/paper_figures.py
```

They read `studies/neversink/output/`. The gates `maps` and `ensemble` of `main` switch the two
figures; Fig. 7 alone needs only step a.

The script stops if the published area or the number of realisations is not what it expects.

## 4. Comparison study

The comparison study builds the synthetic aquifer in 3D. It makes fine-grid particle and
transport references, then scores full mixing and four particle set-ups on 64 coarse grids.

```bash
python studies/comparison/workflow.py
```

It runs in up to 8 processes. The stored run times add up to about 9 CPU hours, most of them in
the references. Tables go to `studies/comparison/output/tables/`, saved fields to
`studies/comparison/output/fields/` and `references/`, and study figures to
`studies/comparison/output/figures/`. Edit the gates in `main` to rerun parts.

Then draw Figs 6 and 8. Fig. 8 reads the Neversink window output
(`studies/neversink/output/window/`), so run step 3f first. Fig. 6 needs only the comparison
study:

```bash
python studies/comparison/paper_figures.py
PYTHONPATH=studies/comparison:$PYTHONPATH python -c "import paper_figures as p; \
p.main(neversink=False)"    # Fig. 6 only
```

## Helper modules

The scripts above import these modules, which draw nothing on their own: `paper/method_figures.py`,
`paper/example_figures.py`, `paper/example_figures_b.py`, `paper/neversink_figures.py`,
`neversink/figures.py`, `neversink/mp7_convention.py`, `neversink/scenarios.py`,
`neversink/growth_mechanisms.py`, and the `figures.py`, `model.py`, `runs.py`, `methods.py`,
`scoring.py`, `analysis.py` and `problems.py` modules of the comparison and dispersion studies.
