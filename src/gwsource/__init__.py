"""Cell-mixing flow tracing for MODFLOW 6 output (Foley & Black 2013; Black & Foley 2013)."""

from . import diagnostics, ensemble, export, prt, transient, traveltime
from .config import TraceConfig
from .ensemble import EnsembleConfig, EnsembleResult, list_realisations, run_ensemble
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
from .traveltime import TravelTimeResult, travel_time, water_volume

__version__ = "0.0.1"

__all__ = [
    "BackwardResult",
    "EnsembleConfig",
    "EnsembleResult",
    "FlowStep",
    "ForwardResult",
    "Package",
    "Selection",
    "StepReader",
    "TraceConfig",
    "TransientConfig",
    "TransientResult",
    "TravelTimeResult",
    "available_steps",
    "backward",
    "diagnostics",
    "ensemble",
    "export",
    "find_model_files",
    "forward",
    "from_edges",
    "groups_by_boundname",
    "groups_by_package",
    "groups_by_term",
    "groups_by_zone",
    "list_realisations",
    "open_files",
    "open_model",
    "prt",
    "read_step",
    "read_step_files",
    "run_ensemble",
    "select",
    "select_cells",
    "select_zone",
    "trace_transient",
    "transient",
    "travel_time",
    "traveltime",
    "water_volume",
]
