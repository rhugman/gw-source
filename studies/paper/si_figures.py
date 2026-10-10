"""Supporting-information figure S1 of the paper: gross against net accounting, and the F zones
against the PRT zone of weight-losing particles, Neversink calibrated model (streams as cells,
the eight priority wells).

Drawn from the outputs of studies/neversink/net_and_envelope.py (net_vs_gross_wells.csv,
envelope_prt.csv) and the per-cell values that module reads (F: output/fractions_cells.npz; P:
output/prt_volume_thin1/cell_capture_fraction.npy); nothing is traced or rerun.

- (a) Per well, the water each accounting attributes to the well: its pumping (gross) and the
  volume from the source terms under net accounting, which per well equals the throughflow of
  the well's cell. Beside each well, the share of its cell's outflow that the well takes and the
  ratio net / gross. A second axis gives the eight wells together (net volume from the source
  terms, not the sum of the per-well values, which counts water passing between well cells
  twice).
- (b-d) On the start cells of the published particles (uppermost active layer), in the windows
  of Figs 5 and 7: the F > 0.1 and F > 0.5 zones (gross), the outline of the PRT zone P > 0.5
  (weight-losing particles released over the cell volume) and the PRT-zone cells with F <= 0.1.

The plotted numbers are asserted against the CSVs and against the values the caption quotes
(QUOTED). Sizes and conventions follow studies/paper/neversink_figures.py: double column 7 in,
fonts 7 to 8 pt, PNG at 300 dpi and PDF. Run from the repository root:

    PYTHONPATH=src python studies/paper/si_figures.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import neversink_figures as nfig  # noqa: E402  (puts studies/neversink on the path)

import figures as nf  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import net_and_envelope as nae  # noqa: E402
import workflow as wf  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

OUT = nfig.OUT
FIG_DIR = nfig.FIG_DIR
WELL_ORDER = tuple(w for members in nfig.CLUSTERS.values() for w in members)
CLUSTER_REGION = {"U": "NE", "SV_W": "W", "SV_S": "S"}  # published release region per cluster
F_LOW, F_HIGH, P_ZONE = 0.1, 0.5, 0.5
# Values the caption quotes (NS Section 1; net_and_envelope outputs); the plot must round to them.
QUOTED = {
    "pumping": 3671,
    "net_volume_from": 3944,
    "share U___7": 0.44,
    "share SV_487": 0.69,
    "ratio U___7": 2.26,
    "ratio SV_487": 1.43,
    "ratio SV_227": 0.98,
    "net per-well sum": 4621,
    "source SV_227": 3.7,
    "coverage": 0.87,
    "F>0.5 inside PRT zone": 0.92,
    "seeded start cells": 29201,
    "prt_cells": 691,
    "F>0.1 cells": 2139,
    "F>0.5 cells": 445,
    "missed": 89,
    "missed NE": 86,
    "missed S": 2,
    "missed W": 1,
}
ZONE_COLORS = (nfig.ACTIVE_FILL, "#86b6ef", "#1c5cab", nfig.COLORS["prt"])  # codes 0 to 3
ZONE_LABELS = (
    "other start cells",
    "0.1 < F ≤ 0.5",
    "F > 0.5",
    "P > 0.5 and F ≤ 0.1",
)
GROSS, NET = nfig.COLORS["cells"], nfig.COLORS["cells"]  # net drawn hollow, as in Fig. 6


def assert_quoted(value: float, key: str, quoted: dict = QUOTED) -> None:
    """Assert that a plotted value rounds to the number the caption quotes (integers to 1)."""
    doc = quoted[key]
    if isinstance(doc, int):
        assert abs(value - doc) <= 0.5, f"{key}: {value:.4f}, quoted {doc}"
    else:
        nfig.assert_doc(value, doc, key)


# ---------------------------------------------------------------- (a) gross and net accounting


def accounting_table(out: Path = OUT, wells: tuple = WELL_ORDER) -> pd.DataFrame:
    """Return pumping, net volume from, share of cell outflow and net / gross per well and group."""
    table = pd.read_csv(out / "net_vs_gross_wells.csv").set_index("group")
    table = table.loc[[*wells, "priority"]]
    assert np.allclose(table["gross_volume_from"], table["pumping"], rtol=1e-5), "gross closure"
    table["ratio"] = table["net_volume_from"] / table["pumping"]
    for name in ("ratio_net_volume_from", "ratio_net_attribution"):
        if name in table:
            assert np.allclose(table["ratio"], table[name], rtol=1e-12), name
    assert_quoted(table.loc["priority", "pumping"], "pumping")
    assert_quoted(table.loc["priority", "net_volume_from"], "net_volume_from")
    assert_quoted(table.loc["U___7", "well_share_of_outflow"], "share U___7")
    assert_quoted(table.loc["SV_487", "well_share_of_outflow"], "share SV_487")
    for well in ("U___7", "SV_487", "SV_227"):
        assert_quoted(table.loc[well, "ratio"], f"ratio {well}")
    assert_quoted(table.loc[list(wells), "net_volume_from"].sum(), "net per-well sum")
    assert_quoted(table.loc["SV_227", "cell_source_terms"], "source SV_227")
    if "n_cycles" in table:
        assert (table["n_cycles"] == 0).all(), "the caption says there are no flow loops"
    return table


def well_positions(wells: tuple = WELL_ORDER, clusters: dict = nfig.CLUSTERS,
                   gap: float = 0.6) -> np.ndarray:
    """Return the y position of each well's row, with a gap between clusters (top row 0)."""
    cluster_of = {w: k for k, members in clusters.items() for w in members}
    y, positions = 0.0, []
    for n, well in enumerate(wells):
        if n and cluster_of[well] != cluster_of[wells[n - 1]]:
            y += gap
        positions.append(y)
        y += 1.0
    return np.array(positions)


def paired_bars(ax: plt.Axes, y: np.ndarray, gross: np.ndarray, net: np.ndarray,
                height: float = 0.36) -> None:
    """Draw a filled bar (gross) above a hollow bar (net) per row."""
    ax.barh(y - height / 2 - 0.02, gross, height, color=GROSS, lw=0)
    ax.barh(y + height / 2 + 0.02, net, height, facecolor=nfig.SURFACE, edgecolor=NET, lw=1.0)


def draw_wells(ax: plt.Axes, table: pd.DataFrame, x_max: float = 1300.0) -> None:
    """Panel (a), left: pumping and net volume from per well, share and ratio as text columns."""
    wells = [w for w in table.index if w != "priority"]
    y = well_positions(tuple(wells))
    part = table.loc[wells]
    paired_bars(ax, y, part["pumping"].to_numpy(), part["net_volume_from"].to_numpy())
    columns = ((1.10 * x_max, "well share of\ncell outflow"), (1.38 * x_max, "net /\ngross"))
    for x, head in columns:
        ax.text(x, y[0] - 0.75, head, ha="center", va="bottom", fontsize=7, color=nfig.MUTED)
    for yy, (_, r) in zip(y, part.iterrows()):
        ax.text(columns[0][0], yy, f"{100 * r['well_share_of_outflow']:.0f} %", ha="center",
                va="center", fontsize=7)
        ax.text(columns[1][0], yy, f"{r['ratio']:.2f}", ha="center", va="center", fontsize=7)
    ax.set_yticks(y, wells)
    ax.set_ylim(y[-1] + 0.65, y[0] - 0.75)
    ax.set_xlim(0, 1.52 * x_max)
    ax.set_xticks(np.arange(0, x_max + 1, 400))
    ax.spines["bottom"].set_bounds(0, x_max)
    ax.grid(True, axis="x", color=nfig.GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.set_xlabel("water attributed to the well (m³/d)", loc="left")
    ax.set_title("(a) per well", loc="left")


def draw_group(ax: plt.Axes, table: pd.DataFrame) -> None:
    """Panel (a), right: volume from the source terms of the eight wells together."""
    row = table.loc["priority"]
    paired_bars(ax, np.array([0.0]), np.array([row["gross_volume_from"]]),
                np.array([row["net_volume_from"]]), height=0.3)
    for y, value in ((-0.17, row["gross_volume_from"]), (0.17, row["net_volume_from"])):
        ax.text(value + 80, y, f"{value:,.0f}", va="center", fontsize=7)
    ax.set_yticks([-0.17, 0.17], ["gross", "net"])
    ax.set_ylim(0.5, -1.25)
    ax.set_xlim(0, 5200)
    ax.set_xticks([0, 2000, 4000], ["0", "2,000", "4,000"])
    ax.spines["bottom"].set_bounds(0, 4000)
    ax.grid(True, axis="x", color=nfig.GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.set_xlabel("volume from source terms (m³/d)", loc="left")
    ax.set_title("eight wells together", loc="left")


# ---------------------------------------------------------------- (b-d) zones on the start cells


def start_cells(out: Path = OUT) -> pd.DataFrame:
    """Return node, region, F (gross) and P (weight-losing PRT) of every published start cell."""
    endpoints = wf.read_endpoints(columns=("node0",))
    f = np.load(out / "fractions_cells.npz")["priority"]
    p = np.load(out / nae.PRT_RUN / "cell_capture_fraction.npy").astype(float)
    assert len(p) == len(f), "the PRT run is on a different grid"
    node = endpoints["node0"].to_numpy()
    return pd.DataFrame({"node": node, "region": endpoints["region"].to_numpy(), "F": f[node],
                         "P": np.nan_to_num(p[node])})


def zone_codes(cells: pd.DataFrame) -> np.ndarray:
    """Return a zone code per start cell: 0 F <= 0.1, 1 0.1 < F <= 0.5, 2 F > 0.5, 3 missed."""
    f, p = cells["F"].to_numpy(), cells["P"].to_numpy()
    code = np.where(f > F_HIGH, 2, np.where(f > F_LOW, 1, 0))
    return np.where((p > P_ZONE) & (f <= F_LOW), 3, code)


def check_zones(cells: pd.DataFrame, codes: np.ndarray, out: Path = OUT) -> pd.Series:
    """Assert the zone counts against envelope_prt.csv; return the missed cells per region."""
    env = pd.read_csv(out / "envelope_prt.csv").set_index(["region", "prt_zone", "f_zone"])
    row = env.loc[("all", f"P>{P_ZONE:g}", f"F>{F_LOW:g}")]
    p_zone = cells["P"].to_numpy() > P_ZONE
    assert row["prt_cells"] == p_zone.sum() == QUOTED["prt_cells"], "PRT zone"
    assert row["f_cells"] == np.isin(codes, (1, 2)).sum() == QUOTED["F>0.1 cells"], "F > 0.1"
    assert_quoted(row["coverage"], "coverage")
    high = env.loc[("all", f"P>{P_ZONE:g}", f"F>{F_HIGH:g}")]
    assert high["f_cells"] == np.sum(codes == 2) == QUOTED["F>0.5 cells"], "F > 0.5"
    assert_quoted(high["f_zone_inside_prt"], "F>0.5 inside PRT zone")
    notes = pd.read_csv(out / "envelope_prt_notes.csv").iloc[0]
    assert notes["seeded_start_cells"] == QUOTED["seeded start cells"], "seeded start cells"
    assert notes["start_cells_F>0.1"] == QUOTED["F>0.1 cells"], "F > 0.1 start cells"
    assert notes["unseeded_F>0.1"] == 0, "the caption says every F > 0.1 start cell is seeded"
    missed = pd.Series(codes == 3).groupby(cells["region"].to_numpy()).sum()
    assert row["missed_cells"] == missed.sum() == QUOTED["missed"], "missed cells"
    for region, n in missed.items():
        assert env.loc[(region, f"P>{P_ZONE:g}", f"F>{F_LOW:g}"), "missed_cells"] == n, region
        assert n == QUOTED[f"missed {region}"], region
    return missed


def cell_grid(nodes: np.ndarray, values: np.ndarray, shape: tuple) -> np.ndarray:
    """Return values on the (row, column) grid at the nodes' columns, NaN elsewhere."""
    nrow, ncol = shape
    grid = np.full(shape, np.nan)
    cell = nodes % (nrow * ncol)
    grid[cell // ncol, cell % ncol] = values
    return grid


def draw_zone_map(ax: plt.Axes, codes: np.ndarray, p_zone: np.ndarray, wells_ij: list,
                  window: tuple, title: str) -> None:
    """Draw the zone codes, the PRT-zone outline and the wells in one cluster window."""
    r0, r1, c0, c1 = window
    nrow = codes.shape[0]
    km = nf.CELL_KM
    extent = (c0 * km, (c1 + 1) * km, (nrow - r1 - 1) * km, (nrow - r0) * km)
    ax.imshow(codes[r0 : r1 + 1, c0 : c1 + 1], cmap=ListedColormap(ZONE_COLORS), vmin=-0.5,
              vmax=3.5, extent=extent, interpolation="nearest")
    yy, xx = np.mgrid[r0 : r1 + 1, c0 : c1 + 1]
    ax.contour((xx + 0.5) * km, (nrow - yy - 0.5) * km, p_zone[r0 : r1 + 1, c0 : c1 + 1],
               levels=[0.5], colors=nfig.COLORS["prt"], linewidths=0.8)
    for i, j in wells_ij:
        if r0 <= i <= r1 and c0 <= j <= c1:
            ax.plot((j + 0.5) * km, (nrow - i - 0.5) * km, "o", ms=4, mfc=nfig.INK,
                    mec=nfig.SURFACE, mew=1.0)
    ax.set_title(title, loc="left")
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7)


def window_counts(codes: np.ndarray, windows: dict) -> dict:
    """Return the number of missed cells (code 3) inside each window."""
    return {name: int(np.sum(codes[r0 : r1 + 1, c0 : c1 + 1] == 3))
            for name, (r0, r1, c0, c1) in windows.items()}


# ---------------------------------------------------------------- figure


def map_legend_handles() -> list:
    """Return the legend entries of the zone maps."""
    handles = [Patch(facecolor=c, edgecolor="none", label=lab)
               for c, lab in zip(ZONE_COLORS, ZONE_LABELS)]
    handles.append(plt.Line2D([], [], color=nfig.COLORS["prt"], lw=0.9,
                              label="PRT zone, P > 0.5 (outline)"))
    handles.append(plt.Line2D([], [], ls="", marker="o", ms=4, mfc=nfig.INK, mec=nfig.SURFACE,
                              label="priority wells"))
    return handles


def accounting_legend_handles() -> list:
    """Return the legend entries of panel (a)."""
    return [Patch(facecolor=GROSS, edgecolor="none", label="gross accounting (= pumping)"),
            Patch(facecolor=nfig.SURFACE, edgecolor=NET, lw=1.0, label="net accounting")]


def make_figS1(fig_dir: Path, table: pd.DataFrame, codes: np.ndarray, p_zone: np.ndarray,
               windows: dict, wells: dict, missed: pd.Series) -> Path:
    """Fig. S1: (a) gross and net accounting per well; (b-d) F zones against the PRT zone."""
    nfig.paper_style()
    fig = plt.figure(figsize=(nfig.DOUBLE, 5.0), layout="constrained")
    top, bottom = fig.subfigures(2, 1, height_ratios=(1.0, 1.12))
    ax_wells, ax_group = top.subplots(1, 2, width_ratios=(2.5, 1.0))
    draw_wells(ax_wells, table)
    draw_group(ax_group, table)
    ax_group.legend(handles=accounting_legend_handles(), loc="upper left",
                    bbox_to_anchor=(-0.04, 1.0), handlelength=1.4)
    axes = bottom.subplots(1, len(windows))
    wells_ij = list(nfig.well_ij(wells, codes.shape).values())
    for ax, letter, (name, window) in zip(axes, "bcd", windows.items()):
        n = missed[CLUSTER_REGION[name]]
        title = f"({letter}) {name}: F > 0.1 misses {n}"
        draw_zone_map(ax, codes, p_zone, wells_ij, window, title)
        ax.set_xlabel("x from grid origin (km)")
    axes[0].set_ylabel("y (km)")
    bottom.legend(handles=map_legend_handles(), loc="outside lower center", ncol=3,
                  handlelength=1.4, columnspacing=1.2)
    return nfig.save(fig, fig_dir, "figS1_net_and_envelope")


def main(fig_dir: Path = FIG_DIR, out: Path = OUT) -> Path:
    """Make Fig. S1 in fig_dir from the outputs in out; return the PNG path."""
    idomain = wf.grid_idomain(out / "optimal")
    shape = idomain.shape[1:]
    wells = wf.PRIORITY_WELLS
    table = accounting_table(out)
    cells = start_cells(out)
    codes = zone_codes(cells)
    missed = check_zones(cells, codes, out)
    nodes = cells["node"].to_numpy()
    code_grid = cell_grid(nodes, codes, shape)
    p_grid = cell_grid(nodes, (cells["P"].to_numpy() > P_ZONE).astype(float), shape)
    windows = nfig.map_windows(nfig.capture_fields(idomain, out), nfig.published_mask(shape, out),
                               wells)
    in_windows = window_counts(code_grid, windows)
    for name, n in in_windows.items():
        assert n == missed[CLUSTER_REGION[name]], f"{name}: {n} missed cells in the window"
    return make_figS1(fig_dir, table, code_grid, np.nan_to_num(p_grid) > 0, windows, wells,
                      missed)


if __name__ == "__main__":
    t0 = time.perf_counter()
    print(main())
    print(f"{time.perf_counter() - t0:.1f} s")
