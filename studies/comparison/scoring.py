"""Map the fine references to coarse grids and score coarse-grid captures against them.

Fine to coarse. Every coarse cell (dx = 12.5 to 100 m) is an exact block of fine cells (the
fine cell size divides it, and both grids start at the plan origin). The reference value of a
coarse cell is the flow-weighted mean of the reference capture probability over the fine top
cells inside it, the weights being their recharge inflow:

    R_c = sum_f (q_f R_f) / sum_f q_f.

This is the share of the coarse cell's recharge that reaches the well, which is exactly what
F and P estimate for that cell, so it is the target a perfect coarse method would hit. Here the
recharge rate is uniform, so the weights are equal and R_c is the area share of the coarse
cell that is captured; the weights are kept so the rule stays right for non-uniform recharge.

Metrics of a coarse field M against a reference (R_c on the coarse grid, R_f on the fine):
- jaccard: |{M > 0.5} and {R_c > 0.5}| / |{M > 0.5} or {R_c > 0.5}|, cells of equal area;
- size_ratio: area(M > 0.5) / area(R_f > 0.5), the physical area of the fine reference;
- rmse: root mean square of M - R_c over the cells where either is above 0.01;
- share_error_<source>: method share - reference share of the well's pumping;
- closure: the method's traced water / pumping (the reference closures are reported apart).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_LABELS = ("recharge", "stream", "inflow")
KEEP_COLUMNS = ("label", "physical", "screen", "stream", "dx", "nlay", "method", "closure",
                "well_weak_share", "n_particles")
RMSE_FLOOR = 0.01
THRESHOLD = 0.5


def block_factor(fine_dx: float, coarse_dx: float) -> int:
    """Return the number of fine cells along one coarse cell side (asserts an exact nesting)."""
    factor = round(coarse_dx / fine_dx)
    assert factor >= 1 and abs(factor * fine_dx - coarse_dx) < 1e-9, (
        f"fine cell size {fine_dx} does not nest in {coarse_dx}"
    )
    return factor


def to_coarse(fine: np.ndarray, weight: np.ndarray, factor: int) -> np.ndarray:
    """Return the weight-averaged block means of a fine (nrow, ncol) field."""
    nr, nc = fine.shape
    assert nr % factor == 0 and nc % factor == 0, "the fine grid does not tile the coarse grid"
    shape = (nr // factor, factor, nc // factor, factor)
    num = (fine * weight).reshape(shape).sum(axis=(1, 3))
    den = weight.reshape(shape).sum(axis=(1, 3))
    assert (den > 0).all(), "a coarse cell has no recharge weight"
    return num / den


def zone_width(fine: np.ndarray, dx: float, well_x: float, band: float) -> float:
    """Return the mean width of the fine zone (> 0.5) over the `band` m up-gradient of the well."""
    xc = (np.arange(fine.shape[1]) + 0.5) * dx
    cols = (xc > well_x - band) & (xc < well_x)
    return float((fine[:, cols] > THRESHOLD).sum() * dx * dx / band)


def zone_length(fine: np.ndarray, dx: float, well_x: float) -> float:
    """Return the along-flow length of the fine zone: well x minus the zone's west end."""
    cols = np.flatnonzero((fine > THRESHOLD).any(axis=0))
    assert len(cols), "empty reference zone"
    return float(well_x - cols.min() * dx)


def score(method: np.ndarray, ref_coarse: np.ndarray, ref_fine_area: float,
          dx: float) -> dict:
    """Return Jaccard, size ratio and RMSE of a coarse field against a reference."""
    m, r = method > THRESHOLD, ref_coarse > THRESHOLD
    union = (m | r).sum()
    keep = np.maximum(method, ref_coarse) > RMSE_FLOOR
    return {
        "jaccard": float((m & r).sum() / union) if union else 1.0,
        "size_ratio": float(m.sum() * dx * dx / ref_fine_area),
        "rmse": float(np.sqrt(np.mean((method[keep] - ref_coarse[keep]) ** 2))),
    }


def share_errors(shares: dict, ref_shares: dict) -> dict:
    """Return method share minus reference share per source, and the largest magnitude."""
    out = {f"share_error_{k}": shares[k] - ref_shares[k] for k in ref_shares}
    out["share_error_max"] = max(abs(v) for v in out.values())
    return out


# ---------------------------------------------------------------- the score table


def load_references(refs: Path, physical: str, disp_dx: float) -> tuple[dict, dict]:
    """Return {reference name: (fine field, fine dx, shares)} and the R_adv summary."""
    adv = json.loads((refs / f"adv_{physical}.json").read_text())
    adv_fields = np.load(refs / f"adv_{physical}.npz")
    out = {"R_adv": (adv_fields["PRT 27 well"], adv["dx"], adv["shares"])}
    name = f"disp_{physical}_dx{disp_dx:g}".replace(".", "p")
    disp = json.loads((refs / f"{name}.json").read_text())
    disp_fields = np.load(refs / f"{name}.npz")
    for key in disp_fields.files:
        out[key] = (disp_fields[key], disp_dx, disp[key]["shares"])
    return out, adv


def reference_rows(physical: str, dx: float, refs: dict, rech: float) -> list[dict]:
    """Return the score of each mapped reference against itself (the discretisation floor)."""
    rows = []
    for name, (fine, fine_dx, shares) in refs.items():
        mapped = to_coarse(fine, np.full(fine.shape, rech * fine_dx**2),
                           block_factor(fine_dx, dx))
        area = float((fine > THRESHOLD).sum() * fine_dx**2)
        rows.append({"physical": physical, "dx": dx, "reference": name, "method": "mapped",
                     **score(mapped, mapped, area, dx)})
    return rows


def score_table(coarse: pd.DataFrame, fields_dir: Path, refs_dir: Path, disp_dx: float,
                rech: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the scores of every coarse field against every reference, and the floor rows."""
    rows, floor = [], []
    for physical, part in coarse.groupby("physical"):
        refs, adv = load_references(refs_dir, physical, disp_dx)
        mapped = {}
        for dx in sorted(part["dx"].unique()):
            floor += reference_rows(physical, dx, refs, rech)
            for name, (fine, fine_dx, _) in refs.items():
                weight = np.full(fine.shape, rech * fine_dx**2)
                mapped[name, dx] = to_coarse(fine, weight, block_factor(fine_dx, dx))
        for _, row in part.iterrows():
            fields = np.load(fields_dir / f"{row['label']}.npz")
            field = fields[row["method"]]
            shares = {k: row[f"share_{k}"] for k in SOURCE_LABELS}
            for name, (fine, fine_dx, ref_shares) in refs.items():
                alpha = float(name.split()[-1]) if name.startswith("R_disp") else 0.0
                area = float((fine > THRESHOLD).sum() * fine_dx**2)
                rows.append({
                    **{k: row[k] for k in KEEP_COLUMNS}, "reference": name,
                    "alpha_t": alpha, "W": adv["W"], "L": adv["L"],
                    "dx_over_w": row["dx"] / adv["W"],
                    "dx_over_disp": row["dx"] / np.sqrt(alpha * adv["L"]) if alpha else np.nan,
                    **score(field, mapped[name, row["dx"]], area, row["dx"]),
                    **share_errors(shares, ref_shares),
                })
    return pd.DataFrame(rows), pd.DataFrame(floor)
