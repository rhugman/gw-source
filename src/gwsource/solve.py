"""Solve (I - P) X = B for many right-hand sides; detect, report and (net mode) remove cycles.

Solvers:
- topological: if the dependency graph of the matrix is acyclic, permute it to lower-triangular
  form (dependencies first) and solve by substitution (scipy's compiled spsolve_triangular).
  This is the reference method's algorithm [FB13] in matrix form.
- block: permute the matrix to block lower-triangular form, one diagonal block per strongly
  connected component in topological order, and factorise it with SuperLU in that natural
  order (no fill-reducing column permutation, no pivoting). Fill-in is then confined to the
  rows and columns of the cyclic blocks, so a 1M-cell graph with thousands of small cycles
  factorises in well under a second. Works for any graph; the default for cyclic graphs.
- lu: sparse LU with SuperLU's default COLAMD ordering on the original matrix, factorised once
  and reused for every column. Kept as a reference; its fill-in makes it impractical beyond
  about 1e5 cells of a 3D grid.
- auto: topological if the graph is acyclic, otherwise block.

factorize() returns the factorisation (a Factor) so that further right-hand sides that depend on
the first solution (the travel-time systems of gwsource.traveltime) reuse it.

Pivoting is not needed: I - P is a (weakly) row-diagonally dominant M-matrix. It is singular only
on a closed recirculation loop, a strongly connected set with no exit: no dependency leaves it
and no row in it has an exit share 1 - sum_j P_ij (a sink, or in forward mode a source) above a
tolerance. isolate_closed_loops() finds these before the solve, turns their rows into identity
rows with a zero right-hand side (fraction 0: water circulating in them never reaches, or never
came from, any group) and reports them.

Cycles are the strongly connected components with more than one cell of the positive-flow
digraph (scipy.sparse.csgraph.connected_components with connection="strong"). scipy labels the
components in reverse topological order of the condensed graph; the order is verified, with
Kahn's algorithm as a fallback.
"""

from collections import deque
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu, spsolve_triangular

from .assemble import Edges

CLOSED_LOOP_TOL = 1e-12


@dataclass
class Cycle:
    """One strongly connected set of cells in the flow graph (a flow cycle or network of cycles).

    internal_flow is the sum of the flows on the edges inside the set; min_edge_flow the
    smallest of them. The circulation fields are filled by diagnostics.cycle_report().
    """

    cells: np.ndarray
    internal_flow: float
    min_edge_flow: float
    circulation: float = np.nan
    circulating_throughflow: float = np.nan
    throughflow_share: float = np.nan
    closed: bool = False

    @property
    def n_cells(self) -> int:
        """Number of cells in the cycle set."""
        return len(self.cells)


def strong_components(n: int, src: np.ndarray, dst: np.ndarray) -> tuple[int, np.ndarray]:
    """Return (number of components, labels) of the strongly connected components of a digraph."""
    graph = sp.coo_matrix((np.ones(len(src)), (src, dst)), shape=(n, n)).tocsr()
    return connected_components(graph, directed=True, connection="strong")


def find_cycles(n: int, edges: Edges) -> list[Cycle]:
    """Return every strongly connected set of more than one cell, with its internal edge flows."""
    _, labels = strong_components(n, edges.src, edges.dst)
    sizes = np.bincount(labels)
    cycles = []
    for label in np.flatnonzero(sizes > 1):
        internal = (labels[edges.src] == label) & (labels[edges.dst] == label)
        cycles.append(
            Cycle(
                cells=np.flatnonzero(labels == label),
                internal_flow=float(edges.q[internal].sum()),
                min_edge_flow=float(edges.q[internal].min()),
            )
        )
    return cycles


def _walk_to_cycle(start: int, out_edges: dict[int, list[int]], dst: np.ndarray) -> list[int]:
    """Follow out-edges from start until a cell repeats; return the edge indices of that cycle."""
    seen, path, node = {}, [], start
    while node not in seen:
        seen[node] = len(path)
        edge = out_edges[node][0]
        path.append(edge)
        node = int(dst[edge])
    return path[seen[node] :]


def remove_cycle_edges(n: int, edges: Edges) -> np.ndarray:
    """Return a keep-mask deleting the smallest edge of each cycle until the graph is acyclic."""
    keep = np.ones(len(edges.q), dtype=bool)
    while True:
        _, labels = strong_components(n, edges.src[keep], edges.dst[keep])
        sizes = np.bincount(labels)
        if sizes.max(initial=0) <= 1:
            return keep
        for label in np.flatnonzero(sizes > 1):
            idx = np.flatnonzero(keep & (labels[edges.src] == label) & (labels[edges.dst] == label))
            out_edges: dict[int, list[int]] = {}
            for e in idx:
                out_edges.setdefault(int(edges.src[e]), []).append(int(e))
            cycle = _walk_to_cycle(int(edges.src[idx[0]]), out_edges, edges.dst)
            keep[cycle[int(np.argmin(edges.q[cycle]))]] = False


def _dependency_edges(matrix: sp.csr_matrix) -> tuple[np.ndarray, np.ndarray]:
    """Return (before, after) pairs: row i depends on column j, so j must be solved before i."""
    coo = matrix.tocoo()
    off = (coo.row != coo.col) & (coo.data != 0.0)
    return coo.col[off], coo.row[off]


def _kahn_order(n: int, before: np.ndarray, after: np.ndarray) -> np.ndarray | None:
    """Return a topological order by Kahn's algorithm, or None if the graph has a cycle."""
    adjacency = sp.csr_matrix((np.ones(len(before)), (before, after)), shape=(n, n))
    indegree = np.bincount(adjacency.indices, minlength=n)  # duplicates merged by csr_matrix
    queue = deque(np.flatnonzero(indegree == 0).tolist())
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in adjacency.indices[adjacency.indptr[node] : adjacency.indptr[node + 1]]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(int(nxt))
    return np.asarray(order) if len(order) == n else None


def component_order(
    n: int, before: np.ndarray, after: np.ndarray, labels: np.ndarray
) -> np.ndarray:
    """Return a cell order with the components in topological order (cells of one together)."""
    n_comp = int(labels.max()) + 1 if n else 0
    order = np.argsort(-labels, kind="stable")
    rank = n_comp - 1 - labels  # scipy labels components in reverse topological order
    between = labels[before] != labels[after]
    if np.all(rank[before[between]] < rank[after[between]]):
        return order
    comp_order = _kahn_order(n_comp, labels[before[between]], labels[after[between]])
    assert comp_order is not None, "condensed component graph is not acyclic"
    rank = np.empty(n_comp, dtype=np.int64)
    rank[comp_order] = np.arange(n_comp)
    return np.argsort(rank[labels], kind="stable")


def topological_order(n: int, before: np.ndarray, after: np.ndarray) -> np.ndarray | None:
    """Return an order in which every 'before' cell precedes its 'after' cell, or None if cyclic."""
    n_comp, labels = strong_components(n, before, after)
    if n_comp < n:
        return None
    return component_order(n, before, after, labels)


def closed_components(
    matrix: sp.csr_matrix, labels: np.ndarray, tol: float = CLOSED_LOOP_TOL
) -> np.ndarray:
    """Return a cell mask of the strongly connected sets (> 1 cell) of I - P with no exit."""
    coo = matrix.tocoo()
    off = (coo.row != coo.col) & (coo.data != 0.0)
    rows, cols = coo.row[off], coo.col[off]
    n_comp = int(labels.max()) + 1 if labels.size else 0
    has_exit = np.zeros(n_comp, dtype=bool)
    has_exit[labels[rows[labels[rows] != labels[cols]]]] = True
    exit_share = np.asarray(matrix.sum(axis=1)).ravel()  # 1 - sum_j P_ij
    has_exit[labels[exit_share > tol]] = True
    closed = (np.bincount(labels, minlength=n_comp) > 1) & ~has_exit
    return closed[labels]


@dataclass
class DependencyGraph:
    """Dependency edges of a system matrix and their strongly connected components."""

    before: np.ndarray
    after: np.ndarray
    n_components: int
    labels: np.ndarray


def dependency_graph(matrix: sp.csr_matrix) -> DependencyGraph:
    """Return the dependency edges of matrix and their strongly connected components."""
    before, after = _dependency_edges(matrix)
    n_comp, labels = strong_components(matrix.shape[0], before, after)
    return DependencyGraph(before, after, int(n_comp), labels)


def _split_by_label(cells: np.ndarray, labels: np.ndarray) -> list[np.ndarray]:
    """Return the cells grouped by component label (each group sorted)."""
    order = np.lexsort((cells, labels[cells]))
    cells = cells[order]
    breaks = np.flatnonzero(np.diff(labels[cells])) + 1
    return np.split(cells, breaks) if cells.size else []


def isolate_closed_loops(
    matrix: sp.csr_matrix,
    rhs: np.ndarray,
    tol: float = CLOSED_LOOP_TOL,
    graph: DependencyGraph | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, list[np.ndarray]]:
    """Return (matrix, rhs, loops) with closed recirculation loops set to identity rows, rhs 0."""
    graph = dependency_graph(matrix) if graph is None else graph
    closed = closed_components(matrix, graph.labels, tol)
    if not closed.any():
        return matrix, rhs, []
    rhs = np.array(rhs, dtype=float)
    rhs[closed] = 0.0
    return identity_rows(matrix, closed), rhs, _split_by_label(np.flatnonzero(closed), graph.labels)


def identity_rows(matrix: sp.csr_matrix, closed: np.ndarray) -> sp.csr_matrix:
    """Return matrix with the off-diagonal entries of the closed rows removed."""
    coo = matrix.tocoo()
    keep = ~closed[coo.row] | (coo.row == coo.col)
    return sp.csr_matrix((coo.data[keep], (coo.row[keep], coo.col[keep])), shape=matrix.shape)


@dataclass
class Factor:
    """A factorised system matrix, reusable for further right-hand sides (e.g. travel times).

    kind is the solver used; order the cell order of the permuted matrix (None for "lu");
    triangular the permuted lower-triangular matrix ("topological"); lu the SuperLU object
    ("block" and "lu"). zero_rows marks closed-loop cells whose rows were made identity rows:
    their right-hand side is forced to 0 by solve(), as isolate_closed_loops() did for the first
    solve. Not picklable (SuperLU objects are not); keep it within one process.
    """

    kind: str
    order: np.ndarray | None = None
    triangular: sp.csr_matrix | None = None
    lu: object | None = None
    zero_rows: np.ndarray | None = None

    def solve(self, rhs: np.ndarray) -> np.ndarray:
        """Return X with matrix @ X = rhs (rows of closed loops forced to 0)."""
        rhs = np.array(rhs, dtype=float)
        if self.zero_rows is not None:
            rhs[self.zero_rows] = 0.0
        if self.kind == "lu":
            return self.lu.solve(rhs)
        if self.kind == "topological":
            x_perm = spsolve_triangular(self.triangular, rhs[self.order], lower=True)
        else:
            x_perm = self.lu.solve(rhs[self.order])
        x = np.empty_like(x_perm)
        x[self.order] = x_perm
        return x


def factor_topological(matrix: sp.csr_matrix, order: np.ndarray) -> Factor:
    """Permute the matrix to lower-triangular form for substitution."""
    return Factor("topological", order=order, triangular=matrix[order][:, order].tocsr())


def factor_lu(matrix: sp.csr_matrix) -> Factor:
    """Factorise with SuperLU and its default COLAMD ordering."""
    return Factor("lu", lu=splu(matrix.tocsc()))


def factor_block(matrix: sp.csr_matrix, order: np.ndarray) -> Factor:
    """Factorise with SuperLU in block lower-triangular (component) order, without reordering."""
    permuted = matrix[order][:, order].tocsc()
    lu = splu(permuted, permc_spec="NATURAL", diag_pivot_thresh=0.0)
    return Factor("block", order=order, lu=lu)


def factorize(
    matrix: sp.csr_matrix, solver: str = "auto", graph: DependencyGraph | None = None
) -> Factor:
    """Return a reusable factorisation of matrix with the chosen solver (see module docstring).

    graph, if given, must be dependency_graph(matrix) (it saves recomputing the components).
    """
    if solver == "lu":
        return factor_lu(matrix)
    n = matrix.shape[0]
    graph = dependency_graph(matrix) if graph is None else graph
    acyclic = graph.n_components == n
    assert acyclic or solver != "topological", (
        "the flow graph has cycles; the topological solver cannot be used (use 'auto' or 'block')"
    )
    order = component_order(n, graph.before, graph.after, graph.labels)
    if acyclic and solver != "block":
        return factor_topological(matrix, order)
    return factor_block(matrix, order)


def solve_topological(matrix: sp.csr_matrix, rhs: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Solve by substitution after permuting the matrix to lower-triangular form."""
    return factor_topological(matrix, order).solve(rhs)


def solve_lu(matrix: sp.csr_matrix, rhs: np.ndarray) -> np.ndarray:
    """Solve with one sparse LU factorisation reused for every right-hand-side column."""
    return factor_lu(matrix).solve(rhs)


def solve_block(matrix: sp.csr_matrix, rhs: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Solve by SuperLU in block lower-triangular (component) order, without reordering."""
    return factor_block(matrix, order).solve(rhs)


def solve_system(
    matrix: sp.csr_matrix,
    rhs: np.ndarray,
    solver: str = "auto",
    graph: DependencyGraph | None = None,
) -> tuple[np.ndarray, str]:
    """Solve matrix @ X = rhs; return (X, name of the solver used).

    graph, if given, must be dependency_graph(matrix) (it saves recomputing the components).
    """
    factor = factorize(matrix, solver, graph)
    return factor.solve(rhs), factor.kind
