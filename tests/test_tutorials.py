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
    """The quickstart model runs; the well's water comes from recharge, the west edge and river."""
    import herebedragons as hbd

    run = hbd.build_quickstart(tmp_path, mf6_exe)
    assert run.grb_file.is_file() and run.budget_file.is_file() and run.head_file.is_file()
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=["supply_well"])
    res = gs.backward(step, {"well": well})
    rate = -sum(rate for _, _, rate in run.spec.wells)
    assert res.volume_from["well"].sum() == pytest.approx(rate, rel=1e-8)
    table = hbd.volume_from_table(res, "well")
    assert set(table.index) == {"RCH", "RIV", "CHD"}
    assert np.all(table["share"] > 0.05)
    assert hbd.feature_cells(step, "RIV").size == run.spec.nrow


def test_voronoi_builder(tmp_path, mf6_exe):
    """The vorflow DISV model centres the well cell on the well and the river cells on the river.

    Its river conductance adds up to the DIS total, and the well's water closes on the pumping.
    """
    pytest.importorskip("vorflow")
    import herebedragons as hbd

    run = hbd.build_voronoi(tmp_path, mf6_exe)
    spec = run.spec
    step = gs.read_step(run.ws, boundnames=True)
    centres = gs.export.cell_centres(run.grb_file)
    well_node = run.info["well_nodes"]["supply_well"]
    assert np.allclose(centres[well_node], spec.xy(spec.wells[0][1]))
    riv_x = (spec.riv_col + 0.5) * spec.delr
    assert np.allclose(centres[run.info["riv_cells"], 0], riv_x)
    riv = run.gwf.get_package("riv").stress_period_data.get_data(0)
    assert riv["cond"].sum() == pytest.approx(spec.riv_cond * spec.nrow, rel=1e-12)
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
