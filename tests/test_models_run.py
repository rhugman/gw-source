"""Build and run every test model, and check the outputs Phase 1 relies on are present."""

from pathlib import Path

import flopy
import numpy as np
import pytest
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from models import (
    MODEL_KEYS,
    build_base_dis,
    build_layered_dis,
    build_model,
    build_transient_dis,
    build_xt3d_dis,
)


def _record_names(budget_file: Path) -> list[str]:
    """Return the stripped budget record names in a budget file."""
    cbc = flopy.utils.CellBudgetFile(str(budget_file))
    return [name.strip() for name in cbc.get_unique_record_names(decode=True)]


@pytest.mark.parametrize("key", MODEL_KEYS)
def test_model_runs_and_writes_outputs(key, tmp_path, mf6_exe, triangle_exe):
    """Each model terminates normally and writes .grb, budget (with FLOW-JA-FACE) and heads."""
    run = build_model(key, tmp_path, mf6_exe, triangle_exe)
    assert run.name == key
    for path in (run.grb_file, run.budget_file, run.head_file):
        assert path.is_file(), f"missing output {path.name}"

    names = _record_names(run.budget_file)
    assert "FLOW-JA-FACE" in names
    assert "DATA-SAT" in names
    for package in ("WEL", "CHD", "RCH"):
        assert package in names, f"{package} flows not saved"

    grb = flopy.mf6.utils.MfGrdFile(str(run.grb_file), verbose=False)
    cbc = flopy.utils.CellBudgetFile(str(run.budget_file))
    flowja = cbc.get_data(text="FLOW-JA-FACE")[0]
    assert flowja.size == grb.nja, "FLOW-JA-FACE length does not match the grid's NJA"

    heads = flopy.utils.HeadFile(str(run.head_file))
    assert len(heads.get_times()) == len(cbc.get_times())


def test_transient_model_saves_storage(tmp_path, mf6_exe):
    """The transient model saves STO-SS and STO-SY for every time step."""
    run = build_transient_dis(tmp_path, mf6_exe)
    names = _record_names(run.budget_file)
    assert "STO-SS" in names and "STO-SY" in names
    cbc = flopy.utils.CellBudgetFile(str(run.budget_file))
    assert len(cbc.get_times()) == 13


def test_layered_model_has_genuine_weak_sink(tmp_path, mf6_exe):
    """The small well's cell still passes water on to its neighbours (a weak sink)."""
    run = build_layered_dis(tmp_path, mf6_exe)
    grb = flopy.mf6.utils.MfGrdFile(str(run.grb_file), verbose=False)
    cbc = flopy.utils.CellBudgetFile(str(run.budget_file))
    flowja = cbc.get_data(text="FLOW-JA-FACE")[0].ravel()
    node = run.notes["weak_well_node"]
    face_flows = flowja[grb.ia[node] + 1 : grb.ia[node + 1]]
    well_q = cbc.get_data(text="WEL")[0]
    q_weak = well_q["q"][well_q["node"] == node + 1]
    assert q_weak.size == 1 and q_weak[0] < 0.0
    outflow = -face_flows[face_flows < 0.0].sum()
    assert outflow > 10.0 * abs(q_weak[0]), "small well is not a weak sink"


def test_base_model_has_inactive_cells(tmp_path, mf6_exe):
    """Model 1 carries IDOMAIN = 0 cells, needed to check user vs reduced node numbering."""
    run = build_base_dis(tmp_path, mf6_exe)
    grb = flopy.mf6.utils.MfGrdFile(str(run.grb_file), verbose=False)
    assert np.sum(np.asarray(grb.idomain) == 0) == len(run.notes["inactive_cells"])


def _largest_flow_cycle(grb_file: Path, budget_file: Path) -> int:
    """Return the size of the largest strongly connected set of cells in the positive-flow graph."""
    grb = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False)
    flowja = flopy.utils.CellBudgetFile(str(budget_file)).get_data(text="FLOW-JA-FACE")[0].ravel()
    ia, ja = np.asarray(grb.ia), np.asarray(grb.ja)
    rows = np.repeat(np.arange(grb.nodes), np.diff(ia))
    out = (rows != ja) & (flowja < 0.0)  # negative FLOW-JA-FACE: flow out of row into ja
    graph = coo_matrix((np.ones(out.sum()), (rows[out], ja[out])), shape=(grb.nodes, grb.nodes))
    _, labels = connected_components(graph, directed=True, connection="strong")
    return int(np.bincount(labels).max())


def test_xt3d_model_has_flow_cycle(tmp_path, mf6_exe):
    """XT3D with rotated anisotropy produces at least one flow cycle; plain DIS does not."""
    xt3d = build_xt3d_dis(tmp_path / "xt3d", mf6_exe)
    base = build_base_dis(tmp_path / "base", mf6_exe)
    assert _largest_flow_cycle(xt3d.grb_file, xt3d.budget_file) > 1
    assert _largest_flow_cycle(base.grb_file, base.budget_file) == 1
