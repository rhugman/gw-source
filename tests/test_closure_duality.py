"""Closure, duality and boundary-control identities on every steady test model and on model 6 steps.

Gross accounting identities (derived in gwsource.diagnostics), with r the per-cell residual:
    backward:  sum(volume_from) - sum(F r) = destination sink inflow
    forward:   sum(volume_to) + sum(G r) = source inflow
    duality:   flow S->D by backward - flow S->D by forward = sum(F G r)
They must hold to 1e-10 relative with the residual term, and to within the model's total budget
error sum(|r|) without it.
"""

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.diagnostics import backward_closure, budget_error, duality, forward_closure

STEADY = ("m1_dis", "m2_dis3lay", "m3_disv", "m4_disu_vert", "m4_disu_novert", "m5_xt3d")
TRANSIENT_STEPS = ((0, 0), (0, 1), (3, 1), (0, 2), (2, 2), (0, 3), (3, 3))
RTOL = 1e-10


def _assert_check(check, abs_residual: float) -> None:
    """Assert an identity holds to RTOL with the residual term and to the budget error without."""
    assert abs(check.error) <= RTOL * max(abs(check.rhs), 1.0), check
    assert abs(check.error_without_residual) <= abs_residual + RTOL * max(abs(check.rhs), 1.0), check


def check_identities(step: gs.FlowStep) -> None:
    """Run backward and forward per package and check closure and every duality pair."""
    groups = gs.groups_by_package(step)
    back = gs.backward(step, groups)
    fwd = gs.forward(step, groups)
    abs_residual = budget_error(step)["abs_residual"]
    for name in groups:
        _assert_check(backward_closure(step, back, name), abs_residual)
        _assert_check(forward_closure(step, fwd, name), abs_residual)
    for dest in groups:
        for source in groups:
            _assert_check(duality(step, back, dest, fwd, source), abs_residual)
    total_sink = sum(back.destination_inflow.values())
    total_source = sum(fwd.source_inflow.values())
    assert sum(v.sum() for v in back.volume_from.values()) == pytest.approx(total_source, rel=1e-8)
    assert sum(v.sum() for v in fwd.volume_to.values()) == pytest.approx(total_sink, rel=1e-8)


def check_boundary_control(step: gs.FlowStep) -> None:
    """With one group per sink term, F sums to 1 on every cell that has outflow."""
    groups = gs.groups_by_term(step, step.term_flow < 0.0)
    res = gs.backward(step, groups)
    total = np.sum([res.fraction_through[g] for g in groups], axis=0)
    drains = cell_budget(step, flow_edges(step)).outflow > 0.0
    np.testing.assert_allclose(total[drains], 1.0, atol=1e-12)
    np.testing.assert_array_equal(total[~drains], 0.0)


@pytest.mark.parametrize("key", STEADY)
def test_steady_identities(key, model_run):
    """Closure and duality hold on every steady test model."""
    check_identities(gs.read_step(model_run(key).ws))


@pytest.mark.parametrize("kstpkper", TRANSIENT_STEPS)
def test_transient_step_identities(kstpkper, model_run):
    """Closure and duality hold on single time steps of the transient model (storage as terms)."""
    check_identities(gs.read_step(model_run("m6_transient").ws, kstpkper=kstpkper))


@pytest.mark.parametrize("key", STEADY)
def test_steady_boundary_control(key, model_run):
    """Boundary-control fractions sum to 1 on every steady test model."""
    check_boundary_control(gs.read_step(model_run(key).ws))


@pytest.mark.parametrize("kstpkper", [(0, 1), (3, 3)])
def test_transient_boundary_control(kstpkper, model_run):
    """Boundary-control fractions sum to 1 with storage sinks as destinations."""
    check_boundary_control(gs.read_step(model_run("m6_transient").ws, kstpkper=kstpkper))
