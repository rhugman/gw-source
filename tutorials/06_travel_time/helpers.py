"""Helpers local to tutorial 06 (travel time): flux-weighted means and time-of-travel zones.

The Eulerian outputs of gwsource.travel_time are per cell; the particle results of
gwsource.prt.track_particles are per particle and per release cell. These helpers put the two
on the same footing: flux-weighted means over the water entering the model, split by source
package, and the area of a time-of-travel zone.
"""

import numpy as np

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges

DAYS_PER_YEAR = 365.25


def source_flow_by_package(step: gs.FlowStep) -> dict[str, np.ndarray]:
    """Return {package: per-cell inflow from that package's source terms [L3/T]}."""
    inflow = np.maximum(step.term_flow, 0.0)
    out = {}
    for index, name in enumerate(step.package_names):
        mine = step.term_package == index
        flows = np.bincount(step.term_cell[mine], weights=inflow[mine], minlength=step.n_cells)
        if flows.sum() > 0.0:
            out[name] = flows
    return out


def time_to_exit_cell(tt: gs.TravelTimeResult, group: str) -> np.ndarray:
    """Return the fraction-weighted time until the water enters the cell where it leaves (m - x)."""
    return tt.weighted_time[group] - tt.exit_cell_time[group]


def flux_weighted_mean(
    source: np.ndarray, weighted_time: np.ndarray, fraction: np.ndarray
) -> float:
    """Return sum(source x m) / sum(source x F): the mean over the water entering in source."""
    return float(source @ weighted_time / (source @ fraction))


def eulerian_means(
    step: gs.FlowStep, res: gs.BackwardResult, tt: gs.TravelTimeResult, group: str
) -> dict[str, dict[str, float]]:
    """Return flux-weighted Eulerian mean times (all sources and by package), both end points."""
    fraction = res.fraction_through[group]
    sources = {"all sources": cell_budget(step, flow_edges(step)).source}
    sources.update(source_flow_by_package(step))
    to_exit = time_to_exit_cell(tt, group)
    return {
        name: {
            "to the well": flux_weighted_mean(flow, tt.weighted_time[group], fraction),
            "to the well cell": flux_weighted_mean(flow, to_exit, fraction),
        }
        for name, flow in sources.items()
    }


def zone_area(
    area: np.ndarray, time: np.ndarray, fraction: np.ndarray, limit: float, f_min: float = 0.5
) -> float:
    """Return the area of the cells with fraction >= f_min and time <= limit (NaN time: out)."""
    inside = (fraction >= f_min) & np.isfinite(time) & (time <= limit)
    return float(area[inside].sum())
