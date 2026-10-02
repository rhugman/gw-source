"""Reshape per-cell results to the model grid and save them: npz, netCDF, GeoPackage, CSV.

Grid shapes and dimensions:
- DIS: (nlay, nrow, ncol), dims (layer, row, col);
- DISV: (nlay, ncpl), dims (layer, icell2d);
- DISU and hand-built graphs: (nodes,), dim (node).
Index coordinates are 1-based, as in MODFLOW. Inactive cells are NaN.

npz keys are '<output>__<group>' for per-group arrays, '<output>__<group>__<package>' for the
by-term splits and '<output>_<statistic>__<group>' for transient statistics.

netCDF (xarray; optional dependency, extra 'export'): one variable per output with dims
(group, *grid) and (group, package, *grid) for the by-term splits; transient statistics are
'<output>_<statistic>' (group, *grid), and the analysed steps form a 'time' dimension (totim,
kstp, kper, weight, the per-step group inflow and, with keep_series, every step's outputs).
Variables carry long_name and units (from the model's LENGTH_UNITS and TIME_UNITS when known);
the 'provenance' attribute records the package version, model files, steps and options.

GeoPackage (FloPy modelgrid -> geopandas; optional): one polygon layer per model layer
('layer_1', ...) for DIS and DISV, one layer 'nodes' for DISU, with one column per output and
group. DISU needs cell vertices in the binary grid file; without them export fails with a
clear message.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .diagnostics import cycle_ids, cycle_table
from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult
from .solve import Cycle

KEY_SEP = "__"
BACKWARD_ARRAYS = (
    "fraction_through",
    "volume_through",
    "flux_through",
    "volume_from",
    "fraction_from_cell_input",
    "fraction_from_total",
    "flux_from",
)
BACKWARD_SPLITS = ("volume_from_by_term",)
FORWARD_ARRAYS = ("source_fraction", "volume_through", "volume_to")
FORWARD_SPLITS = ("volume_to_by_term",)
GRID_DIMS = {"DIS": ("layer", "row", "col"), "DISV": ("layer", "icell2d")}
LENGTH_SYMBOLS = {"meters": "m", "feet": "ft", "centimeters": "cm"}
TIME_SYMBOLS = {"seconds": "s", "minutes": "min", "hours": "h", "days": "d", "years": "yr"}
OUTPUT_INFO = {  # name: (long name, unit kind)
    "fraction_through": ("fraction of the water through the cell that reaches the group", "1"),
    "volume_through": ("rate of water through the cell reaching (or from) the group", "volume"),
    "flux_through": ("volume_through per unit cell plan area", "flux"),
    "volume_from": ("rate of water entering in the cell that reaches the group", "volume"),
    "volume_from_by_term": ("volume_from split by inflow package", "volume"),
    "fraction_from_cell_input": ("fraction of the cell's inflow terms that reaches the group", "1"),
    "fraction_from_total": ("cell share of all water reaching the group", "1"),
    "flux_from": ("volume_from per unit cell plan area", "flux"),
    "source_fraction": ("fraction of the water in the cell that came from the group", "1"),
    "volume_to": ("rate of water leaving in the cell that came from the group", "volume"),
    "volume_to_by_term": ("volume_to split by outflow package", "volume"),
}
STAT_INFO = {
    "min": "minimum over time steps",
    "max": "maximum over time steps",
    "mean": "weighted mean over time steps",
    "asn": "always (1) / sometimes (0.5) / never (0) above the threshold",
    "probability_in_range": "weighted share of time steps within the value range",
    "exceedance_count": "number of time steps above the threshold",
}


# ---------------------------------------------------------------- arrays and npz


def to_grid(step: FlowStep, values: np.ndarray) -> np.ndarray:
    """Return per-cell values reshaped to the grid, with inactive cells set to NaN."""
    values = np.asarray(values, dtype=float)
    assert values.shape == (step.n_cells,), "expected one value per cell"
    out = np.where(step.active, values, np.nan)
    return out.reshape(step.grid_shape)


def _output_names(result: BackwardResult | ForwardResult) -> tuple[tuple, tuple]:
    """Return (per-group output names, by-term split names) of a result type."""
    if isinstance(result, BackwardResult):
        return BACKWARD_ARRAYS, BACKWARD_SPLITS
    return FORWARD_ARRAYS, FORWARD_SPLITS


def result_arrays(step: FlowStep, result: BackwardResult | ForwardResult) -> dict[str, np.ndarray]:
    """Return every per-cell output as gridded arrays keyed '<output>__<group>[__<package>]'."""
    names, splits = _output_names(result)
    arrays = {}
    for name in names:
        per_group = getattr(result, name)
        for group, values in (per_group or {}).items():
            arrays[KEY_SEP.join((name, group))] = to_grid(step, values)
    for name in splits:
        for group, by_package in getattr(result, name).items():
            for package, values in by_package.items():
                arrays[KEY_SEP.join((name, group, package))] = to_grid(step, values)
    return arrays


def transient_arrays(result) -> dict[str, np.ndarray]:
    """Return every transient statistic as gridded arrays keyed '<output>_<stat>__<group>'."""
    arrays = {}
    for stat, by_output in result.stats.items():
        for output, by_group in by_output.items():
            for group, values in by_group.items():
                key = KEY_SEP.join((f"{output}_{stat}", group))
                arrays[key] = to_grid(result.template, values)
    return arrays


def _grid_extras(step: FlowStep) -> dict[str, np.ndarray]:
    """Return the active mask and (if known) the cell area as gridded arrays."""
    extras = {"active": step.active.reshape(step.grid_shape)}
    if step.area is not None:
        extras["area"] = to_grid(step, step.area)
    return extras


def save_npz(path: str | Path, step: FlowStep, result: BackwardResult | ForwardResult) -> Path:
    """Save a result's gridded arrays, the active mask, cell area and cycle ids to a .npz."""
    path = Path(path)
    arrays = result_arrays(step, result)
    arrays.update(_grid_extras(step))
    arrays["cycle_id"] = cycle_ids(step.n_cells, result.cycles).reshape(step.grid_shape)
    np.savez_compressed(path, **arrays)
    return path


def save_transient_npz(path: str | Path, result) -> Path:
    """Save a transient result's statistics, step table, active mask and area to a .npz."""
    path = Path(path)
    arrays = transient_arrays(result)
    arrays.update(_grid_extras(result.template))
    arrays["kstpkper"] = np.asarray(result.steps, dtype=np.int64)
    arrays["totim"] = result.totim
    arrays["weights"] = result.weights
    np.savez_compressed(path, **arrays)
    return path


def save_cycle_report(path: str | Path, cycles: list[Cycle]) -> Path:
    """Write a cycle report (diagnostics.cycle_report) to CSV, one row per cycle."""
    import csv

    path = Path(path)
    rows = cycle_table(cycles)
    fields = list(rows[0]) if rows else ["cycle", "n_cells", "circulation", "cells"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


# ---------------------------------------------------------------- netCDF


def grid_dims(step: FlowStep) -> tuple[str, ...]:
    """Return the dimension names of the grid of a step."""
    return GRID_DIMS.get(step.grid_type, ("node",))


def grid_coords(step: FlowStep) -> dict[str, np.ndarray]:
    """Return 1-based index coordinates of the grid dimensions."""
    return {d: np.arange(1, n + 1) for d, n in zip(grid_dims(step), step.grid_shape)}


def unit_string(step: FlowStep, kind: str) -> str:
    """Return a units string ('1', volume rate, flux, area or time) from the model's units."""
    if kind in ("1", "count"):
        return "1"
    units = step.notes.get("units", {})
    length = LENGTH_SYMBOLS.get(units.get("length", ""), "L")
    time = TIME_SYMBOLS.get(units.get("time", ""), "T")
    symbols = {
        "volume": f"{length}3 {time}-1",
        "flux": f"{length} {time}-1",
        "area": f"{length}2",
        "time": time,
    }
    return symbols[kind]


def _attrs(step: FlowStep, output: str, stat: str | None = None) -> dict[str, str]:
    """Return long_name and units attributes of an output (and statistic)."""
    long_name, kind = OUTPUT_INFO.get(output, (output, "1"))
    if stat is None:
        return {"long_name": long_name, "units": unit_string(step, kind)}
    if stat in ("asn", "probability_in_range", "exceedance_count"):
        kind = "1"
    return {"long_name": f"{long_name}: {STAT_INFO[stat]}", "units": unit_string(step, kind)}


def _gridded_stack(
    step: FlowStep, per_group: dict[str, np.ndarray], groups: list[str]
) -> np.ndarray:
    """Return (group, *grid) values, NaN for inactive cells."""
    return np.stack([to_grid(step, per_group[g]) for g in groups])


def _split_stack(
    step: FlowStep, by_term: dict[str, dict[str, np.ndarray]], groups: list[str]
) -> tuple[list[str], np.ndarray]:
    """Return (packages, (group, package, *grid) values); missing package splits are 0."""
    packages = sorted({p for g in groups for p in by_term[g]})
    zeros = np.zeros(step.n_cells)
    data = np.stack(
        [np.stack([to_grid(step, by_term[g].get(p, zeros)) for p in packages]) for g in groups]
    )
    return packages, data


def provenance(step: FlowStep, extra: dict) -> str:
    """Return a JSON provenance string: package version, model files, time and options."""
    from . import __version__

    record = {
        "package": "gwsource",
        "version": __version__,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": step.notes.get("model"),
        "grb_file": step.notes.get("grb_file"),
        "budget_file": step.notes.get("budget_file"),
        "grid_type": step.grid_type,
        **extra,
    }
    return json.dumps(record, default=str)


def _base_dataset(step: FlowStep, groups: list[str]):
    """Return an xarray Dataset with grid and group coordinates, active mask and area."""
    import xarray as xr

    dims = grid_dims(step)
    ds = xr.Dataset(coords={"group": np.asarray(groups, dtype=object), **grid_coords(step)})
    ds["active"] = (dims, step.active.reshape(step.grid_shape).astype(np.int8))
    ds["active"].attrs = {"long_name": "active cell (IDOMAIN > 0)", "units": "1"}
    if step.area is not None:
        ds["area"] = (dims, to_grid(step, step.area))
        ds["area"].attrs = {"long_name": "cell plan area", "units": unit_string(step, "area")}
    return ds


def to_dataset(step: FlowStep, result: BackwardResult | ForwardResult):
    """Return an xarray Dataset of every output of a single-step result."""
    groups = result.groups
    dims = grid_dims(step)
    ds = _base_dataset(step, groups)
    names, splits = _output_names(result)
    for name in names:
        per_group = getattr(result, name)
        if per_group is None:
            continue
        ds[name] = (("group", *dims), _gridded_stack(step, per_group, groups))
        ds[name].attrs = _attrs(step, name)
    for name in splits:
        packages, data = _split_stack(step, getattr(result, name), groups)
        ds = ds.assign_coords(package=np.asarray(packages, dtype=object))
        ds[name] = (("group", "package", *dims), data)
        ds[name].attrs = _attrs(step, name)
    inflow = (
        result.destination_inflow if isinstance(result, BackwardResult) else result.source_inflow
    )
    inflow_name = "destination_inflow" if isinstance(result, BackwardResult) else "source_inflow"
    ds[inflow_name] = (("group",), np.array([inflow[g] for g in groups]))
    ds[inflow_name].attrs = {
        "long_name": "group sink (or source) term total",
        "units": unit_string(step, "volume"),
    }
    ds["cycle_id"] = (dims, cycle_ids(step.n_cells, result.cycles).reshape(step.grid_shape))
    ds["cycle_id"].attrs = {
        "long_name": "index of the flow cycle the cell belongs to (-1: none)",
        "units": "1",
    }
    mode = "backward" if isinstance(result, BackwardResult) else "forward"
    ds.attrs = {
        "title": f"gwsource {mode} trace",
        "provenance": provenance(
            step,
            {
                "mode": mode,
                "steps": [step.kstpkper],
                "totim": [step.totim],
                "accounting": result.accounting,
                "solver_used": result.solver_used,
            },
        ),
    }
    return ds


def _add_time(ds, result):
    """Add the step table (time dimension) and per-step group inflow to a transient Dataset."""
    steps = np.asarray(result.steps, dtype=np.int64).reshape(-1, 2)
    ds = ds.assign_coords(
        time=("time", result.totim), kstp=("time", steps[:, 0] + 1), kper=("time", steps[:, 1] + 1)
    )
    ds["time"].attrs = {
        "long_name": "simulation time at the end of the step (totim)",
        "units": unit_string(result.template, "time"),
    }
    ds["step_weight"] = (("time",), result.weights)
    ds["step_weight"].attrs = {
        "long_name": f"step weight ({result.config.weighting} weighting)",
        "units": "1",
    }
    ds["group_inflow"] = (
        ("time", "group"),
        np.column_stack([result.group_inflow[g] for g in result.groups]),
    )
    ds["group_inflow"].attrs = {
        "long_name": "group sink (or source) term total per step",
        "units": unit_string(result.template, "volume"),
    }
    return ds


def transient_dataset(result):
    """Return an xarray Dataset of a transient result's statistics (and series, if kept)."""
    step, groups = result.template, result.groups
    dims = grid_dims(step)
    ds = _add_time(_base_dataset(step, groups), result)
    for stat, by_output in result.stats.items():
        for output, per_group in by_output.items():
            name = f"{output}_{stat}"
            ds[name] = (("group", *dims), _gridded_stack(step, per_group, groups))
            ds[name].attrs = _attrs(step, output, stat)
    for output, per_group in (result.series or {}).items():
        data = np.stack([per_group[g] for g in groups], axis=1)  # (time, group, cells)
        data = np.where(step.active, data, np.nan).reshape(
            len(result.steps), len(groups), *step.grid_shape
        )
        ds[output] = (("time", "group", *dims), data)
        ds[output].attrs = _attrs(step, output)
    config = result.config
    ds.attrs = {
        "title": f"gwsource {result.mode} trace, statistics over time steps",
        "provenance": provenance(
            step,
            {
                "mode": result.mode,
                "steps": result.steps,
                "weighting": config.weighting,
                "threshold": config.threshold,
                "value_range": config.value_range,
                "test_output": result.test_output,
                "accounting": result.trace_config.accounting,
            },
        ),
    }
    return ds


def to_netcdf(path: str | Path, step_or_result, result=None) -> Path:
    """Write a single-step result (step, result) or a TransientResult to a netCDF file."""
    path = Path(path)
    if result is None:
        ds = transient_dataset(step_or_result)
    else:
        ds = to_dataset(step_or_result, result)
    ds.to_netcdf(path)
    return path


# ---------------------------------------------------------------- GeoPackage


def cell_polygons(grb_file: str | Path):
    """Return a GeoDataFrame of cell polygons from the binary grid file (FloPy modelgrid).

    One row per cell of a layer for DIS and DISV, one per node for DISU.
    """
    import flopy

    grb = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False)
    assert grb.grid_type != "DISU" or grb.verts is not None, (
        f"{grb_file} has no cell vertices: GeoPackage export of a DISU grid needs VERTICES and "
        "CELL2D in the DISU input (the binary grid file then carries them)"
    )
    return grb.modelgrid.to_geodataframe()


def _layer_index(step: FlowStep) -> dict[str, np.ndarray]:
    """Return 1-based index columns of the cells of one layer (DIS: row, col; DISV: icell2d)."""
    if step.grid_type == "DIS":
        _, nrow, ncol = step.grid_shape
        return {
            "row": np.repeat(np.arange(1, nrow + 1), ncol),
            "col": np.tile(np.arange(1, ncol + 1), nrow),
        }
    return {"icell2d": np.arange(1, step.grid_shape[1] + 1)}


def _layer_frames(step: FlowStep, polygons, arrays: dict[str, np.ndarray], crs=None):
    """Yield (layer name, GeoDataFrame) with one column per array, per model layer."""
    flat = {k: np.asarray(v, dtype=float).reshape(-1) for k, v in arrays.items()}
    active = step.active.astype(np.int8)
    if step.grid_type not in ("DIS", "DISV"):
        assert len(polygons) == step.n_cells, "grid file polygons do not match the step's grid"
        columns = {"node": np.arange(1, step.n_cells + 1), "active": active, **flat}
        yield "nodes", _frame(polygons, columns, crs)
        return
    nlay = step.grid_shape[0]
    ncpl = step.n_cells // nlay
    assert len(polygons) == ncpl, "grid file polygons do not match the step's grid"
    for k in range(nlay):
        cells = slice(k * ncpl, (k + 1) * ncpl)
        columns = {"layer": np.full(ncpl, k + 1), **_layer_index(step), "active": active[cells]}
        columns.update({key: values[cells] for key, values in flat.items()})
        yield f"layer_{k + 1}", _frame(polygons, columns, crs)


def _frame(polygons, columns: dict[str, np.ndarray], crs=None):
    """Return a GeoDataFrame with the polygons' geometry, the given columns and a CRS."""
    import geopandas as gpd

    crs = polygons.crs if crs is None else crs
    return gpd.GeoDataFrame(columns, geometry=polygons.geometry.values, crs=crs)


def to_geopackage(path: str | Path, step_or_result, result=None, grb_file=None, crs=None) -> Path:
    """Write a single-step result (step, result) or a TransientResult to a GeoPackage.

    crs (e.g. 'EPSG:2193') sets the layer CRS; the grid file has none.
    """
    path = Path(path)
    if result is None:
        step, arrays = step_or_result.template, transient_arrays(step_or_result)
    else:
        step, arrays = step_or_result, result_arrays(step_or_result, result)
    grb_file = grb_file or step.notes.get("grb_file")
    assert grb_file is not None, "pass grb_file= (the step was not read from a model)"
    polygons = cell_polygons(grb_file)
    if path.exists():
        path.unlink()
    for layer, frame in _layer_frames(step, polygons, arrays, crs):
        frame.to_file(path, layer=layer, driver="GPKG")
    return path


# ---------------------------------------------------------------- quick-look map


def plot_map(
    grb_file: str | Path, step: FlowStep, values: np.ndarray, layer: int = 0, ax=None, **kwargs
):
    """Draw a quick-look map of per-cell values with FloPy's PlotMapView; return the collection."""
    import flopy

    modelgrid = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False).modelgrid
    pmv = flopy.plot.PlotMapView(modelgrid=modelgrid, layer=layer, ax=ax)
    gridded = to_grid(step, values)
    return pmv.plot_array(np.ma.masked_invalid(gridded), **kwargs)
