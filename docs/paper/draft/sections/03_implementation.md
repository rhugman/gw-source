# 3. Implementation

## 3.1 MODFLOW 6 output, package networks and multi-model simulations

The code reads MODFLOW 6 output files only (Langevin et al. 2017). The cell connections come from the binary grid file, whose connection arrays (IA, JA) take the same form for DIS, DISV and DISU grids, so the matrices and the solve do not depend on grid type. A package that hands water to the water mover (MVR) writes two records per boundary, for example DRN and DRN-TO-MVR; both are kept as sink terms, because the cell budget closes only with both. The flow model needs SAVE_FLOWS in NPF, STO and every stress package, and BUDGET SAVE in OC for the steps to be traced.

Package networks are read from each advanced package's own budget file. SFR reaches, lakes, MAW wells and UZF cells become extra cells, joined to the aquifer by their exchange flows and to each other by stream routing, lake outlets and MVR transfers. The code first checks that the GWF and package budgets agree on each aquifer exchange, by default to 10⁻⁴ of the package's largest exchange. <!-- network.py, packages.py; PLAN Phase 4A notes (aquifer exchange tolerance, AQUIFER_RTOL = 1e-4) --> Models joined by GWF-GWF exchanges are read as one system, and the solve and checks of §2 apply unchanged.

## 3.2 Selections, outputs, sub-steps and particle tracking

Destinations and sources are selected by package, boundname, cells or zone, again on every time step. Results go to npz, netCDF or GeoPackage files, and an ensemble routine traces each realisation in turn and keeps statistics per cell. For transient tracking, each flow step can be split into m equal transport sub-steps, with flows held constant and water volumes interpolated, without changing the flow model (§4.3).

A post-processing routine for MODFLOW 6 particle tracking (PRT) [check: PRT documentation] uses flow-weighted release: particles start from every source term, each carrying a weight proportional to that term's flow, on the face given by IFLOWFACE (the cell face a boundary flow is assigned to) where set. In every cell they pass, weight-losing particles lose weight to each sink in proportion to the flow that sink takes from the cell's outflow, the particle analogue of gross accounting (§2.3).

## 3.3 Cost

On a synthetic three-dimensional grid of one million cells without flow loops, the solve for four destination groups took 0.55 s, plus 0.24 s to assemble the matrices; with 7,000 flow loops added (the largest of 649 cells) the solve took 0.42 s (one desktop computer, 16 cores). <!-- PLAN Phase 2 notes (Benchmarks); benchmarks/bench_solver.py --> Memory limits the number of groups: each costs about 90 MB per million cells, so thousands of wells are grouped by package, boundname or zone, or traced in batches. <!-- PLAN Phase 2 notes (Memory limit) --> On the 1.68-million-cell Neversink model a trace takes seconds (§5.1). <!-- NS §1 (1,683,680 cells), Summary -->

Transient tracking factorises each step's matrix once for all tagged groups. On tutorial 08 (1,600 cells, 121 steps; §4.4), with one transport step per flow step, it took 0.75 s forward and 0.80 s backward. <!-- tutorial 08 §§3, 5 --> Memory is one array of time steps × cells per group and output (§7). There is no timing yet on a large transient model [check].
