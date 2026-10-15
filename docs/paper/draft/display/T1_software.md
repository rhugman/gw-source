## Table 1

**Table 1.** What the code reads, how destinations and sources are chosen, and what it returns. The last column gives the worked example in Section 4 that shows each item. MODFLOW 6 option names are given where a user must set them. <!-- evidence: src/gwsource (mf6io.py, network.py, selectors.py, metrics.py, traveltime.py, transient.py, tracking.py, ensemble.py, export.py, prt.py); tutorials 01–10 (calls used in each); docs/paper/outline.md §3.4 (example numbering) -->

| | Item | What it is or needs | Shown in |
|---|---|---|---|
| **Inputs** | Binary grid file | Cell connections of a DIS, DISV or DISU grid. Written by MODFLOW 6 by default | §4.1, §4.4 |
| | GWF budget file | Cell-to-cell flows and every source and sink term. SAVE_FLOWS in each package, budget saved in Output Control | §4.1 |
| | Every time step saved | Needed for transient tracking (SAVE BUDGET ALL) | §4.8, §4.10 |
| | Saturated thickness | For travel times and transient tracking. NPF SAVE_SATURATION, or the head file | §4.6, §4.8 |
| | Porosity | Given by the user. Needed for travel times and transient tracking, not for fractions | §4.6, §4.8 |
| | Package budget files | SFR, LAK, MAW, UZF and MVR budgets (BUDGET FILEOUT), to trace through package networks | §4.7 |
| | Linked models | GWF models joined by exchanges, read as one system (SAVE_FLOWS in the exchange) | §4.7 |
| **Selections** | Package | All terms of a package, such as all recharge or all wells | §4.1, §4.3 |
| | Boundname | Terms with a given boundname, such as one well. Read from the package input files | §4.1 |
| | Boundary number | Terms with given boundary numbers in a package | – |
| | Cells | All terms in the given cells (gross accounting), or the cells themselves (net accounting) | §4.2 |
| | Zone | Cells with a given zone value, alone or with a package, such as the recharge on one field | §4.3, §4.4 |
| **Outputs** | Backward fraction F | Share of each cell's water that ends at the destination | §4.1 |
| | Forward fraction G | Share of each cell's water that came from the source | §4.3 |
| | Volumes | Volume through, volume from and volume to, and their split by package | §4.1, §4.3 |
| | Gross and net accounting | Water credited to a weak-sink well under each rule. Boundary-control maps | §4.2 |
| | Budget checks | Closure, forward–backward and boundary-control checks with every trace | §4.1–§4.3 |
| | Mean travel time | Mean time to the destination under full mixing | §4.6 |
| | Snapshot statistics | Minimum, mean and maximum F over time steps. Cells always, sometimes or never above a threshold | §4.5 |
| | Transient tracking | Tagged fractions c (forward) and w (backward in time). Destination's water by source, time step and initial water | §4.8, §4.10 |
| | Ensemble statistics | Mean, probability of exceeding a threshold, and exact or histogram quantiles over realisations | §4.9 |
| | PRT release points | Particle runs on the same flows, for comparison | §4.6 |
| | Export | NumPy and netCDF files (§4.1). GeoPackage polygons for GIS (§4.4) | §4.1, §4.4 |
