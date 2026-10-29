"""Tutorial notebooks run top to bottom, and the shared tutorial helpers build a working model.

The notebook tests are marked 'tutorials' and deselected by default (pytest -m tutorials runs
them). Each notebook is read into memory and executed with nbclient in its own folder (so its
relative paths and the tutorials/_work workspaces resolve as they do in Jupyter); the executed
copy is written to tmp_path, never over the committed notebook and its outputs.
"""

from pathlib import Path

import numpy as np
import pytest

import gwsource as gs

TUTORIALS_DIR = Path(__file__).resolve().parents[1] / "tutorials"
NOTEBOOKS = sorted(TUTORIALS_DIR.glob("[0-9][0-9]_*/*.ipynb"))
CELL_TIMEOUT = 600  # seconds per cell


def execute_notebook(path: Path, out_dir: Path) -> Path:
    """Execute a notebook in its own folder and write the executed copy to out_dir."""
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb, timeout=CELL_TIMEOUT, kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()
    out = out_dir / path.name
    nbformat.write(nb, out)
    return out


@pytest.mark.tutorials
@pytest.mark.parametrize("path", NOTEBOOKS, ids=[p.parent.name for p in NOTEBOOKS])
def test_notebook_runs(path, tmp_path):
    """The notebook executes without errors."""
    assert execute_notebook(path, tmp_path).is_file()


def test_tutorials_found():
    """At least the quickstart notebook exists and is picked up by the notebook test."""
    assert TUTORIALS_DIR / "01_quickstart" / "01_quickstart.ipynb" in NOTEBOOKS


def test_quickstart_builder(tmp_path, mf6_exe):
    """The quickstart model runs; the well's water comes from recharge, the west edge and stream."""
    import herebedragons as hbd

    run = hbd.build_quickstart(tmp_path, mf6_exe)
    assert run.grb_file.is_file() and run.budget_file.is_file() and run.head_file.is_file()
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=["supply_well"])
    res = gs.backward(step, {"well": well})
    rate = -sum(rate for _, _, rate in run.spec.wells)
    assert res.volume_from["well"].sum() == pytest.approx(rate, rel=1e-8)
    table = hbd.volume_from_table(res, "well")
    assert set(table.index) == {"RCH", "SFR", "CHD"}
    assert np.all(table["share"] > 0.05)
    assert hbd.feature_cells(step, "SFR").size == run.spec.nrow
    assert run.info["sfr_budget_file"].is_file()


def test_voronoi_builder(tmp_path, mf6_exe):
    """The vorflow DISV model centres the well cell on the well and the stream cells on the stream.

    Its stream reaches add up to the stream's length, and the well's water closes on the pumping.
    """
    pytest.importorskip("vorflow")
    import herebedragons as hbd

    run = hbd.build_voronoi(tmp_path, mf6_exe)
    spec = run.spec
    step = gs.read_step(run.ws, boundnames=True)
    centres = gs.export.cell_centres(run.grb_file)
    well_node = run.info["well_nodes"]["supply_well"]
    assert np.allclose(centres[well_node], spec.xy(spec.wells[0][1]))
    assert np.allclose(centres[run.info["stream_cells"], 0], hbd.stream_x(spec))
    reaches = run.gwf.get_package("sfr").packagedata.get_data()
    assert reaches["rlen"].sum() == pytest.approx(spec.ly, rel=1e-12)
    res = gs.backward(step, {"well": gs.select(step, boundnames=["supply_well"])})
    assert res.volume_from["well"].sum() == pytest.approx(800.0, rel=1e-8)


def load_tutorial_helpers(folder: str):
    """Import a tutorial's own helpers.py under a unique module name (each tutorial has one)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        f"helpers_{folder}", TUTORIALS_DIR / folder / "helpers.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bedekar_builder(tmp_path, mf6_exe):
    """Tutorial 10's model has the published rates and the published long-time shares at the well.

    Bedekar et al. (2024), p. 305-306: 454.5 m3/d lateral inflow, 306.03 m3/d recharge, 700 m3/d
    pumped from period 2; after 25 years about 48 % lateral inflow, 29 % recharge, 23 % stream.
    """
    helpers = load_tutorial_helpers("10_unit_concentration")
    run = helpers.build_bedekar(tmp_path, mf6_exe, nstp=25)
    reader = gs.open_model(run.ws, boundnames=True)
    first = helpers.package_budget(reader.read(reader.steps[0]))
    last_step = reader.read(reader.steps[-1])
    last = helpers.package_budget(last_step)
    assert first.loc["INFLOW", "in"] == pytest.approx(454.5, rel=1e-8)
    assert first.loc["RCH", "in"] == pytest.approx(306.03, rel=1e-8)
    assert first.loc["RIV", "in"] == pytest.approx(0.0, abs=1e-8)  # the stream is only a sink
    assert last.loc["PUMP", "out"] == pytest.approx(700.0, rel=1e-8)
    assert last.loc["RIV", "in"] > 100.0 and last.loc["RIV", "out"] > 100.0
    names = {"INFLOW": "lateral inflow", "RCH": "recharge", "RIV": "stream"}
    shares = helpers.steady_shares(last_step, helpers.WELL, names)
    assert shares["lateral inflow"] == pytest.approx(0.48, abs=0.01)
    assert shares["recharge"] == pytest.approx(0.29, abs=0.01)
    assert shares["stream"] == pytest.approx(0.23, abs=0.01)


def test_dispersion_problem_a(tmp_path, mf6_exe):
    """Tutorial 11's problem A pumps 500 m3/d and its F > 0.5 zone is close to the analytical zone.

    On 100 m cells with the flow along the rows, the study gives an F > 0.5 area 6.9 % larger than
    the zone of Javandel and Tsang (1986) and a band 0.1 < F < 0.9 of 3.3 cells.
    """
    helpers = load_tutorial_helpers("11_numerical_dispersion")
    import herebedragons as hbd

    spec = helpers.ProblemA()
    raster = helpers.make_raster(spec.lx, spec.ly, 2.5, 200.0)
    raster.set_reference(helpers.capture_zone_mask(raster.xr, raster.yr, spec))
    run = helpers.problem_a_run(tmp_path, mf6_exe, hbd.exe_path("triangle"), spec, "DIS", 100.0, raster)
    res = gs.backward(run["step"], helpers.well_group(run["step"]))
    assert res.destination_inflow[helpers.WELL] == pytest.approx(500.0, rel=1e-8)
    rows = {r["method"]: r for r in helpers.metrics_rows({}, run, raster)}
    assert rows["full mixing"]["area_err_0.5"] == pytest.approx(0.0686, abs=2e-3)
    assert rows["full mixing"]["band_cells"] == pytest.approx(3.33, abs=0.02)
    assert rows["cell-averaged exact"]["band_cells"] < 1.0
