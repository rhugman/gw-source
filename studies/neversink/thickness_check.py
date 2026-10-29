"""Neversink: does layer thickness drive the full-mixing (F) versus particle (P) difference?

Saturated thickness of a cell = min(head, top) - bottom, from the calibrated run's binary grid
file and head file. Five checks, all on results that exist (no new model runs):

1. thickness per layer in the 1 km window around the priority wells;
2. bottleneck cells (the cells making 80 % of a path's loss) and split cells against the other
   cells of the same layer, within the same 250 m distance band to the wells;
3. loss per path cell against thickness, by direction (lateral, up, under stream);
4. many-particle disagreement |F - P| and agreement class against the thickness of the start
   cell and of the whole column;
5. the same, controlling for plan distance to the nearest priority well.

Writes output/diagnostics/fig6_thickness.png and thickness_check.csv (main checkout).

    python studies/neversink/thickness_check.py
"""

from pathlib import Path

import flopy
import numpy as np
import pandas as pd
from scipy import stats

import diagnostics as dg
import workflow as wf

import matplotlib.pyplot as plt  # noqa: E402

DIAG = dg.DIAG_DIR
OUT = DIAG.parent
WS = OUT / "optimal"
WINDOW_M = 1000.0
NEAR_BINS = (0.0, 250.0, 500.0, 750.0, 1000.0)  # bands inside the window (matching, task 2)
DIST_BINS = (0.0, 250.0, 500.0, 1000.0, 2000.0, np.inf)  # task 4 and 5
DIST_LABELS = ("< 250", "250-500", "500-1000", "1000-2000", "> 2000")
MIN_N = 30  # smallest group drawn or counted in a stratified statistic
CELL = dg.CELL
INK, MUTED, SURFACE = dg.INK, dg.MUTED, dg.SURFACE
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]  # validated order
LOSS_COLORS = {"lateral": CAT[0], "up": CAT[5], "sink": CAT[3]}
LOSS_LABELS = {"lateral": "lateral", "up": "upward", "sink": "under stream"}


# ---------------------------------------------------------------- grid and thickness


def saturated_thickness(ws: Path = WS) -> tuple[np.ndarray, np.ndarray]:
    """Return the saturated thickness (nlay, nrow, ncol), NaN in inactive cells, and idomain."""
    grb = flopy.mf6.utils.MfGrdFile(ws / f"{wf.MODEL}.dis.grb")
    shape = (grb.nlay, grb.nrow, grb.ncol)
    idomain = np.asarray(grb.idomain).reshape(shape)
    bot = np.asarray(grb.bot).reshape(shape)
    top = np.concatenate([np.asarray(grb.top).reshape(1, *shape[1:]), bot[:-1]])
    head = flopy.utils.HeadFile(ws / f"{wf.MODEL}.hds").get_data()
    active = (idomain > 0) & (np.abs(head) < 1e20)
    th = np.clip(np.minimum(head, top) - bot, 0.0, None)
    return np.where(active, th, np.nan), idomain


def plan_distance_to_wells(node: np.ndarray, shape: tuple) -> np.ndarray:
    """Return the plan distance (m) from each node to the nearest priority-well cell."""
    from scipy.spatial import cKDTree

    _, wi, wj = dg.node_klij(np.array(list(wf.PRIORITY_WELLS.values())), shape)
    _, i, j = dg.node_klij(node, shape)
    return cKDTree(np.column_stack([wi, wj]) * CELL).query(np.column_stack([i, j]) * CELL)[0]


# ---------------------------------------------------------------- statistics helpers


def spearman(x, y) -> tuple[float, float]:
    """Return Spearman rho and its p value (NaN if either input is constant)."""
    x, y = np.asarray(x), np.asarray(y)
    if len(x) < 5 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return np.nan, np.nan
    r = stats.spearmanr(x, y)
    return float(r.statistic), float(r.pvalue)


def partial_spearman(x, y, control) -> float:
    """Return the Spearman correlation of x and y after removing the rank-linear effect of control."""
    def resid(a, c):
        ra, rc = stats.rankdata(a), stats.rankdata(c)
        slope = np.polyfit(rc, ra, 1)
        return ra - np.polyval(slope, rc)

    return float(np.corrcoef(resid(x, control), resid(y, control))[0, 1])


def stratified_rho(x, y, strata) -> float:
    """Return the n-weighted mean Spearman rho within strata (strata under MIN_N dropped)."""
    x, y, strata = np.asarray(x), np.asarray(y), np.asarray(strata)
    rho, n = [], []
    for s in np.unique(strata):
        m = strata == s
        if m.sum() >= MIN_N:
            r, _ = spearman(x[m], y[m])
            if np.isfinite(r):
                rho.append(r)
                n.append(m.sum())
    return float(np.average(rho, weights=n)) if rho else np.nan


def band_index(d, bins) -> np.ndarray:
    """Return the index of the distance band of each distance."""
    return np.digitize(d, bins[1:-1])


def percentile_in_reference(value, group, ref_value, ref_group) -> np.ndarray:
    """Return each value's percentile (0 to 1) among the reference values of its own group."""
    out = np.full(len(value), np.nan)
    for g in np.unique(group):
        ref = np.sort(ref_value[ref_group == g])
        m = group == g
        if len(ref):
            out[m] = (np.searchsorted(ref, value[m], "left")
                      + np.searchsorted(ref, value[m], "right")) / (2 * len(ref))
    return out


# ---------------------------------------------------------------- the five checks


def window_table(th: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task 1: thickness per layer within WINDOW_M of the priority wells, and everywhere."""
    shape = th.shape
    nodes = np.flatnonzero(np.isfinite(th.ravel()))
    d = plan_distance_to_wells(nodes, shape)
    cells = pd.DataFrame({"node": nodes, "layer": dg.node_klij(nodes, shape)[0] + 1,
                          "dist": d, "th": th.ravel()[nodes]})
    rows = []
    for where, sub in (("within 1 km of wells", cells[cells["dist"] <= WINDOW_M]),
                       ("whole model", cells)):
        for layer, g in sub.groupby("layer"):
            q = g["th"].quantile([0.1, 0.5, 0.9])
            rows.append({"analysis": "1 thickness", "subset": f"{where}, layer {layer}",
                         "n": len(g), "mean_m": g["th"].mean(), "p10_m": q[0.1],
                         "median_m": q[0.5], "p90_m": q[0.9]})
    return pd.DataFrame(rows), cells


def path_cells_table(th: np.ndarray) -> pd.DataFrame:
    """Per path cell: loss by direction, thickness, distance to wells and bottleneck flag."""
    b = pd.read_csv(DIAG / "path_budget_cells.csv")
    flat = th.ravel()
    b["th"] = flat[b["cell"]]
    b["dist"] = plan_distance_to_wells(b["cell"].to_numpy(), th.shape)
    assert b["th"].notna().all(), "a path cell is inactive in the grid file"
    b["bottleneck"] = False
    for pid, g in b.groupby("pid"):
        total = g["deficit"].sum()
        order = g.sort_values("deficit", ascending=False)
        n80 = int(np.searchsorted(np.cumsum(order["deficit"].to_numpy()), 0.8 * total) + 1)
        b.loc[order.index[:n80], "bottleneck"] = True
    return b


def bottleneck_rows(b: pd.DataFrame, cells: pd.DataFrame, th: np.ndarray) -> list[dict]:
    """Task 2: bottleneck cells against the rest of their paths, and split cells against the
    cells within 1 km of the wells (raw, then matched on layer and distance band)."""
    rows = []
    per = b.groupby(["pid", "bottleneck"])["th"].median().unstack()
    per = per.dropna()
    w = stats.wilcoxon(per[True], per[False])
    rows.append({"analysis": "2 bottleneck vs rest of path", "subset": "median per path, paired",
                 "n": len(per), "median_a_m": per[True].median(), "median_b_m": per[False].median(),
                 "stat": "Wilcoxon p", "value": w.pvalue,
                 "note": "a = bottleneck cells, b = other cells of the path"})
    near = cells[cells["dist"] <= WINDOW_M].copy()
    near["band"] = band_index(near["dist"], NEAR_BINS)
    near["stratum"] = near["layer"] * 10 + near["band"]
    ref_th, ref_stratum = near["th"].to_numpy(), near["stratum"].to_numpy()

    def matched(df, label, note):
        u = df.drop_duplicates("cell").copy()
        u = u[u["dist"] <= WINDOW_M]
        u["stratum"] = (dg.node_klij(u["cell"], th.shape)[0] + 1) * 10 + band_index(u["dist"], NEAR_BINS)
        pct = percentile_in_reference(u["th"].to_numpy(), u["stratum"].to_numpy(), ref_th, ref_stratum)
        pct = pct[np.isfinite(pct)]
        rows.append({"analysis": "2 " + label, "subset": "percentile among window cells of same layer and 250 m band",
                     "n": len(pct), "mean_percentile": pct.mean(), "stat": "Wilcoxon p vs 0.5",
                     "value": stats.wilcoxon(pct - 0.5).pvalue, "note": note})

    pcell = b.rename(columns={"cell": "cell"})
    matched(pcell[pcell["bottleneck"]], "bottleneck cells, matched", "unique cells")
    matched(pcell[~pcell["bottleneck"]], "other path cells, matched", "unique cells")
    s = pd.read_csv(DIAG / "split_cells.csv").drop_duplicates("cell")
    s["th"] = th.ravel()[s["cell"]]
    s["dist"] = plan_distance_to_wells(s["cell"].to_numpy(), th.shape)
    rows.append({"analysis": "2 split cells vs window cells", "subset": "raw, unique split cells vs all cells within 1 km",
                 "n": int((s["dist"] <= WINDOW_M).sum()),
                 "median_a_m": s.loc[s["dist"] <= WINDOW_M, "th"].median(),
                 "median_b_m": near["th"].median(), "stat": "Mann-Whitney p",
                 "value": stats.mannwhitneyu(s.loc[s["dist"] <= WINDOW_M, "th"], near["th"]).pvalue,
                 "note": "a = split cells, b = all active cells within 1 km"})
    matched(s, "split cells, matched", "unique split cells")
    return rows


def loss_rows(b: pd.DataFrame) -> list[dict]:
    """Tasks 3 and 5 on path cells: loss against thickness by direction, raw, within distance
    bands (stratified), partial on distance, and within layers."""
    rows = []
    band = band_index(b["dist"].to_numpy(), (0, 250, 500, 1000, np.inf))
    for d in ("lateral", "up", "sink"):
        loss = b[f"deficit_{d}"].to_numpy()
        pos = loss > 0
        raw, p = spearman(b["th"], loss)
        rows.append({"analysis": "3 loss vs thickness", "subset": f"{d}, all path cells", "n": len(b),
                     "stat": "Spearman rho", "value": raw, "p": p})
        r, p = spearman(b["th"][pos], loss[pos])
        rows.append({"analysis": "3 loss vs thickness", "subset": f"{d}, cells with loss > 0",
                     "n": int(pos.sum()), "stat": "Spearman rho", "value": r, "p": p})
        rows.append({"analysis": "5 distance control", "subset": f"loss {d}, partial on distance",
                     "n": len(b), "stat": "partial Spearman rho",
                     "value": partial_spearman(b["th"], loss, b["dist"])})
        rows.append({"analysis": "5 distance control", "subset": f"loss {d}, within distance bands",
                     "n": len(b), "stat": "stratified Spearman rho",
                     "value": stratified_rho(b["th"], loss, band)})
        for layer in (2, 4):
            m = (b["layer"] == layer).to_numpy()
            r, p = spearman(b["th"][m], loss[m])
            rows.append({"analysis": "5 layer control", "subset": f"loss {d}, layer {layer}",
                         "n": int(m.sum()), "stat": "Spearman rho", "value": r, "p": p})
    near = b["dist"] <= 500
    rows.append({"analysis": "3 loss vs thickness", "subset": "share of path cells within 500 m of a well",
                 "n": len(b), "stat": "share", "value": float(near.mean())})
    rows.append({"analysis": "5 distance control", "subset": "thickness vs distance to well, path cells",
                 "n": len(b), "stat": "Spearman rho", "value": spearman(b["th"], b["dist"])[0]})
    for lab, m in (("bottleneck", b["bottleneck"]), ("other", ~b["bottleneck"])):
        rows.append({"analysis": "5 distance control", "subset": f"median distance to well, {lab} cells",
                     "n": int(m.sum()), "stat": "median m", "value": float(b.loc[m, "dist"].median())})
    for k, (lo, hi) in enumerate(zip((0, 250, 500, 1000), (250, 500, 1000, np.inf))):
        g = b[band == k]
        for lab, m in (("bottleneck", g["bottleneck"]), ("other", ~g["bottleneck"])):
            rows.append({"analysis": "5 bottleneck by distance", "subset": f"{lo}-{hi} m, {lab}",
                         "n": int(m.sum()), "stat": "median thickness m",
                         "value": float(g.loc[m, "th"].median()) if m.any() else np.nan})
    return rows


def start_cells_table(th: np.ndarray) -> pd.DataFrame:
    """Per many-particle start cell: F, P, class, start-cell and column thickness, distance."""
    p = pd.read_csv(OUT / "prt_many_particles_cells.csv", usecols=[
        "node0", "published_priority", "P_priority", "F_gross_strong_priority"])
    p = p.dropna(subset=["P_priority"])
    shape = th.shape
    k, i, j = dg.node_klij(p["node0"].to_numpy(), shape)
    p["layer"] = k + 1
    p["th_start"] = th[k, i, j]
    p["th_column"] = np.nansum(th, axis=0)[i, j]
    p["dist"] = plan_distance_to_wells(p["node0"].to_numpy(), shape)
    f, pub = p["F_gross_strong_priority"].to_numpy(), p["published_priority"].to_numpy(bool)
    p["diff"] = np.abs(f - p["P_priority"].to_numpy())
    cls = np.select([pub & (f > dg.F_HIGH), pub, f > dg.F_HIGH, f > dg.F_LOW], [1, 2, 3, 4], 0)
    p["cls"] = cls
    p["disputed"] = np.where(cls > 0, (cls > 1).astype(float), np.nan)
    p = p[np.isfinite(p["th_start"])]
    return p


def start_rows(p: pd.DataFrame) -> list[dict]:
    """Tasks 4 and 5 on start cells: raw, within distance bands, partial on distance."""
    rows = []
    band = band_index(p["dist"].to_numpy(), DIST_BINS)
    near = p[p["dist"] <= 2000.0]
    nband = band_index(near["dist"].to_numpy(), DIST_BINS)
    for pop_name, pop, pband in (("all start cells", p, band), ("within 2 km of wells", near, nband)):
        for thick in ("th_start", "th_column"):
            for target, label in (("diff", "|F-P|"), ("disputed", "disputed class share")):
                sub = pop.dropna(subset=[target]) if target == "disputed" else pop
                sb = band_index(sub["dist"].to_numpy(), DIST_BINS)
                raw, pv = spearman(sub[thick], sub[target])
                rows.append({"analysis": "4 start cells", "subset": f"{label} vs {thick}, {pop_name}",
                             "n": len(sub), "stat": "Spearman rho", "value": raw, "p": pv})
                rows.append({"analysis": "5 distance control",
                             "subset": f"{label} vs {thick}, {pop_name}, partial on distance",
                             "n": len(sub), "stat": "partial Spearman rho",
                             "value": partial_spearman(sub[thick], sub[target], sub["dist"])})
                rows.append({"analysis": "5 distance control",
                             "subset": f"{label} vs {thick}, {pop_name}, within distance bands",
                             "n": len(sub), "stat": "stratified Spearman rho",
                             "value": stratified_rho(sub[thick], sub[target], sb)})
    for k, lab in enumerate(DIST_LABELS):
        g = p[band == k]
        r, _ = spearman(g["th_start"], g["diff"])
        rows.append({"analysis": "5 distance band", "subset": f"{lab} m: |F-P| vs start thickness",
                     "n": len(g), "stat": "Spearman rho", "value": r,
                     "median_a_m": g["th_start"].median(), "mean_diff": g["diff"].mean()})
    rows.append({"analysis": "5 distance control", "subset": "start thickness vs distance to well, all start cells",
                 "n": len(p), "stat": "Spearman rho", "value": spearman(p["th_start"], p["dist"])[0]})
    return rows


# ---------------------------------------------------------------- figure


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "text.color": INK, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    })


def ecdf(ax, values, **kw) -> None:
    v = np.sort(np.asarray(values))
    ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", **kw)


def binned(x, y, edges) -> pd.DataFrame:
    """Return mean, standard error, count and mean x of y in the bins of x."""
    k = np.digitize(x, edges[1:-1])
    rows = []
    for b in range(len(edges) - 1):
        m = k == b
        if m.sum() >= MIN_N:
            rows.append({"x": np.mean(np.asarray(x)[m]), "y": np.mean(np.asarray(y)[m]),
                         "se": np.std(np.asarray(y)[m], ddof=1) / np.sqrt(m.sum()), "n": int(m.sum())})
    return pd.DataFrame(rows)


def figure(cells, b, split_th, p, summary, path: Path) -> Path:
    style()
    fig, ax = plt.subplots(2, 3, figsize=(13.5, 8.2), constrained_layout=True)
    near = cells[cells["dist"] <= WINDOW_M]

    a = ax[0, 0]
    layers = sorted(near["layer"].unique())
    data = [near.loc[near["layer"] == l, "th"] for l in layers]
    box = a.boxplot(data, positions=layers, widths=0.55, patch_artist=True, showfliers=False,
                    medianprops={"color": INK, "lw": 1.5}, whiskerprops={"color": MUTED},
                    capprops={"color": MUTED}, boxprops={"edgecolor": MUTED})
    for patch, l in zip(box["boxes"], layers):
        patch.set_facecolor(CAT[l - 1])
        patch.set_alpha(0.85)
    for l, d in zip(layers, data):
        a.text(l, -0.08, f"n={len(d):,}", ha="center", va="top", fontsize=7.5, color=MUTED, transform=a.get_xaxis_transform())
    a.set_xticks(layers)
    a.set_xlabel("layer", labelpad=14)
    a.set_ylabel("saturated thickness (m)")
    a.set_title("a  Thickness by layer, within 1 km of the wells", loc="left", fontsize=9.5)

    a = ax[0, 1]
    ecdf(a, near["th"], color=MUTED, lw=1.6, label="all cells within 1 km")
    ecdf(a, b.loc[~b["bottleneck"], "th"], color=CAT[0], lw=1.6, label="path cells, other")
    ecdf(a, b.loc[b["bottleneck"], "th"], color=CAT[1], lw=1.6, label="path cells, bottleneck (80 % of loss)")
    ecdf(a, split_th, color=CAT[2], lw=1.6, label="split cells")
    a.set_xscale("log")
    a.set_xlabel("saturated thickness (m)")
    a.set_ylabel("cumulative share of cells")
    a.legend(frameon=False, fontsize=7.5, loc="upper left")
    a.set_title("b  Bottleneck and split cells against other cells", loc="left", fontsize=9.5)

    a = ax[0, 2]
    edges = np.quantile(b["th"], np.linspace(0, 1, 7))
    for d in ("lateral", "up", "sink"):
        t = binned(b["th"].to_numpy(), b[f"deficit_{d}"].to_numpy(), edges)
        a.errorbar(t["x"], t["y"], t["se"], color=LOSS_COLORS[d], marker="o", ms=5, lw=1.5, capsize=2,
                   label=LOSS_LABELS[d])
    a.axhline(0, color=MUTED, lw=0.6)
    a.set_xscale("log")
    a.set_xlabel("saturated thickness of the path cell (m)")
    a.set_ylabel("mean loss per cell (F units)")
    a.legend(frameon=False, fontsize=8)
    a.set_title("c  Loss per cell against thickness, by direction", loc="left", fontsize=9.5)

    pn = p[p["dist"] <= 2000.0]
    edges = np.quantile(pn["th_start"], np.linspace(0, 1, 5))
    edges = np.unique(edges)
    for col, target, ylabel, title in (
        (ax[1, 0], "diff", "mean |F - P| of start cells", "d  |F - P| against start-cell thickness"),
        (ax[1, 1], "disputed", "share of classified cells in dispute", "e  Disputed class against start-cell thickness"),
    ):
        for k, lab in enumerate(DIST_LABELS[:4]):
            g = p[band_index(p["dist"].to_numpy(), DIST_BINS) == k]
            g = g.dropna(subset=[target])
            t = binned(g["th_start"].to_numpy(), g[target].to_numpy(), edges)
            if len(t):
                col.errorbar(t["x"], t["y"], t["se"], color=CAT[k], marker="o", ms=4.5, lw=1.4, capsize=2,
                             label=f"{lab} m from well")
        col.set_xlabel("saturated thickness of the start cell (m)")
        col.set_ylabel(ylabel)
        col.set_title(title, loc="left", fontsize=9.5)
    ax[1, 0].legend(frameon=False, fontsize=7.5)

    a = ax[1, 2]
    s = summary
    y = np.arange(len(s))[::-1]
    a.barh(y + 0.19, s["raw"], height=0.36, color=CAT[1], label="raw")
    a.barh(y - 0.19, s["controlled"], height=0.36, color=CAT[0], label="within distance bands")
    a.set_yticks(y)
    a.set_yticklabels(s["label"], fontsize=8)
    a.axvline(0, color=MUTED, lw=0.6)
    a.set_xlabel("Spearman rho with saturated thickness")
    a.legend(frameon=False, fontsize=8, loc="upper left")
    a.set_xlim(-0.3, 0.5)
    a.set_title("f  Rank correlation with thickness", loc="left", fontsize=9.5)
    fig.savefig(path, dpi=dg.DPI)
    plt.close(fig)
    return path


def main() -> list[Path]:
    th, _ = saturated_thickness()
    win, cells = window_table(th)
    b = path_cells_table(th)
    p = start_cells_table(th)
    rows = [*win.to_dict("records"), *bottleneck_rows(b, cells, th), *loss_rows(b), *start_rows(p)]
    table = pd.DataFrame(rows)
    table.to_csv(DIAG / "thickness_check.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 95, "display.max_rows", 500)
    print(table.round(4).to_string())

    def val(analysis, subset, stat=None):
        t = table[(table["analysis"] == analysis) & (table["subset"] == subset)]
        return float(t["value"].iloc[0])

    summary = pd.DataFrame([
        ("loss lateral", val("3 loss vs thickness", "lateral, all path cells"),
         val("5 distance control", "loss lateral, within distance bands")),
        ("loss upward", val("3 loss vs thickness", "up, all path cells"),
         val("5 distance control", "loss up, within distance bands")),
        ("loss under stream", val("3 loss vs thickness", "sink, all path cells"),
         val("5 distance control", "loss sink, within distance bands")),
        ("|F - P|, start cell", val("4 start cells", "|F-P| vs th_start, within 2 km of wells"),
         val("5 distance control", "|F-P| vs th_start, within 2 km of wells, within distance bands")),
        ("|F - P|, column sum", val("4 start cells", "|F-P| vs th_column, within 2 km of wells"),
         val("5 distance control", "|F-P| vs th_column, within 2 km of wells, within distance bands")),
        ("disputed class, start cell", val("4 start cells", "disputed class share vs th_start, within 2 km of wells"),
         val("5 distance control", "disputed class share vs th_start, within 2 km of wells, within distance bands")),
    ], columns=["label", "raw", "controlled"])
    s = pd.read_csv(DIAG / "split_cells.csv").drop_duplicates("cell")
    split_th = th.ravel()[s["cell"]]
    return [figure(cells, b, split_th[np.isfinite(split_th)], p, summary, DIAG / "fig6_thickness.png")]


if __name__ == "__main__":
    for path in main():
        print(path)
