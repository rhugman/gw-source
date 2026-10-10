# 3. Implementation

## 3.1 MODFLOW 6 output, package networks and multi-model simulations

The code reads only MODFLOW 6 output (Langevin et al. 2017): the binary grid file, which stores cell connections in the same form for structured (DIS), vertex (DISV) and unstructured (DISU) grids, and the GWF budget files, saved with SAVE_FLOWS and BUDGET SAVE. A package that passes water to the water mover (MVR) writes two records per boundary (e.g. DRN and DRN-TO-MVR); both are kept, because the cell budget closes only with both. SFR reaches, lakes (LAK), multi-aquifer wells (MAW) and unsaturated-zone cells (UZF) can be added as extra cells from their packages' budget files. The code first checks that the GWF and package budgets agree on each aquifer exchange, by default to 1 × 10⁻⁴ of the largest exchange. <!-- network.py, packages.py; PLAN Phase 4A notes (AQUIFER_RTOL = 1e-4) --> GWF models joined by exchanges are read as one system.

## 3.2 Selections, outputs, sub-steps and particle tracking

Destinations and sources are selected by package, boundname, cells or zone, per time step. Snapshots (§2.7) keep running statistics per cell (extremes, time-weighted means, threshold counts). <!-- src/gwsource/transient.py docstring (TransientConfig statistics) --> Results are written as NumPy (npz), netCDF or GeoPackage files, and ensembles are traced realisation by realisation, with per-cell statistics. Each flow step can be split into m equal transport sub-steps, with the flows held constant and the water volumes interpolated (§4.4).

For MODFLOW 6 particle tracking (PRT) [check: PRT documentation], the code writes flow-weighted release points: particles start from every source term with a weight proportional to its flow, on the face given by IFLOWFACE (the cell face a boundary flow is assigned to) where the package sets it. Weight-losing particles lose weight to each sink they pass, in proportion to the sink's share of the cell's outflow: the particle analogue of gross accounting (§2.3).

## 3.3 Cost

A steady trace of nine groups on the 1.68-million-cell Neversink model took 2–3 s (§5.1). <!-- NS Summary, §1 --> On a synthetic grid of one million cells, a trace of four groups took about 1.1 s, of which 0.55 s was solving the equations; with 7,000 flow loops added, solving took 0.42 s (desktop computer, 64 GB). <!-- PLAN Phase 2 notes (Benchmarks: assembly 0.24, components 0.10, closed-loop check 0.10, solve 0.55, metrics 0.11 s; sum 1.10 s; largest loop 649 cells); benchmarks/bench_solver.py --> Each group costs about 90 MB of memory per million cells, so 100 wells traced separately on 1.68 million cells would need about 15 GB; wells are best grouped or traced in batches. <!-- PLAN Phase 2 notes (Memory limit); estimate 90 MB × 1.68 × 100 = 15 GB, not run -->

Transient tracking has been timed only on tutorial 08 (1,600 cells, 121 steps; §4.4) [check]: 0.75 s forward and 0.80 s backward, with one transport step per flow step. <!-- tutorial 08 §§3, 5 --> Its memory grows with the number of time steps (§7).
