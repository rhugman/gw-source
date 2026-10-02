"""Build destination (backward) or source (forward) groups from a FlowStep.

A Selection carries two masks:
- ``terms``: which external term entries belong to the group. Gross accounting uses this. In
  backward mode only the selected entries that are sinks (negative flow) act as destinations;
  in forward mode only the selected entries that are sources (positive flow) act as sources.
- ``cells``: which cells belong to the group. Net accounting uses this (destination or source
  cells are fixed at fraction 1).

Selecting by cells therefore means "all external terms located in those cells" in gross mode,
and "those cells" in net mode. Selecting by package, bound or boundname marks the cells that
host the selected entries. A zone array selects the cells where zone == value (any grid type:
the array may have the grid shape or one value per cell); combine it with package= to pick,
for example, the recharge falling on one zone as a forward source.

Boundnames need a FlowStep read with boundnames=True (they are not in the budget file). A
boundname that is absent in a step (e.g. a well listed only in some stress periods) selects
nothing in that step rather than failing, so groups can be re-selected on every time step.

Groups are plain dicts {group name: Selection}.
"""

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from .flowstep import FlowStep


@dataclass
class Selection:
    """Boolean masks over the external term entries and over the cells of a FlowStep."""

    terms: np.ndarray
    cells: np.ndarray


def _package_mask(step: FlowStep, package: str | Iterable[str]) -> np.ndarray:
    """Return entries whose package name, budget text or parent package matches (any case).

    A package's *-TO-MVR record matches the package too: selecting 'DRN' selects all water
    leaving the aquifer through the drains, whether or not the mover then passes it on.
    """
    wanted = {package.upper()} if isinstance(package, str) else {p.upper() for p in package}
    hits = [bool(p.aliases & wanted) for p in step.packages]
    assert any(hits), f"no package matches {sorted(wanted)}; have {step.package_names}"
    return np.asarray(hits, dtype=bool)[step.term_package]


def _cell_mask(step: FlowStep, cells) -> np.ndarray:
    """Return a cell mask from 0-based cell indices or a boolean mask."""
    cells = np.asarray(cells)
    if cells.dtype == bool:
        assert cells.size == step.n_cells, "boolean cell mask must have one value per cell"
        return cells.ravel().copy()
    mask = np.zeros(step.n_cells, dtype=bool)
    mask[cells.ravel()] = True
    return mask


def _boundname_mask(step: FlowStep, boundnames: Iterable[str]) -> np.ndarray:
    """Return entries whose boundname is in the list (case-insensitive)."""
    assert step.term_boundname is not None, "this FlowStep has no boundnames"
    wanted = {b.upper() for b in boundnames}
    return np.array([str(b).upper() in wanted for b in step.term_boundname], dtype=bool)


def select(
    step: FlowStep,
    package: str | Iterable[str] | None = None,
    bounds: Iterable[int] | None = None,
    boundnames: Iterable[str] | None = None,
    cells=None,
    term_mask: np.ndarray | None = None,
) -> Selection:
    """Return the Selection of external terms (and cells) matching all of the given criteria."""
    terms = np.ones(step.n_terms, dtype=bool)
    if package is not None:
        terms &= _package_mask(step, package)
    if bounds is not None:
        terms &= np.isin(step.term_bound, np.asarray(list(bounds)))
    if boundnames is not None:
        terms &= _boundname_mask(step, boundnames)
    if term_mask is not None:
        assert len(term_mask) == step.n_terms, "term_mask must have one value per term entry"
        terms &= np.asarray(term_mask, dtype=bool)
    if cells is None:
        cell_mask = np.zeros(step.n_cells, dtype=bool)
        cell_mask[step.term_cell[terms]] = True
        return Selection(terms=terms, cells=cell_mask)
    cell_mask = _cell_mask(step, cells)
    return Selection(terms=terms & cell_mask[step.term_cell], cells=cell_mask)


def select_cells(step: FlowStep, cells) -> Selection:
    """Return the Selection of the given cells and every external term located in them."""
    return select(step, cells=cells)


def groups_by_package(step: FlowStep) -> dict[str, Selection]:
    """Return one group per package (term-table entry), named by package name."""
    return {
        p.name: select(step, term_mask=step.term_package == i) for i, p in enumerate(step.packages)
    }


def groups_by_term(step: FlowStep, term_mask: np.ndarray | None = None) -> dict[str, Selection]:
    """Return one group per external term entry (optionally only those in term_mask)."""
    idx = np.arange(step.n_terms) if term_mask is None else np.flatnonzero(term_mask)
    groups = {}
    for k in idx:
        mask = np.zeros(step.n_terms, dtype=bool)
        mask[k] = True
        name = f"{step.packages[step.term_package[k]].name}:{step.term_bound[k]}"
        groups[name] = select(step, term_mask=mask)
    return groups


def zone_mask(step: FlowStep, zones, values) -> np.ndarray:
    """Return the cells whose zone is one of values; zones has the grid shape or one per cell."""
    zones = np.asarray(zones)
    assert zones.size == step.n_cells, "zone array must have one value per cell"
    return np.isin(zones.ravel(), np.atleast_1d(values))


def select_zone(step: FlowStep, zones, values, **criteria) -> Selection:
    """Return the Selection of the cells where zone is in values (and any other select criteria)."""
    return select(step, cells=zone_mask(step, zones, values), **criteria)


def groups_by_zone(
    step: FlowStep, zones, skip: Iterable = (0,), prefix: str = "zone_", **criteria
) -> dict[str, Selection]:
    """Return one group per zone value (except those in skip), named '<prefix><value>'."""
    values = [v for v in np.unique(np.asarray(zones)) if v not in set(skip)]
    return {f"{prefix}{v}": select_zone(step, zones, v, **criteria) for v in values}


def groups_by_boundname(step: FlowStep, package: str | None = None) -> dict[str, Selection]:
    """Return one group per boundname present in the step (optionally only of one package)."""
    assert step.term_boundname is not None, "no boundnames: read the step with boundnames=True"
    mask = np.ones(step.n_terms, dtype=bool) if package is None else _package_mask(step, package)
    names = sorted({str(b) for b in step.term_boundname[mask] if b})
    return {name: select(step, boundnames=[name], term_mask=mask) for name in names}
