"""Tutorial-module loader and travel-time constants shared by the example-model figures.

Imported by synthetic_figures.py.
"""

import importlib.util
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))

import method_figures as mfig  # noqa: E402  (repository paths)

TUTORIAL_DIR = mfig.TUTORIAL_DIR

CAPTURE_F = 0.5  # travel times are mapped where F is above this
ZONE_YEARS = (5, 25)  # time-of-travel zones (years)


# ---------------------------------------------------------------- shared helpers


def tutorial_modules(tutorial: str, tutorial_dir: Path = TUTORIAL_DIR):
    """Import herebedragons and one tutorial's helpers.py (under a unique name); return both."""
    if str(tutorial_dir) not in sys.path:
        sys.path.insert(0, str(tutorial_dir))
    import herebedragons as hbd

    name = f"helpers_{tutorial.split('_')[0]}"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, tutorial_dir / tutorial / "helpers.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return hbd, sys.modules[name]
