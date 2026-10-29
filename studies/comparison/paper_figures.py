"""Paper figures of the comparison between full-mixing tracing and particle tracking.

Two figures at Groundwater sizes (7 in wide, 300 dpi PNG), drawn from stored results only:

- fig_comparison_synthetic.png, the synthetic 3D study (this folder, output/tables, fields and
  references): (a)-(e) capture-probability maps of one case (lower-half screen, stream near,
  25 m cells, 4 layers), (f) RMSE against the advective reference vs dx / W, (g) RMSE against
  the dispersive reference vs dx / sqrt(alpha_T L), (h) closure of the far-stream cases by
  layer count.
- fig_neversink_window.png, the Neversink window study (main checkout's
  studies/neversink/output/window): (a)-(d) maps of F and P at 50 m with 4 layers and at 12.5 m
  with 16 layers, with the published U area outlined; (e) start cells above 0.5 per run;
  (f) overlap of the F > 0.5 and P > 0.5 areas in the same run.

Capture probability uses one map in both figures: viridis in the classes of the paper's F maps
(edges 0.01, 0.1, 0.25, 0.5, 0.75, 1; grey below 0.01). Method colours follow the house
palette: full mixing blue, particles orange (stopped at weak sinks: squares, dashed; passing:
triangles, solid), full mixing with every sink strong aqua.

Run with the project environment from the repository root of this checkout:

    PYTHONPATH=src python studies/comparison/paper_figures.py
"""

import importlib.util
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import model as m  # noqa: E402
import runs  # noqa: E402
import scoring  # noqa: E402

REPO = HERE.parents[1]


def main_checkout(repo: Path = REPO, probe: str = "studies/neversink/output/window") -> Path:
    """Return the checkout that holds the untracked outputs: this one, or the main checkout
    that holds this worktree (.claude/worktrees/<name>)."""
    for root in (repo, *repo.parents):
        if (root / probe).is_dir():
            return root
    raise FileNotFoundError(f"no checkout above {repo} holds {probe}")


MAIN_REPO = main_checkout()
SYN_OUT = HERE / "output"
NEV_DIR = REPO / "studies" / "neversink"
NEV_OUT = MAIN_REPO / "studies" / "neversink" / "output" / "window"
FIG_OUT = MAIN_REPO / "docs" / "paper" / "overleaf" / "figures_2026-10-27"

WIDTH = 7.0  # in, Groundwater full width
DPI = 300
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ACTIVE_FILL = "#e9e8e4"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
STREAM = "#3987e5"
WELL = "#e34948"
CAPTURE_EDGES = (0.01, 0.1, 0.25, 0.5, 0.75, 1.0)
CAPTURE_CMAP = "viridis"
HALO = [patheffects.withStroke(linewidth=2.2, foreground="white")]

# method key: (label, colour, marker, line style)
SYN_METHODS = {
    "F": ("full mixing (F)", BLUE, "o", "-"),
    "PRT 27 stop": ("particles, stopped at weak sinks", ORANGE, "s", "--"),
    "PRT 27 pass": ("particles, passing weak sinks", ORANGE, "^", "-"),
}
NEV_METHODS = {
    "F_gross": ("full mixing (F)", BLUE, "o", "-"),
    "F_gross_strong": ("full mixing, every sink strong", AQUA, "D", ":"),
    "P": ("particles, stopped at weak sinks", ORANGE, "s", "--"),
}

MAP_CASE = m.Case(25.0, 4, "lower", "near")
MAP_WINDOW = (0.0, 1500.0, 250.0, 950.0)  # x0, x1, y0, y1 (m)
ALPHA_SHOWN = 1.0  # m, dispersive reference on the maps
CLOSURE_STREAM = "far"

NEV_CELL = 50.0  # m, regional cell size
NEV_NLAY = 4
NEV_MAP_RUNS = ("n1z1_chd", "n4z4_chd")
# runs in plot order: 4 layers (50, 25, 12.5 m), 25 m (8, 16, 32 layers), 12.5 m (8, 16 layers)
NEV_GROUPS = (("n1z1_chd", "n2z1_chd", "n4z1_chd"), ("n2z2_chd", "n2z4_chd", "n2z8_chd"),
              ("n4z2_chd", "n4z4_chd"))
NEV_MAP_PAD = 12  # regional cells around the published area on the maps
AREA_T = 0.5


def style() -> None:
    """Set the paper style: sans-serif 7-8 pt, thin recessive axes, no frame on legends."""
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 7.5, "axes.titlesize": 7.5,
        "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "axes.linewidth": 0.6, "axes.edgecolor": MUTED,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK, "ytick.labelcolor": INK, "grid.color": GRID,
        "grid.linewidth": 0.5, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "lines.linewidth": 1.2, "lines.markersize": 4.0,
    })


def capture_scale() -> tuple[ListedColormap, BoundaryNorm]:
    """Return the classed capture-probability map (grey below 0.01, white for no data)."""
    edges = np.array(CAPTURE_EDGES)
    colors = plt.get_cmap(CAPTURE_CMAP)(np.linspace(0.0, 1.0, len(edges) - 1))
    cmap = ListedColormap(colors).with_extremes(under=ACTIVE_FILL, bad="white")
    return cmap, BoundaryNorm(edges, cmap.N)


def letter(ax: plt.Axes, text: str, inside: bool = False) -> None:
    """Write a panel letter at the top left of an axes."""
    if inside:
        ax.text(0.02, 0.96, text, transform=ax.transAxes, ha="left", va="top", color=INK,
                fontweight="bold", path_effects=HALO)
    else:
        ax.set_title(text, loc="left", fontweight="bold")


def capture_colorbar(fig: plt.Figure, cax: plt.Axes, image) -> None:
    """Draw the horizontal capture-probability colour bar."""
    bar = fig.colorbar(image, cax=cax, orientation="horizontal", extend="min",
                       ticks=CAPTURE_EDGES)
    bar.ax.set_xticklabels([f"{t:g}" for t in CAPTURE_EDGES])
    bar.set_label("capture probability (grey: below 0.01)")
    bar.outline.set_linewidth(0.5)


def plain_log_axis(ax: plt.Axes, ticks: tuple, axis: str = "x") -> None:
    """Log axis with plain tick labels."""
    if axis == "x":
        ax.set_xscale("log")
        ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    else:
        ax.set_yscale("log")
        ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.minorticks_off()


# ---------------------------------------------------------------- synthetic study


def synthetic_maps(case: m.Case = MAP_CASE, out: Path = SYN_OUT) -> tuple[list, np.ndarray]:
    """Return the five map fields (label, coarse field) and the fine advective reference."""
    rech = m.Design().rech
    refs = out / "references"
    adv = np.load(refs / f"adv_{case.physical}.npz")["PRT 27 well"]
    disp_dx = runs.DISP_DX[-1]
    disp_name = f"disp_{case.physical}_dx{disp_dx:g}".replace(".", "p")
    disp = np.load(refs / f"{disp_name}.npz")[f"R_disp {ALPHA_SHOWN:g}"]
    fields = np.load(out / "fields" / f"{case.label}.npz")

    def mapped(fine: np.ndarray, fine_dx: float) -> np.ndarray:
        weight = np.full(fine.shape, rech * fine_dx**2)
        return scoring.to_coarse(fine, weight, scoring.block_factor(fine_dx, case.dx))

    panels = [
        ("advective reference", mapped(adv, runs.REF_DX)),
        (f"dispersive reference, $\\alpha_T$ = {ALPHA_SHOWN:g} m", mapped(disp, disp_dx)),
        (SYN_METHODS["F"][0], fields["F"]),
        (SYN_METHODS["PRT 27 stop"][0], fields["PRT 27 stop"]),
        (SYN_METHODS["PRT 27 pass"][0], fields["PRT 27 pass"]),
    ]
    return panels, adv


def draw_synthetic_map(ax: plt.Axes, field: np.ndarray, adv: np.ndarray, case: m.Case,
                       window: tuple = MAP_WINDOW):
    """Map one coarse field with the advective 0.5 edge, the stream and the well."""
    d = m.Design()
    cmap, norm = capture_scale()
    image = ax.imshow(field, extent=(0, d.lx, 0, d.ly), origin="upper", cmap=cmap, norm=norm,
                      interpolation="nearest")
    xr = (np.arange(adv.shape[1]) + 0.5) * runs.REF_DX
    yr = d.ly - (np.arange(adv.shape[0]) + 0.5) * runs.REF_DX
    edge = ax.contour(xr, yr, adv, levels=[0.5], colors=INK, linewidths=0.8)
    edge.set(path_effects=HALO)
    ax.plot([d.stream_x[case.stream]] * 2, [window[2], window[3]], color=STREAM, lw=1.0,
            path_effects=HALO)
    ax.plot(d.well_x, d.well_y, "o", ms=4, mfc=WELL, mec=INK, mew=0.5)
    ax.set_xlim(window[0], window[1])
    ax.set_ylim(window[2], window[3])
    ax.set_aspect("equal")
    ax.set_xticks([0, 500, 1000, 1500])
    ax.set_yticks([400, 600, 800])
    return image


def ratio_jitter(method: str) -> float:
    """Return a small multiplicative x offset per method so stacked points stay visible."""
    return {"F": 0.95, "PRT 27 stop": 1.0, "PRT 27 pass": 1.05}[method]


def panel_rmse_adv(ax: plt.Axes, scores: pd.DataFrame) -> None:
    """RMSE against the advective reference vs dx / W, every coarse run; fill: layer count."""
    adv = scores[scores["reference"] == "R_adv"]
    for method, (_, colour, marker, _) in SYN_METHODS.items():
        part = adv[adv["method"] == method]
        for few in (True, False):
            sub = part[(part["nlay"] <= 2) == few]
            ax.scatter(sub["dx_over_w"] * ratio_jitter(method), sub["rmse"], s=14,
                       marker=marker, facecolor="white" if few else colour, edgecolor=colour,
                       lw=0.7, alpha=0.9, zorder=3)
    plain_log_axis(ax, (0.025, 0.05, 0.1, 0.2, 0.4))
    ax.set_ylim(0, None)
    ax.set_xlabel("$\\Delta x$ / W")
    ax.set_ylabel("RMSE against the advective reference")
    ax.grid(True, axis="y")


def panel_rmse_disp(ax: plt.Axes, scores: pd.DataFrame) -> None:
    """Mean RMSE against each dispersive reference vs dx / sqrt(alpha_T L), one line per alpha_T."""
    disp = scores[scores["reference"].str.startswith("R_disp")]
    means = (disp[disp["method"].isin(SYN_METHODS)]
             .groupby(["method", "alpha_t", "dx"])[["dx_over_disp", "rmse"]].mean()
             .reset_index())
    for method, (_, colour, marker, ls) in SYN_METHODS.items():
        for alpha in runs.ALPHA_T:
            rows = means[(means["method"] == method) & (means["alpha_t"] == alpha)]
            rows = rows.sort_values("dx")
            ax.plot(rows["dx_over_disp"], rows["rmse"], ls=ls, marker=marker, color=colour,
                    mfc=colour, mec=colour)
    # label each group in the empty band under the lines, with a vertical leader to the left
    # end of its full-mixing line; two rows keep the labels apart
    rows_y = {max(runs.ALPHA_T): 0.045, 1.0: 0.085, min(runs.ALPHA_T): 0.045}
    for alpha in runs.ALPHA_T:
        rows = means[(means["method"] == "F") & (means["alpha_t"] == alpha)].sort_values("dx")
        x0, y0 = rows["dx_over_disp"].iloc[0], rows["rmse"].iloc[0]
        leftmost = alpha == max(runs.ALPHA_T)
        ax.annotate(f"$\\alpha_T$ = {alpha:g} m", (x0, y0), xytext=(x0, rows_y[alpha]),
                    textcoords="data", ha="left" if leftmost else "center", va="top",
                    fontsize=6.5, color=MUTED,
                    arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5,
                                "shrinkA": 1, "shrinkB": 3})
    plain_log_axis(ax, (0.1, 0.3, 1.0, 3.0, 10.0))
    ax.set_ylim(0, None)
    ax.set_xlabel("$\\Delta x$ / $\\sqrt{\\alpha_T L}$")
    ax.set_ylabel("RMSE against the dispersive reference")
    ax.grid(True, axis="y")


def panel_closure(ax: plt.Axes, coarse: pd.DataFrame, stream: str = CLOSURE_STREAM) -> None:
    """Closure of the far-stream runs by layer count: mean, with the range over cell sizes and
    screens as a bar."""
    part = coarse[(coarse["stream"] == stream) & coarse["method"].isin(SYN_METHODS)]
    stats = part.groupby(["method", "nlay"])["closure"].agg(["mean", "min", "max"]).reset_index()
    ax.axhline(1.0, color=INK, lw=0.6)
    offsets = {"F": 0.94, "PRT 27 stop": 1.0, "PRT 27 pass": 1.06}
    for method, (_, colour, marker, ls) in SYN_METHODS.items():
        rows = stats[stats["method"] == method].sort_values("nlay")
        x = rows["nlay"] * offsets[method]
        ax.errorbar(x, rows["mean"], yerr=[rows["mean"] - rows["min"], rows["max"] - rows["mean"]],
                    ls=ls, marker=marker, color=colour, mfc=colour, mec=colour, elinewidth=0.7,
                    capsize=0)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8], ["1", "2", "4", "8"])
    ax.minorticks_off()
    ax.set_ylim(0, 1.5)
    ax.set_xlabel("layers")
    ax.set_ylabel("water traced to the well / pumping")
    ax.grid(True, axis="y")


def fig_synthetic(path: Path, out: Path = SYN_OUT) -> None:
    """Figure A: maps of one case, the two error panels and the closure panel."""
    scores = pd.read_csv(out / "tables" / "scores.csv")
    coarse = pd.read_csv(out / "tables" / "coarse_runs.csv")
    panels, adv = synthetic_maps(out=out)
    fig = plt.figure(figsize=(WIDTH, 6.1), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(1.08, 1.0))
    maps = top.subplots(2, 3, sharex=True, sharey=True)
    for k, (ax, (label, field)) in enumerate(zip(maps.ravel(), panels)):
        image = draw_synthetic_map(ax, field, adv, MAP_CASE)
        ax.set_title(f"({'abcde'[k]}) {label}", loc="left")
    for ax in maps[:, 0]:
        ax.set_ylabel("y (m)")
    for ax in maps[1]:
        ax.set_xlabel("x (m)")
    key = maps[1, 2]
    key.set_axis_off()
    cax = key.inset_axes((0.05, 0.62, 0.9, 0.1))
    capture_colorbar(fig, cax, image)
    handles = [
        Line2D([], [], color=INK, lw=0.8, path_effects=HALO,
               label="advective reference, 0.5 contour"),
        Line2D([], [], color=STREAM, lw=1.0, label="stream"),
        Line2D([], [], ls="", marker="o", ms=4, mfc=WELL, mec=INK, mew=0.5, label="well"),
    ]
    key.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.05))
    axes = bottom.subplots(1, 3)
    panel_rmse_adv(axes[0], scores)
    panel_rmse_disp(axes[1], scores)
    panel_closure(axes[2], coarse)
    for ax, tag in zip(axes, "fgh"):
        letter(ax, f"({tag})")
    handles = [Line2D([], [], color=c, ls=ls, marker=mk, mfc=c, mec=c, label=lab)
               for lab, c, mk, ls in SYN_METHODS.values()]
    handles += [Line2D([], [], ls="", marker="o", mfc="white", mec=MUTED, label="1 or 2 layers"),
                Line2D([], [], ls="", marker="o", mfc=MUTED, mec=MUTED, label="4 or 8 layers")]
    bottom.legend(handles=handles, loc="outside lower center", ncol=5, handlelength=2.4,
                  columnspacing=1.2)
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------- Neversink window


def neversink_workflow():
    """Return studies/neversink/workflow.py as a module (it shares its name with this folder's)."""
    spec = importlib.util.spec_from_file_location("neversink_workflow", NEV_DIR / "workflow.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def regional_shape(dis_file: Path) -> tuple[int, int, int]:
    """Return (nlay, nrow, ncol) from the DIMENSIONS block of a DIS file."""
    dims = {}
    for line in dis_file.read_text().splitlines():
        words = line.split()
        if len(words) == 2 and words[0].upper() in ("NLAY", "NROW", "NCOL"):
            dims[words[0].upper()] = int(words[1])
    return dims["NLAY"], dims["NROW"], dims["NCOL"]


def published_starts(nw, window: dict, shape: tuple) -> pd.Series:
    """Return the published U mask of the start cells inside the window, without its edge
    (as window.scored_starts)."""
    endpoints = nw.read_endpoints()
    _, nrow, ncol = shape
    r, c = np.divmod(endpoints["node0"].to_numpy() % (nrow * ncol), ncol)
    inside = ((r >= window["r0"] + 1) & (r <= window["r1"] - 1)
              & (c >= window["c0"] + 1) & (c <= window["c1"] - 1))
    u_nodes = [n for w, n in nw.PRIORITY_WELLS.items() if w.startswith("U")]
    mask = nw.mp7_mask(endpoints, u_nodes)
    assert mask[~inside].sum() == 0, "published U cells outside the window"
    return pd.Series(mask[inside], index=endpoints["node0"].to_numpy()[inside])


def u_wells(wel_file: Path) -> pd.DataFrame:
    """Return the U wells' 0-based row and column from the regional WEL list."""
    wells = pd.read_csv(wel_file, sep=r"\s+", comment="#", names=["k", "i", "j", "q", "name"])
    wells = wells[wells["name"].str.startswith("U")].copy()
    wells[["i", "j"]] -= 1
    return wells


def plan_image(values: pd.Series, window: dict, shape: tuple) -> np.ndarray:
    """Return a (row, column) image of the window with each start cell's value (NaN elsewhere)."""
    _, nrow, ncol = shape
    image = np.full((window["r1"] - window["r0"] + 1, window["c1"] - window["c0"] + 1), np.nan)
    r, c = np.divmod(values.index.to_numpy() % (nrow * ncol), ncol)
    image[r - window["r0"], c - window["c0"]] = values.to_numpy()
    return image


def run_label(run: str, sep: str = ", ") -> str:
    """Return 'cell size, layers' of a run name such as n2z1_chd."""
    n, nz = (int(v) for v in run.split("_")[0][1:].split("z"))
    return f"{NEV_CELL / n:g} m{sep}{NEV_NLAY * nz} layers"


def neversink_maps(fig: plt.Figure, axes: np.ndarray, cells: pd.DataFrame,
                   published: pd.Series, window: dict, shape: tuple, wells: pd.DataFrame):
    """Map F and P of the first and last map runs, cropped to the published area plus a pad."""
    cmap, norm = capture_scale()
    pub = plan_image(published.astype(float), window, shape)
    box = np.argwhere(np.nan_to_num(pub) > 0)
    i0, i1 = box[:, 0].min() - NEV_MAP_PAD, box[:, 0].max() + NEV_MAP_PAD
    j0, j1 = box[:, 1].min() - NEV_MAP_PAD, box[:, 1].max() + NEV_MAP_PAD
    assert i0 >= 0 and j0 >= 0 and i1 < pub.shape[0] and j1 < pub.shape[1], "crop off window"
    km = NEV_CELL / 1e3
    extent = (0.0, (j1 - j0 + 1) * km, 0.0, (i1 - i0 + 1) * km)
    yy, xx = np.mgrid[i0 : i1 + 1, j0 : j1 + 1]
    x_c, y_c = (xx - j0 + 0.5) * km, (i1 - yy + 0.5) * km
    wx = (wells["j"] - window["c0"] - j0 + 0.5) * km
    wy = (i1 - (wells["i"] - window["r0"]) + 0.5) * km
    rows = (("F_gross", NEV_METHODS["F_gross"][0]), ("P", NEV_METHODS["P"][0]))
    for a, (method, label) in enumerate(rows):
        for b, run in enumerate(NEV_MAP_RUNS):
            ax = axes[a, b]
            frame = cells[cells["run"] == run].set_index("node0").loc[published.index]
            image = plan_image(frame[method], window, shape)[i0 : i1 + 1, j0 : j1 + 1]
            im = ax.imshow(image, cmap=cmap, norm=norm, extent=extent, origin="upper",
                           interpolation="nearest")
            edge = ax.contour(x_c, y_c, np.nan_to_num(pub[i0 : i1 + 1, j0 : j1 + 1]),
                              levels=[0.5], colors=INK, linewidths=0.8)
            edge.set(path_effects=HALO)
            ax.plot(wx, wy, "o", ls="", ms=3.5, mfc=WELL, mec=INK, mew=0.5)
            letter(ax, f"({'abcd'[2 * a + b]})", inside=True)
            if a == 0:
                ax.set_title(run_label(run))
            if b == 0:
                ax.set_ylabel(f"{label}\nkm")
            if a == 1:
                ax.set_xlabel("km")
    return im


def refinement_x() -> tuple[np.ndarray, list[str]]:
    """Return x positions with a gap between the run groups, and the runs in that order."""
    x, order, pos = [], [], 0.0
    for group in NEV_GROUPS:
        for run in group:
            x.append(pos)
            order.append(run)
            pos += 1.0
        pos += 0.6
    return np.array(x), order


def refinement_axis(ax: plt.Axes, x: np.ndarray, order: list[str]) -> None:
    """Label the run axis with cell size and layer count."""
    ax.set_xticks(x, [run_label(r, "\n").replace(" m", "").replace(" layers", "")
                      for r in order])
    ax.set_xlim(x[0] - 0.5, x[-1] + 0.5)
    ax.grid(True, axis="y")


def panel_cells(ax: plt.Axes, refinement: pd.DataFrame, published_cells: int) -> None:
    """Start cells above 0.5 per run and method, with the published count as a line."""
    x, order = refinement_x()
    table = refinement.set_index("run").loc[order]
    ax.axhline(published_cells, color=INK, lw=0.8, ls="-.")
    ax.annotate(f"published area, {published_cells} cells", (x[-1] + 0.4, published_cells),
                xytext=(0, 3), textcoords="offset points", ha="right", va="bottom",
                fontsize=6.5, color=INK)
    starts = np.r_[0, np.cumsum([len(g) for g in NEV_GROUPS])]
    for method, (label, colour, marker, ls) in NEV_METHODS.items():
        for s0, s1 in zip(starts[:-1], starts[1:]):
            ax.plot(x[s0:s1], table[f"{method}_cells"].to_numpy()[s0:s1], ls=ls, marker=marker,
                    color=colour, mfc=colour, mec=colour, label=label if s0 == 0 else None)
    refinement_axis(ax, x, order)
    ax.set_ylim(0, 800)
    ax.set_ylabel("start cells above 0.5")
    ax.legend(loc="lower right")


def panel_agreement(ax: plt.Axes, refinement: pd.DataFrame) -> None:
    """Overlap of the F > 0.5 and P > 0.5 areas of the same run."""
    x, order = refinement_x()
    table = refinement.set_index("run").loc[order]
    starts = np.r_[0, np.cumsum([len(g) for g in NEV_GROUPS])]
    for s0, s1 in zip(starts[:-1], starts[1:]):
        ax.plot(x[s0:s1], table["F_gross_vs_P_same_run_jaccard"].to_numpy()[s0:s1], ls="-",
                marker="o", color=MUTED, mfc=MUTED, mec=MUTED)
    refinement_axis(ax, x, order)
    ax.set_ylim(0, 1)
    ax.set_ylabel("overlap of the F and P areas\nabove 0.5 in the same run")


def fig_neversink(path: Path, out: Path = NEV_OUT) -> None:
    """Figure B: maps of F and P at two resolutions, cells above 0.5 and F-P overlap by run."""
    nw = neversink_workflow()
    shape = regional_shape(nw.MODEL_SRC / f"{nw.MODEL}.dis")
    window = json.loads((out / "run_log.json").read_text())["window"]
    published = published_starts(nw, window, shape)
    cells = pd.read_csv(out / "start_cells.csv.gz")
    refinement = pd.read_csv(out / "refinement.csv")
    wells = u_wells(nw.MODEL_SRC / "wel_000.dat")
    fig = plt.figure(figsize=(WIDTH, 4.6), layout="constrained")
    left, right = fig.subfigures(1, 2, width_ratios=(1.25, 1.0))
    maps = left.subplots(2, 2, sharex=True, sharey=True)
    image = neversink_maps(fig, maps, cells, published, window, shape, wells)
    bar = left.colorbar(image, ax=maps, orientation="horizontal", location="bottom",
                        extend="min", ticks=CAPTURE_EDGES, shrink=0.85, aspect=30)
    bar.ax.set_xticklabels([f"{t:g}" for t in CAPTURE_EDGES])
    bar.set_label("capture probability (grey: below 0.01)")
    bar.outline.set_linewidth(0.5)
    handles = [Line2D([], [], color=INK, lw=0.8, path_effects=HALO, label="published area"),
               Line2D([], [], ls="", marker="o", ms=3.5, mfc=WELL, mec=INK, mew=0.5,
                      label="wells of cluster U")]
    left.legend(handles=handles, loc="outside lower center", ncol=2)
    axes = right.subplots(2, 1, sharex=True)
    panel_cells(axes[0], refinement, int(published.sum()))
    panel_agreement(axes[1], refinement)
    axes[0].tick_params(labelbottom=False)
    axes[1].set_xlabel("cell size (m), above, and layers, below")
    letter(axes[0], "(e)")
    letter(axes[1], "(f)")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def main(synthetic: bool = True, neversink: bool = True, out_dir: Path = FIG_OUT) -> None:
    """Draw the two paper figures into out_dir."""
    style()
    out_dir.mkdir(parents=True, exist_ok=True)
    if synthetic:
        fig_synthetic(out_dir / "fig_comparison_synthetic.png")
    if neversink:
        fig_neversink(out_dir / "fig_neversink_window.png")


if __name__ == "__main__":
    main()
