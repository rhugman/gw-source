"""Neversink case study: gross against net accounting, and F thresholds against a particle zone.

Two checks on the calibrated model (streams as cells, the eight priority wells), both on the
flow field of workflow.py (output/optimal) and without new MF6 or PRT runs.

Net against gross. Net accounting (the reference method [FB13]; PLAN §2.4) uses only the
intercell flows: s_i = O^edges_i - I^edges_i, throughflow T_i = I^edges_i + max(s_i, 0), the
destination cells absorb (f = 1) and elsewhere f_i = sum_j q_ij f_j / T_i. The water attributed
to a group is the throughflow of its cells (destination_inflow), against the wells' own pumping
under gross accounting. F differs between the modes only in the destination cells and in cells
with both source and sink terms (O_gross = I^edges + sources there, T = max(I^edges, O^edges));
elsewhere the row equations are the same and the difference is inherited from downstream.

Net closure. Summing f_i T_i = sum_j q_ij f_j over the non-destination cells gives, with D the
destination cells and s+ = max(s, 0),

    sum_i f_i s+_i = sum_{d in D} T_d - sum_{D->D} q - sum_{D->not D} q_ij f_j

The left side is the net volume from (volume_from); the two subtracted terms are water that
passes from one destination cell to another (counted in both throughflows) and water that leaves
a destination cell and reaches another destination cell further on. Net mode uses edges only,
so there is no budget-residual term.

Envelope. docs/dispersion_study.md found that F >= 0.1 contained the non-stopping particle
reference zone in every synthetic run. Here the reference is the thinned flux-weighted PRT run
released over the cell volume (output/prt_volume_thin1; NS Table 3): P is the flow-weighted share
of the water released in a cell that reaches the priority wells. Both are evaluated on the start
cells of the published particles (uppermost active layer), as in workflow.compare_masks.

Run with the project environment after workflow.py (it needs output/optimal and the PRT run):

    python studies/neversink/net_and_envelope.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

PRT_RUN = "prt_volume_thin1"
F_THRESHOLDS = (0.1, 0.5)
P_ZONES = (0.1, 0.5)
# Published release regions: NE holds the U cluster (U_917, U__55, U___7, U___8), S the southern
# SV well (SV_487), W the north SV wells (SV_193, SV_227, SV_407), by the published end cells.
REGIONS = ("all", *wf.MP7_REGIONS)


# ---------------------------------------------------------------- net against gross


def trace_both(ws: Path) -> tuple[gs.FlowStep, dict, dict[str, gs.BackwardResult], dict]:
    """Read the step and trace the well groups with gross and net accounting; return run times."""
    step = gs.read_step(ws, boundnames=True)
    groups = wf.well_groups(step)
    results, seconds = {}, {}
    for mode in ("gross", "net"):
        t0 = time.perf_counter()
        results[mode] = gs.backward(step, groups, gs.TraceConfig(accounting=mode))
        seconds[mode] = time.perf_counter() - t0
    return step, groups, results, seconds


def net_closure(edges: gs.Edges, dest: np.ndarray, f: np.ndarray, throughflow: float) -> dict:
    """Return the terms of the net closure identity (module docstring) for one group."""
    from_dest, to_dest = dest[edges.src], dest[edges.dst]
    dest_to_dest = float(edges.q[from_dest & to_dest].sum())
    dest_onward = float(np.sum(edges.q[from_dest & ~to_dest] * f[edges.dst[from_dest & ~to_dest]]))
    return {
        "dest_to_dest_flow": dest_to_dest,
        "dest_onward_to_dest": dest_onward,
        "net_closure_rhs": throughflow - dest_to_dest - dest_onward,
    }


def well_cell_budget(step: gs.FlowStep, sel: gs.Selection, budget: gs.CellBudget) -> dict:
    """Return the summed budget of a group's cells and the share of their outflow the wells take."""
    cells = sel.cells
    pumping = float(-step.term_flow[sel.terms].sum())
    outflow = float(budget.outflow[cells].sum())
    return {
        "well_cells": int(cells.sum()),
        "pumping": pumping,
        "cell_face_inflow": float(budget.edge_in[cells].sum()),
        "cell_source_terms": float(budget.source[cells].sum()),
        "cell_face_outflow": float(budget.edge_out[cells].sum()),
        "cell_other_sinks": float(budget.sink[cells].sum()) - pumping,
        "cell_outflow": outflow,
        "well_share_of_outflow": pumping / outflow,
    }


def accounting_table(
    step: gs.FlowStep, groups: dict, results: dict[str, gs.BackwardResult], seconds: dict
) -> pd.DataFrame:
    """Return, per group, pumping, the net-mode attribution, their ratio and the closure terms."""
    edges = gs.flow_edges(step)
    budget = gs.cell_budget(step, edges)
    gross, net = results["gross"], results["net"]
    rows = []
    for group, sel in groups.items():
        row = {"group": group, **well_cell_budget(step, sel, budget)}
        assert np.isclose(row["pumping"], gross.destination_inflow[group], rtol=1e-12)
        check = gs.diagnostics.backward_closure(step, gross, group)
        row["gross_volume_from"] = float(gross.volume_from[group].sum())
        row["gross_closure_error"] = check.error
        row["net_attributed"] = net.destination_inflow[group]
        row["net_volume_from"] = float(net.volume_from[group].sum())
        row.update(net_closure(edges, sel.cells, net.fraction_through[group], row["net_attributed"]))
        row["net_closure_error"] = row["net_volume_from"] - row["net_closure_rhs"]
        row["ratio_net_attributed"] = row["net_attributed"] / row["pumping"]
        row["ratio_net_volume_from"] = row["net_volume_from"] / row["pumping"]
        row["gross_seconds"], row["net_seconds"] = seconds["gross"], seconds["net"]
        rows.append(row)
    return pd.DataFrame(rows)


def mask_table(results: dict[str, gs.BackwardResult], endpoints: pd.DataFrame) -> pd.DataFrame:
    """Return workflow.compare_masks for both accounting modes."""
    frames = [wf.compare_masks(r, endpoints).assign(accounting=m) for m, r in results.items()]
    return pd.concat(frames, ignore_index=True)


def cell_classes(step: gs.FlowStep, dest: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return a class label per cell (priority well, SFR, other WEL/CHD, rest) and a mixed flag.

    Mixed cells have both source and sink terms; there F differs between the modes locally.
    """
    names = np.array([p.name.split("_")[0] for p in step.packages])
    package = names[step.term_package]
    label = np.full(step.n_cells, "rest", dtype=object)
    for name, cls in (("CHD", "other WEL/CHD"), ("WEL", "other WEL/CHD"), ("SFR", "SFR")):
        label[np.unique(step.term_cell[package == name])] = cls
    label[dest] = "priority well"
    source, sink = gs.assemble.term_totals(step)
    return label, (source > 0) & (sink > 0)


def class_table(
    step: gs.FlowStep,
    results: dict[str, gs.BackwardResult],
    dest: np.ndarray,
    start: np.ndarray,
    group: str = "priority",
) -> pd.DataFrame:
    """Return F and volume from per cell class, gross and net, for one group.

    local_amplification is the mean of O_gross / T_net over the mixed cells of the class that
    reach the group in either mode: the factor by which net mode raises F in that cell for the
    same F downstream.
    """
    label, mixed = cell_classes(step, dest)
    edges = gs.flow_edges(step)
    budget = gs.cell_budget(step, edges)
    _, throughflow = gs.assemble.net_balance(step.n_cells, edges)
    f = {m: r.fraction_through[group] for m, r in results.items()}
    reached = (f["gross"] > 0) | (f["net"] > 0)
    is_start = np.zeros(step.n_cells, dtype=bool)
    is_start[start] = True
    rows = []
    for cls in ("priority well", "SFR", "other WEL/CHD", "rest"):
        in_cls = label == cls
        mix = in_cls & mixed & reached & (throughflow > 0)
        row = {"class": cls, "cells_reached": int(np.sum(in_cls & reached))}
        row["mixed_cells_reached"] = int(mix.sum())
        ratio = budget.outflow[mix] / throughflow[mix]
        row["local_amplification"] = float(ratio.mean()) if mix.any() else np.nan
        row["start_cells"] = int(np.sum(in_cls & is_start))
        for m, r in results.items():
            row[f"{m}_volume_from"] = float(r.volume_from[group][in_cls].sum())
            row[f"{m}_sum_F_start"] = float(f[m][in_cls & is_start].sum())
            row[f"{m}_start_F>0.5"] = int(np.sum(in_cls & is_start & (f[m] > 0.5)))
        row["start_net_minus_gross>0.1"] = int(np.sum(in_cls & is_start & (f["net"] - f["gross"] > 0.1)))
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F zones against the PRT zone


def start_cell_values(
    step: gs.FlowStep, result: gs.BackwardResult, endpoints: pd.DataFrame, p: np.ndarray
) -> pd.DataFrame:
    """Return F, P, recharge, SFR leakage and all source inflow of the start cells (priority)."""
    start = endpoints["node0"].to_numpy()
    assert len(np.unique(start)) == len(start), "a start cell appears twice"
    by_package = gs.metrics.per_cell_by_package(step, sign=+1)
    source, _ = gs.assemble.term_totals(step)
    return pd.DataFrame(
        {
            "node": start,
            "region": endpoints["region"].to_numpy(),
            "F": result.fraction_through["priority"][start],
            "P": np.nan_to_num(p[start]),
            "recharge": by_package["RCHA"][start],
            "sfr": by_package["SFR_0"][start],
            "source": source[start],
        }
    )


def f_zones(f: np.ndarray, n_matched: int, thresholds: tuple[float, ...]) -> dict:
    """Return the F zones: F > t for each threshold and the n_matched cells with the largest F."""
    zones = {f"F>{t:g}": f > t for t in thresholds}
    top = np.zeros(len(f), dtype=bool)
    top[np.argsort(-f, kind="stable")[:n_matched]] = True
    zones["F area-matched"] = top
    return zones


def zone_row(cells: pd.DataFrame, f_zone: np.ndarray, p_zone: np.ndarray) -> dict:
    """Return coverage, area ratio, missed recharge and the reverse check of one F zone."""
    missed = p_zone & ~f_zone
    rch, src, p = cells["recharge"].to_numpy(), cells["source"].to_numpy(), cells["P"].to_numpy()
    n_p, n_f = int(p_zone.sum()), int(f_zone.sum())
    return {
        "prt_cells": n_p,
        "f_cells": n_f,
        "min_F_in_zone": float(cells["F"].to_numpy()[f_zone].min()) if n_f else np.nan,
        "area_ratio": n_f / n_p if n_p else np.nan,
        "coverage": float(np.sum(p_zone & f_zone) / n_p) if n_p else np.nan,
        "missed_cells": int(missed.sum()),
        "missed_cells_sfr": int(np.sum(missed & (cells["sfr"].to_numpy() > 0))),
        "median_F_missed": float(np.median(cells["F"].to_numpy()[missed])) if missed.any() else np.nan,
        "recharge_prt_zone": float(rch[p_zone].sum()),
        "recharge_missed": float(rch[missed].sum()),
        "source_missed": float(src[missed].sum()),
        "captured_source_missed": float(np.sum(p[missed] * src[missed])),
        "f_zone_inside_prt": float(np.sum(p_zone & f_zone) / n_f) if n_f else np.nan,
        "jaccard": wf.jaccard(f_zone, p_zone),
    }


def envelope_table(
    cells: pd.DataFrame,
    p_zones: tuple[float, ...] = P_ZONES,
    thresholds: tuple[float, ...] = F_THRESHOLDS,
    regions: tuple[str, ...] = REGIONS,
) -> pd.DataFrame:
    """Return zone_row for every region, PRT zone (P > z) and F zone (thresholds, area-matched)."""
    rows = []
    for region in regions:
        sub = cells if region == "all" else cells[cells["region"] == region]
        f = sub["F"].to_numpy()
        for z in p_zones:
            p_zone = sub["P"].to_numpy() > z
            for name, f_zone in f_zones(f, int(p_zone.sum()), thresholds).items():
                row = {"region": region, "prt_zone": f"P>{z:g}", "f_zone": name}
                rows.append({**row, **zone_row(sub, f_zone, p_zone)})
    return pd.DataFrame(rows)


def main(run_net: bool = True, run_envelope: bool = True, out: Path = wf.OUT) -> None:
    """Run the selected checks; tables go to out."""
    ws = out / "optimal"
    t0 = time.perf_counter()
    step, groups, results, seconds = trace_both(ws)
    endpoints = wf.read_endpoints()
    print(f"read and traced in {time.perf_counter() - t0:.1f} s ({seconds})")
    if run_net:
        accounting_table(step, groups, results, seconds).to_csv(
            out / "net_vs_gross_wells.csv", index=False
        )
        mask_table(results, endpoints).to_csv(out / "net_vs_gross_mp7.csv", index=False)
        dest, start = groups["priority"].cells, endpoints["node0"].to_numpy()
        class_table(step, results, dest, start).to_csv(
            out / "net_vs_gross_cell_classes.csv", index=False
        )
    if run_envelope:
        p = np.load(out / PRT_RUN / "cell_capture_fraction.npy").astype(float)
        assert len(p) == step.n_cells, "the PRT run is on a different grid"
        cells = start_cell_values(step, results["gross"], endpoints, p)
        envelope_table(cells).to_csv(out / "envelope_prt.csv", index=False)
    print(f"done in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
