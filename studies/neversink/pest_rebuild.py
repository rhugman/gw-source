"""Neversink case study, ensemble input: MF6 input for any realisation of the published iES
ensemble, without PEST++.

The published ensemble (Fienen and others 2021; Corson-Dosch and others 2021) is a set of
multiplier parameters on the base model in neversink_mf6/. The PEST interface folder that turns
parameter values into MF6 input (run_data/: templates, multiplier files, pilot points, kriging
factors, forward_run.py) is not in the source repository, so it is rebuilt here from notebook
0.0_PEST_parameterization (pyemu PstFrom) and checked against the parameter names of the final
control file output/parallel/never_ies_0.noise_lt_obs.pst.

Parameterisation (all multipliers on the neversink_mf6 values, log-transformed):
- K and K33, per layer: pilot points (ordinary kriging of log10 values, exponential variogram
  with range 3 * spacing * 50 m, at most 20 points; spacing 20 cells in layers 1 and 4 and 5 cells
  in layers 2 and 3, only in IDOMAIN == 1 cells) times one multiplier per geology zone of the
  padded K-zone files; capped at 152 m/d (K) and 15.2 m/d (K33).
- Recharge: pilot points on the layer-4 footprint (the notebook reuses the last layer's spacing
  and variogram, so they coincide with the K layer-4 points) times one constant; capped at 1.2
  times the largest base recharge.
- SFR streambed K: one value per NHDPlus line_id written directly into the rhk column.
- WEL rates and CHD heads: one multiplier per cell (CHD fixed at 1).

The rebuilt files must match those that pyemu wrote in 2021 exactly, down to the order of the
kriging neighbours and the rounding of the written arrays. The current pyemu of the project
environment is not relied on for that, and the 2021 copy shipped with the source repository
(python_packages_static/pyemu) does not import with NumPy 2. So the pieces of pyemu 2021 that
PstFrom used (setup_pilotpoints_grid, OrdinaryKrige.calc_factors_grid, fac2real,
apply_list_and_array_pars) are ported below with the same neighbour order and file rounding. The
rebuilt base realisation is checked against the published calibrated input (neversink_optimal/,
written from the iteration-4 base realisation by notebook 3.2), and three realisations against
the simulated values in never_ies_0.noise_lt_obs.4.obs.csv.

The MODPATH Monte Carlo ensemble (modpath_par_ens.csv) is rebuilt with the notebook 3.2
rejection sampling: iteration 4, phi < 3200 and |PERC_DISC| < 0.01 (read from the iteration-0
observation file, as the notebook does). That gives 358 realisations, with 'base' last. Rows
0..356 of that table (the runs) have a published mask, 'base' has none; mask k is run
mask_run_order()[k] (text-sorted run names; mc_masks.py), written to mask_index.csv.

Run with the project environment (MF6 from <repo>/bin):

    python studies/neversink/pest_rebuild.py

Edit the gates in __main__ to rerun parts. Output goes to studies/neversink/output/pest/
(git-ignored).
"""

import json
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import flopy
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import workflow as wf

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "external" / "neversink_workflow"
BASE_MODEL = SOURCE / "neversink_mf6"
OPTIMAL_MODEL = SOURCE / "neversink_optimal"
PARALLEL = SOURCE / "output" / "parallel"
PROCESSED = SOURCE / "processed_data"
PEST_DIR = HERE / "output" / "pest"

MODEL = "neversink"
PST_ROOT = "never_ies_0.noise_lt_obs"
BEST_ITER = 4
PHI_TOO_HIGH = 3200.0
PERC_DISC_MAX = 0.01
N_MASKS = 357  # published masks per scenario (runs 0..356; the base realisation has none)
NLAY = 4

# Notebook 0.0 settings
PP_SPACE = {0: 20, 1: 5, 2: 5, 3: 20}
RCH_PP_LAYER = 3  # rch pilot points reuse the last loop's zone, spacing and variogram
K_ULT_UB = {"k": 152.0, "k33": 15.2}
RCH_ULT_UB_FACTOR = 1.2
PP_MAXPTS = 20
PP_EPSILON = 1.0e-7  # pyemu geostats EPSILON
PP_FILL, PP_LOWER, PP_UPPER = 1.0, 1.0e-10, 1.0e10
LSOBS_EVERY = 50
LSOBS_DROP = ((0, 150, 50), (3, 150, 100), (3, 100, 50))
ARRAY_FMT = "%15.6E"  # pyemu writes multiplier and model arrays with this format
FACTOR_FMT = "%12.8g"  # and kriging weights with this one

# Base-model files that are MF6 output, not input
OUTPUT_FILES = (
    "mfsim.lst", "*.list", "*.grb", "*.obs.output.csv", "neversink.head.obs", "*.chk",
    "*.json", "postproc", "tables", "original", "*.hds", "*.cbc", "*.bin",
)

PP_NAME = re.compile(r"^(k|k33|rch)_pp_:(\d)_i:(\d+)_j:(\d+)$")
ZONE_NAME = re.compile(r"^multiplier_(k|k33)_(\d)_:0_zone:(\d+)$")
RCH_CONST = "multiplier_const_rch_const_:0"
LIST_NAME = re.compile(r"^(wel|chd)__:0_usecol:3_idx0:(\d+)_idx1:(\d+)_idx2:(\d+)$")


@dataclass
class Interface:
    """The rebuilt PEST interface: everything needed to turn parameter values into MF6 input."""

    pp: pd.DataFrame  # one row per pilot point: set, layer, i, j, parnme
    factors: dict  # factor layer -> (cells, neighbours, weights)
    k_zones: np.ndarray  # (nlay, nrow, ncol) K-zone ids, 0 outside IDOMAIN == 1
    rch_ult_ub: float


# ---------------------------------------------------------------------------------------------
# Pilot points and kriging factors (ports of pyemu 2021)
# ---------------------------------------------------------------------------------------------


def load_idomain(model_dir: Path = BASE_MODEL, nlay: int = NLAY) -> np.ndarray:
    """Return IDOMAIN with pass-through cells (-1) set to 0, as notebook 0.0 does."""
    idm = np.stack([np.loadtxt(model_dir / f"idomain_{k:03d}.dat", dtype=int) for k in range(nlay)])
    idm[idm == -1] = 0
    return idm


def load_k_zones(idm: np.ndarray, processed: Path = PROCESSED) -> np.ndarray:
    """Return the geology K zones per layer, zeroed outside IDOMAIN == 1."""
    zones = []
    for k in range(idm.shape[0]):
        kz = np.loadtxt(processed / f"padded_L{k}_K_Zone_50mGrid.dat").astype(int)
        kz[idm[k] != 1] = 0
        zones.append(kz)
    return np.stack(zones)


def cell_centres(model_dir: Path = BASE_MODEL) -> tuple[np.ndarray, np.ndarray]:
    """Return x and y of the cell centres (nrow, ncol) from the modflow-setup grid file."""
    grid = json.loads((model_dir / f"{MODEL}_grid.json").read_text())
    assert grid["angrot"] == 0.0, "rotated grids not handled"
    delr, delc = np.asarray(grid["delr"]), np.asarray(grid["delc"])
    x = grid["xul"] + np.cumsum(delr) - 0.5 * delr
    y = grid["yul"] - (np.cumsum(delc) - 0.5 * delc)
    return np.meshgrid(x, y)


def pilot_point_cells(zone: np.ndarray, every_n: int) -> np.ndarray:
    """Return the (i, j) of the pilot points in pyemu.pp_utils.setup_pilotpoints_grid order."""
    start = int(every_n / 2.0)
    cells = [
        (i, j)
        for i in range(start, zone.shape[0] - start, every_n)
        for j in range(start, zone.shape[1] - start, every_n)
        if zone[i, j] > 0
    ]
    return np.array(cells, dtype=int)


def exp_cov(h: np.ndarray, a: float) -> np.ndarray:
    """Return the exponential covariance (contribution 1, no nugget) at distance h."""
    return np.exp(-h / a)


def kriging_factors(
    pp_xy: np.ndarray,
    cell_xy: np.ndarray,
    a: float,
    maxpts: int = PP_MAXPTS,
    epsilon: float = PP_EPSILON,
    chunk: int = 20000,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ordinary-kriging neighbours and weights (n_cells, maxpts) of each target cell.

    As pyemu OrdinaryKrige: the maxpts nearest points by an unstable quicksort of the squared
    distances (ties then fall as in pyemu), and weight 1 on a point within epsilon of the cell.
    """
    n_pts = len(pp_xy)
    m = min(maxpts, n_pts)
    pp_cov = exp_cov(np.hypot(*(pp_xy[:, None, :] - pp_xy[None, :, :]).transpose(2, 0, 1)), a)
    nbrs = np.empty((len(cell_xy), m), dtype=np.int32)
    weights = np.empty((len(cell_xy), m))
    for s in range(0, len(cell_xy), chunk):
        xy = cell_xy[s : s + chunk]
        d2 = (pp_xy[None, :, 0] - xy[:, 0, None]) ** 2 + (pp_xy[None, :, 1] - xy[:, 1, None]) ** 2
        nb = np.argsort(d2, axis=1, kind="quicksort")[:, :m]
        dist = np.sqrt(np.take_along_axis(d2, nb, axis=1))
        lhs = np.ones((len(xy), m + 1, m + 1))
        lhs[:, :m, :m] = pp_cov[nb[:, :, None], nb[:, None, :]]
        lhs[:, m, m] = 0.0
        rhs = np.ones((len(xy), m + 1))
        rhs[:, :m] = exp_cov(dist, a)
        w = np.linalg.solve(lhs, rhs[..., None])[..., 0][:, :m]
        w = as_written(w, FACTOR_FMT)
        snap = dist[:, 0] <= epsilon
        w[snap] = 0.0
        w[snap, 0] = 1.0
        nbrs[s : s + chunk], weights[s : s + chunk] = nb, w
    return nbrs, weights


def build_pilot_points(idm: np.ndarray, pp_space: dict = PP_SPACE) -> pd.DataFrame:
    """Return every pilot point parameter (k, k33 per layer and rch) with its name and cell."""
    rows = []
    for tag in ("k", "k33"):
        for layer, every_n in pp_space.items():
            for n, (i, j) in enumerate(pilot_point_cells(idm[layer], every_n)):
                name = f"{tag}_pp_:{layer}_i:{i}_j:{j}"
                rows.append({"set": tag, "layer": layer, "fac_layer": layer, "n": n, "i": i, "j": j, "parnme": name})
    for n, (i, j) in enumerate(pilot_point_cells(idm[RCH_PP_LAYER], pp_space[RCH_PP_LAYER])):
        name = f"rch_pp_:0_i:{i}_j:{j}"
        rows.append({"set": "rch", "layer": 0, "fac_layer": RCH_PP_LAYER, "n": n, "i": i, "j": j, "parnme": name})
    return pd.DataFrame(rows)


def build_factors(
    idm: np.ndarray, pp: pd.DataFrame, x: np.ndarray, y: np.ndarray, pp_space: dict = PP_SPACE, delr: float = 50.0
) -> dict:
    """Return per layer the target cells (flat index), neighbours and kriging weights."""
    factors = {}
    for layer, every_n in pp_space.items():
        pts = pp.loc[(pp["set"] == "k") & (pp["layer"] == layer)].sort_values("n")
        pp_xy = np.column_stack([x[pts["i"], pts["j"]], y[pts["i"], pts["j"]]])
        cells = np.flatnonzero(idm[layer].ravel() == 1)
        cell_xy = np.column_stack([x.ravel()[cells], y.ravel()[cells]])
        nbrs, weights = kriging_factors(pp_xy, cell_xy, a=delr * 3 * every_n)
        factors[layer] = (cells, nbrs, weights)
    return factors


def check_against_pst(pp: pd.DataFrame, k_zones: np.ndarray, par_data: pd.DataFrame) -> dict:
    """Assert that the rebuilt interface uses exactly the parameters of the published pst."""
    names = set(par_data.index)
    expected_pp = {n for n in names if PP_NAME.match(n)}
    assert set(pp["parnme"]) == expected_pp, "pilot point locations differ from the pst"
    zone_pars = set()
    for tag in ("k", "k33"):
        for layer in range(k_zones.shape[0]):
            zone_pars |= {f"multiplier_{tag}_{layer}_:0_zone:{z}" for z in np.unique(k_zones[layer]) if z > 0}
    assert zone_pars == {n for n in names if ZONE_NAME.match(n)}, "K zones differ from the pst"
    other = names - expected_pp - zone_pars - {RCH_CONST}
    assert all(LIST_NAME.match(n) or n.startswith("sfrk_") for n in other), "unknown parameters"
    return {"pilot_points": len(expected_pp), "zones": len(zone_pars), "other": len(other)}


def build_interface(
    pest_dir: Path = PEST_DIR, model_dir: Path = BASE_MODEL, parallel: Path = PARALLEL
) -> dict:
    """Rebuild the interface into pest_dir and return parameter counts."""
    pest_dir.mkdir(parents=True, exist_ok=True)
    idm = load_idomain(model_dir)
    k_zones = load_k_zones(idm)
    x, y = cell_centres(model_dir)
    pp = build_pilot_points(idm)
    counts = check_against_pst(pp, k_zones, read_par_data(parallel))
    t0 = time.perf_counter()
    factors = build_factors(idm, pp, x, y)
    counts["factor_seconds"] = time.perf_counter() - t0
    pp.to_csv(pest_dir / "pilot_points.csv", index=False)
    np.savez_compressed(pest_dir / "k_zones.npz", k_zones=k_zones)
    for layer, (cells, nbrs, weights) in factors.items():
        np.savez_compressed(pest_dir / f"pp_factors_{layer}.npz", cells=cells, nbrs=nbrs, weights=weights)
    rch_ub = RCH_ULT_UB_FACTOR * float(np.loadtxt(model_dir / "rch_000.dat").max())
    (pest_dir / "ult_bounds.json").write_text(json.dumps({**K_ULT_UB, "rch": rch_ub}, indent=1))
    write_land_surface_indices(pest_dir / "land_surf_obs-indices.csv", model_dir)
    return counts


def load_interface(pest_dir: Path = PEST_DIR) -> Interface:
    """Read the interface written by build_interface."""
    assert (pest_dir / "pilot_points.csv").is_file(), f"run build_interface first ({pest_dir})"
    factors = {}
    for layer in range(NLAY):
        f = np.load(pest_dir / f"pp_factors_{layer}.npz")
        factors[layer] = (f["cells"], f["nbrs"], f["weights"])
    bounds = json.loads((pest_dir / "ult_bounds.json").read_text())
    return Interface(
        pp=pd.read_csv(pest_dir / "pilot_points.csv"),
        factors=factors,
        k_zones=np.load(pest_dir / "k_zones.npz")["k_zones"],
        rch_ult_ub=bounds["rch"],
    )


# ---------------------------------------------------------------------------------------------
# Ensembles
# ---------------------------------------------------------------------------------------------


def read_par_data(parallel: Path = PARALLEL, pst_root: str = PST_ROOT) -> pd.DataFrame:
    """Return the parameter data of the final iES control file, indexed by name."""
    par_data = pd.read_csv(parallel / f"{pst_root}.par_data.csv", usecols=range(9))
    return par_data.set_index("parnme")


def kept_realisations(
    parallel: Path = PARALLEL,
    pst_root: str = PST_ROOT,
    best_iter: int = BEST_ITER,
    phi_too_high: float = PHI_TOO_HIGH,
    perc_disc_max: float = PERC_DISC_MAX,
) -> np.ndarray:
    """Return the realisation names kept by the notebook 3.2 rejection sampling, in its order."""
    phi = pd.read_csv(parallel / f"{pst_root}.phi.actual.csv", index_col=0)
    phivec = phi.loc[best_iter].iloc[5:]
    keep = phivec[phivec < phi_too_high].index.values
    # notebook 3.2 reads the mass balance from the iteration-0 file, not iteration best_iter
    ens = pd.read_csv(parallel / f"{pst_root}.0.obs.csv", index_col=0, dtype={"real_name": str})
    perc_disc = ens.loc[keep, "perc_disc"].abs()
    return perc_disc[perc_disc < perc_disc_max].index.values


def build_par_ensemble(
    out_file: Path, parallel: Path = PARALLEL, pst_root: str = PST_ROOT, best_iter: int = BEST_ITER
) -> pd.DataFrame:
    """Write modpath_par_ens.csv (the MODPATH Monte Carlo ensemble) and return it."""
    keep = kept_realisations(parallel, pst_root, best_iter)
    par_ens = pd.read_csv(parallel / f"{pst_root}.{best_iter}.par.csv", index_col=0, dtype={"real_name": str})
    par_ens = par_ens.loc[keep]
    assert list(par_ens.columns) == list(read_par_data(parallel).index), "parameter order differs"
    par_ens.to_csv(out_file)
    return par_ens


def mask_run_order(n_masks: int = N_MASKS) -> list[int]:
    """Return the run (row of modpath_par_ens.csv) of every published mask, in mask order.

    scripts/modpath_mc_varq.py saves run r as mp_results_{r}_{qrat}.zip and the masks follow
    those names sorted as text ('100_' before '10_'); the order is the same in every scenario.
    """
    return sorted(range(n_masks), key=lambda r: f"mp_results_{r}_baserat.zip")


def mask_index_table(real_names: list[str], n_masks: int = N_MASKS) -> pd.DataFrame:
    """Return per realisation (table order) its run index and published mask index (-1: none)."""
    mask = np.full(len(real_names), -1)
    mask[mask_run_order(n_masks)] = np.arange(n_masks)
    runs = np.arange(len(real_names))
    return pd.DataFrame({"real_name": list(real_names), "run_index": runs, "mask_index": mask})


def realisation_pars(real_name: str, par_ens_file: Path = PEST_DIR / "modpath_par_ens.csv") -> pd.Series:
    """Return the parameter values of one realisation of the Monte Carlo ensemble."""
    par_ens = pd.read_csv(par_ens_file, index_col=0, dtype={"real_name": str})
    par_ens.index = par_ens.index.astype(str)
    assert real_name in par_ens.index, f"{real_name} not in {par_ens_file.name}"
    return par_ens.loc[real_name]


# ---------------------------------------------------------------------------------------------
# Applying parameters (ports of pyemu fac2real and apply_list_and_array_pars)
# ---------------------------------------------------------------------------------------------


def as_written(a: np.ndarray, fmt: str = ARRAY_FMT) -> np.ndarray:
    """Return a rounded as savetxt(fmt) then loadtxt would give it."""
    a = np.asarray(a, dtype=float)
    return np.fromiter((float(fmt % v) for v in a.ravel().tolist()), float, a.size).reshape(a.shape)


def pp_array(values: np.ndarray, factors: tuple, shape: tuple) -> np.ndarray:
    """Return the kriged multiplier array (fac2real with log transform, fill 1, as written)."""
    cells, nbrs, weights = factors
    arr = np.full(int(np.prod(shape)), PP_FILL)
    kriged = 10.0 ** np.sum(weights * np.log10(values)[nbrs], axis=1)
    arr[cells] = as_written(np.clip(kriged, PP_LOWER, PP_UPPER))
    return arr.reshape(shape)


def zone_array(zones: np.ndarray, values: dict) -> np.ndarray:
    """Return the zone multiplier array (1 outside the zones)."""
    arr = np.ones(zones.shape)
    for z, v in values.items():
        arr[zones == z] = v
    return arr


def pp_values(pars: pd.Series, pp: pd.DataFrame, tag: str, layer: int) -> np.ndarray:
    """Return the pilot point values of one set in factor order."""
    pts = pp.loc[(pp["set"] == tag) & (pp["layer"] == layer)].sort_values("n")
    return pars.loc[pts["parnme"]].to_numpy(dtype=float)


def write_array(path: Path, arr: np.ndarray) -> None:
    """Write a model array as pyemu does."""
    np.savetxt(path, np.atleast_2d(arr), fmt=ARRAY_FMT, delimiter="")


def apply_k_pars(ws: Path, pars: pd.Series, iface: Interface, model_dir: Path = BASE_MODEL) -> None:
    """Write k{L}.dat and k33{L}.dat: base * pilot points * zones, capped."""
    for tag in ("k", "k33"):
        for layer in range(NLAY):
            org = np.loadtxt(model_dir / f"{tag}{layer}.dat")
            mult_pp = pp_array(pp_values(pars, iface.pp, tag, layer), iface.factors[layer], org.shape)
            zones = iface.k_zones[layer]
            zvals = {z: pars[f"multiplier_{tag}_{layer}_:0_zone:{z}"] for z in np.unique(zones) if z > 0}
            arr = org * mult_pp * zone_array(zones, zvals)
            write_array(ws / f"{tag}{layer}.dat", np.minimum(arr, K_ULT_UB[tag]))


def apply_rch_pars(ws: Path, pars: pd.Series, iface: Interface, model_dir: Path = BASE_MODEL) -> None:
    """Write rch_000.dat: base * pilot points * constant, capped.

    Both multipliers act only on the layer-4 footprint (the zone array of notebook 0.0).
    """
    org = np.loadtxt(model_dir / "rch_000.dat")
    factors = iface.factors[RCH_PP_LAYER]
    mult_pp = pp_array(pp_values(pars, iface.pp, "rch", 0), factors, org.shape)
    mult_const = np.ones(org.size)
    mult_const[factors[0]] = pars[RCH_CONST]
    arr = org * mult_pp * mult_const.reshape(org.shape)
    write_array(ws / "rch_000.dat", np.minimum(arr, iface.rch_ult_ub))


def apply_list_pars(ws: Path, pars: pd.Series, tag: str, model_dir: Path = BASE_MODEL) -> None:
    """Write wel_000.dat or chd_000.dat with column 4 multiplied per cell."""
    fname = f"{tag}_000.dat"
    lines = (model_dir / fname).read_text().splitlines()
    header = [line for line in lines if line.startswith("#")]
    rows = [line.split() for line in lines if line.strip() and not line.startswith("#")]
    mult = {}
    for name in pars.index:
        match = LIST_NAME.match(name)
        if match and match.group(1) == tag:
            mult[tuple(int(v) + 1 for v in match.groups()[1:])] = float(pars[name])
    out = []
    for row in rows:
        cell = tuple(int(v) for v in row[:3])
        assert cell in mult, f"no {tag} multiplier for cell {cell}"
        row[3] = repr(float(row[3]) * mult[cell])
        out.append(" ".join(row))
    (ws / fname).write_text("\n".join(header + out) + "\n")


def apply_sfr_pars(ws: Path, pars: pd.Series, model_dir: Path = BASE_MODEL) -> None:
    """Write the SFR packagedata with rhk set to the line_id parameter (the notebook template)."""
    fname = f"{MODEL}_packagedata.dat"
    lines = (model_dir / fname).read_text().splitlines()
    header = [line.strip() for line in lines if "#" in line]
    out = []
    for line in lines:
        if "#" in line or not line.strip():
            continue
        words = line.split()
        words[-6] = repr(float(pars[f"sfrk_{words[-1]}"]))
        out.append(" ".join(words))
    (ws / fname).write_text("\n".join(header + out) + "\n")


def copy_base_model(ws: Path, model_dir: Path = BASE_MODEL) -> None:
    """Copy the base MF6 input (no output files) into a clean workspace."""
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(model_dir, ws, ignore=shutil.ignore_patterns(*OUTPUT_FILES))


def write_realisation(
    real_name: str,
    ws: Path,
    pars: pd.Series | None = None,
    iface: Interface | None = None,
    npf_options: tuple[str, ...] = ("SAVE_SPECIFIC_DISCHARGE", "SAVE_SATURATION"),
    dvclose: tuple | None = None,
    pest_dir: Path = PEST_DIR,
) -> Path:
    """Write a runnable MF6 workspace for one realisation of the Monte Carlo ensemble.

    pars overrides the ensemble row (e.g. for an iteration-4 realisation that was rejected);
    npf_options are added for gwsource and PRT; dvclose as in workflow.prepare_model.
    """
    if pars is None:
        pars = realisation_pars(real_name, pest_dir / "modpath_par_ens.csv")
    if iface is None:
        iface = load_interface(pest_dir)
    copy_base_model(ws)
    apply_k_pars(ws, pars, iface)
    apply_rch_pars(ws, pars, iface)
    for tag in ("wel", "chd"):
        apply_list_pars(ws, pars, tag)
    apply_sfr_pars(ws, pars)
    wf.update_ims(ws / "mfsim.ims", dvclose)
    for option in npf_options:
        wf.add_npf_option(ws / f"{MODEL}.npf", option)
    (ws / "realisation.txt").write_text(f"{real_name}\n")
    return ws


# ---------------------------------------------------------------------------------------------
# Observations (port of scripts/get_observations.py)
# ---------------------------------------------------------------------------------------------


def write_land_surface_indices(path: Path, model_dir: Path = BASE_MODEL) -> pd.DataFrame:
    """Write the land-surface observation cells of notebook 0.0 (k, i, j, obsname)."""
    id3 = np.loadtxt(model_dir / "idomain_003.dat", dtype=int)
    irch = np.loadtxt(model_dir / "irch.dat", dtype=int) - 1
    nrow, ncol = id3.shape
    jj, ii = np.meshgrid(range(0, ncol, LSOBS_EVERY), range(0, nrow, LSOBS_EVERY))
    keep = [(irch[i, j], i, j) for i, j in zip(ii.ravel(), jj.ravel()) if id3[i, j] == 1]
    keep = [p for p in keep if p not in LSOBS_DROP]
    df = pd.DataFrame(keep, columns=["k", "i", "j"])
    df["obsname"] = [f"land_surf_obs_{i}_{j}" for _, i, j in keep]
    df.to_csv(path, index=False)
    return df


def transmissivities(heads: np.ndarray, hk: np.ndarray, top: np.ndarray, botm: np.ndarray, r: int, c: int) -> np.ndarray:
    """Return the saturated transmissivity of every layer at (r, c) (get_transmissivities)."""
    h = heads[:, r, c]
    tops = np.concatenate([[top[r, c]], botm[:-1, r, c]])
    bots = botm[:, r, c].copy()
    open_top = np.minimum(tops, h)
    thick = open_top - bots
    if np.all(thick < 0):
        thick[np.argmax(thick)] = 1.0
    thick[thick < 0] = 0.0
    thick[np.isnan(h)] = 0.0
    return thick * hk[:, r, c]


def read_head_obs_meta(obs_file: Path) -> pd.DataFrame:
    """Return name, layer, row, col (0-based) of the continuous head observations."""
    lines = [line.strip().lower() for line in obs_file.read_text().splitlines()]
    start = next(n for n, v in enumerate(lines) if "begin continuous" in v)
    end = next(n for n, v in enumerate(lines) if "end continuous" in v)
    rows = [line.split() for line in lines[start + 1 : end] if line]
    meta = pd.DataFrame(rows, columns=["name", "type", "lay", "row", "col"])
    for col in ("lay", "row", "col"):
        meta[col] = meta[col].astype(int) - 1
    return meta


def extract_observations(ws: Path, lsobs_file: Path = PEST_DIR / "land_surf_obs-indices.csv") -> pd.Series:
    """Return the PEST observations (q_*, h_*, perc_disc, land_surf_obs_*) of a finished run."""
    heads = flopy.utils.HeadFile(ws / f"{MODEL}.hds").get_data()
    hk = np.stack([np.loadtxt(ws / f"k{k}.dat") for k in range(NLAY)])
    top = np.loadtxt(ws / "top.dat")
    botm = np.stack(
        [np.loadtxt(ws / f"botm_{k:03d}.dat") for k in range(NLAY - 1)]
        + [np.loadtxt(ws / f"{MODEL}_layer_5_new_botm_elevations.dat")]
    )
    sfr = pd.read_csv(ws / f"{MODEL}.sfr.obs.output.csv").drop(columns="time").iloc[0]
    obs = {f"q_{name}": -float(v) for name, v in sfr.items()}
    sim_h = pd.read_csv(ws / f"{MODEL}.head.obs").drop(columns="time").iloc[0]
    meta = read_head_obs_meta(ws / f"{MODEL}.obs")
    roots = ["h_" + c.lower().split(".")[0] for c in sim_h.index]
    assert roots == ["h_" + n for n in meta["name"]], "head obs output and metadata differ"
    meta["head"] = sim_h.to_numpy(dtype=float)
    assert meta["head"].mean() != 0.0, "MF6 did not converge"
    for name, group in meta.groupby("name", sort=False):
        t = transmissivities(heads, hk, top, botm, group["row"].iloc[0], group["col"].iloc[0])
        t_frac = t[group["lay"].to_numpy()] / t.sum()
        obs[f"h_{name}"] = float(np.nansum(group["head"].to_numpy() * t_frac))
    flux, _ = flopy.utils.Mf6ListBudget(ws / f"{MODEL}.list").get_dataframes()
    obs["perc_disc"] = float(flux["PERCENT_DISCREPANCY"].to_numpy()[0])
    ls = pd.read_csv(lsobs_file)
    for k, i, j, name in ls.itertuples(index=False):
        obs[name] = float(heads[k, i, j])
    return pd.Series(obs)


def compare_observations(sim: pd.Series, stored: pd.Series) -> pd.DataFrame:
    """Return max and median |sim - stored| per observation group (relative for flows)."""
    common = sim.index.intersection(stored.index)
    assert len(common) == len(stored), f"missing observations: {set(stored.index) - set(sim.index)}"
    diff = (sim[common] - stored[common]).abs()
    groups = {
        "h_": "head [m]", "land_surf": "land surface head [m]", "q_": "flow [rel]", "perc_disc": "perc_disc [%]",
    }
    rows = []
    for prefix, label in groups.items():
        sel = [n for n in common if n.startswith(prefix)]
        d = diff[sel]
        if prefix == "q_":
            d = d / stored[sel].abs()
        rows.append({"group": label, "n": len(sel), "max": d.max(), "median": d.median()})
    return pd.DataFrame(rows)


def stored_observations(real_name: str, parallel: Path = PARALLEL, best_iter: int = BEST_ITER) -> pd.Series:
    """Return the simulated values stored by pestpp-ies for one realisation."""
    obs = pd.read_csv(parallel / f"{PST_ROOT}.{best_iter}.obs.csv", index_col=0, dtype={"real_name": str})
    obs.index = obs.index.astype(str)
    return obs.loc[real_name].astype(float)


# ---------------------------------------------------------------------------------------------
# Checks against the published calibrated input
# ---------------------------------------------------------------------------------------------


def max_rel_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Return max |a - b| / max(|b|, tiny)."""
    return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-30)))


def compare_with_optimal(ws: Path, ref: Path = OPTIMAL_MODEL) -> pd.DataFrame:
    """Compare the parameterised input of ws with the published calibrated model input."""
    rows = []
    for tag in ("k", "k33"):
        for layer in range(NLAY):
            f = f"{tag}{layer}.dat"
            rows.append({"file": f, "max_rel_diff": max_rel_diff(np.loadtxt(ws / f), np.loadtxt(ref / f))})
    rows.append({"file": "rch_000.dat", "max_rel_diff": max_rel_diff(np.loadtxt(ws / "rch_000.dat"), np.loadtxt(ref / "rch_000.dat"))})
    for f, col in (("wel_000.dat", 3), ("chd_000.dat", 3), (f"{MODEL}_packagedata.dat", 9)):
        a = pd.read_csv(ws / f, sep=r"\s+", comment="#", header=None)[col].to_numpy(float)
        b = pd.read_csv(ref / f, sep=r"\s+", comment="#", header=None)[col].to_numpy(float)
        rows.append({"file": f, "max_rel_diff": max_rel_diff(a, b)})
    return pd.DataFrame(rows)


def main(
    rebuild_interface: bool = True,
    rebuild_ensemble: bool = True,
    check_base_input: bool = True,
    run_checks: bool = True,
    check_reals: tuple[str, ...] = ("base", "0", "280"),  # 0 and 280: rows 0 and 200
    pest_dir: Path = PEST_DIR,
) -> None:
    """Rebuild the interface and ensemble, then check realisations; tables go to pest_dir."""
    pest_dir.mkdir(parents=True, exist_ok=True)
    if rebuild_interface:
        counts = build_interface(pest_dir)
        pd.Series(counts).to_csv(pest_dir / "interface_counts.csv", header=["value"])
    if rebuild_ensemble:
        par_ens = build_par_ensemble(pest_dir / "modpath_par_ens.csv")
        assert len(par_ens) == 358, f"expected 358 realisations, got {len(par_ens)}"
        mask_index_table(list(par_ens.index)).to_csv(pest_dir / "mask_index.csv", index=False)
    iface = load_interface(pest_dir)
    reals_dir = pest_dir / "reals"
    if check_base_input:
        t0 = time.perf_counter()
        ws = write_realisation("base", reals_dir / "base", iface=iface, pest_dir=pest_dir)
        seconds = time.perf_counter() - t0
        compare_with_optimal(ws).assign(write_seconds=seconds).to_csv(pest_dir / "check_base_input.csv", index=False)
    if run_checks:
        exe = wf.mf6_exe()
        rows = []
        for real in check_reals:
            ws = reals_dir / real
            t0 = time.perf_counter()
            write_realisation(real, ws, iface=iface, pest_dir=pest_dir)
            write_seconds = time.perf_counter() - t0
            mf6_seconds = wf.run_mf6(ws, exe)
            table = compare_observations(extract_observations(ws, pest_dir / "land_surf_obs-indices.csv"), stored_observations(real))
            table = table.assign(real=real, write_seconds=write_seconds, mf6_seconds=mf6_seconds)
            if real == "base":
                table["max_dh_vs_published_hds"] = wf.head_difference(ws)
            rows.append(table)
        pd.concat(rows).to_csv(pest_dir / "check_observations.csv", index=False)


if __name__ == "__main__":
    main()
