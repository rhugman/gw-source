<!-- Reduced draft: main-text Table 1 of the full draft (display/T1_software.md), moved into the SI with its pointers changed to the reduced main text and SI. -->

## {SI: inputs, selections and outputs}

**Table.** What the code reads, how destinations and sources are chosen, and what it returns. The last column gives the worked example that shows each item, in the main text (Section 4) or in this Supporting Information. MODFLOW 6 option names are given where a user must set them. <!-- evidence: src/gwsource (mf6io.py, network.py, selectors.py, metrics.py, traveltime.py, transient.py, tracking.py, ensemble.py, export.py, prt.py); tutorials 01–10 (calls used in each); docs/paper/outline.md §3.4 (example numbering) -->

| | Item | What it is or needs | Shown in |
|---|---|---|---|
| **Inputs** | Binary grid file | Cell connections of a DIS, DISV or DISU grid. Written by MODFLOW 6 by default | Section 4, {SI: the same trace on different grids} |
| | GWF budget file | Cell-to-cell flows and every source and sink term. SAVE_FLOWS in each package, budget saved in Output Control | Section 4 |
| | Every time step saved | Needed for transient tracking (SAVE BUDGET ALL) | Section 4, {SI: a new well's source mix} |
| | Saturated thickness | For travel times and transient tracking. NPF SAVE_SATURATION, or the head file | {SI: mean travel time to the well}, Section 4 |
| | Porosity | Given by the user. Needed for travel times and transient tracking, not for fractions | {SI: mean travel time to the well}, Section 4 |
| | Package budget files | SFR, LAK, MAW, UZF and MVR budgets (BUDGET FILEOUT), to trace through package networks | {SI: streams, drains, wells and linked models} |
| | Linked models | GWF models joined by exchanges, read as one system (SAVE_FLOWS in the exchange) | {SI: streams, drains, wells and linked models} |
| **Selections** | Package | All terms of a package, such as all recharge or all wells | Section 4, {SI: where each source's water goes} |
| | Boundname | Terms with a given boundname, such as one well. Read from the package input files | Section 4 |
| | Boundary number | Terms with given boundary numbers in a package | – |
| | Cells | All terms in the given cells (gross accounting), or the cells themselves (net accounting) | {SI: accounting at a small well} |
| | Zone | Cells with a given zone value, alone or with a package, such as the recharge on one field | {SI: where each source's water goes}, {SI: the same trace on different grids} |
| **Outputs** | Backward fraction F | Share of each cell's water that ends at the destination | Section 4 |
| | Forward fraction G | Share of each cell's water that came from the source | {SI: where each source's water goes} |
| | Volumes | Volume through, volume from and volume to, and their split by package | Section 4, {SI: where each source's water goes} |
| | Gross and net accounting | Water attributed to a weak-sink well under each rule. Boundary-control maps | {SI: accounting at a small well} |
| | Budget checks | Closure, forward–backward and boundary-control checks with every trace | Section 4, {SI: accounting at a small well}, {SI: where each source's water goes} |
| | Mean travel time | Mean time to the destination under full mixing | {SI: mean travel time to the well} |
| | Snapshot statistics | Minimum, mean and maximum F over time steps. Cells always, sometimes or never above a threshold | {SI: the contributing area through the seasons} |
| | Transient tracking | Tagged fractions c (forward) and w (backward in time). Destination's water by source, time step and initial water | Section 4, {SI: a new well's source mix} |
| | Ensemble statistics | Mean, probability of exceeding a threshold, and exact or histogram quantiles over realisations | Section 4 |
| | PRT release points | Particle runs on the same flows, for comparison | {SI: mean travel time to the well} |
| | Export | NumPy and netCDF files. GeoPackage polygons for GIS ({SI: the same trace on different grids}) | {SI: the same trace on different grids} |
