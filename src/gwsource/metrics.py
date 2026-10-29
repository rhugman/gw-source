"""Result containers and the per-cell metrics derived from the solved fractions.

Backward (capture) outputs per destination group g:
- fraction_through F: fraction of the water passing through the cell that reaches g.
- volume_through: F x O (gross) or F x T (net), volume rate of that water [L3/T].
- flux_through: volume_through / cell plan area [L/T] (None without areas).
- volume_from: F x (source terms of the cell) (gross) or F x max(s, 0) (net): water that enters
  the model in this cell and reaches g [L3/T].
- volume_from_by_term: volume_from split by package (gross only): F x (that package's source
  flow in the cell), e.g. recharge, river leakage, storage release.
- fraction_from_cell_input: F on cells that have source terms (net mode: net source cells),
  NaN elsewhere: the fraction of the water entering the model in the cell that reaches g
  (2013 definition, Black & Foley 2013).
- fraction_from_total: volume_from / sum(volume_from): the cell's share of all model inflow that
  reaches g; sums to 1 (later definition, Black, Foley & Witterick 2021).
- flux_from: volume_from / cell plan area.
- destination_inflow: water entering the destination: sum of |q| of the group's sink terms
  (gross) or the water reaching the destination cells with each passage counted once (net):
  sum_D T_d - sum_{D->D} q - sum_{D->not D} q f_j, which equals the net volume from. For a single
  destination cell that no water leaves and reaches again it is that cell's throughflow T. In net
  accounting it depends on the solved fractions, not on the budget alone (gwsource.assemble).
- destination_throughflow (net only, empty in gross): sum of the destination cells' throughflow
  T. For a group of several cells it counts water passing between them more than once.
- absorbing: (cells, groups) mask of the strong-sink cells that absorb in each group's solve
  (TraceConfig.strong_sinks; net mode leaves out the group's own fixed cells), None without
  strong sinks. The closure check needs it (gwsource.diagnostics).

Forward (fate) outputs per source group g:
- source_fraction G: fraction of the water in the cell that came from g (dilution ratio C/C0).
- volume_through: G x I (gross) or G x T (net).
- volume_to: G x (sink terms of the cell) (gross) or G x max(-s, 0) (net).
- volume_to_by_term: volume_to split by package (gross only).
- source_inflow: sum of the group's source terms (gross) or the water leaving the source cells
  with each passage counted once (net): sum_S T_s - sum_{S->S} q - sum_{not S->S} q g_j, which
  equals the net volume to. For a single source cell that no water leaves and comes back to it is
  that cell's throughflow T. In net accounting it depends on the solved fractions.
- source_throughflow (net only, empty in gross): sum of the source cells' throughflow T. For a
  group of several cells it counts water passing between them more than once.

Gross results also keep the factorised system matrix (factor; not picklable) so that the travel
times of gwsource.traveltime reuse it.
"""

from dataclasses import dataclass, field

import numpy as np

from .flowstep import FlowStep
from .selectors import Selection
from .solve import Cycle, Factor


@dataclass
class BackwardResult:
    """Per-group backward-tracing outputs; every array has one value per cell."""

    accounting: str
    selections: dict[str, Selection]
    fraction_through: dict[str, np.ndarray]
    volume_through: dict[str, np.ndarray]
    volume_from: dict[str, np.ndarray]
    volume_from_by_term: dict[str, dict[str, np.ndarray]]
    fraction_from_cell_input: dict[str, np.ndarray]
    fraction_from_total: dict[str, np.ndarray]
    flux_through: dict[str, np.ndarray] | None
    flux_from: dict[str, np.ndarray] | None
    destination_inflow: dict[str, float]
    destination_throughflow: dict[str, float] = field(default_factory=dict)
    solver_used: list[str] = field(default_factory=list)
    cycles: list[Cycle] = field(default_factory=list)
    closed_loops: list[np.ndarray] = field(default_factory=list)
    factor: Factor | None = field(default=None, repr=False, compare=False)
    absorbing: np.ndarray | None = None

    @property
    def groups(self) -> list[str]:
        """Group names."""
        return list(self.selections)


@dataclass
class ForwardResult:
    """Per-group forward-tracing outputs; every array has one value per cell."""

    accounting: str
    selections: dict[str, Selection]
    source_fraction: dict[str, np.ndarray]
    volume_through: dict[str, np.ndarray]
    volume_to: dict[str, np.ndarray]
    volume_to_by_term: dict[str, dict[str, np.ndarray]]
    source_inflow: dict[str, float]
    source_throughflow: dict[str, float] = field(default_factory=dict)
    solver_used: list[str] = field(default_factory=list)
    cycles: list[Cycle] = field(default_factory=list)
    closed_loops: list[np.ndarray] = field(default_factory=list)
    factor: Factor | None = field(default=None, repr=False, compare=False)

    @property
    def groups(self) -> list[str]:
        """Group names."""
        return list(self.selections)


def per_cell_by_package(step: FlowStep, sign: int) -> dict[str, np.ndarray]:
    """Return {package name: per-cell |q| of its terms with the given sign}, if it has any."""
    flow = np.maximum(sign * step.term_flow, 0.0)
    out = {}
    for p, package in enumerate(step.packages):
        mask = step.term_package == p
        if np.any(flow[mask] > 0.0):
            out[package.name] = np.bincount(
                step.term_cell[mask], weights=flow[mask], minlength=step.n_cells
            )
    return out


def divide_by_area(values: dict[str, np.ndarray], area: np.ndarray | None) -> dict | None:
    """Return each array divided by the cell area, or None if there are no areas."""
    if area is None:
        return None
    return {
        k: np.divide(v, area, out=np.full_like(v, np.nan), where=area > 0) for k, v in values.items()
    }


def share_of_total(values: np.ndarray) -> np.ndarray:
    """Return values / sum(values), or zeros if the sum is zero."""
    total = values.sum()
    return values / total if total > 0.0 else np.zeros_like(values)


def backward_metrics(
    step: FlowStep,
    selections: dict[str, Selection],
    fraction: np.ndarray,
    through: np.ndarray,
    source: np.ndarray,
    source_by_package: dict[str, np.ndarray],
    destination_inflow: np.ndarray,
    accounting: str,
) -> BackwardResult:
    """Return backward outputs from fractions (cells, groups) and the per-cell flows they weight.

    through and source may be (cells,) or (cells, groups) (net mode varies them by group).
    """
    names = list(selections)
    through = np.broadcast_to(through.reshape(step.n_cells, -1), fraction.shape)
    source = np.broadcast_to(source.reshape(step.n_cells, -1), fraction.shape)
    f = {g: fraction[:, i] for i, g in enumerate(names)}
    vol_from = {g: fraction[:, i] * source[:, i] for i, g in enumerate(names)}
    vol_through = {g: fraction[:, i] * through[:, i] for i, g in enumerate(names)}
    by_term = {g: {p: f[g] * q for p, q in source_by_package.items()} for g in names}
    from_input = {g: np.where(source[:, i] > 0.0, f[g], np.nan) for i, g in enumerate(names)}
    return BackwardResult(
        accounting=accounting,
        selections=selections,
        fraction_through=f,
        volume_through=vol_through,
        volume_from=vol_from,
        volume_from_by_term=by_term,
        fraction_from_cell_input=from_input,
        fraction_from_total={g: share_of_total(v) for g, v in vol_from.items()},
        flux_through=divide_by_area(vol_through, step.area),
        flux_from=divide_by_area(vol_from, step.area),
        destination_inflow={g: float(v) for g, v in zip(names, destination_inflow)},
    )


def forward_metrics(
    step: FlowStep,
    selections: dict[str, Selection],
    fraction: np.ndarray,
    through: np.ndarray,
    sink: np.ndarray,
    sink_by_package: dict[str, np.ndarray],
    source_inflow: np.ndarray,
    accounting: str,
) -> ForwardResult:
    """Return forward outputs from fractions (cells, groups) and the per-cell flows they weight."""
    names = list(selections)
    through = np.broadcast_to(through.reshape(step.n_cells, -1), fraction.shape)
    sink = np.broadcast_to(sink.reshape(step.n_cells, -1), fraction.shape)
    g_frac = {g: fraction[:, i] for i, g in enumerate(names)}
    return ForwardResult(
        accounting=accounting,
        selections=selections,
        source_fraction=g_frac,
        volume_through={g: fraction[:, i] * through[:, i] for i, g in enumerate(names)},
        volume_to={g: fraction[:, i] * sink[:, i] for i, g in enumerate(names)},
        volume_to_by_term={
            g: {p: g_frac[g] * q for p, q in sink_by_package.items()} for g in names
        },
        source_inflow={g: float(v) for g, v in zip(names, source_inflow)},
    )
