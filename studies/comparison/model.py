"""The synthetic 3D aquifer of the comparison study: one well, a gaining SFR stream, recharge,
a regional inflow edge and an outflow edge, on DIS grids of any square cell size and layer
count.

Plan (x east, y north, metres): LX x LY, flow from west to east. A confined aquifer of fixed
thickness (TOP to BOT), isotropic horizontal K and vertical anisotropy K / K33. Every layer is
confined (ICELLTYPE 0), so the flow problem is linear and the saturated thickness equals the
cell thickness on every grid.

- Regional inflow: a specified flux (WEL package 'inflow') into the west column, U m2/d per
  metre of edge, spread over the layers by thickness. A specified flux keeps the regional flow
  the same on every grid.
- Recharge: RCH on the top layer.
- Regional outflow: constant head (CHD package 'outflow') in every layer of the east column.
- Stream: up-gradient (west) of the well, 100 m ('near') or 500 m ('far') from it. SFR
  reaches run down one column (north to south) in the top layer, with a fixed width and bed
  conductivity, so the conductance per metre of stream is the same on every grid. Every reach
  is SIMPLE with a specified stage (falling by the stream slope), which keeps the flow problem
  linear; the upstream inflow is large enough that no reach runs dry. The stream gains water
  overall. Regional water reaches the well by passing beneath it, and when the stream is near
  the well its reaches beside the well lose water that the well captures. gwsource reads the
  reach leakage as one external term per cell (sources and sinks), not as package nodes.
- Well: WEL package 'well' at one point, screened over the full thickness or its lower half,
  the rate shared among the screened layers by thickness. On one layer the lower-half screen
  cannot be resolved and the well takes the whole layer.

The well, stream line and the regional edge sit at points that are inside cells for every cell
size from 100 m to 6.25 m (x = k 6.25 + 3.125), so no grid puts a feature on a cell edge.
"""

from dataclasses import dataclass
from pathlib import Path

import flopy
import numpy as np

import herebedragons as hbd

SCREENS = ("full", "lower")
FLOW_IMS = {"complexity": "simple", "outer_maximum": 50, "outer_dvclose": 1e-9,
            "inner_dvclose": 1e-10, "rcloserecord": 1e-7, "inner_maximum": 2000}
STREAMS = ("near", "far")


@dataclass(frozen=True)
class Design:
    """Aquifer, stresses and feature positions (lengths in m, time in d)."""

    lx: float = 2000.0
    ly: float = 1200.0
    top: float = 50.0
    bot: float = 0.0
    k: float = 10.0
    anisotropy: float = 10.0  # K / K33
    rech: float = 5.0e-4
    inflow_u: float = 0.5  # m2/d per m of west edge
    well_x: float = 1203.125
    well_y: float = 603.125
    well_rate: float = 500.0  # m3/d, pumped
    stream_x: dict = None  # set in __post_init__
    stream_width: float = 5.0
    stream_bed_k: float = 1.0
    stream_bed_thick: float = 0.2  # thin: the bed stays inside a 1.56 m top layer
    stream_stage: float = 49.5  # at the north end
    stream_depth: float = 0.5
    stream_slope: float = 1.0e-4
    stream_inflow: float = 5000.0  # large, so no reach runs dry
    outflow_head: float = 48.0
    porosity: float = 0.3

    def __post_init__(self) -> None:
        """Set the default stream positions (frozen dataclass: through object.__setattr__)."""
        if self.stream_x is None:
            object.__setattr__(self, "stream_x", {"near": 1103.125, "far": 703.125})

    @property
    def thickness(self) -> float:
        """Aquifer thickness [m]."""
        return self.top - self.bot


@dataclass(frozen=True)
class Case:
    """One model: cell size, layer count, well screen and stream position."""

    dx: float
    nlay: int
    screen: str
    stream: str

    def __post_init__(self) -> None:
        """Validate the options."""
        assert self.screen in SCREENS, f"screen must be one of {SCREENS}"
        assert self.stream in STREAMS, f"stream must be one of {STREAMS}"

    @property
    def physical(self) -> str:
        """Name of the physical case (screen and stream; the grid does not change it)."""
        return f"{self.screen}_{self.stream}"

    @property
    def label(self) -> str:
        """Unique, file-safe name of the model."""
        return f"{self.physical}_dx{self.dx:g}_l{self.nlay}".replace(".", "p")


@dataclass
class Grid:
    """Shape and layer bottoms of a DIS grid of the design."""

    dx: float
    nlay: int
    nrow: int
    ncol: int
    botm: np.ndarray

    @property
    def ncpl(self) -> int:
        """Cells per layer."""
        return self.nrow * self.ncol

    def rc(self, x: float, y: float, ly: float) -> tuple[int, int]:
        """Return the (row, col) holding the point (x, y); row 0 is the north edge."""
        return int((ly - y) // self.dx), int(x // self.dx)

    def node(self, layer: int, row: int, col: int) -> int:
        """Return the 0-based node of (layer, row, col)."""
        return (layer * self.nrow + row) * self.ncol + col


def make_grid(design: Design, dx: float, nlay: int) -> Grid:
    """Return the DIS grid of a cell size and layer count (cells must tile the plan exactly)."""
    nrow, ncol = round(design.ly / dx), round(design.lx / dx)
    assert abs(nrow * dx - design.ly) < 1e-9 and abs(ncol * dx - design.lx) < 1e-9, (
        f"cell size {dx} does not divide the {design.lx} x {design.ly} m plan"
    )
    botm = np.linspace(design.top, design.bot, nlay + 1)[1:]
    return Grid(dx, nlay, nrow, ncol, botm)


def screened_layers(grid: Grid, design: Design, screen: str) -> np.ndarray:
    """Return the layers the well screens: all, or those whose centre is in the lower half."""
    if screen == "full" or grid.nlay == 1:
        return np.arange(grid.nlay)
    z = np.r_[design.top, grid.botm]
    centre = 0.5 * (z[:-1] + z[1:])
    return np.flatnonzero(centre < design.bot + 0.5 * design.thickness)


def layer_thickness(grid: Grid, design: Design) -> np.ndarray:
    """Return the thickness of each layer [m]."""
    return -np.diff(np.r_[design.top, grid.botm])


def well_records(grid: Grid, design: Design, screen: str) -> list:
    """Return the WEL records of the well: rate shared among the screened layers by thickness."""
    row, col = grid.rc(design.well_x, design.well_y, design.ly)
    layers = screened_layers(grid, design, screen)
    b = layer_thickness(grid, design)[layers]
    return [((int(lay), row, col), -design.well_rate * bi / b.sum()) for lay, bi in zip(layers, b)]


def inflow_records(grid: Grid, design: Design) -> list:
    """Return the WEL records of the regional inflow into the west column (by thickness)."""
    b = layer_thickness(grid, design)
    return [((lay, row, 0), design.inflow_u * grid.dx * b[lay] / design.thickness)
            for lay in range(grid.nlay) for row in range(grid.nrow)]


def reach_stage(rno: int, grid: Grid, design: Design) -> float:
    """Return the specified stage of a reach: falling north to south by the stream slope."""
    return design.stream_stage - design.stream_slope * (rno + 0.5) * grid.dx


def sfr_perioddata(grid: Grid, design: Design) -> list:
    """Return SFR period data: upstream inflow, and every reach SIMPLE at its specified stage."""
    rows = [(0, "INFLOW", design.stream_inflow)]
    for rno in range(grid.nrow):
        rows += [(rno, "STATUS", "SIMPLE"), (rno, "STAGE", reach_stage(rno, grid, design))]
    return rows


def sfr_reaches(grid: Grid, design: Design, stream: str) -> tuple[list, list]:
    """Return SFR packagedata and connectiondata for the stream column (north to south)."""
    col = int(design.stream_x[stream] // grid.dx)
    packagedata, connections = [], []
    for rno in range(grid.nrow):
        ncon = int(rno > 0) + int(rno < grid.nrow - 1)
        packagedata.append((
            rno, (0, rno, col), grid.dx, design.stream_width, design.stream_slope,
            reach_stage(rno, grid, design) - design.stream_depth, design.stream_bed_thick,
            design.stream_bed_k, 0.03, ncon, 1.0, 0,
        ))
        conn = [rno] + ([rno - 1] if rno > 0 else []) + ([-(rno + 1)] if rno < grid.nrow - 1 else [])
        connections.append(conn)
    return packagedata, connections


def build_model(ws: Path, exe: Path, design: Design, case: Case) -> hbd.ModelRun:
    """Write and run the steady flow model of one case; return the tutorial ModelRun."""
    grid = make_grid(design, case.dx, case.nlay)
    name = "gwf"
    sim, gwf = hbd.make_sim(name, ws, exe, hbd.STEADY, FLOW_IMS)
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=grid.nlay, nrow=grid.nrow, ncol=grid.ncol, delr=grid.dx, delc=grid.dx,
        top=design.top, botm=grid.botm, length_units="meters", filename=f"{name}.dis",
    )
    hbd.add_npf_ic_oc(gwf, name, k=design.k, icelltype=0, strt=design.stream_stage,
                      k33=design.k / design.anisotropy)
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data={0: inflow_records(grid, design)},
                            save_flows=True, pname="inflow", filename=f"{name}.inflow.wel")
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data={0: well_records(grid, design, case.screen)},
                            save_flows=True, pname="well", filename=f"{name}.well.wel")
    flopy.mf6.ModflowGwfrcha(gwf, recharge=design.rech, save_flows=True, pname="rch")
    outflow = [((lay, row, grid.ncol - 1), design.outflow_head)
               for lay in range(grid.nlay) for row in range(grid.nrow)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: outflow}, save_flows=True,
                            pname="outflow")
    packagedata, connections = sfr_reaches(grid, design, case.stream)
    flopy.mf6.ModflowGwfsfr(
        gwf, nreaches=grid.nrow, packagedata=packagedata, connectiondata=connections,
        perioddata={0: sfr_perioddata(grid, design)}, save_flows=True, pname="sfr",
    )
    info = {"case": case, "grid": grid, "well_nodes": well_nodes(grid, design, case.screen)}
    return hbd.run_model(sim, gwf, name, ws, f"{name}.dis", design, info)


def well_nodes(grid: Grid, design: Design, screen: str) -> np.ndarray:
    """Return the 0-based nodes of the well cells."""
    return np.array([grid.node(*cellid) for cellid, _ in well_records(grid, design, screen)])

