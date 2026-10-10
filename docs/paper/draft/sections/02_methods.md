# 2. Methods

## 2.1 Cells, flows, source and sink terms

Each active cell of the flow model is treated as fully mixed. Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017); the flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. Every other budget term (recharge, wells, drains, river and streamflow-routing (SFR) leakage, constant heads, storage) is kept separate, by package and boundary, as a source term (into the cell) or a sink term (out of it). With $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ the totals of a cell's source and sink terms,

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i$$

are its total inflow, total outflow and cell budget error (Fig. 1a). The cell budget error is reported, never forced to zero.

[[Figure 1]]

The outflow of cell $i$ through the destination's sink terms is $d_i$, and its inflow through the selected source terms is $s_i$.

## 2.2 Backward and forward fractions

The backward fraction $F_i$ is the share of the water leaving cell $i$ that leaves the model through the destination. Because the cell is fully mixed, all its outflows carry the same water, so

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}.$$

In words: the share of a cell's water that reaches the destination is the share leaving directly through it plus the outflow-weighted mean of its downstream neighbours' shares. In the eight-cell example of Fig. 1b, the well takes 6 of the 11 m³/d passing through its cell, so $F = 6/11 = 0.55$ there and in the cells that drain only through it. <!-- README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS (cell 6: 9 + 1 in from neighbours, 1 recharge; 6 to the well, 5 on) --> The backward fraction is a share of flow, not a probability.

Written for all cells at once, with $P_{ij} = q_{ij}/O_i$ the outflow shares,

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}, \tag{1}$$

where $\mathbf{I}$ is the identity matrix, $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms, and $\mathbf{D}$ marks which sink terms belong to which destination group. In words: the cell rule above, for every cell and every destination group at once.

The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source. It is built in the same way from inflow shares, $Q_{ij} = q_{ji}/I_i$:

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}, \tag{2}$$

with $\mathbf{R}$ the share of each cell's inflow that enters through each source term and $\mathbf{T}$ marking which source terms belong to which source group. In words: the same rule, run downstream with inflow shares.

The fractions give volumes: the water passing through cell $i$ that reaches the destination ($F_i O_i$), the water entering through each source term that reaches it ($F_i$ times the term), and the water leaving through each sink term that came from the source ($G_i$ times the term).

## 2.3 Gross and net accounting

Under gross accounting, the default, each sink term in a cell takes its share of the cell's total outflow and the rest passes on to the neighbours, as in equation (1). A well is then credited with what it pumps, as in a transport model (§4.1). Net accounting is the reference method's bookkeeping (Foley and Black 2013). It uses the cell-to-cell flows only, with each cell's net source (cell-to-cell outflow minus inflow) in place of its source and sink terms, and fixes the destination cells at $F = 1$. Net accounting credits a weak-sink well with all the water passing its cell (its net attribution): 33.7 m³/d, or 6.7 times its 5.0 m³/d pumping, in the accounting tutorial (tutorial 02; §9), where gross accounting gives $F = 0.15$ in the well cell and credits the pumping (Fig. 1c). <!-- README_method.md Fig. 1c; tutorials/02_accounting (weak_well 33.667, 6.733) --> For a group selected by package or boundary, only the cells where the selected terms flow in the traced direction are fixed {SI: net accounting, fixed cells}. Net accounting is kept to reproduce studies made with the reference method (§4.1).

## 2.4 Solution in flow order

Without flow loops, a cell's backward fraction depends only on cells downstream of it, and the equations are solved cell by cell in flow order, from the destination upstream (backward) or from the sources downstream (forward), as in the reference method's flow-order pass. Flow loops are groups of cells whose cell-to-cell flows form closed circuits, as with the XT3D option or where stream reaches exchange water with aquifer cells in both directions. Each loop is solved as one small block, and the blocks in flow order; no connection is deleted. Closed recirculation loops, with no outflow to any sink or to a cell outside the loop, are found beforehand, given $F = 0$ and reported. For the specialist, the method is a block-triangular sparse LU factorisation over the strongly connected components; the matrix is an M-matrix, so the factorisation needs no pivoting, and under gross accounting one factorisation serves every destination group.

## 2.5 Water-budget checks

Adding the cell equations, each multiplied by its outflow (backward) or inflow (forward), cancels the cell-to-cell flows and leaves three identities. The backward closure check is

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{3}$$

In words: the water entering through every source term, weighted by its share that reaches the destination and corrected by the cell budget errors, adds up to the destination inflow. The forward closure check, $\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i$, is its mirror image: the water from a source, followed to every sink, adds up to that source's inflow. The forward–backward check is

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{4}$$

In words: the volume from a source to a destination is the same traced backward ($F$ times the source inflow) or forward ($G$ times the destination outflow), once the cell budget errors are included. Mathematically it is a duality identity of equations (1) and (2). The boundary-control check tests that, in every cell with outflow, the backward fractions to all sink terms add up to 1; mapped, these fractions show each cell's share going to the river, to each well and so on (boundary-control maps).

The flow model's budget error enters these identities through $r_i$, so their errors measure only how the equations are built and solved. A failed check therefore points to the tracing itself; a budget term that was not read shows up instead as a large cell budget error. Under net accounting the net sources take up the cell budget errors, so the closure check has no such term and tests only the sum over all cells.

## 2.6 Mean travel time

With $V_i$ the water volume of a cell (porosity times saturated volume) and $\tau_i = V_i/O_i$ its mean residence time, the mean travel time from entering cell $i$ to leaving the model through the destination is $m_i/F_i$, where

$$(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F} \tag{5}$$

and $\circ$ is the cell-by-cell product. In words: each cell adds its residence time, weighted by the share of its water that reaches the destination, and these times are carried upstream with the outflow shares of $F$. This time includes the residence in the cell where the water leaves, for a well its own cell; particles stopped on entering a well cell measure the time to enter it, $m_i/F_i$ less the mean residence there. Travel times are defined under gross accounting. Being means over mixed water, they should not be used alone to draw a time-of-travel zone (§6). {SI: travel-time identity}

## 2.7 Transient models: snapshots

As in the published descriptions of the reference method (Foley and Black 2013; Environment Agency 2019), a snapshot traces one time step as a steady state on its own flows. Storage release is a source term and storage gain a sink term, and nothing is carried between steps (Fig. 1d, left). Statistics over the steps are accumulated step by step (§3.2). Snapshots describe each step's flow paths, but they have no travel lag, and the water released from storage has no origin. On the seasonal model of §4.4, storage release supplies up to 50 % of the well's water in summer. <!-- README_method.md Fig. 4a caption; studies/paper/transient_figure.py (summer storage peak 49.7 %); tutorial 08 §2 -->

## 2.8 Transient tracking through storage; water volumes

Transient tracking treats each cell, and each reach, lake or well added as an extra cell (§3.1), as a fully mixed volume of water, and carries tagged water from step to step (Fig. 1d, right). Storage terms are no longer source or sink terms; they change the cell's water volume from $V_i^{\mathrm{old}}$ at the start of a step to $V_i^{\mathrm{new}}$ at its end. With $c_i$ the tagged fraction of a cell's water, step $n$ of length $\Delta t$ is

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{6}$$

where $O_i$ now leaves out storage. In words: tagged water at the end of a step is the tagged water at its start, plus arrivals from upstream cells and selected source terms, less what leaves at the cell's end-of-step mix. The scheme is implicit, upstream weighted and free of dispersion, on the flow model's own time steps, so every step must be saved (OC BUDGET ALL); the water volume needs porosity. The cell budget error leaves at the cell's own fraction, the flow-error correction of GWT (Langevin et al. 2022).

Each step is solved as in §2.4, with one matrix for all tagged groups. Initial water, the water in the model at the start of the simulation, can be tagged as its own group. With the default "flow" volumes, the volume starts at porosity times saturated volume and is then carried by the storage flows, so every cell's water balance and tagged-water balance is exact. With the "gwt" volumes, porosity times saturated volume at the end of each step as in GWT, forward transient tracking is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, tagged water then appears or disappears at step boundaries, because GWT recomputes each volume from the new heads with porosity, while the storage flows use specific yield. On test model 6 (§4.1) the two options differ by at most 1.2 × 10⁻⁴ in $c$ and 6 × 10⁻³ in the backward fraction in time (§2.9). <!-- PLAN Phase 4B notes, "Volume modes" (porosity 0.3, Sy 0.2) --> Forward transient tracking is not new (§1; Table 1); §2.9 adds backward tracking in time.

## 2.9 Backward tracking in time

Backward tracking in time is not MODPATH backward tracking, in which particles run in reverse from the well. Its result, the backward fraction in time $w_i^n$, answers the question: of the water in cell $i$ at the start of step $n$, or entering it during the step, what fraction leaves through the destination before the end of the simulation? It is solved from the end of the simulation back to the start, each step with the forward step's equations transposed (inflow and outflow swap roles, as between equations (1) and (2)). It is the discrete analogue of adjoint methods for continuous transport (Neupauer and Wilson 1999; Cornaton and Perrochet 2006).

The same run gives the fractions leaving through other sinks and still stored at the end; with $w$ they add up to 1, less the flow-error correction and, with "gwt" volumes, the step-boundary losses. With every source and the initial water tagged, it splits the destination's outflow by source term, time step and initial water, and the parts add up to that outflow (the closure check). The transient forward–backward check is

$$\sum_n \Delta t \sum_i d_i^n c_i^n = \sum_n \Delta t \sum_i s_i^n w_i^n + \sum_i V_i^0 c_i^0 w_i^1, \tag{7}$$

with $V_i^0$ the water volume of cell $i$ at the start of the first step and $c_i^0$ its tagged initial fraction. In words: the tagged water the destination takes over the simulation (forward) equals each step's tagged inflow and the tagged initial water, each times its fraction that later reaches the destination (backward). The check is exact for either volume option (§4.2).
