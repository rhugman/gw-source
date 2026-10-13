# 2. Methods

## 2.1 Cells, flows, source and sink terms

Each active cell is treated as fully mixed (Section 1). Cells exchange water through the cell-to-cell flows of the MODFLOW 6 budget file (FLOW-JA-FACE; Langevin et al. 2017). The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. All other budget terms, such as recharge, wells, rivers and storage, are kept separate by package and boundary. A term that brings water into a cell is a source term. A term that takes water out is a sink term. If $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the totals of a cell's source and sink terms, its total inflow, total outflow and cell budget error are (Fig. 1a)

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{1}$$

The cell budget error is reported and never forced to zero.

A trace is one solve of the method for chosen destinations or sources. The destination is the sink terms traced to, such as one well's pumping. Sink terms traced as one unit, such as all the wells of a wellfield, form a destination group. The outflow of cell $i$ through a destination is $d_i$. The source is the source terms traced from, and $s_i$ is the inflow of cell $i$ through them.

[[Figure 1]]

## 2.2 Backward and forward fractions

A contributing area is drawn from the backward fraction $F_i$. $F_i$ is the share of the water leaving cell $i$ that later leaves the model through the destination. Because the cell is fully mixed, all its outflows carry the same water. So

$$F_i = \sum_j \frac{q_{ij}}{O_i}\, F_j + \frac{d_i}{O_i}. \tag{2}$$

In words: the share of a cell's water that reaches the destination is the share leaving directly through it plus the outflow-weighted mean of its downstream neighbours' shares. In the eight-cell example of Fig. 1b, the well takes 6 of the 11 m³/d passing through its cell. So $F = 6/11 = 0.55$ in the well cell and in the cells whose water all flows through it. <!-- README_method.md Fig. 1b; studies/paper/method_figures.py GRAPH_EDGES, GRAPH_TERMS (cell 6: 9 + 1 in from neighbours, 1 recharge; 6 to the well, 5 on) -->

Let $P_{ij} = q_{ij}/O_i$ be the share of cell $i$'s outflow that goes to cell $j$. For every cell at once, Eq. (2) then becomes

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}, \tag{3}$$

where $\mathbf{I}$ is the identity matrix, $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms, and $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group.

The forward fraction $G_i$ answers the reverse question. It is the share of the water entering cell $i$ that came from the source. It follows in the same way from the inflow shares $Q_{ij} = q_{ji}/I_i$:

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}, \tag{4}$$

where $\mathbf{R}$ holds the share of each cell's inflow that enters through each source term and $\mathbf{T}$ marks which source terms belong to which source group. A fraction times a flow gives a volume of water. For example, $F_i O_i$ is the water passing through cell $i$ that reaches the destination.

## 2.3 Gross and net accounting

Equation (2) needs a rule for weak sinks (Section 1). Our default is gross accounting. Each sink term then takes its share of the cell's total outflow, and the rest passes on to the neighbours. A well is credited with what it pumps, as in MODALL (Potter et al. 2008) and in a transport model (Section 4.1). <!-- Potter p. 336, Fig. 1: the sink cell's capture fraction is the well's outflow over the cell's total inflow, drawn for a weak sink -->

Net accounting credits a sink with all the water that passes through its cell, as FlowSource does (Foley and Black 2013). The destination cells are fixed at $F = 1$, so all the water that passes through them counts as reaching the destination ({SI: net accounting, fixed cells}). In the example of Fig. 1b, gross accounting credits the well with the 6 m³/d it pumps. Net accounting also credits it with the 5 m³/d that flow on through its cell to the river.

In a three-layer example model, a well pumping 5.0 m³/d sits in a cell that carries 33.7 m³/d (Fig. 1c; {SI: example and test models}). <!-- tutorials/herebedragons.py::build_layered, LAYERED_WELLS (weak_well in layer 3 of 3, 5 m³/d); README_method.md Fig. 1c (whose cell carries 33.7 m³/d) --> Net accounting credits this well with 33.7 m³/d, 6.7 times its pumping. <!-- README_method.md Fig. 1c; tutorials/02_accounting (weak_well 33.667, 6.733) --> Net accounting is kept to reproduce studies made with FlowSource (Section 4.1).

## 2.4 Solution in flow order

Equation (2) gives a cell's $F$ from the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource.

Flow loops break this order. A flow loop is a group of cells among which water circulates, so that water leaving a cell can return to it. No ordering of the cells in a loop is purely downstream, so a single pass cannot solve a loop exactly. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each, which they expect to change results negligibly. <!-- references/docs/text/2013_Foley_Black_FlowSource_DAG_algorithms.txt, cycle section: "Cycles do, albeit rarely, occur"; "multilayer models which have stability problems"; "the edge with the lowest volume is removed"; "negligible in all but the rarest cases" -->

We keep every flow and solve each loop exactly as one block of equations. In linear-algebra terms, the solve is a block-triangular sparse LU factorisation, with each flow loop as one block ({SI: solution of the linear systems}).

## 2.5 Water-budget checks

Four checks tell the user whether a trace agrees with the model's water budget. They test the solve, not the flow model itself. Each must hold exactly, because each follows from adding up the cell equations. The first is the backward closure check:

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{5}$$

The check says that the water entering through every source term, weighted by its $F$ and corrected for the cell budget errors, equals the water that leaves through the destination. Its mirror image is the forward closure check:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i. \tag{6}$$

The third is the forward–backward check:

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{7}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included. The fourth is the boundary-control check. In every cell with outflow, the backward fractions to all sink terms must add up to 1. Maps of these fractions (boundary-control maps) show where each cell's water goes.

Because the checks include the flow model's budget errors $r_i$, a failed check points to an error in the tracing, not in the flow model.

## 2.6 Mean travel time

Fractions say how much water arrives, not when. Let $V_i$ be the volume of water in cell $i$, which is porosity times saturated volume. Its mean residence time is $\tau_i = V_i/O_i$. The mean travel time from entering cell $i$ to leaving the model through the destination is then $m_i/F_i$, where

$$(\mathbf{I} - \mathbf{P})\,\mathbf{m} = \boldsymbol{\tau} \circ \mathbf{F} \tag{8}$$

and $\circ$ is the cell-by-cell product ({SI: travel-time identity}). Each cell adds its residence time, weighted by its $F$, and passes the sum upstream with the outflow shares. Travel times are defined under gross accounting. A mean travel time averages fast and slow water that have mixed in the cells. It should not be used alone to draw a time-of-travel zone (Section 6.4).

## 2.7 Transient models: snapshots and transient tracking

Existing full-mixing methods treat a transient model as a series of snapshots (Foley and Black 2013; Environment Agency 2019). A snapshot traces one time step as a steady state. Storage release is a source term and storage gain a sink term. Nothing is carried from one step to the next (Fig. 1d, left). Snapshots therefore have no travel lag between steps. Nor can they say where the water released from storage came from. On the seasonal example model of Section 4.4, such water makes up as much as 50 % of the well's water in summer. <!-- README_method.md Fig. 4a caption; studies/paper/transient_figure.py (summer storage peak 49.7 %); tutorial 08 §2 -->

We extend full mixing through time. We refer to this as transient tracking. Water from the chosen sources is tagged, as a tracer would be, and carried through storage from step to step (Fig. 1d, right). Each cell, and each reach, lake or well added as an extra cell (Section 3.1), is a fully mixed volume of water. Storage terms change this volume from $V_i^{\mathrm{old}}$ at the start of a step to $V_i^{\mathrm{new}}$ at its end. Let $c_i$ be the tagged fraction of a cell's water. Step $n$ of length $\Delta t$ is then

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big], \tag{9}$$

where $O_i$ now leaves out storage. Each cell's tagged water at the end of a step is its tagged water at the start, plus arrivals from upstream cells and source terms, less what leaves at the cell's end-of-step mix.

As in GWT, the scheme is implicit, so outflows carry the cell's mix at the end of the step. It is upstream weighted, so inflows carry the mix of the cell they come from. It adds no dispersion. It runs on the flow model's own time steps, so the budget of every step must be saved (SAVE BUDGET ALL in the Output Control file).

MODFLOW's cell budget never balances exactly, so each cell has a small error $r_i$. We let this error leave the cell carrying the cell's own mix of water. GWT treats the error in the same way, which Langevin et al. (2022) call the flow-error correction.

The water in the model at the start of the simulation can be tagged as its own group, called initial water. By default, each cell's water volume starts at porosity times saturated volume and is then carried by the storage flows. With these "flow" volumes, every water balance closes exactly. A "gwt" option resets the volumes at the end of each step, as GWT does, which can create or remove tagged water at step boundaries. Forward transient tracking is then unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). We recommend the default unless a result must match a GWT run ({SI: water volume options}).

## 2.8 Backward tracking in time

Forward transient tracking is not new (Section 1; Table 1). What we add is backward tracking in time. It answers the question behind a time-limited protection zone: which water in the aquifer will reach a sink, and by when? It is not MODPATH backward tracking, in which particles run in reverse from the sink. Its result is the backward fraction in time, $w_i^n$. Take the water in cell $i$ at the start of step $n$, together with the water that enters the cell during the step. $w_i^n$ is the share of that water that leaves through the destination before the simulation ends. A map of $w$ is a time-limited contributing area, such as the 30-year area of Fig. 4d. The solve runs step by step from the end of the simulation back to the start, with inflow and outflow swapping roles. It is the discrete counterpart of adjoint methods for continuous transport (Neupauer and Wilson 1999; Cornaton and Perrochet 2006).

The same run gives the fractions of each cell's water that leave through other sinks or are still stored at the end. Together with $w$, they add up to 1, apart from the flow-error correction and the step-boundary changes of the "gwt" volumes. With every source and the initial water tagged, the run splits the destination's outflow by source term, time step and initial water. The transient forward–backward check is

$$\sum_n \Delta t \sum_i d_i^n c_i^n = \sum_n \Delta t \sum_i s_i^n w_i^n + \sum_i V_i^0 c_i^0 w_i^1, \tag{10}$$

where $V_i^0$ and $c_i^0$ are the water volume and tagged fraction of cell $i$ at the start. This check says that the tagged water the destination takes, found by forward tracking, equals the tagged inflow and initial water, each multiplied by its share that later reaches the destination. The check holds exactly for either volume option (Section 4.2).
