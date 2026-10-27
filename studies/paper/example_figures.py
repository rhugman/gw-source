"""Worked-example figures of the paper (Figs 2 to 6, Sections 4.1 to 4.5); captions in
docs/paper/draft/display/E1.md, text in docs/paper/draft/sections/04a_examples.md.

Each figure rebuilds the example model with the builders the notebooks use
(tutorials/herebedragons.py, and tutorials/02_accounting/helpers.py for the worked example of
Foley and Black 2013) and traces it with the notebooks' calls, so the figures show the
notebooks' numbers.

- Fig. 2 (Section 4.1, notebook 01): (a) F of the supply well with the F = 0.1 and 0.5
  contours; (b) the flow-weighted share P of each release cell's water that weight-losing PRT
  particles deliver to the well, with the F = 0.5 contour of (a); (c) the well's water by source.
- Fig. 3 (Section 4.2, notebook 02): (a) the 3 x 3 worked example coloured by net F;
  (b, c) net and gross F of the 5 m3/d well in layer 3, log scale, in a window around it.
- Fig. 4 (Section 4.3, notebook 03): (a) G of river water near the well; (b) G of the recharge
  on a 300 m field, log scale; (c) the fate of the water from each source.
- Fig. 5 (Section 4.4, notebook 04): F on the regular grid (a) and on a Voronoi grid refined
  around the well and the river (b), with grid close-ups as insets; (c) F with XT3D and
  rotating anisotropy, flow-loop cells marked.
- Fig. 6 (Section 4.5, notebook 05): (a-d) F in the middle step of each season of the last
  year; (e) nested zones from statistics over the 36 seasonal steps.

All F maps use viridis from 0 to 1 with white contours (dashed F = 0.1, solid F = 0.5), river
cells in sky blue and the well as a white star; G maps use YlOrRd with black contours.
Source colours follow Fig. 9 (studies/paper/transient_figure.py). The numbers the text and
captions quote are in QUOTED and asserted before plotting. Sizes follow
studies/paper/method_figures.py: 7 in wide, 7 to 8 pt, PNG at 300 dpi and PDF. Run from the
repository root (model workspaces in studies/paper/output/example_figures, git-ignored):

    PYTHONPATH=src:tutorials python studies/paper/example_figures.py
"""

import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (style, palette, save, find_mf6)

import flopy  # noqa: E402
import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm, Normalize  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

TUTORIAL_DIR = mfig.TUTORIAL_DIR
ACCOUNTING_HELPERS = TUTORIAL_DIR / "02_accounting" / "helpers.py"
WORK_DIR = mfig.WORK_DIR / "example_figures"
WELL = "supply_well"
WEAK_WELL = "weak_well"
THRESHOLDS = (0.1, 0.5)  # F contours: dashed, solid
POROSITY = 0.3  # PRT porosity of notebook 01 (sets speeds, not paths)
EDGE = (0.05, 0.95)  # F range of the edge cells in the particle check
LOG_FLOOR = 1e-4  # values below the log scale (0 included) take its end colour
FIELD_ROWS = (10, 16)  # 0-based [start, stop) rows of the field of notebook 03
FIELD_COLS = (12, 18)
FIELD_NITRATE = 50.0  # mg/L, invented
CHLORIDE = {"river": 80.0, "west edge": 25.0, "recharge": 5.0}  # mg/L, invented
FORWARD_SOURCES = {"river": "RIV", "west edge": "CHD", "recharge": "RCH"}
RIVER_WINDOW = ((1250.0, 1650.0), (775.0, 1175.0))  # (x, y) limits (m) of Fig. 4a
WEAK_WINDOW = ((0.0, 1000.0), (950.0, 1450.0))  # (x, y) limits (m) of Fig. 3b, c
GRID_WINDOW = ((1325.0, 1625.0), (825.0, 1125.0))  # (x, y) limits (m) of the Fig. 5 insets
N_YEARS = 3
STEPS_PER_SEASON = 3
SNAPSHOT_SOURCES = {
    "recharge": ("RCH",), "storage": ("STO-SS", "STO-SY"), "river": ("RIV",),
    "west edge": ("CHD",),
}

OKABE_ITO = mfig.OKABE_ITO
F_CMAP = plt.get_cmap("viridis")
G_CMAP = plt.get_cmap("YlOrRd")
F_CONTOUR = "white"
G_CONTOUR = "black"
RIVER_COLOUR = OKABE_ITO["sky"]
WELL_COLOUR = OKABE_ITO["vermillion"]  # the well's share in bar charts
STAR_COLOUR = "white"  # the well on maps
CHD_COLOUR = "#9a9a9a"
LOOP_COLOUR = OKABE_ITO["vermillion"]
SOURCE_COLOURS = {  # as Fig. 9
    "recharge": OKABE_ITO["blue"], "west edge": OKABE_ITO["green"], "river": RIVER_COLOUR,
    "storage": OKABE_ITO["orange"],
}
SOURCE_LABELS = {
    "RCH": "recharge", "CHD": "west edge", "RIV": "river leakage",
}
ZONE_COLOURS = ("#ffffff", "#c6dbef", "#fdb863", "#5e3c99")  # outside, ring, seasonal, inner
ZONE_LABELS = ("outside", "ring", "seasonal zone", "inner zone")

# Numbers the text and captions quote; computed values must round (half up) to them.
QUOTED = {
    "fig2": {
        "cells F > 0.1": 630, "area F > 0.1 (km2)": 1.575,
        "cells F > 0.5": 457, "area F > 0.5 (km2)": 1.143,
        "expected area (km2)": 1.173,
        "recharge (m3/d)": 568.6, "west edge (m3/d)": 118.1, "river (m3/d)": 113.3,
        "recharge share": 0.711, "west edge share": 0.148, "river share": 0.142,
        "pumping (m3/d)": 800.0,
        "particles": 18208, "release cells": 1133, "captured (m3/d)": 799.9,
        "cells P > 0.5": 467, "area P > 0.5 (km2)": 1.168,
        "F > 0.5 vs P (%)": -2.1, "F > 0.1 vs P (%)": 34.9,
        "P cells outside F > 0.1": 0, "P cells outside F > 0.5": 14,
        "mean |P - F|": 0.058, "mean |P - F|, edge": 0.164, "edge cells": 372,
    },
    "fig3": {
        "cell inflow (m3/d)": 33.67, "pumping (m3/d)": 5.0, "passed on (m3/d)": 28.67,
        "F gross": 0.149, "F net": 1.0, "credited net (m3/d)": 33.667, "net / gross": 6.733,
        "net F strip layer 3, min": 0.93, "net F strip layer 3, max": 0.99,
        "gross F to the supply well": 0.821, "water entering A": 10.0,
    },
    "fig4": {
        "river in (m3/d)": 113.3, "river to well (m3/d)": 113.3,
        "west edge in (m3/d)": 323.9, "west edge to well (m3/d)": 118.1,
        "west edge share to well": 0.365,
        "recharge in (m3/d)": 1950.0, "recharge to well (m3/d)": 568.6,
        "recharge to river (m3/d)": 1381.4, "recharge share to well": 0.292,
        "G river at well": 0.142, "G west edge at well": 0.148, "G recharge at well": 0.711,
        "losing row first": 19, "losing row last": 23,
        "field cells": 36, "field recharge (m3/d)": 45.0, "field to well (m3/d)": 17.7,
        "field to river (m3/d)": 27.3, "field share to well": 0.39,
        "G field at well": 0.0222, "nitrate at well (mg/L)": 1.11, "chloride at well (mg/L)": 18.6,
    },
    "fig5": {
        "cells DIS": 1600, "cells DISV": 3241, "expected area DIS (km2)": 1.173,
        "expected area DISV (km2)": 1.178, "expected area change (%)": 0.4,
        "river share DIS": 0.142, "river share DISV": 0.140,
        "river distance DIS (m)": 100.0, "river distance DISV (m)": 100.0,
        "west edge share DIS": 0.148, "west edge share DISV": 0.133,
        "west edge in DIS (m3/d)": 323.9, "west edge in DISV (m3/d)": 289.9,
        "loops": 5, "loop cells": 40, "circulation (m3/d)": 4.42,
        "net F change, edges deleted": 0.155, "cells above 0.01, edges deleted": 24,
    },
    "fig6": {
        "pumping wet (m3/d)": 640.0, "pumping wet-to-dry (m3/d)": 800.0,
        "pumping dry (m3/d)": 1120.0, "pumping dry-to-wet (m3/d)": 640.0,
        "area F > 0.5 wet (km2)": 0.59, "area F > 0.5 dry (km2)": 1.35,
        "west end wet (m)": 375.0, "west end dry (m)": 25.0,
        "dry storage share": 0.525, "wet recharge share": 0.911,
        "inner (km2)": 0.52, "seasonal (km2)": 0.93, "ring (km2)": 0.41,
        "envelope (km2)": 1.86, "seasonal steps": 36,
    },
}
BELOW = {  # upper bounds stated in words
    "fig2 closure": 1e-8,
    "fig3 worked example": 1e-14,
    "fig5 DISU vs DIS": 1e-12,
    "fig5 block vs LU": 1e-15,
    "fig6 closure (m3/d)": 1e-6,
}


# ---------------------------------------------------------------- imports and checks


def import_tutorial_modules(tutorial_dir: Path = TUTORIAL_DIR,
                            helpers_file: Path = ACCOUNTING_HELPERS):
    """Import herebedragons and notebook 02's helpers (under a unique module name)."""
    if str(tutorial_dir) not in sys.path:
        sys.path.insert(0, str(tutorial_dir))
    import herebedragons as hbd

    spec = importlib.util.spec_from_file_location("accounting_helpers", helpers_file)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    return hbd, helpers


def round_half_up(value: float, digits: int) -> float:
    """Round half up, as the notebooks print areas (1.1425 -> 1.143)."""
    scale = 10.0 ** digits
    return float(np.floor(value * scale + 0.5 + 1e-9) / scale)


def check_quoted(computed: dict, quoted: dict) -> None:
    """Assert that every quoted number matches the computed value at its printed precision."""
    for key, value in quoted.items():
        got = computed[key]
        if isinstance(value, int):
            assert int(round(got)) == value and abs(got - round(got)) < 1e-9, \
                f"{key}: computed {got}, quoted {value}"
        else:
            text = repr(value)
            digits = len(text.split(".")[1]) if "." in text else 0
            assert abs(round_half_up(got, digits) - value) < 1e-9, \
                f"{key}: computed {got:.5f}, quoted {value}"


def km2(area_m2: float) -> float:
    """Return an area in km2."""
    return area_m2 / 1e6


# ---------------------------------------------------------------- Example 4.1


def compute_quickstart(hbd, work: Path, mf6_exe: Path, well: str = WELL,
                       porosity: float = POROSITY) -> dict:
    """Build and trace notebook 01's model; run the PRT particle check."""
    run = hbd.build_quickstart(work / "quickstart", mf6_exe)
    step = gs.read_step(run.ws, boundnames=True)
    selection = gs.select(step, boundnames=[well])
    res = gs.backward(step, {well: selection})
    prt = gs.track_particles(run.ws, step, res, well, gs.PrtConfig(porosity=porosity), mf6_exe,
                             work / "quickstart_prt")
    return {
        "run": run, "step": step, "res": res, "f": res.fraction_through[well],
        "well_cell": int(np.flatnonzero(selection.cells)[0]),
        "by_source": hbd.volume_from_table(res, well),
        "closure": gs.diagnostics.backward_closure(step, res, well), "prt": prt,
    }


def quickstart_values(data: dict, thresholds: tuple = THRESHOLDS, edge: tuple = EDGE) -> dict:
    """Return the Fig. 2 numbers of the text."""
    step, f, prt = data["step"], data["f"], data["prt"]
    area = step.area
    p = prt.cell_capture_fraction
    released = np.isfinite(p)
    at_edge = released & (f > edge[0]) & (f < edge[1])
    p_zone = np.nan_to_num(p) > 0.5
    volumes = data["by_source"]["volume_from"]
    shares = data["by_source"]["share"]
    values = {
        "expected area (km2)": km2(float(f @ area)),
        "pumping (m3/d)": data["res"].destination_inflow[WELL],
        "particles": prt.release.n, "release cells": int(released.sum()),
        "captured (m3/d)": prt.captured_flow,
        "cells P > 0.5": int(p_zone.sum()), "area P > 0.5 (km2)": km2(area[p_zone].sum()),
        "mean |P - F|": float(np.abs(p - f)[released].mean()),
        "mean |P - F|, edge": float(np.abs(p - f)[at_edge].mean()),
        "edge cells": int(at_edge.sum()),
    }
    for t in thresholds:
        zone = f > t
        values[f"cells F > {t}"] = int(zone.sum())
        values[f"area F > {t} (km2)"] = km2(area[zone].sum())
        values[f"F > {t} vs P (%)"] = 100.0 * (area[zone].sum() / area[p_zone].sum() - 1.0)
        values[f"P cells outside F > {t}"] = int((p_zone & ~zone).sum())
    for package, name in (("RCH", "recharge"), ("CHD", "west edge"), ("RIV", "river")):
        values[f"{name} (m3/d)"] = float(volumes[package])
        values[f"{name} share"] = float(shares[package])
    return values


# ---------------------------------------------------------------- Example 4.2


def worked_example(helpers) -> dict:
    """Trace the worked example of Foley and Black (2013) to A under net accounting."""
    fb_step = helpers.fb13_step()
    labels = list(helpers.FB13_LABELS)
    res = gs.backward(fb_step, {"A": gs.select_cells(fb_step, [labels.index("A")])},
                      gs.TraceConfig(accounting="net"))
    published = np.array([  # Foley and Black (2013), Figs 5-8: F, volume through, volume from
        [1.0, 0.5, 0.625, 1.0, 0.75, 0.75, 0.0, 0.75, 0.75],
        [10.0, 5.0, 6.25, 5.0, 7.5, 6.0, 0.0, 1.5, 0.75],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 1.5, 0.75],
    ])
    computed = np.array([res.fraction_through["A"][:9], res.volume_through["A"][:9],
                         res.volume_from["A"][:9]])
    return {"f": res.fraction_through["A"], "inflow": res.destination_inflow["A"],
            "error": float(np.abs(computed - published).max())}


def compute_layered(hbd, helpers, work: Path, mf6_exe: Path,
                    wells: tuple[str, str] = (WELL, WEAK_WELL)) -> dict:
    """Build notebook 02's three-layer model and trace both wells, gross and net."""
    run = hbd.build_layered(work / "layered", mf6_exe)
    step = gs.read_step(run.ws, boundnames=True)
    selections = {name: gs.select(step, boundnames=[name]) for name in wells}
    gross = gs.backward(step, selections, gs.TraceConfig())
    net = gs.backward(step, selections, gs.TraceConfig(accounting="net"))
    weak = dict((name, cellid) for name, cellid, _ in run.info["wells"])[WEAK_WELL]
    return {"run": run, "step": step, "gross": gross, "net": net, "weak_cellid": weak,
            "weak_cell": run.info["weak_well_node"], "budget": gs.cell_budget(step),
            "fb13": worked_example(helpers)}


def layered_values(data: dict) -> dict:
    """Return the Fig. 3 numbers of the text."""
    step, budget, cell = data["step"], data["budget"], data["weak_cell"]
    gross, net = data["gross"], data["net"]
    layer, row, col = data["weak_cellid"]
    strip = net.fraction_through[WEAK_WELL].reshape(step.grid_shape)[layer, row, :col]
    credited_gross = float(gross.volume_from[WEAK_WELL].sum())
    credited_net = float(net.volume_from[WEAK_WELL].sum())
    return {
        "cell inflow (m3/d)": float(budget.inflow[cell]),
        "pumping (m3/d)": float(budget.sink[cell]),
        "passed on (m3/d)": float(budget.edge_out[cell]),
        "F gross": float(gross.fraction_through[WEAK_WELL][cell]),
        "F net": float(net.fraction_through[WEAK_WELL][cell]),
        "credited net (m3/d)": credited_net, "net / gross": credited_net / credited_gross,
        "net F strip layer 3, min": float(strip.min()),
        "net F strip layer 3, max": float(strip.max()),
        "gross F to the supply well": float(gross.fraction_through[WELL][cell]),
        "water entering A": data["fb13"]["inflow"],
    }


# ---------------------------------------------------------------- Example 4.3


def compute_forward(hbd, work: Path, mf6_exe: Path, sources: dict = FORWARD_SOURCES,
                    field_rows: tuple = FIELD_ROWS, field_cols: tuple = FIELD_COLS) -> dict:
    """Build notebook 03's model; trace the sources and the field forward."""
    run = hbd.build_quickstart(work / "forward", mf6_exe)
    spec = run.spec
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=[WELL])
    selections = {name: gs.select(step, package=p) for name, p in sources.items()}
    fwd = gs.forward(step, selections)
    zones = np.zeros((spec.nrow, spec.ncol), dtype=int)
    zones[slice(*field_rows), slice(*field_cols)] = 1
    field = gs.select_zone(step, zones, 1, package="RCH")
    return {"run": run, "step": step, "fwd": fwd, "field": field,
            "field_fwd": gs.forward(step, {"field": field}),
            "well_cell": int(np.flatnonzero(well.cells)[0])}


def forward_fate(fwd: gs.ForwardResult, sources: dict = FORWARD_SOURCES) -> pd.DataFrame:
    """Return, per source, the inflow and the volumes to the well and to the river (m3/d)."""
    rows = {name: {"in": fwd.source_inflow[name],
                   "to the well": float(fwd.volume_to_by_term[name]["WEL"].sum()),
                   "to the river": float(fwd.volume_to_by_term[name]["RIV"].sum())}
            for name in sources}
    return pd.DataFrame(rows).T


def forward_values(data: dict, chloride: dict = CHLORIDE, nitrate: float = FIELD_NITRATE) -> dict:
    """Return the Fig. 4 numbers of the text."""
    step, fwd, cell = data["step"], data["fwd"], data["well_cell"]
    fate = forward_fate(fwd)
    riv = step.term_package == step.package_names.index("RIV")
    losing_rows = step.term_cell[riv & (step.term_flow > 0.0)] // data["run"].spec.ncol + 1
    field_fwd = data["field_fwd"]
    field_in = field_fwd.source_inflow["field"]
    g_field = field_fwd.source_fraction["field"][cell]
    to_well = float(field_fwd.volume_to_by_term["field"]["WEL"].sum())
    values = {
        "losing row first": int(losing_rows.min()), "losing row last": int(losing_rows.max()),
        "field cells": int(data["field"].terms.sum()), "field recharge (m3/d)": field_in,
        "field to well (m3/d)": to_well,
        "field to river (m3/d)": float(field_fwd.volume_to_by_term["field"]["RIV"].sum()),
        "field share to well": to_well / field_in, "G field at well": g_field,
        "nitrate at well (mg/L)": g_field * nitrate,
        "chloride at well (mg/L)": sum(fwd.source_fraction[n][cell] * c
                                       for n, c in chloride.items()),
    }
    for name in fate.index:
        values[f"{name} in (m3/d)"] = fate.loc[name, "in"]
        values[f"{name} to well (m3/d)"] = fate.loc[name, "to the well"]
        values[f"{name} to river (m3/d)"] = fate.loc[name, "to the river"]
        values[f"{name} share to well"] = fate.loc[name, "to the well"] / fate.loc[name, "in"]
        values[f"G {name} at well"] = fwd.source_fraction[name][cell]
    return values


# ---------------------------------------------------------------- Example 4.4


def trace_well(run, well: str = WELL) -> tuple[gs.FlowStep, gs.BackwardResult]:
    """Read a model's step and trace the well backward."""
    step = gs.read_step(run.ws, boundnames=True)
    return step, gs.backward(step, {well: gs.select(step, boundnames=[well])})


def compute_grids(hbd, work: Path, mf6_exe: Path) -> dict:
    """Build notebook 04's DIS, DISV, DISU and XT3D models and trace the well on each.

    The DISV grid is notebook 04's vorflow grid (hbd.build_voronoi with its default sizes).
    """
    runs = {
        "DIS": hbd.build_quickstart(work / "grids_dis", mf6_exe),
        "DISV": hbd.build_voronoi(work / "grids_disv", mf6_exe),
        "DISU": hbd.build_disu(work / "grids_disu", mf6_exe, with_vertices=True),
        "XT3D": hbd.build_xt3d(work / "grids_xt3d", mf6_exe),
    }
    traced = {label: trace_well(run) for label, run in runs.items()}
    step_x, res_x = traced["XT3D"]
    cycles = gs.diagnostics.cycle_report(step_x, res_x)
    groups = {WELL: gs.select(step_x, boundnames=[WELL])}
    lu = gs.backward(step_x, groups, gs.TraceConfig(solver="lu"))
    net_exact = gs.backward(step_x, groups, gs.TraceConfig(accounting="net"))
    net_deleted = gs.backward(step_x, groups,
                              gs.TraceConfig(accounting="net", remove_cycles=True))
    return {
        "runs": runs, "steps": {k: v[0] for k, v in traced.items()},
        "results": {k: v[1] for k, v in traced.items()}, "cycles": cycles,
        "loop_cells": gs.diagnostics.cycle_ids(step_x.n_cells, cycles) >= 0,
        "block_vs_lu": float(np.abs(lu.fraction_through[WELL]
                                    - res_x.fraction_through[WELL]).max()),
        "net_deleted_change": np.abs(net_deleted.fraction_through[WELL]
                                     - net_exact.fraction_through[WELL]),
    }


def river_distance(hbd, run, step: gs.FlowStep, res: gs.BackwardResult) -> float:
    """Return the distance (m) from the well's cell centre to the nearest river cell centre."""
    centres = gs.export.cell_centres(run.grb_file)
    well_xy = centres[np.flatnonzero(res.selections[WELL].cells)[0]]
    return float(np.hypot(*(centres[hbd.feature_cells(step, "RIV")] - well_xy).T).min())


def grids_values(hbd, data: dict) -> dict:
    """Return the Fig. 5 numbers of the text."""
    steps, results, runs = data["steps"], data["results"], data["runs"]
    values = {}
    for label in ("DIS", "DISV"):
        f, area = results[label].fraction_through[WELL], steps[label].area
        values[f"cells {label}"] = steps[label].n_cells
        values[f"expected area {label} (km2)"] = km2(float(f @ area))
        shares = hbd.volume_from_table(results[label], WELL)["share"]
        values[f"river share {label}"] = float(shares["RIV"])
        values[f"west edge share {label}"] = float(shares["CHD"])
        chd = gs.select(steps[label], package="CHD")
        values[f"west edge in {label} (m3/d)"] = float(steps[label].term_flow[chd.terms].sum())
        values[f"river distance {label} (m)"] = river_distance(hbd, runs[label], steps[label],
                                                               results[label])
    values["expected area change (%)"] = 100.0 * (
        values["expected area DISV (km2)"] / values["expected area DIS (km2)"] - 1.0)
    change = data["net_deleted_change"]
    values.update({
        "loops": len(data["cycles"]), "loop cells": int(data["loop_cells"].sum()),
        "circulation (m3/d)": float(sum(c.circulation for c in data["cycles"])),
        "net F change, edges deleted": float(change.max()),
        "cells above 0.01, edges deleted": int((change > 0.01).sum()),
    })
    return values


# ---------------------------------------------------------------- Example 4.5


def compute_seasons(hbd, work: Path, mf6_exe: Path, n_years: int = N_YEARS,
                    steps_per_season: int = STEPS_PER_SEASON,
                    sources: dict = SNAPSHOT_SOURCES) -> dict:
    """Build notebook 05's seasonal model; trace every step and the snapshot statistics."""
    run = hbd.build_transient(work / "seasons", mf6_exe, n_years=n_years,
                              steps_per_season=steps_per_season)
    reader = gs.open_model(run.ws, boundnames=True)
    groups = {WELL: {"boundnames": [WELL]}}
    rows, maps = [], {}
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        res = gs.backward(step, {WELL: gs.select(step, boundnames=[WELL])})
        by_package = {name: v.sum() for name, v in res.volume_from_by_term[WELL].items()}
        row = {label: sum(by_package.get(p, 0.0) for p in packages)
               for label, packages in sources.items()}
        row.update({"season": run.info["season"][kstpkper[1]],
                    "pumping": res.destination_inflow[WELL]})
        rows.append(row)
        maps[kstpkper] = (step, res.fraction_through[WELL])
    seasonal = list(range(1, 4 * n_years + 1))
    config = gs.TransientConfig(steps=seasonal, outputs=("fraction_through",), threshold=0.5)
    stats = gs.trace_transient(reader, groups, "backward", config)
    last_year = [(steps_per_season // 2, kper) for kper in seasonal[-4:]]
    return {"run": run, "by_step": pd.DataFrame(rows), "stats": stats,
            "snapshots": {run.info["season"][ks[1]]: maps[ks] for ks in last_year}}


def nested_zones(stats, threshold: float = 0.1) -> np.ndarray:
    """Return the zone class per cell: 0 outside, 1 ring, 2 seasonal zone, 3 inner zone."""
    asn = stats.stats["asn"]["fraction_through"][WELL]
    f_max = stats.stats["max"]["fraction_through"][WELL]
    classes = np.zeros(stats.template.n_cells)
    classes[f_max > threshold] = 1
    classes[asn == 0.5] = 2
    classes[asn == 1.0] = 3
    return classes


def seasons_values(data: dict, sources: dict = SNAPSHOT_SOURCES) -> dict:
    """Return the Fig. 6 numbers of the text."""
    run, by_step, stats = data["run"], data["by_step"], data["stats"]
    centres = gs.export.cell_centres(run.grb_file)
    values = {}
    for season, (step, f) in data["snapshots"].items():
        river_x = centres[step.term_cell[step.term_package
                                         == step.package_names.index("RIV")], 0].min()
        zone = (f > 0.5) & (centres[:, 0] < river_x)
        values[f"pumping {season} (m3/d)"] = float(-step.term_flow[
            step.term_package == step.package_names.index("WEL")].sum())
        values[f"area F > 0.5 {season} (km2)"] = km2(step.area[f > 0.5].sum())
        values[f"west end {season} (m)"] = float(centres[zone, 0].min())
    seasonal = by_step[by_step["season"] != "steady"]
    shares = seasonal.groupby("season", sort=False)[list(sources)].mean()
    shares = shares.div(shares.sum(axis=1), axis=0)
    classes = nested_zones(stats)
    area = stats.template.area
    values.update({
        "dry storage share": shares.loc["dry", "storage"],
        "wet recharge share": shares.loc["wet", "recharge"],
        "inner (km2)": km2(area[classes == 3].sum()),
        "seasonal (km2)": km2(area[classes == 2].sum()),
        "ring (km2)": km2(area[classes == 1].sum()),
        "envelope (km2)": km2(area[classes > 0].sum()),
        "seasonal steps": len(stats.steps),
        "closure (m3/d)": float((by_step[list(sources)].sum(axis=1)
                                 - by_step["pumping"]).abs().max()),
    })
    return values


# ---------------------------------------------------------------- map drawing


def model_grid(grb_file: Path):
    """Return the FloPy model grid of a binary grid file."""
    return flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False).modelgrid


def draw_values(ax, grb_file: Path, step: gs.FlowStep, values: np.ndarray, cmap, norm,
                layer: int = 0):
    """Colour every cell of one layer by a per-cell value; NaN cells stay blank."""
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(grb_file), layer=layer, ax=ax)
    gridded = np.ma.masked_invalid(gs.export.to_grid(step, values))
    return pmv.plot_array(gridded, cmap=cmap, norm=norm, edgecolor="face", linewidth=0.3)


def draw_contours(ax, grb_file: Path, step: gs.FlowStep, values: np.ndarray, levels: tuple,
                  colour: str, styles: tuple, layer: int = 0, width: float = 1.0):
    """Draw contours of a per-cell value at the given levels."""
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(grb_file), layer=layer, ax=ax)
    gridded = np.ma.masked_invalid(gs.export.to_grid(step, values))
    return pmv.contour_array(gridded, levels=list(levels), colors=colour,
                             linestyles=list(styles), linewidths=width)


def draw_f_contours(ax, grb_file: Path, step: gs.FlowStep, f: np.ndarray,
                    levels: tuple = THRESHOLDS, colour: str = F_CONTOUR, layer: int = 0):
    """Draw the F = 0.1 (dashed) and F = 0.5 (solid) contours."""
    styles = ("--", "-") if len(levels) == 2 else ("-",) * len(levels)
    return draw_contours(ax, grb_file, step, f, levels, colour, styles, layer)


def draw_cells(ax, grb_file: Path, step: gs.FlowStep, cells: np.ndarray, colour: str,
               layer: int = 0) -> None:
    """Fill the given cells with one colour."""
    values = np.full(step.n_cells, np.nan)
    values[cells] = 1.0
    draw_values(ax, grb_file, step, values, ListedColormap([colour]), Normalize(0.0, 2.0),
                layer)


def draw_well(ax, grb_file: Path, cells: np.ndarray, size: float = 70.0,
              colour: str = STAR_COLOUR) -> None:
    """Mark wells with a star."""
    xy = gs.export.cell_centres(grb_file)[np.atleast_1d(cells)]
    ax.scatter(xy[:, 0], xy[:, 1], marker="*", s=size, color=colour, edgecolor="black",
               linewidth=0.6, zorder=6)


def draw_features(ax, hbd, grb_file: Path, step: gs.FlowStep, well_cells: np.ndarray,
                  river: bool = True) -> None:
    """Fill the river cells and mark the well."""
    if river:
        draw_cells(ax, grb_file, step, hbd.feature_cells(step, "RIV"), RIVER_COLOUR)
    draw_well(ax, grb_file, well_cells)


def km_axes(ax, window: tuple | None = None, extent: float = 2000.0, step_km: float = 0.5,
            x_label: bool = True, y_label: bool = True) -> None:
    """Equal-aspect map axes in km with the given window (m) or the whole domain."""
    window = ((0.0, extent), (0.0, extent)) if window is None else window
    ax.set_xlim(*window[0])
    ax.set_ylim(*window[1])
    ax.set_aspect("equal")
    km = FuncFormatter(lambda v, _: f"{v / 1000:g}")
    for axis, (lo, hi) in ((ax.xaxis, window[0]), (ax.yaxis, window[1])):
        ticks = np.arange(np.ceil(lo / (1000 * step_km)), np.floor(hi / (1000 * step_km)) + 1)
        axis.set_ticks(ticks * 1000 * step_km)
        axis.set_major_formatter(km)
    ax.set_xlabel("x (km)" if x_label else "")
    ax.set_ylabel("y (km)" if y_label else "")
    if not x_label:
        ax.tick_params(labelbottom=False)
    if not y_label:
        ax.tick_params(labelleft=False)
    ax.spines[["top", "right"]].set_visible(True)


def panel_title(ax, text: str) -> None:
    """Bold panel title at the top left."""
    ax.set_title(text, loc="left", fontweight="bold", fontsize=8, pad=3)


def colour_bar(fig, mappable, cax, label: str, ticks=None) -> None:
    """Add a slim colour bar."""
    bar = fig.colorbar(mappable, cax=cax, ticks=ticks)
    bar.set_label(label)
    bar.outline.set_linewidth(0.5)
    bar.ax.tick_params(labelsize=7)


def f_map(ax, hbd, grb_file: Path, step: gs.FlowStep, f: np.ndarray, well_cells,
          contours: bool = True):
    """Draw an F map (viridis 0 to 1), its contours, the river and the well."""
    image = draw_values(ax, grb_file, step, f, F_CMAP, Normalize(0.0, 1.0))
    if contours:
        draw_f_contours(ax, grb_file, step, f)
    draw_features(ax, hbd, grb_file, step, well_cells)
    return image


# ---------------------------------------------------------------- Fig. 2


def source_bars(ax, volumes: list[float], shares: list[float], names: list[str],
                colours: list[str], xlabel: str) -> None:
    """Horizontal bars of volumes by source, labelled with their shares."""
    y = np.arange(len(names))
    ax.barh(y, volumes, color=colours, height=0.62)
    for yi, volume, share in zip(y, volumes, shares):
        ax.text(volume + 0.02 * max(volumes), yi, f"{share:.0%}".replace("%", " %"),
                va="center", ha="left", fontsize=7)
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.25 * max(volumes))
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)


def make_fig2(out_dir: Path, hbd, data: dict) -> list[Path]:
    """Fig. 2: F, the particle share and the well's water by source (Section 4.1)."""
    run, step, f = data["run"], data["step"], data["f"]
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 2.7))
    ax_f = fig.add_axes((0.065, 0.16, 0.278, 0.72))
    ax_p = fig.add_axes((0.36, 0.16, 0.278, 0.72))
    cax = fig.add_axes((0.648, 0.16, 0.012, 0.72))
    ax_c = fig.add_axes((0.825, 0.3, 0.16, 0.5))
    image = f_map(ax_f, hbd, run.grb_file, step, f, data["well_cell"])
    draw_values(ax_p, run.grb_file, step, data["prt"].cell_capture_fraction, F_CMAP,
                Normalize(0.0, 1.0))
    draw_f_contours(ax_p, run.grb_file, step, f, levels=(0.5,))
    draw_features(ax_p, hbd, run.grb_file, step, data["well_cell"])
    km_axes(ax_f)
    km_axes(ax_p, y_label=False)
    panel_title(ax_f, "(a) F, full mixing")
    panel_title(ax_p, "(b) particle share")
    colour_bar(fig, image, cax, "F or particle share (-)")
    table = data["by_source"]
    names = [SOURCE_LABELS[p] for p in table.index]
    colours = [SOURCE_COLOURS[{"RCH": "recharge", "CHD": "west edge", "RIV": "river"}[p]]
               for p in table.index]
    source_bars(ax_c, list(table["volume_from"]), list(table["share"]), names, colours,
                "water reaching\nthe well (m³/d)")
    fig.text(0.715, 0.88, "(c) the well's water by source", ha="left", va="bottom",
             fontweight="bold", fontsize=8)
    return mfig.save(fig, out_dir, "fig2_contributing_area")


# ---------------------------------------------------------------- Fig. 3


def draw_worked_example(ax, helpers, f: np.ndarray, half: float = 0.36,
                        spacing: float = 1.3) -> None:
    """Panel (a): the 3 x 3 worked example, cells coloured by net F, flows as arrows."""
    labels = helpers.FB13_LABELS
    positions = {k: (spacing * x, spacing * y) for k, (x, y) in helpers.FB13_POSITIONS.items()}
    for i, label in enumerate(labels):
        x, y = positions[label]
        outside = label in helpers.FB13_OUTSIDE
        face = "white" if outside else F_CMAP(f[i])
        ax.add_patch(Rectangle((x - half, y - half), 2 * half, 2 * half, facecolor=face,
                               edgecolor=mfig.MUTED, lw=0.8, ls="--" if outside else "-"))
        ink = "black" if outside or f[i] > 0.6 else "white"
        ax.text(x, y + 0.11, label, ha="center", va="center", fontsize=8, fontweight="bold",
                color=ink)
        if not outside:
            ax.text(x, y - 0.14, f"{f[i]:.3g}", ha="center", va="center", fontsize=7,
                    color=ink)
    for a, b, q in helpers.FB13_EDGES:
        start, end = np.asarray(positions[a], float), np.asarray(positions[b], float)
        unit = (end - start) / np.linalg.norm(end - start)
        p0, p1 = start + (half + 0.03) * unit, end - (half + 0.03) * unit
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7,
                                     color=mfig.INK, lw=0.6 + 0.12 * q, shrinkA=0, shrinkB=0))
        side = np.array([-unit[1], unit[0]])
        mid = 0.5 * (p0 + p1) + 0.13 * side
        ax.text(*mid, f"{q:g}", ha="center", va="center", fontsize=7)
    ax.set_xlim(-0.45, 4.7)
    ax.set_ylim(-0.45, 4.7)
    ax.set_aspect("equal")
    ax.axis("off")


def weak_map(ax, hbd, data: dict, f: np.ndarray, layer: int, norm):
    """Map F of the weak well in one layer (log scale), with the CHD cells and the well."""
    run, step = data["run"], data["step"]
    image = draw_values(ax, run.grb_file, step, np.maximum(f, LOG_FLOOR), F_CMAP, norm, layer)
    centres = gs.export.cell_centres(run.grb_file)
    chd = hbd.feature_cells(step, "CHD", layer)
    ax.scatter(centres[chd, 0], centres[chd, 1], marker="s", s=9, color=CHD_COLOUR,
               edgecolor="black", linewidth=0.3, zorder=5)
    draw_well(ax, run.grb_file, data["weak_cell"], size=80)
    return image


def make_fig3(out_dir: Path, hbd, helpers, data: dict) -> list[Path]:
    """Fig. 3: the worked example and net against gross F of a weak sink (Section 4.2)."""
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 3.55))
    ax_a = fig.add_axes((0.01, 0.065, 0.36, 0.86))  # top at 0.925, level with panel (b)
    draw_worked_example(ax_a, helpers, data["fb13"]["f"])
    ax_a.set_anchor("N")  # the equal-aspect drawing sits at the top of its box
    panel_title(ax_a, "(a) worked example, net F to cell A")
    norm = LogNorm(1e-3, 1.0)
    layer = data["weak_cellid"][0]
    titles = {"net": "(b) net accounting, layer 3", "gross": "(c) gross accounting, layer 3"}
    for n, (mode, title) in enumerate(titles.items()):
        ax = fig.add_axes((0.43, 0.585 - 0.455 * n, 0.42, 0.34))
        image = weak_map(ax, hbd, data, data[mode].fraction_through[WEAK_WELL], layer, norm)
        km_axes(ax, WEAK_WINDOW, step_km=0.25, x_label=n == 1)
        panel_title(ax, title)
    cax = fig.add_axes((0.875, 0.13, 0.014, 0.795))
    colour_bar(fig, image, cax, "F of the 5 m³/d well (-)", ticks=(1e-3, 1e-2, 1e-1, 1.0))
    cax.set_yticklabels(["≤0.001", "0.01", "0.1", "1"])
    return mfig.save(fig, out_dir, "fig3_accounting")


# ---------------------------------------------------------------- Fig. 4


def field_rectangle(ax, spec, rows: tuple = FIELD_ROWS, cols: tuple = FIELD_COLS) -> None:
    """Outline the field."""
    x0, y0 = cols[0] * spec.delr, spec.ly - rows[1] * spec.delc
    ax.add_patch(Rectangle((x0, y0), (cols[1] - cols[0]) * spec.delr,
                           (rows[1] - rows[0]) * spec.delc, fill=False, edgecolor="black",
                           linewidth=1.0, zorder=5))


def fate_bars(ax, fate: pd.DataFrame) -> None:
    """Stacked horizontal bars: each source's water to the well and to the river."""
    names = {"river": "river", "west edge": "west edge", "recharge": "recharge"}
    y = np.arange(len(fate))
    ax.barh(y, fate["to the well"], color=WELL_COLOUR, height=0.62, label="to the well")
    ax.barh(y, fate["to the river"], left=fate["to the well"], color=RIVER_COLOUR,
            height=0.62, label="to the river")
    ax.set_yticks(y, [names[n] for n in fate.index])
    ax.invert_yaxis()
    ax.set_xlim(0.0, 2200.0)
    ax.set_xticks((0, 1000, 2000))
    ax.set_xlabel("water leaving\nthe model (m³/d)")
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper right", handlelength=1.0, borderaxespad=0.0)


def draw_river_outline(ax, hbd, grb_file: Path, step: gs.FlowStep,
                       colour: str = RIVER_COLOUR) -> None:
    """Outline the river cells (DIS), so that the values in them stay visible."""
    model = model_grid(grb_file)
    for cell in hbd.feature_cells(step, "RIV"):
        verts = np.asarray(model.get_cell_vertices(int(cell)))
        ax.add_patch(plt.Polygon(verts, closed=True, fill=False, edgecolor=colour,
                                 linewidth=0.9, zorder=4))


def make_fig4(out_dir: Path, hbd, data: dict, levels: tuple = (0.05, 0.2, 0.5),
              styles: tuple = (":", "--", "-")) -> list[Path]:
    """Fig. 4: G of river water, G of a field's recharge and the fate by source (Section 4.3)."""
    run, step = data["run"], data["step"]
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 2.6))
    ax_a = fig.add_axes((0.065, 0.17, 0.215, 0.62))
    cax_a = fig.add_axes((0.287, 0.17, 0.011, 0.62))
    ax_b = fig.add_axes((0.43, 0.17, 0.215, 0.62))
    cax_b = fig.add_axes((0.652, 0.17, 0.011, 0.62))
    ax_c = fig.add_axes((0.865, 0.25, 0.12, 0.5))
    g_river = data["fwd"].source_fraction["river"]
    image = draw_values(ax_a, run.grb_file, step, g_river, G_CMAP, Normalize(0.0, 1.0))
    draw_contours(ax_a, run.grb_file, step, g_river, levels, G_CONTOUR, styles, width=0.8)
    draw_river_outline(ax_a, hbd, run.grb_file, step)
    draw_well(ax_a, run.grb_file, data["well_cell"])
    handles = [plt.Line2D([], [], color=G_CONTOUR, ls=ls, lw=0.8, label=f"G = {level:g}")
               for level, ls in zip(levels, styles)]
    ax_a.legend(handles=handles, loc="upper left", handlelength=1.8, borderaxespad=0.3,
                labelspacing=0.3)
    km_axes(ax_a, RIVER_WINDOW, step_km=0.1)
    colour_bar(fig, image, cax_a, "G of river water (-)")
    panel_title(ax_a, "(a) river water")
    g_field = data["field_fwd"].source_fraction["field"]
    image = draw_values(ax_b, run.grb_file, step, np.maximum(g_field, LOG_FLOOR), G_CMAP,
                        LogNorm(1e-3, 1.0))
    field_rectangle(ax_b, run.spec)
    draw_features(ax_b, hbd, run.grb_file, step, data["well_cell"])
    km_axes(ax_b)
    colour_bar(fig, image, cax_b, "G of the field's recharge (-)", ticks=(1e-3, 1e-2, 1e-1, 1.0))
    cax_b.set_yticklabels(["≤0.001", "0.01", "0.1", "1"])
    panel_title(ax_b, "(b) recharge on a field")
    fate_bars(ax_c, forward_fate(data["fwd"]))
    fig.text(0.775, 0.8, "(c) fate by source", ha="left", va="bottom", fontweight="bold",
             fontsize=8)
    return mfig.save(fig, out_dir, "fig4_forward")


# ---------------------------------------------------------------- Fig. 5


def grid_inset(ax, hbd, run, step: gs.FlowStep, res: gs.BackwardResult,
               window: tuple = GRID_WINDOW, bounds=(0.71, 0.01, 0.28, 0.28)) -> None:
    """Inset: grid lines, river cells and the well in a window; the window outlined on the map."""
    inset = ax.inset_axes(bounds)
    inset.set_facecolor("white")
    draw_cells(inset, run.grb_file, step, hbd.feature_cells(step, "RIV"), RIVER_COLOUR)
    pmv = flopy.plot.PlotMapView(modelgrid=model_grid(run.grb_file), ax=inset)
    pmv.plot_grid(linewidth=0.3, color="#6e6e6e")
    draw_well(inset, run.grb_file, np.flatnonzero(res.selections[WELL].cells), size=20)  # small: refined cells stay visible
    inset.set_xlim(*window[0])
    inset.set_ylim(*window[1])
    inset.set_aspect("equal")
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("white")
        spine.set_linewidth(1.0)
    (x0, x1), (y0, y1) = window
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="white",
                           linewidth=0.8, zorder=7))


def make_fig5(out_dir: Path, hbd, data: dict) -> list[Path]:
    """Fig. 5: F on DIS, on a Voronoi grid and with XT3D and flow loops (Section 4.4)."""
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 2.65))
    gsp = fig.add_gridspec(1, 4, width_ratios=(1.0, 1.0, 1.0, 0.05), left=0.06, right=0.93,
                           top=0.9, bottom=0.15, wspace=0.1)
    titles = {"DIS": "(a) regular grid (DIS)", "DISV": "(b) Voronoi grid (DISV)",
              "XT3D": "(c) XT3D, rotating anisotropy"}
    for n, (label, title) in enumerate(titles.items()):
        ax = fig.add_subplot(gsp[n])
        run, step, res = data["runs"][label], data["steps"][label], data["results"][label]
        well_cells = np.flatnonzero(res.selections[WELL].cells)
        image = f_map(ax, hbd, run.grb_file, step, res.fraction_through[WELL], well_cells)
        if label in ("DIS", "DISV"):
            grid_inset(ax, hbd, run, step, res)
        else:
            centres = gs.export.cell_centres(run.grb_file)[data["loop_cells"]]
            ax.scatter(centres[:, 0], centres[:, 1], marker="s", s=10, facecolors="none",
                       edgecolors=LOOP_COLOUR, linewidths=0.8, zorder=6)
        km_axes(ax, y_label=n == 0)
        panel_title(ax, title)
    cax = fig.add_subplot(gsp[3])
    colour_bar(fig, image, cax, "F (-)")
    return mfig.save(fig, out_dir, "fig5_grids")


# ---------------------------------------------------------------- Fig. 6


def zone_legend(fig, anchor: tuple, colours: tuple = ZONE_COLOURS,
                labels: tuple = ZONE_LABELS) -> None:
    """Legend of the nested zones and the mean F line, in two columns."""
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=c, edgecolor=mfig.MUTED, lw=0.4, label=lab)
               for c, lab in zip(colours[1:][::-1], labels[1:][::-1])]
    handles.append(plt.Line2D([], [], color="black", lw=1.0, label="mean F = 0.5"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=anchor, ncol=2,
               handlelength=1.3, labelspacing=0.45, columnspacing=1.0, borderaxespad=0.0)


def make_fig6(out_dir: Path, hbd, data: dict, values: dict) -> list[Path]:
    """Fig. 6: seasonal F snapshots and the nested zones (Section 4.5)."""
    run, stats = data["run"], data["stats"]
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 3.8))
    well_cells = np.array(list(run.info["well_nodes"].values()))
    x0, y0, size, gap_x, gap_y = 0.075, 0.115, (0.203, 0.374), 0.02, 0.07
    for n, (season, (step, f)) in enumerate(data["snapshots"].items()):
        row, col = divmod(n, 2)
        box = (x0 + col * (size[0] + gap_x), y0 + (1 - row) * (size[1] + gap_y), *size)
        ax = fig.add_axes(box)
        image = f_map(ax, hbd, run.grb_file, step, f, well_cells)
        km_axes(ax, step_km=1.0, x_label=row == 1, y_label=col == 0)
        pumping = values[f"pumping {season} (m3/d)"]
        panel_title(ax, f"({'abcd'[n]}) {season}, {pumping:,.0f} m³/d")
    cax = fig.add_axes((0.525, y0, 0.012, 2 * size[1] + gap_y))
    colour_bar(fig, image, cax, "F (-)")
    ax_e = fig.add_axes((0.655, y0, 0.33, 0.608))
    classes = nested_zones(stats)
    draw_values(ax_e, run.grb_file, stats.template, classes, ListedColormap(ZONE_COLOURS),
                BoundaryNorm(np.arange(-0.5, 4.0), 4))
    f_mean = stats.stats["mean"]["fraction_through"][WELL]
    draw_contours(ax_e, run.grb_file, stats.template, f_mean, (0.5,), "black", ("-",))
    draw_features(ax_e, hbd, run.grb_file, stats.template, well_cells)
    km_axes(ax_e)
    fig.text(0.6, 2 * size[1] + gap_y + y0 + 0.005, "(e) nested zones, 36 steps",
             ha="left", va="bottom", fontweight="bold", fontsize=8)
    zone_legend(fig, (0.62, 0.9))
    return mfig.save(fig, out_dir, "fig6_seasons")


# ---------------------------------------------------------------- driver


def report(name: str, values: dict) -> None:
    """Print the computed numbers of one figure."""
    print(name + ":", {k: round(float(v), 4) for k, v in values.items()})


def main(
    out_dir: Path = mfig.FIG_DIR,
    work: Path = WORK_DIR,
    fig2: bool = True,
    fig3: bool = True,
    fig4: bool = True,
    fig5: bool = True,
    fig6: bool = True,
    quoted: dict = QUOTED,
    below: dict = BELOW,
) -> None:
    """Build the example models, assert the quoted numbers and draw Figs 2 to 6."""
    mfig.paper_style()
    hbd, helpers = import_tutorial_modules()
    mf6_exe, start = mfig.find_mf6(), time.perf_counter()
    if fig2:
        data = compute_quickstart(hbd, work, mf6_exe)
        values = quickstart_values(data)
        report("Fig. 2", values)
        check_quoted(values, quoted["fig2"])
        assert data["closure"].relative_error < below["fig2 closure"], data["closure"]
        print("wrote", make_fig2(out_dir, hbd, data))
    if fig3:
        data = compute_layered(hbd, helpers, work, mf6_exe)
        values = layered_values(data)
        report("Fig. 3", values)
        check_quoted(values, quoted["fig3"])
        assert data["fb13"]["error"] < below["fig3 worked example"], data["fb13"]["error"]
        print("wrote", make_fig3(out_dir, hbd, helpers, data))
    if fig4:
        data = compute_forward(hbd, work, mf6_exe)
        values = forward_values(data)
        report("Fig. 4", values)
        check_quoted(values, quoted["fig4"])
        print("wrote", make_fig4(out_dir, hbd, data))
    if fig5:
        data = compute_grids(hbd, work, mf6_exe)
        values = grids_values(hbd, data)
        report("Fig. 5", values)
        check_quoted(values, quoted["fig5"])
        disu = np.abs(data["results"]["DISU"].fraction_through[WELL]
                      - data["results"]["DIS"].fraction_through[WELL]).max()
        assert disu < below["fig5 DISU vs DIS"], disu
        assert data["block_vs_lu"] < below["fig5 block vs LU"], data["block_vs_lu"]
        print("wrote", make_fig5(out_dir, hbd, data))
    if fig6:
        data = compute_seasons(hbd, work, mf6_exe)
        values = seasons_values(data)
        report("Fig. 6", values)
        check_quoted(values, quoted["fig6"])
        assert values["closure (m3/d)"] < below["fig6 closure (m3/d)"], values["closure (m3/d)"]
        print("wrote", make_fig6(out_dir, hbd, data, values))
    print(f"done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
