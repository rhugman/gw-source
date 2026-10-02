"""Reshape per-cell results to the model grid, save them to .npz, and draw a quick-look map.

Grid shapes: (nlay, nrow, ncol) for DIS, (nlay, ncpl) for DISV, (nodes,) for DISU and hand-built
graphs. Inactive cells are NaN. The .npz keys are '<output>__<group>' for per-group arrays and
'<output>__<group>__<package>' for the by-term splits; netCDF and GeoPackage come in Phase 2.
"""

from pathlib import Path

import numpy as np

from .flowstep import FlowStep
from .metrics import BackwardResult, ForwardResult

KEY_SEP = "__"
BACKWARD_ARRAYS = (
    "fraction_through",
    "volume_through",
    "flux_through",
    "volume_from",
    "fraction_from_cell_input",
    "fraction_from_total",
    "flux_from",
)
BACKWARD_SPLITS = ("volume_from_by_term",)
FORWARD_ARRAYS = ("source_fraction", "volume_through", "volume_to")
FORWARD_SPLITS = ("volume_to_by_term",)


def to_grid(step: FlowStep, values: np.ndarray) -> np.ndarray:
    """Return per-cell values reshaped to the grid, with inactive cells set to NaN."""
    values = np.asarray(values, dtype=float)
    assert values.shape == (step.n_cells,), "expected one value per cell"
    out = np.where(step.active, values, np.nan)
    return out.reshape(step.grid_shape)


def result_arrays(step: FlowStep, result: BackwardResult | ForwardResult) -> dict[str, np.ndarray]:
    """Return every per-cell output as gridded arrays keyed '<output>__<group>[__<package>]'."""
    is_backward = isinstance(result, BackwardResult)
    names = BACKWARD_ARRAYS if is_backward else FORWARD_ARRAYS
    splits = BACKWARD_SPLITS if is_backward else FORWARD_SPLITS
    arrays = {}
    for name in names:
        per_group = getattr(result, name)
        for group, values in (per_group or {}).items():
            arrays[KEY_SEP.join((name, group))] = to_grid(step, values)
    for name in splits:
        for group, by_package in getattr(result, name).items():
            for package, values in by_package.items():
                arrays[KEY_SEP.join((name, group, package))] = to_grid(step, values)
    return arrays


def save_npz(path: str | Path, step: FlowStep, result: BackwardResult | ForwardResult) -> Path:
    """Save a result's gridded arrays, plus the active mask and cell area, to a compressed .npz."""
    path = Path(path)
    arrays = result_arrays(step, result)
    arrays["active"] = step.active.reshape(step.grid_shape)
    if step.area is not None:
        arrays["area"] = to_grid(step, step.area)
    np.savez_compressed(path, **arrays)
    return path


def plot_map(
    grb_file: str | Path, step: FlowStep, values: np.ndarray, layer: int = 0, ax=None, **kwargs
):
    """Draw a quick-look map of per-cell values with FloPy's PlotMapView; return the collection."""
    import flopy

    modelgrid = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False).modelgrid
    pmv = flopy.plot.PlotMapView(modelgrid=modelgrid, layer=layer, ax=ax)
    gridded = to_grid(step, values)
    return pmv.plot_array(np.ma.masked_invalid(gridded), **kwargs)
