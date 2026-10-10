"""Ensemble driver: trace one time step of many model realisations that share one grid.

Each realisation is a simulation folder (e.g. one per parameter realisation of a PEST++ IES
ensemble, run by a sweep). For every realisation the driver reads one time step, re-selects
the groups (a dict of select() arguments, or a top-level function step -> groups), runs the
backward or forward trace (and, with porosity, the Eulerian travel times of
gwsource.traveltime), and folds the requested per-cell outputs into running statistics, so only
one realisation's outputs are in memory at a time (plus the quantile store, below).

Every realisation must have the same connectivity: the IA/JA arrays of the binary grid file are
hashed and compared with the first realisation's (the flows, terms and saturation may differ).

Statistics per output, group and cell (NaN values, e.g. travel times where the fraction is 0,
are left out cell by cell; count is the number of realisations where the value is defined):
- min, max, mean;
- exceedance[t]: probability that the value exceeds t, i.e. count(value > t) / count; for
  fraction_through this is the capture probability P(F > t);
- quantiles[q]: numpy's default ("linear") quantile over the defined values.
  Exact: if the float32 stack of all values (realisations x cells x outputs x groups x 4 bytes)
  fits memory_budget, the stack is kept and the quantiles are exact (up to float32 rounding).
  Approximate: otherwise each output keeps a fixed-bin histogram per cell over
  histogram_range[output] (default (0, 1), right for fractions; set it for times or volumes).
  An order statistic is placed uniformly inside its bin and clamped to the cell's [min, max];
  the error of a quantile is at most one bin width, (high - low) / histogram_bins, for values
  inside the range (values outside are counted in the end bins). Memory: histogram_bins x
  cells x 4 bytes per output and group.

Parallel runs (max_workers > 1) trace realisations in a ProcessPoolExecutor; results come back
in realisation order and are folded in that order, so the statistics are identical to a serial
run. Each worker returns plain arrays (the trace results hold an unpicklable factorisation).
"""

import hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .config import TraceConfig
from .mf6io import open_model
from .trace import backward, forward
from .transient import DEFAULT_OUTPUT, MODES, GroupSpec, resolve_groups
from .traveltime import DEFAULT_FRACTION_THRESHOLD, travel_time

TRAVEL_TIME_OUTPUTS = ("mean_time", "weighted_time", "mean_time_to_exit_cell")


@dataclass
class EnsembleConfig:
    """Options of an ensemble run.

    mode: "backward" or "forward".
    outputs: per-cell outputs to summarise (default fraction_through / source_fraction); any
        per-cell output of the trace result, or a travel-time output if porosity is set.
    kstpkper: the 0-based time step to read from every realisation.
    thresholds: exceedance probabilities P(value > t) are computed for each t.
    quantiles: probabilities in [0, 1].
    memory_budget: bytes allowed for the exact-quantile float32 stack.
    histogram_bins, histogram_range: the approximate-quantile histogram ({output: (low, high)};
        outputs not listed use (0, 1)).
    porosity: scalar or per-cell; enables travel-time outputs.
    max_workers: 1 (default) runs serially; > 1 uses that many processes.
    model: GWF model name if a simulation has several.
    boundnames: load each realisation's boundnames from the package input (FloPy), so groups
        can be selected by boundname; off by default because it reads the model input files.
    """

    mode: str = "backward"
    outputs: tuple[str, ...] | None = None
    kstpkper: tuple[int, int] = (0, 0)
    thresholds: tuple[float, ...] = ()
    quantiles: tuple[float, ...] = (0.05, 0.5, 0.95)
    memory_budget: float = 2.0e9
    histogram_bins: int = 200
    histogram_range: dict[str, tuple[float, float]] | None = None
    porosity: float | np.ndarray | None = None
    fraction_threshold: float = DEFAULT_FRACTION_THRESHOLD
    max_workers: int = 1
    model: str | None = None
    boundnames: bool = False

    def __post_init__(self) -> None:
        """Validate option values."""
        assert self.mode in MODES, f"mode must be one of {MODES}"
        assert all(0.0 <= q <= 1.0 for q in self.quantiles), "quantiles must be in [0, 1]"
        assert self.histogram_bins >= 1 and self.max_workers >= 1, "bins and workers must be >= 1"

    def resolved_outputs(self) -> list[str]:
        """Return the outputs, with the mode default if none were given."""
        outputs = list(self.outputs or (DEFAULT_OUTPUT[self.mode],))
        needs_porosity = [o for o in outputs if o in TRAVEL_TIME_OUTPUTS]
        assert not needs_porosity or self.porosity is not None, (
            f"outputs {needs_porosity} need porosity"
        )
        return outputs

    def bin_range(self, output: str) -> tuple[float, float]:
        """Return the histogram range of an output."""
        low, high = (self.histogram_range or {}).get(output, (0.0, 1.0))
        assert high > low, f"histogram range of {output} must have high > low"
        return float(low), float(high)


@dataclass
class Realisation:
    """Outputs of one realisation: values[(output, group)] per cell, group scalars, grid hash."""

    ws: Path
    grid_hash: str
    values: dict[tuple[str, str], np.ndarray]
    group_inflow: dict[str, float]
    mean_transit_time: dict[str, float]


@dataclass
class Accumulator:
    """Running statistics of one output and group over realisations (arrays per cell)."""

    minimum: np.ndarray
    maximum: np.ndarray
    total: np.ndarray
    count: np.ndarray
    exceed: np.ndarray
    stack: np.ndarray | None = None
    hist: np.ndarray | None = None
    bin_range: tuple[float, float] = (0.0, 1.0)


@dataclass
class EnsembleResult:
    """Ensemble statistics: stats[name][output][group], exceedance[t][...], quantiles[q][...].

    stats names: min, max, mean, count. quantile_method is "exact" or "histogram" (bin_width
    is the histogram's bin width per output, the bound on the quantile error). group_inflow and
    mean_transit_time hold one value per realisation; group_inflow is the destination (backward)
    or source (forward) inflow, which in net accounting counts each passage once
    (gwsource.metrics).
    """

    config: EnsembleConfig
    realisations: list[Path]
    groups: list[str]
    outputs: list[str]
    stats: dict[str, dict[str, dict[str, np.ndarray]]]
    exceedance: dict[float, dict[str, dict[str, np.ndarray]]]
    quantiles: dict[float, dict[str, dict[str, np.ndarray]]]
    quantile_method: str
    group_inflow: dict[str, np.ndarray]
    mean_transit_time: dict[str, np.ndarray] = field(default_factory=dict)
    bin_width: dict[str, float] = field(default_factory=dict)


def list_realisations(root: str | Path, pattern: str = "*") -> list[Path]:
    """Return the sorted folders under root matching pattern that hold an mfsim.nam."""
    folders = sorted(p for p in Path(root).glob(pattern) if (p / "mfsim.nam").is_file())
    assert folders, f"no simulation folders matching {pattern!r} under {root}"
    return folders


def grid_hash(ia: np.ndarray, ja: np.ndarray) -> str:
    """Return a hash of the connectivity arrays."""
    digest = hashlib.sha256(np.asarray(ia, np.int64).tobytes())
    digest.update(np.asarray(ja, np.int64).tobytes())
    return digest.hexdigest()


def trace_realisation(
    ws: Path, groups: GroupSpec, config: EnsembleConfig, trace_config: TraceConfig
) -> Realisation:
    """Read, trace and reduce one realisation to the requested per-cell outputs."""
    reader = open_model(ws, config.model, boundnames=config.boundnames)
    step = reader.read(config.kstpkper)
    step_groups = resolve_groups(step, groups)
    trace = backward if config.mode == "backward" else forward
    result = trace(step, step_groups, trace_config)
    tt = None
    if config.porosity is not None:
        tt = travel_time(step, result, config.porosity, config.fraction_threshold)
    values = {}
    for output in config.resolved_outputs():
        source = tt if output in TRAVEL_TIME_OUTPUTS else result
        by_group = getattr(source, output, None)
        assert isinstance(by_group, dict), f"output {output!r} is not available"
        for group, array in by_group.items():
            values[(output, group)] = np.asarray(array, dtype=float)
    inflow = result.destination_inflow if config.mode == "backward" else result.source_inflow
    return Realisation(
        ws=Path(ws),
        grid_hash=grid_hash(step.ia, step.ja),
        values=values,
        group_inflow=dict(inflow),
        mean_transit_time={} if tt is None else dict(tt.mean_transit_time),
    )


def _run_one(args: tuple) -> Realisation:
    """Unpack arguments for trace_realisation (ProcessPoolExecutor.map passes one object)."""
    return trace_realisation(*args)


def iterate_realisations(
    workspaces: list[Path], groups: GroupSpec, config: EnsembleConfig, trace_config: TraceConfig
):
    """Yield the Realisation of each workspace in order, serially or with a process pool."""
    jobs = [(Path(ws), groups, config, trace_config) for ws in workspaces]
    if config.max_workers == 1:
        for job in jobs:
            yield _run_one(job)
        return
    batch = 2 * config.max_workers  # bound the number of finished results held in memory
    with ProcessPoolExecutor(max_workers=config.max_workers) as pool:
        for start in range(0, len(jobs), batch):
            yield from pool.map(_run_one, jobs[start : start + batch])


def new_accumulator(
    n_cells: int, n_real: int, n_thresholds: int, exact: bool, bins: int, bin_range: tuple
) -> Accumulator:
    """Return empty accumulators for one output and group."""
    return Accumulator(
        minimum=np.full(n_cells, np.inf),
        maximum=np.full(n_cells, -np.inf),
        total=np.zeros(n_cells),
        count=np.zeros(n_cells, dtype=np.int64),
        exceed=np.zeros((n_thresholds, n_cells), dtype=np.int64),
        stack=np.full((n_real, n_cells), np.nan, dtype=np.float32) if exact else None,
        hist=None if exact else np.zeros((bins, n_cells), dtype=np.uint32),
        bin_range=bin_range,
    )


def histogram_bin(values: np.ndarray, bin_range: tuple[float, float], bins: int) -> np.ndarray:
    """Return the histogram bin of each value (values outside the range go to the end bins)."""
    low, high = bin_range
    index = np.floor((values - low) / (high - low) * bins)
    return np.clip(np.nan_to_num(index), 0, bins - 1).astype(np.int64)


def fold(acc: Accumulator, values: np.ndarray, index: int, thresholds: tuple) -> None:
    """Fold one realisation's per-cell values (NaN = undefined) into the accumulators."""
    valid = np.isfinite(values)
    v = np.where(valid, values, 0.0)
    np.fmin(acc.minimum, np.where(valid, values, np.inf), out=acc.minimum)
    np.fmax(acc.maximum, np.where(valid, values, -np.inf), out=acc.maximum)
    acc.total += v
    acc.count += valid
    for i, t in enumerate(thresholds):
        acc.exceed[i] += valid & (v > t)
    if acc.stack is not None:
        acc.stack[index] = values
    else:
        cells = np.flatnonzero(valid)
        bins = acc.hist.shape[0]
        acc.hist[histogram_bin(values[cells], acc.bin_range, bins), cells] += 1


def exact_quantiles(stack: np.ndarray, probs: tuple, chunk: int = 100_000) -> np.ndarray:
    """Return (len(probs), cells) quantiles over the defined values of a (real, cells) stack."""
    out = np.full((len(probs), stack.shape[1]), np.nan)
    for start in range(0, stack.shape[1], chunk):
        block = stack[:, start : start + chunk].astype(float)
        defined = np.isfinite(block).any(axis=0)
        if defined.any():
            out[:, start : start + chunk][:, defined] = np.nanquantile(
                block[:, defined], probs, axis=0
            )
    return out


def _order_statistic(
    hist: np.ndarray, cum: np.ndarray, rank: np.ndarray, bin_range: tuple[float, float]
) -> np.ndarray:
    """Return the rank-th (0-based) smallest value per cell, placed uniformly inside its bin."""
    bins, n = hist.shape
    low, high = bin_range
    width = (high - low) / bins
    b = np.minimum((cum <= rank[None, :]).sum(axis=0), bins - 1)  # first bin with cum > rank
    cols = np.arange(n)
    before = np.where(b > 0, cum[np.maximum(b - 1, 0), cols], 0)
    in_bin = np.maximum(hist[b, cols], 1)
    return low + (b + (rank - before + 0.5) / in_bin) * width


def histogram_quantiles(acc: Accumulator, probs: tuple, chunk: int = 50_000) -> np.ndarray:
    """Return (len(probs), cells) approximate quantiles (numpy 'linear' rule) from histograms."""
    count = acc.count
    out = np.full((len(probs), count.size), np.nan)
    for start in range(0, count.size, chunk):
        cells = slice(start, start + chunk)
        hist, n = acc.hist[:, cells], count[cells]
        cum = np.cumsum(hist, axis=0, dtype=np.int64)
        lo, hi = acc.minimum[cells], acc.maximum[cells]
        for i, q in enumerate(probs):
            h = (np.maximum(n, 1) - 1) * q
            k0 = np.floor(h).astype(np.int64)
            k1 = np.minimum(k0 + 1, np.maximum(n - 1, 0))
            x0 = np.clip(_order_statistic(hist, cum, k0, acc.bin_range), lo, hi)
            x1 = np.clip(_order_statistic(hist, cum, k1, acc.bin_range), lo, hi)
            with np.errstate(invalid="ignore"):  # cells with no value have lo = inf, hi = -inf
                out[i, cells] = np.where(n > 0, x0 + (h - k0) * (x1 - x0), np.nan)
    return out


def finish(acc: Accumulator, thresholds: tuple, probs: tuple) -> dict:
    """Return the statistics of one output and group from its accumulators."""
    none = acc.count == 0
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(none, np.nan, acc.total / np.maximum(acc.count, 1))
        exceed = np.where(none, np.nan, acc.exceed / np.maximum(acc.count, 1))
    if acc.stack is not None:
        quant = exact_quantiles(acc.stack, probs)
    else:
        quant = histogram_quantiles(acc, probs)
    return {
        "min": np.where(none, np.nan, acc.minimum),
        "max": np.where(none, np.nan, acc.maximum),
        "mean": mean,
        "count": acc.count.copy(),
        "exceedance": {t: exceed[i] for i, t in enumerate(thresholds)},
        "quantiles": {q: quant[i] for i, q in enumerate(probs)},
    }


def stack_bytes(n_real: int, n_cells: int, n_series: int) -> int:
    """Return the size of the exact-quantile float32 stack in bytes."""
    return 4 * n_real * n_cells * n_series


def run_ensemble(
    workspaces: list[str | Path],
    groups: GroupSpec,
    config: EnsembleConfig | None = None,
    trace_config: TraceConfig | None = None,
) -> EnsembleResult:
    """Trace every realisation and return streaming statistics over the ensemble."""
    config = EnsembleConfig() if config is None else config
    trace_config = TraceConfig() if trace_config is None else trace_config
    workspaces = [Path(ws) for ws in workspaces]
    assert workspaces, "no realisations given"
    outputs = config.resolved_outputs()
    acc: dict[tuple[str, str], Accumulator] = {}
    inflow: dict[str, list[float]] = {}
    transit: dict[str, list[float]] = {}
    first_hash, exact = None, True
    for index, real in enumerate(iterate_realisations(workspaces, groups, config, trace_config)):
        if first_hash is None:
            first_hash = real.grid_hash
            n_cells = next(iter(real.values.values())).size
            exact = stack_bytes(len(workspaces), n_cells, len(real.values)) <= config.memory_budget
            for key in real.values:
                acc[key] = new_accumulator(
                    n_cells,
                    len(workspaces),
                    len(config.thresholds),
                    exact,
                    config.histogram_bins,
                    config.bin_range(key[0]),
                )
        assert real.grid_hash == first_hash, (
            f"{real.ws}: grid connectivity (IA/JA) differs from {workspaces[0]}"
        )
        assert real.values.keys() == acc.keys(), f"{real.ws}: groups or outputs differ"
        for key, values in real.values.items():
            fold(acc[key], values, index, config.thresholds)
        for group, value in real.group_inflow.items():
            inflow.setdefault(group, []).append(value)
        for group, value in real.mean_transit_time.items():
            transit.setdefault(group, []).append(value)
    return _collect(config, workspaces, outputs, acc, inflow, transit, exact)


def _collect(
    config: EnsembleConfig,
    workspaces: list[Path],
    outputs: list[str],
    acc: dict[tuple[str, str], Accumulator],
    inflow: dict[str, list[float]],
    transit: dict[str, list[float]],
    exact: bool,
) -> EnsembleResult:
    """Return the EnsembleResult from the finished accumulators."""
    stats: dict = {}
    exceedance: dict = {t: {} for t in config.thresholds}
    quantiles: dict = {q: {} for q in config.quantiles}
    for (output, group), running in acc.items():
        done = finish(running, config.thresholds, config.quantiles)
        for name in ("min", "max", "mean", "count"):
            stats.setdefault(name, {}).setdefault(output, {})[group] = done[name]
        for t, values in done["exceedance"].items():
            exceedance[t].setdefault(output, {})[group] = values
        for q, values in done["quantiles"].items():
            quantiles[q].setdefault(output, {})[group] = values
    widths = {}
    if not exact:
        widths = {
            o: (config.bin_range(o)[1] - config.bin_range(o)[0]) / config.histogram_bins
            for o in outputs
        }
    return EnsembleResult(
        config=config,
        realisations=workspaces,
        groups=list(inflow),
        outputs=outputs,
        stats=stats,
        exceedance=exceedance,
        quantiles=quantiles,
        quantile_method="exact" if exact else "histogram",
        group_inflow={g: np.asarray(v) for g, v in inflow.items()},
        mean_transit_time={g: np.asarray(v) for g, v in transit.items()},
        bin_width=widths,
    )
