"""Solver benchmark on synthetic FlowSteps (no MF6): time per stage and peak memory.

Each case runs in its own subprocess so the peak resident memory (ru_maxrss) is per case.
Stages: build the synthetic step (not counted), assemble (edges, cell budget, matrix and
right-hand sides), strongly connected components of the dependency graph (shared by the next
two stages), closed-loop check, solve (topological, block or COLAMD LU; includes ordering and
permutation) and metrics (the full backward() outputs). solve_s for "lu" does not use the
components. Run from the repository root:

    python benchmarks/bench_solver.py            # default table
    python benchmarks/bench_solver.py --quick    # small sizes only
"""

import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SHAPES = {
    "50k": (20, 50, 50),
    "100k": (10, 100, 100),
    "250k": (25, 100, 100),
    "1M": (100, 100, 100),
}
DEFAULT_CASES = [  # (size, cycles per 1000 cells, solver, groups)
    ("50k", 0, "lu", 4),
    ("50k", 0, "topological", 4),
    ("50k", 0, "block", 4),
    ("50k", 10, "lu", 4),
    ("50k", 10, "block", 4),
    ("100k", 0, "lu", 4),
    ("250k", 0, "topological", 4),
    ("250k", 0, "block", 4),
    ("250k", 10, "block", 4),
    ("1M", 0, "topological", 4),
    ("1M", 0, "block", 4),
    ("1M", 10, "block", 4),
    ("1M", 0, "topological", 1),
    ("1M", 0, "topological", 10),
    ("1M", 0, "topological", 50),
]
QUICK_CASES = [("50k", 0, "topological", 4), ("50k", 10, "block", 4), ("50k", 10, "lu", 4)]


def peak_rss_mb() -> float:
    """Return this process's peak resident memory in MB (ru_maxrss: bytes on macOS, KB on Linux)."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / 2**20 if sys.platform == "darwin" else rss / 2**10


def run_case(size: str, cycles_per_1000: int, solver: str, n_groups: int) -> dict:
    """Build, assemble, solve and post-process one case; return stage times and memory."""
    sys.path.insert(0, str(HERE))
    from synthetic import inject_cycles, sink_groups, smooth_step

    from gwsource.assemble import (
        cell_budget,
        flow_edges,
        gross_backward_system,
        group_term_flows,
    )
    from gwsource.metrics import backward_metrics, per_cell_by_package
    from gwsource.solve import dependency_graph, find_cycles, isolate_closed_loops, solve_system

    shape = SHAPES[size]
    n = int(np.prod(shape))
    n_cycles = n * cycles_per_1000 // 1000
    step = inject_cycles(shape, n_cycles, 3.0) if n_cycles else smooth_step(shape)
    groups = sink_groups(step, n_groups)
    base_mb = peak_rss_mb()
    t0 = time.perf_counter()
    edges = flow_edges(step)
    budget = cell_budget(step, edges)
    matrix, rhs = gross_backward_system(step, edges, budget, groups)
    t1 = time.perf_counter()
    graph = dependency_graph(matrix)
    t_graph = time.perf_counter()
    matrix, rhs, loops = isolate_closed_loops(matrix, rhs, graph=graph)
    t2 = time.perf_counter()
    fraction, used = solve_system(matrix, rhs, solver, None if loops else graph)
    t3 = time.perf_counter()
    destination = group_term_flows(step, groups, sign=-1).sum(axis=0)
    by_package = per_cell_by_package(step, sign=+1)
    backward_metrics(
        step, groups, fraction, budget.outflow, budget.source, by_package, destination, "gross"
    )
    t4 = time.perf_counter()
    cycles = find_cycles(n, edges)
    t5 = time.perf_counter()
    residual = float(np.abs(matrix @ fraction - rhs).max())
    return {
        "size": size,
        "cells": n,
        "edges": int(len(edges.q)),
        "cyclic_sets": len(cycles),
        "largest_set": max((c.n_cells for c in cycles), default=1),
        "solver": used,
        "groups": n_groups,
        "assemble_s": round(t1 - t0, 3),
        "components_s": round(t_graph - t1, 3),
        "closed_check_s": round(t2 - t_graph, 3),
        "solve_s": round(t3 - t2, 3),
        "metrics_s": round(t4 - t3, 3),
        "cycle_scan_s": round(t5 - t4, 3),
        "max_residual": residual,
        "base_mb": round(base_mb),
        "peak_mb": round(peak_rss_mb()),
    }


def run_in_subprocess(case: tuple) -> dict:
    """Run one case in a fresh Python process and return its result dict."""
    code = f"import sys; sys.path.insert(0, {str(HERE)!r}); import bench_solver as b; " \
        f"import json; print(json.dumps(b.run_case(*{case!r})))"  # fmt: skip
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def main(cases: list[tuple]) -> list[dict]:
    """Run every case and print a table."""
    columns = (
        "size", "cells", "cyclic_sets", "largest_set", "solver", "groups", "assemble_s",
        "components_s", "closed_check_s", "solve_s", "metrics_s", "base_mb", "peak_mb",
        "max_residual",
    )  # fmt: skip
    print("\t".join(columns))
    results = []
    for case in cases:
        result = run_in_subprocess(case)
        results.append(result)
        print("\t".join(str(result[c]) for c in columns), flush=True)
    return results


if __name__ == "__main__":
    main(QUICK_CASES if "--quick" in sys.argv else DEFAULT_CASES)
