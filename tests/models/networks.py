"""Package-network test models: MAW across layers (model 8), LAK + UZF + MVR (model 9).

Model 8 is model 2's grid and stresses with a lower vertical conductivity and one MAW well
screened in all three layers. With a small pumping rate the well takes water from the upper
layer and injects part of it into the bottom layer, so the well moves water between layers.

Model 9 is a 3-layer grid with two lakes (IDOMAIN = 0 cells in layer 1, connected horizontally
to their layer-1 neighbours and vertically to layer 2): lake A spills through an outlet into
lake B, and lake B through an outlet out of the model. A UZF area west of the lakes receives
infiltration; its eastern cells get more than they can take, and the rejected infiltration is
moved by MVR into lake A. A well in the bottom layer pumps downstream of lake B. One steady
period, then a transient period. Every advanced package and MVR saves its own budget file.
"""

from pathlib import Path

import flopy
import numpy as np

from .common import ModelRun, add_npf_ic_oc, make_sim, run_model

STEADY = ((1.0, 1, 1.0),)
LAYERED = {"nlay": 3, "nrow": 15, "ncol": 25, "delr": 50.0, "top": 10.0,
           "botm": (-10.0, -30.0, -60.0)}
MAW_CELL = (7, 12)
MAW_RATE = -30.0


def _layered_dis(gwf, name: str, idomain=None) -> str:
    """Add the 3-layer DIS of models 2, 8 and 9 and return its file name."""
    g = LAYERED
    dis_filename = f"{name}.dis"
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=g["nlay"], nrow=g["nrow"], ncol=g["ncol"], delr=g["delr"], delc=g["delr"],
        top=g["top"], botm=list(g["botm"]), idomain=idomain, filename=dis_filename,
    )
    return dis_filename


def _edge_chd(gwf, west: float, east: float) -> None:
    """Add constant heads on the west and east edges of every layer."""
    g = LAYERED
    chd = [((k, r, 0), west) for k in range(g["nlay"]) for r in range(g["nrow"])]
    chd += [((k, r, g["ncol"] - 1), east) for k in range(g["nlay"]) for r in range(g["nrow"])]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data={0: chd}, save_flows=True, pname="chd")


def _layer_elevations() -> list[float]:
    """Return the top of layer 1 followed by every layer bottom."""
    return [LAYERED["top"], *LAYERED["botm"]]


def build_maw_dis(ws: Path, exe: Path) -> ModelRun:
    """Model 8: model 2 with k33 = 0.01 k and a MAW well screened in all three layers."""
    name = "m8_maw"
    g = LAYERED
    sim, gwf = make_sim(name, ws, exe, STEADY)
    dis_filename = _layered_dis(gwf, name)
    k = np.array([10.0, 2.0, 15.0])[:, None, None] * np.ones((g["nlay"], g["nrow"], g["ncol"]))
    add_npf_ic_oc(gwf, name, k=k, icelltype=[1, 0, 0], strt=6.0, k33=0.01 * k)
    _edge_chd(gwf, 9.0, 2.0)
    rch = [((0, r, c), 5.0e-4) for r in range(g["nrow"]) for c in range(g["ncol"])]
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [((2, 7, 5), -5.0)]}, save_flows=True, pname="wel"
    )
    z = _layer_elevations()
    connections = [(0, k, (k, *MAW_CELL), z[k], z[k + 1], 0.0, 0.0) for k in range(g["nlay"])]
    flopy.mf6.ModflowGwfmaw(
        gwf,
        nmawwells=1,
        packagedata=[(0, 0.15, z[-1], 6.0, "THIEM", g["nlay"])],
        connectiondata=connections,
        perioddata={0: [(0, "RATE", MAW_RATE)]},
        save_flows=True,
        budget_filerecord=f"{name}.maw.bud",
        pname="maw",
    )
    notes = {"maw_cell": MAW_CELL, "maw_rate": MAW_RATE}
    return run_model(sim, gwf, name, ws, dis_filename, notes)


# ---------------------------------------------------------------- model 9: LAK, UZF, MVR

LAKES = {"lake_a": ((5, 8), (5, 8), 7.5), "lake_b": ((5, 8), (15, 18), 6.0)}  # rows, cols, stage
UZF_ROWS, UZF_COLS = (9, 13), (2, 9)
UZF_VKS = 1.0e-3
UZF_FINF = 6.0e-4
UZF_FINF_EAST = 3.0e-3  # above VKS: rejected infiltration, moved to lake A
UZF_EAST_COLS = (7, 9)
LAK_WELL = ((2, 6, 21), -150.0)
TRANSIENT_PERIODS = ((1.0, 1, 1.0), (50.0, 2, 1.0))


def lake_idomain() -> np.ndarray:
    """Return the (nlay, nrow, ncol) IDOMAIN with the lake cells of layer 1 removed."""
    g = LAYERED
    idomain = np.ones((g["nlay"], g["nrow"], g["ncol"]), dtype=int)
    for (r0, r1), (c0, c1), _ in LAKES.values():
        idomain[0, r0:r1, c0:c1] = 0
    return idomain


def _lake_connections(lake: int, rows: tuple, cols: tuple) -> list[tuple]:
    """Return LAK connections: vertical to layer 2 below, horizontal to layer-1 neighbours."""
    conns = []
    for r in range(*rows):
        for c in range(*cols):
            conns.append([lake, (1, r, c), "VERTICAL", 0.5, 0.0, 0.0, 0.0, 0.0])
    width = LAYERED["delr"]
    for r in range(*rows):
        for c in (cols[0] - 1, cols[1]):
            conns.append([lake, (0, r, c), "HORIZONTAL", 0.5, -10.0, 10.0, width / 2, width])
    for c in range(*cols):
        for r in (rows[0] - 1, rows[1]):
            conns.append([lake, (0, r, c), "HORIZONTAL", 0.5, -10.0, 10.0, width / 2, width])
    return [(c[0], i, *c[1:]) for i, c in enumerate(conns)]


def _add_lakes(gwf, name: str) -> None:
    """Add LAK: lake A spills into lake B, lake B out of the model; rain and evaporation."""
    packagedata, connections = [], []
    for lake, (rows, cols, stage) in enumerate(LAKES.values()):
        conns = _lake_connections(lake, rows, cols)
        packagedata.append((lake, stage, len(conns), list(LAKES)[lake]))
        connections += conns
    outlets = [  # (outlet, lake in, lake out (-1: out of the model), type, invert, width, ...)
        (0, 0, 1, "MANNING", 7.0, 5.0, 0.03, 1.0e-3),
        (1, 1, -1, "MANNING", 5.5, 5.0, 0.03, 1.0e-3),
    ]
    perioddata = [(lake, key, value) for lake in range(2) for key, value in
                  (("RAINFALL", 2.0e-3), ("EVAPORATION", 1.0e-3))]
    flopy.mf6.ModflowGwflak(
        gwf, nlakes=2, noutlets=len(outlets), packagedata=packagedata, connectiondata=connections,
        outlets=outlets, perioddata={0: perioddata}, boundnames=True, mover=True,
        save_flows=True, budget_filerecord=f"{name}.lak.bud", pname="lak",
    )


def _uzf_cells() -> list[tuple[int, int]]:
    """Return the (row, col) of every UZF cell."""
    return [(r, c) for r in range(*UZF_ROWS) for c in range(*UZF_COLS)]


def _add_uzf(gwf, name: str) -> None:
    """Add UZF on a block of layer-1 cells; the eastern cells reject part of their infiltration."""
    packagedata, perioddata = [], []
    for i, (r, c) in enumerate(_uzf_cells()):
        packagedata.append((i, (0, r, c), 1, -1, 0.5, UZF_VKS, 0.05, 0.35, 0.1, 4.0))
        finf = UZF_FINF_EAST if UZF_EAST_COLS[0] <= c < UZF_EAST_COLS[1] else UZF_FINF
        perioddata.append((i, finf, 0.0, 1.0, 0.06, 0.0, 0.0, 0.0))
    flopy.mf6.ModflowGwfuzf(
        gwf, nuzfcells=len(packagedata), packagedata=packagedata, perioddata={0: perioddata},
        mover=True, save_flows=True, budget_filerecord=f"{name}.uzf.bud", pname="uzf",
    )


def _add_mover(gwf, name: str) -> None:
    """Move the rejected infiltration of the eastern UZF cells into lake A."""
    east = [i for i, (_, c) in enumerate(_uzf_cells()) if UZF_EAST_COLS[0] <= c < UZF_EAST_COLS[1]]
    perioddata = [("uzf", i, "lak", 0, "FACTOR", 1.0) for i in east]
    flopy.mf6.ModflowGwfmvr(
        gwf, maxmvr=len(perioddata), maxpackages=2, packages=[("uzf",), ("lak",)],
        perioddata={0: perioddata}, budget_filerecord=f"{name}.mvr.bud",
    )


def _recharge_cells(idomain: np.ndarray) -> list[tuple[int, int, int]]:
    """Return the active layer-1 cells outside the UZF area (they get RCH)."""
    uzf = set(_uzf_cells())
    g = LAYERED
    return [
        (0, r, c) for r in range(g["nrow"]) for c in range(g["ncol"])
        if idomain[0, r, c] > 0 and (r, c) not in uzf
    ]


def build_lak_uzf_dis(ws: Path, exe: Path) -> ModelRun:
    """Model 9: two lakes connected by an outlet, UZF with rejected infiltration moved to a lake."""
    name = "m9_lak_uzf"
    g = LAYERED
    sim, gwf = make_sim(
        name, ws, exe, TRANSIENT_PERIODS, {"complexity": "moderate", "outer_maximum": 500}
    )
    idomain = lake_idomain()
    dis_filename = _layered_dis(gwf, name, idomain)
    k = np.array([10.0, 2.0, 15.0])[:, None, None] * np.ones((g["nlay"], g["nrow"], g["ncol"]))
    add_npf_ic_oc(gwf, name, k=k, icelltype=[1, 0, 0], strt=7.0, k33=0.1 * k)
    flopy.mf6.ModflowGwfsto(
        gwf, iconvert=[1, 0, 0], ss=1.0e-5, sy=0.2, steady_state={0: True}, transient={1: True},
        save_flows=True,
    )
    _edge_chd(gwf, 9.0, 4.0)
    rch = [(cell, 4.0e-4) for cell in _recharge_cells(idomain)]
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: [LAK_WELL]}, save_flows=True, pname="wel"
    )
    _add_lakes(gwf, name)
    _add_uzf(gwf, name)
    _add_mover(gwf, name)
    notes = {"lakes": LAKES, "uzf_cells": _uzf_cells(), "well": LAK_WELL}
    return run_model(sim, gwf, name, ws, dis_filename, notes)
