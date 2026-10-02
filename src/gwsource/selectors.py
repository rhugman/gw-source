"""Build destination (backward) or source (forward) groups from a FlowStep.

A Selection carries two masks:
- ``terms``: which external term entries belong to the group. Gross accounting uses this. In
  backward mode only the selected entries that are sinks (negative flow) act as destinations;
  in forward mode only the selected entries that are sources (positive flow) act as sources.
- ``cells``: which cells belong to the group. Net accounting uses this (destination or source
  cells are fixed at fraction 1).

Selecting by cells therefore means "all external terms located in those cells" in gross mode,
and "those cells" in net mode. Selecting by package, bound or boundname marks the cells that
host the selected entries.

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
    """Return entries whose package name or budget text matches (case-insensitive)."""
    wanted = {package.upper()} if isinstance(package, str) else {p.upper() for p in package}
    hits = [p.name.upper() in wanted or p.text.upper() in wanted for p in step.packages]
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
