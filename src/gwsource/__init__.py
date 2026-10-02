"""Cell-mixing flow tracing for MODFLOW 6 output (Foley & Black 2013; Black & Foley 2013)."""

from . import diagnostics, export
from .config import TraceConfig
from .flowstep import FlowStep, Package, from_edges
from .metrics import BackwardResult, ForwardResult
from .mf6io import available_steps, find_model_files, read_step, read_step_files
from .selectors import Selection, groups_by_package, groups_by_term, select, select_cells
from .trace import backward, forward

__version__ = "0.0.1"

__all__ = [
    "BackwardResult",
    "FlowStep",
    "ForwardResult",
    "Package",
    "Selection",
    "TraceConfig",
    "available_steps",
    "backward",
    "diagnostics",
    "export",
    "find_model_files",
    "forward",
    "from_edges",
    "groups_by_package",
    "groups_by_term",
    "read_step",
    "read_step_files",
    "select",
    "select_cells",
]
