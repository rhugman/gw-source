"""Experimental face-to-face routing (Chowdhury 2016) within DIS cells.

Checks: the single-cell partition against Chowdhury's (2016) closed-form case formulas and
against per-particle Pollock (1988) exit times; mass balance of the partition; Chowdhury's
planar 3x3 example (his Figure 4.6 values: A and I drop to 0, B, D, F and H are 0.5, C, E
and G are 1); zero lateral spreading of a diagonal uniform flow; agreement with full mixing
where every cell has a single outflow face or routing is switched off; closure, boundary
control and bounds on MF6 test model 1.
"""

import numpy as np
import pytest

import gwsource as gs
from gwsource.experimental import face_routing as fr
from gwsource.flowstep import Package, from_edges

CHOWDHURY_ORDER = (0, 3, 1, 2)  # clockwise from the left face: x1, y2, x2, y1 (face indices)


# ---------------------------------------------------------------- single cell


def balanced_lateral_flows(rng: np.random.Generator, top_inflow: float = 0.0) -> np.ndarray:
    """Return random (6,) net face outflows that balance, with optional top inflow (face 5)."""
    net = np.zeros(6)
    net[:3] = rng.uniform(-1.0, 1.0, 3)
    net[5] = -top_inflow
    net[3] = -net[:3].sum() - net[5]
    return net


def axis_exit(v1: float, v2: float, length: float, s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (exit time, side 0/1) along one axis from positions s in [0, 1] (Pollock 1988)."""
    v = v1 + (v2 - v1) * s
    gradient = (v2 - v1) / length
    t = np.full(s.shape, np.inf)
    side = np.where(v > 0.0, 1, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        if abs(gradient) > 1e-14:
            t_hi = np.log(v2 / v) / gradient
            t_lo = np.log(v1 / v) / gradient
        else:
            t_hi = length * (1.0 - s) / v
            t_lo = length * s / -v
    t = np.where((v > 0.0) & (v2 > 0.0), t_hi, t)
    t = np.where((v < 0.0) & (v1 < 0.0), t_lo, t)
    return t, side


def particle_plan(net: np.ndarray, dx: float, dy: float, n: int = 200_000) -> np.ndarray:
    """Return W estimated from particles spread uniformly over each inflow face."""
    rng = np.random.default_rng(1)
    vel = ((-net[0] / dy, net[1] / dy), (-net[2] / dx, net[3] / dx))
    length = (dx, dy)
    plan = np.zeros((6, 6))
    for face in np.flatnonzero(net < 0.0):
        start = [rng.uniform(0.0, 1.0, n), rng.uniform(0.0, 1.0, n)]
        if face < 4:
            axis = face // 2
            start[axis] = np.full(n, float(face % 2))
        times, sides = zip(*(axis_exit(*vel[a], length[a], start[a]) for a in (0, 1)))
        first = np.argmin(np.column_stack(times), axis=1)
        exit_face = 2 * first + np.choose(first, sides)
        plan[face] = np.bincount(exit_face, minlength=6) / n
    return plan


def chowdhury_plan(net: np.ndarray) -> np.ndarray | None:
    """Return Q[i, j] from Chowdhury's (2016) 2-inflow/2-outflow formulas, or None if not that case.

    Type 1 (opposite inflows): stagnation-point split, eqs. 3.26-3.29 and 3.36-3.39.
    Type 2 (adjacent inflows): reference-inflow rule, eqs. 3.59-3.66.
    """
    q = np.abs(net[:4])
    inflow = net[:4] < 0.0
    if inflow.sum() != 2:
        return None
    flows = np.zeros((6, 6))
    if inflow[0] == inflow[1]:  # opposite inflows
        ins, outs = np.flatnonzero(inflow), np.flatnonzero(~inflow)
        split = q[outs[0]] / (q[outs[0]] + q[outs[1]])
        for i in ins:
            flows[i, outs[0]], flows[i, outs[1]] = split * q[i], (1.0 - split) * q[i]
        return flows
    order = list(CHOWDHURY_ORDER)
    pos = [k for k in range(4) if inflow[order[k]] and inflow[order[(k + 1) % 4]]][0]
    r, r1, r2, r3 = (order[(pos + k) % 4] for k in range(4))
    if q[r] >= q[r3]:
        flows[r, r2], flows[r, r3], flows[r1, r2] = q[r] - q[r3], q[r3], q[r1]
    else:
        flows[r, r3], flows[r1, r2], flows[r1, r3] = q[r], q[r2], q[r1] - q[r2]
    return flows


def test_plan_matches_chowdhury_formulas():
    """Divergence-free 2-in/2-out cells: Pollock exit times give Chowdhury's closed forms."""
    rng = np.random.default_rng(16)
    checked = 0
    for _ in range(400):
        net = balanced_lateral_flows(rng)
        expected = chowdhury_plan(net)
        if expected is None:
            continue
        dx, dy = rng.uniform(5.0, 200.0, 2)
        plan = fr.cell_plan(net, dx, dy)
        flows = np.maximum(-net, 0.0)[:, None] * plan
        np.testing.assert_allclose(flows, expected, atol=1e-12 * np.abs(net).max())
        checked += 1
    assert checked > 100


@pytest.mark.parametrize("top", [0.0, 0.6])
def test_plan_mass_balance_and_rows(top):
    """Rows sum to 1 and the routed inflows rebuild every outflow face (balanced cells)."""
    rng = np.random.default_rng(7)
    for _ in range(300):
        net = balanced_lateral_flows(rng, top)
        if not (net > 0.0).any():
            continue
        dx, dy = rng.uniform(5.0, 200.0, 2)
        plan = fr.cell_plan(net, dx, dy)
        inflow = net < 0.0
        np.testing.assert_allclose(plan[inflow].sum(axis=1), 1.0, rtol=0, atol=1e-13)
        assert np.all(plan[~inflow] == 0.0) and np.all(plan >= 0.0)
        rebuilt = np.maximum(-net, 0.0) @ plan
        np.testing.assert_allclose(rebuilt, np.maximum(net, 0.0), atol=1e-12)


def mixing_plan(net: np.ndarray) -> np.ndarray:
    """Return the full-mixing W: every inflow face split over the outflow faces by their flow."""
    out = np.maximum(net, 0.0)
    return np.where((net < 0.0)[:, None], out / out.sum(), 0.0)


@pytest.mark.parametrize("seed", [3, 4, 5, 6])
@pytest.mark.parametrize("top", [0.0, 0.8])
def test_plan_matches_particles(seed, top):
    """W agrees with per-particle Pollock exit times (200k particles per face: error ~ 0.003).

    Cells are drawn until full mixing differs from W by more than 0.05, so the check can tell
    the two apart.
    """
    rng = np.random.default_rng(seed)
    while True:
        net = balanced_lateral_flows(rng, top)
        dx, dy = rng.uniform(10.0, 100.0, 2)
        plan = fr.cell_plan(net, dx, dy)
        if np.abs(plan - mixing_plan(net)).max() > 0.05:
            break
    particles = particle_plan(net, dx, dy)
    np.testing.assert_allclose(plan, particles, atol=0.006)
    assert np.abs(mixing_plan(net) - particles).max() > 0.04


def test_uniform_cell_is_straight_through():
    """Uniform flow along x: all water entering x1 leaves through x2, none sideways."""
    plan = fr.cell_plan(np.array([-2.0, 2.0, 0.0, 0.0, 0.0, 0.0]), 10.0, 10.0)
    assert plan[0, 1] == 1.0 and plan[0].sum() == 1.0


# ---------------------------------------------------------------- hand-built grids


def grid_step(
    nrow: int, ncol: int, edges: list, terms: list, packages: list[Package]
) -> gs.FlowStep:
    """Return a 1-layer DIS FlowStep from edges (src, dst, q) and terms (cell, q, package)."""
    src, dst, q = (np.array(v) for v in zip(*edges))
    cell, flow, pkg = (np.array(v) for v in zip(*terms))
    return from_edges(
        nrow * ncol, src, dst, q, cell, flow, pkg, packages,
        grid_shape=(1, nrow, ncol), grid_type="DIS",
    )


BOUNDARY = [Package("EAST", "CHD"), Package("NORTH", "CHD"), Package("WEST", "CHD"),
            Package("SOUTH", "CHD")]
BOUNDARY_IFACE = {"EAST": 2, "NORTH": 4, "WEST": 1, "SOUTH": 3}


def diagonal_flow(n: int, qx: float = 2.0, qy: float = 2.0) -> gs.FlowStep:
    """Return uniform flow to the south-west on an n x n grid, boundary flows on the faces."""
    node = lambda i, j: i * n + j  # noqa: E731
    edges, terms = [], []
    for i in range(n):
        for j in range(n):
            if j > 0:
                edges.append((node(i, j), node(i, j - 1), qx))
            if i < n - 1:
                edges.append((node(i, j), node(i + 1, j), qy))
    terms += [(node(i, n - 1), qx, 0) for i in range(n)]
    terms += [(node(0, j), qy, 1) for j in range(n)]
    terms += [(node(i, 0), -qx, 2) for i in range(n)]
    terms += [(node(n - 1, j), -qy, 3) for j in range(n)]
    return grid_step(n, n, edges, terms, BOUNDARY)


def test_chowdhury_planar_3x3():
    """Chowdhury (2016) §4.1.2: peripheral cells A and I drop from > 0 (full mixing) to 0."""
    step = diagonal_flow(3)
    dest = {"G": gs.select(step, cells=[6])}
    config = fr.FaceRoutingConfig(iface=BOUNDARY_IFACE)
    routed = fr.route_backward(step, dest, np.ones(3), np.ones(3), config)
    expected = np.array([[0.0, 0.5, 1.0], [0.5, 1.0, 0.5], [1.0, 0.5, 0.0]])
    np.testing.assert_allclose(routed.fraction_through["G"].reshape(3, 3), expected, atol=1e-12)
    assert routed.routed.all()
    mixed = gs.backward(step, dest).fraction_through["G"].reshape(3, 3)
    assert mixed[0, 0] > 0.2 and mixed[2, 2] > 0.2  # A and I under full mixing
    check = fr.closure(routed, "G")
    assert abs(check.error) < 1e-12 and check.lhs == pytest.approx(4.0)


def test_diagonal_flow_has_no_lateral_spreading():
    """45-degree uniform flow: the water of one outflow face comes from one inflow face only."""
    n = 12
    step = diagonal_flow(n)
    west = np.flatnonzero(step.term_package == 2)
    dest = {"one_face": gs.select(step, term_mask=np.isin(np.arange(step.n_terms), west[5]))}
    config = fr.FaceRoutingConfig(iface=BOUNDARY_IFACE)
    routed = fr.route_backward(step, dest, np.ones(n), np.ones(n), config)
    faces = routed.face_fraction["one_face"]
    assert np.all((np.abs(faces) < 1e-12) | (np.abs(faces - 1.0) < 1e-12))
    sources = routed.term_fraction["one_face"][step.term_flow > 0.0]
    assert np.sum(sources > 0.5) == 1 and np.all((sources < 1e-12) | (sources > 1 - 1e-12))
    mixed = gs.backward(step, dest).fraction_through["one_face"]
    assert np.sum(mixed > 1e-6) > 2 * np.sum(routed.fraction_through["one_face"] > 1e-6)


def tree_flow(n: int, seed: int = 3) -> gs.FlowStep:
    """Return a drainage-tree flow: recharge on every cell, one outflow face per cell, a well.

    Each cell drains west or south (west edge and south edge drain through boundary sinks); the
    well (internal sink) takes part of one cell's outflow, so that cell is a mixed weak sink.
    """
    rng = np.random.default_rng(seed)
    node = lambda i, j: i * n + j  # noqa: E731
    down = {}
    for i in range(n):
        for j in range(n):
            west = j > 0 and (i == n - 1 or rng.random() < 0.5)
            down[node(i, j)] = node(i, j - 1) if west else (node(i + 1, j) if i < n - 1 else None)
    total = {c: 1.0 for c in down}
    well_cell, well_rate = node(n // 2, n // 2), 0.5
    order = sorted(down, key=lambda c: (c // n, -(c % n)))  # north to south, east to west
    edges, terms = [], [(c, 1.0, 0) for c in down]
    for c in order:
        out = total[c] - (well_rate if c == well_cell else 0.0)
        if down[c] is None:
            terms.append((c, -out, 1 if c % n == 0 else 2))
        else:
            edges.append((c, down[c], out))
            total[down[c]] += out
    terms.append((well_cell, -well_rate, 3))
    packages = [Package("RCH", "RCH"), Package("WEST", "CHD"), Package("SOUTH", "CHD"),
                Package("WEL", "WEL")]
    return grid_step(n, n, edges, terms, packages)


def test_single_outflow_face_matches_full_mixing():
    """Every cell has one outflow face: routing and full mixing give the same fractions."""
    n = 9
    step = tree_flow(n)
    groups = gs.groups_by_package(step)
    config = fr.FaceRoutingConfig(iface={"RCH": 6, "WEST": 1, "SOUTH": 3})
    routed = fr.route_backward(step, groups, np.ones(n), np.ones(n), config)
    mixed = gs.backward(step, groups)
    assert routed.routed.sum() > n * n - 5
    for g in groups:
        np.testing.assert_allclose(
            routed.fraction_through[g], mixed.fraction_through[g], rtol=0, atol=1e-12
        )
        np.testing.assert_allclose(routed.volume_from[g], mixed.volume_from[g], atol=1e-12)
        assert abs(fr.closure(routed, g).error) < 1e-12


# ---------------------------------------------------------------- MF6 model 1


@pytest.fixture(scope="module")
def model1(model_run):
    """Model 1 step, its DIS spacing and the well group."""
    run = model_run("m1_dis")
    step = gs.read_step(run.ws)
    delr, delc = fr.read_dis_spacing(run.grb_file)
    return step, delr, delc


def test_model1_routing_off_reproduces_full_mixing(model1):
    """route=False builds the face graph with every cell mixed: same as gwsource.backward."""
    step, delr, delc = model1
    groups = gs.groups_by_package(step)
    config = fr.FaceRoutingConfig(route=False)
    routed = fr.route_backward(step, groups, delr, delc, config)
    mixed = gs.backward(step, groups)
    for g in groups:
        np.testing.assert_allclose(
            routed.fraction_through[g], mixed.fraction_through[g], rtol=0, atol=1e-10
        )


def test_model1_closure_bounds_and_boundary_control(model1):
    """Closure to round-off, 0 <= F <= 1, fractions to every sink package sum to 1."""
    step, delr, delc = model1
    groups = gs.groups_by_package(step)
    routed = fr.route_backward(step, groups, delr, delc)
    sinks = [g for g in groups if routed.destination_inflow[g] > 0.0]
    assert {"WEL", "CHD", "RIV"} <= {g.upper() for g in sinks}
    total = sum(routed.fraction_through[g] for g in sinks)
    outflow = gs.assemble.cell_budget(step, gs.assemble.flow_edges(step)).outflow
    np.testing.assert_allclose(total[outflow > 0], 1.0, atol=1e-10)
    for g in sinks:
        f = routed.fraction_through[g]
        assert f.min() >= -1e-12 and f.max() <= 1.0 + 1e-12
        check = fr.closure(routed, g)
        assert check.relative_error < 1e-10, (g, check)
    n_mixed = int((~routed.routed & step.active).sum())
    assert 0 < n_mixed < 0.15 * step.active.sum()  # river, CHD, well and divide cells


def test_model1_capture_zone_is_narrower(model1):
    """The well's capture zone (F > 0.01) shrinks under routing; its water total is unchanged."""
    step, delr, delc = model1
    groups = {"wel": gs.select(step, package="WEL")}
    routed = fr.route_backward(step, groups, delr, delc)
    mixed = gs.backward(step, groups)
    area_routed = step.area[routed.fraction_through["wel"] > 0.01].sum()
    area_mixed = step.area[mixed.fraction_through["wel"] > 0.01].sum()
    assert area_routed < area_mixed
    assert routed.volume_from["wel"].sum() == pytest.approx(800.0, rel=1e-6)


def test_three_layer_model_routes_only_cells_with_one_vertical_inflow(model_run):
    """Model 2: layers 1-2 have vertical outflow (mixed); most bottom-layer cells are routed."""
    run = model_run("m2_dis3lay")
    step = gs.read_step(run.ws)
    delr, delc = fr.read_dis_spacing(run.grb_file)
    groups = {"wel": gs.select(step, package="WEL")}
    routed = fr.route_backward(step, groups, delr, delc)
    by_layer = routed.routed.reshape(3, -1).mean(axis=1)
    assert by_layer[0] == 0.0 and by_layer[1] == 0.0 and by_layer[2] > 0.8
    assert fr.closure(routed, "wel").relative_error < 1e-10
