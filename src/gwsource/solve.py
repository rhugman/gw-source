"""Solve (I - P) X = B for many right-hand sides; detect, report and (net mode) remove cycles.

Two solvers (PLAN §2.5):
- topological: if the dependency graph of the matrix is acyclic, permute it to lower-triangular
  form (dependencies first) and solve by substitution. This is the reference method's
  algorithm [FB13] in matrix form.
- lu: sparse LU (scipy.sparse.linalg.splu), factorised once and reused for every column.

Cycles are the strongly connected components with more than one cell of the positive-flow
digraph (scipy.sparse.csgraph.connected_components with connection="strong").
"""

from collections import deque
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu, spsolve_triangular

from .assemble import Edges


@dataclass
class Cycle:
    """One strongly connected set of cells in the flow graph (a flow cycle or network of cycles)."""

    cells: np.ndarray
    internal_flow: float
    min_edge_flow: float

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


def topological_order(n: int, before: np.ndarray, after: np.ndarray) -> np.ndarray | None:
    """Return an order in which every 'before' cell precedes its 'after' cell, or None if cyclic.

    Uses the strongly-connected-component labels (scipy assigns them in reverse topological
    order); the order is verified, with Kahn's algorithm as a fallback.
    """
    n_comp, labels = strong_components(n, before, after)
    if n_comp < n:
        return None
    order = np.argsort(-labels, kind="stable")
    position = np.empty(n, dtype=np.int64)
    position[order] = np.arange(n)
    if np.all(position[before] < position[after]):
        return order
    return _kahn_order(n, before, after)


def solve_topological(matrix: sp.csr_matrix, rhs: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Solve by substitution after permuting the matrix to lower-triangular form."""
    permuted = matrix[order][:, order].tocsr()
    x_perm = spsolve_triangular(permuted, rhs[order], lower=True)
    x = np.empty_like(x_perm)
    x[order] = x_perm
    return x


def solve_lu(matrix: sp.csr_matrix, rhs: np.ndarray) -> np.ndarray:
    """Solve with one sparse LU factorisation reused for every right-hand-side column."""
    lu = splu(matrix.tocsc())
    return lu.solve(np.asarray(rhs, dtype=float))


def solve_system(
    matrix: sp.csr_matrix, rhs: np.ndarray, solver: str = "auto"
) -> tuple[np.ndarray, str]:
    """Solve matrix @ X = rhs; return (X, name of the solver used)."""
    rhs = np.asarray(rhs, dtype=float)
    if solver == "lu":
        return solve_lu(matrix, rhs), "lu"
    before, after = _dependency_edges(matrix)
    order = topological_order(matrix.shape[0], before, after)
    assert order is not None or solver != "topological", (
        "the flow graph has cycles; the topological solver cannot be used (use 'lu' or 'auto')"
    )
    if order is None:
        return solve_lu(matrix, rhs), "lu"
    return solve_topological(matrix, rhs, order), "topological"
