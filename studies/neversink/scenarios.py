"""Neversink case study: WEL parameters of the published pumping scenarios.

The MODPATH Monte Carlo runs (scripts/modpath_mc_varq.py) read one parameter ensemble per
pumping scenario, parens{qrat}.csv, for qrat in baserat, 0.25rat, 0.5rat, 0.75rat, maxrat and
maxrange. Nothing in the source repository builds those files, so the rule below was inferred
from the published per-realisation masks (output/modpath_mc/{qrat}.zip, 357 masks each) and the
pumping table processed_data/2009-2016_ave_pumping.csv (flux_m3: 2009-2016 average, equal to the
rates in neversink_mf6/wel_000.dat; max_flux_m3: permitted maximum).

Inferred rule, for the eight priority wells only (q_base from wel_000.dat, q_max = max_flux_m3):

    q = m * (q_base + f * (q_max - q_base)),  f = 0, 0.25, 0.5, 0.75, 1 for baserat ... maxrat
    maxrange: f ~ U(0, 1) drawn independently for every priority well and realisation

with m the realisation's own WEL multiplier of the well's cell, written as the WEL multiplier
q / q_base. The non-priority wells keep their realisation multipliers. baserat is the ensemble
itself. supplementary_tables/tables.xlsx (Table 1, note 2) states that maximum rates were
"simulated only at priority wells".

How the rule was inferred. Mask cells were counted per MODPATH region (NE: the four U wells; W:
SV_193, SV_227, SV_407; S: SV_487) and divided by the same realisation's baserat count. Mask k
is the same run in every scenario, so the ratio needs no pairing with the rebuilt realisations.
The median area ratio of each scenario was set against the pumping ratio of three candidate
rules (f * q_max, q_base + f (q_max - q_base) and q_base (q_max / q_base)^f), with a fit of
area ~ Q^b per region. The linear rule above is the one that fits all three regions.

maxrange. Inverting each realisation's own area curve (baserat ... maxrat, piecewise linear)
gives f per region. Its spread per region and the correlation between regions were compared
with independent U(0, 1) draws per well, a log-uniform draw, and one draw shared by all wells
or by a cluster; independent uniform draws per well match. The seed and generator of the
published draws are unknown, so maxrange can be reproduced only in distribution:
maxrange_fractions draws f from np.random.default_rng((seed, real_index)), and an f per well can
be passed instead.

Multiplier. The mask areas alone do not show whether the realisation's own multiplier m was
kept. Paired with their realisations, the masks do: mc_masks.run_multiplier_test reruns
realisations with m kept and dropped, and mc_masks.multiplier_table compares each with its
published mask. Default here: kept (keep_multiplier=True).

Run with the project environment to print the priority-well rates of the base realisation in
every scenario:

    python studies/neversink/scenarios.py
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
    keep_multiplier: bool = True,
) -> pd.Series:
    """Return the realisation's parameters with the scenario's priority-well WEL multipliers.

    real_index is the realisation's row in modpath_par_ens.csv (its run index, not its mask
    index); it only seeds the maxrange draw. fractions gives f per well (order of wells) instead
    of the fixed or drawn values. keep_multiplier=True (as published) multiplies the
    realisation's own multiplier in; False replaces it. baserat returns the parameters unchanged
    unless fractions is given.
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
