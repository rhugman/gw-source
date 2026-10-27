"""Model builder, tables and plots local to tutorial 10 (the unit-concentration method).

Bedekar et al. (2024) demonstrate the unit-concentration method on a synthetic MODFLOW-2005 /
MT3D-USGS model. build_bedekar() rebuilds it in MODFLOW 6 with FloPy: 101 x 101 cells of 10 m,
three layers of 10 m (top 30 m), lateral inflow injected by wells along the west edge of every
layer, recharge on layer 1, a stream (RIV, stage 30 m) along the east edge of every layer and a
pumping well 150 m west of the stream on the centre row, in layer 2. Period 1 is a 1-day steady
state without pumping; period 2 pumps 700 m3/d for 25 years. Every time step is saved, as
transient tracking needs. Values the paper does not give are arguments with documented defaults.

The shared helpers (simulation set-up, GWT unit-tracer runs, maps) live in
tutorials/herebedragons.py.
"""

from dataclasses import dataclass
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import herebedragons as hbd  # tutorials/ is on sys.path (the notebook's first cell)

import gwsource as gs

DAYS_PER_YEAR = 365.25
WELL = "pumping_well"
# Plan geometry and stresses of the published model. The stream is a RIV bound in every cell
# of the east column (stage, conductance per cell); east_stream() puts its bottom at the bottom
# of its cell.
SPEC = hbd.AquiferSpec(
    nrow=101, ncol=101, delr=10.0, delc=10.0, top=30.0, botm=0.0, k=10.0, strt=30.0,
    rech=3.0e-4, wells=((WELL, (50, 85), -700.0),),
)
LAYER_BOTM = (20.0, 10.0, 0.0)
STREAM_COL, STREAM_STAGE, STREAM_COND = 100, 30.0, 1000.0  # -, m, m2/d


@dataclass
class StepWindow:
    """The first steps of a StepReader, read as if the simulation ended there.

    Transient tracking reads only steps, read() and step_length(); a window ending at year 5
    gives backward fractions 'reaches the well within 5 years'.
    """

    reader: gs.StepReader
    steps: list[tuple[int, int]]

    def read(self, kstpkper: tuple[int, int]) -> gs.FlowStep:
        """Read one step of the underlying reader."""
        return self.reader.read(kstpkper)

    def step_length(self, kstpkper: tuple[int, int]) -> float:
        """Return the length of one step of the underlying reader."""
        return self.reader.step_length(kstpkper)


# ---------------------------------------------------------------- model


def bedekar_periods(n_years: float, nstp: int, tsmult: float) -> list[tuple[float, int, float]]:
    """Return TDIS periods: a 1-day steady state, then the pumping period."""
    return [(1.0, 1, 1.0), (n_years * DAYS_PER_YEAR, nstp, tsmult)]


def west_inflow(spec: hbd.AquiferSpec, nlay: int, rate: float) -> list:
    """Return WEL records injecting rate [m3/d] into every cell of the west column."""
    return [((lay, row, 0), rate) for lay in range(nlay) for row in range(spec.nrow)]


def east_stream(
    spec: hbd.AquiferSpec,
    botm: tuple[float, ...],
    col: int = STREAM_COL,
    stage: float = STREAM_STAGE,
    cond: float = STREAM_COND,
) -> list:
    """Return RIV records along the east column of every layer (bottom = cell bottom)."""
    return [
        ((lay, row, col), stage, cond, botm[lay], "stream")
        for lay in range(len(botm)) for row in range(spec.nrow)
    ]


def build_bedekar(
    ws: Path,
    exe: Path,
    spec: hbd.AquiferSpec = SPEC,
    botm: tuple[float, ...] = LAYER_BOTM,
    kv: float = 1.0,
    ss: float = 1.0e-5,
    sy: float = 0.1,
    inflow_rate: float = 1.5,
    well_layer: int = 1,
    n_years: float = 25.0,
    nstp: int = 300,
    tsmult: float = 1.0,
) -> hbd.ModelRun:
    """Build and run the Bedekar et al. (2024) demonstration model in MF6; return a ModelRun.

    spec.k is the horizontal and kv the vertical conductivity [m/d]. Every layer is convertible
    (ICELLTYPE 1, ICONVERT 1). The well (boundname 'pumping_well') pumps from period 2 on.
    """
    name = "bedekar"
    periods = bedekar_periods(n_years, nstp, tsmult)
    sim, gwf = hbd.make_sim(name, ws, exe, periods)
    dis_filename = hbd.add_dis(gwf, spec, name, botm=botm)
    hbd.add_npf_ic_oc(gwf, name, k=spec.k, icelltype=1, strt=spec.strt, k33=kv)
    flopy.mf6.ModflowGwfsto(
        gwf, iconvert=1, ss=ss, sy=sy, steady_state={0: True}, transient={1: True},
        save_flows=True,
    )
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={0: west_inflow(spec, len(botm), inflow_rate)},
        save_flows=True, pname="inflow", filename=f"{name}.inflow.wel",
    )
    flopy.mf6.ModflowGwfriv(
        gwf, stress_period_data={0: east_stream(spec, botm)}, boundnames=True,
        save_flows=True, pname="riv",
    )
    rch = [((0, row, col), spec.rech) for row, col in hbd.all_cells(spec)]
    flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: rch}, save_flows=True, pname="rch")
    pump = [((well_layer, *rc), rate, bname) for bname, rc, rate in spec.wells]
    flopy.mf6.ModflowGwfwel(
        gwf, stress_period_data={1: pump}, boundnames=True, save_flows=True, pname="pump",
        filename=f"{name}.pump.wel",
    )
    info = {
        "well_node": spec.node(spec.wells[0][1], well_layer),
        "well_layer": well_layer,
        "periods": periods,
        "sy": sy,
    }
    return hbd.run_model(sim, gwf, name, ws, dis_filename, spec, info)


# ---------------------------------------------------------------- GWT


def gwt_all_cells(ucn_file: Path, steps: list) -> np.ndarray:
    """Return the GWT concentration of every cell at the end of every step (steps x cells)."""
    ucn = flopy.utils.HeadFile(str(ucn_file), text="CONCENTRATION")
    return np.array([np.asarray(ucn.get_data(kstpkper=ks), float).ravel() for ks in steps])


# ---------------------------------------------------------------- steps and tables


def step_end_times(reader: gs.StepReader) -> np.ndarray:
    """Return the simulation time [d] at the end of every saved step."""
    return np.cumsum([reader.step_length(k) for k in reader.steps])


def window(reader: gs.StepReader, end_time: float) -> StepWindow:
    """Return the steps that end by end_time [d] as a StepWindow."""
    ends = step_end_times(reader)
    n = int(np.searchsorted(ends, end_time * (1.0 + 1e-9), side="right"))
    assert n > 0, f"no step ends by {end_time} d"
    return StepWindow(reader=reader, steps=list(reader.steps)[:n])


def sink_volumes(reader, boundname: str) -> np.ndarray:
    """Return the volume [m3] leaving through the terms of a boundname in every step."""
    volumes = []
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        rate = -float(step.term_flow[gs.select(step, boundnames=[boundname]).terms].sum())
        volumes.append(rate * reader.step_length(kstpkper))
    return np.array(volumes)


def well_shares(
    outflow: dict[str, np.ndarray], pumped: np.ndarray, totim: np.ndarray, start: float
) -> pd.DataFrame:
    """Return each group's tagged outflow over the pumped volume, per step with pumping.

    outflow: {group: tagged volume per step}; the index is the time since start [years].
    """
    keep = pumped > 0.0
    out = pd.DataFrame({g: np.asarray(v)[keep] / pumped[keep] for g, v in outflow.items()})
    out.index = pd.Index((totim[keep] - start) / DAYS_PER_YEAR, name="time (yr)")
    return out


def series_at_years(series: pd.DataFrame, years) -> pd.DataFrame:
    """Return the rows of a time-indexed table closest to the given times in years."""
    t = series.index.to_numpy()
    rows = [int(np.argmin(np.abs(t - y))) for y in years]
    out = series.iloc[rows].copy()
    out.index = pd.Index(list(years), name="time (yr)")
    return out


def package_budget(step: gs.FlowStep) -> pd.DataFrame:
    """Return the inflow and outflow [m3/d] of every package of one step."""
    rows = {}
    for index, package in enumerate(step.packages):
        q = step.term_flow[step.term_package == index]
        rows[package.name] = {"in": float(q[q > 0.0].sum()), "out": -float(q[q < 0.0].sum())}
    return pd.DataFrame(rows).T.rename_axis("package")


def steady_shares(step: gs.FlowStep, well: str, names: dict[str, str]) -> pd.Series:
    """Return the well's shares from a steady backward trace of one step, by names[package]."""
    res = gs.backward(step, {well: gs.select(step, boundnames=[well])})
    shares = hbd.volume_from_table(res, well)["share"]
    return shares.groupby(lambda package: names.get(package, package)).sum()


def layer_sum(values: np.ndarray, nlay: int) -> np.ndarray:
    """Return per-node values with the column sums over all layers in layer 1, 0 below."""
    ncpl = values.size // nlay
    out = np.zeros_like(values, dtype=float)
    out[:ncpl] = np.asarray(values, float).reshape(nlay, ncpl).sum(axis=0)
    return out


# ---------------------------------------------------------------- plots


def plot_well_series(ax, ours: pd.DataFrame, gwt: pd.DataFrame, colours: dict) -> None:
    """Plot our shares (thin lines) over the GWT concentrations (wide pale lines)."""
    for group in ours.columns:
        colour = colours.get(group, "0.4")
        ax.plot(gwt.index, gwt[group], color=colour, lw=6.0, alpha=0.3)
        ax.plot(ours.index, ours[group], color=colour, lw=1.4, label=group)
    ax.set_xlim(0.0, float(ours.index.max()))
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("time since pumping started (years)")
    ax.set_ylabel("share of the pumped water (-)")


def mark_well(ax, grb_file: Path, step: gs.FlowStep, well_node: int, layer: int) -> None:
    """Mark the stream cells of one layer and the well (a star) on a map."""
    hbd.overlay_features(ax, grb_file, step, packages=("RIV",), layer=layer, legend=False)
    x, y = gs.export.cell_centres(grb_file)[well_node]
    ax.scatter([x], [y], zorder=6, **hbd.FEATURE_STYLES["WEL"])


def map_panels(
    grb_file: Path, step: gs.FlowStep, panels: list, well_node: int, label: str = "", **kwargs
):
    """Map several (values, layer, title) panels side by side with one shared colour bar."""
    ncols = len(panels)
    fig, axes = plt.subplots(
        1, ncols, figsize=(3.4 * ncols + 1.0, 3.8), squeeze=False, layout="constrained"
    )
    for ax, (values, layer, title) in zip(axes.ravel(), panels):
        hbd.plot_cells(grb_file, step, values, ax=ax, layer=layer, title=title, overlay=False,
                       colorbar=False, **kwargs)
        mark_well(ax, grb_file, step, well_node, layer)
    fig.colorbar(axes[0, 0].collections[0], ax=axes, shrink=0.85, label=label)
    return fig, axes
