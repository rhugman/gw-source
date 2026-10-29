"""Neversink case study: why full mixing and the published particles give different areas.

The published contributing area of the eight priority wells comes from forward MODPATH 7
particles, one at the centre of each start cell (uppermost active layer), that stop at weak
sinks. Full mixing here is gross accounting with every sink strong (TraceConfig(strong_sinks=
"all")): each cell with a sink term is absorbing, F = d / Snk there, so both methods stop
water at every sink and differ only in how water divides inside cells without sinks. F is the
share of the start cell's water that reaches the priority wells.

Agreement classes of the start cells: in both (published and F > 0.5), published only
(F <= 0.5), F > 0.5 only, and F 0.1 to 0.5 only (the F band). Two disputed sets:

- A: F > 0.1 and not published. The fate of their published particle (end status and cell of
  the .mpend files): top face of an SFR cell (status 2), buried SFR cell (a reach with an active
  cell above) or other well as a weak sink (status 3), strong sink (status 5).
- B: published and F <= 0.5. Where the rest of their water goes comes from a second backward
  trace (gross, all sinks strong) with one group per sink: priority wells, other wells, SFR
  reaches with an open top, buried SFR reaches, CHD. The shares sum to 1 in every cell with
  outflow.

Split cells. The disputed particles are retracked with MF6 PRT under the MODPATH 7 conventions
of mp7_convention.py (IFLOWFACE model, drape, stop at weak sinks), with cell-exit records, on
the same flow field. For each particle the split cell is the last cell on its path with
F > 0.1 (A) or F <= 0.5 (B): there the cell's outflow divides between a branch that reaches the
wells and one that does not, and the particle follows one branch. Every cell upstream inherits
the split share under full mixing. Split cells are classed by their relation to the sinks:
beside a priority well (within two cells in plan), sending water straight into an SFR sink cell,
or neither (between the wells' and the streams' catchments).

Distances (Fig. 4) are plan distances between cell centres: to the nearest SFR reach cell (any
layer) and to the nearest priority-well cell.

The model has no DRN package; its sinks are WEL, SFR and CHD. If the many-particle PRT run of
another script has written output/prt_many_particles_cells.* (P per cell), Fig. 3 adds P to
its cell labels.

Needs TraceConfig.strong_sinks (gwsource, branch feature/strong-sinks). Run after workflow.py:

    python studies/neversink/diagnostics.py

Tables and figures (PNG, 300 dpi) go to studies/neversink/output/diagnostics.
"""

import re
import shutil
import sys
from pathlib import Path

import flopy
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "studies" / "paper"))

import mp7_convention as mc  # noqa: E402
import neversink_figures as nfig  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402  (figures sets the Agg backend)
from matplotlib import patheffects  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

OUT = wf.OUT
# output/ may hold linked folders: write next to them
DIAG_DIR = (OUT / "optimal").resolve().parent / "diagnostics"
RUN_DIR = DIAG_DIR / "runs"
TRACK_FILE = DIAG_DIR / "pathlines_disputed.csv.gz"
P_PATTERN = "prt_many_particles_cells.*"
P_FILE = DIAG_DIR.parent / "prt_many_particles_cells.csv"
P_MIN = 0.9  # main disagreement: P >= P_MIN but F < F_HIGH, away from streams
STREAM_MIN_M = 200.0
DEFICIT_PARTS = ("lateral", "up", "down", "sink")
DEFICIT_COLORS = {"lateral": "#2a78d6", "up": "#6250d6", "down": "#1baf7a", "sink": "#eda100"}
DEFICIT_LABELS = {"lateral": "lateral", "up": "up", "down": "down",
                  "sink": "under a stream (sink cell)"}
MANY_ENDS = DIAG_DIR.parent / "prt_many_particles" / "endpoints.npz"
POSITION_BINS = (0, 1, 2, 3, 5, 10, 20, 1000)
POSITION_LABELS = ("1", "2", "3", "4–5", "6–10", "11–20", "> 20")
TRACK_COLUMNS = ("irpt", "icell", "istatus", "ireason", "t", "x", "y", "z")
DPI = 300
CELL = 50.0  # m
F_LOW, F_HIGH = 0.1, 0.5
WINDOW_PAD = 12  # cells around the classified start cells of a cluster
NEAR_WELL_CELLS = 2  # plan (Chebyshev) distance of a split cell "beside a priority well"

INK, MUTED, SURFACE, ACTIVE_FILL = nfig.INK, nfig.MUTED, nfig.SURFACE, nfig.ACTIVE_FILL
RED = "#e34948"
HALO = [patheffects.withStroke(linewidth=1.6, foreground=SURFACE)]
# Agreement classes, codes 1 to 4 (0: other start cells). Blue for the F area, orange for the
# published cells it misses, as the paper's overlap maps; aqua for F > 0.5 outside.
CLASSES = {
    1: ("in both (published, F > 0.5)", "#1c5cab"),
    2: ("published only (F ≤ 0.5)", "#eb6834"),
    3: ("F > 0.5 only", "#1baf7a"),
    4: ("F 0.1–0.5 only", "#86b6ef"),
}
# Sinks, one colour each in Figs 2 and 3
SINK_COLORS = {
    "priority wells": INK,
    "other wells": "#6250d6",
    "SFR, open top": "#2a78d6",
    "SFR, buried": "#1baf7a",
    "CHD": "#eda100",
}
FATES = {  # fate of the published particle of an A cell: colour
    "top face into SFR": SINK_COLORS["SFR, open top"],
    "buried SFR, weak-sink stop": SINK_COLORS["SFR, buried"],
    "other well, weak-sink stop": SINK_COLORS["other wells"],
    "strong sink": SINK_COLORS["CHD"],
    "other": "#9a9994",
}
MECHANISMS = (
    "beside a priority well",
    "beside a stream (water into an SFR cell)",
    "between wells and streams",
)
STREAM_GAIN, STREAM_LOSE = INK, "#9a9994"
PATH_COLORS = {"published": "#eb6834", "not published": INK}
STREAM_BINS = (-1.0, 1.0, 75.0, 175.0, 325.0, 625.0, np.inf)
STREAM_LABELS = ("0", "50", "100–150", "200–300", "350–600", "> 600")
WELL_BINS = (0.0, 250.0, 500.0, 1000.0, 2000.0, np.inf)
WELL_LABELS = ("< 250", "250–500", "500–1000", "1000–2000", "> 2000")


# ---------------------------------------------------------------- traces and cells


def sink_groups(step: gs.FlowStep, priority: gs.Selection, buried: np.ndarray) -> dict:
    """Return one destination group per sink: priority wells, other wells, SFR open, SFR
    buried, CHD (buried: per node, an active cell above)."""
    sink = step.term_flow < 0.0
    package = np.array([p.name for p in step.packages])[step.term_package]
    sfr = sink & (package == "SFR_0")
    under = buried[step.term_cell]
    return {
        "priority wells": priority,
        "other wells": gs.select(step, term_mask=sink & (package == "WEL_0") & ~priority.terms),
        "SFR, open top": gs.select(step, term_mask=sfr & ~under),
        "SFR, buried": gs.select(step, term_mask=sfr & under),
        "CHD": gs.select(step, term_mask=sink & (package == "CHD_0")),
    }


def trace_all(step: gs.FlowStep, buried: np.ndarray) -> dict[str, gs.BackwardResult]:
    """Trace the priority group (gross, and gross with all sinks strong) and the sink groups."""
    priority = wf.well_groups(step)["priority"]
    strong = gs.TraceConfig(accounting="gross", strong_sinks="all")
    return {
        "gross": gs.backward(step, {"priority": priority}, gs.TraceConfig(accounting="gross")),
        "gross_strong": gs.backward(step, {"priority": priority}, strong),
        "sinks": gs.backward(step, sink_groups(step, priority, buried), strong),
    }


def cell_sinks(step: gs.FlowStep, buried: np.ndarray) -> pd.DataFrame:
    """Return per node the net SFR exchange sfr_q (negative: gaining reach), the sinks present
    and whether the cell is buried."""
    package = np.array([p.name for p in step.packages])[step.term_package]
    n = step.n_cells
    priority = np.isin(step.term_boundname, [w.lower() for w in wf.PRIORITY_WELLS])
    sink = step.term_flow < 0.0

    def has(mask: np.ndarray) -> np.ndarray:
        out = np.zeros(n, dtype=bool)
        out[step.term_cell[mask]] = True
        return out

    sfr = package == "SFR_0"
    return pd.DataFrame(
        {
            "sfr": has(sfr),
            "sfr_q": np.bincount(step.term_cell[sfr], weights=step.term_flow[sfr], minlength=n),
            "sfr_sink": has(sink & sfr),
            "priority_well": has(sink & (package == "WEL_0") & priority),
            "other_well": has(sink & (package == "WEL_0") & ~priority),
            "chd_sink": has(sink & (package == "CHD_0")),
            "sink": has(sink),
            "buried": buried,
        }
    )


def node_klij(node, shape: tuple) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return 0-based layer, row and column of nodes on a (nlay, nrow, ncol) grid."""
    _, nrow, ncol = shape
    node = np.asarray(node)
    return node // (nrow * ncol), (node % (nrow * ncol)) // ncol, node % ncol


# ---------------------------------------------------------------- start cells


def fates(endpoints: pd.DataFrame, cells: pd.DataFrame) -> np.ndarray:
    """Return the FATES label of each particle from its MODPATH 7 status, exit face and end cell."""
    end = cells.iloc[endpoints["node"].to_numpy()]
    status = endpoints["status"].to_numpy()
    sfr, buried = end["sfr"].to_numpy(), end["buried"].to_numpy()
    top = (status == 2) & (endpoints["cellface"].to_numpy() == 6) & sfr
    weak = status == 3
    conditions = [top, weak & sfr & buried, weak & end["other_well"].to_numpy(), status == 5]
    return np.select(conditions, list(FATES)[:4], "other")


def particle_table(
    endpoints: pd.DataFrame, results: dict, cells: pd.DataFrame, shape: tuple
) -> pd.DataFrame:
    """Return per published particle its start cell, F, agreement class, set (A, B), the fate
    of an A particle and the sink shares of its start cell."""
    start = endpoints["node0"].to_numpy()
    published = wf.mp7_mask(endpoints, list(wf.PRIORITY_WELLS.values()))
    f = results["gross_strong"].fraction_through["priority"][start]
    k, i, j = node_klij(start, shape)
    table = endpoints.assign(
        layer=k, row=i, col=j, published=published, F=f,
        F_gross=results["gross"].fraction_through["priority"][start],
    )
    table["cls"] = np.select(
        [published & (f > F_HIGH), published, f > F_HIGH, f > F_LOW], [1, 2, 3, 4], 0
    )
    table["set"] = np.select([~published & (f > F_LOW), published & (f <= F_HIGH)], ["A", "B"], "")
    table["fate"] = np.where(table["set"] == "A", fates(endpoints, cells), "")
    sinks = results["sinks"]
    for group in sinks.groups:
        table[f"share {group}"] = sinks.fraction_through[group][start]
    return table


def class_grid(particles: pd.DataFrame, shape: tuple, column: str = "cls") -> np.ndarray:
    """Return a (row, column) grid of a particle column at the start cells (NaN elsewhere)."""
    grid = np.full(shape[1:], np.nan)
    assert not particles.duplicated(["row", "col"]).any(), "two start cells in one column"
    grid[particles["row"], particles["col"]] = particles[column]
    return grid


# ---------------------------------------------------------------- retracked paths


def run_pathlines(
    starts: pd.DataFrame, run_dir: Path = RUN_DIR, exe: Path | None = None
) -> pd.DataFrame:
    """Retrack the given published particles with PRT under the MODPATH 7 conventions.

    Same set-up as mp7_convention (IFLOWFACE model, drape of dry starts, stop at weak sinks),
    with release and cell-exit records. Returns the track records with start_row, the row of
    the particle in starts; the model copy and the PRT folder are deleted afterwards (disk).
    """
    exe = wf.mf6_exe() if exe is None else exe
    ws_face, prt_ws = run_dir / "optimal_iflowface", run_dir / "prt_paths"
    mc.prepare_iflowface_model(ws_face)
    wf.run_mf6(ws_face, exe)
    budget = ws_face / f"{wf.MODEL}.cbc"
    idomain = wf.grid_idomain(ws_face)
    sat = mc.cell_saturation(budget, idomain.size)
    draped = mc.drape_dry_starts(starts, idomain, sat)
    keep = mc.trackable(draped, sat)
    kept = draped[keep].reset_index(drop=True)
    sim = mc.write_mp7_prt(prt_ws, ws_face, budget, kept, exe, tracks=True)
    track_csv = gs.prt.run_prt(sim)
    tracks = pd.read_csv(track_csv, usecols=list(TRACK_COLUMNS))
    tracks["start_row"] = np.flatnonzero(keep)[tracks["irpt"].to_numpy() - 1]
    tracks["icell"] -= 1
    shutil.rmtree(run_dir)
    return tracks


def disputed_tracks(particles: pd.DataFrame, track_file: Path = TRACK_FILE) -> pd.DataFrame:
    """Return the PRT records of every published or F > 0.1 particle (run once, then cached);
    pid is the particle's row in particles."""
    if not track_file.is_file():
        sel = np.flatnonzero(particles["published"] | (particles["F"] > F_LOW)
                             | (particles["F_gross"] > F_LOW))
        tracks = run_pathlines(particles.iloc[sel].reset_index(drop=True))
        tracks["pid"] = sel[tracks.pop("start_row").to_numpy()]
        track_file.parent.mkdir(parents=True, exist_ok=True)
        tracks.to_csv(track_file, index=False)
    tracks = pd.read_csv(track_file)
    return tracks.sort_values(["pid", "t"], kind="stable").reset_index(drop=True)


def path_visits(tracks: pd.DataFrame) -> pd.DataFrame:
    """Return the cells each particle passes, in order (pid, k, cell)."""
    pid, cell = tracks["pid"].to_numpy(), tracks["icell"].to_numpy()
    new = np.r_[True, (pid[1:] != pid[:-1]) | (cell[1:] != cell[:-1])]
    visits = tracks.loc[new, ["pid", "icell"]].rename(columns={"icell": "cell"})
    visits["k"] = visits.groupby("pid").cumcount()
    return visits.reset_index(drop=True)


def end_agreement(particles: pd.DataFrame, tracks: pd.DataFrame) -> pd.DataFrame:
    """Return, per set, how many particles PRT ends in the published end cell."""
    term = tracks[tracks["ireason"] == 3].set_index("pid")["icell"]
    rows = []
    for name in ("A", "B"):
        pid = np.flatnonzero(particles["set"] == name)
        same = term.reindex(pid).to_numpy() == particles["node"].to_numpy()[pid]
        rows.append({"set": name, "particles": len(pid), "same_end_cell": int(same.sum())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- split cells


def face_flows(cell: int, edges: gs.Edges) -> pd.DataFrame:
    """Return the outflow of a cell to each neighbour (dst, q)."""
    out = edges.src == cell
    return pd.DataFrame({"dst": edges.dst[out], "q": edges.q[out]})


def plan_cells_to(nodes: np.ndarray, target: np.ndarray, shape: tuple) -> np.ndarray:
    """Return the plan (Chebyshev) distance in cells from each node to the nearest target node."""
    _, ti, tj = node_klij(target, shape)
    _, i, j = node_klij(nodes, shape)
    return np.maximum(np.abs(i[:, None] - ti), np.abs(j[:, None] - tj)).min(axis=1)


def split_cells(
    particles: pd.DataFrame,
    visits: pd.DataFrame,
    f: np.ndarray,
    cells: pd.DataFrame,
    edges: gs.Edges,
    budget: gs.CellBudget,
    shape: tuple,
) -> pd.DataFrame:
    """Return per A and B particle its split cell, the step out of it and its mechanism.

    The split cell is the last visit with F > F_LOW (A) or F <= F_HIGH (B). to_stream is the
    share of its outflow that goes straight into SFR sink cells.
    """
    v = visits.assign(F=f[visits["cell"].to_numpy()])
    v["set"] = particles["set"].to_numpy()[v["pid"].to_numpy()]
    v = v[v["set"] != ""]
    on_side = np.where(v["set"] == "A", v["F"] > F_LOW, v["F"] <= F_HIGH)
    table = pd.DataFrame({"k": v[on_side].groupby("pid")["k"].max()})
    table["n"] = v.groupby("pid").size().reindex(table.index)
    by_k = v.set_index(["pid", "k"])["cell"]
    pid = table.index.to_numpy()
    table["cell"] = by_k.loc[list(zip(pid, table["k"]))].to_numpy()
    table["next"] = [by_k.get((p, k + 1), -1) for p, k in zip(pid, table["k"])]
    table["set"] = particles["set"].to_numpy()[pid]
    table["F_start"] = particles["F"].to_numpy()[pid]
    table["F_split"] = f[table["cell"]]
    table["F_next"] = np.where(table["next"] >= 0, f[np.maximum(table["next"], 0)], np.nan)
    k0 = node_klij(table["cell"], shape)[0]
    k1 = node_klij(np.maximum(table["next"], 0), shape)[0]
    table["step"] = np.select(
        [table["next"] < 0, k1 < k0, k1 > k0], ["end", "up", "down"], "lateral"
    )
    sink = cells["sfr_sink"].to_numpy()
    to_stream = {}
    for c in np.unique(table["cell"]):
        q = face_flows(c, edges)
        to_stream[c] = q["q"][sink[q["dst"]]].sum() / budget.outflow[c]
    table["to_stream"] = table["cell"].map(to_stream)
    wells = np.flatnonzero(cells["priority_well"].to_numpy())
    table["well_cells"] = plan_cells_to(table["cell"].to_numpy(), wells, shape)
    table["mechanism"] = np.select(
        [table["well_cells"] <= NEAR_WELL_CELLS, table["to_stream"] > 0],
        list(MECHANISMS[:2]),
        MECHANISMS[2],
    )
    return table.reset_index(names="pid")


def mechanism_table(splits: pd.DataFrame) -> pd.DataFrame:
    """Return the disputed particles and distinct split cells per set and mechanism."""
    rows = []
    for (name, mech), part in splits.groupby(["set", "mechanism"]):
        rows.append({
            "set": name, "mechanism": mech, "particles": len(part),
            "share": len(part) / int((splits["set"] == name).sum()),
            "split_cells": part["cell"].nunique(),
            "mean_F_start": part["F_start"].mean(), "mean_F_split": part["F_split"].mean(),
            "mean_F_next": part["F_next"].mean(), "mean_to_stream": part["to_stream"].mean(),
            "split_is_start_cell": int((part["k"] == 0).sum()),
            "step_up": int((part["step"] == "up").sum()),
            "step_into_end_cell": int((part["k"] + 2 == part["n"]).sum()),
        })
    return pd.DataFrame(rows).sort_values(["set", "particles"], ascending=[True, False])


def split_concentration(splits: pd.DataFrame) -> pd.DataFrame:
    """Return, per set, the distinct split cells and how many hold half the particles."""
    rows = []
    for name, part in splits.groupby("set"):
        count = part["cell"].value_counts().to_numpy()
        half = int(np.searchsorted(np.cumsum(count), len(part) / 2) + 1)
        rows.append({"set": name, "particles": len(part), "split_cells": len(count),
                     "cells_with_half_the_particles": half})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- path budgets


def main_population(
    particles: pd.DataFrame, p_file: Path = P_FILE, p_min: float = P_MIN,
    f_max: float = F_HIGH, stream_min: float = STREAM_MIN_M,
) -> np.ndarray:
    """Return the particle ids of the main disagreement: published start cells with no stream
    reach in or next to them, at least stream_min from SFR, with P >= p_min but F < f_max.

    P, the stream class and the distance come from the many-particle PRT table (27 particles
    per start cell, stopping at weak sinks).
    """
    table = pd.read_csv(p_file, usecols=["node0", "stream_class", "sfr_distance_m",
                                         "P_priority"]).set_index("node0")
    table = table.reindex(particles["node0"].to_numpy())
    keep = (particles["published"].to_numpy() & (particles["F"].to_numpy() < f_max)
            & (table["P_priority"].to_numpy() >= p_min)
            & (table["stream_class"].to_numpy() == "neither")
            & (table["sfr_distance_m"].to_numpy() >= stream_min))
    return np.flatnonzero(keep)


def path_budget(
    path: np.ndarray, f: np.ndarray, edges: gs.Edges, budget: gs.CellBudget, shape: tuple
) -> pd.DataFrame:
    """Return, per cell k of a path (cells in order, ending in the well cell), F, the share of
    its outflow into the next path cell (stay) and the F deficit made in it, by direction.

    In a cell without sinks F_k = sum_j w_kj F_j (w = q / O), so
    F_{k+1} - F_k = sum_{j != next} w_kj (F_{k+1} - F_j): every outflow that leaves the path
    costs its share times the F contrast to the next path cell. Summed along the path this
    gives F_end - F_start exactly (asserted by the caller). Directions: lateral (same layer),
    up, down. A path cell with a sink term is absorbing (all sinks strong) and its whole
    F_{k+1} - F_k is booked as deficit_sink: in the published runs such a cell on the path is
    an open-top SFR cell whose flow sits on the top face, which particles below pass under.
    """
    layer = node_klij(path, shape)[0]
    rows = []
    for k, cell in enumerate(path[:-1]):
        nxt = path[k + 1]
        out = face_flows(cell, edges)
        w = out["q"].to_numpy() / budget.outflow[cell]
        dst = out["dst"].to_numpy()
        side = dst != nxt
        contrast = w[side] * (f[nxt] - f[dst[side]])
        k_dst = node_klij(dst[side], shape)[0]
        lateral, up = k_dst == layer[k], k_dst < layer[k]
        sink = budget.sink[cell] > 0.0
        if sink:
            contrast = np.zeros_like(contrast)
        rows.append({
            "k": k, "cell": cell, "layer": layer[k] + 1, "F": f[cell], "F_next": f[nxt],
            "outflow": budget.outflow[cell], "own_sink": budget.sink[cell],
            "stay": float(w[~side].sum()),
            "leave_lateral": float(w[side][lateral].sum()), "leave_up": float(w[side][up].sum()),
            "leave_down": float(w[side][~lateral & ~up].sum()),
            "deficit_lateral": float(contrast[lateral].sum()),
            "deficit_up": float(contrast[up].sum()),
            "deficit_down": float(contrast[~lateral & ~up].sum()),
            "deficit_sink": float(f[nxt] - f[cell]) if sink else 0.0,
        })
    table = pd.DataFrame(rows)
    table["deficit"] = table[[f"deficit_{d}" for d in DEFICIT_PARTS]].sum(axis=1)
    return table


def path_cells(visits: pd.DataFrame, pid: int) -> np.ndarray:
    """Return the cells of one particle's path, in order."""
    return visits.loc[visits["pid"] == pid, "cell"].to_numpy()


def path_summary(
    pids: np.ndarray, visits: pd.DataFrame, f: np.ndarray, edges: gs.Edges,
    budget: gs.CellBudget, particles: pd.DataFrame, shape: tuple, tol: float = 1e-6,
) -> tuple[pd.DataFrame, dict]:
    """Return per particle the budget of its path and the per-cell budgets.

    deficit = F_end - F_start; its shares by direction; cells_80 is the number of path cells
    that make 80 % of the deficit (largest first); max_cell_share the largest single cell's;
    stay_product the product of the stay shares (the share of the start cell's water that
    follows the particle's own cell sequence) and stay_product x F_end its lower bound of F.
    """
    rows, budgets = [], {}
    for pid in pids:
        path = path_cells(visits, pid)
        table = path_budget(path, f, edges, budget, shape)
        budgets[pid] = table
        deficit = f[path[-1]] - f[path[0]]
        assert abs(table["deficit"].sum() - deficit) < tol, f"path {pid} does not close"
        d = np.sort(table["deficit"].to_numpy())[::-1]
        cells_80 = int(np.searchsorted(np.cumsum(d), 0.8 * deficit) + 1)
        rows.append({
            "pid": pid, "region": particles.at[pid, "region"], "cells": len(path),
            "layers": "".join(str(v) for v in np.unique(node_klij(path, shape)[0] + 1)),
            "well": particles.at[pid, "node"], "F_start": f[path[0]], "F_end": f[path[-1]],
            "deficit": deficit, "stay_product": float(table["stay"].prod()),
            **{f"share_{d_}": table[f"deficit_{d_}"].sum() / deficit for d_ in DEFICIT_PARTS},
            "sink_cells": int((table["own_sink"] > 0).sum()),
            "cells_80": cells_80, "max_cell_share": d[0] / deficit,
            "cells_with_loss": int((table["deficit"] > 1e-3).sum()),
        })
    summary = pd.DataFrame(rows)
    summary["stay_bound"] = summary["stay_product"] * summary["F_end"]
    return summary, budgets


# ---------------------------------------------------------------- distances


def plan_distance(particles: pd.DataFrame, targets: np.ndarray, shape: tuple) -> np.ndarray:
    """Return the plan distance (m) from each start cell centre to the nearest target node."""
    _, ti, tj = node_klij(targets, shape)
    tree = cKDTree(np.column_stack([ti, tj]) * CELL)
    d, _ = tree.query(particles[["row", "col"]].to_numpy() * CELL)
    return d


def distance_table(particles: pd.DataFrame, cells: pd.DataFrame, shape: tuple) -> pd.DataFrame:
    """Return the class counts and shares of the classified start cells per distance bin."""
    part = particles[particles["cls"] > 0]
    frames = []
    for name, targets, bins, labels in (
        ("stream", np.flatnonzero(cells["sfr"]), STREAM_BINS, STREAM_LABELS),
        ("well", np.flatnonzero(cells["priority_well"]), WELL_BINS, WELL_LABELS),
    ):
        d = plan_distance(part, targets, shape)
        b = pd.Categorical(pd.cut(d, bins, labels=labels, right=False), categories=labels)
        counts = pd.crosstab(b, part["cls"].to_numpy()).reindex(
            index=list(labels), columns=list(CLASSES), fill_value=0)
        shares = counts.div(counts.sum(axis=1), axis=0)
        table = counts.add_prefix("cells_").join(shares.add_prefix("share_"))
        frames.append(table.assign(to=name).reset_index(names="bin_m"))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- map helpers


def cluster_windows(particles: pd.DataFrame, shape: tuple, pad: int = WINDOW_PAD) -> dict:
    """Return one map window per well cluster (U, SV_W, SV_S) around the wells and the
    classified start cells near them, at the aspect of the paper's map panels."""
    extent = np.isfinite(class_grid(particles[particles["cls"] > 0], shape))
    windows = nfig.nf.cluster_windows(wf.PRIORITY_WELLS, shape[2], extent, pad)
    named = {nfig.WINDOW_NAMES[k]: nfig.fit_aspect(v, shape[1:]) for k, v in windows.items()}
    return {name: named[name] for name in nfig.CLUSTERS}


def km(i: np.ndarray, j: np.ndarray, nrow: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the cell centres (x, y) in km from the grid origin."""
    return nfig.grid_km(i, j, nrow)


def stream_segments(model_dir: Path, cells: pd.DataFrame, shape: tuple) -> dict:
    """Return the SFR reach segments (km) of gaining and losing upstream reaches and the
    centres of the buried reach cells."""
    _, nrow, ncol = shape
    reaches = nfig.sfr_reaches(model_dir / "neversink_packagedata.dat")
    pairs = nfig.sfr_downstream(model_dir / "neversink.sfr")
    node = ((reaches["k"] * nrow + reaches["i"]) * ncol + reaches["j"]).to_numpy()
    gaining = pd.Series(cells["sfr_q"].to_numpy()[node] < 0.0, index=reaches.index)
    buried = cells["buried"].to_numpy()[node]
    x, y = km(reaches["i"].to_numpy(), reaches["j"].to_numpy(), nrow)
    xy = pd.DataFrame({"x": x, "y": y}, index=reaches.index)
    up = np.array([a for a, _ in pairs])
    down = np.array([b for _, b in pairs])
    seg = np.stack([xy.loc[up].to_numpy(), xy.loc[down].to_numpy()], axis=1)
    keep = np.hypot(*(seg[:, 1] - seg[:, 0]).T) <= nfig.MAX_SEGMENT_KM
    g = gaining.loc[up].to_numpy()
    return {"gaining": seg[keep & g], "losing": seg[keep & ~g], "buried": xy[buried].to_numpy()}


def draw_streams(ax: plt.Axes, streams: dict, lw: float = 0.5, buried_ms: float = 1.2,
                 scale: float = 1.0) -> None:
    """Draw gaining reaches (ink), losing reaches (grey) and buried reach cells (red x)."""
    for key, color in (("losing", STREAM_LOSE), ("gaining", STREAM_GAIN)):
        ax.add_collection(LineCollection(streams[key] * scale, colors=color, linewidths=lw,
                                         zorder=3))
    b = streams["buried"] * scale
    ax.plot(b[:, 0], b[:, 1], ls="", marker="x", ms=buried_ms, mew=0.5, color=RED, zorder=4)


def well_label(name: str) -> str:
    """Return a well name without repeated underscores."""
    return re.sub("_+", "_", name)


def draw_wells(ax: plt.Axes, cells: pd.DataFrame, shape: tuple, window: tuple,
               label: bool) -> None:
    """Draw the priority wells (optionally labelled) and the other wells inside window."""
    r0, r1, c0, c1 = window
    nrow = shape[1]
    styles = {
        "other_well": dict(marker="^", ms=3.2, mfc=SURFACE, mec=INK, mew=0.6),
        "priority_well": dict(marker="o", ms=4.2, mfc=SURFACE, mec=INK, mew=1.0),
    }
    for kind, style in styles.items():
        _, i, j = node_klij(np.flatnonzero(cells[kind].to_numpy()), shape)
        inside = (i >= r0) & (i <= r1) & (j >= c0) & (j <= c1)
        x, y = km(i[inside], j[inside], nrow)
        ax.plot(x, y, ls="", zorder=6, **style)
    if not label:
        return
    placed = []
    step_km = 0.08 * (r1 - r0 + 1) * nfig.nf.CELL_KM
    wells = sorted(wf.PRIORITY_WELLS.items(), key=lambda kv: node_klij(kv[1], shape)[1])
    for name, node in wells:
        _, i, j = node_klij(node, shape)
        if not (r0 <= i <= r1 and c0 <= j <= c1):
            continue
        x, y = km(i, j, nrow)
        ty = float(y) + step_km
        while any(abs(ty - p) < step_km for p in placed):
            ty -= step_km
        placed.append(ty)
        ax.annotate(well_label(name), (float(x), float(y)), xytext=(float(x) + 2 * step_km, ty),
                    fontsize=5.8, ha="left", va="center", path_effects=HALO, zorder=7,
                    arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.4})


def map_frame(ax: plt.Axes, window: tuple, nrow: int, title: str) -> None:
    """Fit a map panel to window, hide ticks and set the title."""
    extent = nfig.window_extent(window, nrow)
    ax.set_xlim(extent[:2])
    ax.set_ylim(extent[2:])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, loc="left", fontsize=7)


def category_image(
    ax: plt.Axes, grid: np.ndarray, active: np.ndarray, window: tuple, colors: list
) -> None:
    """Draw integer codes 1..n of grid in colors, other active cells grey."""
    r0, r1, c0, c1 = window
    codes = np.where(np.isfinite(grid), grid, 0.0)
    codes = np.where(active, codes, np.nan)
    cmap = ListedColormap([ACTIVE_FILL, *colors]).with_extremes(bad=SURFACE)
    ax.imshow(codes[r0 : r1 + 1, c0 : c1 + 1], cmap=cmap, vmin=-0.5, vmax=len(colors) + 0.5,
              extent=nfig.window_extent(window, grid.shape[0]), interpolation="nearest")


def stream_handles() -> list:
    """Return legend handles of the stream and well overlays."""
    return [
        plt.Line2D([], [], color=STREAM_GAIN, lw=1, label="SFR reach, gaining"),
        plt.Line2D([], [], color=STREAM_LOSE, lw=1, label="SFR reach, losing"),
        plt.Line2D([], [], ls="", marker="x", ms=3, mew=0.7, color=RED,
                   label="buried SFR cell (active cell above)"),
        plt.Line2D([], [], ls="", marker="o", ms=4, mfc=SURFACE, mec=INK, mew=1.0,
                   label="priority well"),
        plt.Line2D([], [], ls="", marker="^", ms=3.5, mfc=SURFACE, mec=INK, mew=0.6,
                   label="other well"),
    ]


def window_counts(grid: np.ndarray, window: tuple, codes) -> list[int]:
    """Return the number of cells of each code inside window."""
    r0, r1, c0, c1 = window
    part = grid[r0 : r1 + 1, c0 : c1 + 1]
    return [int(np.sum(part == c)) for c in codes]


def save(fig: plt.Figure, name: str, fig_dir: Path = DIAG_DIR) -> Path:
    """Save a figure as PNG (300 dpi) in fig_dir and return the path."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / f"{name}.png"
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- Fig. 1: agreement map


def agreement_map(
    particles: pd.DataFrame, cells: pd.DataFrame, streams: dict, windows: dict,
    active: np.ndarray, shape: tuple,
) -> Path:
    """Fig. 1: agreement classes of the start cells with the sinks, one panel per cluster."""
    nfig.paper_style()
    grid = class_grid(particles, shape)
    colors = [c for _, c in CLASSES.values()]
    fig, axes = plt.subplots(1, len(windows), figsize=(7.2, 3.4), layout="constrained")
    for ax, (name, window) in zip(axes, windows.items()):
        category_image(ax, grid, active, window, colors)
        draw_streams(ax, streams)
        draw_wells(ax, cells, shape, window, label=True)
        counts = " / ".join(str(n) for n in window_counts(grid, window, CLASSES))
        map_frame(ax, window, shape[1], f"{name} window: {counts}")
    x0, _, y0, _ = nfig.window_extent(next(iter(windows.values())), shape[1])
    nfig.scale_bar(axes[0], x0 + 0.3, y0 + 0.3, 1.0)
    handles = [Patch(facecolor=c, label=f"{lab}: {int((particles['cls'] == k).sum())}")
               for k, (lab, c) in CLASSES.items()]
    fig.legend(handles=handles + stream_handles(), loc="outside lower center", ncol=4,
               fontsize=6.3, handlelength=1.4, columnspacing=1.0)
    fig.suptitle("Start cells of the published particles against F (gross, all sinks strong). "
                 "Titles: cells per class in the window, legend order;\nlegend: all three "
                 "release regions. The model has no DRN package.", fontsize=6.8, x=0.01,
                 ha="left")
    return save(fig, "fig1_agreement_map")


# ---------------------------------------------------------------- Fig. 2: fate of disputed cells


def fate_counts(particles: pd.DataFrame, cells: pd.DataFrame, endpoints: pd.DataFrame
                ) -> pd.DataFrame:
    """Return the A cells per fate under gross + strong (main) and plain gross."""
    plain = (~particles["published"] & (particles["F_gross"] > F_LOW)).to_numpy()
    plain_fate = pd.Series(fates(endpoints, cells)[plain]).value_counts()
    main = particles.loc[particles["set"] == "A", "fate"].value_counts()
    return pd.DataFrame({
        "fate": list(FATES),
        "gross_strong": [int(main.get(f, 0)) for f in FATES],
        "gross": [int(plain_fate.get(f, 0)) for f in FATES],
    })


def other_sinks() -> list[str]:
    """Return the sink groups other than the priority wells."""
    return [g for g in SINK_COLORS if g != "priority wells"]


def dominant_other(particles: pd.DataFrame) -> np.ndarray:
    """Return, per particle, the code (1..4, order of other_sinks) of the sink other than the
    priority wells that takes the largest share of its water."""
    shares = particles[[f"share {g}" for g in other_sinks()]].to_numpy()
    return np.argmax(shares, axis=1) + 1


def hbar(ax: plt.Axes, labels: list, values: list, colors: list, fmt,
         ghost: list | None = None) -> None:
    """Draw labelled horizontal bars, top to bottom, with optional dashed comparison bars."""
    y = np.arange(len(labels))[::-1]
    ax.barh(y, values, height=0.62, color=colors, edgecolor=SURFACE, linewidth=0.8)
    ghost_values = ghost if ghost is not None else [None] * len(values)
    if ghost is not None:
        ax.barh(y, ghost, height=0.62, facecolor="none", edgecolor=MUTED, linewidth=0.7,
                ls=(0, (2, 1.5)))
    top = max(max(values), max(ghost) if ghost is not None else 0)
    for yy, v, g in zip(y, values, ghost_values):
        text = fmt(v) if g is None else f"{fmt(v)} ({fmt(g)})"
        ax.text(max(v, g or 0) + 0.03 * top, yy, text, va="center", fontsize=6.3)
    ax.set_yticks(y, labels, fontsize=6.3)
    ax.set_xlim(0, top * 1.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", labelsize=6)


def fate_figure(
    particles: pd.DataFrame, counts: pd.DataFrame, splits: pd.DataFrame, cells: pd.DataFrame,
    streams: dict, windows: dict, active: np.ndarray, shape: tuple,
) -> Path:
    """Fig. 2: (a) fate of the published particles of the A cells, with their split cells;
    (b) where full mixing sends the rest of the water of the B cells."""
    nfig.paper_style()
    nrow = shape[1]
    fig = plt.figure(figsize=(7.4, 8.0), layout="constrained")
    rows = fig.subfigures(3, 1, height_ratios=(1.0, 0.9, 0.85))
    # (a) maps
    a = particles[particles["set"] == "A"]
    code = a["fate"].map({f: k + 1 for k, f in enumerate(FATES)})
    grid_a = class_grid(a.assign(code=code), shape, "code")
    axes = rows[0].subplots(1, len(windows))
    split_a = splits[splits["set"] == "A"]["cell"].value_counts()
    _, si, sj = node_klij(split_a.index.to_numpy(), shape)
    sx, sy = km(si, sj, nrow)
    for ax, (name, window) in zip(axes, windows.items()):
        category_image(ax, grid_a, active, window, list(FATES.values()))
        draw_streams(ax, streams)
        draw_wells(ax, cells, shape, window, label=False)
        ax.scatter(sx, sy, s=2 + 0.3 * split_a.to_numpy(), facecolor="none", edgecolor=RED,
                   linewidth=0.5, zorder=8)
        n = window_counts(grid_a, window, range(1, len(FATES) + 1))
        map_frame(ax, window, nrow, f"(a) {name}: {sum(n)} F-only cells")
    handles = [Patch(facecolor=c, label=f"particle ends: {f}") for f, c in FATES.items()
               if counts.set_index("fate").loc[f, "gross_strong"] > 0]
    handles.append(plt.Line2D([], [], ls="", marker="o", mfc="none", mec=RED, ms=5,
                              label="split cell of these particles (area: particles)"))
    rows[0].legend(handles=handles + stream_handles(), loc="outside lower center", ncol=3,
                   fontsize=6.1, handlelength=1.3, columnspacing=0.9)
    # (b) maps
    b = particles[particles["set"] == "B"]
    grid_b = class_grid(b.assign(code=dominant_other(b)), shape, "code")
    axes = rows[1].subplots(1, len(windows))
    for ax, (name, window) in zip(axes, windows.items()):
        category_image(ax, grid_b, active, window, [SINK_COLORS[g] for g in other_sinks()])
        draw_streams(ax, streams)
        draw_wells(ax, cells, shape, window, label=False)
        n = window_counts(grid_b, window, range(1, 5))
        map_frame(ax, window, nrow, f"(b) {name}: {sum(n)} published cells, F ≤ 0.5")
    handles = [Patch(facecolor=SINK_COLORS[g], label=f"most of the rest to: {g}")
               for g in other_sinks()]
    rows[1].legend(handles=handles, loc="outside lower center", ncol=4, fontsize=6.1,
                   handlelength=1.3, columnspacing=0.9)
    # bars
    ax_a, ax_b = rows[2].subplots(1, 2)
    hbar(ax_a, list(counts["fate"]), list(counts["gross_strong"]), list(FATES.values()),
         lambda v: f"{int(v)}", list(counts["gross"]))
    ax_a.set_title(f"(a) end of the published particle of the {counts['gross_strong'].sum()} "
                   "cells\nwith F > 0.1 outside the published area", loc="left", fontsize=7)
    ax_a.set_xlabel(f"start cells; dashed and in brackets: plain gross ({counts['gross'].sum()}"
                    " cells)", fontsize=6.3)
    groups = list(SINK_COLORS)
    means = [float(b[f"share {g}"].mean()) for g in groups]
    hbar(ax_b, groups, means, [SINK_COLORS[g] for g in groups], lambda v: f"{v:.3f}")
    ax_b.set_title(f"(b) where the water of the {len(b)} published cells\nwith F ≤ 0.5 goes "
                   "(mean share by sink)", loc="left", fontsize=7)
    ax_b.set_xlabel("share of the start cell's water (trace per sink)",
                    fontsize=6.3)
    return save(fig, "fig2_fate_of_disputed_cells")


# ---------------------------------------------------------------- Fig. 3: worked cells


def pick_paths(summary: pd.DataFrame) -> dict:
    """Return three main-set paths: the most typical one ending in a U well and in an SV well
    (deficit cells, path length and largest cell share closest to the medians), and the path
    with the largest share of its deficit made under a stream cell."""
    clean = summary[summary["sink_cells"] == 0]
    score = sum(((clean[c] - clean[c].median()) / clean[c].std()).abs()
                for c in ("cells", "cells_80", "max_cell_share", "share_lateral"))
    is_u = clean["well"].isin([wf.PRIORITY_WELLS[w] for w in nfig.CLUSTERS["U"]])
    under = summary[summary["sink_cells"] > 0]
    return {
        "U well": int(clean.loc[score[is_u].idxmin(), "pid"]),
        "SV well": int(clean.loc[score[~is_u].idxmin(), "pid"]),
        "under a stream": int(under.loc[under["share_sink"].idxmax(), "pid"]),
    }


def loss_cells(paths: dict, budgets: dict, splits: pd.DataFrame, visits: pd.DataFrame
               ) -> dict:
    """Return the worked cells of Fig. 3: the cell making the largest F deficit on each
    example path, and the cell making the most deficit summed over all main-set paths.

    Each entry holds the cell, the ids of the main-set paths through it (published) and of the
    A particles split in it (not published), and the deficit made there.
    """
    total = pd.concat(budgets.values()).groupby("cell")["deficit"].sum()
    cells = {f"largest loss, {name} path": int(budgets[pid].sort_values("deficit").iloc[-1]["cell"])
             for name, pid in paths.items()}
    rest = total.drop(list(cells.values()), errors="ignore")
    cells["largest loss, all paths"] = int(rest.idxmax())
    main = np.array(list(budgets))
    out = {}
    for name, cell in cells.items():
        through = visits.loc[visits["cell"].eq(cell) & visits["pid"].isin(main), "pid"].unique()
        out[name] = {
            "cell": cell,
            "pids": {"published": through,
                     "not published": example_pids(splits, cell)["not published"]},
            "note": f"{len(through)} of {len(main)} paths pass, summed loss {total[cell]:.2f}",
        }
    return out


def load_p(out: Path = DIAG_DIR.parent, pattern: str = P_PATTERN) -> np.ndarray | None:
    """Return P per node from the many-particle PRT run, or None if it has not been written."""
    for path in sorted(out.glob(pattern)):
        if path.suffix == ".npy":
            return np.load(path).astype(float)
        if path.suffix == ".npz":
            data = np.load(path)
            key = next(k for k in data.files if k.lower() in ("p", "priority", "capture"))
            return data[key].astype(float)
        if path.suffix == ".csv":  # one row per published start cell (node0)
            table = pd.read_csv(path, usecols=["node0", "P_priority"])
            p = np.full(int(table["node0"].max()) + 1, np.nan)
            p[table["node0"]] = table["P_priority"]
            return p
    return None


def cell_label(node: int, f: np.ndarray, p: np.ndarray | None) -> str:
    """Return the F (and P) label of a node."""
    text = f"{f[node]:.2f}"
    if p is not None and node < len(p) and np.isfinite(p[node]):
        text += f"\nP {p[node]:.2f}"
    return text


def f_color(value: float):
    """Return the class colour of an F value (neversink_figures.f_classes; grey below 0.01)."""
    cmap, norm = nfig.f_classes()
    return cmap(norm(value)) if value >= nfig.F_EDGES[0] else ACTIVE_FILL


def draw_paths(ax: plt.Axes, tracks: pd.DataFrame, pids: dict, scale: float = 1.0,
               lw: float = 0.6, zorder: int = 8) -> None:
    """Draw the retracked paths of each set of particle ids (plan view)."""
    halo = [patheffects.withStroke(linewidth=lw + 0.8, foreground=SURFACE)]
    for label, ids in pids.items():
        for _, path in tracks[tracks["pid"].isin(ids)].groupby("pid"):
            ax.plot(path["x"] * scale, path["y"] * scale, color=PATH_COLORS[label], lw=lw,
                    alpha=0.85, zorder=zorder, path_effects=halo)


def zoom_panel(
    ax: plt.Axes, cell: int, f: np.ndarray, p: np.ndarray | None, edges: gs.Edges,
    budget: gs.CellBudget, cells: pd.DataFrame, tracks: pd.DataFrame, pids: dict,
    idomain: np.ndarray, streams: dict, title: str, half: int = 2,
) -> None:
    """Plan view of a split cell and its neighbours in its layer: F (and P) per cell, outflow by
    face (arrows, m3/d), vertical outflow and own sinks as text, and the retracked paths."""
    shape = idomain.shape
    _, nrow, ncol = shape
    k, i, j = (int(v) for v in node_klij(cell, shape))
    for ii in range(i - half, i + half + 1):
        for jj in range(j - half, j + half + 1):
            node = (k * nrow + ii) * ncol + jj
            x0, y0 = jj * CELL, (nrow - ii - 1) * CELL
            active = idomain[k, ii, jj] > 0
            sink = bool(cells["sink"].iat[node])
            ax.add_patch(Rectangle((x0, y0), CELL, CELL, zorder=1,
                                   facecolor=f_color(f[node]) if active else SURFACE,
                                   edgecolor=RED if sink else MUTED, lw=1.2 if sink else 0.3))
            if active:
                ax.text(x0 + 0.5 * CELL, y0 + 0.9 * CELL, cell_label(node, f, p), ha="center",
                        va="top", fontsize=5, path_effects=HALO, zorder=5, linespacing=0.9)
            if cells["priority_well"].iat[node]:
                ax.plot(x0 + 0.5 * CELL, y0 + 0.3 * CELL, "o", ms=4.5, mfc=SURFACE, mec=INK,
                        mew=1.0, zorder=6)
    xc, yc = (j + 0.5) * CELL, (nrow - i - 0.5) * CELL
    ax.add_patch(Rectangle((j * CELL, (nrow - i - 1) * CELL), CELL, CELL, facecolor="none",
                           edgecolor=INK, lw=1.6, zorder=7))
    flows = face_flows(cell, edges)
    outflow = budget.outflow[cell]
    vertical = []
    for dst, q in zip(flows["dst"], flows["q"]):
        kk, ii, jj = (int(v) for v in node_klij(dst, shape))
        if kk != k:
            where = "SFR cell" if cells["sfr_sink"].iat[dst] else f"layer {kk + 1}"
            vertical.append(f"{'up' if kk < k else 'down'} {q:.3g} to {where} (F {f[dst]:.2f})")
            continue
        dx, dy = jj - j, -(ii - i)
        lw = 0.5 + 3.0 * q / outflow
        ax.annotate("", xy=(xc + 0.7 * CELL * dx, yc + 0.7 * CELL * dy),
                    xytext=(xc + 0.15 * CELL * dx, yc + 0.15 * CELL * dy), zorder=9,
                    arrowprops={"arrowstyle": "-|>", "color": INK, "lw": lw,
                                "mutation_scale": 5 + 1.5 * lw, "shrinkA": 0, "shrinkB": 0})
        ax.text(xc + 0.88 * CELL * dx + 0.22 * CELL * abs(dy),
                yc + 0.85 * CELL * dy - 0.2 * CELL * abs(dx), f"{q:.0f}", fontsize=5.5,
                ha="center", va="center", path_effects=HALO, zorder=10, fontweight="bold")
    lines = [f"this cell: outflow {outflow:.0f} m³/d, own sinks {budget.sink[cell]:.0f}"]
    lines += vertical or ["no vertical outflow"]
    ax.text(0.0, -0.02, "\n".join(lines), transform=ax.transAxes, fontsize=5.3, va="top",
            linespacing=1.1)
    draw_paths(ax, tracks, pids, lw=0.45, zorder=4)
    draw_streams(ax, streams, lw=1.0, buried_ms=4, scale=1000.0)
    ax.set_xlim((j - half) * CELL, (j + half + 1) * CELL)
    ax.set_ylim((nrow - i - half - 1) * CELL, (nrow - i + half) * CELL)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, loc="left", fontsize=6.3)


def overview_panel(
    ax: plt.Axes, cell: int, f_top: np.ndarray, tracks: pd.DataFrame, pids: dict,
    particles: pd.DataFrame, cells: pd.DataFrame, streams: dict, shape: tuple, title: str,
) -> None:
    """Whole retracked paths through a split cell over F of the uppermost active cells, with
    their start cells and the split cell."""
    nrow, ncol = shape[1:]
    ids = np.concatenate(list(pids.values()))
    part = tracks[tracks["pid"].isin(ids)]
    x, y = part["x"].to_numpy() / 1000, part["y"].to_numpy() / 1000
    size = max(np.ptp(x), np.ptp(y)) + 0.4
    xm, ym = 0.5 * (x.min() + x.max()), 0.5 * (y.min() + y.max())
    x0, x1, y0, y1 = xm - size / 2, xm + size / 2, ym - size / 2, ym + size / 2
    cell_km = nfig.nf.CELL_KM
    window = (max(int(nrow - y1 / cell_km), 0), min(int(nrow - y0 / cell_km), nrow - 1),
              max(int(x0 / cell_km), 0), min(int(x1 / cell_km), ncol - 1))
    cmap, norm = nfig.f_classes()
    ax.imshow(f_top[window[0] : window[1] + 1, window[2] : window[3] + 1], cmap=cmap, norm=norm,
              extent=nfig.window_extent(window, nrow), interpolation="nearest")
    draw_streams(ax, streams, lw=0.6, buried_ms=1.4)
    draw_wells(ax, cells, shape, window, label=False)
    draw_paths(ax, tracks, pids, scale=1e-3, lw=0.45, zorder=5)
    for label, idx in pids.items():
        st = particles.loc[idx]
        sx, sy = km(st["row"].to_numpy(), st["col"].to_numpy(), nrow)
        ax.plot(sx, sy, ls="", marker="s", ms=1.8, mfc=PATH_COLORS[label], mec=SURFACE, mew=0.2,
                zorder=6)
    _, i, j = node_klij(cell, shape)
    cx, cy = km(i, j, nrow)
    ax.add_patch(Rectangle((float(cx) - 0.06, float(cy) - 0.06), 0.12, 0.12, facecolor="none",
                           edgecolor=RED, lw=1.1, zorder=7))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, loc="left", fontsize=6.3)
    bar = 0.5 if size > 1.2 else 0.2
    xb, yb = x0 + 0.06 * size, y0 + 0.05 * size
    ax.plot([xb, xb + bar], [yb, yb], color=INK, lw=1.2, path_effects=HALO, zorder=9)
    ax.text(xb + bar / 2, yb + 0.02 * size, f"{bar * 1000:.0f} m", ha="center", va="bottom",
            fontsize=5.5, path_effects=HALO, zorder=9)


def section_panel(
    ax: plt.Axes, cell: int, f: np.ndarray, tracks: pd.DataFrame, pids: dict,
    cells: pd.DataFrame, grb: flopy.mf6.utils.MfGrdFile, head: np.ndarray, shape: tuple,
    title: str, half: int = 8,
) -> None:
    """Cross-section through a split cell along the main direction of the paths near it: F per
    cell, water table, SFR sink cells and the retracked paths within 1.5 cells of the section."""
    nlay, nrow, ncol = shape
    k, i, j = (int(v) for v in node_klij(cell, shape))
    ids = np.concatenate(list(pids.values()))
    xc, yc = (j + 0.5) * CELL, (nrow - i - 0.5) * CELL
    near = tracks[tracks["pid"].isin(ids)]
    near = near[(np.abs(near["x"] - xc) < half * CELL) & (np.abs(near["y"] - yc) < half * CELL)]
    along_x = np.ptp(near["x"]) >= np.ptp(near["y"])
    bot = np.asarray(grb.bot).reshape(nlay, nrow, ncol)
    tops = np.concatenate([np.asarray(grb.top).reshape(1, nrow, ncol), bot[:-1]], axis=0)
    idomain = np.asarray(grb.idomain).reshape(nlay, nrow, ncol)
    h = head.reshape(nlay, nrow, ncol)
    polys, colors, edgecolors, wt_s, wt_z = [], [], [], [], []
    for d in range(-half, half + 1):
        ii, jj = (i, j + d) if along_x else (i + d, j)
        s0 = (d - 0.5) * CELL
        wet = []
        for kk in range(nlay):
            if idomain[kk, ii, jj] <= 0:
                continue
            node = (kk * nrow + ii) * ncol + jj
            z0, z1 = bot[kk, ii, jj], tops[kk, ii, jj]
            polys.append([(s0, z0), (s0 + CELL, z0), (s0 + CELL, z1), (s0, z1)])
            colors.append(f_color(f[node]))
            edgecolors.append(RED if cells["sfr_sink"].iat[node] else MUTED)
            if h[kk, ii, jj] > z0:
                wet.append(h[kk, ii, jj])
        if wet:
            wt_s += [s0, s0 + CELL]
            wt_z += [wet[0]] * 2
    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors=edgecolors,
                                     linewidths=0.5, zorder=1))
    sfr = [poly for poly, e in zip(polys, edgecolors) if e == RED]
    ax.add_collection(PolyCollection(sfr, facecolors="none", edgecolors=RED, hatch="////",
                                     linewidths=0.8, zorder=2))
    ax.plot(wt_s, wt_z, color="#2a78d6", lw=0.9, zorder=3)
    ax.add_patch(Rectangle((-0.5 * CELL, bot[k, i, j]), CELL, tops[k, i, j] - bot[k, i, j],
                           facecolor="none", edgecolor=INK, lw=1.4, zorder=4))
    for label, idx in pids.items():
        for _, path in tracks[tracks["pid"].isin(idx)].groupby("pid"):
            off = (path["y"] - yc) if along_x else (path["x"] - xc)
            band = np.abs(off) < 1.5 * CELL
            s = (path["x"] - xc) if along_x else -(path["y"] - yc)
            ax.plot(np.where(band, s, np.nan), np.where(band, path["z"], np.nan),
                    color=PATH_COLORS[label], lw=0.6, alpha=0.85, zorder=5)
    z = np.array([pt[1] for poly in polys for pt in poly])
    ax.set_xlim(-(half + 0.5) * CELL, (half + 0.5) * CELL)
    ax.set_ylim(bot[k, i, j] - 10.0, z.max() + 2)
    direction = "west to east" if along_x else "north to south"
    ax.set_xlabel(f"distance from the boxed cell, {direction} (m)", fontsize=6.5)
    ax.set_ylabel("elevation (m)", fontsize=6.5)
    ax.tick_params(labelsize=6)
    ax.set_title(title, loc="left", fontsize=6.5)


def example_pids(splits: pd.DataFrame, cell: int) -> dict:
    """Return the ids of the published (B) and not published (A) particles split in cell."""
    here = splits[splits["cell"] == cell]
    return {
        "published": here.loc[here["set"] == "B", "pid"].to_numpy(),
        "not published": here.loc[here["set"] == "A", "pid"].to_numpy(),
    }


def worked_cells(
    examples: dict, particles: pd.DataFrame, f: np.ndarray, f_top: np.ndarray,
    p: np.ndarray | None, edges: gs.Edges, budget: gs.CellBudget, cells: pd.DataFrame,
    tracks: pd.DataFrame, streams: dict, idomain: np.ndarray, grb: flopy.mf6.utils.MfGrdFile,
    head: np.ndarray,
) -> Path:
    """Fig. 3: the four cells where the main-set paths lose most F, each as a zoom with face
    flows and as an overview of the paths through it, and a cross-section through the first."""
    nfig.paper_style()
    shape = idomain.shape
    fig = plt.figure(figsize=(7.4, 8.3), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(2.5, 1.0))
    axes = top.subplots(2, len(examples))
    letters = iter("abcdefghij")
    for col, (name, ex) in enumerate(examples.items()):
        cell, pids = ex["cell"], ex["pids"]
        k, i, j = (int(v) for v in node_klij(cell, shape))
        title = (f"({next(letters)}) {name}\nlayer {k + 1}, row {i + 1}, col {j + 1}:\n"
                 f"{ex['note']}")
        zoom_panel(axes[0, col], cell, f, p, edges, budget, cells, tracks, pids, idomain,
                   streams, title)
        start = particles.loc[np.concatenate(list(pids.values()))]
        start_f = start["F"]
        text = (f"({next(letters)}) their whole paths; start-cell\nF {start_f.min():.2f} to "
                f"{start_f.max():.2f} (median {start_f.median():.2f})")
        if p is not None:
            start_p = p[np.minimum(start["node0"].to_numpy(), len(p) - 1)]
            text += f"\nmedian start-cell P {np.nanmedian(start_p):.2f}"
        overview_panel(axes[1, col], cell, f_top, tracks, pids, particles, cells, streams,
                       shape, text)
    ax = bottom.subplots(1, 1)
    name, ex = next(iter(examples.items()))
    section_panel(ax, ex["cell"], f, tracks, ex["pids"], cells, grb, head, shape,
                  f"({next(letters)}) cross-section through the cell of (a) (black box): "
                  "hatched SFR sink cells, blue line water table, paths within 75 m")
    cmap, norm = nfig.f_classes()
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.03,
                       pad=0.01, ticks=nfig.F_EDGES, extend="min")
    bar.set_label("F (grey below 0.01)", fontsize=6.5)
    bar.ax.tick_params(labelsize=6)
    handles = [
        plt.Line2D([], [], color=PATH_COLORS["published"], lw=1,
                   label="published path to a priority well (P ≥ 0.9, F < 0.5, away from streams)"),
        plt.Line2D([], [], color=PATH_COLORS["not published"], lw=1,
                   label="path to another sink (F > 0.1, not published)"),
        Patch(facecolor="none", edgecolor=RED, lw=1.2, label="cell with a sink term"),
        *stream_handles()[:3],
    ]
    top.legend(handles=handles, loc="outside lower center", ncol=2, fontsize=6.2,
               handlelength=1.6)
    note = ("\nP: many-particle PRT share at published start cells" if p is not None else "")
    fig.suptitle("Where the main-set paths lose F: F per cell (gross, all sinks strong); "
                 "arrows: outflow by face in "
                 f"m³/d, width by share of the cell's outflow{note}", fontsize=6.8, x=0.01,
                 ha="left")
    return save(fig, "fig3_worked_cells")


# ---------------------------------------------------------------- Fig. 4: gap against distance


def distance_figure(table: pd.DataFrame) -> Path:
    """Fig. 4: share of the start cells in each agreement class by distance to the nearest
    stream cell and to the nearest priority well."""
    nfig.paper_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), layout="constrained")
    titles = {"stream": "nearest SFR reach cell", "well": "nearest priority well"}
    for ax, (to, label) in zip(axes, titles.items()):
        part = table[table["to"] == to]
        x = np.arange(len(part))
        bottom = np.zeros(len(part))
        for code, (lab, color) in CLASSES.items():
            share = part[f"share_{code}"].fillna(0).to_numpy()
            ax.bar(x, share, bottom=bottom, color=color, width=0.78, edgecolor=SURFACE,
                   linewidth=0.8, label=lab)
            bottom += share
        n = part[[f"cells_{c}" for c in CLASSES]].sum(axis=1).to_numpy()
        for xx, nn in zip(x, n):
            ax.text(xx, 1.01, f"{nn}", ha="center", va="bottom", fontsize=6)
        ax.set_xticks(x, part["bin_m"], fontsize=6.3)
        ax.set_xlabel(f"plan distance of the start cell to the {label} (m)", fontsize=7)
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("share of the classified start cells", fontsize=7)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle("Agreement class by distance (numbers: classified start cells per bin; "
                 "F gross, all sinks strong)", fontsize=7, x=0.01, ha="left")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=6.5)
    return save(fig, "fig4_gap_against_distance")


# ---------------------------------------------------------------- Fig. 5: path budgets


def particle_ends(node0: int, ends_file: Path = MANY_ENDS) -> str:
    """Return where the 27 particles of a start cell end, as 'n to <well>' counts."""
    data = np.load(ends_file)
    row = np.flatnonzero(data["node0"] == node0)
    assert len(row) == 1, f"start cell {node0} not in {ends_file}"
    end = data["cell"][row[0]].ravel()  # 0-based, -1 not tracked
    names = {v: well_label(k) for k, v in wf.PRIORITY_WELLS.items()} | {-1: "not tracked"}
    counts = pd.Series([names.get(int(e), "other") for e in end]).value_counts()
    return ", ".join(f"{n} to {w}" for w, n in counts.items())


def deficit_by_position(budgets: dict, bins: tuple = POSITION_BINS) -> pd.DataFrame:
    """Return the share of the summed F deficit of all paths made per distance (in cells along
    the path) before the well, and its split by direction."""
    table = pd.concat([t.assign(before=len(t) - t["k"]) for t in budgets.values()])
    table["bin"] = pd.cut(table["before"], bins, labels=POSITION_LABELS)
    total = table["deficit"].sum()
    out = table.groupby("bin", observed=False)[[f"deficit_{d}" for d in DEFICIT_PARTS]].sum()
    out = out / total
    out["all"] = out.sum(axis=1)
    return out.reset_index()


def unfolded_section(ax: plt.Axes, path: np.ndarray, f: np.ndarray, tracks: pd.DataFrame,
                     pid: int, grb, shape: tuple, title: str) -> None:
    """Cell-by-cell section along a path: slot k shows the layers of the column of path cell k
    coloured by F, the path cell outlined, and the particle's elevation as it leaves each cell."""
    nlay, nrow, ncol = shape
    bot = np.asarray(grb.bot).reshape(nlay, nrow, ncol)
    tops = np.concatenate([np.asarray(grb.top).reshape(1, nrow, ncol), bot[:-1]], axis=0)
    idomain = np.asarray(grb.idomain).reshape(nlay, nrow, ncol)
    polys, colors = [], []
    for k, cell in enumerate(path):
        _, i, j = (int(v) for v in node_klij(cell, shape))
        for kk in range(nlay):
            if idomain[kk, i, j] > 0:
                node = (kk * nrow + i) * ncol + j
                polys.append([(k, bot[kk, i, j]), (k + 1, bot[kk, i, j]),
                              (k + 1, tops[kk, i, j]), (k, tops[kk, i, j])])
                colors.append(f_color(f[node]))
    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors=SURFACE,
                                     linewidths=0.2, zorder=1))
    for k, cell in enumerate(path):
        kk, i, j = (int(v) for v in node_klij(cell, shape))
        ax.add_patch(Rectangle((k, bot[kk, i, j]), 1, tops[kk, i, j] - bot[kk, i, j],
                               facecolor="none", edgecolor=INK, lw=0.6, zorder=3))
    rec = tracks[tracks["pid"] == pid]
    z = rec["z"].to_numpy()
    ax.plot(np.arange(len(z))[: len(path) + 1].clip(max=len(path)), z[: len(path) + 1],
            color=PATH_COLORS["published"], lw=1.0, zorder=4, path_effects=HALO)
    zs = np.array([pt[1] for poly in polys for pt in poly])
    ax.set_xlim(0, len(path))
    ax.set_ylim(zs.min(), zs.max() + 2)
    ax.set_xlabel("cell along the path (start = 0)", fontsize=6.3)
    ax.set_ylabel("elevation (m)", fontsize=6.3)
    ax.tick_params(labelsize=6)
    ax.set_title(title, loc="left", fontsize=6.3)


def deficit_profile(ax: plt.Axes, table: pd.DataFrame, title: str) -> None:
    """F of each path cell, the share of its outflow into the next path cell and the F
    deficit made in it, stacked by direction."""
    x = table["k"].to_numpy() + 0.5
    bottom_pos, bottom_neg = np.zeros(len(x)), np.zeros(len(x))
    for part in DEFICIT_PARTS:
        v = table[f"deficit_{part}"].to_numpy()
        base = np.where(v >= 0, bottom_pos, bottom_neg)
        ax.bar(x, v, bottom=base, width=0.85, color=DEFICIT_COLORS[part],
               label=f"loss: {DEFICIT_LABELS[part]}",
               linewidth=0)
        bottom_pos += np.clip(v, 0, None)
        bottom_neg += np.clip(v, None, 0)
    xf = np.r_[x, x[-1] + 1]
    ax.plot(xf, np.r_[table["F"], table["F_next"].iloc[-1]], color=INK, lw=1.0, marker="o",
            ms=1.8, label="F of the path cell")
    ax.plot(x, table["stay"], color=MUTED, lw=0.7, ls=(0, (2, 1.2)),
            label="share of outflow into the next path cell")
    ax.set_xlim(0, len(x) + 1)
    ax.set_ylim(min(-0.05, bottom_neg.min() - 0.02), 1.05)
    ax.axhline(0, color=MUTED, lw=0.4)
    ax.set_xlabel("cell along the path (start = 0)", fontsize=6.3)
    ax.set_ylabel("F, share, loss", fontsize=6.3)
    ax.tick_params(labelsize=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title(title, loc="left", fontsize=6.3)


def path_plan(ax: plt.Axes, path: np.ndarray, table: pd.DataFrame, f: np.ndarray,
              f_top: np.ndarray, tracks: pd.DataFrame, pid: int, cells: pd.DataFrame,
              streams: dict, shape: tuple, title: str) -> None:
    """Plan of a path: F of the uppermost cells (faint), the path cells coloured by their own
    F, the particle's track and the three cells that make most of the deficit (numbered)."""
    nrow, ncol = shape[1:]
    _, i, j = node_klij(path, shape)
    x, y = km(i, j, nrow)
    pad = 0.3
    size = max(np.ptp(x), np.ptp(y)) + 2 * pad
    xm, ym = 0.5 * (x.min() + x.max()), 0.5 * (y.min() + y.max())
    x0, x1, y0, y1 = xm - size / 2, xm + size / 2, ym - size / 2, ym + size / 2
    c = nfig.nf.CELL_KM
    window = (max(int(nrow - y1 / c), 0), min(int(nrow - y0 / c), nrow - 1),
              max(int(x0 / c), 0), min(int(x1 / c), ncol - 1))
    cmap, norm = nfig.f_classes()
    ax.imshow(f_top[window[0] : window[1] + 1, window[2] : window[3] + 1], cmap=cmap, norm=norm,
              extent=nfig.window_extent(window, nrow), interpolation="nearest", alpha=0.35)
    draw_streams(ax, streams, lw=0.6, buried_ms=1.4)
    draw_wells(ax, cells, shape, window, label=False)
    for xx, yy, node in zip(x, y, path):
        ax.add_patch(Rectangle((xx - c / 2, yy - c / 2), c, c, facecolor=f_color(f[node]),
                               edgecolor=INK, lw=0.4, zorder=5))
    rec = tracks[tracks["pid"] == pid]
    ax.plot(rec["x"] / 1000, rec["y"] / 1000, color=PATH_COLORS["published"], lw=0.8, zorder=6,
            path_effects=HALO)
    top3 = table.sort_values("deficit", ascending=False).head(3)
    for rank, cell in enumerate(top3["cell"], 1):
        _, ci, cj = node_klij(cell, shape)
        cx, cy = km(ci, cj, nrow)
        ax.plot(cx, cy, "o", ms=7, mfc="none", mec=RED, mew=1.0, zorder=7)
        ax.annotate(str(rank), (float(cx), float(cy)), xytext=(5, 5), textcoords="offset points",
                    fontsize=6.5, color=RED, fontweight="bold", path_effects=HALO, zorder=8)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    bar = 0.2 if size < 1.5 else 0.5
    ax.plot([x0 + 0.06 * size, x0 + 0.06 * size + bar], [y0 + 0.05 * size] * 2, color=INK,
            lw=1.2, zorder=9)
    ax.text(x0 + 0.06 * size + bar / 2, y0 + 0.07 * size, f"{bar * 1000:.0f} m", ha="center",
            fontsize=5.5, path_effects=HALO, zorder=9)
    ax.set_title(title, loc="left", fontsize=6.3)


def path_figure(
    paths: dict, budgets: dict, summary: pd.DataFrame, position: pd.DataFrame,
    visits: pd.DataFrame, particles: pd.DataFrame, p: np.ndarray | None, f: np.ndarray,
    f_top: np.ndarray, tracks: pd.DataFrame, cells: pd.DataFrame, streams: dict, grb,
    shape: tuple,
) -> Path:
    """Fig. 5: three published paths from start cells away from streams with P >= 0.9 but
    F < 0.5, cell by cell to the well (plan, section, F and losses), and the losses of all such
    paths by direction and by position before the well."""
    nfig.paper_style()
    fig = plt.figure(figsize=(7.4, 9.4), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(3.0, 1.0))
    axes = top.subplots(len(paths), 3, width_ratios=(1.0, 1.55, 1.55))
    letters = iter("abcdefghijklmn")
    for row, (name, pid) in enumerate(paths.items()):
        path = path_cells(visits, pid)
        table = budgets[pid]
        s = summary.set_index("pid").loc[pid]
        k, i, j = (int(v) for v in node_klij(path[0], shape))
        node0 = int(particles.at[pid, "node0"])
        p_text = f", P {p[node0]:.2f}" if p is not None and node0 < len(p) else ""
        path_plan(axes[row, 0], path, table, f, f_top, tracks, pid, cells, streams, shape,
                  f"({next(letters)}) {name}: start L{k + 1} r{i + 1} c{j + 1}\n"
                  f"F {s['F_start']:.2f}{p_text}; 27 particles:\n{particle_ends(node0)}")
        unfolded_section(axes[row, 1], path, f, tracks, pid, grb, shape,
                         f"({next(letters)}) section cell by cell: {len(path)} cells in layers "
                         f"{', '.join(s['layers'])}\n(outlined: path cell; orange: particle)")
        parts = ", ".join(f"{d} {s[f'share_{d}']:.2f}" for d in DEFICIT_PARTS
                          if abs(s[f"share_{d}"]) >= 0.005)
        deficit_profile(axes[row, 2], table,
                        f"({next(letters)}) loss of F {s['deficit']:.2f}: {parts}\n80 % in "
                        f"{s['cells_80']} cells, largest cell {s['max_cell_share']:.2f}; "
                        f"stay product {s['stay_product']:.1e}")
    handles, labels = axes[0, 2].get_legend_handles_labels()
    top.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=6.2)
    ax_dir, ax_pos, ax_n = bottom.subplots(1, 3, width_ratios=(1.0, 1.4, 1.0))
    groups = {"all": summary, "U wells": summary[summary["region"] == "NE"],
              "SV wells": summary[summary["region"] != "NE"]}
    y = np.arange(len(groups))[::-1]
    for yy, (g, part) in zip(y, groups.items()):
        weights = part["deficit"]
        left = 0.0
        for d in DEFICIT_PARTS:
            v = float((part[f"share_{d}"] * weights).sum() / weights.sum())
            ax_dir.barh(yy, v, left=left if v >= 0 else 0, color=DEFICIT_COLORS[d], height=0.6)
            if v > 0.06:
                ax_dir.text(left + v / 2, yy, f"{v:.2f}", ha="center", va="center", fontsize=5.5,
                            color=SURFACE)
            left += max(v, 0)
    ax_dir.set_yticks(y, [f"{g} ({len(part)})" for g, part in groups.items()], fontsize=6.3)
    ax_dir.set_xlim(0, 1.02)
    ax_dir.set_title(f"({next(letters)}) share of the F loss by direction", loc="left", fontsize=6.5)
    ax_dir.tick_params(labelsize=6)
    xb = np.arange(len(position))
    base = np.zeros(len(xb))
    for d in DEFICIT_PARTS:
        v = position[f"deficit_{d}"].to_numpy()
        ax_pos.bar(xb, v, bottom=base, color=DEFICIT_COLORS[d], width=0.75)
        base += v
    for xx, v in zip(xb, position["all"]):
        ax_pos.text(xx, v + 0.005, f"{v:.2f}", ha="center", fontsize=5.5)
    ax_pos.set_xticks(xb, position["bin"].astype(str), fontsize=6)
    ax_pos.set_xlabel("cells before the well cell", fontsize=6.3)
    ax_pos.set_title(f"({next(letters)}) share of the summed F loss by position", loc="left",
                     fontsize=6.5)
    ax_pos.tick_params(labelsize=6)
    counts = summary["cells_80"].value_counts().sort_index()
    ax_n.bar(counts.index, counts.to_numpy(), color=MUTED, width=0.8)
    ax_n.set_xlabel("path cells making 80 % of the loss", fontsize=6.3)
    ax_n.set_ylabel("paths", fontsize=6.3)
    ax_n.set_title(f"({next(letters)}) paths: median {summary['cells'].median():.0f} cells",
                   loc="left", fontsize=6.5)
    ax_n.tick_params(labelsize=6)
    for ax in (ax_dir, ax_pos, ax_n):
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle(f"Main disagreement: {len(summary)} published start cells with no stream in or "
                 f"next to them (≥ {STREAM_MIN_M:.0f} m), P ≥ {P_MIN} but F < {F_HIGH}.\nLoss "
                 "of a path cell = sum over its outflows not into the next path cell of share × "
                 "(F of the next path cell − F of that neighbour);\nsummed along the path it "
                 "equals F of the well cell − F of the start cell. Under a stream: absorbing SFR "
                 "cell on the path, whose flow sits on the top face for the particles.",
                 fontsize=6.3, x=0.01, ha="left")
    return save(fig, "fig5_path_budgets")


# ---------------------------------------------------------------- main


def main(ws: Path = OUT / "optimal", mp_dir: Path = wf.MP7_OUT, out: Path = DIAG_DIR
         ) -> list[Path]:
    """Trace, retrack the disputed particles (once), write the tables and draw Figs 1 to 5."""
    step = gs.read_step(ws, boundnames=True)
    idomain = wf.grid_idomain(ws)
    shape = idomain.shape
    buried = ~mc.top_face_open(idomain).ravel()
    results = trace_all(step, buried)
    cells = cell_sinks(step, buried)
    edges = gs.flow_edges(step)
    budget = gs.cell_budget(step, edges)
    endpoints = wf.read_endpoints(mp_dir, columns=mc.START_COLUMNS)
    particles = particle_table(endpoints, results, cells, shape)
    f = results["gross_strong"].fraction_through["priority"]
    tracks = disputed_tracks(particles)
    visits = path_visits(tracks)
    splits = split_cells(particles, visits, f, cells, edges, budget, shape)
    disputed = set(np.flatnonzero(particles["set"] != ""))
    assert set(splits["pid"]) == disputed, "a disputed particle has no split cell"
    counts = fate_counts(particles, cells, endpoints)
    out.mkdir(parents=True, exist_ok=True)
    end_agreement(particles, tracks).to_csv(out / "retrack_end_agreement.csv", index=False)
    counts.to_csv(out / "fates_A.csv", index=False)
    mechanism_table(splits).to_csv(out / "mechanisms.csv", index=False)
    split_concentration(splits).to_csv(out / "split_concentration.csv", index=False)
    splits.to_csv(out / "split_cells.csv", index=False)
    b = particles[particles["set"] == "B"]
    b.filter(like="share ").mean().rename("mean_share").to_csv(out / "sink_shares_B.csv")
    distances = distance_table(particles, cells, shape)
    distances.to_csv(out / "gap_against_distance.csv", index=False)
    windows = cluster_windows(particles, shape)
    streams = stream_segments(ws, cells, shape)
    active = (idomain > 0).any(axis=0)
    f_top = nfig.nf.top_map(f, nfig.nf.top_active(idomain))
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{wf.MODEL}.dis.grb")
    head = flopy.utils.HeadFile(ws / f"{wf.MODEL}.hds").get_data().ravel()
    p = load_p()
    main_pids = main_population(particles)
    summary, budgets = path_summary(main_pids, visits, f, edges, budget, particles, shape)
    position = deficit_by_position(budgets)
    summary.to_csv(out / "path_budgets.csv", index=False)
    position.to_csv(out / "path_loss_by_position.csv", index=False)
    pd.concat(budgets, names=["pid", "row"]).to_csv(out / "path_budget_cells.csv")
    paths = pick_paths(summary)
    examples = loss_cells(paths, budgets, splits, visits)
    pd.DataFrame({k: {"cell": v["cell"], "note": v["note"]} for k, v in examples.items()}
                 ).T.to_csv(out / "worked_cells.csv")
    return [
        agreement_map(particles, cells, streams, windows, active, shape),
        fate_figure(particles, counts, splits, cells, streams, windows, active, shape),
        worked_cells(examples, particles, f, f_top, p, edges, budget, cells, tracks, streams,
                     idomain, grb, head),
        path_figure(paths, budgets, summary, position, visits, particles, p, f, f_top, tracks,
                    cells, streams, grb, shape),
        distance_figure(distances),
    ]


if __name__ == "__main__":
    for path in main():
        print(path)
