"""Minimal reproducer: MODFLOW 6 PRT aborts on a cell wet by a saturation film.

Model (one layer, one row, five columns, 100 m x 100 m cells, 10 m thick, NEWTON, convertible):

    col 0          col 1     col 2        col 3     col 4
    DRN at bottom            CHD          -         DRN at bottom
    C = 1e12 m2/d            bottom + 5 m           C = 1e2 m2/d

Recharge 1e-3 m/d on all cells. The very conductive drain in column 0 holds the head a hair
above the cell bottom (1.1e-10 m); with NEWTON the saved saturation (DATA-SAT, the NEWTON
quadratic saturation) is then a film of 6.2e-17. Column 4 has a normal drain (saturation 0.1).
Water flows from the CHD towards both drains.

Cases (each is a separate PRT simulation with a single particle released at the cell centre,
local z 0.5):
1. Datum 300 m (cell bottom 300 m): release in column 0 (the film), column 1 (flows into the
   film cell), column 3 (flows to the normal drain) and column 0 with default PRP options
   (only LOCAL_Z; the other cases also set EXTEND_TRACKING, STOP_AT_WEAK_SINK and
   EXIT_SOLVE_TOLERANCE 1e-5). Then columns 0 and 1 again with the DATA-SAT value of column 0
   set to 0 in a copy of the budget file (the film cell is then dry to PRT).
2. Datum 0 m and 1000 m (same model shifted, same film): release in column 0.
3. Threshold: datums 300 m and 1000 m, the DATA-SAT value of column 0 overwritten in a copy of
   the budget file and bisected (log10) between an aborting and a working saturation. Compared
   with the saturation below which bottom + sat * thickness rounds to bottom in double
   precision; that sum is the cell top PRT computes (MethodDis load_cell_properties) before
   it divides by top - bottom (MethodDis load_cell).

Usage: python make_repro.py [path/to/mf6]   (default: <repo>/bin/mf6)
Output: _work/ next to this script (overwritten), a summary on stdout.
"""

import shutil
import signal
import subprocess
import sys
from pathlib import Path

import flopy
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_EXE = HERE.parents[2] / "bin" / "mf6"
WORK = HERE / "_work"

NCOL = 5
DELR = 100.0
THICK = 10.0
K = 10.0
RECHARGE = 1e-3
CHD_COL, CHD_RISE = 2, 5.0
FILM_COL, FILM_COND = 0, 1e12
OUTLET_COL, OUTLET_COND = 4, 1e2
POROSITY = 0.2
DATUMS = (300.0, 0.0, 1000.0)  # cell bottom elevations; all release cases on the first
PRP_OPTIONS = {  # as in the study that met the abort (with LOCAL_Z, always set)
    "extend_tracking": True,
    "stop_at_weak_sink": True,
    "exit_solve_tolerance": 1e-5,
}
BISECT_STEPS = 40


# ---------------------------------------------------------------- GWF


def write_gwf(ws: Path, exe: Path, bot: float) -> None:
    """Write the GWF model with cell bottom bot."""
    sim = flopy.mf6.MFSimulation(sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim)
    flopy.mf6.ModflowIms(
        sim,
        complexity="complex",
        outer_dvclose=1e-12,
        inner_dvclose=1e-13,
        linear_acceleration="bicgstab",
    )
    gwf = flopy.mf6.ModflowGwf(sim, modelname="gwf", newtonoptions="newton", save_flows=True)
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=1, nrow=1, ncol=NCOL, delr=DELR, delc=DELR, top=bot + THICK, botm=bot
    )
    flopy.mf6.ModflowGwfnpf(
        gwf, icelltype=1, k=K, save_specific_discharge=True, save_saturation=True
    )
    flopy.mf6.ModflowGwfic(gwf, strt=bot + CHD_RISE)
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=[((0, 0, CHD_COL), bot + CHD_RISE)])
    flopy.mf6.ModflowGwfrcha(gwf, recharge=RECHARGE)
    drains = [((0, 0, FILM_COL), bot, FILM_COND), ((0, 0, OUTLET_COL), bot, OUTLET_COND)]
    flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=drains)
    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord="gwf.hds",
        budget_filerecord="gwf.cbc",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )
    sim.write_simulation(silent=True)


def read_head(ws: Path) -> np.ndarray:
    """Return the head of every column."""
    return flopy.utils.HeadFile(ws / "gwf.hds").get_data().ravel()


def read_saturation(budget: Path) -> np.ndarray:
    """Return the saturation of every column (DATA-SAT)."""
    return flopy.utils.CellBudgetFile(budget).get_data(text="DATA-SAT")[0]["sat"]


def set_saturation(budget: Path, out: Path, icol: int, sat: float) -> None:
    """Copy budget to out with the DATA-SAT value of column icol replaced by sat."""
    shutil.copyfile(budget, out)
    cbf = flopy.utils.CellBudgetFile(out)
    irec = [i for i, t in enumerate(cbf.recordarray["text"]) if t.strip() == b"DATA-SAT"]
    assert len(irec) == 1, "expected one DATA-SAT record"
    rec = cbf.get_data(idx=irec[0])[0]
    i = int(np.flatnonzero(rec["node"] == icol + 1)[0])
    ipos = int(cbf.iposarray[irec[0]])
    cbf.close()
    with open(out, "r+b") as f:
        # imeth 6 after ipos: ndat (int32), ndat - 1 auxiliary names (16 chars), nlist (int32),
        # then per entry node (int32), node2 (int32), q (float64), sat (float64)
        f.seek(ipos)
        ndat = int(np.frombuffer(f.read(4), np.int32)[0])
        f.seek(ipos + 4 + 16 * (ndat - 1) + 4 + i * 24 + 16)
        f.write(np.float64(sat).tobytes())
    assert read_saturation(out)[icol] == sat, "DATA-SAT patch did not land"


# ---------------------------------------------------------------- PRT


def write_prt(ws: Path, exe: Path, bot: float, icol: int, budget: str, options: dict) -> None:
    """Write a PRT model with one particle at the centre of column icol (local z 0.5)."""
    sim = flopy.mf6.MFSimulation(sim_name="prt", sim_ws=str(ws), exe_name=str(exe))
    flopy.mf6.ModflowTdis(sim)
    prt = flopy.mf6.ModflowPrt(sim, modelname="prt")
    flopy.mf6.ModflowPrtdis(
        prt, nlay=1, nrow=1, ncol=NCOL, delr=DELR, delc=DELR, top=bot + THICK, botm=bot
    )
    flopy.mf6.ModflowPrtmip(prt, porosity=POROSITY)
    x, y = (icol + 0.5) * DELR, 0.5 * DELR
    flopy.mf6.ModflowPrtprp(
        prt, nreleasepts=1, packagedata=[(0, (0, 0, icol), x, y, 0.5)], local_z=True, **options
    )
    flopy.mf6.ModflowPrtoc(
        prt,
        trackcsv_filerecord="prt.trk.csv",
        track_release=True,
        track_exit=True,
        track_terminate=True,
    )
    flopy.mf6.ModflowPrtfmi(
        prt, packagedata=[("GWFHEAD", "../gwf/gwf.hds"), ("GWFBUDGET", budget)]
    )
    ems = flopy.mf6.ModflowEms(sim, filename="prt.ems")
    sim.register_solution_package(ems, [prt.name])
    sim.write_simulation(silent=True)


# ---------------------------------------------------------------- running


def run_mf6(ws: Path, exe: Path) -> dict:
    """Run mf6 in ws; return the exit status, the signal name and the error line, if any."""
    proc = subprocess.run([str(exe)], cwd=ws, capture_output=True, text=True)
    rc = proc.returncode
    message = [line for line in proc.stderr.splitlines() if "signal" in line.lower()]
    return {
        "returncode": rc,
        "signal": signal.Signals(-rc).name if rc < 0 else "",
        "message": message[0].strip() if message else "",
        "normal": "Normal termination" in proc.stdout,
    }


def end_cell(ws: Path) -> str:
    """Return the column (0-based) and status of the termination record of the particle."""
    track = ws / "prt.trk.csv"
    if not track.exists():
        return "no track file"
    rec = np.genfromtxt(track, delimiter=",", names=True)
    last = np.atleast_1d(rec)[-1]
    return f"column {int(last['icell']) - 1}, istatus {int(last['istatus'])}"


def run_release(case_ws: Path, name: str, exe: Path, bot: float, icol: int, options: dict,
                film_sat: float | None = None) -> dict:
    """Write and run one single-particle PRT case; return its row.

    film_sat: if given, the PRT reads a copy of the budget file with the DATA-SAT value of the
    film column replaced by it; otherwise the GWF budget file itself.
    """
    ws = case_ws / name
    ws.mkdir(parents=True)
    budget = "../gwf/gwf.cbc"
    if film_sat is not None:
        set_saturation(case_ws / "gwf" / "gwf.cbc", ws / "gwf.cbc", FILM_COL, film_sat)
        budget = "gwf.cbc"
    write_prt(ws, exe, bot, icol, budget, options)
    row = run_mf6(ws, exe)
    row.update({"case": name, "column": icol, "end": end_cell(ws) if row["normal"] else ""})
    return row


def build_flow(case_ws: Path, exe: Path, bot: float) -> np.ndarray:
    """Write and run the GWF model; return the saturation per column."""
    gwf_ws = case_ws / "gwf"
    gwf_ws.mkdir(parents=True)
    write_gwf(gwf_ws, exe, bot)
    assert run_mf6(gwf_ws, exe)["normal"], f"GWF run failed in {gwf_ws}"
    sat = read_saturation(gwf_ws / "gwf.cbc")
    head = read_head(gwf_ws)
    print(f"datum {bot:g} m: head - bottom {np.array2string(head - bot, precision=3)}")
    print(f"datum {bot:g} m: saturation    {np.array2string(sat, precision=3)}")
    return sat


def release_cases(case_ws: Path, exe: Path, bot: float, full: bool) -> list[dict]:
    """Run the single-particle releases of one datum (all cases if full, else the film)."""
    cases = [  # (name, release column, PRP options, film saturation override)
        ("film", FILM_COL, PRP_OPTIONS, None),
        ("into_film", 1, PRP_OPTIONS, None),
        ("normal", 3, PRP_OPTIONS, None),
        ("film_default_options", FILM_COL, {}, None),
        ("film_sat_set_to_0", FILM_COL, PRP_OPTIONS, 0.0),
        ("into_film_sat_set_to_0", 1, PRP_OPTIONS, 0.0),
    ]
    if not full:
        cases = cases[:1]
    return [run_release(case_ws, f"prt_{name}", exe, bot, icol, opts, sat)
            for name, icol, opts, sat in cases]


def aborts_at(case_ws: Path, exe: Path, bot: float, sat: float, tag: int) -> bool:
    """Return whether a release in the film column aborts with its saturation set to sat."""
    row = run_release(case_ws, f"prt_sat_{tag:02d}", exe, bot, FILM_COL, PRP_OPTIONS, sat)
    return not row["normal"]


def bisect_threshold(case_ws: Path, exe: Path, bot: float, lo: float = 1e-17,
                     hi: float = 1e-10, steps: int = BISECT_STEPS) -> tuple[float, float]:
    """Bisect log10(saturation) between an aborting lo and a working hi; return the bracket."""
    assert aborts_at(case_ws, exe, bot, lo, 0), "lower bracket does not abort"
    assert not aborts_at(case_ws, exe, bot, hi, 1), "upper bracket aborts"
    for step in range(steps):
        mid = 10.0 ** (0.5 * (np.log10(lo) + np.log10(hi)))
        if aborts_at(case_ws, exe, bot, mid, step + 2):
            lo = mid
        else:
            hi = mid
    return lo, hi


def rounding_threshold(bot: float, thick: float = THICK) -> float:
    """Return the smallest saturation for which bot + sat * thick > bot in double precision."""
    lo, hi = 1e-20, 1e-10
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if np.float64(bot) + np.float64(mid) * np.float64(thick) > np.float64(bot):
            hi = mid
        else:
            lo = mid
    return hi


def print_rows(rows: list[dict], bot: float) -> None:
    """Print one line per release."""
    for r in rows:
        status = "normal termination" if r["normal"] else (
            f"exit {r['returncode']} {r['signal']} '{r['message']}'")
        print(f"datum {bot:g} m, {r['case']:<24} column {r['column']}: {status}"
              + (f" (ends {r['end']})" if r["end"] else ""))


def main(exe: Path = DEFAULT_EXE, work: Path = WORK) -> None:
    """Build every datum, run the releases and the threshold bisections; print a summary."""
    assert exe.exists(), f"mf6 not found at {exe}"
    version = subprocess.run([str(exe), "--version"], capture_output=True, text=True)
    print(version.stdout.strip())
    if work.exists():
        shutil.rmtree(work)
    for bot in DATUMS:
        case_ws = work / f"datum_{bot:g}"
        build_flow(case_ws, exe, bot)
        print_rows(release_cases(case_ws, exe, bot, full=bot == DATUMS[0]), bot)
    for bot in (b for b in DATUMS if b > 0.0):
        lo, hi = bisect_threshold(work / f"datum_{bot:g}", exe, bot)
        print(f"datum {bot:g} m, thickness {THICK:g} m: aborts at saturation {lo:.6e}, "
              f"runs at {hi:.6e}; bottom + sat * thickness > bottom in double precision "
              f"from sat = {rounding_threshold(bot):.6e}")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_EXE)
