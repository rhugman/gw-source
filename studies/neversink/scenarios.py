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

write_rule_evidence recomputes this evidence from the published masks (moved back onto their
cells, ensemble_run.read_mask) and writes it to studies/neversink/output/scenario_rule/:
- region_areas.csv: mask cells per mask, scenario and region;
- hypothesis_ratios.csv, hypothesis_fits.csv: median area ratios against the pumping ratio of
  each candidate rule, and the fit area ~ Q^b with its rms log residual;
- growth_checks.csv: masks whose area grows strictly with f, and the median normalised area;
- maxrange_f.csv, maxrange_spread.csv, maxrange_correlations.csv, maxrange_excess.csv: the
  estimated maxrange f per mask, its spread against the candidate draws, its correlation
  between regions, and the masks whose maxrange area exceeds their maxrat area;
- region_multipliers.csv, multiplier_correlations.csv: each region's multiplier m per mask
  (masks paired with their realisations) and its correlation with the areas;
- mask_shift.csv: the median area ratios from the corrected masks against those from the masks
  as stored (no row shift, counted on the same start cells), their difference per region and
  scenario, and the largest absolute difference (row region = "all"). It checks that the
  inferred rule does not depend on the row correction.
The overlap of the reproduced masks with the published ones is in the mc_masks output
(pairing_check.csv, multiplier_test.csv).

Run with the project environment, after pest_rebuild.py, to print the priority-well rates of
the base realisation in every scenario and write the evidence:

    python studies/neversink/scenarios.py
"""

import sys
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMPORT_DIRS = (HERE, REPO / "studies" / "paper", REPO / "tutorials", REPO / "src")
sys.path[:0] = [str(d) for d in IMPORT_DIRS]  # no PYTHONPATH needed, on any OS

import pest_rebuild as pr  # noqa: E402

PUMPING_CSV = HERE / "external" / "neversink_workflow" / "processed_data" / "2009-2016_ave_pumping.csv"
WEL_FILE = pr.BASE_MODEL / "wel_000.dat"

QRAT_FRACTION = {"baserat": 0.0, "0.25rat": 0.25, "0.5rat": 0.5, "0.75rat": 0.75, "maxrat": 1.0}
QRATS = (*QRAT_FRACTION, "maxrange")
MAXRANGE_SEED = 20210525  # arbitrary: the published seed is unknown
# Published MODPATH release regions and the priority wells whose masks fall in each
REGION_WELLS = {
    "NE": ("U_917", "U__55", "U___7", "U___8"),
    "W": ("SV_193", "SV_227", "SV_407"),
    "S": ("SV_487",),
}
# Candidate rules: q = f q_max; q_base + f (q_max - q_base); q_base (q_max / q_base)^f
HYPOTHESES = ("f_max", "linear", "geometric")
EVIDENCE_DIR = HERE / "output" / "scenario_rule"


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


# ---------------------------------------------------------------- evidence for the inferred rule


def region_areas(
    read_mask, starts: pd.DataFrame, qrats: tuple[str, ...] = QRATS, n_masks: int = pr.N_MASKS
) -> pd.DataFrame:
    """Return the published mask cells per mask, scenario and release region (long table).

    read_mask(index, qrat) returns a mask moved back onto its cells (ensemble_run.read_mask);
    starts holds the published start cells (node0) and their region.
    """
    regions = starts["region"].to_numpy()
    nodes = starts["node0"].to_numpy()
    rows = []
    for qrat in qrats:
        for k in range(n_masks):
            mask = read_mask(k, qrat)
            on_starts = mask.ravel()[nodes % mask.size]
            for name in REGION_WELLS:
                cells = int(on_starts[regions == name].sum())
                rows.append({"mask_index": k, "qrat": qrat, "region": name, "cells": cells})
    return pd.DataFrame(rows)


def area_matrix(areas: pd.DataFrame, region: str, qrats: tuple[str, ...]) -> np.ndarray:
    """Return a region's mask cells as (n_masks, len(qrats)), masks in index order."""
    sub = areas[areas["region"] == region]
    table = sub.pivot(index="mask_index", columns="qrat", values="cells").sort_index()
    return table[list(qrats)].to_numpy(dtype=float)


def pumping_ratio(wells: pd.DataFrame, f: float, hypothesis: str) -> float:
    """Return the pumping of wells under a candidate rule at fraction f, relative to base."""
    q_base, q_max = wells["q_base"].abs().to_numpy(), wells["q_max"].abs().to_numpy()
    q = {
        "f_max": f * q_max,
        "linear": q_base + f * (q_max - q_base),
        "geometric": q_base * (q_max / q_base) ** f,
    }[hypothesis]
    return float(q.sum() / q_base.sum())


def hypothesis_table(areas: pd.DataFrame, wells: pd.DataFrame) -> pd.DataFrame:
    """Return per region and fixed scenario the median area ratio and each rule's pumping ratio.

    The area ratio is a mask's area over the baserat area of the same mask (mask k is the same
    run in every scenario).
    """
    fixed = tuple(QRAT_FRACTION)
    rows = []
    for region, names in REGION_WELLS.items():
        a = area_matrix(areas, region, fixed)
        ratio = a / a[:, :1]
        for i, qrat in enumerate(fixed[1:], start=1):
            median = float(np.median(ratio[:, i]))
            row = {"region": region, "qrat": qrat, "area_ratio_median": median}
            for h in HYPOTHESES:
                f = QRAT_FRACTION[qrat]
                row[f"pumping_ratio_{h}"] = pumping_ratio(wells.loc[list(names)], f, h)
            rows.append(row)
    return pd.DataFrame(rows)


def hypothesis_fits(table: pd.DataFrame) -> pd.DataFrame:
    """Return per region and rule the fit area ratio = pumping ratio^b and its rms log residual.

    The fit is least squares on the logs through (1, 1). A rule with a pumping ratio of 0 in some
    scenario gets NaN (no log).
    """
    rows = []
    for region, g in table.groupby("region", sort=False):
        y = np.log(g["area_ratio_median"].to_numpy())
        for h in HYPOTHESES:
            q = g[f"pumping_ratio_{h}"].to_numpy()
            row = {"region": region, "hypothesis": h, "min_pumping_ratio": float(q.min())}
            if np.all(q > 0.0):
                x = np.log(q)
                b = float(x @ y / (x @ x))
                row.update(b=b, rms_log=float(np.sqrt(np.mean((y - b * x) ** 2))))
            else:
                row.update(b=np.nan, rms_log=np.nan)
            rows.append(row)
    return pd.DataFrame(rows)


def mask_shift_sensitivity(
    corrected: pd.DataFrame, as_stored: pd.DataFrame, wells: pd.DataFrame
) -> pd.DataFrame:
    """Return per region and scenario the median area ratio from corrected and as-stored areas.

    corrected and as_stored are region_areas tables; the last row (region "all") holds the
    largest absolute difference.
    """
    keys = ["region", "qrat"]
    a = hypothesis_table(corrected, wells)[[*keys, "area_ratio_median"]]
    b = hypothesis_table(as_stored, wells)[[*keys, "area_ratio_median"]]
    table = a.merge(b, on=keys, suffixes=("_corrected", "_as_stored"))
    diff = table["area_ratio_median_as_stored"] - table["area_ratio_median_corrected"]
    table["difference"] = diff
    summary = {"region": "all", "qrat": "all", "difference": table["difference"].abs().max()}
    return pd.concat([table, pd.DataFrame([summary])], ignore_index=True)


def growth_checks(areas: pd.DataFrame) -> pd.DataFrame:
    """Return per region the masks whose area grows strictly from baserat to maxrat.

    Also the median normalised area (A - A_base) / (A_max - A_base) of the intermediate
    scenarios; region "all" sums the three regions.
    """
    fixed = tuple(QRAT_FRACTION)
    curves = {r: area_matrix(areas, r, fixed) for r in REGION_WELLS}
    curves["all"] = sum(curves.values())
    rows = []
    for region, a in curves.items():
        increasing = np.all(np.diff(a, axis=1) > 0, axis=1)
        row = {"region": region, "masks": len(a), "strictly_increasing": int(increasing.sum())}
        span = a[:, -1] - a[:, 0]
        for i, qrat in enumerate(fixed[1:-1], start=1):
            row[f"normalised_{qrat}"] = float(np.median((a[:, i] - a[:, 0]) / span))
        rows.append(row)
    return pd.DataFrame(rows)


def invert_area_curve(curve: np.ndarray, area: float, f: np.ndarray) -> float:
    """Return f where a piecewise-linear area curve reaches area, extending the end segments."""
    if area <= curve[0]:
        return float(f[0] + (area - curve[0]) * (f[1] - f[0]) / (curve[1] - curve[0]))
    if area >= curve[-1]:
        return float(f[-1] + (area - curve[-1]) * (f[-1] - f[-2]) / (curve[-1] - curve[-2]))
    return float(np.interp(area, curve, f))


def maxrange_estimates(areas: pd.DataFrame) -> pd.DataFrame:
    """Return per mask and region the maxrange f read off the mask's own area curve.

    Also the maxrange area over the maxrat area. A mask whose curve does not grow strictly in a
    region gets f = NaN there.
    """
    fixed = tuple(QRAT_FRACTION)
    f = np.array(list(QRAT_FRACTION.values()))
    table = {}
    for region in REGION_WELLS:
        curves = area_matrix(areas, region, fixed)
        target = area_matrix(areas, region, ("maxrange",))[:, 0]
        increasing = np.all(np.diff(curves, axis=1) > 0, axis=1)
        table[f"f_{region}"] = [
            invert_area_curve(c, a, f) if ok else np.nan
            for c, a, ok in zip(curves, target, increasing)
        ]
        table[f"maxrange_over_maxrat_{region}"] = target / curves[:, -1]
    table = pd.DataFrame(table)
    table.insert(0, "mask_index", np.arange(len(table)))
    return table


def maxrange_spread(estimates: pd.DataFrame, wells: pd.DataFrame) -> pd.DataFrame:
    """Return per region the spread of the estimated maxrange f against candidate draws.

    Independent U(0, 1) per well: a region's f is the mean of its wells' f weighted by
    q_max - q_base. One U(0, 1) draw for all wells (or per cluster): the std of U(0, 1).
    Log-uniform rate between q_base and q_max: the region's f at the wells' median rates
    sqrt(q_base q_max).
    """
    rows = []
    for region, names in REGION_WELLS.items():
        f = estimates[f"f_{region}"].dropna().to_numpy()
        q_base = wells.loc[list(names), "q_base"].abs().to_numpy()
        q_max = wells.loc[list(names), "q_max"].abs().to_numpy()
        w = q_max - q_base
        rows.append(
            {
                "region": region,
                "wells": len(names),
                "masks": len(f),
                "f_min": float(f.min()),
                "f_median": float(np.median(f)),
                "f_max": float(f.max()),
                "f_std": float(f.std()),
                "std_independent_uniform": float(np.sqrt(np.sum(w**2)) / w.sum() / np.sqrt(12.0)),
                "std_common_uniform": float(1.0 / np.sqrt(12.0)),
                "median_log_uniform": float((np.sqrt(q_base * q_max) - q_base).sum() / w.sum()),
            }
        )
    return pd.DataFrame(rows)


def maxrange_correlations(estimates: pd.DataFrame) -> pd.DataFrame:
    """Return the correlation of the estimated maxrange f between every pair of regions."""
    names = list(REGION_WELLS)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pair = estimates[[f"f_{a}", f"f_{b}"]].dropna().to_numpy()
            r = float(np.corrcoef(pair[:, 0], pair[:, 1])[0, 1])
            rows.append({"region_a": a, "region_b": b, "masks": len(pair), "r": r})
    return pd.DataFrame(rows)


def maxrange_excess(estimates: pd.DataFrame) -> pd.DataFrame:
    """Return per region the masks whose maxrange area exceeds their maxrat area."""
    rows = []
    for region in REGION_WELLS:
        ratio = estimates[f"maxrange_over_maxrat_{region}"]
        rows.append(
            {
                "region": region,
                "masks_above_maxrat": int((ratio > 1.0).sum()),
                "max_excess": float(ratio.max() - 1.0),
                "max_f": float(estimates[f"f_{region}"].max()),
            }
        )
    return pd.DataFrame(rows)


def region_multipliers(
    wells: pd.DataFrame, par_ens: pd.DataFrame, mask_reals: list[str]
) -> pd.DataFrame:
    """Return per mask (mask order) the q_base-weighted mean WEL multiplier m of each region."""
    table = {}
    for region, names in REGION_WELLS.items():
        sub = wells.loc[list(names)]
        m = par_ens.loc[mask_reals, list(sub["parnme"])].to_numpy(dtype=float)
        weight = sub["q_base"].abs().to_numpy()
        table[f"m_{region}"] = m @ weight / weight.sum()
    table = pd.DataFrame(table)
    table.insert(0, "mask_index", np.arange(len(table)))
    return table


def multiplier_correlations(
    areas: pd.DataFrame, multipliers: pd.DataFrame, estimates: pd.DataFrame
) -> pd.DataFrame:
    """Return per region the correlation of m with the area of every scenario.

    Also with the maxrange-over-maxrat area ratio. Masks are paired with their realisations
    (pest_rebuild.mask_run_order), so m is the multiplier of the run behind each mask.
    """
    rows = []
    for region in REGION_WELLS:
        m = multipliers[f"m_{region}"].to_numpy()
        quantities = {f"area_{q}": area_matrix(areas, region, (q,))[:, 0] for q in QRATS}
        quantities["maxrange_over_maxrat"] = estimates[f"maxrange_over_maxrat_{region}"].to_numpy()
        for name, values in quantities.items():
            r = float(np.corrcoef(values, m)[0, 1])
            rows.append({"region": region, "quantity": name, "r_with_m": r})
    return pd.DataFrame(rows)


def write_rule_evidence(out: Path = EVIDENCE_DIR, pest_dir: Path = pr.PEST_DIR) -> None:
    """Recompute the evidence for the inferred scenario rule and write it to out as CSV."""
    # Imported here, not at the top, because ensemble_run imports this module.
    import ensemble_run as er
    import workflow as wf

    out.mkdir(parents=True, exist_ok=True)
    wells = priority_well_table()
    endpoints = wf.read_endpoints()
    areas = region_areas(er.read_mask, endpoints)
    areas.to_csv(out / "region_areas.csv", index=False)
    as_stored = region_areas(partial(er.read_mask, corrected=False), endpoints)
    mask_shift_sensitivity(areas, as_stored, wells).to_csv(out / "mask_shift.csv", index=False)
    table = hypothesis_table(areas, wells)
    table.to_csv(out / "hypothesis_ratios.csv", index=False)
    hypothesis_fits(table).to_csv(out / "hypothesis_fits.csv", index=False)
    growth_checks(areas).to_csv(out / "growth_checks.csv", index=False)
    estimates = maxrange_estimates(areas)
    estimates.to_csv(out / "maxrange_f.csv", index=False)
    maxrange_spread(estimates, wells).to_csv(out / "maxrange_spread.csv", index=False)
    maxrange_correlations(estimates).to_csv(out / "maxrange_correlations.csv", index=False)
    maxrange_excess(estimates).to_csv(out / "maxrange_excess.csv", index=False)
    pairing = er.mask_table(pest_dir)
    pairing = pairing[pairing["mask_index"] >= 0].sort_values("mask_index")
    par_ens = pd.read_csv(pest_dir / "modpath_par_ens.csv", index_col=0, dtype={"real_name": str})
    par_ens.index = par_ens.index.astype(str)
    multipliers = region_multipliers(wells, par_ens, list(pairing["real_name"].astype(str)))
    multipliers.to_csv(out / "region_multipliers.csv", index=False)
    correlations = multiplier_correlations(areas, multipliers, estimates)
    correlations.to_csv(out / "multiplier_correlations.csv", index=False)


def main(print_rates: bool = True, write_evidence: bool = True) -> None:
    """Print the base realisation's priority-well rates per scenario; write the rule evidence."""
    if print_rates:
        wells = priority_well_table()
        pars = pr.realisation_pars("base")
        table = {q: scenario_rates(scenario_pars(pars, q, 357, wells), wells) for q in QRATS}
        print(pd.DataFrame(table).round(1))
    if write_evidence:
        write_rule_evidence()


if __name__ == "__main__":
    main()
