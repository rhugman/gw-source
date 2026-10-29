"""Neversink case study: a refined window around the U wells, where particles and full mixing
should meet.

Question. On the 50 m regional grid, 27 PRT particles per start cell (prt_many_particles.py) give
a contributing area (share P > 0.5) about twice the full-mixing F > 0.5 area, and
diagnostics.py puts the gap at a few bottleneck cells next to the wells, where the capture zone
is narrower than a cell. Neither method on that grid is the truth. As the grid is refined, the
mixing inside cells shrinks, so F and P should approach one advective answer: the advective
reference of the window (R_adv).

Regional run. The calibrated model rerun with the tight head criteria of
workflow.TIGHT_DVCLOSE, and with RCH and SFR on the open top face (mp7_convention.add_iflowface;
the aux column does not change the flows). The window takes its boundary values from it and is
solved with the same criteria, so the two are converged alike.

Window. A rectangle of the regional grid around the U wells (U_917, U__55, U___7, U___8): the
bounding box of their published contributing cells and of their regional F > 0.1 cells (gross,
and gross with every sink strong), plus PAD cells on each side, clipped to the model. It keeps
the four layers, the properties, recharge, wells and CHD cells inside it, and the SFR reaches
inside it; a reach whose upstream reach lies outside gets that inflow from the regional SFR
budget.

Boundary. Two options at the regional resolution: the regional heads as CHD in the outermost
wet cells that have an active neighbour outside the window ("chd"), or the regional flows across
the window edge as WEL terms on that face ("flux", IFLOWFACE of the face, so particles see a
face flow). Both are compared with the regional run (check_regional.csv); the one closer in its
cell-to-cell flows is used for the refined windows. The edge outflows of "flux" need MF6
AUTO_FLOW_REDUCE (EDGE_AFR) to converge on refined grids, and that cut moves its 1x heads by up
to 0.9 m at the edge; "chd" stays within 2 mm, and is chosen. CHD cells take no recharge or SFR
exchange (MF6), which only touches the edge ring, at least 10 cells from any start cell with
F or P > 0.01.

Refinement (RESOLUTIONS). Each cell is split into n x n columns and each layer into nz even
sublayers: a horizontal series (50, 25, 12.5 m at 4 layers), a vertical series (4 to 32 layers
at 25 m) and 12.5 m with 8 and 16 layers, the finest run. IDOMAIN, K, K33 and the recharge rate are copied to the children. A well stays a
point and a stream a line, so refinement removes the smearing of each over a 50 m cell:
- a well is a point at its cell centre: its rate is split evenly over the children that touch
  the centre (2 x 2 for even n), and over the sublayers by their saturated thickness;
- a stream is the polyline through the centres of its reach cells: a reach is the part of that
  line inside its cell (from the centre half-way to each connected reach), cut into sub-reaches
  by the child cells it crosses, each with the reach's length times its share of the line;
  width, gradient, streambed top, thickness and K stay; the sublayer is the one that holds the
  streambed bottom;
- regional CHD cells give their head to every wet child; the edge CHD heads go on the outermost
  children; the edge flows are spread evenly along the edge and over the sublayers by their
  saturated thickness.

Methods, per run, on the published start cells inside the window (all in the NE region):
- F of the U wells, gross, and gross with every sink strong (strong_sinks.py);
- P: 27 PRT particles per original start cell, at local x, y and z = 1/6, 1/2 and 5/6 of the
  original cell, as in prt_many_particles.py (STOP_AT_WEAK_SINK, porosity 0.3, RCH on the top
  face, SFR on the top face where it is open, EXTEND_TRACKING). P is the share that ends in a
  cell with a U well; "centre" is the middle particle alone (the published convention).
Each point goes to the child cell that holds it; a point on a child face (x or y = 1/2 at even n)
is moved 1 µm into the east or south child. Its height is the same fraction of the saturated
thickness of the original layer in that child column. Where that is dry, or wet only by a film
(saturation < 1e-10, where PRT aborts), the point drapes to the next layer down, as the published
dry starts did. F of a start cell is the mean F of its 27 release cells, so F and P sample the
same points. The regional run uses the same code (n = nz = 1).

Physical reference (adjoint_part, run by hand on a kept model): adjoint MF6 GWT on the reversed
flow field with alpha_T = ALPHA_T, as set up in studies/comparison/methods.py (its reverse_budget
and solver settings; run_adjoint here adds the window's IDOMAIN). The no-dispersion run is first
asserted equal to F (gross) to ADJOINT_ATOL. C of a start cell is the mean over its 27 release
cells, as F. Tried on the 12.5 m, 8-layer window (2.8M cells): the check passed (max |C - F|
7e-10, 1.5 min), but the alpha_T = 1 m run did not converge in 50 outer iterations (30 min), so
the window has no physical reference (run_log.json, adjoint_gwt).

Metrics on the scored start cells (the published start cells inside the window, without its edge
cells), per method and run: cells with value > 0.5, Jaccard index and size ratio of that area
against the reference area, RMSE over cells where either value exceeds 0.01, and Jaccard index
and size ratio against the published U area. Two references, both on the finest grid: P, and F
gross with every sink strong.

Outputs in studies/neversink/output/window/: check_regional.csv (1x window
against the regional run), runs.csv (per run: cells, package flows, edge-flow cuts, run
times), metrics.csv, refinement.csv (the summary table), adjoint_cells.csv, start_cells.csv.gz (per start cell and run), run_log.json and figures/. The model and PRT
workspaces are deleted once read (keep_models=True keeps them).

Needs TraceConfig.strong_sinks (gwsource, branch feature/strong-sinks). Run after workflow.py:

    python studies/neversink/window.py
"""

import json
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import flopy  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy.sparse as sp  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMPORT_DIRS = (HERE, REPO / "studies" / "paper", REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import mp7_convention as mp7  # noqa: E402
import prt_many_particles as pm  # noqa: E402
import strong_sinks as ss  # noqa: E402
import workflow as wf  # noqa: E402

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import neversink_figures as nfig  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

# The study output folder (resolved, so that a linked output/ folder is followed).
OUT_DIR = (wf.OUT / "optimal").resolve().parent / "window"
FIG_DIR = OUT_DIR / "figures"
MODEL = wf.MODEL
CELL = 50.0  # regional cell size [m]
U_WELLS = {w: n for w, n in wf.PRIORITY_WELLS.items() if w.startswith("U")}
PAD = 30  # regional cells around the box of the U areas
MIN_MARGIN = 10  # regional cells between the window edge and any start cell with F or P > 0.01
# (n, nz): horizontal and vertical refinement; a horizontal series at 4 layers, a vertical series
# at 25 m, and 12.5 m with 8 and 16 layers; the last (finest) run is the reference
RESOLUTIONS = ((1, 1), (2, 1), (4, 1), (2, 2), (2, 4), (2, 8), (4, 2), (4, 4))
BOUNDARIES = ("chd", "flux")
SIDES = {"W": (0, -1, 1), "N": (-1, 0, 2), "E": (0, 1, 3), "S": (1, 0, 4)}  # drow, dcol, face
BOTM_FILES = ("botm_000.dat", "botm_001.dat", "botm_002.dat",
              "neversink_layer_5_new_botm_elevations.dat")
SFR_COLUMNS = ("rno", "k", "i", "j", "rlen", "rwid", "rgrd", "rtp", "rbth", "rhk", "man", "ncon",
               "ustrf", "ndv")
N_SPLIT = pm.N_SPLIT
CENTRE = pm.CENTRE
FILM_SAT = pm.FILM_SAT
NUDGE = 1e-6  # [m] moves a point on a child face into the east or south child
REACH_SAMPLES = 64  # points per half-segment of the stream line
F_CASES = pm.F_CASES
METHODS = {"F_gross": "F, gross", "F_gross_strong": "F, gross, every sink strong",
           "P": "P, 27 particles", "centre": "centre particle"}
AREA_T = 0.5
ACTIVE = 0.01
# Gates for the 1x window against the regional run: largest head difference [m] and the
# Jaccard index of every > 0.5 area (F and P)
MAX_DH = 0.05
MIN_JACCARD = 0.95
ADJOINT_DIR = HERE.parent / "comparison"
ALPHA_T = 1.0  # [m] transverse dispersivity of the physical reference
ADJOINT_ATOL = 1e-6  # no-dispersion adjoint against F (the synthetic study asserts 1e-8)
# Edge outflows of the flux boundary are reduced where the head falls below the cell bottom plus
# this share of the thickness (MF6 AUTO_FLOW_REDUCE). Without it the refined windows do not
# converge: at the north and south edges thin wet layers lose water out of the window, and a
# fixed outflow there makes Newton cycle (0.001 still cycled at 12.5 m with 8 layers). The
# reductions are reported per run (the 1x window included) and asserted below
# MAX_EDGE_REDUCTION of the edge outflow.
EDGE_AFR = 0.05
AFR_CSV = "edge_afr.csv"
MAX_EDGE_REDUCTION = 0.03


# ---------------------------------------------------------------- regional model


@dataclass
class Regional:
    """Arrays and lists of the regional run that the window needs (0-based indices)."""

    top: np.ndarray
    botm: np.ndarray
    idomain: np.ndarray
    k: np.ndarray
    k33: np.ndarray
    irch: np.ndarray
    rch: np.ndarray
    head: np.ndarray
    sat: np.ndarray
    wells: pd.DataFrame
    chd: pd.DataFrame
    reaches: pd.DataFrame
    up: dict
    down: dict
    inflow: dict
    reach_flow: dict
    ia: np.ndarray
    ja: np.ndarray
    flowja: np.ndarray


def build_regional(ws: Path, exe: Path) -> float:
    """Copy the calibrated model (tight criteria, RCH and SFR on the open top face); run it."""
    wf.prepare_model(ws, dvclose=wf.TIGHT_DVCLOSE)
    mp7.add_iflowface(ws)
    return wf.run_mf6(ws, exe)


def read_array(path: Path, shape: tuple) -> np.ndarray:
    """Return a free-format text array of the given shape."""
    values = np.array(path.read_text(encoding="utf-8").split(), dtype=float)
    assert values.size == np.prod(shape), f"{path.name}: {values.size} values, not {shape}"
    return values.reshape(shape)


def sfr_block(sfr_file: Path, block: str) -> list[list[str]]:
    """Return the split lines of one block of an SFR input file."""
    lines, inside = [], False
    for line in sfr_file.read_text(encoding="utf-8").splitlines():
        words = line.split()
        if not words or words[0].startswith("#"):
            continue
        if words[0].upper() == "BEGIN" and words[1].upper() == block.upper():
            inside = True
        elif words[0].upper() == "END" and inside:
            return lines
        elif inside:
            lines.append(words)
    raise AssertionError(f"no {block} block in {sfr_file}")


def read_sfr(ws: Path) -> tuple[pd.DataFrame, dict, dict, dict, dict]:
    """Return the reaches, their upstream and downstream reaches, inflows and reach-to-reach flows.

    reach_flow[(r, u)] is the regional flow into reach r from reach u (SFR budget).
    """
    data = np.loadtxt(ws / "neversink_packagedata.dat", comments="#", usecols=range(14), ndmin=2)
    reaches = pd.DataFrame(data, columns=SFR_COLUMNS)
    for col in ("rno", "k", "i", "j"):
        reaches[col] = reaches[col].astype(int) - 1
    assert np.array_equal(reaches["rno"], np.arange(len(reaches))), "reaches are not in order"
    assert (reaches["ndv"] == 0).all() and (reaches["ustrf"] == 1.0).all(), "diversions found"
    up, down = {}, {}
    for words in sfr_block(ws / f"{MODEL}.sfr", "connectiondata"):
        r, ic = int(words[0]) - 1, [int(w) for w in words[1:]]
        up[r] = [c - 1 for c in ic if c > 0]
        down[r] = [-c - 1 for c in ic if c < 0]
    assert all(len(d) <= 1 for d in down.values()), "a reach with two downstream reaches"
    inflow = {}
    for words in sfr_block(ws / f"{MODEL}.sfr", "period"):
        assert words[1].lower() == "inflow", f"SFR period setting {words[1]} is not handled"
        inflow[int(words[0]) - 1] = float(words[2])
    rec = flopy.utils.CellBudgetFile(ws / f"{MODEL}.sfr.cbc").get_data(text="FLOW-JA-FACE")[0]
    reach_flow = {(int(n) - 1, int(m) - 1): float(q) for n, m, q in
                  zip(rec["node"], rec["node2"], rec["q"])}
    return reaches, up, down, inflow, reach_flow


def read_regional(ws: Path) -> Regional:
    """Read the regional input arrays and lists, heads, saturation and flows."""
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{MODEL}.dis.grb", verbose=False)
    shape = (grb.nlay, grb.nrow, grb.ncol)
    plan = shape[1:]
    botm = np.stack([read_array(ws / f, plan) for f in BOTM_FILES])
    assert np.allclose(botm.ravel(), grb.bot), "bottoms differ from the binary grid"
    head = flopy.utils.HeadFile(ws / f"{MODEL}.hds").get_data()
    sat = mp7.cell_saturation(ws / f"{MODEL}.cbc", int(np.prod(shape))).reshape(shape)
    wells = pd.read_csv(ws / "wel_000.dat", sep=r"\s+", comment="#",
                        names=["k", "i", "j", "q", "name"])
    chd = pd.read_csv(ws / "chd_000.dat", sep=r"\s+", comment="#", names=["k", "i", "j", "head"])
    for frame in (wells, chd):
        frame[["k", "i", "j"]] -= 1
    reaches, up, down, inflow, reach_flow = read_sfr(ws)
    flowja = flopy.utils.CellBudgetFile(ws / f"{MODEL}.cbc").get_data(text="FLOW-JA-FACE")[0]
    return Regional(
        top=read_array(ws / "top.dat", plan), botm=botm, idomain=wf.grid_idomain(ws),
        k=np.stack([read_array(ws / f"k{i}.dat", plan) for i in range(shape[0])]),
        k33=np.stack([read_array(ws / f"k33{i}.dat", plan) for i in range(shape[0])]),
        irch=read_array(ws / "irch.dat", plan).astype(int) - 1,
        rch=read_array(ws / "rch_000.dat", plan), head=head, sat=sat, wells=wells, chd=chd,
        reaches=reaches, up=up, down=down, inflow=inflow, reach_flow=reach_flow,
        ia=np.asarray(grb.ia), ja=np.asarray(grb.ja), flowja=np.ravel(flowja),
    )


# ---------------------------------------------------------------- window and refined grid


@dataclass(frozen=True)
class Window:
    """Inclusive regional rows and columns of the window."""

    r0: int
    r1: int
    c0: int
    c1: int

    @property
    def nrow(self) -> int:
        return self.r1 - self.r0 + 1

    @property
    def ncol(self) -> int:
        return self.c1 - self.c0 + 1

    def contains(self, r: np.ndarray, c: np.ndarray, margin: int = 0) -> np.ndarray:
        """Return whether regional (row, column) lie inside, at least margin cells from the edge."""
        return ((r >= self.r0 + margin) & (r <= self.r1 - margin)
                & (c >= self.c0 + margin) & (c <= self.c1 - margin))


@dataclass(frozen=True)
class Spec:
    """A model on the window: refinement n (columns) and nz (layers), and its boundary."""

    window: Window
    n: int
    nz: int
    boundary: str

    @property
    def name(self) -> str:
        return f"n{self.n}z{self.nz}_{self.boundary}"


def choose_window(shape: tuple, nodes: np.ndarray, pad: int = PAD) -> Window:
    """Return the box of the given regional nodes plus pad cells, clipped to the grid."""
    _, nrow, ncol = shape
    r, c = np.divmod(nodes % (nrow * ncol), ncol)
    return Window(max(r.min() - pad, 0), min(r.max() + pad, nrow - 1),
                  max(c.min() - pad, 0), min(c.max() + pad, ncol - 1))


def child_index(spec: Spec, nlay: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the regional layer, row and column of every child layer, row and column."""
    w = spec.window
    layers = np.arange(nlay * spec.nz) // spec.nz
    rows = w.r0 + np.arange(w.nrow * spec.n) // spec.n
    cols = w.c0 + np.arange(w.ncol * spec.n) // spec.n
    return layers, rows, cols


def layer_edges(reg: Regional, k: int, i: int, j: int, nz: int) -> np.ndarray:
    """Return the nz + 1 elevations, top down, of the sublayers of regional cell (k, i, j)."""
    top = reg.top[i, j] if k == 0 else reg.botm[k - 1, i, j]
    edges = top - np.arange(nz + 1) / nz * (top - reg.botm[k, i, j])
    edges[-1] = reg.botm[k, i, j]
    return edges


def sublayer_shares(reg: Regional, k: int, i: int, j: int, nz: int,
                    dry_ok: bool = False) -> np.ndarray:
    """Return the share of each sublayer of a regional cell in its saturated thickness.

    dry_ok: a dry cell (Newton lets an upstream wet cell feed it) gives all to the bottom one.
    """
    edges = layer_edges(reg, k, i, j, nz)
    wet = np.clip(np.minimum(reg.head[k, i, j], edges[:-1]) - edges[1:], 0.0, None)
    if wet.sum() == 0 and dry_ok:
        wet[-1] = 1.0
    assert wet.sum() > 0, f"cell {(k, i, j)} is dry"
    return wet / wet.sum()


def grid_arrays(reg: Regional, spec: Spec) -> dict[str, np.ndarray]:
    """Return DIS, NPF, IC and recharge arrays of the refined window."""
    nlay = reg.botm.shape[0]
    layers, rows, cols = child_index(spec, nlay)
    sub = np.arange(nlay * spec.nz) % spec.nz
    tops = np.concatenate([reg.top[None], reg.botm[:-1]])
    cut = np.ix_(layers, rows, cols)
    thick = (tops - reg.botm)[cut]
    botm = tops[cut] - ((sub + 1) / spec.nz)[:, None, None] * thick
    last = sub == spec.nz - 1
    botm[last] = reg.botm[np.ix_(layers[last], rows, cols)]
    head = reg.head[cut]
    top = reg.top[np.ix_(rows, cols)]
    return {
        "top": top, "botm": botm, "idomain": reg.idomain[cut].astype(int),
        "k": reg.k[cut], "k33": reg.k33[cut],
        "strt": np.where(np.abs(head) < 1e29, head, np.broadcast_to(top, head.shape)),
        "irch": reg.irch[np.ix_(rows, cols)] * spec.nz, "rch": reg.rch[np.ix_(rows, cols)],
    }


def point_children(i: int, j: int, spec: Spec) -> list[tuple[int, int]]:
    """Return the child (row, column) that touch the centre of regional column (i, j)."""
    n, w = spec.n, spec.window
    ri, cj = (i - w.r0) * n + n // 2, (j - w.c0) * n + n // 2
    if n % 2:
        return [(ri, cj)]
    return [(ri - a, cj - b) for a in (1, 0) for b in (1, 0)]


def refined_wells(reg: Regional, spec: Spec) -> pd.DataFrame:
    """Return the wells of the window as child cells: the rate split over the centre children."""
    w = spec.window
    rows = []
    inside = reg.wells[w.contains(reg.wells["i"], reg.wells["j"])]
    for well in inside.itertuples():
        cells = point_children(well.i, well.j, spec)
        shares = sublayer_shares(reg, well.k, well.i, well.j, spec.nz)
        for s, share in enumerate(shares):
            for r, c in cells:
                if share > 0:
                    rows.append((well.k * spec.nz + s, r, c, well.q * share / len(cells), well.name))
    out = pd.DataFrame(rows, columns=["k", "i", "j", "q", "name"])
    assert np.allclose(out.groupby("name")["q"].sum(), inside.groupby("name")["q"].sum())
    return out


def children_of(i: int, j: int, spec: Spec, side: str | None = None) -> list[tuple[int, int]]:
    """Return the child (row, column) of a regional column, or only those on one side of it."""
    n, w = spec.n, spec.window
    ri, cj = (i - w.r0) * n, (j - w.c0) * n
    rr = {"N": [ri], "S": [ri + n - 1]}.get(side, list(range(ri, ri + n)))
    cc = {"W": [cj], "E": [cj + n - 1]}.get(side, list(range(cj, cj + n)))
    return [(r, c) for r in rr for c in cc]


def wet_sublayers(reg: Regional, k: int, i: int, j: int, nz: int, head: float) -> list[int]:
    """Return the sublayers of a regional cell whose bottom lies below head."""
    edges = layer_edges(reg, k, i, j, nz)
    return [s for s in range(nz) if head > edges[s + 1]]


def refined_chd(reg: Regional, spec: Spec) -> pd.DataFrame:
    """Return the regional CHD cells inside the window as child cells (every wet child)."""
    w = spec.window
    rows = []
    for cell in reg.chd[w.contains(reg.chd["i"], reg.chd["j"])].itertuples():
        for s in wet_sublayers(reg, cell.k, cell.i, cell.j, spec.nz, cell.head):
            for r, c in children_of(cell.i, cell.j, spec):
                rows.append((cell.k * spec.nz + s, r, c, cell.head))
    return pd.DataFrame(rows, columns=["k", "i", "j", "head"])


def connection_flow(reg: Regional, n: int, m: int) -> float | None:
    """Return the regional flow into cell n from cell m, or None if they are not connected."""
    seg = slice(reg.ia[n] + 1, reg.ia[n + 1])
    hit = np.flatnonzero(reg.ja[seg] == m)
    return float(reg.flowja[seg][hit[0]]) if hit.size else None


def edge_faces(reg: Regional, win: Window) -> pd.DataFrame:
    """Return every face of the window edge with an active regional cell on both sides.

    q_in is the regional flow into the window cell through that face.
    """
    nlay, nrow, ncol = reg.idomain.shape
    edge = {"W": [(i, win.c0) for i in range(win.r0, win.r1 + 1)],
            "E": [(i, win.c1) for i in range(win.r0, win.r1 + 1)],
            "N": [(win.r0, j) for j in range(win.c0, win.c1 + 1)],
            "S": [(win.r1, j) for j in range(win.c0, win.c1 + 1)]}
    rows = []
    for side, cells in edge.items():
        dr, dc, face = SIDES[side]
        for i, j in cells:
            io, jo = i + dr, j + dc
            if not (0 <= io < nrow and 0 <= jo < ncol):
                continue
            for k in range(nlay):
                if reg.idomain[k, i, j] <= 0 or reg.idomain[k, io, jo] <= 0:
                    continue
                n = np.ravel_multi_index((k, i, j), (nlay, nrow, ncol))
                m = np.ravel_multi_index((k, io, jo), (nlay, nrow, ncol))
                q = connection_flow(reg, n, m)
                if q is not None:
                    dh = reg.head[k, io, jo] - reg.head[k, i, j]
                    rows.append((k, i, j, side, face, q, dh))
    faces = pd.DataFrame(rows, columns=["k", "i", "j", "side", "iflowface", "q_in", "dh_in"])
    clear = (np.abs(faces["dh_in"]) > 1e-3) & (faces["q_in"] != 0.0)  # q = 0: a dry side
    agree = np.mean(np.sign(faces["q_in"][clear]) == np.sign(faces["dh_in"][clear]))
    assert agree > 0.99, f"edge flow and head difference agree in sign for only {agree:.3f}"
    return faces


def edge_chd(reg: Regional, spec: Spec, faces: pd.DataFrame) -> pd.DataFrame:
    """Return CHD at the regional head on the outermost children of the wet edge cells."""
    rows = []
    for f in faces.itertuples():
        if reg.sat[f.k, f.i, f.j] <= 0:
            continue
        head = float(reg.head[f.k, f.i, f.j])
        for s in wet_sublayers(reg, f.k, f.i, f.j, spec.nz, head):
            for r, c in children_of(f.i, f.j, spec, f.side):
                rows.append((f.k * spec.nz + s, r, c, head))
    return pd.DataFrame(rows, columns=["k", "i", "j", "head"]).drop_duplicates(["k", "i", "j"])


def edge_flux(reg: Regional, spec: Spec, faces: pd.DataFrame) -> pd.DataFrame:
    """Return the edge flows as WEL terms on the outermost children, on the face (IFLOWFACE)."""
    rows = []
    for f in faces.itertuples():
        if f.q_in == 0.0:
            continue
        shares = sublayer_shares(reg, f.k, f.i, f.j, spec.nz, dry_ok=True)
        children = children_of(f.i, f.j, spec, f.side)
        for s, share in enumerate(shares):
            for r, c in children:
                if share > 0:
                    rows.append((f.k * spec.nz + s, r, c, f.q_in * share / len(children),
                                 f.iflowface))
    out = pd.DataFrame(rows, columns=["k", "i", "j", "q", "iflowface"])
    assert np.isclose(out["q"].sum(), faces["q_in"].sum()), "edge flows lost"
    return out


# ---------------------------------------------------------------- streams


def window_reaches(reg: Regional, win: Window) -> np.ndarray:
    """Return the regional reaches inside the window."""
    r = reg.reaches
    return r.loc[win.contains(r["i"], r["j"]), "rno"].to_numpy()


def reach_line(reg: Regional, rno: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return the reach's part of the stream line, in flow order, as (start, end) points.

    Points are (row, column) in regional cell units; a reach runs from half-way to each upstream
    reach to its cell centre, then half-way to its downstream reach.
    """
    centre = reg.reaches.loc[rno, ["i", "j"]].to_numpy(dtype=float) + 0.5
    other = lambda q: reg.reaches.loc[q, ["i", "j"]].to_numpy(dtype=float) + 0.5  # noqa: E731
    parts = [(0.5 * (other(u) + centre), centre) for u in reg.up.get(rno, [])]
    parts += [(centre, 0.5 * (centre + other(d))) for d in reg.down.get(rno, [])]
    return [(a, b) for a, b in parts if np.hypot(*(b - a)) > 0]


def reach_children(reg: Regional, rno: int, spec: Spec, m: int = REACH_SAMPLES) -> pd.DataFrame:
    """Return the child (row, column) cells along a reach, in flow order, with their share."""
    w = spec.window
    i, j = reg.reaches.loc[rno, ["i", "j"]].astype(int)
    parts = reach_line(reg, rno)
    t = (np.arange(m) + 0.5) / m
    if parts:
        pts = np.concatenate([a + t[:, None] * (b - a) for a, b in parts])
        wts = np.concatenate([np.full(m, np.hypot(*(b - a)) / m) for a, b in parts])
    else:  # isolated reach or all neighbours in the same cell: the cell centre
        pts, wts = np.array([[i + 0.5 + NUDGE, j + 0.5 + NUDGE]]), np.ones(1)
    eps = 1e-9
    pts[:, 0] = np.clip(pts[:, 0], i + eps, i + 1 - eps)
    pts[:, 1] = np.clip(pts[:, 1], j + eps, j + 1 - eps)
    frame = pd.DataFrame({"i": np.floor((pts[:, 0] - w.r0) * spec.n).astype(int),
                          "j": np.floor((pts[:, 1] - w.c0) * spec.n).astype(int), "w": wts})
    cells = frame.groupby(["i", "j"], sort=False)["w"].sum().reset_index()
    cells["share"] = cells["w"] / cells["w"].sum()
    return cells[["i", "j", "share"]]


def reach_sublayer(reg: Regional, reach: pd.Series, nz: int) -> int:
    """Return the sublayer of the reach cell that holds the streambed bottom (top one if above)."""
    edges = layer_edges(reg, int(reach.k), int(reach.i), int(reach.j), nz)
    bottom = reach.rtp - reach.rbth
    assert bottom >= edges[-1] - 1e-6, f"reach {reach.rno}: streambed below the cell bottom"
    return int(np.clip(np.searchsorted(-edges[1:], -bottom), 0, nz - 1))


def refined_sfr(reg: Regional, spec: Spec, open_top: np.ndarray) -> dict:
    """Return the packagedata, connections and inflows of the window's (sub-)reaches.

    A reach whose upstream reach lies outside the window gets that reach's regional flow into
    it as inflow (plus its own regional inflow, if any).
    """
    ids = window_reaches(reg, spec.window)
    inside = set(ids.tolist())
    rows, first, last = [], {}, {}
    for rno in ids:
        reach = reg.reaches.loc[rno]
        s = reach_sublayer(reg, reach, spec.nz)
        k = int(reach.k) * spec.nz + s
        cells = reach_children(reg, rno, spec)
        first[rno] = len(rows)
        for c in cells.itertuples():
            rows.append({"k": k, "i": c.i, "j": c.j, "rlen": reach.rlen * c.share,
                         "rwid": reach.rwid, "rgrd": reach.rgrd, "rtp": reach.rtp,
                         "rbth": reach.rbth, "rhk": reach.rhk, "man": reach.man,
                         "iflowface": -1 if open_top[k, c.i, c.j] else 0, "parent": rno})
        last[rno] = len(rows) - 1
    length = pd.DataFrame(rows).groupby("parent")["rlen"].sum()
    assert np.allclose(length.to_numpy(), reg.reaches.loc[length.index, "rlen"]), "reach length"
    up = {s: [] for s in range(len(rows))}
    down = {s: [] for s in range(len(rows))}
    for rno in ids:
        for s in range(first[rno], last[rno]):
            down[s].append(s + 1)
            up[s + 1].append(s)
        for d in reg.down.get(rno, []):
            if d in inside:
                down[last[rno]].append(first[d])
                up[first[d]].append(last[rno])
    inflow = {}
    for rno in ids:
        q = reg.inflow.get(rno, 0.0)
        q += sum(reg.reach_flow[(rno, u)] for u in reg.up.get(rno, []) if u not in inside)
        if q != 0.0:
            assert q > 0, f"reach {rno}: negative inflow {q}"
            inflow[first[rno]] = q
    return {"packagedata": pd.DataFrame(rows), "up": up, "down": down, "inflow": inflow}


def write_sfr(ws: Path, sfr: dict) -> None:
    """Write the SFR file (1-based input) and add it to the model name file."""
    data = sfr["packagedata"]
    lines = ["BEGIN options", "  AUXILIARY  IFLOWFACE", "  SAVE_FLOWS",
             f"  BUDGET  FILEOUT  {MODEL}.sfr.cbc", "  UNIT_CONVERSION  86400.0", "END options",
             "", "BEGIN dimensions", f"  NREACHES  {len(data)}", "END dimensions", "",
             "BEGIN packagedata"]
    for s, r in enumerate(data.itertuples()):
        ncon = len(sfr["up"][s]) + len(sfr["down"][s])
        lines.append(f"  {s + 1} {r.k + 1} {r.i + 1} {r.j + 1} {r.rlen:.10g} {r.rwid:.10g} "
                     f"{r.rgrd:.10g} {r.rtp:.10g} {r.rbth:.10g} {r.rhk:.10g} {r.man:.10g} "
                     f"{ncon} 1.0 0 {r.iflowface}")
    lines += ["END packagedata", "", "BEGIN connectiondata"]
    for s in range(len(data)):
        ic = [u + 1 for u in sfr["up"][s]] + [-(d + 1) for d in sfr["down"][s]]
        lines.append("  " + " ".join(str(v) for v in [s + 1, *ic]))
    lines += ["END connectiondata", "", "BEGIN period  1"]
    lines += [f"  {s + 1}  inflow  {q:.10g}" for s, q in sfr["inflow"].items()]
    lines += ["END period  1", ""]
    (ws / f"{MODEL}.sfr").write_text("\n".join(lines), encoding="utf-8")
    nam = ws / f"{MODEL}.nam"
    text = nam.read_text(encoding="utf-8")
    assert "END packages" in text, "no packages block in the name file"
    nam.write_text(text.replace("END packages", f"  SFR6  {MODEL}.sfr  sfr_0\nEND packages"), encoding="utf-8")


# ---------------------------------------------------------------- window model


def write_window(ws: Path, reg: Regional, spec: Spec, faces: pd.DataFrame, exe: Path) -> dict:
    """Write the window model of spec into ws; return counts of its parts."""
    if ws.exists():
        shutil.rmtree(ws)
    a = grid_arrays(reg, spec)
    nlay, nrow, ncol = a["botm"].shape
    sim = flopy.mf6.MFSimulation(sim_name="mfsim", sim_ws=str(ws), exe_name=str(exe),
                                 verbosity_level=0)
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="days")
    flopy.mf6.ModflowIms(
        sim, complexity="complex", outer_dvclose=wf.TIGHT_DVCLOSE[0], outer_maximum=200,
        under_relaxation="dbd", under_relaxation_gamma=0.0, under_relaxation_theta=0.7,
        under_relaxation_kappa=0.1, under_relaxation_momentum=0.0, backtracking_number=0,
        inner_maximum=175, inner_dvclose=wf.TIGHT_DVCLOSE[1], rcloserecord=[1000.0, "strict"],
        linear_acceleration="bicgstab", relaxation_factor=0.0, preconditioner_levels=0,
        preconditioner_drop_tolerance=0.001, number_orthogonalizations=0,
        scaling_method="none", reordering_method="none",
    )
    gwf = flopy.mf6.ModflowGwf(sim, modelname=MODEL, newtonoptions="under_relaxation",
                               save_flows=True)
    size = CELL / spec.n
    flopy.mf6.ModflowGwfdis(gwf, length_units="meters", nlay=nlay, nrow=nrow, ncol=ncol,
                            delr=size, delc=size, top=a["top"], botm=a["botm"],
                            idomain=a["idomain"])
    flopy.mf6.ModflowGwfic(gwf, strt=a["strt"])
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=1, k=a["k"], k33=a["k33"], save_flows=True,
                            save_specific_discharge=True, save_saturation=True)
    r, c = np.nonzero(a["rch"] != 0)
    kr = a["irch"][r, c]
    on = a["idomain"][kr, r, c] > 0
    recharge = [((kk, rr, cc), q, -1) for kk, rr, cc, q in
                zip(kr[on], r[on], c[on], a["rch"][r[on], c[on]])]
    flopy.mf6.ModflowGwfrch(gwf, auxiliary=["IFLOWFACE"], save_flows=True,
                            stress_period_data={0: recharge}, pname="rch_0")
    wells = refined_wells(reg, spec)
    flopy.mf6.ModflowGwfwel(gwf, boundnames=True, save_flows=True, pname="wel_0",
                            stress_period_data={0: [((w.k, w.i, w.j), w.q, w.name)
                                                    for w in wells.itertuples()]})
    chd = refined_chd(reg, spec)
    if len(chd):
        flopy.mf6.ModflowGwfchd(gwf, save_flows=True, pname="chd_0", filename=f"{MODEL}.chd",
                                stress_period_data={0: [((h.k, h.i, h.j), h.head)
                                                        for h in chd.itertuples()]})
    if spec.boundary == "chd":
        edge = edge_chd(reg, spec, faces)
        flopy.mf6.ModflowGwfchd(gwf, save_flows=True, pname="chd_edge",
                                filename=f"{MODEL}.edge.chd",
                                stress_period_data={0: [((h.k, h.i, h.j), h.head)
                                                        for h in edge.itertuples()]})
    else:
        edge = edge_flux(reg, spec, faces)
        flopy.mf6.ModflowGwfwel(gwf, auxiliary=["IFLOWFACE"], save_flows=True, pname="wel_edge",
                                filename=f"{MODEL}.edge.wel", auto_flow_reduce=EDGE_AFR,
                                afrcsv_filerecord=AFR_CSV,
                                stress_period_data={0: [((e.k, e.i, e.j), e.q, e.iflowface)
                                                        for e in edge.itertuples()]})
    flopy.mf6.ModflowGwfoc(gwf, budget_filerecord=f"{MODEL}.cbc", head_filerecord=f"{MODEL}.hds",
                           saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")])
    sim.write_simulation(silent=True)
    sfr = refined_sfr(reg, spec, mp7.top_face_open(a["idomain"]))
    write_sfr(ws, sfr)
    return {"cells": int(a["idomain"].size), "active_cells": int(np.sum(a["idomain"] > 0)),
            "recharge_cells": len(recharge), "well_terms": len(wells), "chd_cells": len(chd),
            "edge_terms": len(edge), "reaches": len(sfr["packagedata"]),
            "parent_reaches": int(sfr["packagedata"]["parent"].nunique()),
            "sfr_inflow": float(sum(sfr["inflow"].values()))}


def edge_reduction(ws: Path, faces: pd.DataFrame) -> dict:
    """Return the edge outflow cut by AUTO_FLOW_REDUCE and its share of the edge outflow."""
    path = ws / AFR_CSV
    cut = float(-pd.read_csv(path)["wel-reduction"].sum()) if path.exists() else 0.0
    outflow = float(-faces.loc[faces["q_in"] < 0, "q_in"].sum())
    share = cut / outflow
    assert share < MAX_EDGE_REDUCTION, f"edge outflow reduced by {share:.3%}"
    return {"edge_outflow": outflow, "edge_outflow_reduced": cut, "edge_reduced_share": share}


def list_discrepancy(ws: Path) -> float:
    """Return the volumetric budget's percent discrepancy from the model list file."""
    lines = [ln for ln in (ws / f"{MODEL}.lst").read_text(encoding="utf-8").splitlines()
             if "PERCENT DISCREPANCY" in ln]
    assert lines, "no budget in the list file"
    return float(lines[-1].split("=")[1].split()[0])


# ---------------------------------------------------------------- flow check (1x)


def term_by_cell(cbc: Path, text: str, n_cells: int) -> np.ndarray:
    """Return the net flow per cell of the packages of one budget text, without the edge terms.

    The window's edge CHD or WEL terms are a package of their own (name ending in "EDGE").
    """
    budget = flopy.utils.CellBudgetFile(cbc)
    out = np.zeros(n_cells)
    for idx in np.flatnonzero(budget.recordarray["text"] == text.rjust(16).encode()):
        if budget.recordarray["paknam2"][idx].decode().strip().upper().endswith("EDGE"):
            continue
        rec = budget.get_record(int(idx))
        np.add.at(out, rec["node"] - 1, rec["q"])
    return out


def window_nodes(win: Window, shape: tuple) -> np.ndarray:
    """Return the regional node of every cell of a 1x window (window node order)."""
    index = np.ix_(range(shape[0]), range(win.r0, win.r1 + 1), range(win.c0, win.c1 + 1))
    return np.ravel_multi_index(index, shape).ravel()


def flow_check(reg_ws: Path, win_ws: Path, win: Window, shape: tuple) -> dict:
    """Compare heads, cell-to-cell flows and boundary flows of a 1x window with the regional run.

    Heads: active cells wet in both runs. Flows: faces between window cells, and those between
    cells off the edge ring ("interior"). Boundary flows: RCH, WEL, SFR and CHD of the model's own
    packages (not the edge terms) summed over the window cells, and the largest cell difference.
    """
    reg_node = window_nodes(win, shape)
    n_reg, n_win = int(np.prod(shape)), reg_node.size
    h_reg = flopy.utils.HeadFile(reg_ws / f"{MODEL}.hds").get_data().ravel()[reg_node]
    h_win = flopy.utils.HeadFile(win_ws / f"{MODEL}.hds").get_data().ravel()
    s_reg = mp7.cell_saturation(reg_ws / f"{MODEL}.cbc", n_reg)[reg_node]
    s_win = mp7.cell_saturation(win_ws / f"{MODEL}.cbc", n_win)
    _, rr, cc = np.unravel_index(np.arange(n_win), (shape[0], win.nrow, win.ncol))
    interior = (rr > 0) & (rr < win.nrow - 1) & (cc > 0) & (cc < win.ncol - 1)
    wet = (s_reg > 0) & (s_win > 0)
    dh = np.abs(h_win - h_reg)
    out = {"wet_cells": int(wet.sum()),
           "wet_status_differs": int(np.sum((s_reg > 0) != (s_win > 0))),
           "max_dh_m": float(dh[wet].max()), "max_dh_interior_m": float(dh[wet & interior].max()),
           "mean_dh_m": float(dh[wet].mean())}
    grb_r = flopy.mf6.utils.MfGrdFile(reg_ws / f"{MODEL}.dis.grb", verbose=False)
    grb_w = flopy.mf6.utils.MfGrdFile(win_ws / f"{MODEL}.dis.grb", verbose=False)
    q_reg = flopy.utils.CellBudgetFile(reg_ws / f"{MODEL}.cbc").get_data(text="FLOW-JA-FACE")[0]
    q_win = flopy.utils.CellBudgetFile(win_ws / f"{MODEL}.cbc").get_data(text="FLOW-JA-FACE")[0]
    reg_matrix = sp.csr_matrix((np.ravel(q_reg), grb_r.ja, grb_r.ia), shape=(n_reg, n_reg))
    ia, ja = np.asarray(grb_w.ia), np.asarray(grb_w.ja)
    row = np.repeat(np.arange(n_win), np.diff(ia))
    face = row != ja
    q_w = np.ravel(q_win)[face]
    q_r = np.asarray(reg_matrix[reg_node[row[face]], reg_node[ja[face]]]).ravel()
    inner = interior[row[face]] & interior[ja[face]]
    dq = np.abs(q_w - q_r)
    out.update({"max_abs_q": float(np.abs(q_r).max()), "max_dq": float(dq.max()),
                "max_dq_interior": float(dq[inner].max()),
                "sum_dq_over_sum_q": float(dq.sum() / np.abs(q_r).sum())})
    for text in ("RCH", "WEL", "SFR", "CHD"):
        win_total = term_by_cell(win_ws / f"{MODEL}.cbc", text, n_win)
        reg_text = {"RCH": "RCHA"}.get(text, text)
        reg_total = term_by_cell(reg_ws / f"{MODEL}.cbc", reg_text, n_reg)[reg_node]
        out[f"{text}_window"] = float(win_total.sum())
        out[f"{text}_regional"] = float(reg_total.sum())
        out[f"{text}_max_cell_diff"] = float(np.abs(win_total - reg_total).max())
    return out


# ---------------------------------------------------------------- F and P on one model


def trace_u(ws: Path, wells: dict = U_WELLS) -> dict:
    """Trace the U wells (gross, and gross with every sink strong); return F, cells and checks."""
    t0 = time.perf_counter()
    step = gs.read_step(ws, boundnames=True)
    read_seconds = time.perf_counter() - t0
    groups = {"U": gs.select(step, package="WEL", boundnames=list(wells))}
    results, seconds = ss.trace_cases(step, groups, F_CASES)
    closure = gs.diagnostics.backward_closure(step, results["gross"], "U")
    assert abs(closure.error) < 1e-6, f"closure error {closure.error}"
    well_cells = np.flatnonzero(groups["U"].cells)
    well_rate = float(-step.term_flow[groups["U"].terms].sum())
    package_flows = {}
    for i, pkg in enumerate(step.packages):
        q = step.term_flow[step.term_package == i]
        package_flows[f"in_{pkg.name}"] = float(q[q > 0].sum())
        package_flows[f"out_{pkg.name}"] = float(q[q < 0].sum())
    return {
        "F": {case: r.fraction_through["U"][: step.n_cells] for case, r in results.items()},
        "well_cells": well_cells,
        "checks": {"u_well_rate": well_rate, "u_inflow_gross": results["gross"].destination_inflow["U"],
                   "closure_error": closure.error, "budget_relative_residual":
                   gs.diagnostics.budget_error(step)["relative"], "read_seconds": read_seconds,
                   **{f"trace_seconds_{k}": v for k, v in seconds.items()}, **package_flows},
    }


@dataclass
class ModelGrid:
    """What the release needs of a model: its DIS arrays and saturation, and where it sits."""

    top: np.ndarray
    botm: np.ndarray
    idomain: np.ndarray
    sat: np.ndarray
    spec: Spec


def model_grid(ws: Path, spec: Spec) -> ModelGrid:
    """Read the DIS arrays and the saturation of a model run."""
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{MODEL}.dis.grb", verbose=False)
    shape = (grb.nlay, grb.nrow, grb.ncol)
    sat = mp7.cell_saturation(ws / f"{MODEL}.cbc", int(np.prod(shape))).reshape(shape)
    return ModelGrid(top=np.asarray(grb.top).reshape(shape[1:]),
                     botm=np.asarray(grb.bot).reshape(shape), idomain=wf.grid_idomain(ws),
                     sat=sat, spec=spec)


def release_points(grid: ModelGrid, node0: np.ndarray, reg_shape: tuple) -> dict[str, np.ndarray]:
    """Return cell, x, y and local z of the 27 points of every start, shaped (start, z, y, x).

    The points sit at local 1/6, 1/2 and 5/6 of the original (regional) start cell. Height: the
    same fraction of the saturated thickness of the original layer in the child column, the
    first layer from the start layer down with a saturated thickness (cells wet by less than
    FILM_SAT count as dry).
    """
    spec, w = grid.spec, grid.spec.window
    _, nrow_reg, ncol_reg = reg_shape
    nlay_c, nrow_c, ncol_c = grid.botm.shape
    nlay = nlay_c // spec.nz
    k0, rc = np.divmod(node0, nrow_reg * ncol_reg)
    r, c = np.divmod(rc, ncol_reg)
    assert w.contains(r, c).all(), "a start lies outside the window"
    local = (np.arange(N_SPLIT) + 0.5) / N_SPLIT
    lz, ly, lx = np.meshgrid(local, local, local, indexing="ij")
    size = CELL / spec.n
    height = w.nrow * CELL
    x = (c - w.c0)[:, None, None, None] * CELL + lx[None] * CELL + NUDGE
    y = height - (r - w.r0 + 1)[:, None, None, None] * CELL + ly[None] * CELL - NUDGE
    col = np.floor(x / size).astype(int).ravel()
    row = np.floor((height - y) / size).astype(int).ravel()
    zeta = np.broadcast_to(lz[None], x.shape).ravel()
    start_layer = np.broadcast_to(k0[:, None, None, None], x.shape).ravel()
    tops = np.concatenate([grid.top[None], grid.botm[:-1]])
    wet = np.where((grid.sat >= FILM_SAT) & (grid.idomain > 0), grid.sat * (tops - grid.botm), 0.0)
    wet_cols = wet[:, row, col].reshape(nlay, spec.nz, -1)  # (layer, sublayer top down, point)
    total = wet_cols.sum(axis=1)
    total[np.arange(nlay)[:, None] < start_layer[None]] = 0.0
    assert (total > 0).any(axis=0).all(), "a point has no wet layer below its start"
    layer = np.argmax(total > 0, axis=0)
    pts = np.arange(len(layer))
    subs = wet_cols[layer, :, pts][:, ::-1]  # (point, sublayer bottom up)
    depth = zeta * total[layer, pts]
    cum = np.cumsum(subs, axis=1)
    idx = np.argmax(cum >= depth[:, None] - 1e-12, axis=1)
    below = cum[pts, idx] - subs[pts, idx]
    z_local = (depth - below) / subs[pts, idx]
    assert np.all(subs[pts, idx] > 0) and np.all((z_local > 0) & (z_local <= 1 + 1e-9))
    child_layer = layer * spec.nz + (spec.nz - 1 - idx)
    cell = np.ravel_multi_index((child_layer, row, col), grid.botm.shape)
    shape = x.shape
    return {"cell": cell.reshape(shape), "x": np.broadcast_to(x, shape).copy(),
            "y": np.broadcast_to(y, shape).copy(), "z": np.minimum(z_local, 1.0).reshape(shape)}


def run_particles(ws: Path, points: dict, exe: Path, prt_dir: Path) -> tuple[dict, dict]:
    """Run PRT (one simulation per local z level, side by side); return end points and times."""
    grid = gs.prt.load_prt_grid(ws, MODEL, "DIS")
    config = gs.prt.PrtConfig(porosity=wf.MP7_POROSITY, exit_solve_tolerance=1e-5)
    folders = []
    for level in range(N_SPLIT):
        release = pm.level_release(points, level)
        prt_ws = prt_dir / f"z{level}"
        gs.prt.write_prt(prt_ws, ws, grid, release, config, exe, MODEL,
                         budget_file=ws / f"{MODEL}.cbc", stop_at_weak_sink=True,
                         track_release=False, track_exit=False, clear_ws=True)
        folders.append(prt_ws)
    seconds = pm.run_side_by_side(folders, exe)
    n_starts = points["cell"].shape[0]
    ends = {"cell": np.full((n_starts, N_SPLIT, N_SPLIT**2), -1, dtype=np.int64),
            "status": np.full((n_starts, N_SPLIT, N_SPLIT**2), -1, dtype=np.int64)}
    for level, folder in enumerate(folders):
        run = gs.prt.endpoints(gs.prt.read_tracks(folder / "prt.trk.csv"), n_starts * N_SPLIT**2)
        for key in ends:
            ends[key][:, level] = run[key].reshape(n_starts, -1)
    shutil.rmtree(prt_dir)
    assert (ends["status"] >= 0).all(), "a particle did not terminate"
    return {k: v.reshape(n_starts, -1) for k, v in ends.items()}, seconds


def score_run(name: str, ws: Path, spec: Spec, node0: np.ndarray, reg_shape: tuple, exe: Path,
              out: Path, trace: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Trace F (unless trace is given) and run P on one model; return per-start table, summary."""
    t0 = time.perf_counter()
    trace = trace_u(ws) if trace is None else trace
    grid = model_grid(ws, spec)
    points = release_points(grid, node0, reg_shape)
    cells = points["cell"].reshape(len(node0), -1)
    ends, prt_seconds = run_particles(ws, points, exe, out / f"prt_{name}")
    hit = np.isin(ends["cell"], trace["well_cells"])
    table = pd.DataFrame({"run": name, "node0": node0,
                          "F_gross": trace["F"]["gross"][cells].mean(axis=1),
                          "F_gross_strong": trace["F"]["gross_strong"][cells].mean(axis=1),
                          "P": hit.mean(axis=1), "centre": hit[:, CENTRE].astype(float)})
    status, count = np.unique(ends["status"], return_counts=True)
    summary = {"run": name, "n": spec.n, "nz": spec.nz, "boundary": spec.boundary,
               "cell_size_m": CELL / spec.n, "layers": grid.botm.shape[0],
               "cells": int(grid.idomain.size), "particles": int(ends["cell"].size),
               "share_ending_in_U_wells": float(hit.mean()),
               **{f"particles_status_{s}": int(n) for s, n in zip(status, count)},
               **trace["checks"], "prt_seconds": prt_seconds["wall"],
               "score_seconds": time.perf_counter() - t0}
    return table, summary


# ---------------------------------------------------------------- physical reference (adjoint GWT)


def comparison_methods():
    """Import studies/comparison/methods.py (the adjoint GWT set-up of the synthetic study)."""
    assert (ADJOINT_DIR / "methods.py").is_file(), "no studies/comparison/methods.py"
    sys.path.insert(0, str(ADJOINT_DIR))
    import methods  # noqa: PLC0415

    return methods


def run_adjoint(gwf_ws: Path, reversed_file: Path, ws: Path, exe: Path, n_wells: int,
                alpha_t: float) -> np.ndarray:
    """Run steady adjoint GWT on the reversed flows; return the concentration per node.

    The set-up of comparison methods.run_adjoint (Neupauer and Wilson 1999: the U wells, now
    sources, at concentration 1, every other source at 0; UPSTREAM advection; XT3D dispersion
    with alpha_L = 10 alpha_T, alpha_T in all transverse directions; one step of ADJOINT_DAYS;
    its IMS settings), with the window's IDOMAIN, which that function does not pass on.
    """
    cm = comparison_methods()
    grid = model_grid(gwf_ws, None)
    grb = flopy.mf6.utils.MfGrdFile(gwf_ws / f"{MODEL}.dis.grb", verbose=False)
    if ws.exists():
        shutil.rmtree(ws)
    name = "adj"
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe),
                                 verbosity_level=0)
    flopy.mf6.ModflowTdis(sim, nper=1, time_units="days", perioddata=[(cm.ADJOINT_DAYS, 1, 1.0)])
    gwt = flopy.mf6.ModflowGwt(sim, modelname=name)
    flopy.mf6.ModflowIms(sim, **cm.ADJOINT_IMS, filename=f"{name}.ims")
    nlay, nrow, ncol = grid.botm.shape
    flopy.mf6.ModflowGwtdis(gwt, nlay=nlay, nrow=nrow, ncol=ncol, delr=np.asarray(grb.delr),
                            delc=np.asarray(grb.delc), top=grid.top, botm=grid.botm,
                            idomain=grid.idomain)
    flopy.mf6.ModflowGwtic(gwt, strt=0.0)
    flopy.mf6.ModflowGwtmst(gwt, porosity=wf.MP7_POROSITY)
    flopy.mf6.ModflowGwtadv(gwt, scheme="UPSTREAM")
    if alpha_t > 0.0:
        flopy.mf6.ModflowGwtdsp(gwt, alh=10.0 * alpha_t, alv=10.0 * alpha_t, ath1=alpha_t,
                                ath2=alpha_t, atv=alpha_t, diffc=0.0)
    flopy.mf6.ModflowGwtfmi(gwt, flow_imbalance_correction=True, packagedata=[
        ("GWFHEAD", str((gwf_ws / f"{MODEL}.hds").resolve())),
        ("GWFBUDGET", str(reversed_file.resolve()))])
    flopy.mf6.ModflowUtlspc(gwt, maxbound=n_wells, filename="wells.spc", pname="spc_wells",
                            perioddata={0: [(i, "CONCENTRATION", 1.0) for i in range(n_wells)]})
    flopy.mf6.ModflowGwtssm(gwt, fileinput=[("WEL_0", "wells.spc")])
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord=f"{name}.ucn",
                           saverecord=[("CONCENTRATION", "LAST")])
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "adjoint GWT run failed:\n" + "\n".join(buff[-20:])
    conc = flopy.utils.HeadFile(str(ws / f"{name}.ucn"), text="CONCENTRATION").get_data()
    return np.asarray(conc, dtype=float).ravel()


def adjoint_part(spec: Spec, published: pd.Series, reg_shape: tuple, exe: Path, out: Path,
                 alpha_t: float = ALPHA_T) -> dict:
    """Validate the adjoint against F on the kept model of spec, then run it at alpha_t.

    Writes adjoint_cells.csv (C per start cell: the mean over its 27 release cells, as F) and
    returns the check and run times.
    """
    cm = comparison_methods()
    ws = out / spec.name
    reversed_file = ws / "reversed.cbc"
    t0 = time.perf_counter()
    cm.reverse_budget(ws / f"{MODEL}.cbc", reversed_file)
    trace = trace_u(ws)
    step_wells = len(refined_wells(read_regional(out / "regional"), spec))
    active = model_grid(ws, spec).idomain.ravel() > 0
    log = {"reverse_seconds": time.perf_counter() - t0}
    t0 = time.perf_counter()
    conc0 = run_adjoint(ws, reversed_file, ws / "adjoint_0", exe, step_wells, 0.0)
    error = float(np.abs(conc0 - trace["F"]["gross"])[active].max())
    log.update({"adjoint0_seconds": time.perf_counter() - t0, "max_abs_C0_minus_F": error})
    assert error < ADJOINT_ATOL, f"adjoint differs from F by {error:.2e}"
    t0 = time.perf_counter()
    conc = run_adjoint(ws, reversed_file, ws / f"adjoint_{alpha_t:g}", exe, step_wells, alpha_t)
    log[f"adjoint_{alpha_t:g}_seconds"] = time.perf_counter() - t0
    log["c_min"], log["c_max"] = float(conc[active].min()), float(conc[active].max())
    points = release_points(model_grid(ws, spec), published.index.to_numpy(), reg_shape)
    cells = points["cell"].reshape(len(published), -1)
    pd.DataFrame({"node0": published.index, "R_disp": conc[cells].mean(axis=1),
                  "C0": conc0[cells].mean(axis=1)}).to_csv(out / "adjoint_cells.csv",
                                                           index=False)
    return log


# ---------------------------------------------------------------- comparison and metrics


def area_metrics(value: np.ndarray, ref: np.ndarray, t: float = AREA_T,
                 active: float = ACTIVE) -> dict:
    """Return the > t area of value against that of ref (Jaccard, size ratio) and the RMSE."""
    on = (value > active) | (ref > active)
    return {"cells": int(np.sum(value > t)), "ref_cells": int(np.sum(ref > t)),
            "jaccard": wf.jaccard(value > t, ref > t),
            "size_ratio": float(np.sum(value > t) / max(np.sum(ref > t), 1)),
            "rmse_active": float(np.sqrt(np.mean((value[on] - ref[on]) ** 2))),
            "active_cells": int(on.sum())}


def check_table(cells: pd.DataFrame, flows: dict, runs: dict) -> pd.DataFrame:
    """Return the 1x windows against the regional run: flows, and F and P per method."""
    reg = cells[cells["run"] == "regional"].set_index("node0")
    rows = []
    for boundary in BOUNDARIES:
        name = Spec(None, 1, 1, boundary).name
        win = cells[cells["run"] == name].set_index("node0").loc[reg.index]
        row = {"boundary": boundary, **flows[boundary],
               "u_well_rate_window": runs[name]["u_well_rate"],
               "u_well_rate_regional": runs["regional"]["u_well_rate"]}
        for method in METHODS:
            m = area_metrics(win[method].to_numpy(), reg[method].to_numpy())
            row.update({f"{method}_cells_window": m["cells"], f"{method}_cells_regional":
                        m["ref_cells"], f"{method}_jaccard": m["jaccard"],
                        f"{method}_rmse": m["rmse_active"],
                        f"{method}_max_abs_diff": float(np.abs(win[method] - reg[method]).max())})
        rows.append(row)
    return pd.DataFrame(rows)


def metrics_table(cells: pd.DataFrame, published: pd.Series, runs: list[str],
                  references: dict) -> pd.DataFrame:
    """Return, per run, method and reference, the area metrics; and against the published area."""
    rows = []
    pub = published.to_numpy().astype(float)
    for run in runs:
        frame = cells[cells["run"] == run].set_index("node0").loc[published.index]
        for method in METHODS:
            value = frame[method].to_numpy()
            for ref_name, ref in references.items():
                rows.append({"run": run, "method": method, "reference": ref_name,
                             **area_metrics(value, ref)})
            m = area_metrics(value, pub)
            rows.append({"run": run, "method": method, "reference": "published", **m})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- figures

METHOD_STYLE = {  # colour (validated default palette slots, as the paper figures), marker, line
    "F_gross": (nfig.COLORS["cells"], "o", "-"),
    "F_gross_strong": (nfig.COLORS["cells"], "s", "--"),
    "P": (nfig.COLORS["prt"], "D", "-"),
    "centre": (nfig.COLORS["prt"], "^", ":"),
}
NLAY = 4  # regional layers


def run_label(run: str, sep: str = ", ") -> str:
    """Return 'cell size, layers' of a run name such as n2z1_flux."""
    n, nz = (int(v) for v in run.split("_")[0][1:].split("z"))
    return f"{CELL / n:g} m{sep}{NLAY * nz} layers"


def series_panels(ax_area: plt.Axes, ax_rmse: plt.Axes, metrics: pd.DataFrame, runs: list[str],
                  x: np.ndarray, reference: str) -> None:
    """Plot each method's > 0.5 area and RMSE over one series of runs."""
    for method, (color, marker, ls) in METHOD_STYLE.items():
        sub = metrics[(metrics["method"] == method) & (metrics["reference"] == reference)]
        sub = sub.set_index("run").loc[runs]
        kw = {"color": color, "marker": marker, "ls": ls, "lw": 1.5, "ms": 5,
              "label": METHODS[method]}
        ax_area.plot(x, sub["cells"], **kw)
        ax_rmse.plot(x, sub["rmse_active"], **kw)


def plot_convergence(metrics: pd.DataFrame, horizontal: list[str], vertical: list[str],
                     finest: list[str], path: Path, reference: str = "P_finest") -> None:
    """Plot the > 0.5 area and the RMSE against the finest P, per method, along both series.

    Left: cell size at 4 layers. Right: layers at 25 m, then the 12.5 m runs with more layers
    set apart. The published area is the dash-dot line.
    """
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.4), sharey="row", layout="constrained")
    xh = np.arange(len(horizontal))
    xv = np.r_[np.arange(len(vertical)), len(vertical) + 0.6 + np.arange(len(finest))]
    series_panels(axes[0, 0], axes[1, 0], metrics, horizontal, xh, reference)
    series_panels(axes[0, 1], axes[1, 1], metrics, [*vertical, *finest], xv, reference)
    published = metrics.loc[metrics["reference"] == "published", "ref_cells"].iloc[0]
    for ax in axes[0]:
        ax.axhline(published, color=nfig.INK, lw=0.8, ls="-.")
    axes[0, 0].annotate(f"published, {published} cells", (xh[-1], published), xytext=(0, 4),
                        textcoords="offset points", ha="right", va="bottom", fontsize=7,
                        color=nfig.INK)
    axes[0, 0].set_ylabel("Start cells with value > 0.5")
    axes[1, 0].set_ylabel(f"RMSE against P of the finest run\n(cells with either > {ACTIVE})")
    for row in axes:
        row[0].set_ylim(0, None)
    labels_h = [run_label(r, "\n") for r in horizontal]
    labels_v = [run_label(r, "\n") for r in [*vertical, *finest]]
    for col, (x, labels, title) in enumerate(((xh, labels_h, "cell size, 4 layers"),
                                              (xv, labels_v, "layers at 25 m; 12.5 m"))):
        for row, tag in enumerate("ac" if col == 0 else "bd"):
            ax = axes[row, col]
            ax.set_xticks(x, labels, fontsize=7)
            ax.grid(axis="y", color=nfig.GRID, lw=0.5)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.set_title(f"({tag}) {title}", loc="left", fontsize=8)
    axes[0, 0].legend(fontsize=7, frameon=False, loc="lower left")
    fig.savefig(path, dpi=300)
    plt.close(fig)


def start_grid(values: pd.Series, win: Window, reg_shape: tuple) -> np.ndarray:
    """Return a (row, column) image of the window with each start cell's value (NaN elsewhere)."""
    _, nrow, ncol = reg_shape
    image = np.full((win.nrow, win.ncol), np.nan)
    r, c = np.divmod(values.index.to_numpy() % (nrow * ncol), ncol)
    image[r - win.r0, c - win.c0] = values.to_numpy()
    return image


def plot_maps(cells: pd.DataFrame, published: pd.Series, runs: list[str], win: Window,
              reg_shape: tuple, wells: pd.DataFrame, path: Path) -> None:
    """Map F (gross) and P per start cell for each run, with the published U area outlined.

    Colour classes as the F maps of neversink_figures (viridis, edges 0.01 to 1); grey below 0.01.
    """
    rows = (("F_gross", "F, gross"), ("P", "P, 27 particles"))
    edges = np.array(nfig.F_EDGES)
    colors = plt.get_cmap(nfig.F_COLORMAP)(np.linspace(0.0, 1.0, len(edges) - 1))
    cmap = ListedColormap(colors).with_extremes(under=nfig.ACTIVE_FILL, bad="white")
    norm = BoundaryNorm(edges, cmap.N)
    pub = start_grid(published.astype(float), win, reg_shape)
    box = np.argwhere(np.nan_to_num(pub) > 0)
    pad = 12
    i0, i1 = max(box[:, 0].min() - pad, 0), min(box[:, 0].max() + pad, win.nrow - 1)
    j0, j1 = max(box[:, 1].min() - pad, 0), min(box[:, 1].max() + pad, win.ncol - 1)
    km = CELL / 1e3
    extent = (j0 * km, (j1 + 1) * km, -(i1 + 1) * km, -i0 * km)
    fig, axes = plt.subplots(len(rows), len(runs), figsize=(7.0, 3.3), sharex=True, sharey=True,
                             layout="constrained")
    yy, xx = np.mgrid[i0 : i1 + 1, j0 : j1 + 1]
    u = wells[wells["name"].isin(U_WELLS)]
    for a, (method, label) in enumerate(rows):
        for b, run in enumerate(runs):
            ax = axes[a, b]
            frame = cells[cells["run"] == run].set_index("node0").loc[published.index]
            image = start_grid(frame[method], win, reg_shape)[i0 : i1 + 1, j0 : j1 + 1]
            im = ax.imshow(image, cmap=cmap, norm=norm, extent=extent, interpolation="nearest")
            ax.contour((xx + 0.5) * km, -(yy + 0.5) * km,
                       np.nan_to_num(pub[i0 : i1 + 1, j0 : j1 + 1]), levels=[0.5],
                       colors=nfig.INK, linewidths=0.8)
            ax.plot((u["j"] - win.c0 + 0.5) * km, -(u["i"] - win.r0 + 0.5) * km, "o", ms=3.5,
                    mfc=nfig.COLORS["prt"], mec=nfig.INK, mew=0.6)
            ax.text(0.03, 0.03, f"{int(np.sum(frame[method] > AREA_T))} cells > {AREA_T}",
                    transform=ax.transAxes, fontsize=7, color=nfig.INK,
                    bbox={"fc": "white", "ec": "none", "pad": 1})
            if a == 0:
                ax.set_title(run_label(run), fontsize=8)
            if b == 0:
                ax.set_ylabel(f"{label}\nkm", fontsize=8)
            ax.tick_params(labelsize=7)
    fig.colorbar(im, ax=axes, shrink=0.8, extend="min",
                 label="Capture probability (grey: < 0.01)")
    fig.supxlabel("km (window coordinates); black line: published U contributing cells; "
                  "dots: U wells", fontsize=8)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def refinement_table(cells: pd.DataFrame, metrics: pd.DataFrame, runs: list[str],
                     published: pd.Series) -> pd.DataFrame:
    """Return per run the > 0.5 area of each method, F against P in the same run, and the
    RMSE and Jaccard index of each method against P of the finest run."""
    rows = []
    for run in runs:
        frame = cells[cells["run"] == run].set_index("node0").loc[published.index]
        row = {"run": run, "label": run_label(run) if run != "regional" else "regional, 50 m"}
        for method in METHODS:
            m = metrics[(metrics["run"] == run) & (metrics["method"] == method)]
            ref = m[m["reference"] == "P_finest"].iloc[0]
            pub = m[m["reference"] == "published"].iloc[0]
            row.update({f"{method}_cells": int(ref["cells"]),
                        f"{method}_rmse_vs_P_finest": ref["rmse_active"],
                        f"{method}_jaccard_vs_P_finest": ref["jaccard"],
                        f"{method}_jaccard_vs_published": pub["jaccard"]})
        for case in ("F_gross", "F_gross_strong"):
            fp = area_metrics(frame[case].to_numpy(), frame["P"].to_numpy())
            row[f"{case}_vs_P_same_run_rmse"] = fp["rmse_active"]
            row[f"{case}_vs_P_same_run_jaccard"] = fp["jaccard"]
        rows.append(row)
    return pd.DataFrame(rows)


def analyse_runs(published: pd.Series, win: Window, reg_shape: tuple, wells: pd.DataFrame,
                 boundary: str, out: Path) -> None:
    """Write metrics.csv, refinement.csv and the figures from the stored runs."""
    cells = pd.read_csv(out / "start_cells.csv.gz")
    names = {(n, nz): Spec(win, n, nz, boundary).name for n, nz in RESOLUTIONS}
    runs = [names[r] for r in RESOLUTIONS]
    assert set(runs) <= set(cells["run"]), f"missing runs: {set(runs) - set(cells['run'])}"
    finest = cells[cells["run"] == runs[-1]].set_index("node0").loc[published.index]
    references = {"P_finest": finest["P"].to_numpy(),
                  "F_strong_finest": finest["F_gross_strong"].to_numpy()}
    metrics = metrics_table(cells, published, ["regional", *runs], references)
    metrics.to_csv(out / "metrics.csv", index=False)
    refinement_table(cells, metrics, ["regional", *runs], published).to_csv(
        out / "refinement.csv", index=False)
    horizontal = [names[(n, 1)] for n in (1, 2, 4)]
    vertical = [names[(2, nz)] for nz in (1, 2, 4, 8)]
    finest = [names[(4, nz)] for nz in (2, 4)]
    plot_convergence(metrics, horizontal, vertical, finest, FIG_DIR / "convergence.png")
    plot_maps(cells, published, [*horizontal, runs[-1]], win, reg_shape, wells,
              FIG_DIR / "maps.png")


# ---------------------------------------------------------------- orchestration


def scored_starts(endpoints: pd.DataFrame, win: Window, reg_shape: tuple) -> pd.Series:
    """Return the published U mask of the start cells inside the window, without its edge."""
    _, nrow, ncol = reg_shape
    r, c = np.divmod(endpoints["node0"].to_numpy() % (nrow * ncol), ncol)
    inside = win.contains(r, c, margin=1)
    mask = wf.mp7_mask(endpoints, list(U_WELLS.values()))
    assert mask[~inside].sum() == 0, "published U cells outside the window"
    return pd.Series(mask[inside], index=endpoints["node0"].to_numpy()[inside], name="published")


def check_margin(cells: pd.DataFrame, win: Window, reg_shape: tuple, margin: int) -> dict:
    """Return the closest approach (cells) of a regional F or P > 0.01 start to each window edge.

    Edges on the model edge are left out of the assertion (no flow crosses them).
    """
    _, nrow, ncol = reg_shape
    reg = cells[cells["run"] == "regional"]
    on = (reg[list(METHODS)] > ACTIVE).any(axis=1).to_numpy()
    r, c = np.divmod(reg["node0"].to_numpy()[on] % (nrow * ncol), ncol)
    gaps = {"W": (c - win.c0).min(), "E": (win.c1 - c).min(), "N": (r - win.r0).min(),
            "S": (win.r1 - r).min()}
    model_edge = {"W": win.c0 == 0, "E": win.c1 == ncol - 1, "N": win.r0 == 0,
                  "S": win.r1 == nrow - 1}
    out = {f"gap_{side}_cells": int(g) for side, g in gaps.items()}
    inner = [g for side, g in gaps.items() if not model_edge[side]]
    assert min(inner) >= margin, f"window too small: {out}"
    return out


def store_run(table: pd.DataFrame, summary: dict, out: Path) -> None:
    """Replace one run's rows in start_cells.csv.gz and runs.csv (created if absent)."""
    cells_file, runs_file = out / "start_cells.csv.gz", out / "runs.csv"
    name = summary["run"]
    cells = pd.read_csv(cells_file) if cells_file.exists() else pd.DataFrame()
    runs = pd.read_csv(runs_file) if runs_file.exists() else pd.DataFrame()
    if len(cells):
        cells = cells[cells["run"] != name]
        runs = runs[runs["run"] != name]
    pd.concat([cells, table]).to_csv(cells_file, index=False)
    pd.concat([runs, pd.DataFrame([summary])]).to_csv(runs_file, index=False)


def window_run(reg: Regional, spec: Spec, faces: pd.DataFrame, published: pd.Series,
               exe: Path, out: Path, keep_model: bool) -> tuple[Path, pd.DataFrame, dict]:
    """Write, run and score one window model; return its folder, start-cell table and summary."""
    ws = out / spec.name
    t0 = time.perf_counter()
    parts = write_window(ws, reg, spec, faces, exe)
    parts["write_seconds"] = time.perf_counter() - t0
    parts["mf6_seconds"] = wf.run_mf6(ws, exe)
    parts["discrepancy_pct"] = list_discrepancy(ws)
    if spec.boundary == "flux":
        parts.update(edge_reduction(ws, faces))
    table, summary = score_run(spec.name, ws, spec, published.index.to_numpy(),
                               reg.idomain.shape, exe, out)
    summary.update(parts)
    store_run(table, summary, out)
    print(f"{spec.name}: {summary}", flush=True)
    if not keep_model:
        shutil.rmtree(ws)
    return ws, table, summary


def regional_part(reg_ws: Path, reg: Regional, endpoints: pd.DataFrame, exe: Path,
                  out: Path, log: dict) -> None:
    """Choose the window from the regional F and published area, and score the regional run."""
    reg_shape = reg.idomain.shape
    trace = trace_u(reg_ws)
    start = endpoints["node0"].to_numpy()
    f_above = np.zeros(len(start), dtype=bool)
    for f in trace["F"].values():
        f_above |= f[start] > 0.1
    box_nodes = start[f_above | wf.mp7_mask(endpoints, list(U_WELLS.values()))]
    win = choose_window(reg_shape, box_nodes)
    log["window"] = {"r0": int(win.r0), "r1": int(win.r1), "c0": int(win.c0), "c1": int(win.c1),
                     "pad": PAD, "nrow": int(win.nrow), "ncol": int(win.ncol)}
    published = scored_starts(endpoints, win, reg_shape)
    spec = Spec(Window(0, reg_shape[1] - 1, 0, reg_shape[2] - 1), 1, 1, "regional")
    table, summary = score_run("regional", reg_ws, spec, published.index.to_numpy(), reg_shape,
                               exe, out, trace)
    log["margin"] = check_margin(table, win, reg_shape, MIN_MARGIN)
    store_run(table, summary, out)


def check_part(reg_ws: Path, reg: Regional, win: Window, faces: pd.DataFrame,
               published: pd.Series, exe: Path, out: Path, log: dict) -> None:
    """Run both 1x windows, compare them with the regional run, gate and choose the boundary."""
    flows = {}
    for boundary in BOUNDARIES:
        spec = Spec(win, 1, 1, boundary)
        ws, _, summary = window_run(reg, spec, faces, published, exe, out, keep_model=True)
        flows[boundary] = {**flow_check(reg_ws, ws, win, reg.idomain.shape),
                           **{k: summary[k] for k in ("discrepancy_pct", "mf6_seconds")}}
        shutil.rmtree(ws)
    cells = pd.read_csv(out / "start_cells.csv.gz")
    runs = pd.read_csv(out / "runs.csv").set_index("run", drop=False).to_dict("index")
    check = check_table(cells, flows, runs)
    check.to_csv(out / "check_regional.csv", index=False)
    best = check.sort_values("sum_dq_over_sum_q")["boundary"].iloc[0]
    chosen = check.set_index("boundary").loc[best]
    assert chosen["max_dh_m"] < MAX_DH, f"1x window heads differ by {chosen['max_dh_m']} m"
    for method in METHODS:
        assert chosen[f"{method}_jaccard"] >= MIN_JACCARD, f"1x window: {method} differs"
    log["boundary"] = best


def main(run_regional: bool = True, run_check: bool = True,
         refine: tuple = RESOLUTIONS[1:], analyse: bool = True, keep_models: bool = False,
         out: Path = OUT_DIR) -> None:
    """Build and score the regional run, the 1x check and the refined windows in refine.

    Each part writes its rows to start_cells.csv.gz and runs.csv, so parts can be rerun alone.
    """
    exe = wf.mf6_exe()
    out.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)
    log_file = out / "run_log.json"
    log = json.loads(log_file.read_text(encoding="utf-8")) if log_file.exists() else {}
    reg_ws = out / "regional"
    if run_regional:
        log["regional_mf6_seconds"] = build_regional(reg_ws, exe)
    reg = read_regional(reg_ws)
    reg_shape = reg.idomain.shape
    endpoints = wf.read_endpoints()
    if run_regional:
        regional_part(reg_ws, reg, endpoints, exe, out, log)
        log_file.write_text(json.dumps(log, indent=1), encoding="utf-8")
    win = Window(**{k: log["window"][k] for k in ("r0", "r1", "c0", "c1")})
    published = scored_starts(endpoints, win, reg_shape)
    faces = edge_faces(reg, win)
    faces.to_csv(out / "edge_faces.csv", index=False)
    if run_check:
        check_part(reg_ws, reg, win, faces, published, exe, out, log)
        log_file.write_text(json.dumps(log, indent=1), encoding="utf-8")
    for n, nz in refine:
        window_run(reg, Spec(win, n, nz, log["boundary"]), faces, published, exe, out,
                   keep_models)
    log_file.write_text(json.dumps(log, indent=1), encoding="utf-8")
    if analyse:
        analyse_runs(published, win, reg_shape, reg.wells, log["boundary"], out)
    if not keep_models and analyse:
        shutil.rmtree(reg_ws)


if __name__ == "__main__":
    main()
