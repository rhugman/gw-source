"""Net mode reproduces the 3x3 worked example of Foley & Black (2013), Figs 5-8.

Cells A-I are the 3x3 grid (A B C / D E F / G H I), destination A. Two extra cells stand for the
area outside the picture: J sends 10 into C, and K receives the 5 that B sends out of the picture.
C's throughflow is therefore 10, as the text implies.
"""

import numpy as np
import pytest

import gwsource as gs

LABELS = "ABCDEFGHIJK"
EDGES = [  # (from, to, flow)
    ("B", "A", 5.0), ("D", "A", 5.0), ("C", "B", 5.0), ("E", "B", 5.0), ("B", "K", 5.0),
    ("E", "D", 5.0), ("C", "F", 5.0), ("F", "E", 8.0), ("I", "F", 1.0), ("H", "E", 2.0),
    ("J", "C", 10.0),
]
EXPECTED_F = {"A": 1.0, "B": 0.5, "C": 0.625, "D": 1.0, "E": 0.75, "F": 0.75, "G": 0.0, "H": 0.75, "I": 0.75}
EXPECTED_V_THROUGH = {"A": 10.0, "B": 5.0, "C": 6.25, "D": 5.0, "E": 7.5, "F": 6.0, "G": 0.0, "H": 1.5, "I": 0.75}
EXPECTED_V_FROM = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0, "F": 1.5, "G": 0.0, "H": 1.5, "I": 0.75}


def fb13_step() -> gs.FlowStep:
    """Return the worked example as a hand-built FlowStep (no external terms needed in net mode)."""
    index = {label: i for i, label in enumerate(LABELS)}
    src = [index[a] for a, _, _ in EDGES]
    dst = [index[b] for _, b, _ in EDGES]
    q = [flow for _, _, flow in EDGES]
    return gs.from_edges(len(LABELS), src, dst, q)


def _by_label(values: np.ndarray) -> dict[str, float]:
    """Return the values of cells A-I keyed by label."""
    return {label: float(values[i]) for i, label in enumerate(LABELS[:9])}


@pytest.mark.parametrize("solver", ["auto", "topological", "lu"])
def test_fb13_worked_example(solver):
    """Fraction through, volume through and volume from match the published numbers exactly."""
    step = fb13_step()
    config = gs.TraceConfig(accounting="net", solver=solver)
    res = gs.backward(step, {"A": gs.select_cells(step, [0])}, config)
    for got, expected in (
        (res.fraction_through["A"], EXPECTED_F),
        (res.volume_through["A"], EXPECTED_V_THROUGH),
        (res.volume_from["A"], EXPECTED_V_FROM),
    ):
        assert _by_label(got) == pytest.approx(expected, abs=1e-14)


def test_fb13_closure_and_outside_cells():
    """All 10 units entering A come from J (6.25) and the net sources F, H, I (3.75); K gets none."""
    step = fb13_step()
    res = gs.backward(step, {"A": gs.select_cells(step, [0])}, gs.TraceConfig(accounting="net"))
    v_from = res.volume_from["A"]
    assert v_from[LABELS.index("J")] == pytest.approx(6.25)
    assert res.fraction_through["A"][LABELS.index("K")] == 0.0
    assert v_from.sum() == pytest.approx(res.destination_inflow["A"]) == pytest.approx(10.0)
    assert res.destination_throughflow["A"] == res.destination_inflow["A"] == 10.0
    assert res.fraction_from_total["A"].sum() == pytest.approx(1.0)
    assert res.fraction_from_cell_input["A"][LABELS.index("F")] == pytest.approx(0.75)
    assert np.isnan(res.fraction_from_cell_input["A"][LABELS.index("E")])
