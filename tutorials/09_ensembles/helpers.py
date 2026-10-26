"""Helpers local to tutorial 09 (ensembles): the pilot-point ensemble, per-realisation
summaries, a process-pool check, the face-routing comparison and a small PEST++ IES history match.

The ensemble describes ln K with pilot points on a regular grid. The pilot-point values are
drawn with a Gaussian correlation exp(-(r / L)^2) and kriged to every cell with simple kriging
around ln(mean K). Each realisation is rerun in a folder of its own, so that gwsource can trace
it. The same folders and functions serve the prior (section 1 of the notebook) and the PEST++
IES posterior (section 9).

gwsource.run_ensemble folds per-cell outputs into statistics over the realisations. The
well's split by source package is a sum over cells, not a per-cell output, so this module
traces each realisation once more to tabulate it (cheap for a small model).

The synthetic "true" aquifer of section 9 is not built from pilot points. It is a field of
herebedragons.random_k_field: white noise smoothed with a Gaussian filter of width s, which has
the correlation exp(-(r / 2s)^2). With L = 2s the truth and the prior share their statistics.
"""

import inspect
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager, redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

import gwsource as gs


def process_pool_available() -> bool:
    """Return False where the OS refuses process pools (e.g. a sandbox without semaphores)."""
    try:
        ProcessPoolExecutor(max_workers=1).shutdown()
    except (PermissionError, NotImplementedError, OSError):  # raised by the system-limits check
        return False
    return True


def realisation_summary(
    ws: Path, group: str, select_kwargs: dict, thresholds: tuple[float, ...]
) -> dict[str, float]:
    """Return one realisation's source shares of the group and its capture areas [km2]."""
    step = gs.read_step(ws, boundnames=True)
    res = gs.backward(step, {group: gs.select(step, **select_kwargs)})
    by_term = res.volume_from_by_term[group]
    total = sum(float(v.sum()) for v in by_term.values())
    row = {f"share {name}": float(v.sum()) / total for name, v in by_term.items() if v.sum() > 0}
    fraction = res.fraction_through[group]
    for t in thresholds:
        row[f"area F>{t} (km2)"] = float(step.area[fraction > t].sum()) / 1e6
    return row


def summarise_realisations(
    workspaces: list[Path], group: str, select_kwargs: dict, thresholds: tuple[float, ...]
) -> pd.DataFrame:
    """Return a table with one row per realisation (shares by source package, capture areas)."""
    rows = {
        Path(ws).name: realisation_summary(ws, group, select_kwargs, thresholds)
        for ws in workspaces
    }
    return pd.DataFrame(rows).T.fillna(0.0)


def max_quantile_difference(
    exact: gs.EnsembleResult, approx: gs.EnsembleResult, output: str, group: str
) -> dict[float, float]:
    """Return {quantile: largest |approx - exact|} over the cells whose values all lie in range."""
    low, high = exact.config.bin_range(output)
    tol = 1e-9 * (high - low)  # round-off, e.g. F = 1 + 1e-15
    stats = exact.stats
    inside = (stats["min"][output][group] >= low - tol) & (stats["max"][output][group] <= high + tol)
    out = {}
    for q in exact.config.quantiles:
        a, b = exact.quantiles[q][output][group], approx.quantiles[q][output][group]
        cells = inside & np.isfinite(a) & np.isfinite(b)
        out[q] = float(np.abs(a[cells] - b[cells]).max())
    return out


# ---------------------------------------------------------------- mixing assumption


def capture_summary(step: gs.FlowStep, result, group: str) -> dict[str, float]:
    """Return the area F > 0.5, the band 0.1 < F < 0.9 [km2] and the river share of one trace."""
    fraction = result.fraction_through[group]
    by_term = {name: float(v.sum()) for name, v in result.volume_from_by_term[group].items()}
    return {
        "area F > 0.5 (km2)": float(step.area[fraction > 0.5].sum()) / 1e6,
        "band 0.1 < F < 0.9 (km2)": float(step.area[(fraction > 0.1) & (fraction < 0.9)].sum()) / 1e6,
        "river share": by_term.get("RIV", 0.0) / sum(by_term.values()),
    }


def face_routing_trace(step: gs.FlowStep, grb_file: Path, groups: dict):
    """Return the backward trace of groups with face-to-face routing (experimental, DIS only)."""
    from gwsource.experimental import face_routing

    delr, delc = face_routing.read_dis_spacing(str(grb_file))
    return face_routing.route_backward(step, groups, delr, delc)


# ---------------------------------------------------------------- PEST++ IES history matching
#
# The PEST++ forward run is a plain Python script, forward_run.py, written into the template
# folder. It is built from the three self-contained functions below (imports inside, settings
# passed as arguments), as pyemu's add_py_function does, so it does not import this module.


def pestpp_exe(bin_dir: Path, name: str = "pestpp-ies") -> Path:
    """Return bin_dir/<name>; if it is missing, install PEST++ there with pyemu's get_pestpp."""
    suffix = ".exe" if sys.platform.startswith("win") else ""
    exe = Path(bin_dir) / f"{name}{suffix}"
    if not exe.is_file():
        from pyemu.utils.get_pestpp import run_main

        downloads_dir = Path(tempfile.gettempdir()) / "gwsource_downloads"  # not ~/Downloads
        downloads_dir.mkdir(parents=True, exist_ok=True)
        run_main(bindir=str(bin_dir), downloads_dir=str(downloads_dir), quiet=True)
    assert exe.is_file(), f"{exe} not found after get_pestpp"
    return exe


def observation_cells(spec, n_obs: int, seed: int) -> list[tuple[int, int]]:
    """Return n_obs random (row, col) cells, away from the constant heads, river and wells."""
    blocked = {(r, 0) for r in range(spec.nrow)} | {(r, spec.riv_col) for r in range(spec.nrow)}
    blocked |= {rc for _, rc, _ in spec.wells}
    cells = [(r, c) for r in range(spec.nrow) for c in range(spec.ncol) if (r, c) not in blocked]
    picks = np.random.default_rng(seed).choice(len(cells), size=n_obs, replace=False)
    return [cells[i] for i in sorted(picks)]


def observed_heads(head_file: Path, nodes: list[int], noise_sd: float, seed: int) -> np.ndarray:
    """Return the heads at the given nodes plus Gaussian measurement noise (synthetic data)."""
    import flopy

    heads = flopy.utils.HeadFile(str(head_file)).get_data().ravel()[nodes]
    return heads + np.random.default_rng(seed).normal(0.0, noise_sd, len(nodes))


def pilot_point_cells(spec, spacing: int) -> list[tuple[int, int]]:
    """Return the (row, col) cells of a regular pilot-point grid, spacing cells apart."""
    first = spacing // 2
    return [
        (r, c) for r in range(first, spec.nrow, spacing) for c in range(first, spec.ncol, spacing)
    ]


def gaussian_correlation(xy_a: np.ndarray, xy_b: np.ndarray, length: float) -> np.ndarray:
    """Return the correlation exp(-(r / length)^2) between two sets of points."""
    distance = np.hypot(xy_a[:, None, 0] - xy_b[None, :, 0], xy_a[:, None, 1] - xy_b[None, :, 1])
    return np.exp(-((distance / length) ** 2))


def pilot_point_covariance(spec, pp_cells: list, length: float, nugget: float) -> np.ndarray:
    """Return the correlation matrix of z at the pilot points (plus a small nugget)."""
    xy = np.array([spec.xy(rc) for rc in pp_cells])
    return gaussian_correlation(xy, xy, length) + nugget * np.eye(len(pp_cells))


def kriging_weights(spec, pp_cells: list, length: float, nugget: float) -> np.ndarray:
    """Return simple-kriging weights (nrow, ncol, n_pp) from the pilot points to every cell."""
    pp_xy = np.array([spec.xy(rc) for rc in pp_cells])
    cell_xy = np.array([spec.xy((r, c)) for r in range(spec.nrow) for c in range(spec.ncol)])
    c_pp = pilot_point_covariance(spec, pp_cells, length, nugget)
    c_cp = gaussian_correlation(cell_xy, pp_xy, length)
    weights = np.linalg.solve(c_pp, c_cp.T).T
    return weights.reshape(spec.nrow, spec.ncol, len(pp_cells))


def draw_prior(
    cov: np.ndarray, mean_k: float, sigma_lnk: float, n_real: int, seed: int
) -> np.ndarray:
    """Return (n_real, n_pp) pilot-point K values, K = mean_k exp(sigma_lnk z), z ~ N(0, cov)."""
    chol = np.linalg.cholesky(cov)
    z = np.random.default_rng(seed).standard_normal((n_real, len(cov))) @ chol.T
    return mean_k * np.exp(sigma_lnk * z)


def write_k_array(ws: str = ".", mean_k: float = 5.0) -> None:
    """Forward-run step 1: krige ln K from pilot_points.dat and write the K array to k.txt."""
    import os

    import numpy as np

    values = np.loadtxt(os.path.join(ws, "pilot_points.dat"), usecols=1, ndmin=1)
    weights = np.load(os.path.join(ws, "kriging_weights.npy"))
    ln_k = np.log(mean_k) + weights @ (np.log(values) - np.log(mean_k))
    np.savetxt(os.path.join(ws, "k.txt"), np.exp(ln_k), fmt="%.8e")


def run_mf6(ws: str = ".", exe: str = "./mf6") -> None:
    """Forward-run step 2: run MODFLOW 6 in ws and check for normal termination."""
    import os
    import subprocess

    subprocess.run([exe], cwd=ws, check=True, capture_output=True)
    with open(os.path.join(ws, "mfsim.lst")) as handle:
        assert "Normal termination" in handle.read(), "MF6 did not terminate normally"


def write_head_observations(ws: str = ".", head_file: str = "quickstart.hds") -> None:
    """Forward-run step 3: write the heads at the cells of obs_cells.csv to heads.csv.

    Reads the first record of the MF6 head file (the only one of a steady one-layer model).
    """
    import os

    import numpy as np

    header = np.dtype([
        ("kstp", "<i4"), ("kper", "<i4"), ("pertim", "<f8"), ("totim", "<f8"),
        ("text", "S16"), ("ncol", "<i4"), ("nrow", "<i4"), ("ilay", "<i4"),
    ])
    with open(os.path.join(ws, head_file), "rb") as handle:
        info = np.fromfile(handle, dtype=header, count=1)[0]
        heads = np.fromfile(handle, dtype="<f8", count=int(info["ncol"]) * int(info["nrow"]))
    names = np.loadtxt(os.path.join(ws, "obs_cells.csv"), delimiter=",", skiprows=1,
                       usecols=0, dtype=str, ndmin=1)
    nodes = np.loadtxt(os.path.join(ws, "obs_cells.csv"), delimiter=",", skiprows=1,
                       usecols=1, dtype=int, ndmin=1)
    with open(os.path.join(ws, "heads.csv"), "w") as handle:
        handle.write("name,head\n")
        for name, node in zip(names, nodes):
            handle.write(f"{name},{heads[node]:.10e}\n")


FORWARD_RUN_FUNCTIONS = (write_k_array, run_mf6, write_head_observations)


def write_forward_run(template_ws: Path, mean_k: float) -> None:
    """Write forward_run.py (the three forward-run functions and a main block) into template_ws."""
    source = "\n\n".join(inspect.getsource(func) for func in FORWARD_RUN_FUNCTIONS)
    main = (
        'if __name__ == "__main__":\n'
        f'    write_k_array(".", mean_k={mean_k!r})\n'
        '    run_mf6(".", "./mf6")\n'
        '    write_head_observations(".", "quickstart.hds")\n'
    )
    (Path(template_ws) / "forward_run.py").write_text(f"{source}\n\n{main}")


def par_name(i: int) -> str:
    """Return the PEST parameter name of pilot point i."""
    return f"pp_{i:03d}"


def obs_name(i: int) -> str:
    """Return the PEST observation name of head observation i."""
    return f"h_{i:02d}"


def write_pilot_points(ws: Path, values: np.ndarray) -> None:
    """Write pilot_points.dat (name, K) as the PEST template would."""
    lines = [f"{par_name(i)} {v:.10e}" for i, v in enumerate(values)]
    (Path(ws) / "pilot_points.dat").write_text("\n".join(lines) + "\n")


def write_pest_io_files(template_ws: Path, n_pp: int, n_obs: int) -> None:
    """Write the PEST template (pilot_points.dat.tpl) and instruction (heads.csv.ins) files."""
    tpl = ["ptf ~"] + [f"{par_name(i)} ~ {par_name(i):^14} ~" for i in range(n_pp)]
    (Path(template_ws) / "pilot_points.dat.tpl").write_text("\n".join(tpl) + "\n")
    ins = ["pif ~", "l1"] + [f"l1 ~,~ !{obs_name(i)}!" for i in range(n_obs)]
    (Path(template_ws) / "heads.csv.ins").write_text("\n".join(ins) + "\n")


def build_kriged_model(
    model_ws: Path, mf6: Path, spec, weights: np.ndarray, mean_k: float
) -> Path:
    """Build the quickstart model with K read from k.txt, kriged from pilot points; run it once.

    The folder holds the kriging weights and a copy of MF6, so that run_parameter_ensemble and
    the PEST++ forward run can rerun it with new pilot-point values. It starts at K = mean_k.
    """
    import herebedragons as hbd

    run = hbd.build_quickstart(model_ws, mf6, spec)
    run.gwf.npf.k.store_as_external_file("k.txt")
    run.sim.write_simulation(silent=True)
    shutil.copy2(mf6, model_ws / mf6.name)
    np.save(model_ws / "kriging_weights.npy", weights)
    write_pilot_points(model_ws, np.full(weights.shape[-1], mean_k))
    write_k_array(str(model_ws), mean_k)
    run_mf6(str(model_ws), f"./{mf6.name}")
    return model_ws


def build_pest_template(
    template_ws: Path,
    mf6: Path,
    spec,
    pp_cells: list,
    weights: np.ndarray,
    obs_cells: list,
    mean_k: float,
) -> Path:
    """Build the kriged model and add the PEST files (template, instructions, forward run)."""
    build_kriged_model(template_ws, mf6, spec, weights, mean_k)
    lines = ["name,node"] + [f"{obs_name(i)},{spec.node(rc)}" for i, rc in enumerate(obs_cells)]
    (template_ws / "obs_cells.csv").write_text("\n".join(lines) + "\n")
    write_pest_io_files(template_ws, len(pp_cells), len(obs_cells))
    write_forward_run(template_ws, mean_k)
    write_head_observations(str(template_ws))
    return template_ws


def build_pst(
    template_ws: Path,
    observed: np.ndarray,
    noise_sd: float,
    mean_k: float,
    k_bounds: tuple[float, float],
    pestpp_options: dict,
    noptmax: int,
    case: str = "case",
):
    """Write <case>.pst in template_ws: log-K pilot points, head observations weighted 1/noise_sd."""
    import pyemu

    ws = Path(template_ws)
    pst = pyemu.Pst.from_io_files(
        str(ws / "pilot_points.dat.tpl"), str(ws / "pilot_points.dat"),
        str(ws / "heads.csv.ins"), str(ws / "heads.csv"), pst_path=".",
    )
    par = pst.parameter_data
    par.loc[:, "partrans"] = "log"
    par.loc[:, "parval1"] = mean_k
    par.loc[:, "parlbnd"], par.loc[:, "parubnd"] = k_bounds
    par.loc[:, "pargp"] = "pp"
    obs = pst.observation_data
    names = [obs_name(i) for i in range(len(observed))]
    obs.loc[names, "obsval"] = observed
    obs.loc[names, "weight"] = 1.0 / noise_sd
    obs.loc[names, "obgnme"] = "heads"
    obs.loc[names, "standard_deviation"] = noise_sd  # IES draws the observation noise from this
    pst.model_command = ["python forward_run.py"]  # run_ies puts this Python first on the PATH
    pst.control_data.noptmax = noptmax
    pst.pestpp_options.update(pestpp_options)
    pst.write(str(ws / f"{case}.pst"), version=2)
    return pst


def prior_frame(values: np.ndarray) -> pd.DataFrame:
    """Return a parameter ensemble as a table: one row per realisation, one column per pilot point."""
    columns = [par_name(i) for i in range(values.shape[1])]
    return pd.DataFrame(values, columns=columns, index=pd.Index(range(len(values)), name="real"))


def write_prior(template_ws: Path, values: np.ndarray, file_name: str = "prior.csv") -> None:
    """Write the prior parameter ensemble (one row per realisation, one column per pilot point)."""
    prior_frame(values).to_csv(Path(template_ws) / file_name)


def run_ies(
    template_ws: Path, pestpp: Path, pst_name: str, n_workers: int, master_ws: Path
) -> Path:
    """Run pestpp-ies with n_workers local workers (pyemu.os_utils.start_workers); return master_ws.

    The workers talk to the master over local TCP ports. n_workers=0 runs PEST++ serially in
    master_ws instead, without workers or ports (much slower). pyemu's progress messages (the
    reserved port, "still running" every 5 s) go to start_workers.log next to master_ws, not to
    the notebook. PEST++ errors still reach stderr.
    """
    import pyemu

    shutil.copy2(pestpp, Path(template_ws) / pestpp.name)
    with python_first_on_path():
        if n_workers == 0:
            shutil.rmtree(master_ws, ignore_errors=True)
            shutil.copytree(template_ws, master_ws)
            subprocess.run([f"./{pestpp.name}", pst_name], cwd=master_ws, check=True,
                           capture_output=True)
        else:
            port = pyemu.os_utils.PortManager(log_level=logging.WARNING).get_available_port()
            log_file = Path(master_ws).parent / "start_workers.log"
            with open(log_file, "w") as log, redirect_stdout(log):
                pyemu.os_utils.start_workers(
                    str(template_ws), pestpp.name, pst_name, num_workers=n_workers,
                    worker_root=str(Path(master_ws).parent), master_dir=str(master_ws),
                    port=port, silent_master=True,
                )
    return Path(master_ws)


@contextmanager
def python_first_on_path():
    """Put this Python's folder first on the PATH while PEST++ runs "python forward_run.py"."""
    old = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), old])
    try:
        yield
    finally:
        os.environ["PATH"] = old


def last_iteration(master_ws: Path, case: str = "case") -> int:
    """Return the last iteration for which PEST++ IES wrote a parameter ensemble."""
    iterations = [int(p.name.split(".")[1]) for p in Path(master_ws).glob(f"{case}.*.par.csv")]
    assert iterations, f"no {case}.*.par.csv in {master_ws}"
    return max(iterations)


def read_par_ensemble(master_ws: Path, iteration: int, case: str = "case") -> pd.DataFrame:
    """Return the parameter ensemble of one iteration (0 = prior) as K values."""
    frame = pd.read_csv(Path(master_ws) / f"{case}.{iteration}.par.csv", index_col=0)
    frame.columns = frame.columns.str.lower()
    return frame


def read_phi(master_ws: Path, case: str = "case") -> pd.DataFrame:
    """Return the measurement objective function per iteration (mean, min, max over realisations)."""
    phi = pd.read_csv(Path(master_ws) / f"{case}.phi.actual.csv", index_col=0)
    return phi[["total_runs", "mean", "standard_deviation", "min", "max"]]


def run_parameter_ensemble(
    model_ws: Path, root: Path, ensemble: pd.DataFrame, mf6: Path, mean_k: float
) -> list[Path]:
    """Run every realisation of a parameter ensemble in root/real_000, ...; return the folders.

    model_ws is the kriged model (build_kriged_model) or the PEST template built on it.
    """
    skip = shutil.ignore_patterns(
        "mf6", "mf6.exe", "pestpp-ies*", "*.pst", "*.csv.ins", "*.tpl", "prior.csv"
    )
    folders = []
    for real, values in ensemble.iterrows():
        name = f"{real:03d}" if isinstance(real, (int, np.integer)) else str(real)
        ws = Path(root) / f"real_{name}"
        shutil.copytree(model_ws, ws, ignore=skip, dirs_exist_ok=True)
        write_pilot_points(ws, values.to_numpy())
        write_k_array(str(ws), mean_k)
        run_mf6(str(ws), str(mf6))
        folders.append(ws)
    return folders


def capture_probability_summary(
    ens: gs.EnsembleResult, table: pd.DataFrame, area: np.ndarray, group: str
) -> dict[str, float]:
    """Return the areas of P(F > 0.5) classes [km2] and the spread of the river share."""
    prob = ens.exceedance[0.5]["fraction_through"][group]
    river = table["share RIV"] if "share RIV" in table else pd.Series(0.0, index=table.index)
    return {
        "realisations": len(table),
        "area P >= 0.5 (km2)": float(area[prob >= 0.5].sum()) / 1e6,
        "area P >= 0.9 (km2)": float(area[prob >= 0.9].sum()) / 1e6,
        "band 0.1 < P < 0.9 (km2)": float(area[(prob > 0.1) & (prob < 0.9)].sum()) / 1e6,
        "river share 5 %": river.quantile(0.05),
        "river share median": river.median(),
        "river share 95 %": river.quantile(0.95),
        "river share min": river.min(),
        "river share max": river.max(),
    }


def truth_overlap(prob: np.ndarray, truth_fraction: np.ndarray, area: np.ndarray) -> dict[str, float]:
    """Compare a capture probability map with the true zone F > 0.5 (synthetic test only)."""
    zone = truth_fraction > 0.5
    core = prob >= 0.9
    return {
        "true zone with P >= 0.5 (%)": 100.0 * area[zone & (prob >= 0.5)].sum() / area[zone].sum(),
        "true zone with P < 0.1 (km2)": float(area[zone & (prob < 0.1)].sum()) / 1e6,
        "area P >= 0.9 inside the true zone (%)": 100.0 * area[zone & core].sum() / area[core].sum(),
    }
