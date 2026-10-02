"""Transient snapshots: trace selected time steps one by one and keep streaming statistics.

Each selected time step is treated as an independent steady state (PLAN §2.7, Phase 2): storage
release is a source term and storage gain a sink term, as the budget file reports them. The
grid and budget files are opened once (mf6io.StepReader) and every step is read, traced and
folded into running statistics before the next is read, so memory does not grow with the number
of steps (unless keep_series=True).

Groups are re-selected on every step, because the term list (and the bound number of a named
boundary) can change between stress periods. Pass either a dict {group: select() keyword
arguments}, e.g. {"wel": {"package": "WEL"}, "east": {"boundnames": ["well_east"]}}, or a
function step -> {group: Selection}.

Statistics per group and per requested output, cell by cell (TransientConfig):
- min, max: over the steps.
- mean: weighted mean. weighting="time" (default) weights each step by its length DELT, so the
  mean is the time average over the analysed steps; weighting="equal" gives every step weight 1.
- asn: always / sometimes / never above the threshold: 1 if value > threshold in every step,
  0 if in none, 0.5 otherwise (on test_output).
- probability_in_range: weighted share of steps with low <= value <= high (on test_output),
  with the same weights as the mean.
- exceedance_count: number of steps with value > threshold (on test_output; not weighted).
NaN values (e.g. fraction_from_cell_input where a cell has no inflow term in a step) are left
out cell by cell: means and probabilities are then over the steps where the value is defined,
and a cell defined in no step gets NaN.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from .config import TraceConfig
from .flowstep import FlowStep
from .mf6io import StepReader
from .selectors import Selection, select
from .trace import backward, forward

MODES = ("backward", "forward")
WEIGHTINGS = ("time", "equal")
DEFAULT_OUTPUT = {"backward": "fraction_through", "forward": "source_fraction"}
VALUE_STATS = ("min", "max", "mean")
TEST_STATS = ("asn", "probability_in_range", "exceedance_count")

GroupSpec = dict[str, dict] | Callable[[FlowStep], dict[str, Selection]]


@dataclass
class TransientConfig:
    """Options of a transient (snapshot) run.

    steps: "all", a list of 0-based stress periods (every saved step in them), or a list of
        0-based (kstp, kper) pairs.
    outputs: per-group outputs to summarise (default fraction_through backward, source_fraction
        forward). Any per-cell output of BackwardResult/ForwardResult can be named.
    weighting: "time" (default; weights = step length) or "equal" (weight 1 per step), used by
        the mean and probability_in_range.
    threshold: threshold of asn and exceedance_count (value > threshold counts), or None.
    value_range: (low, high) of probability_in_range (inclusive), or None.
    test_output: output the threshold and range apply to (default: the first of outputs).
    keep_series: also keep every step's outputs in memory (for export with a time dimension).
    """

    steps: str | list = "all"
    outputs: tuple[str, ...] | None = None
    weighting: str = "time"
    threshold: float | None = None
    value_range: tuple[float, float] | None = None
    test_output: str | None = None
    keep_series: bool = False

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.weighting in WEIGHTINGS, f"weighting must be one of {WEIGHTINGS}"
        is_list = isinstance(self.steps, (list, tuple))
        assert is_list or self.steps == "all", "steps must be 'all' or a list"
        if self.value_range is not None:
            assert len(self.value_range) == 2 and self.value_range[0] <= self.value_range[1], (
                "value_range must be (low, high) with low <= high"
            )


@dataclass
class RunningStats:
    """Streaming accumulators of one output of one group (all arrays per cell)."""

    minimum: np.ndarray
    maximum: np.ndarray
    weighted_sum: np.ndarray
    weight_total: np.ndarray
    n_valid: np.ndarray
    n_exceed: np.ndarray
    weight_in_range: np.ndarray


@dataclass
class TransientResult:
    """Statistics over time steps: stats[statistic][output][group] -> per-cell array.

    steps, totim and weights describe the analysed steps in order; group_inflow[group] holds,
    per step, the group's destination inflow (backward) or source inflow (forward). series
    (keep_series=True) holds series[output][group] -> (n_steps, n_cells).
    """

    mode: str
    config: TransientConfig
    trace_config: TraceConfig
    groups: list[str]
    outputs: list[str]
    test_output: str
    steps: list[tuple[int, int]]
    totim: np.ndarray
    weights: np.ndarray
    stats: dict[str, dict[str, dict[str, np.ndarray]]]
    group_inflow: dict[str, np.ndarray]
    solver_used: list[str]
    n_cycles: np.ndarray
    n_closed_loops: np.ndarray
    template: FlowStep
    series: dict[str, dict[str, np.ndarray]] | None = None
    notes: dict = field(default_factory=dict)


def select_steps(available: list[tuple[int, int]], steps: str | list) -> list[tuple[int, int]]:
    """Return the saved (kstp, kper) to analyse: all, those in listed periods, or listed pairs."""
    if isinstance(steps, str):
        return list(available)
    steps = list(steps)
    assert steps, "no time steps selected"
    if all(isinstance(s, (int, np.integer)) for s in steps):
        periods = {int(s) for s in steps}
        chosen = [ks for ks in available if ks[1] in periods]
        assert chosen, f"no saved time steps in stress periods {sorted(periods)}"
        return chosen
    chosen = [tuple(int(v) for v in s) for s in steps]
    missing = [ks for ks in chosen if ks not in set(available)]
    assert not missing, f"time steps {missing} are not in the budget file"
    return chosen


def resolve_groups(step: FlowStep, spec: GroupSpec) -> dict[str, Selection]:
    """Return the groups of one step from a dict of select() arguments or a function."""
    if callable(spec):
        return spec(step)
    assert isinstance(spec, dict) and spec, (
        "groups must be a dict {name: select kwargs} or a function"
    )
    return {name: select(step, **kwargs) for name, kwargs in spec.items()}


def new_stats(n: int) -> RunningStats:
    """Return empty accumulators for n cells."""
    return RunningStats(
        minimum=np.full(n, np.inf),
        maximum=np.full(n, -np.inf),
        weighted_sum=np.zeros(n),
        weight_total=np.zeros(n),
        n_valid=np.zeros(n, dtype=np.int64),
        n_exceed=np.zeros(n, dtype=np.int64),
        weight_in_range=np.zeros(n),
    )


def update_stats(
    stats: RunningStats,
    values: np.ndarray,
    weight: float,
    threshold: float | None,
    value_range: tuple[float, float] | None,
) -> None:
    """Fold one step's per-cell values (NaN = undefined) into the accumulators."""
    valid = np.isfinite(values)
    v = np.where(valid, values, 0.0)
    np.fmin(stats.minimum, np.where(valid, values, np.inf), out=stats.minimum)
    np.fmax(stats.maximum, np.where(valid, values, -np.inf), out=stats.maximum)
    stats.weighted_sum += weight * v
    stats.weight_total += weight * valid
    stats.n_valid += valid
    if threshold is not None:
        stats.n_exceed += valid & (v > threshold)
    if value_range is not None:
        inside = valid & (v >= value_range[0]) & (v <= value_range[1])
        stats.weight_in_range += weight * inside


def _divide(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """Return num / den, NaN where den is 0."""
    return np.divide(num, den, out=np.full(num.shape, np.nan), where=den > 0)


def finish_stats(
    stats: RunningStats, threshold: float | None, value_range: tuple[float, float] | None
) -> dict[str, np.ndarray]:
    """Return the statistics of one output and group from its accumulators."""
    none = stats.n_valid == 0
    out = {
        "min": np.where(none, np.nan, stats.minimum),
        "max": np.where(none, np.nan, stats.maximum),
        "mean": _divide(stats.weighted_sum, stats.weight_total),
    }
    if threshold is not None:
        asn = np.where(stats.n_exceed == stats.n_valid, 1.0, 0.5)
        asn[stats.n_exceed == 0] = 0.0
        out["asn"] = np.where(none, np.nan, asn)
        out["exceedance_count"] = stats.n_exceed.copy()
    if value_range is not None:
        out["probability_in_range"] = _divide(stats.weight_in_range, stats.weight_total)
    return out


def step_weight(reader: StepReader, kstpkper: tuple[int, int], weighting: str) -> float:
    """Return a step's weight: its length DELT (time weighting) or 1 (equal weighting)."""
    return reader.step_length(kstpkper) if weighting == "time" else 1.0


def _output_values(result, output: str) -> dict[str, np.ndarray]:
    """Return {group: per-cell values} of one output of a trace result."""
    values = getattr(result, output, None)
    assert isinstance(values, dict), (
        f"output {output!r} is not available (unknown name, or flux outputs without cell areas)"
    )
    return values


def _inflow(result, mode: str) -> dict[str, float]:
    """Return each group's destination (backward) or source (forward) inflow."""
    return result.destination_inflow if mode == "backward" else result.source_inflow


def _resolve_outputs(config: TransientConfig, mode: str) -> tuple[list[str], str]:
    """Return (outputs, test output) with mode defaults filled in."""
    outputs = list(config.outputs or (DEFAULT_OUTPUT[mode],))
    test_output = config.test_output or outputs[0]
    if test_output not in outputs:
        outputs.append(test_output)
    return outputs, test_output


@dataclass
class StepLog:
    """Per-step records of a transient run, in step order."""

    weights: list[float] = field(default_factory=list)
    totim: list[float] = field(default_factory=list)
    solvers: list[str] = field(default_factory=list)
    n_cycles: list[int] = field(default_factory=list)
    n_closed: list[int] = field(default_factory=list)
    inflow: dict[str, list[float]] = field(default_factory=dict)


def _log_step(log: StepLog, step: FlowStep, result, mode: str, weight: float) -> None:
    """Append one step's weight, time, solver, cycle counts and group inflows to the log."""
    log.weights.append(weight)
    log.totim.append(step.totim if step.totim is not None else np.nan)
    log.solvers.extend(result.solver_used)
    log.n_cycles.append(len(result.cycles))
    log.n_closed.append(len(result.closed_loops))
    for group, value in _inflow(result, mode).items():
        log.inflow.setdefault(group, []).append(value)


def _fold_outputs(
    acc: dict[str, dict[str, RunningStats]],
    result,
    outputs: list[str],
    test_output: str,
    config: TransientConfig,
    weight: float,
) -> None:
    """Fold one step's outputs of every group into the running statistics."""
    for output in outputs:
        is_test = output == test_output
        threshold = config.threshold if is_test else None
        value_range = config.value_range if is_test else None
        for group, values in _output_values(result, output).items():
            stats = acc.setdefault(output, {}).setdefault(group, new_stats(values.size))
            update_stats(stats, values, weight, threshold, value_range)


def _store_series(series: dict, result, outputs: list[str], index: int, n_steps: int) -> None:
    """Copy one step's outputs into the kept series (output -> group -> (steps, cells))."""
    for output in outputs:
        for group, values in _output_values(result, output).items():
            stack = series.setdefault(output, {}).setdefault(
                group, np.empty((n_steps, values.size))
            )
            stack[index] = values


def trace_transient(
    reader: StepReader,
    groups: GroupSpec,
    mode: str = "backward",
    config: TransientConfig | None = None,
    trace_config: TraceConfig | None = None,
) -> TransientResult:
    """Trace every selected time step and return streaming statistics over the steps."""
    assert mode in MODES, f"mode must be one of {MODES}"
    config = TransientConfig() if config is None else config
    trace_config = TraceConfig() if trace_config is None else trace_config
    outputs, test_output = _resolve_outputs(config, mode)
    steps = select_steps(reader.steps, config.steps)
    trace = backward if mode == "backward" else forward
    acc: dict[str, dict[str, RunningStats]] = {}
    series = {} if config.keep_series else None
    log, names = StepLog(), None
    for index, kstpkper in enumerate(steps):
        step = reader.read(kstpkper)
        step_groups = resolve_groups(step, groups)
        names = list(step_groups) if names is None else names
        assert list(step_groups) == names, f"group names changed at step {kstpkper}"
        result = trace(step, step_groups, trace_config)
        weight = step_weight(reader, kstpkper, config.weighting)
        _fold_outputs(acc, result, outputs, test_output, config, weight)
        if series is not None:
            _store_series(series, result, outputs, index, len(steps))
        _log_step(log, step, result, mode, weight)
    return TransientResult(
        mode=mode,
        config=config,
        trace_config=trace_config,
        groups=names,
        outputs=outputs,
        test_output=test_output,
        steps=steps,
        totim=np.asarray(log.totim),
        weights=np.asarray(log.weights),
        stats=_collect_stats(acc, test_output, config),
        group_inflow={g: np.asarray(v) for g, v in log.inflow.items()},
        solver_used=log.solvers,
        n_cycles=np.asarray(log.n_cycles),
        n_closed_loops=np.asarray(log.n_closed),
        template=step,
        series=series,
        notes=dict(reader.notes or {}),
    )


def _collect_stats(
    acc: dict[str, dict[str, RunningStats]], test_output: str, config: TransientConfig
) -> dict[str, dict[str, dict[str, np.ndarray]]]:
    """Return stats[statistic][output][group] from the accumulators."""
    stats: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    for output, by_group in acc.items():
        is_test = output == test_output
        for group, running in by_group.items():
            finished = finish_stats(
                running,
                config.threshold if is_test else None,
                config.value_range if is_test else None,
            )
            for name, values in finished.items():
                stats.setdefault(name, {}).setdefault(output, {})[group] = values
    return stats
