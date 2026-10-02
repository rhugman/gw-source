# gwsource tutorials

Jupyter notebooks that teach cell-mixing flow tracing with `gwsource`, from a first capture zone to transient tracking and parameter ensembles. Each notebook builds its own small MODFLOW 6 model, runs in under about two minutes, and is committed with its outputs so it reads on GitHub without running it.

## Setup and launch

1. Create the environment and download MODFLOW 6 into `bin/` (once; see the [main README](../README.md)):

   ```bash
   scripts/setup_env.sh
   ```

   The `gw-source` environment includes JupyterLab and the notebook tools (`environment.yml`). To add them to an existing environment: `mamba install -n gw-source -c conda-forge jupyterlab ipykernel nbclient nbformat nbconvert`.

2. Launch JupyterLab from the repository root:

   ```bash
   mamba activate gw-source
   jupyter lab tutorials/
   ```

3. Open a notebook and run all cells. Model workspaces are written to `tutorials/_work/<tutorial>/` (git-ignored; safe to delete).

The notebooks share the model builders and plotting helpers in [`herebedragons.py`](herebedragons.py); the notebooks themselves are the narrative. To check that every notebook still runs: `pytest -m tutorials` (deselected from the default test run).

## Order

Start with 01 and 02: they introduce the outputs and the accounting that every later tutorial uses. After that, 03 to 09 can be read in any order; the list below is the suggested one.

| # | Tutorial | What it answers | What you learn | Runtime |
|---|---|---|---|---|
| 01 | [Quickstart](01_quickstart/01_quickstart.ipynb) | Where does the water pumped by a well come from? | Build and run a model, read a step, select a well, backward trace; fraction through and the F = 0.1 / 0.5 capture-zone contours; volume through and volume from; the split by source (recharge, river, boundary); the closure check; npz and netCDF export | ~10 s |
| 02 | Accounting *(planned)* | What exactly is being computed? | Full mixing; gross vs net mode; weak sinks; the Foley & Black (2013) 3×3 worked example on a hand-built graph; closure, duality and residual diagnostics; boundary-control maps (fractions to every sink sum to 1) | < 1 min |
| 03 | Forward mode *(planned)* | Where does the water from a source go, and how much of it is in each well? | Source fractions (river water and recharge in wells), dilution ratio, volume to; forward/backward duality | < 1 min |
| 04 | Grids *(planned)* | Does it work on my grid? | DISV (Voronoi) and DISU grids; XT3D and flow cycles, the cycle report; zone and boundname selectors; GeoPackage and netCDF export | < 1 min |
| 05 | Transient snapshots *(planned)* | How does the capture zone change through the seasons? | Time steps as snapshots; min/max/mean, always/sometimes/never, probability within a range, exceedance; time vs equal weighting; storage as a source | < 1 min |
| 06 | Travel time *(planned)* | How old is the water reaching the well? | Eulerian mean travel time and the volume identity; comparison with MF6 PRT flux-weighted particles; time-of-travel zones | < 2 min |
| 07 | Networks and multi-model *(planned)* | What if water moves through streams, drains or wells between layers, or across models? | Package networks (SFR with MVR routing, MAW across layers); multi-model simulations (a split model gives the same answer) | < 1 min |
| 08 | Transient tracking *(planned)* | How much of the well water arrived since pumping started? | True transient tracking through storage, forward and backward (adjoint); volume modes "flow" vs "gwt"; tagged initial water; comparison with MF6 GWT; sub-stepping | < 2 min |
| 09 | Ensembles *(planned)* | How sure are we about the capture zone? | Capture probability across random-K realisations; quantiles; parallel runs; how this plugs into a PEST++ IES workflow (described, not run) | < 2 min |

Thresholds on the fraction through, and the numerical dispersion of full mixing, are discussed in [`docs/dispersion_study.md`](../docs/dispersion_study.md). The method and equations are in [`PLAN.md`](../PLAN.md).

## The tutorial models

All models share one plan: a 2 km × 2 km unconfined aquifer in 50 m cells with recharge, a constant-head west edge (regional inflow), a north–south river and a supply well next to it. `herebedragons.py` builds variants of it:

| Builder | Model |
|---|---|
| `build_quickstart` | steady, one layer (tutorial 01) |
| `build_layered` | three layers, partially penetrating supply well and a weak-sink well |
| `build_voronoi`, `build_disu` | DISV Voronoi grid; DISU copy with or without vertices |
| `build_xt3d` | heterogeneous anisotropic K with XT3D (flow cycles) |
| `build_transient` | storage, seasonal recharge and pumping |
| `build_stream_mover` | SFR stream fed by drains through the water mover, leaking back to the aquifer |
| `build_maw` | three layers with a multi-aquifer well that moves water between layers |
| `build_realisation`, `build_ensemble` | seeded random log-K realisations |
