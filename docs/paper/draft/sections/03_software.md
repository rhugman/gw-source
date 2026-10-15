# 3. The software

The method of Section 2 is implemented in `gwsource`, an open-source Python package (MIT licence) that works on the output of a MODFLOW 6 run. This section describes how the package is used, what it reads and what it returns. Table 1 lists its inputs, selections and outputs, each with the example in Section 4 that shows it.

[[Table 1]]

## 3.1 Workflow

In a typical session, the user runs MODFLOW 6 with the flows saved and reads one time step of the flows into Python. The user then selects the destinations or sources and traces them. The trace returns the outputs with their budget checks, ready to export for mapping. The lines below trace the well of Section 4.1 back to its sources. <!-- evidence: tutorials/01_quickstart (same calls); run on the quickstart model on 2026-10-15: volume from by package RCH 568.6, CHD 118.1, RIV 113.3 m³/d, closure relative error 0.0, netCDF and GeoPackage written -->

```python
import gwsource as gs

step = gs.read_step("model", boundnames=True)       # grid and flows of one time step
well = gs.select(step, boundnames=["supply_well"])   # the destination
res = gs.backward(step, {"supply_well": well})       # backward trace
F = res.fraction_through["supply_well"]              # F in every cell
by_source = {p: v.sum() for p, v in res.volume_from_by_term["supply_well"].items()}
check = gs.diagnostics.backward_closure(step, res, "supply_well")
print(by_source, check.relative_error)               # m3/d by package; closure check
gs.export.to_netcdf("supply_well.nc", step, res)
gs.export.to_geopackage("supply_well.gpkg", step, res)
```

A forward trace from a source uses `gs.forward` in the same way. Transient snapshots, transient tracking and ensembles have functions of their own that take the same selections (Table 1).

## 3.2 Inputs and selections

The code reads MODFLOW 6 output, not the model's input files. It needs the binary grid file and the budget file of the Groundwater Flow (GWF) model, on any grid type. The flows are saved with the SAVE_FLOWS option in each package and with the budget saved in the Output Control file. Transient tracking needs the budget of every time step (SAVE BUDGET ALL). Travel times need the saturated thickness of each cell, taken from the saturation saved by the Node Property Flow package or from the head file. <!-- evidence: src/gwsource/mf6io.py module docstring (grb and cbc; DATA-SAT from NPF SAVE_SATURATION, else heads); src/gwsource/traveltime.py water_volume assertions -->

Where a package passes water to the water mover (MVR), the code reads both of its budget records. A budget term that is not read shows up as a large cell budget error. Stream reaches (SFR), lakes (LAK), multi-aquifer wells (MAW) and unsaturated-zone cells (UZF) can be added as extra cells from their own budget files. Water is then traced along streams and through lakes and wells. The code checks that the budget of each such package agrees with the aquifer budget. GWF models joined by exchanges are read as one system. <!-- evidence: src/gwsource/mf6io.py docstring (mover records); src/gwsource/network.py open_simulation (package_nodes need BUDGET FILEOUT, MVR too; aquifer_rtol = AQUIFER_RTOL = 1e-4) -->

Destinations and sources can be chosen by package, by boundary number, by boundname, by cells or by a zone array. They can be combined, for example to trace the recharge on one zone forward as one source (Section 4.3). Any number of groups can be traced together. Boundnames are read from the package input files, because the budget file does not hold them. <!-- evidence: src/gwsource/selectors.py (select: package, bounds, boundnames, cells, term, model; select_zone; groups_by_package, groups_by_boundname, groups_by_zone; boundnames need read_step(boundnames=True)) -->

## 3.3 Outputs

A trace of one time step gives $F$ or $G$ in every cell, the volumes of Section 2.3 and their split by package. Given a porosity, it also gives mean travel times. Snapshots give statistics over the time steps, such as the minimum, mean and maximum $F$ in each cell. Transient tracking gives the tagged fractions $c$ and $w$ in each step. It also splits a destination's water by source and by time step. An ensemble trace gives, for each cell, the mean, the probability that $F$ exceeds a threshold and quantiles over the realisations. Quantiles can be exact or taken from histograms. Histograms keep the memory bounded for large ensembles (Section 4.9). Outputs export to NumPy files, to netCDF files with units and a record of the model files and options, and to GeoPackage polygons for GIS. The code can also write release points for MODFLOW 6 particle tracking (PRT), so that full mixing and particles can be compared on the same flows (Section 4.6). <!-- evidence: src/gwsource/transient.py (TransientConfig statistics); src/gwsource/tracking.py; src/gwsource/ensemble.py (EnsembleConfig thresholds, quantiles, memory_budget, histogram_bins); src/gwsource/export.py (save_npz, to_netcdf with provenance, to_geopackage); src/gwsource/prt.py (release_points, write_prt) -->

## 3.4 Cost and testing

Cost decides whether a trace can be repeated for every realisation of an ensemble. On the Neversink model of Section 5, with 1.68 million cells, one steady-state trace of nine destination groups took 2–3 s. About 1 s of this was reading the budget file. Memory use peaked at 2.5 GB (Apple M4 Max, 64 GB). Each further group added about 0.19 GB. Wells can be traced in batches on smaller machines. <!-- evidence: reviews/r4_memory.md (load 1.0 to 1.2 s, load plus trace 2.4 to 2.7 s; peak RSS 2.52 GB, nine groups; one group 0.98 GB; (2.52 − 0.98) / 8 = 0.19 GB per group); NS Summary, §1 --> <!-- left out (outline §3.3): the 1-million-cell synthetic benchmark (0.55 s for four groups), PLAN Phase 2 notes; not rerun --> In a PEST++ workflow, the trace could run at the end of each forward run. We have not tested it under the PEST++ run manager [check]. <!-- PEST++ forward-run use untested; outline §3.4 item 4.9 decides to run the PEST++ section of the ensemble example -->

The package comes with automated tests on ten small test models and on the worked example of Foley and Black (2013). The tests run the budget checks of Section 2.5. They also compare the results with MODFLOW 6 GWT and PRT, between grid types, and between one model and the same model split into several ({SI: verification on the test models}). <!-- evidence: tests/ (test_models_run.py, test_closure_duality.py, test_fb13_example.py, test_gwt_equilibrium.py, test_prt.py, test_multimodel.py, test_tracking_mf6.py); previous/04_verification.md §4.1 (ten test models) -->
