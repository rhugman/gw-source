"""Thin helper to check Eulerian travel times against forward particle tracking with MF6 PRT.

What it does
------------
1. Contributing cells: cells whose backward fraction F to the destination group exceeds a
   threshold (under full mixing F = 0 means no flow path, so no particle could arrive either).
2. Release points: one set per source term (positive external flow, optionally restricted to a
   source Selection) in a contributing cell, placed where PRT's velocity field brings that
   term's water in. Every point carries an equal-area (or equal-length) share of q_term, so
   sums over particles are flux-weighted.
   Plan points: the cell's plan polygon (DIS or DISV) is split into a fan of triangles from its
   centroid, each triangle into k x k equal sub-triangles, and a point is placed at each
   sub-triangle's centroid (weight = sub-triangle area / cell area).
   Distributed terms (IFLOWFACE = 0, or no IFLOWFACE auxiliary): each plan point is released
   at z_levels local z = (i + 0.5) / z_levels (fractions of the saturated thickness), so the
   points fill the cell volume. That is how MF6 represents a boundary source by default:
   recharge, river or drain leakage and edge CHD/GHB inflow are distributed over the cell, and
   PRT's velocity field has the matching uniform divergence. Releasing everything at one
   height is not consistent with that field. In particular release_z=1 (the water table)
   traps the particles of the top layer at the water table: the top face carries no flow, so
   the vertical velocity there is zero and they never descend (in a 3-layer test model all of
   them ended in layer 1 and none reached a well in layer 3).
   Face terms: a package can assign its flow to a cell face with the auxiliary variable
   IFLOWFACE (AUXILIARY IFLOWFACE in the GWF package; the value is saved as a column of its
   budget record, which is where PRT reads it, see gwsource.mf6io). Values (MF6 PRT source:
   prt-fmi.f90, MethodDis, MethodDisv): 0 = distributed; -1 = top; -2 = bottom; i = 1..nvert =
   lateral face i, the edge from vertex i to vertex i + 1 of the cell polygon (DISV: the
   CELL2D vertex order; DIS: 1 west, 2 north, 3 east, 4 south). PRT then treats the term as a
   flux through that face (a boundary face flow, no divergence inside the cell), and the
   consistent release is on that face: top or bottom face terms at the plan points with local
   z = 1 or 0 (one height); a lateral face term at points along its edge (as many as the
   cell has plan points, at the midpoints of equal pieces) x the z_levels heights, a
   midpoint rule for a flux spread uniformly over the saturated face. Recharge on the top
   face is the uppermost water of the column and descends only as recharge is added on top
   of it downstream (in the 3-layer test model with IFLOWFACE = -1 no recharge particle
   reaches the bottom-layer wells; volume seeding there credits them with 6.9 m3/d of it).
3. PRT: a separate simulation (own folder) with PRT DIS/DISV copied from the GWF input, MIP
   porosity, PRP with EXTEND_TRACKING (the last steady period is extended until particles
   terminate), FMI reading the GWF head and budget files, and EMS. FloPy writes the input; the
   MF6 executable is passed explicitly. PRT needs DATA-SPDIS (NPF SAVE_SPECIFIC_DISCHARGE).
   Particles run until they terminate (strong sink, boundary face); there is no stop zone.
4. Tracks: release, cell-exit and termination records (CSV track output). icell is the 1-based
   user node; the records give each particle's sequence of cells and the time it entered them.

Weak sinks and the destination (stop_at_weak_sink is deliberately left off). PRT does not
report which boundary package removes water, and with STOP_AT_WEAK_SINK a particle would stop
in every weak sink cell (sinks plus outflow faces), also those of other boundaries (e.g. the
gaining river cells between recharge and a well), which truncates paths. Instead each particle
carries the full-mixing accounting of the gross method along its advective path: in every cell
j it visits (the release cell included, each cell once), its remaining weight W gives
d_j / O_j x W to the destination (d_j = the group's sink flow in j, O_j = the gross outflow of
j) and keeps (1 - Snk_j / O_j) x W (Snk_j = all sink terms of j, the destination's included).
The captured weight is the sum over the path; its arrival time is the entry time into each j.
Nothing is dropped: water that passes a destination cell, or a well that takes only part of
its cell's outflow, is followed on to the destination cells further down.
With thin_weak_sinks=False the particles lose only the destination's share (1 - d_j / O_j), as
in a plain particle run; that over-counts the water reaching the destination, because the
water that other sinks remove on the way is counted too.

Consistency. If the release points resolve the sources and the cell survival splits the
weight among the outflow faces as the flow does, the captured flow equals the destination
inflow (the duality of the gross method, now along advective paths). Observed:
- 3-layer test model (wells in the bottom layer, a weak well upstream of a strong one):
  402.6 of 405 m3/d with k = 3 and 2 levels, 405.3 with k = 4 and 16 levels. An earlier
  version that released at the water table and stopped particles in the first destination
  cell, dropping the rest of their weight, captured 266 m3/d; volume seeding with that stop
  rule about 306 m3/d.
  With recharge on the top face (IFLOWFACE = -1, same GWF flows): 405.8 released on the top
  face, 412.7 seeded over the volume. With the CHD edges on their lateral faces instead (1
  west, 3 east; not in the test suite): 398 to 412 m3/d for k = 3..6 and 2..8 levels, the same
  scatter as volume seeding of the CHD (395 to 403): each edge cell brings ~126 m3/d, so a few
  particles on the capture-zone edge move the sum.
- Neversink (4 layers, 1.68M cells, eight wells, k = 1, 4 levels): 3,736 of 3,671 m3/d,
  every well within 11 % of its rate; the earlier version 1,940 (water table) and 3,005
  (mid-cell). A single mid-cell height gives 3,722 there, so the z levels matter most where
  the alternative would be the water table. Over five seeding layouts the total scattered
  between 0.0 and +1.8 % without a trend (quadrature, not the thinning factor); the per-well
  errors shrank with the number of z levels (RMS 18 % with one, 6 % with four).
Which sources supply the water differs between advection and mixing (Neversink: 51 % stream
leakage along the paths, 43 % under full mixing), and so do per-cell capture fractions; that
is the method difference, not an error.

What is measured. Water is counted as arriving when it ENTERS a destination cell (at once for
a particle released in it). The arrival time is therefore comparable with
TravelTimeResult.mean_time_to_exit_cell (the time until the water enters the cell through
whose sink it leaves); mean_time also includes the residence in that cell.

PRT supports DIS and DISV only; for DISU the Eulerian travel time is the only option.

Network steps (gwsource.network: several models, or package nodes) are not supported: the
destination shares and the particle weights assume that the destination sinks and every node
of the graph are cells of the one GWF model PRT tracks in, and particles do not follow package
networks (an SFR reach, a MAW well bore) or cross into other models. track_particles() raises
NotImplementedError for them.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import flopy
import numpy as np

from .assemble import cell_budget, flow_edges, group_term_flows
from .flowstep import FlowStep
from .metrics import BackwardResult
from .mf6io import _block_lines, _option_value, find_model_files
from .selectors import Selection
from .traveltime import cell_porosity

TERMINATE_REASON = 3
PRT_GRIDS = ("DIS", "DISV")
IFLOWFACE_TOP, IFLOWFACE_BOTTOM = -1, -2


@dataclass
class PrtConfig:
    """Options of a PRT run.

    porosity: scalar or per-cell (required; use the same value as for the Eulerian times).
    fraction_threshold: seed only cells with backward fraction above this.
    subdivisions: k; each fan triangle of a cell gets k * k points (4 k^2 points per DIS cell).
    z_levels: n; each plan point of a distributed term is released at the n local
        z = (i + 0.5) / n, i = 0..n-1, so the points fill the saturated cell volume (see module
        docstring); lateral face terms use the same heights. A one-layer grid has no vertical
        flow and gets one level. Top and bottom face terms (IFLOWFACE -1, -2) are always
        released on their face (local z 1 or 0).
    release_z: optional single local z instead of the levels (0 = cell bottom, 1 = water
        table / cell top); release_z=1 traps particles of distributed terms at the water table
        of the top layer.
    thin_weak_sinks: multiply particle weights by the full-mixing survival of every cell they
        pass, so other sinks remove their share (see module docstring).
    exit_solve_tolerance: PRP EXIT_SOLVE_TOLERANCE.
    stoptraveltime: optional PRP STOPTRAVELTIME.
    """

    porosity: float | np.ndarray
    fraction_threshold: float = 1e-6
    subdivisions: int = 2
    z_levels: int = 4
    release_z: float | None = None
    thin_weak_sinks: bool = True
    exit_solve_tolerance: float = 1e-5
    stoptraveltime: float | None = None

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.subdivisions >= 1, "subdivisions must be >= 1"
        assert self.z_levels >= 1, "z_levels must be >= 1"
        if self.release_z is not None:
            assert 0.0 <= self.release_z <= 1.0, "release_z is a local z in [0, 1]"

    def local_z(self, nlay: int) -> np.ndarray:
        """Return the local z of the release levels (one if release_z is set or nlay is 1)."""
        if self.release_z is not None:
            return np.array([self.release_z])
        levels = 1 if nlay == 1 else self.z_levels  # one layer: no vertical flow, z is irrelevant
        return (np.arange(levels) + 0.5) / levels


@dataclass
class ReleasePoints:
    """Particle release points: 0-based cell (user node), x, y, local z, flow weight, package."""

    cell: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    weight: np.ndarray
    package: np.ndarray

    @property
    def n(self) -> int:
        """Number of release points (particles)."""
        return len(self.cell)


@dataclass
class PrtResult:
    """Per-particle end points and flux-weighted arrival statistics at the destination.

    arrival_time: capture-weighted mean time from release to entering the destination cells,
        per particle (NaN if not captured).
    captured_weight: particle weight x the share of it captured along its path (see module
        docstring; 0 if it passes no destination cell).
    mean_arrival: flux-weighted mean arrival time of the captured particles.
    captured_flow: sum of captured weights (compare with the group's inflow from these sources).
    cell_mean_arrival, cell_capture_fraction: per release cell (NaN where nothing was released);
    package_mean_arrival: flux-weighted mean arrival time by source package.
    """

    release: ReleasePoints
    end_cell: np.ndarray
    end_status: np.ndarray
    arrival_time: np.ndarray
    captured_weight: np.ndarray
    mean_arrival: float
    captured_flow: float
    released_flow: float
    cell_mean_arrival: np.ndarray
    cell_capture_fraction: np.ndarray
    package_mean_arrival: dict[str, float]
    ws: Path


# ---------------------------------------------------------------- grid and release points


@dataclass
class PrtGrid:
    """GWF discretisation copied for PRT: grid type, FloPy keyword arguments, cell polygons."""

    grid_type: str
    dis_kwargs: dict
    polygons: list[np.ndarray]
    ncpl: int


def _dis_polygons(delr: np.ndarray, delc: np.ndarray) -> list[np.ndarray]:
    """Return the (row-major) cell rectangles of a DIS layer in local coordinates.

    Vertices run clockwise from the south-west corner, so edge i (vertex i to i + 1) is MF6's
    DIS face i (1 west, 2 north, 3 east, 4 south), as edge i of a DISV cell is its face i.
    """
    x = np.concatenate([[0.0], np.cumsum(delr)])
    y = delc.sum() - np.concatenate([[0.0], np.cumsum(delc)])
    return [
        np.array([[x[c], y[r + 1]], [x[c], y[r]], [x[c + 1], y[r]], [x[c + 1], y[r + 1]]])
        for r in range(len(delc))
        for c in range(len(delr))
    ]


def _disv_polygons(vertices, cell2d) -> list[np.ndarray]:
    """Return each DISV cell's vertex polygon from FloPy vertices and cell2d records."""
    xy = {int(v[0]): (float(v[1]), float(v[2])) for v in vertices}
    polygons = []
    for rec in cell2d:
        ids = [int(i) for i in list(rec)[4 : 4 + int(rec[3])]]
        polygons.append(np.array([xy[i] for i in ids]))
    return polygons


def _common_dis_kwargs(dis) -> dict:
    """Return the keyword arguments shared by DIS and DISV (origin, rotation, units, idomain)."""
    idomain = dis.idomain.array
    return {
        "xorigin": dis.xorigin.get_data(),
        "yorigin": dis.yorigin.get_data(),
        "angrot": dis.angrot.get_data(),
        "length_units": dis.length_units.get_data(),
        "top": dis.top.array,
        "botm": dis.botm.array,
        "idomain": None if idomain is None else idomain,
    }


def load_prt_grid(ws: str | Path, model: str, dis_type: str) -> PrtGrid:
    """Load the GWF DIS or DISV input with FloPy and return what PRT needs from it."""
    assert dis_type in PRT_GRIDS, (
        f"MF6 PRT supports DIS and DISV grids only, not {dis_type}; for DISU use the Eulerian "
        "travel time (gwsource.traveltime)"
    )
    key = dis_type.lower()
    sim = flopy.mf6.MFSimulation.load(sim_ws=str(ws), load_only=[key], verbosity_level=0)
    dis = getattr(sim.get_model(model), key)
    kwargs = _common_dis_kwargs(dis)
    if dis_type == "DIS":
        delr, delc = dis.delr.array, dis.delc.array
        kwargs.update(
            nlay=dis.nlay.get_data(), nrow=len(delc), ncol=len(delr), delr=delr, delc=delc
        )
        return PrtGrid("DIS", kwargs, _dis_polygons(delr, delc), len(delr) * len(delc))
    vertices = [tuple(v) for v in dis.vertices.get_data()]
    cell2d = [tuple(c for c in rec if c is not None) for rec in dis.cell2d.get_data()]
    kwargs.update(
        nlay=dis.nlay.get_data(),
        ncpl=dis.ncpl.get_data(),
        nvert=len(vertices),
        vertices=vertices,
        cell2d=cell2d,
    )
    return PrtGrid("DISV", kwargs, _disv_polygons(vertices, cell2d), dis.ncpl.get_data())


def fan_points(polygon: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (points (n, 2), area weights summing to 1) spread uniformly over a convex polygon.

    The polygon is split into triangles from its centroid; each triangle into k * k equal
    sub-triangles, with one point at each sub-triangle's centroid.
    """
    centroid = _polygon_centroid(polygon)
    unit = _subtriangle_centroids(k)  # barycentric (a, b) of the k^2 sub-triangle centroids
    points, weights = [], []
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        area = 0.5 * abs(
            (a[0] - centroid[0]) * (b[1] - centroid[1])
            - (b[0] - centroid[0]) * (a[1] - centroid[1])
        )
        points.append(centroid + unit[:, :1] * (a - centroid) + unit[:, 1:] * (b - centroid))
        weights.append(np.full(len(unit), area / len(unit)))
    weights = np.concatenate(weights)
    return np.vstack(points), weights / weights.sum()


def _polygon_centroid(polygon: np.ndarray) -> np.ndarray:
    """Return the area centroid of a simple polygon."""
    x, y = polygon[:, 0], polygon[:, 1]
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    cross = x * yn - xn * y
    area = cross.sum() / 2.0
    return np.array([((x + xn) * cross).sum(), ((y + yn) * cross).sum()]) / (6.0 * area)


def _subtriangle_centroids(k: int) -> np.ndarray:
    """Return barycentric coordinates (along the two edges) of the k^2 sub-triangle centroids."""
    out = []
    for i in range(k):
        for j in range(k - i):
            out.append(((i + 1 / 3) / k, (j + 1 / 3) / k))  # upward sub-triangle
            if i + j < k - 1:
                out.append(((i + 2 / 3) / k, (j + 2 / 3) / k))  # downward sub-triangle
    return np.array(out)


def edge_points(polygon: np.ndarray, face: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (points (n, 2), equal weights summing to 1) along lateral face `face` (1-based).

    Face i is the polygon edge from vertex i to vertex i + 1 (MF6 PRT numbering); the points
    are the midpoints of n equal pieces of it.
    """
    assert 1 <= face <= len(polygon), f"IFLOWFACE {face} is not a face of a {len(polygon)}-gon"
    a, b = polygon[face - 1], polygon[face % len(polygon)]
    t = (np.arange(n) + 0.5) / n
    return a + t[:, None] * (b - a), np.full(n, 1.0 / n)


def term_points(
    polygon: np.ndarray, iflowface: int, k: int, local_z: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (plan points (n, 2), local z, weight shares summing to 1) of one source term.

    IFLOWFACE 0: the cell volume (fan points x local_z); top (-1) or bottom (-2) face: the fan
    points at local z 1 or 0; lateral face i: as many points along edge i as the fan has, x
    local_z.
    """
    if iflowface in (IFLOWFACE_TOP, IFLOWFACE_BOTTOM):
        points, share = fan_points(polygon, k)
        z = 1.0 if iflowface == IFLOWFACE_TOP else 0.0
        return points, np.full(len(share), z), share
    if iflowface == 0:
        points, share = fan_points(polygon, k)
    else:
        points, share = edge_points(polygon, iflowface, len(polygon) * k * k)
    nz = len(local_z)
    return np.repeat(points, nz, axis=0), np.tile(local_z, len(points)), np.repeat(share, nz) / nz


def release_points(
    step: FlowStep,
    grid: PrtGrid,
    contributing: np.ndarray,
    source: Selection | None,
    subdivisions: int,
    local_z: np.ndarray,
) -> ReleasePoints:
    """Return flux-weighted release points for the source terms in contributing cells.

    Each term is released over its cell volume or over its IFLOWFACE face (term_points).
    """
    flow = np.maximum(step.term_flow, 0.0)
    keep = (flow > 0.0) & contributing[step.term_cell]
    if source is not None:
        keep &= source.terms
    iflowface = step.term_iflowface
    if iflowface is None:
        iflowface = np.zeros(step.n_terms, dtype=np.int64)
    parts = {"cell": [], "xy": [], "z": [], "weight": [], "package": []}
    for k in np.flatnonzero(keep):
        cell = int(step.term_cell[k])
        polygon = grid.polygons[cell % grid.ncpl]
        points, z, share = term_points(polygon, int(iflowface[k]), subdivisions, local_z)
        parts["cell"].append(np.full(len(share), cell))
        parts["xy"].append(points)
        parts["z"].append(z)
        parts["weight"].append(flow[k] * share)
        name = step.packages[step.term_package[k]].name
        parts["package"].append(np.full(len(share), name, dtype=object))
    assert parts["cell"], "no source terms in the contributing cells: nothing to release"
    xy = np.vstack(parts["xy"])
    return ReleasePoints(
        cell=np.concatenate(parts["cell"]),
        x=xy[:, 0],
        y=xy[:, 1],
        z=np.concatenate(parts["z"]),
        weight=np.concatenate(parts["weight"]),
        package=np.concatenate(parts["package"]),
    )


# ---------------------------------------------------------------- PRT simulation


def _tdis_perioddata(tdis_file: Path) -> tuple[list[tuple[float, int, float]], str | None]:
    """Return the GWF TDIS period data and time units."""
    rows = _block_lines(tdis_file, "PERIODDATA")
    perioddata = [(float(r[0]), int(r[1]), float(r[2])) for r in rows]
    return perioddata, _option_value(tdis_file, "TIME_UNITS")


def _cellid(cell: int, grid: PrtGrid) -> tuple[int, ...]:
    """Return the PRT cellid (layer, row, col) or (layer, icpl) of a 0-based user node."""
    layer, icpl = divmod(int(cell), grid.ncpl)
    if grid.grid_type == "DIS":
        return (layer, *divmod(icpl, grid.dis_kwargs["ncol"]))
    return (layer, icpl)


def _assert_spdis(budget_file: Path) -> None:
    """Assert that the GWF budget file holds DATA-SPDIS, which PRT needs."""
    names = {
        n.decode().strip()
        for n in flopy.utils.CellBudgetFile(str(budget_file)).get_unique_record_names()
    }
    assert "DATA-SPDIS" in names, (
        "PRT needs specific discharge: set SAVE_SPECIFIC_DISCHARGE (and SAVE_FLOWS) in the GWF NPF"
    )


def write_prt(
    prt_ws: Path,
    gwf_ws: Path,
    grid: PrtGrid,
    release: ReleasePoints,
    config: PrtConfig,
    exe: str | Path,
    model: str | None = None,
) -> flopy.mf6.MFSimulation:
    """Write a PRT simulation tracking the release points until they leave the model."""
    files = find_model_files(gwf_ws, model)
    assert files.head_file is not None, "PRT needs the GWF head file (OC HEAD FILEOUT)"
    _assert_spdis(files.budget_file)
    perioddata, time_units = _tdis_perioddata(files.tdis_file)
    prt_ws = Path(prt_ws)
    prt_ws.mkdir(parents=True, exist_ok=True)
    sim = flopy.mf6.MFSimulation(sim_name="prt", sim_ws=str(prt_ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim, nper=len(perioddata), perioddata=perioddata, time_units=time_units)
    prt = flopy.mf6.ModflowPrt(sim, modelname="prt")
    dis_class = flopy.mf6.ModflowPrtdis if grid.grid_type == "DIS" else flopy.mf6.ModflowPrtdisv
    dis_class(prt, **{k: v for k, v in grid.dis_kwargs.items() if v is not None})
    n_cells = grid.ncpl * int(grid.dis_kwargs["nlay"])
    flopy.mf6.ModflowPrtmip(prt, porosity=cell_porosity(config.porosity, n_cells))
    packagedata = [
        (i, _cellid(c, grid), x, y, z)
        for i, (c, x, y, z) in enumerate(zip(release.cell, release.x, release.y, release.z))
    ]
    flopy.mf6.ModflowPrtprp(
        prt,
        nreleasepts=len(packagedata),
        packagedata=packagedata,
        local_z=True,
        extend_tracking=True,
        exit_solve_tolerance=config.exit_solve_tolerance,
        stoptraveltime=config.stoptraveltime,
    )
    flopy.mf6.ModflowPrtoc(
        prt,
        trackcsv_filerecord="prt.trk.csv",
        track_release=True,
        track_exit=True,
        track_terminate=True,
    )
    gwf_files = [("GWFHEAD", files.head_file), ("GWFBUDGET", files.budget_file)]
    flopy.mf6.ModflowPrtfmi(
        prt, packagedata=[(kind, _relative(path, prt_ws)) for kind, path in gwf_files]
    )
    ems = flopy.mf6.ModflowEms(sim, filename="prt.ems")
    sim.register_solution_package(ems, [prt.name])
    sim.write_simulation(silent=True)
    return sim


def _relative(path: Path, start: Path) -> str:
    """Return path relative to start (MF6 reads FMI files relative to the simulation folder)."""
    return os.path.relpath(Path(path).resolve(), Path(start).resolve())


def run_prt(sim: flopy.mf6.MFSimulation) -> Path:
    """Run a written PRT simulation and return the CSV track file."""
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "MF6 PRT run failed:\n" + "\n".join(buff[-20:])
    return Path(sim.sim_path) / "prt.trk.csv"


TRACK_COLUMNS = {"irpt": 4, "icell": 6, "istatus": 8, "ireason": 9, "trelease": 10, "t": 11}


def read_tracks(track_csv: str | Path) -> np.ndarray:
    """Return particle, cell, status, reason and times of a PRT CSV track file (record order)."""
    dtype = [(name, "f8" if name in ("trelease", "t") else "i8") for name in TRACK_COLUMNS]
    return np.loadtxt(
        track_csv,
        delimiter=",",
        skiprows=1,
        usecols=tuple(TRACK_COLUMNS.values()),
        dtype=dtype,
        ndmin=1,
    )


def endpoints(tracks: np.ndarray, n_particles: int) -> dict[str, np.ndarray]:
    """Return, per particle (release point order), its end cell (0-based), status and time."""
    term = tracks[tracks["ireason"] == TERMINATE_REASON]
    index = term["irpt"] - 1
    assert len(np.unique(index)) == len(index), "a particle terminated twice"
    out = {
        "cell": np.full(n_particles, -1, dtype=np.int64),
        "status": np.full(n_particles, -1, dtype=np.int64),
        "time": np.full(n_particles, np.nan),
    }
    out["cell"][index] = term["icell"] - 1
    out["status"][index] = term["istatus"]
    out["time"][index] = term["t"] - term["trelease"]
    return out


def cell_visits(tracks: np.ndarray) -> dict[str, np.ndarray]:
    """Return the cells each particle passes, in order, with the time it entered them.

    A particle is released in its first cell (entry time 0); every cell-exit record ends one
    visit, and the next record's cell is the next visit, entered at the exit time. Only the
    first visit of a cell counts (a particle that re-enters a cell, e.g. by grazing a face, is
    not counted twice).
    """
    order = np.lexsort((np.arange(len(tracks)), tracks["t"], tracks["irpt"]))
    rec = tracks[order]
    particle, cell = rec["irpt"] - 1, rec["icell"] - 1
    first = np.r_[True, particle[1:] != particle[:-1]]
    new_visit = first | np.r_[True, cell[1:] != cell[:-1]]
    entry = np.where(first, rec["t"], np.r_[rec["t"][0], rec["t"][:-1]]) - rec["trelease"]
    visits = {"particle": particle[new_visit], "cell": cell[new_visit], "time": entry[new_visit]}
    pairs = np.column_stack([visits["particle"], visits["cell"]])
    keep = np.sort(np.unique(pairs, axis=0, return_index=True)[1])
    return {key: v[keep] for key, v in visits.items()}


def capture_along_paths(
    visits: dict[str, np.ndarray], n_particles: int, share: np.ndarray, survival: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return, per particle, the captured share of its weight and the mean capture time.

    In each visited cell j the particle's remaining weight W gives share_j x W to the destination
    and keeps survival_j x W; the capture time is the entry time into j.
    """
    p = visits["particle"]
    log_f = np.log(np.maximum(survival[visits["cell"]], 1e-300))
    cum = np.cumsum(log_f)
    start = np.r_[0, np.flatnonzero(p[1:] != p[:-1]) + 1]
    offset = np.repeat(cum[start] - log_f[start], np.diff(np.r_[start, len(p)]))
    remaining = np.exp(cum - log_f - offset)  # product of survival over the earlier visits
    gain = remaining * share[visits["cell"]]
    captured = np.bincount(p, weights=gain, minlength=n_particles)
    time_sum = np.bincount(p, weights=gain * visits["time"], minlength=n_particles)
    mean_time = np.divide(
        time_sum, captured, out=np.full(n_particles, np.nan), where=captured > 0
    )
    return captured, mean_time


# ---------------------------------------------------------------- statistics


def destination_share(step: FlowStep, destination: Selection) -> np.ndarray:
    """Return d_k / O_k per cell: the share of a cell's outflow leaving through the group."""
    outflow = cell_budget(step, flow_edges(step)).outflow
    d = group_term_flows(step, {"d": destination}, sign=-1)[:, 0]
    return np.divide(d, outflow, out=np.zeros_like(d), where=outflow > 0)


def weak_sink_survival(step: FlowStep) -> np.ndarray:
    """Return 1 - Snk / O per cell (1 where O = 0): the share of the outflow through faces."""
    budget = cell_budget(step, flow_edges(step))
    removed = np.divide(
        budget.sink, budget.outflow, out=np.zeros(step.n_cells), where=budget.outflow > 0
    )
    return 1.0 - removed


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Return the weighted mean of values (NaN if the weights sum to 0)."""
    total = weights.sum()
    return float(np.dot(np.nan_to_num(values), weights) / total) if total > 0 else np.nan


def arrival_statistics(
    step: FlowStep,
    release: ReleasePoints,
    ends: dict,
    captured_share: np.ndarray,
    arrival: np.ndarray,
    ws: Path,
) -> PrtResult:
    """Return per-particle captured weights and flux-weighted arrival statistics.

    captured_share and arrival are the per-particle results of capture_along_paths().
    """
    cw = release.weight * captured_share
    arrival = np.where(cw > 0, arrival, np.nan)
    n = step.n_cells
    released = np.bincount(release.cell, weights=release.weight, minlength=n)
    cw_cell = np.bincount(release.cell, weights=cw, minlength=n)
    cwt_cell = np.bincount(release.cell, weights=cw * np.nan_to_num(arrival), minlength=n)
    packages = np.unique(release.package)
    return PrtResult(
        release=release,
        end_cell=ends["cell"],
        end_status=ends["status"],
        arrival_time=arrival,
        captured_weight=cw,
        mean_arrival=_weighted_mean(arrival, cw),
        captured_flow=float(cw.sum()),
        released_flow=float(release.weight.sum()),
        cell_mean_arrival=np.divide(cwt_cell, cw_cell, out=np.full(n, np.nan), where=cw_cell > 0),
        cell_capture_fraction=np.divide(
            cw_cell, released, out=np.full(n, np.nan), where=released > 0
        ),
        package_mean_arrival={
            str(p): _weighted_mean(arrival, np.where(release.package == p, cw, 0.0))
            for p in packages
        },
        ws=ws,
    )


def check_cells_only(step: FlowStep, destination: Selection) -> None:
    """Raise NotImplementedError for network steps (package-node destinations, several models)."""
    if not step.is_network:
        return
    on_packages = [
        b.label for b in step.blocks if b.kind == "package" and destination.cells[b.nodes].any()
    ]
    if on_packages:
        raise NotImplementedError(
            f"the destination lies on package nodes ({', '.join(on_packages)}); the PRT helper "
            "stops particles in cells only"
        )
    raise NotImplementedError(
        "the PRT helper needs a single-model step without package nodes (particles do not "
        "follow package networks or cross models); read the model with read_step()"
    )


def track_particles(
    gwf_ws: str | Path,
    step: FlowStep,
    result: BackwardResult,
    group: str,
    config: PrtConfig,
    exe: str | Path,
    prt_ws: str | Path,
    source: Selection | None = None,
    model: str | None = None,
) -> PrtResult:
    """Seed, run and evaluate forward PRT particles for one backward destination group.

    step and result are the GWF step and its backward trace (gross). Particles are released
    from the source terms (all, or those in source) of cells with F > fraction_threshold.
    """
    assert result.accounting == "gross", "use a gross-accounting backward result"
    check_cells_only(step, result.selections[group])
    files = find_model_files(gwf_ws, model)
    grid = load_prt_grid(gwf_ws, files.model, files.dis_type)
    contributing = result.fraction_through[group] > config.fraction_threshold
    local_z = config.local_z(int(grid.dis_kwargs["nlay"]))
    release = release_points(step, grid, contributing, source, config.subdivisions, local_z)
    sim = write_prt(Path(prt_ws), Path(gwf_ws), grid, release, config, exe, files.model)
    tracks = read_tracks(run_prt(sim))
    share = destination_share(step, result.selections[group])
    survival = weak_sink_survival(step) if config.thin_weak_sinks else 1.0 - share
    captured, arrival = capture_along_paths(cell_visits(tracks), release.n, share, survival)
    ends = endpoints(tracks, release.n)
    return arrival_statistics(step, release, ends, captured, arrival, Path(prt_ws))
