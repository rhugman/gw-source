# Where does it come from and where does it go? Fast, open-source flow tracing for MODFLOW 6 models

**Article Impact Statement:** Open-source code turns saved MODFLOW 6 flows into contributing areas, water sources and travel times for any well or stream, in steady-state or transient flow.

**Abstract:** Groundwater studies often ask where water comes from and where it goes. Which land feeds a well, spring or stream? How much of a well's water is river water? Where does recharge under a polluted field end up? We present open-source code, `gwsource`, that answers such questions from the flows a MODFLOW 6 model saves. The code treats the water in each cell as fully mixed, like earlier methods. It computes the share of each cell's water that ends at a well, a stream or another outlet. The same trace splits a well's water by source and gives mean travel times. The code extends the method to every MODFLOW 6 grid type, stream network and linked model. It handles weak sinks. It carries tagged water through storage between time steps, forward and backward in time. Every result is checked against the flow model's water budget. The paper presents ten worked examples. Each checks an output a practitioner would use against other commonly used approaches. Results matched MODFLOW 6 transport to its solver tolerance with the same water volumes. They matched particle tracking in totals and mean travel times, as any method that conserves water should. At the edges of areas the two differ cell by cell. On a regional model of 1.68 million cells, one trace of eight wells, alone and together, took 2–3 s. That is small next to the model run itself. Tracing is cheap enough to include in history matching and similar analyses. Full-mixing areas are wider than particle-tracked areas. Particle tracking remains better where a sharp edge or first arrival matters.

**Key words:** flow tracing; full mixing; MODFLOW 6; contributing area; sources of water; travel time; transient tracking; ensemble; source protection

# 1. Introduction

Practitioners who ask where groundwater comes from and where it goes also need to know how the answers change through the year and how sure they can be of them.

Methods that answer these questions from a groundwater flow model fall into four families. Particle tracking follows particles of water along flow paths. It is the standard tool for mapping a well's contributing area. This is the land where water enters the aquifer and later reaches the well. In MODFLOW models it runs in MODPATH (Pollock 2016) or in the particle-tracking model of MODFLOW 6 (PRT; Langevin et al. 2026). Transport with tagged water gives the water from one source a concentration of 1 and all other water a concentration of 0. A cell's concentration is then the share of its water that came from that source (Bedekar et al. 2024). In MODFLOW 6 it runs in the Groundwater Transport (GWT) Model, with one model for each source (Langevin et al. 2022). As documented, the unit-concentration method steps forward in time only. It gives the share of each cell's water that came from a source, but not the share that will later reach a well. Adjoint and age methods solve transport equations of their own (Neupauer and Wilson 1999; Goode 1996). Full-mixing flow tracing splits each cell's mixed water among its outflows.

Particle tracking has one difficulty at weak sinks. Sink terms are the boundaries that remove water from a cell, such as a pumping well or a gaining stream. A weak sink is a cell whose sink terms take only part of the cell's outflow. A particle cannot split. It must either stop at a weak sink or pass on. If it stops, all its water is counted as reaching the sink. If it passes, none of it is. The rule chosen changes the contributing area (Section 5).

Under full mixing, a weak sink can take just its share of the cell's water. The rest passes on to the neighbouring cells. Two published full-mixing programs apply different rules at a weak-sink well. FlowSource (Foley and Black 2013) is used to draw source protection zones in England (Environment Agency 2019). These zones restrict activities that could pollute the water a supply well pumps. FlowSource counts all the water passing through a weak-sink well's cell as the well's water. We refer to this as net accounting. For transient models, it traces each time step as a steady-state flow field. We refer to such a trace as a snapshot. MODALL (Potter et al. 2008) applies full mixing to steady-state MODFLOW-88 models. At a weak-sink well it counts only the water the well pumps. We refer to this as gross accounting. All these methods are compared in Supporting Information, Table S1.

This paper presents open-source code, `gwsource`, that extends the full-mixing method of FlowSource to MODFLOW 6. It reads every MODFLOW 6 grid type, stream networks and linked models. It uses gross accounting by default. It checks every result against the water budget. In transient models, it carries tagged water through storage, forward and backward in time. Risk-based studies run an ensemble of model versions that fit the measurements about equally well (Fienen et al. 2022). The code is fast enough to trace every version.

Section 4 works through ten examples. Each checks an output a practitioner would use against another approach. Section 5 applies the code to a published regional model. Section 6 sets out the trade-offs of full mixing.

# 2. Method

**Overview.** This section explains how the code traces water and what each of its outputs means. A backward trace follows the water of a destination, such as a well, back to where it entered the model. A forward trace follows the water of a source, such as recharge, to where it leaves. Both work on the cell-by-cell flows that a MODFLOW 6 model saves, for one time step or for every step of a transient model. The backward fraction F maps where a sink's water comes from. A contributing area follows from it (example A in Section 4). The forward fraction G maps where a source's water goes. A trace also splits a sink's water by source, for example into recharge and river water. With a porosity, a trace also gives mean travel times (example C). For transient models, the code either traces each time step on its own flows or carries tagged water through storage (example B). The derivations and the solution of the equations are given in the Supporting Information (Supporting Information, Text S1).

**Full mixing and the cell budget.** Every output of the code rests on the assumption of full mixing. Full mixing treats each active model cell as one well-mixed volume of water. All the water leaving a cell then has the same mix of origins and the same mix of fates, whichever outflow it takes. At the edge of a contributing area, the water of a cell then splits between the sink and other outlets, where particles from the same cell would mostly either reach the sink or miss it. For this reason, areas traced under full mixing are wider and more diffuse than particle areas. Larger cells widen them further (Section 6).

The code reads the cell-to-cell flows (FLOW-JA-FACE; Langevin et al. 2017) and the source and sink terms from the MODFLOW 6 budget file. The flow from cell $i$ to its neighbour $j$ is $q_{ij} \ge 0$. Source terms, such as recharge or leakage from a river, bring water into a cell. Sink terms, such as wells or drains, take it out. Each term is kept separate by package and by boundary, so that a trace can follow the water of individual boundary conditions. A stream reach, a lake or a multi-aquifer well can stay a source or sink term of the aquifer cells it exchanges water with. It can also be traced as a cell of its own, from its package budget file, so that its flows to the aquifer, to other reaches and through the water mover (MVR) become flows $q_{ij}$ like any other. The cells of models linked by exchanges are treated as one set of cells. The choice between a term and a cell changes how a trace splits a sink's water by source (example C in Section 4).

If $\mathrm{Src}_i$ and $\mathrm{Snk}_i$ are the sums of the source and sink terms of cell $i$, its total inflow, total outflow and cell budget error are

$$I_i = \sum_j q_{ji} + \mathrm{Src}_i, \qquad O_i = \sum_j q_{ij} + \mathrm{Snk}_i, \qquad r_i = I_i - O_i. \tag{1}$$

The cell budgets of a MODFLOW model do not balance exactly, because the solver stops once the heads and residuals meet convergence tolerances. The cell budget error $r_i$ is usually small but not zero. The code reports this error but never forces it to zero. Because F is written with each cell's outflow and G with its inflow, the error enters the water-budget checks that link them (below).

**The backward fraction F.** The backward fraction answers the question of where the water of a sink comes from. We refer to the sink terms that a trace follows as the destination. The destination can be one well, one stream reach or a group of wells traced together. The backward fraction $F_i$ is the share of the water leaving cell $i$ that later leaves the model through the destination. Let $d_i$ be the outflow of cell $i$ through the destination, and $P_{ij} = q_{ij}/O_i$ the share of its outflow that goes to cell $j$. Under full mixing, the water that cell $i$ sends to cell $j$ shares the fate of all the water leaving $j$. In volumes and in shares, this gives

$$F_i\, O_i = \sum_j q_{ij}\, F_j + d_i , \qquad F_i = \sum_j P_{ij}\, F_j + \frac{d_i}{O_i}. \tag{2}$$

A cell's F is the share of its outflow that leaves through the destination directly, plus the outflow-weighted sum of the F of its downstream neighbours. Eq. (2) holds in every cell, so one solve of these linear equations gives the fractions to every destination group at once. Where water circulates among cells, as it can with the XT3D option of MODFLOW 6 for anisotropic flow (Provost et al. 2017), the code solves each such flow loop exactly. FlowSource instead deletes the smallest flow in each loop (Foley and Black 2013; Supporting Information, Text S1).

A map of F shows where a destination's water comes from. A contributing area is the set of cells where F exceeds a threshold that the user chooses, such as 0.5. Because F takes in-between values at the edge of an area, the choice of threshold is a judgement (Section 6). The sum of F times the cell area gives a size of the area without a threshold. We refer to it as the expected area.

Fig. 1a works through an eight-cell example in which water enters at the west edge and as recharge and leaves through a well and a river. The well cell receives 11 m³/d, of which its well pumps 6 m³/d. The other 5 m³/d flow on to the river without returning to the well. Eq. (2) then gives F = 6/11 = 0.55 in the well cell. All the water of the two cells west of the well cell flows into it, so they share its F. The cells of the upper row send part of their water past the well to the river, so their F is lower.

![](fig/fig_method_single.png)

**Figure 1.** (a) Backward fractions F (in cells) to a 6 m³/d well in an eight-cell example (gross accounting). Water enters from the west and as recharge of 1 m³/d per cell. It leaves through the well and a river. Arrow widths show flows. Only the well cell's flows are numbered (m³/d). In the well cell, F = 6/11 = 0.55. (b) One cell i of a transient model. A snapshot (top) traces each time step on its own flows. Water released from storage then enters the cell as a source of unknown origin. Transient tracking (bottom) carries the water stored in the cell at the end of step n into step n + 1. There it mixes with the inflows of that step. V is the cell's water volume and c the share of its water that is tagged. The height of the fill shows V and its shade shows c.

**Gross and net accounting at weak sinks.** The well cell of Fig. 1a is a weak sink, because its well takes only part of the cell's outflow (Section 1). At a weak sink the method needs a rule for how much of the cell's water to attribute to the sink. Eq. (2) applies gross accounting (Section 1). Each sink term takes its share of the cell's total outflow. Only that share counts as the sink's water, while the rest of the cell's outflow passes on to its neighbours. Gross accounting is the default because it attributes to each sink only the water that the sink takes from the model, as the MODFLOW 6 Groundwater Transport (GWT) Model does (Langevin et al. 2022), so that the water traced to a well adds up to what it pumps.

Under net accounting, the destination cells are fixed at F = 1. All the water that flows into them from other cells then counts as the destination's water. This is how FlowSource attributes water at a well (Foley and Black 2013; Supporting Information, Text S1). In Fig. 1a, net accounting adds the 5 m³/d that flow on through the well cell to the river. It leaves out the 1 m³/d of recharge on the well cell itself, because it works from the cell-to-cell flows only. The well is therefore attributed the 10 m³/d that flow into its cell from its neighbours, against the 6 m³/d it pumps. The difference is largest at a small well in a cell that carries much more water than the well pumps (Table 1, row 02).

**The forward fraction G.** The forward fraction answers the opposite question, which is where the water of a source goes. The forward fraction $G_i$ is the share of the water entering cell $i$ that came from the source. Let $s_i$ be the inflow of cell $i$ through the source. The volume of water entering cell $i$ that came from the source is then

$$G_i\, I_i = \sum_j q_{ji}\, G_j + s_i . \tag{3}$$

A cell's G is the share of its inflow that enters directly from the source, plus the inflow-weighted sum of the G of its upstream neighbours. Eq. (3) mirrors Eq. (2), with inflows in place of outflows. A map of G shows how much of each cell's water came from the source (Fig. 2c). G equals the concentration that GWT reaches at equilibrium on the same grid, with upstream weighting and no dispersion, when the source water carries a concentration of 1 and all other water a concentration of 0 (Table 1, row 03).

**Volumes and the water-budget checks.** A fraction says what share of a cell's water reaches the destination, but not how much water that is. A fraction times a flow gives a volume of water per unit time. We refer to these rates as volumes. The volume through cell $i$ is $F_i O_i$. It says how much of the water passing through the cell later reaches the destination. The volume from cell $i$ is $F_i$ times the cell's inflow through its source terms. It says how much water enters the model in that cell and later reaches the destination. The volumes from all cells, added up package by package, split the destination's water by source (Fig. 2b). In the same way, the volumes of a forward trace split a source's water by the sink through which it leaves.

Because they are volumes of water, the results of a backward or forward trace can be checked against the flows that MODFLOW 6 simulated. The closure check follows from adding Eq. (2) over all cells. It says that the source water traced to the destination, once corrected for the cell budget errors, adds up to the water the destination takes. The forward–backward check requires the volume from a source to a destination to be the same whether it is traced backward from the destination or forward from the source. The boundary-control check traces every sink of the model at once. It requires the fractions to all sinks to add up to 1 in every cell with outflow, so that the water of every cell leaves the model somewhere. All three checks hold exactly for any flow field, except in loops where water circulates without ever reaching a sink (Supporting Information, Text S1). As a result, a check error larger than round-off points to a fault in the tracing. The checks test the solution of the equations. They cannot show that the flow model is right, or that full mixing describes how water moves in the aquifer.

**Mean travel time.** Fractions say how much water reaches a destination, but not when it arrives. Travel times, unlike fractions, need a porosity. The water volume $V_i$ of cell $i$ is porosity times the saturated volume of the cell. Water stays in a fully mixed cell for a mean residence time $\tau_i = V_i/O_i$, whichever outflow it then takes. Let $t_i$ be the mean travel time from entering cell $i$ to leaving the model through the destination, for the water that does leave there. The code solves for $m_i = F_i\, t_i$, because $m_i$ obeys an equation of the same form as Eq. (2),

$$m_i = \tau_i\, F_i + \sum_j P_{ij}\, m_j . \tag{4}$$

Each cell adds its own residence time, weighted by its F, to the times of its downstream neighbours. The code reports the mean travel time $t_i = m_i/F_i$ only where F is above a small threshold (Fig. 2d), because where F is close to zero the mean rests on very little water. Mean travel times are defined for gross accounting only. Eq. (4) weights each cell's residence time by the share of its outflow that leaves through the destination. Under net accounting a destination cell has F = 1, although part of its water flows on to other sinks, so this weight no longer matches the water that leaves through the destination. A mean travel time averages fast and slow water that have mixed in the cells, so it is not a first-arrival time.

**Transient flow: snapshots and transient tracking.** FlowSource (Foley and Black 2013) traces a transient model one time step at a time, as if the flows of each step were steady-state (Environment Agency 2019). We refer to such a trace as a snapshot. Water released from storage then counts as a source term. Water taken into storage counts as a sink term (Fig. 1b, top). This is a limitation, because in a transient model the water that reaches a sink in one step may have entered the aquifer in an earlier one. A snapshot cannot show recharge of the wet season reaching a well in the dry season. It also cannot say where the water released from storage came from.

We extend full mixing through time. We refer to this as transient tracking. Water from the chosen sources is tagged, as a tracer would be, and carried from step to step through the water volume of each cell (Fig. 1b, bottom). The hydraulic mixing-cell method of Partington et al. (2011) carries mixed water through storage in a similar way in integrated surface water–groundwater models. Storage terms are not traced as source or sink terms. Instead they change the water volume of a cell over step $n$ from $V_i^{\mathrm{old}}$ to $V_i^{\mathrm{new}}$, with $V_i^{\mathrm{old}} - V_i^{\mathrm{new}} = \Delta t^n S_i$, where $\Delta t^n$ is the length of the step and $S_i$ the net release from storage. Let $c_i^n$ be the share of the water in cell $i$ at the end of step $n$ that is tagged. With all flows taken from step $n$,

$$V_i^{\mathrm{new}} c_i^n - V_i^{\mathrm{old}} c_i^{n-1} = \Delta t^n \Big[ \sum_j q_{ji}\, c_j^n + s_i^n - (O_i + r_i)\, c_i^n \Big]. \tag{5}$$

Here $O_i$ and $s_i$ leave out the storage terms, but $r_i$ is still the cell budget error of Eq. (1), with the storage terms included. In Fig. 1b (bottom), $V_i^n$ stands for $V_i^{\mathrm{new}}$ of step $n$.

Eq. (5) is the balance of tagged water in one cell over one step. The outflows carry the cell's mix at the end of the step, because the scheme is implicit in time, as in GWT (Langevin et al. 2022). The term $r_i c_i$ lets the cell budget error leave the cell at the cell's own mix, as the flow-imbalance correction of GWT does. The code applies this correction by default. Water moves by advection only, with no dispersion, diffusion, sorption or decay. Some spreading still comes from mixing whole cells and from long time steps (Supporting Information, Text S1).

Transient tracking needs a porosity and the budget of every time step. The Output Control setting SAVE BUDGET ALL writes this budget. We refer to the water in the model at the start of the simulation as initial water. It can be tagged as its own group. Two choices also affect the result. By default, the water volume of each cell starts at porosity times saturated volume and then changes only by the storage flows, so that every cell's water balance closes exactly. As an option, the volume is reset to porosity times saturated volume at the end of each step, as in GWT, so that results can be compared with a GWT run. Long implicit time steps make tagged water arrive too early. For this reason, each flow step can also be split into shorter transport sub-steps without a change to the flow model. The SI describes both options (Supporting Information, Text S1). Example B (Section 4) shows their effect.

**Backward tracking in time.** Forward tracking says how much of each cell's water came from a source. It cannot say which of the water now in the aquifer will reach a sink, or by when. Backward tracking in time answers this question. It solves a balance of the same form as Eq. (5), with the roles of inflow and outflow swapped, from the last step of the simulation back to the first. This differs from MODPATH backward tracking, in which particles start at the sink and move against the flow. Backward tracking in time is the discrete counterpart of the adjoint methods that solve a transport equation backward in time (Neupauer and Wilson 1999; Cornaton and Perrochet 2006).

The backward fraction in time $w_i^n$ is the share of the water in cell $i$ at the start of step $n$, or entering it during the step, that leaves through the destination before the simulation ends. Over step $n$,

$$\Big[ V_i^{\mathrm{new}} + \Delta t^n\, (O_i + r_i) \Big]\, w_i^n = \Delta t^n \Big[ \sum_j q_{ij}\, w_j^n + d_i^n \Big] + V_i^{\mathrm{old},\,n+1}\, w_i^{n+1}. \tag{6}$$

The water in a cell during a step can reach the destination by three routes. It can leave through the destination directly, flow to a neighbour, or stay in the cell into the next step, with the volume at the start of that step. No water can reach the destination after the last step, so the solve starts there with w = 0.

A map of w at the start of the simulation shows the share of each cell's water that the destination takes before the simulation ends, for example within 30 years (Fig. 2f). A threshold on this map gives a time-limited contributing area. The same backward run also gives the share of each cell's water that leaves through other sinks and the share still stored in the model at the end. The three shares add up to 1, apart from a remainder that the code reports (Supporting Information, Text S1). As in steady-state flow, a forward–backward check links the forward and backward runs (Supporting Information, Text S1). When the flows are held constant for long enough, c tends to the steady-state forward fraction G. In the same limit, w at the first step tends to the steady-state backward fraction F.

# 3. Software and cost

The method is implemented in `gwsource`. It is an open-source Python package (MIT licence). It reads the binary grid file and the budget file of a MODFLOW 6 Groundwater Flow (GWF) model, on any grid type. Stream reaches, lakes and multi-aquifer wells can be traced as extra cells from their own budget files. The inputs, selections and outputs are listed in Supporting Information, Table S2.

The regional model of Section 5 has 1.68 million cells. On an Apple M4 Max with 64 GB of memory, one trace of its eight wells, alone and together, took 2–3 s. Its memory peaked at 2.5 GB. The MODFLOW 6 run of that model takes 44 s (Supporting Information, Text S2). The package is tested on ten small test models and two published examples (Supporting Information, Figure S1).

# 4. Worked examples

This section shows how a practitioner can use the code to answer three common questions and how far each answer can be trusted. The three worked examples ask where a well's water comes from (example A), how much of it is already in the aquifer (example B), and how much comes from each source and how old it is (example C). Each compares its result with another common approach, such as particle tracking, transport with tagged water or a published study. The example sink is a well, but each output applies in the same way to a stream reach, a drain, a lake or a group of them. Fig. 2 shows one output of each type. Table 1, at the end of this section, summarises the ten notebooks that ship with the code.

All examples start from one small example model. It is a single unconfined layer of 40 × 40 cells of 50 m, with recharge of 5 × 10⁻⁴ m/d on every cell. The layer is 50 m thick and has a hydraulic conductivity of 5 m/d. A constant head along the west edge brings in regional groundwater. A river runs north–south 100 m east of a supply well that pumps 800 m³/d. Each example ships with the code as a Jupyter notebook that builds its model, reproduces its numbers and draws its figures (Section 7).

![](fig/fig_gallery.png)

**Figure 2.** Outputs for the example well (Section 4). (a) Backward fraction F. White lines: F = 0.1 (dashed) and 0.5 (solid). (b) The well's water by source (m³/d). (c) Forward fraction G of recharge on the outlined field. (d) Mean travel time where F > 0.5. (e) Cells with F > 0.5 in all (inner zone) or some (seasonal zone) of 36 seasonal snapshots. Ring: F > 0.1 in some snapshots. (f) Share of each cell's water pumped within 30 years. (g) Share of 50 posterior realisations with F > 0.5. Red dashed line: true F = 0.5. (h) F on a Voronoi grid. Panels (f) and (h) use the colours and lines of (a). Star: well. Blue cells: river.

**Example A: where does the well's water come from?** A protection zone around a supply well starts from the land whose water reaches the well. For this reason, a practitioner needs to know how large that area is, how far it reaches and how much to trust its edge. Fig. 2a maps F for the supply well. The size of the contributing area depends on the threshold that the user chooses. Cells with F > 0.5 cover 1.143 km², against 1.575 km² for cells with F > 0.1. The expected area of Section 2 does not need a threshold. Here it lies between the two, at 1.173 km². Both areas reach the west edge of the model, about 1.4 km from the well. They reach this far because 15 % of the well's water enters at the west edge as regional inflow. Both areas also extend east of the river, as far as the east edge of the model. Near the well the river loses water to the aquifer, so groundwater from the east can pass through the river cells to the well.

The closure check of Section 2 tests the trace behind these numbers. The traced sources add up to the 800 m³/d pumped, with a relative closure error of 0.0. This check tests the solution of the equations, but it cannot test the position of the area's edge. The edge is where full mixing and particle tracking are expected to differ, so it needs a check of its own. For this check the code runs MODFLOW 6 PRT on the same flows. Particles start from every source term in cells with F > 10⁻⁶. Each particle carries a share of its term's flow as a weight. It loses part of that weight at every other sink it passes, in proportion to the flow that sink takes from the cell. We refer to these as weight-losing particles. They are the particle counterpart of gross accounting. Similar weighting rules at sinks appear in the travel-time method of Visser et al. (2009) and the solute-transport method of Winston et al. (2018). Because the particles lose weight at each sink by the full-mixing shares, they are not an independent particle reference. They show how much full mixing spreads water between sinks.

A particle run conserves water when the weight its particles deliver to each sink equals the water that sink takes. Weight-losing particles conserve water, so they deliver what the well pumps whatever the shape of the area (Table 1, row 01). The comparison of areas is more telling. On this model the F > 0.5 area is close in size to the area from which the particles deliver most of their water. The particle share of a cell is the share of the weight released there that reaches the well (Fig. 3a). We refer to the cells with a particle share above 0.5 as the particle area. It covers 1.168 km². The F > 0.5 area is 2.1 % smaller and leaves out 14 of its cells. The F > 0.1 area is 35 % larger. It holds every cell of the particle area. The two methods differ most at the edge of the area. In the 372 cells with F between 0.05 and 0.95, the particle share and F differ by 0.164 on average. In those cells most particles either reach the well or miss it, while full mixing gives the cell an in-between value (Section 2).

![](fig/fig_examples_ab.png)

**Figure 3.** Checks of worked examples A and B. (a) Particle share in each cell of the example model where weight-losing PRT particles start. The particle share is the share of the water released in a cell that the particles deliver to the well. Cells without particles are blank. White lines: F = 0.1 (dashed) and F = 0.5 (solid) from full mixing. Star: well. Blue cells: river. (b) The well's water by origin in the unit-concentration example of Bedekar et al. (2024), rebuilt in MODFLOW 6. Stored water is the water in the aquifer at the start of the run, one day before pumping starts. It is the initial water of Section 2. Lines: forward transient tracking. Open circles: values read off Figure 2 of Bedekar et al. (2024).

For the practitioner, this means that on this model the F > 0.5 area is a fair estimate of the particle area. Because the F > 0.1 area holds every particle cell, it serves here as a cautious outer limit. Section 5 shows that a regional model need not behave in the same way.

**Example B: how much of the pumped water is already in the aquifer?** A manager may ask how much of the water pumped over the coming decades is already in the aquifer today. The answer matters where new recharge differs in quality from the water already stored, for example after a change in land use. A seasonal version of the example model shows why snapshots cannot answer this question (Section 2). In this version, recharge is multiplied by 1.8, 1.0, 0.1 and 1.1 in the wet, wet-to-dry, dry and dry-to-wet seasons. The well pumps between 640 and 1,120 m³/d. The model runs for 30 years, with one time step per season and 121 time steps in all. Seasonal snapshots show which cells lie in the contributing area in every season and which in some seasons only (Fig. 2e; Table 1, row 05). Averaged over the 30 years, the snapshots give the well's water as about 60 % recharge and 15 % storage release (Supporting Information, Figure S2a). A snapshot cannot say where that stored water came from. It may be old water or recharge of the last wet season.

Transient tracking follows the stored water. It shows that most of the water pumped in the first decades was already in the aquifer. The tracking uses a porosity of 0.3 and four transport sub-steps per flow step. The run starts from a steady state in which the well already pumps. Initial water is therefore not water from before pumping began. Of all the water pumped in the first 10 years, 81 % was initial water. This share is 98 % for the first year and 68 % over 30 years. Even in the last season of year 30, the well's water is 51.6 % initial water, 32.9 % recharge and 15.5 % river water. In that season recharge supplies about a third of the well's water, against about 60 % averaged over the snapshots. New recharge mixes into a large volume of older water, because a column of this aquifer holds about 64 years of recharge. With one layer, the model cannot hold young water above old water, so a layered model may give other shares.

Backward tracking in time shows which of the water now in the aquifer reaches the well. Only the water near the well and along the main flow path reaches it within 30 years (Fig. 2f). Most of the water in the steady-state contributing area is still on its way at the end. Of the 8.77 million m³ pumped over 30 years, backward tracking attributes 67.7 % to initial water. This equals the 68 % of the forward run, as the forward–backward check requires.

On the same model, transient tracking with GWT's water volumes and one transport step per flow step matched a GWT run with tagged recharge to 9.8 × 10⁻¹⁴ in every cell and step. Both codes solve the same equations, so this is a consistency test. It shows that the code solves Eq. (5) as GWT does. With one transport step per flow step, the two volume options of Section 2 change the fractions by less than 0.004 on this model, although porosity (0.3) differs from specific yield (0.2) (Supporting Information, Text S3). Transport sub-steps matter more, because long implicit steps make new water arrive too early. Four sub-steps per flow step remove most of this effect on this model (Supporting Information, Text S3).

The GWT check compares two codes that solve the same equations. An external check needs a published transient study made with other codes. Bedekar et al. (2024) used the unit-concentration method to show how a new well's water changes from stored water to water from its sources. This method is the transport with tagged water of Section 1. Their model has three layers, with lateral inflow along its west edge, recharge on the top layer, a stream along its east edge and a well that pumps for 25 years. They ran MODFLOW-2005 and MT3D-USGS, with one transport run per source. We rebuilt their model in MODFLOW 6 (Supporting Information, Text S2). One forward tracking run with four tags reproduces the published curves (Fig. 3b). At year 25, the well's water is 48.2 % lateral inflow, 29.2 % recharge and 22.5 % stream water. Bedekar et al. (2024) give 48 %, 29 % and 23 %. Over 15 times read off their Figure 2, the largest difference is 1.3 percentage points, on the lateral-inflow front at year 10. The values read off the published figure are themselves good to about one percentage point. Backward tracking in time adds a map of the time-limited contributing area (Supporting Information, Figure S3). Within 25 years, this area comes close to the steady-state F > 0.5 area of the final flows. We expect that a forward unit-concentration model would need one run per zone of the aquifer to give such a map, though we have not tested this.

For the practitioner, this means that snapshots and transient tracking answer different questions. A snapshot treats the flows of each step as steady, so it says which sources feed the well but not when their water entered the aquifer. Transient tracking shows that most of the water pumped over the next decade is already in the aquifer. Where new recharge differs in quality from the stored water, we would therefore expect the well's water to change over decades rather than seasons on a model like this one.

**Example C: how much water comes from each source, and how old is it?** Many studies need a sink's water split by source more than the edge of its area. A water-quality study, for example, may need to know how much of a well's water is river water and how old the water from each source is. On the example model, the well's total water and the mean travel time of all its water depend much less on mixing than the edge of an area does. Section 5 shows that on a regional model the split by source can still differ between methods by several percentage points. The backward trace of example A splits the 800 m³/d pumped into 71 % recharge, 15 % inflow at the west edge and 14 % river leakage (Fig. 2b). A forward trace asks the reverse question of where a source's water goes, for example the recharge under a field where fertiliser is spread. Of the recharge on a field of 300 m × 300 m, 39 % reaches the well (Fig. 2c). A forward trace from each source gives the same split of the well's water as the backward trace (Table 1, row 03). In a test problem with a river and recharge, the shares by source were the same to three digits whether water was mixed across whole cells, routed from face to face or followed with particles on the same grid (Supporting Information, Text S5).

The split by source also depends on where the trace stops. A second version of the example model shows this. In it, the river becomes a stream that flows from north to south. Two drains pass their water to the stream through the water mover. The well of this version takes a different mix of water from the well of example A. For this reason, its shares cannot be compared with the 14 % of river leakage given above. When the stream reaches stay source and sink terms of the aquifer cells, stream leakage supplies 32 % of the well's water. When the reaches are traced as cells of their own, that water splits into 129 m³/d of inflow at the upstream end of the stream and 126 m³/d of recharge that had discharged to the drains or the stream. A study that reports how much of a well's water is stream water should therefore say which of the two choices it made.

Full mixing and weight-losing particles give nearly the same mean travel time for all of the well's water, but they agree less well for river water. With a porosity of 0.3, the backward trace also gives mean travel times (Fig. 2d). They are taken to the point where the water enters the well cell, because particle trackers stop particles there (Supporting Information, Text S1). The mean travel time is 2.1 years for river leakage, 41.6 years for recharge and 108.4 years for inflow at the west edge. Over all the water it is 45.9 years, against 45.7 years for the particles (−0.5 %). This agreement is not an independent test. Any method that conserves water gives the mean travel time to the well as the volume of water bound for the well divided by its inflow, here 46.0 years. The time to the well cell is shorter by the time the water spends in that cell, about 0.1 years. The agreement therefore tests only the volume attributed to the well. That volume is nearly the same in both methods. By source, the particle times differ by −2.1 % for recharge and +2.1 % for the west edge, but by −20.1 % for river leakage. We attribute the river difference to its short path. River water reaches the well through few cells, so the mixing in those cells weighs more in its mean.

The comparison cell by cell is the informative one. In the 456 cells with F ≥ 0.5, apart from the well cell, the median ratio of particle time to full-mixing time is 0.96. In the 676 cells with F < 0.5, it is 5.72. A particle from a cell with small F follows one slow path around the edge of the area. Full mixing instead averages over all the paths that the cell's water takes. The same difference shows in the time-of-travel zones of Fig. 2d. The 25-year zone covers 0.455 km² under full mixing and 0.465 km² for particles (+2.2 %). The 5-year zone covers 0.098 against 0.122 km² (+25.6 %). On this evidence, we would take a well's overall mean travel time from full mixing. We would check its split by source with particles where the split matters (Section 5). We would draw a short time-of-travel zone with particles (Section 6).

**All ten notebooks.** Table 1 lists all ten notebooks. Eight of them ran in 10 s or less. Row 04 runs the trace of example A on other grid types (Fig. 2h). Row 09 applies the trace to an ensemble of models. Many sets of parameters can fit the measured heads about equally well. We refer to each set as a realisation and to a group of realisations as an ensemble. PEST++ IES is the iterative ensemble smoother of the PEST++ software (White 2018; White et al. 2020). History matching with PEST++ IES adjusts the realisations until they fit the measurements. We refer to the ensemble before history matching as the prior and to the history-matched ensemble as the posterior. In row 09, the measurements come from a synthetic true model, so the posterior can be compared with the truth (Fig. 2g; Supporting Information, Figure S4). A narrower posterior is not necessarily a correct one. One synthetic case cannot show how reliable posteriors are in general. Here the trace ran on each realisation after PEST++ IES had finished. We have not tested running it inside each PEST++ model run.

**Table 1.** The ten notebooks that ship with the code. Each row gives a notebook's question, its main output, the other approach or published study it is compared with and how closely the two agree. Letters after the notebook number give the worked example of this section that describes the notebook in detail. Every notebook also runs the water-budget checks of Section 2. Differences of about 10⁻¹⁰ or smaller are round-off. All notebooks use the example model of this section or a version of it (Supporting Information, Text S2). Supporting Information, Text S3 describes the rows that the worked examples do not cover in full.

| Notebook | Question | Output | Compared with | Agreement | Fig. 2 panel |
|---|---|---|---|---|---|
| 01 (A, C) | Where does a well's water come from? | F map, F > 0.5 and F > 0.1 areas, the well's water by source | Weight-losing PRT particles | F > 0.5 area 2.1 % smaller than the particle area | a, b |
| 02 | What is computed, and what changes at a weak sink? | Gross and net accounting, fractions to every sink. At a small well that pumps 5 m³/d from a cell that carries 33.7 m³/d, net accounting attributes all 33.7 m³/d to the well (6.7 times its pumping) | The published worked example of Foley and Black (2013) | Published example reproduced to 1 × 10⁻¹⁴. Fractions to all sinks add up to 1 within 1 × 10⁻¹⁵ | – |
| 03 (A, C) | Where does a source's water go? | G maps, fate of the recharge on a field | GWT with tagged water, run to equilibrium | 4.2 × 10⁻¹³ in all 1,600 cells | c |
| 04 | Does it work on my grid? | The same trace on regular (DIS), Voronoi (DISV) and fully unstructured (DISU) grids. Flow loops with XT3D | The same model on the regular grid. A solve of the whole system at once | DISU equals DIS in every cell. On DISV the expected area is 1.178 against 1.173 km² (+0.4 %), but F falls from 0.5 to 0.1 over 186 m against 121 m. The loop-by-loop solve agrees with the whole-system solve to 3.3 × 10⁻¹⁶ | h |
| 05 (B) | How does the area change through the seasons? | Seasonal snapshots of a 3-year run. The F > 0.5 area grows from 0.59 km² in the wet season to 1.35 km² in the dry season | – | Every snapshot closes within 1 × 10⁻⁶ m³/d | e |
| 06 (C) | How old is the water reaching the well? | Mean travel time map, 5- and 25-year zones, travel time by source | Weight-losing PRT particles | All water within 0.5 %, not an independent test. Wide differences at the edge of the area | d |
| 07 (C) | What if water passes through streams, drains, wells or linked models? | The well's water by source, with stream reaches traced as cells of their own or not. A multi-aquifer well. A model split into three linked models | The same model unsplit | 2.1 × 10⁻¹³ in F | – |
| 08 (B) | How much of the pumped water was already in the aquifer? | The well's water by origin through time. Backward fractions in time | GWT with tagged recharge | 9.8 × 10⁻¹⁴ over 1,600 cells and 121 steps | f |
| 09 | How does parameter uncertainty change the area? | Probability of contribution over 50 realisations, before and after history matching with PEST++ IES | A synthetic true model | The band with a probability between 0.1 and 0.9 shrinks from 1.10 to 0.35 km². A probability of at least 0.5 covers 93 % of the true F > 0.5 area (prior 79 %). Of the cells with a probability of at least 0.9, 86–87 % lie in the true area, before and after. Histogram quantiles within one bin width of the exact ones. Serial and parallel runs identical | g |
| 10 (B) | Does it reproduce a published unit-concentration study? | The well's water by source over 25 years. Time-limited contributing areas | Bedekar et al. (2024), Figure 2. Four GWT runs | Within 1.3 percentage points of the published curves (0.6 up to year 15 with 7.6-day sub-steps). GWT to 1.5 × 10⁻¹⁰ | – |

# 5. A regional model: Neversink

This section shows that a trace works and stays fast on a published regional model. It also explains why full-mixing areas differ from the published particle areas, so that a practitioner can read one next to the other. The USGS Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022) is a steady-state MODFLOW 6 model of 1.68 million cells. The published study refers to eight of its wells as priority wells. Together they pump 3,671 m³/d. The model has 358 realisations from history matching with PEST++ IES (Section 4). We refer to the realisation with the published calibrated parameter values as the calibrated model.

The published study mapped the wells' contributing area in the calibrated model with MODPATH 7 (Pollock 2016). One particle started in the uppermost active cell of each column near the wells. We refer to these cells as the start cells. The published contributing cells are the 980 start cells whose particle ends in a priority well. We traced the wells in the calibrated model with gross accounting. The stream reaches stayed source and sink terms of the aquifer cells.

A trace of all the wells took a few seconds, less than the fastest PRT run on the same flows. On an Apple M4 Max with 64 GB of memory, one trace of nine destination groups (each well alone and all eight together) took 2–3 s and peaked at 2.5 GB of memory. Each further group added about 0.19 GB (Supporting Information, Text S4). The closure check held to 1 × 10⁻¹² m³/d or better for every group. PRT took about 30 s when it wrote only where each particle ends. With full particle tracks, it took about 5 min with particles released at one height in each cell and about 13 min with particles released at four heights. These times do not compare like with like. One trace gives F in every cell, the volumes and the checks. A PRT run gives particle shares only in the cells it seeds. PRT memory was not measured. Across the ensemble, two traces of each realisation, without and with the stream network, took about 9 s.

The full-mixing areas differ from the published area. The overlap of two areas is the number of cells in both divided by the number in either. The published area comes from one reasonable choice of particle settings. The published runs put recharge and stream flows on the top face of a cell where no active cell lies above it. They stopped a particle in the first weak-sink cell it entered. They moved a particle that started in a dry cell down to the first active cell below. We refer to this setting as draping. PRT on the same flows reproduces the published area with these settings (overlap 0.998). Without the top-face setting, the overlap falls to 0.65. Without draping, it falls to 0.96. Two of our particle runs do not conserve water in the sense of Section 4. Particles that lose weight only at the wells deliver 2.6 times the wells' inflow (overlap 0.29). Particles released at the water table deliver 0.66 times it (overlap 0.39). Leaving these two runs out, the particle settings alone move the overlap from 0.62 to 0.998 (Supporting Information, Text S4).

The full-mixing areas overlap the published area less than any of these particle runs do. The areas where F exceeds 0.5 and 0.1 have overlaps of 0.41 and 0.30. We infer that the main reason is the one seen in example A. Full mixing splits each cell's water among all its outflows, while a particle follows one path. On average, the published cells send 42 % of their water to the wells. Many of them therefore fall below F = 0.5 (Fig. 4a). The F > 0.1 area holds 73 % of them (711 of 980). Fig. 4b shows this for a window around four of the wells, where the F > 0.1 area holds 538 of the 688 published cells.

Weight-losing particles (Section 4) lose weight at each sink as full mixing does. For this reason they measure only the spreading that full mixing adds between sinks. The F > 0.1 area holds 87 % of the 691 start cells where these particles deliver more than half their water to the wells (Supporting Information, Figure S5a). This share is an upper bound, because the particles started only in cells with F > 10⁻⁶. They therefore needed the trace before they could run. The 89 cells it misses supply 6 % of the particles' water to the wells (227 m³/d).

![](fig/fig_neversink_single.png)

**Figure 4.** F and the published contributing cells of the Neversink model, in a 7.1 × 9.25 km window around four of the priority wells. The window holds 688 of the 980 published cells. (a) F in the calibrated model, with the published cells outlined. (b) The F > 0.1 area against the published cells. Dark blue: in both (538 cells). Orange: published only (150). Light blue: F > 0.1 only (1,090).

Weak sinks add to the difference. A buried stream cell holds a stream reach and has another active cell above it. Where such a reach gains water, it is a weak sink that stops published particles. In the published runs, 26,828 particles stopped in buried stream cells and 466 in the five priority wells that take only part of their cell's outflow. Each stopped particle counts in full as reaching that sink, while full mixing passes the rest of the cell's water on (Supporting Information, Text S4). Net accounting attributes to a weak-sink well all the water that enters its cell. It raises the F > 0.5 overlap only from 0.41 to 0.44. At the weak-sink wells, gross accounting comes closer to the published cell counts than net accounting does.

Example C (Section 4) showed that a sink's split by source depends on how stream reaches are traced. On this model the split also depends on the method. With the stream reaches left as source and sink terms, full mixing attributes 57 % of the wells' water to recharge and 43 % to stream leakage. With the reaches traced as cells of their own, all of the wells' water traces back to recharge. Along weight-losing particle paths, with the reaches again left as source and sink terms, the split is 49 % recharge and 51 % stream leakage. Both methods deliver the wells' total inflow to within 2 %. We infer, without tracing it cell by cell, that stream water leaking near the wells stays on particle paths that end at a well. Full mixing instead gives that water the average fate of all the water leaving the cells it passes. A split by source on a regional model should therefore be reported with the method that gave it.

For the practitioner, a particle area depends on its particle settings as much as on the flow model. The comparison that isolates full mixing is a particle run that loses weight at sinks as full mixing does. Against that run, the F > 0.1 area held 87 % of the particle area on this model, so a low threshold on F did not give a complete outer limit.

# 6. Trade-offs and conclusions

Full-mixing areas are wider and more diffuse than particle areas (Section 5). Their edge is a band of cells where F lies between 0.1 and 0.9. In two simple test problems, halving the cell size made the band only about 30 % narrower (Supporting Information, Text S5; Supporting Information, Figure S6). On squares turned by 45° to the flow, the band was 1.8 times as wide as on squares aligned with it (Supporting Information, Text S5). Where the edge of an area matters, finer cells along it and a grid aligned with the main flow narrow the band.

No single threshold on F therefore reproduces a particle area everywhere. The threshold is a judgement about the purpose of the area. Both the threshold and the accounting should be reported with the area. In the test problems, on cells of 50 m or less, the F > 0.5 area was within 5 % of the size of the reference area. The F > 0.1 area missed at most 0.1 % of the reference area. It was 8 to 90 % larger. On Neversink, the F > 0.1 area still missed cells that weight-losing particles assign to the wells (Section 5). So a low threshold does not guarantee a cautious area on a regional model.

Transient tracking has so far been tested on synthetic models only. Its memory grows with the number of time steps. Movers between models (the MVE package) are not implemented yet. Without cell vertices, the code cannot map results on a DISU grid. A well's water by source and the mean travel time of all its water depend much less on mixing than the edge of its area does (Section 4). We would therefore use particles where a sharp edge or a first arrival matters, such as a short time-of-travel zone. We would use GWT where dispersion, sorption or decay matter, because transient tracking moves water by advection only (Langevin et al. 2022). Full mixing suits questions about many sinks, unstructured grids, package networks or many realisations.

# 7. Code and Data Availability

The code, `gwsource`, is open source under the MIT licence at https://github.com/rhugman/gw-source [check: public URL]. This paper uses version 0.0.1 [check: release version and tag]. Each example ships with the code as a Jupyter notebook that reproduces its numbers and figure (Supporting Information, Text S2). The same release holds the verification tables (docs/verification.md), the test models (tests/models/README.md) and the notes of the Neversink study (docs/neversink_study.md). The Neversink model is in a USGS data release (Fienen and Corson-Dosch 2021). The files behind every figure will be archived on Zenodo [check: DOI].

# References

Bedekar, V., C. Neville, M.J. Tonkin, R.D. Bartlett, and P. Plato. 2024. A unit-concentration method to quantify source contribution. *Groundwater* 62, no. 2: 303–309. https://doi.org/10.1111/gwat.13333

Cornaton, F., and P. Perrochet. 2006. Groundwater age, life expectancy and transit time distributions in advective–dispersive systems: 1. Generalized reservoir theory. *Advances in Water Resources* 29, no. 9: 1267–1291. https://doi.org/10.1016/j.advwatres.2005.10.009

Corson-Dosch, N.T., M.N. Fienen, J.S. Finkelstein, A.T. Leaf, J.T. White, J. Woda, and J.H. Williams. 2022. Areas contributing recharge to priority wells in valley-fill aquifers in the Neversink River and Rondout Creek drainage basins, New York. U.S. Geological Survey Scientific Investigations Report 2021–5112. Reston, Virginia: USGS. https://doi.org/10.3133/sir20215112

Environment Agency. 2019. *Manual for the Production of Groundwater Source Protection Zones*. Bristol, UK: Environment Agency. https://assets.publishing.service.gov.uk/media/5d41a020e5274a0a0bf7757c/Manual-for-the-production-of-Groundwater-Source-Protection-Zones.pdf

Fienen, M.N., and N.T. Corson-Dosch. 2021. Groundwater model archive and workflow for Neversink/Rondout Basin, New York, source water delineation. U.S. Geological Survey data release. https://doi.org/10.5066/P9HWSOHP

Fienen, M.N., N.T. Corson-Dosch, J.T. White, A.T. Leaf, and R.J. Hunt. 2022. Risk-based wellhead protection decision support: A repeatable workflow approach. *Groundwater* 60, no. 1: 71–86. https://doi.org/10.1111/gwat.13129

Foley, C., and A. Black. 2013. Efficiently delineating volumetric capture areas and flow pathways using directed acyclic graphs and MODFLOW; description of the algorithms within FlowSource. In *Proceedings of MODFLOW and More 2013: Translating Science into Practice*, Golden, Colorado, June 2–5, 2013, 571–581 [check: pages against the proceedings]. Golden, Colorado: IGWMC, Colorado School of Mines. https://groundwater-science.co.uk/wp-content/uploads/2013_FSv6_DAGPaper.pdf

Goode, D.J. 1996. Direct simulation of groundwater age. *Water Resources Research* 32, no. 2: 289–296. https://doi.org/10.1029/95WR03401

Langevin, C.D., J.D. Hughes, E.R. Banta, R.G. Niswonger, S. Panday, and A.M. Provost. 2017. Documentation for the MODFLOW 6 Groundwater Flow Model. U.S. Geological Survey Techniques and Methods, book 6, chap. A55. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A55

Langevin, C.D., A.M. Provost, S. Panday, and J.D. Hughes. 2022. Documentation for the MODFLOW 6 Groundwater Transport Model. U.S. Geological Survey Techniques and Methods, book 6, chap. A61. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A61

Langevin, C.D., J.D. Hughes, A.M. Provost, M.J. Russcher, M.J. Reno, W.P. Bonelli, E.D. Morway, S. Titus, R.G. Niswonger, S. Panday, D. Merrick, and E.R. Banta. 2026. MODFLOW 6 Modular Hydrologic Model version 6.8.1. U.S. Geological Survey Software Release, 23 September 2026. https://doi.org/10.5066/P1PGE9XW

Neupauer, R.M., and J.L. Wilson. 1999. Adjoint method for obtaining backward-in-time location and travel time probabilities of a conservative groundwater contaminant. *Water Resources Research* 35, no. 11: 3389–3398. https://doi.org/10.1029/1999WR900190

Partington, D., P. Brunner, C.T. Simmons, R. Therrien, A.D. Werner, G.C. Dandy, and H.R. Maier. 2011. A hydraulic mixing-cell method to quantify the groundwater component of streamflow within spatially distributed fully integrated surface water–groundwater flow models. *Environmental Modelling & Software* 26, no. 7: 886–898. https://doi.org/10.1016/j.envsoft.2011.02.007

Pollock, D.W. 2016. User guide for MODPATH Version 7—A particle-tracking model for MODFLOW. U.S. Geological Survey Open-File Report 2016–1086. Reston, Virginia: USGS. https://doi.org/10.3133/ofr20161086

Potter, S.T., E. Moreno-Barbero, and C.E. Divine. 2008. MODALL: A practical tool for designing and optimizing capture systems. *Ground Water* 46, no. 2: 335–340. https://doi.org/10.1111/j.1745-6584.2007.00410.x

Provost, A.M., C.D. Langevin, and J.D. Hughes. 2017. Documentation for the "XT3D" option in the Node Property Flow (NPF) Package of MODFLOW 6. U.S. Geological Survey Techniques and Methods, book 6, chap. A56. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A56

Visser, A., R. Heerdink, H.P. Broers, and M.F.P. Bierkens. 2009. Travel time distributions derived from particle tracking in models containing weak sinks. *Ground Water* 47, no. 2: 237–245. https://doi.org/10.1111/j.1745-6584.2008.00542.x

White, J.T. 2018. A model-independent iterative ensemble smoother for efficient history-matching and uncertainty quantification in very high dimensions. *Environmental Modelling & Software* 109: 191–201. https://doi.org/10.1016/j.envsoft.2018.06.009

White, J.T., R.J. Hunt, M.N. Fienen, and J.E. Doherty. 2020. Approaches to highly parameterized inversion: PEST++ Version 5, a software suite for parameter estimation, uncertainty analysis, management optimization and sensitivity analysis. U.S. Geological Survey Techniques and Methods 7C26. Reston, Virginia: USGS. https://doi.org/10.3133/tm7C26

Winston, R.B., L.F. Konikow, and G.Z. Hornberger. 2018. Volume-weighted particle-tracking method for solute-transport modeling; Implementation in MODFLOW–GWT. U.S. Geological Survey Techniques and Methods, book 6, chap. A58. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A58

# Supporting Information (draft)

## Table S1. Comparison of methods

**Table.** Five ways to compute the share of each cell's water that reaches a destination, or that came from a source, from the flows of a groundwater flow model. The columns are MODALL (Potter et al. 2008), FlowSource (Foley and Black 2013; Black and Foley 2013), this paper's code, unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022) and hydraulic mixing cells as published by Partington et al. (2011). Section 2 and Text S1 define the fractions F, G, c and w, and gross and net accounting. The MODALL and FlowSource columns describe the programs as published in 2008 and 2013. Years in parentheses date a statement to the 2013 papers. We found no published description of later versions. The sources of each column are listed after the footnotes.

| | MODALL (Potter et al. 2008) | FlowSource (Foley and Black 2013; Black and Foley 2013) | This paper's code | GWT unit concentration (Bedekar et al. 2024; Langevin et al. 2022) | Hydraulic mixing cells (Partington et al. 2011) |
|-------------|---------------|-------------------|-----------------|------------------|------------------|
| What is solved, and how | Cell by cell, outward from each well; cell order not described | Fractions cell by cell in flow order; one pass per time step | Linear equations in flow order; transient tracking: implicit steps | Implicit time steps, iterative solver; no documented steady-state option¹ | Explicit, on the flow model's steps; stable only for short steps² |
| Mixing in a cell | Full mixing | Full mixing | Full mixing | Full mixing with upstream weighting and no dispersion | Modified mixing cell; tends to full mixing as steps shorten³ |
| Accounting at weak sinks | Gross: well cell's fraction is pumping over inflow | Net: all water passing through a destination cell counted as reaching it | Gross (default); net as an option | Gross: sinks remove water at the cell's concentration | Outflow at the previous step's mix; gross in effect (our reading) |
| Flow loops | Not described | Smallest-flow connection in each loop deleted (2013) | Solved exactly; closed recirculation loops set to F = 0⁴ | None needed: one implicit solution over all cells (our inference) | Not discussed; fixed stream flow direction assumed |
| Outputs | Capture fraction (F) per well and summed over wells | F, volumes through and from; particle travel time | F, G and volumes by term; transient tracking: c and w | Concentration, read as the share of water from the tagged source | Fractions by flow component per stream cell, plus initial water |
| Transient models: water carried through storage? | No: steady-state MODFLOW-88 models only | No: each step traced as a steady state (snapshots) | Yes, transient tracking (needs porosity); snapshots also | Yes (needs porosity) | Yes: stream-cell water volumes carried step to step |
| Backward in time? | No | No | Yes, solved from the end of the simulation | No⁵ | No |
| Destinations or sources per run | One well per calculation; source fractions said possible, not described | One destination group (any number of cells) per calculation | Gross: all groups in one solve per direction; net: one group per solve | One tagged source per GWT model; several models per simulation | All flow components together; not user-chosen terms |
| Built-in water-budget checks | Not described | None described; flow loops reported (2013) | Closure, forward–backward, travel-time closure; more in transient tracking | Mass budget, a tagged-water balance; no backward closure or forward–backward check | Sum-of-fractions error; global volume error, gaining reaches only |
| Grids and packages | MODFLOW-88 finite-difference grids; wells, drains, rivers, recharge | Structured MODFLOW grids; method said to apply to unstructured grids (2013); package networks not documented | All MODFLOW 6 grid types, multi-model simulations, package networks | DIS, DISV, DISU; SFR, LAK, MAW, UZF and MVR transport | HydroGeoSphere stream cells; said to apply to other codes |
| Open implementation | Free from the authors; source code not mentioned | No; VB.NET source for academic use on request (2013) | Yes (`gwsource`, MIT) | Yes (MODFLOW 6, USGS) | Excel (Visual Basic) post-processor; availability not stated |

¹ Steady state is reached by running transient steps until concentrations stabilise (Langevin et al. 2022). In our test, one step with porosity 0 gave the steady-state G to 1 × 10⁻¹². This use of porosity 0 is not documented.

² The update is stable only while a step's inflow or outflow volume does not exceed the cell's storage (Partington et al. 2011). Later versions add sub-steps (Partington et al. 2013) and aquifer cells (Schilling et al. 2017). All of them step forward in time only.

³ After Campana and Simpson (1984): water leaving a cell over a step carries the previous step's mix.

⁴ A closed recirculation loop is a group of cells with no outflow to any sink or to a cell outside the group. Such loops are reported. No connections are deleted.

⁵ No backward option is documented (Langevin et al. 2022). Bedekar et al. (2024) read well capture forward in time, from the concentration simulated at the well.

**Sources.** We read every source below in full unless a page range is given. The two 2013 conference papers have no page numbers, so we cite them by section heading.

- **MODALL.** Potter et al. (2008, pp. 335–340) describe full mixing on a steady-state MODFLOW-88 model (p. 336). At the sink cell the capture fraction is the pumping divided by the cell's inflow (p. 336, Fig. 1). We read this as gross accounting. The other cells follow one at a time, outward from the well. Source fractions, the reversed-flow MT3DMS run and the free distribution are on pp. 336–338. McLane and Cecan (2009, pp. 172–173) comment on the spread of the fractions on coarse grids.
- **FlowSource.** Foley and Black (2013, Method and Evaluation) give the flow-order pass and the deletion of the smallest flow in each loop. Their section "Description of Calculation" gives the full mixing and the net accounting at destination cells. The snapshot treatment of transient models is in Foley and Black (2013, Introduction) and Black and Foley (2013, Introduction and Problem Description). The outputs, the checks and the availability on request are in the Introduction and end matter of both papers.
- **This paper's code.** The entries rest on Sections 2–4, on Text S1 and on the open code.
- **GWT unit concentration.** Langevin et al. (2022) was read in part. The steady-state statement is in its abstract and on p. 1–7. Upstream weighting is described on pp. 4–1 to 4–2. The flow-imbalance correction is on p. 2–6 (eq. 2–14). The removal of water at the cell's concentration is on p. 5–3 (eq. 5–7). The grids and the transport in packages are listed on pp. 1–6 to 1–7. Bedekar et al. (2024, pp. 303–309) give the method, its uses and the forward reading of well capture (p. 306, Fig. 2).
- **Hydraulic mixing cells.** The column rests on the authors' manuscript of Partington et al. (2011). The update and its stability limit are given in Section 3.1 (Eqs 8–10). The mixing rule is in Section 3.2. The two checks are in Section 3.3.1 (Eqs 13–14). Partington et al. (2012, 2013), Schilling et al. (2017) and Nogueira et al. (2022) describe later versions.

Footnote 1 rests on our own test. We ran a GWT model with MODFLOW 6 (6.9.0.dev0) on the saved flows of test model 1, with upstream weighting, no dispersion and the flow-imbalance correction on. Without the storage package (MST) the run stops at input. With one transport step of 1 day and an MST porosity of 0, the largest difference from G over the 594 active cells was 9.5 × 10⁻¹³ with recharge tagged and 9.7 × 10⁻¹³ with the river tagged.

## Text S1. Method in full

This text gives the parts of the method that Section 2 only names. It covers the matrix form and solution of the equations, the derivation of the water-budget checks, the details of net accounting and the travel time to where water enters a sink cell. It then gives the matrix form of transient tracking and backward tracking in time, the derivation of the transient check, and the details of the water volume options and transport sub-steps. Equation numbers without an S refer to the main text.

### Matrix form and solution of the linear systems

With the outflow shares $P_{ij} = q_{ij}/O_i$ of Eq. (2), the fraction form of Eq. (2), written for all cells together, is

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{S1}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve gives every group. Under gross accounting, a sink term $k$ in cell $i$ takes the share $|q_k|/O_i$ of the cell's outflow. These shares are the entries of $\mathbf{S}$. A cell with no outflow is given $F = 0$.

Eq. (3) divided by $I_i$ and written for every cell, with the inflow shares $Q_{ij} = q_{ji}/I_i$, gives in the same way

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{S2}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group. A cell with no inflow is given $G = 0$.

Equation (2) gives a cell's $F$ from the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource (Foley and Black 2013). A flow loop is a group of cells among which water circulates. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each loop. Foley and Black (2013) expect this to change the results very little. We keep every flow and solve each loop exactly. The matrix is ordered so that the cells come in flow order, with each loop as one block. It is then factorised once by sparse LU decomposition. A model of a million cells with thousands of small loops is factorised in well under a second.

The matrix $\mathbf{I} - \mathbf{P}$ is singular only on a closed recirculation loop. No cell of such a loop has outflow to a sink or to a cell outside the loop, so its water never reaches a sink. These loops are given $F = 0$ and reported. The code also reports every other flow loop and the flow that goes round it. Under gross accounting, one factorisation serves every destination group and the travel times of Eq. (4).

### Why the water-budget checks hold exactly

The checks of Section 2 follow from adding up the volume forms of Eqs. (2) and (3) over all cells. On the right of Eq. (2), each flow $q_{ij}$ appears once, multiplied by the $F$ of the cell it enters. The flows into cell $j$ add up to $I_j - \mathrm{Src}_j$. With $r_i = I_i - O_i$, the sum of Eq. (2) over all cells becomes the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{S3}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. Adding Eq. (3) over all cells gives the forward closure check in the same way:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i . \tag{S4}$$

The forward–backward check links the two systems. Multiply the volume form of Eq. (2) by $G_i$ and Eq. (3) by $F_i$, and add each over all cells. Both results then hold the same double sum of the cell-to-cell flows, $\sum_i \sum_j q_{ij}\, G_i\, F_j$. It cancels when one result is subtracted from the other. What remains is the forward–backward check

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{S5}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included.

The boundary-control check traces every sink term of the model, each as its own destination. The sum of their fractions solves the fraction form of Eq. (2) with $d_i$ replaced by the total sink outflow $\mathrm{Snk}_i$. A value of 1 in every cell solves that equation, because $\sum_j q_{ij} + \mathrm{Snk}_i = O_i$. The solution is unique outside closed recirculation loops. The fractions to all sinks therefore add up to 1 in every other cell with outflow.

The travel-time closure check follows in the same way from multiplying Eq. (4) by each cell's outflow and adding over all cells,

$$\sum_i \mathrm{Src}_i\, m_i - \sum_i r_i\, m_i = \sum_i V_i F_i . \tag{S6}$$

The right-hand side is the volume of water in the model that will end at the destination. The term $\mathrm{Src}_i F_i$ is the volume from cell $i$, and by Eq. (S3) these volumes add up to the destination's inflow once the cell budget errors are included. Eq. (S6) therefore says that this volume equals the destination's inflow times the flow-weighted mean travel time of all its water, apart from the cell budget error terms.

The closure, forward–backward and travel-time checks include the cell budget errors $r_i$. The boundary-control check needs no error term, because it follows from the definition of the outflow. All the checks therefore hold exactly for any flow field, also one that does not balance, outside closed recirculation loops. The errors reported by the code are then round-off, unless the tracing itself is wrong. The code also reports the errors without the budget error terms.

### Net accounting

Net accounting reproduces the way FlowSource attributes water (Foley and Black 2013). It works from the cell-to-cell flows only. With $I^e_i$ and $O^e_i$ the cell-to-cell inflow and outflow of cell $i$, the water passing through the cell is $H_i = I^e_i + \max(O^e_i - I^e_i, 0)$. Outside the destination cells, the backward fraction is

$$f_i = \frac{1}{H_i} \sum_j q_{ij}\, f_j . \tag{S7}$$

The destination cells are fixed at $f = 1$. Their outflows to other cells are ignored. The source terms of the destination cells themselves, such as the recharge on a well's own cell, are also left out, because net accounting uses only the cell-to-cell flows. A forward trace works in the same way on the reversed flows.

Which cells are fixed depends on how the group was selected. A selection by cells or by zone fixes all its cells, as FlowSource does (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace these are the cells where the term is a sink. A well listed at zero rate is therefore not fixed in a backward trace. The same holds for a drain above the water table and a losing river cell.

Net accounting has no cell budget error term. It solves one destination group at a time, because each group fixes its own cells. As an option, it can delete the smallest flow in each flow loop, to compare with studies made with FlowSource.

### Travel time to where the water enters the sink cell

The mean travel time $t_i = m_i/F_i$ of Eq. (4) includes the time spent in the cell where the water leaves, for a well its own cell. Particle trackers that stop particles on entering a sink cell (MODFLOW 6 PRT, MODPATH) measure the time until the water enters that cell. The code also gives this time, as $(m_i - x_i)/F_i$, where $x$ solves $(\mathbf{I} - \mathbf{P})\,\mathbf{x} = \boldsymbol{\tau} \circ (\mathbf{S}\,\mathbf{D})$. Here $\circ$ is the cell-by-cell product. It is the full-mixing time that Text S3 compares with particles.

### Matrix form of transient tracking and backward tracking in time

For all cells, step $n$ of Eq. (5) is one set of linear equations,

$$\mathbf{A}^n \mathbf{c}^n = \mathbf{B}^n \mathbf{c}^{n-1} + \Delta t^n\, \mathbf{s}^n . \tag{S8}$$

$\mathbf{B}^n$ holds the start volumes $V_i^{\mathrm{old}}$ on its diagonal. $\mathbf{A}^n$ holds the other terms of Eq. (5). Each step is solved in flow order as above. Because every cell holds water, no flow loop makes the matrix singular. One factorisation per step, or per sub-step when the volumes change, serves every tagged group. The tagged initial water starts with $c = 1$ in every cell and has no source. Because the storage terms change the volume by $V_i^{\mathrm{old}} - V_i^{\mathrm{new}} = \Delta t^n S_i$ under both volume options, a run that tags every source and the initial water gives $c = 1$ in every cell, with the flow-imbalance correction on.

Backward tracking in time solves the adjoint of Eq. (S8) (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). The adjoint holds the same flows with the roles of inflow and outflow swapped. The tagged water that the destination takes over the whole simulation is $J = \sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n$, where $\mathbf{d}^n$ holds the destination outflow of each cell in step $n$. The backward fraction in time $\mathbf{w}^n$ solves, from the last step $N$ back to the first,

$$\left(\mathbf{A}^n\right)^{\mathsf T} \mathbf{w}^n = \Delta t^n\, \mathbf{d}^n + \mathbf{B}^{n+1} \mathbf{w}^{n+1}, \qquad \mathbf{w}^{N+1} = \mathbf{0} . \tag{S9}$$

Row $i$ of Eq. (S9) is Eq. (6). One value of $w$ describes both the water in a cell at the start of a step and the water entering it during the step, because the implicit scheme mixes the two alike before any water leaves.

The transient forward–backward check follows from Eqs. (S8) and (S9) in the same way as Eq. (S5):

$$\sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n = \sum_n \Delta t^n\, \mathbf{s}^n \cdot \mathbf{w}^n + \sum_i V_i^{\mathrm{old},1}\, c_i^0\, w_i^1 . \tag{S10}$$

The check says that the tagged water the destination takes equals the tagged inflow and the tagged initial water, each multiplied by its share that later reaches the destination. It holds exactly for either volume option and with or without sub-steps. In a backward run, the shares to the destination, to other sinks and still in storage at the end add up to 1, apart from a remainder that the code reports. The remainder is the water that the flow-imbalance correction removes and, with "gwt" volumes, the tagged water that appears or disappears at step boundaries. With "gwt" volumes it need not be small. Test model 10 checks the limit in which c tends to G and w to F under flows held constant (Figure S1).

**Water volume options.** In the default, called "flow", each cell's water volume starts at porosity times saturated volume. It then changes only by the storage flows of the flow model, so every water balance closes exactly. In the "gwt" option, the volume is reset to porosity times saturated volume at the end of each step, as in MODFLOW 6 GWT. Forward transient tracking with this option is unit-concentration transport in GWT with upstream weighting, no dispersion, the flow-imbalance correction and one transport step per flow step (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, tagged water then appears or disappears at step boundaries. We recommend the default unless a result must match a GWT run.

**Transport sub-steps.** Long implicit time steps make tagged water arrive too early (Text S3). Sub-steps reduce this effect without a change to the flow model. Each flow step is split into a chosen number of equal transport sub-steps. The flows stay constant within the flow step. The water volumes change linearly between the start and end of the step.

## Text S2. Software, verification and models

This text describes how the code is tested and the models behind the worked examples of Section 4, so that a reader can rebuild them without the code. All example models are small and synthetic. Each example ships with the code as a Jupyter notebook that builds its model, runs MODFLOW 6 and reproduces its numbers and figure (Section 7). Lengths are in metres and times in days. Rows and columns are counted from 1, from the north-west corner, and layers from the top.

### Inputs and cost

Table S2 lists what the code reads, how destinations and sources are chosen and what it returns.

### Verification

The automated tests run on ten small test models and two hand-built networks. Figure S1 shows the largest error of each check. The test models cover the DIS, DISV and DISU grids, the XT3D option, storage, streams (SFR), the water mover (MVR), multi-aquifer wells (MAW), lakes (LAK), the unsaturated zone (UZF) and simulations split into linked models. Test model 1 is the base case. It is one layer of 20 × 30 cells of 50 m, with constant heads on the west edge, a river along one column, recharge and a well pumping 800 m³/d. The two hand-built networks are the worked example of Foley and Black (2013) and a network of 15 cells with flow loops. The archived code release (Section 7) describes the test models in tests/models/README.md. It lists the error of each check on each model in docs/verification.md.

### The example model

The example model is one convertible layer (DIS) of 40 × 40 cells of 50 m, 2 km on each side. The top is at 20 m and the bottom at −30 m. The hydraulic conductivity is 5 m/d everywhere. Constant heads of 10 m (CHD) fill the 40 cells of column 1. A river (RIV) fills the 40 cells of column 31, with a stage of 6 m, a bottom of 4 m and a conductance of 500 m²/d per cell. Recharge of 5 × 10⁻⁴ m/d (RCH) falls on every cell. The supply well (WEL) pumps 800 m³/d from row 21, column 29. Its cell centre is 100 m west of the river cell centres. The model is steady state. Travel times and particle tracking use a porosity of 0.3.

The weight-losing PRT particles of Section 4 are released from every source term of every cell with $F > 10^{-6}$. Each source term gets 16 release points, spread over the cell in plan. This gives 18,208 particles from 1,133 cells.

### Variants of the example model

Each variant below names only what changes from the example model.

- **Three-layer model.** The layer bottoms are at 0, −12 and −30 m. The horizontal hydraulic conductivity is 10, 1 and 15 m/d from the top. The vertical conductivity is one tenth of the horizontal. The constant heads fill column 1 of every layer. The supply well pumps from layer 3. A small well pumps 5 m³/d from layer 3 at row 17, column 13, 800 m west and 200 m north of the supply well.
- **Field and GWT run.** The forward example traces the recharge on a field of 6 × 6 cells in rows 11–16 and columns 13–18. The GWT model reads the saved flows and runs for 10⁶ days in 10 steps, with a porosity of 0.3, upstream weighting, no dispersion and the flow-imbalance correction. River leakage has a concentration of 1. All other water has a concentration of 0.
- **Grids.** The Voronoi grid (DISV) is built with vorflow version 0.2.0 (Hugman and Sanchez 2026). Its cells are about 50 m across away from the well and the river. They shrink to 10 m at the well and 12.5 m along the river. The grid has 3,241 cells. Two DISU models hold the 1,600 cells of the example model, one with cell vertices and one without. The XT3D model adds the XT3D option and a random, anisotropic hydraulic conductivity, with a ratio of 20:1 and an axis that rotates across the model.
- **Seasonal model.** The layer has a specific yield of 0.2 and a specific storage of 10⁻⁵ m⁻¹. A steady-state period of 1 day is followed by seasons of 91.3 days. The recharge is multiplied by 1.8 in the wet season, 1.0 in the wet-to-dry transition, 0.1 in the dry season and 1.1 in the dry-to-wet transition. The well pumps 640, 800, 1,120 and 640 m³/d in the same seasons. The snapshot example runs 3 years with three time steps per season. The transient-tracking example runs 30 years with one time step per season, 121 time steps in all. Its well already pumps at its mean rate in the steady-state period. Its tracking uses a porosity of 0.3, four transport sub-steps and the default "flow" water volumes.
- **Streams, drains and linked models.** The river becomes an SFR stream with one reach per row, flowing from north to south. The first reach receives 300 m³/d. Two drains in column 15, at rows 9 and 23, pass 80 % and 100 % of their water to the first reach through the water mover (MVR). The split model divides the example model into three models joined by exchanges, with the FloPy model splitter (Hughes et al. 2024). The well and the river then lie in different models.

### The ensemble and history matching

The 50 realisations of the ensemble differ only in their hydraulic conductivity. Each field is set at 100 pilot points, 200 m apart, and interpolated to every cell by simple kriging of $\ln K$ around $\ln 5$. The correlation between two points a distance $r$ apart is $\exp(-(r/400\ \mathrm{m})^2)$. The prior draws the pilot-point values as $K = 5 \exp(0.8\, z)$, where $z$ is a correlated standard normal variable.

The true aquifer is a random field with the same statistics. It is made by smoothing white noise, not from pilot points. A kriged field is smoother between the pilot points than the true field. So no realisation can reproduce the true field exactly. The river supplies 9.4 % of the water the true model pumps. Its steady-state heads in 40 random cells are the measurements. Each head has added noise with a standard deviation of 0.05 m. PEST++ IES adjusts the 100 pilot-point values of each realisation to fit these heads, with weights of one over the noise. After three iterations, the mean weighted sum of squared head residuals had fallen from 3,491.7 to 55.5. A fit within the noise would give about 40, the number of measurements. The 50 posterior realisations are then rerun and traced in the same way as the prior.

### The rebuilt model of Bedekar et al. (2024)

We rebuilt the MODFLOW-2005 model of Bedekar et al. (2024, pp. 305–306 and Fig. 1) in MODFLOW 6. The grid has 101 × 101 cells of 10 m and three layers of 10 m, with the top at 30 m. The horizontal hydraulic conductivity is 10 and the vertical conductivity 1. The specific storage is 10⁻⁵ m⁻¹, the specific yield 0.1 and the porosity 0.1. Lateral inflow of 454.5 m³/d enters along the west column of all three layers. Recharge of 3 × 10⁻⁴ m/d falls on layer 1. A stream (RIV) fills the east column, with a stage of 30 m and a conductance of 1,000 m²/d per cell. The well pumps 700 m³/d for 25 years after a steady-state period of 1 day without pumping. The paper leaves some values open. We made the following choices.

- The paper gives the hydraulic conductivity in feet per day and the other inputs in metric units. We read it as metres per day. A rerun in feet per day moved the long-run shares by at most 0.1 percentage points.
- All three layers are convertible. The river bottom is at the bottom of each cell.
- The well is in layer 2, where Fig. 1 of the paper draws its screen, at row 51, column 86. That is 150 m west of the stream cell centres.
- The pumping period has 300 equal steps of 30.4 days. The tracking uses the "gwt" water volumes.
- All the water in the model at the start is tagged as initial water. The paper instead fixes the concentration of the stored water at 1 during the first period.

For the comparison, four MODFLOW 6 GWT models carry one tagged group each. They have the settings of the GWT run of the field example, except a porosity of 0.1.

## Table S2. Inputs, selections and outputs

**Table.** What the code reads, how destinations and sources are chosen, and what it returns. The last column gives where each item is shown, in the main text (Section 4) or in Text S3. MODFLOW 6 option names are given where a user must set them.

| | Item | What it is or needs | Shown in |
|---------|-----------------|--------------------------------------------------------|------------------|
| **Inputs** | Binary grid file | Cell connections of a DIS, DISV or DISU grid. Written by MODFLOW 6 by default | Section 4, Text S3 |
| | GWF budget file | Cell-to-cell flows and every source and sink term. SAVE_FLOWS in each package, budget saved in Output Control | Section 4 |
| | Every time step saved | Needed for transient tracking (SAVE BUDGET ALL) | Section 4, Text S3 |
| | Saturated thickness | For travel times and transient tracking. NPF SAVE_SATURATION, or the head file | Section 4, Text S3 |
| | Porosity | Given by the user. Needed for travel times and transient tracking, not for fractions | Section 4, Text S3 |
| | Package budget files | SFR, LAK, MAW, UZF and MVR budgets (BUDGET FILEOUT), to trace through package networks | Section 4, Text S3 |
| | Linked models | GWF models joined by exchanges, read as one system (SAVE_FLOWS in the exchange) | Section 4, Text S3 |
| **Selections** | Package | All terms of a package, such as all recharge or all wells | Section 4 |
| | Boundname | Terms with a given boundname, such as one well. Read from the package input files | Section 4 |
| | Boundary number | Terms with given boundary numbers in a package | – |
| | Cells | All terms in the given cells (gross accounting), or the cells themselves (net accounting) | Text S3 |
| | Zone | Cells with a given zone value, alone or with a package, such as the recharge on one field | Section 4, Text S3 |
| **Outputs** | Backward fraction F | Share of each cell's water that ends at the destination | Section 4 |
| | Forward fraction G | Share of each cell's water that came from the source | Section 4, Text S3 |
| | Volumes | Volume through, volume from and volume to, and their split by package | Section 4 |
| | Gross and net accounting | Water attributed to a weak-sink well under each rule. Boundary-control maps | Section 4, Text S3 |
| | Budget checks | Closure, forward–backward and boundary-control checks with every trace | Section 4, Text S3 |
| | Mean travel time | Mean time to the destination under full mixing | Section 4, Text S3 |
| | Snapshot statistics | Minimum, mean and maximum F over time steps. Cells always, sometimes or never above a threshold | Section 4, Text S3 |
| | Transient tracking | Tagged fractions c (forward) and w (backward in time). Destination's water by source, time step and initial water | Section 4, Text S3 |
| | Ensemble statistics | Mean, probability of exceeding a threshold, and exact or histogram quantiles over realisations | Section 4 |
| | PRT release points | Particle runs on the same flows, for comparison | Section 4, Text S3 |
| | Export | NumPy and netCDF files. GeoPackage polygons for GIS | – |

## Figure S1. Verification checks on the test models

![](fig/figS21_verification.png){width=90%}

**Figure.** Largest error of each verification check of the automated tests. Each row is one check. Each marker is the largest error of that check on one case. The cases are the ten test models, the worked example of Foley and Black (2013) and a hand-built network of 15 cells. Markers in the "exact" column have an error of zero. The dashed line is machine precision, the size of rounding error. Light grey bars are the tolerances of the automated tests. A row with two bars has a looser tolerance for one model. Upper block: steady-state and snapshot checks. Lower block: transient tracking checks. Its last row tests transport sub-steps. The closure checks are relative to the destination or source inflow. The forward–backward checks are relative to the volume traced from the source to the destination. These three are absolute, in m³/d, where that flow is below 1 m³/d. The comparisons with GWT, the boundary-control check, the published example and the steady-state limits are absolute differences of fractions. DISU against DIS, split against single models and sub-steps against refined steps are relative to the largest output value. PRT is relative to the well's inflow. The water balance is relative to the cell's water volume. The tagged-water balance is relative to its largest term.

## Text S3. The worked examples in brief

This text backs the rows of Table 1 in Section 4. Worked examples A, B and C of Section 4 give their own results and checks. For the other rows, and for the checks of example B, this text gives what changes in the model, the main results and the checks. Text S2 describes the models. The figures of this text follow it.

**Accounting at a small well.** The two accountings of Section 2 differ only at weak sinks. A small well in strong regional flow is a typical weak sink. This example shows how much the choice of accounting changes the water attributed to such a well. It uses the three-layer model, where a small well pumps 5 m³/d upgradient of the supply well. The small well's cell carries 33.7 m³/d. Gross accounting counts only the 5 m³/d that the well pumps. F in the well's cell is then 5/33.7 = 0.149. Net accounting fixes F = 1 in the cell. It attributes all 33.7 m³/d to the well. This is 6.7 times what the well pumps. Under gross accounting, 82 % of the water in the small well's cell flows on to the supply well. The supply well takes all the water that flows into its cell. Both accountings therefore give it the same water.

Net accounting reproduces the worked example of Foley and Black (2013) in every cell to 1 × 10⁻¹⁴. This check is independent of the code, because the example's fractions, volumes through and volumes from are published. On the three-layer model, the fractions to all sinks add up to 1 within 1 × 10⁻¹⁵, as the boundary-control check of Section 2 requires.

**Transient checks on the seasonal example model.** Example B of Section 4 tracks the well's water on the 30-year seasonal model. The table lists the checks of transient tracking on this model. The rows use the main run, with four transport sub-steps per flow step and the default "flow" volumes, except where a row names another set-up.

| check | largest error |
|--------------------------------------------------------------------------------|--------------------|
| forward tracking against backward tracking in time, tagged volumes of every tag, main run | 4.3 × 10⁻¹⁶ |
| tracked recharge fraction against a GWT run, "gwt" volumes, one transport step per flow step | 9.8 × 10⁻¹⁴ |
| fractions to the well, to the river and still stored, which must add up to 1 in every cell, "flow" volumes, one transport step per flow step | 2.5 × 10⁻¹¹ |
| backward closure, main run | 0 |
| tagged-water balances, main run (four transport sub-steps) | 9.9 × 10⁻¹⁶ |

The two water volume options of Text S1 give nearly the same result here. Both were run with one transport step per flow step. With "gwt" volumes, about 5,300 m³ of the 45.6 million m³ of initial water is lost over 30 years. The year-30 share of initial water is 0.5167 with these volumes and 0.5166 with the default "flow" volumes. With one transport step per flow step, the two options differ by up to 1.9 × 10⁻⁴ in the forward fractions and up to 3.7 × 10⁻³ in the backward fractions.

Long transport steps make tagged water arrive too early. With one transport step per flow step, new recharge made up 0.0078 of the well's water in the first step. It made up 0.0049 with four sub-steps and 0.0042 with 16. With one, four and 16 sub-steps, the river supplied 3.6, 3.1 and 3.0 % of the well's water in the last season of year 1. From four sub-steps to 16, the year-1 shares moved by at most 0.2 percentage points. The main runs therefore use four.

**Ensembles.** Figure S4 maps the probability of contribution before and after history matching. The area where it lies between 0.1 and 0.9 shrinks from 1.10 km² in the prior to 0.35 km² in the posterior. The posterior gives a probability of at least 0.5 to 93 % of the true F > 0.5 area, against 79 % for the prior.

**Where each source's water goes.** A forward trace starts at a source rather than at a well. Example C of Section 4 gives its main results. G in the well cell gives the pumped water by source, with the same shares as the backward trace of Section 4. The forward and backward traces give the same volume from each source to the well within 1 × 10⁻⁶ m³/d. The difference equals the cell budget error term of Eq. (S5). The GWT run reaches equilibrium after 10⁶ days. Its concentrations of river water then equal G in every cell to 4.2 × 10⁻¹³.

**The same trace on different grids.** The two DISU models give the DIS result in every cell. On the Voronoi grid, the contributing area has the same shape and reach. Its expected area is 1.178 km², against 1.173 km² on the regular grid. The expected area is the sum of F times the cell area over all cells. North of the well, F falls from 0.5 to 0.1 over 186 m on the Voronoi grid, against 121 m on the regular grid. On the regular grid the water flows along the rows, so each cell passes nearly all its water to one neighbour. Each Voronoi cell splits its water among two or three downstream cells, because its faces lie at many angles to the flow. We read the wider edge as a sideways spread of F by these splits. Text S5 tests this reading on squares turned to the flow.

With the XT3D option, the flow across a face depends on the heads of the surrounding cells as well. Water can then go round in flow loops. The trace of the XT3D model found five groups of cells with flow loops, 40 cells in all. Together they circulate 4.4 m³/d. That is 0.016 % of the summed outflow of all cells in the model. The loop-by-loop solve of Text S1 equals a solve of the whole system at once to 3.3 × 10⁻¹⁶. Under net accounting, deleting the smallest flow of each loop, as FlowSource does, changes F by up to 0.155 on this model.

**The contributing area through the seasons.** Each of the 36 seasonal steps of the 3-year seasonal model is traced as a snapshot. The F > 0.5 area is smallest in the wet season, at 0.59 km². In that season the well pumps least. The rising water table also puts water into storage. Storage then acts as a sink that takes part of each cell's water. In the dry season the F > 0.5 area grows to 1.35 km². Statistics over the 36 steps give nested zones (Fig. 2e). Cells with F > 0.5 in every step form an inner zone of 0.52 km². Cells with F > 0.5 in some steps add a seasonal zone of 0.93 km². Cells with F > 0.1 in at least one step add a further 0.41 km². These nested zones are one way to combine the maps. They are not a rule for drawing protection zones. In every snapshot, the traced sources add up to the pumping within 1 × 10⁻⁶ m³/d.

**Streams, drains and linked models.** On the aquifer cells alone, the trace stops at the stream. Stream leakage then supplies 32 % of the well's water. With the reaches traced as cells of their own, that water splits into 129 m³/d of upstream stream inflow and 126 m³/d of recharge. That recharge had discharged to the drains or the stream. The traced volumes add up to the pumping to round-off, with and without the reaches as cells. The split model gives F to within 2 × 10⁻¹³ of the single model. Both simulations solve the same flow equations, so this is a consistency test. It shows that no water is lost where the models meet.

## Figure S2. Snapshots and transient tracking over 30 years

![](fig/fig9_transient_tracking.png){width=80%}

**Figure.** Snapshots and transient tracking on the 30-year seasonal example model (Section 4). Star: supply well. In (c–f), sky-blue cells mark the river. White contours mark fractions of 0.1 (dashed) and 0.5 (solid). (a) Snapshots: the well's water by source, each step traced on its own flows. (b) Forward transient tracking: the well's water by tagged source, including initial water. The dashed line is the initial water's share of all water pumped so far. Its labels give this share after 1, 10 and 30 years. (c) Steady-state F for the first step's flows. (d–f) Backward tracking in time: for the water in each cell at the start, the fractions that leave through the well (w) or the river within 30 years, and the fraction still stored.

## Figure S3. Time-limited contributing areas in the unit-concentration example

![](fig/figS24_unit_concentration_maps.png)

**Figure.** Backward tracking in time in the unit-concentration example of Bedekar et al. (2024), rebuilt in MODFLOW 6. Main-text Fig. 3b shows the well's water by origin in the same model. The maps show layer 2, where the well is screened. Star: well. (a–d) For the water in each cell at the start, colour gives the fraction that the well pumps within 1, 5, 10 and 25 years. (e) Steady-state backward fraction F for the flows of the last time step, for comparison.

## Figure S4. Probability of contribution before and after history matching

![](fig/fig10_ensembles.png)

**Figure.** Probability of contribution before and after history matching on the example model (Section 4). The probability of contribution of a cell is the share of realisations in which more than half of the cell's water ends at the well (F > 0.5). (a) Probability of contribution over 50 prior realisations of the hydraulic conductivity field. (b) The same over the 50 realisations after history matching to heads with PEST++ IES. Black lines: probabilities of 0.1, 0.5 and 0.9. Red dashed line: F = 0.5 in the synthetic true model, which supplied the measured heads. White circles: the 40 cells with head measurements. (c) Share of the pumped water that comes from the river, in each prior and posterior realisation. Each dot is one realisation. Boxes span the 25 to 75 % range and whiskers the 5 to 95 % range. Red dashed line: the river share of the true model.

## Text S4. The Neversink comparison

Section 5 compares full mixing with the published particle tracking of the Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022). Section 5 also defines the calibrated model, the start cells, the published contributing cells and the overlap. This text gives the cost of the trace and of the particle runs, the delineations behind the overlaps and how the published particles end. The model is in a USGS data release (Fienen and Corson-Dosch 2021).

The 122,021 start cells are the uppermost active cell of each column in three regions around the wells. The expected area of a map of F is the sum of F over the start cells. It is a size of the contributing area that needs no threshold. All Neversink cells are 50 m squares, so expected areas are given as numbers of cells.

### Cost of the trace and of the particle runs

The trace was timed on an Apple M4 Max with 16 cores and 64 GB of memory. One trace of the nine destination groups took 2.4 to 2.7 s in all. Reading the budget file took 1.0 to 1.2 s of this. The trace itself took 1.4 to 1.5 s. Memory peaked at 2.52 GB, of which 0.52 GB was the loaded budget. A trace of the eight wells together, as one group, peaked at 0.98 GB. Each further group therefore adds about 0.19 GB on this model of 1.68 million cells. The closure check held to 1 × 10⁻¹² m³/d or better for every group. This was so with the stream reaches left as source and sink terms and with them traced as the stream network.

The PRT runs of Section 5 differ in what they release and what they write. The runs that reproduce the published area release one unweighted particle at each published start and write only where each particle ends. Each took about 30 s. The flow-weighted runs release particles from every source term of the 30,180 cells with F > 10⁻⁶, in all layers, and write full tracks. With four release points in plan at one height, 122,112 particles took about 5 min and wrote a track file of about 1.5 GB. With the same points at four heights, 488,448 particles took about 13 min and wrote about 6 GB. The peak memory of PRT was not measured.

### Delineations on one flow field

The table compares the delineations of the eight wells' contributing area on the calibrated model, with the stream reaches left as source and sink terms of the aquifer cells. Each is compared with the 980 published contributing cells.

| method | delineation | overlap | expected area (cells) | flow attributed to the wells (m³/d) |
|------------------------|------------------------------------|---------|-------------|------------------|
| Full mixing, gross accounting | F > 0.1 | 0.30 | 910 | 3,671 |
| | F > 0.5 | 0.41 | 910 | 3,671 |
| | area-matched (980 cells) | 0.41 | 910 | 3,671 |
| Full mixing, net accounting | F > 0.1 | 0.28 | 978 | 3,944 |
| | F > 0.5 | 0.44 | 978 | 3,944 |
| | area-matched (980 cells) | 0.40 | 978 | 3,944 |
| PRT, flow-weighted, weight-losing | released over the cell volume, P > 0.5 | 0.62 | 794 | 3,736 |
| | released mid-cell, P > 0.5 | 0.62 | 781 | 3,722 |
| | released at the water table, P > 0.5 | 0.39 | 592 | 2,413 |
| PRT, flow-weighted, losing weight only at wells | released over the cell volume, P > 0.5 | 0.29 | 2,857 | 9,555 |
| PRT, published starts | MODFLOW 6 default, dry starts dropped to the water table | 0.62 | 730 | – |
| | MODFLOW 6 default, dry starts draped | 0.65 | 754 | – |
| | top face where open, dry starts dropped | 0.96 | 969 | – |
| | top face where open, dry starts draped (published settings) | 0.998 | 982 | – |

Thresholds are strict. The area-matched delineation takes the 980 start cells with the largest F. For flow-weighted PRT, the expected area is the particle weight that reaches the wells, in cells. For published starts, it is the number of start cells whose particle ends in a priority well. The flow-weighted particles were released from the source terms of the 30,180 cells with F > 10⁻⁶, in all layers. P is the share of the water released in a start cell that the particles deliver to the wells. The published-start runs use one unweighted particle per published start, stopped at every weak sink. "MODFLOW 6 default" spreads recharge and stream flows through the cell. "Top face where open" puts them on the top face through IFLOWFACE, the MODFLOW 6 setting that assigns a boundary flow to one cell face.

The wells take 3,671 m³/d. Gross accounting attributes exactly this flow to them. Net accounting attributes 3,944 m³/d, because it also counts the water that passes on from the well cells. Weight-losing particles deliver within 2 % of the wells' inflow. Particles that lose weight only at the wells deliver 9,555 m³/d. That is 2.6 times the wells' inflow. They keep the weight that streams and other sinks take on the way. Their delivery is therefore water the particles assign to the wells, not water that flows into them.

The 87 % of Section 5 is 602 of the 691 start cells where weight-losing particles released over the cell volume deliver more than half their water to the wells. It is an upper bound, because the particles were released only from cells with F > 10⁻⁶. A cell left out that would have delivered more than half its water would be one more missed cell. The weight-losing particles also lose weight at each sink by the full-mixing shares. For this reason they are not an independent particle area. The comparison measures only the spreading that full mixing adds between sinks.

With the stream reaches left as source and sink terms, full mixing traces 2,100 m³/d of the wells' water to recharge and 1,571 m³/d to stream leakage. Along the paths of the weight-losing particles, the wells receive 344 m³/d more stream water and 279 m³/d less recharge. Most of the extra stream water leaks from reaches 0.4 to 1.3 km south of the U wells and 0.5 to 1.2 km from SV_487. In a cell that receives both sources, the two reach the wells in the same proportion under either method. The difference therefore comes from where each source enters the aquifer.

### End states of the published particles

Each published MODPATH 7 particle on the calibrated model ends in one of three ways. We classed each end cell on the MODFLOW 6 budget. A strong sink sends all of its outflow to boundary sinks. A weak sink sends only part of it.

| end state (MODPATH status) | particles | end cells | particles ending in a priority well |
|----------------------------|-----------|---------------------------------------------|----------------|
| leaves the model through a cell face (2) | 89,920 | top face of a stream cell with no active cell above: 88,781; side face next to a dry cell: 1,139 | 0 |
| stopped on entering a weak-sink cell (3) | 27,631 | buried stream cells: 26,828; wells: 612; constant heads: 191 | 466 |
| ends in a cell with no exit face (5) | 4,470 | wells: 2,570; buried stream cells: 1,472; constant heads: 428 | 514 |

The 980 published contributing cells are the 514 particles that end in the three priority wells that take all of their cell's outflow. They also include the 466 particles stopped in the five priority wells that take only part of it.

A buried stream cell is a cell with an SFR reach and another active cell above it. The published runs put recharge and stream flows on the top face of the cell. MODPATH 7 does this only where the top face has no active neighbour. Elsewhere the flow stays spread through the cell. A particle that reaches a stream cell with no active cell above therefore leaves through the top face (status 2). A particle that reaches a buried stream cell is stopped there as at a weak sink (status 3). Every particle that stops in a stream cell has an active cell above it. None of those that leave through a stream cell's top face has.

At the weak-sink wells, the published particles and full mixing treat the cell's water differently. The well of U\_\_\_7 takes 44 % of its cell's outflow. All the water of a published particle that enters the cell still counts as reaching U\_\_\_7. Under full mixing, the other 56 % of the cell's outflow passes on, most of it to U\_\_\_8 and U\_917. So 97 % of the water in the cell reaches a priority well (F = 0.97).

### The ensemble

Section 5 gives the cost of the two traces of each realisation. One trace left the stream reaches as source and sink terms. The other traced them as the stream network. The whole ensemble, with its MODFLOW 6 runs, took 76 min in six parallel processes. The published study maps a probability of contribution. It is the share of 357 published Monte Carlo contributing areas that contain a cell. Mean F over the realisations, with the stream reaches left as source and sink terms, is the full-mixing counterpart (Figure S5b). It correlates with the published probability at r = 0.80. Its expected area is 0.90 times the published one. The stored published areas lie one row south of their cells, so we moved them one row north before this comparison. The archived code release (Section 7) explains this offset in docs/neversink_study.md.

## Figure S5. Neversink particle area and ensemble mean F

![](fig/figS22_neversink_cd.png)

**Figure.** The eight priority wells of the Neversink/Rondout model, in the 7.1 × 9.25 km window of main-text Fig. 4. All maps show the uppermost active cell, with the stream reaches left as source and sink terms and gross accounting. (a) The F > 0.1 area against the area where weight-losing PRT particles, released over the cell volume, deliver more than half their water to the wells (P > 0.5). Dark blue: in both (495 cells in this window). Orange: particles only (86). Light blue: F > 0.1 only (1,133). (b) Mean F over 358 realisations, with the published probability of contribution 0.5 outlined. Grey: below 0.01. (c) The model, the three regions of the published particle runs (dashed) and the window. Orange dots: wells. Blue lines: SFR reaches. Scale bar (a): 2 km.

## Text S5. Numerical dispersion test problems

Full mixing spreads the edge of a contributing area over a band of cells, because each cell mixes the water it receives. This spreading comes from the grid, not from the aquifer. We refer to it as numerical dispersion. Two test problems measure how wide the band is and how it changes with cell size $h$.

Problem A is a confined aquifer, 2 km × 2 km, with a transmissivity of 500 m²/d, a regional hydraulic gradient of 0.002 and one well pumping 500 m³/d. The perimeter cells hold the analytical head of uniform flow plus a well. The reference is the analytical capture zone of Javandel and Tsang (1986). The regional flow runs along the grid rows or at 30° to them. The grids have square cells of 200 to 12.5 m (DIS) or Voronoi cells of about the same mean size (DISV). Problem B is test model 1 without its inactive cells (Text S2). It is one unconfined layer of 1.5 km × 1 km, with recharge, a river, a constant-head west edge and a well pumping 800 m³/d. Its grids have cells of 100 to 12.5 m. Its reference is PRT on the 12.5 m grid, with about 94,000 flow-weighted particles released at the water table. East of the river, all water passes the gaining river. The river is a weak sink there. So the areas of problem B are compared west of the river only.

Across cell sizes, the band where F lies between 0.1 and 0.9 was 1.2–12 cells wide (Figure S6). In metres, it narrowed only as about the square root of $h$, with fitted rates of 0.4–0.6. For cells of 50 m or less, the size of the F > 0.5 area was within 5 % of the reference area. The F > 0.1 area missed at most 0.1 % of the reference area in every run. For cells of 12.5–50 m, it was 30–90 % larger than the reference area in problem A and 8–16 % larger in problem B. Voronoi grids spread the edge no less than square cells. Face-to-face routing (Chowdhury 2016) is an experimental 2D option that passes water between cell faces instead of mixing it across the whole cell. It removed 35–70 % of the excess spreading. It did not change how fast the band narrows with $h$, because water still mixes across each cell face.

The orientation of the grid matters as well. On the example model, F falls from 0.5 to 0.1 north of the well over 121 m on the regular grid, whose rows run along the flow. On squares of 47 m turned by 45° to the flow, the same band is 215 m wide. That is 1.8 times as wide. On a Voronoi grid with cells of about 25 m, it is 126 m wide.

Totals depend much less on mixing. On the same grid, the well's shares by source were the same to three digits under full mixing, face routing and particles. For cells of 50 m or less, the flow-weighted mean travel time of all the water reaching the well was within 2 % of particle tracking in problem B and within 4 % of the analytical value in problem A.

The dispersion study draws areas with F ≥ 0.1 and F ≥ 0.5, while the main text writes F > 0.1 and F > 0.5. No full-mixing cell in these tests has F exactly 0.1 or 0.5, so both forms select the same full-mixing cells.

## Figure S6. Numerical dispersion maps and cell size

![](fig/figS23_numerical_dispersion.png)

**Figure.** Numerical dispersion of full mixing. F is the share of a cell's water that reaches the well (dot). (a–d) Problem A on 50 m cells, with uniform flow at 30° to the grid rows. The first map is the exact capture zone averaged over each cell, the best a cell-based method can do. Dashed: the analytical capture-zone edge. (e–h) Problem B: PRT on the 12.5 m grid and the three methods on 50 m cells. Dashed: the PRT F = 0.5 edge. Grey line: the gaining river. DIS: square cells. DISV: Voronoi cells. (i–n) The width of the band where 0.1 < F < 0.9, and the relative error in the size of the F > 0.1 and F > 0.5 areas, against the mean cell size h. Top row: problem A, with flow along the grid rows (solid) or at 30° to them (dotted). Bottom row: problem B. Dashed guide: $h^{0.5}$. Grey band: ±5 %.

## References cited only in the Supporting Information

Black, A., and C. Foley. 2013. FlowSource: A program to efficiently delineate volumetric capture areas, pathways and source areas in groundwater models. In *Proceedings of MODFLOW and More 2013: Translating Science into Practice*, Golden, Colorado, June 2–5, 2013, 652–663. Golden, Colorado: IGWMC, Colorado School of Mines. https://groundwater-science.co.uk/wp-content/uploads/2013_FSv6_ApplicationPaper.pdf

Campana, M.E., and E.S. Simpson. 1984. Groundwater residence times and recharge rates using a discrete-state compartment model and C-14 data. *Journal of Hydrology* 72, no. 1–2: 171–185. https://doi.org/10.1016/0022-1694(84)90190-2

Chowdhury, M.A. 2016. Assessing the connectivity of groundwater wells to surface-water using a volumetric capture delineation tool. MASc thesis, University of Waterloo, Waterloo, Ontario, Canada. http://hdl.handle.net/10012/10981

Cornaton, F., and P. Perrochet. 2006. Groundwater age, life expectancy and transit time distributions in advective–dispersive systems: 1. Generalized reservoir theory. *Advances in Water Resources* 29, no. 9: 1267–1291. https://doi.org/10.1016/j.advwatres.2005.10.009

Corson-Dosch, N.T., M.N. Fienen, J.S. Finkelstein, A.T. Leaf, J.T. White, J. Woda, and J.H. Williams. 2022. Areas contributing recharge to priority wells in valley-fill aquifers in the Neversink River and Rondout Creek drainage basins, New York. U.S. Geological Survey Scientific Investigations Report 2021–5112. Reston, Virginia: USGS. https://doi.org/10.3133/sir20215112

Hughes, J.D., C.D. Langevin, S.R. Paulinski, J.D. Larsen, and D. Brakenhoff. 2024. FloPy workflows for creating structured and unstructured MODFLOW models. *Groundwater* 62, no. 1: 124–139. https://doi.org/10.1111/gwat.13327

Hugman, R., and O. Sanchez. 2026. vorflow: Voronoi mesh generation for MODFLOW 6. Version 0.2.0. Software, released 5 October 2026. https://github.com/rhugman/vorflow

Javandel, I., and C.-F. Tsang. 1986. Capture-zone type curves: A tool for aquifer cleanup. *Ground Water* 24, no. 5: 616–625. https://doi.org/10.1111/j.1745-6584.1986.tb03710.x

Langevin, C.D., J.D. Hughes, E.R. Banta, R.G. Niswonger, S. Panday, and A.M. Provost. 2017. Documentation for the MODFLOW 6 Groundwater Flow Model. U.S. Geological Survey Techniques and Methods, book 6, chap. A55. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A55

McLane, C., and L. Cecan. 2009. Comment on "MODALL: A practical tool for designing and optimizing capture systems," by S.T. Potter, E. Moreno-Barbero, and C.E. Divine. *Ground Water* 47, no. 2: 172–173. https://doi.org/10.1111/j.1745-6584.2008.00527_1.x

Nogueira, G.E.H., C. Schmidt, D. Partington, P. Brunner, and J.H. Fleckenstein. 2022. Spatiotemporal variations in water sources and mixing spots in a riparian zone. *Hydrology and Earth System Sciences* 26, no. 7: 1883–1905. https://doi.org/10.5194/hess-26-1883-2022

Partington, D., P. Brunner, C.T. Simmons, A.D. Werner, R. Therrien, H.R. Maier, and G.C. Dandy. 2012. Evaluation of outputs from automated baseflow separation methods against simulated baseflow from a physically based, surface water–groundwater flow model. *Journal of Hydrology* 458–459: 28–39. https://doi.org/10.1016/j.jhydrol.2012.06.029

Partington, D., P. Brunner, S. Frei, C.T. Simmons, A.D. Werner, R. Therrien, H.R. Maier, G.C. Dandy, and J.H. Fleckenstein. 2013. Interpreting streamflow generation mechanisms from integrated surface-subsurface flow models of a riparian wetland and catchment. *Water Resources Research* 49, no. 9: 5501–5519. https://doi.org/10.1002/wrcr.20405

Provost, A.M., C.D. Langevin, and J.D. Hughes. 2017. Documentation for the "XT3D" option in the Node Property Flow (NPF) Package of MODFLOW 6. U.S. Geological Survey Techniques and Methods, book 6, chap. A56. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A56

Schilling, O.S., C. Gerber, D.J. Partington, R. Purtschert, M.S. Brennwald, R. Kipfer, D. Hunkeler, and P. Brunner. 2017. Advancing physically-based flow simulations of alluvial systems through atmospheric noble gases and the novel ³⁷Ar tracer method. *Water Resources Research* 53, no. 12: 10465–10490. https://doi.org/10.1002/2017WR020754
