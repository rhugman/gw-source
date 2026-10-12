## Table 1

**Table 1.** Four ways to compute, from a groundwater flow model's flows, the share of each cell's water that reaches a destination or came from a source: FlowSource (Foley and Black 2013; Black and Foley 2013), this formulation, unit-concentration transport in GWT (Bedekar et al. 2024 [check: abstract only]; Langevin et al. 2022) and hydraulic mixing cells as published by Partington et al. (2011). The fractions F, G, c and w and gross and net accounting are defined in Section 2. The FlowSource column describes the program as published in 2013, and years in parentheses date a statement to those papers; we found no published description of later versions. MODALL (Potter et al. 2008) has no column because its solution method could not be established. Fuller notes and the source of each cell are in {SI: Table 1 notes and sources}.

| | FlowSource (Foley and Black 2013; Black and Foley 2013) | This formulation | GWT unit concentration (Bedekar et al. 2024; Langevin et al. 2022) | Hydraulic mixing cells (Partington et al. 2011) |
|---|---|---|---|---|
| What is solved, and how | Fractions cell by cell in flow order; one pass per time step | Linear equations in flow order; transient tracking: implicit steps | Implicit time steps, iterative solver; no documented steady-state option¹ | Explicit, on the flow model's steps; stable only for short steps² |
| Mixing in a cell | Full mixing | Full mixing | Full mixing with upstream weighting and no dispersion | Modified mixing cell; tends to full mixing as steps shorten³ |
| Accounting at weak sinks | Net: destination cell credited with all water passing through | Gross (default); net as an option | Gross: sinks remove water at the cell's concentration | Outflow at the previous step's mix; gross in effect (our reading) |
| Flow loops | Smallest-flow connection in each loop deleted (2013) | Solved exactly; closed recirculation loops set to F = 0⁴ | None needed: one implicit solution over all cells (our inference) | Not discussed; fixed stream flow direction assumed |
| Outputs | F, volumes through and from; particle travel time | F, G and volumes by term; transient tracking: c and w | Concentration, read as the share of water from the tagged source | Fractions by flow component per stream cell, plus initial water |
| Transient models: water carried through storage? | No: each step traced as a steady state (snapshots) | Yes, transient tracking (needs porosity); snapshots also | Yes (needs porosity) | Yes: stream-cell water volumes carried step to step |
| Backward in time? | No | Yes, solved from the end of the simulation | No⁵ [check: Bedekar et al. 2024 full text] | No |
| Destinations or sources per run | One destination group (any number of cells) per calculation | Gross: all groups in one run; net: one group per run | One tagged source per GWT model; several models per simulation | All flow components together; not user-chosen terms |
| Built-in water-budget checks | None described; flow loops reported (2013) | Closure, forward–backward, travel-time closure; more in transient tracking | Mass budget, a tagged-water balance; no source-to-destination check | Sum-of-fractions error; global volume error, gaining reaches only |
| Grids and packages | Structured MODFLOW grids; method said to apply to unstructured grids (2013); package networks not documented | All MODFLOW 6 grid types, multi-model simulations, package networks | DIS, DISV, DISU; SFR, LAK, MAW, UZF and MVR transport | HydroGeoSphere stream cells; said to apply to other codes |
| Open implementation | No: commercial; VB.NET source for academic use on request (2013) | Yes (`gwsource`, MIT) | Yes (MODFLOW 6, USGS) | Excel (Visual Basic) post-processor; availability not stated |

¹ Steady state is reached by running transient steps until concentrations stabilise (Langevin et al. 2022). In our test, one step with porosity 0 gave the steady G to 1 × 10⁻¹², an undocumented use. <!-- table1_methods.md footnote 2 and Sources, GWT 'Solved, how': 9.5 × 10⁻¹³ and 9.7 × 10⁻¹³ on test model 1 -->

² Each step's fractions come from the previous step's; the update is stable only while a step's inflow or outflow volume does not exceed the cell's storage. Later versions add overland and aquifer cells and sub-steps; all step forward in time only.

³ After Campana and Simpson (1984): water leaving a cell over a step carries the previous step's mix.

⁴ A group of cells with no outflow to any sink or to a cell outside the group; reported, with no connections deleted.

⁵ No backward option is documented (Langevin et al. 2022); of Bedekar et al. (2024) we read only the abstract, which lists well capture analysis among the uses without saying how it is done.
