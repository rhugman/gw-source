"""Transient tracking on hand-built graphs: analytical reservoir, duality, closure and balances.

The random networks change their edges, sources, sinks and storage from step to step (and have
flow cycles), so the sparsity pattern and term table differ between steps, as in MF6 output.
"""

from dataclasses import dataclass, replace

import numpy as np
import pytest

import gwsource as gs
from gwsource import tracking as tr

RTOL = 1e-12


@dataclass
class ListReader:
    """A reader over a list of hand-built FlowSteps (one step per stress period)."""

    step_list: list
    deltas: list

    @property
    def steps(self) -> list[tuple[int, int]]:
        """(kstp, kper) of every step."""
        return [(0, i) for i in range(len(self.step_list))]

    def step_length(self, kstpkper: tuple[int, int]) -> float:
        """Length of a step."""
        return self.deltas[kstpkper[1]]

    def read(self, kstpkper: tuple[int, int]) -> gs.FlowStep:
        """Return a step."""
        return self.step_list[kstpkper[1]]


def reservoir_reader(volume: float, q: float, deltas: list[float]) -> ListReader:
    """Return one fully mixed node with inflow q (package IN) and outflow q (package OUT)."""
    steps, time = [], 0.0
    packages = [gs.Package("IN", "IN"), gs.Package("OUT", "OUT")]
    for delt in deltas:
        time += delt
        steps.append(
            gs.from_edges(
                1, [], [], [], term_cell=[0, 0], term_flow=[q, -q], term_package=[0, 1],
                packages=packages, area=np.ones(1), saturated_thickness=np.full(1, volume),
                totim=time,
            )
        )
    return ListReader(steps, deltas)


def test_single_reservoir_matches_implicit_euler():
    """c^n = (V c^(n-1) + dt q) / (V + dt q) for one mixed reservoir, forward and adjoint."""
    volume, q, deltas = 50.0, 2.0, [1.0, 5.0, 10.0, 3.0]
    reader = reservoir_reader(volume, q, deltas)
    config = tr.TrackingConfig(porosity=1.0, initial_water={"old": "all"})
    fwd = tr.track_forward(reader, {"in": {"package": "IN"}}, config)
    c, c_old = 0.0, 1.0
    for n, delt in enumerate(deltas):
        c = (volume * c + delt * q) / (volume + delt * q)
        c_old = volume * c_old / (volume + delt * q)
        assert np.isclose(fwd.source_fraction["in"][n, 0], c, rtol=RTOL)
        assert np.isclose(fwd.source_fraction["old"][n, 0], c_old, rtol=RTOL)
    bwd = tr.track_backward(reader, {"out": {"package": "OUT"}}, config)
    w = 0.0
    for n in range(len(deltas) - 1, -1, -1):
        w = (deltas[n] * q + volume * w) / (volume + deltas[n] * q)
        assert np.isclose(bwd.fraction_through["out"][n, 0], w, rtol=RTOL)
    total_out = q * sum(deltas)
    assert np.isclose(tr.backward_closure(bwd, "out").lhs, total_out, rtol=RTOL)


PACKAGES = [
    gs.Package("A", "A"),
    gs.Package("B", "B"),
    gs.Package("WEL", "WEL"),
    gs.Package("DRN", "DRN"),
    gs.Package("STO-SY", "STO-SY"),
]


def random_step(rng, n: int, time: float, delt: float, residual: float) -> gs.FlowStep:
    """Return a random step: cyclic edges, sources A/B, sinks WEL/DRN, storage closing the budget.

    residual: size of the random budget residual left in each node (0: storage closes exactly).
    """
    src = rng.integers(0, n, 3 * n)
    dst = rng.integers(0, n, 3 * n)
    keep = src != dst
    pairs = {(int(a), int(b)) for a, b in zip(src[keep], dst[keep])}
    pairs = [(a, b) for a, b in pairs if (b, a) not in pairs or a < b]
    src, dst = np.array(pairs).T
    q = rng.uniform(0.1, 1.0, len(src))
    cells = rng.permutation(n)
    term_cell = np.concatenate([cells[:3], cells[3:5], cells[5:8], cells[2:4], np.arange(n)])
    package = np.concatenate([[0] * 3, [1] * 2, [2] * 3, [3] * 2, [4] * n])
    flow = np.concatenate([rng.uniform(0.5, 2.0, 5), -rng.uniform(0.5, 2.0, 5), np.zeros(n)])
    edge_net = np.bincount(dst, q, n) - np.bincount(src, q, n)
    term_net = np.bincount(term_cell[:10], flow[:10], n)
    flow[10:] = -(edge_net + term_net) + residual * rng.normal(size=n)
    volume = rng.uniform(40.0, 80.0, n) + delt * np.abs(flow[10:])
    return gs.from_edges(
        n, src, dst, q, term_cell=term_cell, term_flow=flow, term_package=package,
        packages=PACKAGES, area=np.ones(n), saturated_thickness=volume, totim=time,
    )


def random_reader(seed: int, residual: float = 0.0, n: int = 15) -> ListReader:
    """Return a reader over 6 random steps of varying length."""
    rng = np.random.default_rng(seed)
    deltas = [0.5, 2.0, 1.0, 4.0, 1.5, 3.0]
    times = np.cumsum(deltas)
    steps = [random_step(rng, n, t, d, residual) for t, d in zip(times, deltas)]
    return ListReader(steps, deltas)


SOURCES = {"a": {"package": "A"}, "b": {"package": "B"}}
DESTINATIONS = {"wel": {"package": "WEL"}, "drn": {"package": "DRN"}}
INITIAL = {"all": "all", "first": [0, 1, 2]}


def run_both(reader, mode: str, correction: bool, solver: str = "auto"):
    """Return forward and backward tracking runs with the standard groups."""
    config = tr.TrackingConfig(
        porosity=1.0, volume_mode=mode, flow_error_correction=correction, solver=solver,
        initial_water=INITIAL,
    )
    fwd = tr.track_forward(reader, SOURCES, config, sinks=DESTINATIONS)
    bwd = tr.track_backward(reader, DESTINATIONS, config, sources=SOURCES)
    return fwd, bwd


@pytest.mark.parametrize("mode", tr.VOLUME_MODES)
@pytest.mark.parametrize("correction", [True, False])
@pytest.mark.parametrize("solver", ["auto", "lu"])
def test_random_network_duality_and_closure(mode, correction, solver):
    """Forward tagged outflow equals the adjoint inner product; closure and balances exact."""
    reader = random_reader(seed=7, residual=0.05)
    fwd, bwd = run_both(reader, mode, correction, solver)
    if solver == "auto":
        assert "block" in fwd.solver_used and "block" in bwd.solver_used  # the graphs cycle
    for d in DESTINATIONS:
        for s in [*SOURCES, *INITIAL]:
            check = tr.tracking_duality(fwd, s, bwd, d)
            assert check.rhs > 0.0
            assert check.relative_error < 1e-12, (s, d, check)
        assert tr.backward_closure(bwd, d).relative_error < 1e-12
        if not correction:  # the residual term is what closes the closure without correction
            assert abs(tr.backward_closure(bwd, d).error_without_residual) > 1e-6
    for g in fwd.groups:
        assert tr.forward_balance_error(fwd, g) < 1e-13


@pytest.mark.parametrize("mode", tr.VOLUME_MODES)
def test_partition_of_unity_and_tagging_everything(mode):
    """All sources and initial water tagged gives c = 1; adjoint fractions add up to 1."""
    reader = random_reader(seed=11, residual=0.0)
    config = tr.TrackingConfig(porosity=1.0, volume_mode=mode, initial_water={"init": "all"})
    fwd = tr.track_forward(reader, {"src": {"package": ["A", "B"]}}, config)
    total = fwd.source_fraction["src"] + fwd.source_fraction["init"]
    assert np.allclose(total, 1.0, rtol=0, atol=1e-13)
    bwd = tr.track_backward(reader, DESTINATIONS, config)
    any_sink = bwd.fraction_through["wel"] + bwd.fraction_through["drn"]
    assert np.allclose(bwd.fraction_any_sink, any_sink, atol=1e-14)
    assert np.all(bwd.fraction_through["wel"] >= -1e-15)
    assert np.all(bwd.fraction_to_other_sinks("wel") >= -1e-15)
    unaccounted = bwd.fraction_unaccounted
    if mode == "flow":  # tagged water is conserved: everything ends at a sink or in storage
        assert np.nanmax(np.abs(unaccounted)) < 1e-13
        assert np.all(fwd.volume_jump == 0.0)
    else:  # volumes jump between steps (here the random volumes are unrelated step to step)
        assert np.nanmax(np.abs(unaccounted)) > 1e-3
        assert fwd.volume_jump[1:].min() > 0.0
    assert fwd.water_balance_error.max() < 1e-12


def test_flow_mode_carries_volume_from_storage():
    """Flow mode: V^old of a step is V^new of the previous one; V^new = V^old - dt S."""
    reader = random_reader(seed=3)
    config = tr.TrackingConfig(porosity=1.0, volume_mode="flow")
    first = reader.read((0, 0))
    flows = tr.step_flows(first)
    start = tr.gwt_volumes(first, flows, 1.0, reader.deltas[0]).old
    volume = start.copy()
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        flows = tr.step_flows(step)
        volumes = tr.step_volumes(step, flows, config, reader.step_length(kstpkper),
                                  None if kstpkper[1] == 0 else volume)
        assert np.allclose(volumes.old, volume, rtol=1e-14)
        volume = volumes.old - reader.step_length(kstpkper) * flows.storage
        assert np.allclose(volumes.new, volume, rtol=1e-14)


def test_storage_terms_are_not_sources():
    """Groups selected by cells leave out storage terms; storage is volume, not a source."""
    reader = random_reader(seed=5)
    config = tr.TrackingConfig(porosity=1.0, initial_water={"init": "all"})
    by_cells = tr.track_forward(reader, lambda s: {"c": gs.select_cells(s, np.arange(15))}, config)
    by_package = tr.track_forward(reader, {"c": {"package": ["A", "B"]}}, config)
    assert np.allclose(by_cells.source_fraction["c"], by_package.source_fraction["c"], atol=1e-15)
    assert "STO-SY" not in by_cells.outflow_by_package["c"]


def test_missing_step_is_rejected():
    """A gap in time (a step not saved) stops the run."""
    reader = random_reader(seed=1)
    reader.step_list = reader.step_list[:2] + reader.step_list[3:]
    reader.deltas = reader.deltas[:2] + reader.deltas[3:]
    with pytest.raises(AssertionError, match="BUDGET ALL"):
        tr.track_forward(reader, SOURCES, tr.TrackingConfig(porosity=1.0))


def test_negative_flow_volume_is_rejected():
    """Flow mode stops when the storage change would empty a node below zero."""
    volume, q = 10.0, 2.0
    packages = [gs.Package("IN", "IN"), gs.Package("STO-SY", "STO-SY")]
    steps = []
    for k, time in enumerate((1.0, 2.0)):
        storage = 0.0 if k == 0 else 30.0  # release 30 per unit time, more than the volume
        steps.append(
            gs.from_edges(
                1, [], [], [], term_cell=[0, 0], term_flow=[q, storage],
                term_package=[0, 1], packages=packages, area=np.ones(1),
                saturated_thickness=np.full(1, volume), totim=time,
            )
        )
    reader = ListReader(steps, [1.0, 1.0])
    config = tr.TrackingConfig(porosity=1.0, volume_mode="flow", flow_error_correction=False)
    with pytest.raises(AssertionError, match="negative"):
        tr.track_forward(reader, {"in": {"package": "IN"}}, config)


# ---------------------------------------------------------------- transport sub-steps


def test_substeps_single_reservoir():
    """m sub-steps per flow step are m implicit-Euler steps of dt/m, forward and adjoint."""
    volume, q, deltas, m = 50.0, 2.0, [1.0, 5.0, 10.0, 3.0], 4
    reader = reservoir_reader(volume, q, deltas)
    config = tr.TrackingConfig(porosity=1.0, initial_water={"old": "all"}, substeps=m)
    sinks = {"out": {"package": "OUT"}}
    fwd = tr.track_forward(reader, {"in": {"package": "IN"}}, config, sinks=sinks)
    c, out = 0.0, 0.0
    for n, delt in enumerate(deltas):
        dt, out = delt / m, 0.0
        for _ in range(m):
            c = (volume * c + dt * q) / (volume + dt * q)
            out += dt * q * c
        assert np.isclose(fwd.source_fraction["in"][n, 0], c, rtol=RTOL)
        assert np.isclose(fwd.outflow_to["out"]["in"][n], out, rtol=RTOL)
    bwd = tr.track_backward(reader, {"out": {"package": "OUT"}}, config)
    w = 0.0
    for n in range(len(deltas) - 1, -1, -1):
        dt = deltas[n] / m
        for _ in range(m):
            w = (dt * q + volume * w) / (volume + dt * q)
        assert np.isclose(bwd.fraction_through["out"][n, 0], w, rtol=RTOL)
    assert np.isclose(tr.backward_closure(bwd, "out").lhs, q * sum(deltas), rtol=RTOL)


@pytest.mark.parametrize("mode", tr.VOLUME_MODES)
@pytest.mark.parametrize("correction", [True, False])
def test_substeps_duality_closure_and_balance(mode, correction):
    """With sub-steps the duality, closure and tagged balances stay exact (storage changes)."""
    reader = random_reader(seed=7, residual=0.05)
    config = tr.TrackingConfig(
        porosity=1.0, volume_mode=mode, flow_error_correction=correction,
        initial_water=INITIAL, substeps=3,
    )
    fwd = tr.track_forward(reader, SOURCES, config, sinks=DESTINATIONS)
    bwd = tr.track_backward(reader, DESTINATIONS, config, sources=SOURCES)
    plain = tr.track_forward(reader, SOURCES, tr.TrackingConfig(porosity=1.0, volume_mode=mode))
    assert not np.allclose(fwd.source_fraction["a"], plain.source_fraction["a"], atol=1e-6)
    for d in DESTINATIONS:
        for s in [*SOURCES, *INITIAL]:
            assert tr.tracking_duality(fwd, s, bwd, d).relative_error < 1e-12, (s, d)
        assert tr.backward_closure(bwd, d).relative_error < 1e-12
    for g in fwd.groups:
        assert tr.forward_balance_error(fwd, g) < 1e-13


def steady_reader(seed: int, repeat: int) -> ListReader:
    """Return random steps without storage (closure term relabelled), each repeated `repeat`
    times with 1/repeat of its length, so the flows are constant within each original step."""
    base = random_reader(seed, residual=0.0)
    packages = PACKAGES[:4] + [gs.Package("GHB", "GHB")]
    steps, deltas, time = [], [], 0.0
    for step, delt in zip(base.step_list, base.deltas):
        for _ in range(repeat):
            time += delt / repeat
            steps.append(replace(step, packages=packages, totim=time))
            deltas.append(delt / repeat)
    return ListReader(steps, deltas)


def substep_refinement_pairs(m: int = 3) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Return (output, with m sub-steps, with m times more flow steps) for every compared output.

    The coarse run uses m transport sub-steps per flow step; the fine run a flow model with m
    times more steps of the same flows. Fractions are compared at the end of each coarse step,
    outflows and volumes summed over the m fine steps.
    """
    coarse, fine = steady_reader(9, 1), steady_reader(9, m)
    config = tr.TrackingConfig(porosity=1.0, initial_water={"init": "all"}, substeps=m)
    plain = tr.TrackingConfig(porosity=1.0, initial_water={"init": "all"})
    fwd_c = tr.track_forward(coarse, SOURCES, config, sinks=DESTINATIONS)
    fwd_f = tr.track_forward(fine, SOURCES, plain, sinks=DESTINATIONS)
    pairs = []
    for g in fwd_c.groups:
        pairs.append((f"c {g}", fwd_c.source_fraction[g], fwd_f.source_fraction[g][m - 1 :: m]))
        for d in DESTINATIONS:
            per_step = fwd_f.outflow_to[d][g].reshape(-1, m).sum(axis=1)
            pairs.append((f"outflow {g} to {d}", fwd_c.outflow_to[d][g], per_step))
    bwd_c = tr.track_backward(coarse, DESTINATIONS, config, sources=SOURCES)
    bwd_f = tr.track_backward(fine, DESTINATIONS, plain, sources=SOURCES)
    for d in DESTINATIONS:
        pairs.append((f"w {d}", bwd_c.fraction_through[d], bwd_f.fraction_through[d][::m]))
        for s in SOURCES:
            per_step = bwd_f.volume_from_group[d][s].reshape(-1, m).sum(axis=1)
            pairs.append((f"volume from {s} to {d}", bwd_c.volume_from_group[d][s], per_step))
    return pairs


def test_substeps_equal_refined_flow_steps():
    """Sub-steps give the same result as a flow model with m times more steps of equal flows."""
    for name, coarse, fine in substep_refinement_pairs(m=3):
        atol = 1e-14 if name[0] in "cw" else 0.0
        np.testing.assert_allclose(coarse, fine, rtol=1e-12, atol=atol, err_msg=name)
