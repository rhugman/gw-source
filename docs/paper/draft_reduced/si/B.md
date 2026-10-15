## {SI: method in full}

This text derives the equations of Section 2 and shows how they are solved. Equation numbers without an S refer to the main text. <!-- assembled in alt round 1 from the si/B.md items "net accounting, fixed cells", "travel-time identity", "solution of the linear systems" and "water volume options", and from previous/02_methods.md §§2.3, 2.4, 2.5, 2.7 and 2.8 (main-text Methods of the earlier draft); slimmed in SI round 1 (reviews/si_r1_prose.md, S1) -->

Two fractions describe where a cell's water goes and where it came from. The backward fraction $F_i$ is the share of the water in cell $i$ that later leaves the model through a chosen destination, such as a well. The forward fraction $G_i$ is the share of the water in cell $i$ that entered the model through a chosen source, such as recharge on one field. A weak sink is a cell whose sink terms take only part of the cell's outflow. The rest of its water flows on to the neighbouring cells. <!-- evidence: docs/paper/terms.md (F, G, weak sink); main text Sections 1 and 2 -->

### The backward and forward fractions

Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017). The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. All other budget terms, such as recharge, wells, rivers and storage, are kept separate by package and boundary. A term that brings water into a cell is a source term. A term that takes water out is a sink term. If $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the totals of a cell's source and sink terms, its total inflow, total outflow and cell budget error are

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{S1}$$

The cell budget of a MODFLOW model never balances exactly, so $r_i$ is small but not zero. <!-- evidence: src/gwsource/diagnostics.py (cell_residual, budget_error); full draft sections/02_methods.md, Eq. (1) --> The outflow of cell $i$ through the destination is $d_i$. The inflow of cell $i$ through the source is $s_i$.

Full mixing means that all water leaving a cell has the same mix of origins and fates. Take the water that leaves cell $i$ in one day. The part $d_i$ leaves through the destination directly. The part $q_{ij}$ goes to neighbour $j$. A share $F_j$ of that part later leaves through the destination. So the volume of water leaving cell $i$ that ends at the destination is

$$F_i\, O_i = \sum_j q_{ij}\, F_j + d_i . \tag{S2}$$

Dividing by $O_i$ gives Eq. (1). Let $P_{ij} = q_{ij}/O_i$ be the share of cell $i$'s outflow that goes to cell $j$. For all cells together, Eq. (1) is then

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{S3}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group. Under gross accounting, a sink term $k$ in cell $i$ takes the share $|q_k|/O_i$ of the cell's outflow. These shares are the entries of $\mathbf{S}$. A cell with no outflow is given $F = 0$. <!-- src/gwsource/assemble.py module docstring (gross accounting rows; cells with O_i = 0 get an identity row and zero right-hand side) -->

The forward fraction follows from the inflow in the same way. The water entering cell $i$ in one day comes from the neighbours and from the source and sink terms. A share $G_j$ of the water from neighbour $j$ came from the source. All of $s_i$ came from it. So

$$G_i\, I_i = \sum_j q_{ji}\, G_j + s_i . \tag{S4}$$

Dividing by $I_i$ and writing the result for every cell, with the inflow shares $Q_{ij} = q_{ji}/I_i$, gives

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{S5}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group. A cell with no inflow is given $G = 0$. <!-- src/gwsource/assemble.py (forward rows G_i - sum_j (q_ji/I_i) G_j = sum_{k in S} q_k / I_i) -->

### Volumes

A fraction times a flow gives a volume of water per unit time. The volume through cell $i$ is $F_i O_i$. It is the part of the water passing through the cell that reaches the destination. The volume from cell $i$ is $F_i$ times the cell's inflow through its source terms. Its sum over all cells, package by package, splits the destination's water by source (Section 4, Fig. 2b). A forward trace gives the matching volumes from $G$. <!-- evidence: src/gwsource/metrics.py docstring (volume_through = F x O, gross; volume_from, volume_from_by_term; forward volume_through = G x I, volume_to, volume_to_by_term); full draft Section 2.3 -->

### Why the water-budget checks hold exactly

The checks of Section 2 follow from adding up Eqs. (S2) and (S4) over all cells. On the right of Eq. (S2), each flow $q_{ij}$ appears once, multiplied by the $F$ of the cell it enters. The flows into cell $j$ add up to $I_j - \mathrm{Src}_j$. With $r_i = I_i - O_i$, the sum of Eq. (S2) over all cells becomes the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{S6}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. Adding Eq. (S4) over all cells gives the forward closure check in the same way:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i . \tag{S7}$$

The forward–backward check links the two systems. Multiply Eq. (S2) by $G_i$ and Eq. (S4) by $F_i$, and add each over all cells. Both results then hold the same double sum of the cell-to-cell flows, $\sum_i \sum_j q_{ij}\, G_i\, F_j$. It cancels when one result is subtracted from the other. What remains is the forward–backward check

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{S8}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included.

The boundary-control check traces every sink term of the model, each as its own destination. The sum of their fractions solves Eq. (1) with $d_i$ replaced by the total sink outflow $\mathrm{Snk}_i$. A value of 1 in every cell solves that equation, because $\sum_j q_{ij} + \mathrm{Snk}_i = O_i$. The solution is unique outside closed recirculation loops, which are described below. So the fractions to all sinks add up to 1 in every other cell with outflow.

The checks include the cell budget errors $r_i$. So they hold exactly for any flow field, also one that does not balance. The errors reported by the code are then round-off, unless the tracing itself is wrong. The code also reports the errors without the budget error terms. <!-- src/gwsource/diagnostics.py module docstring (exact identities; "with the residual term the checks hold to round-off; without it they hold to within the model's budget error"); src/gwsource/diagnostics.py Check (error and error_without_residual) -->

### Solution of the linear systems

Equation (1) gives a cell's $F$ from the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource (Foley and Black 2013). A flow loop is a group of cells among which water circulates. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each loop. Foley and Black (2013) expect this to change the results very little. <!-- references/docs/text/2013_Foley_Black_FlowSource_DAG_algorithms.txt, cycle section: "Cycles do, albeit rarely, occur"; "multilayer models which have stability problems"; "the edge with the lowest volume is removed"; "negligible in all but the rarest cases" --> We keep every flow and solve each loop exactly. The matrix is ordered so that the cells come in flow order, with each loop as one block. It is then factorised once by sparse LU decomposition. A model of a million cells with thousands of small loops is factorised in well under a second. <!-- src/gwsource/solve.py module docstring (topological and block solvers; "a 1M-cell graph with thousands of small cycles factorises in well under a second") -->

The matrix $\mathbf{I} - \mathbf{P}$ is singular only on a closed recirculation loop. No cell of such a loop has outflow to a sink or to a cell outside the loop, so its water never reaches a sink. These loops are given $F = 0$ and reported. The code also reports every other flow loop and the flow that goes round it. Under gross accounting, one factorisation serves every destination group and the travel times of Eq. (S10). <!-- src/gwsource/solve.py module docstring (isolate_closed_loops; factorize() reuse for gwsource.traveltime); src/gwsource/diagnostics.py module docstring (cycle report) -->

### Net accounting

Net accounting reproduces the way FlowSource attributes water (Foley and Black 2013). It works from the cell-to-cell flows only. With $I^e_i$ and $O^e_i$ the cell-to-cell inflow and outflow of cell $i$, the water passing through the cell is $T_i = I^e_i + \max(O^e_i - I^e_i, 0)$. Outside the destination cells, the backward fraction is

$$f_i = \frac{1}{T_i} \sum_j q_{ij}\, f_j . \tag{S9}$$

The destination cells are fixed at $f = 1$. Their outflows to other cells are ignored. A forward trace works in the same way on the reversed flows. <!-- src/gwsource/assemble.py module docstring (net accounting: s_i = O^edges_i - I^edges_i, T_i = I^edges_i + max(s_i, 0); destination cells absorbing; forward on the reversed graph); PLAN §2.4 -->

Which cells are fixed depends on how the group was selected. A selection by cells or by zone fixes all its cells, as FlowSource does (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace these are the cells where the term is a sink. A well listed at zero rate is therefore not fixed in a backward trace. The same holds for a drain above the water table and a losing river cell. <!-- PLAN §2.4; src/gwsource/trace.py::net_fixed_cells; shortened in SI round 1 (reviews/si_r1_prose.md, Rewrite 2) -->

Net accounting has no cell budget error term. It solves one destination group at a time, because each group fixes its own cells. As an option, it can delete the smallest flow in each flow loop, to compare with studies made with FlowSource. <!-- PLAN §2.4; src/gwsource/assemble.py and diagnostics.py docstrings; src/gwsource/config.py (remove_cycles: net mode only; delete the smallest edge of each flow cycle) -->

### Mean travel time

Fractions say how much water arrives, not when. Let $V_i$ be the volume of water in cell $i$. It is porosity times the saturated volume of the cell. Fractions need no porosity, but travel times do. A parcel of water stays in a fully mixed cell for a random time with the mean $\tau_i = V_i/O_i$. Under full mixing, the time a parcel spends in a cell does not depend on the route by which it leaves. Let $m_i$ be the mean travel time from entering cell $i$ to leaving the model, counted only for water that leaves through the destination, and weighted by $F_i$. A parcel spends on average $\tau_i$ in cell $i$ and then moves to cell $j$ with probability $P_{ij}$. So

$$m_i = \tau_i\, F_i + \sum_j P_{ij}\, m_j . \tag{S10}$$

In matrix form this is $(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F}$, where $\circ$ is the cell-by-cell product. The mean travel time of the water that reaches the destination is $m_i/F_i$. It is defined only under gross accounting, and only where $F_i$ is above a small threshold. <!-- src/gwsource/traveltime.py module docstring (m_i = E[R_i] P(D) + sum_j P_ij m_j; mean_time = m / F, NaN where F <= fraction_threshold; gross accounting only) -->

The travel times have a closure check of their own. Multiplying Eq. (S10) by each cell's outflow and adding over all cells gives

$$\sum_i \mathrm{Src}_i\, m_i - \sum_i r_i\, m_i = \sum_i V_i F_i . \tag{S11}$$

The right-hand side is the volume of water that will end at the destination. The check says that this volume, divided by the destination's inflow, equals the flow-weighted mean travel time of all the water reaching the destination, once the cell budget errors are included. <!-- src/gwsource/traveltime.py docstring, "Exact identity (backward)"; derivation shortened in SI round 1 -->

The mean travel time $m_i/F_i$ includes the time spent in the cell where the water leaves, for a well its own cell. Particle trackers that stop particles on entering a sink cell (MODFLOW 6 PRT, MODPATH) measure the time until the water enters that cell. The code also gives this time, as $(m_i - x_i)/F_i$, where $x$ solves $(\mathbf{I} - \mathbf{P})\,\mathbf{x} = \boldsymbol{\tau} \circ (\mathbf{S}\,\mathbf{D})$. It is the full-mixing time that {SI: the worked examples in brief} compares with particles. <!-- src/gwsource/traveltime.py docstring (mean_time_to_exit_cell); the test-model-1 values (9,607 d and 9,574 d) moved to docs/verification.md in SI round 1 -->

### Transient tracking

Transient tracking carries tagged water from step to step (Section 2). Each cell, and each reach, lake or well added as an extra cell (Section 3), is a fully mixed volume of water. The storage terms of the flow model are not traced as source or sink terms. Instead they change the volume of water in the cell. Over step $n$, of length $\Delta t$, the volume changes from $V_i^{\mathrm{old}}$ to $V_i^{\mathrm{new}}$. Let $c_i$ be the share of a cell's water that is tagged. The tagged water at the end of the step is the tagged water at the start, plus what arrives, less what leaves:

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{S12}$$

where $O_i$ now leaves out storage. <!-- src/gwsource/tracking.py module docstring, forward scheme, eq. (1) -->

As in MODFLOW 6 GWT, the scheme is implicit in time. So outflows over the step carry the cell's mix at the end of the step. Inflows carry the mix of the cell they come from. The scheme adds no dispersion. It runs on the flow model's own time steps, so the budget of every step must be saved (SAVE BUDGET ALL). <!-- previous/02_methods.md §2.7; src/gwsource/tracking.py module docstring -->

The cell budget error $r_i$ leaves the cell, or enters it, at the cell's own mix of water. GWT treats the error in the same way, which Langevin et al. (2022) call the flow-imbalance correction. With this correction, Eq. (S12) leaves every tagged fraction at 1 when every source and the initial water are tagged. <!-- src/gwsource/tracking.py module docstring (a = 1: FLOW_IMBALANCE_CORRECTION, Langevin et al. 2022 eq. 2-14/2-15; c = 1 solves (1) when every source and the initial water are tagged) -->

For all cells, step $n$ is one set of linear equations,

$$\mathbf{A}^n \mathbf{c}^n = \mathbf{B}^n \mathbf{c}^{n-1} + \Delta t\, \mathbf{s}^n . \tag{S13}$$

$\mathbf{B}^n$ holds the start volumes $V_i^{\mathrm{old}}$ on its diagonal. $\mathbf{A}^n$ holds the other terms of Eq. (S12). Each step is solved in flow order as above. Because every cell holds water, no flow loop makes the matrix singular. One factorisation per step serves every tagged group. <!-- src/gwsource/tracking.py module docstring (A^n c^n = B^n c^(n-1) + dt s^n; row sums V^old + dt Src >= 0; no closed-loop isolation needed since V > 0) -->

The water in the model at the start of the simulation can be tagged as its own group, the initial water. It starts with $c = 1$ in every cell and has no source. <!-- src/gwsource/tracking.py module docstring (tagged initial water) -->

**Water volume options.** In the default, called "flow", each cell's water volume starts at porosity times saturated volume. It then changes only by the storage flows of the flow model, so every water balance closes exactly. In the "gwt" option, the volume is reset to porosity times saturated volume at the end of each step, as in MODFLOW 6 GWT. Forward transient tracking with this option is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, tagged water then appears or disappears at step boundaries. We recommend the default unless a result must match a GWT run. <!-- moved from §2.7 in round 5 (v6 §2.8 text); src/gwsource/tracking.py module docstring (volumes: "gwt" and "flow"); the numbers (1.9 × 10⁻⁴ and 3.7 × 10⁻³) kept only in the examples text in SI round 1 -->

**Transport sub-steps.** Long implicit time steps make tagged water arrive too early ({SI: the worked examples in brief}). Sub-steps reduce this effect without a change to the flow model. Each flow step is split into $m$ equal transport sub-steps. The flows stay constant within the flow step. The water volumes change linearly between the start and end of the step. <!-- src/gwsource/tracking.py module docstring (sub-steps: equal transport sub-steps of dt/m, flows constant, volumes interpolated linearly; per-step outputs at flow-step boundaries; m = 1 reproduces the unsplit scheme exactly) -->

### Backward tracking in time

Backward tracking in time solves the adjoint of Eq. (S13) (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). The adjoint holds the same flows with the roles of inflow and outflow swapped. The tagged water that the destination takes over the whole simulation is $J = \sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n$, where $\mathbf{d}^n$ holds the destination outflow of each cell in step $n$. The backward fraction in time $\mathbf{w}^n$ solves, from the last step $N$ back to the first,

$$\left(\mathbf{A}^n\right)^{\mathsf T} \mathbf{w}^n = \Delta t^n\, \mathbf{d}^n + \mathbf{B}^{n+1} \mathbf{w}^{n+1}, \qquad \mathbf{w}^{N+1} = \mathbf{0} . \tag{S14}$$

The solve runs from the end of the simulation back to the start. $w_i^n$ is the share of the water in cell $i$ at the start of step $n$, together with the water entering the cell during the step, that leaves through the destination before the simulation ends. The implicit scheme mixes these two kinds of water alike, so one value describes both. <!-- src/gwsource/tracking.py module docstring, backward (adjoint) scheme, eq. (2) -->

The same backward equations give the fraction that leaves through the other sinks and the fraction still stored at the end. The three fractions add up to 1 in every cell and step, apart from a small remainder that the code reports. <!-- src/gwsource/tracking.py module docstring (fraction_through + fraction_to_other_sinks + fraction_in_storage_at_end + fraction_unaccounted = 1) -->

The transient forward–backward check follows from Eqs. (S13) and (S14) in the same way as Eq. (S8):

$$\sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n = \sum_n \Delta t^n\, \mathbf{s}^n \cdot \mathbf{w}^n + \sum_i V_i^{\mathrm{old},1}\, c_i^0\, w_i^1 . \tag{S15}$$

The check says that the tagged water the destination takes equals the tagged inflow and the tagged initial water, each multiplied by its share that later reaches the destination. It holds exactly for either volume option and with or without sub-steps. <!-- src/gwsource/tracking.py module docstring (duality identity (3), exact for any volumes and any a; volume_from per node and step, initial_volume_from); previous/02_methods.md §2.8 eq. (10); derivation shortened in SI round 1 -->

With flows held constant for long enough, the tagged fraction $c$ tends to the steady-state forward fraction $G$. The fraction $w$ at the first step tends to the steady-state backward fraction $F$. Test model 10 checks this limit ({SI: verification checks on the test models}). <!-- src/gwsource/tracking.py module docstring ("Limit: with flows held constant for long enough, c^n tends to the steady source_fraction ... and w^1 to the steady fraction_through") -->
