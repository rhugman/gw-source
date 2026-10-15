"""Transient-tracking figure of the paper (Fig. 9, file fig9_transient_tracking): tutorial 08's
seasonal model, snapshots against transient tracking through storage. Outline: docs/paper/outline.md §5.4 and §6; wording: docs/paper/terms.md.

The model is tutorial 08's (tutorials/herebedragons.py::build_transient): the tutorial aquifer
(one layer, 40 x 40 cells of 50 m) with storage, a 1-day steady first period and four seasons a
year for 30 years, every step saved (121 steps). The well pumps from t = 0, so the initial state
is a pumped steady state and "initial water" is the water in the aquifer at the start of the
simulation, not before pumping. The tables are tutorial 08's own helpers
(tutorials/08_transient_tracking/helpers.py), so the figure shows the tutorial's numbers.

- (a) Snapshots: each step traced backward on its own flows, storage release a source term;
  the well's water by source term.
- (b) Transient tracking forward with recharge, river leakage, west-edge inflow and the initial
  water tagged: the well's water by origin, and the initial water's share of all water pumped
  so far.
- (c-f) The steady F of the first step (no time limit); then, from backward tracking in time,
  for the water in each cell at the start, the fraction that reaches the well within 30 years,
  leaves through the river, or is still stored at the end.

Every panel uses the default "flow" volumes and four transport sub-steps per flow step (about
23 days; one step per 91-day flow step nearly doubles early arrivals, tutorial 08 §9). Forward
and backward runs share these options, so the forward-backward check pairs them to round-off.
Two extra runs at one transport step per flow step serve the checks: "gwt" volumes against an
MF6 GWT unit-tracer run on the same flows (tutorial 08 §8), and "flow" volumes for the difference between the two volume options. A
16-sub-step run bounds the effect of the transport step on the year-1 shares.

The caption numbers are in QUOTED and asserted against the computed values before plotting.
Sizes follow studies/paper/method_figures.py: double column 7 in, fonts 7 to 8 pt, PNG at
300 dpi and PDF, Okabe-Ito colours. The maps follow studies/paper/example_figures.py:
viridis from 0 to 1 with white contours (dashed 0.1, solid 0.5), river cells in sky blue and the
well as a white star. Run from the repository root (model workspaces in
studies/paper/output, git-ignored):

    PYTHONPATH=src:tutorials python studies/paper/transient_figure.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (style, palette, save, find_mf6)

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

TUTORIAL_DIR = mfig.TUTORIAL_DIR
TUTORIAL08_DIR = TUTORIAL_DIR / "08_transient_tracking"
FIG_NAME = "fig9_transient_tracking"
WELL = "supply_well"
N_YEARS = 30
POROSITY = 0.3
SUBSTEPS = 4  # transport sub-steps per flow step in every panel
SUBSTEPS_FINE = 16  # sensitivity of the year-1 shares to the transport step
SOURCES = {  # tutorial 08's tagged source groups
    "recharge": {"package": "RCH"},
    "river": {"package": "RIV"},
    "west edge": {"package": "CHD"},
}
DESTINATIONS = {WELL: {"boundnames": [WELL]}}
CUMULATIVE_YEARS = (1, 10, 30)
OKABE_ITO = mfig.OKABE_ITO
COLOURS = {
    "recharge": OKABE_ITO["blue"],
    "river": OKABE_ITO["sky"],
    "west edge": OKABE_ITO["green"],
    "storage": OKABE_ITO["orange"],
    "initial": "#c8c8c8",
}
F_CMAP = "viridis"  # maps, as studies/paper/example_figures.py
F_CONTOUR = "white"
THRESHOLDS = (0.1, 0.5)  # map contours: dashed, solid
RIVER_COLOUR = OKABE_ITO["sky"]
STAR_COLOUR = "white"  # the well on maps
STAR_SIZE = 70.0
LABELS = {
    "recharge": "recharge",
    "river": "river leakage",
    "west edge": "west-edge inflow (CHD)",
    "storage": "storage release, (a) only",
    "initial": "initial water, (b) only",
}
# Values the caption quotes; the computed values must round to them.
QUOTED = {
    "n_steps": 121,
    "n_cells": 1600,
    "recharge factor, winter": 1.8,
    "recharge factor, summer": 0.1,
    "pumping factor, summer": 1.4,
    "pumping, summer (m3/d)": 1120,
    "snapshot recharge, mean": 0.60,
    "snapshot west edge, mean": 0.12,
    "snapshot storage, mean": 0.15,
    "snapshot storage, max": 0.50,
    "year 1 initial": 0.95,
    "year 1 river": 0.03,
    "year 30 initial": 0.52,
    "year 30 recharge": 0.33,
    "year 30 river": 0.16,
    "cumulative initial, year 1": 0.98,
    "cumulative initial, year 10": 0.81,
    "cumulative initial, year 30": 0.68,
    "pumping, 30 years (m3)": 8_766_800,
    "volume recharge (million m3)": 1.62,
    "volume river (million m3)": 1.21,
    "volume initial (million m3)": 5.94,
    "share initial, backward": 0.677,
    "substep sensitivity, year 1 (pp)": 0.2,
    "gwt agreement": "9.8e-14",
}
BELOW = {  # upper bounds the caption states in words
    "year 1 recharge": 0.02,  # "under 2 % recharge"
    "year 30 west edge": 5e-4,  # "no west-edge inflow" (rounds to 0.0 %)
    "w at the west edge": 0.01,  # "the 30-year zone (d) does not reach the west edge"
    "volume options": 2e-4,  # "the two options differ by less than 2 x 10^-4"
    "duality": 1e-12,  # forward-backward check, relative (tutorial 08 §6 asserts 1e-10)
    "closure": 1e-12,
    "fractions sum": 1e-9,  # w + to the river + still stored = 1 (reached: 2.5e-11)
}
STEADY_F_AT_WEST_EDGE = 0.5  # "the steady zone (c) reaches the west edge": F above this there


def import_tutorial_helpers(tutorial_dir: Path = TUTORIAL_DIR,
                            tutorial08_dir: Path = TUTORIAL08_DIR):
    """Import the shared tutorial builders and tutorial 08's helpers; return both modules."""
    for path in (tutorial_dir, tutorial08_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import helpers
    import herebedragons as hbd

    return hbd, helpers


# ---------------------------------------------------------------- computation


def snapshot_shares(summary: pd.DataFrame) -> pd.DataFrame:
    """Return the snapshot shares of the well's water by source term, indexed by time (years)."""
    columns = {"snapshot RCH": "recharge", "snapshot RIV": "river", "snapshot CHD": "west edge",
               "snapshot storage": "storage"}
    return summary.set_index("time (yr)")[list(columns)].rename(columns=columns)


def mean_snapshot(snapshot: pd.DataFrame, summary: pd.DataFrame) -> pd.Series:
    """Return the snapshot shares averaged over the seasonal steps, weighted by step length."""
    weights = summary["delt (d)"].iloc[1:].to_numpy()
    return pd.Series({c: np.average(snapshot[c].iloc[1:], weights=weights)
                      for c in snapshot.columns})


def seasonal_factors(info: dict) -> dict[str, float]:
    """Return the winter and summer recharge and summer pumping factors over their means."""
    rch = np.asarray(info["recharge_factor"][1:])
    wel = np.asarray(info["pumping_factor"][1:])
    season = np.asarray(info["season"][1:])
    return {
        "recharge factor, winter": rch[season == "winter"].mean() / rch.mean(),
        "recharge factor, summer": rch[season == "summer"].mean() / rch.mean(),
        "pumping factor, summer": wel[season == "summer"].mean() / wel.mean(),
    }


def cumulative_initial(fwd: gs.ForwardTracking, days_per_year: float, well: str) -> pd.Series:
    """Return the initial water's share of all water the well has pumped up to each step."""
    pumped = pd.DataFrame({g: fwd.outflow_to[well][g] for g in fwd.groups})
    cumulative = pumped.cumsum()
    share = cumulative["initial"] / cumulative.sum(axis=1)
    share.index = pd.Index(fwd.totim / days_per_year, name="time (yr)")
    return share


def closure_split(bwd: gs.BackwardTracking, well: str) -> dict[str, float]:
    """Return the well's outflow over the simulation and its split (m3) by source and initial."""
    closure = gs.tracking.backward_closure(bwd, well)
    volumes = {p: float(v.sum()) for p, v in bwd.volume_from_by_package[well].items()}
    volumes["initial"] = float(bwd.initial_volume_from[well].sum())
    return {"outflow": closure.rhs, "relative_error": closure.relative_error, **volumes}


def sink_packages(reader, storage_texts: tuple[str, ...] = ("STO-SS", "STO-SY")) -> set[str]:
    """Return the packages with outflow in any step, storage terms excluded."""
    names = set()
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        out = step.term_flow < 0.0
        names |= {step.packages[k].name.upper() for k in np.unique(step.term_package[out])}
    return names - {t.upper() for t in storage_texts}


def track(reader, sources: dict, destinations: dict, porosity: float, substeps: int,
          volume_mode: str = "flow") -> gs.ForwardTracking:
    """Track the sources and the initial water forward with the given options."""
    config = gs.TrackingConfig(porosity=porosity, initial_water={"initial": "all"},
                               volume_mode=volume_mode, substeps=substeps)
    return gs.track_forward(reader, sources, config, sinks=destinations)


def gwt_agreement(hbd, run, fwd_gwt: gs.ForwardTracking, active: np.ndarray, work: Path,
                  mf6_exe: Path, porosity: float) -> float:
    """Run tutorial 08's MF6 GWT recharge tracer; return max |c - C_GWT| over cells and steps."""
    import flopy

    assert fwd_gwt.config.volume_mode == "gwt", "GWT agreement holds with GWT's volumes only"
    assert fwd_gwt.config.substeps == 1, "GWT steps with the flow model's time steps"
    ucn_file = hbd.run_gwt_tracer(run, work / "gwt", mf6_exe, porosity, tagged=("rch",))
    ucn = flopy.utils.HeadFile(str(ucn_file), text="CONCENTRATION")
    conc = np.array([np.asarray(ucn.get_data(kstpkper=ks), float).ravel()
                     for ks in fwd_gwt.steps])
    return float(np.abs(conc[:, active] - fwd_gwt.source_fraction["recharge"][:, active]).max())


def volume_mode_difference(fwd_a: gs.ForwardTracking, fwd_b: gs.ForwardTracking,
                           active: np.ndarray) -> float:
    """Return the largest |c_a - c_b| over all tags, active cells and steps."""
    return max(float(np.abs(fwd_a.source_fraction[g] - fwd_b.source_fraction[g])[:, active].max())
               for g in fwd_a.groups)


def year1_shares(fwd: gs.ForwardTracking, helpers, well: str) -> pd.Series:
    """Return the well's per-step shares and the cumulative initial share at the end of year 1."""
    n = helpers.year_steps(fwd.totim, (1,))[0]
    shares = helpers.origin_shares(fwd, well).iloc[n]
    cumulative = cumulative_initial(fwd, helpers.DAYS_PER_YEAR, well).iloc[n]
    return pd.concat([shares, pd.Series({"cumulative initial": cumulative})])


def compute(
    work: Path,
    mf6_exe: Path,
    n_years: int = N_YEARS,
    porosity: float = POROSITY,
    substeps: int = SUBSTEPS,
    substeps_fine: int = SUBSTEPS_FINE,
    sources: dict = SOURCES,
    destinations: dict = DESTINATIONS,
    well: str = WELL,
    years: tuple[int, ...] = CUMULATIVE_YEARS,
) -> dict:
    """Build and run tutorial 08's model, track it forward and backward; return what is plotted."""
    hbd, helpers = import_tutorial_helpers()
    run = hbd.build_transient(work / "tutorial08_transient", mf6_exe, n_years=n_years,
                              steps_per_season=1)
    reader = gs.open_model(run.ws, boundnames=True)
    summary = helpers.step_summary(reader, well)
    first = reader.read(reader.steps[0])
    fwd = track(reader, sources, destinations, porosity, substeps)
    config = fwd.config
    bwd = gs.track_backward(reader, destinations, config, sources=sources)
    fwd_fine = track(reader, sources, destinations, porosity, substeps_fine)
    fwd_gwt = track(reader, sources, destinations, porosity, 1, volume_mode="gwt")
    fwd_flow1 = track(reader, sources, destinations, porosity, 1)
    steady = gs.backward(first, {well: gs.select(first, boundnames=[well])})
    snapshot = snapshot_shares(summary)
    origin = helpers.origin_shares(fwd, well)[["initial", "recharge", "river", "west edge"]]
    return {
        "first": first,
        "spec": run.spec,
        "well_node": run.info["well_nodes"][well],
        "river_cells": hbd.feature_cells(first, "RIV"),
        "n_steps": len(fwd.steps),
        "factors": seasonal_factors(run.info),
        "pumping_max": float(summary["well rate (m3/d)"].max()),
        "snapshot": snapshot,
        "snapshot_mean": mean_snapshot(snapshot, summary),
        "origin": origin,
        "year_steps": dict(zip(years, helpers.year_steps(fwd.totim, years))),
        "cumulative_initial": cumulative_initial(fwd, helpers.DAYS_PER_YEAR, well),
        "maps": {
            "steady": steady.fraction_through[well],
            "well": bwd.fraction_through[well][0],
            "river": bwd.fraction_to_other_sinks(well)[0],
            "stored": bwd.fraction_in_storage_at_end[0],
        },
        "closure": closure_split(bwd, well),
        "duality": {g: gs.tracking.tracking_duality(fwd, g, bwd, well).relative_error
                    for g in [*sources, "initial"]},
        "sink_packages": sink_packages(reader),
        "substep_sensitivity": float((year1_shares(fwd_fine, helpers, well)
                                      - year1_shares(fwd, helpers, well)).abs().max()),
        "gwt_error": gwt_agreement(hbd, run, fwd_gwt, first.active, work, mf6_exe, porosity),
        "volume_mode_diff": volume_mode_difference(fwd_gwt, fwd_flow1, first.active),
    }


def computed_values(data: dict, years: tuple[int, ...] = CUMULATIVE_YEARS) -> dict[str, float]:
    """Return the computed value of every QUOTED key."""
    origin, at = data["origin"], data["year_steps"]
    closure, mean = data["closure"], data["snapshot_mean"]
    return {
        "n_steps": data["n_steps"],
        "n_cells": int(data["first"].active.sum()),
        **data["factors"],
        "pumping, summer (m3/d)": data["pumping_max"],
        "snapshot recharge, mean": mean["recharge"],
        "snapshot west edge, mean": mean["west edge"],
        "snapshot storage, mean": mean["storage"],
        "snapshot storage, max": float(data["snapshot"]["storage"].max()),
        "year 1 initial": origin["initial"].iloc[at[1]],
        "year 1 river": origin["river"].iloc[at[1]],
        "year 30 initial": origin["initial"].iloc[at[30]],
        "year 30 recharge": origin["recharge"].iloc[at[30]],
        "year 30 river": origin["river"].iloc[at[30]],
        **{f"cumulative initial, year {y}": data["cumulative_initial"].iloc[at[y]]
           for y in years},
        "pumping, 30 years (m3)": closure["outflow"],
        "volume recharge (million m3)": closure["RCH"] / 1e6,
        "volume river (million m3)": closure["RIV"] / 1e6,
        "volume initial (million m3)": closure["initial"] / 1e6,
        "share initial, backward": closure["initial"] / closure["outflow"],
        "substep sensitivity, year 1 (pp)": 100.0 * data["substep_sensitivity"],
        "gwt agreement": data["gwt_error"],
    }


def check_rounding(computed: dict, quoted: dict = QUOTED) -> None:
    """Assert that every caption number rounds to the computed value."""
    for key, value in quoted.items():
        got = computed[key]
        if isinstance(value, str):
            assert f"{got:.1e}" == value, f"{key}: computed {got:.2e}, caption {value}"
        elif isinstance(value, int):  # rounded to its last non-zero digit
            zeros = len(str(value)) - len(str(value).rstrip("0"))
            assert round(got, -zeros) == value, f"{key}: computed {got:,.1f}, caption {value:,}"
        elif key.startswith("substep"):
            assert got < value, f"{key}: computed {got:.3f}, caption 'at most {value}'"
        else:
            digits = len(f"{value}".split(".")[1])
            assert round(got, digits) == value, f"{key}: computed {got:.4f}, caption {value}"


def check_quoted(data: dict, quoted: dict = QUOTED, below: dict = BELOW,
                 steady_f_at_west_edge: float = STEADY_F_AT_WEST_EDGE) -> dict[str, float]:
    """Assert the caption numbers and the statements made in words; return the values."""
    computed = computed_values(data)
    check_rounding(computed, quoted)
    origin, at, closure = data["origin"], data["year_steps"], data["closure"]
    first, maps = data["first"], data["maps"]
    assert origin["recharge"].iloc[at[1]] < below["year 1 recharge"]
    assert origin["west edge"].iloc[at[30]] < below["year 30 west edge"]
    assert abs(closure["relative_error"]) < below["closure"]
    assert max(data["duality"].values()) < below["duality"], data["duality"]
    initial_forward = data["cumulative_initial"].iloc[at[30]]
    initial_backward = closure["initial"] / closure["outflow"]
    assert abs(initial_forward - initial_backward) < below["duality"]
    assert data["volume_mode_diff"] < below["volume options"]
    assert data["sink_packages"] == {"WEL", "RIV"}, "caption: the river is the only other sink"
    total = maps["well"] + maps["river"] + maps["stored"]
    assert np.abs(total[first.active] - 1.0).max() < below["fractions sum"]
    west = gs.export.to_grid(first, maps["steady"])[0][:, 0]
    assert west.max() > steady_f_at_west_edge, "caption: the steady zone reaches the west edge"
    west_w = gs.export.to_grid(first, maps["well"])[0][:, 0]
    assert west_w.max() < below["w at the west edge"], "caption: (d) misses the west edge"
    return computed


# ---------------------------------------------------------------- drawing


def stacked_shares(ax, shares: pd.DataFrame, order: list[str], colours: dict = COLOURS,
                   edgecolor: str = "white") -> None:
    """Stacked area of per-step shares against time; step ends on the x axis."""
    x = np.concatenate([[0.0], shares.index.to_numpy()])
    bands = [np.concatenate([[shares[c].iloc[0]], shares[c].to_numpy()]) for c in order]
    ax.stackplot(x, *bands, colors=[colours[c] for c in order], step="pre",
                 edgecolor=edgecolor, linewidth=0.3)
    ax.set_xlim(0.0, float(shares.index.max()))
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks((0.0, 0.5, 1.0))
    ax.set_ylabel("share of the\nwell's water (-)")


def draw_cumulative(ax, share: pd.Series, year_steps: dict[int, int],
                    n_years: int = N_YEARS, label_year: float = 20.0) -> None:
    """Draw the initial water's share of all water pumped so far, dashed and labelled."""
    from matplotlib import patheffects

    halo = [patheffects.withStroke(linewidth=2.8, foreground="white")]
    box = {"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85}
    ax.plot(share.index, share.to_numpy(), color=mfig.INK, lw=1.2, ls=(0, (4, 2)),
            path_effects=halo)
    for year, n in year_steps.items():
        x, y = share.index[n], share.iloc[n]
        ax.plot(x, y, marker="o", ms=3.5, color=mfig.INK, mec="white", mew=0.5, zorder=5,
                clip_on=False)
        ha = "right" if year == n_years else "left"
        dx = -0.4 if year == n_years else 0.4
        ax.text(x + dx, y - 0.05, f"{y:.0%}".replace("%", " %"), ha=ha, va="top", fontsize=7,
                bbox=box)
    n_label = int(np.argmin(np.abs(share.index.to_numpy() - label_year)))
    ax.text(share.index[n_label], share.iloc[n_label] + 0.05,
            "initial water, share of all water pumped so far", ha="center", va="bottom",
            fontsize=7, bbox=box)


def map_extent(spec) -> tuple[float, float, float, float]:
    """Return the map extent (km) of the tutorial grid."""
    return (0.0, spec.lx / 1000.0, 0.0, spec.ly / 1000.0)


def cell_centres_km(spec) -> tuple[np.ndarray, np.ndarray]:
    """Return the x and y (km) of the cell centres of the tutorial grid."""
    x = (np.arange(spec.ncol) + 0.5) * spec.delr / 1000.0
    y = (spec.ly - (np.arange(spec.nrow) + 0.5) * spec.delc) / 1000.0
    return x, y


def draw_contours(ax, grid: np.ndarray, spec, levels: tuple = THRESHOLDS,
                  colour: str = F_CONTOUR) -> None:
    """Draw the 0.1 (dashed) and 0.5 (solid) contours of a per-cell fraction."""
    x, y = cell_centres_km(spec)
    ax.contour(x, y, np.ma.masked_invalid(grid), levels=list(levels), colors=colour,
               linestyles=["--", "-"], linewidths=1.0)


def draw_river(ax, first: gs.FlowStep, river_cells: np.ndarray, spec,
               colour: str = RIVER_COLOUR) -> None:
    """Fill the river cells with one colour."""
    values = np.full(first.n_cells, np.nan)
    values[river_cells] = 1.0
    grid = np.ma.masked_invalid(gs.export.to_grid(first, values)[0])
    ax.imshow(grid, cmap=ListedColormap([colour]), vmin=0.0, vmax=2.0, extent=map_extent(spec),
              origin="upper", interpolation="nearest")


def draw_map(ax, first: gs.FlowStep, values: np.ndarray, spec, well_node: int,
             river_cells: np.ndarray, star_colour: str = STAR_COLOUR,
             star_size: float = STAR_SIZE):
    """Map one per-cell fraction (viridis, 0 to 1) with contours, the river and the well."""
    grid = gs.export.to_grid(first, values)[0]
    image = ax.imshow(grid, cmap=F_CMAP, vmin=0.0, vmax=1.0, extent=map_extent(spec),
                      origin="upper", interpolation="nearest")
    draw_contours(ax, grid, spec)
    draw_river(ax, first, river_cells, spec)
    x_well, y_well = spec.xy(divmod(well_node, spec.ncol))
    ax.scatter(x_well / 1000.0, y_well / 1000.0, marker="*", s=star_size, color=star_colour,
               edgecolor="black", linewidth=0.6, zorder=6)
    ax.set_xlim(0.0, spec.lx / 1000.0)
    ax.set_ylim(0.0, spec.ly / 1000.0)
    ax.set_xticks((0, 1, 2))
    ax.set_yticks((0, 1, 2))
    ax.set_aspect("equal")
    return image


def series_legend(fig, anchor: tuple[float, float], colours: dict = COLOURS,
                  labels: dict = LABELS) -> None:
    """Legend of the two series panels, right of them."""
    handles = [plt.Rectangle((0, 0), 1, 1, color=colours[k], label=labels[k])
               for k in ("initial", "recharge", "river", "west edge", "storage")]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=anchor, handlelength=1.4,
               labelspacing=0.6)


def make_figure(out_dir: Path, data: dict, fig_name: str = FIG_NAME) -> list[Path]:
    """Fig. 9: snapshot and tracked shares of the well's water, and four backward maps."""
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 5.0))
    top = fig.add_gridspec(2, 1, left=0.085, right=0.75, top=0.955, bottom=0.53, hspace=0.32)
    ax_snap = fig.add_subplot(top[0])
    ax_track = fig.add_subplot(top[1], sharex=ax_snap)
    stacked_shares(ax_snap, data["snapshot"], ["recharge", "river", "west edge", "storage"],
                   edgecolor="none")
    stacked_shares(ax_track, data["origin"], ["initial", "recharge", "river", "west edge"])
    draw_cumulative(ax_track, data["cumulative_initial"], data["year_steps"])
    plt.setp(ax_snap.get_xticklabels(), visible=False)
    ax_track.set_xlabel("time since the start of the simulation (years)")
    ax_snap.set_title("(a) snapshots", loc="left", fontweight="bold")
    ax_track.set_title("(b) transient tracking", loc="left", fontweight="bold")
    series_legend(fig, (0.765, 0.745))

    bottom = fig.add_gridspec(1, 4, left=0.07, right=0.89, top=0.39, bottom=0.07, wspace=0.12)
    titles = {
        "steady": "(c) steady F, first step\n(no time limit)",
        "well": "(d) to the well\nwithin 30 years",
        "river": "(e) to the river\nwithin 30 years",
        "stored": "(f) still stored\nafter 30 years",
    }
    axes = [fig.add_subplot(bottom[0, i]) for i in range(4)]
    for ax, (key, title) in zip(axes, titles.items()):
        image = draw_map(ax, data["first"], data["maps"][key], data["spec"], data["well_node"],
                         data["river_cells"])
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("x (km)")
    axes[0].set_ylabel("y (km)")
    for ax in axes[1:]:
        plt.setp(ax.get_yticklabels(), visible=False)
    cax = fig.add_axes((0.905, 0.07, 0.013, 0.32))
    bar = fig.colorbar(image, cax=cax)
    bar.set_label("fraction (-)")
    bar.outline.set_linewidth(0.5)
    return mfig.save(fig, out_dir, fig_name)


# ---------------------------------------------------------------- driver


def main(out_dir: Path = mfig.FIG_DIR, work: Path = mfig.WORK_DIR) -> dict[str, float]:
    """Build tutorial 08's model, check the caption numbers and write Fig. 9."""
    mfig.paper_style()
    start = time.perf_counter()
    data = compute(work, mfig.find_mf6())
    computed = check_quoted(data)
    for key, value in computed.items():
        print(f"{key}: {value}")
    print("largest |c(flow) - c(gwt)|, one transport step:", data["volume_mode_diff"])
    print("forward-backward check, relative:", data["duality"])
    print("wrote", make_figure(out_dir, data))
    print(f"done in {time.perf_counter() - start:.1f} s")
    return computed


if __name__ == "__main__":
    main()
