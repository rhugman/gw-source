"""Model 7: the base problem with drains passing water to a stream through the water mover (MVR).

The river line of model 1 is replaced by an SFR stream along the same column, flowing north to
south. Two drains sit upstream of the well; MVR moves 70 % of drain A's outflow and all of drain
B's outflow into the first stream reach. Drains and wells carry boundnames. The upper stream reaches
lose water to the aquifer, so drained water re-enters the aquifer downstream and part of it
reaches the wells (the package-network routing test of Phase 4). SFR and MVR save their own
budget files (used only when tracing with package nodes). The model has two
steady stress periods; the well list changes between them (different order, different wells),
so the budget's bound number (ID2) of a named well differs by stress period.
"""

from pathlib import Path

import flopy

from .common import (
    BaseSpec,
    ModelRun,
    add_npf_ic_oc,
    base_chd_cells,
    base_rch_cells,
    make_sim,
    run_model,
)
from .structured import _add_base_dis, _dis_cellid

MOVER_PERIODS = ((1.0, 1, 1.0), (1.0, 1, 1.0))
DRAINS = (("drn_a", (6, 12), 5.2, 200.0), ("drn_b", (14, 12), 5.3, 150.0))
WELLS = {  # stress period: [(boundname, (row, col), rate)]
    0: [("well_east", (10, 17), -800.0), ("well_west", (4, 6), -150.0)],
    1: [
        ("well_north", (2, 15), -100.0),
        ("well_west", (4, 6), -300.0),
        ("well_east", (10, 17), -500.0),
    ],
}
DRN_TO_SFR = ((0, "FACTOR", 0.7), (1, "FACTOR", 1.0))  # (drain index, mover type, value)


def _sfr_packagedata(spec: BaseSpec) -> tuple[list, list]:
    """Return SFR packagedata and connectiondata for a stream along the river column."""
    rwid, rgrd, rbth, rhk, man, ustrf, ndv = 5.0, 1.0e-3, 1.0, 0.5, 0.03, 1.0, 0
    packagedata, connections = [], []
    for rno in range(spec.nrow):
        cellid = (0, rno, spec.riv_col)
        rtp = spec.riv_rbot + 1.0 - 0.02 * rno
        ncon = int(rno > 0) + int(rno < spec.nrow - 1)
        row = (rno, cellid, spec.delc, rwid, rgrd, rtp, rbth, rhk, man, ncon, ustrf, ndv)
        packagedata.append((*row, f"reach_{rno + 1}"))
        conn = [rno]
        if rno > 0:
            conn.append(rno - 1)
        if rno < spec.nrow - 1:
            conn.append(-(rno + 1))
        connections.append(conn)
    return packagedata, connections


def _add_mover_packages(gwf, spec: BaseSpec) -> None:
    """Add DRN (with mover), SFR (with mover) and MVR moving drain water to the first reach."""
    drn = [((0, *rc), elev, cond, name) for name, rc, elev, cond in DRAINS]
    flopy.mf6.ModflowGwfdrn(
        gwf, stress_period_data={0: drn}, boundnames=True, mover=True, save_flows=True, pname="drn"
    )
    packagedata, connections = _sfr_packagedata(spec)
    flopy.mf6.ModflowGwfsfr(
        gwf,
        nreaches=spec.nrow,
        packagedata=packagedata,
        connectiondata=connections,
        perioddata={0: [(0, "INFLOW", 500.0)]},
        boundnames=True,
        mover=True,
        save_flows=True,
        budget_filerecord=f"{gwf.name}.sfr.bud",
        pname="sfr",
    )
    perioddata = [("drn", i, "sfr", 0, kind, value) for i, kind, value in DRN_TO_SFR]
    flopy.mf6.ModflowGwfmvr(
        gwf,
        maxmvr=len(perioddata),
        maxpackages=2,
        packages=[("drn",), ("sfr",)],
        perioddata={0: perioddata},
        budget_filerecord=f"{gwf.name}.mvr.bud",
    )


def build_mover_dis(ws: Path, exe: Path, spec: BaseSpec | None = None) -> ModelRun:
    """Model 7: DIS base problem with DRN -> MVR -> SFR, named bounds and a changing well list."""
    spec = BaseSpec() if spec is None else spec
    name = "m7_mover"
    sim, gwf = make_sim(
        name, ws, exe, MOVER_PERIODS, {"complexity": "moderate", "outer_maximum": 500}
    )
    dis_filename = _add_base_dis(gwf, spec, name)
    add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt)
    chd = [(_dis_cellid(rc), head) for rc, head in base_chd_cells(spec)]
    rch = [(_dis_cellid(rc), rate) for rc, rate in base_rch_cells(spec, spec.rech)]
    wel = {
        kper: [(_dis_cellid(rc), rate, bname) for bname, rc, rate in wells]
        for kper, wells in WELLS.items()
    }
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data=wel, boundnames=True, save_flows=True, pname="wel"
    )
    _add_mover_packages(gwf, spec)
    notes = {"spec": spec, "wells": WELLS, "drains": DRAINS}
    return run_model(sim, gwf, name, ws, dis_filename, notes)
