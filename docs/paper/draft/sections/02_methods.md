# 2. Method in brief

This section defines the quantities the code computes. The derivations and the solution of the equations are given in the Supporting Information ({SI: method in full}).

## 2.1 Full mixing and the cell budget

Full mixing treats each active model cell as one well-mixed volume of water (Section 1). The water in a cell leaves through each of its outflows in proportion to the size of that outflow. <!-- evidence: docs/paper/terms.md (full mixing); src/gwsource/assemble.py (outflow shares q_ij / O_i) -->

Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017). The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. All other budget terms, such as recharge, wells, rivers and storage, are kept separate by package and boundary. A term that brings water into a cell is a source term. A term that takes water out is a sink term. If $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the totals of a cell's source and sink terms, its total inflow, total outflow and cell budget error are (Fig. 1a)

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{1}$$

The cell budget of a MODFLOW model never balances exactly, so $r_i$ is small but not zero. <!-- evidence: src/gwsource/diagnostics.py (cell_residual, budget_error) -->

A trace is one solve for a chosen set of destinations or sources. A destination is the sink terms traced to, such as one well's pumping. Sink terms traced as one unit, such as all the wells of a wellfield, form a destination group. A source is the source terms traced from, such as recharge. The outflow of cell $i$ through the destination is $d_i$. The inflow of cell $i$ through the source is $s_i$.

[[Figure 1]]

## 2.2 Backward and forward fractions

The backward fraction $F_i$ tells where a destination's water comes from. It is the share of the water leaving cell $i$ that later leaves the model through the destination. Because the cell is fully mixed, all its outflows carry the same water. So

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}. \tag{2}$$

In words: the share of a cell's water that reaches the destination is the share that leaves directly through it plus the outflow-weighted mean of the shares of its downstream neighbours. Fig. 1b works through an eight-cell example. <!-- evidence: docs/paper/figures/README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS (cell 6: 9 + 1 in from neighbours, 1 recharge; 6 to the well, 5 on) -->

Let $P_{ij} = q_{ij}/O_i$ be the share of cell $i$'s outflow that goes to cell $j$. Written for every cell at once, Eq. (2) becomes

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{3}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group.

The forward fraction $G_i$ tells where a source's water goes. It is the share of the water entering cell $i$ that came from the source. It follows in the same way from the inflow shares $Q_{ij} = q_{ji}/I_i$ as

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{4}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group.

Most cells can be solved one at a time along the flow paths. Flow loops are the exception. They are groups of cells among which water circulates, for example with the XT3D option of MODFLOW 6 (Provost et al. 2017). The code solves each loop exactly as one small block of equations ({SI: method in full}). <!-- evidence: src/gwsource/config.py (solver "auto": topological substitution if acyclic, block-triangular sparse LU otherwise); src/gwsource/solve.py -->

## 2.3 Volumes

A fraction says what share of a cell's water reaches the destination, but not how much water that is. A fraction times a flow gives a volume of water per unit time. The volume through cell $i$ is $F_i O_i$. It is the part of the water passing through the cell that reaches the destination. <!-- evidence: src/gwsource/metrics.py docstring (volume_through = F x O, gross) -->

The volume from cell $i$ is $F_i$ times the cell's inflow through its source terms. It is the water entering the model in that cell that reaches the destination. Summing the volume from over all cells, package by package, splits the destination's water by source (Section 4.1). <!-- evidence: src/gwsource/metrics.py docstring (volume_from, volume_from_by_term) --> A forward trace gives the matching volumes from $G$. They split a source's water by where it leaves the model (Section 4.3). <!-- evidence: src/gwsource/metrics.py docstring (forward volume_through = G x I, volume_to, volume_to_by_term) -->

## 2.4 Gross and net accounting

At a weak sink, Eq. (2) needs a rule for how much of the cell's water to credit to the sink (Section 1). Our default is gross accounting. Each sink term then takes its share of the cell's total outflow. The rest passes on to the neighbours. A well is credited with the water it pumps, as in a transport model. <!-- evidence: Potter et al. 2008 p. 336, Fig. 1 (the sink cell's capture fraction is the well's outflow over the cell's total inflow, drawn for a weak sink); src/gwsource/config.py (accounting "gross" default) -->

Net accounting credits a sink with all the water that passes through its cell. The destination cells are then fixed at $F = 1$. In the example of Fig. 1b, gross accounting credits the well with the 6 m³/d it pumps. Net accounting also credits it with the 5 m³/d that flow on through its cell to the river. At a small well, the difference can be several times the pumping (Fig. 1c; Section 4.2). <!-- evidence: src/gwsource/config.py (net: destination cells absorbing, the reference method, for regression and comparison only); tutorials/02_accounting (weak_well 5 m³/d, net 33.667 m³/d, 6.7 times) -->

## 2.5 Water-budget checks

Each trace comes with checks that the traced volumes agree with the flows the model saved. Each check must hold exactly, because it follows from adding up the cell equations. The first is the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{5}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. The forward closure check is its mirror image for a source. The forward–backward check is

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{6}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included. A third check, the boundary-control check, is described with the example of Section 4.2. <!-- evidence: src/gwsource/diagnostics.py (backward_closure, forward_closure, duality); docs/paper/terms.md (closure, forward–backward and boundary-control checks) -->

The checks test that the fractions were solved correctly from the flows that were read. A large error in a check points to a fault in the tracing. The checks cannot show that the flow model is right. Nor can they show that full mixing describes how water moves in the aquifer.

## 2.6 Mean travel time

Fractions say how much water arrives, not when. Let $V_i$ be the volume of water in cell $i$. It is porosity times the saturated volume of the cell. Fractions need no porosity, but travel times do. The mean residence time of cell $i$ is $\tau_i = V_i/O_i$. The mean travel time from entering cell $i$ to leaving the model through the destination is then $m_i/F_i$, where

$$(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F}. \tag{7}$$

Here $\circ$ is the cell-by-cell product. Each cell adds its own residence time, weighted by its $F$. The sum then passes upstream with the outflow shares. A mean travel time averages fast and slow water that have mixed in the cells, so it is not a first-arrival time (Section 4.6). <!-- evidence: src/gwsource/traveltime.py (travel_time: porosity required, no default; gross accounting only; residence_time = V / O) -->

## 2.7 Transient flow: snapshots and transient tracking

In a transient model, the water reaching a well depends on what happened in earlier time steps. A snapshot (Section 1) ignores this. It treats storage release as a source term (Fig. 1d, left). A snapshot therefore assumes that water reaches the well in the same step it entered. Water recharged in winter cannot appear at the well in summer. We refer to this as having no travel lag. Snapshots also cannot say where the water released from storage came from. Section 4.5 shows snapshots of a seasonal model.

Transient tracking extends full mixing through time. Water from the chosen sources is tagged, as a tracer would be. The tagged water is carried through storage from step to step (Fig. 1d, right). Storage terms change a cell's water volume from $V_i^{\mathrm{old}}$ at the start of a step to $V_i^{\mathrm{new}}$ at its end. Let $c_i$ be the share of a cell's water that is tagged. Step $n$ of length $\Delta t$ is then

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{8}$$

where $O_i$ now leaves out storage. A cell's tagged water at the end of a step is its tagged water at the start, plus arrivals from upstream cells and source terms, less what leaves at the cell's end-of-step mix. The step is solved as in GWT, without dispersion (Langevin et al. 2022). Transient tracking needs porosity and the budget of every time step. The water in the model at the start of the simulation can be tagged as its own group. We refer to it as initial water. <!-- evidence: src/gwsource/tracking.py module docstring and TrackingConfig (porosity required; flow_error_correction as GWT FLOW_IMBALANCE_CORRECTION; initial_water; volume_mode "gwt") -->

Forward tracking cannot tell which of the water now in the aquifer will reach the destination, and by when. Backward tracking in time answers that question. It differs from MODPATH backward tracking, in which particles run in reverse from the sink. The code solves the step equations from the end of the simulation back to the start ({SI: method in full}). The result is the backward fraction in time $w_i^n$. It is the share of the water in cell $i$ at the start of step $n$, or entering it during the step, that leaves through the destination before the simulation ends. A map of $w$ is a time-limited contributing area (Sections 4.8 and 4.10). <!-- evidence: src/gwsource/tracking.py (track_backward, tracking_duality); docs/paper/terms.md (backward fraction in time w) -->
