"""Model 7 (DRN -> MVR -> SFR): how *-TO-MVR records enter the aquifer-side accounting.

MF6 writes, for a provider package with MOVER, two aquifer-side records per bound: DRN (the part
of the drain outflow that leaves the model) and DRN-TO-MVR (the part handed to the mover). These
tests show that they partition the drain's head-dependent flow (no double counting), that the
cell budget only closes with both as sink terms, and that the gross identities still hold.
"""

import flopy
import numpy as np
import pytest
from test_closure_duality import check_boundary_control, check_identities
from test_mf6io import mf6_diagonal

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges


def drain_records(step: gs.FlowStep) -> dict[str, np.ndarray]:
    """Return {'DRN': q, 'DRN-TO-MVR': q} by bound number for the drain package of model 7."""
    out = {}
    for p, package in enumerate(step.packages):
        if package.text in ("DRN", "DRN-TO-MVR"):
            mask = step.term_package == p
            order = np.argsort(step.term_bound[mask])
            out[package.text] = step.term_flow[mask][order]
    return out


@pytest.mark.parametrize("kstpkper", [(0, 0), (0, 1)])
def test_mover_records_partition_drain_flow(kstpkper, model_run):
    """DRN + DRN-TO-MVR equals the drain's C (h - elev); the mover share matches its FACTOR."""
    run = model_run("m7_mover")
    step = gs.read_step(run.ws, kstpkper=kstpkper)
    records = drain_records(step)
    assert [p.name for p in step.packages if p.text.startswith("DRN")] == ["DRN", "DRN:DRN-TO-MVR"]
    heads = flopy.utils.HeadFile(str(run.head_file)).get_data(kstpkper=kstpkper).ravel()
    spec = run.notes["spec"]
    for bound, (_, (row, col), elev, cond) in enumerate(run.notes["drains"]):
        node = row * spec.ncol + col
        expected = -cond * max(heads[node] - elev, 0.0)
        total = records["DRN"][bound] + records["DRN-TO-MVR"][bound]
        assert total == pytest.approx(expected, rel=1e-6)
    shares = records["DRN-TO-MVR"] / (records["DRN"] + records["DRN-TO-MVR"])
    np.testing.assert_allclose(shares, [0.7, 1.0], rtol=1e-6)


@pytest.mark.parametrize("kstpkper", [(0, 0), (0, 1)])
def test_mover_residual_needs_to_mvr_terms(kstpkper, model_run):
    """With the TO-MVR sinks the residual matches MF6's own; without them it is off by them."""
    step = gs.read_step(model_run("m7_mover").ws, kstpkper=kstpkper)
    budget = cell_budget(step, flow_edges(step))
    scale = np.maximum(np.maximum(budget.inflow, budget.outflow), 1.0)
    assert np.all(np.abs(budget.residual) <= 1e-8 * scale)
    # MF6 computes the mover share from the provider rate at the last outer iteration, so its
    # reported residual and the records can differ at the solver tolerance (~1e-9 relative).
    np.testing.assert_array_less(np.abs(budget.residual - mf6_diagonal(step)), 1e-9 * scale)
    mover = gs.select(step, package="DRN-TO-MVR")
    without = step.term_flow.copy()
    without[mover.terms] = 0.0
    step_without = gs.FlowStep(**{**step.__dict__, "term_flow": without})
    residual_without = cell_budget(step_without, flow_edges(step_without)).residual
    cells = step.term_cell[mover.terms]
    np.testing.assert_allclose(
        residual_without[cells] - budget.residual[cells], -step.term_flow[mover.terms], rtol=1e-12
    )


@pytest.mark.parametrize("kstpkper", [(0, 0), (0, 1)])
def test_mover_model_identities(kstpkper, model_run):
    """Closure and duality hold to 1e-10 (with the residual term) and F sums to 1 on model 7."""
    step = gs.read_step(model_run("m7_mover").ws, kstpkper=kstpkper)
    check_identities(step)
    check_boundary_control(step)


def test_drain_selection_includes_mover_part(model_run):
    """'DRN' selects all water leaving through the drains; 'DRN-TO-MVR' only the moved part."""
    step = gs.read_step(model_run("m7_mover").ws)
    records = drain_records(step)
    drains = gs.backward(step, {"drn": gs.select(step, package="DRN")})
    moved = gs.backward(step, {"mvr": gs.select(step, package="DRN-TO-MVR")})
    assert drains.destination_inflow["drn"] == pytest.approx(
        -(records["DRN"].sum() + records["DRN-TO-MVR"].sum())
    )
    assert moved.destination_inflow["mvr"] == pytest.approx(-records["DRN-TO-MVR"].sum())
    assert set(gs.groups_by_package(step)) == {"WEL", "DRN", "DRN:DRN-TO-MVR", "RCH", "CHD", "SFR"}
