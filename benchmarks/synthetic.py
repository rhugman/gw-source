"""Synthetic FlowSteps on a 3D block grid for solver benchmarks (no MF6 needed).

Flows come from a random smooth head field with uniform conductance between face neighbours, so
the flow graph is acyclic (water always runs down the head gradient). Each cell's imbalance is
closed with an external term: a source ('RCH') where outflow exceeds inflow, a sink ('SNK')
where inflow exceeds outflow, so every cell balances exactly. inject_cycles() adds closed
circulations around 2 x 2 blocks of cells; circulation is divergence-free, so cells still
balance, but strong enough circulation reverses faces and creates flow cycles.
"""

import numpy as np

import gwsource as gs


def smooth_heads(shape: tuple[int, int, int], seed: int, n_modes: int = 6) -> np.ndarray:
    """Return a smooth random head field: a regional gradient plus a few long-wave modes."""
    rng = np.random.default_rng(seed)
    nlay, nrow, ncol = shape
    z, y, x = np.meshgrid(
        np.linspace(0, 1, nlay), np.linspace(0, 1, nrow), np.linspace(0, 1, ncol), indexing="ij"
    )
    heads = 10.0 * (1.0 - x) + 0.5 * z
    for _ in range(n_modes):
        kx, ky, kz = rng.uniform(0.5, 3.0, size=3)
        phase = rng.uniform(0, 2 * np.pi, size=3)
        heads += rng.uniform(0.2, 1.0) * (
            np.sin(np.pi * kx * x + phase[0])
            * np.sin(np.pi * ky * y + phase[1])
            * np.cos(np.pi * kz * z + phase[2])
        )
    heads += 1e-9 * rng.standard_normal(shape)  # break exact ties so no face has zero flow
    return heads


def face_pairs(shape: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Return (a, b) node pairs of every face between neighbouring cells of a block grid."""
    nodes = np.arange(np.prod(shape)).reshape(shape)
    a = [nodes[1:, :, :].ravel(), nodes[:, 1:, :].ravel(), nodes[:, :, 1:].ravel()]
    b = [nodes[:-1, :, :].ravel(), nodes[:, :-1, :].ravel(), nodes[:, :, :-1].ravel()]
    return np.concatenate(a), np.concatenate(b)


def step_from_face_flows(
    shape: tuple[int, int, int], a: np.ndarray, b: np.ndarray, flow_ab: np.ndarray
) -> gs.FlowStep:
    """Build a balanced FlowStep from signed face flows a->b, closing each cell with a term."""
    n = int(np.prod(shape))
    src = np.where(flow_ab > 0, a, b)
    dst = np.where(flow_ab > 0, b, a)
    q = np.abs(flow_ab)
    keep = q > 0
    src, dst, q = src[keep], dst[keep], q[keep]
    net_out = np.bincount(src, weights=q, minlength=n) - np.bincount(dst, weights=q, minlength=n)
    term_flow = net_out  # positive (source) where the cell exports more than it receives
    has_term = term_flow != 0.0
    cells = np.flatnonzero(has_term)
    package = np.where(term_flow[cells] > 0, 0, 1)
    packages = [gs.Package("RCH", "RCH"), gs.Package("SNK", "SNK")]
    return gs.from_edges(
        n,
        src,
        dst,
        q,
        cells,
        term_flow[cells],
        package,
        packages=packages,
        grid_shape=shape,
        grid_type="DIS",
        area=np.ones(n),
    )


def smooth_step(shape: tuple[int, int, int], seed: int = 1) -> gs.FlowStep:
    """Return an acyclic, balanced FlowStep from a smooth random head field on a block grid."""
    heads = smooth_heads(shape, seed).ravel()
    a, b = face_pairs(shape)
    return step_from_face_flows(shape, a, b, heads[a] - heads[b])


def inject_cycles(
    shape: tuple[int, int, int], n_cycles: int, strength: float, seed: int = 1
) -> gs.FlowStep:
    """Return smooth_step flows plus n_cycles circulations around random 2 x 2 row-column blocks."""
    nlay, nrow, ncol = shape
    heads = smooth_heads(shape, seed).ravel()
    a, b = face_pairs(shape)
    flow = heads[a] - heads[b]
    face_index = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(a, b))}
    rng = np.random.default_rng(seed + 1)
    nodes = np.arange(np.prod(shape)).reshape(shape)
    scale = np.median(np.abs(flow))
    for _ in range(n_cycles):
        k, i, j = rng.integers(0, nlay), rng.integers(0, nrow - 1), rng.integers(0, ncol - 1)
        ring = [nodes[k, i, j], nodes[k, i, j + 1], nodes[k, i + 1, j + 1], nodes[k, i + 1, j]]
        for u, v in zip(ring, ring[1:] + ring[:1]):
            c = strength * scale
            key = (int(u), int(v))
            if key in face_index:
                flow[face_index[key]] += c
            else:
                flow[face_index[(int(v), int(u))]] -= c
    return step_from_face_flows(shape, a, b, flow)


def sink_groups(step: gs.FlowStep, n_groups: int, seed: int = 1) -> dict[str, gs.Selection]:
    """Return n_groups destination groups, each a random subset of the sink terms."""
    rng = np.random.default_rng(seed)
    sinks = np.flatnonzero(step.term_flow < 0)
    label = rng.integers(0, n_groups, size=sinks.size)
    groups = {}
    for g in range(n_groups):
        mask = np.zeros(step.n_terms, dtype=bool)
        mask[sinks[label == g]] = True
        groups[f"g{g}"] = gs.select(step, term_mask=mask)
    return groups
