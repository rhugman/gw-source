# 2. Method in brief

The derivations and the solution of the equations are given in {SI: method in full}.

## 2.1 Full mixing and the backward and forward fractions

Full mixing treats each active model cell as one well-mixed volume of water. Its water leaves through each outflow in proportion to the size of that outflow. <!-- evidence: docs/paper/terms.md (full mixing); src/gwsource/assemble.py (outflow shares q_ij / O_i) --> The code reads the cell-to-cell flows and the source and sink terms, such as recharge, wells and rivers, from the MODFLOW 6 budget file.

A backward trace follows water to a destination, such as one well or a wellfield. The backward fraction $F_i$ is the share of the water leaving cell $i$ that later leaves the model through the destination. All outflows of a fully mixed cell carry the same water. So

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}, \tag{1}$$

where $q_{ij}$ is the flow from cell $i$ to its neighbour $j$. The total outflow of the cell is $O_i$. Its outflow through the destination is $d_i$. In words: a cell's share is the share that leaves directly through the destination plus the outflow-weighted mean of its downstream neighbours' shares. Fig. 1 works through an eight-cell example. <!-- evidence: docs/paper/figures/README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS; studies/paper/gallery_figure.py make_method_single --> The code solves Eq. (1) for all cells at once, in the order the water flows. <!-- evidence: src/gwsource/config.py (solver "auto": topological substitution if acyclic, block-triangular sparse LU otherwise); src/gwsource/solve.py --> A contributing area is the set of cells where F exceeds a chosen threshold, such as one half. The backward trace also splits the destination's water by source. This split is the sum over all cells of F times each cell's inflow through source terms. <!-- evidence: src/gwsource/metrics.py docstring (volume_from, volume_from_by_term) -->

[[Figure 1]]

A forward trace follows water from a source, such as recharge. The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source.

## 2.2 Gross and net accounting

At a weak sink, Eq. (1) needs one of the two rules of Section 1. By default the code uses gross accounting, as a transport model does. Each sink term then takes its share of the cell's outflow. <!-- evidence: Potter et al. 2008 p. 336, Fig. 1; src/gwsource/config.py (accounting "gross" default) --> In Fig. 1, gross accounting gives the well the 6 m³/d it pumps. Net accounting adds the 5 m³/d that flow on through the well cell to the river. <!-- evidence: studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS (cell 6: 9 + 1 in from neighbours, 1 recharge; 6 to the well, 5 on); full draft Section 2.4; src/gwsource/config.py (net: destination cells absorbing, the reference method, for regression and comparison only) --> We would use net accounting to reproduce a FlowSource study.

## 2.3 Water-budget checks and mean travel time

Each trace comes with checks that the traced volumes agree with the saved flows. For example, the closure check requires the source water traced to a well to add up to its pumping. <!-- evidence: src/gwsource/diagnostics.py (backward_closure, forward_closure, duality); docs/paper/terms.md (closure, forward–backward and boundary-control checks) --> The checks test the solution, not the flow model or the assumption of full mixing. With a porosity, the code also gives mean travel times ({SI: method in full}). A mean travel time is not a first-arrival time. <!-- evidence: src/gwsource/traveltime.py (travel_time: porosity required, no default; gross accounting only; residence_time = V / O) -->

## 2.4 Transient flow: snapshots and transient tracking

A snapshot traces each time step on its own flows, as if they were steady. Water that enters the aquifer in a step can then reach the well only in that same step. A snapshot cannot show recharge from the wet season reaching the well in the dry season. Water released from storage was already in the aquifer at the start of the step. A snapshot treats it as a source of unknown origin.

Transient tracking extends full mixing through time. Water from the chosen sources is tagged, as a tracer would be. The tagged water is carried through storage from step to step. Hydraulic mixing cells carry mixed water through storage in integrated surface water–groundwater models in a similar way (Partington et al. 2011). <!-- references/docs/text/2011_Partington_etal_hydraulic_mixing_cell.txt (volumetric balance of each flow component over each time step, from the previous step's storage); full draft Section 6 --> Each step is solved as in GWT, without dispersion (Langevin et al. 2022). Transient tracking needs porosity and the budget of every time step. The water in the model at the start can be tagged as its own group. We refer to it as initial water. <!-- evidence: src/gwsource/tracking.py module docstring and TrackingConfig (porosity required; flow_error_correction as GWT FLOW_IMBALANCE_CORRECTION; initial_water; volume_mode "gwt") --> Backward tracking in time solves the backward counterpart of each step, from the end of the simulation to its start. It gives the share of the water in each cell that leaves through the destination before the simulation ends. A map of this share is a time-limited contributing area (Section 4.2). <!-- evidence: src/gwsource/tracking.py (track_backward, tracking_duality); docs/paper/terms.md (backward fraction in time w) -->
