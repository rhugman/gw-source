"""FloPy builders for the small MF6 test models; each builds, writes and runs one model."""

from .common import BaseSpec, ModelRun
from .mover import build_mover_dis
from .networks import build_lak_uzf_dis, build_maw_dis
from .structured import build_base_dis, build_layered_dis, build_transient_dis, build_xt3d_dis
from .unstructured import build_base_disu, build_voronoi_disv

MODEL_KEYS = (
    "m1_dis",
    "m2_dis3lay",
    "m3_disv",
    "m4_disu_vert",
    "m4_disu_novert",
    "m5_xt3d",
    "m6_transient",
    "m7_mover",
    "m8_maw",
    "m9_lak_uzf",
)


def build_model(key: str, ws, mf6_exe, triangle_exe) -> ModelRun:
    """Build and run the test model named by key."""
    builders = {
        "m1_dis": lambda: build_base_dis(ws, mf6_exe),
        "m2_dis3lay": lambda: build_layered_dis(ws, mf6_exe),
        "m3_disv": lambda: build_voronoi_disv(ws, mf6_exe, triangle_exe),
        "m4_disu_vert": lambda: build_base_disu(ws, mf6_exe, with_vertices=True),
        "m4_disu_novert": lambda: build_base_disu(ws, mf6_exe, with_vertices=False),
        "m5_xt3d": lambda: build_xt3d_dis(ws, mf6_exe),
        "m6_transient": lambda: build_transient_dis(ws, mf6_exe),
        "m7_mover": lambda: build_mover_dis(ws, mf6_exe),
        "m8_maw": lambda: build_maw_dis(ws, mf6_exe),
        "m9_lak_uzf": lambda: build_lak_uzf_dis(ws, mf6_exe),
    }
    assert key in builders, f"unknown test model {key!r}"
    return builders[key]()

__all__ = [
    "MODEL_KEYS",
    "BaseSpec",
    "ModelRun",
    "build_base_dis",
    "build_base_disu",
    "build_lak_uzf_dis",
    "build_layered_dis",
    "build_maw_dis",
    "build_model",
    "build_mover_dis",
    "build_transient_dis",
    "build_voronoi_disv",
    "build_xt3d_dis",
]
