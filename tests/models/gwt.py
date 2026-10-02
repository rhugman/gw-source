"""MF6 GWT unit-concentration models that read a test model's flows through FMI (Phase 4B check).

The GWT model is a separate simulation with the flow model's DIS and TDIS. FMI reads the GWF
head and budget files (so the flows are exactly those gwsource reads). ADV is UPSTREAM, there
is no DSP, MST has the given porosity and no sorption or decay, and FMI applies
FLOW_IMBALANCE_CORRECTION (the residual of each cell acts as a sink or source at the cell
concentration, as gwsource.tracking does by default). SSM gives every bound of the tagged
packages concentration 1 through SPC files; inflows of every other package have concentration
0. IC sets the initial concentration (1 tags the water present at the start).

With sft_inflow set (model 7), FMI also reads the SFR and MVR budget files and the GWT model
gets SFT (stream transport; EXT-INFLOW concentration sft_inflow) and MVT (mover transport), so
tagged water is routed through the stream reaches and the water mover as in a package network.
"""

from pathlib import Path

import flopy
import numpy as np

GWT_IMS = {
    "complexity": "simple",
    "outer_dvclose": 1.0e-13,
    "outer_maximum": 50,
    "inner_maximum": 1000,
    "inner_dvclose": 1.0e-14,
    "rcloserecord": 1.0e-12,
    "linear_acceleration": "bicgstab",
}


def _copy_tdis(gwf_sim, sim) -> None:
    """Add a TDIS with the flow simulation's periods."""
    tdis = gwf_sim.tdis
    flopy.mf6.ModflowTdis(
        sim,
        nper=tdis.nper.get_data(),
        perioddata=[tuple(r) for r in tdis.perioddata.get_data()],
        time_units=tdis.time_units.get_data(),
    )


def _copy_dis(gwf, gwt) -> None:
    """Add a DIS with the flow model's grid (DIS grids only)."""
    dis = gwf.dis
    flopy.mf6.ModflowGwtdis(
        gwt,
        nlay=dis.nlay.get_data(),
        nrow=dis.nrow.get_data(),
        ncol=dis.ncol.get_data(),
        delr=dis.delr.get_data(),
        delc=dis.delc.get_data(),
        top=dis.top.get_data(),
        botm=dis.botm.get_data(),
        idomain=dis.idomain.get_data(),
    )


def _spc_files(gwf, gwt, tagged: tuple[str, ...]) -> list[tuple]:
    """Add one SPC file per tagged package (concentration 1 on every bound, every period)."""
    fileinput = []
    for pname in tagged:
        package = gwf.get_package(pname)
        spd = package.stress_period_data.get_data()
        perioddata = {
            kper: [(i, "CONCENTRATION", 1.0) for i in range(len(rows))]
            for kper, rows in spd.items()
        }
        filename = f"{pname}.spc"
        flopy.mf6.ModflowUtlspc(
            gwt,
            maxbound=max(len(r) for r in spd.values()),
            perioddata=perioddata,
            filename=filename,
            pname=f"spc_{pname}",
        )
        fileinput.append((pname, filename))
    return fileinput


def _budget_file(package) -> str:
    """Return the BUDGET FILEOUT name of a GWF package (SFR, MVR)."""
    return package.budget_filerecord.get_data()[0][0]


def _add_stream_transport(run, gwt, sft_inflow: float) -> list[tuple[str, str]]:
    """Add SFT and MVT; return the FMI entries of the SFR and MVR budget files."""
    sfr = run.gwf.get_package("sfr")
    nreaches = sfr.nreaches.get_data()
    flopy.mf6.ModflowGwtsft(
        gwt,
        flow_package_name="sfr",
        packagedata=[(i, 0.0) for i in range(nreaches)],
        reachperioddata={0: [(0, "INFLOW", sft_inflow)]},
        concentration_filerecord="gwt.sft.ucn",
        pname="sft",
    )
    flopy.mf6.ModflowGwtmvt(gwt)
    mvr = run.gwf.get_package("mvr")
    return [
        ("GWFMOVER", str((Path(run.ws) / _budget_file(mvr)).resolve())),
        ("sfr", str((Path(run.ws) / _budget_file(sfr)).resolve())),
    ]


def build_gwt_fmi(
    run,
    ws: Path,
    exe: Path,
    porosity: float,
    tagged: tuple[str, ...] = (),
    strt: float | np.ndarray = 0.0,
    flow_imbalance_correction: bool = True,
    sft_inflow: float | None = None,
) -> Path:
    """Build and run a GWT simulation on a DIS test model's saved flows; return the UCN file.

    With sft_inflow, the stream reach concentrations are in 'gwt.sft.ucn' next to it.
    """
    ws = Path(ws)
    name = "gwt"
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=str(ws), exe_name=str(exe))
    _copy_tdis(run.sim, sim)
    gwt = flopy.mf6.ModflowGwt(sim, modelname=name)
    flopy.mf6.ModflowIms(sim, **GWT_IMS, filename=f"{name}.ims")
    _copy_dis(run.gwf, gwt)
    flopy.mf6.ModflowGwtic(gwt, strt=strt)
    flopy.mf6.ModflowGwtmst(gwt, porosity=porosity)
    flopy.mf6.ModflowGwtadv(gwt, scheme="UPSTREAM")
    packagedata = [
        ("GWFHEAD", str(Path(run.head_file).resolve())),
        ("GWFBUDGET", str(Path(run.budget_file).resolve())),
    ]
    if sft_inflow is not None:
        packagedata += _add_stream_transport(run, gwt, sft_inflow)
    flopy.mf6.ModflowGwtfmi(
        gwt, flow_imbalance_correction=flow_imbalance_correction, packagedata=packagedata
    )
    fileinput = _spc_files(run.gwf, gwt, tagged)
    flopy.mf6.ModflowGwtssm(gwt, fileinput=fileinput or None)
    flopy.mf6.ModflowGwtoc(
        gwt,
        concentration_filerecord=f"{name}.ucn",
        budget_filerecord=f"{name}.cbc",
        saverecord=[("CONCENTRATION", "ALL"), ("BUDGET", "ALL")],
    )
    sim.write_simulation(silent=True)
    success, buff = sim.run_simulation(silent=True, report=True)
    assert success, "GWT run failed:\n" + "\n".join(buff[-20:])
    return ws / f"{name}.ucn"
