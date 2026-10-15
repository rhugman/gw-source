## {SI: method in full}

Section 2 of the main text gives the backward fraction (Eq. 1) and describes the rest of the method in words. This text gives the method in full. It defines the cell budget, derives the equations and shows how they are solved and why the water-budget checks must hold. It then gives net accounting, the mean travel time and transient tracking in full. Equation numbers without an S refer to the main text. {SI: method schematic} illustrates the method. <!-- assembled in alt round 1 from the si/B.md items "net accounting, fixed cells", "travel-time identity", "solution of the linear systems" and "water volume options", and from previous/02_methods.md §§2.3, 2.4, 2.5, 2.7 and 2.8 (main-text Methods of the earlier draft) -->

### The backward and forward fractions

Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017). The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. All other budget terms, such as recharge, wells, rivers and storage, are kept separate by package and boundary. A term that brings water into a cell is a source term. A term that takes water out is a sink term. If $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the totals of a cell's source and sink terms, its total inflow, total outflow and cell budget error are ({SI: method schematic}a)

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{S1}$$

The cell budget of a MODFLOW model never balances exactly, so $r_i$ is small but not zero. <!-- evidence: src/gwsource/diagnostics.py (cell_residual, budget_error); full draft sections/02_methods.md, Eq. (1) --> The outflow of cell $i$ through the destination is $d_i$. The inflow of cell $i$ through the source is $s_i$.

Full mixing means that all water leaving a cell has the same mix of origins and fates. Take the water that leaves cell $i$ in one day. The part $d_i$ leaves through the destination directly. The part $q_{ij}$ goes to neighbour $j$, and a share $F_j$ of it later leaves through the destination. So the volume of water leaving cell $i$ that ends at the destination is

$$F_i\, O_i = \sum_j q_{ij}\, F_j + d_i . \tag{S2}$$

Dividing by $O_i$ gives Eq. (1). Let $P_{ij} = q_{ij}/O_i$ be the share of cell $i$'s outflow that goes to cell $j$. Written for every cell at once, Eq. (1) becomes

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{S3}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group. Under gross accounting, a sink term $k$ in cell $i$ takes the share $|q_k|/O_i$ of the cell's outflow. These shares are the entries of $\mathbf{S}$. A cell with no outflow is given $F = 0$. <!-- src/gwsource/assemble.py module docstring (gross accounting rows; cells with O_i = 0 get an identity row and zero right-hand side) -->

The forward fraction follows from the inflow in the same way. The water entering cell $i$ in one day comes from the neighbours and from the source and sink terms. A share $G_j$ of the water from neighbour $j$ came from the source. All of $s_i$ came from it. So

$$G_i\, I_i = \sum_j q_{ji}\, G_j + s_i . \tag{S4}$$

Dividing by $I_i$ and writing the result for every cell, with the inflow shares $Q_{ij} = q_{ji}/I_i$, gives

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{S5}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group. A cell with no inflow is given $G = 0$. <!-- src/gwsource/assemble.py (forward rows G_i - sum_j (q_ji/I_i) G_j = sum_{k in S} q_k / I_i) -->

### Volumes

A fraction says what share of a cell's water reaches the destination, but not how much water that is. A fraction times a flow gives a volume of water per unit time. The volume through cell $i$ is $F_i O_i$. It is the part of the water passing through the cell that reaches the destination. The volume from cell $i$ is $F_i$ times the cell's inflow through its source terms. It is the water entering the model in that cell that reaches the destination. Summing the volume from over all cells, package by package, splits the destination's water by source (Section 4, Fig. 2b). A forward trace gives the matching volumes from $G$. They split a source's water by where it leaves the model ({SI: where each source's water goes}). <!-- evidence: src/gwsource/metrics.py docstring (volume_through = F x O, gross; volume_from, volume_from_by_term; forward volume_through = G x I, volume_to, volume_to_by_term); full draft Section 2.3 -->

### Why the water-budget checks hold exactly

The checks of Section 2 follow from adding up Eqs. (S2) and (S4) over all cells. Adding Eq. (S2) over all cells gives $\sum_i F_i O_i$ on the left. On the right, each flow $q_{ij}$ appears once, multiplied by the $F$ of the cell it enters. Summed over the cells it leaves, the flow into cell $j$ is $\sum_i q_{ij} = I_j - \mathrm{Src}_j$. So

$$\sum_i F_i\, O_i = \sum_j F_j \left(I_j - \mathrm{Src}_j\right) + \sum_i d_i .$$

Moving terms and using $r_i = I_i - O_i$ gives the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{S6}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. Adding Eq. (S4) over all cells gives the forward closure check in the same way:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i . \tag{S7}$$

The forward–backward check is a duality identity of the two systems. Multiply Eq. (S2) by $G_i$ and Eq. (S4) by $F_i$, and add each over all cells. Both results then hold the same double sum of the cell-to-cell flows, $\sum_i \sum_j q_{ij}\, G_i\, F_j$. It cancels when one result is subtracted from the other. What remains is the forward–backward check

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{S8}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included.

The boundary-control check traces every sink term of the model, each as its own destination. The sum of their fractions solves Eq. (1) with $d_i$ replaced by the total sink outflow $\mathrm{Snk}_i$. A value of 1 in every cell solves that equation, because $\sum_j q_{ij} + \mathrm{Snk}_i = O_i$. The solution is unique outside closed recirculation loops, which are described below. So the fractions to all sinks add up to 1 in every other cell with outflow.

The checks include the cell budget errors $r_i$. So they hold exactly for any flow field, also one that does not balance. The errors reported by the code are then round-off, unless the tracing itself is wrong. Without the error terms, the checks would hold only to within the budget error of the flow model. The code reports both values. <!-- src/gwsource/diagnostics.py module docstring (exact identities; "with the residual term the checks hold to round-off; without it they hold to within the model's budget error"); src/gwsource/diagnostics.py Check (error and error_without_residual) -->

### Solution of the linear systems

Equation (1) gives a cell's $F$ from the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource (Foley and Black 2013).

Flow loops break this order. A flow loop is a group of cells among which water circulates, so that water leaving a cell can return to it. No order of the cells in a loop is purely downstream, so a single pass cannot solve a loop exactly. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each loop. Foley and Black (2013) expect this to change the results very little. <!-- references/docs/text/2013_Foley_Black_FlowSource_DAG_algorithms.txt, cycle section: "Cycles do, albeit rarely, occur"; "multilayer models which have stability problems"; "the edge with the lowest volume is removed"; "negligible in all but the rarest cases" --> We keep every flow and solve each loop exactly.

Equations (S3) and (S5) are solved in flow order. Where the cell-to-cell flows contain no loop, the matrix is reordered to triangular form, with every cell after the cells it depends on. It is then solved by substitution. This is the flow-order algorithm of FlowSource in matrix form. Where there are loops, the matrix is reordered to block-triangular form. Each block is one strongly connected component of the flows, which is either one flow loop or one single cell. The blocks are in flow order. The matrix is then factorised once by sparse LU decomposition in that order. The extra non-zero entries that a factorisation creates stay inside the loop blocks. So a model of a million cells with thousands of small loops is factorised in well under a second. <!-- src/gwsource/solve.py module docstring (topological and block solvers; "a 1M-cell graph with thousands of small cycles factorises in well under a second") -->

Each cell's outflow shares add up to at most 1. So $\mathbf{I} - \mathbf{P}$ is a weakly row-diagonally dominant M-matrix. Its factorisation therefore needs no pivoting, the row swaps that otherwise guard against the growth of round-off. The matrix is singular only on a closed recirculation loop. This is a set of cells with no outflow to any sink or to a cell outside the set. Water in such a loop never reaches a sink. These loops are found before the solve, given $F = 0$ and reported. No flows are deleted. Under gross accounting, one factorisation serves every destination group. It is reused for the travel-time system of Eq. (S10). <!-- src/gwsource/solve.py module docstring ("Pivoting is not needed: I - P is a (weakly) row-diagonally dominant M-matrix"; isolate_closed_loops; factorize() reuse for gwsource.traveltime) -->

The code also reports every flow loop, with the flow that goes round it and its share of the flow through the model. A large loop, or one that carries much water, may point to a problem in the flow model, such as poor convergence or extreme anisotropy. <!-- src/gwsource/diagnostics.py module docstring (cycle report: flow that goes round each strongly connected set, by cycle cancelling, and its share of the model throughflow) -->

### Net accounting

Net accounting reproduces the bookkeeping of FlowSource (Foley and Black 2013). It works from the cell-to-cell flows only. Each cell's source and sink terms are replaced by one net term, equal to its cell-to-cell outflow minus its cell-to-cell inflow. With $I^e_i$ and $O^e_i$ the cell-to-cell inflow and outflow of cell $i$, the net term is $n_i = O^e_i - I^e_i$. The water passing through the cell is then $T_i = I^e_i + \max(n_i, 0)$. Outside the destination cells, the backward fraction is

$$f_i = \frac{1}{T_i} \sum_j q_{ij}\, f_j . \tag{S9}$$

The destination cells are fixed at $f = 1$. Their outflows to other cells are ignored. A forward trace works in the same way on the reversed flows, with the source cells fixed at $g = 1$. <!-- src/gwsource/assemble.py module docstring (net accounting: s_i = O^edges_i - I^edges_i, T_i = I^edges_i + max(s_i, 0); destination cells absorbing; forward on the reversed graph); PLAN §2.4 -->

Which cells are fixed depends on how the group was selected. A pure cell or zone selection fixes all its cells, as FlowSource defines groups (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace, these are the cells where a selected term is a sink. In a forward trace, they are the cells where it is a source. This also holds when a term criterion is combined with cells or a zone. A cell with selected terms of both signs is fixed in both directions. A group with no such term fixes no cell, so every fraction is 0. A well listed at zero rate, a drain above the water table, or a losing river cell in a backward trace is therefore not fixed. On a stream network, a package selection fixes only the reaches whose records flow in the traced direction. To fix a whole stream, select its reaches as cells. <!-- PLAN §2.4; src/gwsource/trace.py::net_fixed_cells -->

Net accounting has no cell budget error term. The water it attributes to a group counts each passage once. It is the water passing through the fixed cells, less the water passing from one fixed cell to another, and less the water that leaves the group and reaches it again. Its closure check compares the volume from the sources with this net inflow. The check tests the sum of the equations over the cells outside the group, not each cell. Its error is exactly the sum of those cells' equation errors. <!-- PLAN §2.4; src/gwsource/assemble.py and diagnostics.py docstrings --> Net accounting solves one destination group at a time, because each group fixes its own cells. As an option, it can delete the smallest flow in each flow loop, as FlowSource does. This option exists only to compare with studies made with FlowSource. <!-- src/gwsource/config.py (remove_cycles: net mode only; delete the smallest edge of each flow cycle) -->

### Mean travel time

Fractions say how much water arrives, not when. Let $V_i$ be the volume of water in cell $i$. It is porosity times the saturated volume of the cell. Fractions need no porosity, but travel times do. A parcel of water that enters a fully mixed cell stays there for a random time. The mean of that time is $\tau_i = V_i/O_i$. Under full mixing, the time a parcel spends in a cell does not depend on the route by which it leaves. Let $m_i$ be the mean travel time from entering cell $i$ to leaving the model, counted only for water that leaves through the destination, and weighted by $F_i$. A parcel spends on average $\tau_i$ in cell $i$ and then moves to cell $j$ with probability $P_{ij}$. So

$$m_i = \tau_i\, F_i + \sum_j P_{ij}\, m_j . \tag{S10}$$

In matrix form this is $(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F}$, where $\circ$ is the cell-by-cell product. The mean travel time of the water that reaches the destination is $m_i/F_i$. It is defined only under gross accounting, and only where $F_i$ is above a small threshold. <!-- src/gwsource/traveltime.py module docstring (m_i = E[R_i] P(D) + sum_j P_ij m_j; mean_time = m / F, NaN where F <= fraction_threshold; gross accounting only) -->

Multiplying each cell's travel-time equation (Eq. S10) by its outflow and adding over all cells gives, with the cell budget errors $r_i$,

$$\sum_i \mathrm{Src}_i\, m_i - \sum_i r_i\, m_i = \sum_i V_i F_i . \tag{S11}$$

Divided by the destination inflow $\sum_i d_i$, the right-hand side is the turnover time. This is the volume of water that ends at the destination divided by the destination's inflow. By the backward closure check (Eq. S6), the left-hand side divided by the same inflow is the flow-weighted mean travel time of all water reaching the destination. The two are therefore equal once the cell budget errors are included. <!-- src/gwsource/traveltime.py docstring, "Exact identity (backward)" -->

The mean travel time $m_i/F_i$ includes the time spent in the cell where the water leaves, for a well its own cell. The time until the water enters that cell is $(m_i - x_i)/F_i$, where $x$ solves $(\mathbf{I} - \mathbf{P})\,\mathbf{x} = \boldsymbol{\tau} \circ (\mathbf{S}\,\mathbf{D})$. Here $x$ is the mean time spent in the cell of exit, weighted by the share leaving there through the destination. Particle trackers that stop particles on entering a sink cell (MODFLOW 6 PRT, MODPATH) measure this second time. It is the full-mixing time that is compared with particles in {SI: verification errors per check and model} and in {SI: mean travel time to the well}. <!-- src/gwsource/traveltime.py docstring (mean_time_to_exit_cell) --> On test model 1, the water reaching the well takes 9,607 d on average including its time in the well cell, and 9,574 d to enter that cell. <!-- PLAN Phase 3 notes, PRT (model 1: Eulerian 9574 d to the exit cell, 9607 d including it) -->

### Transient tracking

Transient tracking carries tagged water from step to step (Section 2; {SI: method schematic}d). Each cell, and each reach, lake or well added as an extra cell (Section 3), is a fully mixed volume of water. The storage terms of the flow model are not traced as source or sink terms. They change the volume of water in the cell instead. In step $n$, of length $\Delta t$, the volume changes from $V_i^{\mathrm{old}}$ to $V_i^{\mathrm{new}}$. The change equals the storage release over the step. The tagged water in the cell at the end of the step is the tagged water at the start, plus what arrives, less what leaves. Let $c_i$ be the share of a cell's water that is tagged. Step $n$ of length $\Delta t$ is then

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{S12}$$

where $O_i$ now leaves out storage. <!-- src/gwsource/tracking.py module docstring, forward scheme, eq. (1) -->

As in MODFLOW 6 GWT, the scheme is implicit in time. So outflows over the step carry the cell's mix at the end of the step. It is upstream weighted. So inflows carry the mix of the cell they come from. It adds no dispersion. It runs on the flow model's own time steps, so the budget of every step must be saved (SAVE BUDGET ALL in the Output Control file). <!-- previous/02_methods.md §2.7; src/gwsource/tracking.py module docstring -->

The cell budget error $r_i$ leaves the cell, or enters it, at the cell's own mix of water. GWT treats the error in the same way, which Langevin et al. (2022) call the flow-imbalance correction. With this correction, Eq. (S12) leaves every tagged fraction at 1 when every source and the initial water are tagged. <!-- src/gwsource/tracking.py module docstring (a = 1: FLOW_IMBALANCE_CORRECTION, Langevin et al. 2022 eq. 2-14/2-15; c = 1 solves (1) when every source and the initial water are tagged) -->

For all cells, step $n$ is one set of linear equations,

$$\mathbf{A}^n \mathbf{c}^n = \mathbf{B}^n \mathbf{c}^{n-1} + \Delta t\, \mathbf{s}^n . \tag{S13}$$

$\mathbf{B}^n$ is a diagonal matrix of the start volumes $V_i^{\mathrm{old}}$. $\mathbf{A}^n$ has $V_i^{\mathrm{new}} + \Delta t\,(O_i + r_i)$ on its diagonal and $-\Delta t\, q_{ji}$ in row $i$, column $j$. Each row of $\mathbf{A}^n$ adds up to $V_i^{\mathrm{old}} + \Delta t\, \mathrm{Src}_i$, which is not negative. So $\mathbf{A}^n$ is an M-matrix, like $\mathbf{I} - \mathbf{P}$. Each step is solved in flow order as above. Because every cell holds water, no flow loop makes the matrix singular. One factorisation per step serves every tagged group. <!-- src/gwsource/tracking.py module docstring (A^n c^n = B^n c^(n-1) + dt s^n; row sums V^old + dt Src >= 0; no closed-loop isolation needed since V > 0) -->

The water in the model at the start of the simulation can be tagged as its own group, the initial water. It starts with $c = 1$ in every cell and has no source. <!-- src/gwsource/tracking.py module docstring (tagged initial water) -->

#### Water volume options

Transient tracking needs the water volume of every cell at the start and end of each step. The code offers two options. In the default, called "flow", each volume starts at porosity times saturated volume. It then changes only by the storage flows of the flow model. Every cell's water balance and tagged-water balance then close exactly. In the "gwt" option, the volume is reset to porosity times saturated volume at the end of each step, as in MODFLOW 6 GWT. Forward transient tracking with this option is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, the reset volume does not match the storage flows. Tagged water then appears or disappears at step boundaries. The code reports this volume. On the 30-year seasonal example model, with one transport step per flow step, the forward fractions of the two options differ by up to 1.9 × 10⁻⁴ and the backward fractions by up to 3.7 × 10⁻³. The volume that appears or disappears on that model is given in {SI: transient checks on the seasonal example model}. We recommend the default unless a result must match a GWT run. <!-- moved from §2.7 in round 5 (v6 §2.8 text); src/gwsource/tracking.py module docstring (volumes: "gwt" and "flow"); README_method.md Fig. 4 caption ("the two options differ by less than 2 × 10⁻⁴"); tutorials/08_transient_tracking/08_transient_tracking.ipynb §7, cell 20 ("largest difference between the modes: 1.9e-04 in c, 3.7e-03 in w (any cell, any step)"), added in the cleanup pass -->

With "flow" volumes, a cell whose volume would fall below zero stops the run with an error. This can happen where porosity is much smaller than the specific yield. <!-- src/gwsource/tracking.py module docstring ("A node whose volume would become negative ... stops the run with an error") -->

#### Transport sub-steps

Implicit time steps spread tagged water in time, by an amount that grows with the step length. Long steps therefore make tagged water arrive too early ({SI: transient checks on the seasonal example model}). Sub-steps reduce this effect without a change to the flow model. Each flow step is split into $m$ equal transport sub-steps of length $\Delta t/m$. The flows stay constant within the flow step. The water volumes change linearly between $V^{\mathrm{old}}$ and $V^{\mathrm{new}}$, which is what a constant storage flow gives. Outputs are reported at the ends of the flow steps. With $m = 1$ the scheme is the one above. <!-- src/gwsource/tracking.py module docstring (sub-steps: equal transport sub-steps of dt/m, flows constant, volumes interpolated linearly; per-step outputs at flow-step boundaries; m = 1 reproduces the unsplit scheme exactly) -->

### Backward tracking in time

Backward tracking in time is the discrete adjoint of Eq. (S13) (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). The tagged water that the destination takes over the whole simulation is $J = \sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n$, where $\mathbf{d}^n$ holds the destination outflow of each cell in step $n$. The backward fraction in time $\mathbf{w}^n$ solves, from the last step $N$ back to the first,

$$\left(\mathbf{A}^n\right)^{\mathsf T} \mathbf{w}^n = \Delta t^n\, \mathbf{d}^n + \mathbf{B}^{n+1} \mathbf{w}^{n+1}, \qquad \mathbf{w}^{N+1} = \mathbf{0} . \tag{S14}$$

The transpose swaps the roles of inflow and outflow. So the solve runs against the flow, from the end of the simulation back to the start. $w_i^n$ is the share of the water in cell $i$ at the start of step $n$, together with the water entering the cell during the step, that leaves through the destination before the simulation ends. The implicit scheme mixes these two kinds of water alike, so one value describes both. <!-- src/gwsource/tracking.py module docstring, backward (adjoint) scheme, eq. (2) -->

The same backward equations give the other fates of the water. With every remaining sink as the destination, they give the fraction that leaves through any sink. With no destination, and the end volumes as the condition at the last step, they give the fraction still stored at the end. The fraction to the destination, the fraction to other sinks and the fraction still stored add up to 1 in every cell and step. The flow-imbalance correction and, with "gwt" volumes, the step-boundary changes remove a small remainder. The code reports this remainder. <!-- src/gwsource/tracking.py module docstring (fraction_through + fraction_to_other_sinks + fraction_in_storage_at_end + fraction_unaccounted = 1) -->

The transient forward–backward check follows from Eqs. (S13) and (S14). Multiply Eq. (S13) by $\mathbf{w}^n$ and Eq. (S14) by $\mathbf{c}^n$, and add each over all steps. The terms in $\mathbf{A}^n$ are equal and cancel. The terms in $\mathbf{B}$ cancel from one step to the next, except at the first step. What remains is

$$\sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n = \sum_n \Delta t^n\, \mathbf{s}^n \cdot \mathbf{w}^n + \sum_i V_i^{\mathrm{old},1}\, c_i^0\, w_i^1 . \tag{S15}$$

The check says that the tagged water the destination takes, found by forward tracking, equals the tagged inflow and the tagged initial water, each multiplied by its share that later reaches the destination. It holds exactly for either volume option and with or without sub-steps. With every source and the initial water tagged, the right-hand side splits the destination's outflow by source term, time step and initial water. <!-- src/gwsource/tracking.py module docstring (duality identity (3), exact for any volumes and any a; volume_from per node and step, initial_volume_from); previous/02_methods.md §2.8 eq. (10) -->

With flows held constant for long enough, the tagged fraction $c$ tends to the steady forward fraction $G$, and $w$ at the first step tends to the steady backward fraction $F$. The storage terms are then zero, so the tracked system and the steady system have the same flows. Test model 10 checks this limit ({SI: verification errors per check and model}). <!-- src/gwsource/tracking.py module docstring ("Limit: with flows held constant for long enough, c^n tends to the steady source_fraction ... and w^1 to the steady fraction_through") -->
