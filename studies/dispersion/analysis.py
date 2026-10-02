"""Metrics of the dispersion study: analytical capture zone, raster sampling and zone metrics.

All zone metrics are computed on one fine raster shared by every grid, so DIS and DISV results
and different cell sizes are compared on the same points. A grid's per-cell field F is sampled
at the raster points (point-in-cell), then compared with a reference field on the raster (the
analytical capture-zone indicator, or a particle capture fraction) inside an evaluation window
that leaves out a band along the model boundary.

Metrics per field F against a reference R (0/1 or a fraction):
- area_t: area where F >= t, for each threshold t, and its error relative to the reference
  area (area where R >= 0.5);
- jaccard_t: |{F >= t} and {R >= 0.5}| / |{F >= t} or {R >= 0.5}|;
- missed_t: share of the reference zone where F < t (0: the zone F >= t covers it all);
- band_width: area where 0.1 < F < 0.9 divided by the length L of the reference zone edge
  (the R = 0.5 contour in the window): the mean distance between the F = 0.1 and F = 0.9
  contours across the zone edge;
- smear_width: integral of |F - R| over the window divided by L (mean misplaced width);
- f_area: integral of F over the window (for full mixing in a confined layer the flux-weighted
  mean travel time to the well is porosity x thickness x f_area over the whole domain / Q).
Widths are also given in cell units (divided by the grid's mean cell size).
"""

import contourpy
import numpy as np
from matplotlib.path import Path as MplPath

THRESHOLDS = (0.01, 0.1, 0.5)
JITTER = (1.1e-6, 0.7e-6)  # moves raster points off cell edges for the point-in-polygon test
BAND = (0.1, 0.9)


def capture_zone_mask(x: np.ndarray, y: np.ndarray, spec) -> np.ndarray:
    """Return True where (x, y) lies in the analytical capture zone of uniform flow + a well.

    In flow-aligned coordinates (s along the regional flow, n across, well at the origin) the
    dividing streamline is s = n / tan(2 pi U n / Q) for |n| < Q / (2 U), with U the regional
    discharge per unit width; the zone is the upstream side, s <= that curve (Javandel and
    Tsang 1986; stagnation point at s = Q / (2 pi U)).
    """
    theta = np.radians(spec.angle_deg)
    dx, dy = np.asarray(x) - spec.well_x, np.asarray(y) - spec.well_y
    s = dx * np.cos(theta) + dy * np.sin(theta)
    n = np.abs(-dx * np.sin(theta) + dy * np.cos(theta))
    u, q = spec.regional_discharge, spec.rate
    half = q / (2.0 * u)
    inside = n < half
    angle = 2.0 * np.pi * u * np.where(inside, n, 0.0) / q
    with np.errstate(divide="ignore", invalid="ignore"):
        divide = np.where(n > 1e-9, n / np.tan(angle), q / (2.0 * np.pi * u))
    return inside & (s <= divide)


def divide_line(spec, n_points: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Return x, y of the analytical dividing streamline (both branches, for plotting)."""
    u, q = spec.regional_discharge, spec.rate
    n = np.linspace(-0.4999, 0.4999, n_points) * q / u
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(np.abs(n) > 1e-9, n / np.tan(2.0 * np.pi * u * n / q), q / (2 * np.pi * u))
    theta = np.radians(spec.angle_deg)
    x = spec.well_x + s * np.cos(theta) - n * np.sin(theta)
    y = spec.well_y + s * np.sin(theta) + n * np.cos(theta)
    return x, y


def raster_points(lx: float, ly: float, spacing: float) -> tuple[np.ndarray, np.ndarray]:
    """Return 2D arrays of raster-cell centres over [0, lx] x [0, ly] (row 0 at y = 0)."""
    xs = np.arange(spacing / 2, lx, spacing)
    ys = np.arange(spacing / 2, ly, spacing)
    return np.meshgrid(xs, ys)


def raster_cells(modelgrid, xr: np.ndarray, yr: np.ndarray, spacing: float) -> np.ndarray:
    """Return the one-layer cell number containing each raster point (-1 if none)."""
    if modelgrid.grid_type == "structured":
        col = np.searchsorted(np.cumsum(modelgrid.delr), xr, side="right")
        row = np.searchsorted(np.cumsum(modelgrid.delc), np.sum(modelgrid.delc) - yr, side="right")
        return row * modelgrid.ncol + col
    index = np.full(xr.shape, -1, dtype=np.int64)
    x0, y0 = xr[0, 0], yr[0, 0]
    for i in range(modelgrid.ncpl):
        poly = np.asarray(modelgrid.get_cell_vertices(i))
        c0 = max(int(np.floor((poly[:, 0].min() - x0) / spacing)), 0)
        c1 = min(int(np.ceil((poly[:, 0].max() - x0) / spacing)) + 1, xr.shape[1])
        r0 = max(int(np.floor((poly[:, 1].min() - y0) / spacing)), 0)
        r1 = min(int(np.ceil((poly[:, 1].max() - y0) / spacing)) + 1, xr.shape[0])
        sub_x, sub_y = xr[r0:r1, c0:c1] + JITTER[0], yr[r0:r1, c0:c1] + JITTER[1]
        hit = MplPath(poly).contains_points(np.column_stack([sub_x.ravel(), sub_y.ravel()]))
        block = index[r0:r1, c0:c1]
        block[hit.reshape(block.shape) & (block < 0)] = i
    assert (index >= 0).all(), "some raster points are not inside any cell"
    return index


def window_mask(xr: np.ndarray, yr: np.ndarray, lx: float, ly: float, margin: float) -> np.ndarray:
    """Return the raster points at least margin from the domain boundary."""
    return (xr > margin) & (xr < lx - margin) & (yr > margin) & (yr < ly - margin)


def contour_length(xr: np.ndarray, yr: np.ndarray, field: np.ndarray, level: float = 0.5) -> float:
    """Return the total length of the level contour of a raster field."""
    lines = contourpy.contour_generator(xr, yr, field).lines(level)
    return float(sum(np.hypot(*np.diff(seg, axis=0).T).sum() for seg in lines))


def cell_average(index: np.ndarray, values: np.ndarray, n_cells: int) -> np.ndarray:
    """Return the per-cell mean of raster values (the cell-averaged reference field)."""
    total = np.bincount(index.ravel(), weights=values.ravel().astype(float), minlength=n_cells)
    count = np.bincount(index.ravel(), minlength=n_cells)
    return np.divide(total, count, out=np.zeros(n_cells), where=count > 0)


def zone_metrics(
    f: np.ndarray,
    ref: np.ndarray,
    window: np.ndarray,
    pixel_area: float,
    edge_length: float,
    cell_size: float,
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> dict[str, float]:
    """Return the zone metrics of a raster field f against a reference ref (see module)."""
    f, ref_zone = f[window], ref[window] >= 0.5
    ref_area = ref_zone.sum() * pixel_area
    out = {"ref_area": float(ref_area), "f_area": float(f.sum() * pixel_area)}
    for t in thresholds:
        zone = f >= t
        out[f"area_{t}"] = float(zone.sum() * pixel_area)
        out[f"area_err_{t}"] = float(zone.sum() * pixel_area / ref_area - 1.0)
        out[f"missed_{t}"] = float((ref_zone & ~zone).sum() / ref_zone.sum())
        union = (zone | ref_zone).sum()
        out[f"jaccard_{t}"] = float((zone & ref_zone).sum() / union) if union else 1.0
    band = ((f > BAND[0]) & (f < BAND[1])).sum() * pixel_area
    out["band_width"] = float(band / edge_length)
    out["smear_width"] = float(np.abs(f - ref[window]).sum() * pixel_area / edge_length)
    out["band_cells"] = out["band_width"] / cell_size
    out["smear_cells"] = out["smear_width"] / cell_size
    return out


def convergence_rate(h: np.ndarray, error: np.ndarray) -> float:
    """Return the least-squares slope of log|error| against log h (NaN if fewer than 2 points)."""
    keep = np.abs(error) > 0
    if keep.sum() < 2:
        return float("nan")
    return float(np.polyfit(np.log(h[keep]), np.log(np.abs(error[keep])), 1)[0])
