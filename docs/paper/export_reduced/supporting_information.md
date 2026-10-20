# Supporting Information for “Where does it come from and where does it go? Open-source flow tracing for MODFLOW 6 models”


# Table S1. Comparison of methods

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

¹ Steady state is reached by running transient steps until concentrations stabilise (Langevin et al. 2022). In our test on the saved flows of test model 1, one GWT step of 1 day with the storage package (MST) and a porosity of 0 reproduced the steady-state G to 1 × 10⁻¹². GWT does not run without MST. This use of porosity 0 is not documented.

² The update is stable only while a step's inflow or outflow volume does not exceed the cell's storage (Partington et al. 2011). Later versions add sub-steps (Partington et al. 2013) and aquifer cells (Schilling et al. 2017). All of them step forward in time only.

³ After Campana and Simpson (1984): water leaving a cell over a step carries the previous step's mix.

⁴ A closed recirculation loop is a group of cells with no outflow to any sink or to a cell outside the group. Such loops are reported. No connections are deleted.

⁵ No backward option is documented (Langevin et al. 2022). Bedekar et al. (2024) read well capture forward in time, from the concentration simulated at the well.

# Text S1. Method in full

This section describes the methods in full. It covers the matrix form and solution of the equations, the derivation of the water-budget checks, the details of net accounting and the travel time to where water enters a sink cell. It then presents the matrix form of transient tracking and backward tracking in time, the derivation of the transient check, and the details of the water volume options and transport sub-steps. Equation numbers without an S refer to the main text.

## Matrix form and solution of the linear systems

With the outflow shares $P_{ij} = q_{ij}/O_i$ of Eq. (2), the fraction form of Eq. (2), written for all cells together, is

$$(\mathbf{I} - \mathbf{P})\,\mathbf{F} = \mathbf{S}\,\mathbf{D}. \tag{S1}$$

Here $\mathbf{I}$ is the identity matrix. $\mathbf{S}$ holds the share of each cell's outflow that leaves through each of its sink terms. $\mathbf{D}$ marks which sink terms belong to which destination group. Each column of $\mathbf{F}$ holds the fractions to one destination group, so one solve yields every group. Under gross accounting, a sink term $k$ in cell $i$ takes the share $|q_k|/O_i$ of the cell's outflow. These shares are the entries of $\mathbf{S}$. A cell with no outflow is assigned $F = 0$.

Eq. (3) divided by $I_i$ and written for every cell, with the inflow shares $Q_{ij} = q_{ji}/I_i$, yields in the same way

$$(\mathbf{I} - \mathbf{Q})\,\mathbf{G} = \mathbf{R}\,\mathbf{T}. \tag{S2}$$

$\mathbf{R}$ holds the share of each cell's inflow that enters through each source term. $\mathbf{T}$ marks which source terms belong to which source group. A cell with no inflow is assigned $G = 0$.

Equation (2) expresses a cell's $F$ in terms of the $F$ of the cells downstream of it. Where water never returns to a cell it has left, the cells can be solved one at a time along the flow paths, as in FlowSource (Foley and Black 2013). A flow loop is a group of cells among which water circulates. Loops arise with the XT3D option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water in both directions. Foley and Black (2013) report loops as rare, mostly in unstable multilayer models. FlowSource deletes the smallest flow in each loop. Foley and Black (2013) expect this to change the results very little. We keep every flow and solve each loop exactly. The matrix is ordered so that the cells come in flow order, with each loop as one block. It is then factorised once by sparse LU decomposition. A model of a million cells with thousands of small loops is factorised in well under a second.

The matrix $\mathbf{I} - \mathbf{P}$ is singular only on a closed recirculation loop. No cell of such a loop has outflow to a sink or to a cell outside the loop, so its water never reaches a sink. These loops are assigned $F = 0$ and reported. The code also reports every other flow loop and the flow that goes round it. Under gross accounting, one factorisation serves every destination group and the travel times of Eq. (4).

## Why the water-budget checks are met to round-off

The checks of Section 2 follow from adding up the volume forms of Eqs. (2) and (3) over all cells. On the right of Eq. (2), each flow $q_{ij}$ appears once, multiplied by the $F$ of the cell it enters. The flows into cell $j$ add up to $I_j - \mathrm{Src}_j$. With $r_i = I_i - O_i$, the sum of Eq. (2) over all cells becomes the backward closure check

$$\sum_i F_i\, \mathrm{Src}_i - \sum_i F_i\, r_i = \sum_i d_i. \tag{S3}$$

It says that the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. Adding Eq. (3) over all cells yields the forward closure check in the same way:

$$\sum_i G_i\, \mathrm{Snk}_i + \sum_i G_i\, r_i = \sum_i s_i . \tag{S4}$$

The forward–backward check links the two systems. Multiply the volume form of Eq. (2) by $G_i$ and Eq. (3) by $F_i$, and add each over all cells. Both results then hold the same double sum of the cell-to-cell flows, $\sum_i \sum_j q_{ij}\, G_i\, F_j$. It cancels when one result is subtracted from the other. What remains is the forward–backward check

$$\sum_i F_i\, s_i - \sum_i G_i\, d_i = \sum_i F_i\, G_i\, r_i. \tag{S5}$$

So the volume from a source to a destination is the same whether it is traced backward or forward, once the cell budget errors are included.

The boundary-control check traces every sink term of the model, each as its own destination. The sum of their fractions solves the fraction form of Eq. (2) with $d_i$ replaced by the total sink outflow $\mathrm{Snk}_i$. A value of 1 in every cell solves that equation, because $\sum_j q_{ij} + \mathrm{Snk}_i = O_i$. The solution is unique outside closed recirculation loops. The fractions to all sinks therefore add up to 1 in every other cell with outflow.

The travel-time closure check follows in the same way from multiplying Eq. (4) by each cell's outflow and adding over all cells,

$$\sum_i \mathrm{Src}_i\, m_i - \sum_i r_i\, m_i = \sum_i V_i F_i . \tag{S6}$$

The right-hand side is the volume of water in the model that will end at the destination. The term $\mathrm{Src}_i F_i$ is the volume from cell $i$, and by Eq. (S3) these volumes add up to the destination's inflow once the cell budget errors are included. Eq. (S6) therefore says that this volume equals the destination's inflow times the flow-weighted mean travel time of all its water, apart from the cell budget error terms.

The closure, forward–backward and travel-time checks include the cell budget errors $r_i$. The boundary-control check needs no error term, because it follows from the definition of the outflow. All the checks are therefore met to round-off for any flow field, even one that does not balance, outside closed recirculation loops. The errors reported by the code are then round-off, unless the tracing itself is wrong. The code also reports the errors without the budget error terms.

## Net accounting

Net accounting reproduces the way FlowSource attributes water (Foley and Black 2013). It works from the cell-to-cell flows only. With $I^e_i$ and $O^e_i$ the cell-to-cell inflow and outflow of cell $i$, the water passing through the cell is $H_i = I^e_i + \max(O^e_i - I^e_i, 0)$. Outside the destination cells, the backward fraction is

$$f_i = \frac{1}{H_i} \sum_j q_{ij}\, f_j . \tag{S7}$$

The destination cells are fixed at $f = 1$. Their outflows to other cells are ignored. The source terms of the destination cells themselves, such as the recharge on a well's own cell, are also left out, because net accounting uses only the cell-to-cell flows. A forward trace works in the same way on the reversed flows.

Which cells are fixed depends on how the group was selected. A selection by cells or by zone fixes all its cells, as FlowSource does (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace these are the cells where the term is a sink. A well listed at zero rate is therefore not fixed in a backward trace. The same holds for a drain above the water table and a losing river cell.

Net accounting has no cell budget error term. It solves one destination group at a time, because each group fixes its own cells. As an option, it can delete the smallest flow in each flow loop, to compare with studies made with FlowSource.

## Travel time to where the water enters the sink cell

The mean travel time $t_i = m_i/F_i$ of Eq. (4) includes the time spent in the cell where the water leaves, for a well its own cell. Particle trackers that stop particles on entering a sink cell (MODFLOW 6 PRT, MODPATH) measure the time until the water enters that cell. The code also computes this time, as $(m_i - x_i)/F_i$, where $x$ solves $(\mathbf{I} - \mathbf{P})\,\mathbf{x} = \boldsymbol{\tau} \circ (\mathbf{S}\,\mathbf{D})$. Here $\circ$ is the cell-by-cell product. It is the full-mixing time that Section 3 compares with particles (Table 1, row 06).

## Matrix form of transient tracking and backward tracking in time

For all cells, step $n$ of Eq. (5) is one set of linear equations,

$$\mathbf{A}^n \mathbf{c}^n = \mathbf{B}^n \mathbf{c}^{n-1} + \Delta t^n\, \mathbf{s}^n . \tag{S8}$$

$\mathbf{B}^n$ holds the start volumes $V_i^{\mathrm{old}}$ on its diagonal. $\mathbf{A}^n$ holds the other terms of Eq. (5). Each step is solved in flow order as above. Because every cell holds water, no flow loop makes the matrix singular. One factorisation per step, or per sub-step when the volumes change, serves every tagged group. The tagged initial water starts with $c = 1$ in every cell and has no source. Because the storage terms change the volume by $V_i^{\mathrm{old}} - V_i^{\mathrm{new}} = \Delta t^n S_i$ under both volume options, a run that tags every source and the initial water yields $c = 1$ in every cell, with the flow-imbalance correction on.

Backward tracking in time solves the adjoint of Eq. (S8) (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). The adjoint holds the same flows with the roles of inflow and outflow swapped. The tagged water that the destination takes over the whole simulation is $J = \sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n$, where $\mathbf{d}^n$ holds the destination outflow of each cell in step $n$. The backward fraction in time $\mathbf{w}^n$ solves, from the last step $N$ back to the first,

$$\left(\mathbf{A}^n\right)^{\mathsf T} \mathbf{w}^n = \Delta t^n\, \mathbf{d}^n + \mathbf{B}^{n+1} \mathbf{w}^{n+1}, \qquad \mathbf{w}^{N+1} = \mathbf{0} . \tag{S9}$$

Row $i$ of Eq. (S9) is Eq. (6). One value of $w$ describes both the water in a cell at the start of a step and the water entering it during the step, because the implicit scheme mixes the two alike before any water leaves.

The transient forward–backward check follows from Eqs. (S8) and (S9) in the same way as Eq. (S5):

$$\sum_n \Delta t^n\, \mathbf{d}^n \cdot \mathbf{c}^n = \sum_n \Delta t^n\, \mathbf{s}^n \cdot \mathbf{w}^n + \sum_i V_i^{\mathrm{old},1}\, c_i^0\, w_i^1 . \tag{S10}$$

The check says that the tagged water the destination takes equals the tagged inflow and the tagged initial water, each multiplied by its share that later reaches the destination. It is met to round-off for either volume option and with or without sub-steps. In a backward run, the shares to the destination, to other sinks and still in storage at the end add up to 1, apart from a remainder that the code reports. The remainder is the water that the flow-imbalance correction removes and, with "gwt" volumes, the tagged water that appears or disappears at step boundaries. With "gwt" volumes it need not be small. Test model 10 checks the limit in which c tends to G and w to F under flows held constant.

**Water volume options.** The two options differ in how often porosity times saturated volume sets a cell's water volume. In the default, called "flow", it sets the volume only once, at the start of the run. After that, the volume changes only by the storage flows of the flow model, which follow the specific yield and specific storage. Every water balance then closes exactly, but the volume can drift away from porosity times saturated volume. In the "gwt" option, porosity times saturated volume sets the volume again at the end of every step, as in MODFLOW 6 GWT. The volume at the start of a step then differs from the volume at the end of the step before. Forward transient tracking with this option is equivalent to unit-concentration transport in GWT with upstream weighting, no dispersion, the flow-imbalance correction and one transport step per flow step (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, tagged water therefore appears or disappears at step boundaries. We recommend the default unless a result must match a GWT run.

**Transport sub-steps.** Long implicit time steps make tagged water arrive too early (Text S2). Sub-steps reduce this effect without a change to the flow model. Each flow step is split into a chosen number of equal transport sub-steps. The flows stay constant within the flow step. The water volumes change linearly between the start and end of the step.

# Text S2. The worked examples in brief

This text gives the details behind three points of Section 3. These are the weight-losing particles, the transport sub-steps and water volumes of example B, and the ensemble of Table 1 row 09. The other rows of Table 1 are reproduced by their notebooks (Section 6). The figures of this text follow it.

**Weight-losing particles.** Section 3 compares the contributing area of example A with MODFLOW 6 PRT on the same flows. Particles start from every source term in cells with F > 10⁻⁶. Each particle carries a share of its term's flow as a weight. It loses part of that weight at every other sink it passes, in proportion to the flow that sink takes from the cell. These particles are the particle counterpart of gross accounting. Similar weighting rules at sinks appear in the travel-time method of Visser et al. (2009) and the solute-transport method of Winston et al. (2018). Because the particles lose weight in this way, they deliver what the well pumps whatever the shape of the area (799.9 of 800 m³/d). The particle share of a cell is the share of the weight released there that reaches the well (main-text Fig. 3a). Cells with a particle share above 0.5 cover 1.168 km². The F > 0.5 area is 2.1 % smaller. The F > 0.1 area holds all of these cells.

**Water volumes and transport sub-steps in example B.** The two water volume options of Text S1 yield nearly the same result on the 30-year seasonal model. With one transport step per flow step, the year-30 share of initial water in the well's water is 0.5167 with "gwt" volumes and 0.5166 with the default "flow" volumes. The fractions differ by at most 3.7 × 10⁻³. Long transport steps make tagged water arrive too early. With one transport step per flow step, new recharge made up 0.0078 of the well's water in the first step. It made up 0.0049 with four sub-steps and 0.0042 with 16. The main runs therefore use four sub-steps.

**Ensembles.** Many sets of parameters can fit the measured heads about equally well. We refer to each set as a realisation and to a group of realisations as an ensemble. History matching with PEST++ IES, the iterative ensemble smoother of PEST++ (White 2018; White et al. 2020), adjusts the realisations until they fit the measurements. We refer to the ensemble before history matching as the prior and to the history-matched ensemble as the posterior. Table 1 row 09 uses 50 realisations of the hydraulic conductivity of the example model. The measured heads come from a synthetic true model, so the posterior can be compared with the truth. Figure S3 maps the probability of contribution before and after history matching. The posterior assigns a probability of at least 0.5 to 93 % of the true F > 0.5 area, against 79 % for the prior. A narrower posterior is not necessarily a correct one. One synthetic case cannot show how reliable posteriors are in general.

# Figure S1. Snapshots and transient tracking over 30 years

![](fig/fig9_transient_tracking.png){width=80%}

**Figure.** Snapshots and transient tracking on the 30-year seasonal example model (Section 3). Star: supply well. In (c–f), sky-blue cells mark the river. White contours mark fractions of 0.1 (dashed) and 0.5 (solid). (a) Snapshots: the well's water by source, each step traced on its own flows. (b) Forward transient tracking: the well's water by tagged source, including initial water. The dashed line is the initial water's share of all water pumped so far. Its labels show this share after 1, 10 and 30 years. (c) Steady-state F for the first step's flows. (d–f) Backward tracking in time: for the water in each cell at the start, the fractions that leave through the well (w) or the river within 30 years, and the fraction still stored.

# Figure S2. Time-limited contributing areas in the unit-concentration example

![](fig/figS24_unit_concentration_maps.png)

**Figure.** Backward tracking in time in the unit-concentration example of Bedekar et al. (2024), rebuilt in MODFLOW 6. Main-text Fig. 3b shows the well's water by origin in the same model. The maps show layer 2, where the well is screened. Star: well. (a–d) For the water in each cell at the start, colour shows the fraction that the well pumps within 1, 5, 10 and 25 years. (e) Steady-state backward fraction F for the flows of the last time step, for comparison.

# Figure S3. Probability of contribution before and after history matching

![](fig/fig10_ensembles.png)

**Figure.** Probability of contribution before and after history matching on the example model (Section 3). The probability of contribution of a cell is the share of realisations in which more than half of the cell's water ends at the well (F > 0.5). (a) Probability of contribution over 50 prior realisations of the hydraulic conductivity field. (b) The same over the 50 realisations after history matching to heads with PEST++ IES. Black lines: probabilities of 0.1, 0.5 and 0.9. Red dashed line: F = 0.5 in the synthetic true model, which supplied the measured heads. White circles: the 40 cells with head measurements. (c) Share of the pumped water that comes from the river, in each prior and posterior realisation. Each dot is one realisation. Boxes span the 25 to 75 % range and whiskers the 5 to 95 % range. Red dashed line: the river share of the true model.

# Text S3. The Neversink comparison

Section 4 compares full mixing with the published particle tracking of the Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022). Section 4 also defines the calibrated model, the start cells and the published contributing area. This text reports the cost of the trace and of the particle runs, the delineations behind the comparison and how the published particles end. The model is in a USGS data release (Fienen and Corson-Dosch 2021).

The 122,021 start cells are the uppermost active cell of each column in three regions around the wells. The expected area of a map of F is the sum of F over the start cells. It is a size of the contributing area that needs no threshold. All Neversink cells are 50 m squares, so expected areas are expressed as numbers of cells.

## Cost of the trace and of the particle runs

The trace was timed on an Apple M4 Max with 16 cores and 64 GB of memory. One trace of the nine destination groups took 2.4 to 2.7 s in all. Reading the budget file took 1.0 to 1.2 s of this. The trace itself took 1.4 to 1.5 s. Memory peaked at 2.52 GB, of which 0.52 GB was the loaded budget. A trace of the eight wells together, as one group, peaked at 0.98 GB. Each further group therefore adds about 0.19 GB on this model of 1.68 million cells. The closure check held to 1 × 10⁻¹² m³/d or better for every group. This was so with the stream reaches left as source and sink terms and with them traced as the stream network.

The PRT runs of Section 4 differ in what they release and what they write. The runs that reproduce the published area release one unweighted particle at each published start and write only where each particle ends. Each took about 30 s. The flow-weighted runs release particles from every source term of the 30,180 cells with F > 10⁻⁶, in all layers, and write full tracks. With four release points in plan at one height, 122,112 particles took about 5 min and wrote a track file of about 1.5 GB. With the same points at four heights, 488,448 particles took about 13 min and wrote about 6 GB. The peak memory of PRT was not measured.

## Delineations on one flow field

The table compares the delineations of the eight wells' contributing area on the calibrated model, with the stream reaches left as source and sink terms of the aquifer cells. Each is compared with the published contributing area of 980 cells. The table lists the size of each delineation and the share of the published area it covers. Both are needed, because a larger area covers more of the published area.

| method | delineation | area (cells) | published area covered (%) | expected area (cells) | flow attributed to the wells (m³/d) |
|------------------------|------------------------------------|---------|---------|-------------|------------------|
| Full mixing, gross accounting | F > 0.1 | 2,139 | 73 | 910 | 3,671 |
| | F > 0.5 | 445 | 43 | 910 | 3,671 |
| | area-matched (980 cells) | 980 | 58 | 910 | 3,671 |
| Full mixing, net accounting | F > 0.1 | 2,470 | 76 | 978 | 3,944 |
| | F > 0.5 | 478 | 46 | 978 | 3,944 |
| | area-matched (980 cells) | 980 | 57 | 978 | 3,944 |
| PRT, flow-weighted, weight-losing | released over the cell volume, P > 0.5 | 691 | 65 | 794 | 3,736 |
| | released mid-cell, P > 0.5 | 707 | 66 | 781 | 3,722 |
| | released at the water table, P > 0.5 | 502 | 42 | 592 | 2,413 |
| PRT, flow-weighted, losing weight only at wells | released over the cell volume, P > 0.5 | 2,633 | 83 | 2,857 | – |
| PRT, published starts | MODFLOW 6 default, dry starts dropped to the water table | 730 | 67 | 730 | – |
| | MODFLOW 6 default, dry starts draped | 754 | 69 | 754 | – |
| | top face where open, dry starts dropped | 969 | 98 | 969 | – |
| | top face where open, dry starts draped (published settings) | 982 | 100 | 982 | – |

Thresholds are strict. The area-matched delineation takes the 980 start cells with the largest F. For flow-weighted PRT, the expected area is the particle weight that reaches the wells, in cells. For published starts, it is the number of start cells whose particle ends in a priority well. The flow-weighted particles were released from the source terms of the 30,180 cells with F > 10⁻⁶, in all layers. P is the share of the water released in a start cell that the particles deliver to the wells. The published-start runs use one unweighted particle per published start, stopped at every weak sink. "MODFLOW 6 default" spreads recharge and stream flows through the cell. "Top face where open" puts them on the top face through IFLOWFACE, the MODFLOW 6 setting that assigns a boundary flow to one cell face.

The wells take 3,671 m³/d. Gross accounting attributes exactly this flow to them. Net accounting attributes 3,944 m³/d, because it also counts the water that passes on from the well cells. Weight-losing particles deliver within 2 % of the wells' inflow.

The 87 % of Section 4 is 602 of the 691 start cells where weight-losing particles released over the cell volume deliver more than half their water to the wells. It is an upper bound, because the particles were released only from cells with F > 10⁻⁶. A cell left out that would have delivered more than half its water would be one more missed cell. The weight-losing particles also lose weight at each sink by the full-mixing shares. For this reason they are not an independent particle area. The comparison measures only the spreading that full mixing adds between sinks.

With the stream reaches left as source and sink terms, full mixing traces 2,100 m³/d of the wells' water to recharge and 1,571 m³/d to stream leakage. Along the paths of the weight-losing particles, the wells receive 344 m³/d more stream water and 279 m³/d less recharge. Most of the extra stream water leaks from reaches 0.4 to 1.3 km south of the U wells and 0.5 to 1.2 km from SV_487. In a cell that receives both sources, the two reach the wells in the same proportion under either method. The difference therefore comes from where each source enters the aquifer.

## End states of the published particles

Each published MODPATH 7 particle on the calibrated model ends in one of three ways. We classed each end cell on the MODFLOW 6 budget. A strong sink sends all of its outflow to boundary sinks. A weak sink sends only part of it.

| end state (MODPATH status) | particles | end cells | particles ending in a priority well |
|----------------------------|-----------|---------------------------------------------|----------------|
| leaves the model through a cell face (2) | 89,920 | top face of a stream cell with no active cell above: 88,781; side face next to a dry cell: 1,139 | 0 |
| stopped on entering a weak-sink cell (3) | 27,631 | buried stream cells: 26,828; wells: 612; constant heads: 191 | 466 |
| ends in a cell with no exit face (5) | 4,470 | wells: 2,570; buried stream cells: 1,472; constant heads: 428 | 514 |

Each published particle starts in its own cell, so the 980 cells of the published contributing area are the start cells of 980 particles that end in a priority well. Of these particles, 514 end in the three priority wells that take all of their cell's outflow. The other 466 stop in the five priority wells that take only part of it.

A buried stream cell is a cell with an SFR reach and another active cell above it. The published runs put recharge and stream flows on the top face of the cell. MODPATH 7 does this only where the top face has no active neighbour. Elsewhere the flow stays spread through the cell. A particle that reaches a stream cell with no active cell above therefore leaves through the top face (status 2). A particle that reaches a buried stream cell is stopped there as at a weak sink (status 3). Every particle that stops in a stream cell has an active cell above it. None of those that leave through a stream cell's top face has.

At the weak-sink wells, the published particles and full mixing treat the cell's water differently. The well of U\_\_\_7 takes 44 % of its cell's outflow. All the water of a published particle that enters the cell still counts as reaching U\_\_\_7. Under full mixing, the other 56 % of the cell's outflow passes on, most of it to U\_\_\_8 and U\_917. So 97 % of the water in the cell reaches a priority well (F = 0.97).

## The ensemble

Section 4 reports the cost of the two traces of each realisation. One trace left the stream reaches as source and sink terms. The other traced them as the stream network. The whole ensemble, with its MODFLOW 6 runs, took 76 min in six parallel processes. The published study maps a probability of contribution. It is the share of 357 published Monte Carlo contributing areas that contain a cell. Mean F over the realisations, with the stream reaches left as source and sink terms, is the full-mixing counterpart (Figure S4b). It correlates with the published probability at r = 0.80. Its expected area is 0.90 times the published one. The stored published areas lie one row south of their cells, so we moved them one row north before this comparison. The archived code release (Section 6) explains this offset in docs/neversink_study.md.

# Figure S4. Neversink particle area and ensemble mean F

![](fig/figS22_neversink_cd.png)

**Figure.** The eight priority wells of the Neversink/Rondout model, in the 7.1 × 9.25 km window of main-text Fig. 4. All maps show the uppermost active cell, with the stream reaches left as source and sink terms and gross accounting. (a) The F > 0.1 area against the area where weight-losing PRT particles, released over the cell volume, deliver more than half their water to the wells (P > 0.5). Dark blue: in both (495 cells in this window). Orange: particles only (86). Light blue: F > 0.1 only (1,133). (b) Mean F over 358 realisations, with the published probability of contribution 0.5 outlined. Grey: below 0.01. (c) The model, the three regions of the published particle runs (dashed) and the window. Orange dots: wells. Blue lines: SFR reaches. Scale bar (a): 2 km.

# Text S4. Numerical dispersion test problems

Full mixing spreads the edge of a contributing area over a band of cells, because each cell mixes the water it receives. This spreading comes from the grid, not from the aquifer. We refer to it as numerical dispersion. Notebook 11 of the release (Table 1) measures it on two test problems. The first is a well in uniform regional flow, compared with the analytical capture zone of Javandel and Tsang (1986). The second is a test model with a river, compared with PRT on a fine grid. The notebook shows how the band changes with cell size and grid orientation. Figure S5 shows the band on cells of 50 m.

# Figure S5. Numerical dispersion maps and cell size

![](fig/figS23_numerical_dispersion.png)

**Figure.** Numerical dispersion of full mixing. F is the share of a cell's water that reaches the well (dot). (a–d) Problem A on 50 m cells, with uniform flow at 30° to the grid rows. The first map is the exact capture zone averaged over each cell, the best a cell-based method can do. Dashed: the analytical capture-zone edge. (e–h) Problem B: PRT on the 12.5 m grid and the three methods on 50 m cells. Dashed: the PRT F = 0.5 edge. Grey line: the gaining river. DIS: square cells. DISV: Voronoi cells. (i–n) The width of the band where 0.1 < F < 0.9, and the relative error in the size of the F > 0.1 and F > 0.5 areas, against the mean cell size h. Top row: problem A, with flow along the grid rows (solid) or at 30° to them (dotted). Bottom row: problem B. Dashed guide: $h^{0.5}$. Grey band: ±5 %.

# References cited only in the Supporting Information

Black, A., and C. Foley. 2013. FlowSource: A program to efficiently delineate volumetric capture areas, pathways and source areas in groundwater models. In *Proceedings of MODFLOW and More 2013: Translating Science into Practice*, Golden, Colorado, June 2–5, 2013, 652–663. Golden, Colorado: IGWMC, Colorado School of Mines. https://groundwater-science.co.uk/wp-content/uploads/2013_FSv6_ApplicationPaper.pdf

Campana, M.E., and E.S. Simpson. 1984. Groundwater residence times and recharge rates using a discrete-state compartment model and C-14 data. *Journal of Hydrology* 72, no. 1–2: 171–185. https://doi.org/10.1016/0022-1694(84)90190-2

Chowdhury, M.A. 2016. Assessing the connectivity of groundwater wells to surface-water using a volumetric capture delineation tool. MASc thesis, University of Waterloo, Waterloo, Ontario, Canada. http://hdl.handle.net/10012/10981

Cornaton, F., and P. Perrochet. 2006. Groundwater age, life expectancy and transit time distributions in advective–dispersive systems: 1. Generalized reservoir theory. *Advances in Water Resources* 29, no. 9: 1267–1291. https://doi.org/10.1016/j.advwatres.2005.10.009

Corson-Dosch, N.T., M.N. Fienen, J.S. Finkelstein, A.T. Leaf, J.T. White, J. Woda, and J.H. Williams. 2022. Areas contributing recharge to priority wells in valley-fill aquifers in the Neversink River and Rondout Creek drainage basins, New York. U.S. Geological Survey Scientific Investigations Report 2021–5112. Reston, Virginia: USGS. https://doi.org/10.3133/sir20215112

Hughes, J.D., C.D. Langevin, S.R. Paulinski, J.D. Larsen, and D. Brakenhoff. 2024. FloPy workflows for creating structured and unstructured MODFLOW models. *Groundwater* 62, no. 1: 124–139. https://doi.org/10.1111/gwat.13327

Hugman, R., and O. Sanchez. 2026. vorflow: Voronoi mesh generation for MODFLOW 6. Version 0.2.0. Software, released 5 October 2026. https://github.com/rhugman/vorflow

Langevin, C.D., J.D. Hughes, E.R. Banta, R.G. Niswonger, S. Panday, and A.M. Provost. 2017. Documentation for the MODFLOW 6 Groundwater Flow Model. U.S. Geological Survey Techniques and Methods, book 6, chap. A55. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A55

McLane, C., and L. Cecan. 2009. Comment on "MODALL: A practical tool for designing and optimizing capture systems," by S.T. Potter, E. Moreno-Barbero, and C.E. Divine. *Ground Water* 47, no. 2: 172–173. https://doi.org/10.1111/j.1745-6584.2008.00527_1.x

Nogueira, G.E.H., C. Schmidt, D. Partington, P. Brunner, and J.H. Fleckenstein. 2022. Spatiotemporal variations in water sources and mixing spots in a riparian zone. *Hydrology and Earth System Sciences* 26, no. 7: 1883–1905. https://doi.org/10.5194/hess-26-1883-2022

Partington, D., P. Brunner, C.T. Simmons, A.D. Werner, R. Therrien, H.R. Maier, and G.C. Dandy. 2012. Evaluation of outputs from automated baseflow separation methods against simulated baseflow from a physically based, surface water–groundwater flow model. *Journal of Hydrology* 458–459: 28–39. https://doi.org/10.1016/j.jhydrol.2012.06.029

Partington, D., P. Brunner, S. Frei, C.T. Simmons, A.D. Werner, R. Therrien, H.R. Maier, G.C. Dandy, and J.H. Fleckenstein. 2013. Interpreting streamflow generation mechanisms from integrated surface-subsurface flow models of a riparian wetland and catchment. *Water Resources Research* 49, no. 9: 5501–5519. https://doi.org/10.1002/wrcr.20405

Provost, A.M., C.D. Langevin, and J.D. Hughes. 2017. Documentation for the "XT3D" option in the Node Property Flow (NPF) Package of MODFLOW 6. U.S. Geological Survey Techniques and Methods, book 6, chap. A56. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A56

Schilling, O.S., C. Gerber, D.J. Partington, R. Purtschert, M.S. Brennwald, R. Kipfer, D. Hunkeler, and P. Brunner. 2017. Advancing physically-based flow simulations of alluvial systems through atmospheric noble gases and the novel ³⁷Ar tracer method. *Water Resources Research* 53, no. 12: 10465–10490. https://doi.org/10.1002/2017WR020754
Visser, A., R. Heerdink, H.P. Broers, and M.F.P. Bierkens. 2009. Travel time distributions derived from particle tracking in models containing weak sinks. *Ground Water* 47, no. 2: 237–245. https://doi.org/10.1111/j.1745-6584.2008.00542.x

White, J.T. 2018. A model-independent iterative ensemble smoother for efficient history-matching and uncertainty quantification in very high dimensions. *Environmental Modelling & Software* 109: 191–201. https://doi.org/10.1016/j.envsoft.2018.06.009

White, J.T., R.J. Hunt, M.N. Fienen, and J.E. Doherty. 2020. Approaches to highly parameterized inversion: PEST++ Version 5, a software suite for parameter estimation, uncertainty analysis, management optimization and sensitivity analysis. U.S. Geological Survey Techniques and Methods 7C26. Reston, Virginia: USGS. https://doi.org/10.3133/tm7C26

Winston, R.B., L.F. Konikow, and G.Z. Hornberger. 2018. Volume-weighted particle-tracking method for solute-transport modeling; Implementation in MODFLOW–GWT. U.S. Geological Survey Techniques and Methods, book 6, chap. A58. Reston, Virginia: USGS. https://doi.org/10.3133/tm6A58
