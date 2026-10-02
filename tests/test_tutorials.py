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
