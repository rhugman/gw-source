"""The analytical reference of the dispersion study (studies/dispersion): capture-zone geometry.

For uniform flow U (per unit width) and a well pumping Q, the capture zone is Q / (2 U) wide in
total at the well, tends to Q / U far upstream, and its stagnation point lies Q / (2 pi U)
downstream of the well (Javandel and Tsang 1986). Checked for a flow direction oblique to x.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "studies" / "dispersion"))
import analysis as an  # noqa: E402
import problems as pb  # noqa: E402


def zone_width(spec, s: float, n_points: int = 200_001) -> float:
    """Return the width of the analytical zone across the flow at distance s along the flow."""
    theta = np.radians(spec.angle_deg)
    n = np.linspace(-1.0, 1.0, n_points) * spec.rate / spec.regional_discharge
    x = spec.well_x + s * np.cos(theta) - n * np.sin(theta)
    y = spec.well_y + s * np.sin(theta) + n * np.cos(theta)
    inside = an.capture_zone_mask(x, y, spec)
    return float(inside.sum() * (n[1] - n[0]))


@pytest.mark.parametrize("angle", [0.0, 30.0])
def test_analytic_capture_zone_geometry(angle):
    """Width Q/(2U) at the well, Q/U far upstream, nothing beyond the stagnation point."""
    spec = pb.AnalyticSpec(angle_deg=angle)
    full = spec.rate / spec.regional_discharge
    assert zone_width(spec, 0.0) == pytest.approx(full / 2, rel=1e-3)
    far = 20 * full  # far upstream the width falls short of Q/U by Q^2 / (2 pi U^2 s)
    deficit = spec.rate**2 / (2 * np.pi * spec.regional_discharge**2 * far)
    assert zone_width(spec, -far) == pytest.approx(full - deficit, rel=1e-4)
    stagnation = spec.rate / (2 * np.pi * spec.regional_discharge)
    assert zone_width(spec, 0.99 * stagnation) > 0.0
    assert zone_width(spec, 1.01 * stagnation) == 0.0


def test_analytic_head_is_uniform_flow_far_from_the_well():
    """The boundary heads follow the regional gradient along the flow direction."""
    spec = pb.AnalyticSpec(angle_deg=30.0, rate=0.0)
    theta = np.radians(spec.angle_deg)
    x = spec.well_x + np.array([0.0, 100.0]) * np.cos(theta)
    y = spec.well_y + np.array([0.0, 100.0]) * np.sin(theta)
    h = pb.analytic_head(x, y, spec)
    assert h[0] - h[1] == pytest.approx(100.0 * spec.gradient)
