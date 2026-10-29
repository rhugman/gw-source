"""Neversink case study: the published MODPATH 7 contributing cells reproduced with MF6 PRT.

The published mask (workflow.py) comes from forward MODPATH 7 runs with these conventions: one
particle at the centre of each cell of the uppermost active layer (local x, y, z = 0.5), porosity
0.3, weak sinks stop particles (WeakSinkOption 2), the MPBAS file assigns RCH and SFR flows to
the top face (default IFACE 6), and the particle groups drape (DrapeOption 1, the "2 n 1" line
of the MPSIM files). Here the same particles are run with MF6 PRT on the same flow field and
their end cells are compared particle by particle with the published end points.

Face assignment. MF6 boundary packages take an auxiliary variable IFLOWFACE that PRT reads from
the GWF budget file (MF6 6.5 and later; prt-fmi.f90): 0 or absent = distributed over the cell (a
source, or a sink that makes the cell a weak sink), -1 = top face, -2 = bottom face, 1 to n =
lateral faces. The aux column does not change the flow solution. MODPATH 7 puts a face-assigned
flow on the face only where the face is a model boundary (no active neighbour,
ModpathCellData.f90); on an internal face it falls back to a distributed source or sink. PRT
adds it to the face whatever lies behind it, and a particle that leaves through a face with net
boundary outflow terminates there (status 2). To match MODPATH 7, IFLOWFACE = -1 is set only
where the cell has no active cell above (vertical pass-through cells, IDOMAIN -1, skipped, as
MF6 connects across them), and 0 elsewhere. SFR reaches with an active cell above stay
distributed.

Dry start cells (drape). Many start cells are dry in the Newton solution (saturation 0, head
below the cell bottom). With DrapeOption 1, MODPATH 7 moves a particle whose
start cell is inactive to the top-most active cell below and keeps its local coordinates
(MPath7.f90), so it starts at local z 0.5 of that cell's saturated thickness. PRT instead drops
such a particle to the water table of the cell below (its DRAPE option also places it at the
water table). drape_dry_starts() moves those starts to the first wet cell below explicitly; the
variants with and without it test, by their agreement with the published end cells, whether the
published runs treated dry cells as inactive. The MODPATH 7 source read
here (develop branch) marks a cell inactive only where its head equals HDRY, which MF6 does not
write in this model, so this can only be inferred from the end points, not from the code.

Remaining difference. The published runs also stop particles (status 2) at a lateral face whose
neighbour is dry, as if the dry cell were inactive. PRT has no such rule: it passes the particle
into the dry cell and drops it to the cell below. mp7_reproduction_status.csv counts the
particles by MODPATH 7 and PRT status, so these stops show up there.

Variants (PRT with STOP_AT_WEAK_SINK, EXTEND_TRACKING, no stop zone, termination records only):
face assignment (IFLOWFACE as above, or MF6's default of distributing the boundary flows over
the cell, which makes every gaining stream cell a weak sink), drape or not, and the rerun flow
field or the published MF6 6.2 one (published_flows: its cell-to-cell and boundary flows put in
the rerun budget file, saturation from its heads).

A particle contributes if it ends in one of the eight priority well cells, as in the published
mask (workflow.mp7_mask). reproduce() (called by workflow.py) writes mp7_iflowface_check.csv,
mp7_reproduction.csv and mp7_reproduction_status.csv to studies/neversink/output/.
"""

import shutil
from pathlib import Path

import flopy
import numpy as np
import pandas as pd

import gwsource as gs
import workflow as wf

IFLOWFACE_TOP = -1
START_COLUMNS = (
    "particleid", "node0", "x0", "y0", "zloc0", "node", "status", "cellface", "time"
)
# (name, IFLOWFACE model, drape dry starts, published flows)
VARIANTS = (
    ("mp7_conventions", True, True, False),
    ("mp7_conventions_published_flows", True, True, True),
    ("no_drape", True, False, False),
    ("distributed", False, True, False),
    ("distributed_no_drape", False, False, False),
)
# A particle released in a cell wet by a film (saturation 1.4e-16, head at the cell bottom) makes
# MF6 6.9.0.dev0 PRT abort (SIGILL) at release; such starts are left out (one in this model).
MIN_SAT = 1e-15


# ---------------------------------------------------------------- IFLOWFACE model copy


def top_face_open(idomain: np.ndarray) -> np.ndarray:
    """Return, per cell (nlay, nrow, ncol), whether no active cell lies above it.

    Vertical pass-through cells (IDOMAIN -1) connect the cells above and below them, so they are
    skipped; an inactive cell (0) closes the column.
    """
    open_top = np.ones(idomain.shape, dtype=bool)
    for k in range(1, idomain.shape[0]):
        above = np.zeros(idomain.shape[1:], dtype=bool)
        passing = np.ones(idomain.shape[1:], dtype=bool)
        for kk in range(k - 1, -1, -1):
            above |= passing & (idomain[kk] > 0)
            passing &= idomain[kk] < 0
        open_top[k] = ~above
    return open_top


def sfr_reach_cells(packagedata_file: Path) -> np.ndarray:
    """Return the 0-based (layer, row, column) of every SFR reach in a packagedata file."""
    rows = np.loadtxt(packagedata_file, comments="#", usecols=(1, 2, 3), dtype=int, ndmin=2)
    return rows - 1


def add_aux_option(text: str, name: str, block: str = "options") -> str:
    """Return package text with name added to the AUXILIARY option (created if absent)."""
    lines = text.splitlines()
    begin = next(i for i, ln in enumerate(lines) if ln.strip().upper() == f"BEGIN {block.upper()}")
    for i in range(begin + 1, len(lines)):
        words = lines[i].split()
        if words and words[0].upper() == "END":
            lines.insert(i, f"  AUXILIARY  {name}")
            break
        if words and words[0].upper() in ("AUX", "AUXILIARY"):
            lines[i] = f"{lines[i]}  {name}"
            break
    return "\n".join(lines) + "\n"


def add_rcha_iflowface(rcha_file: Path, value: int = IFLOWFACE_TOP) -> None:
    """Assign all recharge of a READASARRAYS RCH file (one period block) to one face."""
    text = add_aux_option(rcha_file.read_text(encoding="utf-8"), "IFLOWFACE")
    assert text.upper().count("BEGIN PERIOD") == 1, "expected one period block"
    head, tail = text.split("END period", 1)
    rcha_file.write_text(f"{head}  IFLOWFACE\n    CONSTANT  {value:d}\nEND period{tail}", encoding="utf-8")


def add_sfr_iflowface(sfr_file: Path, packagedata_file: Path, faces: np.ndarray) -> None:
    """Append an IFLOWFACE aux value per reach to the SFR packagedata (after the existing aux)."""
    sfr_file.write_text(add_aux_option(sfr_file.read_text(encoding="utf-8"), "IFLOWFACE"),
                        encoding="utf-8")
    lines = packagedata_file.read_text(encoding="utf-8").splitlines()
    data = [i for i, ln in enumerate(lines) if ln.strip() and not ln.lstrip().startswith("#")]
    assert len(data) == len(faces), "one IFLOWFACE value per reach"
    for i, face in zip(data, faces):
        lines[i] = f"{lines[i]} {int(face):d}"
    packagedata_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_iflowface_model(ws: Path, src: Path = wf.MODEL_SRC) -> dict:
    """Copy the calibrated model and assign RCH and SFR flows to the top face where it is open.

    Returns the number of SFR reaches put on the top face and left distributed.
    """
    wf.prepare_model(ws, src)
    return add_iflowface(ws)


def add_iflowface(ws: Path) -> dict:
    """Assign the RCH and SFR flows of a model input to the top face where it is open (in place).

    Returns the number of SFR reaches put on the top face and left distributed.
    """
    sim = flopy.mf6.MFSimulation.load(sim_ws=str(ws), load_only=["dis"], verbosity_level=0)
    idomain = sim.get_model(wf.MODEL).dis.idomain.array
    reaches = sfr_reach_cells(ws / "neversink_packagedata.dat")
    on_top = top_face_open(idomain)[tuple(reaches.T)]
    add_rcha_iflowface(ws / f"{wf.MODEL}.rcha")
    faces = np.where(on_top, IFLOWFACE_TOP, 0)
    add_sfr_iflowface(ws / f"{wf.MODEL}.sfr", ws / "neversink_packagedata.dat", faces)
    return {"sfr_top_face": int(on_top.sum()), "sfr_distributed": int((~on_top).sum())}


def flow_difference(ws: Path, ref_ws: Path, model: str = wf.MODEL) -> dict:
    """Return the largest head and cell-to-cell flow differences between two runs."""
    h = flopy.utils.HeadFile(ws / f"{model}.hds").get_data()
    h_ref = flopy.utils.HeadFile(ref_ws / f"{model}.hds").get_data()
    q = flopy.utils.CellBudgetFile(ws / f"{model}.cbc").get_data(text="FLOW-JA-FACE")[0]
    q_ref = flopy.utils.CellBudgetFile(ref_ws / f"{model}.cbc").get_data(text="FLOW-JA-FACE")[0]
    return {
        "max_dh": float(np.abs(h - h_ref).max()),
        "max_dq": float(np.abs(q - q_ref).max()),
        "max_q": float(np.abs(q_ref).max()),
    }


# ---------------------------------------------------------------- budget files


def budget_record(path: Path, text: str, mode: str = "r") -> np.memmap:
    """Return a memory map of the data of one budget record (IMETH 1 array or IMETH 6 list)."""
    cbc = flopy.utils.CellBudgetFile(path)
    idx = int(np.flatnonzero(cbc.recordarray["text"] == text.rjust(16).encode())[0])
    imeth = int(cbc.recordarray["imeth"][idx])
    assert imeth in (1, 6), f"{text}: IMETH {imeth} is not handled"
    with open(path, "rb") as f:
        f.seek(int(cbc.iposarray[idx]))
        if imeth == 1:
            n = int(cbc.recordarray["ncol"][idx])
            return np.memmap(path, dtype=np.float64, mode=mode, offset=f.tell(), shape=(n,))
        naux = int(np.fromfile(f, np.int32, 1)[0]) - 1
        names = [f.read(16).decode().strip() for _ in range(naux)]
        nlist = int(np.fromfile(f, np.int32, 1)[0])
        offset = f.tell()
    fields = [("node", np.int32), ("node2", np.int32), ("q", np.float64)]
    dtype = np.dtype(fields + [(n, np.float64) for n in names])
    return np.memmap(path, dtype=dtype, mode=mode, offset=offset, shape=(nlist,))


def write_published_flow_budget(
    budget_file: Path, out_file: Path, ref_dir: Path = wf.REF_OUT, model: str = wf.MODEL
) -> dict:
    """Copy a budget file with the flows and saturation of the published MF6 run put in.

    The published MODPATH 7 runs read the published MF6 6.2 output. Its budget file has no
    DATA-SAT or DATA-SPDIS, so the rerun's file is the template: FLOW-JA-FACE and the boundary
    flows are replaced by the published ones and the saturation by (h - bottom) / thickness of
    the published heads (clipped to 0..1). Returns the largest change per record.
    """
    shutil.copyfile(budget_file, out_file)
    ref = ref_dir / f"{model}.cbc"
    changes = {}
    pairs = (("FLOW-JA-FACE", "FLOW-JA-FACE"), ("WEL", "WEL"), ("RCHA", "RCH"), ("CHD", "CHD"),
             ("SFR", "SFR"))
    for text, ref_text in pairs:
        new, old = budget_record(out_file, text, "r+"), budget_record(ref, ref_text)
        if new.dtype.names is None:
            changes[text] = float(np.abs(new - old).max())
            new[:] = old
        else:
            assert np.array_equal(new["node"], old["node"]), f"{text}: different cells"
            changes[text] = float(np.abs(new["q"] - old["q"]).max())
            new["q"] = old["q"]
        new.flush()
    grb = flopy.mf6.utils.MfGrdFile(ref_dir / f"{model}.dis.grb")
    bot = np.ravel(grb.bot)
    top = np.concatenate([np.ravel(grb.top), bot[: -grb.nrow * grb.ncol]])
    head = flopy.utils.HeadFile(ref_dir / f"{model}.hds").get_data().ravel()
    sat = budget_record(out_file, "DATA-SAT", "r+")
    n = sat["node"] - 1
    linear = np.clip((head[n] - bot[n]) / (top[n] - bot[n]), 0.0, 1.0)
    changes["DATA-SAT"] = float(np.abs(sat["sat"] - linear).max())
    sat["sat"] = linear
    sat.flush()
    return changes


def write_distributed_budget(
    budget_file: Path, out_file: Path, texts: tuple[str, ...] = ("RCHA", "SFR")
) -> None:
    """Copy a budget file with the IFLOWFACE column of the given records set to 0 (distributed).

    PRT reads the face assignment from the budget file, so the copy gives the MF6 default of
    distributing these flows over the cell without another flow run.
    """
    shutil.copyfile(budget_file, out_file)
    for text in texts:
        record = budget_record(out_file, text, "r+")
        assert "IFLOWFACE" in record.dtype.names, f"{text}: no IFLOWFACE column"
        record["IFLOWFACE"] = 0.0
        record.flush()


def cell_saturation(budget_file: Path, n_cells: int) -> np.ndarray:
    """Return the saturation of every cell (user nodes, 0 where inactive) from DATA-SAT."""
    rec = flopy.utils.CellBudgetFile(budget_file).get_data(text="DATA-SAT")[0]
    sat = np.zeros(n_cells)
    sat[rec["node"] - 1] = rec["sat"]
    return sat


# ---------------------------------------------------------------- particles and PRT run


def drape_dry_starts(starts: pd.DataFrame, idomain: np.ndarray, sat: np.ndarray) -> pd.DataFrame:
    """Move starts in dry cells to the first active, wet cell below (same x, y and local z)."""
    ncpl = idomain[0].size
    flat = idomain.ravel()
    node = starts["node0"].to_numpy().copy()
    for i in np.flatnonzero(sat[node] == 0.0):
        n = node[i] + ncpl
        while n < flat.size and (flat[n] < 0 or sat[n] == 0.0):
            n += ncpl
        assert n < flat.size and flat[n] > 0, f"no wet cell below start {starts['node0'].iloc[i]}"
        node[i] = n
    return starts.assign(node0=node)


def trackable(starts: pd.DataFrame, sat: np.ndarray, min_sat: float = MIN_SAT) -> np.ndarray:
    """Return, per start, False where the start cell is wet by less than min_sat (see MIN_SAT)."""
    s = sat[starts["node0"].to_numpy()]
    return (s == 0.0) | (s >= min_sat)


def write_mp7_prt(
    prt_ws: Path,
    gwf_ws: Path,
    budget_file: Path,
    starts: pd.DataFrame,
    exe: Path,
    porosity: float = wf.MP7_POROSITY,
    model: str = wf.MODEL,
    stop_at_weak_sink: bool = True,
    tracks: bool = False,
) -> flopy.mf6.MFSimulation:
    """Write a PRT run with one particle per start (cell, x, y, local z), stopping at weak sinks.

    stop_at_weak_sink=False lets the particles pass weak sinks; tracks=True also writes the
    release and cell-exit records (gwsource.prt.cell_visits), not only the terminations.
    """
    n = len(starts)
    release = gs.prt.ReleasePoints(
        cell=starts["node0"].to_numpy(),
        x=starts["x0"].to_numpy(),
        y=starts["y0"].to_numpy(),
        z=starts["zloc0"].to_numpy(),
        weight=np.ones(n),
        package=np.full(n, "", dtype=object),
    )
    grid = gs.prt.load_prt_grid(gwf_ws, model, "DIS")
    config = gs.prt.PrtConfig(porosity=porosity, exit_solve_tolerance=1e-5)
    return gs.prt.write_prt(
        prt_ws, gwf_ws, grid, release, config, exe, model,
        budget_file=budget_file, stop_at_weak_sink=stop_at_weak_sink,
        track_release=tracks, track_exit=tracks, clear_ws=True,
    )


def run_endpoints(sim: flopy.mf6.MFSimulation, keep: np.ndarray) -> dict[str, np.ndarray]:
    """Run a PRT simulation of the starts in keep; return end cell, status and time per start.

    Starts left out get end cell -1, status -1 and time NaN.
    """
    track_csv = gs.prt.run_prt(sim)
    run = gs.prt.endpoints(gs.prt.read_tracks(track_csv), int(keep.sum()))
    track_csv.unlink()
    ends = {
        "cell": np.full(len(keep), -1, dtype=np.int64),
        "status": np.full(len(keep), -1, dtype=np.int64),
        "time": np.full(len(keep), np.nan),
    }
    for key, values in run.items():
        ends[key][keep] = values
    return ends


def run_variant(
    prt_ws: Path, gwf_ws: Path, budget_file: Path, starts: pd.DataFrame, exe: Path, drape: bool
) -> dict[str, np.ndarray]:
    """Track the published starts on one flow field and save the end points in prt_ws."""
    idomain = wf.grid_idomain(gwf_ws)
    sat = cell_saturation(budget_file, idomain.size)
    if drape:
        starts = drape_dry_starts(starts, idomain, sat)
    keep = trackable(starts, sat)
    sim = write_mp7_prt(prt_ws, gwf_ws, budget_file, starts[keep].reset_index(drop=True), exe)
    ends = run_endpoints(sim, keep)
    np.savez_compressed(prt_ws / "endpoints.npz", **ends)
    return ends


# ---------------------------------------------------------------- comparison


def compare_endpoints(
    starts: pd.DataFrame, ends: dict[str, np.ndarray], wells: dict = wf.PRIORITY_WELLS
) -> dict:
    """Compare PRT end points with the published ones: same end cell, status, mask Jaccard."""
    mp7_node, prt_node = starts["node"].to_numpy(), ends["cell"]
    nodes = list(wells.values())
    mp7_mask, prt_mask = np.isin(mp7_node, nodes), np.isin(prt_node, nodes)
    same = mp7_node == prt_node
    timed = same & (ends["time"] > 0) & (starts["time"].to_numpy() > 0)
    ratio = ends["time"][timed] / starts["time"].to_numpy()[timed]
    row = {
        "particles": len(starts),
        "not_tracked": int(np.sum(prt_node < 0)),
        "same_end_cell": float(same.mean()),
        "same_status": float(np.mean(starts["status"].to_numpy() == ends["status"])),
        "same_cell_time_within_1pct": float(np.mean(np.abs(ratio - 1.0) < 0.01)),
        "mp7_cells": int(mp7_mask.sum()),
        "prt_cells": int(prt_mask.sum()),
        "both_cells": int(np.sum(mp7_mask & prt_mask)),
        "jaccard": wf.jaccard(mp7_mask, prt_mask),
    }
    for name, node in wells.items():
        a, b = mp7_node == node, prt_node == node
        row[f"mp7_{name}"], row[f"prt_{name}"] = int(a.sum()), int(b.sum())
        row[f"jaccard_{name}"] = wf.jaccard(a, b)
    return row


def status_crosstab(starts: pd.DataFrame, ends: dict[str, np.ndarray]) -> pd.DataFrame:
    """Return particle counts by MODPATH 7 status and PRT status (-1 = not tracked)."""
    table = pd.crosstab(
        pd.Series(starts["status"].to_numpy(), name="mp7_status"),
        pd.Series(ends["status"], name="prt_status"),
    )
    return table.stack().rename("particles").reset_index()


def reproduce(
    out: Path, exe: Path, ws_ref: Path, variants: tuple = VARIANTS
) -> pd.DataFrame:
    """Run the PRT variants on the published starts and write the comparison tables to out.

    ws_ref is the rerun of the calibrated model (workflow.prepare_model); the IFLOWFACE copy and
    the PRT runs go to out.
    """
    ws_face = out / "optimal_iflowface"
    faces = prepare_iflowface_model(ws_face)
    seconds = wf.run_mf6(ws_face, exe)
    check = {**faces, "mf6_seconds": seconds, **flow_difference(ws_face, ws_ref)}
    published = out / "neversink_published_flows.cbc"
    check.update(write_published_flow_budget(ws_face / f"{wf.MODEL}.cbc", published))
    pd.DataFrame([check]).to_csv(out / "mp7_iflowface_check.csv", index=False)
    starts = wf.read_endpoints(columns=START_COLUMNS)
    rows, tabs = [], []
    for name, iflowface, drape, published_flows in variants:
        gwf_ws = ws_face if iflowface else ws_ref
        budget = published if published_flows else gwf_ws / f"{wf.MODEL}.cbc"
        ends = run_variant(out / f"prt_mp7_{name}", gwf_ws, budget, starts, exe, drape)
        rows.append({"variant": name, **compare_endpoints(starts, ends)})
        tabs.append(status_crosstab(starts, ends).assign(variant=name))
    pd.concat(tabs).to_csv(out / "mp7_reproduction_status.csv", index=False)
    table = pd.DataFrame(rows)
    table.to_csv(out / "mp7_reproduction.csv", index=False)
    return table
