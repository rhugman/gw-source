# Installation

## From PyPI

```bash
pip install gwsource
```

The optional extras add netCDF and GeoPackage export (`gwsource[export]`) and the notebook tools
(`gwsource[notebooks]`). `gwsource` reads MODFLOW 6 output; to build and run models you also need
the MODFLOW 6 executable, for example with FloPy's `get-modflow :flopy`.

## Development environment

The repository's `scripts/setup_env.sh` creates the `gw-source` conda environment from
`environment.yml` (FloPy from its `develop` branch, `gwsource` installed editable) and downloads
the MODFLOW 6 nightly build into `bin/`. The tests and the tutorials use that environment. See the
[README](https://github.com/rhugman/gw-source#readme) and the
[contributing guide](https://github.com/rhugman/gw-source/blob/main/CONTRIBUTING.md).
