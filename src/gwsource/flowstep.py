"""FlowStep: the grid- and simulator-agnostic description of one flow time step.

Everything downstream (assembly, solve, metrics, diagnostics) reads only a FlowStep, so tests can
build graphs by hand without MF6.

Conventions
-----------
- Cells are numbered 0..n_cells-1. For MF6 output this is the *user* node number minus one; the
  binary grid file stores IA/JA in user numbering with empty rows for cells removed by IDOMAIN,
  and FLOW-JA-FACE is aligned with those IA/JA arrays.
- ``ia``/``ja`` are 0-based CSR connectivity. A row may contain its own cell (MF6 stores the
  diagonal first); diagonal entries are ignored for the flow graph. MF6 writes the cell budget
  residual (net inflow) in the diagonal of FLOW-JA-FACE.
- ``flowja[p]`` for connection p = (n, ja[p]) is the flow INTO cell n FROM cell ja[p] (MF6 sign
  convention). It must be antisymmetric over the off-diagonal entries.
- External terms are one entry per boundary (one row of an MF6 list budget record, or one cell
  of an array record such as STO-SS). ``term_flow`` is positive INTO the cell: a positive entry
  is a source term, a negative entry is a sink term. Entries with zero flow are neither.
- ``packages`` is the term table: ``term_package`` indexes into it.
- ``saturated_thickness`` (optional, per cell) is the saturated thickness of the cell for this
  step; with ``area`` it gives the water volume that travel times need (gwsource.traveltime).

Networks (Phase 4, gwsource.network): the "cells" may be the global nodes of a whole
simulation: the cells of every GWF model, then optional package nodes (SFR reaches, LAK lakes,
MAW wells, UZF cells). ``blocks`` lists the contiguous node ranges (NodeBlock) in order;
an empty list means a plain single-model step whose nodes are its cells. Package nodes have no
area or saturated thickness (NaN); ``fixed_volume`` holds their water volume from the package
output (NaN on cells, whose volume comes from porosity x area x saturated thickness).
"""

from dataclasses import dataclass, field

import numpy as np

MOVER_SUFFIX = "-TO-MVR"
MOVER_TEXT = "TO-MVR"  # every mover record ends so ('UZF-GWD TO-MVR' has a space, not a dash)
MODEL_SEP = "/"
BLOCK_KINDS = ("model", "package")


@dataclass(frozen=True)
class Package:
    """One budget record of external terms: unique name (e.g. 'WEL-1'), budget text ('WEL').

    parent is the MF6 package that wrote the record when one package writes several records
    (e.g. 'DRN' writes DRN and DRN-TO-MVR); empty means the record name itself.
    model is the GWF model that owns the record in a multi-model step (the name is then
    '<model>/<record name>'); partner is the other model of a GWF-GWF exchange record.
    """

    name: str
    text: str
    parent: str = ""
    model: str = ""
    partner: str = ""

    @property
    def local_name(self) -> str:
        """Name without the '<model>/' prefix of a multi-model step."""
        return self.name.split(MODEL_SEP, 1)[-1] if self.model else self.name

    @property
    def aliases(self) -> set[str]:
        """Upper-case names a selector can use: name, local name, text, parent, text w/o -TO-MVR."""
        names = {
            self.name,
            self.local_name,
            self.text,
            self.parent,
            self.text.removesuffix(MOVER_SUFFIX),
        }
        return {n.upper() for n in names if n}

    @property
    def is_mover(self) -> bool:
        """True for a *-TO-MVR record (water handed to the water mover)."""
        return self.text.upper().endswith(MOVER_TEXT)


@dataclass(frozen=True)
class NodeBlock:
    """A contiguous range of global nodes: the cells of one GWF model or one package's nodes.

    kind is 'model' or 'package'; model is the owning GWF model; name is the model name or the
    package name (e.g. 'SFR'); package_type the package type ('SFR', 'LAK', 'MAW', 'UZF').
    grid_shape and grid_type describe a model's grid; a package block is (n,) 'package'.
    """

    name: str
    kind: str
    model: str
    offset: int
    n: int
    grid_shape: tuple[int, ...]
    grid_type: str
    package_type: str = ""

    def __post_init__(self) -> None:
        """Validate the block kind."""
        assert self.kind in BLOCK_KINDS, f"block kind must be one of {BLOCK_KINDS}"

    @property
    def nodes(self) -> np.ndarray:
        """Global node indices of the block."""
        return np.arange(self.offset, self.offset + self.n)

    @property
    def label(self) -> str:
        """'<model>' for a model block, '<model>/<package>' for a package block."""
        return self.model if self.kind == "model" else f"{self.model}{MODEL_SEP}{self.name}"


@dataclass
class FlowStep:
    """Cell connectivity, intercell flows and external terms for one time step."""

    ia: np.ndarray
    ja: np.ndarray
    flowja: np.ndarray
    term_cell: np.ndarray
    term_flow: np.ndarray
    term_package: np.ndarray
    term_bound: np.ndarray
    packages: list[Package]
    term_boundname: np.ndarray | None = None
    area: np.ndarray | None = None
    saturated_thickness: np.ndarray | None = None
    active: np.ndarray | None = None
    grid_shape: tuple[int, ...] | None = None
    grid_type: str = "graph"
    kstpkper: tuple[int, int] | None = None
    totim: float | None = None
    notes: dict = field(default_factory=dict)
    blocks: list[NodeBlock] = field(default_factory=list)
    fixed_volume: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Coerce array types, fill defaults and validate shapes."""
        self.ia = np.asarray(self.ia, dtype=np.int64)
        self.ja = np.asarray(self.ja, dtype=np.int64)
        self.flowja = np.asarray(self.flowja, dtype=float)
        self.term_cell = np.asarray(self.term_cell, dtype=np.int64)
        self.term_flow = np.asarray(self.term_flow, dtype=float)
        self.term_package = np.asarray(self.term_package, dtype=np.int64)
        self.term_bound = np.asarray(self.term_bound, dtype=np.int64)
        n = self.n_cells
        if self.active is None:
            self.active = np.ones(n, dtype=bool)
        if self.grid_shape is None:
            self.grid_shape = (n,)
        validate_step(self)

    @property
    def n_cells(self) -> int:
        """Number of cells (rows of the connectivity)."""
        return len(self.ia) - 1

    @property
    def n_terms(self) -> int:
        """Number of external term entries."""
        return len(self.term_flow)

    @property
    def package_names(self) -> list[str]:
        """Package names in term-table order."""
        return [p.name for p in self.packages]

    @property
    def is_network(self) -> bool:
        """True if the nodes are split into blocks (several models and/or package nodes)."""
        return bool(self.blocks)

    @property
    def model_names(self) -> list[str]:
        """Names of the GWF models whose cells are nodes of this step (empty if not a network)."""
        return [b.name for b in self.blocks if b.kind == "model"]

    def block(self, label: str) -> NodeBlock:
        """Return the block with the given label ('<model>' or '<model>/<package>') or name."""
        found = [b for b in self.blocks if label.upper() in (b.label.upper(), b.name.upper())]
        labels = [b.label for b in self.blocks]
        assert len(found) == 1, f"block {label!r} not found once in {labels}"
        return found[0]


def validate_step(step: FlowStep) -> None:
    """Assert that a FlowStep's arrays are mutually consistent."""
    n = step.n_cells
    assert step.ia[0] == 0 and np.all(np.diff(step.ia) >= 0), "ia must be CSR row pointers"
    assert len(step.ja) == step.ia[-1] == len(step.flowja), "ja/flowja length must equal ia[-1]"
    assert len(step.ja) == 0 or (step.ja.min() >= 0 and step.ja.max() < n), "ja out of range"
    m = step.n_terms
    for name in ("term_cell", "term_package", "term_bound"):
        assert len(getattr(step, name)) == m, f"{name} must have one entry per term"
    assert m == 0 or (step.term_cell.min() >= 0 and step.term_cell.max() < n), "term_cell range"
    assert m == 0 or step.term_package.max() < len(step.packages), "term_package range"
    if step.term_boundname is not None:
        assert len(step.term_boundname) == m, "term_boundname must have one entry per term"
    if step.area is not None:
        assert len(step.area) == n, "area must have one value per cell"
    if step.saturated_thickness is not None:
        assert len(step.saturated_thickness) == n, "saturated_thickness: one value per cell"
    assert len(step.active) == n, "active must have one value per cell"
    assert int(np.prod(step.grid_shape)) == n, "grid_shape must hold n_cells values"
    if step.fixed_volume is not None:
        assert len(step.fixed_volume) == n, "fixed_volume must have one value per node"
    if step.blocks:
        ends = [b.offset + b.n for b in step.blocks]
        starts = [b.offset for b in step.blocks]
        assert starts[0] == 0 and starts[1:] == ends[:-1] and ends[-1] == n, (
            "blocks must tile the nodes 0..n-1 in order"
        )


def connection_rows(ia: np.ndarray) -> np.ndarray:
    """Return the row (cell) index of every CSR entry."""
    return np.repeat(np.arange(len(ia) - 1), np.diff(ia))


def csr_from_edges(
    n_cells: int, src: np.ndarray, dst: np.ndarray, q: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (ia, ja, flowja), diagonal first in each row, for directed edges src→dst of flow q."""
    src, dst = np.asarray(src, dtype=np.int64), np.asarray(dst, dtype=np.int64)
    q = np.asarray(q, dtype=float)
    assert np.all(src != dst), "self edges are not allowed"
    diag = np.arange(n_cells)
    rows = np.concatenate([diag, src, dst])
    cols = np.concatenate([diag, dst, src])
    vals = np.concatenate([np.zeros(n_cells), -q, q])  # row src loses q, row dst gains q
    is_diag = np.concatenate([np.ones(n_cells, bool), np.zeros(2 * len(src), bool)])
    order = np.lexsort((np.where(is_diag, -1, cols), rows))  # by row, diagonal first
    ia = np.concatenate([[0], np.cumsum(np.bincount(rows, minlength=n_cells))])
    return ia, cols[order], vals[order]


def from_edges(
    n_cells: int,
    src,
    dst,
    q,
    term_cell=(),
    term_flow=(),
    term_package=(),
    packages: list[Package] | None = None,
    **kwargs,
) -> FlowStep:
    """Build a FlowStep from directed edges and external terms (bound numbers 1..k per package)."""
    ia, ja, flowja = csr_from_edges(n_cells, src, dst, q)
    term_package = np.asarray(term_package, dtype=np.int64)
    packages = [] if packages is None else packages
    term_bound = np.zeros(len(term_package), dtype=np.int64)
    for p in range(len(packages)):
        sel = term_package == p
        term_bound[sel] = np.arange(1, sel.sum() + 1)
    return FlowStep(
        ia=ia,
        ja=ja,
        flowja=flowja,
        term_cell=term_cell,
        term_flow=term_flow,
        term_package=term_package,
        term_bound=term_bound,
        packages=packages,
        **kwargs,
    )
