"""Figures (PNG, light theme) and markdown summary tables of the dispersion study.

Colours follow one fixed assignment across figures: full mixing on DIS blue, face routing on
DIS orange, full mixing on DISV aqua, particles and references in neutral ink; magnitude maps
use a single-hue blue ramp; sub-step counts an ordinal blue ramp.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

import analysis as an  # noqa: E402
import problems as pb  # noqa: E402

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SURFACE = "#fcfcfb"
SERIES = {
    ("DIS", "mixing"): "#2a78d6",
    ("DIS", "routing"): "#eb6834",
    ("DISV", "mixing"): "#1baf7a",
    ("DIS", "particles"): INK,
    ("DIS", "cell_average"): "#9a9994",
    ("DISV", "cell_average"): "#9a9994",
}
LABELS = {
    ("DIS", "mixing"): "full mixing, DIS",
    ("DIS", "routing"): "face routing, DIS",
    ("DISV", "mixing"): "full mixing, DISV",
    ("DIS", "particles"): "PRT particles, DIS",
    ("DIS", "cell_average"): "cell-averaged exact zone",
}
BLUES = LinearSegmentedColormap.from_list(
    "blues", [SURFACE, "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)
ORDINAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]


def _style() -> None:
    """Set a light, recessive matplotlib style."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
        "ytick.color": MUTED, "text.color": INK, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9, "axes.titlesize": 9.5, "legend.frameon": False, "lines.linewidth": 2,
    })


def _map_panel(ax, field: np.ndarray, extent: tuple, title: str):
    """Draw one fraction map (raster, row 0 at y = 0)."""
    image = ax.imshow(field, origin="lower", extent=extent, cmap=BLUES, vmin=0, vmax=1)
    ax.set_title(title, loc="left")
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return image


def _size_axis(ax, sizes=(200, 100, 50, 25, 12.5)) -> None:
    """Log cell-size axis, finest grid on the right, ticks at the series' cell sizes."""
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.set_xticks([], minor=True)
    ax.set_xticklabels([f"{s:g}" for s in sizes])
    ax.set_xlim(260, 10)
    ax.set_xlabel("mean cell size (m)")


def analytic_maps(out: Path, fig_dir: Path, h: float = 50.0) -> None:
    """Fraction maps of problem A at cell size h for both flow directions, with the divide."""
    maps = np.load(out / "a_maps.npz")
    methods = [("DIS", "mixing"), ("DIS", "routing"), ("DISV", "mixing")]
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.6), constrained_layout=True)
    for r, angle in enumerate((0.0, 30.0)):
        spec = pb.AnalyticSpec(angle_deg=angle)
        extent = (0, spec.lx, 0, spec.ly)
        dx, dy = an.divide_line(spec)
        for c, (kind, method) in enumerate(methods):
            ax = axes[r, c]
            image = _map_panel(
                ax, maps[f"{angle:g}_{kind}_{h:g}_{method}"], extent,
                f"{LABELS[(kind, method)]}, flow at {angle:g}°",
            )
            ax.plot(dx, dy, color=INK, lw=1.2, ls="--")
            ax.set_xlim(0, spec.lx)
            ax.set_ylim(0, spec.ly)
    fig.colorbar(image, ax=axes, shrink=0.6, label="fraction of the water reaching the well")
    fig.suptitle(
        f"Problem A, h = {h:g} m: capture fraction; dashed line = analytical capture-zone edge",
        x=0.01, ha="left",
    )
    fig.savefig(fig_dir / "dispersion_analytic_maps.png", dpi=150)
    plt.close(fig)


def _series(ax, table: pd.DataFrame, key: tuple, column: str, angle=None, **kwargs) -> None:
    """Plot one metric against the mean cell size for one grid kind and method."""
    kind, method = key
    sel = (table.kind == kind) & (table.method == method)
    if angle is not None:
        sel &= table.angle == angle
    rows = table[sel].sort_values("mean_h")
    ax.plot(rows.mean_h, rows[column], color=SERIES[key], marker="o", ms=4, **kwargs)


def analytic_convergence(out: Path, fig_dir: Path) -> None:
    """Edge-band width and area errors against cell size for problem A."""
    table = pd.read_csv(out / "a_metrics.csv")
    keys = [("DIS", "mixing"), ("DIS", "routing"), ("DISV", "mixing"), ("DIS", "cell_average")]
    panels = [
        ("band_width", "width of the 0.1 < F < 0.9 band (m)", True),
        ("area_err_0.1", "relative area error, F ≥ 0.1", True),
        ("area_err_0.01", "relative area error, F ≥ 0.01", True),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), constrained_layout=True)
    for ax, (column, label, log) in zip(axes, panels):
        for key in keys:
            for angle, ls in ((0.0, "-"), (30.0, ":")):
                kwargs = {"ls": ls}
                if key[1] == "cell_average":
                    kwargs["lw"] = 1.2
                _series(ax, table, key, column, angle, **kwargs)
        _size_axis(ax)
        ax.set_yscale("log" if log else "linear")
        ax.set_title(label, loc="left")
    handles = [plt.Line2D([], [], color=SERIES[k], lw=2) for k in keys]
    handles += [plt.Line2D([], [], color=MUTED, ls=ls, lw=1.5) for ls in ("-", ":")]
    labels = [LABELS[k] for k in keys] + ["flow along the grid (0°)", "flow at 30°"]
    fig.legend(handles, labels, loc="outside lower center", ncol=3)
    fig.savefig(fig_dir / "dispersion_analytic_convergence.png", dpi=150)
    plt.close(fig)


def model1_maps(out: Path, fig_dir: Path, h: float = 50.0) -> None:
    """Recharge capture fraction of problem B: PRT on the finest grid vs the methods at h."""
    maps = np.load(out / "b_maps.npz")
    spec = pb.Model1Spec()
    extent = (0, spec.lx, 0, spec.ly)
    panels = [
        ("ref", "PRT particles, DIS 12.5 m (reference)"),
        (f"DIS_{h:g}_particles", f"PRT particles, DIS {h:g} m"),
        (f"DIS_{h:g}_mixing", f"full mixing, DIS {h:g} m"),
        (f"DIS_{h:g}_routing", f"face routing, DIS {h:g} m"),
        (f"DISV_{h:g}_mixing", f"full mixing, DISV {h:g} m"),
        ("DIS_12.5_routing", "face routing, DIS 12.5 m"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(10.0, 4.9), constrained_layout=True)
    ref = maps["ref"]
    for ax, (key, title) in zip(axes.ravel(), panels):
        image = _map_panel(ax, maps[key], extent, title)
        ax.contour(np.linspace(0, spec.lx, ref.shape[1]), np.linspace(0, spec.ly, ref.shape[0]),
                   ref, levels=[0.5], colors=INK, linewidths=1.0, linestyles="--")
        ax.plot(spec.well_x, spec.well_y, marker="o", color=INK, ms=3)
        ax.axvline(spec.riv_x, color=MUTED, lw=0.8)
        ax.set_xlim(500, spec.lx)
    label = "fraction of the cell's recharge reaching the well"
    fig.colorbar(image, ax=axes, shrink=0.6, label=label)
    fig.suptitle(
        "Problem B: recharge capture fraction (x > 500 m); dashed = reference zone edge "
        "(PRT, 0.5); grey = river",
        x=0.01, ha="left",
    )
    fig.savefig(fig_dir / "dispersion_model1_maps.png", dpi=150)
    plt.close(fig)


def model1_convergence(out: Path, fig_dir: Path) -> None:
    """Edge-band width and capture-zone agreement against cell size for problem B."""
    table = pd.read_csv(out / "b_metrics.csv")
    keys = [("DIS", "mixing"), ("DIS", "routing"), ("DISV", "mixing"), ("DIS", "particles")]
    panels = [
        ("band_width", "width of the 0.1 < F < 0.9 band (m)", "log"),
        ("area_err_0.1", "relative area error, F ≥ 0.1", "linear"),
        ("jaccard_0.5", "Jaccard index vs reference, F ≥ 0.5", "linear"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.5), constrained_layout=True)
    for ax, (column, label, scale) in zip(axes, panels):
        for key in keys:
            _series(ax, table, key, column)
        _size_axis(ax, (100, 50, 25, 12.5))
        ax.set_xlim(130, 10)
        ax.set_yscale(scale)
        ax.set_title(label, loc="left")
    handles = [plt.Line2D([], [], color=SERIES[k], lw=2) for k in keys]
    fig.legend(handles, [LABELS[k] for k in keys], loc="outside lower center", ncol=4)
    fig.savefig(fig_dir / "dispersion_model1_convergence.png", dpi=150)
    plt.close(fig)


def transient_curves(out: Path, fig_dir: Path, substeps: tuple[int, ...]) -> None:
    """Share of post-t0 water in the well per flow step, by sub-step count, and its error."""
    table = pd.read_csv(out / "t_curves.csv")
    sizes = sorted(table.h.unique(), reverse=True)
    fig, axes = plt.subplots(2, len(sizes), figsize=(10.0, 5.6), sharex=True, sharey="row",
                             constrained_layout=True, height_ratios=(1.6, 1.0))
    for c, h in enumerate(sizes):
        rows = table[table.h == h]
        prt = rows[rows.method == "particles"].fraction.to_numpy()
        ends = rows[rows.method == "particles"].t.to_numpy() / 1000
        edges = np.concatenate([[0.0], ends])
        for colour, n_sub in zip(ORDINAL, substeps):
            f = rows[rows.method == f"substeps_{n_sub}"].fraction.to_numpy()
            label = f"{n_sub} sub-step{'s' if n_sub > 1 else ''} per 2000 d flow step"
            axes[0, c].stairs(f, edges, color=colour, lw=2, label=label)
            axes[1, c].stairs(f - prt, edges, color=colour, lw=2)
        axes[0, c].stairs(prt, edges, color=INK, ls="--", lw=1.5, label="PRT particles, same grid")
        axes[1, c].axhline(0.0, color=INK, ls="--", lw=1.0)
        axes[0, c].set_title(f"DIS {h:g} m", loc="left")
        axes[1, c].set_xlabel("time since tagging started (1000 d)")
        axes[1, c].set_xlim(0, 20)
    axes[0, 0].set_ylabel("share of new water in the well")
    axes[1, 0].set_ylabel("difference to PRT")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3)
    fig.savefig(fig_dir / "dispersion_transient_substeps.png", dpi=150)
    plt.close(fig)


def make_all(out: Path, fig_dir: Path, config) -> None:
    """Make every figure of the study."""
    _style()
    analytic_maps(out, fig_dir)
    analytic_convergence(out, fig_dir)
    model1_maps(out, fig_dir)
    model1_convergence(out, fig_dir)
    transient_curves(out, fig_dir, config.substeps)


# ---------------------------------------------------------------- tables


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    """Return a DataFrame as a GitHub markdown table."""
    def cell(v):
        if isinstance(v, float):
            return f"{v:.{digits}g}" if abs(v) < 1e4 else f"{v:.0f}"
        return str(v)
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |",
             "|" + "---|" * len(frame.columns)]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


def rates(table: pd.DataFrame, by: list[str], columns: list[str]) -> pd.DataFrame:
    """Return convergence rates (slope of log error vs log h) per group."""
    out = []
    for key, rows in table.groupby(by):
        key = key if isinstance(key, tuple) else (key,)
        h = rows.mean_h.to_numpy()
        out.append({**dict(zip(by, key)),
                    **{c: an.convergence_rate(h, rows[c].to_numpy()) for c in columns}})
    return pd.DataFrame(out)


def transient_summary(curves: pd.DataFrame, substeps: tuple[int, ...]) -> pd.DataFrame:
    """Return per grid and sub-step count: mean |difference| to PRT and to the finest stepping."""
    rows = []
    for h, sel in curves.groupby("h"):
        prt = sel[sel.method == "particles"].fraction.to_numpy()
        finest = sel[sel.method == f"substeps_{max(substeps)}"].fraction.to_numpy()
        for n_sub in substeps:
            c = sel[sel.method == f"substeps_{n_sub}"]
            f = c.fraction.to_numpy()
            rows.append({
                "h": h, "substeps": n_sub, "dt_transport_d": 2000.0 / n_sub,
                "share_2000d": f[0], "share_4000d": f[1], "share_10000d": f[4],
                "mean_abs_diff_vs_prt": float(np.abs(f - prt).mean()) if prt.size else np.nan,
                "mean_abs_diff_vs_finest": float(np.abs(f - finest).mean()),
                "seconds": float(c.seconds.iloc[0]),
            })
        if prt.size:
            rows.append({"h": h, "substeps": "PRT", "share_2000d": prt[0], "share_4000d": prt[1],
                         "share_10000d": prt[4]})
    return pd.DataFrame(rows)


def write_tables(out: Path, config) -> None:
    """Write output/summary.md with the metric, share and transient tables of the study."""
    a = pd.read_csv(out / "a_metrics.csv")
    b = pd.read_csv(out / "b_metrics.csv")
    shares = pd.read_csv(out / "b_shares.csv")
    curves = pd.read_csv(out / "t_curves.csv")
    a_cols = ["angle", "kind", "h", "mean_h", "method", "area_err_0.01", "area_err_0.1",
              "area_err_0.5", "jaccard_0.5", "missed_0.1", "missed_0.5", "band_width",
              "band_cells", "smear_width", "tt_err"]
    b_cols = ["kind", "h", "mean_h", "method", "area_err_0.01", "area_err_0.1", "area_err_0.5",
              "jaccard_0.5", "missed_0.1", "missed_0.5", "band_width", "band_cells", "mean_time",
              "mean_time_to_exit_cell"]
    err_cols = ["area_err_0.01", "area_err_0.1", "band_width", "smear_width"]
    sections = [
        ("Problem A metrics", markdown_table(a[a_cols])),
        ("Problem A convergence rates (slope of log metric vs log h)",
         markdown_table(rates(a[a.method != "cell_average"], ["angle", "kind", "method"],
                              err_cols))),
        ("Problem B metrics (reference: PRT on DIS 12.5 m)", markdown_table(b[b_cols])),
        ("Problem B shares of the well water by source package", markdown_table(shares)),
        ("Transient: share of post-t0 water in the well", markdown_table(
            transient_summary(curves, config.substeps))),
    ]
    text = "\n\n".join(f"## {title}\n\n{body}" for title, body in sections)
    (out / "summary.md").write_text("# Dispersion study tables (generated)\n\n" + text + "\n")
