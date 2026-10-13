# 2. Methods

## 2.1 Cells, flows, source and sink terms

Each active cell of the flow model is treated as fully mixed. All water leaving such a cell carries the same mix of origins. Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017). The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. Every other budget term (recharge, wells, drains, river and SFR leakage, constant heads, storage) is kept separate, by package and boundary, as a source term (into the cell) or a sink term (out of it). With $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ the totals of a cell's source and sink terms (Fig. 1a),

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{1}$$

In words: a cell's total inflow $I_i$ is the water from its neighbours and its source terms. Its total outflow $O_i$ is the water to its neighbours and its sink terms. The cell budget error $r_i$ is the difference. It is reported, never forced to zero. The outflow of cell $i$ through the destination's sink terms is $d_i$. Its inflow through the selected source terms is $s_i$.

[[Figure 1]]

## 2.2 Backward and forward fractions

A contributing area rests on the backward fraction $F_i$, the share of the water leaving cell $i$ that leaves the model through the destination. Because the cell is fully mixed, all its outflows carry the same water. So

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}. \tag{2}$$

In words: the share of a cell's water that reaches the destination is the share leaving directly through it plus the outflow-weighted mean of its downstream neighbours' shares. In the eight-cell example of Fig. 1b, the well takes 6 of the 11 m³/d passing through its cell. So $F = 6/11 = 0.55$ there and in the cells that drain only through it. <!-- README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS (cell 6: 9 + 1 in from neighbours, 1 recharge; 6 to the well, 5 on) -->

Written for every cell at once, with $P_{ij} = q_{ij}/O_i$ the outflow shares, Eq. (2) becomes

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}, \tag{3}$$

where $\mathbf{I}$ is the identity matrix, $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms, and $\mathbf{D}$ marks which sink terms belong to which destination group. In words: Eq. (2), for every cell and every destination group at once.

The reverse question is where a cell's water came from. The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source. It is built in the same way from inflow shares, $Q_{ij} = q_{ji}/I_i$:

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}, \tag{4}$$

with $\mathbf{R}$ the share of each cell's inflow that enters through each source term and $\mathbf{T}$ marking which source terms belong to which source group. In words: the same rule, run downstream with inflow shares. The fractions give volumes. Of the water passing through cell $i$, $F_i O_i$ reaches the destination. Of the water entering through a source term, $F_i$ times the term reaches it. Of the water leaving through a sink term, $G_i$ times the term came from the source.

## 2.3 Gross and net accounting

Equation (2) needs a rule for a weak sink, a sink term that takes only part of its cell's outflow. Under gross accounting, our default, each sink term takes its share of the cell's total outflow. The rest passes on to the neighbours. A well is then credited with what it pumps, as in a transport model (Section 4.1).

Net accounting credits a sink with all the water that passes through its cell, as FlowSource does (Foley and Black 2013). It uses the cell-to-cell flows only, with each cell's net source (cell-to-cell outflow minus inflow) in place of its source and sink terms. The destination cells are fixed at $F = 1$ ({SI: net accounting, fixed cells}). In the example of Fig. 1b, net accounting fixes the well cell at $F = 1$. It credits the well with its 6 m³/d of pumping plus the 5 m³/d that flow on to the river.

The gap grows with the flow past the sink. In a three-layer example model, a well pumping 5.0 m³/d sits in a cell that carries 33.7 m³/d (Fig. 1c; {SI: example and test models}). <!-- tutorials/herebedragons.py::build_layered, LAYERED_WELLS (weak_well in layer 3 of 3, 5 m³/d); README_method.md Fig. 1c (whose cell carries 33.7 m³/d) --> Net accounting credits this well with 33.7 m³/d, 6.7 times its pumping. Gross accounting gives $F = 0.15$ in the well cell and credits the pumping. <!-- README_method.md Fig. 1c; tutorials/02_accounting (weak_well 33.667, 6.733) --> Net accounting is kept to reproduce studies made with FlowSource (Section 4.1).

## 2.4 Solution in flow order

Where water moves between cells in one direction only, the cells can be put in flow order, each after the cells its water flows to. The equations are then solved one cell at a time, from the destination upstream (backward) or from the sources downstream (forward). FlowSource uses such a flow-order pass.

Flow loops break this order. A flow loop is a group of cells among which water circulates, so that water leaving a cell can return to it. No ordering of the cells in a loop is purely downstream. A single pass in flow order therefore cannot solve a loop exactly. Loops arise with the XT3D (extended three-dimensional) option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water both ways.

Each loop is solved exactly as one small block of equations. The blocks are solved in flow order. No cell-to-cell flow is dropped to break a loop. A closed recirculation loop has no outflow to any sink or to a cell outside it. Such loops are found beforehand, given $F = 0$ and reported. Numerically, the solve is a block-triangular sparse LU factorisation over the strongly connected components. Each cell's outflow shares sum to at most 1. The matrix is therefore an M-matrix. Its factorisation needs no pivoting (reordering for numerical stability). Under gross accounting, one factorisation serves every destination group.

## 2.5 Water-budget checks

Three checks, which must hold exactly in any model, tell the user whether a trace is right. They follow from adding up the cell equations. The backward closure check is

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{5}$$

In words: the water entering through every source term, weighted by its share that reaches the destination and corrected by the cell budget errors, adds up to the destination inflow. The forward closure check, $\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i$, is its mirror image. The water from a source, followed to every sink, adds up to that source's inflow. The forward–backward check is

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{6}$$

In words: the volume from a source to a destination is the same traced backward ($F$ times the source inflow) or forward ($G$ times the destination outflow), once the cell budget errors are included. It holds because Eqs (3) and (4) mirror each other (a duality). The boundary-control check tests that, in every cell with outflow, the backward fractions to all sink terms add up to 1. Mapped, they show each cell's share going to each sink (boundary-control maps).

Because the flow model's budget error enters each check through $r_i$, a failed check points to the tracing itself. A budget term that was not read shows up instead as a large cell budget error.

## 2.6 Mean travel time

Fractions say how much water arrives, not when. With $V_i$ the water volume of a cell (porosity times saturated volume) and $\tau_i = V_i/O_i$ its mean residence time, the mean travel time from entering cell $i$ to leaving the model through the destination is $m_i/F_i$, where

$$(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F} \tag{7}$$

and $\circ$ is the cell-by-cell product. In words: each cell adds its residence time, weighted by the share of its water that reaches the destination. These times are carried upstream with the outflow shares of $F$. The travel time includes the time spent in the cell where the water leaves ({SI: travel-time identity}). Travel times are defined under gross accounting. Because they are means over mixed water, they should not be used alone to draw a time-of-travel zone (Section 6.5).

## 2.7 Transient models: snapshots and transient tracking

Existing full-mixing methods treat a transient model as a series of snapshots (Foley and Black 2013; Environment Agency 2019). A snapshot traces one time step as if its flows were steady. Storage release is a source term and storage gain a sink term. Nothing is carried from one step to the next (Fig. 1d, left). Snapshots show each step's flow paths. They have no travel time. The water released from storage has no known origin. On the seasonal example model of Section 4.4, storage release supplies up to 50 % of the well's water in summer. <!-- README_method.md Fig. 4a caption; studies/paper/transient_figure.py (summer storage peak 49.7 %); tutorial 08 §2 -->

Transient tracking, the extension used here, carries tagged water through storage from step to step (Fig. 1d, right). Each cell, and each reach, lake or well added as an extra cell (Section 3.1), is a fully mixed volume of water. Storage terms now change the cell's water volume from $V_i^{\mathrm{old}}$ at the start of a step to $V_i^{\mathrm{new}}$ at its end. With $c_i$ the tagged fraction of a cell's water, step $n$ of length $\Delta t$ is

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{8}$$

where $O_i$ now leaves out storage. In words: tagged water at the end of a step is the tagged water at its start, plus arrivals from upstream cells and selected source terms, less what leaves at the cell's end-of-step mix.

The scheme is implicit, with outflows at the cell's end-of-step mix. It is upstream weighted, with inflows at the mix of the cell they come from. No dispersion is added. The scheme runs on the flow model's own time steps. The budget of every step must therefore be saved (SAVE BUDGET ALL in the Output Control (OC) file). The water volume needs porosity. MODFLOW's cell budget never balances exactly. The small error $r_i$ is allowed to leave each cell carrying that cell's own mix of water. GWT handles the error the same way, as its flow-error correction (Langevin et al. 2022).

Each step is solved as in Section 2.4, with one matrix for all tagged groups. Initial water, the water in the model at the start of the simulation, can be tagged as its own group. The default "flow" volumes start at porosity times saturated volume and are then carried by the storage flows. Every cell's water balance and tagged-water balance is then exact. With the "gwt" volumes, porosity times saturated volume at the end of each step as in GWT, forward transient tracking is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). But where porosity differs from specific yield, tagged water appears or disappears at step boundaries (Section 4.4). Forward transient tracking is not new (Section 1; Table 1). What we add is backward tracking in time.

## 2.8 Backward tracking in time

Forward tracking says what a sink's water is made of. Backward tracking in time answers the reverse question for a time-limited protection zone: which water in the aquifer will reach the sink, and by when? It is not MODPATH backward tracking, in which particles run in reverse from the sink. Its result, the backward fraction in time $w_i^n$, is the fraction of the water in cell $i$ at the start of step $n$, or entering it during the step, that leaves through the destination before the end of the simulation. It is solved from the end of the simulation back to the start, each step with the forward step's equations transposed (inflow and outflow swap roles). It is the discrete counterpart of adjoint methods for continuous transport (Neupauer and Wilson 1999; Cornaton and Perrochet 2006).

The same run gives the fractions of each cell's water that leave through other sinks and that are still stored at the end. With $w$, they add up to 1, less the flow-error correction and, with "gwt" volumes, the step-boundary adjustments. With every source and the initial water tagged, the run splits the destination's outflow by source term, time step and initial water. The parts add up to that outflow (the closure check). This split tells a manager how much of the water a sink took was already stored at the start (Section 4.4). The transient forward–backward check is

$$\sum_n \Delta t \sum_i d_i^n c_i^n = \sum_n \Delta t \sum_i s_i^n w_i^n + \sum_i V_i^0 c_i^0 w_i^1, \tag{9}$$

with $V_i^0$ the water volume of cell $i$ at the start of the first step and $c_i^0$ its tagged initial fraction. In words: the tagged water the destination takes over the simulation (forward) equals each step's tagged inflow and the tagged initial water, each times its fraction that later reaches the destination (backward). The check holds exactly for either volume option (Section 4.2).
