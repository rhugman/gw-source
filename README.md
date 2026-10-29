# gw-source

`gwsource` post-processes MODFLOW 6 groundwater-flow output to work out, for every cell, what fraction and volume of its water reaches a chosen destination (capture) or came from a chosen source (fate). It builds on the cell-mixing flow-tracing method of Foley & Black (2013) and Black & Foley (2013), solved as a sparse linear system so that cycles, weak sinks and many destinations are handled exactly.

Status: in development. The package traces steady flow and single time steps of transient flow (snapshots), and it tracks water forward and backward through storage in transient flow. It computes the mean travel time from the flow field (Eulerian), and it exports results to netCDF and GeoPackage. It also handles multi-model simulations and package networks, and it includes an ensemble driver and a helper that compares results with MF6 particle tracking (PRT).

## Setup

Requires [mamba](https://mamba.readthedocs.io/) (or micromamba/conda) and network access.

```bash
scripts/setup_env.sh
```

This script:

1. creates or updates the `gw-source` environment from `environment.yml` (conda-forge packages, FloPy from its `develop` branch, and this package installed editable);
2. reinstalls FloPy `develop` and regenerates its MF6 classes from the MODFLOW 6 `develop` definition files;
3. downloads the MODFLOW 6 nightly build, `triangle` (used by a test model) and PEST++ (with pyemu's `get-pestpp`, used by tutorial 09) into `bin/`;
4. prints the FloPy version and commit and `mf6 --version`.

Rerun it whenever you want to pick up new FloPy or MODFLOW 6 changes.

On Windows, run the script from Git Bash, or run the same steps in PowerShell from the repository root:

```powershell
micromamba env create -y -n gw-source -f environment.yml  # or: micromamba env update -n gw-source -f environment.yml
micromamba run -n gw-source python -m pip install --upgrade --force-reinstall --no-deps "flopy[codegen] @ git+https://github.com/modflowpy/flopy.git@develop"
micromamba run -n gw-source python -m pip install "flopy[codegen] @ git+https://github.com/modflowpy/flopy.git@develop"
micromamba run -n gw-source python -m flopy.mf6.utils.generate_classes --ref develop
New-Item -ItemType Directory -Force bin, $env:TEMP\gw-source-downloads | Out-Null
micromamba run -n gw-source get-modflow --repo modflow6-nightly-build --downloads-dir $env:TEMP\gw-source-downloads bin
micromamba run -n gw-source get-modflow --repo executables --subset triangle --downloads-dir $env:TEMP\gw-source-downloads bin
micromamba run -n gw-source get-pestpp --downloads-dir $env:TEMP\gw-source-downloads bin
bin\mf6.exe --version
```

Use `mamba` or `conda` in place of `micromamba` if that is what you have.

## Tutorials

Jupyter notebooks in [`tutorials/`](tutorials/README.md), starting with a quickstart capture-zone example: `jupyter lab tutorials/`.

## Tests

```bash
mamba run -n gw-source pytest
```

The pytest header records the FloPy commit and MF6 version used. The tests build and run small MF6 models in temporary folders, so `bin/mf6` (`bin\mf6.exe` on Windows) must exist. Large checks are marked `slow` and skipped by default (`pytest -m slow` runs them); so is the execution of the tutorial notebooks (`pytest -m tutorials`).

## Benchmarks

`python benchmarks/bench_solver.py` times the solver on synthetic grids up to 1M cells; `python benchmarks/bench_mf6.py` builds a 250,000-cell MF6 model (in `benchmarks/large_ws`) and times I/O, assembly and solve per time step.

## Licence

MIT; see [`LICENSE`](LICENSE).
