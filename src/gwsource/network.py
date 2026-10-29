"""Global node graph of a simulation: several GWF models, their exchanges, package nodes and MVR.

Nodes (gwsource.flowstep.NodeBlock, in this order): the cells of every GWF model (user node
numbering, model by model as listed in mfsim.nam or given), then one node per reach, lake, well
or UZF cell of every enabled advanced package (open_simulation(package_nodes=...)). A FlowStep
built here has blocks; everything downstream (assembly, solve, metrics, diagnostics, travel
time) works on it unchanged, because it is just a larger graph.

Edges (each water transfer counted once):
- intercell flows of each model (FLOW-JA-FACE, IMETH = 1);
- GWF-GWF exchanges between two models that are both read: from the exchange's FLOW-JA-FACE
  record (IMETH = 6) of the first model that lists it; the second model's record must be its
  exact negative (checked); both models' boundary terms are dropped. An exchange with a model
  that is not read stays a boundary term ('GWF-GWF').
- cell <-> package node: the GWF budget's aquifer-side record of that package (SFR, LAK, MAW,
  UZF-GWRCH), after checking, cell by cell, that the package budget's GWF record is its negative
  to aquifer_rtol (default AQUIFER_RTOL) of the package's largest exchange; the record is then
  an edge, no longer a term;
- package node <-> package node: the package budget's FLOW-JA-FACE (SFR reach to reach, LAK
  outlet to lake, UZF cell to cell);
- MVR (see below).
Every other record is a source or sink term of its node (gwsource.packages lists them). Package
node terms are named '<package>:<record>' (parent = the package name, package_type = its type),
so select(package='MAW') selects all terms of the MAW wells, whatever the package is called, and
select(package='MAW', term='RATE') their pumping.
With several models, every term package name is prefixed '<model>/'; selectors also match the
name without the prefix, so select(package='WEL') selects the wells of every model.

Water mover. With an MVR budget file, each transfer of q from a provider (package, bound) to a
receiver package node becomes an edge, if the receiver package has nodes and the provider's
TO-MVR record(s) for that bound are in the graph: on a cell (DRN-TO-MVR, 'UZF-GWD TO-MVR', ...)
or on an enabled package node (TO-MVR, RATE-TO-MVR, REJ-INF-TO-MVR, ...). When one provider
bound has several such records (a UZF cell's REJ-INF-TO-MVR and its cell's GWD TO-MVR; a MAW
well's RATE-TO-MVR and FW-RATE-TO-MVR), the transfer is shared among them in proportion to their
rates. The routed rate is taken off the provider's TO-MVR sink and the receiver's FROM-MVR
source; a remainder within MOVER_SNAP_RTOL of the original record (MF6 computes the moved share
at the last outer iteration, so the records differ at solver tolerance) is set to 0 and shows up
in the node residual instead. Transfers that cannot be routed stay sink and source terms, as
without package nodes. Movers between models (the simulation-level MVE) are not read.

Residuals: the FLOW-JA-FACE diagonal of a cell keeps MF6's own residual (which includes its
exchange flows); the diagonal of a package node is the sum of all its records in the package
budget, MF6's balance of that node. diagnostics.cell_residual() recomputes both from the graph.

Water volume: package nodes take the VOLUME auxiliary of their STORAGE record (SFR reach, lake,
MAW well, UZF cell) as FlowStep.fixed_volume; a package without it gets zero-volume nodes
(listed in notes['zero_volume_packages']). Cells keep area x saturated thickness x porosity.

Per-model output: model_view() and result_view() cut a network step and a trace result down to
one model's cells (with that model's grid shape and files), so the single-model exports and
reshaping (gwsource.export) apply; package_rows() lists the package-node results as a table.
"""

from dataclasses import dataclass, field, replace
from pathlib import Path

import flopy
import numpy as np

from .flowstep import MODEL_SEP, FlowStep, NodeBlock, Package, connection_rows
from .metrics import BackwardResult, ForwardResult
from .mf6io import (
    EXCHANGE_TEXT,
    StepReader,
    _block_lines,
    _find_model_entry,
    open_model,
)
from .packages import (
    ANTISYMMETRY_RTOL,
    AQUIFER_TEXTS,
    FROM_MOVER_TEXT,
    MoverTransfer,
    PackageFiles,
    PackageStep,
    find_mover_budget,
    find_package_files,
    read_mover_step,
    read_package_step,
)
from .selectors import Selection
from .solve import Cycle

MOVER_SNAP_RTOL = 1e-6
AQUIFER_RTOL = 1e-4
NETWORK_GRID = "network"
NETWORK_NOTE_KEYS = ("units", "delt", "thickness_from")


# ---------------------------------------------------------------- assembly pieces


@dataclass
class TermTable:
    """External term entries under assembly: global node, flow, package, bound, boundname."""

    node: np.ndarray
    flow: np.ndarray
    package: np.ndarray
    bound: np.ndarray
    boundname: np.ndarray
    packages: list[Package]
    keep: np.ndarray

    def of_package(self, index: int) -> np.ndarray:
        """Return the entry indices of one package that are still kept."""
        return np.flatnonzero((self.package == index) & self.keep)


@dataclass
class Links:
    """CSR triplets (row, column, FLOW-JA-FACE value) of the global graph under assembly."""

    rows: list[np.ndarray] = field(default_factory=list)
    cols: list[np.ndarray] = field(default_factory=list)
    vals: list[np.ndarray] = field(default_factory=list)

    def add(self, rows, cols, vals) -> None:
        """Append entries (flowja convention: value = flow INTO row FROM column)."""
        self.rows.append(np.asarray(rows, dtype=np.int64))
        self.cols.append(np.asarray(cols, dtype=np.int64))
        self.vals.append(np.asarray(vals, dtype=float))

    def add_flows(self, into, from_, q) -> None:
        """Append a connection both ways for a flow q INTO node `into` FROM node `from_`."""
        self.add(into, from_, q)
        self.add(from_, into, -np.asarray(q, dtype=float))


def block_offsets(sizes: list[int]) -> list[int]:
    """Return the first global node of each block."""
    return [0, *np.cumsum(sizes)[:-1].tolist()] if sizes else []


def model_blocks(steps: dict[str, FlowStep]) -> list[NodeBlock]:
    """Return one block per model, in order."""
    offsets = block_offsets([s.n_cells for s in steps.values()])
    return [
        NodeBlock(m, "model", m, off, s.n_cells, tuple(s.grid_shape), s.grid_type)
        for (m, s), off in zip(steps.items(), offsets)
    ]


def package_blocks(pkg_steps: list[PackageStep], start: int) -> list[NodeBlock]:
    """Return one block per enabled package, after the model blocks."""
    offsets = [start + o for o in block_offsets([p.files.n for p in pkg_steps])]
    return [
        NodeBlock(
            p.files.name, "package", p.files.model, off, p.files.n, (p.files.n,), "package",
            p.files.package_type,
        )
        for p, off in zip(pkg_steps, offsets)
    ]


def _prefix(model: str, multi: bool) -> str:
    """Return the term-name prefix '<model>/' of a multi-model step, else ''."""
    return f"{model}{MODEL_SEP}" if multi else ""


def model_terms(steps: dict[str, FlowStep], blocks: list[NodeBlock], multi: bool) -> TermTable:
    """Return the term table of every model's external terms, on global nodes."""
    parts: dict[str, list] = {k: [] for k in ("node", "flow", "package", "bound", "boundname")}
    packages: list[Package] = []
    for block, step in zip(blocks, steps.values()):
        start = len(packages)
        for p in step.packages:
            name = _prefix(block.model, multi) + p.name
            packages.append(replace(p, name=name, model=block.model))
        parts["node"].append(step.term_cell + block.offset)
        parts["flow"].append(step.term_flow)
        parts["package"].append(step.term_package + start)
        parts["bound"].append(step.term_bound)
        names = step.term_boundname
        parts["boundname"].append(np.full(step.n_terms, "", object) if names is None else names)
    return _table(parts, packages)


def _table(parts: dict[str, list], packages: list[Package]) -> TermTable:
    """Return a TermTable from lists of per-record arrays."""
    dtypes = {"node": np.int64, "flow": float, "package": np.int64, "bound": np.int64}
    cat = {}
    for key, arrays in parts.items():
        dtype = dtypes.get(key, object)
        cat[key] = np.concatenate(arrays).astype(dtype) if arrays else np.zeros(0, dtype)
    return TermTable(**cat, packages=packages, keep=np.ones(len(cat["flow"]), dtype=bool))


def package_terms(
    pkg_steps: list[PackageStep], blocks: list[NodeBlock], multi: bool, names_of
) -> TermTable:
    """Return the term table of every package node's source and sink records."""
    parts: dict[str, list] = {k: [] for k in ("node", "flow", "package", "bound", "boundname")}
    packages: list[Package] = []
    for pkg, block in zip(pkg_steps, blocks):
        for text, (node, q) in pkg.terms.items():
            name = f"{_prefix(block.model, multi)}{block.name}:{text}"
            package = Package(name, text, block.name, block.model, package_type=block.package_type)
            packages.append(package)
            parts["node"].append(node + block.offset)
            parts["flow"].append(q)
            parts["package"].append(np.full(len(node), len(packages) - 1, dtype=np.int64))
            parts["bound"].append(node + 1)
            parts["boundname"].append(names_of(block.model, block.name, node + 1))
    return _table(parts, packages)


def join_tables(first: TermTable, second: TermTable) -> TermTable:
    """Return the two term tables concatenated (second's packages after first's)."""
    shift = len(first.packages)
    return TermTable(
        node=np.concatenate([first.node, second.node]),
        flow=np.concatenate([first.flow, second.flow]),
        package=np.concatenate([first.package, second.package + shift]),
        bound=np.concatenate([first.bound, second.bound]),
        boundname=np.concatenate([first.boundname, second.boundname]),
        packages=first.packages + second.packages,
        keep=np.concatenate([first.keep, second.keep]),
    )


# ---------------------------------------------------------------- edges


def model_links(links: Links, steps: dict[str, FlowStep], blocks: list[NodeBlock]) -> None:
    """Add every model's FLOW-JA-FACE (diagonal included) on global nodes."""
    for block, step in zip(blocks, steps.values()):
        links.add(connection_rows(step.ia) + block.offset, step.ja + block.offset, step.flowja)


def _assert_negatives(a: np.ndarray, b: np.ndarray, label: str) -> None:
    """Assert that b is the negative of a to ANTISYMMETRY_RTOL of the largest flow."""
    scale = max(float(np.abs(a).max(initial=0.0)), 1.0)
    assert np.abs(a + b).max(initial=0.0) <= ANTISYMMETRY_RTOL * scale, (
        f"{label}: the two sides of the exchange are not equal and opposite"
    )


def exchange_links(links: Links, table: TermTable, blocks: list[NodeBlock]) -> list[str]:
    """Turn GWF-GWF exchange terms between models that are both read into edges; return names."""
    offset = {b.model.upper(): b.offset for b in blocks if b.kind == "model"}
    done = []
    for p, package in enumerate(table.packages):
        partner = package.partner.upper()
        if package.text != EXCHANGE_TEXT or partner not in offset or package.local_name in done:
            continue
        mine = table.of_package(p)
        other = [
            i for i, o in enumerate(table.packages)
            if o.text == EXCHANGE_TEXT and o.local_name == package.local_name and i != p
        ]
        assert len(other) == 1, f"exchange {package.local_name}: record missing in {partner}"
        theirs = table.of_package(other[0])
        here, there = table.node[mine], table.bound[mine] - 1 + offset[partner]
        key_mine = here * (1 << 32) + there
        key_theirs = (table.bound[theirs] - 1 + offset[package.model.upper()]) * (1 << 32)
        key_theirs = key_theirs + table.node[theirs]
        order = np.argsort(key_theirs)
        pos = np.searchsorted(key_theirs[order], key_mine)
        assert np.array_equal(key_theirs[order][pos], key_mine), (
            f"exchange {package.local_name}: connections differ between the two models"
        )
        _assert_negatives(table.flow[mine], table.flow[theirs][order][pos], package.local_name)
        links.add_flows(here, there, table.flow[mine])
        table.keep[mine] = False
        table.keep[theirs] = False
        done.append(package.local_name)
    return done


def _aquifer_packages(table: TermTable, block: NodeBlock) -> list[int]:
    """Return the term-table packages of the GWF budget's aquifer-side records of a package."""
    texts = AQUIFER_TEXTS[block.package_type]
    return [
        i for i, p in enumerate(table.packages)
        if p.model == block.model
        and (p.parent or p.local_name).upper() == block.name.upper()
        and p.text in texts
    ]


def _pair_sums(first: np.ndarray, second: np.ndarray, q: np.ndarray, n2: int):
    """Return (unique pair keys, summed q) of (first, second) pairs."""
    keys, inverse = np.unique(first * n2 + second, return_inverse=True)
    return keys, np.bincount(inverse, weights=q, minlength=len(keys))


def aquifer_links(
    links: Links,
    table: TermTable,
    pkg_steps: list[PackageStep],
    blocks: list[NodeBlock],
    model_offset: dict[str, int],
    n_nodes: int,
    aquifer_rtol: float = AQUIFER_RTOL,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Turn each package's cell exchange into edges and drop the aquifer-side GWF records.

    Returns {block label: (global package nodes, global cells)} of the aquifer connections.

    The edges take the GWF budget's values (so cell residuals stay MF6's); the package budget's
    GWF record must have the same connections with opposite flows to aquifer_rtol of the
    package's largest exchange (the two sides differ at solver tolerance: MF6 evaluates them
    with the head and the package stage of different iterates). A larger tolerance lets a
    loosely solved model through: the difference stays in the package node's residual (its
    balance in the package budget), which closure and duality include as the residual term.
    """
    connections = {}
    for pkg, block in zip(pkg_steps, blocks):
        indices = np.concatenate(
            [table.of_package(p) for p in _aquifer_packages(table, block)] or [np.zeros(0, int)]
        )
        cell, q = table.node[indices], table.flow[indices]
        node = table.bound[indices] - 1 + block.offset
        node_p, cell_p, q_p = pkg.aquifer
        keys, sums = _pair_sums(node, cell, q, n_nodes)
        keys_p, sums_p = _pair_sums(
            node_p + block.offset, cell_p + model_offset[block.model], q_p, n_nodes
        )
        label = f"{block.label} aquifer exchange"
        assert np.array_equal(keys, keys_p), f"{label}: connections differ between the budgets"
        scale = max(float(np.abs(sums).max(initial=0.0)), 1.0)
        rdiff = np.abs(sums + sums_p) / scale
        assert rdiff.max(initial=0.0) <= aquifer_rtol, (
            f"{label}: the GWF and package budgets disagree by up to {rdiff.max():.3g} of the "
            f"largest exchange ({scale:.6g}) on {int((rdiff > aquifer_rtol).sum())} of "
            f"{len(rdiff)} connections (aquifer_rtol={aquifer_rtol:g}). This is usually solver "
            "tolerance (MF6 evaluates the two sides with different iterates): tighten the "
            "solver (OUTER_DVCLOSE / INNER_DVCLOSE) or pass aquifer_rtol=<value>"
        )
        links.add_flows(cell, node, q)
        table.keep[indices] = False
        connections[block.label] = (node, cell)
    return connections


def internal_links(links: Links, pkg_steps: list[PackageStep], blocks: list[NodeBlock]) -> None:
    """Add package-package edges (SFR reach to reach, LAK outlets, UZF cell to cell)."""
    for pkg, block in zip(pkg_steps, blocks):
        src, dst, q = pkg.internal
        links.add_flows(dst + block.offset, src + block.offset, q)


def _group_by(keys: np.ndarray, indices: np.ndarray) -> dict[int, np.ndarray]:
    """Return {key: the indices with that key}."""
    out: dict[int, list] = {}
    for key, index in zip(keys.tolist(), indices.tolist()):
        out.setdefault(key, []).append(index)
    return {k: np.asarray(v, dtype=np.int64) for k, v in out.items()}


def mover_records(table: TermTable) -> tuple[dict, dict]:
    """Index the kept mover records once.

    Returns ({(model, provider package): {bound: TO-MVR entries}},
    {(model, receiver package): {global node: FROM-MVR entries}}).
    """
    providers: dict[tuple[str, str], list] = {}
    receivers: dict[tuple[str, str], list] = {}
    for p, package in enumerate(table.packages):
        owner = (package.model, (package.parent or package.local_name).upper())
        if package.is_mover:
            providers.setdefault(owner, []).append(p)
        elif package.text == FROM_MOVER_TEXT:
            receivers.setdefault(owner, []).append(p)
    by_bound = {}
    for owner, packages in providers.items():
        idx = np.flatnonzero(np.isin(table.package, packages) & table.keep)
        by_bound[owner] = _group_by(table.bound[idx], idx)
    by_node = {}
    for owner, packages in receivers.items():
        idx = np.flatnonzero(np.isin(table.package, packages) & table.keep)
        by_node[owner] = _group_by(table.node[idx], idx)
    return by_bound, by_node


def mover_links(
    links: Links, table: TermTable, transfers: dict[str, MoverTransfer], blocks: list[NodeBlock]
) -> float:
    """Route MVR transfers between nodes of the graph; return the total routed rate."""
    original = table.flow.copy()
    providers, receivers = mover_records(table)
    routed = 0.0
    for model, moved in transfers.items():
        blocks_by_name = {b.name.upper(): b for b in blocks if b.model == model}
        for k in np.flatnonzero(moved.q > 0.0):
            block = blocks_by_name.get(moved.receiver[k])
            records = providers.get((model, moved.provider[k]), {}).get(int(moved.provider_id[k]))
            if block is None or records is None:
                continue
            rates = -table.flow[records]
            if rates.sum() <= 0.0:
                continue
            dst = block.offset + int(moved.receiver_id[k]) - 1
            share = moved.q[k] * rates / rates.sum()
            src = table.node[records]
            other = src != dst
            links.add_flows(np.full(other.sum(), dst), src[other], share[other])
            table.flow[records] += share
            receiver = receivers.get((model, block.name.upper()), {}).get(dst)
            assert receiver is not None, f"{block.label}: no FROM-MVR record for node {dst}"
            table.flow[receiver[0]] -= moved.q[k]
            routed += float(moved.q[k])
    changed = table.flow != original
    snap = changed & (np.abs(table.flow) <= MOVER_SNAP_RTOL * np.abs(original))
    table.flow[snap] = 0.0
    return routed


def package_diagonals(links: Links, pkg_steps: list[PackageStep], blocks: list[NodeBlock]) -> None:
    """Add each package node's own budget residual as its diagonal entry."""
    for pkg, block in zip(pkg_steps, blocks):
        links.add(block.nodes, block.nodes, pkg.residual)


def build_csr(n: int, links: Links) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (ia, ja, flowja) sorted by row, diagonal first, then by column."""
    rows, cols = np.concatenate(links.rows), np.concatenate(links.cols)
    vals = np.concatenate(links.vals)
    order = np.lexsort((cols, rows != cols, rows))
    ia = np.concatenate([[0], np.cumsum(np.bincount(rows, minlength=n))])
    return ia, cols[order], vals[order]


def compact_terms(table: TermTable) -> TermTable:
    """Return the kept entries; packages whose entries all became edges are removed.

    Packages that had no entries in the budget (an empty record) are kept, as in a cells-only
    step, so that selecting them still works.
    """
    n_packages = len(table.packages)
    had = np.bincount(table.package, minlength=n_packages) > 0
    kept = np.bincount(table.package[table.keep], minlength=n_packages) > 0
    used = np.flatnonzero(kept | ~had)
    new_index = np.full(len(table.packages), -1, dtype=np.int64)
    new_index[used] = np.arange(len(used))
    keep = table.keep
    return TermTable(
        node=table.node[keep],
        flow=table.flow[keep],
        package=new_index[table.package[keep]],
        bound=table.bound[keep],
        boundname=table.boundname[keep],
        packages=[table.packages[i] for i in used],
        keep=np.ones(int(keep.sum()), dtype=bool),
    )


# ---------------------------------------------------------------- the network step


def _concat_or_nan(arrays: list[np.ndarray | None], sizes: list[int]) -> np.ndarray | None:
    """Concatenate per-block arrays, NaN for missing ones; None if all are missing."""
    if all(a is None for a in arrays):
        return None
    return np.concatenate(
        [np.full(n, np.nan) if a is None else np.asarray(a, float) for a, n in zip(arrays, sizes)]
    )


def build_network(
    steps: dict[str, FlowStep],
    pkg_steps: list[PackageStep],
    transfers: dict[str, MoverTransfer],
    names_of=None,
    aquifer_rtol: float = AQUIFER_RTOL,
) -> FlowStep:
    """Return the global FlowStep of several model steps, package steps and MVR transfers.

    aquifer_rtol: tolerance of the GWF and package budgets' aquifer exchange (aquifer_links).
    """
    assert steps, "no model steps"
    multi = len(steps) > 1
    m_blocks = model_blocks(steps)
    n_cells = sum(b.n for b in m_blocks)
    p_blocks = package_blocks(pkg_steps, n_cells)
    blocks = m_blocks + p_blocks
    n = n_cells + sum(b.n for b in p_blocks)
    names_of = names_of or (lambda model, package, bounds: np.full(len(bounds), "", object))
    table = join_tables(
        model_terms(steps, m_blocks, multi), package_terms(pkg_steps, p_blocks, multi, names_of)
    )
    links = Links()
    model_links(links, steps, m_blocks)
    exchanges = exchange_links(links, table, m_blocks)
    offsets = {b.model: b.offset for b in m_blocks}
    connections = aquifer_links(links, table, pkg_steps, p_blocks, offsets, n, aquifer_rtol)
    internal_links(links, pkg_steps, p_blocks)
    routed = mover_links(links, table, transfers, p_blocks)
    package_diagonals(links, pkg_steps, p_blocks)
    terms = compact_terms(table)
    ia, ja, flowja = build_csr(n, links)
    first = next(iter(steps.values()))
    pkg_sizes = [b.n for b in p_blocks]
    volume = [np.nan_to_num(p.volume, nan=0.0) for p in pkg_steps]
    return FlowStep(
        ia=ia,
        ja=ja,
        flowja=flowja,
        term_cell=terms.node,
        term_flow=terms.flow,
        term_package=terms.package,
        term_bound=terms.bound,
        packages=terms.packages,
        term_boundname=terms.boundname,
        area=_concat_or_nan([s.area for s in steps.values()] + [None] * len(p_blocks),
                            [b.n for b in blocks]),
        saturated_thickness=_concat_or_nan(
            [s.saturated_thickness for s in steps.values()] + [None] * len(p_blocks),
            [b.n for b in blocks],
        ),
        active=np.concatenate([s.active for s in steps.values()] + [np.ones(sum(pkg_sizes), bool)]),
        grid_shape=(n,),
        grid_type=NETWORK_GRID,
        kstpkper=first.kstpkper,
        totim=first.totim,
        notes={
            **{k: first.notes[k] for k in NETWORK_NOTE_KEYS if k in first.notes},
            "network": True,
            "model_notes": {m: s.notes for m, s in steps.items()},
            "exchanges": exchanges,
            "mover_routed": routed,
            "package_connections": connections,
            "zero_volume_packages": [
                b.label for b, p in zip(p_blocks, pkg_steps) if np.isnan(p.volume).all()
            ],
        },
        blocks=blocks,
        fixed_volume=np.concatenate([np.full(n_cells, np.nan), *volume]) if volume else None,
    )


# ---------------------------------------------------------------- reader


def _exchange_entries(ws: Path) -> list[tuple[Path, str, str]]:
    """Return (file, model 1, model 2) of each GWF6-GWF6 exchange in mfsim.nam."""
    return [
        (ws / t[1], t[2], t[3])
        for t in _block_lines(ws / "mfsim.nam", "EXCHANGES")
        if t[0].upper() == "GWF6-GWF6"
    ]


def _assert_exchanges_saved(ws: Path, models: list[str]) -> None:
    """Assert that every exchange between two read models saves its flows."""
    wanted = {m.upper() for m in models}
    for path, m1, m2 in _exchange_entries(ws):
        if {m1.upper(), m2.upper()} <= wanted:
            options = [t[0].upper() for t in _block_lines(path, "OPTIONS")]
            assert "SAVE_FLOWS" in options, (
                f"exchange {path.name} does not save its flows: add SAVE_FLOWS to its OPTIONS"
            )


def simulation_models(ws: str | Path) -> list[str]:
    """Return the names of every GWF6 model in mfsim.nam, in order."""
    return [
        t[2] for t in _block_lines(Path(ws) / "mfsim.nam", "MODELS") if t[0].upper() == "GWF6"
    ]


@dataclass
class NetworkReader:
    """Every model's grid and budget, and the package and MVR budgets, opened once.

    read() returns the global FlowStep of one time step; steps and step_length() follow the first
    model, so trace_transient() works on a NetworkReader as on a StepReader. aquifer_rtol is the
    tolerance of the GWF and package budgets' aquifer exchange (see aquifer_links).
    The budget files stay open until close() (or the end of a with block).
    """

    models: dict[str, StepReader]
    packages: list[tuple[PackageFiles, flopy.utils.CellBudgetFile]]
    movers: dict[str, flopy.utils.CellBudgetFile]
    notes: dict = field(default_factory=dict)
    aquifer_rtol: float = AQUIFER_RTOL

    def close(self) -> None:
        """Close every model's files and the package and MVR budget files."""
        for reader in self.models.values():
            reader.close()
        for _, cbc in self.packages:
            cbc.close()
        for cbc in self.movers.values():
            cbc.close()

    def __enter__(self) -> "NetworkReader":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def steps(self) -> list[tuple[int, int]]:
        """0-based (kstp, kper) of every saved time step (of the first model)."""
        return next(iter(self.models.values())).steps

    def step_length(self, kstpkper: tuple[int, int]) -> float:
        """Return the length (DELT) of a saved time step."""
        return next(iter(self.models.values())).step_length(kstpkper)

    def _boundnames(self, kper: int):
        """Return a function (model, package, bounds) -> boundnames for package-node terms."""

        def names_of(model: str, package: str, bounds: np.ndarray) -> np.ndarray:
            table = self.models[model].boundnames
            if table is None:
                return np.full(len(bounds), "", dtype=object)
            return table.names(package, kper, bounds)

        return names_of

    def read(self, kstpkper: tuple[int, int] = (0, 0)) -> FlowStep:
        """Read one time step of every model and package into one global FlowStep."""
        steps = {m: r.read(kstpkper) for m, r in self.models.items()}
        pkg_steps = [read_package_step(cbc, f, kstpkper) for f, cbc in self.packages]
        transfers = {m: read_mover_step(cbc, kstpkper) for m, cbc in self.movers.items()}
        step = build_network(
            steps, pkg_steps, transfers, self._boundnames(kstpkper[1]), self.aquifer_rtol
        )
        step.notes.update(self.notes)
        return step


def open_simulation(
    ws: str | Path,
    models: list[str] | None = None,
    package_nodes: tuple[str, ...] = (),
    boundnames: bool = False,
    aquifer_rtol: float = AQUIFER_RTOL,
) -> NetworkReader:
    """Open the models of a simulation (all GWF models by default) and their package budgets.

    package_nodes: package types that get nodes, e.g. ("SFR", "MAW"); each needs BUDGET FILEOUT,
    and MVR (if present in a model with package nodes) needs BUDGET FILEOUT too.
    aquifer_rtol: largest allowed difference, relative to a package's largest aquifer exchange,
    between the GWF budget's record of the package and the package budget's GWF record. The two
    differ at solver tolerance; a loosely solved model may need more than the default, and the
    difference then shows up in the package nodes' residuals.
    """
    ws = Path(ws)
    if models is None:
        names = simulation_models(ws)
    else:
        names = [_find_model_entry(ws, m)[0] for m in models]
    assert names, f"no GWF model in {ws / 'mfsim.nam'}"
    _assert_exchanges_saved(ws, names)
    readers = {m: open_model(ws, m, boundnames=boundnames) for m in names}
    packages, movers = [], {}
    for m in names:
        nam_file = _find_model_entry(ws, m)[1]
        found = find_package_files(nam_file, m, package_nodes) if package_nodes else []
        packages += [(f, flopy.utils.CellBudgetFile(str(f.budget_file))) for f in found]
        mover = find_mover_budget(nam_file) if found else None
        if mover is not None:
            movers[m] = flopy.utils.CellBudgetFile(str(mover))
    missing = {t.upper() for t in package_nodes} - {f.package_type for f, _ in packages}
    assert not missing, f"no {sorted(missing)} package in models {names}"
    notes = {"models": names, "package_nodes": tuple(t.upper() for t in package_nodes)}
    return NetworkReader(readers, packages, movers, notes, aquifer_rtol)


def read_network(
    ws: str | Path,
    kstpkper: tuple[int, int] = (0, 0),
    models: list[str] | None = None,
    package_nodes: tuple[str, ...] = (),
    boundnames: bool = False,
    aquifer_rtol: float = AQUIFER_RTOL,
) -> FlowStep:
    """Read one time step of a simulation's models (and package nodes) into one global FlowStep.

    aquifer_rtol: tolerance of the aquifer exchange check (see open_simulation).
    """
    with open_simulation(ws, models, package_nodes, boundnames, aquifer_rtol) as reader:
        return reader.read(kstpkper)


# ---------------------------------------------------------------- per-model views


def global_values(step: FlowStep, per_model: dict[str, np.ndarray], fill: float = np.nan):
    """Return a per-node array from {model: per-cell array (any shape)}; fill elsewhere."""
    out = np.full(step.n_cells, fill, dtype=float)
    for model, values in per_model.items():
        block = step.block(model)
        assert block.kind == "model", f"{model} is not a model block"
        out[block.nodes] = np.broadcast_to(np.asarray(values, float).ravel(), (block.n,))
    return out


def global_nodes(step: FlowStep, label: str, local) -> np.ndarray:
    """Return the global nodes of 0-based local indices (cells or package nodes) of a block."""
    block = step.block(label)
    local = np.asarray(local, dtype=np.int64)
    assert local.size == 0 or (local.min() >= 0 and local.max() < block.n), "local index range"
    return local + block.offset


def _view_csr(step: FlowStep, block: NodeBlock) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the CSR arrays of the connections inside one block, in local numbering."""
    lo, hi = step.ia[block.offset], step.ia[block.offset + block.n]
    rows = connection_rows(step.ia)[lo:hi] - block.offset
    cols = step.ja[lo:hi] - block.offset
    inside = (cols >= 0) & (cols < block.n)
    ia = np.concatenate([[0], np.cumsum(np.bincount(rows[inside], minlength=block.n))])
    return ia, cols[inside], step.flowja[lo:hi][inside]


def _model_notes(step: FlowStep, model: str) -> dict:
    """Return the file notes of one model of a network step (plus the step's delt)."""
    notes = dict(step.notes.get("model_notes", {}).get(model, {}))
    notes.setdefault("units", step.notes.get("units", {}))
    return notes


def model_block(step: FlowStep, model: str | None = None) -> NodeBlock:
    """Return a model's block; model may be omitted when the step has only one model."""
    models = step.model_names
    model = models[0] if model is None and len(models) == 1 else model
    assert model is not None, f"several models in this step: choose one of {models}"
    block = step.block(model)
    assert block.kind == "model", f"{model} is not a model block"
    return block


def model_view(step: FlowStep, model: str | None = None) -> FlowStep:
    """Return one model's cells as a single-model FlowStep (for export and reshaping only).

    Edges to other models and to package nodes are left out, so its budgets do not close; trace
    the network step and cut the result with result_view().
    """
    if not step.is_network:
        return step
    block = model_block(step, model)
    ia, ja, flowja = _view_csr(step, block)
    terms = term_index(step, block)
    sl = slice(block.offset, block.offset + block.n)
    return FlowStep(
        ia=ia,
        ja=ja,
        flowja=flowja,
        term_cell=step.term_cell[terms] - block.offset,
        term_flow=step.term_flow[terms],
        term_package=step.term_package[terms],
        term_bound=step.term_bound[terms],
        packages=step.packages,
        term_boundname=None if step.term_boundname is None else step.term_boundname[terms],
        area=_slice(step.area, sl),
        saturated_thickness=_slice(step.saturated_thickness, sl),
        active=step.active[sl],
        grid_shape=block.grid_shape,
        grid_type=block.grid_type,
        kstpkper=step.kstpkper,
        totim=step.totim,
        notes=_model_notes(step, block.model),
    )


def _slice(values: np.ndarray | None, sl: slice) -> np.ndarray | None:
    """Return values[sl], or None."""
    return None if values is None else values[sl]


def term_index(step: FlowStep, block: NodeBlock) -> np.ndarray:
    """Return the indices of the term entries located on a block's nodes."""
    cells = step.term_cell
    return np.flatnonzero((cells >= block.offset) & (cells < block.offset + block.n))


def _cut(values: dict | None, sl: slice) -> dict | None:
    """Return {key: array[sl]} (nested one level for by-term splits), or None."""
    if values is None:
        return None
    return {k: _cut(v, sl) if isinstance(v, dict) else v[sl] for k, v in values.items()}


def _cut_cycles(cycles: list[Cycle], block: NodeBlock) -> list[Cycle]:
    """Return the cycles that touch a block, with their cells in local numbering."""
    out = []
    for c in cycles:
        inside = c.cells[(c.cells >= block.offset) & (c.cells < block.offset + block.n)]
        if inside.size:
            out.append(replace(c, cells=inside - block.offset))
    return out


def result_view(result: BackwardResult | ForwardResult, step: FlowStep, model: str | None = None):
    """Return a trace result cut down to one model's cells (pairs with model_view())."""
    if not step.is_network:
        return result
    block = model_block(step, model)
    sl = slice(block.offset, block.offset + block.n)
    terms = term_index(step, block)
    selections = {
        g: Selection(terms=s.terms[terms], cells=s.cells[sl], term_criteria=s.term_criteria)
        for g, s in result.selections.items()
    }
    changes = {"selections": selections, "factor": None}
    for name, value in vars(result).items():
        if isinstance(value, dict) and name not in ("selections",) and value:
            first = next(iter(value.values()))
            if isinstance(first, (np.ndarray, dict)):
                changes[name] = _cut(value, sl)
    changes["cycles"] = _cut_cycles(result.cycles, block)
    changes["closed_loops"] = [
        c[(c >= block.offset) & (c < block.offset + block.n)] - block.offset
        for c in result.closed_loops
    ]
    return replace(result, **changes)


def transient_view(result, model: str | None = None):
    """Return a TransientResult cut down to one model's cells (statistics and kept series)."""
    step = result.template
    if not step.is_network:
        return result
    block = model_block(step, model)
    sl = slice(block.offset, block.offset + block.n)
    stats = {s: {o: _cut(g, sl) for o, g in by.items()} for s, by in result.stats.items()}
    series = None
    if result.series is not None:
        series = {o: {g: v[:, sl] for g, v in by.items()} for o, by in result.series.items()}
    return replace(result, stats=stats, series=series, template=model_view(step, block.model))


def package_rows(step: FlowStep, result: BackwardResult | ForwardResult) -> list[dict]:
    """Return one row per package node: block, id and every per-node output of every group."""
    rows = []
    outputs = {
        name: value for name, value in vars(result).items()
        if isinstance(value, dict) and value and isinstance(next(iter(value.values())), np.ndarray)
        and name != "selections"
    }
    for block in step.blocks:
        if block.kind != "package":
            continue
        for local, node in enumerate(block.nodes):
            row = {
                "model": block.model,
                "package": block.name,
                "package_type": block.package_type,
                "id": local + 1,
                "node": int(node),
            }
            for name, per_group in outputs.items():
                for group, values in per_group.items():
                    row[f"{name}__{group}"] = float(values[node])
            rows.append(row)
    return rows


def package_cells(step: FlowStep, block: NodeBlock) -> list[np.ndarray]:
    """Return, per package node, the global cells of its aquifer connections (not MVR edges)."""
    nodes, cells = step.notes["package_connections"][block.label]
    return [cells[nodes == node] for node in block.nodes]
