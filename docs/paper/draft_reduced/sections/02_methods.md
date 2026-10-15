# 2. Method in brief

The derivations and the solution of the equations are given in {SI: method in full}.

## 2.1 Full mixing and the backward and forward fractions

Full mixing treats each active model cell as one well-mixed volume of water. Its water leaves through each outflow in proportion to the size of that outflow. <!-- evidence: docs/paper/terms.md (full mixing); src/gwsource/assemble.py (outflow shares q_ij / O_i) --> The code reads the cell-to-cell flows and the source and sink terms, such as recharge, wells and rivers, from the MODFLOW 6 budget file.

A backward trace follows water to a destination, such as one well or a wellfield. The backward fraction $F_i$ is the share of the water leaving cell $i$ that later leaves the model through the destination. All outflows of a fully mixed cell carry the same water. So

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}, \tag{1}$$

where $q_{ij}$ is the flow from cell $i$ to its neighbour $j$. The total outflow of the cell is $O_i$. Its outflow through the destination is $d_i$. In words: the share of a cell's water that reaches the destination is the share that leaves directly through it plus the outflow-weighted mean of the shares of its downstream neighbours. An eight-cell example is worked through in {SI: method schematic}. <!-- evidence: docs/paper/figures/README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS --> The code solves Eq. (1) for all cells at once, in the order the water flows. <!-- evidence: src/gwsource/config.py (solver "auto": topological substitution if acyclic, block-triangular sparse LU otherwise); src/gwsource/solve.py --> A contributing area is the set of cells where F exceeds a chosen threshold, such as one half.

A forward trace follows water from a source, such as recharge. The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source. The sum over all cells of F times each cell's inflow from source terms splits the destination's water by source. <!-- evidence: src/gwsource/metrics.py docstring (volume_from, volume_from_by_term) -->

## 2.2 Gross and net accounting

At a weak sink, Eq. (1) needs a rule for how much of the cell's water to attribute to the sink. By default the code uses gross accounting. Each sink term then takes its share of the cell's outflow, as in a transport model. <!-- evidence: Potter et al. 2008 p. 336, Fig. 1; src/gwsource/config.py (accounting "gross" default) --> Net accounting attributes to a sink all the water that passes through its cell. <!-- evidence: src/gwsource/config.py (net: destination cells absorbing, the reference method, for regression and comparison only) -->

## 2.3 Water-budget checks and mean travel time

Each trace comes with checks that the traced volumes agree with the saved flows. For example, the source water traced to a well must add up to its pumping. <!-- evidence: src/gwsource/diagnostics.py (backward_closure, forward_closure, duality); docs/paper/terms.md (closure, forward–backward and boundary-control checks) --> The checks test the solution, not the flow model or the assumption of full mixing. With a porosity, the code also gives mean travel times ({SI: method in full}). A mean travel time is not a first-arrival time. <!-- evidence: src/gwsource/traveltime.py (travel_time: porosity required, no default; gross accounting only; residence_time = V / O) -->

## 2.4 Transient flow: snapshots and transient tracking

A snapshot treats storage terms as source and sink terms. It therefore assumes that water reaches the well in the same step it entered. It cannot say where the water released from storage came from.

Transient tracking extends full mixing through time. Water from the chosen sources is tagged, as a tracer would be. The tagged water is carried through storage from step to step. Each step is solved as in GWT, without dispersion (Langevin et al. 2022). Transient tracking needs porosity and the budget of every time step. The water in the model at the start can be tagged as its own group. We refer to it as initial water. <!-- evidence: src/gwsource/tracking.py module docstring and TrackingConfig (porosity required; flow_error_correction as GWT FLOW_IMBALANCE_CORRECTION; initial_water; volume_mode "gwt") --> Backward tracking in time solves the backward counterpart of each step, from the end of the simulation to its start. It gives the share of the water in each cell that leaves through the destination before the simulation ends. A map of this share is a time-limited contributing area (Section 4.2). <!-- evidence: src/gwsource/tracking.py (track_backward, tracking_duality); docs/paper/terms.md (backward fraction in time w) -->
