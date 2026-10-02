# gw-source

`gwsource` post-processes MODFLOW 6 groundwater-flow output to work out, for every cell, what fraction and volume of its water reaches a chosen destination (capture) or came from a chosen source (fate). It builds on the cell-mixing flow-tracing method of Foley & Black (2013) and Black & Foley (2013), solved as a sparse linear system so that cycles, weak sinks and many destinations are handled exactly.

Status: early development (Phases 0–4: steady and transient snapshot tracing, netCDF/GeoPackage export, Eulerian mean travel time, an MF6 PRT comparison helper, an ensemble driver, multi-model simulations and package networks, and true transient forward/adjoint tracking through storage). See [`PLAN.md`](PLAN.md) for the design.

## Setup

Requires [mamba](https://mamba.readthedocs.io/) (or micromamba/conda) and network access.

```bash
scripts/setup_env.sh
```

This script:

1. creates or updates the `gw-source` environment from `environment.yml` (conda-forge packages, FloPy from its `develop` branch, and this package installed editable);
2. reinstalls FloPy `develop` and regenerates its MF6 classes from the MODFLOW 6 `develop` definition files;
3. downloads the MODFLOW 6 nightly build (and `triangle`, used by a test model) into `bin/`;
4. prints the FloPy version and commit and `mf6 --version`.

Rerun it whenever you want to pick up new FloPy or MODFLOW 6 changes.

## Tutorials

Jupyter notebooks in [`tutorials/`](tutorials/README.md), starting with a quickstart capture-zone example: `jupyter lab tutorials/`.

## Tests

```bash
mamba run -n gw-source pytest
```

The pytest header records the FloPy commit and MF6 version used. The tests build and run small MF6 models in temporary folders, so `bin/mf6` must exist. Large checks are marked `slow` and skipped by default (`pytest -m slow` runs them); so is the execution of the tutorial notebooks (`pytest -m tutorials`).

## Benchmarks

`python benchmarks/bench_solver.py` times the solver on synthetic grids up to 1M cells; `python benchmarks/bench_mf6.py` builds a 250,000-cell MF6 model (in `benchmarks/large_ws`) and times I/O, assembly and solve per time step.

## Licence

MIT; see [`LICENSE`](LICENSE).
