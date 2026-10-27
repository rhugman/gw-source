"""Configuration of a trace: accounting mode, solver choice, strong sinks and cycle handling."""

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
    strong_sinks: backward traces only; package selectors (names, budget texts or types, any
        case, as select(package=)) whose sink cells are absorbing, or "all" for every cell with
        a sink term. A strong-sink cell passes no water on to its neighbours, as a cell that
        stops particles (MODPATH 7 weak sink option "stop"). Gross: its F is its destination
        share of its sink outflow, d_i / Snk_i, so water in a cell with sinks of several groups
        is split by their flows. Net: destination cells stay fixed at 1 and the other
        strong-sink cells absorb with f = 0. Default () keeps every cell mixing.
        Any outflowing sink term (q < 0), however small, makes its cell absorbing, as the
        MODPATH 7 stop option does. A package's *-TO-MVR record matches the package and is
        one of its sink terms: MF6 splits a provider's outflow between the package record and
        its -TO-MVR record, so Snk counts that outflow once, as their sum. trace_transient and
        the ensembles pass this config to every step or realisation, so strong sinks apply to
        each steady backward snapshot.
    """

    accounting: str = "gross"
    solver: str = "auto"
    remove_cycles: bool = False
    closed_loop_tol: float = 1e-12
    strong_sinks: str | tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.accounting in ACCOUNTING_MODES, f"accounting must be one of {ACCOUNTING_MODES}"
        assert self.solver in SOLVERS, f"solver must be one of {SOLVERS}"
        assert not (self.remove_cycles and self.accounting != "net"), (
            "remove_cycles is only available in net mode"
        )
        if self.strong_sinks != "all":
            assert not isinstance(self.strong_sinks, str), (
                'strong_sinks must be "all" or a collection of package names, e.g. ("WEL",)'
            )
            self.strong_sinks = tuple(self.strong_sinks)
