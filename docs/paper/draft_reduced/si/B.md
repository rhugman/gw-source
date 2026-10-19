## {SI: method in full}

This text gives the parts of the method that Section 2 only names. It covers the matrix form and solution of the equations, the derivation of the water-budget checks, the details of net accounting and the travel time to where water enters a sink cell. It then gives the matrix form of transient tracking and backward tracking in time, the derivation of the transient check, the water volume options and transport sub-steps. Equation numbers without an S refer to the main text. <!-- assembled in alt round 1 from the si/B.md items "net accounting, fixed cells", "travel-time identity", "solution of the linear systems" and "water volume options", and from previous/02_methods.md §§2.3, 2.4, 2.5, 2.7 and 2.8; slimmed in SI round 1 (reviews/si_r1_prose.md, S1); in round 2 the fractions, volumes, mean travel time, transient tracking and backward tracking in time moved to main-text Section 2 (outline.md Section 3.2 and Section 5), and the equations were renumbered (old S1, S2, S4, S10, S11, S12 and S14 are now main-text Eqs. 1, 2, 4, 5, 6, 7 and 8; old S3, S5, S6, S7, S8, S9, S13, S14 and S15 are now S1, S2, S3, S4, S5, S6, S7, S8 and S9) -->

### Matrix form and solution of the linear systems

Let $P_{ij} = q_{ij}/O_i$ be the share of cell $i$'s outflow that goes to cell $j$. Eq. (3), written for all cells together, is then

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{S1}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group. Under gross accounting, a sink term $k$ in cell $i$ takes the share $|q_k|/O_i$ of the cell's outflow. These shares are the entries of $\mathbf{S}$. A cell with no outflow is given $F = 0$. <!-- src/gwsource/assemble.py module docstring (gross accounting rows; cells with O_i = 0 get an identity row and zero right-hand side) -->

Eq. (4) divided by $I_i$ and written for every cell, with the inflow shares $Q_{ij} = q_{ji}/I_i$, gives in the same way

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{S2}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group. A cell with no inflow is given $G = 0$. <!-- src/gwsource/assemble.py (forward rows G_i - sum_j (q_ji/I_i) G_j = sum_{k in S} q_k / I_i) -->

Equation (3) gives a cell's $F$ from the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource (Foley and Black 2013). A flow loop is a group of cells among which water circulates. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each loop. Foley and Black (2013) expect this to change the results very little. <!-- references/docs/text/2013_Foley_Black_FlowSource_DAG_algorithms.txt, cycle section: "Cycles do, albeit rarely, occur"; "multilayer models which have stability problems"; "the edge with the lowest volume is removed"; "negligible in all but the rarest cases" --> We keep every flow and solve each loop exactly. The matrix is ordered so that the cells come in flow order, with each loop as one block. It is then factorised once by sparse LU decomposition. A model of a million cells with thousands of small loops is factorised in well under a second. <!-- src/gwsource/solve.py module docstring (topological and block solvers; "a 1M-cell graph with thousands of small cycles factorises in well under a second") -->

The matrix $\mathbf{I} - \mathbf{P}$ is singular only on a closed recirculation loop. No cell of such a loop has outflow to a sink or to a cell outside the loop, so its water never reaches a sink. These loops are given $F = 0$ and reported. The code also reports every other flow loop and the flow that goes round it. Under gross accounting, one factorisation serves every destination group and the travel times of Eq. (5). <!-- src/gwsource/solve.py module docstring (isolate_closed_loops; factorize() reuse for gwsource.traveltime); src/gwsource/diagnostics.py module docstring (cycle report) -->

### Why the water-budget checks hold exactly

The checks of Section 2 follow from adding up Eqs. (2) and (4) over all cells. On the right of Eq. (2), each flow $q_{ij}$ appears once, multiplied by the $F$ of the cell it enters. The flows into cell $j$ add up to $I_j - \mathrm{Src}_j$. With $r_i = I_i - O_i$, the sum of Eq. (2) over all cells becomes the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{S3}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. Adding Eq. (4) over all cells gives the forward closure check in the same way:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i . \tag{S4}$$

The forward–backward check links the two systems. Multiply Eq. (2) by $G_i$ and Eq. (4) by $F_i$, and add each over all cells. Both results then hold the same double sum of the cell-to-cell flows, $\sum_i \sum_j q_{ij}\, G_i\, F_j$. It cancels when one result is subtracted from the other. What remains is the forward–backward check

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{S5}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included.

The boundary-control check traces every sink term of the model, each as its own destination. The sum of their fractions solves Eq. (3) with $d_i$ replaced by the total sink outflow $\mathrm{Snk}_i$. A value of 1 in every cell solves that equation, because $\sum_j q_{ij} + \mathrm{Snk}_i = O_i$. The solution is unique outside closed recirculation loops. So the fractions to all sinks add up to 1 in every other cell with outflow.

The travel-time closure check, Eq. (6), follows in the same way from multiplying Eq. (5) by each cell's outflow and adding over all cells. <!-- src/gwsource/traveltime.py docstring, "Exact identity (backward)" -->

The checks include the cell budget errors $r_i$. So they hold exactly for any flow field, also one that does not balance. The errors reported by the code are then round-off, unless the tracing itself is wrong. The code also reports the errors without the budget error terms. <!-- src/gwsource/diagnostics.py module docstring (exact identities; "with the residual term the checks hold to round-off; without it they hold to within the model's budget error"); src/gwsource/diagnostics.py Check (error and error_without_residual) -->

### Net accounting

Net accounting reproduces the way FlowSource attributes water (Foley and Black 2013). It works from the cell-to-cell flows only. With $I^e_i$ and $O^e_i$ the cell-to-cell inflow and outflow of cell $i$, the water passing through the cell is $T_i = I^e_i + \max(O^e_i - I^e_i, 0)$. Outside the destination cells, the backward fraction is

$$f_i = \frac{1}{T_i} \sum_j q_{ij}\, f_j . \tag{S6}$$

The destination cells are fixed at $f = 1$. Their outflows to other cells are ignored. A forward trace works in the same way on the reversed flows. <!-- src/gwsource/assemble.py module docstring (net accounting: s_i = O^edges_i - I^edges_i, T_i = I^edges_i + max(s_i, 0); destination cells absorbing; forward on the reversed graph); PLAN §2.4 -->

Which cells are fixed depends on how the group was selected. A selection by cells or by zone fixes all its cells, as FlowSource does (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace these are the cells where the term is a sink. A well listed at zero rate is therefore not fixed in a backward trace. The same holds for a drain above the water table and a losing river cell. <!-- PLAN §2.4; src/gwsource/trace.py::net_fixed_cells; shortened in SI round 1 (reviews/si_r1_prose.md, Rewrite 2) -->

Net accounting has no cell budget error term. It solves one destination group at a time, because each group fixes its own cells. As an option, it can delete the smallest flow in each flow loop, to compare with studies made with FlowSource. <!-- PLAN §2.4; src/gwsource/assemble.py and diagnostics.py docstrings; src/gwsource/config.py (remove_cycles: net mode only; delete the smallest edge of each flow cycle) -->

### Travel time to where the water enters the sink cell

The mean travel time $m_i/F_i$ of Eq. (5) includes the time spent in the cell where the water leaves, for a well its own cell. Particle trackers that stop particles on entering a sink cell (MODFLOW 6 PRT, MODPATH) measure the time until the water enters that cell. The code also gives this time, as $(m_i - x_i)/F_i$, where $x$ solves $(\mathbf{I} - \mathbf{P})\,\mathbf{x} = \boldsymbol{\tau} \circ (\mathbf{S}\,\mathbf{D})$. Here $\circ$ is the cell-by-cell product. It is the full-mixing time that {SI: the worked examples in brief} compares with particles. <!-- src/gwsource/traveltime.py docstring (mean_time_to_exit_cell); the test-model-1 values (9,607 d and 9,574 d) moved to docs/verification.md in SI round 1 -->

### Matrix form of transient tracking and backward tracking in time

For all cells, step $n$ of Eq. (7) is one set of linear equations,

$$\mathbf{A}^n \mathbf{c}^n = \mathbf{B}^n \mathbf{c}^{n-1} + \Delta t\, \mathbf{s}^n . \tag{S7}$$

$\mathbf{B}^n$ holds the start volumes $V_i^{\mathrm{old}}$ on its diagonal. $\mathbf{A}^n$ holds the other terms of Eq. (7). Each step is solved in flow order as above. Because every cell holds water, no flow loop makes the matrix singular. One factorisation per step serves every tagged group. <!-- src/gwsource/tracking.py module docstring (A^n c^n = B^n c^(n-1) + dt s^n; row sums V^old + dt Src >= 0; no closed-loop isolation needed since V > 0) --> The tagged initial water starts with $c = 1$ in every cell and has no source. <!-- src/gwsource/tracking.py module docstring (tagged initial water) -->

Backward tracking in time solves the adjoint of Eq. (S7) (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). The adjoint holds the same flows with the roles of inflow and outflow swapped. The tagged water that the destination takes over the whole simulation is $J = \sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n$, where $\mathbf{d}^n$ holds the destination outflow of each cell in step $n$. The backward fraction in time $\mathbf{w}^n$ solves, from the last step $N$ back to the first,

$$\left(\mathbf{A}^n\right)^{\mathsf T} \mathbf{w}^n = \Delta t^n\, \mathbf{d}^n + \mathbf{B}^{n+1} \mathbf{w}^{n+1}, \qquad \mathbf{w}^{N+1} = \mathbf{0} . \tag{S8}$$

Row $i$ of Eq. (S8) is Eq. (8). <!-- src/gwsource/tracking.py module docstring, backward (adjoint) scheme, eq. (2); step_matrix (A = diag(V^new + dt (O + a r)) - dt Q^T) -->

The transient forward–backward check follows from Eqs. (S7) and (S8) in the same way as Eq. (S5):

$$\sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n = \sum_n \Delta t^n\, \mathbf{s}^n \cdot \mathbf{w}^n + \sum_i V_i^{\mathrm{old},1}\, c_i^0\, w_i^1 . \tag{S9}$$

The check says that the tagged water the destination takes equals the tagged inflow and the tagged initial water, each multiplied by its share that later reaches the destination. It holds exactly for either volume option and with or without sub-steps. <!-- src/gwsource/tracking.py module docstring (duality identity (3), exact for any volumes and any a; volume_from per node and step, initial_volume_from); previous/02_methods.md §2.8 eq. (10); derivation shortened in SI round 1 --> Test model 10 checks the limit in which c tends to G and w to F under flows held constant ({SI: verification checks on the test models}). <!-- src/gwsource/tracking.py module docstring ("Limit: with flows held constant for long enough, c^n tends to the steady source_fraction ... and w^1 to the steady fraction_through") -->

**Water volume options.** In the default, called "flow", each cell's water volume starts at porosity times saturated volume. It then changes only by the storage flows of the flow model, so every water balance closes exactly. In the "gwt" option, the volume is reset to porosity times saturated volume at the end of each step, as in MODFLOW 6 GWT. Forward transient tracking with this option is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, tagged water then appears or disappears at step boundaries. We recommend the default unless a result must match a GWT run. <!-- moved from §2.7 in round 5 (v6 §2.8 text); src/gwsource/tracking.py module docstring (volumes: "gwt" and "flow"); the numbers (1.9 × 10⁻⁴ and 3.7 × 10⁻³) kept only in the examples text in SI round 1 -->

**Transport sub-steps.** Long implicit time steps make tagged water arrive too early ({SI: the worked examples in brief}). Sub-steps reduce this effect without a change to the flow model. Each flow step is split into a chosen number of equal transport sub-steps. The flows stay constant within the flow step. The water volumes change linearly between the start and end of the step. <!-- src/gwsource/tracking.py module docstring (sub-steps: equal transport sub-steps of dt/m, flows constant, volumes interpolated linearly; per-step outputs at flow-step boundaries; m = 1 reproduces the unsplit scheme exactly) -->
