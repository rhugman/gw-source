"""Gallery figure of the reduced paper: one full-width figure with every type of output the
examples produce, and a single-column crop of the method schematic.

Each panel answers one question about the supply well of the tutorial aquifer (40 x 40 cells
of 50 m, a river at x = 1.5 km, a west edge of fixed head and an 800 m3/d well):

- (a) Which area? The backward fraction F (Fig. 2a of the full draft).
- (b) From which source? The well's water by source term (Fig. 2c).
- (c) Where does it go? The forward fraction G of the recharge on a field (Fig. 4b).
- (d) How long? The mean travel time to the well inside the F > 0.5 area (Fig. 7a).
- (e) Through the seasons? Nested zones from 36 seasonal snapshots (Fig. 6e).
- (f) Within 30 years? The backward fraction in time w from transient tracking (Fig. 9d).
- (g) How sure? The probability of contribution from the PEST++ IES posterior (Fig. 10b).
- (h) On an unstructured grid? F on the vorflow Voronoi (DISV) grid (Fig. 5b).

The panels reuse the compute functions of studies/paper/example_figures.py (Figs 2 to 6),
example_figures_b.py (Figs 7 and 10) and transient_figure.py (Fig. 9), so they show the same
numbers; the QUOTED dicts of those scripts are asserted again here, and this figure's own
caption numbers are in QUOTED. Panel (g) reuses the PEST++ IES output of example_figures_b.py
(copied into this script's workspace), so PEST++ does not run again.

All maps share the 2 km x 2 km extent, the sky-blue river cells and the white well star of
example_figures.py, and are drawn in model metres with km ticks on the outer panels only.

The method crop draws panel (b) of Fig. 1 alone (method_figures.draw_graph), one column wide.

    PYTHONPATH=src:tutorials:studies/paper python studies/paper/gallery_figure.py
"""

import shutil
import sys
import time
from pathlib import Path

import numpy as np

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import example_figures as ef  # noqa: E402
import example_figures_b as efb  # noqa: E402
import method_figures as mfig  # noqa: E402
import transient_figure as tf  # noqa: E402

import gwsource as gs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm, Normalize  # noqa: E402

WORK_DIR = mfig.WORK_DIR / "gallery_figure"
IES_MASTER = efb.WORK_DIR / "fig10" / "master"  # PEST++ IES output of example_figures_b.py
FIG_NAME = "fig_gallery"
METHOD_NAME = "fig_method_single"
WELL = "supply_well"
YEAR = 365.25  # days
EXTENT = 2000.0  # m, every map
FULL_WIDTH = 6.75  # in, 17.15 cm
SINGLE_WIDTH = 8.25 / 2.54  # in
TRAVEL_NORM = (0.1, 100.0)  # years
ZONE_YEARS = (5, 25)
ZONE_LABEL_XY = {25: (860.0, 1000.0)}  # m, inline contour label of (d)
ZONE_NOTE_XY = {5: ((1300.0, 830.0), (1180.0, 420.0))}  # m, (contour point, label) of (d)
ZONE_COLOUR = "tab:cyan"
G_LEVELS = (1e-3, 1.0)  # log range of G in (c)
PROB_CMAP = "YlGnBu"
TRUTH_COLOUR = "tab:red"
GRID_LINE = (1.0, 1.0, 1.0, 0.35)  # cell edges of the Voronoi grid in (h)
SOURCE_NAMES = {"RCH": "recharge", "CHD": "west edge", "RIV": "river"}
TITLES = {  # question (bold), output type (plain)
    "a": ("(a) Which area?", "backward fraction F"),
    "b": ("(b) From which source?", "volume from (m³/d)"),
    "c": ("(c) Where does it go?", "forward fraction G of a field"),
    "d": ("(d) How long?", "mean travel time, F > 0.5"),
    "e": ("(e) Through the seasons?", "nested zones, 36 steps"),
    "f": ("(f) Within 30 years?", "fraction in time w"),
    "g": ("(g) How sure?", "probability P(F > 0.5)"),
    "h": ("(h) Unstructured grid?", "F on a Voronoi grid"),
}

# Numbers the caption and the panels state: {name: (value, decimals)}; the computed value must
# round (half up) to the value at that many decimals.
QUOTED = {
    "pumping (m3/d)": (800, 0),
    "recharge (m3/d)": (569, 0), "west edge (m3/d)": (118, 0), "river (m3/d)": (113, 0),
    "recharge share (%)": (71, 0), "west edge share (%)": (15, 0), "river share (%)": (14, 0),
    "F contours": ((0.1, 0.5), 0),
    "zone years": ((5, 25), 0),
    "seasonal steps": (36, 0),
    "years tracked": (30, 0),
    "realisations": (50, 0),
}


# ---------------------------------------------------------------- computation


def seed_ies_output(work: Path, master: Path = IES_MASTER) -> None:
    """Copy the PEST++ IES output of example_figures_b.py into this workspace, once."""
    target = work / "fig10" / "master"
    if (target / "case.phi.actual.csv").is_file():
        return
    assert (master / "case.phi.actual.csv").is_file(), \
        f"{master} has no PEST++ output: run example_figures_b.py first"
    shutil.copytree(master, target, dirs_exist_ok=True)


def map_layer(grb_file: Path, step: gs.FlowStep, values: np.ndarray, well_cells,
              hbd) -> dict:
    """Return what a map panel draws: grid file, step, values, river and well cells."""
    return {"grb": grb_file, "step": step, "values": values,
            "river": hbd.feature_cells(step, "RIV"), "well": np.atleast_1d(well_cells)}


def compute_steady(hbd, work: Path, mf6: Path) -> dict:
    """Panels (a), (b), (c) and (h): quickstart, forward and grid examples; check Figs 2, 4, 5."""
    quick = ef.compute_quickstart(hbd, work, mf6)
    ef.check_quoted(ef.quickstart_values(quick), ef.QUOTED["fig2"])
    fwd = ef.compute_forward(hbd, work, mf6)
    ef.check_quoted(ef.forward_values(fwd), ef.QUOTED["fig4"])
    grids = ef.compute_grids(hbd, work, mf6)
    ef.check_quoted(ef.grids_values(hbd, grids), ef.QUOTED["fig5"])
    disv_run, disv_step = grids["runs"]["DISV"], grids["steps"]["DISV"]
    disv_res = grids["results"]["DISV"]
    table = quick["by_source"]
    return {
        "a": map_layer(quick["run"].grb_file, quick["step"], quick["f"], quick["well_cell"], hbd),
        "b": {"volume": table["volume_from"].rename(SOURCE_NAMES),
              "share": table["share"].rename(SOURCE_NAMES),
              "pumping": quick["res"].destination_inflow[WELL]},
        "c": {**map_layer(fwd["run"].grb_file, fwd["step"],
                          fwd["field_fwd"].source_fraction["field"], fwd["well_cell"], hbd),
              "spec": fwd["run"].spec},
        "h": {**map_layer(disv_run.grb_file, disv_step, disv_res.fraction_through[WELL],
                          np.flatnonzero(disv_res.selections[WELL].cells), hbd)},
    }


def compute_travel_time(hbd, work: Path, mf6: Path) -> dict:
    """Panel (d): mean travel time inside F > 0.5 (Fig. 7a); check Fig. 7."""
    data = efb.compute_fig7(work, mf6)
    values = efb.fig7_values(data)
    efb.check_quoted(values, efb.QUOTED_FIG7, "Fig. 7")
    assert ZONE_YEARS == efb.ZONE_YEARS, "the zones of Fig. 7"
    f = data["res"].fraction_through[WELL]
    years = np.where(f > efb.CAPTURE_F, data["tt"].mean_time[WELL], np.nan) / YEAR
    return map_layer(data["run"].grb_file, data["step"], years, data["well_cell"], hbd)


def compute_season_zones(hbd, work: Path, mf6: Path) -> dict:
    """Panel (e): nested zones from the seasonal snapshots (Fig. 6e); check Fig. 6."""
    data = ef.compute_seasons(hbd, work, mf6)
    values = ef.seasons_values(data)
    ef.check_quoted(values, ef.QUOTED["fig6"])
    run, stats = data["run"], data["stats"]
    wells = np.array(list(run.info["well_nodes"].values()))
    return {**map_layer(run.grb_file, stats.template, ef.nested_zones(stats), wells, hbd),
            "seasons": list(data["snapshots"]), "seasonal steps": values["seasonal steps"]}


def compute_time_limited(hbd, work: Path, mf6: Path) -> dict:
    """Panel (f): the fraction in time w for 30 years (Fig. 9d); check Fig. 9."""
    data = tf.compute(work, mf6)
    tf.check_quoted(data)
    grb = work / "tutorial08_transient" / "transient.dis.grb"
    return {**map_layer(grb, data["first"], data["maps"]["well"], data["well_node"], hbd),
            "years tracked": tf.N_YEARS}


def compute_probability(hbd, work: Path, mf6: Path) -> dict:
    """Panel (g): posterior probability of contribution (Fig. 10b); check Fig. 10."""
    seed_ies_output(work)
    data = efb.compute_fig10(work, mf6, mf6.parent / "pestpp-ies", run_ies=False)
    efb.check_quoted(efb.fig10_values(data), efb.QUOTED_FIG10, "Fig. 10")
    spec = data["spec"]
    posterior = data["ensembles"]["posterior"]
    return {**map_layer(data["base"].grb_file, data["base_step"], posterior["prob"],
                        spec.node(spec.wells[0][1]), hbd),
            "truth": data["truth_res"].fraction_through[WELL],
            "realisations": len(posterior["table"])}


def compute_panels(work: Path = WORK_DIR) -> dict:
    """Build every example model, assert the source figures' numbers; return the panels."""
    hbd, _ = ef.import_tutorial_modules()
    mf6 = mfig.find_mf6()
    panels = compute_steady(hbd, work, mf6)
    panels["d"] = compute_travel_time(hbd, work, mf6)
    panels["e"] = compute_season_zones(hbd, work, mf6)
    panels["f"] = compute_time_limited(hbd, work, mf6)
    panels["g"] = compute_probability(hbd, work, mf6)
    return panels


def check_quoted(computed: dict, quoted: dict) -> None:
    """Assert that every quoted number is the computed value rounded half up (tuples: equal)."""
    for name, (value, decimals) in quoted.items():
        got = computed[name]
        if isinstance(value, tuple):
            assert tuple(got) == value, f"{name}: drawn {got}, quoted {value}"
            continue
        assert abs(ef.round_half_up(got, decimals) - value) < 1e-9, \
            f"{name}: computed {got}, quoted {value}"
    print(f"gallery: {len(quoted)} quoted numbers match")


def gallery_values(panels: dict, thresholds: tuple = ef.THRESHOLDS,
                   zone_years: tuple = ZONE_YEARS) -> dict:
    """Return the computed (or drawn) value of every QUOTED key."""
    b = panels["b"]
    values = {"pumping (m3/d)": b["pumping"],
              "F contours": thresholds, "zone years": zone_years,
              "seasonal steps": panels["e"]["seasonal steps"],
              "years tracked": panels["f"]["years tracked"],
              "realisations": panels["g"]["realisations"]}
    for name in SOURCE_NAMES.values():
        values[f"{name} (m3/d)"] = float(b["volume"][name])
        values[f"{name} share (%)"] = 100.0 * float(b["share"][name])
    return values


# ---------------------------------------------------------------- drawing helpers


def draw_layer(ax, layer: dict, cmap, norm, values: np.ndarray | None = None):
    """Colour the cells of a map layer, fill the river cells and mark the well."""
    image = ef.draw_values(ax, layer["grb"], layer["step"],
                           layer["values"] if values is None else values, cmap, norm)
    ef.draw_cells(ax, layer["grb"], layer["step"], layer["river"], ef.RIVER_COLOUR)
    ef.draw_well(ax, layer["grb"], layer["well"], size=55.0)
    return image


def map_axes(ax, left: bool, bottom: bool, extent: float = EXTENT) -> None:
    """Square 2 km map axes; km ticks only on the outer panels."""
    ef.km_axes(ax, extent=extent, step_km=1.0, x_label=bottom, y_label=left)
    if not left:
        ax.tick_params(axis="y", length=0)
    if not bottom:
        ax.tick_params(axis="x", length=0)
    ax.xaxis.labelpad = 1
    ax.yaxis.labelpad = 1


def panel_title(ax, question: str, output: str) -> None:
    """Two-line title: the question in bold, the output type below it in plain type."""
    ax.text(0.0, 1.035 + 0.085, question, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=7.5, fontweight="bold")
    ax.text(0.0, 1.03, output, transform=ax.transAxes, ha="left", va="bottom", fontsize=7)


def inset_bar(fig, ax, mappable, label: str, ticks: tuple, ticklabels: tuple | None = None,
              colour: str = "black", bounds: tuple = (0.05, 0.9, 0.42, 0.045)) -> None:
    """Small horizontal colour bar inside the top of a map, its label at its right."""
    cax = ax.inset_axes(bounds)
    bar = fig.colorbar(mappable, cax=cax, orientation="horizontal", ticks=ticks)
    if ticklabels is not None:
        bar.ax.set_xticklabels(ticklabels)
    bar.ax.tick_params(labelsize=7, colors=colour, length=2, pad=1, width=0.5)
    bar.outline.set_edgecolor(colour)
    bar.outline.set_linewidth(0.5)
    bar.ax.minorticks_off()
    ax.text(bounds[0] + bounds[2] + 0.03, bounds[1] + bounds[3] / 2, label,
            transform=ax.transAxes, ha="left", va="center", fontsize=7, color=colour)


# ---------------------------------------------------------------- panels


def draw_area(fig, ax, layer: dict):
    """(a) F with the F = 0.1 (dashed) and 0.5 (solid) contours; the shared F colour bar."""
    image = draw_layer(ax, layer, ef.F_CMAP, Normalize(0.0, 1.0))
    ef.draw_f_contours(ax, layer["grb"], layer["step"], layer["values"])
    inset_bar(fig, ax, image, "F, w (-)", (0.0, 0.5, 1.0), ("0", "0.5", "1"), "white")


def draw_sources(ax, data: dict, colours: dict = ef.SOURCE_COLOURS) -> None:
    """(b) Volume from each source as horizontal bars, named above, share at the bar end."""
    volume, share = data["volume"], data["share"]
    names = list(volume.index)
    y = np.arange(len(names)) * 1.0
    top = max(volume)
    ax.barh(y, volume, color=[colours[n] for n in names], height=0.42)
    for yi, name in zip(y, names):
        ax.text(0.0, yi - 0.3, f"{name}, {volume[name]:.0f}", ha="left", va="bottom",
                fontsize=7)
        ax.text(volume[name] + 0.03 * top, yi, f"{share[name]:.0%}".replace("%", " %"),
                ha="left", va="center", fontsize=7)
    ax.text(0.0, y[-1] + 0.65, f"pumping {data['pumping']:.0f}", ha="left", va="top",
            fontsize=7, color=mfig.MUTED)
    ax.set_xlim(0.0, 1.32 * top)
    ax.set_ylim(y[-1] + 0.95, y[0] - 0.75)
    ax.set_box_aspect(1.0)
    ax.axis("off")


def draw_fate(fig, ax, layer: dict, levels: tuple = G_LEVELS) -> None:
    """(c) G of the recharge on a field (log scale), the field outlined."""
    norm = LogNorm(*levels)
    image = draw_layer(ax, layer, ef.G_CMAP, norm, np.maximum(layer["values"], levels[0]))
    ef.field_rectangle(ax, layer["spec"])
    inset_bar(fig, ax, image, "G (-)", (1e-3, 1e-2, 1e-1, 1.0), ("≤0.001", "", "0.1", "1"),
              bounds=(0.13, 0.9, 0.36, 0.045))


def draw_travel_time(fig, ax, layer: dict, norm: tuple = TRAVEL_NORM,
                     zone_years: tuple = ZONE_YEARS, label_xy: dict = ZONE_LABEL_XY,
                     note_xy: dict = ZONE_NOTE_XY) -> None:
    """(d) Mean travel time inside F > 0.5 (log, magma_r) with the 5- and 25-year contours.

    The 25-year contour is labelled inline; the 5-year zone is too small, so its label sits
    below the map's F > 0.5 area with a leader line.
    """
    image = draw_layer(ax, layer, "magma_r", LogNorm(*norm))
    years = layer["values"]
    closed = np.where(np.isfinite(years), years, 10.0 * norm[1])  # zones close at F = 0.5
    lines = ef.draw_contours(ax, layer["grb"], layer["step"], closed, zone_years, ZONE_COLOUR,
                             ("-",) * len(zone_years), width=1.0)
    ax.clabel(lines, levels=list(label_xy), fmt={y: f"{y} yr" for y in label_xy}, fontsize=7,
              inline_spacing=1, manual=list(label_xy.values()))
    for years, (point, text) in note_xy.items():  # small zone: label outside, with a leader
        ax.annotate(f"{years} yr", point, text, color=ZONE_COLOUR, fontsize=7, ha="center",
                    va="top", arrowprops={"arrowstyle": "-", "color": ZONE_COLOUR, "lw": 0.8,
                                          "shrinkA": 1, "shrinkB": 0})
    inset_bar(fig, ax, image, "years", (0.1, 1.0, 10.0, 100.0), ("0.1", "1", "10", "100"),
              bounds=(0.08, 0.9, 0.42, 0.045))


def draw_seasons(ax, layer: dict, colours: tuple = ef.ZONE_COLOURS,
                 labels: tuple = ef.ZONE_LABELS) -> None:
    """(e) Inner zone, seasonal zone and ring from the seasonal snapshots, with a legend."""
    draw_layer(ax, layer, ListedColormap(colours), BoundaryNorm(np.arange(-0.5, 4.0), 4))
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=c, edgecolor=mfig.MUTED, lw=0.4, label=lab)
               for c, lab in zip(colours[1:][::-1], labels[1:][::-1])]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=1,
              handlelength=1.0, handleheight=0.8, labelspacing=0.15, borderaxespad=0.25,
              handletextpad=0.4)


def draw_time_limited(ax, layer: dict) -> None:
    """(f) The fraction w of each cell's water that the well pumps within 30 years."""
    draw_layer(ax, layer, ef.F_CMAP, Normalize(0.0, 1.0))
    ef.draw_f_contours(ax, layer["grb"], layer["step"], layer["values"])


def draw_probability(fig, ax, layer: dict) -> None:
    """(g) Posterior probability of contribution with the true F = 0.5 contour."""
    image = draw_layer(ax, layer, plt.get_cmap(PROB_CMAP), Normalize(0.0, 1.0))
    ef.draw_contours(ax, layer["grb"], layer["step"], layer["truth"], (0.5,), TRUTH_COLOUR,
                     ("--",), width=1.1)
    inset_bar(fig, ax, image, "P (-)", (0.0, 0.5, 1.0), ("0", "0.5", "1"))


def draw_unstructured(ax, layer: dict, line: tuple = GRID_LINE) -> None:
    """(h) F on the Voronoi grid with its contours; the cell edges drawn faintly."""
    draw_layer(ax, layer, ef.F_CMAP, Normalize(0.0, 1.0))
    pmv = ef.flopy.plot.PlotMapView(modelgrid=ef.model_grid(layer["grb"]), ax=ax)
    pmv.plot_grid(linewidth=0.15, color=line)
    ef.draw_f_contours(ax, layer["grb"], layer["step"], layer["values"])


# ---------------------------------------------------------------- figures


def panel_axes(fig, size: tuple[float, float], left: float = 0.36, right: float = 0.04,
               top: float = 0.33, bottom: float = 0.37, row_gap: float = 0.33) -> dict:
    """Return the eight square axes (2 rows x 4) placed in inches on a figure of the size."""
    width, height = size
    side = (height - top - bottom - row_gap) / 2.0
    gap = (width - left - right - 4 * side) / 3.0
    assert gap > 0.05, f"panels too wide: gap {gap:.3f} in"
    axes = {}
    for n, key in enumerate("abcdefgh"):
        row, col = divmod(n, 4)
        x0 = left + col * (side + gap)
        y0 = bottom + (1 - row) * (side + row_gap)
        axes[key] = fig.add_axes((x0 / width, y0 / height, side / width, side / height))
    return axes


def make_gallery(out_dir: Path, panels: dict, height: float = 3.78,
                 fig_name: str = FIG_NAME) -> list[Path]:
    """Gallery figure: the eight output types, two rows of four square panels."""
    fig = plt.figure(figsize=(FULL_WIDTH, height))
    axes = panel_axes(fig, (FULL_WIDTH, height))
    draw_area(fig, axes["a"], panels["a"])
    draw_sources(axes["b"], panels["b"])
    draw_fate(fig, axes["c"], panels["c"])
    draw_travel_time(fig, axes["d"], panels["d"])
    draw_seasons(axes["e"], panels["e"])
    draw_time_limited(axes["f"], panels["f"])
    draw_probability(fig, axes["g"], panels["g"])
    draw_unstructured(axes["h"], panels["h"])
    for n, (key, ax) in enumerate(axes.items()):
        if key != "b":
            map_axes(ax, left=n % 4 == 0, bottom=n >= 4)
        panel_title(ax, *TITLES[key])
    return mfig.save(fig, out_dir, fig_name)


def make_method_single(out_dir: Path, height: float = 1.62,
                       fig_name: str = METHOD_NAME) -> list[Path]:
    """Panel (b) of the method schematic alone, one column wide: F on the eight-cell graph."""
    step = mfig.graph_step()
    f, inflow, _ = mfig.graph_fractions(step)
    assert inflow == 6.0 and abs(f[6] - 6 / 11) < 1e-12, (inflow, f[6])
    fig = plt.figure(figsize=(SINGLE_WIDTH, height))
    ax = fig.add_axes((0.0, 0.0, 1.0, 0.9))
    mfig.draw_graph(ax, f)
    mfig.draw_graph_labels(ax, inflow)
    fig.text(0.02, 0.985, "Backward fraction F to a well", ha="left", va="top", fontsize=8,
             fontweight="bold")
    return mfig.save(fig, out_dir, fig_name)


# ---------------------------------------------------------------- driver


def main(
    out_dir: Path = mfig.FIG_DIR,
    work: Path = WORK_DIR,
    gallery: bool = True,
    method: bool = True,
    quoted: dict = QUOTED,
) -> None:
    """Compute the panels, assert the quoted numbers and draw the gallery and the method crop."""
    mfig.paper_style()
    start = time.perf_counter()
    if gallery:
        panels = compute_panels(work)
        values = gallery_values(panels)
        print("gallery:", values)
        check_quoted(values, quoted)
        print("wrote", make_gallery(out_dir, panels))
    if method:
        print("wrote", make_method_single(out_dir))
    print(f"done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
