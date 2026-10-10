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

Network steps (gwsource.network): to_grid() reshapes one model's part (model=, optional when
the step has one model). The single-result exports above take a network step with one model
directly (its cells only); with several models use save_network(), which writes one npz per
model ('<prefix>_<model>.npz'), the package-node results as CSV ('<prefix>_packages.csv', one row
per reach, lake, well or UZF cell) and, optionally, a GeoPackage with one polygon layer per
model layer ('<model>_layer_<k>') and a point layer 'package_nodes' (each package node placed at
the mean centre of the cells it exchanges water with).

Transient tracking (gwsource.tracking): tracking_dataset() gives (time, group, *grid) variables
(time = end of step forward, start of step backward) plus the per-step balance tables, for one
model's cells; save_tracking_npz() writes one npz per step ('<prefix>_<index>.npz'), gridded for
one model or flat over every global node of a network (package nodes included).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .diagnostics import cycle_ids, cycle_table
from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult
from .network import (
    model_block,
    model_view,
    package_cells,
    package_rows,
    result_view,
    transient_view,
)
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
    "tracked_source_fraction": (
        "fraction of the water in the node at the end of the step that came from the group",
        "1",
    ),
    "tracked_fraction_through": (
        "fraction of the water in the node during the step that leaves through the group "
        "before the end of the simulation",
        "1",
    ),
    "tracked_volume_from": (
        "water entering through the node's source terms during the step that leaves through "
        "the group",
        "water",
    ),
    "fraction_any_sink": ("fraction of the water that leaves through any sink before the end", "1"),
    "fraction_in_storage_at_end": ("fraction of the water still in the model at the end", "1"),
}
TRACKING_SERIES = {  # result attribute: dataset variable
    "source_fraction": "tracked_source_fraction",
    "fraction_through": "tracked_fraction_through",
    "volume_from": "tracked_volume_from",
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


def to_grid(step: FlowStep, values: np.ndarray, model: str | None = None) -> np.ndarray:
    """Return per-cell values reshaped to the grid, with inactive cells set to NaN.

    For a network step, the part of one model (model= may be omitted if there is only one).
    """
    values = np.asarray(values, dtype=float)
    assert values.shape == (step.n_cells,), "expected one value per cell"
    if step.is_network:
        block = model_block(step, model)
        sl = slice(block.offset, block.offset + block.n)
        return np.where(step.active[sl], values[sl], np.nan).reshape(block.grid_shape)
    out = np.where(step.active, values, np.nan)
    return out.reshape(step.grid_shape)


def single_model(step: FlowStep, result):
    """Return (step, result) cut to the only model of a network step; unchanged otherwise."""
    if not step.is_network:
        return step, result
    assert len(step.model_names) == 1, (
        "several models: use save_network(), or model_view()/result_view() per model"
    )
    return model_view(step), result_view(result, step)


def single_model_transient(result):
    """Return a TransientResult cut to the only model of its network template."""
    if not result.template.is_network:
        return result
    assert len(result.template.model_names) == 1, "several models: use network.transient_view()"
    return transient_view(result)


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
    step, result = single_model(step, result)
    arrays = result_arrays(step, result)
    arrays.update(_grid_extras(step))
    arrays["cycle_id"] = cycle_ids(step.n_cells, result.cycles).reshape(step.grid_shape)
    np.savez_compressed(path, **arrays)
    return path


def save_transient_npz(path: str | Path, result) -> Path:
    """Save a transient result's statistics, step table, active mask and area to a .npz."""
    path = Path(path)
    result = single_model_transient(result)
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
        "water": f"{length}3",
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


def inflow_long_name(mode: str, accounting: str) -> str:
    """Return the long_name of a group's destination (backward) or source (forward) inflow."""
    names = {
        ("backward", "gross"): "water removed by the group's sink terms",
        ("backward", "net"): (
            "water reaching the destination cells, each passage counted once "
            "(net accounting; equals the net volume from)"
        ),
        ("forward", "gross"): "water entering through the group's source terms",
        ("forward", "net"): (
            "water leaving the source cells, each passage counted once "
            "(net accounting; equals the net volume to)"
        ),
    }
    assert (mode, accounting) in names, f"unknown mode/accounting {mode}/{accounting}"
    return names[(mode, accounting)]


def to_dataset(step: FlowStep, result: BackwardResult | ForwardResult):
    """Return an xarray Dataset of every output of a single-step result."""
    step, result = single_model(step, result)
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
        by_term = getattr(result, name)
        if not any(by_term[g] for g in groups):  # net accounting has no by-term splits
            continue
        packages, data = _split_stack(step, by_term, groups)
        ds = ds.assign_coords(package=np.asarray(packages, dtype=object))
        ds[name] = (("group", "package", *dims), data)
        ds[name].attrs = _attrs(step, name)
    backward = isinstance(result, BackwardResult)
    prefix = "destination" if backward else "source"
    mode = "backward" if backward else "forward"
    inflow = result.destination_inflow if backward else result.source_inflow
    ds[f"{prefix}_inflow"] = (("group",), np.array([inflow[g] for g in groups]))
    ds[f"{prefix}_inflow"].attrs = {
        "long_name": inflow_long_name(mode, result.accounting),
        "units": unit_string(step, "volume"),
    }
    throughflow = result.destination_throughflow if backward else result.source_throughflow
    if throughflow:
        ds[f"{prefix}_throughflow"] = (("group",), np.array([throughflow[g] for g in groups]))
        ds[f"{prefix}_throughflow"].attrs = {
            "long_name": f"sum of the {prefix} cells' throughflow (net accounting)",
            "units": unit_string(step, "volume"),
        }
    ds["cycle_id"] = (dims, cycle_ids(step.n_cells, result.cycles).reshape(step.grid_shape))
    ds["cycle_id"].attrs = {
        "long_name": "index of the flow cycle the cell belongs to (-1: none)",
        "units": "1",
    }
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
        "long_name": inflow_long_name(result.mode, result.trace_config.accounting) + ", per step",
        "units": unit_string(result.template, "volume"),
    }
    return ds


def transient_dataset(result):
    """Return an xarray Dataset of a transient result's statistics (and series, if kept)."""
    result = single_model_transient(result)
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
        transient = single_model_transient(step_or_result)
        step, arrays = transient.template, transient_arrays(transient)
    else:
        step, result = single_model(step_or_result, result)
        arrays = result_arrays(step, result)
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


# ---------------------------------------------------------------- networks


def cell_centres(grb_file: str | Path) -> np.ndarray:
    """Return the (x, y) centre of every user node from a binary grid file, shape (nodes, 2)."""
    import flopy

    grb = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False)
    grid = grb.modelgrid
    x, y = np.ravel(grid.xcellcenters), np.ravel(grid.ycellcenters)
    reps = int(grb.nodes) // x.size  # DIS and DISV: the same centres in every layer
    return np.column_stack([np.tile(x, reps), np.tile(y, reps)])


def package_points(step: FlowStep) -> dict[int, tuple[float, float]]:
    """Return {global package node: (x, y)}, the mean centre of the cells it exchanges with."""
    points = {}
    for block in step.blocks:
        if block.kind != "package":
            continue
        model = step.block(block.model)
        grb_file = step.notes.get("model_notes", {}).get(block.model, {}).get("grb_file")
        if grb_file is None:
            continue
        centres = cell_centres(grb_file)
        for node, cells in zip(block.nodes, package_cells(step, block)):
            if cells.size:
                points[int(node)] = tuple(centres[cells - model.offset].mean(axis=0))
    return points


def save_package_csv(path: str | Path, step: FlowStep, result, points=None) -> Path:
    """Write the package-node results (network.package_rows) to CSV, with x, y if known."""
    import csv

    path = Path(path)
    rows = package_rows(step, result)
    points = package_points(step) if points is None else points
    for row in rows:
        row["x"], row["y"] = points.get(row["node"], (np.nan, np.nan))
    fields = list(rows[0]) if rows else ["model", "package", "id", "node"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _package_frame(step: FlowStep, result, points, crs=None):
    """Return a GeoDataFrame of the package nodes that have a location (points)."""
    import geopandas as gpd
    from shapely.geometry import Point

    rows = [r for r in package_rows(step, result) if r["node"] in points]
    geometry = [Point(points[r["node"]]) for r in rows]
    return gpd.GeoDataFrame(rows, geometry=geometry, crs=crs)


def save_network(
    directory: str | Path,
    step: FlowStep,
    result: BackwardResult | ForwardResult,
    prefix: str = "trace",
    geopackage: bool = False,
    crs=None,
) -> list[Path]:
    """Write a network result: one npz per model, package nodes as CSV, optional GeoPackage."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    gpkg = directory / f"{prefix}.gpkg"
    if geopackage and gpkg.exists():
        gpkg.unlink()
    for model in step.model_names if step.is_network else [None]:
        view, view_result = model_view(step, model), result_view(result, step, model)
        written.append(save_npz(directory / f"{prefix}_{model or 'model'}.npz", view, view_result))
        if geopackage:
            polygons = cell_polygons(view.notes["grb_file"])
            frames = _layer_frames(view, polygons, result_arrays(view, view_result), crs)
            for layer, frame in frames:
                frame.to_file(gpkg, layer=f"{model}_{layer}", driver="GPKG")
    if any(b.kind == "package" for b in step.blocks):
        points = package_points(step)
        written.append(save_package_csv(directory / f"{prefix}_packages.csv", step, result, points))
        if geopackage and points:
            _package_frame(step, result, points, crs).to_file(
                gpkg, layer="package_nodes", driver="GPKG"
            )
    if geopackage:
        written.append(gpkg)
    return written


# ---------------------------------------------------------------- transient tracking


def _tracking_view(result, model: str | None) -> tuple[FlowStep, slice]:
    """Return the (one-model) template step of a tracking result and its node slice."""
    step = result.template
    if not step.is_network:
        return step, slice(0, step.n_cells)
    block = model_block(step, model)
    return model_view(step, block.model), slice(block.offset, block.offset + block.n)


def _tracking_series(result) -> dict[str, dict[str, np.ndarray]]:
    """Return {result attribute: {group: (n_steps, n) series}} of a tracking result."""
    assert result.config.keep_series, "export needs a tracking run with keep_series=True"
    names = [a for a in TRACKING_SERIES if hasattr(result, a)]
    return {a: getattr(result, a) for a in names}


def _tracking_time(result) -> np.ndarray:
    """Return the time of each row: end of step (forward) or start of step (backward)."""
    return result.totim if hasattr(result, "source_fraction") else result.totim - result.delt


def _gridded_series(step: FlowStep, series: np.ndarray, sl: slice) -> np.ndarray:
    """Return a (n_steps, n) node series as (n_steps, *grid), NaN on inactive cells."""
    return np.stack([to_grid(step, row[sl]) for row in series])


def _step_table(groups: list[str], per_group: dict, step: FlowStep, long_name: str) -> tuple:
    """Return a (time, group) variable of water volumes from {group: (n_steps,)} values."""
    attrs = {"long_name": long_name, "units": unit_string(step, "water")}
    return (("time", "group"), np.column_stack([per_group[g] for g in groups]), attrs)


def tracking_dataset(result, model: str | None = None):
    """Return an xarray Dataset of a transient tracking result (time, group, *grid).

    Forward: tracked_source_fraction at the end of each step and the tagged-water balance per
    step and group ('balance_<key>'). Backward: tracked_fraction_through and
    tracked_volume_from at the start of each step, fraction_any_sink,
    fraction_in_storage_at_end and the destination outflow per step. For a network, one
    model's cells (model=); package nodes are in save_tracking_npz.
    """
    step, sl = _tracking_view(result, model)
    groups, dims = result.groups, grid_dims(step)
    ds = _base_dataset(step, groups)
    steps = np.asarray(result.steps, dtype=np.int64).reshape(-1, 2)
    ds = ds.assign_coords(
        time=("time", _tracking_time(result)),
        kstp=("time", steps[:, 0] + 1),
        kper=("time", steps[:, 1] + 1),
    )
    ds["time"].attrs = {"long_name": "simulation time", "units": unit_string(step, "time")}
    ds["delt"] = (("time",), result.delt)
    for attr, per_group in _tracking_series(result).items():
        name = TRACKING_SERIES[attr]
        data = np.stack([_gridded_series(step, per_group[g], sl) for g in groups], axis=1)
        ds[name] = (("time", "group", *dims), data)
        ds[name].attrs = _attrs(step, name)
    if hasattr(result, "source_fraction"):
        for key in next(iter(result.balance.values())):
            per_group = {g: result.balance[g][key] for g in groups}
            ds[f"balance_{key}"] = _step_table(groups, per_group, step, f"tagged water: {key}")
    else:
        for name in ("fraction_any_sink", "fraction_in_storage_at_end"):
            ds[name] = (("time", *dims), _gridded_series(step, getattr(result, name), sl))
            ds[name].attrs = _attrs(step, name)
        ds["destination_outflow"] = _step_table(
            groups, result.destination_outflow, step, "water leaving through the group"
        )
    mode = "forward" if hasattr(result, "source_fraction") else "backward"
    extra = {
        "mode": f"tracking {mode}",
        "volume_mode": result.config.volume_mode,
        "flow_error_correction": result.config.flow_error_correction,
        "steps": result.steps,
    }
    ds.attrs = {
        "title": f"gwsource transient tracking, {mode}",
        "provenance": provenance(step, extra),
    }
    return ds


def _step_values(step: FlowStep, values: np.ndarray, sl: slice, flat: bool) -> np.ndarray:
    """Return one step's node values: flat (whole network) or one model's gridded cells."""
    return values[sl] if flat else to_grid(step, values[sl])


def save_tracking_npz(
    directory: str | Path, result, prefix: str = "tracking", model: str | None = None
) -> list[Path]:
    """Write one npz per time step of a tracking result ('<prefix>_<step index>.npz').

    Each file holds the step's per-node outputs as '<output>__<group>' (gridded for a single
    model; for a network with model=None, flat over all global nodes, package nodes included),
    and its kstpkper, totim and delt.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    whole = result.template.is_network and model is None
    step, sl = (result.template, slice(None)) if whole else _tracking_view(result, model)
    series = _tracking_series(result)
    if not hasattr(result, "source_fraction"):
        series["fraction_any_sink"] = {"all": result.fraction_any_sink}
        series["fraction_in_storage_at_end"] = {"all": result.fraction_in_storage_at_end}
    written = []
    for index, kstpkper in enumerate(result.steps):
        arrays = {
            KEY_SEP.join((attr, g)): _step_values(step, values[index], sl, whole)
            for attr, per_group in series.items()
            for g, values in per_group.items()
        }
        arrays.update(
            kstpkper=np.asarray(kstpkper),
            totim=result.totim[index],
            delt=result.delt[index],
            time=_tracking_time(result)[index],
        )
        path = directory / f"{prefix}_{index:04d}.npz"
        np.savez_compressed(path, **arrays)
        written.append(path)
    return written
