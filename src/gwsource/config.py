"""Configuration of a trace: accounting mode, solver choice and net-mode cycle handling."""

from dataclasses import dataclass

ACCOUNTING_MODES = ("gross", "net")
SOLVERS = ("auto", "topological", "block", "lu")


@dataclass
class TraceConfig:
    """Options for backward() and forward().

    accounting: "gross" (default; one sink/source node per external term, outflow/inflow
        normalisation) or "net" (net source/sink per cell, destination cells absorbing; the
        reference method of Foley & Black 2013, for regression and comparison only).
    solver: "auto" (topological substitution if the flow graph is acyclic, block-triangular
        sparse LU otherwise), "topological" (fails on cyclic graphs), "block" (block-triangular
        LU in strongly-connected-component order) or "lu" (SuperLU with COLAMD ordering on the
        whole matrix; slow on large 3D grids, kept as a reference).
    closed_loop_tol: a strongly connected set with no edge leaving it and no row whose exit
        share (sink or source flow / cell throughflow) exceeds this is a closed recirculation
        loop; its fractions are set to 0 and it is reported (result.closed_loops).
    remove_cycles: net mode only; delete the smallest edge of each flow cycle until the graph is
        acyclic, as the reference method does.
    """

    accounting: str = "gross"
    solver: str = "auto"
    remove_cycles: bool = False
    closed_loop_tol: float = 1e-12

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.accounting in ACCOUNTING_MODES, f"accounting must be one of {ACCOUNTING_MODES}"
        assert self.solver in SOLVERS, f"solver must be one of {SOLVERS}"
        assert not (self.remove_cycles and self.accounting != "net"), (
            "remove_cycles is only available in net mode"
        )
