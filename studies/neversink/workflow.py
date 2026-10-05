"""Neversink/Rondout case study, stage 1: capture of the eight priority wells in the calibrated
(base) model, gwsource backward tracing against the published MODPATH 7 contributing areas.

The model is the USGS Neversink/Rondout MODFLOW 6 model (Fienen and others 2021; Corson-Dosch and
others 2021), public domain, from https://github.com/usgs/neversink_workflow. Its calibrated
("optimal") input and the MODPATH 7 endpoint files of that model are in the repository; a sparse
checkout of it goes in studies/neversink/external/ (git-ignored).

The published areas contributing recharge come from forward MODPATH 7 runs: one particle per
cell of the uppermost active layer in three regions (NE, S and W) around the well clusters, weak
sinks stopping particles, and a cell counts as contributing if its particle ends in one of the
eight priority wells. Here the same cells are given the backward capture fraction F of the cell
in which the particle starts, so the MODPATH mask and F > threshold can be compared cell by cell.

Run from anywhere with the project environment (MF6 from <repo>/bin):

    python studies/neversink/workflow.py

Edit the gates in __main__ to rerun parts. Model copies and tables go to
studies/neversink/output/ (git-ignored).
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

import flopy
import numpy as np
import pandas as pd

import gwsource as gs

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = HERE / "external" / "neversink_workflow"
MODEL_SRC = SOURCE / "neversink_optimal"
REF_OUT = SOURCE / "output" / "neversink_mf6_optimal_output"
MP7_OUT = SOURCE / "output" / "neversink_mp7_optimal_output"
OUT = HERE / "output"
FIG_DIR = REPO / "docs" / "figures"
BIN = REPO / "bin"

MODEL = "neversink"
MP7_REGIONS = ("NE", "S", "W")
# Priority wells: WEL boundnames and their 0-based MODPATH destination nodes
# (scripts/get_endpoints.py of the source repository).
PRIORITY_WELLS = {
    "SV_193": 1042614,
    "SV_227": 214382,
    "SV_407": 1041449,
    "SV_487": 344623,
    "U_917": 574351,
    "U__55": 562588,
    "U___7": 575587,
    "U___8": 574968,
}
THRESHOLDS = (0.0, 0.1, 0.5)
MP7_POROSITY = 0.3  # all layers, from the published MPBAS files
# The SFR network trace needs the GWF and SFR budgets to agree on the aquifer exchange to 1e-4
# of the largest reach flow; with the published 0.01 m criterion three reaches miss that.
TIGHT_DVCLOSE = (1e-4, 1e-6)
# PRT checks: (release_z, thin_weak_sinks); release_z None spreads the points over the cell volume
PRT_CASES = ((None, True), (None, False), (1.0, True), (0.5, True))
PRT_Z_LEVELS = 4


def mf6_exe(bin_dir: Path = BIN) -> Path:
    """Return the MF6 executable in bin_dir."""
    exe = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    assert exe.is_file(), "run scripts/setup_env.sh to fetch mf6"
    return exe


def prepare_model(ws: Path, src: Path = MODEL_SRC, dvclose: tuple | None = None) -> None:
    """Copy the calibrated MF6 input (not the MODPATH files) into a clean workspace.

    dvclose=(outer, inner) replaces the published head-change criteria (0.01 m, 1e-4 m).
    """
    assert src.is_dir(), f"no model input at {src}: see the module docstring"
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(src, ws, ignore=shutil.ignore_patterns("*.mp*"))
    update_ims(ws / "mfsim.ims", dvclose)
    for option in ("SAVE_SPECIFIC_DISCHARGE", "SAVE_SATURATION"):
        add_npf_option(ws / f"{MODEL}.npf", option)


def add_npf_option(npf_file: Path, option: str) -> None:
    """Add an option to the NPF OPTIONS block (PRT needs specific discharge and saturation)."""
    text = npf_file.read_text()
    assert "BEGIN options" in text, f"no options block in {npf_file}"
    if option not in text.upper():
        text = text.replace("BEGIN options", f"BEGIN options\n  {option}", 1)
    npf_file.write_text(text)


def update_ims(ims_file: Path, dvclose: tuple | None = None) -> None:
    """Rename the IMS keywords that MF6 6.2 accepted and current MF6 rejects.

    OUTER_HCLOSE and INNER_HCLOSE became OUTER_DVCLOSE and INNER_DVCLOSE (same meaning);
    OUTER_RCLOSEBND was already unused in MF6 6.2 and is dropped. dvclose=(outer, inner)
    also sets new values.
    """
    renamed = {"OUTER_HCLOSE": "OUTER_DVCLOSE", "INNER_HCLOSE": "INNER_DVCLOSE"}
    values = dict(zip(renamed.values(), dvclose)) if dvclose is not None else {}
    lines = []
    for line in ims_file.read_text().splitlines():
        words = line.split()
        key = words[0].upper() if words else ""
        if key == "OUTER_RCLOSEBND":
            continue
        if key in renamed:
            new_key = renamed[key]
            value = f"{values[new_key]:g}" if new_key in values else words[1]
            line = f"  {new_key}  {value}"
        lines.append(line)
    ims_file.write_text("\n".join(lines) + "\n")


def run_mf6(ws: Path, exe: Path) -> float:
    """Run MF6 in ws, assert normal termination and return the run time in seconds."""
    t0 = time.perf_counter()
    proc = subprocess.run([str(exe)], cwd=ws, capture_output=True, text=True)
    assert "Normal termination" in proc.stdout, f"MF6 failed in {ws}:\n{proc.stdout[-2000:]}"
    return time.perf_counter() - t0


def head_difference(ws: Path, ref_dir: Path = REF_OUT, model: str = MODEL) -> float:
    """Return the largest absolute head difference to the published run (active cells)."""
    new = flopy.utils.HeadFile(ws / f"{model}.hds").get_data()
    ref = flopy.utils.HeadFile(ref_dir / f"{model}.hds").get_data()
    active = np.abs(ref) < 1e29
    assert np.array_equal(active, np.abs(new) < 1e29), "active cells differ from the published run"
    return float(np.abs(new - ref)[active].max())


def well_groups(step: gs.FlowStep, wells: dict = PRIORITY_WELLS) -> dict[str, gs.Selection]:
    """Return one destination group per priority well plus 'priority' (all eight together)."""
    groups = {name: gs.select(step, package="WEL", boundnames=[name]) for name in wells}
    groups["priority"] = gs.select(step, package="WEL", boundnames=list(wells))
    return groups


def trace_wells(ws: Path, package_nodes: tuple[str, ...] = ()) -> tuple:
    """Read the steady step and trace backward from the priority wells.

    package_nodes=("SFR",) gives the stream reaches their own nodes, so water that leaks from a
    reach can be traced back up the stream network to where it entered the model.
    """
    if package_nodes:
        step = gs.read_network(ws, package_nodes=package_nodes, boundnames=True)
    else:
        step = gs.read_step(ws, boundnames=True)
    t0 = time.perf_counter()
    result = gs.backward(step, well_groups(step))
    return step, result, time.perf_counter() - t0


def trace_checks(step: gs.FlowStep, result: gs.BackwardResult) -> pd.DataFrame:
    """Return the closure check and destination inflow of every group."""
    rows = []
    for group in result.groups:
        check = gs.diagnostics.backward_closure(step, result, group)
        rows.append(
            {
                "group": group,
                "destination_inflow": result.destination_inflow[group],
                "closure_error": check.error,
                "closure_error_no_residual": check.error_without_residual,
            }
        )
    return pd.DataFrame(rows)


def read_endpoints(mp_dir: Path = MP7_OUT, regions: tuple[str, ...] = MP7_REGIONS) -> pd.DataFrame:
    """Return start (node0) and end (node) cell, status and exit face of every MODPATH 7 particle.

    Nodes are 0-based; cellface is the face the particle last crossed (0 = inside, 6 = top).
    """
    columns = ["particleid", "node0", "node", "status", "cellface"]
    frames = []
    for region in regions:
        ep = flopy.utils.EndpointFile(mp_dir / f"{MODEL}_mp_forward_weak_{region}.mpend")
        data = pd.DataFrame.from_records(ep.get_alldata())
        frames.append(data[columns].assign(region=region))
    return pd.concat(frames, ignore_index=True)


def mp7_mask(endpoints: pd.DataFrame, dest_nodes: list[int]) -> np.ndarray:
    """Return, per particle, whether it ends in one of dest_nodes (the published criterion)."""
    return endpoints["node"].isin(dest_nodes).to_numpy()


def endpoint_status(
    endpoints: pd.DataFrame, step: gs.FlowStep, wells: dict = PRIORITY_WELLS
) -> pd.DataFrame:
    """Return, per MODPATH 7 status, the kind of cell the particles end in and the wells reached.

    The end cell is classed on the MF6 budget: a strong sink sends all its outflow to boundary
    sinks (no face outflow), a weak sink part of it. Columns end_<package> count end cells by the
    package of their sink; top_face counts exits through the top face, where the published MPBAS
    file places RCH and SFR flows (IFACE 6).
    """
    budget = gs.cell_budget(step)
    node = endpoints["node"].to_numpy()
    sink, face_out = budget.sink[node], budget.edge_out[node]
    strong = (sink > 0) & (face_out <= 1e-12 * sink)
    sink_package = np.full(step.n_cells, "", dtype=object)
    names = np.array([pkg.name for pkg in step.packages], dtype=object)
    leaving = step.term_flow < 0
    sink_package[step.term_cell[leaving]] = names[step.term_package[leaving]]
    table = pd.DataFrame(
        {
            "status": endpoints["status"].to_numpy(),
            "strong_sink": strong,
            "weak_sink": (sink > 0) & ~strong,
            "no_sink": sink <= 0,
            "top_face": endpoints["cellface"].to_numpy() == 6,
            "package": sink_package[node],
            "well": endpoints["node"].map({v: k for k, v in wells.items()}).to_numpy(),
        }
    )
    rows = table.groupby("status")[["strong_sink", "weak_sink", "no_sink", "top_face"]].sum()
    rows.insert(0, "particles", table.groupby("status").size())
    by_package = pd.crosstab(table["status"], table["package"]).add_prefix("end_")
    by_well = pd.crosstab(table["status"], table["well"]).reindex(columns=list(wells), fill_value=0)
    out = rows.join(by_package).join(by_well).fillna(0).astype(int)
    return out.drop(columns="end_", errors="ignore").reset_index()


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    """Return |a and b| / |a or b| of two boolean arrays (1 if both are empty)."""
    union = np.sum(a | b)
    return float(np.sum(a & b) / union) if union else 1.0


def compare_masks(
    result: gs.BackwardResult,
    endpoints: pd.DataFrame,
    wells: dict = PRIORITY_WELLS,
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> pd.DataFrame:
    """Compare the MODPATH 7 masks with F > threshold at the particle start cells, per group.

    expected_cells is the sum of F over the start cells: the number of contributing cells that
    full mixing implies, to set against the MODPATH count.
    """
    start = endpoints["node0"].to_numpy()
    rows = []
    for group in result.groups:
        nodes = list(wells.values()) if group == "priority" else [wells[group]]
        mask = mp7_mask(endpoints, nodes)
        f = result.fraction_through[group][start]
        row = {"group": group, "mp7_cells": int(mask.sum()), "expected_cells": float(f.sum())}
        for t in thresholds:
            row[f"cells_F>{t}"] = int(np.sum(f > t))
            row[f"jaccard_F>{t}"] = jaccard(mask, f > t)
        top = np.zeros(len(f), dtype=bool)
        top[np.argsort(-f, kind="stable")[: mask.sum()]] = True
        row["area_matched_F"] = float(f[top].min()) if mask.any() else np.nan
        row["jaccard_area_matched"] = jaccard(mask, top)
        row["mean_F_in_mp7"] = float(f[mask].mean()) if mask.any() else np.nan
        row["mp7_hits_F0"] = int(np.sum(mask & (f <= 0.0)))
        rows.append(row)
    return pd.DataFrame(rows)


def run_prt(
    ws: Path,
    step: gs.FlowStep,
    result: gs.BackwardResult,
    exe: Path,
    prt_ws: Path,
    thin_weak_sinks: bool,
    group: str = "priority",
    release_z: float | None = None,
    porosity: float = MP7_POROSITY,
    subdivisions: int = 1,
    z_levels: int = PRT_Z_LEVELS,
) -> gs.prt.PrtResult:
    """Run flux-weighted PRT particles from every source term of the cells that reach group.

    release_z=None spreads the points over the cell volume (z_levels heights), as MF6 spreads the
    sources; 1.0 releases at the water table, where top-layer particles stay (no flow through the
    top face); the published MODPATH runs place one particle at the cell centre (0.5).
    """
    config = gs.PrtConfig(
        porosity=porosity,
        subdivisions=subdivisions,
        z_levels=z_levels,
        release_z=release_z,
        thin_weak_sinks=thin_weak_sinks,
    )
    return gs.track_particles(ws, step, result, group, config, exe, prt_ws)


def compare_prt(
    prt: gs.prt.PrtResult,
    result: gs.BackwardResult,
    endpoints: pd.DataFrame,
    group: str = "priority",
    wells: dict = PRIORITY_WELLS,
) -> dict:
    """Compare PRT capture with F (all release cells) and with the MODPATH 7 mask (start cells)."""
    f = result.fraction_through[group]
    seeded = np.isfinite(prt.cell_capture_fraction)
    p = prt.cell_capture_fraction
    start = endpoints["node0"].to_numpy()
    mask = mp7_mask(endpoints, list(wells.values()))
    p_start = np.nan_to_num(p[start])
    return {
        "released_flow": prt.released_flow,
        "captured_flow": prt.captured_flow,
        "destination_inflow": result.destination_inflow[group],
        "seeded_cells": int(seeded.sum()),
        "max_abs_F_minus_prt": float(np.abs(f[seeded] - p[seeded]).max()),
        "mean_abs_F_minus_prt": float(np.abs(f[seeded] - p[seeded]).mean()),
        "mp7_cells": int(mask.sum()),
        "prt_expected_cells": float(p_start.sum()),
        "jaccard_mp7_prt>0.5": jaccard(mask, p_start > 0.5),
        "jaccard_mp7_prt>0": jaccard(mask, p_start > 0.0),
    }


def source_coverage(step: gs.FlowStep, result: gs.BackwardResult, start: np.ndarray) -> pd.DataFrame:
    """Return, per group, the share of the destination inflow that enters in the start cells.

    Water entering elsewhere (deeper layers, outside the three release regions) cannot be seen
    by the published particles.
    """
    rows = []
    for group in result.groups:
        vf = result.volume_from[group]
        rows.append({"group": group, "share_from_start_cells": float(vf[start].sum() / vf.sum())})
    return pd.DataFrame(rows)


def grid_idomain(ws: Path, model: str = MODEL) -> np.ndarray:
    """Return IDOMAIN as (nlay, nrow, ncol) from the binary grid file."""
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{model}.dis.grb")
    return np.asarray(grb.idomain).reshape(grb.nlay, grb.nrow, grb.ncol)


def source_table(result: gs.BackwardResult) -> pd.DataFrame:
    """Return the water reaching each group by source package [L3/T]."""
    rows = [
        {"group": g, **{pkg: float(v.sum()) for pkg, v in result.volume_from_by_term[g].items()}}
        for g in result.groups
    ]
    return pd.DataFrame(rows)


def save_fractions(path: Path, result: gs.BackwardResult, n_cells: int) -> None:
    """Save every group's F on the first n_cells nodes (the model cells) as float32."""
    np.savez_compressed(
        path, **{g: result.fraction_through[g][:n_cells].astype(np.float32) for g in result.groups}
    )


# ---------------------------------------------------------------- PRT sources by well
# One thinned PRT run (volume seeding) evaluated for every well group, to split each well's
# particle capture by source package and compare it with full mixing (Section 3).
SOURCE_PACKAGES = ("RCHA", "SFR_0")
# Plan distance classes [m] of a source cell from the well; below 75 m: the well cell and its
# eight neighbours (50 m cells)
DISTANCE_BINS = (0.0, 75.0, 250.0, 500.0, 1000.0, 2000.0, np.inf)


def prt_release(
    ws: Path,
    step: gs.FlowStep,
    result: gs.BackwardResult,
    config: gs.PrtConfig,
    group: str = "priority",
    model: str = MODEL,
) -> tuple[gs.prt.PrtGrid, gs.prt.ReleasePoints]:
    """Return the PRT grid and the release points of the cells reaching group (track_particles)."""
    files = gs.find_model_files(ws, model)
    grid = gs.prt.load_prt_grid(ws, files.model, files.dis_type)
    contributing = result.fraction_through[group] > config.fraction_threshold
    local_z = config.local_z(int(grid.dis_kwargs["nlay"]))
    release = gs.prt.release_points(step, grid, contributing, None, config.subdivisions, local_z)
    return grid, release


def capture_by_group(
    track_file: Path, step: gs.FlowStep, result: gs.BackwardResult, n_particles: int
) -> dict[str, np.ndarray]:
    """Return every group's thinned captured share of each particle's weight; deletes the tracks."""
    visits = gs.prt.cell_visits(gs.prt.read_tracks(track_file))
    track_file.unlink()  # 6 GB for 488k particles; the visits hold what is needed
    survival = gs.prt.weak_sink_survival(step)
    captured = {}
    for group in result.groups:
        share = gs.prt.destination_share(step, result.selections[group])
        captured[group] = gs.prt.capture_along_paths(visits, n_particles, share, survival)[0]
    return captured


def run_prt_by_group(
    ws: Path,
    step: gs.FlowStep,
    result: gs.BackwardResult,
    exe: Path,
    prt_ws: Path,
    porosity: float = MP7_POROSITY,
    subdivisions: int = 1,
    z_levels: int = PRT_Z_LEVELS,
) -> tuple[gs.prt.PrtGrid, gs.prt.ReleasePoints, dict[str, np.ndarray]]:
    """Run one thinned PRT from the cells reaching any priority well and evaluate every group."""
    config = gs.PrtConfig(porosity=porosity, subdivisions=subdivisions, z_levels=z_levels)
    grid, release = prt_release(ws, step, result, config)
    sim = gs.prt.write_prt(prt_ws, ws, grid, release, config, exe, MODEL)
    return grid, release, capture_by_group(gs.prt.run_prt(sim), step, result, release.n)


def cell_distance(grid: gs.prt.PrtGrid, cells: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Return the plan distance from each cell's centre to the nearest target cell's centre."""
    centres = np.array([p.mean(axis=0) for p in grid.polygons])  # vertex mean: the DIS cell centre
    xy, txy = centres[cells % grid.ncpl], centres[np.unique(targets % grid.ncpl)]
    dx, dy = xy[:, None, 0] - txy[None, :, 0], xy[:, None, 1] - txy[None, :, 1]
    return np.hypot(dx, dy).min(axis=1)


def prt_sources_by_well(
    result: gs.BackwardResult,
    release: gs.prt.ReleasePoints,
    captured: dict[str, np.ndarray],
    packages: tuple[str, ...] = SOURCE_PACKAGES,
) -> pd.DataFrame:
    """Return, per group, the water by source package under full mixing and along PRT paths."""
    rows = []
    for group in result.groups:
        row = {"group": group}
        for pkg in packages:
            row[f"mixing_{pkg}"] = float(result.volume_from_by_term[group][pkg].sum())
            is_pkg = release.package == pkg
            row[f"prt_{pkg}"] = float(np.sum(release.weight * captured[group] * is_pkg))
        for method in ("mixing", "prt"):
            row[f"{method}_total"] = sum(row[f"{method}_{pkg}"] for pkg in packages)
        for pkg in packages:
            for method in ("mixing", "prt"):
                row[f"{method}_share_{pkg}"] = row[f"{method}_{pkg}"] / row[f"{method}_total"]
            row[f"prt_minus_mixing_{pkg}"] = row[f"prt_{pkg}"] - row[f"mixing_{pkg}"]
        rows.append(row)
    return pd.DataFrame(rows)


def prt_sources_by_distance(
    result: gs.BackwardResult,
    grid: gs.prt.PrtGrid,
    release: gs.prt.ReleasePoints,
    captured: dict[str, np.ndarray],
    packages: tuple[str, ...] = SOURCE_PACKAGES,
    bins: tuple[float, ...] = DISTANCE_BINS,
) -> pd.DataFrame:
    """Return the released flow and the water reaching each group by package and distance.

    Distance is the plan distance of the source cell from the group's well cell(s); the water
    reaching the group is given under full mixing and along PRT paths.

    mean_F and mean_P are the flow-weighted capture fractions of those sources (water reaching
    the group / released flow).
    """
    cells = np.unique(release.cell)
    n_cells = len(result.fraction_through["priority"])
    rows = []
    for group in result.groups:
        distance = cell_distance(grid, cells, np.flatnonzero(result.selections[group].cells))
        bin_of_cell = np.digitize(distance, bins) - 1
        for pkg in packages:
            is_pkg = release.package == pkg
            w = release.weight * is_pkg
            q = np.bincount(release.cell, weights=w, minlength=n_cells)
            p = np.bincount(release.cell, weights=w * captured[group], minlength=n_cells)
            f = result.volume_from_by_term[group][pkg]
            for b in range(len(bins) - 1):
                sel = cells[bin_of_cell == b]
                row = {"group": group, "package": pkg, "from_m": bins[b], "to_m": bins[b + 1]}
                row.update(released=q[sel].sum(), mixing=f[sel].sum(), prt=p[sel].sum())
                rows.append(row)
    table = pd.DataFrame(rows)
    table["prt_minus_mixing"] = table["prt"] - table["mixing"]
    table["mean_F"] = table["mixing"] / table["released"]
    table["mean_P"] = table["prt"] / table["released"]
    return table


def prt_capture_by_depth(
    result: gs.BackwardResult,
    release: gs.prt.ReleasePoints,
    captured: dict[str, np.ndarray],
    packages: tuple[str, ...] = SOURCE_PACKAGES,
) -> pd.DataFrame:
    """Return the released flow and the water reaching each group by package and release height.

    The full-mixing value is the same at every height (local z): F does not depend on it.
    """
    levels = np.unique(release.z)
    rows = []
    for group in result.groups:
        for pkg in packages:
            mixing = float(result.volume_from_by_term[group][pkg].sum()) / len(levels)
            for z in levels:
                sel = (release.package == pkg) & (release.z == z)
                rows.append(
                    {
                        "group": group,
                        "package": pkg,
                        "local_z": z,
                        "released": float(release.weight[sel].sum()),
                        "mixing": mixing,
                        "prt": float(np.sum(release.weight[sel] * captured[group][sel])),
                    }
                )
    return pd.DataFrame(rows)


def write_prt_sources(
    ws: Path, step: gs.FlowStep, result: gs.BackwardResult, exe: Path, out: Path
) -> None:
    """Run the per-group PRT evaluation and write the source tables and per-particle capture."""
    prt_ws = out / "prt_by_well"
    grid, release, captured = run_prt_by_group(ws, step, result, exe, prt_ws)
    np.savez_compressed(
        prt_ws / "particle_capture.npz",
        cell=release.cell,
        package=release.package.astype(str),
        z=release.z,
        weight=release.weight,
        **{g: c.astype(np.float32) for g, c in captured.items()},
    )
    by_well = prt_sources_by_well(result, release, captured)
    wells = by_well[by_well["group"] != "priority"]["prt_total"].sum()
    priority = by_well.loc[by_well["group"] == "priority", "prt_total"].item()
    assert abs(wells - priority) <= 1e-6 * priority, "the wells' capture does not sum to priority"
    by_distance = prt_sources_by_distance(result, grid, release, captured)
    by_depth = prt_capture_by_depth(result, release, captured)
    by_well.to_csv(out / "prt_sources_by_well.csv", index=False)
    by_distance.to_csv(out / "prt_sources_by_distance.csv", index=False)
    by_depth.to_csv(out / "prt_capture_by_depth.csv", index=False)


def main(
    run_published: bool = True,
    run_tight: bool = True,
    compare_mp7: bool = True,
    run_prt_check: bool = True,
    run_prt_sources: bool = True,
    make_figures: bool = True,
    out: Path = OUT,
    fig_dir: Path = FIG_DIR,
) -> None:
    """Run the selected parts of stage 1; tables go to out."""
    exe = mf6_exe()
    out.mkdir(parents=True, exist_ok=True)
    ws, ws_tight = out / "optimal", out / "optimal_tight"
    runs = []
    if run_published:
        prepare_model(ws)
        runs.append({"run": "published", "seconds": run_mf6(ws, exe), "max_dh": head_difference(ws)})
    if run_tight:
        prepare_model(ws_tight, dvclose=TIGHT_DVCLOSE)
        runs.append(
            {"run": "tight", "seconds": run_mf6(ws_tight, exe), "max_dh": head_difference(ws_tight)}
        )
    if runs:
        pd.DataFrame(runs).to_csv(out / "mf6_runs.csv", index=False)
    if compare_mp7:
        step, result, seconds = trace_wells(ws)
        endpoints = read_endpoints()
        trace_checks(step, result).assign(seconds=seconds).to_csv(out / "checks_cells.csv", index=False)
        compare_masks(result, endpoints).to_csv(out / "mp7_comparison.csv", index=False)
        endpoint_status(endpoints, step).to_csv(out / "mp7_status.csv", index=False)
        source_coverage(step, result, endpoints["node0"].to_numpy()).to_csv(
            out / "mp7_coverage.csv", index=False
        )
        source_table(result).to_csv(out / "sources_cells.csv", index=False)
        save_fractions(out / "fractions_cells.npz", result, step.n_cells)
        mask = mp7_mask(endpoints, list(PRIORITY_WELLS.values()))
        np.savez_compressed(out / "mp7_priority.npz", node0=endpoints["node0"], captured=mask)
        net_step, net_result, seconds = trace_wells(ws_tight, package_nodes=("SFR",))
        trace_checks(net_step, net_result).assign(seconds=seconds).to_csv(
            out / "checks_sfr_network.csv", index=False
        )
        source_table(net_result).to_csv(out / "sources_sfr_network.csv", index=False)
        save_fractions(out / "fractions_sfr_network.npz", net_result, step.n_cells)
    if run_prt_check:
        step, result, _ = trace_wells(ws)
        endpoints = read_endpoints()
        rows = []
        for release_z, thin in PRT_CASES:
            release = "volume" if release_z is None else f"z{release_z:g}"
            prt_ws = out / f"prt_{release}_thin{int(thin)}"
            prt = run_prt(ws, step, result, exe, prt_ws, thin, release_z=release_z)
            row = {"release": release, "thin_weak_sinks": thin}
            rows.append({**row, **compare_prt(prt, result, endpoints)})
            np.save(prt_ws / "cell_capture_fraction.npy", prt.cell_capture_fraction.astype(np.float32))
            (prt_ws / "prt.trk.csv").unlink()  # 1.5 GB; the result is in the table
        pd.DataFrame(rows).to_csv(out / "prt_comparison.csv", index=False)
    if run_prt_sources:
        step, result, _ = trace_wells(ws)
        write_prt_sources(ws, step, result, exe, out)
    if make_figures:
        sys.path.insert(0, str(HERE))
        import figures

        figures.capture_maps(out, fig_dir, grid_idomain(ws), PRIORITY_WELLS)
        figures.jaccard_table(out).to_csv(out / "agreement_with_mp7.csv", index=False)


if __name__ == "__main__":
    main()
