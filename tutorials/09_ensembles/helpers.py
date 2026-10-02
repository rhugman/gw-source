"""Helpers local to tutorial 09 (ensembles): per-realisation summaries and a process-pool check.

gwsource.run_ensemble folds per-cell outputs into statistics over the realisations. The
well's split by source package is a sum over cells, not a per-cell output, so this module
traces each realisation once more to tabulate it (cheap for a small model).
"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

import gwsource as gs


def process_pool_available() -> bool:
    """Return False where the OS refuses process pools (e.g. a sandbox without semaphores)."""
    try:
        ProcessPoolExecutor(max_workers=1).shutdown()
    except (PermissionError, NotImplementedError, OSError):  # raised by the system-limits check
        return False
    return True


def realisation_summary(
    ws: Path, group: str, select_kwargs: dict, thresholds: tuple[float, ...]
) -> dict[str, float]:
    """Return one realisation's source shares of the group and its capture areas [km2]."""
    step = gs.read_step(ws, boundnames=True)
    res = gs.backward(step, {group: gs.select(step, **select_kwargs)})
    by_term = res.volume_from_by_term[group]
    total = sum(float(v.sum()) for v in by_term.values())
    row = {f"share {name}": float(v.sum()) / total for name, v in by_term.items() if v.sum() > 0}
    fraction = res.fraction_through[group]
    for t in thresholds:
        row[f"area F>{t} (km2)"] = float(step.area[fraction > t].sum()) / 1e6
    return row


def summarise_realisations(
    workspaces: list[Path], group: str, select_kwargs: dict, thresholds: tuple[float, ...]
) -> pd.DataFrame:
    """Return a table with one row per realisation (shares by source package, capture areas)."""
    rows = {
        Path(ws).name: realisation_summary(ws, group, select_kwargs, thresholds)
        for ws in workspaces
    }
    return pd.DataFrame(rows).T.fillna(0.0)


def max_quantile_difference(
    exact: gs.EnsembleResult, approx: gs.EnsembleResult, output: str, group: str
) -> dict[float, float]:
    """Return {quantile: largest |approx - exact|} over the cells whose values all lie in range."""
    low, high = exact.config.bin_range(output)
    tol = 1e-9 * (high - low)  # round-off, e.g. F = 1 + 1e-15
    stats = exact.stats
    inside = (stats["min"][output][group] >= low - tol) & (stats["max"][output][group] <= high + tol)
    out = {}
    for q in exact.config.quantiles:
        a, b = exact.quantiles[q][output][group], approx.quantiles[q][output][group]
        cells = inside & np.isfinite(a) & np.isfinite(b)
        out[q] = float(np.abs(a[cells] - b[cells]).max())
    return out
