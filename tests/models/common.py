"""Shared pieces for the small MF6 test models: run record, base problem spec and package helpers.

Every model writes the binary grid file, a budget file with SAVE_FLOWS on NPF, STO and every
stress package, heads, DATA-SAT (SAVE_SATURATION) and, except on DISU without vertices,
DATA-SPDIS (SAVE_SPECIFIC_DISCHARGE, which MF6 PRT needs to track particles). The base problem
("model 1") is a single unconfined layer with recharge, one pumping well, a river line and a
constant-head west edge. Its stresses are defined on (row, col) so the DIS, DISU and transient
variants share them. The well draws the river down so that some river reaches gain and others
lose water.
"""

from dataclasses import dataclass, field
from pathlib import Path

import flopy
import numpy as np


@dataclass
class ModelRun:
    """Paths and objects a test needs from a built and run model."""

    name: str
    ws: Path
    sim: flopy.mf6.MFSimulation
    gwf: flopy.mf6.ModflowGwf
    grb_file: Path
    budget_file: Path
    head_file: Path
    notes: dict = field(default_factory=dict)


@dataclass
class BaseSpec:
    """Geometry and stresses of the base 1-layer problem (model 1)."""

    nrow: int = 20
    ncol: int = 30
    delr: float = 50.0
    delc: float = 50.0
    top: float = 20.0
    botm: float = -30.0
    k: float = 10.0
    strt: float = 10.0
    rech: float = 1.0e-3
    chd_head: float = 5.0
    riv_col: int = 22
    riv_stage: float = 6.0
    riv_cond: float = 500.0
    riv_rbot: float = 4.0
    wel_cell: tuple[int, int] = (10, 17)
    wel_rate: float = -800.0
    inactive_cells: tuple[tuple[int, int], ...] = (
        (0, 27), (0, 28), (0, 29), (1, 28), (1, 29), (2, 29),
    )


def base_idomain(spec: BaseSpec) -> np.ndarray:
    """Return the (nrow, ncol) IDOMAIN array of the base problem."""
    idomain = np.ones((spec.nrow, spec.ncol), dtype=int)
    for row, col in spec.inactive_cells:
        idomain[row, col] = 0
    return idomain


def base_chd_cells(spec: BaseSpec) -> list[tuple[tuple[int, int], float]]:
    """Return ((row, col), head) for the constant-head west edge."""
    return [((row, 0), spec.chd_head) for row in range(spec.nrow)]


def base_riv_cells(spec: BaseSpec) -> list[tuple[tuple[int, int], float, float, float]]:
    """Return ((row, col), stage, cond, rbot) for the river line along one column."""
    return [
        ((row, spec.riv_col), spec.riv_stage, spec.riv_cond, spec.riv_rbot)
        for row in range(spec.nrow)
    ]


def base_rch_cells(spec: BaseSpec, rech: float) -> list[tuple[tuple[int, int], float]]:
    """Return ((row, col), rate) for recharge on every active cell."""
    idomain = base_idomain(spec)
    return [
        ((row, col), rech)
        for row in range(spec.nrow)
        for col in range(spec.ncol)
        if idomain[row, col] > 0
    ]


def make_sim(
    name: str, ws: Path, exe: Path, perioddata: tuple | list, ims_kwargs: dict | None = None
):
    """Create the simulation, TDIS, IMS (defaults overridable) and an empty GWF model."""
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim, nper=len(perioddata), perioddata=list(perioddata), time_units="days")
    ims = {
        "complexity": "simple",
        "outer_dvclose": 1.0e-9,
        "outer_maximum": 200,
        "inner_maximum": 300,
        "inner_dvclose": 1.0e-10,
        "rcloserecord": 1.0e-8,
        "linear_acceleration": "bicgstab",
    }
    ims.update(ims_kwargs or {})
    flopy.mf6.ModflowIms(sim, **ims)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    return sim, gwf


def add_npf_ic_oc(
    gwf, name: str, k, icelltype, strt, save_specific_discharge: bool = True, **npf_kwargs
) -> None:
    """Add NPF (flows, saturation and specific discharge saved), IC, and OC (heads, budget).

    MF6 cannot compute specific discharge on a DISU grid without vertices, so that model passes
    save_specific_discharge=False.
    """
    flopy.mf6.ModflowGwfnpf(
        gwf,
        icelltype=icelltype,
        k=k,
        save_flows=True,
        save_saturation=True,
        save_specific_discharge=save_specific_discharge,
        **npf_kwargs,
    )
    flopy.mf6.ModflowGwfic(gwf, strt=strt)
    flopy.mf6.ModflowGwfoc(
        gwf,
        budget_filerecord=f"{name}.cbc",
        head_filerecord=f"{name}.hds",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )


def add_base_stresses(
    gwf, spec: BaseSpec, to_cellid, wel_rates: list[float], rch_factors: list[float]
) -> None:
    """Add CHD, RIV, WEL and RCH of the base problem; WEL and RCH vary by stress period."""
    assert len(wel_rates) == len(rch_factors), "one WEL rate and RCH factor per stress period"
    chd = [(to_cellid(rc), head) for rc, head in base_chd_cells(spec)]
    riv = [(to_cellid(rc), stage, cond, rbot) for rc, stage, cond, rbot in base_riv_cells(spec)]
    wel = {kper: [(to_cellid(spec.wel_cell), rate)] for kper, rate in enumerate(wel_rates)}
    rch = {
        kper: [(to_cellid(rc), rate) for rc, rate in base_rch_cells(spec, spec.rech * factor)]
        for kper, factor in enumerate(rch_factors)
    }
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data={0: riv}, save_flows=True, pname="riv")
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel, save_flows=True, pname="wel")
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data=rch, save_flows=True, pname="rch")


def run_model(sim, gwf, name: str, ws: Path, dis_filename: str, notes: dict) -> ModelRun:
    """Write and run the simulation, assert normal termination, and return a ModelRun."""
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, f"MF6 run of {name} failed:\n" + "\n".join(buff[-20:])
    lst_text = (ws / "mfsim.lst").read_text(encoding="utf-8")
    assert "Normal termination of simulation" in lst_text, f"{name}: no normal termination"
    return ModelRun(
        name=name,
        ws=ws,
        sim=sim,
        gwf=gwf,
        grb_file=ws / f"{dis_filename}.grb",
        budget_file=ws / f"{name}.cbc",
        head_file=ws / f"{name}.hds",
        notes=notes,
    )
