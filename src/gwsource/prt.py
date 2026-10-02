"""Thin helper to check Eulerian travel times against forward particle tracking with MF6 PRT.

What it does
------------
1. Contributing cells: cells whose backward fraction F to the destination group exceeds a
   threshold (under full mixing F = 0 means no flow path, so no particle could arrive either).
2. Release points: one set per source term (positive external flow, optionally restricted to a
   source Selection) in a contributing cell, spread over the cell's plan polygon (DIS or DISV):
   the polygon is split into a fan of triangles from its centroid, each triangle into k x k
   equal sub-triangles, and a point is placed at each sub-triangle's centroid. Every point
   carries the flow weight q_term x (sub-triangle area / cell area), so sums over particles are
   flux-weighted for a source spread uniformly over the cell (recharge, river or drain leakage).
   Points are released at local z = release_z (1.0 = the water table for a convertible cell,
   the cell top if confined), i.e. where areal recharge enters. Lateral sources (a CHD or GHB
   on a model edge) are seeded the same way; that is an approximation of where they enter.
3. PRT: a separate simulation (own folder) with PRT DIS/DISV copied from the GWF input, MIP
   porosity, PRP with EXTEND_TRACKING (the last steady period is extended until particles
   terminate), FMI reading the GWF head and budget files, and EMS. FloPy writes the input; the
   MF6 executable is passed explicitly. PRT needs DATA-SPDIS (NPF SAVE_SPECIFIC_DISCHARGE).
4. Tracks: release, cell-exit and termination records (CSV track output). icell is the 1-based
   user node; the termination record gives the end cell, status and time of each particle.

Weak sinks and the destination (stop_at_weak_sink is deliberately left off). PRT does not
report which boundary package removes a particle, only the cell where it stops. A particle
stops on entering a cell with no exit face (a strong sink, status 5); with STOP_AT_WEAK_SINK it
would also stop in every weak sink cell (sinks plus outflow faces, status 3). That option is
not used: it stops particles at the weak sinks of every other boundary too (e.g. the gaining
river cells between recharge and a well), which truncates their paths. Instead
- the cells that host the destination's sink terms form a stop zone (MIP IZONE = 1, PRP
  ISTOPZONE = 1): a particle stops on entering one of them (status 6) and arrives at the
  destination with the share d_k / O_k of its weight (d_k = the group's sink flow in cell k,
  O_k = the gross outflow of k), the proportional weak-sink accounting of the gross method;
- particles pass through the weak sinks of other groups, and with thin_weak_sinks=True (the
  default) their weight is multiplied by the full-mixing survival 1 - Snk_j / O_j of every
  cell j they visit outside the stop zone (Snk_j = sink terms of j), so that the captured flow
  stays consistent with the flow budget. With thin_weak_sinks=False they pass unchanged, as in
  a plain particle run, which over-counts the water reaching the destination.
The remaining 1 - d_k / O_k of a particle's weight in a destination cell is dropped, not
tracked on; that under-counts a destination group whose cells lie downstream of one another
(e.g. a river line); for a single well cell nothing is lost.

What is measured. Particles stop on ENTERING the destination cell, and a particle released
inside it stops at once. The arrival time is therefore comparable with
TravelTimeResult.mean_time_to_exit_cell (the time until the water enters the cell through
whose sink it leaves); mean_time also includes the residence in that cell.

PRT supports DIS and DISV only; for DISU the Eulerian travel time is the only option.

Network steps (gwsource.network: several models, or package nodes) are not supported: the stop
zone and the particle weights assume that the destination sinks and every node of the graph are
cells of the one GWF model PRT tracks in, and particles do not follow package networks (an SFR
reach, a MAW well bore) or cross into other models. track_particles() raises NotImplementedError
for them.
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

STOP_ZONE = 1
STOP_ZONE_STATUS = 6  # terminated on entering a cell of the stop zone
TERMINATE_REASON = 3
PRT_GRIDS = ("DIS", "DISV")


@dataclass
class PrtConfig:
    """Options of a PRT run.

    porosity: scalar or per-cell (required; use the same value as for the Eulerian times).
    fraction_threshold: seed only cells with backward fraction above this.
    subdivisions: k; each fan triangle of a cell gets k * k points (4 k^2 points per DIS cell).
    release_z: local z of the release points (0 = cell bottom, 1 = water table / cell top).
    thin_weak_sinks: multiply particle weights by the full-mixing survival of the weak sinks
        they pass outside the destination (see module docstring).
    exit_solve_tolerance: PRP EXIT_SOLVE_TOLERANCE.
    stoptraveltime: optional PRP STOPTRAVELTIME.
    """

    porosity: float | np.ndarray
    fraction_threshold: float = 1e-6
    subdivisions: int = 2
    release_z: float = 1.0
    thin_weak_sinks: bool = True
    exit_solve_tolerance: float = 1e-5
    stoptraveltime: float | None = None

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.subdivisions >= 1, "subdivisions must be >= 1"
        assert 0.0 <= self.release_z <= 1.0, "release_z is a local z in [0, 1]"


@dataclass
class ReleasePoints:
    """Particle release points: 0-based cell (user node), local x, y, flow weight and package."""

    cell: np.ndarray
    x: np.ndarray
    y: np.ndarray
    weight: np.ndarray
    package: np.ndarray

    @property
    def n(self) -> int:
        """Number of release points (particles)."""
        return len(self.cell)


@dataclass
class PrtResult:
    """Per-particle end points and flux-weighted arrival statistics at the destination.

    arrival_time: time from release to termination, per particle (NaN if not captured).
    captured_weight: particle weight x survival through other weak sinks x destination share
        of its end cell (0 if not captured).
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
    """Return the (row-major) cell rectangles of a DIS layer in local coordinates."""
    x = np.concatenate([[0.0], np.cumsum(delr)])
    y = delc.sum() - np.concatenate([[0.0], np.cumsum(delc)])
    return [
        np.array([[x[c], y[r]], [x[c + 1], y[r]], [x[c + 1], y[r + 1]], [x[c], y[r + 1]]])
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


def release_points(
    step: FlowStep,
    grid: PrtGrid,
    contributing: np.ndarray,
    source: Selection | None,
    subdivisions: int,
) -> ReleasePoints:
    """Return flux-weighted release points for the source terms in contributing cells."""
    flow = np.maximum(step.term_flow, 0.0)
    keep = (flow > 0.0) & contributing[step.term_cell]
    if source is not None:
        keep &= source.terms
    parts = {"cell": [], "xy": [], "weight": [], "package": []}
    for k in np.flatnonzero(keep):
        cell = int(step.term_cell[k])
        points, share = fan_points(grid.polygons[cell % grid.ncpl], subdivisions)
        parts["cell"].append(np.full(len(share), cell))
        parts["xy"].append(points)
        parts["weight"].append(flow[k] * share)
        name = step.packages[step.term_package[k]].name
        parts["package"].append(np.full(len(share), name, dtype=object))
    assert parts["cell"], "no source terms in the contributing cells: nothing to release"
    xy = np.vstack(parts["xy"])
    return ReleasePoints(
        cell=np.concatenate(parts["cell"]),
        x=xy[:, 0],
        y=xy[:, 1],
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
    stop_cells: np.ndarray,
    model: str | None = None,
) -> flopy.mf6.MFSimulation:
    """Write a PRT simulation tracking the release points; stop_cells form the stop zone."""
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
    izone = np.where(stop_cells, STOP_ZONE, 0)
    flopy.mf6.ModflowPrtmip(prt, porosity=cell_porosity(config.porosity, n_cells), izone=izone)
    packagedata = [
        (i, _cellid(c, grid), x, y, config.release_z)
        for i, (c, x, y) in enumerate(zip(release.cell, release.x, release.y))
    ]
    flopy.mf6.ModflowPrtprp(
        prt,
        nreleasepts=len(packagedata),
        packagedata=packagedata,
        local_z=True,
        extend_tracking=True,
        exit_solve_tolerance=config.exit_solve_tolerance,
        istopzone=STOP_ZONE,
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


def read_tracks(track_csv: str | Path) -> np.ndarray:
    """Return the records of a PRT CSV track file as a structured array."""
    return np.genfromtxt(track_csv, delimiter=",", names=True, dtype=None, encoding="utf-8")


def endpoints(tracks: np.ndarray, n_particles: int) -> dict[str, np.ndarray]:
    """Return, per particle (release point order), its end cell (0-based), status and time."""
    term = tracks[tracks["ireason"] == TERMINATE_REASON]
    index = term["irpt"].astype(int) - 1
    assert len(np.unique(index)) == len(index), "a particle terminated twice"
    out = {
        "cell": np.full(n_particles, -1, dtype=np.int64),
        "status": np.full(n_particles, -1, dtype=np.int64),
        "time": np.full(n_particles, np.nan),
    }
    out["cell"][index] = term["icell"].astype(np.int64) - 1
    out["status"][index] = term["istatus"].astype(np.int64)
    out["time"][index] = term["t"] - term["trelease"]
    return out


def path_survival(tracks: np.ndarray, n_particles: int, survival: np.ndarray) -> np.ndarray:
    """Return, per particle, the product of the cell survival factors over the cells it visited."""
    particle = tracks["irpt"].astype(np.int64) - 1
    cell = tracks["icell"].astype(np.int64) - 1
    pairs = np.unique(np.column_stack([particle, cell]), axis=0)  # each visited cell once
    log_factor = np.log(np.maximum(survival[pairs[:, 1]], 1e-300))
    return np.exp(np.bincount(pairs[:, 0], weights=log_factor, minlength=n_particles))


# ---------------------------------------------------------------- statistics


def destination_share(step: FlowStep, destination: Selection) -> np.ndarray:
    """Return d_k / O_k per cell: the share of a cell's outflow leaving through the group."""
    outflow = cell_budget(step, flow_edges(step)).outflow
    d = group_term_flows(step, {"d": destination}, sign=-1)[:, 0]
    return np.divide(d, outflow, out=np.zeros_like(d), where=outflow > 0)


def weak_sink_survival(step: FlowStep, stop_cells: np.ndarray) -> np.ndarray:
    """Return 1 - Snk / O per cell (1 in the stop zone and where O = 0)."""
    budget = cell_budget(step, flow_edges(step))
    removed = np.divide(
        budget.sink, budget.outflow, out=np.zeros(step.n_cells), where=budget.outflow > 0
    )
    return np.where(stop_cells, 1.0, 1.0 - removed)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Return the weighted mean of values (NaN if the weights sum to 0)."""
    total = weights.sum()
    return float(np.dot(np.nan_to_num(values), weights) / total) if total > 0 else np.nan


def arrival_statistics(
    step: FlowStep,
    release: ReleasePoints,
    ends: dict,
    share: np.ndarray,
    survival: np.ndarray,
    ws: Path,
) -> PrtResult:
    """Return per-particle captured weights and flux-weighted arrival statistics.

    survival is the per-particle weight factor for the weak sinks passed on the way (1 if not
    thinned). A particle is captured if it terminated in the stop zone.
    """
    captured = (ends["status"] == STOP_ZONE_STATUS) & (ends["cell"] >= 0)
    end_share = share[np.maximum(ends["cell"], 0)]
    cw = np.where(captured, release.weight * survival * end_share, 0.0)
    arrival = np.where(cw > 0, ends["time"], np.nan)
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
    release = release_points(step, grid, contributing, source, config.subdivisions)
    share = destination_share(step, result.selections[group])
    stop_cells = share > 0.0
    sim = write_prt(Path(prt_ws), Path(gwf_ws), grid, release, config, exe, stop_cells, files.model)
    tracks = read_tracks(run_prt(sim))
    survival = np.ones(release.n)
    if config.thin_weak_sinks:
        survival = path_survival(tracks, release.n, weak_sink_survival(step, stop_cells))
    ends = endpoints(tracks, release.n)
    return arrival_statistics(step, release, ends, share, survival, Path(prt_ws))
