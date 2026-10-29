"""MF6 models of the dispersion study: DIS and Voronoi DISV grids of two steady problems.

Problem A ("analytic"): uniform regional flow plus one pumping well in a confined aquifer of
constant transmissivity T. The heads on the perimeter cells are fixed (CHD) to the analytical
solution h = h0 - i s + Q / (4 pi T) ln(r^2), s the distance along the regional flow direction,
so the capture zone inside the domain approaches the classic analytical divide (see
analysis.capture_zone_mask).

Problem B ("model1"): the physics of test model 1 (tests/models/common.py): one unconfined
layer with recharge, a river line, a constant-head west edge and a pumping well; here without
inactive cells, with the well and river placed at points that are inside cells (not on cell
edges) for every cell size of the series, and the river conductance given per unit length.
Problem B also has a transient variant with the steady flows held for many time steps (no
storage), for the time-stepping part of the study.

Coordinates: model x, y with the origin at the lower-left corner of the domain (DIS rows count
from the top). Grids are built by cell size h: DIS with h x h cells, DISV with a smooth,
quasi-uniform Voronoi grid from vorflow (CGAL refinement and Lloyd relaxation) whose mean cell
size is brought to h (it is reported, not assumed). Voronoi seeds on the domain edge give half
cells there, as in any bounded Voronoi grid.
"""

from dataclasses import dataclass, field
from pathlib import Path

import flopy
import numpy as np
import vorflow.vorflowpp as vfp
from flopy.utils.gridintersect import GridIntersect
from shapely.geometry import LineString, Point

GRID_KINDS = ("DIS", "DISV")
EDGE_TOL = 1e-6
VORONOI_ITERS = 30  # Lloyd relaxation iterations of vorflow
VORONOI_GRADATION = 1.2  # vorflow size gradation (uniform target size: no effect)
VORONOI_SIZE_RATIO = 0.6  # first guess of mean cell size over vorflow's background size


@dataclass
class AnalyticSpec:
    """Problem A: uniform flow + well, confined, constant T (lengths in m, time in d)."""

    lx: float = 2000.0
    ly: float = 2000.0
    k: float = 10.0
    thickness: float = 50.0
    gradient: float = 0.002
    rate: float = 500.0
    angle_deg: float = 0.0
    well_x: float = 1403.125
    well_y: float = 1003.125
    h0: float = 100.0

    @property
    def transmissivity(self) -> float:
        """Aquifer transmissivity T = k b."""
        return self.k * self.thickness

    @property
    def regional_discharge(self) -> float:
        """Regional discharge per unit width U = T i."""
        return self.transmissivity * self.gradient


@dataclass
class Model1Spec:
    """Problem B: test model 1's physics on a 1500 m x 1000 m domain."""

    lx: float = 1500.0
    ly: float = 1000.0
    k: float = 10.0
    top: float = 20.0
    botm: float = -30.0
    strt: float = 10.0
    rech: float = 1.0e-3
    chd_head: float = 5.0
    riv_x: float = 1128.125
    riv_stage: float = 6.0
    riv_cond_per_m: float = 10.0
    riv_rbot: float = 4.0
    well_x: float = 878.125
    well_y: float = 471.875
    well_rate: float = -800.0


@dataclass
class GridModel:
    """A built and run model: workspace, name, grid kind and cell size, FloPy model grid."""

    ws: Path
    name: str
    kind: str
    h: float
    modelgrid: object
    notes: dict = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        """Number of cells (one layer)."""
        return int(self.modelgrid.ncpl)

    @property
    def grb_file(self) -> Path:
        """Binary grid file."""
        suffix = "dis" if self.kind == "DIS" else "disv"
        return self.ws / f"{self.name}.{suffix}.grb"

    @property
    def mean_cell_size(self) -> float:
        """Square root of the mean cell area."""
        return float(np.sqrt(np.mean(cell_areas(self.modelgrid))))


# ---------------------------------------------------------------- grids


def vorflow_cells(lx: float, ly: float, size: float, iters: int = VORONOI_ITERS,
                  gradation: float = VORONOI_GRADATION) -> list:
    """Return vorflow's (seed, polygon) Voronoi cells over [0, lx] x [0, ly] for one size."""
    mesher = vfp.HydroMesher()
    mesher.add_domain([(0.0, 0.0), (lx, 0.0), (lx, ly), (0.0, ly)], edge_resolution=size)
    mesher.generate(size, gradation, iters, method=vfp.GenerationMethod.CGAL_DEFAULT)
    return mesher.get_voronoi_cells()


def polygon_area(xy: np.ndarray) -> float:
    """Return the signed area of a polygon (positive counter-clockwise)."""
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def voronoi_cells(lx: float, ly: float, h: float, ratio: float = VORONOI_SIZE_RATIO) -> list:
    """Return Voronoi cells over the domain whose mean cell size is close to h.

    vorflow's background size is the target edge length of its triangles, so the first guess
    is h / ratio; one rescaling by the mean cell size reached then brings it to h.
    """
    size = h / ratio
    cells = vorflow_cells(lx, ly, size)
    mean_h = np.sqrt(lx * ly / len(cells))
    cells = vorflow_cells(lx, ly, size * h / mean_h)
    areas = [abs(polygon_area(np.asarray(poly))) for _, poly in cells]
    assert abs(sum(areas) / (lx * ly) - 1.0) < 1e-9, "the Voronoi cells must tile the domain"
    return cells


def voronoi_gridprops(lx: float, ly: float, h: float, digits: int = 6) -> dict:
    """Return DISV grid properties of a vorflow Voronoi grid of mean cell size about h.

    The cell centres are the Voronoi seeds; shared vertices are merged after rounding to digits
    decimals, and every cell is written clockwise as MF6 requires.
    """
    vertex_ids, cell2d = {}, []
    for icell, (seed, poly) in enumerate(voronoi_cells(lx, ly, h)):
        xy = np.round(np.asarray(poly, dtype=float), digits) + 0.0  # + 0.0 drops -0.0
        if polygon_area(xy) > 0:
            xy = xy[::-1]
        ids = [vertex_ids.setdefault((x, y), len(vertex_ids)) for x, y in map(tuple, xy)]
        ids = [v for n, v in enumerate(ids) if v != ids[n - 1]]  # drop repeated vertices
        cell2d.append([icell, float(seed[0]), float(seed[1]), len(ids), *ids])
    vertices = [[i, x, y] for (x, y), i in vertex_ids.items()]
    return {"ncpl": len(cell2d), "nvert": len(vertices), "vertices": vertices, "cell2d": cell2d}


def cell_areas(modelgrid) -> np.ndarray:
    """Return the plan area of every cell of a one-layer FloPy model grid."""
    if modelgrid.grid_type == "structured":
        return np.outer(modelgrid.delc, modelgrid.delr).ravel()
    areas = []
    for i in range(modelgrid.ncpl):
        xy = np.asarray(modelgrid.get_cell_vertices(i))
        x, y = xy[:, 0], xy[:, 1]
        areas.append(0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))
    return np.asarray(areas)


def boundary_cells(modelgrid, lx: float, ly: float) -> np.ndarray:
    """Return the cells with a vertex on the domain boundary (one layer)."""
    out = []
    for i in range(modelgrid.ncpl):
        xy = np.asarray(modelgrid.get_cell_vertices(*cellid_2d(modelgrid, i)))
        x, y = xy[:, 0], xy[:, 1]
        edge = (x.min() < EDGE_TOL) | (y.min() < EDGE_TOL)
        edge |= (x.max() > lx - EDGE_TOL) | (y.max() > ly - EDGE_TOL)
        if edge:
            out.append(i)
    return np.asarray(out, dtype=int)


def cellid_2d(modelgrid, i: int) -> tuple[int, ...]:
    """Return the (row, col) of a structured cell number, or (i,) for a vertex grid."""
    if modelgrid.grid_type == "structured":
        return tuple(int(v) for v in divmod(i, modelgrid.ncol))
    return (i,)


def cell_centres(modelgrid) -> tuple[np.ndarray, np.ndarray]:
    """Return the x and y of every cell centre (one layer, cell order)."""
    return np.ravel(modelgrid.xcellcenters), np.ravel(modelgrid.ycellcenters)


def add_discretisation(gwf, kind: str, h: float, lx: float, ly: float, top, botm) -> str:
    """Add DIS (h x h cells) or a Voronoi DISV and return the discretisation file name."""
    assert kind in GRID_KINDS, f"grid kind must be one of {GRID_KINDS}"
    name = gwf.name
    if kind == "DIS":
        nrow, ncol = int(round(ly / h)), int(round(lx / h))
        assert abs(nrow * h - ly) < EDGE_TOL and abs(ncol * h - lx) < EDGE_TOL, "h must divide"
        flopy.mf6.ModflowGwfdis(
            gwf, nlay=1, nrow=nrow, ncol=ncol, delr=h, delc=h, top=top, botm=botm,
            filename=f"{name}.dis",
        )
        return f"{name}.dis"
    props = voronoi_gridprops(lx, ly, h)
    flopy.mf6.ModflowGwfdisv(gwf, nlay=1, top=top, botm=botm, filename=f"{name}.disv", **props)
    return f"{name}.disv"


def make_sim(name: str, ws: Path, exe: Path, perioddata: list):
    """Create a simulation (TDIS, IMS) and an empty GWF model."""
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim, nper=len(perioddata), perioddata=perioddata, time_units="days")
    flopy.mf6.ModflowIms(
        sim, complexity="simple", outer_dvclose=1e-10, outer_maximum=300, inner_maximum=500,
        inner_dvclose=1e-11, rcloserecord=1e-9, linear_acceleration="bicgstab",
    )
    return sim, flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)


def add_npf_ic_oc(gwf, k: float, icelltype: int, strt) -> None:
    """Add NPF (flows, saturation, specific discharge), IC and OC (heads and budget every step)."""
    flopy.mf6.ModflowGwfnpf(
        gwf, icelltype=icelltype, k=k, save_flows=True, save_saturation=True,
        save_specific_discharge=True,
    )
    flopy.mf6.ModflowGwfic(gwf, strt=strt)
    flopy.mf6.ModflowGwfoc(
        gwf, budget_filerecord=f"{gwf.name}.cbc", head_filerecord=f"{gwf.name}.hds",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )


def run(sim) -> None:
    """Write and run a simulation, asserting success."""
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "MF6 run failed:\n" + "\n".join(buff[-20:])


def cell_at(modelgrid, x: float, y: float) -> int:
    """Return the one-layer cell number containing the point (x, y)."""
    if modelgrid.grid_type == "structured":
        row, col = modelgrid.intersect(x, y)
        return int(row * modelgrid.ncol + col)
    hits = GridIntersect(modelgrid).intersects(Point(x, y), dataframe=False).cellids
    assert len(hits) == 1, f"({x}, {y}) is on a cell edge"
    return int(hits[0])


# ---------------------------------------------------------------- problem A


def analytic_head(x, y, spec: AnalyticSpec):
    """Return the analytical head of uniform flow + a pumping well (Thiem superposition)."""
    theta = np.radians(spec.angle_deg)
    dx, dy = np.asarray(x) - spec.well_x, np.asarray(y) - spec.well_y
    along = dx * np.cos(theta) + dy * np.sin(theta)
    r2 = np.maximum(dx * dx + dy * dy, 1e-6)
    well = spec.rate / (4.0 * np.pi * spec.transmissivity) * np.log(r2)
    return spec.h0 - spec.gradient * along + well


def build_analytic(ws: Path, exe: Path, spec: AnalyticSpec, kind: str, h: float) -> GridModel:
    """Build and run problem A on one grid."""
    name = "a_" + kind.lower()
    ws.mkdir(parents=True, exist_ok=True)
    sim, gwf = make_sim(name, ws, exe, [(1.0, 1, 1.0)])
    add_discretisation(gwf, kind, h, spec.lx, spec.ly, spec.thickness, 0.0)
    grid = gwf.modelgrid
    add_npf_ic_oc(gwf, spec.k, 0, spec.h0)
    perimeter = boundary_cells(grid, spec.lx, spec.ly)
    xc, yc = cell_centres(grid)
    heads = analytic_head(xc[perimeter], yc[perimeter], spec)
    chd = [((0, *cellid_2d(grid, int(i))), float(hd)) for i, hd in zip(perimeter, heads)]
    well = cell_at(grid, spec.well_x, spec.well_y)
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [((0, *cellid_2d(grid, well)), -spec.rate)]},
        save_flows=True, pname="wel",
    )
    run(sim)
    return GridModel(ws, name, kind, h, grid, {"well_cell": well, "spec": spec})


# ---------------------------------------------------------------- problem B


def river_cells(modelgrid, spec: Model1Spec) -> list[tuple[int, float]]:
    """Return (cell, river length in the cell) along the line x = riv_x."""
    line = LineString([(spec.riv_x, 0.0), (spec.riv_x, spec.ly)])
    result = GridIntersect(modelgrid).intersect(line, geo_dataframe=False)
    assert abs(sum(result["lengths"]) - spec.ly) < EDGE_TOL, "the river must not run on cell edges"
    # FloPy >= 3.10 gives node numbers in "cellid"; older versions only "cellids", (row, col)
    # tuples on a structured grid
    cells = result["cellid"] if "cellid" in result.dtype.names else result["cellids"]
    nodes = [c[0] * modelgrid.ncol + c[1] if isinstance(c, tuple) else c for c in cells]
    return [
        (int(cell), float(length))
        for cell, length in zip(nodes, result["lengths"])
        if length > EDGE_TOL
    ]


def west_edge_cells(modelgrid) -> np.ndarray:
    """Return the cells with a vertex on x = 0."""
    out = []
    for i in range(modelgrid.ncpl):
        xy = np.asarray(modelgrid.get_cell_vertices(*cellid_2d(modelgrid, i)))
        if xy[:, 0].min() < EDGE_TOL:
            out.append(i)
    return np.asarray(out, dtype=int)


def add_model1_stresses(gwf, spec: Model1Spec) -> dict:
    """Add CHD (west edge), RIV (per-length conductance), WEL and RCH; return the stress cells."""
    grid = gwf.modelgrid
    cid = lambda i: (0, *cellid_2d(grid, int(i)))  # noqa: E731
    chd_cells = west_edge_cells(grid)
    rivs = river_cells(grid, spec)
    well = cell_at(grid, spec.well_x, spec.well_y)
    chd = [(cid(i), spec.chd_head) for i in chd_cells]
    riv = [(cid(i), spec.riv_stage, spec.riv_cond_per_m * length, spec.riv_rbot)
           for i, length in rivs]
    rch = [(cid(i), spec.rech) for i in range(grid.ncpl)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data={0: riv}, save_flows=True, pname="riv")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [(cid(well), spec.well_rate)]}, save_flows=True, pname="wel"
    )
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    return {"well_cell": well, "riv_cells": [i for i, _ in rivs], "chd_cells": chd_cells}


def build_model1(
    ws: Path,
    exe: Path,
    spec: Model1Spec,
    kind: str,
    h: float,
    perioddata: list | None = None,
) -> GridModel:
    """Build and run problem B on one grid (steady; perioddata gives a multi-step variant)."""
    name = "b_" + kind.lower()
    ws.mkdir(parents=True, exist_ok=True)
    sim, gwf = make_sim(name, ws, exe, perioddata or [(1.0, 1, 1.0)])
    add_discretisation(gwf, kind, h, spec.lx, spec.ly, spec.top, spec.botm)
    add_npf_ic_oc(gwf, spec.k, 1, spec.strt)
    cells = add_model1_stresses(gwf, spec)
    run(sim)
    return GridModel(ws, name, kind, h, gwf.modelgrid, {**cells, "spec": spec})
