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

Start with 01 and 02: they introduce the outputs and the accounting that every later tutorial uses. After that, 03 to 10 can be read in any order; the list below is the suggested one.

| # | Tutorial | What it answers | What you learn | Runtime |
|---|---|---|---|---|
| 01 | [Quickstart](01_quickstart/01_quickstart.ipynb) | Where does the water pumped by a well come from? | Build and run a model, read a step, select a well, backward trace; fraction through and the F > 0.1 and F > 0.5 capture zones; volume through and volume from; the split by source (recharge, river, boundary); the closure check; F against flow-weighted MF6 PRT particles (zone areas, mean \|P − F\|); npz and netCDF export | ~5 s |
| 02 | [Accounting](02_accounting/02_accounting.ipynb) | What exactly is being computed? | Full mixing and the linear system; the Foley & Black (2013) 3×3 worked example rebuilt by hand (net accounting, exact match); gross vs net accounting on a weak-sink well (net attributes 6.7× the pumping); residual, closure and duality diagnostics; boundary-control and dominant-sink maps | ~5 s |
| 03 | [Forward mode](03_forward/03_forward.ipynb) | Where does the water in each cell, and in the well, come from? | Source fractions of river water, regional inflow and recharge; the well's water by source; source fraction as dilution ratio C/C0 and mixing of source concentrations; volume to by sink; a recharge zone (hypothetical fertilised field) reaching the well; forward/backward duality; agreement with MF6 GWT at equilibrium (≤ 4.2e-13) | ~5 s |
| 04 | [Grids](04_grids/04_grids.ipynb) | Does it work on my grid? | The same trace code on DIS, Voronoi DISV and DISU (with and without vertices); DIS = DISU exactly, DISV close; what DISU without vertices can and cannot do; XT3D flow loops, the loop report and the exact block solver; boundname and zone-array selectors; GeoPackage and netCDF export | ~10 s |
| 05 | [Transient snapshots](05_transient_snapshots/05_transient_snapshots.ipynb) | How does the capture zone change through the seasons? | Time steps as snapshots and their limits (no travel lag, storage as source/sink); the well's water by source per step; min/max/mean F, always/sometimes/never, exceedance count, probability of volume through > 1 m³/d; time vs equal weighting; one way to combine the maps into nested zones | ~10 s |
| 06 | [Travel time](06_travel_time/06_travel_time.ipynb) | How old is the water reaching the well? | Porosity as an explicit input; Eulerian mean travel time and time-of-travel zones; the exact volume identity ΣVF/Q; weight-losing, flow-weighted MF6 PRT particles: overall agreement (largely the volume identity), per-cell differences and why; when to use particles vs Eulerian times | ~10 s |
| 07 | [Networks and multi-model](07_networks_multimodel/07_networks_multimodel.ipynb) | What if water moves through streams, drains or wells between layers, or across models? | Cells-only vs package-node traces; SFR reaches and MVR transfers as nodes and edges (drain → mover → stream → aquifer → well); MAW borehole across layers; a split simulation matches the single model; required save options and limitations | ~3 s |
| 08 | [Transient tracking](08_transient_tracking/08_transient_tracking.ipynb) | How much of the well water arrived since the simulation started? | Why snapshots are not transport; forward tracking of tagged sources and initial water; backward (adjoint) fate maps and closure; duality; volume modes "gwt" vs "flow"; agreement with MF6 GWT; four transport sub-steps per flow step, and why (early arrival) | ~15 s |
| 09 | [Ensembles](09_ensembles/09_ensembles.ipynb) | How sure are we about the capture zone? | 20 random-K realisations; capture probability P(F > 0.1) and P(F > 0.5); mean and quantile maps; spread of the well's source shares; exact vs histogram quantiles and the memory budget; serial vs parallel runs; parameter spread vs full mixing and face routing; a PEST++ IES history match (100 pilot points, 40 heads, run with local workers) and the prior vs posterior capture probability and river share | ~1.5 min |
| 10 | [Unit concentration](10_unit_concentration/10_unit_concentration.ipynb) | Does tracking reproduce a published unit-concentration study? | The Bedekar et al. (2024) example rebuilt in MF6 and the values the paper leaves open; well shares of lateral inflow, recharge, stream and stored water over 25 years; agreement with four MF6 GWT unit-concentration runs (≤ 1.5e-10) and with the paper's Figure 2 (≤ 1.3 percentage points); the steady long-time limit; transport sub-steps and arrival fronts; backward time-limited contributing areas and where the pumped recharge and stream water entered | ~2.5 min |

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

Tutorial 10 does not use this plan. It rebuilds the published model of Bedekar et al. (2024) with its own builder, `build_bedekar` in [`10_unit_concentration/helpers.py`](10_unit_concentration/helpers.py): 101 × 101 cells of 10 m in three layers, lateral inflow on the west edge, a stream on the east edge and a well pumping 700 m³/d from year 0.
