"""Reader checks on the MF6 test models: node numbering, sign convention, geometry, file lookup."""

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.flowstep import connection_rows
from gwsource.mf6io import polygon_areas

STEADY = ("m1_dis", "m2_dis3lay", "m3_disv", "m4_disu_vert", "m4_disu_novert", "m5_xt3d")


def mf6_diagonal(step: gs.FlowStep) -> np.ndarray:
    """Return the diagonal entries of FLOW-JA-FACE per cell (0 for empty rows)."""
    rows = connection_rows(step.ia)
    diag = rows == step.ja
    out = np.zeros(step.n_cells)
    out[rows[diag]] = step.flowja[diag]
    return out


@pytest.mark.parametrize("key", STEADY + ("m6_transient",))
def test_sign_convention_and_residual(key, model_run):
    """Off-diagonal inflow plus all external terms (positive = into cell) closes every cell budget.

    The per-cell residual is tiny compared with the cell throughflow, and equals what MF6 stores
    in the diagonal of FLOW-JA-FACE. Checked on every saved step of the transient model.
    """
    run = model_run(key)
    for kstpkper in gs.available_steps(run.budget_file):
        step = gs.read_step(run.ws, kstpkper=kstpkper)
        budget = cell_budget(step, flow_edges(step))
        scale = np.maximum(budget.inflow, budget.outflow)
        assert np.all(np.abs(budget.residual) <= 1e-8 * np.maximum(scale, 1.0))
        np.testing.assert_allclose(budget.residual, mf6_diagonal(step), atol=1e-12)
        np.testing.assert_array_equal(budget.residual[~step.active], 0.0)


@pytest.mark.parametrize("key", ["m1_dis", "m4_disu_vert", "m4_disu_novert", "m5_xt3d"])
def test_inactive_cells_are_isolated_user_nodes(key, model_run):
    """IDOMAIN = 0 cells keep empty rows, no connection points at them, and no term sits in them."""
    run = model_run(key)
    step = gs.read_step(run.ws)
    spec = run.notes["spec"]
    inactive = [r * spec.ncol + c for r, c in spec.inactive_cells]
    assert np.flatnonzero(~step.active).tolist() == sorted(inactive)
    assert np.all(np.diff(step.ia)[inactive] == 0)
    assert not np.isin(step.ja, inactive).any()
    assert not np.isin(step.term_cell, inactive).any()


def test_package_terms_use_user_nodes(model_run):
    """WEL sits in the user node of (row 10, col 17) although six lower-numbered cells are inactive."""
    run = model_run("m1_dis")
    step = gs.read_step(run.ws)
    wel = gs.select(step, package="WEL")
    spec = run.notes["spec"]
    assert step.term_cell[wel.terms].tolist() == [spec.wel_cell[0] * spec.ncol + spec.wel_cell[1]]
    assert step.term_flow[wel.terms].tolist() == [spec.wel_rate]


def test_grid_shapes_and_areas(model_run):
    """Grid shapes per type; areas from DELR x DELC, vertices, or the DISU input."""
    ncpl = model_run("m3_disv").notes["ncpl"]
    expected = {  # key: (grid type, shape, total plan area of all cells)
        "m1_dis": ("DIS", (1, 20, 30), 1.5e6),
        "m2_dis3lay": ("DIS", (3, 15, 25), 3 * 1250.0 * 750.0),
        "m3_disv": ("DISV", (1, ncpl), 1.5e6),
        "m4_disu_vert": ("DISU", (600,), 1.5e6),
        "m4_disu_novert": ("DISU", (600,), 1.5e6),
    }
    for key, (grid_type, shape, total_area) in expected.items():
        step = gs.read_step(model_run(key).ws)
        assert step.grid_type == grid_type and step.grid_shape == shape
        assert step.area.sum() == pytest.approx(total_area)


def test_disu_area_sources(model_run):
    """DISU with vertices takes area from the grid file; without, read_step_files gives None."""
    with_vert = model_run("m4_disu_vert")
    no_vert = model_run("m4_disu_novert")
    files = gs.find_model_files(no_vert.ws)
    assert gs.read_step_files(files.grb_file, files.budget_file).area is None
    files = gs.find_model_files(with_vert.ws)
    np.testing.assert_array_equal(gs.read_step_files(files.grb_file, files.budget_file).area, 2500.0)


def test_find_model_files(model_run):
    """Name-file parsing finds the binary grid and budget files written by the model."""
    run = model_run("m3_disv")
    files = gs.find_model_files(run.ws)
    assert files.grb_file == run.grb_file and files.budget_file == run.budget_file
    assert files.dis_type == "DISV" and files.model.lower() == "m3_disv"


def test_transient_steps_and_storage_terms(model_run):
    """The transient model lists 13 steps and reads STO-SS / STO-SY as array terms."""
    run = model_run("m6_transient")
    steps = gs.available_steps(run.budget_file)
    assert len(steps) == 13 and steps[0] == (0, 0) and steps[-1] == (3, 3)
    step = gs.read_step(run.ws, kstpkper=(0, 1))
    assert {"STO-SS", "STO-SY"} <= set(step.package_names)
    sy = gs.select(step, package="STO-SY")
    assert sy.terms.sum() == step.active.sum()


def test_polygon_areas():
    """Shoelace areas of a unit square and a closed right triangle."""
    vertices = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [2.0, 0.0]])
    iavert = np.array([0, 4, 8])
    javert = np.array([0, 1, 2, 3, 1, 4, 2, 1])  # second polygon repeats its first vertex
    np.testing.assert_allclose(polygon_areas(vertices, iavert, javert), [1.0, 0.5])
