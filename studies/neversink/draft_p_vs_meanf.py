"""DRAFT figure for discussion, not for the paper: published probability of contribution P
against ensemble mean F on the start cells of the published particles.

(a) joint distribution of P and mean F (2D histogram, log counts) with the median of mean F in
P bins and its 10-90 % band; (b) mean F - P in the cluster U window of SI Fig. S1. Windows,
wells and SFR reaches come from paper_figures.py. Reads stored outputs only.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm, ListedColormap

import ensemble_run
import paper_figures as pfig
import neversink_figures as nvf
import workflow as wf

OUT_PNG = pfig.OVERLEAF / "si_2026-10-29" / "drafts" / "p_vs_meanf.png"
SHOWN = 0.01  # cells with mean F below this and P = 0 are left out of (a), grey in (b)
P_EDGES = np.linspace(0.0, 1.0, 11)
SPLIT = 0.5  # quadrant threshold on P and mean F


def start_values(maps_file: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return the P and mean F grids and their values on the start cells."""
    maps = np.load(maps_file)
    p, mean_f = maps["mp7"], np.nan_to_num(maps["cells:mean_F"])
    starts = ensemble_run.start_cells(*p.shape)
    return p, mean_f, p.ravel()[starts], mean_f.ravel()[starts]


def binned(p: np.ndarray, f: np.ndarray, edges: np.ndarray) -> list[tuple]:
    """Return (lo, hi, n, p10, median, p90) of f in P bins over the cells with P > 0."""
    rows = []
    for k, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        last = k == len(edges) - 2
        sel = (p > lo if k == 0 else p >= lo) & (p <= hi if last else p < hi)
        q = np.percentile(f[sel], [10, 50, 90]) if sel.any() else (np.nan,) * 3
        rows.append((lo, hi, int(sel.sum()), *q))
    return rows


def report(p: np.ndarray, f: np.ndarray, rows: list[tuple]) -> None:
    """Print the checks against the author's numbers, the bins and the quadrant counts."""
    print(f"start cells {len(p)}, r = {np.corrcoef(p, f)[0, 1]:.3f}, "
          f"sum F / sum P = {f.sum() / p.sum():.3f}")
    for edges in ((0, 0.1), (0.1, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.0)):
        print(f"  check bin {edges}: median {binned(p, f, np.array(edges))[0][4]:.3f}")
    for lo, hi, n, q10, q50, q90 in rows:
        print(f"  P {lo:.1f}-{hi:.1f}: n {n:6d}  p10 {q10:.3f}  median {q50:.3f}  p90 {q90:.3f}")
    hp, hf = p >= SPLIT, f >= SPLIT
    print(f"  P>=0.5 & F>=0.5 {np.sum(hp & hf)}, P>=0.5 & F<0.5 {np.sum(hp & ~hf)}, "
          f"P<0.5 & F>=0.5 {np.sum(~hp & hf)}, P<0.5 & F<0.5 {np.sum(~hp & ~hf)}")


def joint_panel(ax: plt.Axes, fig: plt.Figure, p: np.ndarray, f: np.ndarray, rows: list) -> None:
    """Draw panel (a): 2D histogram of P and mean F, 1:1 line, binned medians and band."""
    sel = (p > 0) | (f > SHOWN)
    edges = np.linspace(0, 1, 41)
    counts, _, _ = np.histogram2d(p[sel], f[sel], bins=[edges, edges])
    image = ax.pcolormesh(edges, edges, np.ma.masked_equal(counts.T, 0), cmap="viridis",
                          norm=LogNorm(vmin=1, vmax=counts.max()), rasterized=True)
    ax.plot([0, 1], [0, 1], ls="--", color=nvf.INK, lw=0.8)
    mid = np.array([(lo + hi) / 2 for lo, hi, *_ in rows])
    q10, q50, q90 = (np.array([r[k] for r in rows]) for k in (3, 4, 5))
    for q in (q10, q90):
        ax.plot(mid, q, color="#eb6834", lw=0.6)
    ax.plot(mid, q50, "o-", color="#eb6834", ms=3, lw=1.0, mec=nvf.INK, mew=0.4)
    r = np.corrcoef(p, f)[0, 1]
    ax.text(0.03, 0.97, f"r = {r:.3f}\nΣ mean F / Σ P = {f.sum() / p.sum():.3f}\n"
            f"{sel.sum():,} cells", transform=ax.transAxes, va="top", ha="left", fontsize=7)
    ax.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xlabel="published probability P",
           ylabel="ensemble mean F")
    handles = [plt.Line2D([], [], ls="--", color=nvf.INK, lw=0.8, label="1:1"),
               plt.Line2D([], [], color="#eb6834", marker="o", ms=3, mec=nvf.INK, mew=0.4,
                          label="median in P bins\n(thin: 10 and 90 %)")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.8), frameon=False,
              fontsize=6.5)
    bar = fig.colorbar(image, ax=ax, fraction=0.05, pad=0.02)
    bar.set_label("start cells per bin", fontsize=7)


def difference_panel(ax: plt.Axes, fig: plt.Figure, p: np.ndarray, mean_f: np.ndarray,
                     idomain: np.ndarray, window: tuple, segments: np.ndarray) -> None:
    """Draw panel (b): mean F - P in window, grey where both are below SHOWN."""
    nrow, ncol = p.shape
    r0, r1, c0, c1 = window
    active = (idomain > 0).any(axis=0)
    diff = np.where(active, mean_f - p, np.nan)[r0 : r1 + 1, c0 : c1 + 1]
    low = ((mean_f < SHOWN) & (p < SHOWN) & active)[r0 : r1 + 1, c0 : c1 + 1]
    extent = nvf.window_extent(window, nrow)
    ax.imshow(np.where(low, 1.0, np.nan), cmap=ListedColormap(["#d9d9d9"]), extent=extent,
              interpolation="nearest")
    image = ax.imshow(np.where(low, np.nan, diff), cmap="PuOr", vmin=-1, vmax=1, extent=extent,
                      interpolation="nearest")
    ax.add_collection(LineCollection(segments, colors=nvf.STREAM, linewidths=0.4, alpha=0.8,
                                     zorder=2))
    xk, yk = pfig.window_grid(window, nrow)
    ax.contour(xk, yk, p[r0 : r1 + 1, c0 : c1 + 1], levels=[0.5], colors=nvf.INK,
               linewidths=0.9, zorder=4)
    wells = np.array([ij for ij in nvf.well_ij(wf.PRIORITY_WELLS, (nrow, ncol)).values()
                      if r0 <= ij[0] <= r1 and c0 <= ij[1] <= c1])
    x, y = nvf.grid_km(wells[:, 0], wells[:, 1], nrow)
    ax.plot(x, y, "o", ms=3.5, mfc=nvf.SURFACE, mec=nvf.INK, mew=0.7, zorder=5)
    x0, x1, y0, y1 = pfig.aspect_limits(extent)
    ax.set(xlim=(x0, x1), ylim=(y0, y1), aspect="equal", xticks=[], yticks=[])
    pfig.scale_bar(ax, window, nrow, 2.0)
    ax.text(0.99, 0.02, "black line: P = 0.5\ngrey: P and mean F < 0.01", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6.5)
    bar = fig.colorbar(image, ax=ax, fraction=0.05, pad=0.02, shrink=0.75)
    bar.set_label("mean F − P", fontsize=7)


def main(out_png: Path = OUT_PNG) -> Path:
    """Load the stored outputs, print the numbers and draw the draft figure."""
    out = nvf.find_data_dir() / "output"
    model_dir = out / "optimal"
    idomain = wf.grid_idomain(model_dir)
    shape = idomain.shape[1:]
    published = nvf.published_mask(shape, out)
    f_cal = nvf.capture_fields(idomain, out)["streams as cells"]
    window = pfig.fig4_windows(idomain, f_cal, published, out)["U"]
    segments = nvf.model_segments(model_dir, shape[0])
    p, mean_f, p_s, f_s = start_values(out / "ensemble" / "probability_maps.npz")
    rows = binned(p_s, f_s, P_EDGES)
    report(p_s, f_s, rows)
    nvf.paper_style()
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(17 / 2.54, 8 / 2.54),
                                     width_ratios=[1, 1.15], constrained_layout=True)
    joint_panel(ax_a, fig, p_s, f_s, rows)
    ax_a.set_title("(a) start cells: P against mean F", loc="left")
    difference_panel(ax_b, fig, p, mean_f, idomain, window, segments)
    ax_b.set_title(f"(b) mean F − P, {pfig.WINDOW_TITLES['U']}", loc="left")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    return out_png


if __name__ == "__main__":
    print(main())
