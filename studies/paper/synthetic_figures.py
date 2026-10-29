"""Figures of Section 3 (synthetic examples): one figure per example, on the model with the
SFR stream (tutorials/herebedragons.py of branch tutorials/sfr-stream).

The example model: one unconfined layer of 40 x 40 cells of 50 m, recharge, a constant-head west
edge, an SFR stream north to south in column 31 and an 800 m3/d supply well in column 29.

- fig_example_a (Example A): F to the supply well (one column wide).
- fig_example_b (Example B, one column): (a) mean travel time to the well where F > 0.5 with
  the 5- and 25-year contours; (b) forward fraction G of the recharge on a field.
- fig_example_c (Example C, one column): F to the supply well in the model with two drains and
  a water mover, (a) with the stream as a source and sink of the aquifer cells and (b) with the
  stream reaches traced as cells.
- fig_example_d (Example D, one column): (a) the share w of each cell's water that the well
  pumps within 30 years (backward transient tracking); (b) the well's water by origin through
  30 years (forward transient tracking).

The panels reuse the drawing helpers of gallery_figure.py and example_figures.py (viridis F with
white F = 0.1 dashed and F = 0.5 solid contours, sky-blue stream cells, white well star). Every
caption number is in QUOTED and asserted (rounded half up) before plotting. Workspaces go under
$TMPDIR and are deleted at the end.

    PYTHONPATH=<sfr worktree>/src:<sfr worktree>/tutorials:studies/paper \
        python studies/paper/synthetic_figures.py
"""

import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import gallery_figure as gf  # noqa: E402
import example_figures as ef  # noqa: E402
import example_figures_b as efb  # noqa: E402
import method_figures as mfig  # noqa: E402

import gwsource as gs  # noqa: E402
import herebedragons as hbd  # noqa: E402  (the SFR version: tutorials of the sfr worktree first)
import flopy  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from flopy.mf6.utils.postprocessing import get_structured_faceflows  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

TUTORIAL_DIR = Path(hbd.__file__).resolve().parent
OUT_DIR = mfig.REPO.parents[2] / "docs" / "paper" / "overleaf" / "synthetic_2026-10-28"
WORK_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "synthetic_figures"
WELL = "supply_well"
SINGLE_WIDTH = 8.25 / 2.54  # in, one column
YEAR = 365.25  # days
EXTENT = 2000.0  # m
FULL_WIDTH = 6.75  # in
POROSITY = 0.3
N_YEARS = 30
SUBSTEPS = 4
TRACK_SOURCES = {"recharge": {"package": "RCH"}, "stream": {"package": "SFR"},
                 "west edge": {"package": "CHD"}}
FORWARD_SOURCES = {"stream": "SFR", "west edge": "CHD", "recharge": "RCH"}
PACKAGE_NAMES = {"RCH": "recharge", "CHD": "west edge", "SFR": "stream"}
CUMULATIVE_YEARS = (1, 10, 30)
OKABE_ITO = mfig.OKABE_ITO
INITIAL_COLOUR = "#7f7f7f"  # initial (stored) water, as a line
COLOURS = {"recharge": OKABE_ITO["blue"], "west edge": OKABE_ITO["vermillion"],
           "stream": OKABE_ITO["sky"], "initial": INITIAL_COLOUR}
ZONE_LABEL_XY = {5: (1170.0, 1000.0), 25: (860.0, 1000.0)}  # m, inline labels of the contours
DRAIN_MARK = dict(marker="s", s=42, facecolor="none", linewidths=1.6)
EXAMPLE_C_DRAINS = (  # (boundname, (row, col), elevation [m], conductance [m2/d]); in this order the
    ("drain_b", (22, 14), 6.0, 50.0), ("drain_a", (32, 14), 3.0, 200.0))  # mover passes 80 % and 100 %
FLOW_ARROW = dict(color=OKABE_ITO["orange"], width=0.005, scale=30, pivot="middle", zorder=3)
NETWORK_COLOUR = "#d7191c"  # red drains of Fig. C, apart from the orange flow arrows

# Caption numbers: {name: (value, decimals)}; the computed value must round half up to the value.
QUOTED = {
    # model and budget (m3/d)
    "recharge in (m3/d)": (1950.0, 1), "west edge in (m3/d)": (338.0, 1),
    "stream leakage in (m3/d)": (111.7, 1), "stream leakage out (m3/d)": (1599.7, 1),
    "F in the supply-well cell": (1.000, 3),
    # Example A, base model
    "A cells F > 0.1": (616, 0), "A area F > 0.1 (km2)": (1.540, 3),
    "A cells F > 0.5": (459, 0), "A area F > 0.5 (km2)": (1.148, 3),
    "A recharge (m3/d)": (565.9, 1), "A west edge (m3/d)": (122.4, 1),
    "A stream (m3/d)": (111.7, 1),
    "A recharge (%)": (70.7, 1), "A west edge (%)": (15.3, 1), "A stream (%)": (14.0, 1),
    # Example D
    "snapshot mean recharge": (0.59, 2), "snapshot mean stream": (0.13, 2),
    "snapshot mean west edge": (0.12, 2), "snapshot mean storage": (0.15, 2),
    "transient steps": (121, 0),
    "cumulative initial, year 1": (0.976, 3), "cumulative initial, year 10": (0.814, 3),
    "cumulative initial, year 30": (0.678, 3),
    "year 30 initial": (0.517, 3), "year 30 recharge": (0.330, 3),
    "year 30 stream": (0.153, 3), "year 30 west edge": (0.0, 3),
    "backward initial": (0.678, 3), "backward recharge": (0.185, 3),
    "backward stream": (0.136, 3),
    # Example B
    "field cells": (36, 0), "field recharge (m3/d)": (45.0, 1),
    "field to well (m3/d)": (18.9, 1), "field to well (%)": (42, 0),
    "field to stream (m3/d)": (26.1, 1), "field to stream (%)": (58, 0),
    "field share of the well's water (%)": (2.4, 1),
    "mean time, all water (yr)": (45.7, 1), "mean time, recharge (yr)": (41.2, 1),
    "mean time, west edge (yr)": (106.1, 1), "mean time, stream (yr)": (2.2, 1),
    "zone 5 yr (km2)": (0.098, 3), "zone 25 yr (km2)": (0.448, 3),
    "mover routed (m3/d)": (700.3, 1),
    "F drain_a cell": (0.106, 3), "F drain_b cell": (0.109, 3),
    "largest F increase from tracing the reaches": (0.11, 2),
    "cells with F increase > 0.01": (982, 0),
    "area F > 0.1, reaches not traced (km2)": (1.5525, 4),
    "area F > 0.1, reaches traced (km2)": (3.03, 2),
    "cells only recharge (m3/d)": (512.7, 1), "cells only west edge (m3/d)": (135.2, 1),
    "cells only stream (m3/d)": (152.0, 1),
    "cells only recharge (%)": (64.1, 1), "cells only west edge (%)": (16.9, 1),
    "cells only stream (%)": (19.0, 1),
    "reaches recharge (m3/d)": (611.6, 1), "reaches west edge (m3/d)": (188.4, 1),
    "reaches stream (m3/d)": (0.0, 1),
    "reaches recharge (%)": (76.5, 1), "reaches west edge (%)": (23.5, 1),
    "through the mover (m3/d)": (74.0, 1), "through the mover (%)": (9.3, 1),
}
BELOW = {  # upper bounds stated in words
    "A closure": 1e-12, "forward-backward difference": 1e-12,
    "drain closure": 1e-8,
}


# ---------------------------------------------------------------- shared


def clean_dir(path: Path) -> Path:
    """Remove and recreate a workspace folder."""
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def km2(area_m2: float) -> float:
    """Return an area in km2."""
    return area_m2 / 1e6


def map_layer(grb_file: Path, step: gs.FlowStep, values: np.ndarray, well_cells) -> dict:
    """Return what a map panel draws: grid file, step, values, stream and well cells."""
    return {"grb": grb_file, "step": step, "values": values,
            "river": hbd.feature_cells(step, "SFR"), "well": np.atleast_1d(well_cells)}


def package_in_out(step: gs.FlowStep, package: str) -> tuple[float, float]:
    """Return a package's total inflow to and outflow from the cells (m3/d)."""
    q = step.term_flow[step.term_package == step.package_names.index(package)]
    return float(q[q > 0].sum()), float(-q[q < 0].sum())


def by_source(res: gs.BackwardResult, well: str = WELL,
              names: dict = PACKAGE_NAMES) -> pd.Series:
    """Return the well's water by source package (m3/d), named, zero for absent sources."""
    volumes = {k: float(v.sum()) for k, v in res.volume_from_by_term[well].items()}
    return pd.Series({name: volumes.get(p, 0.0) for p, name in names.items()})


# ---------------------------------------------------------------- Example A


def compute_example_a(work: Path, mf6: Path) -> dict:
    """Example model: F to the supply well."""
    run = hbd.build_quickstart(work / "base", mf6)
    step = gs.read_step(run.ws, boundnames=True)
    selection = gs.select(step, boundnames=[WELL])
    res = gs.backward(step, {WELL: selection})
    return {"grb": run.grb_file, "step": step, "res": res,
            "well_cell": int(np.flatnonzero(selection.cells)[0]),
            "closure": gs.diagnostics.backward_closure(step, res, WELL)}


def example_a_values(data: dict) -> dict:
    """Return the Example A numbers."""
    step, f = data["step"], data["res"].fraction_through[WELL]
    volumes = by_source(data["res"])
    values = {"F in the supply-well cell": float(f[data["well_cell"]])}
    for package, name in (("RCH", "recharge"), ("CHD", "west edge")):
        values[f"{name} in (m3/d)"] = package_in_out(step, package)[0]
    values["stream leakage in (m3/d)"], values["stream leakage out (m3/d)"] = \
        package_in_out(step, "SFR")
    for t in ef.THRESHOLDS:
        values[f"A cells F > {t}"] = int((f > t).sum())
        values[f"A area F > {t} (km2)"] = km2(step.area[f > t].sum())
    for name, volume in volumes.items():
        values[f"A {name} (m3/d)"] = volume
        values[f"A {name} (%)"] = 100.0 * volume / volumes.sum()
    values["A closure"] = data["closure"].relative_error
    return values


# ---------------------------------------------------------------- Example D


def cumulative_initial(fwd: gs.ForwardTracking, well: str = WELL) -> pd.Series:
    """Return the initial water's share of all water the well has pumped up to each step."""
    cumulative = pd.DataFrame({g: fwd.outflow_to[well][g] for g in fwd.groups}).cumsum()
    share = cumulative["initial"] / cumulative.sum(axis=1)
    share.index = pd.Index(fwd.totim / YEAR, name="time (yr)")
    return share


def mean_snapshot(summary: pd.DataFrame) -> pd.Series:
    """Return the snapshot shares averaged over the transient steps, weighted by step length."""
    columns = {"snapshot RCH": "recharge", "snapshot SFR": "stream",
               "snapshot CHD": "west edge", "snapshot storage": "storage"}
    weights = summary["delt (d)"].iloc[1:].to_numpy()
    return pd.Series({name: np.average(summary[c].iloc[1:], weights=weights)
                      for c, name in columns.items()})


def compute_transient(work: Path, mf6: Path, h08, n_years: int = N_YEARS,
                      porosity: float = POROSITY, substeps: int = SUBSTEPS) -> dict:
    """30-year seasonal model tracked forward and backward with the initial water tagged."""
    run = hbd.build_transient(work / "transient", mf6, n_years=n_years, steps_per_season=1)
    reader = gs.open_model(run.ws, boundnames=True)
    destinations = {WELL: {"boundnames": [WELL]}}
    config = gs.TrackingConfig(porosity=porosity, initial_water={"initial": "all"},
                               substeps=substeps)
    fwd = gs.track_forward(reader, TRACK_SOURCES, config, sinks=destinations)
    bwd = gs.track_backward(reader, destinations, config, sources=TRACK_SOURCES)
    first = reader.read(reader.steps[0])
    split = {p: float(v.sum()) for p, v in bwd.volume_from_by_package[WELL].items()}
    split["initial"] = float(bwd.initial_volume_from[WELL].sum())
    duality = max(gs.tracking.tracking_duality(fwd, g, bwd, WELL).relative_error
                  for g in [*TRACK_SOURCES, "initial"])
    return {**map_layer(run.grb_file, first, bwd.fraction_through[WELL][0],
                        run.info["well_nodes"][WELL]),
            "origin": h08.origin_shares(fwd, WELL)[["initial", "recharge", "stream",
                                                    "west edge"]],
            "cumulative": cumulative_initial(fwd),
            "year_steps": h08.year_steps(fwd.totim, CUMULATIVE_YEARS),
            "n_steps": len(fwd.steps), "split": split,
            "duality": duality, "snapshot_mean": mean_snapshot(h08.step_summary(reader, WELL))}


def example_d_values(transient: dict) -> dict:
    """Return the Example D numbers."""
    values = {"transient steps": transient["n_steps"]}
    for name, share in transient["snapshot_mean"].items():
        values[f"snapshot mean {name}"] = float(share)
    steps = transient["year_steps"]
    for year, n in zip(CUMULATIVE_YEARS, steps):
        values[f"cumulative initial, year {year}"] = float(transient["cumulative"].iloc[n])
    for name, share in transient["origin"].iloc[steps[-1]].items():
        values[f"year 30 {name}"] = float(share)
    split = transient["split"]
    total = sum(split.values())
    for key, name in (("initial", "initial"), ("RCH", "recharge"), ("SFR", "stream")):
        values[f"backward {name}"] = split.get(key, 0.0) / total
    values["forward-backward difference"] = transient["duality"]
    return values


# ---------------------------------------------------------------- Example B


def compute_forward(work: Path, mf6: Path) -> dict:
    """Forward fraction G of the recharge on the field."""
    run = hbd.build_quickstart(work / "forward", mf6)
    spec = run.spec
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=[WELL])
    zones = np.zeros((spec.nrow, spec.ncol), dtype=int)
    zones[slice(*ef.FIELD_ROWS), slice(*ef.FIELD_COLS)] = 1
    field = gs.select_zone(step, zones, 1, package="RCH")
    fwd = gs.forward(step, {"field": field})
    return {**map_layer(run.grb_file, step, fwd.source_fraction["field"],
                        np.flatnonzero(well.cells)),
            "spec": spec, "field": field, "fwd": fwd}


def compute_travel_time(work: Path, mf6: Path, h06, porosity: float = POROSITY) -> dict:
    """Mean travel time to the well inside F > 0.5, and the mean times by source."""
    run = hbd.build_quickstart(work / "travel_time", mf6)
    step = gs.read_step(run.ws, boundnames=True)
    well = gs.select(step, boundnames=[WELL])
    res = gs.backward(step, {WELL: well})
    tt = gs.travel_time(step, res, porosity)
    f = res.fraction_through[WELL]
    years = np.where(f > efb.CAPTURE_F, tt.mean_time[WELL], np.nan) / YEAR
    return {**map_layer(run.grb_file, step, years, np.flatnonzero(well.cells)),
            "tt": tt, "f": f, "means": h06.eulerian_means(step, res, tt, WELL),
            "zone_area": h06.zone_area}


def flow_directions(ws: Path, grb_file: Path) -> tuple[np.ndarray, np.ndarray]:
    """Cell-centred groundwater flow (x east, y north, m3/d) of a one-layer DIS model."""
    budget = flopy.utils.CellBudgetFile(next(Path(ws).glob("*.cbc")), precision="double")
    right, front, _ = get_structured_faceflows(budget.get_data(text="FLOW-JA-FACE")[0][0][0],
                                               grb_file=str(grb_file))
    right, front = right[0], front[0]  # front: towards the next row (south)
    qx = 0.5 * (right + np.pad(right, ((0, 0), (1, 0)))[:, :-1])
    qy = -0.5 * (front + np.pad(front, ((1, 0), (0, 0)))[:-1, :])
    return qx, qy


def compute_drains(work: Path, mf6: Path, h07) -> dict:
    """Drains and mover model traced on the cells only and with the stream reaches as nodes."""
    stream = hbd.build_stream_mover(work / "drains", mf6, drains=EXAMPLE_C_DRAINS)
    cells_only = gs.read_step(stream.ws, boundnames=True)
    back_off = gs.backward(cells_only, {WELL: gs.select(cells_only, boundnames=[WELL])})
    network = gs.open_simulation(stream.ws, package_nodes=("SFR",), boundnames=True).read((0, 0))
    back_on = gs.backward(network, {WELL: gs.select(network, boundnames=[WELL])})
    reaches = network.block("SFR").nodes
    mover = h07.edges_between(network, list(stream.info["drain_nodes"].values()), reaches)
    f_on = back_on.fraction_through[WELL]
    closure = max(gs.diagnostics.backward_closure(s, r, WELL).relative_error
                  for s, r in ((cells_only, back_off), (network, back_on)))
    n_cells = cells_only.n_cells
    f_off = back_off.fraction_through[WELL]
    qx, qy = flow_directions(stream.ws, stream.grb_file)
    return {"f_off": f_off, "gain": f_on[:n_cells] - f_off,"cells only": by_source(back_off), "reaches": by_source(back_on),
            "via mover": float((mover["q"] * f_on[mover["dst"]]).sum()),
            "routed": network.notes["mover_routed"], "closure": closure, "qx": qx, "qy": qy,
            "drain_nodes": stream.info["drain_nodes"],
            **map_layer(stream.grb_file, cells_only, f_on[:n_cells],
                        stream.info["well_nodes"][WELL])}


def example_b_values(fate: dict, travel: dict) -> dict:
    """Return the Example B numbers."""
    fwd, step = fate["fwd"], fate["step"]
    field_in = fwd.source_inflow["field"]
    to_well = float(fwd.volume_to_by_term["field"]["WEL"].sum())
    to_stream = float(fwd.volume_to_by_term["field"]["SFR"].sum())
    values = {"field cells": int(fate["field"].terms.sum()), "field recharge (m3/d)": field_in,
              "field to well (m3/d)": to_well, "field to well (%)": 100.0 * to_well / field_in,
              "field to stream (m3/d)": to_stream,
              "field to stream (%)": 100.0 * to_stream / field_in,
              "field share of the well's water (%)":
                  100.0 * float(fate["values"][fate["well"][0]])}
    means = travel["means"]
    for key, name in (("all sources", "all water"), ("RCH", "recharge"), ("CHD", "west edge"),
                      ("SFR", "stream")):
        values[f"mean time, {name} (yr)"] = means[key]["to the well"] / YEAR
    tt = travel["tt"]
    for years in efb.ZONE_YEARS:
        values[f"zone {years} yr (km2)"] = km2(travel["zone_area"](
            travel["step"].area, tt.mean_time[WELL], travel["f"], years * YEAR))
    return values


def example_c_values(drains: dict) -> dict:
    """Return the Example C numbers (drains, water mover and stream reaches as nodes)."""
    values = {"mover routed (m3/d)": drains["routed"]}
    for name, node in drains["drain_nodes"].items():
        values[f"F {name} cell"] = float(drains["values"][node])
    gain, area = drains["gain"], drains["step"].area
    values["largest F increase from tracing the reaches"] = float(gain.max())
    values["cells with F increase > 0.01"] = int((gain > 0.01).sum())
    values["area F > 0.1, reaches not traced (km2)"] = km2(area[drains["f_off"] > 0.1].sum())
    values["area F > 0.1, reaches traced (km2)"] = km2(area[drains["values"] > 0.1].sum())
    for label, key in (("cells only", "cells only"), ("reaches", "reaches")):
        series = drains[key]
        for name, volume in series.items():
            values[f"{label} {name} (m3/d)"] = volume
            values[f"{label} {name} (%)"] = 100.0 * volume / series.sum()
    values["through the mover (m3/d)"] = drains["via mover"]
    values["through the mover (%)"] = 100.0 * drains["via mover"] / drains["reaches"].sum()
    values["drain closure"] = drains["closure"]
    return values


# ---------------------------------------------------------------- checks


def check_quoted(computed: dict, quoted: dict = QUOTED, below: dict = BELOW) -> None:
    """Assert every quoted number (rounded half up) and every stated upper bound."""
    for name, (value, decimals) in quoted.items():
        got = computed[name]
        assert abs(ef.round_half_up(got, decimals) - value) < 1e-9, \
            f"{name}: computed {got}, quoted {value}"
    for name, bound in below.items():
        assert computed[name] < bound, f"{name}: computed {computed[name]}, bound {bound}"
    print(f"synthetic figures: {len(quoted)} quoted numbers and {len(below)} bounds match")


# ---------------------------------------------------------------- drawing


def panel_letter(ax, letter: str, colour: str = "black") -> None:
    """Bold panel letter at the top left, above the axes."""
    ax.text(0.0, 1.02, f"({letter})", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8, fontweight="bold", color=colour)


def panel_title(ax, letter: str, title: str) -> None:
    """Bold panel letter with a short title after it, above the axes."""
    panel_letter(ax, letter)
    ax.annotate(title, xy=(0.0, 1.02), xycoords="axes fraction", xytext=(18, 0),
                textcoords="offset points", ha="left", va="bottom", fontsize=7)


def axes_in(fig, size: tuple, box: tuple):
    """Add axes placed in inches (x0, y0, w, h) on a figure of the given size."""
    w, h = size
    return fig.add_axes((box[0] / w, box[1] / h, box[2] / w, box[3] / h))


def colour_bar(fig, image, cax, label: str, ticks: tuple) -> None:
    """Slim vertical colour bar with a label."""
    bar = fig.colorbar(image, cax=cax, ticks=ticks)
    bar.set_label(label, labelpad=2)
    bar.outline.set_linewidth(0.5)
    bar.ax.tick_params(labelsize=7, length=2, pad=1)


def f_panel(ax, layer: dict):
    """F map (viridis 0 to 1) with its contours, the stream and the wells."""
    image = gf.draw_layer(ax, layer, ef.F_CMAP, Normalize(0.0, 1.0))
    ef.draw_f_contours(ax, layer["grb"], layer["step"], layer["values"])
    return image


def make_example_a(data: dict, out_dir: Path, height: float = 2.6) -> list[Path]:
    """Fig. A: F of the supply well, one column wide."""
    size = (SINGLE_WIDTH, height)
    bottom, top, left = 0.4, 0.1, 0.4
    side = height - bottom - top
    assert left + side + 0.65 <= SINGLE_WIDTH, "no room for the colour bar"
    fig = plt.figure(figsize=size)
    ax = axes_in(fig, size, (left, bottom, side, side))
    cax = axes_in(fig, size, (left + side + 0.1, bottom, 0.1, side))
    image = f_panel(ax, map_layer(data["grb"], data["step"],
                                  data["res"].fraction_through[WELL], data["well_cell"]))
    gf.map_axes(ax, left=True, bottom=True)
    colour_bar(fig, image, cax, "F (-)", (0.0, 0.25, 0.5, 0.75, 1.0))
    return mfig.save(fig, out_dir, "fig_example_a")


def draw_origin(ax, transient: dict) -> None:
    """Fig. D (b): the well's water by origin through 30 years."""
    origin = transient["origin"]
    labels = {"initial": "initial water", "recharge": "recharge", "stream": "stream",
              "west edge": "west boundary"}
    for name in ("initial", "recharge", "stream", "west edge"):  # legend top to bottom, as the curves
        ax.plot(origin.index, origin[name], color=COLOURS[name], lw=1.2, label=labels[name])
    ax.legend(loc="upper right", fontsize=7, frameon=False, handlelength=2.0, labelspacing=0.3)
    ax.set_xlim(0.0, N_YEARS)
    ax.set_ylim(-0.03, 1.0)  # below 0 so the west-boundary line at 0 shows
    ax.set_xticks((0, 10, 20, 30))
    ax.set_yticks((0.0, 0.25, 0.5, 0.75, 1.0))
    ax.set_xlabel("time (years)", labelpad=1)
    ax.set_ylabel("share (-)", labelpad=2)


def make_example_d(transient: dict, out_dir: Path, height: float = 5.0) -> list[Path]:
    """Fig. B, one column wide: w within 30 years (a) above the well's water by origin (b)."""
    size = (SINGLE_WIDTH, height)
    left, side = 0.5, 2.05
    assert left + side + 0.65 <= SINGLE_WIDTH, "no room for the colour bar"
    chart_bottom, chart_h, gap = 0.38, 1.75, 0.55
    map_bottom = chart_bottom + chart_h + gap
    assert map_bottom + side + 0.2 <= height, "panels do not fit"
    fig = plt.figure(figsize=size)
    ax_a = axes_in(fig, size, (left, map_bottom, side, side))
    cax = axes_in(fig, size, (left + side + 0.1, map_bottom, 0.1, side))
    ax_b = axes_in(fig, size, (left, chart_bottom, SINGLE_WIDTH - left - 0.1, chart_h))
    image = f_panel(ax_a, transient)
    gf.map_axes(ax_a, left=True, bottom=True)
    colour_bar(fig, image, cax, "w (-)", (0.0, 0.25, 0.5, 0.75, 1.0))
    draw_origin(ax_b, transient)
    titles = ("initial water pumped within 30 years", "the well's water by origin")
    for ax, letter, title in zip((ax_a, ax_b), "ab", titles):
        panel_title(ax, letter, title)
    return mfig.save(fig, out_dir, "fig_example_d")


def make_example_b(travel: dict, fate: dict, out_dir: Path, height: float = 5.3) -> list[Path]:
    """Fig. B, one column wide: mean travel time inside F > 0.5 (a) above G of the field (b)."""
    size = (SINGLE_WIDTH, height)
    left, side, gap, bottom, bar = 0.42, 2.2, 0.3, 0.38, 0.08
    assert left + side + 0.08 + bar + 0.45 <= SINGLE_WIDTH, "no room for the colour bars"
    bottom_a = bottom + side + gap
    assert bottom_a + side + 0.2 <= height, "maps do not fit"
    fig = plt.figure(figsize=size)
    ax_a = axes_in(fig, size, (left, bottom_a, side, side))
    ax_b = axes_in(fig, size, (left, bottom, side, side))
    images = (gf.draw_travel_time(fig, ax_a, travel, label_xy=ZONE_LABEL_XY, note_xy={},
                                  inset=False),
              gf.draw_fate(fig, ax_b, fate, inset=False))
    bars = (("travel time (years)", (0.1, 1.0, 10.0, 100.0), ("0.1", "1", "10", "100")),
            ("G (-)", (1e-3, 1e-2, 1e-1, 1.0), ("0.001", "0.01", "0.1", "1")))
    titles = ("mean travel time to the well", "where the field's recharge goes")
    for ax, base, letter, title, image, (label, ticks, tick_labels) in zip(
            (ax_a, ax_b), (bottom_a, bottom), "ab", titles, images, bars):
        gf.map_axes(ax, left=True, bottom=ax is ax_b)
        panel_title(ax, letter, title)
        cax = axes_in(fig, size, (left + side + 0.08, base, bar, side))
        colour_bar(fig, image, cax, label, ticks)
        cax.set_yticklabels(tick_labels)
        cax.minorticks_off()
    return mfig.save(fig, out_dir, "fig_example_b")


def cell_xy(node: int, ncol: int = 40, delr: float = 50.0, extent: float = EXTENT) -> tuple:
    """Return the model (x, y) of the centre of a one-layer DIS node (row 0 at the north)."""
    row, col = divmod(node, ncol)
    return (col + 0.5) * delr, extent - (row + 0.5) * delr


def draw_network(ax, drains: dict, colour: str) -> None:
    """Fig. C: drains (open squares)."""
    xy = np.array([cell_xy(n) for n in drains["drain_nodes"].values()])
    ax.scatter(xy[:, 0], xy[:, 1], zorder=4, edgecolor=colour, **DRAIN_MARK)


def draw_flow_arrows(ax, drains: dict, every: int = 3, ncol: int = 40, delr: float = 50.0) -> None:
    """Fig. C: groundwater flow direction (arrows of one length) on every few cells."""
    qx, qy = drains["qx"], drains["qy"]
    rows = cols = slice(every // 2, ncol, every)
    centres = (np.arange(ncol) + 0.5) * delr
    x, y = np.meshgrid(centres, EXTENT - centres)
    speed = np.hypot(qx, qy)
    ax.quiver(x[rows, cols], y[rows, cols], (qx / speed)[rows, cols], (qy / speed)[rows, cols],
              **FLOW_ARROW)


def make_example_c(drains: dict, out_dir: Path, height: float = 5.5) -> list[Path]:
    """Fig. C, one column wide: F with the stream as a plain source (a) and routed (b)."""
    size = (SINGLE_WIDTH, height)
    left, side, gap, bottom, bar = 0.42, 2.3, 0.3, 0.38, 0.08
    assert left + side + 0.08 + bar + 0.35 <= SINGLE_WIDTH, "no room for the colour bars"
    bottom_a = bottom + side + gap
    assert bottom_a + side + 0.2 <= height, "maps do not fit"
    fig = plt.figure(figsize=size)
    titles = ("stream as a source", "routed through the mover and stream")
    for base, letter, title, values in zip((bottom_a, bottom), "ab", titles,
                                           (drains["f_off"], drains["values"])):
        ax = axes_in(fig, size, (left, base, side, side))
        image = f_panel(ax, {**drains, "values": values})
        draw_flow_arrows(ax, drains)
        draw_network(ax, drains, NETWORK_COLOUR)
        gf.map_axes(ax, left=True, bottom=base == bottom)
        panel_title(ax, letter, title)
        cax = axes_in(fig, size, (left + side + 0.08, base, bar, side))
        colour_bar(fig, image, cax, "F (-)", (0.0, 0.5, 1.0))
    return mfig.save(fig, out_dir, "fig_example_c")


# ---------------------------------------------------------------- driver


def main(out_dir: Path = OUT_DIR, work: Path = WORK_DIR, keep_work: bool = False) -> None:
    """Build and trace every model, assert the caption numbers and draw the figures of Examples A to D."""
    mfig.paper_style()
    start = time.perf_counter()
    mf6 = mfig.find_mf6()
    clean_dir(work)
    _, h06 = efb.tutorial_modules("06_travel_time", TUTORIAL_DIR)
    _, h07 = efb.tutorial_modules("07_networks_multimodel", TUTORIAL_DIR)
    _, h08 = efb.tutorial_modules("08_transient_tracking", TUTORIAL_DIR)
    data_a = compute_example_a(work, mf6)
    values = example_a_values(data_a)
    transient = compute_transient(work, mf6, h08)
    values.update(example_d_values(transient))
    fate = compute_forward(work, mf6)
    travel = compute_travel_time(work, mf6, h06)
    drains = compute_drains(work, mf6, h07)
    values.update(example_b_values(fate, travel))
    values.update(example_c_values(drains))
    for name, value in values.items():
        print(f"  {name}: {value}")
    check_quoted(values)
    print("wrote", make_example_a(data_a, out_dir))
    print("wrote", make_example_b(travel, fate, out_dir))
    print("wrote", make_example_c(drains, out_dir))
    print("wrote", make_example_d(transient, out_dir))
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
