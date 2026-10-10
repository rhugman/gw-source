"""Transient-tracking figure of the paper (Fig. 10): tutorial 08's seasonal model, snapshots
against transient tracking through storage. Outline: docs/paper/outline.md §5.4 and §6.

The model is tutorial 08's (tutorials/herebedragons.py::build_transient): the tutorial aquifer
(one layer, 40 x 40 cells of 50 m) with storage, a 1-day steady first period and four seasons a
year for 30 years, every step saved (121 steps). The tables are tutorial 08's own helpers
(tutorials/08_transient_tracking/helpers.py), so the figure shows the tutorial's numbers.

- (a) Snapshots: each step traced backward on its own flows, storage release a source term;
  the well's water by source term.
- (b) Transient tracking forward (default "flow" volumes, porosity 0.3) with recharge, river,
  west-edge inflow and the initial water tagged: the well's water by origin, and the initial
  water's share of all water pumped so far.
- (c-f) Backward: the steady F of the first step (no time limit), then for the water in each
  cell at the start, the fraction that reaches the well within 30 years, leaves through other
  sinks, or is still stored at the end.

The caption numbers are in QUOTED and asserted against the computed values before plotting,
including the agreement with an MF6 GWT unit-tracer run on the same flows ("gwt" volumes; the
verification on test models 6 and 7 is Fig. 2's). Sizes follow studies/paper/method_figures.py:
double column 7 in, fonts 7 to 8 pt, PNG at 300 dpi and PDF, Okabe-Ito colours. Run from the
repository root (model workspaces in studies/paper/output, git-ignored):

    PYTHONPATH=src python studies/paper/transient_figure.py
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

TUTORIAL_DIR = mfig.TUTORIAL_DIR
TUTORIAL08_DIR = TUTORIAL_DIR / "08_transient_tracking"
FIG_NAME = "fig10_transient_tracking"
WELL = "supply_well"
N_YEARS = 30
POROSITY = 0.3
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
LABELS = {
    "recharge": "recharge",
    "river": "river leakage",
    "west edge": "west-edge inflow (CHD)",
    "storage": "storage release (snapshots)",
    "initial": "initial water (tracking)",
}
# Values the caption quotes (outline §5.4, tutorial 08); the computed values must round to them.
QUOTED = {
    "n_steps": 121,
    "n_cells": 1600,
    "snapshot recharge, mean": 0.60,
    "snapshot storage, mean": 0.15,
    "year 1 initial": 0.95,
    "year 1 river": 0.04,
    "year 30 initial": 0.52,
    "year 30 recharge": 0.33,
    "year 30 river": 0.15,
    "cumulative initial, year 1": 0.97,
    "cumulative initial, year 10": 0.81,
    "cumulative initial, year 30": 0.68,
    "well outflow, 30 years (m3)": 8_766_800,
    "closure river": 0.138,
    "closure recharge": 0.185,
    "closure initial": 0.676,
    "gwt agreement": "9.8e-14",
}
YEAR1_RECHARGE_BELOW = 0.02  # "under 2 % recharge" in year 1
WEST_EDGE_BELOW = 5e-4  # "none from the west edge" at year 30 (rounds to 0.0 %)


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


def cumulative_initial(fwd: gs.ForwardTracking, days_per_year: float,
                       well: str = WELL) -> pd.Series:
    """Return the initial water's share of all water the well has pumped up to each step."""
    pumped = pd.DataFrame({g: fwd.outflow_to[well][g] for g in fwd.groups})
    cumulative = pumped.cumsum()
    share = cumulative["initial"] / cumulative.sum(axis=1)
    share.index = pd.Index(fwd.totim / days_per_year, name="time (yr)")
    return share


def closure_split(bwd: gs.BackwardTracking, well: str = WELL) -> dict[str, float]:
    """Return the well's outflow over the simulation and its split by source and initial water."""
    closure = gs.tracking.backward_closure(bwd, well)
    parts = {p: float(v.sum()) for p, v in bwd.volume_from_by_package[well].items()}
    parts["initial"] = float(bwd.initial_volume_from[well].sum())
    split = {k: v / closure.rhs for k, v in parts.items()}
    return {"outflow": closure.rhs, "relative_error": closure.relative_error, **split}


def sink_packages(reader, storage_texts: tuple[str, ...] = ("STO-SS", "STO-SY")) -> set[str]:
    """Return the packages with outflow in any step, storage terms excluded."""
    names = set()
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        out = step.term_flow < 0.0
        names |= {step.packages[k].name.upper() for k in np.unique(step.term_package[out])}
    return names - {t.upper() for t in storage_texts}


def gwt_agreement(hbd, run, reader, work: Path, mf6_exe: Path, porosity: float = POROSITY) -> float:
    """Run tutorial 08's MF6 GWT recharge tracer; return max |c - C_GWT| over cells and steps."""
    import flopy

    config = gs.TrackingConfig(porosity=porosity, volume_mode="gwt")
    fwd = gs.track_forward(reader, {"recharge": SOURCES["recharge"]}, config)
    ucn_file = hbd.run_gwt_tracer(run, work / "gwt", mf6_exe, porosity, tagged=("rch",))
    ucn = flopy.utils.HeadFile(str(ucn_file), text="CONCENTRATION")
    conc = np.array([np.asarray(ucn.get_data(kstpkper=ks), float).ravel() for ks in fwd.steps])
    active = reader.read(reader.steps[0]).active
    return float(np.abs(conc[:, active] - fwd.source_fraction["recharge"][:, active]).max())


def compute(work: Path, mf6_exe: Path) -> dict:
    """Build and run tutorial 08's model, track it forward and backward; return what is plotted."""
    hbd, helpers = import_tutorial_helpers()
    run = hbd.build_transient(work / "tutorial08_transient", mf6_exe, n_years=N_YEARS,
                              steps_per_season=1)
    reader = gs.open_model(run.ws, boundnames=True)
    summary = helpers.step_summary(reader, WELL)
    config = gs.TrackingConfig(porosity=POROSITY, initial_water={"initial": "all"})
    fwd = gs.track_forward(reader, SOURCES, config, sinks=DESTINATIONS)
    bwd = gs.track_backward(reader, DESTINATIONS, config, sources=SOURCES)
    first = reader.read(reader.steps[0])
    steady = gs.backward(first, {WELL: gs.select(first, boundnames=[WELL])})
    snapshot = snapshot_shares(summary)
    origin = helpers.origin_shares(fwd, WELL)[["recharge", "river", "west edge", "initial"]]
    return {
        "first": first,
        "well_node": run.info["well_nodes"][WELL],
        "riv_col": run.spec.riv_col,
        "spec": run.spec,
        "n_steps": len(fwd.steps),
        "snapshot": snapshot,
        "snapshot_mean": mean_snapshot(snapshot, summary),
        "origin": origin,
        "year_steps": dict(zip(CUMULATIVE_YEARS, helpers.year_steps(fwd.totim, CUMULATIVE_YEARS))),
        "cumulative_initial": cumulative_initial(fwd, helpers.DAYS_PER_YEAR),
        "maps": {
            "steady": steady.fraction_through[WELL],
            "well": bwd.fraction_through[WELL][0],
            "other": bwd.fraction_to_other_sinks(WELL)[0],
            "stored": bwd.fraction_in_storage_at_end[0],
        },
        "closure": closure_split(bwd),
        "sink_packages": sink_packages(reader),
        "gwt_error": gwt_agreement(hbd, run, reader, work, mf6_exe),
    }


def check_quoted(data: dict, quoted: dict = QUOTED) -> dict[str, float]:
    """Assert that every caption number rounds to the computed value; return the values."""
    origin, years = data["origin"], data["year_steps"]
    first, closure = data["first"], data["closure"]
    computed = {
        "n_steps": data["n_steps"],
        "n_cells": int(first.active.sum()),
        "snapshot recharge, mean": data["snapshot_mean"]["recharge"],
        "snapshot storage, mean": data["snapshot_mean"]["storage"],
        "year 1 initial": origin["initial"].iloc[years[1]],
        "year 1 river": origin["river"].iloc[years[1]],
        "year 30 initial": origin["initial"].iloc[years[30]],
        "year 30 recharge": origin["recharge"].iloc[years[30]],
        "year 30 river": origin["river"].iloc[years[30]],
        **{f"cumulative initial, year {y}": data["cumulative_initial"].iloc[years[y]]
           for y in CUMULATIVE_YEARS},
        "well outflow, 30 years (m3)": closure["outflow"],
        "closure river": closure["RIV"],
        "closure recharge": closure["RCH"],
        "closure initial": closure["initial"],
        "gwt agreement": data["gwt_error"],
    }
    for key, value in quoted.items():
        got = computed[key]
        if isinstance(value, str):
            assert f"{got:.1e}" == value, f"{key}: computed {got:.2e}, caption {value}"
        elif isinstance(value, int) and value > 1000:
            assert round(got, -2) == value, f"{key}: computed {got:,.1f}, caption {value:,}"
        elif isinstance(value, int):
            assert got == value, f"{key}: computed {got}, caption {value}"
        else:
            digits = len(f"{value}".split(".")[1])
            assert round(got, digits) == value, f"{key}: computed {got:.4f}, caption {value}"
    assert origin["recharge"].iloc[years[1]] < YEAR1_RECHARGE_BELOW
    assert origin["west edge"].iloc[years[30]] < WEST_EDGE_BELOW
    assert abs(closure["relative_error"]) < 1e-12
    assert data["sink_packages"] == {"WEL", "RIV"}, "caption: the river is the only other sink"
    total = data["maps"]["well"] + data["maps"]["other"] + data["maps"]["stored"]
    assert np.abs(total[first.active] - 1.0).max() < 5e-5, "fate fractions must add up to 1"
    return computed


# ---------------------------------------------------------------- drawing


def stacked_shares(ax, shares: pd.DataFrame, order: list[str]) -> None:
    """Stacked area of per-step shares against time; white edges separate the bands."""
    x = np.concatenate([[0.0], shares.index.to_numpy()])
    bands = [np.concatenate([[shares[c].iloc[0]], shares[c].to_numpy()]) for c in order]
    ax.stackplot(x, *bands, colors=[COLOURS[c] for c in order], step="pre",
                 edgecolor="white", linewidth=0.3)
    ax.set_xlim(0.0, float(shares.index.max()))
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks((0.0, 0.5, 1.0))
    ax.set_ylabel("share of the\nwell's water (-)")


def draw_cumulative(ax, share: pd.Series, year_steps: dict[int, int]) -> None:
    """Draw the initial water's share of all water pumped so far, with labelled years."""
    ax.plot(share.index, share.to_numpy(), color=mfig.INK, lw=1.2)
    for year, n in year_steps.items():
        x, y = share.index[n], share.iloc[n]
        ax.plot(x, y, marker="o", ms=3.5, color=mfig.INK, mec="white", mew=0.5, zorder=5,
                clip_on=False)
        ha = "right" if year == N_YEARS else "left"
        dx = -0.3 if year == N_YEARS else 0.3
        ax.text(x + dx, y - 0.05, f"{y:.0%}".replace("%", " %"), ha=ha, va="top", fontsize=7)


def map_extent(spec) -> tuple[float, float, float, float]:
    """Return the map extent (km) of the tutorial grid."""
    return (0.0, spec.lx / 1000.0, 0.0, spec.ly / 1000.0)


def draw_map(ax, first: gs.FlowStep, values: np.ndarray, spec, riv_col: int, well_node: int):
    """Map one per-cell fraction (0 to 1) with the river column and the well marked."""
    grid = gs.export.to_grid(first, values)[0]
    image = ax.imshow(grid, cmap=mfig.F_CMAP, vmin=0.0, vmax=1.0, extent=map_extent(spec),
                      origin="upper", interpolation="nearest")
    x_river = (riv_col + 0.5) * spec.delr / 1000.0
    ax.plot([x_river, x_river], [0.0, spec.ly / 1000.0], color=mfig.MUTED, lw=0.8, ls=(0, (3, 1.5)))
    row, col = divmod(well_node, spec.ncol)
    x_well, y_well = spec.xy((row, col))
    ax.plot(x_well / 1000.0, y_well / 1000.0, marker="v", color=OKABE_ITO["vermillion"], ms=4.5,
            mec="white", mew=0.5)
    ax.set_xticks((0, 1, 2))
    ax.set_yticks((0, 1, 2))
    ax.set_aspect("equal")
    return image


def series_legend(fig, anchor: tuple[float, float]) -> None:
    """Legend of the two series panels, right of them."""
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOURS[k], label=LABELS[k])
               for k in ("recharge", "river", "west edge", "storage", "initial")]
    handles.append(plt.Line2D([], [], color=mfig.INK, lw=1.2, marker="o", ms=3.5, mec="white",
                              label="initial water, share of\nall water pumped so far"))
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=anchor, handlelength=2.0,
               labelspacing=0.6)


def make_figure(out_dir: Path, data: dict) -> list[Path]:
    """Fig. 10: snapshot and tracked shares of the well's water, and four backward maps."""
    fig = plt.figure(figsize=(mfig.FULL_WIDTH, 5.0))
    top = fig.add_gridspec(2, 1, left=0.085, right=0.72, top=0.955, bottom=0.53, hspace=0.32)
    ax_snap = fig.add_subplot(top[0])
    ax_track = fig.add_subplot(top[1], sharex=ax_snap)
    stacked_shares(ax_snap, data["snapshot"], ["recharge", "river", "west edge", "storage"])
    stacked_shares(ax_track, data["origin"], ["recharge", "river", "west edge", "initial"])
    draw_cumulative(ax_track, data["cumulative_initial"], data["year_steps"])
    plt.setp(ax_snap.get_xticklabels(), visible=False)
    ax_track.set_xlabel("time since the start of the simulation (years)")
    ax_snap.set_title("(a) snapshots: each step traced on its own flows, storage release a "
                      "source term", loc="left", fontweight="bold")
    ax_track.set_title("(b) transient tracking: tagged water carried through storage",
                       loc="left", fontweight="bold")
    series_legend(fig, (0.735, 0.745))

    bottom = fig.add_gridspec(1, 4, left=0.07, right=0.89, top=0.39, bottom=0.07, wspace=0.12)
    titles = {
        "steady": "(c) steady F, first step\n(no time limit)",
        "well": "(d) to the well\nwithin 30 years",
        "other": "(e) to other sinks\nwithin 30 years",
        "stored": "(f) still stored\nafter 30 years",
    }
    axes = [fig.add_subplot(bottom[0, i]) for i in range(4)]
    for ax, (key, title) in zip(axes, titles.items()):
        image = draw_map(ax, data["first"], data["maps"][key], data["spec"], data["riv_col"],
                         data["well_node"])
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("x (km)")
    axes[0].set_ylabel("y (km)")
    for ax in axes[1:]:
        plt.setp(ax.get_yticklabels(), visible=False)
    cax = fig.add_axes((0.905, 0.07, 0.013, 0.32))
    bar = fig.colorbar(image, cax=cax)
    bar.set_label("fraction (-)")
    bar.outline.set_linewidth(0.5)
    return mfig.save(fig, out_dir, FIG_NAME)


# ---------------------------------------------------------------- driver


def main(out_dir: Path = mfig.FIG_DIR, work: Path = mfig.WORK_DIR) -> dict[str, float]:
    """Build tutorial 08's model, check the caption numbers and write Fig. 10."""
    mfig.paper_style()
    start = time.perf_counter()
    data = compute(work, mfig.find_mf6())
    computed = check_quoted(data)
    for key, value in computed.items():
        print(f"{key}: {value}")
    print("wrote", make_figure(out_dir, data))
    print(f"done in {time.perf_counter() - start:.1f} s")
    return computed


if __name__ == "__main__":
    main()
