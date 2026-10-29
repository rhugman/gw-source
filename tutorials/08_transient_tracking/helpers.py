"""Tables and plots local to tutorial 08 (true transient tracking through storage).

The shared builders and map helpers live in tutorials/herebedragons.py; this module adds the
per-step snapshot summary of a well (tutorial 05's view, used as the contrast), the split of a
well's tagged outflow by origin, and a time-series plot of those shares.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import herebedragons as hbd  # tutorials/ is on sys.path (the notebook's first cell)

import gwsource as gs

DAYS_PER_YEAR = 365.25
STORAGE_TERMS = ("STO-SS", "STO-SY")


def step_summary(reader, boundname: str) -> pd.DataFrame:
    """Per saved step: time, well rate, recharge, storage flows and the well's snapshot shares.

    The snapshot shares are tutorial 05's view: each step traced backward on its own, with
    storage release as a source term ('storage' sums STO-SS and STO-SY).
    """
    rows = []
    for kstpkper in reader.steps:
        step = reader.read(kstpkper)
        well = gs.select(step, boundnames=[boundname])
        back = gs.backward(step, {"well": well})
        by_term = {k: float(v.sum()) for k, v in back.volume_from_by_term["well"].items()}
        total = sum(by_term.values())
        storage = gs.select(step, package=list(STORAGE_TERMS)).terms
        q_sto = step.term_flow[storage]
        row = {
            "time (yr)": step.totim / DAYS_PER_YEAR,
            "delt (d)": reader.step_length(kstpkper),
            "well rate (m3/d)": -float(step.term_flow[well.terms].sum()),
            "recharge (m3/d)": float(step.term_flow[gs.select(step, package="RCH").terms].sum()),
            "storage release (m3/d)": float(q_sto[q_sto > 0].sum()),
            "storage gain (m3/d)": -float(q_sto[q_sto < 0].sum()),
        }
        for name in ("RCH", "SFR", "CHD"):
            row[f"snapshot {name}"] = by_term.get(name, 0.0) / total
        row["snapshot storage"] = sum(by_term.get(t, 0.0) for t in STORAGE_TERMS) / total
        rows.append(row)
    return pd.DataFrame(rows, index=pd.Index(range(len(rows)), name="step"))


def origin_shares(fwd: gs.ForwardTracking, sink: str) -> pd.DataFrame:
    """Per step, the share of each tagged group in the water leaving through a sink group."""
    out = pd.DataFrame({g: fwd.outflow_to[sink][g] for g in fwd.groups})
    out.index = pd.Index(fwd.totim / DAYS_PER_YEAR, name="time (yr)")
    return out.div(out.sum(axis=1), axis=0)


def plot_shares(ax, shares: pd.DataFrame, colours: dict, title: str = "") -> None:
    """Stacked area of per-step shares (columns) against time; step ends on the x axis."""
    ax.stackplot(
        shares.index, *[shares[c] for c in shares.columns], labels=list(shares.columns),
        colors=[colours.get(c, "0.6") for c in shares.columns], step="pre", alpha=0.85,
    )
    ax.set_xlim(0.0, float(shares.index.max()))
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("time since the start (years)")
    ax.set_ylabel("share of the well's water (-)")
    ax.set_title(title)


def year_steps(totim: np.ndarray, years) -> list[int]:
    """Return the index of the step that ends closest to each given time in years."""
    t = np.asarray(totim) / DAYS_PER_YEAR
    return [int(np.argmin(np.abs(t - y))) for y in years]


def map_panels(
    grb_file, step: gs.FlowStep, panels: list, ncols: int, label: str = "", **kwargs
):
    """Map several per-cell arrays [(values, title)] side by side with one shared colour bar."""
    nrows = int(np.ceil(len(panels) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols + 1.0, 4.0 * nrows), squeeze=False)
    for ax, (values, title) in zip(axes.ravel(), panels):
        hbd.plot_cells(grb_file, step, values, ax=ax, title=title, overlay=False, colorbar=False,
                       **kwargs)
        hbd.overlay_features(ax, grb_file, step, packages=("SFR", "WEL"), legend=False)
    for ax in axes.ravel()[len(panels):]:
        ax.axis("off")
    fig.colorbar(axes[0, 0].collections[0], ax=axes, shrink=0.8, label=label)
    return fig, axes
