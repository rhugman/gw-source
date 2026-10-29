"""Neversink case study: many particles per start cell against the full-mixing fraction F.

The published contributing area comes from one MODPATH 7 particle at the centre of each start
cell (the uppermost active cells of the three regions, 122,021 cells). Full mixing gives each
cell a fraction F, the share of the water leaving the cell that reaches the priority wells.
Here every start cell gets N_SPLIT^3 = 27 PRT particles spread evenly through it (local x, y
and z at 1/6, 1/2 and 5/6), with the published conventions of mp7_convention.py: porosity 0.3,
weak sinks stop particles (STOP_AT_WEAK_SINK), RCH and SFR flows on the top face where it is
open (IFLOWFACE -1), dry start cells draped to the first wet cell below, EXTEND_TRACKING, no
stop zone or time. The middle particle of the 27 is the published centre particle.

P of a start cell is the share of its 27 particles that end in a priority well cell. P is
compared cell by cell with F of the release cell (the draped cell for dry starts) from the
gross trace, and from the gross trace with every sink strong (strong_sinks="all"), which like
the particles stops all water at every sink cell. If P matches F, the gap between F and the
published area comes from releasing one particle per cell; if not, from full mixing itself.

The particles run in N_SPLIT PRT simulations (one per local z level) side by side. Only the
termination records are written; the end points are kept in OUT_DIR / RUN_DIR / endpoints.npz,
the PRT workspaces and the IFLOWFACE model copy are deleted once read.

Needs TraceConfig.strong_sinks (gwsource, branch feature/strong-sinks). Run after workflow.py:

    python studies/neversink/prt_many_particles.py
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mp7_convention as mp7  # noqa: E402
import strong_sinks as ss  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402

# The study output folder (resolved, so that a linked output/ folder is followed).
OUT_DIR = (wf.OUT / "optimal").resolve().parent
RUN_DIR = "prt_many_particles"
FIG_DIR = OUT_DIR / "diagnostics"
N_SPLIT = 3  # particles per cell along each local axis
CENTRE = (N_SPLIT**3) // 2  # index of the centre particle in a cell's (z, y, x) order
CLUSTERS = {
    "priority": tuple(wf.PRIORITY_WELLS),
    "U": tuple(w for w in wf.PRIORITY_WELLS if w.startswith("U")),
    "SV": tuple(w for w in wf.PRIORITY_WELLS if w.startswith("SV")),
}
F_CASES = {"gross": ("gross", ()), "gross_strong": ("gross", "all")}
DISTANCE_BINS = (0.0, 50.0, 100.0, 200.0, 400.0, 800.0, np.inf)  # plan distance to SFR [m]
STREAM_CLASSES = ("gaining stream", "buried stream", "neither")
AREA_THRESHOLD = 0.5
# Off-centre particles in a cell wet by a film (saturation 2e-14 to 1e-13 here, 8 start cells)
# make MF6 PRT abort (SIGILL) at release; such starts are left out (growth_mechanisms.FILM_SAT).
FILM_SAT = 1e-10
ACTIVE = 0.01  # F or P above this: a start cell that sends water to the wells


# ---------------------------------------------------------------- particles


def iflowface_model(ws: Path, exe: Path) -> float:
    """Build and run the calibrated model with RCH and SFR on the open top face; return seconds."""
    mp7.prepare_iflowface_model(ws)
    return wf.run_mf6(ws, exe)


def release_starts(ws: Path, min_sat: float = FILM_SAT) -> tuple[pd.DataFrame, np.ndarray]:
    """Return the published starts with the draped release cell, and which can be tracked."""
    starts = wf.read_endpoints(columns=mp7.START_COLUMNS)
    idomain = wf.grid_idomain(ws)
    sat = mp7.cell_saturation(ws / f"{wf.MODEL}.cbc", idomain.size)
    draped = mp7.drape_dry_starts(starts, idomain, sat)
    starts = starts.assign(node_release=draped["node0"].to_numpy())
    return starts, mp7.trackable(draped, sat, min_sat)


def spread_points(
    starts: pd.DataFrame, grid: gs.prt.PrtGrid, n: int = N_SPLIT
) -> dict[str, np.ndarray]:
    """Return x, y, local z and cell of n^3 points per start, shaped (start, z, y, x)."""
    local = (np.arange(n) + 0.5) / n
    node = starts["node_release"].to_numpy()
    poly = np.stack([grid.polygons[c] for c in node % grid.ncpl])
    x0, x1 = poly[:, :, 0].min(axis=1), poly[:, :, 0].max(axis=1)
    y0, y1 = poly[:, :, 1].min(axis=1), poly[:, :, 1].max(axis=1)
    assert np.allclose(0.5 * (x0 + x1), starts["x0"]), "start x is not the cell centre"
    assert np.allclose(0.5 * (y0 + y1), starts["y0"]), "start y is not the cell centre"
    shape = (len(node), n, n, n)
    lz, ly, lx = np.meshgrid(local, local, local, indexing="ij")
    return {
        "cell": np.broadcast_to(node[:, None, None, None], shape),
        "x": x0[:, None, None, None] + lx[None] * (x1 - x0)[:, None, None, None],
        "y": y0[:, None, None, None] + ly[None] * (y1 - y0)[:, None, None, None],
        "z": np.broadcast_to(lz[None], shape),
    }


def level_release(points: dict[str, np.ndarray], level: int) -> gs.prt.ReleasePoints:
    """Return the release points of one local z level, in (start, y, x) order."""
    cell = points["cell"][:, level].ravel()
    return gs.prt.ReleasePoints(
        cell=cell,
        x=points["x"][:, level].ravel(),
        y=points["y"][:, level].ravel(),
        z=points["z"][:, level].ravel(),
        weight=np.ones(len(cell)),
        package=np.full(len(cell), "", dtype=object),
    )


def write_levels(
    run_dir: Path, gwf_ws: Path, points: dict[str, np.ndarray], exe: Path
) -> list[Path]:
    """Write one PRT simulation per local z level (published conventions); return their folders."""
    grid = gs.prt.load_prt_grid(gwf_ws, wf.MODEL, "DIS")
    config = gs.prt.PrtConfig(porosity=wf.MP7_POROSITY, exit_solve_tolerance=1e-5)
    folders = []
    for level in range(points["z"].shape[1]):
        prt_ws = run_dir / f"z{level}"
        gs.prt.write_prt(
            prt_ws, gwf_ws, grid, level_release(points, level), config, exe, wf.MODEL,
            budget_file=gwf_ws / f"{wf.MODEL}.cbc", stop_at_weak_sink=True,
            track_release=False, track_exit=False, clear_ws=True,
        )
        folders.append(prt_ws)
    return folders


def run_side_by_side(folders: list[Path], exe: Path) -> dict[str, float]:
    """Run the PRT simulations in parallel processes; return wall and per-run seconds."""
    t0 = time.perf_counter()
    procs = [subprocess.Popen([str(exe)], cwd=f, stdout=subprocess.DEVNULL) for f in folders]
    seconds = {}
    for folder, proc in zip(folders, procs):
        assert proc.wait() == 0, f"PRT failed in {folder}"
        seconds[folder.name] = time.perf_counter() - t0
    assert all("Normal termination" in (f / "mfsim.lst").read_text()[-3000:] for f in folders)
    return {"wall": time.perf_counter() - t0, **seconds}


def read_levels(folders: list[Path], n_starts: int, keep: np.ndarray) -> dict[str, np.ndarray]:
    """Return end cell, status and time per particle, shaped (start, z, y, x); -1 = not tracked."""
    n = N_SPLIT
    ends = {
        "cell": np.full((n_starts, n, n * n), -1, dtype=np.int32),
        "status": np.full((n_starts, n, n * n), -1, dtype=np.int8),
        "time": np.full((n_starts, n, n * n), np.nan, dtype=np.float32),
    }
    for level, folder in enumerate(folders):
        tracks = gs.prt.read_tracks(folder / "prt.trk.csv")
        run = gs.prt.endpoints(tracks, int(keep.sum()) * n * n)
        for key, values in run.items():
            ends[key][keep, level] = values.reshape(-1, n * n)
    return {key: v.reshape(n_starts, n, n, n) for key, v in ends.items()}


def run_particles(out: Path = OUT_DIR, exe: Path | None = None) -> None:
    """Build the flow field, run the 27 particles per start cell and save their end points."""
    exe = wf.mf6_exe() if exe is None else exe
    run_dir = out / RUN_DIR
    gwf_ws = out / "optimal_iflowface"
    log = {"mf6_seconds": iflowface_model(gwf_ws, exe)}
    starts, keep = release_starts(gwf_ws)
    grid = gs.prt.load_prt_grid(gwf_ws, wf.MODEL, "DIS")
    points = spread_points(starts, grid)
    t0 = time.perf_counter()
    folders = write_levels(run_dir, gwf_ws, {k: v[keep] for k, v in points.items()}, exe)
    log["write_seconds"] = time.perf_counter() - t0
    log.update({f"prt_seconds_{k}": v for k, v in run_side_by_side(folders, exe).items()})
    ends = read_levels(folders, len(starts), keep)
    np.savez_compressed(
        run_dir / "endpoints.npz", node0=starts["node0"].to_numpy(),
        node_release=starts["node_release"].to_numpy(), **ends,
    )
    log.update({"starts": len(starts), "tracked_starts": int(keep.sum()),
                "particles": int(keep.sum()) * N_SPLIT**3, "dry_starts_draped":
                int(np.sum(starts["node0"] != starts["node_release"]))})
    (run_dir / "run_log.json").write_text(json.dumps(log, indent=1))
    for folder in folders:
        shutil.rmtree(folder)
    shutil.rmtree(gwf_ws)


# ---------------------------------------------------------------- cell table


def cluster_groups(step: gs.FlowStep, clusters: dict = CLUSTERS) -> dict[str, gs.Selection]:
    """Return one WEL destination group per cluster of priority wells."""
    return {name: gs.select(step, package="WEL", boundnames=list(w)) for name, w in clusters.items()}


def cell_sinks(step: gs.FlowStep) -> np.ndarray:
    """Return, per cell, the packages with a sink term there joined by '+' ('' if none)."""
    names = np.array([p.name for p in step.packages], dtype=object)
    leaving = step.term_flow < 0
    frame = pd.DataFrame({"cell": step.term_cell[leaving], "pkg": names[step.term_package[leaving]]})
    joined = frame.drop_duplicates().groupby("cell")["pkg"].agg(lambda p: "+".join(sorted(p)))
    out = np.full(step.n_cells, "", dtype=object)
    out[joined.index.to_numpy()] = joined.to_numpy()
    return out


def stream_class(ws: Path, step: gs.FlowStep, cells: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return per cell the stream class and the plan distance [m] to the nearest SFR reach.

    gaining stream: the cell or a face neighbour holds an SFR reach on the open top face that
    takes water from the aquifer; buried stream: the cell or a neighbour holds a reach below an
    active cell (distributed, a weak sink where it gains); neither: no reach in or next to it.
    A cell next to both is put in the first of these classes.
    """
    idomain = wf.grid_idomain(ws)
    nlay, nrow, ncol = idomain.shape
    reaches = mp7.sfr_reach_cells(ws / "neversink_packagedata.dat")
    on_top = mp7.top_face_open(idomain)[tuple(reaches.T)]
    reach_node = np.ravel_multi_index(tuple(reaches.T), idomain.shape)
    sfr = np.array([p.name.startswith("SFR") for p in step.packages])[step.term_package]
    exchange = np.bincount(step.term_cell[sfr], step.term_flow[sfr], minlength=step.n_cells)
    gaining = np.zeros(idomain.size, dtype=bool)
    gaining[reach_node[on_top & (exchange[reach_node] < 0)]] = True
    buried = np.zeros(idomain.size, dtype=bool)
    buried[reach_node[~on_top]] = True
    k, r, c = np.unravel_index(cells, idomain.shape)
    near_gaining, near_buried = gaining[cells].copy(), buried[cells].copy()
    for dk, dr, dc in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        kk, rr, cc = k + dk, r + dr, c + dc
        inside = (kk >= 0) & (kk < nlay) & (rr >= 0) & (rr < nrow) & (cc >= 0) & (cc < ncol)
        nb = np.ravel_multi_index((kk[inside], rr[inside], cc[inside]), idomain.shape)
        near_gaining[inside] |= gaining[nb]
        near_buried[inside] |= buried[nb]
    label = np.where(near_gaining, STREAM_CLASSES[0],
                     np.where(near_buried, STREAM_CLASSES[1], STREAM_CLASSES[2]))
    xy = np.column_stack([c, r]) + 0.5
    tree = cKDTree(np.unique(reaches[:, 1:][:, ::-1], axis=0) + 0.5)
    cell_size = float(np.ravel(gs.prt.load_prt_grid(ws, wf.MODEL, "DIS").dis_kwargs["delr"])[0])
    return label, tree.query(xy)[0] * cell_size


def particle_shares(ends: dict, clusters: dict = CLUSTERS) -> dict[str, np.ndarray]:
    """Return per start the share of its particles ending in each cluster's well cells."""
    cell = ends["cell"].reshape(len(ends["cell"]), -1)
    tracked = cell[:, 0] >= 0
    shares = {}
    for name, wells in clusters.items():
        hit = np.isin(cell, [wf.PRIORITY_WELLS[w] for w in wells])
        shares[name] = np.where(tracked, hit.mean(axis=1), np.nan)
        shares[f"{name}_centre"] = np.where(tracked, hit[:, CENTRE], np.nan)
    return shares


def cell_table(ws: Path, ends: dict, endpoints: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return the per-start table (F, P, centre, published, stream class) and the trace times."""
    step = gs.read_step(ws, boundnames=True)
    results, seconds = ss.trace_cases(step, cluster_groups(step), F_CASES)
    node = ends["node_release"]
    assert np.array_equal(ends["node0"], endpoints["node0"].to_numpy()), "start order differs"
    label, distance = stream_class(ws, step, node)
    table = pd.DataFrame({
        "node0": ends["node0"], "node": node, "region": endpoints["region"].to_numpy(),
        "stream_class": label, "sfr_distance_m": distance, "cell_sinks": cell_sinks(step)[node],
        "mp7_status": endpoints["status"].to_numpy(),
    })
    shares = particle_shares(ends)
    for name, wells in CLUSTERS.items():
        nodes = [wf.PRIORITY_WELLS[w] for w in wells]
        table[f"published_{name}"] = wf.mp7_mask(endpoints, nodes)
        table[f"P_{name}"] = shares[name]
        table[f"centre_{name}"] = shares[f"{name}_centre"]
        for case, result in results.items():
            table[f"F_{case}_{name}"] = result.fraction_through[name][node]
    return table, seconds


def end_table(ends: dict, step: gs.FlowStep) -> pd.DataFrame:
    """Return the particles by PRT status and the sink packages of the end cell."""
    cell = ends["cell"].ravel()
    tracked = cell >= 0
    sinks = cell_sinks(step)[cell[tracked]]
    well = np.isin(cell[tracked], list(wf.PRIORITY_WELLS.values()))
    frame = pd.DataFrame({"status": ends["status"].ravel()[tracked], "end_cell_sinks": sinks,
                          "priority_well": well})
    table = frame.value_counts().rename("particles").reset_index()
    table["share"] = table["particles"] / tracked.sum()
    return table.sort_values("particles", ascending=False)


# ---------------------------------------------------------------- comparison


def agreement_row(f: np.ndarray, p: np.ndarray, published: np.ndarray, t: float) -> dict:
    """Return RMSE, bias (mean F - P), correlation and the areas above t against the published."""
    d = f - p
    return {
        "cells": len(f),
        "rmse": float(np.sqrt(np.mean(d**2))),
        "bias": float(np.mean(d)),
        "corr": float(np.corrcoef(f, p)[0, 1]),
        "published_cells": int(published.sum()),
        f"P>{t}_cells": int(np.sum(p > t)),
        f"F>{t}_cells": int(np.sum(f > t)),
        f"coverage_P>{t}": float(np.mean(p[published] > t)),
        f"coverage_F>{t}": float(np.mean(f[published] > t)),
        f"jaccard_P_F>{t}": wf.jaccard(p > t, f > t),
        f"jaccard_P_published>{t}": wf.jaccard(p > t, published),
        f"jaccard_F_published>{t}": wf.jaccard(f > t, published),
    }


def metrics(
    table: pd.DataFrame, t: float = AREA_THRESHOLD, active: float = ACTIVE
) -> pd.DataFrame:
    """Return agreement rows per cluster, F case, particle measure (P or centre) and cell set.

    Cell sets: all tracked start cells, and the active ones, where F (either case) or P of the
    cluster exceeds active (most start cells are far from the wells, F = P = 0 there).
    """
    rows = []
    tracked = table[table["P_priority"].notna()]
    for name in CLUSTERS:
        values = np.column_stack([tracked[f"F_{c}_{name}"] for c in F_CASES] + [tracked[f"P_{name}"]])
        cell_sets = {"all": np.ones(len(tracked), dtype=bool),
                     f"F or P > {active}": (values > active).any(axis=1)}
        for cells, on in cell_sets.items():
            published = tracked[f"published_{name}"].to_numpy()[on]
            for case in F_CASES:
                f = tracked[f"F_{case}_{name}"].to_numpy()[on]
                for measure in ("P", "centre"):
                    p = tracked[f"{measure}_{name}"].to_numpy()[on]
                    rows.append({"group": name, "cell_set": cells, "F": case,
                                 "particles": measure, **agreement_row(f, p, published, t)})
    return pd.DataFrame(rows)


def sanity_check(table: pd.DataFrame) -> dict:
    """Return the centre-particle area against the published area (priority group)."""
    published = table["published_priority"].to_numpy()
    centre = table["centre_priority"].to_numpy() > 0.5
    return {"published_cells": int(published.sum()), "centre_cells": int(centre.sum()),
            "both": int(np.sum(published & centre)), "jaccard": wf.jaccard(published, centre)}


def class_metrics(
    table: pd.DataFrame, case: str = "gross_strong", bins: tuple = DISTANCE_BINS
) -> pd.DataFrame:
    """Return the agreement of P with F (priority group) per stream class, SFR distance class
    and published particle status, with each class's share of the squared error."""
    tracked = table[table["P_priority"].notna()].copy()
    tracked["d"] = tracked[f"F_{case}_priority"] - tracked["P_priority"]
    tracked["sfr_distance"] = pd.cut(tracked["sfr_distance_m"], bins, right=False).astype(str)
    total = np.sum(tracked["d"] ** 2)
    frames = []
    for column in ("stream_class", "sfr_distance", "mp7_status"):
        g = tracked.groupby(column)["d"]
        frames.append(pd.DataFrame({
            "by": column, "class": g.size().index.astype(str), "cells": g.size().to_numpy(),
            "rmse": np.sqrt(g.apply(lambda d: np.mean(d**2))).to_numpy(),
            "bias": g.mean().to_numpy(),
            "share_of_squared_error": (g.apply(lambda d: np.sum(d**2)) / total).to_numpy(),
            "cells_|F-P|>0.25": g.apply(lambda d: int(np.sum(np.abs(d) > 0.25))).to_numpy(),
        }))
    return pd.concat(frames, ignore_index=True)


def plot_scatter(table: pd.DataFrame, path: Path, group: str = "priority") -> None:
    """Hexbin of F (rows: gross, gross with strong sinks) against P, one column per stream class.

    Only cells where F or P exceeds 0.01 are binned (the rest sit at the origin); the count of
    the others is printed in each panel.
    """
    tracked = table[table[f"P_{group}"].notna()]
    rows = (("gross_strong", "F, gross, every sink strong"), ("gross", "F, gross"))
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.8), sharex=True, sharey=True,
                             layout="constrained")
    for i, (case, ylabel) in enumerate(rows):
        for j, label in enumerate(STREAM_CLASSES):
            ax = axes[i, j]
            sub = tracked[tracked["stream_class"] == label]
            f, p = sub[f"F_{case}_{group}"].to_numpy(), sub[f"P_{group}"].to_numpy()
            near_zero = (f <= 0.01) & (p <= 0.01)
            hb = ax.hexbin(p[~near_zero], f[~near_zero], gridsize=28, extent=(0, 1, 0, 1),
                           bins="log", mincnt=1, cmap="viridis", vmin=1, vmax=3000,
                           linewidths=0.2, edgecolors="face")
            ax.plot([0, 1], [0, 1], color="0.35", lw=0.8, ls="--")
            rmse = np.sqrt(np.mean((f - p) ** 2))
            ax.text(0.03, 0.97, f"{len(sub):,} cells\n{near_zero.sum():,} with F, P ≤ 0.01\n"
                    f"RMSE {rmse:.3f}", transform=ax.transAxes, va="top", fontsize=8,
                    color="0.15")
            ax.set_aspect("equal")
            if i == 0:
                ax.set_title(label.capitalize(), fontsize=10)
            if j == 0:
                ax.set_ylabel(ylabel)
            ax.grid(color="0.9", lw=0.5)
            ax.set_axisbelow(True)
    fig.supxlabel("P, share of the 27 particles of the cell that reach the wells", fontsize=10)
    fig.colorbar(hb, ax=axes, shrink=0.7, label="Start cells per hexagon")
    fig.suptitle("Priority wells: full-mixing F against the particle share P, by start cell",
                 fontsize=11)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def analyse(out: Path = OUT_DIR, ws: Path = wf.OUT / "optimal") -> None:
    """Compare P with F and write the tables and the figure."""
    run_dir = out / RUN_DIR
    ends = dict(np.load(run_dir / "endpoints.npz"))
    endpoints = wf.read_endpoints()
    table, seconds = cell_table(ws, ends, endpoints)
    table.to_csv(out / "prt_many_particles_cells.csv", index=False)
    metrics(table).to_csv(out / "prt_many_particles_metrics.csv", index=False)
    class_metrics(table).to_csv(out / "prt_many_particles_classes.csv", index=False)
    end_table(ends, gs.read_step(ws, boundnames=True)).to_csv(
        out / "prt_many_particles_ends.csv", index=False)
    check = {**sanity_check(table), **{f"trace_seconds_{k}": v for k, v in seconds.items()}}
    pd.DataFrame([check]).to_csv(out / "prt_many_particles_check.csv", index=False)
    FIG_DIR.mkdir(exist_ok=True)
    plot_scatter(table, FIG_DIR / "prt_many_particles_F_vs_P.png")


def main(run: bool = True, analyse_runs: bool = True) -> None:
    """Run the particles and compare them with F."""
    if run:
        run_particles()
    if analyse_runs:
        analyse()


if __name__ == "__main__":
    main()
