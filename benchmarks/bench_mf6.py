"""End-to-end benchmark on a large MF6 model: I/O vs assembly vs solve per time step.

Builds (once) a confined 4-layer DIS model of 4 x 250 x 250 = 250,000 cells with heterogeneous
K, constant heads on two sides, areal recharge, a river line, drains and 40 wells, a steady
first stress period and two transient periods of two steps (5 saved steps). Then times:
- opening the files (binary grid read once, budget file index);
- per step: reading the step (I/O), assembly, closed-loop check, solve and metrics, for one
  group per package and for one group per well (40 right-hand sides);
- the whole transient loop with streaming statistics.
Run from the repository root (the model is written to benchmarks/large_ws, git-ignored):

    python benchmarks/bench_mf6.py
"""

import resource
import sys
import time
from pathlib import Path

import flopy
import numpy as np

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges, gross_backward_system
from gwsource.solve import find_cycles, isolate_closed_loops, solve_system

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SHAPE = (4, 250, 250)
CELL = 40.0
N_WELLS = 40


def peak_rss_mb() -> float:
    """Return this process's peak resident memory in MB."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / 2**20 if sys.platform == "darwin" else rss / 2**10


def k_field(shape: tuple[int, int, int], seed: int = 5) -> np.ndarray:
    """Return a smooth lognormal hydraulic conductivity field."""
    rng = np.random.default_rng(seed)
    nlay, nrow, ncol = shape
    y, x = np.meshgrid(np.linspace(0, 1, nrow), np.linspace(0, 1, ncol), indexing="ij")
    logk = np.zeros((nrow, ncol))
    for _ in range(12):
        kx, ky = rng.uniform(1.0, 8.0, size=2)
        logk += rng.normal(0, 0.3) * np.sin(np.pi * kx * x + rng.uniform(0, 6)) * np.cos(
            np.pi * ky * y + rng.uniform(0, 6)
        )
    layer_factor = np.array([5.0, 1.0, 10.0, 3.0])[:nlay, None, None]
    return layer_factor * np.exp(logk)[None]


def build_model(ws: Path, exe: Path) -> Path:
    """Write and run the benchmark model; return its workspace."""
    nlay, nrow, ncol = SHAPE
    name = "bench"
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    perioddata = [(1.0, 1, 1.0), (180.0, 2, 1.0), (180.0, 2, 1.0)]
    flopy.mf6.ModflowTdis(sim, nper=3, perioddata=perioddata, time_units="days")
    flopy.mf6.ModflowIms(
        sim, complexity="simple", outer_dvclose=1e-6, inner_dvclose=1e-8, rcloserecord=1e-3,
        inner_maximum=500, linear_acceleration="bicgstab",
    )  # fmt: skip
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    botm = [-20.0, -40.0, -80.0, -120.0][:nlay]
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=CELL, delc=CELL, top=0.0, botm=botm,
        length_units="meters",
    )  # fmt: skip
    k = k_field(SHAPE)
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=k, k33=0.1 * k, save_flows=True)
    flopy.mf6.ModflowGwfic(gwf, strt=5.0)
    flopy.mf6.ModflowGwfsto(
        gwf, iconvert=0, ss=1e-5, sy=0.1, steady_state={0: True}, transient={1: True},
        save_flows=True,
    )  # fmt: skip
    chd = [((lay, row, 0), 0.0) for lay in range(nlay) for row in range(nrow)]
    chd += [((lay, 0, col), 12.0) for lay in range(nlay) for col in range(1, ncol)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True)
    rch = {0: 5e-4, 1: 2e-4, 2: 8e-4}
    flopy.mf6.ModflowGwfrcha(gwf, recharge=rch, save_flows=True)
    riv_col = ncol // 2
    riv = [((0, row, riv_col), 6.0 - 4.0 * row / nrow, 2000.0, 0.0) for row in range(nrow)]
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data={0: riv}, save_flows=True)
    drn = [((0, row, col), 4.0, 500.0) for row in range(150, 200) for col in range(30, 40)]
    flopy.mf6.ModflowGwfdrn(gwf, stress_period_data={0: drn}, save_flows=True)
    rng = np.random.default_rng(11)
    cells = rng.choice(nrow * ncol, size=N_WELLS, replace=False)
    wel = {
        kper: [((2, int(c) // ncol, int(c) % ncol), -rate) for c in cells]
        for kper, rate in enumerate([800.0, 1500.0, 500.0])
    }
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel, save_flows=True)
    flopy.mf6.ModflowGwfoc(
        gwf, budget_filerecord=f"{name}.cbc", head_filerecord=f"{name}.hds",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )  # fmt: skip
    sim.write_simulation(silent=True)
    t0 = time.perf_counter()
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "\n".join(buff[-20:])
    print(f"MF6 run: {time.perf_counter() - t0:.1f} s", flush=True)
    return ws


def time_step(reader: gs.StepReader, kstpkper: tuple[int, int], per_well: bool) -> dict:
    """Return stage times of one step for package groups or one group per well."""
    t0 = time.perf_counter()
    step = reader.read(kstpkper)
    t1 = time.perf_counter()
    if per_well:
        groups = gs.groups_by_term(step, gs.select(step, package="WEL").terms)
    else:
        groups = gs.groups_by_package(step)
    edges = flow_edges(step)
    budget = cell_budget(step, edges)
    matrix, rhs = gross_backward_system(step, edges, budget, groups)
    t2 = time.perf_counter()
    matrix, rhs, _ = isolate_closed_loops(matrix, rhs)
    t3 = time.perf_counter()
    _, solver = solve_system(matrix, rhs)
    t4 = time.perf_counter()
    gs.backward(step, groups)  # full trace incl. metrics, for its total time
    t5 = time.perf_counter()
    find_cycles(step.n_cells, edges)
    t6 = time.perf_counter()
    return {
        "step": kstpkper,
        "groups": len(groups),
        "solver": solver,
        "read_s": t1 - t0,
        "assemble_s": t2 - t1,
        "closed_check_s": t3 - t2,
        "solve_s": t4 - t3,
        "backward_total_s": t5 - t4,
        "cycle_scan_s": t6 - t5,
    }


def main(ws: Path = HERE / "large_ws", rebuild: bool = False) -> None:
    """Build the model if needed, then print per-stage timings and peak memory."""
    exe = REPO / "bin" / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    if rebuild or not (ws / "bench.cbc").is_file():
        ws.mkdir(parents=True, exist_ok=True)
        build_model(ws, exe)
    t0 = time.perf_counter()
    reader = gs.open_model(ws)
    print(f"open files (grid + budget index): {time.perf_counter() - t0:.2f} s; "
          f"{reader.grid.ia.size - 1} cells, {reader.grid.ja.size} connections")  # fmt: skip
    for per_well in (False, True):
        for kstpkper in reader.steps:
            row = time_step(reader, kstpkper, per_well)
            print({k: round(v, 3) if isinstance(v, float) else v for k, v in row.items()})
    t0 = time.perf_counter()
    config = gs.TransientConfig(threshold=0.1, value_range=(0.1, 1.0))
    groups = {"wel": {"package": "WEL"}, "riv": {"package": "RIV"}}
    res = gs.trace_transient(reader, groups, config=config)
    print(f"transient loop, {len(res.steps)} steps, 2 groups: {time.perf_counter() - t0:.2f} s")
    print(f"peak memory: {peak_rss_mb():.0f} MB")


if __name__ == "__main__":
    main(rebuild="--rebuild" in sys.argv)
