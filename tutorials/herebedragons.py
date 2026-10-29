"""Shared helpers for the gwsource tutorials: paths, small MF6 model builders and map plots.

This is the one support module that all tutorial notebooks import (as hbd). It holds the
tutorial model builders, an MF6 GWT tracer runner, wrappers around FloPy's model splitter, and
table and map helpers. It is tutorial code, not part of the gwsource API.

The notebooks are the narrative; everything reusable lives here. Every builder writes and runs
one small MODFLOW 6 model in the workspace it is given and returns a ModelRun. All models save
what gwsource needs: the binary grid file, a budget file (SAVE_FLOWS on NPF, STO and every
package; BUDGET FILEOUT on SFR, MAW and MVR), heads, DATA-SAT (SAVE_SATURATION) and DATA-SPDIS
(SAVE_SPECIFIC_DISCHARGE, which MF6 PRT needs).

The tutorial aquifer (AquiferSpec) is a single unconfined layer, 2 km x 2 km in 50 m cells.
Recharge falls everywhere; a constant head on the west edge (10 m) brings regional inflow from
upland, and a stream (SFR) flowing north to south along one column, its stage close to 6 m,
drains the aquifer. A supply well just west of the stream draws it down, so the well captures
recharge, regional inflow from the west edge and some stream water. The stream reaches are
source/sink terms of their aquifer cells unless a trace reads them as nodes. The variants keep
this plan so results compare across tutorials: three layers (with a weak-sink well), Voronoi
DISV, DISU, XT3D anisotropy, transient seasons, drains feeding the stream through the water
mover, a multi-aquifer well, and random log-K realisations.

Stresses are given on (row, col) of the tutorial grid; the stream reaches carry the boundnames
'stream_north' and 'stream_south', and wells carry their own names.
"""

import importlib.util
import shutil
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np

import gwsource as gs

WORK_DIR_NAME = "_work"
STEADY = ((1.0, 1, 1.0),)
IMS_SETTINGS = {
    "complexity": "simple",
    "outer_dvclose": 1.0e-9,
    "outer_maximum": 200,
    "inner_maximum": 300,
    "inner_dvclose": 1.0e-10,
    "rcloserecord": 1.0e-8,
    "linear_acceleration": "bicgstab",
}
VORONOI_BACKGROUND = 50.0  # m: vorflow mesh size away from the features (as the DIS cells)
VORONOI_WELL_SIZE = 10.0  # m: vorflow mesh size at the wells
VORONOI_RIVER_SIZE = 12.5  # m: vorflow mesh size along the stream
SEASONS = ("wet", "wet-to-dry", "dry", "dry-to-wet")  # named by recharge (SEASON_RECHARGE)
SEASON_RECHARGE = (1.8, 1.0, 0.1, 1.1)  # multipliers of AquiferSpec.rech
SEASON_PUMPING = (0.8, 1.0, 1.4, 0.8)  # multipliers of the well rates
FEATURE_STYLES = {  # package: scatter style for overlay_features()
    "CHD": {"marker": "s", "s": 6, "color": "0.45", "label": "constant head"},
    "RIV": {"marker": "s", "s": 10, "color": "tab:blue", "label": "river"},
    "SFR": {"marker": "s", "s": 10, "color": "tab:blue", "label": "stream"},
    "DRN": {"marker": "v", "s": 50, "color": "tab:green", "edgecolor": "k", "label": "drain"},
    "WEL": {"marker": "*", "s": 160, "color": "tab:red", "edgecolor": "k", "label": "well"},
    "MAW": {"marker": "*", "s": 160, "color": "tab:orange", "edgecolor": "k", "label": "MAW well"},
}


# ---------------------------------------------------------------- paths


def repo_root() -> Path:
    """Return the repository root (the parent of tutorials/)."""
    return Path(__file__).resolve().parents[1]


def exe_path(name: str, bin_dir: Path | None = None) -> Path:
    """Return the path of an executable in <repo>/bin, failing with a setup hint if missing."""
    bin_dir = repo_root() / "bin" if bin_dir is None else Path(bin_dir)
    suffix = ".exe" if sys.platform.startswith("win") else ""
    exe = bin_dir / f"{name}{suffix}"
    assert exe.is_file(), f"{exe} not found; run scripts/setup_env.sh to download it into bin/"
    return exe


def mf6_exe() -> Path:
    """Return the MODFLOW 6 executable in <repo>/bin."""
    return exe_path("mf6")


def work_dir(name: str, clean: bool = False) -> Path:
    """Return tutorials/_work/<name> (git-ignored), created; clean=True empties it first."""
    path = Path(__file__).resolve().parent / WORK_DIR_NAME / name
    if clean and path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------- model description


@dataclass
class AquiferSpec:
    """Plan geometry, properties and stresses of the tutorial aquifer (stresses on (row, col)).

    k may be a scalar or a (nrow, ncol) array. wells: (boundname, (row, col), rate [m3/d]).
    The stream bed top falls from stream_top at the north edge by stream_slope per metre; its
    conductance per metre of stream is stream_bed_k x stream_width / stream_bed_thick.
    """

    nrow: int = 40
    ncol: int = 40
    delr: float = 50.0
    delc: float = 50.0
    top: float = 20.0
    botm: float = -30.0
    k: float | np.ndarray = 5.0
    strt: float = 10.0
    rech: float = 5.0e-4
    chd_head: float = 10.0
    stream_col: int = 30
    stream_top: float = 6.0  # m, bed top at the north edge
    stream_slope: float = 1.0e-4  # bed slope (-), also the slope in Manning's equation
    stream_width: float = 5.0  # m
    stream_bed_k: float = 2.0  # m/d
    stream_bed_thick: float = 1.0  # m
    stream_manning: float = 0.03  # s/m^(1/3)
    wells: tuple[tuple[str, tuple[int, int], float], ...] = (
        ("supply_well", (20, 28), -800.0),
    )

    @property
    def lx(self) -> float:
        """Domain length west-east [m]."""
        return self.ncol * self.delr

    @property
    def ly(self) -> float:
        """Domain length south-north [m]."""
        return self.nrow * self.delc

    def xy(self, rc: tuple[int, int]) -> tuple[float, float]:
        """Return the model (x, y) of the centre of cell (row, col); row 0 is the north edge."""
        return (rc[1] + 0.5) * self.delr, self.ly - (rc[0] + 0.5) * self.delc

    def node(self, rc: tuple[int, int], layer: int = 0) -> int:
        """Return the 0-based node number of (row, col) in a DIS/DISU layer."""
        return (layer * self.nrow + rc[0]) * self.ncol + rc[1]


@dataclass
class ModelRun:
    """What a notebook needs from a built and run model: paths, FloPy objects and notes."""

    name: str
    ws: Path
    sim: flopy.mf6.MFSimulation
    gwf: flopy.mf6.ModflowGwf
    grb_file: Path
    budget_file: Path
    head_file: Path
    spec: AquiferSpec
    info: dict = field(default_factory=dict)


def stream_boundname(y: float, spec: AquiferSpec) -> str:
    """Return the boundname of the stream reach at y ('stream_north' or 'stream_south')."""
    return "stream_north" if y > spec.ly / 2.0 else "stream_south"


def chd_cells(spec: AquiferSpec) -> list[tuple[int, int]]:
    """Return the (row, col) of the constant-head west edge."""
    return [(row, 0) for row in range(spec.nrow)]


def stream_cells(spec: AquiferSpec) -> list[tuple[int, int]]:
    """Return the (row, col) of the stream column, north to south."""
    return [(row, spec.stream_col) for row in range(spec.nrow)]


def stream_x(spec: AquiferSpec) -> float:
    """Return the x of the stream line [m] (the centre of the stream column)."""
    return (spec.stream_col + 0.5) * spec.delr


def all_cells(spec: AquiferSpec) -> list[tuple[int, int]]:
    """Return the (row, col) of every cell of one layer."""
    return [(row, col) for row in range(spec.nrow) for col in range(spec.ncol)]


def k_layer(spec: AquiferSpec) -> np.ndarray:
    """Return the (nrow, ncol) hydraulic conductivity of the spec."""
    return np.broadcast_to(np.asarray(spec.k, dtype=float), (spec.nrow, spec.ncol)).copy()


# ---------------------------------------------------------------- shared FloPy pieces


def make_sim(
    name: str, ws: Path, exe: Path, perioddata, ims_kwargs: dict | None = None
) -> tuple[flopy.mf6.MFSimulation, flopy.mf6.ModflowGwf]:
    """Create the simulation, TDIS, IMS (settings overridable) and an empty GWF model."""
    ws = Path(ws)
    ws.mkdir(parents=True, exist_ok=True)
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(
        sim, nper=len(perioddata), perioddata=list(perioddata), time_units="days"
    )
    flopy.mf6.ModflowIms(sim, **{**IMS_SETTINGS, **(ims_kwargs or {})})
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    return sim, gwf


def add_dis(gwf, spec: AquiferSpec, name: str, botm=None) -> str:
    """Add a DIS package of the tutorial plan (one layer, or len(botm) layers); return its file."""
    botm = [spec.botm] if botm is None else list(botm)
    filename = f"{name}.dis"
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=len(botm), nrow=spec.nrow, ncol=spec.ncol, delr=spec.delr, delc=spec.delc,
        top=spec.top, botm=botm, length_units="meters", filename=filename,
    )
    return filename


def add_npf_ic_oc(gwf, name: str, k, icelltype, strt, **npf_kwargs) -> None:
    """Add NPF (flows, saturation and specific discharge saved), IC, and OC (all heads, budgets)."""
    flopy.mf6.ModflowGwfnpf(
        gwf, icelltype=icelltype, k=k, save_flows=True, save_saturation=True,
        save_specific_discharge=True, **npf_kwargs,
    )
    flopy.mf6.ModflowGwfic(gwf, strt=strt)
    flopy.mf6.ModflowGwfoc(
        gwf, budget_filerecord=f"{name}.cbc", head_filerecord=f"{name}.hds",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )


def add_sfr(
    gwf,
    spec: AquiferSpec,
    name: str,
    cellids: list,
    lengths: list[float],
    ys: list[float],
    mover: bool = False,
) -> None:
    """Add the stream as SFR: one reach per cell, given north to south, flowing south.

    The stream has no inflow from upstream: its water is groundwater seepage (and moved water).

    lengths are the reach lengths [m] and ys the y of the reach cells [m]; the bed top of a
    reach is set by its distance from the north edge. SFR writes its own budget file (needed to
    trace with package nodes: gs.open_simulation(ws, package_nodes=("SFR",))).
    """
    n = len(cellids)
    packagedata, connections = [], []
    for rno, (cellid, length, y) in enumerate(zip(cellids, lengths, ys)):
        rtp = spec.stream_top - spec.stream_slope * (spec.ly - y)
        ncon = int(rno > 0) + int(rno < n - 1)
        packagedata.append((
            rno, cellid, length, spec.stream_width, spec.stream_slope, rtp,
            spec.stream_bed_thick, spec.stream_bed_k, spec.stream_manning, ncon, 1.0, 0,
            stream_boundname(y, spec),
        ))
        upstream = [rno - 1] if rno > 0 else []
        downstream = [-(rno + 1)] if rno < n - 1 else []
        connections.append([rno, *upstream, *downstream])
    flopy.mf6.ModflowGwfsfr(
        gwf, nreaches=n, packagedata=packagedata, connectiondata=connections,
        perioddata={0: [(0, "INFLOW", 0.0)]},  # FloPy's model splitter needs a PERIOD block
        boundnames=True, mover=mover,
        length_conversion=1.0, time_conversion=86400.0,  # Manning's n in m and s; model in m, d
        save_flows=True, budget_filerecord=f"{name}.sfr.bud", pname="sfr",
    )


def add_stresses(
    gwf,
    spec: AquiferSpec,
    to_cellid,
    name: str,
    pumping: tuple[float, ...] = (1.0,),
    recharge: tuple[float, ...] = (1.0,),
    wells: bool = True,
    nlay: int = 1,
    stream_mover: bool = False,
) -> None:
    """Add CHD (every layer), the SFR stream, WEL and RCH (top layer); WEL, RCH scaled per period.

    Layers below the first (nlay > 1) are addressed as DIS (layer, row, col). stream_mover lets
    the stream take part in a water mover (MVR).
    """
    assert len(pumping) == len(recharge), "one pumping and one recharge factor per period"
    chd = [(to_cellid(rc), spec.chd_head) for rc in chd_cells(spec)]
    chd += [((lay, *rc), spec.chd_head) for lay in range(1, nlay) for rc in chd_cells(spec)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    cells = stream_cells(spec)
    add_sfr(
        gwf, spec, name, [to_cellid(rc) for rc in cells], [spec.delc] * len(cells),
        [spec.xy(rc)[1] for rc in cells], mover=stream_mover,
    )
    if wells:
        wel = {
            kper: [(to_cellid(rc), rate * factor, bname) for bname, rc, rate in spec.wells]
            for kper, factor in enumerate(pumping)
        }
        flopy.mf6.ModflowGwfwel(
            gwf, stress_period_data=wel, boundnames=True, save_flows=True, pname="wel"
        )
    rch = {
        kper: [(to_cellid(rc), spec.rech * factor) for rc in all_cells(spec)]
        for kper, factor in enumerate(recharge)
    }
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data=rch, save_flows=True, pname="rch")


def run_model(
    sim, gwf, name: str, ws: Path, dis_filename: str, spec: AquiferSpec, info: dict
) -> ModelRun:
    """Write and run the simulation, assert normal termination, and return a ModelRun.

    info['sfr_budget_file'] is set when the model has the stream.
    """
    ws = Path(ws)
    if gwf.get_package("sfr") is not None:
        info = {**info, "sfr_budget_file": ws / f"{name}.sfr.bud"}
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, f"MF6 run of {name} failed:\n" + "\n".join(buff[-20:])
    assert "Normal termination" in (ws / "mfsim.lst").read_text(encoding="utf-8"), f"{name}: no normal termination"
    return ModelRun(
        name=name, ws=ws, sim=sim, gwf=gwf, grb_file=ws / f"{dis_filename}.grb",
        budget_file=ws / f"{name}.cbc", head_file=ws / f"{name}.hds", spec=spec, info=info,
    )


def _dis_cellid(layer: int = 0):
    """Return a function mapping (row, col) to a DIS cellid in the given layer."""
    return lambda rc: (layer, rc[0], rc[1])


def _well_nodes(spec: AquiferSpec, layer: int = 0) -> dict[str, int]:
    """Return {well boundname: 0-based node} on a DIS/DISU grid."""
    return {bname: spec.node(rc, layer) for bname, rc, _ in spec.wells}


# ---------------------------------------------------------------- (a) quickstart model


def build_quickstart(ws: Path, exe: Path, spec: AquiferSpec | None = None) -> ModelRun:
    """Steady 1-layer DIS model: recharge, a supply well, a stream and a constant-head west edge."""
    spec = AquiferSpec() if spec is None else spec
    name = "quickstart"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = add_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=k_layer(spec), icelltype=1, strt=spec.strt)
    add_stresses(gwf, spec, _dis_cellid(), name)
    info = {"well_nodes": _well_nodes(spec)}
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (b) three layers, weak sink

LAYER_BOTM = (0.0, -12.0, -30.0)
LAYER_K = (10.0, 1.0, 15.0)
LAYERED_WELLS = (  # (boundname, (layer, row, col), rate)
    ("supply_well", (2, 20, 28), -800.0),
    ("weak_well", (2, 16, 12), -5.0),
)


def build_layered(
    ws: Path,
    exe: Path,
    spec: AquiferSpec | None = None,
    botm: tuple[float, ...] = LAYER_BOTM,
    layer_k: tuple[float, ...] = LAYER_K,
    k33_ratio: float = 0.1,
    wells: tuple = LAYERED_WELLS,
) -> ModelRun:
    """Steady 3-layer DIS model; the supply well and a small weak-sink well screen layer 3 only.

    The stream and recharge act on layer 1, the constant heads on every layer. spec.wells is
    ignored; wells are (boundname, (layer, row, col), rate). info['weak_well_node'] is the
    0-based node of 'weak_well' when present.
    """
    spec = AquiferSpec() if spec is None else spec
    assert len(botm) == len(layer_k), "one conductivity per layer"
    name = "layered"
    nlay = len(botm)
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = add_dis(gwf, spec, name, botm=botm)
    k = np.asarray(layer_k)[:, None, None] * k_layer(spec) / float(np.mean(k_layer(spec)))
    add_npf_ic_oc(
        gwf, name, k=k, icelltype=[1] + [0] * (nlay - 1), strt=spec.strt, k33=k33_ratio * k
    )
    add_stresses(gwf, spec, _dis_cellid(), name, wells=False, nlay=nlay)
    wel = [(cellid, rate, bname) for bname, cellid, rate in wells]
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: wel}, boundnames=True, save_flows=True, pname="wel"
    )
    nodes = {b: int(np.ravel_multi_index(c, (nlay, spec.nrow, spec.ncol))) for b, c, _ in wells}
    info = {"well_nodes": nodes, "weak_well_node": nodes.get("weak_well"), "wells": wells}
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (c) DISV Voronoi and DISU


def require_vorflow():
    """Return the vorflow module, failing with an install hint if it is missing."""
    assert importlib.util.find_spec("vorflow") is not None, (
        "the Voronoi grid needs vorflow, an optional dependency of the tutorials only "
        "(gwsource itself does not need it): pip install vorflow"
    )
    import vorflow

    return vorflow


def vorflow_cells(
    spec: AquiferSpec,
    background: float = VORONOI_BACKGROUND,
    well_size: float = VORONOI_WELL_SIZE,
    river_size: float = VORONOI_RIVER_SIZE,
):
    """Mesh the tutorial domain with vorflow; return its Voronoi cells as a GeoDataFrame.

    background is the mesh size away from the features [m]. The mesh is refined to well_size
    at each well (a point) and to river_size along the stream (a line), and grows back to
    background with vorflow's default growth factor (1.2 from cell to cell). Each well point
    is the centre of its cell, and the stream cells are centred on the stream line.
    """
    from shapely.geometry import LineString, Point, box

    vorflow = require_vorflow()
    vorflow.set_verbosity(0)  # no progress messages; warnings and errors still show
    x = stream_x(spec)
    blueprint = vorflow.ConceptualMesh()
    blueprint.add_polygon(box(0.0, 0.0, spec.lx, spec.ly), zone_id=1)
    blueprint.add_line(LineString([(x, 0.0), (x, spec.ly)]), "stream", river_size)
    for bname, rc, _ in spec.wells:
        blueprint.add_point(Point(spec.xy(rc)), bname, well_size)
    polys, lines, points = blueprint.generate()
    mesher = vorflow.MeshGenerator(background_lc=background)
    mesher.generate(polys, lines, points)
    return vorflow.VoronoiTessellator(mesher, blueprint).generate()


def disv_gridprops(cells, decimals: int = 6) -> dict:
    """Return DISV ncpl, nvert, vertices and cell2d of Voronoi cells (clockwise, shared vertices).

    cells is a GeoDataFrame of polygons with the generator of each cell in columns x and y.
    The generator is the cell centre, so each connection is perpendicular to its shared face.
    Vertices that agree to `decimals` decimal places [m] are merged.
    """
    from shapely.geometry.polygon import orient

    index, vertices, cell2d = {}, [], []
    for icell, (polygon, xc, yc) in enumerate(zip(cells.geometry, cells["x"], cells["y"])):
        ring = orient(polygon, sign=-1.0).exterior.coords[:-1]  # MF6 needs clockwise vertices
        iverts = []
        for x, y in ring:
            key = (round(x, decimals), round(y, decimals))
            if key not in index:
                index[key] = len(vertices)
                vertices.append([len(vertices), x, y])
            iverts.append(index[key])
        cell2d.append([icell, float(xc), float(yc), len(iverts), *iverts])
    return {"ncpl": len(cell2d), "nvert": len(vertices), "vertices": vertices, "cell2d": cell2d}


def voronoi_stress_cells(gridprops: dict, spec: AquiferSpec) -> dict[str, list]:
    """Place the stresses on Voronoi cells by geometry: west edge, stream line, well points.

    The stream cells are the cells that the stream line crosses over a length > 0, north to
    south; 'stream_lengths' holds the crossed lengths [m].
    """
    from flopy.utils.gridintersect import GridIntersect
    from shapely.geometry import LineString, Point

    mg = flopy.discretization.VertexGrid(
        vertices=gridprops["vertices"], cell2d=gridprops["cell2d"],
        top=np.full(gridprops["ncpl"], spec.top),
        botm=np.full((1, gridprops["ncpl"]), spec.botm),
    )
    gi = GridIntersect(mg)
    x = stream_x(spec)
    crossed = gi.intersect(LineString([(x, 0.0), (x, spec.ly)]), geo_dataframe=False)
    lengths = {
        int(i): float(length) for i, length in zip(crossed.cellids, crossed.lengths) if length > 0.0
    }
    stream = sorted(lengths, key=lambda i: -mg.ycellcenters[i])
    xv = np.array([v[1] for v in gridprops["vertices"]])
    chd = [i for i, c in enumerate(gridprops["cell2d"]) if xv[np.array(c[4:], int)].min() < 1e-6]
    wells = [int(gi.intersects(Point(spec.xy(rc)), dataframe=False).cellids[0])
             for _, rc, _ in spec.wells]
    return {
        "chd": chd, "stream": stream, "stream_lengths": [lengths[i] for i in stream],
        "wells": wells, "cell_y": list(mg.ycellcenters),
    }


def build_voronoi(
    ws: Path,
    exe: Path,
    spec: AquiferSpec | None = None,
    background: float = VORONOI_BACKGROUND,
    well_size: float = VORONOI_WELL_SIZE,
    river_size: float = VORONOI_RIVER_SIZE,
) -> ModelRun:
    """Steady 1-layer DISV Voronoi version of the quickstart model (same physical problem).

    The grid comes from vorflow (vorflow_cells): cells about `background` m across, refined
    to well_size at the wells and to river_size along the stream. Each stream reach is as long
    as the stream line in its cell, so the stream matches the DIS model.
    """
    spec = AquiferSpec() if spec is None else spec
    gridprops = disv_gridprops(vorflow_cells(spec, background, well_size, river_size))
    return build_disv(ws, exe, gridprops, spec, name="voronoi")


def build_disv(ws: Path, exe: Path, gridprops: dict, spec: AquiferSpec, name: str) -> ModelRun:
    """Steady 1-layer DISV quickstart model on any polygon grid (stresses by voronoi_stress_cells).

    gridprops holds DISV ncpl, nvert, vertices and cell2d (disv_gridprops). Each stream reach is
    as long as the stream line in its cell, so the stream matches the DIS model.
    """
    ws = Path(ws)
    cells = voronoi_stress_cells(gridprops, spec)
    ncpl = gridprops["ncpl"]
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = f"{name}.disv"
    flopy.mf6.ModflowGwfdisv(
        gwf, nlay=1, top=spec.top, botm=spec.botm, length_units="meters",
        filename=dis_filename, **gridprops,
    )
    add_npf_ic_oc(gwf, name, k=float(np.mean(k_layer(spec))), icelltype=1, strt=spec.strt)
    chd = [((0, i), spec.chd_head) for i in cells["chd"]]
    wel = [((0, i), rate, bname) for (bname, _, rate), i in zip(spec.wells, cells["wells"])]
    rch = [((0, i), spec.rech) for i in range(ncpl)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    add_sfr(
        gwf, spec, name, [(0, i) for i in cells["stream"]], cells["stream_lengths"],
        [cells["cell_y"][i] for i in cells["stream"]],
    )
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: wel}, boundnames=True, save_flows=True, pname="wel"
    )
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    info = {
        "ncpl": ncpl,
        "well_nodes": {b: i for (b, _, _), i in zip(spec.wells, cells["wells"])},
        "stream_cells": cells["stream"],
        "chd_cells": cells["chd"],
    }
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


def rotated_square_cells(
    spec: AquiferSpec,
    side: float,
    anchor: tuple[float, float],
    angle: float = 45.0,
    decimals: int = 6,
):
    """Tile the tutorial domain with squares rotated by `angle` degrees; return a GeoDataFrame.

    One square is centred on `anchor` [m]. Squares cut by the domain edge are clipped. Each
    cell keeps its square centre in columns x and y when the clipped cell still covers it
    (the connections to its neighbours then stay perpendicular to the shared faces), and the
    centroid of the clipped cell otherwise. Corners and centres are rounded to `decimals`
    decimal places [m], so neighbours share exact corners and a line through a row of centres
    touches the neighbouring squares at their corners only.
    """
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, box

    domain = box(0.0, 0.0, spec.lx, spec.ly)
    theta = np.radians(angle)
    u = side * np.array([np.cos(theta), np.sin(theta)])  # lattice vector along the first side
    v = side * np.array([-np.sin(theta), np.cos(theta)])  # lattice vector along the second side

    def point(a: float, b: float) -> tuple[float, float]:
        """Return the rounded position anchor + a u + b v."""
        x, y = np.asarray(anchor) + a * u + b * v
        return round(float(x), decimals), round(float(y), decimals)

    n = int(np.ceil(np.hypot(spec.lx, spec.ly) / side)) + 1
    polygons, xs, ys = [], [], []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            xc, yc = point(i, j)
            if not (-side <= xc <= spec.lx + side and -side <= yc <= spec.ly + side):
                continue
            corners = [point(i + a, j + b) for a, b in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5))]
            cell = Polygon(corners).intersection(domain)
            if cell.geom_type != "Polygon" or cell.area < 1e-6 * side**2:
                continue
            centre = (xc, yc) if cell.covers(Point(xc, yc)) else cell.centroid.coords[0]
            polygons.append(cell)
            xs.append(float(centre[0]))
            ys.append(float(centre[1]))
    return gpd.GeoDataFrame({"x": xs, "y": ys}, geometry=polygons)


def build_rotated_squares(
    ws: Path, exe: Path, side: float, spec: AquiferSpec | None = None, angle: float = 45.0
) -> ModelRun:
    """Steady DISV quickstart model on squares rotated by `angle`, one centred on the first well.

    The stream, the west edge and the wells are placed on the cells by the rules of
    build_voronoi (voronoi_stress_cells).
    """
    spec = AquiferSpec() if spec is None else spec
    anchor = spec.xy(spec.wells[0][1])
    gridprops = disv_gridprops(rotated_square_cells(spec, side, anchor, angle))
    return build_disv(ws, exe, gridprops, spec, name="rotated")


# ---------------------------------------------------------------- edge of a capture zone


def edge_band_area(F: np.ndarray, area: np.ndarray, low: float = 0.1, high: float = 0.9) -> float:
    """Return the summed area of the cells with low < F < high (the edge band) [area units]."""
    F = np.asarray(F, dtype=float)
    return float(np.asarray(area)[(F > low) & (F < high)].sum())


def transect_profile(
    centres: np.ndarray, values: np.ndarray, x: float, y: np.ndarray
) -> np.ndarray:
    """Return per-cell values interpolated linearly between cell centres along a line x = const."""
    from scipy.interpolate import LinearNDInterpolator

    interpolate = LinearNDInterpolator(np.asarray(centres)[:, :2], np.asarray(values, dtype=float))
    return interpolate(np.full(len(y), x), np.asarray(y, dtype=float))


def band_width_north(
    y: np.ndarray, profile: np.ndarray, low: float = 0.1, high: float = 0.5
) -> tuple[float, float, float]:
    """Return (y at F = high, y at F = low, their distance) north of the peak of a profile.

    profile is F sampled at the increasing positions y. Each crossing is the first one north of
    the largest F, located by linear interpolation between samples.
    """
    y, profile = np.asarray(y, dtype=float), np.asarray(profile, dtype=float)
    start = int(np.nanargmax(profile))
    crossings = []
    for level in (high, low):
        below = np.flatnonzero(profile[start:] < level)
        assert below.size, f"F does not fall below {level} north of the peak"
        k = start + int(below[0])
        f0, f1 = profile[k - 1], profile[k]
        crossings.append(float(y[k - 1] + (f0 - level) / (f0 - f1) * (y[k] - y[k - 1])))
    return crossings[0], crossings[1], crossings[1] - crossings[0]


def build_disu(ws: Path, exe: Path, spec: AquiferSpec | None = None) -> ModelRun:
    """Steady DISU copy of the quickstart model (same cells and connections, with vertices)."""
    from flopy.utils.gridutil import get_disu_kwargs

    spec = AquiferSpec() if spec is None else spec
    name = "disu"
    disu_kwargs = get_disu_kwargs(
        1, spec.nrow, spec.ncol, np.full(spec.ncol, spec.delr), np.full(spec.nrow, spec.delc),
        spec.top, np.array([spec.botm]), return_vertices=True,
    )
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = f"{name}.disu"
    flopy.mf6.ModflowGwfdisu(gwf, length_units="meters", filename=dis_filename, **disu_kwargs)
    add_npf_ic_oc(gwf, name, k=k_layer(spec).ravel(), icelltype=1, strt=spec.strt)
    add_stresses(gwf, spec, lambda rc: (spec.node(rc),), name)
    info = {"well_nodes": _well_nodes(spec)}
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (d) XT3D anisotropy


def xt3d_k_field(
    spec: AquiferSpec, seed: int = 20131, anisotropy: float = 0.05, sigma_lnk: float = 1.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return heterogeneous k, k22 = anisotropy x k and a spatially varying angle1 [degrees]."""
    rng = np.random.default_rng(seed)
    shape = (spec.nrow, spec.ncol)
    k = float(np.mean(k_layer(spec))) * np.exp(rng.normal(0.0, sigma_lnk, size=shape))
    rows, cols = np.indices(shape)
    angle1 = 45.0 * np.sin(2.0 * np.pi * cols / 12.0) * np.cos(2.0 * np.pi * rows / 10.0)
    return k, anisotropy * k, angle1


def build_xt3d(
    ws: Path, exe: Path, spec: AquiferSpec | None = None, seed: int = 20131
) -> ModelRun:
    """Steady quickstart model with XT3D, heterogeneous anisotropic K and rotated axes (cycles)."""
    spec = AquiferSpec() if spec is None else spec
    name = "xt3d"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = add_dis(gwf, spec, name)
    k, k22, angle1 = xt3d_k_field(spec, seed)
    add_npf_ic_oc(
        gwf, name, k=k, icelltype=1, strt=spec.strt, k22=k22, angle1=angle1, xt3doptions=True
    )
    add_stresses(gwf, spec, _dis_cellid(), name)
    info = {"well_nodes": _well_nodes(spec), "k": k, "k22": k22, "angle1": angle1}
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (e) transient seasons


def seasonal_periods(
    n_years: int, steps_per_season: int, season_length: float = 365.25 / 4.0
) -> list[tuple[float, int, float]]:
    """Return TDIS periods: a 1-day steady start, then four seasons per year."""
    return [(1.0, 1, 1.0)] + [(season_length, steps_per_season, 1.0)] * (4 * n_years)


def build_transient(
    ws: Path,
    exe: Path,
    spec: AquiferSpec | None = None,
    n_years: int = 3,
    steps_per_season: int = 3,
    sy: float = 0.2,
    ss: float = 1.0e-5,
    recharge: tuple[float, ...] = SEASON_RECHARGE,
    pumping: tuple[float, ...] = SEASON_PUMPING,
) -> ModelRun:
    """Quickstart model with STO: a steady first period, then seasonal recharge and pumping.

    recharge and pumping are the four seasonal multipliers (wet, wet-to-dry, dry, dry-to-wet).
    Every time step is saved. info holds the per-period multipliers and season names.
    """
    spec = AquiferSpec() if spec is None else spec
    assert len(recharge) == len(pumping) == 4, "four seasonal multipliers each"
    name = "transient"
    periods = seasonal_periods(n_years, steps_per_season)
    rch_factors = (1.0, *(recharge * n_years))
    wel_factors = (1.0, *(pumping * n_years))
    sim, gwf = make_sim(name, ws, exe, periods)
    dis_filename = add_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=k_layer(spec), icelltype=1, strt=spec.strt)
    flopy.mf6.ModflowGwfsto(
        gwf, iconvert=1, ss=ss, sy=sy, steady_state={0: True}, transient={1: True},
        save_flows=True,
    )
    add_stresses(gwf, spec, _dis_cellid(), name, pumping=wel_factors, recharge=rch_factors)
    info = {
        "well_nodes": _well_nodes(spec),
        "periods": periods,
        "season": ("steady", *(SEASONS * n_years)),
        "recharge_factor": rch_factors,
        "pumping_factor": wel_factors,
        "sy": sy,
    }
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (f) drains and mover, MAW

STREAM_DRAINS = (("drain_a", (8, 14), 6.2, 50.0), ("drain_b", (22, 14), 6.0, 50.0))
DRAIN_TO_STREAM = ((0, "FACTOR", 0.8), (1, "FACTOR", 1.0))  # (drain index, type, value)


def build_stream_mover(
    ws: Path,
    exe: Path,
    spec: AquiferSpec | None = None,
    drains: tuple = STREAM_DRAINS,
) -> ModelRun:
    """Quickstart model plus two drains that feed the stream through the water mover (MVR).

    The drains west of the stream hand their outflow (80 % and 100 %) to the first reach;
    the stream carries it south, and the reaches near the well lose part of it back to the
    aquifer. drains: (boundname, (row, col), elevation, conductance). MVR writes its own budget
    file, which a trace with package nodes needs (as the SFR one).
    """
    spec = AquiferSpec() if spec is None else spec
    name = "stream"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = add_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=k_layer(spec), icelltype=1, strt=spec.strt)
    add_stresses(gwf, spec, _dis_cellid(), name, stream_mover=True)
    drn = [((0, *rc), elev, cond, bname) for bname, rc, elev, cond in drains]
    flopy.mf6.ModflowGwfdrn(
        gwf, stress_period_data={0: drn}, boundnames=True, mover=True, save_flows=True, pname="drn"
    )
    movers = [
        ("drn", i, "sfr", 0, kind, value) for i, kind, value in DRAIN_TO_STREAM[: len(drains)]
    ]
    flopy.mf6.ModflowGwfmvr(
        gwf, maxmvr=len(movers), maxpackages=2, packages=[("drn",), ("sfr",)],
        perioddata={0: movers}, budget_filerecord=f"{name}.mvr.bud",
    )
    info = {
        "well_nodes": _well_nodes(spec),
        "drain_nodes": {b: spec.node(rc) for b, rc, _, _ in drains},
        "mvr_budget_file": Path(ws) / f"{name}.mvr.bud",
    }
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


def build_maw(
    ws: Path,
    exe: Path,
    spec: AquiferSpec | None = None,
    maw_cell: tuple[int, int] = (20, 18),
    maw_rate: float = -10.0,
    botm: tuple[float, ...] = LAYER_BOTM,
    layer_k: tuple[float, ...] = LAYER_K,
    k33_ratio: float = 0.01,
) -> ModelRun:
    """Steady 3-layer model with a multi-aquifer well (MAW) screened in every layer.

    The layered model's supply well stays (layer 3); the MAW pumps little, so it takes water
    from layer 1 (higher head) and loses part of it into the deeper layers: the well moves water
    between layers. MAW writes its own budget file (package nodes: package_nodes=("MAW",)).
    """
    spec = AquiferSpec() if spec is None else spec
    name = "maw"
    nlay = len(botm)
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = add_dis(gwf, spec, name, botm=botm)
    k = np.asarray(layer_k)[:, None, None] * k_layer(spec) / float(np.mean(k_layer(spec)))
    add_npf_ic_oc(
        gwf, name, k=k, icelltype=[1] + [0] * (nlay - 1), strt=spec.strt, k33=k33_ratio * k
    )
    add_stresses(gwf, spec, _dis_cellid(), name, wells=False, nlay=nlay)
    supply = LAYERED_WELLS[0]
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [(supply[1], supply[2], supply[0])]}, boundnames=True,
        save_flows=True, pname="wel",
    )
    z = [spec.top, *botm]
    connections = [(0, lay, (lay, *maw_cell), z[lay], z[lay + 1], 0.0, 0.0) for lay in range(nlay)]
    flopy.mf6.ModflowGwfmaw(
        gwf, nmawwells=1, packagedata=[(0, 0.15, z[-1], spec.strt, "THIEM", nlay, "maw_well")],
        connectiondata=connections, perioddata={0: [(0, "RATE", maw_rate)]}, boundnames=True,
        save_flows=True, budget_filerecord=f"{name}.maw.bud", pname="maw",
    )
    shape = (nlay, spec.nrow, spec.ncol)
    info = {
        "maw_cell": maw_cell,
        "maw_rate": maw_rate,
        "maw_nodes": [int(np.ravel_multi_index((lay, *maw_cell), shape)) for lay in range(nlay)],
        "well_nodes": {supply[0]: int(np.ravel_multi_index(supply[1], shape))},
        "maw_budget_file": Path(ws) / f"{name}.maw.bud",
    }
    return run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- (g) random K fields


def random_k_field(
    spec: AquiferSpec, seed: int, sigma_lnk: float = 0.8, correlation_cells: float = 4.0
) -> np.ndarray:
    """Return a (nrow, ncol) log-normal K field: smoothed Gaussian noise, geometric mean spec.k."""
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    z = gaussian_filter(rng.standard_normal((spec.nrow, spec.ncol)), correlation_cells,
                        mode="reflect")
    z = (z - z.mean()) / z.std()
    return float(np.mean(k_layer(spec))) * np.exp(sigma_lnk * z)


def build_realisation(
    ws: Path,
    exe: Path,
    seed: int,
    spec: AquiferSpec | None = None,
    sigma_lnk: float = 0.8,
    correlation_cells: float = 4.0,
) -> ModelRun:
    """Quickstart model with one seeded random K realisation (info['k'] holds the field)."""
    spec = AquiferSpec() if spec is None else spec
    k = random_k_field(spec, seed, sigma_lnk, correlation_cells)
    run = build_quickstart(ws, exe, replace(spec, k=k))
    run.info.update({"k": k, "seed": seed})
    return run


# ---------------------------------------------------------------- multi-model and GWT


def split_model(run: ModelRun, labels: np.ndarray, ws: Path, exe: Path):
    """Split a model with FloPy's Mf6Splitter (exchange flows saved), run it; return the splitter.

    labels holds one model number per cell of a layer ((nrow, ncol) for DIS, (ncpl,) for DISV).
    """
    from flopy.mf6.utils import Mf6Splitter

    sim = flopy.mf6.MFSimulation.load(sim_ws=str(run.ws), verbosity_level=0)
    splitter = Mf6Splitter(sim)
    new = splitter.split_model(np.asarray(labels))
    for exchange in new.exchange_files:
        exchange.save_flows = True
    new.set_sim_path(str(ws))
    new.exe_name = str(exe)
    new.write_simulation(silent=True)
    success, buff = new.run_simulation(silent=True, report=True)
    assert success, "split model run failed:\n" + "\n".join(buff[-20:])
    return splitter


def map_back(splitter, step: gs.FlowStep, values: np.ndarray) -> np.ndarray:
    """Return per-node values of a split-model network step on the original model's nodes."""
    per_model = {}
    for block in step.blocks:
        if block.kind != "model":
            continue
        number = int(block.model.rsplit("_", 1)[-1])
        per_model[number] = np.asarray(values[block.nodes], float).reshape(block.grid_shape)
    return np.asarray(splitter.reconstruct_array(per_model), float).ravel()


GWT_IMS = {
    "complexity": "simple",
    "outer_dvclose": 1.0e-10,
    "outer_maximum": 50,
    "inner_maximum": 1000,
    "inner_dvclose": 1.0e-12,
    "rcloserecord": 1.0e-10,
    "linear_acceleration": "bicgstab",
}


def _bound_counts(package) -> dict[int, int]:
    """Return {period: number of bounds} of a GWF package (list-based stresses, or SFR reaches)."""
    if package.package_type == "sfr":
        return {0: int(package.nreaches.get_data())}
    return {kper: len(rows) for kper, rows in package.stress_period_data.get_data().items()}


def _spc_files(gwf, gwt, tagged: tuple[str, ...]) -> list[tuple[str, str]]:
    """Add one SPC file per tagged package (concentration 1 on every bound and period).

    An SFR package without SFT is a plain source/sink of GWT; its bounds are the reaches.
    """
    fileinput = []
    for pname in tagged:
        counts = _bound_counts(gwf.get_package(pname))
        perioddata = {
            kper: [(i, "CONCENTRATION", 1.0) for i in range(n)] for kper, n in counts.items()
        }
        filename = f"{pname}.spc"
        flopy.mf6.ModflowUtlspc(
            gwt, maxbound=max(counts.values()), perioddata=perioddata,
            filename=filename, pname=f"spc_{pname}",
        )
        fileinput.append((pname, filename))
    return fileinput


def run_gwt_tracer(
    run: ModelRun,
    ws: Path,
    exe: Path,
    porosity: float,
    tagged: tuple[str, ...] = ("rch",),
    strt: float | np.ndarray = 0.0,
    ims_kwargs: dict | None = None,
    perioddata: list[tuple[float, int, float]] | None = None,
) -> Path:
    """Run an MF6 GWT unit-tracer model on a DIS model's saved flows; return the UCN file.

    Upstream advection, no dispersion, FLOW_IMBALANCE_CORRECTION; every bound of the tagged
    packages (pnames) has concentration 1, all other inflow 0; strt tags the initial water.
    ims_kwargs override GWT_IMS. perioddata (perlen, nstp, tsmult) replaces the flow model's
    TDIS; MF6 reuses the single budget step of a steady flow model for every GWT step, so a
    long period runs a steady model to equilibrium.
    """
    ws = Path(ws)
    ws.mkdir(parents=True, exist_ok=True)
    name = "gwt"
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    if perioddata is None:
        perioddata = [tuple(r) for r in run.sim.tdis.perioddata.get_data()]
    flopy.mf6.ModflowTdis(sim, nper=len(perioddata), time_units="days", perioddata=perioddata)
    gwt = flopy.mf6.ModflowGwt(sim, modelname=name)
    flopy.mf6.ModflowIms(sim, **{**GWT_IMS, **(ims_kwargs or {})}, filename=f"{name}.ims")
    dis = run.gwf.dis
    flopy.mf6.ModflowGwtdis(
        gwt, nlay=dis.nlay.get_data(), nrow=dis.nrow.get_data(), ncol=dis.ncol.get_data(),
        delr=dis.delr.get_data(), delc=dis.delc.get_data(), top=dis.top.get_data(),
        botm=dis.botm.get_data(),
    )
    flopy.mf6.ModflowGwtic(gwt, strt=strt)
    flopy.mf6.ModflowGwtmst(gwt, porosity=porosity)
    flopy.mf6.ModflowGwtadv(gwt, scheme="UPSTREAM")
    flopy.mf6.ModflowGwtfmi(
        gwt, flow_imbalance_correction=True,
        packagedata=[("GWFHEAD", str(run.head_file.resolve())),
                     ("GWFBUDGET", str(run.budget_file.resolve()))],
    )
    flopy.mf6.ModflowGwtssm(gwt, fileinput=_spc_files(run.gwf, gwt, tagged) or None)
    flopy.mf6.ModflowGwtoc(
        gwt, concentration_filerecord=f"{name}.ucn", budget_filerecord=f"{name}.cbc",
        saverecord=[("CONCENTRATION", "ALL"), ("BUDGET", "ALL")],
    )
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "GWT run failed:\n" + "\n".join(buff[-20:])
    return ws / f"{name}.ucn"


# ---------------------------------------------------------------- tables


def volume_from_table(result: gs.BackwardResult, group: str):
    """Return a pandas table of the group's inflow by source package: volume [m3/d] and share."""
    import pandas as pd

    volumes = {k: float(v.sum()) for k, v in result.volume_from_by_term[group].items()}
    frame = pd.DataFrame({"volume_from": volumes}).rename_axis("source")
    frame = frame[frame["volume_from"] > 0.0].sort_values("volume_from", ascending=False)
    frame["share"] = frame["volume_from"] / frame["volume_from"].sum()
    return frame


# ---------------------------------------------------------------- maps


def model_grid(grb_file: Path):
    """Return the FloPy modelgrid stored in a binary grid file."""
    return flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False).modelgrid


def node_layer(step: gs.FlowStep) -> np.ndarray:
    """Return the 0-based layer of every node (DIS, DISV; 0 everywhere for DISU)."""
    nlay = step.grid_shape[0] if step.grid_type in ("DIS", "DISV") else 1
    return np.arange(step.n_cells) // (step.n_cells // nlay)


def feature_cells(step: gs.FlowStep, package: str, layer: int | None = None) -> np.ndarray:
    """Return the 0-based cells holding terms of a package (optionally in one layer only)."""
    hits = [package.upper() in p.aliases for p in step.packages]
    if not any(hits):
        return np.array([], dtype=int)
    cells = np.unique(step.term_cell[np.asarray(hits)[step.term_package]])
    if layer is not None:
        cells = cells[node_layer(step)[cells] == layer]
    return cells


def overlay_features(
    ax, grb_file: Path, step: gs.FlowStep, packages: tuple[str, ...] = tuple(FEATURE_STYLES),
    layer: int | None = None, legend: bool = True,
) -> None:
    """Mark the cells of wells, rivers, streams, drains and constant heads at their centres."""
    centres = gs.export.cell_centres(grb_file)
    for package in packages:
        cells = feature_cells(step, package, layer)
        if cells.size:
            xy = centres[cells]
            ax.scatter(xy[:, 0], xy[:, 1], zorder=5, **FEATURE_STYLES[package])
    if legend:
        ax.legend(loc="lower left", fontsize=8, framealpha=0.9)


def plot_cells(
    grb_file: Path,
    step: gs.FlowStep,
    values: np.ndarray,
    ax=None,
    layer: int = 0,
    title: str = "",
    label: str = "",
    overlay: bool = True,
    colorbar: bool = True,
    **kwargs,
):
    """Map one value per cell (any grid type with vertices), with features and a colour bar."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7.0, 5.0))
    collection = gs.export.plot_map(grb_file, step, values, layer=layer, ax=ax, **kwargs)
    if overlay:
        overlay_features(ax, grb_file, step, layer=None)
    if colorbar:
        plt.colorbar(collection, ax=ax, shrink=0.85, label=label)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(title)
    return ax


def add_contours(
    ax,
    grb_file: Path,
    step: gs.FlowStep,
    values: np.ndarray,
    levels: tuple[float, ...],
    layer: int = 0,
    colors: str | tuple = "k",
    linestyles=None,
    fmt: str = "F = %.1f",
):
    """Draw labelled contours of a per-cell array (e.g. F = 0.1 and 0.5 capture thresholds)."""
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(grb_file), layer=layer, ax=ax)
    gridded = gs.export.to_grid(step, values)
    contours = pmv.contour_array(
        np.ma.masked_invalid(gridded), levels=list(levels), colors=colors, linestyles=linestyles,
        linewidths=1.5,
    )
    ax.clabel(contours, fmt=fmt, fontsize=8)
    return contours
