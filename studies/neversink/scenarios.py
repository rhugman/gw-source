"""Neversink case study, stage 3 prerequisite: WEL parameters of the published pumping scenarios.

The MODPATH Monte Carlo runs (scripts/modpath_mc_varq.py) read one parameter ensemble per
pumping scenario, parens{qrat}.csv, for qrat in baserat, 0.25rat, 0.5rat, 0.75rat, maxrat and
maxrange. Nothing in the source repository builds those files, so the rule below was inferred
from the published per-realisation masks (output/modpath_mc/{qrat}.zip, 357 masks each) and the
pumping table processed_data/2009-2016_ave_pumping.csv (flux_m3: 2009-2016 average, equal to the
rates in neversink_mf6/wel_000.dat; max_flux_m3: permitted maximum).

Inferred rule, for the eight priority wells only (q_base from wel_000.dat, q_max = max_flux_m3):

    q = q_base + f * (q_max - q_base),  f = 0, 0.25, 0.5, 0.75, 1 for baserat ... maxrat
    maxrange: f ~ U(0, 1) drawn independently for every priority well and realisation

written as the WEL multiplier q / q_base of the well's cell. The non-priority wells keep their
realisation multipliers. baserat is the ensemble itself.

Evidence. Mask cells were counted per MODPATH region (NE: the four U wells; W: SV_193, SV_227,
SV_407; S: SV_487) and divided by the same realisation's baserat count. The table gives the
median area ratio over the 357 realisations against the pumping ratio of each hypothesis, with
the fit of area ~ Q^b and its rms log residual:

    region  scenario  area   f*max  base+f(max-base)  base*(max/base)^f
    NE      0.25rat   1.72   0.82   1.57              1.34
            0.5rat    2.34   1.65   2.15              1.80
            0.75rat   2.76   2.47   2.72              2.43
            maxrat    3.28   3.29   3.29              3.29
            rms              0.41   0.05              0.16
    W       0.25rat   2.21   1.67   2.42              1.61
            0.5rat    3.18   3.34   3.84              2.59
            0.75rat   4.07   5.01   5.26              4.16
            maxrat    4.81   6.69   6.69              6.69
            rms              0.18   0.03              0.25
    S       0.25rat   1.50   1.00   1.75              1.41
            0.5rat    2.09   2.00   2.50              2.00
            0.75rat   2.69   3.00   3.25              2.83
            maxrat    3.19   4.00   4.00              4.00
            rms              0.21   0.03              0.09

- f * max is ruled out: it lowers the U-cluster pumping to 0.82 of base in 0.25rat, where the
  published U area grows by a factor of 1.7 in every realisation.
- base + f(max - base) fits all three regions (rms 0.03 to 0.05, b = 0.82 to 1.04). Between
  baserat and maxrat, the normalised area (A - A_base) / (A_max - A_base) is 0.30, 0.57 and 0.78
  for f = 0.25, 0.5 and 0.75 (all wells together): a concave area-rate relation on rates linear
  in f.
- Areas increase strictly from baserat to maxrat in every realisation and region.
- supplementary_tables/tables.xlsx (Table 1, note 2): maximum rates were "simulated only at
  priority wells". The masks cannot test this further (they only count priority-well cells).

maxrange. Inverting each realisation's own area curve (baserat ... maxrat, piecewise linear)
gives f per region. It is never below 0 (no realisation below its baserat area), its spread
matches independent U(0, 1) draws per well, and the regions are uncorrelated (r = 0.03 to 0.15):

    region  wells  std of f  std expected (independent U(0, 1) per well, rate-weighted)
    S       1      0.30      0.29
    NE      4      0.16      0.16
    W       3      0.17      0.18

For S (one well) f is close to uniform on (0, 1), median 0.53; a log-uniform draw between base
and max would give a median of 0.33. A draw common to all wells, or one per cluster, would give
0.29 in every region and correlated regions. The seed and generator of the published draws are
unknown, so maxrange can be reproduced only in distribution: maxrange_fractions draws f from
np.random.default_rng((seed, real_index)), and an f per well can be passed instead.

Uncertain:
- Whether the realisation's own WEL multiplier m (0.93 to 1.08 for the priority wells) was kept
  (q = m * (...)) or replaced. The masks do not resolve it: the area does not correlate with m
  even in baserat. Default here: replaced (keep_multiplier=False).
- In 23 realisations the S maxrange area exceeds the maxrat area by up to 8 % (estimated f up to
  1.11), unrelated to m. This may be noise of the cell count, or a draw bound slightly above max.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import pest_rebuild as pr

HERE = Path(__file__).resolve().parent
PUMPING_CSV = HERE / "external" / "neversink_workflow" / "processed_data" / "2009-2016_ave_pumping.csv"
WEL_FILE = pr.BASE_MODEL / "wel_000.dat"

QRAT_FRACTION = {"baserat": 0.0, "0.25rat": 0.25, "0.5rat": 0.5, "0.75rat": 0.75, "maxrat": 1.0}
QRATS = (*QRAT_FRACTION, "maxrange")
MAXRANGE_SEED = 20210525  # arbitrary: the published seed is unknown


def priority_well_table(pumping_csv: Path = PUMPING_CSV, wel_file: Path = WEL_FILE) -> pd.DataFrame:
    """Return per priority well its WEL parameter name, base and maximum rate (negative, m3/d)."""
    pump = pd.read_csv(pumping_csv)
    pump = pump.loc[pump["WellType"] == "Priority"].set_index("ID_Well")
    wel = pd.read_csv(wel_file, sep=r"\s+", comment=None)
    wel.columns = ["k", "i", "j", "q", "boundname"]
    wel = wel.set_index("boundname").loc[pump.index]
    assert wel.index.is_unique, "a priority well appears twice in the WEL file"
    cells = list(zip(wel["k"], wel["i"], wel["j"]))
    assert len(set(cells)) == len(cells), "two priority wells share a cell (and a multiplier)"
    table = pd.DataFrame(
        {
            "parnme": [f"wel__:0_usecol:3_idx0:{k - 1}_idx1:{i - 1}_idx2:{j - 1}" for k, i, j in cells],
            "q_base": wel["q"].to_numpy(float),
            "q_max": pump["max_flux_m3"].to_numpy(float),
        },
        index=wel.index,
    )
    assert np.allclose(table["q_base"], pump["flux_m3"], rtol=1e-4), "wel_000.dat differs from flux_m3"
    assert (table["q_max"] < table["q_base"]).all() and (table["q_base"] < 0).all(), "rates not pumping"
    return table


def maxrange_fractions(real_index: int, n_wells: int, seed: int = MAXRANGE_SEED) -> np.ndarray:
    """Return one f ~ U(0, 1) per priority well for a maxrange realisation (reproducible)."""
    return np.random.default_rng((seed, real_index)).uniform(0.0, 1.0, n_wells)


def scenario_fractions(
    qrat: str, real_index: int, n_wells: int, seed: int = MAXRANGE_SEED, fractions: np.ndarray | None = None
) -> np.ndarray:
    """Return f per priority well: fixed for the qrat scenarios, drawn (or given) for maxrange."""
    assert qrat in QRATS, f"unknown scenario {qrat}"
    if fractions is not None:
        f = np.asarray(fractions, dtype=float)
    elif qrat == "maxrange":
        f = maxrange_fractions(real_index, n_wells, seed)
    else:
        f = np.full(n_wells, QRAT_FRACTION[qrat])
    assert f.shape == (n_wells,) and np.all((f >= 0.0) & (f <= 1.0)), "f must be in [0, 1] per well"
    return f


def scenario_pars(
    pars: pd.Series,
    qrat: str,
    real_index: int,
    wells: pd.DataFrame | None = None,
    seed: int = MAXRANGE_SEED,
    fractions: np.ndarray | None = None,
    keep_multiplier: bool = False,
) -> pd.Series:
    """Return the realisation's parameters with the scenario's priority-well WEL multipliers.

    real_index is the position in modpath_par_ens.csv (= the published mask index); it only
    seeds the maxrange draw. fractions gives f per well (order of wells) instead of the fixed
    or drawn values. keep_multiplier=True multiplies the realisation's own multiplier in rather
    than replacing it. baserat returns the parameters unchanged unless fractions is given.
    """
    if wells is None:
        wells = priority_well_table()
    out = pars.copy()
    if qrat == "baserat" and fractions is None:
        return out
    f = scenario_fractions(qrat, real_index, len(wells), seed, fractions)
    mult = 1.0 + f * (wells["q_max"].to_numpy() / wells["q_base"].to_numpy() - 1.0)
    names = wells["parnme"].to_numpy()
    assert set(names) <= set(out.index), "priority-well WEL parameters missing from pars"
    current = out.loc[names].to_numpy(dtype=float)
    out.loc[names] = mult * current if keep_multiplier else mult
    return out


def scenario_rates(pars: pd.Series, wells: pd.DataFrame | None = None) -> pd.Series:
    """Return the priority-well rates (m3/d, positive) that pars give."""
    if wells is None:
        wells = priority_well_table()
    return -wells["q_base"] * pars.loc[wells["parnme"]].to_numpy(dtype=float)


if __name__ == "__main__":
    wells = priority_well_table()
    pars = pr.realisation_pars("base")
    table = {q: scenario_rates(scenario_pars(pars, q, 357, wells), wells) for q in QRATS}
    print(pd.DataFrame(table).round(1))
