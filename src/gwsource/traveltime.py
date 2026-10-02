"""Eulerian mean travel time (backward) and mean age (forward) under full mixing (PLAN §2.6).

Water volume and residence time
-------------------------------
The water volume of cell i is V_i = porosity_i x area_i x saturated thickness_i (FlowStep
.saturated_thickness: DATA-SAT x (top - bot), or from heads; confined cells fully saturated; see
gwsource.mf6io). A fully mixed cell is a well-mixed reservoir: the time a parcel spends in it is
exponentially distributed with mean tau_i = V_i / O_i (backward; O_i = gross outflow) or
tau_i = V_i / I_i (forward; I_i = gross inflow); the two are equal when the cell budget closes.
Cells with O_i = 0 (or I_i = 0) have no residence time (NaN) and take no part.
Package nodes of a network step (gwsource.network) have their own water volume
(FlowStep.fixed_volume: SFR reach, lake, MAW well or UZF cell volume from the package budget's
STORAGE VOLUME), so the identities below hold over cells and package nodes alike.

Backward: mean travel time to a destination group
-------------------------------------------------
Let T be the time from a parcel entering cell i until it leaves the model, and D the event
"it leaves through a sink term of the destination group". Under full mixing the residence time
R_i in cell i is independent of the route by which the parcel leaves it, so with
m_i = E[T 1_D] (the capture-weighted expected time) and P_ij = q_ij / O_i:

    m_i = E[R_i] P(D) + sum_j P_ij m_j  =>  (I - P) m = tau o F

the same matrix as the backward solve (I - P) F = S D, factorised once (BackwardResult.factor)
and reused with one extra right-hand side per group. The conditional mean travel time is

    mean_time_i = m_i / F_i      (NaN where F_i <= fraction_threshold)

It is the mean time from entering cell i (from a neighbour or a source term) until leaving the
model through a destination sink term, and it includes the residence in the cell where the
water leaves (for a well, its own cell). mean_time_to_exit_cell removes that last residence:
x solves (I - P) x = tau o (S D) (the expected residence in the cell of exit, weighted by the
probability of exiting there through the destination), and (m - x) / F is the mean time until
the water enters the cell through whose sink term it leaves. Particle trackers that stop
particles on entering a sink cell (MF6 PRT, MODPATH) measure the latter.

Exact identity (backward). Multiply row i of the m-equation by O_i (tau_i O_i = V_i) and sum
over all cells; the intercell terms cancel exactly as in the closure identity
(gwsource.diagnostics), leaving, with Src_i the source total and r_i = I_i - O_i the residual:

    sum_i Src_i m_i - sum_i r_i m_i = sum_i V_i F_i

Since sum_i Src_i F_i - sum_i r_i F_i = Q_D (destination inflow), the flux-weighted mean
travel time of all water reaching the destination, sum Src m / sum Src F, equals
sum V F / Q_D up to the residual terms: the water volume that ends at the destination divided
by the destination inflow (a turnover time). For mean_time_to_exit_cell the right-hand side
is sum V F - sum_i tau_i d_i (d_i the destination sink flow in cell i).

Forward: mean age of water from a source group
----------------------------------------------
With Q_ij = q_ji / I_i, tau_i = V_i / I_i and G the source fraction, n_i = E[A 1_S] (A the age
of water leaving cell i since it entered the model, 1_S that it entered through the source
group) satisfies (I - Q) n = tau o G, with the forward matrix. mean_time_i = n_i / G_i is the
mean age of the water in cell i (equal to that of the water leaving it, under full mixing) that
came from the group, including its residence in cell i. Identity, with Snk_i the sink total:

    sum_i Snk_i n_i + sum_i r_i n_i = sum_i V_i G_i

so the flux-weighted mean age at all sinks of the water from the group is sum V G / Q_S.

These are means over the mixed distribution, not first advective arrivals: they complement
particle tracking for time-of-travel zone criteria rather than replacing it.
"""

from dataclasses import dataclass

import numpy as np

from .assemble import (
    cell_budget,
    flow_edges,
    gross_backward_system,
    gross_forward_system,
    group_term_flows,
)
from .diagnostics import Check
from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult
from .network import global_values
from .solve import Factor, factorize, isolate_closed_loops

DEFAULT_FRACTION_THRESHOLD = 1e-10


@dataclass
class TravelTimeResult:
    """Per-group mean travel times (backward) or ages (forward); arrays have one value per cell.

    weighted_time: m (backward) or n (forward), the fraction-weighted expected time.
    mean_time: m / F or n / G where the fraction exceeds fraction_threshold, NaN elsewhere.
    mean_time_to_exit_cell: backward only, (m - x) / F (see module docstring); exit_cell_time
        holds x.
    water_volume, residence_time: per cell (residence time NaN where O or I is 0).
    group_volume: sum V F (sum V G), the water volume that ends at (came from) the group.
    group_inflow: destination (source) inflow Q of the group.
    mean_transit_time: group_volume / group_inflow.
    flux_weighted_time: sum Src m / sum Src F (backward) or sum Snk n / sum Snk G (forward), the
        flux-weighted mean over all water entering (leaving) the model; equal to
        mean_transit_time up to the budget residual.
    """

    mode: str
    fraction_threshold: float
    water_volume: np.ndarray
    residence_time: np.ndarray
    weighted_time: dict[str, np.ndarray]
    mean_time: dict[str, np.ndarray]
    mean_time_to_exit_cell: dict[str, np.ndarray] | None
    group_volume: dict[str, float]
    group_inflow: dict[str, float]
    mean_transit_time: dict[str, float]
    flux_weighted_time: dict[str, float]
    exit_cell_time: dict[str, np.ndarray] | None = None

    @property
    def groups(self) -> list[str]:
        """Group names."""
        return list(self.weighted_time)


def cell_porosity(porosity, n_cells: int) -> np.ndarray:
    """Return porosity as a per-cell array from a scalar or an array of the grid's size."""
    values = np.broadcast_to(np.asarray(porosity, dtype=float).ravel(), (n_cells,)).copy()
    assert np.all(values[np.isfinite(values)] > 0.0), "porosity must be positive"
    return values


def water_volume(step: FlowStep, porosity) -> np.ndarray:
    """Return V = porosity x area x saturated thickness per cell (0 in inactive cells).

    Nodes with a fixed volume (package nodes of a network step) take it instead. porosity may
    also be a dict {model: per-cell porosity} for a network step.
    """
    assert step.area is not None, (
        "travel times need cell areas: DIS/DISV give them; for DISU without vertices pass area= "
        "or read the step with open_model/read_step (AREA from the DISU input)"
    )
    assert step.saturated_thickness is not None, (
        "travel times need the saturated thickness: save DATA-SAT (NPF SAVE_SATURATION) or heads, "
        "or set FlowStep.saturated_thickness"
    )
    if isinstance(porosity, dict):
        porosity = global_values(step, porosity, fill=1.0)
    pore = cell_porosity(porosity, step.n_cells)
    volume = pore * step.area * step.saturated_thickness
    if step.fixed_volume is not None:
        volume = np.where(np.isfinite(step.fixed_volume), step.fixed_volume, volume)
    return np.where(step.active, volume, 0.0)


def residence_time(volume: np.ndarray, throughflow: np.ndarray) -> np.ndarray:
    """Return tau = V / throughflow, NaN where the throughflow is 0."""
    return np.divide(volume, throughflow, out=np.full(volume.shape, np.nan), where=throughflow > 0)


def _system_factor(step: FlowStep, result, mode: str) -> Factor:
    """Return the result's stored factorisation, or rebuild it (closed loops isolated)."""
    if result.factor is not None:
        return result.factor
    edges = flow_edges(step)
    budget = cell_budget(step, edges)
    build = gross_backward_system if mode == "backward" else gross_forward_system
    matrix, rhs = build(step, edges, budget, result.selections)
    matrix, _, loops = isolate_closed_loops(matrix, rhs)
    factor = factorize(matrix)
    factor.zero_rows = np.concatenate(loops) if loops else None
    return factor


def _ratio(num: np.ndarray, frac: np.ndarray, threshold: float) -> np.ndarray:
    """Return num / frac where frac > threshold, NaN elsewhere."""
    return np.divide(num, frac, out=np.full(num.shape, np.nan), where=frac > threshold)


def _safe_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """Return num / den elementwise, NaN where den is 0."""
    return np.divide(num, den, out=np.full(np.shape(num), np.nan), where=den > 0)


def _time_rhs(
    tau: np.ndarray, frac: np.ndarray, group_flow: np.ndarray, through: np.ndarray, mode: str
) -> np.ndarray:
    """Return the right-hand sides tau o F (one per group), plus tau o (S D) when backward."""
    rhs = tau[:, None] * frac
    if mode == "forward":
        return rhs
    exit_share = _safe_ratio(group_flow, through[:, None])
    return np.hstack([rhs, tau[:, None] * np.nan_to_num(exit_share)])


def travel_time(
    step: FlowStep,
    result: BackwardResult | ForwardResult,
    porosity,
    fraction_threshold: float = DEFAULT_FRACTION_THRESHOLD,
) -> TravelTimeResult:
    """Return mean travel times (BackwardResult) or mean ages (ForwardResult) of every group.

    porosity: scalar or one value per cell (required; there is no default). The result must be
    a gross-accounting trace of this step; its factorisation is reused when it has one.
    """
    assert result.accounting == "gross", "travel times are defined for gross accounting only"
    mode = "backward" if isinstance(result, BackwardResult) else "forward"
    volume = water_volume(step, porosity)
    budget = cell_budget(step, flow_edges(step))
    through = budget.outflow if mode == "backward" else budget.inflow
    tau = residence_time(volume, through)
    names = list(result.selections)
    frac = np.column_stack([_group_fraction(result, g) for g in names])
    group_flow = group_term_flows(step, result.selections, -1 if mode == "backward" else +1)
    rhs = _time_rhs(np.nan_to_num(tau), frac, group_flow, through, mode)
    solution = _system_factor(step, result, mode).solve(rhs).reshape(step.n_cells, -1)
    weighted = solution[:, : len(names)]
    entry_flow = budget.source if mode == "backward" else budget.sink
    group_volume, group_inflow = volume @ frac, group_flow.sum(axis=0)
    flux_weighted = _safe_ratio(entry_flow @ weighted, entry_flow @ frac)
    exit_time = to_exit = None
    if mode == "backward":
        x = solution[:, len(names) :]
        exit_time = {g: x[:, i] for i, g in enumerate(names)}
        to_exit = {
            g: _ratio(weighted[:, i] - x[:, i], frac[:, i], fraction_threshold)
            for i, g in enumerate(names)
        }
    return TravelTimeResult(
        mode=mode,
        fraction_threshold=fraction_threshold,
        water_volume=volume,
        residence_time=tau,
        weighted_time={g: weighted[:, i] for i, g in enumerate(names)},
        mean_time={
            g: _ratio(weighted[:, i], frac[:, i], fraction_threshold) for i, g in enumerate(names)
        },
        mean_time_to_exit_cell=to_exit,
        group_volume=dict(zip(names, group_volume.tolist())),
        group_inflow=dict(zip(names, group_inflow.tolist())),
        mean_transit_time=dict(zip(names, _safe_ratio(group_volume, group_inflow).tolist())),
        flux_weighted_time=dict(zip(names, flux_weighted.tolist())),
        exit_cell_time=exit_time,
    )


def _group_fraction(result: BackwardResult | ForwardResult, group: str) -> np.ndarray:
    """Return the group's F (backward) or G (forward)."""
    if isinstance(result, BackwardResult):
        return result.fraction_through[group]
    return result.source_fraction[group]


def travel_time_closure(
    step: FlowStep, result: BackwardResult | ForwardResult, tt: TravelTimeResult, group: str
) -> Check:
    """Return the identity sum Src m - sum r m = sum V F (backward) or its forward analogue.

    Forward: sum Snk n + sum r n = sum V G. Check.error is zero to round-off.
    """
    budget = cell_budget(step, flow_edges(step))
    m = tt.weighted_time[group]
    entry = budget.source if tt.mode == "backward" else budget.sink
    sign = 1.0 if tt.mode == "backward" else -1.0
    return Check(
        lhs=float(entry @ m),
        rhs=float(tt.water_volume @ _group_fraction(result, group)),
        residual_term=sign * float(budget.residual @ m),
    )


def exit_cell_closure(
    step: FlowStep, result: BackwardResult, tt: TravelTimeResult, group: str
) -> Check:
    """Return sum Src (m - x) - sum r (m - x) = sum V F - sum tau d (backward only)."""
    assert tt.mode == "backward", "the exit-cell identity is for backward travel times"
    budget = cell_budget(step, flow_edges(step))
    mx = tt.weighted_time[group] - tt.exit_cell_time[group]
    tau = np.nan_to_num(tt.residence_time, nan=0.0)
    d = group_term_flows(step, {group: result.selections[group]}, sign=-1)[:, 0]
    return Check(
        lhs=float(budget.source @ mx),
        rhs=float(tt.water_volume @ result.fraction_through[group] - tau @ d),
        residual_term=float(budget.residual @ mx),
    )
