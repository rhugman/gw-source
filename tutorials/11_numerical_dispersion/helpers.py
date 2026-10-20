"""Test problems, references and edge metrics local to tutorial 11 (numerical dispersion).

Two steady one-layer problems, each built on square DIS cells and on Voronoi DISV cells of
several sizes h (the dispersion study of docs/dispersion_study.md, condensed):

- Problem A: uniform regional flow plus one pumping well in a confined aquifer of constant
  transmissivity T. The perimeter cells hold the analytical head h0 - i s + Q / (4 pi T) ln r^2
  (s the distance along the regional flow), so the capture zone inside the domain approaches
  the analytical one of Javandel and Tsang (1986). The regional flow runs at angle_deg to the
  grid rows.
- Problem B: one unconfined layer with recharge, a river line, a constant-head west edge and a
  pumping well. The well and river sit at points that are inside cells for every cell size, and
  the river conductance is given per metre of river. The reference is MF6 PRT on the finest DIS
  grid (gwsource.prt), compared per cell with the fraction of each cell's recharge that reaches
  the well.

Every per-cell field is sampled on one fine raster shared by all grids, inside a window that
leaves out a band along the model boundary, and compared there with the reference (a 0/1
indicator or a particle capture fraction). Metrics of a field F against a reference R:

- area error at t: area(F > t) / area(R >= 0.5) - 1;
- missed at t: share of the reference zone where F <= t;
- Jaccard index at 0.5: overlap / union of {F > 0.5} and the reference zone;
- band width: area(0.1 < F < 0.9) / length of the R = 0.5 contour, the mean distance between
  the F = 0.1 and F = 0.9 contours across the zone edge; in cells: divided by the mean cell size.

DISV grids are Voronoi grids made with Triangle (maximum triangle area h^2) through FloPy; their
mean cell size is reported, not assumed. The shared helpers live in tutorials/herebedragons.py.
"""

from dataclasses import dataclass, field
from pathlib import Path

import contourpy
import flopy
import numpy as np
import pandas as pd
from flopy.utils.gridintersect import GridIntersect
from flopy.utils.triangle import Triangle
from flopy.utils.voronoi import VoronoiGrid
from matplotlib.path import Path as MplPath
from shapely.geometry import LineString, Point

import herebedragons as hbd  # tutorials/ is on sys.path (the notebook's first cell)

import gwsource as gs
from gwsource.experimental import face_routing as fr
from gwsource.prt import PrtConfig, track_particles

GRID_KINDS = ("DIS", "DISV")
EDGE_TOL = 1e-6
THRESHOLDS = (0.01, 0.1, 0.5)
BAND = (0.1, 0.9)
JITTER = (1.1e-6, 0.7e-6)  # moves raster points off cell edges for the point-in-polygon test
WELL = "wel"  # destination group name: the WEL package
CELL_SIZE_TICKS = (12.5, 25.0, 50.0, 100.0, 200.0)  # m, x ticks of the convergence plots


@dataclass
class ProblemA:
    """Problem A: uniform flow plus a well, confined, constant T (lengths in m, time in d)."""

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
        """Aquifer transmissivity T = k b [m2/d]."""
        return self.k * self.thickness

    @property
    def regional_discharge(self) -> float:
        """Regional discharge per unit width U = T i [m2/d]."""
        return self.transmissivity * self.gradient


@dataclass
class ProblemB:
    """Problem B: one unconfined layer, recharge, river, west constant head and a well."""

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
    """A built and run one-layer model: workspace, name, grid kind, cell size and grid."""

    ws: Path
    name: str
    kind: str
    h: float
    modelgrid: object
    info: dict = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        """Number of cells."""
        return int(self.modelgrid.ncpl)

    @property
    def grb_file(self) -> Path:
        """Binary grid file."""
        return self.ws / f"{self.name}.{self.kind.lower()}.grb"

    @property
    def mean_cell_size(self) -> float:
        """Square root of the mean cell area [m]."""
        return float(np.sqrt(np.mean(cell_areas(self.modelgrid))))


# ---------------------------------------------------------------- grids


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


def cellid_2d(modelgrid, i: int) -> tuple[int, ...]:
    """Return the (row, col) of a structured cell number, or (i,) for a vertex grid."""
    if modelgrid.grid_type == "structured":
        return tuple(int(v) for v in divmod(i, modelgrid.ncol))
    return (i,)


def cell_vertices(modelgrid, i: int) -> np.ndarray:
    """Return the x, y of the vertices of one cell."""
    return np.asarray(modelgrid.get_cell_vertices(*cellid_2d(modelgrid, i)))


def boundary_cells(modelgrid, lx: float, ly: float) -> np.ndarray:
    """Return the cells with a vertex on the domain boundary."""
    out = []
    for i in range(modelgrid.ncpl):
        xy = cell_vertices(modelgrid, i)
        on_edge = (xy.min(axis=0) < EDGE_TOL).any()
        on_edge |= xy[:, 0].max() > lx - EDGE_TOL or xy[:, 1].max() > ly - EDGE_TOL
        if on_edge:
            out.append(i)
    return np.asarray(out, dtype=int)


def west_edge_cells(modelgrid) -> np.ndarray:
    """Return the cells with a vertex on x = 0."""
    return np.asarray([i for i in range(modelgrid.ncpl)
                       if cell_vertices(modelgrid, i)[:, 0].min() < EDGE_TOL], dtype=int)


def cell_at(modelgrid, x: float, y: float) -> int:
    """Return the cell number containing the point (x, y)."""
    if modelgrid.grid_type == "structured":
        row, col = modelgrid.intersect(x, y)
        return int(row * modelgrid.ncol + col)
    return int(GridIntersect(modelgrid).intersects(Point(x, y), dataframe=False).cellids[0])


def voronoi_gridprops(ws: Path, triangle_exe: Path, lx: float, ly: float, h: float) -> dict:
    """Return DISV grid properties of a Voronoi grid over [0, lx] x [0, ly] (Triangle area h^2)."""
    tri_ws = ws / "triangle"
    tri_ws.mkdir(parents=True, exist_ok=True)
    tri = Triangle(model_ws=str(tri_ws), exe_name=str(triangle_exe), maximum_area=h * h, angle=30.0)
    tri.add_polygon([(0.0, 0.0), (lx, 0.0), (lx, ly), (0.0, ly)])
    tri.build(verbose=False)
    return VoronoiGrid(tri).get_disv_gridprops()


def add_discretisation(gwf, ws: Path, triangle_exe: Path, kind: str, h: float, lx: float,
                       ly: float, top: float, botm: float) -> None:
    """Add DIS (h x h cells) or a Voronoi DISV (Triangle maximum area h^2)."""
    assert kind in GRID_KINDS, f"grid kind must be one of {GRID_KINDS}"
    if kind == "DIS":
        nrow, ncol = int(round(ly / h)), int(round(lx / h))
        assert abs(nrow * h - ly) < EDGE_TOL and abs(ncol * h - lx) < EDGE_TOL, "h must divide"
        flopy.mf6.ModflowGwfdis(gwf, nlay=1, nrow=nrow, ncol=ncol, delr=h, delc=h, top=top,
                                botm=botm, filename=f"{gwf.name}.dis")
        return
    props = voronoi_gridprops(ws, triangle_exe, lx, ly, h)
    flopy.mf6.ModflowGwfdisv(gwf, nlay=1, top=top, botm=botm, filename=f"{gwf.name}.disv", **props)


def make_sim(name: str, ws: Path, exe: Path):
    """Create a steady one-step simulation (TDIS, IMS) and an empty GWF model."""
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="days")
    flopy.mf6.ModflowIms(
        sim, complexity="simple", outer_dvclose=1e-10, outer_maximum=300, inner_maximum=500,
        inner_dvclose=1e-11, rcloserecord=1e-9, linear_acceleration="bicgstab",
    )
    return sim, flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)


def add_npf_ic_oc(gwf, k: float, icelltype: int, strt: float) -> None:
    """Add NPF (saturation and specific discharge saved, as PRT needs), IC and OC."""
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=icelltype, k=k, save_flows=True,
                            save_saturation=True, save_specific_discharge=True)
    flopy.mf6.ModflowGwfic(gwf, strt=strt)
    flopy.mf6.ModflowGwfoc(gwf, budget_filerecord=f"{gwf.name}.cbc",
                           head_filerecord=f"{gwf.name}.hds",
                           saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")])


def run(sim) -> None:
    """Write and run a simulation, asserting success."""
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "MF6 run failed:\n" + "\n".join(buff[-20:])


# ---------------------------------------------------------------- problem A


def analytic_head(x, y, spec: ProblemA) -> np.ndarray:
    """Return the analytical head of uniform flow plus a pumping well (superposition)."""
    theta = np.radians(spec.angle_deg)
    dx, dy = np.asarray(x) - spec.well_x, np.asarray(y) - spec.well_y
    along = dx * np.cos(theta) + dy * np.sin(theta)
    r2 = np.maximum(dx * dx + dy * dy, 1e-6)
    well = spec.rate / (4.0 * np.pi * spec.transmissivity) * np.log(r2)
    return spec.h0 - spec.gradient * along + well


def build_problem_a(ws: Path, exe: Path, triangle_exe: Path, spec: ProblemA, kind: str,
                    h: float) -> GridModel:
    """Build and run problem A on one grid."""
    name = "a_" + kind.lower()
    ws.mkdir(parents=True, exist_ok=True)
    sim, gwf = make_sim(name, ws, exe)
    add_discretisation(gwf, ws, triangle_exe, kind, h, spec.lx, spec.ly, spec.thickness, 0.0)
    grid = gwf.modelgrid
    add_npf_ic_oc(gwf, spec.k, 0, spec.h0)
    perimeter = boundary_cells(grid, spec.lx, spec.ly)
    xc, yc = np.ravel(grid.xcellcenters), np.ravel(grid.ycellcenters)
    heads = analytic_head(xc[perimeter], yc[perimeter], spec)
    chd = [((0, *cellid_2d(grid, int(i))), float(hd)) for i, hd in zip(perimeter, heads)]
    well = cell_at(grid, spec.well_x, spec.well_y)
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [((0, *cellid_2d(grid, well)), -spec.rate)]},
        save_flows=True, pname="wel",
    )
    run(sim)
    return GridModel(ws, name, kind, h, grid, {"well_cell": well})


def capture_zone_mask(x: np.ndarray, y: np.ndarray, spec: ProblemA) -> np.ndarray:
    """Return True where (x, y) lies in the analytical capture zone (Javandel and Tsang 1986).

    In flow-aligned coordinates (s along the regional flow, n across, well at the origin) the
    dividing streamline is s = n / tan(2 pi U n / Q) for |n| < Q / (2 U); the zone is the
    upstream side of it. The stagnation point lies at s = Q / (2 pi U) downstream of the well.
    """
    theta = np.radians(spec.angle_deg)
    dx, dy = np.asarray(x) - spec.well_x, np.asarray(y) - spec.well_y
    s = dx * np.cos(theta) + dy * np.sin(theta)
    n = np.abs(-dx * np.sin(theta) + dy * np.cos(theta))
    u, q = spec.regional_discharge, spec.rate
    inside = n < q / (2.0 * u)
    angle = 2.0 * np.pi * u * np.where(inside, n, 0.0) / q
    with np.errstate(divide="ignore", invalid="ignore"):
        divide = np.where(n > 1e-9, n / np.tan(angle), q / (2.0 * np.pi * u))
    return inside & (s <= divide)


def divide_line(spec: ProblemA, n_points: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Return x, y of the analytical dividing streamline (both branches, for plotting)."""
    u, q = spec.regional_discharge, spec.rate
    n = np.linspace(-0.4999, 0.4999, n_points) * q / u
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(np.abs(n) > 1e-9, n / np.tan(2.0 * np.pi * u * n / q), q / (2 * np.pi * u))
    theta = np.radians(spec.angle_deg)
    return (spec.well_x + s * np.cos(theta) - n * np.sin(theta),
            spec.well_y + s * np.sin(theta) + n * np.cos(theta))


# ---------------------------------------------------------------- problem B


def river_cells(modelgrid, spec: ProblemB) -> list[tuple[int, float]]:
    """Return (cell, river length in the cell) along the line x = riv_x."""
    line = LineString([(spec.riv_x, 0.0), (spec.riv_x, spec.ly)])
    result = GridIntersect(modelgrid).intersect(line, geo_dataframe=False)
    return [(int(c), float(length)) for c, length in zip(result["cellid"], result["lengths"])
            if length > EDGE_TOL]


def build_problem_b(ws: Path, exe: Path, triangle_exe: Path, spec: ProblemB, kind: str,
                    h: float) -> GridModel:
    """Build and run problem B on one grid."""
    name = "b_" + kind.lower()
    ws.mkdir(parents=True, exist_ok=True)
    sim, gwf = make_sim(name, ws, exe)
    add_discretisation(gwf, ws, triangle_exe, kind, h, spec.lx, spec.ly, spec.top, spec.botm)
    add_npf_ic_oc(gwf, spec.k, 1, spec.strt)
    grid = gwf.modelgrid
    cid = lambda i: (0, *cellid_2d(grid, int(i)))  # noqa: E731
    rivs = river_cells(grid, spec)
    well = cell_at(grid, spec.well_x, spec.well_y)
    chd = [(cid(i), spec.chd_head) for i in west_edge_cells(grid)]
    riv = [(cid(i), spec.riv_stage, spec.riv_cond_per_m * length, spec.riv_rbot)
           for i, length in rivs]
    rch = [(cid(i), spec.rech) for i in range(grid.ncpl)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data={0: riv}, save_flows=True, pname="riv")
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data={0: [(cid(well), spec.well_rate)]},
                            save_flows=True, pname="wel")
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    run(sim)
    return GridModel(ws, name, kind, h, grid, {"well_cell": well, "riv_cells": [i for i, _ in rivs]})


def recharge_fraction(step: gs.FlowStep, term_fraction: np.ndarray) -> np.ndarray:
    """Return, per cell, the fraction of the cell's recharge that reaches the well."""
    out = np.zeros(step.n_cells)
    rch = np.flatnonzero(gs.select(step, package="RCH").terms)
    out[step.term_cell[rch]] = term_fraction[rch]
    return out


# ---------------------------------------------------------------- tracing


def well_group(step: gs.FlowStep) -> dict[str, gs.Selection]:
    """Return the destination group: the WEL package."""
    return {WELL: gs.select(step, package="WEL")}


def face_routing(model: GridModel, step: gs.FlowStep) -> fr.FaceRoutingResult:
    """Return the face-routing backward trace to the well (DIS only; recharge on the top face)."""
    delr, delc = fr.read_dis_spacing(str(model.grb_file))
    return fr.route_backward(step, well_group(step), delr, delc)


def package_shares(volume_from_by_term: dict, total: float) -> dict[str, float]:
    """Return the share of the well water by source package."""
    return {p.split("-")[0].upper(): float(v.sum() / total) for p, v in volume_from_by_term.items()}


def prt_shares(prt) -> dict[str, float]:
    """Return the share of the captured particle flow by release package."""
    packages = np.asarray([str(p).split("-")[0].upper() for p in prt.release.package])
    return {str(p): float(prt.captured_weight[packages == p].sum() / prt.captured_flow)
            for p in np.unique(packages)}


def run_prt(model: GridModel, step: gs.FlowStep, mixed: gs.BackwardResult, exe: Path,
            porosity: float, subdivisions: int) -> dict:
    """Run flow-weighted MF6 PRT particles to the well; return the per-cell fraction and totals."""
    prt = track_particles(model.ws, step, mixed, WELL,
                          PrtConfig(porosity=porosity, subdivisions=subdivisions), exe,
                          model.ws / "prt")
    return {
        "fraction": np.nan_to_num(prt.cell_capture_fraction),
        "mean_time": float(prt.mean_arrival),
        "n_particles": int(len(prt.captured_weight)),
        "captured_flow": float(prt.captured_flow),
        "shares": prt_shares(prt),
    }


# ---------------------------------------------------------------- raster and metrics


@dataclass
class Raster:
    """The shared raster of one problem: points, evaluation window, reference and its edge."""

    xr: np.ndarray
    yr: np.ndarray
    spacing: float
    window: np.ndarray
    ref: np.ndarray | None = None
    edge: float = float("nan")

    @property
    def pixel(self) -> float:
        """Area of one raster cell [m2]."""
        return self.spacing**2

    def set_reference(self, ref: np.ndarray) -> None:
        """Set the reference field and the length of its 0.5 contour inside the window."""
        self.ref = ref
        masked = np.ma.masked_where(~self.window, ref.astype(float))
        self.edge = contour_length(self.xr, self.yr, masked)


def make_raster(lx: float, ly: float, spacing: float, margin: float) -> Raster:
    """Return the raster of cell centres over [0, lx] x [0, ly] and its evaluation window."""
    xr, yr = np.meshgrid(np.arange(spacing / 2, lx, spacing), np.arange(spacing / 2, ly, spacing))
    window = (xr > margin) & (xr < lx - margin) & (yr > margin) & (yr < ly - margin)
    return Raster(xr, yr, spacing, window)


def raster_cells(modelgrid, raster: Raster) -> np.ndarray:
    """Return the cell number containing each raster point."""
    xr, yr, spacing = raster.xr, raster.yr, raster.spacing
    if modelgrid.grid_type == "structured":
        col = np.searchsorted(np.cumsum(modelgrid.delr), xr, side="right")
        row = np.searchsorted(np.cumsum(modelgrid.delc), np.sum(modelgrid.delc) - yr, side="right")
        return row * modelgrid.ncol + col
    index = np.full(xr.shape, -1, dtype=np.int64)
    x0, y0 = xr[0, 0], yr[0, 0]
    for i in range(modelgrid.ncpl):
        poly = np.asarray(modelgrid.get_cell_vertices(i))
        c0 = max(int(np.floor((poly[:, 0].min() - x0) / spacing)), 0)
        c1 = min(int(np.ceil((poly[:, 0].max() - x0) / spacing)) + 1, xr.shape[1])
        r0 = max(int(np.floor((poly[:, 1].min() - y0) / spacing)), 0)
        r1 = min(int(np.ceil((poly[:, 1].max() - y0) / spacing)) + 1, xr.shape[0])
        sub_x, sub_y = xr[r0:r1, c0:c1] + JITTER[0], yr[r0:r1, c0:c1] + JITTER[1]
        hit = MplPath(poly).contains_points(np.column_stack([sub_x.ravel(), sub_y.ravel()]))
        block = index[r0:r1, c0:c1]
        block[hit.reshape(block.shape) & (block < 0)] = i
    assert (index >= 0).all(), "some raster points are not inside any cell"
    return index


def contour_length(xr: np.ndarray, yr: np.ndarray, values: np.ndarray, level: float = 0.5) -> float:
    """Return the total length of the level contour of a raster field."""
    lines = contourpy.contour_generator(xr, yr, values).lines(level)
    return float(sum(np.hypot(*np.diff(seg, axis=0).T).sum() for seg in lines))


def cell_average(index: np.ndarray, values: np.ndarray, n_cells: int) -> np.ndarray:
    """Return the per-cell mean of raster values (the cell-averaged reference field)."""
    total = np.bincount(index.ravel(), weights=values.ravel().astype(float), minlength=n_cells)
    count = np.bincount(index.ravel(), minlength=n_cells)
    return np.divide(total, count, out=np.zeros(n_cells), where=count > 0)


def zone_metrics(f: np.ndarray, raster: Raster, cell_size: float,
                 thresholds: tuple[float, ...] = THRESHOLDS) -> dict[str, float]:
    """Return the zone metrics of a raster field f against the raster's reference (see module)."""
    f, ref_zone = f[raster.window], raster.ref[raster.window] >= 0.5
    out = {}
    for t in thresholds:
        zone = f > t
        out[f"area_err_{t}"] = float(zone.sum() / ref_zone.sum() - 1.0)
        out[f"missed_{t}"] = float((ref_zone & ~zone).sum() / ref_zone.sum())
    zone = f > 0.5
    out["jaccard_0.5"] = float((zone & ref_zone).sum() / (zone | ref_zone).sum())
    band = ((f > BAND[0]) & (f < BAND[1])).sum() * raster.pixel
    out["band_width"] = float(band / raster.edge)
    out["band_cells"] = out["band_width"] / cell_size
    return out


def metrics_rows(base: dict, run: dict, raster: Raster) -> list[dict]:
    """Return one metrics row per method of a run (needs run['index'], its raster cells)."""
    h_mean = run["model"].mean_cell_size
    return [{**base, "mean_h": h_mean, "cells": run["model"].n_cells, "method": method,
             **zone_metrics(f[run["index"]], raster, h_mean)}
            for method, f in run["fields"].items()]


def convergence_rate(h: np.ndarray, values: np.ndarray) -> float:
    """Return the least-squares slope of log|values| against log h."""
    h, values = np.asarray(h, float), np.abs(np.asarray(values, float))
    keep = values > 0
    assert keep.sum() >= 2, "need at least two non-zero values"
    return float(np.polyfit(np.log(h[keep]), np.log(values[keep]), 1)[0])


def rates_table(table: pd.DataFrame, by: list[str],
                columns: tuple[str, ...] = ("band_width", "area_err_0.1")) -> pd.DataFrame:
    """Return the convergence rate of each column against the mean cell size, per group."""
    rows = {key: {c: convergence_rate(part["mean_h"], part[c]) for c in columns}
            for key, part in table.groupby(by)}
    return pd.DataFrame(rows).T.rename_axis(by)


# ---------------------------------------------------------------- one grid of each problem


def problem_a_run(ws: Path, exe: Path, triangle_exe: Path, spec: ProblemA, kind: str, h: float,
                  raster: Raster) -> dict:
    """Run problem A on one grid: full mixing, face routing (DIS) and the cell-averaged zone."""
    model = build_problem_a(ws, exe, triangle_exe, spec, kind, h)
    step = gs.read_step(model.ws)
    index = raster_cells(model.modelgrid, raster)
    fields = {"full mixing": gs.backward(step, well_group(step)).fraction_through[WELL]}
    if kind == "DIS":
        fields["face routing"] = face_routing(model, step).fraction_through[WELL]
    fields["cell-averaged exact"] = cell_average(index, raster.ref, model.n_cells)
    return {"model": model, "step": step, "index": index, "fields": fields}


def problem_b_run(ws: Path, exe: Path, triangle_exe: Path, spec: ProblemB, kind: str, h: float,
                  porosity: float, prt_subdivisions: int = 2) -> dict:
    """Run problem B on one grid: full mixing; on DIS also face routing and MF6 PRT."""
    model = build_problem_b(ws, exe, triangle_exe, spec, kind, h)
    step = gs.read_step(model.ws)
    mixed = gs.backward(step, well_group(step))
    q = mixed.destination_inflow[WELL]
    tt = gs.travel_time(step, mixed, porosity)
    out = {
        "model": model, "step": step, "well_inflow": q,
        "fields": {"full mixing": mixed.fraction_through[WELL]},
        "shares": {"full mixing": package_shares(mixed.volume_from_by_term[WELL], q)},
        "mean_time": {"full mixing": float(tt.mean_transit_time[WELL])},
    }
    if kind == "DIS":
        routed = face_routing(model, step)
        volume = gs.water_volume(step, porosity)
        out["fields"]["face routing"] = recharge_fraction(step, routed.term_fraction[WELL])
        out["shares"]["face routing"] = package_shares(routed.volume_from_by_term[WELL], q)
        out["mean_time"]["face routing"] = float(volume @ routed.fraction_through[WELL] / q)
        prt = run_prt(model, step, mixed, exe, porosity, prt_subdivisions)
        out["prt"] = prt
        out["fields"]["PRT"] = prt["fraction"]
        out["shares"]["PRT"] = prt["shares"]
        out["mean_time"]["PRT"] = prt["mean_time"]
    return out


# ---------------------------------------------------------------- plots


def plot_field(ax, model: GridModel, step: gs.FlowStep, values: np.ndarray, title: str,
               well_xy: tuple[float, float], colorbar: bool = False):
    """Map one per-cell field on its grid, with the well as a red dot."""
    hbd.plot_cells(model.grb_file, step, values, ax=ax, title=title, label="F (-)",
                   overlay=False, colorbar=colorbar, cmap="viridis", vmin=0.0, vmax=1.0)
    ax.plot(*well_xy, "o", color="tab:red", ms=4, mec="k", mew=0.5)
    return ax


def plot_convergence(axes, table: pd.DataFrame, series: list[tuple[str, dict, dict]],
                     guide_h: tuple[float, float]) -> None:
    """Plot band width and the F > 0.1 and F > 0.5 area errors against the mean cell size.

    series: (label, column values that select the rows, line style) per line. guide_h: the cell
    sizes between which the dashed h^0.5 guide is drawn on the band-width panel.
    """
    for label, select, style in series:
        part = table.loc[(table[list(select)] == pd.Series(select)).all(axis=1)].sort_values("mean_h")
        axes[0].loglog(part["mean_h"], part["band_width"], label=label, **style)
        axes[1].semilogx(part["mean_h"], 100.0 * part["area_err_0.1"], **style)
        axes[2].semilogx(part["mean_h"], 100.0 * part["area_err_0.5"], **style)
    h = np.geomspace(*guide_h, 20)
    top = table["band_width"].max()
    axes[0].loglog(h, 0.8 * top * np.sqrt(h / h.max()), "k--", lw=0.8, label="$h^{0.5}$")
    for ax in axes[1:]:
        ax.axhspan(-5.0, 5.0, color="0.85", zorder=0)
        ax.axhline(0.0, color="0.4", lw=0.6)
    for ax, ylabel in zip(axes, ("band width 0.1 < F < 0.9 (m)", "area error F > 0.1 (%)",
                                 "area error F > 0.5 (%)")):
        ax.set_xticks(CELL_SIZE_TICKS, [f"{t:g}" for t in CELL_SIZE_TICKS])
        ax.minorticks_off()
        ax.set_xlabel("mean cell size h (m)")
        ax.set_ylabel(ylabel)
        ax.grid(True, which="both", lw=0.3, alpha=0.5)
