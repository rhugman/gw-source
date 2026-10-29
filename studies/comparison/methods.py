"""The capture estimates scored by the comparison study, each run on one built model.

Every method returns a Capture: the capture probability of the recharge falling on each top
cell (the contributing-area field, shape (nrow, ncol)), the well's water by source package and
the closure (water traced back to the well over its pumping).

1. gwsource F (gross accounting): the backward fraction of each cell's outflow that reaches the
   well. Recharge enters its cell and mixes, so the recharge capture probability of a top cell
   is that cell's F. Shares are gwsource's volume_from_by_term; their sum is the well inflow by
   construction (asserted).
2. MF6 PRT, flow-weighted (gwsource.prt's PRT writer and track reader). Particles start from
   every source term (recharge, regional inflow, losing stream reaches) in cells with
   F > F_MIN: under full mixing F = 0 means that no flow path leads to the well, so no particle
   from there can arrive either. Each term's flow is shared equally among its particles:
   - 'centre': one particle at the cell centre, local z 0.5;
   - '27': a 3 x 3 plan lattice at (i + 0.5) / 3 of the cell sides, times local z 1/6, 1/2, 5/6.
   A particle is captured if it terminates in a well cell. Three stopping rules:
   - 'pass': no stop at weak sinks; a particle passing a weak well cell is captured only if it
     ends in another well cell;
   - 'stop': PRP STOP_AT_WEAK_SINK; a particle stops in the first cell with any sink, so it is
     captured if that cell is a well cell;
   - 'well': a stop zone (MIP IZONE, PRP ISTOPZONE) on the well cells only; a particle is
     captured on entering a well cell, and passes the other weak sinks (the stream). This is
     the rule of the advective reference, on grids where the well cells are nearly strong.
   P of a top cell is the captured share of its recharge particles.
3. Adjoint MF6 GWT (Neupauer and Wilson 1999): transport on the reversed flow field. The GWF
   budget file is reversed with FloPy (CellBudgetFile.reverse: every FLOW-JA-FACE and every
   boundary flow negated, so sources and sinks swap; one steady step, so the time reversal is
   the identity). The well, now a source, enters at concentration 1 (SPC); the other new
   sources (gaining stream reaches, the outflow edge) at 0; the old sources (recharge, inflow,
   losing reaches) remove water at the cell concentration. At steady state the concentration
   of a cell is the probability that water entering there reaches the well. FloPy's reverse
   does not negate DATA-SPDIS; GWT uses the specific discharge only in the dispersion tensor,
   which depends on products q_i q_j / |q| and is unchanged by the sign.
   Steady state: one transport step of ADJOINT_DAYS, so the storage term is negligible.
   With no dispersion and UPSTREAM advection the cell equation is gwsource's gross equation, so
   C must equal F (validated, asserted). For R_disp: DSP with alpha_L = 10 alpha_T horizontally
   and vertically, alpha_T for both transverse directions, no molecular diffusion, XT3D (MF6
   default), UPSTREAM advection (why not TVD: see runs.py).
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

import flopy
import numpy as np

import gwsource as gs
import herebedragons as hbd
from gwsource import prt as gprt

WELL = "well"
F_MIN = 1e-12
CLOSURE_TOL = 1e-6  # the cell budgets close to the flow solve's residual (RCLOSE 1e-7 m3/d)
SOURCES = {"RCH": "recharge", "SFR": "stream", "INFLOW": "inflow"}
PRT_LAYOUTS = ("centre", "27")
STOP_RULES = ("pass", "stop", "well")
ADJOINT_DAYS = 1.0e14
ADJOINT_IMS = {  # ILUT: the XT3D dispersion matrix is not an M-matrix; ILU(0) stalls at 1M cells
    **hbd.GWT_IMS, "outer_dvclose": 1e-12, "inner_dvclose": 1e-13, "rcloserecord": 1e-10,
    "outer_maximum": 50, "inner_maximum": 3000, "preconditioner_levels": 3,
    "preconditioner_drop_tolerance": 1e-4, "scaling_method": "diagonal",
}


@dataclass
class Capture:
    """One method's answer on one grid: top-cell recharge capture, shares and closure."""

    method: str
    p_top: np.ndarray  # (nrow, ncol)
    shares: dict  # source label: share of the well's pumping
    closure: float  # water traced to the well / pumping
    info: dict


def source_label(package: str) -> str:
    """Return the source label of a package name ('other' if not one of SOURCES)."""
    return SOURCES.get(package.split("-")[0].upper(), "other")


def label_shares(volumes: dict, pumping: float) -> dict:
    """Return {source label: volume / pumping} with every label of SOURCES present."""
    out = {label: 0.0 for label in SOURCES.values()}
    for package, volume in volumes.items():
        label = source_label(package)
        out[label] = out.get(label, 0.0) + float(volume) / pumping
    return out


def top_layer(values: np.ndarray, grid) -> np.ndarray:
    """Return the top-layer part of a per-node array as (nrow, ncol)."""
    return np.asarray(values[: grid.ncpl], dtype=float).reshape(grid.nrow, grid.ncol)


# ---------------------------------------------------------------- gwsource


def trace(ws: Path) -> tuple[gs.FlowStep, gs.BackwardResult]:
    """Read the steady step and trace it backward to the well (gross accounting)."""
    step = gs.read_step(ws)
    result = gs.backward(step, {WELL: gs.select(step, package="WELL")})
    return step, result


def gwsource_capture(result: gs.BackwardResult, grid, pumping: float) -> Capture:
    """Return gwsource F as a Capture; assert that the shares close on the well inflow."""
    inflow = result.destination_inflow[WELL]
    assert abs(inflow - pumping) < 1e-6 * pumping, f"well inflow {inflow} is not {pumping}"
    volumes = {p: v.sum() for p, v in result.volume_from_by_term[WELL].items()}
    closure = sum(volumes.values()) / pumping
    assert abs(closure - 1.0) < CLOSURE_TOL, f"gwsource shares do not close: {closure}"
    return Capture("F", top_layer(result.fraction_through[WELL], grid),
                   label_shares(volumes, pumping), closure, {})


# ---------------------------------------------------------------- MF6 PRT


def lattice(layout: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the plan fractions (n, 2) and local z (m,) of a release layout."""
    if layout == "centre":
        return np.array([[0.5, 0.5]]), np.array([0.5])
    assert layout == "27", f"layout must be one of {PRT_LAYOUTS}"
    f = (np.arange(3) + 0.5) / 3.0
    fx, fy = np.meshgrid(f, f)
    return np.column_stack([fx.ravel(), fy.ravel()]), f


def release_points(step: gs.FlowStep, contributing: np.ndarray, grid, layout: str,
                   ly: float) -> gprt.ReleasePoints:
    """Return flow-weighted release points of every source term in the contributing cells."""
    plan, local_z = lattice(layout)
    flow = np.maximum(step.term_flow, 0.0)
    terms = np.flatnonzero((flow > 0.0) & contributing[step.term_cell])
    cells = step.term_cell[terms]
    row, col = np.divmod(cells % grid.ncpl, grid.ncol)
    n_plan, n_z = len(plan), len(local_z)
    n = n_plan * n_z
    x = (col[:, None] + np.tile(plan[:, 0], n_z)[None, :]) * grid.dx
    y = ly - (row[:, None] + np.tile(plan[:, 1], n_z)[None, :]) * grid.dx
    z = np.repeat(local_z, n_plan)
    names = np.array([step.packages[p].name for p in step.term_package[terms]], dtype=object)
    return gprt.ReleasePoints(
        cell=np.repeat(cells, n), x=x.ravel(), y=y.ravel(), z=np.tile(z, len(terms)),
        weight=np.repeat(flow[terms] / n, n), package=np.repeat(names, n),
    )


def write_stop_zone(sim, well_nodes: np.ndarray, n_cells: int) -> None:
    """Put the well cells in stop zone 1 (MIP IZONE, PRP ISTOPZONE) and rewrite the PRT input."""
    prt = sim.get_model("prt")
    zone = np.zeros(n_cells, dtype=int)
    zone[well_nodes] = 1
    prt.mip.izone.set_data(zone.reshape(prt.dis.nlay.get_data(), prt.dis.nrow.get_data(),
                                        prt.dis.ncol.get_data()))
    prt.prp.istopzone.set_data(1)
    sim.write_simulation(silent=True)


def prt_capture(ws: Path, step: gs.FlowStep, result: gs.BackwardResult, grid, design,
                well_nodes: np.ndarray, layout: str, rule: str, exe: Path) -> Capture:
    """Run MF6 PRT with one release layout and stopping rule; return the Capture."""
    assert rule in STOP_RULES, f"rule must be one of {STOP_RULES}"
    contributing = result.fraction_through[WELL] > F_MIN
    release = release_points(step, contributing, grid, layout, design.ly)
    prt_grid = gprt.load_prt_grid(ws, "gwf", "DIS")
    config = gs.PrtConfig(porosity=design.porosity)
    prt_ws = ws / f"prt_{layout}_{rule}"
    sim = gprt.write_prt(prt_ws, ws, prt_grid, release, config, exe, "gwf",
                         stop_at_weak_sink=rule == "stop", track_release=False,
                         track_exit=False, clear_ws=True)
    if rule == "well":
        write_stop_zone(sim, well_nodes, step.n_cells)
    ends = gprt.endpoints(gprt.read_tracks(gprt.run_prt(sim)), release.n)
    gprt.assert_terminated(ends, release)
    captured = np.isin(ends["cell"], well_nodes)
    weight = np.where(captured, release.weight, 0.0)
    shutil.rmtree(prt_ws)
    return Capture(
        f"PRT {layout} {rule}",
        recharge_share(release, weight, grid),
        label_shares(package_sums(release, weight), design.well_rate),
        float(weight.sum() / design.well_rate),
        {"n_particles": int(release.n)},
    )


def package_sums(release: gprt.ReleasePoints, weight: np.ndarray) -> dict:
    """Return the captured weight summed by release package."""
    return {str(p): float(weight[release.package == p].sum()) for p in np.unique(release.package)}


def recharge_share(release: gprt.ReleasePoints, captured_weight: np.ndarray, grid) -> np.ndarray:
    """Return, per top cell, the captured share of its recharge particles (0 where none)."""
    rch = np.array([source_label(p) == "recharge" for p in release.package])
    cells = release.cell[rch]
    assert (cells < grid.ncpl).all(), "recharge particles outside the top layer"
    total = np.bincount(cells, weights=release.weight[rch], minlength=grid.ncpl)
    got = np.bincount(cells, weights=captured_weight[rch], minlength=grid.ncpl)
    share = np.divide(got, total, out=np.zeros(grid.ncpl), where=total > 0)
    return share.reshape(grid.nrow, grid.ncol)


# ---------------------------------------------------------------- adjoint MF6 GWT


def reverse_budget(budget_file: Path, reversed_file: Path) -> None:
    """Write the reversed budget (FloPy) and assert what changed and what did not."""
    cbc = flopy.utils.CellBudgetFile(str(budget_file))
    assert len(cbc.get_kstpkper()) == 1, "the adjoint needs one steady flow step"
    cbc.reverse(str(reversed_file))
    rev = flopy.utils.CellBudgetFile(str(reversed_file))
    n = len(cbc)
    assert len(rev) == n, "record count changed"
    for i in range(n):  # one step: the reversed file holds the records in reverse order
        head, head_rev = cbc.recordarray[i], rev.recordarray[n - 1 - i]
        assert head["text"] == head_rev["text"], "record order changed"
        a, b = cbc.get_data(idx=i)[0], rev.get_data(idx=n - 1 - i)[0]
        name = head["text"].decode().strip()
        if name == "FLOW-JA-FACE":
            assert np.array_equal(np.ravel(a), -np.ravel(b)), "FLOW-JA-FACE not negated"
        elif name == "DATA-SAT":
            assert np.array_equal(a["sat"], b["sat"]), "saturation changed"
        else:
            assert head["paknam2"] == head_rev["paknam2"], "package order changed"
            assert np.array_equal(a["node"], b["node"]), f"{name} nodes changed"
            assert np.array_equal(a["q"], -b["q"]), f"{name} not negated"
    cbc.close()
    rev.close()


def run_adjoint(run: hbd.ModelRun, reversed_file: Path, ws: Path, exe: Path,
                alpha_t: float = 0.0) -> np.ndarray:
    """Run steady adjoint GWT on the reversed flows; return the per-node concentration."""
    ws.mkdir(parents=True, exist_ok=True)
    name = "adj"
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim, nper=1, time_units="days", perioddata=[(ADJOINT_DAYS, 1, 1.0)])
    gwt = flopy.mf6.ModflowGwt(sim, modelname=name)
    flopy.mf6.ModflowIms(sim, **ADJOINT_IMS, filename=f"{name}.ims")
    dis = run.gwf.dis
    flopy.mf6.ModflowGwtdis(
        gwt, nlay=dis.nlay.get_data(), nrow=dis.nrow.get_data(), ncol=dis.ncol.get_data(),
        delr=dis.delr.get_data(), delc=dis.delc.get_data(), top=dis.top.get_data(),
        botm=dis.botm.get_data(),
    )
    flopy.mf6.ModflowGwtic(gwt, strt=0.0)
    flopy.mf6.ModflowGwtmst(gwt, porosity=run.spec.porosity)
    flopy.mf6.ModflowGwtadv(gwt, scheme="UPSTREAM")
    if alpha_t > 0.0:
        flopy.mf6.ModflowGwtdsp(gwt, alh=10.0 * alpha_t, alv=10.0 * alpha_t, ath1=alpha_t,
                                ath2=alpha_t, atv=alpha_t, diffc=0.0)
    flopy.mf6.ModflowGwtfmi(
        gwt, flow_imbalance_correction=True,
        packagedata=[("GWFHEAD", str(run.head_file.resolve())),
                     ("GWFBUDGET", str(Path(reversed_file).resolve()))],
    )
    flopy.mf6.ModflowGwtssm(gwt, fileinput=hbd._spc_files(run.gwf, gwt, (WELL,)))
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord=f"{name}.ucn",
                           saverecord=[("CONCENTRATION", "LAST")])
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "adjoint GWT run failed:\n" + "\n".join(buff[-20:])
    conc = flopy.utils.HeadFile(str(ws / f"{name}.ucn"), text="CONCENTRATION").get_data()
    return np.asarray(conc, dtype=float).ravel()


def adjoint_capture(conc: np.ndarray, step: gs.FlowStep, grid, pumping: float,
                    method: str) -> Capture:
    """Return an adjoint concentration field as a Capture (shares: sum of C q over sources)."""
    flow = np.maximum(step.term_flow, 0.0)
    carried = conc[step.term_cell] * flow
    volumes = {}
    for p, package in enumerate(step.packages):
        mask = step.term_package == p
        if flow[mask].sum() > 0.0:
            volumes[package.name] = float(carried[mask].sum())
    closure = sum(volumes.values()) / pumping
    return Capture(method, top_layer(conc, grid), label_shares(volumes, pumping), closure,
                   {"c_min": float(conc.min()), "c_max": float(conc.max())})


def validate_adjoint(run: hbd.ModelRun, result: gs.BackwardResult, reversed_file: Path,
                     ws: Path, exe: Path, atol: float) -> float:
    """Assert that the no-dispersion upstream adjoint equals gwsource F; return max |C - F|."""
    conc = run_adjoint(run, reversed_file, ws, exe)
    error = float(np.abs(conc - result.fraction_through[WELL]).max())
    assert error < atol, f"adjoint GWT differs from gwsource F by {error:.2e} (> {atol:.0e})"
    return error

