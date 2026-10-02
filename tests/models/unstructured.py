"""DISV (Voronoi) and DISU versions of the base test model (model 1).

The DISV model is a Voronoi grid built with FloPy's Triangle and VoronoiGrid utilities (the
triangle executable comes from get-modflow). Its stresses are placed by geometry, so it is the
same physical problem as model 1 on a different grid. The DISU models are cell-for-cell copies
of model 1, built with get_disu_kwargs, with and without vertices; they keep model 1's IDOMAIN.
"""

from pathlib import Path

import flopy
import numpy as np
from flopy.utils.gridintersect import GridIntersect
from flopy.utils.gridutil import get_disu_kwargs
from flopy.utils.triangle import Triangle
from flopy.utils.voronoi import VoronoiGrid
from shapely.geometry import LineString, Point

from .common import (
    BaseSpec,
    ModelRun,
    add_base_stresses,
    add_npf_ic_oc,
    base_idomain,
    make_sim,
    run_model,
)

STEADY = ((1.0, 1, 1.0),)


def voronoi_gridprops(ws: Path, triangle_exe: Path, spec: BaseSpec, max_area: float) -> dict:
    """Build a Voronoi grid over the base-problem domain and return its DISV grid properties."""
    lx, ly = spec.ncol * spec.delr, spec.nrow * spec.delc
    tri_ws = ws / "triangle"
    tri_ws.mkdir(parents=True, exist_ok=True)
    tri = Triangle(
        model_ws=str(tri_ws), exe_name=str(triangle_exe), maximum_area=max_area, angle=30.0
    )
    tri.add_polygon([(0.0, 0.0), (lx, 0.0), (lx, ly), (0.0, ly)])
    tri.build(verbose=False)
    return VoronoiGrid(tri).get_disv_gridprops()


def _cell_vertex_x(gridprops: dict) -> list[np.ndarray]:
    """Return the x coordinates of each cell's vertices."""
    xv = np.array([v[1] for v in gridprops["vertices"]])
    return [xv[np.array(c[4:], dtype=int)] for c in gridprops["cell2d"]]


def _voronoi_stress_cells(gridprops: dict, spec: BaseSpec) -> dict:
    """Place the base-problem stresses on Voronoi cells by geometry."""
    mg = flopy.discretization.VertexGrid(
        vertices=gridprops["vertices"], cell2d=gridprops["cell2d"],
        top=np.full(gridprops["ncpl"], spec.top), botm=np.full((1, gridprops["ncpl"]), spec.botm),
    )
    gi = GridIntersect(mg)
    riv_x = (spec.riv_col + 0.5) * spec.delr
    ly = spec.nrow * spec.delc
    wel_xy = ((spec.wel_cell[1] + 0.5) * spec.delr, ly - (spec.wel_cell[0] + 0.5) * spec.delc)
    riv_line = LineString([(riv_x, 0.0), (riv_x, ly)])
    riv = sorted(int(i) for i in gi.intersects(riv_line, dataframe=False).cellids)
    wel = [int(i) for i in gi.intersects(Point(wel_xy), dataframe=False).cellids][:1]
    chd = [i for i, xs in enumerate(_cell_vertex_x(gridprops)) if xs.min() < 1.0e-6]
    return {"chd": chd, "riv": riv, "wel": wel}


def build_voronoi_disv(
    ws: Path, exe: Path, triangle_exe: Path, spec: BaseSpec | None = None, max_area: float = 2500.0
) -> ModelRun:
    """Model 3: DISV Voronoi version of model 1 (all cells active)."""
    spec = BaseSpec() if spec is None else spec
    name = "m3_disv"
    gridprops = voronoi_gridprops(ws, triangle_exe, spec, max_area)
    ncpl = gridprops["ncpl"]
    cells = _voronoi_stress_cells(gridprops, spec)
    assert cells["wel"] and cells["riv"] and cells["chd"], "stress placement on Voronoi grid failed"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = f"{name}.disv"
    flopy.mf6.ModflowGwfdisv(
        gwf, nlay=1, top=spec.top, botm=spec.botm, filename=dis_filename, **gridprops
    )
    add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt)
    chd = [((0, i), spec.chd_head) for i in cells["chd"]]
    riv_cond = spec.riv_cond * spec.nrow / len(cells["riv"])  # same total conductance
    riv = [((0, i), spec.riv_stage, riv_cond, spec.riv_rbot) for i in cells["riv"]]
    wel = [((0, cells["wel"][0]), spec.wel_rate)]
    rch = [((0, i), spec.rech) for i in range(ncpl)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data={0: riv}, save_flows=True, pname="riv")
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data={0: wel}, save_flows=True, pname="wel")
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    notes = {"spec": spec, "ncpl": ncpl, "stress_cells": cells}
    return run_model(sim, gwf, name, ws, dis_filename, notes)


def _disu_cellid(spec: BaseSpec):
    """Return a function mapping (row, col) of the base problem to a DISU cellid."""
    return lambda rc: (rc[0] * spec.ncol + rc[1],)


def build_base_disu(ws: Path, exe: Path, with_vertices: bool, spec: BaseSpec | None = None) -> ModelRun:
    """Model 4: DISU copy of model 1 (same cells, connections and IDOMAIN), with or without vertices."""
    spec = BaseSpec() if spec is None else spec
    name = "m4_disu_vert" if with_vertices else "m4_disu_novert"
    disu_kwargs = get_disu_kwargs(
        1, spec.nrow, spec.ncol,
        np.full(spec.ncol, spec.delr), np.full(spec.nrow, spec.delc),
        spec.top, np.array([spec.botm]), return_vertices=with_vertices,
    )
    if not with_vertices:
        disu_kwargs.pop("nvert", None)
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = f"{name}.disu"
    flopy.mf6.ModflowGwfdisu(
        gwf, idomain=base_idomain(spec).ravel(), filename=dis_filename, **disu_kwargs
    )
    add_npf_ic_oc(
        gwf, name, k=spec.k, icelltype=1, strt=spec.strt, save_specific_discharge=with_vertices
    )
    add_base_stresses(gwf, spec, _disu_cellid(spec), [spec.wel_rate], [1.0])
    notes = {"spec": spec, "inactive_cells": spec.inactive_cells, "with_vertices": with_vertices}
    return run_model(sim, gwf, name, ws, dis_filename, notes)
