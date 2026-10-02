"""Exports and reshaping of network results: per model (split models) and package-node tables."""

import csv

import numpy as np
import pytest
from test_multimodel import split_run  # noqa: F401  (module-scoped fixture)

import gwsource as gs
from gwsource.export import save_network, to_grid

xr = pytest.importorskip("xarray")
gpd = pytest.importorskip("geopandas")


def test_to_grid_per_model(split_run):  # noqa: F811
    """A split network reshapes to each model's own grid; several models need model=."""
    _, ws, _ = split_run("m1_dis")
    net = gs.read_network(ws)
    res = gs.backward(net, {"wel": gs.select(net, package="WEL")})
    for name in net.model_names:
        block = net.block(name)
        grid = to_grid(net, res.fraction_through["wel"], model=name)
        assert grid.shape == block.grid_shape
    with pytest.raises(AssertionError, match="several models"):
        to_grid(net, res.fraction_through["wel"])


def test_save_network_split(split_run, tmp_path):  # noqa: F811
    """save_network writes one npz per model whose arrays match the network result."""
    _, ws, _ = split_run("m1_dis")
    net = gs.read_network(ws)
    res = gs.backward(net, {"wel": gs.select(net, package="WEL")})
    written = save_network(tmp_path, net, res, geopackage=True)
    npz = sorted(p.name for p in written if p.suffix == ".npz")
    assert npz == [f"trace_{m}.npz" for m in net.model_names]
    for name in net.model_names:
        data = np.load(tmp_path / f"trace_{name}.npz")
        np.testing.assert_array_equal(
            data["fraction_through__wel"],
            to_grid(net, res.fraction_through["wel"], model=name),
        )
    layers = gpd.list_layers(tmp_path / "trace.gpkg")["name"].tolist()
    assert sorted(layers) == sorted(f"{m}_layer_1" for m in net.model_names)
    with pytest.raises(AssertionError, match="several models"):
        gs.export.save_npz(tmp_path / "x.npz", net, res)


def test_save_network_package_nodes(model_run, tmp_path):
    """Package-node results go to CSV and to a GeoPackage point layer; cells to their grid."""
    run = model_run("m7_mover")
    net = gs.read_network(run.ws, package_nodes=("SFR",), boundnames=True)
    res = gs.backward(net, {"well": gs.select(net, boundnames=["well_east"])})
    written = save_network(tmp_path, net, res, geopackage=True)
    assert {p.name for p in written} == {"trace_m7_mover.npz", "trace_packages.csv", "trace.gpkg"}
    with (tmp_path / "trace_packages.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 20 and rows[0]["package"] == "SFR" and rows[0]["id"] == "1"
    reaches = net.block("SFR").nodes
    np.testing.assert_allclose(
        [float(r["fraction_through__well"]) for r in rows], res.fraction_through["well"][reaches]
    )
    spec = run.notes["spec"]
    x = [float(r["x"]) for r in rows]
    np.testing.assert_allclose(x, (spec.riv_col + 0.5) * spec.delr)  # reach in its cell centre
    points = gpd.read_file(tmp_path / "trace.gpkg", layer="package_nodes")
    assert len(points) == 20 and points.geometry.geom_type.eq("Point").all()


def test_single_model_network_exports(model_run, tmp_path):
    """The single-result exports accept a one-model network and write its cells."""
    run = model_run("m8_maw")
    net = gs.read_network(run.ws, package_nodes=("MAW",))
    step = gs.read_step(run.ws)
    res = gs.backward(net, {"pump": gs.select(net, package="MAW", term="RATE")})
    path = gs.export.to_netcdf(tmp_path / "maw.nc", net, res)
    with xr.open_dataset(path) as ds:
        assert ds["fraction_through"].shape == (1, *step.grid_shape)
        np.testing.assert_array_equal(
            ds["fraction_through"].values[0], to_grid(net, res.fraction_through["pump"])
        )
    gs.export.save_npz(tmp_path / "maw.npz", net, res)
    assert np.load(tmp_path / "maw.npz")["fraction_through__pump"].shape == step.grid_shape
