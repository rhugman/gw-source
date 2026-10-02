"""Face-to-face routing in rectilinear DIS cells (Chowdhury 2016), an alternative to full mixing.

Full mixing (gwsource.trace) assumes that water entering a cell leaves through every outflow face
in proportion to that face's flow, whatever face it came in through. Here each inflow face's
water is partitioned among the outflow faces with Pollock's (1988) semi-analytical velocity
field, as proposed by Chowdhury (2016), and the trace runs on a graph whose nodes are the cell
faces (connections) rather than the cells.

Velocity field (Pollock 1988)
-----------------------------
In a cell of size dx x dy each velocity component varies linearly along its own axis only:
v_x(x) between the face velocities v_x1 and v_x2 (face flow / face area), v_y(y) likewise. A
particle's motions along x and along y are independent, and the time to reach a face along one
axis depends only on the start position s along that axis:
    t = ln(v_face / v(s)) / A,   A = (v2 - v1) / L      (t = distance / v when A = 0),
infinite if the particle heads for an inflow or no-flow face (a stagnation point lies between).
A particle leaves through the face it reaches first.

Partition of a lateral inflow face. Water enters face x1 (say) spread uniformly over the face
(Pollock's assumption). Every particle needs the same time T to cross the cell along x (infinite
if x2 is not an outflow face); along y its exit time depends only on its entry position y0. The
positions whose particles reach face y2 before T form an interval of closed-form length
    m_y2 = min(v_y2 (1 - exp(-A_y T)) / (A_y dy), share of positions moving towards y2)
(m_y1 is the mirror image); the remainder 1 - m_y1 - m_y2 leaves through x2. This reproduces
Chowdhury's (2016) case formulas for cells with two inflow and two outflow faces (stagnation-point
and corner cases) and also covers the cells with one inflow or one outflow face.

Areal sources: Pollock's treatment of distributed recharge
----------------------------------------------------------
A source term can be put on a cell face with a MODPATH IFACE code (FaceRoutingConfig.iface; by
default recharge enters the top face, IFACE 6). A routed cell may have flow through one vertical
face only, and it must be an inflow (recharge on top of a single-layer model, or leakage from the
layer above): the vertical velocity then falls linearly to 0 at the opposite, closed face, so
water entering through a lateral face never reaches a vertical face and the lateral rows above
are unchanged. The vertical inflow takes what is left of each outflow face by mass balance,
    W[top, g] proportional to max(Q_g - sum_f Q_f W[f, g], 0),
which is exact for Pollock's field (its face flows balance).

Which cells are routed
----------------------
A cell is routed if every external term in it with non-zero flow is assigned to a face, no face
carries both inflow and outflow, at most one vertical face has flow and it is an inflow, and the
cell has both inflow and outflow faces. Every other cell is fully mixed exactly as in
gwsource.trace: cells with internal (IFACE 0) sources or sinks such as wells, river or drain
leakage and constant heads; cells with flow through both vertical faces (most cells of a
multi-layer model: this prototype is 2D); strong sinks and sources (where routing and mixing
coincide). Mixing those cells is a choice, not a derivation: water passing a weak sink is not
split by the face it entered through, so weak-sink cells keep the full-mixing error.

Graph
-----
Unknowns: one value per cell (used by mixed cells; routed cells get identity rows) and one per
positive-flow connection, the "face node" e (the water crossing that face). For a face node e
entering cell j through face f:
    routed j:  F_e = sum_g W_j[f, g] (sum_{b on g} q_b / Q_g F_b + sum_{sinks s on g} q_s / Q_g d_s)
    mixed j:   F_e = F_j,
and a mixed cell is a cell node of gross accounting: F_j = sum_e q_e / O_j F_e + sum_s q_s / O_j d_s
(d_s = 1 for a sink term of the destination group). Solved with gwsource.solve (one
factorisation, one column per group). A source term on face f of a routed cell takes
F_k = sum_g W_j[f, g] (...), a source term in a mixed cell F_k = F_j.

Per-cell outputs (comparable with gwsource.trace): volume_through_j = the sum of q F over the
cell's outflow connections plus its destination sink flows; fraction_through = that / O_j (the
outflow-weighted mean over the cell's outflow faces; F_j itself in mixed cells);
volume_from = the sum over the cell's source terms of q_k F_k.

Closure. With In_m the water a node receives through the plans, r_m = In_m - O_m (mixed cells: the
cell residual; face nodes and sinks of a routed cell: their share of that cell's residual, since
rows of W sum to 1 but its columns match the outflow faces only to the flow model's precision):
    sum_k q_k F_k - sum_m r_m F_m = destination inflow
exactly (to round-off), as in gwsource.diagnostics.backward_closure.

Limitations: DIS only; 2D (at most one vertical inflow face per routed cell); steady flow (one
FlowStep); backward mode only; no travel time. Water is still mixed across each face (where a
streamline crosses a face is not kept), so flow oblique to the grid keeps some lateral spreading,
much less than full mixing.

IFACE codes (MODPATH): 0 internal, 1 column-1 side (x1), 2 column+1 side (x2), 3 row+1 side (y1),
4 row-1 side (y2), 5 bottom (layer+1 side), 6 top (layer-1 side). Arrays here use face index
IFACE - 1 (0..5), and -1 for internal.
"""

import math
from dataclasses import dataclass, field

import flopy
import numpy as np
import scipy.sparse as sp

from ..assemble import Edges, cell_budget, flow_edges
from ..config import SOLVERS
from ..diagnostics import Check
from ..flowstep import FlowStep
from ..selectors import Selection
from ..solve import CLOSED_LOOP_TOL, dependency_graph, factorize, isolate_closed_loops

N_FACES = 6
OPPOSITE = np.array([1, 0, 3, 2, 5, 4])
VERTICAL = (4, 5)
SMALL = 1e-8
MAX_EXPONENT = 700.0


@dataclass
class FaceRoutingConfig:
    """Options of route_backward().

    iface: {package name or budget text: MODPATH IFACE code} for terms that enter or leave
        through a cell face (default: recharge through the top face); all other terms are
        internal and make their cell fully mixed.
    route: False mixes every cell (reproduces gwsource.trace.backward on the face graph).
    solver: as TraceConfig.solver.
    closed_loop_tol: as TraceConfig.closed_loop_tol.
    """

    iface: dict[str, int] = field(default_factory=lambda: {"RCH": 6})
    route: bool = True
    solver: str = "auto"
    closed_loop_tol: float = CLOSED_LOOP_TOL

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.solver in SOLVERS, f"solver must be one of {SOLVERS}"
        assert all(0 <= v <= N_FACES for v in self.iface.values()), "IFACE codes are 0..6"


@dataclass
class CellFaces:
    """Per-cell (n, 6) gross outflow and inflow through each face (connections + face terms)."""

    outflow: np.ndarray
    inflow: np.ndarray

    @property
    def net(self) -> np.ndarray:
        """Net outflow per face (positive out of the cell)."""
        return self.outflow - self.inflow


@dataclass
class FaceGraph:
    """The face-routing system: nodes are cells (0..n-1) then connections (n + edge index).

    transition: P (nodes x nodes); sink_share: nodes x terms; source_map / source_sink: terms x
    nodes / terms x terms (F of a source term = source_map X + source_sink D); residual: per node;
    sink_residual: per term (sinks of routed cells).
    """

    edges: Edges
    out_face: np.ndarray
    in_face: np.ndarray
    routed: np.ndarray
    plans: dict[int, np.ndarray]
    transition: sp.csr_matrix
    sink_share: sp.csr_matrix
    source_map: sp.csr_matrix
    source_sink: sp.csr_matrix
    residual: np.ndarray
    sink_residual: np.ndarray


@dataclass
class FaceRoutingResult:
    """Backward face-routing outputs per destination group (per-cell arrays as in BackwardResult).

    face_fraction[g]: F of each face node (graph.edges order); term_fraction[g]: F of each
    external term (meaningful for source terms); residual_term[g]: the closure residual term.
    """

    selections: dict[str, Selection]
    graph: FaceGraph
    fraction_through: dict[str, np.ndarray]
    volume_through: dict[str, np.ndarray]
    volume_from: dict[str, np.ndarray]
    volume_from_by_term: dict[str, dict[str, np.ndarray]]
    destination_inflow: dict[str, float]
    face_fraction: dict[str, np.ndarray]
    term_fraction: dict[str, np.ndarray]
    residual_term: dict[str, float]
    solver_used: str = ""
    closed_loops: list[np.ndarray] = field(default_factory=list)

    @property
    def routed(self) -> np.ndarray:
        """Cell mask of the routed (not fully mixed) cells."""
        return self.graph.routed


# ---------------------------------------------------------------- grid and faces


def read_dis_spacing(grb_file: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (delr, delc) from a DIS binary grid file."""
    grb = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False)
    assert grb.grid_type == "DIS", f"face routing needs a DIS grid, not {grb.grid_type}"
    return np.asarray(grb.delr, dtype=float), np.asarray(grb.delc, dtype=float)


def check_dis(step: FlowStep, delr: np.ndarray, delc: np.ndarray) -> tuple[int, int, int]:
    """Assert that the step is a DIS grid matching delr/delc; return (nlay, nrow, ncol)."""
    assert step.grid_type == "DIS" and len(step.grid_shape) == 3, "face routing needs a DIS grid"
    assert not step.is_network, "face routing works on a single model's cells"
    nlay, nrow, ncol = step.grid_shape
    assert len(delr) == ncol and len(delc) == nrow, "delr/delc do not match the grid shape"
    return nlay, nrow, ncol


def neighbour_face(src: np.ndarray, dst: np.ndarray, shape: tuple[int, int, int]) -> np.ndarray:
    """Return the face index (IFACE - 1) of cell src through which it connects to dst."""
    ks, is_, js = np.unravel_index(src, shape)
    kd, id_, jd = np.unravel_index(dst, shape)
    dk, di, dj = kd - ks, id_ - is_, jd - js
    face = np.full(len(src), -1, dtype=np.int64)
    for (a, b, c), code in {
        (0, 0, -1): 0,
        (0, 0, 1): 1,
        (0, 1, 0): 2,
        (0, -1, 0): 3,
        (1, 0, 0): 4,
        (-1, 0, 0): 5,
    }.items():
        face[(dk == a) & (di == b) & (dj == c)] = code
    assert np.all(face >= 0), "a connection does not join DIS neighbours"
    return face


def term_faces(step: FlowStep, iface: dict[str, int]) -> np.ndarray:
    """Return the face index of every external term (-1 for internal terms)."""
    wanted = {name.upper(): code for name, code in iface.items()}
    codes = np.zeros(len(step.packages), dtype=np.int64)
    for p, package in enumerate(step.packages):
        hits = [wanted[a] for a in package.aliases if a in wanted]
        if hits:
            codes[p] = hits[0]
    return codes[step.term_package] - 1


def cell_faces(
    n: int, edges: Edges, out_face: np.ndarray, step: FlowStep, term_face: np.ndarray
) -> CellFaces:
    """Return per-cell outflow and inflow through each face (connections + face-assigned terms)."""
    outflow, inflow = np.zeros((n, N_FACES)), np.zeros((n, N_FACES))
    np.add.at(outflow, (edges.src, out_face), edges.q)
    np.add.at(inflow, (edges.dst, OPPOSITE[out_face]), edges.q)
    on_face = term_face >= 0
    cells, faces, q = step.term_cell[on_face], term_face[on_face], step.term_flow[on_face]
    np.add.at(outflow, (cells, faces), np.maximum(-q, 0.0))
    np.add.at(inflow, (cells, faces), np.maximum(q, 0.0))
    return CellFaces(outflow=outflow, inflow=inflow)


def routable_cells(step: FlowStep, faces: CellFaces, term_face: np.ndarray) -> np.ndarray:
    """Return the cells that can be routed (see module docstring); all others are mixed."""
    n = step.n_cells
    internal = (term_face < 0) & (step.term_flow != 0.0)
    has_internal = np.bincount(step.term_cell, weights=internal, minlength=n) > 0
    both_ways = ((faces.inflow > 0.0) & (faces.outflow > 0.0)).any(axis=1)
    vertical_in = faces.inflow[:, VERTICAL] > 0.0
    vertical_out = (faces.outflow[:, VERTICAL] > 0.0).any(axis=1)
    has_in = (faces.inflow > 0.0).any(axis=1)
    has_out = (faces.outflow > 0.0).any(axis=1)
    return (
        step.active
        & ~has_internal
        & ~both_ways
        & ~vertical_out
        & (vertical_in.sum(axis=1) <= 1)
        & has_in
        & has_out
    )


# ---------------------------------------------------------------- one cell (Pollock's field)


def _log1p_ratio(z: float) -> float:
    """Return log(1 + z) / z (1 at z = 0)."""
    return 1.0 - 0.5 * z if abs(z) < SMALL else math.log1p(z) / z


def crossing_time(v_in: float, v_out: float, length: float) -> float:
    """Return the time to cross a cell from an inflow face (speed v_in > 0) to the opposite face.

    v_out is the velocity at the opposite face, positive onwards; inf if it is not an outflow.
    """
    if v_out <= 0.0:
        return math.inf
    return length / v_in * _log1p_ratio((v_out - v_in) / v_in)


def _reach(gradient: float, t: float, length: float) -> float:
    """Return (1 - exp(-A t)) / (A L): exit fraction per unit face velocity within time t."""
    if math.isinf(t):
        return 1.0 / (gradient * length) if gradient > 0.0 else math.inf
    x = gradient * t
    if abs(x) < SMALL:
        return t / length * (1.0 - 0.5 * x)
    if -x > MAX_EXPONENT:
        return math.inf
    return -math.expm1(-x) / (gradient * length)


def exit_measures(v1: float, v2: float, length: float, t: float) -> tuple[float, float]:
    """Return the shares of uniformly spread start positions along an axis leaving through face
    1 and face 2 within time t (v1, v2: face velocities in the +axis direction)."""
    span = v2 - v1
    to2 = 0.0 if v2 <= 0.0 else (1.0 if v1 >= 0.0 else v2 / span)
    to1 = 0.0 if v1 >= 0.0 else (1.0 if v2 <= 0.0 else -v1 / span)
    reach = _reach(span / length, t, length)
    m2 = min(v2 * reach, to2) if v2 > 0.0 else 0.0
    m1 = min(-v1 * reach, to1) if v1 < 0.0 else 0.0
    return m1, m2


def _proportional_row(net: np.ndarray) -> np.ndarray:
    """Return the full-mixing row (outflow faces in proportion to their flow)."""
    out = np.maximum(net, 0.0)
    return out / out.sum()


def lateral_row(face: int, net: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Return the shares of a lateral inflow face's water leaving through each face."""
    vel = ((-net[0] / dy, net[1] / dy), (-net[2] / dx, net[3] / dx))
    length = (dx, dy)
    axis, other = face // 2, 1 - face // 2
    v1, v2 = vel[axis]
    v_in, v_out = (v1, v2) if face % 2 == 0 else (-v2, -v1)
    t = crossing_time(v_in, v_out, length[axis])
    m1, m2 = exit_measures(vel[other][0], vel[other][1], length[other], t)
    row = np.zeros(N_FACES)
    row[2 * other], row[2 * other + 1] = m1, m2
    if math.isfinite(t):
        row[OPPOSITE[face]] = max(1.0 - m1 - m2, 0.0)
    total = row.sum()
    return row / total if total > 0.0 else _proportional_row(net)


def vertical_row(plan: np.ndarray, net: np.ndarray) -> np.ndarray:
    """Return the vertical inflow's shares: what the lateral inflows leave of each outflow face."""
    inflow, outflow = np.maximum(-net, 0.0), np.maximum(net, 0.0)
    taken = inflow[:4] @ plan[:4]
    left = np.maximum(outflow - taken, 0.0)
    total = left.sum()
    return left / total if total > 0.0 else _proportional_row(net)


def cell_plan(net: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Return W[inflow face, outflow face]: share of each inflow face's water per outflow face.

    net: (6,) net outflow per face (IFACE order); rows of non-inflow faces are zero.
    """
    plan = np.zeros((N_FACES, N_FACES))
    for face in range(4):
        if net[face] < 0.0:
            plan[face] = lateral_row(face, net, dx, dy)
    for face in VERTICAL:
        if net[face] < 0.0:
            plan[face] = vertical_row(plan, net)
    return plan


# ---------------------------------------------------------------- graph


def _by_cell(n: int, cells: np.ndarray) -> list[list[int]]:
    """Return, per cell, the indices of the entries located in it."""
    out: list[list[int]] = [[] for _ in range(n)]
    for idx, cell in enumerate(cells):
        out[int(cell)].append(idx)
    return out


@dataclass
class _Triplets:
    """Sparse matrix entries collected row by row."""

    rows: list = field(default_factory=list)
    cols: list = field(default_factory=list)
    vals: list = field(default_factory=list)

    def add(self, row: int, col: int, val: float) -> None:
        """Add one entry."""
        self.rows.append(row)
        self.cols.append(col)
        self.vals.append(val)

    def matrix(self, shape: tuple[int, int]) -> sp.csr_matrix:
        """Return the entries as a CSR matrix (duplicates summed)."""
        return sp.csr_matrix((self.vals, (self.rows, self.cols)), shape=shape)


@dataclass
class _Entities:
    """Per-cell entities: connections leaving and entering (edge indices) and terms (indices)."""

    edges_out: list[list[int]]
    edges_in: list[list[int]]
    terms: list[list[int]]


@dataclass
class _Faces:
    """Face of every edge at its source (out) and destination (in), and of every term."""

    edges: Edges
    out_face: np.ndarray
    in_face: np.ndarray
    term_face: np.ndarray


def _mixed_cell(
    j: int, n: int, ent: _Entities, edges: Edges, step: FlowStep, outflow: float, t: dict
) -> None:
    """Add the gross-accounting rows of a fully mixed cell."""
    for e in ent.edges_out[j]:
        t["P"].add(j, n + e, edges.q[e] / outflow)
    for k in ent.terms[j]:
        q = step.term_flow[k]
        if q < 0.0:
            t["S"].add(j, k, -q / outflow)
        elif q > 0.0:
            t["K"].add(k, j, 1.0)


def _routed_cell(
    j: int,
    n: int,
    ent: _Entities,
    faces: _Faces,
    step: FlowStep,
    plan: np.ndarray,
    cell: CellFaces,
    t: dict,
    residual: np.ndarray,
    sink_residual: np.ndarray,
) -> None:
    """Add the face-routing rows of a routed cell; set its outflow entities' residuals."""
    q_out = cell.outflow[j]
    arrived = cell.inflow[j] @ plan
    flow = step.term_flow
    outs = [(n + e, int(faces.out_face[e]), faces.edges.q[e], False) for e in ent.edges_out[j]]
    outs += [(k, int(faces.term_face[k]), -flow[k], True) for k in ent.terms[j] if flow[k] < 0]
    ins = [(n + e, int(faces.in_face[e]), False) for e in ent.edges_in[j]]
    ins += [(k, int(faces.term_face[k]), True) for k in ent.terms[j] if flow[k] > 0]
    for row, f, is_term in ins:
        for col, g, q, is_sink in outs:
            share = plan[f, g] * q / q_out[g]
            if share == 0.0:
                continue
            key = ("Kd" if is_sink else "K") if is_term else ("S" if is_sink else "P")
            t[key].add(row, col, share)
    for col, g, q, is_sink in outs:
        target = sink_residual if is_sink else residual
        target[col] = q / q_out[g] * arrived[g] - q


def build_graph(
    step: FlowStep, delr: np.ndarray, delc: np.ndarray, config: FaceRoutingConfig
) -> FaceGraph:
    """Return the face-routing graph of a DIS step (see module docstring)."""
    shape = check_dis(step, delr, delc)
    n, n_terms = step.n_cells, step.n_terms
    edges = flow_edges(step)
    out_face = neighbour_face(edges.src, edges.dst, shape)
    term_face = term_faces(step, config.iface)
    faces = cell_faces(n, edges, out_face, step, term_face)
    routed = routable_cells(step, faces, term_face) & config.route
    budget = cell_budget(step, edges)
    n_nodes = n + len(edges.q)
    face_of = _Faces(edges, out_face, OPPOSITE[out_face], term_face)
    residual, sink_residual = np.zeros(n_nodes), np.zeros(n_terms)
    ent = _Entities(_by_cell(n, edges.src), _by_cell(n, edges.dst), _by_cell(n, step.term_cell))
    t = {key: _Triplets() for key in ("P", "S", "K", "Kd")}
    rows, cols = np.unravel_index(np.arange(n), shape)[1:]
    plans = {}
    for j in range(n):
        if routed[j]:
            plans[j] = cell_plan(faces.net[j], delr[cols[j]], delc[rows[j]])
            _routed_cell(j, n, ent, face_of, step, plans[j], faces, t, residual, sink_residual)
        elif budget.outflow[j] > 0.0:
            _mixed_cell(j, n, ent, edges, step, budget.outflow[j], t)
            residual[j] = budget.residual[j]
        else:
            for k in ent.terms[j]:
                if step.term_flow[k] > 0.0:
                    t["K"].add(k, j, 1.0)
    for e in np.flatnonzero(~routed[edges.dst]):
        t["P"].add(n + e, int(edges.dst[e]), 1.0)
    return FaceGraph(
        edges=edges,
        out_face=out_face,
        in_face=face_of.in_face,
        routed=routed,
        plans=plans,
        transition=t["P"].matrix((n_nodes, n_nodes)),
        sink_share=t["S"].matrix((n_nodes, n_terms)),
        source_map=t["K"].matrix((n_terms, n_nodes)),
        source_sink=t["Kd"].matrix((n_terms, n_terms)),
        residual=residual,
        sink_residual=sink_residual,
    )


# ---------------------------------------------------------------- trace


def destination_matrix(step: FlowStep, groups: dict[str, Selection]) -> np.ndarray:
    """Return D (terms x groups): 1 where a selected term is a sink."""
    sink = step.term_flow < 0.0
    return np.column_stack([(sel.terms & sink).astype(float) for sel in groups.values()])


def _solve(graph: FaceGraph, rhs: np.ndarray, config: FaceRoutingConfig):
    """Isolate closed loops, factorise I - P and solve; return (X, solver kind, loops)."""
    n_nodes = graph.transition.shape[0]
    matrix = (sp.identity(n_nodes, format="csr") - graph.transition).tocsr()
    dep = None if config.solver == "lu" else dependency_graph(matrix)
    matrix, rhs, loops = isolate_closed_loops(matrix, rhs, config.closed_loop_tol, dep)
    factor = factorize(matrix, config.solver, None if loops else dep)
    if loops:
        factor.zero_rows = np.concatenate(loops)
    return factor.solve(rhs).reshape(rhs.shape), factor.kind, loops


def _by_package(step: FlowStep, values: np.ndarray) -> dict[str, np.ndarray]:
    """Return {package: per-cell sum of values over its terms} for packages with source terms."""
    out = {}
    for p, package in enumerate(step.packages):
        mask = (step.term_package == p) & (step.term_flow > 0.0)
        if mask.any():
            out[package.name] = np.bincount(
                step.term_cell[mask], weights=values[mask], minlength=step.n_cells
            )
    return out


def route_backward(
    step: FlowStep,
    groups: dict[str, Selection],
    delr: np.ndarray,
    delc: np.ndarray,
    config: FaceRoutingConfig | None = None,
) -> FaceRoutingResult:
    """Trace backward from each destination group with face-to-face routing in DIS cells."""
    config = FaceRoutingConfig() if config is None else config
    assert isinstance(groups, dict) and groups, "groups must be a non-empty dict {name: Selection}"
    graph = build_graph(step, np.asarray(delr, float), np.asarray(delc, float), config)
    dest = destination_matrix(step, groups)
    x, kind, loops = _solve(graph, np.asarray(graph.sink_share @ dest), config)
    n = step.n_cells
    edges = graph.edges
    term_f = np.asarray(graph.source_map @ x) + np.asarray(graph.source_sink @ dest)
    sink_q = np.maximum(-step.term_flow, 0.0)
    source_q = np.maximum(step.term_flow, 0.0)
    outflow = cell_budget(step, edges).outflow
    out = {k: {} for k in ("ft", "vt", "vf", "by", "dest", "face", "term", "res")}
    for i, g in enumerate(groups):
        x_face = x[n:, i]
        through = np.bincount(edges.src, weights=edges.q * x_face, minlength=n)
        through += np.bincount(step.term_cell, weights=sink_q * dest[:, i], minlength=n)
        out["vt"][g] = through
        out["ft"][g] = np.divide(through, outflow, out=np.zeros(n), where=outflow > 0.0)
        out["vf"][g] = np.bincount(step.term_cell, weights=source_q * term_f[:, i], minlength=n)
        out["by"][g] = _by_package(step, source_q * term_f[:, i])
        out["dest"][g] = float(sink_q @ dest[:, i])
        out["face"][g] = x_face
        out["term"][g] = term_f[:, i]
        out["res"][g] = float(graph.residual @ x[:, i] + graph.sink_residual @ dest[:, i])
    return FaceRoutingResult(
        selections=groups,
        graph=graph,
        fraction_through=out["ft"],
        volume_through=out["vt"],
        volume_from=out["vf"],
        volume_from_by_term=out["by"],
        destination_inflow=out["dest"],
        face_fraction=out["face"],
        term_fraction=out["term"],
        residual_term=out["res"],
        solver_used=kind,
        closed_loops=loops,
    )


def closure(result: FaceRoutingResult, group: str) -> Check:
    """Return the closure check sum(volume from) - residual term = destination inflow."""
    return Check(
        lhs=float(result.volume_from[group].sum()),
        rhs=result.destination_inflow[group],
        residual_term=result.residual_term[group],
    )
