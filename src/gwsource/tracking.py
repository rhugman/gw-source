"""True transient mixing-cell tracking: tagged water carried through storage (PLAN §2.7, Phase 4).

Snapshots (gwsource.transient) treat each time step as a steady state in which storage release
is a source and storage gain a sink. Here tagged water is carried from step to step instead:
storage is the memory of the system, not a source. Every node (cell or package node) is a fully
mixed reservoir of water volume V; transport is advective only (no dispersion), upstream
weighted and implicit in time, over the flow model's own time steps. Every time step of the
simulation must be in the budget file (OC BUDGET ALL), so the steps join up in time.

Forward scheme (tagged fraction c = C/C0 per node, step n from t_{n-1} to t_n, length dt)
-----------------------------------------------------------------------------------------
Storage terms (STO-SS, STO-SY, the STORAGE record of package nodes and the CSUB storage terms;
TrackingConfig.storage_texts) are removed from the term table. With q_ij >= 0 the intercell
(and package-network) flow i -> j, s_k > 0 the remaining source terms, d_k = |q_k| the remaining
sink terms, O_i = sum_j q_ij + sum_{k in i} d_k, S_i the storage terms of node i summed (positive
= release) and r_i the node's flow residual (net inflow over all terms, storage included):

    V_i^new c_i^n - V_i^old c_i^(n-1)
        = dt [ sum_j q_ji c_j^n + sum_{k in i, k in S} s_k - (O_i + a r_i) c_i^n ]       (1)

S is the tagged source group and a = 1 if TrackingConfig.flow_error_correction (default): the
residual leaves (r > 0) or enters (r < 0) at the node's own fraction, as MF6 GWT's FMI
FLOW_IMBALANCE_CORRECTION does (Langevin et al. 2022, eq. 2-14/2-15). In matrix form
A^n c^n = B^n c^(n-1) + dt s^n with B^n = diag(V^old) and A^n = diag(V^new + dt (O + a r))
- dt Q^T (Q_ij = q_ij). A^n is an M-matrix: its row sums are V^old + dt Src >= 0 (a = 1), so
the solvers of gwsource.solve apply unchanged (topological substitution when the flow graph is
acyclic, block-triangular LU otherwise; no closed-loop isolation is needed, since V > 0 makes
every recirculation loop non-singular).

Volumes. Both modes satisfy V^old - V^new = dt S within a step, which makes (1) consistent: with
a = 1, c = 1 everywhere solves it whenever every source and the initial water are tagged
(row sum of A^n = V^old + dt Src exactly). They differ in how one step's volumes join the next:
- "gwt": V^new = porosity x area x saturated thickness at the end of the step (package
  nodes: the VOLUME of their STORAGE record) and V^old = V^new + dt S, exactly as MF6 GWT's MST
  (mst_fc_sto) and the advanced transport packages (apt_get_volumes) compute them. The volume
  at the start of step n+1 is then not the volume at the end of step n:
  V^old,n+1 - V^new,n = (Sy - porosity) x area x (fall of the water table in step n+1), plus
  the specific-storage part, whenever porosity differs from the specific yield. At each step
  boundary tagged water c^n x (V^old,n+1 - V^new,n) appears or disappears; it is reported as
  the volume adjustment of the balance. One exception copies MF6 SFT (sft_get_volumes): an
  SFR reach whose storage flow is exactly 0 (SFR without kinematic-wave storage, or a steady
  period) takes the previous step's V^new as V^old (0 at the first step), so its volume is
  carried as in flow mode but its within-step water balance is not closed (reported in
  water_balance_error). This mode reproduces GWT unit-concentration results.
- "flow" (default): the volume is carried by the storage flows themselves. The start volume is
  porosity x saturated volume (package volume) at the end of step 1 plus dt S, then
  V^old,n+1 = V^new,n and V^new = V^old - dt S. The water balance of every node is exact by
  construction and tagged water is conserved across step boundaries. Porosity then only sets
  the initial volume (the mobile water that mixes); the change of volume is the flow model's
  storage change (specific yield and specific storage), so the volume can drift away from
  porosity x saturated volume. A node whose volume would become negative (porosity much smaller
  than the specific yield) stops the run with an error.

Tagged initial water: TrackingConfig.initial_water = {name: "all" or a node mask/indices}
adds one forward column per entry with c^0 = 1 on those nodes and no source: the fraction of
pre-simulation water.

Forward balance per group and step (volumes over the step, all exact to round-off):
    storage_end - storage_start = inflow - outflow - flow_error
with storage_start = sum V^old c^(n-1), storage_end = sum V^new c^n, inflow = dt sum s,
outflow = dt sum_i (sink total of i) c_i (also split by package and by sink group) and
flow_error = dt a sum r_i c_i; volume_adjustment = storage_start^n - storage_end^(n-1) (0 in flow
mode; at step 1 it is 0 and storage_start is the tagged initial water).

Backward (adjoint) scheme
-------------------------
The tagged outflow through a destination group D over the whole simulation is
J = sum_n dt^n d^n . c^n (d^n the destination sink flow per node). Its discrete adjoint runs
backward in time from the end of the simulation, with w^(N+1) = 0:

    (A^n)^T w^n = dt^n d^n + B^(n+1) w^(n+1)                                           (2)

w^n_i is the fraction of the water in node i at the start of step n (time t_(n-1)), or entering
it during step n, that leaves through D before the simulation ends (an exact reading of the
implicit scheme, in which the water present at the start of a step and the water arriving
during it are mixed alike). Multiplying (1) by w^n and (2) by c^n and summing over the steps
gives the duality identity, exact for any volumes and any a:

    J = sum_n dt^n s^n . w^n + sum_i V^old,1_i c^0_i w^1_i                               (3)

(tagged source inflow times the adjoint, plus the tagged initial water times the adjoint at the
start). With every source tagged and c^0 = 1 (and a = 1) the right-hand side splits J by
source term and step: volume_from (per node and step), volume_from_by_package, and the initial
water's share initial_volume_from; their total is the destination outflow (closure). With a = 0
the closure misses sum_n dt r^n . w^n (reported as residual_term).

The backward run also solves (2) for "any sink" (d = every remaining sink) and for the water
still in storage at the end (no d; terminal right-hand side V^new,N). For every node and step
fraction_through[D] + fraction_to_other_sinks + fraction_in_storage_at_end + fraction_unaccounted
= 1, where the unaccounted part is the water removed by the flow-error correction and, in gwt
mode, by the volume adjustments (zero up to the flow residual in flow mode).

Sub-steps (TrackingConfig.substeps = m, default 1): every flow step is split into m equal
transport sub-steps of length dt/m. The flows are constant within a flow step, so this changes
only the time discretisation of the transport, not the flows; the volumes are interpolated
linearly between V^old and V^new (exactly what the constant storage flow gives within the step).
Implicit upstream stepping adds numerical dispersion in time of order dt; sub-steps reduce it
without touching the flow model. Per-step outputs are reported at flow-step boundaries: c at the
end of the step, w at its start, and the step's flow-weighted totals (outflow, volume from,
residual terms) summed over its sub-steps. The duality and closure identities hold unchanged
(the adjoint is that of the sub-stepped scheme). m = 1 reproduces the unsplit scheme exactly.

Limit: with flows held constant for long enough, c^n tends to the steady source_fraction of
gwsource.trace.forward and w^1 to the steady fraction_through of gwsource.trace.backward
(storage terms are zero then, so the snapshot and the tracked systems have the same flows).
"""

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp

from .assemble import Edges, flow_edges, term_totals
from .config import SOLVERS
from .diagnostics import Check
from .flowstep import FlowStep
from .selectors import Selection, _cell_mask
from .solve import factorize
from .transient import GroupSpec, resolve_groups
from .traveltime import water_volume

VOLUME_MODES = ("gwt", "flow")
STORAGE_TEXTS = (
    "STO-SS",
    "STO-SY",
    "STORAGE",
    "CSUB-CGELASTIC",
    "CSUB-ELASTIC",
    "CSUB-INELASTIC",
    "CSUB-WATERCOMP",
)
TIME_RTOL = 1e-9
VOLUME_RTOL = 1e-9
ANY_SINK = "__any_sink__"  # internal adjoint columns of track_backward
STORAGE_END = "__storage_at_end__"
ACTIVE = "__active__"
BALANCE_KEYS = (
    "storage_start",
    "storage_end",
    "inflow",
    "outflow",
    "flow_error",
    "volume_adjustment",
    "error",
)


@dataclass
class TrackingConfig:
    """Options of transient tracking (track_forward, track_backward).

    porosity: scalar, per-node array or {model: per-cell array} (required).
    volume_mode: "flow" (default: volumes carried by the storage flows; exact water balance) or
        "gwt" (volumes from porosity x saturated volume, as MF6 GWT; use it to compare with GWT);
        see the module docstring.
    flow_error_correction: the node residual leaves or enters at the node's fraction (as GWT's
        FLOW_IMBALANCE_CORRECTION); makes the closure exact.
    initial_water: {name: "all" or a node mask / node indices}: forward columns of tagged
        initial water; backward, the initial water's share of each destination's outflow.
    solver: "auto", "topological", "block" or "lu" (gwsource.solve).
    storage_texts: budget texts of the storage terms (taken out of the term table).
    keep_series: keep every step's per-node outputs (else only the last step's state).
    substeps: number of equal transport sub-steps per flow step (1 = the flow model's steps).
    """

    porosity: float | np.ndarray | dict
    volume_mode: str = "flow"
    flow_error_correction: bool = True
    initial_water: dict | None = None
    solver: str = "auto"
    storage_texts: tuple[str, ...] = STORAGE_TEXTS
    keep_series: bool = True
    substeps: int = 1

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.volume_mode in VOLUME_MODES, f"volume_mode must be one of {VOLUME_MODES}"
        assert self.solver in SOLVERS, f"solver must be one of {SOLVERS}"
        assert self.porosity is not None, "porosity is required"
        assert int(self.substeps) == self.substeps >= 1, "substeps must be an integer >= 1"


@dataclass
class StepFlows:
    """The flows of one step as transient tracking uses them (storage terms taken out)."""

    edges: Edges
    tracked: np.ndarray
    source: np.ndarray
    sink: np.ndarray
    outflow: np.ndarray
    inflow: np.ndarray
    storage: np.ndarray
    residual: np.ndarray


@dataclass
class StepVolumes:
    """Water volume of every node at the start (old) and end (new) of a step."""

    old: np.ndarray
    new: np.ndarray


@dataclass
class ForwardTracking:
    """Forward transient tracking: tagged fractions over time and tagged-water balances.

    source_fraction[g]: (n_steps, n) fraction c at the end of each step (only the last step if
    keep_series is False); initial[g]: c at the start. balance[g][key]: per-step volumes (keys in
    BALANCE_KEYS). outflow_by_package[g][package] and outflow_to[sink group][g]: tagged volume
    leaving per step. water_balance_error: per step, max |V^new - V^old - dt (net inflow)| over
    the nodes; volume_jump: max |V^old,n - V^new,n-1| (0 in flow mode).
    """

    config: TrackingConfig
    groups: list[str]
    steps: list[tuple[int, int]]
    totim: np.ndarray
    delt: np.ndarray
    source_fraction: dict[str, np.ndarray]
    initial: dict[str, np.ndarray]
    balance: dict[str, dict[str, np.ndarray]]
    outflow_by_package: dict[str, dict[str, np.ndarray]]
    outflow_to: dict[str, dict[str, np.ndarray]]
    water_balance_error: np.ndarray
    volume_jump: np.ndarray
    template: FlowStep
    solver_used: list[str] = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def cumulative_outflow(self, group: str) -> dict[str, np.ndarray]:
        """Return the tagged outflow of a group by package, cumulated over the steps."""
        return {p: np.cumsum(v) for p, v in self.outflow_by_package[group].items()}


@dataclass
class BackwardTracking:
    """Backward (adjoint) transient tracking from destination groups.

    Row n of every (n_steps, n) array is step n: the water in the node at the start of step n
    (time_start[n]) or entering it during step n. fraction_through[g]: fraction leaving
    through g before the end; fraction_any_sink: through any sink; fraction_in_storage_at_end:
    still in the model at the end. volume_from[g]: water entering through the node's source
    terms during the step that leaves through g (by package: volume_from_by_package[g][p], per
    step totals); initial_volume_from[g]: initial water of each node that leaves through g;
    volume_from_group[g][source group] and initial_volume_from_group[g][name]: the same for the
    source groups and initial_water entries given. destination_outflow[g]: water leaving
    through g in each step. residual_term[g]: per step dt r . w (closure term when the flow-error
    correction is off). active: nodes holding or passing water in the step (the fractions of the
    other nodes are 0 and meaningless).
    """

    config: TrackingConfig
    groups: list[str]
    steps: list[tuple[int, int]]
    totim: np.ndarray
    delt: np.ndarray
    fraction_through: dict[str, np.ndarray]
    fraction_any_sink: np.ndarray
    fraction_in_storage_at_end: np.ndarray
    volume_from: dict[str, np.ndarray]
    volume_from_by_package: dict[str, dict[str, np.ndarray]]
    volume_from_group: dict[str, dict[str, np.ndarray]]
    initial_volume_from: dict[str, np.ndarray]
    initial_volume_from_group: dict[str, dict[str, float]]
    destination_outflow: dict[str, np.ndarray]
    residual_term: dict[str, np.ndarray]
    active: np.ndarray
    template: FlowStep
    solver_used: list[str] = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def time_start(self) -> np.ndarray:
        """Simulation time at the start of each step."""
        return self.totim - self.delt

    def fraction_to_other_sinks(self, group: str) -> np.ndarray:
        """Return the fraction leaving through a sink outside the group before the end."""
        return self.fraction_any_sink - self.fraction_through[group]

    @property
    def fraction_unaccounted(self) -> np.ndarray:
        """Return 1 - any sink - storage at end (flow-error correction, volume adjustments).

        NaN on nodes that are not active in the step.
        """
        rest = 1.0 - self.fraction_any_sink - self.fraction_in_storage_at_end
        return np.where(self.active, rest, np.nan)


# ---------------------------------------------------------------- one step


def storage_mask(step: FlowStep, texts: tuple[str, ...] = STORAGE_TEXTS) -> np.ndarray:
    """Return the term entries that are storage terms (by budget text)."""
    wanted = {t.upper() for t in texts}
    is_storage = np.array([p.text.upper() in wanted for p in step.packages], dtype=bool)
    return is_storage[step.term_package] if step.n_terms else np.zeros(0, dtype=bool)


def step_flows(step: FlowStep, storage_texts: tuple[str, ...] = STORAGE_TEXTS) -> StepFlows:
    """Return the edges, non-storage source and sink totals, storage and residual per node."""
    n = step.n_cells
    edges = flow_edges(step)
    is_storage = storage_mask(step, storage_texts)
    source, sink = term_totals(step, ~is_storage)
    storage = np.bincount(
        step.term_cell, weights=np.where(is_storage, step.term_flow, 0.0), minlength=n
    )
    edge_out = np.bincount(edges.src, weights=edges.q, minlength=n)
    edge_in = np.bincount(edges.dst, weights=edges.q, minlength=n)
    return StepFlows(
        edges=edges,
        tracked=~is_storage,
        source=source,
        sink=sink,
        outflow=edge_out + sink,
        inflow=edge_in + source,
        storage=storage,
        residual=edge_in + source - edge_out - sink + storage,
    )


def sfr_nodes(step: FlowStep) -> np.ndarray:
    """Return a node mask of the SFR reaches of a network step."""
    mask = np.zeros(step.n_cells, dtype=bool)
    for block in step.blocks:
        if block.kind == "package" and block.package_type == "SFR":
            mask[block.nodes] = True
    return mask


def gwt_volumes(
    step: FlowStep, flows: StepFlows, porosity, delt: float, previous: np.ndarray | None = None
) -> StepVolumes:
    """Return V^new = porosity x saturated volume (or package volume), V^old = V^new + dt S.

    SFR reaches whose storage flow is exactly 0 (SFR without kinematic-wave storage, or a
    steady-state period) take the previous step's V^new as V^old instead (0 before the first
    step), as MF6 SFT does (sft_get_volumes); previous is that step's V^new.
    """
    new = water_volume(step, porosity)
    old = new + delt * flows.storage
    carry = sfr_nodes(step) & (flows.storage == 0.0)
    if carry.any():
        before = np.zeros(step.n_cells) if previous is None else previous
        old = np.where(carry, np.where(new == 0.0, 0.0, before), old)
    return StepVolumes(old=old, new=new)


def carried_volumes(old: np.ndarray, flows: StepFlows, delt: float) -> StepVolumes:
    """Return flow-mode volumes: V^new = V^old - dt S (asserting that no volume is negative)."""
    new = old - delt * flows.storage
    scale = max(float(np.abs(old).max(initial=0.0)), 1.0)
    assert new.min(initial=0.0) >= -VOLUME_RTOL * scale, (
        "flow volume mode: a node volume became negative (the storage change exceeds the water "
        "volume; use a larger porosity or volume_mode='gwt')"
    )
    return StepVolumes(old=old, new=np.maximum(new, 0.0))


def substep_volumes(volumes: StepVolumes, index: int, n_sub: int) -> StepVolumes:
    """Return the volumes of sub-step index (0-based) of n_sub, linear between V^old and V^new.

    The first sub-step starts at V^old and the last ends at V^new exactly, so n_sub = 1 returns
    the step's own volumes.
    """
    if n_sub == 1:
        return volumes
    change = volumes.new - volumes.old
    old = volumes.old if index == 0 else volumes.old + change * (index / n_sub)
    last = index == n_sub - 1
    new = volumes.new if last else volumes.old + change * ((index + 1) / n_sub)
    return StepVolumes(old=old, new=new)


def empty_rows(flows: StepFlows, volumes: StepVolumes) -> np.ndarray:
    """Return the nodes with no water and no flow (inactive or dry): identity rows, value 0."""
    return (volumes.new <= 0.0) & (flows.outflow <= 0.0) & (flows.inflow <= 0.0)


def step_matrix(
    flows: StepFlows, volumes: StepVolumes, delt: float, correction: bool
) -> sp.csr_matrix:
    """Return A = diag(V^new + dt (O + a r)) - dt Q^T of the forward step equation (1)."""
    n = len(volumes.new)
    diag = volumes.new + delt * flows.outflow
    if correction:
        diag = diag + delt * flows.residual
    empty = empty_rows(flows, volumes)
    assert np.all(diag[~empty] > 0.0), "transient tracking: a node has a non-positive diagonal"
    diag = np.where(empty, 1.0, diag)
    e = flows.edges
    rows = np.concatenate([np.arange(n), e.dst])
    cols = np.concatenate([np.arange(n), e.src])
    vals = np.concatenate([diag, -delt * e.q])
    return sp.csr_matrix((vals, (rows, cols)), shape=(n, n))


def group_flows(
    step: FlowStep, groups: dict[str, Selection], tracked: np.ndarray, sign: int
) -> np.ndarray:
    """Return (nodes, groups) totals of |q| over each group's tracked terms of the given sign."""
    flow = np.maximum(sign * step.term_flow, 0.0)
    out = np.zeros((step.n_cells, len(groups)))
    for g, sel in enumerate(groups.values()):
        assert len(sel.terms) == step.n_terms, "group selected on a different step"
        weights = np.where(sel.terms & tracked, flow, 0.0)
        out[:, g] = np.bincount(step.term_cell, weights=weights, minlength=step.n_cells)
    return out


def by_package(step: FlowStep, term_values: np.ndarray, tracked: np.ndarray) -> dict[str, float]:
    """Return {package name: sum of term_values} over the packages with tracked term entries."""
    n_packages = len(step.packages)
    totals = np.bincount(step.term_package, weights=term_values, minlength=n_packages)
    present = np.bincount(step.term_package, weights=tracked, minlength=n_packages) > 0
    return {p.name: float(t) for p, t, keep in zip(step.packages, totals, present) if keep}


def _add_series(store: dict, key: str, index: int, value: float, n_steps: int) -> None:
    """Add value to store[key][index], creating a zero series of n_steps if needed."""
    store.setdefault(key, np.zeros(n_steps))[index] += value


# ---------------------------------------------------------------- time and setup


def check_time(totim: float, delt: float, previous: float, kstpkper: tuple) -> None:
    """Assert that a step starts where the previous one ended (every step must be saved)."""
    assert abs(totim - delt - previous) <= TIME_RTOL * max(abs(totim), 1.0), (
        f"step {kstpkper} does not follow the previous saved step: transient tracking needs the "
        "budget of every time step (OC: BUDGET ALL)"
    )


def initial_columns(step: FlowStep, initial_water: dict | None) -> dict[str, np.ndarray]:
    """Return {name: c^0} of the tagged-initial-water entries ('all' or node mask/indices)."""
    out = {}
    for name, nodes in (initial_water or {}).items():
        if isinstance(nodes, str):
            assert nodes == "all", "initial_water entries are 'all' or node masks / indices"
            out[name] = step.active.astype(float)
        else:
            out[name] = _cell_mask(step, nodes).astype(float)
    return out


def _resolve(step: FlowStep, spec: GroupSpec | None) -> dict[str, Selection]:
    """Return the groups of one step, or {} if no spec."""
    return {} if spec is None else resolve_groups(step, spec)


def _check_names(names: list[str] | None, groups: dict, kstpkper: tuple) -> list[str]:
    """Return the group names, asserting that they do not change between steps."""
    if names is None:
        return list(groups)
    assert list(groups) == names, f"group names changed at step {kstpkper}"
    return names


def step_volumes(
    step: FlowStep,
    flows: StepFlows,
    config: TrackingConfig,
    delt: float,
    previous: np.ndarray | None,
) -> StepVolumes:
    """Return the step's volumes; previous is the previous step's V^new (None at the start).

    gwt mode uses previous only for the SFR rule of gwt_volumes(); flow mode carries it, and
    starts from porosity x saturated volume + dt S of the first step.
    """
    if config.volume_mode == "gwt":
        return gwt_volumes(step, flows, config.porosity, delt, previous)
    if previous is None:
        previous = water_volume(step, config.porosity) + delt * flows.storage
    return carried_volumes(previous, flows, delt)


def water_balance_error(
    flows: StepFlows, volumes: StepVolumes, delt: float, correction: bool
) -> float:
    """Return max |V^new - V^old - dt (I - O - a r)| over the nodes (non-storage flows)."""
    net = flows.inflow - flows.outflow - (flows.residual if correction else 0.0)
    return float(np.abs(volumes.new - volumes.old - delt * net).max(initial=0.0))


# ---------------------------------------------------------------- forward


def track_forward(
    reader,
    sources: GroupSpec | None,
    config: TrackingConfig,
    sinks: GroupSpec | None = None,
) -> ForwardTracking:
    """Carry tagged water from source groups (and tagged initial water) through every step.

    reader: StepReader (gwsource.open_model) or NetworkReader (gwsource.open_simulation).
    sources, sinks: dict {group: select() kwargs} or a function step -> {group: Selection},
    re-selected on every step; sinks only report the tagged outflow through each sink group.
    """
    steps = list(reader.steps)
    n_steps = len(steps)
    state = _ForwardState(n_steps=n_steps, keep=config.keep_series)
    for index, kstpkper in enumerate(steps):
        step = reader.read(kstpkper)
        delt = reader.step_length(kstpkper)
        check_time(step.totim, delt, state.time, kstpkper)
        _forward_step(state, step, index, delt, sources, sinks, config)
        state.time = step.totim
    return state.result(config, steps, step)


@dataclass
class _ForwardState:
    """Running state of a forward run."""

    n_steps: int
    keep: bool
    time: float = 0.0
    names: list[str] | None = None
    n_sources: int = 0
    c: np.ndarray | None = None
    initial: dict = field(default_factory=dict)
    v_new: np.ndarray | None = None
    series: dict = field(default_factory=dict)
    balance: dict = field(default_factory=dict)
    by_package: dict = field(default_factory=dict)
    outflow_to: dict = field(default_factory=dict)
    sink_names: list[str] | None = None
    totim: list = field(default_factory=list)
    delt: list = field(default_factory=list)
    wb_error: list = field(default_factory=list)
    jump: list = field(default_factory=list)
    solvers: list = field(default_factory=list)

    def result(self, config: TrackingConfig, steps: list, template: FlowStep) -> ForwardTracking:
        """Return the ForwardTracking of the finished run."""
        return ForwardTracking(
            config=config,
            groups=self.names,
            steps=steps,
            totim=np.asarray(self.totim),
            delt=np.asarray(self.delt),
            source_fraction={g: np.asarray(v) for g, v in self.series.items()},
            initial=self.initial,
            balance=self.balance,
            outflow_by_package=self.by_package,
            outflow_to=self.outflow_to,
            water_balance_error=np.asarray(self.wb_error),
            volume_jump=np.asarray(self.jump),
            template=template,
            solver_used=self.solvers,
        )


def _start_forward(
    state: _ForwardState, step: FlowStep, groups: dict, config: TrackingConfig
) -> None:
    """Set the group names and the initial state on the first step."""
    initial = initial_columns(step, config.initial_water)
    clash = set(initial) & set(groups)
    assert not clash, f"initial_water names clash with source groups: {sorted(clash)}"
    state.names = list(groups) + list(initial)
    assert state.names, "no source group and no initial water to track"
    state.n_sources = len(groups)
    c0 = np.zeros((step.n_cells, len(state.names)))
    for i, values in enumerate(initial.values()):
        c0[:, state.n_sources + i] = values
    state.c = c0
    state.initial = {g: c0[:, i].copy() for i, g in enumerate(state.names)}


def _forward_step(
    state: _ForwardState,
    step: FlowStep,
    index: int,
    delt: float,
    sources: GroupSpec | None,
    sinks: GroupSpec | None,
    config: TrackingConfig,
) -> None:
    """Advance the forward state by one step and record its outputs."""
    groups = _resolve(step, sources)
    if index == 0:
        _start_forward(state, step, groups, config)
    assert list(groups) == state.names[: state.n_sources], f"groups changed at {step.kstpkper}"
    flows = step_flows(step, config.storage_texts)
    volumes = step_volumes(step, flows, config, delt, state.v_new)
    s = np.zeros_like(state.c)
    s[:, : state.n_sources] = group_flows(step, groups, flows.tracked, +1)
    c, c_mean, kind = _forward_substeps(state.c, flows, volumes, delt, s, config)
    _forward_records(state, step, index, delt, flows, volumes, s, c, c_mean, config)
    sink_groups = _resolve(step, sinks)
    state.sink_names = _check_names(state.sink_names, sink_groups, step.kstpkper)
    sink_flow = group_flows(step, sink_groups, flows.tracked, -1)
    for k, sink in enumerate(sink_groups):
        for i, g in enumerate(state.names):
            out = delt * float(sink_flow[:, k] @ c_mean[:, i])
            _add_series(state.outflow_to.setdefault(sink, {}), g, index, out, state.n_steps)
    jump = 0.0 if state.v_new is None else float(np.abs(volumes.old - state.v_new).max())
    state.jump.append(jump)
    state.wb_error.append(water_balance_error(flows, volumes, delt, config.flow_error_correction))
    state.solvers.append(kind)
    state.totim.append(step.totim)
    state.delt.append(delt)
    state.c, state.v_new = c, volumes.new


def _forward_substeps(
    c0: np.ndarray,
    flows: StepFlows,
    volumes: StepVolumes,
    delt: float,
    s: np.ndarray,
    config: TrackingConfig,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Advance c over one flow step in config.substeps sub-steps.

    Return (c at the end, mean of the sub-step values (the step's outflow weighting), solver).
    """
    n_sub = config.substeps
    dt = delt / n_sub
    c, c_mean, factor = c0, None, None
    steady = np.array_equal(volumes.old, volumes.new)
    for m in range(n_sub):
        sub = substep_volumes(volumes, m, n_sub)
        empty = empty_rows(flows, sub)
        if factor is None or not steady:
            matrix = step_matrix(flows, sub, dt, config.flow_error_correction)
            factor = factorize(matrix, config.solver)
        rhs = sub.old[:, None] * c + dt * s
        rhs[empty] = 0.0
        c = factor.solve(rhs).reshape(c0.shape)
        c_mean = c / n_sub if c_mean is None else c_mean + c / n_sub
    return c, c_mean, factor.kind


def _forward_records(
    state: _ForwardState,
    step: FlowStep,
    index: int,
    delt: float,
    flows: StepFlows,
    volumes: StepVolumes,
    s: np.ndarray,
    c: np.ndarray,
    c_mean: np.ndarray,
    config: TrackingConfig,
) -> None:
    """Record one step's fractions, balance and outflow by package for every group.

    c is the fraction at the end of the step, c_mean its mean over the step's sub-steps (equal
    to c without sub-steps), which weights the outflows.
    """
    correction = 1.0 if config.flow_error_correction else 0.0
    sink_terms = np.where(flows.tracked, np.maximum(-step.term_flow, 0.0), 0.0)
    for i, g in enumerate(state.names):
        start = float(volumes.old @ state.c[:, i])
        end = float(volumes.new @ c[:, i])
        inflow = delt * float(s[:, i].sum())
        outflow = delt * float(flows.sink @ c_mean[:, i])
        error_flow = delt * correction * float(flows.residual @ c_mean[:, i])
        previous = start if state.v_new is None else float(state.v_new @ state.c[:, i])
        record = {
            "storage_start": start,
            "storage_end": end,
            "inflow": inflow,
            "outflow": outflow,
            "flow_error": error_flow,
            "volume_adjustment": start - previous,
            "error": end - start - inflow + outflow + error_flow,
        }
        for key, value in record.items():
            _add_series(state.balance.setdefault(g, {}), key, index, value, state.n_steps)
        out_terms = delt * sink_terms * c_mean[step.term_cell, i]
        for package, value in by_package(step, out_terms, flows.tracked).items():
            _add_series(state.by_package.setdefault(g, {}), package, index, value, state.n_steps)
        _keep(state.series, g, c[:, i], index, state.n_steps, state.keep)


def _keep(
    series: dict, key: str, values: np.ndarray, index: int, n_steps: int, keep: bool
) -> None:
    """Store one step's per-node values (every step if keep, else only the latest)."""
    if not keep:
        series[key] = values[None, :].copy()
        return
    stack = series.setdefault(key, np.zeros((n_steps, values.size)))
    stack[index] = values


# ---------------------------------------------------------------- backward


def flow_mode_end_volume(reader, steps: list, config: TrackingConfig) -> np.ndarray:
    """Return V^new of the last step in flow mode (a forward pass over the storage terms)."""
    volume = None
    for kstpkper in steps:
        step = reader.read(kstpkper)
        delt = reader.step_length(kstpkper)
        flows = step_flows(step, config.storage_texts)
        volume = step_volumes(step, flows, config, delt, volume).new
    return volume


def track_backward(
    reader,
    destinations: GroupSpec,
    config: TrackingConfig,
    sources: GroupSpec | None = None,
) -> BackwardTracking:
    """Solve the adjoint backward in time from the end of the simulation for each destination.

    sources (optional): source groups whose share of each destination's outflow is reported
    per step (volume_from_group); config.initial_water entries give initial_volume_from_group.
    """
    steps = list(reader.steps)
    state = _BackwardState(n_steps=len(steps), keep=config.keep_series)
    if config.volume_mode == "flow":
        state.v_new_next = flow_mode_end_volume(reader, steps, config)
    template = upcoming = reader.read(steps[-1])
    for index in range(len(steps) - 1, -1, -1):
        step = upcoming
        upcoming = reader.read(steps[index - 1]) if index > 0 else None
        previous = _previous_volume(upcoming, step, config)
        delt = reader.step_length(steps[index])
        _backward_step(state, step, index, delt, destinations, sources, config, previous)
    _check_times(state, steps)
    return state.result(config, steps, template)


def _previous_volume(
    before: FlowStep | None, step: FlowStep, config: TrackingConfig
) -> np.ndarray | None:
    """Return the previous step's gwt-mode V^new when the SFR rule of gwt_volumes() needs it."""
    if before is None or config.volume_mode != "gwt" or not sfr_nodes(step).any():
        return None
    return water_volume(before, config.porosity)


@dataclass
class _BackwardState:
    """Running state of a backward run (steps visited last to first)."""

    n_steps: int
    keep: bool
    names: list[str] | None = None
    source_names: list[str] | None = None
    carry: np.ndarray | None = None
    v_new_next: np.ndarray | None = None
    series: dict = field(default_factory=dict)
    volume_from: dict = field(default_factory=dict)
    by_package: dict = field(default_factory=dict)
    from_group: dict = field(default_factory=dict)
    initial_from: dict = field(default_factory=dict)
    initial_group: dict = field(default_factory=dict)
    outflow: dict = field(default_factory=dict)
    residual_term: dict = field(default_factory=dict)
    totim: np.ndarray | None = None
    delt: np.ndarray | None = None
    solvers: list = field(default_factory=list)

    def result(self, config: TrackingConfig, steps: list, template: FlowStep) -> BackwardTracking:
        """Return the BackwardTracking of the finished run."""
        return BackwardTracking(
            config=config,
            groups=self.names,
            steps=steps,
            totim=self.totim,
            delt=self.delt,
            fraction_through={g: self.series[g] for g in self.names},
            fraction_any_sink=self.series[ANY_SINK],
            fraction_in_storage_at_end=self.series[STORAGE_END],
            volume_from=self.volume_from,
            volume_from_by_package=self.by_package,
            volume_from_group=self.from_group,
            initial_volume_from=self.initial_from,
            initial_volume_from_group=self.initial_group,
            destination_outflow=self.outflow,
            residual_term=self.residual_term,
            active=self.series[ACTIVE] > 0.0,
            template=template,
            solver_used=self.solvers[::-1],
        )


def _backward_rhs(
    carry: np.ndarray | None,
    step: FlowStep,
    flows: StepFlows,
    volumes: StepVolumes,
    d: np.ndarray,
    delt: float,
    empty: np.ndarray,
) -> np.ndarray:
    """Return dt d^n + B^(n+1) w^(n+1) (+ V^new,N for the storage column at the last step)."""
    rhs = np.column_stack([delt * d, delt * flows.sink, np.zeros(step.n_cells)])
    if carry is None:
        rhs[:, -1] = volumes.new
    else:
        rhs += carry
    rhs[empty] = 0.0
    return rhs


def _backward_substeps(
    carry: np.ndarray | None,
    step: FlowStep,
    flows: StepFlows,
    volumes: StepVolumes,
    d: np.ndarray,
    delt: float,
    config: TrackingConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]:
    """Solve the adjoint of one flow step over its sub-steps, last to first.

    carry is B w of the following step (None at the end of the simulation). Return (w at the
    start of the step, mean of the sub-step values (weights the step's inflows), carry for the
    preceding step, empty rows of the first sub-step, solver).
    """
    n_sub = config.substeps
    dt = delt / n_sub
    w_mean, factor = None, None
    steady = np.array_equal(volumes.old, volumes.new)
    for m in range(n_sub - 1, -1, -1):
        sub = substep_volumes(volumes, m, n_sub)
        empty = empty_rows(flows, sub)
        if factor is None or not steady:
            matrix = step_matrix(flows, sub, dt, config.flow_error_correction)
            factor = factorize(matrix.T.tocsr(), config.solver)
        rhs = _backward_rhs(carry, step, flows, sub, d, dt, empty)
        w = factor.solve(rhs).reshape(rhs.shape)
        w_mean = w / n_sub if w_mean is None else w_mean + w / n_sub
        carry = sub.old[:, None] * w
    return w, w_mean, carry, empty, factor.kind


def _backward_step(
    state: "_BackwardState",
    step: FlowStep,
    index: int,
    delt: float,
    destinations: GroupSpec,
    sources: GroupSpec | None,
    config: TrackingConfig,
    previous: np.ndarray | None,
) -> None:
    """Solve the adjoint of one step and record its outputs."""
    groups = resolve_groups(step, destinations)
    state.names = _check_names(state.names, groups, step.kstpkper)
    for reserved in (ANY_SINK, STORAGE_END, ACTIVE):
        assert reserved not in groups, f"group name {reserved} is reserved"
    flows = step_flows(step, config.storage_texts)
    volumes = _backward_volumes(state, step, flows, config, delt, previous)
    d = group_flows(step, groups, flows.tracked, -1)
    w, w_mean, carry, empty, kind = _backward_substeps(
        state.carry, step, flows, volumes, d, delt, config
    )
    _keep(state.series, ACTIVE, (~empty).astype(float), index, state.n_steps, state.keep)
    _backward_records(state, step, index, delt, flows, w, w_mean, d, groups, sources)
    if index == 0:
        _initial_records(state, step, volumes, w, config)
    _time_record(state, index, step.totim, delt)
    state.solvers.append(kind)
    state.carry = carry
    state.v_new_next = volumes.old


def _backward_volumes(
    state: "_BackwardState",
    step: FlowStep,
    flows: StepFlows,
    config: TrackingConfig,
    delt: float,
    previous: np.ndarray | None,
) -> StepVolumes:
    """Return the step's volumes; in flow mode V^new is the next step's V^old (carried back)."""
    if config.volume_mode == "gwt":
        return gwt_volumes(step, flows, config.porosity, delt, previous)
    new = state.v_new_next
    return StepVolumes(old=new + delt * flows.storage, new=new)


def _backward_records(
    state: "_BackwardState",
    step: FlowStep,
    index: int,
    delt: float,
    flows: StepFlows,
    w: np.ndarray,
    w_mean: np.ndarray,
    d: np.ndarray,
    groups: dict[str, Selection],
    sources: GroupSpec | None,
) -> None:
    """Record one step's adjoint fractions and volumes from sources for every group.

    w is the adjoint at the start of the step, w_mean its mean over the step's sub-steps (equal
    to w without sub-steps), which weights the inflows during the step.
    """
    n_steps = state.n_steps
    source_terms = np.where(flows.tracked, np.maximum(step.term_flow, 0.0), 0.0)
    src_groups = _resolve(step, sources)
    state.source_names = _check_names(state.source_names, src_groups, step.kstpkper)
    src_flow = group_flows(step, src_groups, flows.tracked, +1)
    names = list(groups) + [ANY_SINK, STORAGE_END]
    for i, g in enumerate(names):
        _keep(state.series, g, w[:, i], index, n_steps, state.keep)
    for i, g in enumerate(groups):
        wi = w_mean[:, i]
        _keep(state.volume_from, g, delt * flows.source * wi, index, n_steps, state.keep)
        from_terms = delt * source_terms * wi[step.term_cell]
        for package, value in by_package(step, from_terms, flows.tracked).items():
            _add_series(state.by_package.setdefault(g, {}), package, index, value, n_steps)
        for k, s in enumerate(src_groups):
            value = delt * float(src_flow[:, k] @ wi)
            _add_series(state.from_group.setdefault(g, {}), s, index, value, n_steps)
        _add_series(state.outflow, g, index, delt * float(d[:, i].sum()), n_steps)
        _add_series(state.residual_term, g, index, delt * float(flows.residual @ wi), n_steps)


def _initial_records(
    state: "_BackwardState",
    step: FlowStep,
    volumes: StepVolumes,
    w: np.ndarray,
    config: TrackingConfig,
) -> None:
    """Record the initial water's share of each destination's outflow (first step)."""
    initial = initial_columns(step, config.initial_water)
    for i, g in enumerate(state.names):
        per_node = volumes.old * w[:, i]
        state.initial_from[g] = per_node
        state.initial_group[g] = {name: float(per_node @ c0) for name, c0 in initial.items()}


def _time_record(state: "_BackwardState", index: int, totim: float, delt: float) -> None:
    """Record the end time and length of a step."""
    if state.totim is None:
        state.totim = np.zeros(state.n_steps)
        state.delt = np.zeros(state.n_steps)
    state.totim[index], state.delt[index] = totim, delt


def _check_times(state: "_BackwardState", steps: list) -> None:
    """Assert that the steps join up in time from t = 0."""
    previous = 0.0
    for kstpkper, totim, delt in zip(steps, state.totim, state.delt):
        check_time(totim, delt, previous, kstpkper)
        previous = totim


# ---------------------------------------------------------------- diagnostics


def forward_balance_error(result: ForwardTracking, group: str) -> float:
    """Return max |error| of a group's tagged-water balance relative to its largest term."""
    b = result.balance[group]
    scale = max(
        max(float(np.abs(b[k]).max(initial=0.0)) for k in BALANCE_KEYS if k != "error"), 1e-300
    )
    return float(np.abs(b["error"]).max(initial=0.0)) / scale


def backward_closure(result: BackwardTracking, group: str) -> Check:
    """Return sum(volume from) + initial volume from = destination outflow over the simulation.

    Exact with the flow-error correction (residual_term 0); without it the residual term is
    sum_n dt r^n . w^n.
    """
    lhs = float(sum(v.sum() for v in result.volume_from_by_package[group].values()))
    lhs += float(result.initial_volume_from[group].sum())
    correction = result.config.flow_error_correction
    residual = 0.0 if correction else float(result.residual_term[group].sum())
    outflow = float(result.destination_outflow[group].sum())
    return Check(lhs=lhs, rhs=outflow, residual_term=residual)


def tracking_duality(
    fwd: ForwardTracking, source: str, bwd: BackwardTracking, destination: str
) -> Check:
    """Return the tagged water from source to destination, forward vs adjoint (identity (3)).

    source is a forward group (a source group or an initial_water entry); the forward run must
    report the destination as a sink group, and the backward run the source as a source group
    or initial_water entry. Check.lhs is the adjoint side, Check.rhs the forward side.
    """
    via_forward = float(fwd.outflow_to[destination][source].sum())
    if source in bwd.volume_from_group.get(destination, {}):
        via_adjoint = float(bwd.volume_from_group[destination][source].sum())
    else:
        via_adjoint = 0.0
    via_adjoint += bwd.initial_volume_from_group[destination].get(source, 0.0)
    return Check(lhs=via_adjoint, rhs=via_forward, residual_term=0.0)

