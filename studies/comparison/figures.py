"""Figures of the comparison study (PNG, 200 dpi) from the tables and fields in output/.

Colours: one categorical hue per method family, in a fixed order (gwsource F blue, PRT 27
orange, PRT centre aqua), with the stopping rule as the line or marker style (pass solid / filled,
stop dashed / open). Capture probability is drawn with one multi-hue map (viridis, 0 to 1) on
every map panel.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import scoring  # noqa: E402

CAPTURE_CMAP = "viridis"
METHOD_STYLE = {  # method: (colour, line style, marker, filled)
    "F": ("#2a78d6", "-", "o", True),
    "PRT 27 pass": ("#eb6834", "-", "s", True),
    "PRT 27 stop": ("#eb6834", "--", "s", False),
    "PRT centre pass": ("#1baf7a", "-", "^", True),
    "PRT centre stop": ("#1baf7a", "--", "^", False),
}
REFERENCES = ("R_adv", "R_disp 0.1", "R_disp 1", "R_disp 10")
REF_TITLES = {"R_adv": "advective R_adv", "R_disp 0.1": "R_disp, $\\alpha_T$ = 0.1 m",
              "R_disp 1": "R_disp, $\\alpha_T$ = 1 m", "R_disp 10": "R_disp, $\\alpha_T$ = 10 m"}
RATIO_TICKS_W = (0.025, 0.05, 0.1, 0.2, 0.4)
RATIO_TICKS_DISP = (0.1, 0.3, 1.0, 3.0, 10.0)
DX_TICKS = (6.25, 12.5, 25.0, 50.0, 100.0)
PHYSICAL_TITLES = {"full_near": "full screen, stream near", "full_far": "full screen, stream far",
                   "lower_near": "lower screen, stream near",
                   "lower_far": "lower screen, stream far"}


def style() -> None:
    """Set a quiet house style: thin recessive axes and grid."""
    plt.rcParams.update({
        "font.size": 8, "axes.linewidth": 0.6, "axes.edgecolor": "0.35",
        "axes.labelcolor": "0.15", "xtick.color": "0.35", "ytick.color": "0.35",
        "grid.color": "0.88", "grid.linewidth": 0.5, "axes.grid": True,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "lines.linewidth": 1.6, "lines.markersize": 4.5,
    })


def dx_axis(ax, ticks=DX_TICKS) -> None:
    """Log cell-size axis with plain tick labels."""
    ax.set_xscale("log")
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.set_xlabel("cell size $\\Delta x$ (m)")


def plot_method(ax, x, y, method: str, label: bool = True) -> None:
    """Draw one method's line with its fixed colour, line style and marker."""
    colour, ls, marker, filled = METHOD_STYLE[method]
    ax.plot(x, y, ls=ls, marker=marker, color=colour, mfc=colour if filled else "white",
            mec=colour, label=method if label else None)


def convergence(series: pd.DataFrame, nlay: int, path: Path) -> None:
    """Area of F > 0.5 and P > 0.5 against cell size, per physical case, on nlay layers."""
    horizontal = series[series["nlay"] == nlay]
    fig, axes = plt.subplots(1, 4, figsize=(9.0, 2.6), sharey=True, constrained_layout=True)
    for ax, (physical, title) in zip(axes, PHYSICAL_TITLES.items()):
        part = horizontal[horizontal["physical"] == physical]
        for method, key, label in (("F", "F", "gwsource F > 0.5"),
                                   ("PRT 27 pass", "PRT 27 well", "PRT 27, P > 0.5")):
            rows = part[part["method"] == key].sort_values("dx")
            colour, ls, marker, _ = METHOD_STYLE[method]
            ax.plot(rows["dx"], rows["area"] / 1e4, ls=ls, marker=marker, color=colour,
                    label=label)
        dx_axis(ax)
        ax.set_title(title)
    axes[0].set_ylabel(f"capture area > 0.5 (ha), {nlay} layers")
    axes[0].legend(loc="best")
    fig.savefig(path, dpi=200)
    plt.close(fig)


ERROR_METRICS = (("jaccard", "1 $-$ Jaccard, > 0.5 areas"), ("rmse", "capture RMSE"),
                 ("share_error_max", "largest source-share error"))


def error_grid(scores: pd.DataFrame, by: str, path: Path) -> None:
    """Errors against cell size or layer count (rows: references; columns: metrics).

    Each point is the mean over the other grid variable and the four physical cases.
    """
    fig, axes = plt.subplots(len(REFERENCES), len(ERROR_METRICS), figsize=(8.0, 9.0),
                             sharex=True, sharey="col", constrained_layout=True)
    for i, ref in enumerate(REFERENCES):
        part = scores[scores["reference"] == ref]
        for method in METHOD_STYLE:
            mean = part[part["method"] == method].groupby(by)[[m for m, _ in ERROR_METRICS]]
            mean = mean.mean()
            for j, (metric, _) in enumerate(ERROR_METRICS):
                y = 1.0 - mean[metric] if metric == "jaccard" else mean[metric]
                plot_method(axes[i, j], mean.index, y, method, i == 0 and j == 0)
        axes[i, 0].set_ylabel(REF_TITLES[ref])
    for j, (_, title) in enumerate(ERROR_METRICS):
        axes[0, j].set_title(title)
        axes[0, j].set_ylim(bottom=0.0)
        for ax in axes[:, j]:
            if by == "dx":
                dx_axis(ax, DX_TICKS[1:])
            else:
                ax.set_xscale("log", base=2)
                ax.set_xticks([1, 2, 4, 8], ["1", "2", "4", "8"])
                ax.minorticks_off()
                ax.set_xlabel("layers")
    for ax in axes[:-1].ravel():
        ax.set_xlabel("")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncol=5)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def paired(scores: pd.DataFrame, ref_mask, metric: str, a: str, b: str) -> pd.DataFrame:
    """Return rows with method a's and b's metric side by side, per case and reference."""
    keys = ["label", "reference"]
    part = scores[ref_mask]
    left = part[part["method"] == a].set_index(keys)
    right = part[part["method"] == b].set_index(keys)[metric]
    return left.assign(other=right).reset_index()


def error_vs_ratio(scores: pd.DataFrame, path: Path) -> None:
    """Errors against dx / W (R_adv) and dx / sqrt(alpha_T L) (R_disp), and F minus P."""
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.6), constrained_layout=True)
    adv = scores["reference"] == "R_adv"
    disp = scores["reference"].str.startswith("R_disp")
    for method in ("F", "PRT 27 pass", "PRT centre pass"):
        colour, _, marker, _ = METHOD_STYLE[method]
        a = scores[adv & (scores["method"] == method)]
        d = scores[disp & (scores["method"] == method)]
        axes[0, 0].scatter(a["dx_over_w"], 1.0 - a["jaccard"], s=12, color=colour,
                           marker=marker, label=method, alpha=0.8, lw=0)
        axes[1, 0].scatter(d["dx_over_disp"], d["rmse"], s=12, color=colour, marker=marker,
                           alpha=0.8, lw=0)
    for ax, mask, x, metric in ((axes[0, 1], adv, "dx_over_w", "jaccard"),
                                (axes[1, 1], disp, "dx_over_disp", "rmse")):
        pair = paired(scores, mask, metric, "F", "PRT 27 pass")
        diff = pair[metric] - pair["other"]
        if metric == "jaccard":
            diff = -diff  # positive: F has the larger error
        for alpha, marker in ((0.0, "o"), (0.1, "v"), (1.0, "s"), (10.0, "D")):
            hit = pair["alpha_t"] == alpha
            if hit.any():
                label = "R_adv" if alpha == 0 else f"$\\alpha_T$ = {alpha:g} m"
                ax.scatter(pair.loc[hit, x], diff[hit], s=12, marker=marker, color="0.3",
                           facecolor="none" if alpha else "0.3", lw=0.7, label=label)
        ax.axhline(0.0, color="0.2", lw=0.8)
    for ax in axes[0]:
        ax.set_xscale("log")
        ax.set_xticks(RATIO_TICKS_W, [f"{t:g}" for t in RATIO_TICKS_W])
        ax.minorticks_off()
    for ax in axes[1]:
        ax.set_xscale("log")
        ax.set_xticks(RATIO_TICKS_DISP, [f"{t:g}" for t in RATIO_TICKS_DISP])
        ax.minorticks_off()
    axes[0, 0].set_ylabel("1 $-$ Jaccard against R_adv")
    axes[0, 1].set_ylabel("error of F $-$ error of PRT 27 pass\n(1 $-$ Jaccard, R_adv)")
    axes[1, 0].set_ylabel("RMSE against R_disp")
    axes[1, 1].set_ylabel("RMSE of F $-$ RMSE of PRT 27 pass\n(R_disp)")
    for ax in axes[0]:
        ax.set_xlabel("$\\Delta x$ / W (capture-zone width near the well)")
    for ax in axes[1]:
        ax.set_xlabel("$\\Delta x$ / $\\sqrt{\\alpha_T L}$ (transverse dispersion length)")
    axes[0, 0].legend(loc="lower right")
    axes[1, 1].legend(loc="best")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def map_panels(panels: list[tuple[str, np.ndarray, float]], outline: tuple[np.ndarray, float],
               well_xy: tuple[float, float], stream_x: float, extent_xy: tuple[float, float],
               window: tuple[float, float, float, float], path: Path) -> None:
    """Map capture-probability fields (title, (nrow, ncol) field, dx) with the R_adv 0.5 edge
    (white line), the stream (dashed) and the well (red dot)."""
    fig, axes = plt.subplots(1, len(panels), figsize=(2.3 * len(panels) + 0.8, 2.6),
                             sharey=True, constrained_layout=True)
    lx, ly = extent_xy
    ref, ref_dx = outline
    xr = (np.arange(ref.shape[1]) + 0.5) * ref_dx
    yr = ly - (np.arange(ref.shape[0]) + 0.5) * ref_dx
    for ax, (title, field, _) in zip(axes, panels):
        image = ax.imshow(field, extent=(0, lx, 0, ly), origin="upper", cmap=CAPTURE_CMAP,
                          vmin=0.0, vmax=1.0, interpolation="nearest")
        ax.contour(xr, yr, ref, levels=[0.5], colors="white", linewidths=0.8)
        ax.axvline(stream_x, color="white", lw=0.8, ls="--")
        ax.plot(*well_xy, marker="o", ms=4, color="#e34948", mec="k", mew=0.4)
        ax.set_xlim(window[0], window[1])
        ax.set_ylim(window[2], window[3])
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.grid(False)
        ax.set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    fig.colorbar(image, ax=axes, shrink=0.9, label="capture probability (-)")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def mapped_reference(fine: np.ndarray, fine_dx: float, dx: float, rech: float) -> np.ndarray:
    """Return a fine reference field on the coarse grid (scoring.to_coarse)."""
    weight = np.full(fine.shape, rech * fine_dx**2)
    return scoring.to_coarse(fine, weight, scoring.block_factor(fine_dx, dx))
