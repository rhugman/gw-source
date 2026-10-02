"""Cell-mixing flow tracing for MODFLOW 6 output (Foley & Black 2013; Black & Foley 2013)."""

from . import diagnostics, export, transient
from .config import TraceConfig
from .flowstep import FlowStep, Package, from_edges
from .metrics import BackwardResult, ForwardResult
from .mf6io import (
    StepReader,
    available_steps,
    find_model_files,
    open_files,
    open_model,
    read_step,
    read_step_files,
)
from .selectors import (
    Selection,
    groups_by_boundname,
    groups_by_package,
    groups_by_term,
    groups_by_zone,
    select,
    select_cells,
    select_zone,
)
from .trace import backward, forward
from .transient import TransientConfig, TransientResult, trace_transient

__version__ = "0.0.1"

__all__ = [
    "BackwardResult",
    "FlowStep",
    "ForwardResult",
    "Package",
    "Selection",
    "StepReader",
    "TraceConfig",
    "TransientConfig",
    "TransientResult",
    "available_steps",
    "backward",
    "diagnostics",
    "export",
    "find_model_files",
    "forward",
    "from_edges",
    "groups_by_boundname",
    "groups_by_package",
    "groups_by_term",
    "groups_by_zone",
    "open_files",
    "open_model",
    "read_step",
    "read_step_files",
    "select",
    "select_cells",
    "select_zone",
    "trace_transient",
    "transient",
]
