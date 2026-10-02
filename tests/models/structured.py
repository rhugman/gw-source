"""DIS test models: base steady model, 3-layer weak-sink model, XT3D variant and transient variant.

The base problem has IDOMAIN = 0 cells in the north-east corner, so models 1, 5 and 6 (and the
DISU variants of model 1) exercise the user-to-reduced node mapping.
"""

from pathlib import Path

import flopy
import numpy as np

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


def _dis_cellid(rc: tuple[int, int]) -> tuple[int, int, int]:
    """Map (row, col) of the base problem to a single-layer DIS cellid."""
    return (0, rc[0], rc[1])


def _add_base_dis(gwf, spec: BaseSpec, name: str) -> str:
    """Add the base-problem DIS package and return its file name."""
    dis_filename = f"{name}.dis"
    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=1,
        nrow=spec.nrow,
        ncol=spec.ncol,
        delr=spec.delr,
        delc=spec.delc,
        top=spec.top,
        botm=spec.botm,
        idomain=base_idomain(spec),
        filename=dis_filename,
    )
    return dis_filename


def build_base_dis(ws: Path, exe: Path, spec: BaseSpec | None = None) -> ModelRun:
    """Model 1: 1-layer steady DIS with recharge, a pumping well, a river line and a CHD edge."""
    spec = BaseSpec() if spec is None else spec
    name = "m1_dis"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = _add_base_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt)
    add_base_stresses(gwf, spec, _dis_cellid, [spec.wel_rate], [1.0])
    notes = {"spec": spec, "inactive_cells": spec.inactive_cells}
    return run_model(sim, gwf, name, ws, dis_filename, notes)


def xt3d_k_field(spec: BaseSpec, seed: int = 20131) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return heterogeneous k, k22 and a spatially varying angle1 that make XT3D cross-terms matter."""
    rng = np.random.default_rng(seed)
    shape = (spec.nrow, spec.ncol)
    k = spec.k * np.exp(rng.normal(0.0, 1.0, size=shape))
    k22 = 0.05 * k
    rows, cols = np.indices(shape)
    angle1 = 45.0 * np.sin(2.0 * np.pi * cols / 12.0) * np.cos(2.0 * np.pi * rows / 10.0)
    return k, k22, angle1


def build_xt3d_dis(ws: Path, exe: Path, spec: BaseSpec | None = None) -> ModelRun:
    """Model 5: model 1 with XT3D, heterogeneous anisotropic K and rotated principal axes."""
    spec = BaseSpec() if spec is None else spec
    name = "m5_xt3d"
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = _add_base_dis(gwf, spec, name)
    k, k22, angle1 = xt3d_k_field(spec)
    add_npf_ic_oc(
        gwf, name, k=k, icelltype=1, strt=spec.strt, k22=k22, angle1=angle1, xt3doptions=True
    )
    add_base_stresses(gwf, spec, _dis_cellid, [spec.wel_rate], [1.0])
    notes = {"spec": spec, "inactive_cells": spec.inactive_cells}
    return run_model(sim, gwf, name, ws, dis_filename, notes)


def build_transient_dis(ws: Path, exe: Path, spec: BaseSpec | None = None) -> ModelRun:
    """Model 6: model 1 with STO; a steady first period then transient periods of varying stress."""
    spec = BaseSpec() if spec is None else spec
    name = "m6_transient"
    perioddata = [(1.0, 1, 1.0), (100.0, 4, 1.2), (100.0, 4, 1.2), (100.0, 4, 1.2)]
    wel_rates = [spec.wel_rate, -1200.0, -400.0, -1000.0]
    rch_factors = [1.0, 0.3, 1.5, 0.0]
    sim, gwf = make_sim(name, ws, exe, perioddata)
    dis_filename = _add_base_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt)
    flopy.mf6.ModflowGwfsto(
        gwf,
        iconvert=1,
        ss=1.0e-5,
        sy=0.2,
        steady_state={0: True},
        transient={1: True},
        save_flows=True,
    )
    add_base_stresses(gwf, spec, _dis_cellid, wel_rates, rch_factors)
    notes = {
        "spec": spec,
        "inactive_cells": spec.inactive_cells,
        "wel_rates": wel_rates,
        "rch_factors": rch_factors,
    }
    return run_model(sim, gwf, name, ws, dis_filename, notes)


CONSTANT_FLOW_PERIODS = ((1.0, 1, 1.0), (4.0e5, 30, 1.2))


def build_constant_flow_dis(ws: Path, exe: Path, spec: BaseSpec | None = None) -> ModelRun:
    """Model 10: model 1's steady flows held for a long time (many steps, no storage).

    A short first period, then one long period of geometrically growing steps; every step has
    the same flows, so transient tracking must converge to the steady snapshot fractions.
    """
    spec = BaseSpec() if spec is None else spec
    name = "m10_constant"
    sim, gwf = make_sim(name, ws, exe, CONSTANT_FLOW_PERIODS)
    dis_filename = _add_base_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt)
    n_periods = len(CONSTANT_FLOW_PERIODS)
    add_base_stresses(gwf, spec, _dis_cellid, [spec.wel_rate] * n_periods, [1.0] * n_periods)
    notes = {"spec": spec, "inactive_cells": spec.inactive_cells}
    return run_model(sim, gwf, name, ws, dis_filename, notes)


def build_layered_dis(ws: Path, exe: Path) -> ModelRun:
    """Model 2: 3-layer DIS with regional flow and two wells in the bottom layer only.

    The large well sits in the middle of the grid. The small well extracts much less than the
    regional throughflow of its cell, so it is a genuine weak sink.
    """
    name = "m2_dis3lay"
    nlay, nrow, ncol, delr = 3, 15, 25, 50.0
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = f"{name}.dis"
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delr,
        top=10.0, botm=[-10.0, -30.0, -60.0], filename=dis_filename,
    )
    k = np.array([10.0, 2.0, 15.0])[:, None, None] * np.ones((nlay, nrow, ncol))
    add_npf_ic_oc(gwf, name, k=k, icelltype=[1, 0, 0], strt=6.0, k33=0.1 * k)
    chd = [((lay, row, 0), 9.0) for lay in range(nlay) for row in range(nrow)]
    chd += [((lay, row, ncol - 1), 2.0) for lay in range(nlay) for row in range(nrow)]
    rch = [((0, row, col), 5.0e-4) for row in range(nrow) for col in range(ncol)]
    strong_well, weak_well = (2, 7, 14), (2, 7, 5)
    wel = [(strong_well, -400.0), (weak_well, -5.0)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data={0: wel}, save_flows=True, pname="wel")
    weak_node = int(np.ravel_multi_index(weak_well, (nlay, nrow, ncol)))
    notes = {"strong_well": strong_well, "weak_well": weak_well, "weak_well_node": weak_node}
    return run_model(sim, gwf, name, ws, dis_filename, notes)
