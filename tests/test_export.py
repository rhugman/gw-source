"""netCDF and GeoPackage export: write, read back and compare, on DIS, DISV and DISU grids."""

import json

import numpy as np
import pytest

import gwsource as gs
from gwsource.export import result_arrays, to_grid

xr = pytest.importorskip("xarray")
gpd = pytest.importorskip("geopandas")

GRID_DIMS = {
    "m1_dis": ("layer", "row", "col"),
    "m2_dis3lay": ("layer", "row", "col"),
    "m3_disv": ("layer", "icell2d"),
    "m4_disu_vert": ("node",),
}


def traced(run) -> tuple[gs.FlowStep, gs.BackwardResult]:
    """Return a step and its backward result for one group per package."""
    step = gs.read_step(run.ws)
    return step, gs.backward(step, gs.groups_by_package(step))


@pytest.mark.parametrize("key", ["m1_dis", "m3_disv", "m4_disu_vert"])
def test_netcdf_round_trip(key, model_run, tmp_path):
    """Every output (and by-term split) reads back equal, with grid dims, units and provenance."""
    step, res = traced(model_run(key))
    path = gs.export.to_netcdf(tmp_path / "out.nc", step, res)
    with xr.open_dataset(path) as ds:
        dims = GRID_DIMS[key]
        assert ds["fraction_through"].dims == ("group", *dims)
        assert list(ds["group"].values) == res.groups
        for name, values in result_arrays(step, res).items():
            output, group, *package = name.split("__")
            data = ds[output].sel(group=group)
            if package:
                data = data.sel(package=package[0])
            np.testing.assert_array_equal(data.values, values, err_msg=name)
        np.testing.assert_array_equal(
            ds["active"].values.astype(bool), step.active.reshape(step.grid_shape)
        )
        assert ds["fraction_through"].attrs["units"] == "1"
        assert ds["volume_from"].attrs["units"].endswith("d-1")
        record = json.loads(ds.attrs["provenance"])
        assert record["package"] == "gwsource" and record["steps"] == [[0, 0]]
        assert record["budget_file"].endswith(".cbc") and record["grid_type"] == step.grid_type


def test_netcdf_forward_result(model_run, tmp_path):
    """Forward results export their own outputs and the source inflow."""
    step = gs.read_step(model_run("m1_dis").ws)
    res = gs.forward(step, {"rch": gs.select(step, package="RCH")})
    with xr.open_dataset(gs.export.to_netcdf(tmp_path / "fwd.nc", step, res)) as ds:
        np.testing.assert_array_equal(
            ds["source_fraction"].sel(group="rch").values, to_grid(step, res.source_fraction["rch"])
        )
        assert float(ds["source_inflow"].sel(group="rch")) == res.source_inflow["rch"]
        assert ds["source_inflow"].attrs["long_name"].startswith("water entering through")
        assert "source_throughflow" not in ds


def test_dataset_net_inflow_and_throughflow(model_run):
    """Net results export the inflow under a net label and the throughflow sum beside it."""
    step = gs.read_step(model_run("m1_dis").ws)
    groups = {"wel": gs.select(step, package="WEL")}
    net = gs.TraceConfig(accounting="net")
    back, fwd = gs.backward(step, groups, net), gs.forward(step, groups, net)
    results = {"destination": back, "source": fwd}
    for prefix, res in results.items():
        ds = gs.export.to_dataset(step, res)
        inflow = getattr(res, f"{prefix}_inflow")["wel"]
        throughflow = getattr(res, f"{prefix}_throughflow")["wel"]
        assert float(ds[f"{prefix}_inflow"].sel(group="wel")) == inflow
        assert float(ds[f"{prefix}_throughflow"].sel(group="wel")) == throughflow
        assert "each passage counted once" in ds[f"{prefix}_inflow"].attrs["long_name"]


@pytest.mark.parametrize("key", ["m1_dis", "m2_dis3lay", "m3_disv", "m4_disu_vert"])
def test_geopackage_round_trip(key, model_run, tmp_path):
    """Columns read back equal per layer, and each polygon is the right cell (area, centroid)."""
    run = model_run(key)
    step, res = traced(run)
    path = gs.export.to_geopackage(tmp_path / "out.gpkg", step, res)
    arrays = {k: v.reshape(-1) for k, v in result_arrays(step, res).items()}
    nlay = step.grid_shape[0] if step.grid_type != "DISU" else 1
    ncpl = step.n_cells // nlay
    layers = [f"layer_{k + 1}" for k in range(nlay)] if step.grid_type != "DISU" else ["nodes"]
    for k, layer in enumerate(layers):
        frame = gpd.read_file(path, layer=layer)
        cells = slice(k * ncpl, (k + 1) * ncpl)
        assert len(frame) == ncpl
        for name, values in arrays.items():
            np.testing.assert_array_equal(
                frame[name].to_numpy(dtype=float), values[cells], err_msg=name
            )
        np.testing.assert_allclose(frame.geometry.area.to_numpy(), step.area[cells], rtol=1e-9)
    if step.grid_type == "DIS":
        frame = gpd.read_file(path, layer="layer_1")
        delr, ly = 50.0, 50.0 * step.grid_shape[1]
        np.testing.assert_allclose(frame.geometry.centroid.x, (frame["col"] - 0.5) * delr)
        np.testing.assert_allclose(frame.geometry.centroid.y, ly - (frame["row"] - 0.5) * delr)


def test_geopackage_disu_without_vertices_fails_clearly(model_run, tmp_path):
    """A DISU grid without vertices cannot be mapped: the error says why."""
    step, res = traced(model_run("m4_disu_novert"))
    with pytest.raises(AssertionError, match="no cell vertices"):
        gs.export.to_geopackage(tmp_path / "out.gpkg", step, res)


def test_transient_exports_round_trip(model_run, tmp_path):
    """Transient statistics, the step table and kept series read back from netCDF and GeoPackage."""
    reader = gs.open_model(model_run("m6_transient").ws)
    groups = {"wel": {"package": "WEL"}, "riv": {"package": "RIV"}}
    config = gs.TransientConfig(threshold=0.1, value_range=(0.1, 1.0), keep_series=True)
    res = gs.trace_transient(reader, groups, config=config)
    step = res.template
    with xr.open_dataset(gs.export.to_netcdf(tmp_path / "t.nc", res)) as ds:
        assert ds.sizes["time"] == 13
        np.testing.assert_allclose(ds["time"].values, res.totim)
        np.testing.assert_array_equal(ds["kper"].values, [p + 1 for _, p in res.steps])
        np.testing.assert_array_equal(ds["step_weight"].values, res.weights)
        np.testing.assert_array_equal(
            ds["group_inflow"].sel(group="wel").values, res.group_inflow["wel"]
        )
        for stat in ("min", "max", "mean", "asn", "probability_in_range", "exceedance_count"):
            np.testing.assert_array_equal(
                ds[f"fraction_through_{stat}"].sel(group="riv").values,
                to_grid(step, res.stats[stat]["fraction_through"]["riv"]),
            )
        series = ds["fraction_through"].sel(group="wel").values
        assert series.shape == (13, *step.grid_shape)
        np.testing.assert_array_equal(
            series[4], to_grid(step, res.series["fraction_through"]["wel"][4])
        )
        assert ds["time"].attrs["units"] == "d"
        assert json.loads(ds.attrs["provenance"])["weighting"] == "time"
    frame = gpd.read_file(gs.export.to_geopackage(tmp_path / "t.gpkg", res), layer="layer_1")
    np.testing.assert_array_equal(
        frame["fraction_through_mean__wel"].to_numpy(dtype=float),
        to_grid(step, res.stats["mean"]["fraction_through"]["wel"]).ravel(),
    )
