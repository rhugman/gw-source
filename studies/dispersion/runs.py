"""Drivers of the dispersion study: refinement series, metrics tables and saved maps.

run_analytic(): problem A (uniform flow + well) on DIS and Voronoi DISV grids of several cell
sizes and two flow directions; full mixing, face routing (DIS) and the cell-averaged analytical
zone, each compared with the analytical capture zone on a shared raster.

run_model1(): problem B (test model 1's physics) on DIS and DISV grids; full mixing, face
routing (DIS) and MF6 PRT particles (DIS grids), compared with PRT on the finest DIS grid:
recharge capture zone (zone metrics west of the river only: east of it the gaining river is a
weak sink that every method, the particle helper included, treats by full mixing), shares of the
well water by source package, mean travel time.

run_transient(): problem B's steady flows held for 30 steps of 2000 d; forward transient
tracking of all water entering after t = 0, with 1, 4, 16 and 64 transport sub-steps per flow
step, against the step-averaged PRT arrival-time distribution on the same grid.
"""

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import analysis as an
import problems as pb
import gwsource as gs
from gwsource import tracking as tr
from gwsource.experimental import face_routing as fr
from gwsource.prt import PrtConfig, track_particles


@dataclass
class StudyConfig:
    """Paths and settings of the study (cell sizes in m, times in d)."""

    out: Path
    mf6_exe: Path
    triangle_exe: Path
    sizes_a: tuple[float, ...] = (200.0, 100.0, 50.0, 25.0, 12.5)
    angles: tuple[float, ...] = (0.0, 30.0)
    sizes_b: tuple[float, ...] = (100.0, 50.0, 25.0, 12.5)
    kinds: tuple[str, ...] = ("DIS", "DISV")
    porosity: float = 0.3
    raster: float = 2.5
    margin_a: float = 200.0
    margin_b: float = 25.0
    river_gap: float = 50.0
    prt_subdivisions: int = 2
    map_sizes: tuple[float, ...] = (50.0, 25.0)
    transient_sizes: tuple[float, ...] = (50.0, 12.5)
    transient_period: tuple[float, int, float] = (60000.0, 30, 1.0)
    substeps: tuple[int, ...] = (1, 4, 16, 64)

    @property
    def reference_h(self) -> float:
        """Finest cell size of problem B (its DIS PRT run is the reference)."""
        return min(self.sizes_b)


def _wel_group(step: gs.FlowStep) -> dict[str, gs.Selection]:
    """Return the well destination group."""
    return {"wel": gs.select(step, package="WEL")}


def _routing(model: pb.GridModel, step: gs.FlowStep) -> fr.FaceRoutingResult:
    """Return the face-routing backward trace to the well (recharge through the top face)."""
    delr, delc = fr.read_dis_spacing(model.grb_file)
    return fr.route_backward(step, _wel_group(step), delr, delc)


def _row(base: dict, method: str, metrics: dict) -> dict:
    """Return one metrics table row."""
    return {**base, "method": method, **metrics}


# ---------------------------------------------------------------- problem A


def analytic_fields(model: pb.GridModel, step, index, ref_raster) -> dict[str, np.ndarray]:
    """Return per-cell fields: full mixing, face routing (DIS) and the cell-averaged zone."""
    fields = {"mixing": gs.backward(step, _wel_group(step)).fraction_through["wel"]}
    if model.kind == "DIS":
        fields["routing"] = _routing(model, step).fraction_through["wel"]
    fields["cell_average"] = an.cell_average(index, ref_raster, model.n_cells)
    return fields


def run_analytic(config: StudyConfig) -> tuple[pd.DataFrame, dict]:
    """Run problem A; return the metrics table and raster maps for the figures."""
    rows, maps = [], {}
    for angle in config.angles:
        spec = pb.AnalyticSpec(angle_deg=angle)
        xr, yr = an.raster_points(spec.lx, spec.ly, config.raster)
        ref = an.capture_zone_mask(xr, yr, spec)
        window = an.window_mask(xr, yr, spec.lx, spec.ly, config.margin_a)
        edge = an.contour_length(xr, yr, np.ma.masked_where(~window, ref.astype(float)))
        pixel = config.raster**2
        ref_domain_area = ref.sum() * pixel
        maps[f"ref_{angle:g}"] = ref
        for kind in config.kinds:
            for h in config.sizes_a:
                ws = config.out / "models" / f"a{angle:g}_{kind}_{h:g}"
                t0 = time.perf_counter()
                model = pb.build_analytic(ws, config.mf6_exe, config.triangle_exe, spec, kind, h)
                step = gs.read_step(model.ws)
                index = an.raster_cells(model.modelgrid, xr, yr, config.raster)
                fields = analytic_fields(model, step, index, ref)
                base = {"angle": angle, "kind": kind, "h": h, "mean_h": model.mean_cell_size,
                        "n_cells": model.n_cells, "seconds": time.perf_counter() - t0}
                for method, f in fields.items():
                    m = an.zone_metrics(f[index], ref, window, pixel, edge, model.mean_cell_size)
                    m["tt_err"] = float(f @ step.area / ref_domain_area - 1.0)
                    rows.append(_row(base, method, m))
                    if h in config.map_sizes:
                        maps[f"{angle:g}_{kind}_{h:g}_{method}"] = f[index][::2, ::2]
                print(f"A angle {angle:g} {kind} h={h:g}: {model.n_cells} cells")
    return pd.DataFrame(rows), maps


# ---------------------------------------------------------------- problem B


@dataclass
class Model1Run:
    """Problem B on one grid: the model, its step and per-method outputs."""

    model: pb.GridModel
    step: gs.FlowStep
    fields: dict
    shares: dict
    mean_time: dict
    prt: object | None = None


def recharge_fraction(step: gs.FlowStep, term_fraction: np.ndarray) -> np.ndarray:
    """Return, per cell, the fraction of the cell's recharge that reaches the well."""
    out = np.zeros(step.n_cells)
    rch = np.flatnonzero(gs.select(step, package="RCH").terms)
    out[step.term_cell[rch]] = term_fraction[rch]
    return out


def package_shares(volume_from_by_term: dict, total: float) -> dict[str, float]:
    """Return the share of the well water by source package."""
    return {p.split("-")[0].upper(): float(v.sum() / total) for p, v in volume_from_by_term.items()}


def prt_shares(prt) -> dict[str, float]:
    """Return the share of the captured particle flow by release package."""
    packages = np.asarray([str(p).split("-")[0].upper() for p in prt.release.package])
    return {p: float(prt.captured_weight[packages == p].sum() / prt.captured_flow)
            for p in np.unique(packages)}


def model1_on_grid(config: StudyConfig, spec: pb.Model1Spec, kind: str, h: float) -> Model1Run:
    """Run problem B on one grid with every method that applies to it."""
    ws = config.out / "models" / f"b_{kind}_{h:g}"
    model = pb.build_model1(ws, config.mf6_exe, config.triangle_exe, spec, kind, h)
    step = gs.read_step(model.ws)
    mixed = gs.backward(step, _wel_group(step))
    q = mixed.destination_inflow["wel"]
    tt = gs.travel_time(step, mixed, config.porosity)
    volume = gs.water_volume(step, config.porosity)
    source = gs.assemble.cell_budget(step, gs.assemble.flow_edges(step)).source
    to_exit = tt.weighted_time["wel"] - tt.exit_cell_time["wel"]
    run = Model1Run(
        model=model,
        step=step,
        fields={"mixing": mixed.fraction_through["wel"]},
        shares={"mixing": package_shares(mixed.volume_from_by_term["wel"], q)},
        mean_time={
            "mixing": tt.mean_transit_time["wel"],
            "mixing_to_exit_cell": float(
                source @ to_exit / (source @ mixed.fraction_through["wel"])
            ),
        },
    )
    if kind == "DIS":
        routed = _routing(model, step)
        run.fields["routing"] = recharge_fraction(step, routed.term_fraction["wel"])
        run.shares["routing"] = package_shares(routed.volume_from_by_term["wel"], q)
        run.mean_time["routing"] = float(volume @ routed.fraction_through["wel"] / q)
        prt = track_particles(
            model.ws, step, mixed, "wel",
            PrtConfig(porosity=config.porosity, subdivisions=config.prt_subdivisions),
            config.mf6_exe, ws / "prt",
        )
        run.prt = prt
        run.fields["particles"] = np.nan_to_num(prt.cell_capture_fraction)
        run.shares["particles"] = prt_shares(prt)
        run.mean_time["particles"] = prt.mean_arrival
    return run


def run_model1(config: StudyConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    """Run problem B; return metrics and shares tables, raster maps and the PRT arrivals."""
    spec = pb.Model1Spec()
    xr, yr = an.raster_points(spec.lx, spec.ly, config.raster)
    window = an.window_mask(xr, yr, spec.lx, spec.ly, config.margin_b)
    window &= xr < spec.riv_x - config.river_gap  # west of the river: no weak sinks on the way
    pixel = config.raster**2
    runs = {}
    for kind in config.kinds:
        for h in config.sizes_b:
            t0 = time.perf_counter()
            runs[(kind, h)] = model1_on_grid(config, spec, kind, h)
            runs[(kind, h)].model.notes["seconds"] = time.perf_counter() - t0
            print(f"B {kind} h={h:g}: {runs[(kind, h)].model.n_cells} cells")
    reference = runs[("DIS", config.reference_h)]
    ref_index = an.raster_cells(reference.model.modelgrid, xr, yr, config.raster)
    ref = reference.fields["particles"][ref_index]
    edge = an.contour_length(xr, yr, np.ma.masked_where(~window, ref))
    rows, share_rows, maps, arrivals = [], [], {"ref": ref[::2, ::2]}, {}
    for (kind, h), run in runs.items():
        index = an.raster_cells(run.model.modelgrid, xr, yr, config.raster)
        base = {"kind": kind, "h": h, "mean_h": run.model.mean_cell_size,
                "n_cells": run.model.n_cells, "seconds": run.model.notes["seconds"]}
        for method, f in run.fields.items():
            m = an.zone_metrics(f[index], ref, window, pixel, edge, run.model.mean_cell_size)
            m["mean_time"] = run.mean_time.get(method, np.nan)
            if method == "mixing":
                m["mean_time_to_exit_cell"] = run.mean_time["mixing_to_exit_cell"]
            rows.append(_row(base, method, m))
            if h in config.map_sizes or h == config.reference_h:
                maps[f"{kind}_{h:g}_{method}"] = f[index][::2, ::2]
        for method, shares in run.shares.items():
            share_rows.append({**base, "method": method, **shares})
        if run.prt is not None:
            arrivals[f"{h:g}_time"] = run.prt.arrival_time
            arrivals[f"{h:g}_weight"] = run.prt.captured_weight
    return pd.DataFrame(rows), pd.DataFrame(share_rows), maps, arrivals


# ---------------------------------------------------------------- transient


def step_averaged_cdf(arrival: np.ndarray, weight: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Return the flux-weighted arrival-time CDF averaged over each step (0, ends[0]], ..."""
    keep = weight > 0
    order = np.argsort(arrival[keep])
    t, w = arrival[keep][order], weight[keep][order]
    grid = np.linspace(0.0, ends[-1], 200 * len(ends) + 1)
    cdf = np.searchsorted(t, grid, side="right")
    cum = np.concatenate([[0.0], np.cumsum(w)])[cdf] / w.sum()
    starts = np.concatenate([[0.0], ends[:-1]])
    return np.array([cum[(grid >= a) & (grid <= b)].mean() for a, b in zip(starts, ends)])


def run_transient(config: StudyConfig, arrivals: dict) -> pd.DataFrame:
    """Track all new water to the well with several sub-step counts; return the curves."""
    spec = pb.Model1Spec()
    rows = []
    for h in config.transient_sizes:
        ws = config.out / "models" / f"t_DIS_{h:g}"
        model = pb.build_model1(
            ws, config.mf6_exe, config.triangle_exe, spec, "DIS", h, [config.transient_period]
        )
        reader = gs.open_model(model.ws)
        ends = np.cumsum([reader.step_length(k) for k in reader.steps])
        delt = np.diff(np.concatenate([[0.0], ends]))
        if f"{h:g}_time" in arrivals:
            prt = step_averaged_cdf(arrivals[f"{h:g}_time"], arrivals[f"{h:g}_weight"], ends)
            rows += [{"h": h, "method": "particles", "t": t, "fraction": v}
                     for t, v in zip(ends, prt)]
        for n_sub in config.substeps:
            t0 = time.perf_counter()
            cfg = tr.TrackingConfig(porosity=config.porosity, substeps=n_sub, volume_mode="gwt")
            fwd = tr.track_forward(
                reader, {"new": {"package": ["RCH", "RIV", "CHD"]}}, cfg,
                sinks={"wel": {"package": "WEL"}},
            )
            fraction = fwd.outflow_to["wel"]["new"] / (abs(spec.well_rate) * delt)
            seconds = time.perf_counter() - t0
            rows += [{"h": h, "method": f"substeps_{n_sub}", "t": t, "fraction": v,
                      "seconds": seconds} for t, v in zip(ends, fraction)]
            print(f"T h={h:g} substeps={n_sub}: {seconds:.1f} s")
    return pd.DataFrame(rows)
