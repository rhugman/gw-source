"""Cell-mixing flow tracing for MODFLOW 6 output (Foley & Black 2013; Black & Foley 2013)."""

from . import (
    diagnostics,
    ensemble,
    export,
    graphplot,
    network,
    packages,
    prt,
    tracking,
    transient,
    traveltime,
)
from .assemble import CellBudget, Edges, cell_budget, flow_edges
from .config import TraceConfig
from .ensemble import EnsembleConfig, EnsembleResult, list_realisations, run_ensemble
from .flowstep import FlowStep, NodeBlock, Package, from_edges
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
from .network import (
    NetworkReader,
    global_nodes,
    global_values,
    model_view,
    open_simulation,
    read_network,
    result_view,
)
from .prt import PrtConfig, track_particles
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
from .tracking import (
    BackwardTracking,
    ForwardTracking,
    TrackingConfig,
    track_backward,
    track_forward,
    tracking_duality,
)
from .transient import TransientConfig, TransientResult, trace_transient
from .traveltime import TravelTimeResult, travel_time, water_volume

__version__ = "0.1.0"

__all__ = [
    "BackwardResult",
    "BackwardTracking",
    "CellBudget",
    "Edges",
    "EnsembleConfig",
    "EnsembleResult",
    "FlowStep",
    "ForwardResult",
    "ForwardTracking",
    "NetworkReader",
    "NodeBlock",
    "Package",
    "PrtConfig",
    "Selection",
    "StepReader",
    "TraceConfig",
    "TrackingConfig",
    "TransientConfig",
    "TransientResult",
    "TravelTimeResult",
    "available_steps",
    "backward",
    "cell_budget",
    "diagnostics",
    "ensemble",
    "export",
    "find_model_files",
    "flow_edges",
    "forward",
    "from_edges",
    "global_nodes",
    "global_values",
    "groups_by_boundname",
    "groups_by_package",
    "groups_by_term",
    "groups_by_zone",
    "list_realisations",
    "model_view",
    "network",
    "open_simulation",
    "open_files",
    "open_model",
    "packages",
    "prt",
    "read_network",
    "read_step",
    "read_step_files",
    "result_view",
    "run_ensemble",
    "select",
    "select_cells",
    "select_zone",
    "trace_transient",
    "track_backward",
    "track_forward",
    "track_particles",
    "tracking",
    "tracking_duality",
    "transient",
    "travel_time",
    "traveltime",
    "water_volume",
]
