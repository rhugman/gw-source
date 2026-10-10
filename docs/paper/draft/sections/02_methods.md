# 2. Methods

## 2.1 Cells, flows, source and sink terms

Each active cell of the flow model is treated as fully mixed. The cells are linked by the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017), $q_{ij} \ge 0$ being the flow from cell $i$ to its neighbour $j$. Every other budget term (recharge, wells, drains, river and SFR leakage, constant heads, storage) is kept separate, by package and boundary, as a source term (water entering the cell) or a sink term (water leaving it). For each cell, $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the totals of its source and sink terms, and

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i$$

are its total inflow, total outflow and cell budget error (Fig. 1a). The cell budget error is reported, never forced to zero.

[[Figure 1]]

$d_i$ is the outflow of cell $i$ through the destination's sink terms, and $s_i$ its inflow through the selected source terms. A weak sink is a cell whose sink term takes only part of the cell's outflow. We use gross accounting by default: each sink term in a cell takes its share of the cell's total outflow, and the rest passes on to the neighbours. A weak-sink well is then credited with its pumping.

## 2.2 Backward and forward fractions

The backward fraction $F_i$ is the share of the water leaving cell $i$ that leaves the model through the destination. Because the cell is fully mixed, every outflow carries the same water, so

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}.$$

In words: the share of a cell's water that reaches the destination is the share leaving directly through it plus the outflow-weighted mean of its downstream neighbours' shares. Written for all cells at once, with $P_{ij} = q_{ij}/O_i$ the outflow shares,

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}, \tag{1}$$

where $\mathbf{I}$ is the identity matrix, $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms, and $\mathbf{D}$ assigns sink terms to destination groups (1 if the term belongs to the group, 0 otherwise). $\mathbf{S}\,\mathbf{D}$ is then $d_i/O_i$, one column per group.

The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source. It is built the same way from inflow shares, $Q_{ij} = q_{ji}/I_i$:

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}, \tag{2}$$

with $\mathbf{R}$ the share of each cell's inflow that enters through each source term and $\mathbf{T}$ assigning source terms to source groups. In words: the same rule, run downstream with inflow shares. Because each fraction is a share of the cell's own outflow or inflow, the cell budget errors stay out of the fractions.

From the fractions follow volumes: $F_i O_i$ is the water passing through cell $i$ that reaches the destination, $F_i$ times each source term the water entering there that reaches it, split by package, and $G_i$ times each sink term the water leaving there that came from the source. Giving every sink term its own group yields boundary-control maps: in every cell with outflow, the fractions to all sinks add up to 1. On the eight-cell example of Fig. 1b the well takes 6 of the 11 units passing through its cell, so $F = 6/11 = 0.55$ there and in the cells that drain only through it. <!-- README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS --> $F$ is a share of flow, not a probability (McLane and Cecan 2009).

## 2.3 Gross and net accounting

Net accounting is the reference method's bookkeeping (Foley and Black 2013). It uses the cell-to-cell flows only, with each cell's net source (cell-to-cell outflow minus inflow) in place of its source and sink terms, and fixes the destination cells at $F = 1$, so all water passing through them is credited to the destination. Which cells are fixed depends on the selection: a group selected by package or boundary term fixes only the cells where the selected terms flow in the traced direction (a sink backward, a source forward), while a cell or zone selection fixes all its cells. Net attribution, the source water credited to a well, then includes all the water passing a weak-sink well's cell, where gross accounting credits only the pumping: for the 5.0 m³/d well of tutorial 02, whose cell carries 33.7 m³/d, gross accounting gives $F = 0.15$ in the well cell and credits 5.0 m³/d, while net accounting credits 33.7 m³/d, 6.7 times the pumping (Fig. 1c). <!-- README_method.md Fig. 1c; tutorials/02_accounting (weak_well 33.667, 6.733) --> We keep net accounting as an option, to reproduce studies made with the reference method (§4.1); because the fixed cells change the matrix, it solves one destination group at a time.

## 2.4 Solution in flow order

Without flow loops, a cell's backward fraction depends only on cells downstream of it, and the system is solved cell by cell in flow order, from the destination upstream (backward) or from the sources downstream (forward); this is the reference method's sweep written as equations. Flow loops are groups of cells whose cell-to-cell flows form closed circuits, as with XT3D or where stream reaches exchange water with aquifer cells in both directions. Each loop is solved as one small block, the blocks in flow order; no connection is deleted. A closed recirculation loop, a group of cells with no outflow to any sink or to a cell outside the group, is found before the solve, given $F = 0$ and reported. (For the specialist: block-triangular sparse LU over the strongly connected components; the matrix is an M-matrix, each cell's outflow shares summing to at most 1, so the factorisation needs no reordering for stability, no pivoting.) Under gross accounting one factorisation serves every destination group.

## 2.5 Water-budget checks

Summing the cell equations, each multiplied by its outflow or inflow, cancels the cell-to-cell flows and leaves exact identities. The backward closure check is

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{3}$$

In words: the water entering the model through every source term, weighted by the share that reaches the destination and corrected by the cell budget errors, adds up to the destination inflow. The forward closure check is its mirror image, $\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i$: the water from a source, followed to every sink, adds up to that source's inflow. The forward–backward check,

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i, \tag{4}$$

says that the volume from a source to a destination is the same whether traced backward from the destination ($F$ times the source inflow) or forward from the source ($G$ times the destination outflow), once the cell budget errors are included. Mathematically it is a duality identity of systems (1) and (2). The boundary-control check tests that, in every cell with outflow, the backward fractions to all sink terms add up to 1.

Their error therefore measures the assembly and the solve, not the flow model. Without the cell budget error terms they hold only to within the model's budget error, since $0 \le F \le 1$ gives $|\sum_i F_i r_i| \le \sum_i |r_i|$. Under net accounting the closure check has no cell budget error term and tests the solve only in sum. Section 4.1 reports the errors reached.

## 2.6 Mean travel time

With $V_i$ the water volume of a cell (porosity times saturated volume) and $\tau_i = V_i/O_i$ its mean residence time, the mean travel time to the destination under full mixing is $m_i/F_i$, where

$$(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F} \tag{5}$$

and $\circ$ is the cell-by-cell product. In words: each cell adds its residence time, weighted by the share reaching the destination, and these are carried upstream with the outflow shares of $F$. Equation (5) reuses the factorisation of (1) (gross accounting only). It gives a mean over mixed water (Eulerian), not a particle's (Lagrangian) first arrival. The turnover time $\sum_i V_i F_i / \sum_i d_i$ equals the flow-weighted mean travel time of all water reaching the destination, once the cell budget errors are included.

## 2.7 Transient models: snapshots

As in the published descriptions of the reference method (Foley and Black 2013; Black and Foley 2013; Environment Agency 2019), a snapshot traces a time step as a steady state on its own flows: storage release is a source term and storage gain a sink term, and nothing is carried between steps (Fig. 1d, left). Destinations and sources are selected again on every step. Statistics over the steps (minimum, maximum, time-weighted mean, always/sometimes/never above a threshold, probability within a range, exceedance count) are accumulated step by step, so memory does not grow with their number. Snapshots describe each step's flow paths, but they have no travel lag, and the water released from storage has no origin. On the seasonal model of §4.4, storage release supplies up to 50 % of the well's water in summer. <!-- README_method.md Fig. 4a caption; studies/paper/transient_figure.py (summer storage peak 49.7 %); tutorial 08 §2 -->

## 2.8 Transient tracking through storage; water volumes

Transient tracking treats each cell (and each reach, lake or well added as an extra cell, §3.1) as a fully mixed volume of water $V_i$ and carries tagged water from step to step (Fig. 1d, right). The storage terms leave the list of source and sink terms and act through the change of volume, $V_i^{\mathrm{old}} - V_i^{\mathrm{new}} = \Delta t$ times the net storage release. With $c_i$ the tagged fraction of a cell's water, step $n$ of length $\Delta t$ is

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{6}$$

where $O_i$ now excludes storage. In words: tagged water at the end of a step is the tagged water at its start, plus what arrives from upstream cells and the selected source terms, less what leaves at the cell's end-of-step mix. The scheme is implicit, upstream weighted and free of dispersion, on the flow model's own steps; every step must be saved (OC BUDGET ALL), and the volume needs porosity. The cell budget error leaves (or enters) at the cell's own fraction (flow-error correction, as in MF6 GWT; Langevin et al. 2022; on by default). The solvers of §2.4 apply step by step, with one factorisation per step for all tagged groups. Initial water, the water in the model at the start of the simulation, can be tagged as its own group.

With the default "flow" volumes, the volume starts at porosity times saturated volume and is then carried by the storage flows, so every cell's water and tagged-water balance is exact. The "gwt" volumes are those of MF6 GWT (porosity times saturated volume at the end of each step); with them (6) is unit-concentration transport (Bedekar et al. 2024) in GWT with upstream weighting and no dispersion (Langevin et al. 2022), but where porosity differs from specific yield, tagged water appears or disappears at step boundaries. On test model 6 (porosity 0.3, specific yield 0.2) the two differ by at most $1.2 \times 10^{-4}$ in $c$ and $6 \times 10^{-3}$ in the backward fraction in time. <!-- PLAN Phase 4B notes, "Volume modes" --> Transport sub-steps are described in §3.2.

Forward tracking is not new. Hydraulic mixing cells step forward in time on a similar mixing-cell assumption, explicitly and on the flow model's own steps, first in stream and overland cells (Partington et al. 2011, 2013) and later in aquifer cells (Schilling et al. 2017 [check: not read]; Nogueira et al. 2022). All of these step forward only (Table 1, footnote 3); what we add is the backward tracking of §2.9.

## 2.9 Backward tracking in time

Backward tracking in time is not MODPATH backward tracking, in which particles run in reverse from the well. It is solved from the end of the simulation back to the start, with the transpose of each forward step's matrix, and is the discrete analogue of adjoint methods for continuous transport (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). Its result is the backward fraction in time $w_i^n$: the fraction of the water in cell $i$ at the start of step $n$, or entering it during the step, that leaves through the destination before the end of the simulation. The same run gives the fractions to other sinks and still stored at the end; with $w$ they add up to 1, less the flow-error correction (and the "gwt" step-boundary adjustments). With every source and the initial water tagged, it splits the destination's outflow by source term, time step and initial water (closure).

The transient forward–backward check is

$$\sum_n \Delta t \sum_i d_i^n c_i^n = \sum_n \Delta t \sum_i s_i^n w_i^n + \sum_i V_i^0 c_i^0 w_i^1, \tag{7}$$

with $V_i^0 c_i^0$ the tagged initial water. In words: the tagged water leaving through the destination, from forward tracking, equals the tagged inflow of every step and the tagged initial water, each times the fraction of it that later reaches the destination, from backward tracking. It is exact for either volume option, and §4.2 reports its errors.
