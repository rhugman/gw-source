# Contributing to gwsource

Thank you for your interest in `gwsource`. Bug reports, questions, documentation fixes and code contributions are all welcome.

## Reporting a bug or asking a question

Open an [issue](https://github.com/rhugman/gw-source/issues). For a bug, please include:

- the `gwsource`, FloPy and MODFLOW 6 versions (`mf6 --version`);
- the grid type (DIS, DISV or DISU) and the packages involved;
- a small model or script that shows the problem, if you can share one;
- what you expected and what happened, with the full error message.

## Development environment

The tests and tutorials run against FloPy's `develop` branch and the MODFLOW 6 nightly build. You need [Miniforge](https://conda-forge.org/download/) (mamba and conda) or micromamba, and network access. The commands are the same on Linux, macOS and Windows (on Windows, use the Miniforge Prompt). Run them from the repository root:

```bash
mamba env create -f environment.yml
mamba activate gw-source
python scripts/setup_env.py
```

`environment.yml` holds the conda-forge packages, FloPy from its `develop` branch, and `gwsource` installed editable. `scripts/setup_env.py` then:

1. reinstalls FloPy `develop` and regenerates its MF6 classes from the MODFLOW 6 `develop` definition files;
2. downloads the MODFLOW 6 nightly build, `triangle` (used by the Voronoi grids) and PEST++ (used by tutorial 09) into `bin/`;
3. prints the FloPy version and commit and `mf6 --version`.

Rerun `python scripts/setup_env.py` whenever you want to pick up new FloPy or MODFLOW 6 changes. To update the packages of an existing environment, run `mamba env update -n gw-source -f environment.yml`.

## Running the tests

```bash
mamba run -n gw-source pytest
```

The tests build and run small MODFLOW 6 models in temporary folders, so `bin/mf6` (`bin\mf6.exe` on Windows) must exist. The pytest header records the FloPy commit and MF6 version used. Large checks are marked `slow` and the execution of the tutorial notebooks is marked `tutorials`. Both are skipped by default:

```bash
mamba run -n gw-source pytest -m "slow or tutorials"
```

CI runs the default tests on every push and pull request (Linux, macOS and Windows), and the slow and tutorial tests weekly.

## Benchmarks

`python benchmarks/bench_solver.py` times the solver on synthetic grids up to 1M cells. `python benchmarks/bench_mf6.py` builds a 250,000-cell MF6 model (in `benchmarks/large_ws`) and times I/O, assembly and solve per time step.

## Documentation

The documentation is built with Sphinx from `docs/`. The API reference comes from the docstrings, and the tutorial notebooks are rendered with their committed outputs (they are not executed during the build). To build it locally:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
```

The documentation is published to GitHub Pages from `main`.

## Making a change

1. Fork the repository and create a branch from `main`.
2. Make the change, with a test that fails without it.
3. Keep the code style of the surrounding code: small explicit functions, descriptive names and a docstring for every public function and class.
4. If you change a tutorial notebook, rerun it from the top and commit it with its outputs, so it still reads on GitHub and in the documentation.
5. Run the tests, then open a pull request that explains what the change does and why.

## Releases

Releases are made by the maintainer. The version is set in `src/gwsource/__init__.py` and in `CITATION.cff`. Publishing a GitHub release with a tag `vX.Y.Z` builds the package and uploads it to PyPI, and Zenodo archives the release with a DOI.

## Code of conduct

Please be respectful and constructive in issues, pull requests and discussions.
