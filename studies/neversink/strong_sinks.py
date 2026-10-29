"""Neversink case study: full mixing with every sink strong, against the published MODPATH 7 area.

The published particles stop at every weak sink (MODPATH 7 weak sink option "stop"), so the
published contributing area counts only water that reaches a well without passing through
another sink cell. TraceConfig(strong_sinks="all") gives full mixing the same rule: every cell
with a sink term is absorbing and passes no water on. Gross: F = d / Snk there, the share of
the cell's sink outflow that the wells take. Net: the well cells stay at 1 and every other sink
cell absorbs with F = 0. Water then mixes only inside cells without sinks, so what remains of the
gap to the published area is the mixing inside cells, not the weak-sink rule.

Same flow field (output/optimal) and comparison as net_and_envelope.py: the start cells of the
published particles, F > 0.1 and F > 0.5, per well and for the priority group. coverage is the
share of the published cells with F > t, size the number of cells with F > t over the number of
published cells. Four cases: gross and net, each with no strong sinks (the existing results) and
with every sink strong.

outside_table splits the start cells outside the published area with F > 0.1 by the fate of
their published particle (MODPATH 7 status): 2 left the model through a face (all through the
top face of an SFR cell), 3 stopped in a weak sink (a buried SFR cell), 5 stopped in a strong
sink. Checks: boundary control (one gross group per sink package, all strong: F sums to 1 in
every cell with outflow), closure with the strong-sink term A (net_and_envelope.accounting_table
asserts it to 1e-9 of the group's flow) and the run time of each trace.

Needs TraceConfig.strong_sinks (gwsource, branch feature/strong-sinks). Run after workflow.py:

    python studies/neversink/strong_sinks.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMPORT_DIRS = (HERE, REPO / "studies" / "paper", REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import net_and_envelope as ne  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

CASES = {  # case name: (accounting, strong_sinks)
    "gross": ("gross", ()),
    "net": ("net", ()),
    "gross_strong": ("gross", "all"),
    "net_strong": ("net", "all"),
}
THRESHOLDS = (0.1, 0.5)
STATUS_LABELS = {2: "left through top face (SFR)", 3: "stopped in weak sink (buried SFR)",
                 5: "stopped in strong sink"}


def trace_cases(
    step: gs.FlowStep, groups: dict, cases: dict = CASES
) -> tuple[dict[str, gs.BackwardResult], dict[str, float]]:
    """Trace the well groups in every case; return the results and run times [s]."""
    results, seconds = {}, {}
    for case, (accounting, strong) in cases.items():
        t0 = time.perf_counter()
        config = gs.TraceConfig(accounting=accounting, strong_sinks=strong)
        results[case] = gs.backward(step, groups, config)
        seconds[case] = time.perf_counter() - t0
    return results, seconds


def coverage_table(
    results: dict[str, gs.BackwardResult],
    endpoints: pd.DataFrame,
    thresholds: tuple[float, ...] = THRESHOLDS,
    wells: dict = wf.PRIORITY_WELLS,
) -> pd.DataFrame:
    """Return, per case and group, workflow.compare_masks plus coverage and size per threshold."""
    start = endpoints["node0"].to_numpy()
    frames = []
    for case, result in results.items():
        table = wf.compare_masks(result, endpoints).assign(case=case)
        for t in thresholds:
            cov = []
            for group in table["group"]:
                nodes = list(wells.values()) if group == "priority" else [wells[group]]
                mask = wf.mp7_mask(endpoints, nodes)
                f = result.fraction_through[group][start]
                cov.append(np.sum(mask & (f > t)) / mask.sum())
            table[f"coverage_F>{t}"] = cov
            table[f"size_F>{t}"] = table[f"cells_F>{t}"] / table["mp7_cells"]
        frames.append(table)
    return pd.concat(frames, ignore_index=True)


def outside_table(
    results: dict[str, gs.BackwardResult],
    endpoints: pd.DataFrame,
    threshold: float = 0.1,
    group: str = "priority",
    labels: dict = STATUS_LABELS,
) -> pd.DataFrame:
    """Return, per case, the start cells outside the published area with F > threshold by status."""
    start = endpoints["node0"].to_numpy()
    mask = wf.mp7_mask(endpoints, list(wf.PRIORITY_WELLS.values()))
    rows = []
    for case, result in results.items():
        outside = ~mask & (result.fraction_through[group][start] > threshold)
        counts = endpoints.loc[outside, "status"].value_counts()
        assert set(counts.index) <= set(labels), f"unexpected status in {case}"
        for status, label in labels.items():
            n = int(counts.get(status, 0))
            rows.append({"case": case, "status": status, "fate": label, "cells": n,
                         "share": n / outside.sum(), "outside_cells": int(outside.sum())})
    return pd.DataFrame(rows)


def source_split(results: dict[str, gs.BackwardResult]) -> pd.DataFrame:
    """Return, per case and group, the water reaching it by source package and as shares."""
    frames = []
    for case, result in results.items():
        table = wf.source_table(result)
        packages = [c for c in table.columns if c != "group"]
        total = table[packages].sum(axis=1)
        for pkg in packages:
            table[f"share_{pkg}"] = table[pkg] / total
        frames.append(table.assign(case=case))
    return pd.concat(frames, ignore_index=True)


def boundary_control(step: gs.FlowStep, tol: float = 1e-9) -> dict:
    """Return the largest |sum F - 1| over draining cells, one gross group per sink package.

    Cells off by more than tol are counted with their largest outflow: in this model they carry
    round-off flows, where the budget residual is as large as the outflow.
    """
    sinks = step.term_flow < 0.0
    groups = {
        p.name: gs.select(step, term_mask=sinks & (step.term_package == i))
        for i, p in enumerate(step.packages)
        if np.any(sinks & (step.term_package == i))
    }
    result = gs.backward(step, groups, gs.TraceConfig(strong_sinks="all"))
    total = np.sum([result.fraction_through[g] for g in groups], axis=0)
    outflow = gs.cell_budget(step).outflow
    drains = outflow > 0.0
    off = drains & (np.abs(total - 1.0) > tol)
    return {
        "check": "boundary control, all strong",
        "groups": ", ".join(groups),
        "draining_cells": int(drains.sum()),
        "max_abs_sum_minus_1": float(np.abs(total[drains] - 1.0).max()),
        "cells_off_by_more_than_tol": int(off.sum()),
        "max_outflow_of_cells_off": float(outflow[off].max()) if off.any() else 0.0,
        "max_abs_sum_minus_1_elsewhere": float(np.abs(total[drains & ~off] - 1.0).max()),
        "max_abs_sum_non_draining": float(np.abs(total[~drains]).max()) if (~drains).any() else 0.0,
    }


def wells_table(
    step: gs.FlowStep,
    groups: dict,
    results: dict[str, gs.BackwardResult],
    seconds: dict,
    edges: gs.Edges,
    budget: gs.CellBudget,
) -> pd.DataFrame:
    """Return net_and_envelope.accounting_table of the strong cases with the strong-sink term A."""
    pair = {"gross": results["gross_strong"], "net": results["net_strong"]}
    times = {"gross": seconds["gross_strong"], "net": seconds["net_strong"]}
    table = ne.accounting_table(step, groups, pair, times, edges, budget)
    for mode, result in pair.items():
        table[f"{mode}_strong_sink_term"] = [
            gs.diagnostics.strong_sink_term(step, result, g) for g in table["group"]
        ]
    return table


def main(
    ws: Path = wf.OUT / "optimal", mp_dir: Path = wf.MP7_OUT, out: Path = wf.OUT
) -> None:
    """Trace the four cases on the model in ws and write the strong_sinks_*.csv tables to out."""
    t0 = time.perf_counter()
    step = gs.read_step(ws, boundnames=True)
    groups = wf.well_groups(step)
    results, seconds = trace_cases(step, groups)
    print(f"traced in {seconds}")
    edges = gs.flow_edges(step)
    budget = gs.cell_budget(step, edges)
    endpoints = wf.read_endpoints(mp_dir)
    coverage_table(results, endpoints).to_csv(out / "strong_sinks_mp7.csv", index=False)
    wells_table(step, groups, results, seconds, edges, budget).to_csv(
        out / "strong_sinks_wells.csv", index=False
    )
    outside_table(results, endpoints).to_csv(out / "strong_sinks_outside.csv", index=False)
    source_split(results).to_csv(out / "strong_sinks_sources.csv", index=False)
    checks = pd.DataFrame([boundary_control(step)])
    for case, s in seconds.items():
        checks[f"seconds_{case}"] = s
    checks.to_csv(out / "strong_sinks_checks.csv", index=False)
    print(f"done in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
