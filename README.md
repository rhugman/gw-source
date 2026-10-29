# gwsource

[![ci](https://github.com/rhugman/gw-source/actions/workflows/ci.yml/badge.svg)](https://github.com/rhugman/gw-source/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gwsource)](https://pypi.org/project/gwsource/)
[![docs](https://github.com/rhugman/gw-source/actions/workflows/docs.yml/badge.svg)](https://rhugman.github.io/gw-source/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23782547.svg)](https://doi.org/10.5281/zenodo.23782547)

Where does the water pumped by a well come from? Where does recharge under a polluted site end up? `gwsource` answers such questions from the output of a MODFLOW 6 groundwater-flow model. It reads the binary grid file and the cell-by-cell budget file that the model saves. For every cell it then works out what fraction and volume of the cell's water reaches a chosen destination (backward tracing, or capture) and what fraction came from a chosen source (forward tracing, or fate).

`gwsource` builds upon the cell-mixing flow-tracing method of Foley & Black (2013) and Black & Foley (2013). The code writes the trace as one sparse system of linear equations and solves it for many destinations or sources at once. Flow loops, weak sinks and package networks are therefore handled exactly, and every result is checked against the model's water budget.

## What it does

- Backward (capture) and forward (fate) tracing of steady flow, on DIS, DISV and DISU grids.
- Optional strong sinks: chosen packages take all the water of their cells, as particles stop in a strong sink.
- Transient flow: each time step as a snapshot, or true tracking of tagged water through storage, forward and backward in time.
- Eulerian mean travel time and water age.
- Multi-model simulations, exchanges and advanced-package networks (SFR, LAK, MAW, UZF and the water mover).
- Budget-closure and forward/backward duality checks.
- An ensemble driver for many model realisations, and a helper that compares results with MODFLOW 6 particle tracking (PRT).
- Export to npz, netCDF, GeoPackage and CSV.

## Installation

```bash
pip install gwsource
```

Optional extras: `gwsource[export]` for netCDF and GeoPackage export, and `gwsource[notebooks]` for the tutorial tools. To build and run MODFLOW 6 models you also need the `mf6` executable, for example from FloPy's `get-modflow :flopy`.

The tests and tutorials use a development environment with FloPy from its `develop` branch and the MODFLOW 6 nightly build. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to set it up.

## Quick example

```python
import gwsource as gs

step = gs.read_step("model_ws", boundnames=True)  # one time step of a GWF model
well = gs.select(step, boundnames=["supply_well"])  # the destination: a well
res = gs.backward(step, {"supply_well": well})

capture = res.fraction_through["supply_well"]  # per cell: share of its water that reaches the well
gs.export.to_netcdf("supply_well.nc", step, res)
```

## Documentation and tutorials

The documentation, with the API reference and the tutorials, is at <https://rhugman.github.io/gw-source/>. The tutorials are Jupyter notebooks in [`tutorials/`](tutorials/README.md). They go from a first capture zone to transient tracking and parameter ensembles. Each builds its own small MODFLOW 6 model.

## Citing

If you use `gwsource`, please cite it. The citation details are in [CITATION.cff](CITATION.cff), and GitHub's "Cite this repository" button formats them. Each release is archived on Zenodo, and [doi:10.5281/zenodo.23782547](https://doi.org/10.5281/zenodo.23782547) always resolves to the latest version.

## Contributing

Bug reports, questions and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT; see [`LICENSE`](LICENSE).
