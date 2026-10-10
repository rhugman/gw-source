# Table 1. Methods compared

*Table 1. Four ways to compute, from a groundwater flow model's flows, the share of the water in each cell that reaches a destination or came from a source: the reference method [FB13, BF13; BFW21 and DAL22 for its 2020 version], this formulation, unit-concentration transport in MODFLOW 6 GWT [BED24, LAN22] and hydraulic mixing cells [PAR11]. F is the backward fraction (the share of the water leaving a cell that leaves the model through the destination) and G the forward fraction (the share of the water entering a cell that came from the source); in transient tracking, c is the tagged fraction and w the backward fraction in time. Gross accounting: each sink term in a cell takes its share of the cell's total outflow. Net accounting: a destination cell is credited with all the water passing through it. Cells marked [check] rest on less than the full text of the source; the footnotes say what they rest on. MODALL [POT08] has no column because its solution method could not be established (footnote 7).*

| | The reference method [FB13, BF13] | This formulation | GWT unit concentration [BED24, LAN22] | Hydraulic mixing cells [PAR11] |
|---|---|---|---|---|
| What is solved, and how | Fractions cell by cell, in flow order after sorting the cells; one pass per time step | One sparse linear system per direction, solved cell by cell in flow order, loop by loop where flows form loops; tracking: one implicit step at a time | Transport equation in implicit time steps, iterative solver; no single-step steady state | Explicit update from the previous step's fractions, with sub-steps for stability [check]¹ |
| Mixing in a cell | Full mixing | Full mixing | Full mixing with upstream weighting and no dispersion² | Mixed at each step; within a step, between full mixing and piston flow [check]¹ |
| Accounting at weak sinks | Net: destination cell credited with all its throughflow³ | Gross (default); net as an option | Gross: sinks remove water at the cell's concentration | Gross: outflow leaves with the cell's mix [check]¹ |
| Flow loops | Smallest-flow connection in each loop deleted | Solved exactly; closed recirculation loops given F = 0 and reported | No treatment needed⁴ | No treatment needed⁴ [check]¹ |
| Outputs | F, volume through, volume from (by budget term), fraction from; forward fraction (C/C0); particle travel time; statistics over steps | F, G and volumes by source and sink term; boundary-control maps; mean travel time; statistics over steps; tracking: c, w, fractions to other sinks and still stored | Concentration, read as the share of water from the tagged source | Share of each tagged source in each cell, e.g. groundwater in streamflow [check]¹ |
| Transient models: water carried through storage? | No: each step traced as a steady state (snapshots) | Yes, transient tracking (needs porosity); snapshots also | Yes (needs porosity) | Yes: cell water volumes carried from step to step [check]¹ |
| Backward in time? | No | Yes, solved from the end of the simulation | No⁵ [check] | None described [check]¹ |
| Destinations or sources per solve | One destination group (any number of cells) per run | Gross: all groups at once, one factorisation (per step when tracking); net: one group per solve | One tagged source per GWT model; several models per simulation | All tagged sources in one run [check]¹ |
| Built-in water-budget checks | None published; flow loops reported⁶ | Closure, forward–backward and boundary-control checks; tracking: forward–backward in time, water and tagged-water balance | None described for tracing | None reported; fractions sum to 1 if the water balance is exact [check]¹ |
| Grids and packages | MODFLOW-96 grids (2013); MF6 and MODFLOW-USG unstructured meshes (2020 version); package networks not documented | DIS, DISV, DISU; GWF-GWF exchanges; SFR reaches, lakes, MAW wells and UZF cells as extra cells, linked by MVR | DIS, DISV, DISU; SFR, LAK, MAW, UZF and MVR transport | HydroGeoSphere, surface and subsurface flow [check]¹ |
| Open implementation | No: commercial licence; on request in 2013 | Yes (`gwsource`, MIT) | Yes (MODFLOW 6, USGS) | None found [check]¹ |

¹ Rests on the abstract of [PAR11] and on the description of the method in Nogueira et al. (2022, Sect. 2.2, Eq. 1), an open-access application whose authors include Partington and Brunner. The full text of [PAR11] was not read.

² GWT also offers central-in-space and TVD advection, dispersion and reactions [LAN22]. With upstream weighting and no dispersion its steady limit equals G (Table 2).

³ [FB13] define all water starting in or passing through a destination cell as reaching the destination, so a weak-sink well is credited with all the water passing through its cell.

⁴ Our inference, not stated by the sources: an implicit solve over all cells, or an explicit update from the previous step, needs no flow order.

⁵ [LAN22] documents no backward-in-time option. The abstract of [BED24] lists well capture analysis among the uses without saying how it is done; its full text was not read.

⁶ The 2020 version lists "error checking" among minor changes, without detail [DAL22].

⁷ MODALL [POT08] computes, from MODFLOW cell-by-cell flows, the share of flow in each cell that came from a source or goes to a sink (abstract), for steady-state models, assuming full mixing and without the reference method's flow-order sort [CHO16 §2.3.3, p. 103; FB13]. How it solves, how it treats weak sinks and what it does with flow loops could not be established.

---

## Sources

What each cell rests on, by column. Page numbers are given where the source has them; the 2013 conference papers [FB13, BF13] are cited by section heading because their text has no page numbers.

### Read in full, and read as abstract or secondary account only

- **Read in full:** [FB13] and [BF13] (local text); [BFW21] (11 slides) and [DAL22] (poster); in [LAN22] the abstract, chapter 1 (pp. 1–1 to 1–8), the formulation and flow-imbalance correction of chapter 2 (pp. 2–1, 2–6 to 2–7), mobile storage (p. 3–1), advection weighting (pp. 4–1 to 4–2), the SSM Package (pp. 5–1 to 5–3) and the introduction to chapter 6 (p. 6–1); [CHO16] §2.3.3, §2.4 and p. 103 (local text); the vendor shop notes [GWS-web] (`references/web/`, as listed on 2026-10-01); Nogueira, G.E.H., Schmidt, C., Partington, D., Brunner, P. & Fleckenstein, J.H. (2022), "Spatiotemporal variations in water sources and mixing spots in a riparian zone", *Hydrology and Earth System Sciences* 26, 1883–1905, doi 10.5194/hess-26-1883-2022, read as HTML at https://hess.copernicus.org/articles/26/1883/2022/ (Sect. 2.2 and 4.5; not yet in `references/bibliography.md`).
- **Abstract only:** [PAR11], from the Neuchâtel repository record (https://libra.unine.ch/handle/20.500.14713/59828) and the Flinders University record (https://researchnow.flinders.edu.au/en/publications/a-hydraulic-mixing-cell-method-to-quantify-the-groundwater-compon/). The publisher page was not tried; an author copy is in the Neuchâtel repository as a PDF and was not read, because only web pages were to be read. [BED24], from the Semantic Scholar record (https://api.semanticscholar.org/graph/v1/paper/DOI:10.1111/gwat.13333) and the Clear Creek Associates news page (https://clearcreekassociates.com/bartlett-plato-groundwater/); the Wiley page returned 403. [POT08], from the Europe PMC record of PMID 18194317; the Wiley, Academia.edu, ResearchGate and Semantic Scholar pages returned 403 or no abstract. [MC09] was not read.
- **Secondary accounts:** of [PAR11], Nogueira et al. (2022) and the Aquanty research highlight (https://www.aquanty.com/blog/hgs-research-highlight-sources-surface-water-hydraulic-mixing-cell-modeling), which describes the method as applied to HydroGeoSphere output. Of [POT08], [CHO16], [FB13] and [BF13].

### The reference method

- **Solved, how:** [FB13] Method and Evaluation: cells sorted in flow order, then one arithmetic pass; earlier versions used recursive scans. Each time step processed on its own [FB13] Introduction.
- **Mixing:** [FB13] Description of Calculation (divergent cells split their water in proportion to outflow); stated as full mixing in [CHO16] §2.4.3.
- **Accounting:** [FB13] Description of Calculation: all water starting in or passing through a destination cell reaches the destination (cell A, 100 %); volume from uses each cell's excess of outflow over inflow. The outflows of destination cells are detached so that nothing downstream is counted [FB13] Method.
- **Flow loops:** [FB13] Method (the lowest-volume connection is removed; which one to remove is called an open research question) and Evaluation; [BF13] Introduction to Graphs.
- **Outputs:** [FB13] Introduction and Figs 1–4, 6–8 (volume and fraction through, volume and fraction from; volume from by recharge, storage and boundary term if other budget records are read); [BF13] Introduction (min, max, mean, ASN, probability within range; travel time from forward particles based on MODPATH 6); [BFW21] slide 10 and [DAL22] (forward mode as "an Eulerian transport tool", fraction = C/C0, volume to the receptor); [BFW21] slide 5 (fraction from summing to 100 %).
- **Transient:** [FB13] Introduction and [BF13] Introduction and Problem Description: each time step a "time-instant steady state" (Rushton 2003); particles for travel time tracked through each step's steady flows [BF13] Introduction.
- **Backward in time:** none in [FB13], [BF13], [BFW21] or [DAL22]; it follows from the snapshot treatment.
- **Per solve:** [FB13] Evaluation and [BF13] river-catchment and boundary-control examples: up to about 150,000 destination cells processed as one group; the four boundary-control maps (Figs 18–21) were "processed individually" and sum to 1 in every cell.
- **Checks:** [FB13] Method (flow loops reported to the user as a sign of a model flaw); [DAL22] ("error checking" among minor changes). No closure or other budget check is described.
- **Grids and packages:** [FB13] Introduction (MODFLOW-96 CBC files; method said to apply to MODFLOW-USG and finite elements); [BFW21] slides 6 and 11 and [DAL22] (MF6 and MODFLOW-USG; triangular, quadtree and Voronoi meshes). MF6 exchanges, MVR and package networks are not mentioned in any source (`references/SUMMARY.md` §2.9, §8).
- **Open implementation:** [FB13] and [BF13] end matter (available on request; VB.NET source for academic use on request); [GWS-web] (node-locked, dongle and shared licences sold).

### This formulation

`docs/paper/outline.md` §5.2–5.3 and key messages 1–5; `PLAN.md` §2; `src/gwsource/solve.py` (flow-order and loop-by-loop solvers, closed recirculation loops), `trace.py` (net accounting solved group by group), `tracking.py` (transient tracking, backward tracking in time, one factorisation per step for all tags), `diagnostics.py` (checks), `traveltime.py` (mean travel time, gross accounting only), `network.py` and `mf6io.py` (grids, exchanges, package networks); Table 2. Licence: `LICENSE` (MIT).

### GWT unit concentration

- **Solved, how:** [LAN22] abstract and p. 2–1 (the cell balances form a system of linear equations, solved implicitly with iterative methods); p. 1–7, items 4 and 10 (central, upstream or TVD advection; no single-step steady state).
- **Mixing:** [LAN22] pp. 4–1 to 4–2 (upstream weighting); dispersion is an option (chapter 4). The match to G is this paper's own check (Table 2: ≤ 2.8 × 10⁻¹¹ at equilibrium on models 1 and 2).
- **Accounting:** [LAN22] p. 5–3, eq. 5–7: by default water leaving a cell through a stress package leaves at the cell's concentration. Flow-imbalance correction, p. 2–6, eq. 2–14.
- **Flow loops:** not discussed in [LAN22]; footnote 4.
- **Outputs:** [BED24] abstract (concentration one for the source water assessed, zero for all other water; the concentration gives each source's contribution to sinks; uses: source allocation, well capture analysis, mixing and dilution). Agreement with forward tracking: Table 2.
- **Transient:** [LAN22] p. 3–1, eqs 3–2 and 3–3 (storage of dissolved mass in the cell's water volume, with porosity and saturation, implicit in time) and abstract (no steady-state option).
- **Backward in time:** no reverse or adjoint option in the parts of [LAN22] read; [BED24] abstract silent on how well capture analysis is done [check].
- **Per solve:** [LAN22] p. 1–6, item 1 (one species per GWT model; several GWT models per simulation).
- **Checks:** no check of traced volumes against the water budget, such as a source-to-destination identity, is described in the parts of [LAN22] read.
- **Grids and packages:** [LAN22] pp. 1–6 to 1–7, items 3 and 11 (DIS, DISV, DISU; SFT, LKT, MWT, UZT and MVT, advection only between package features and with the aquifer).
- **Open implementation:** MODFLOW 6 is distributed by the USGS ([LAN22] front matter, MODFLOW web page).

### Hydraulic mixing cells

All cells rest on the [PAR11] abstract and on Nogueira et al. (2022) unless stated otherwise.

- **Solved, how:** Nogueira et al. (2022) Sect. 2.2, Eq. 1: the fraction in a cell at the end of a step is computed from the cell's volume and fraction at the previous step, boundary inflows and inflows from neighbours at their previous-step fractions; an independent sub-time-step routine between the flow model's adaptive steps avoids instability when the water leaving a cell in a step exceeds its stored volume (citing Partington et al. 2013). No system of equations is mentioned.
- **Mixing:** Nogueira et al. (2022) Sect. 2.2 (a "modified mixing rule" between perfect mixing and piston flow, citing [PAR11]) and Sect. 4.5 (fractions perfectly mixed within a cell at every time step).
- **Accounting:** Nogueira et al. (2022) Eq. 1: outflow to boundary conditions is multiplied by the cell's previous-step fraction.
- **Flow loops:** not discussed; footnote 4.
- **Outputs:** [PAR11] abstract (groundwater component of streamflow at any point along a stream, from the flow solution only, without a tracer simulation); Nogueira et al. (2022) Sect. 2.2 (fractions of stream water, groundwater and floodplain water in every cell, plus an initial-water fraction).
- **Transient:** Nogueira et al. (2022) Eq. 1 (cell volumes at the previous and current step).
- **Backward in time:** not described in the [PAR11] abstract, Nogueira et al. (2022) or the Aquanty highlight. Whether [PAR11] itself has one is still open.
- **Per solve:** Nogueira et al. (2022) Sect. 2.2 (several sources tracked together).
- **Checks:** Nogueira et al. (2022) Sect. 2.2 (fractions sum to one for an error-free water balance); no HMC check is reported.
- **Grids and packages:** [PAR11] repository record (subject HydroGeoSphere; fully integrated surface water–groundwater models); Nogueira et al. (2022) Sect. 2.2 (applicable to any model with an explicit water balance per cell, as claimed there).
- **Open implementation:** no public code was found in the pages read.

### MODALL (no column)

[POT08] abstract (Europe PMC): MODALL uses the MODFLOW cell-by-cell flow terms to evaluate the flow balance between cells and gives the share of flow in each cell from a source or to a sink; compared with an analytical solution, MODPATH and MT3DMS. [CHO16] §2.3.3 (pp. 23–24) and §2.4: steady-state MODFLOW only; outputs equal the reference method's fraction through. [CHO16] p. 103: full mixing, numerical dispersion on coarse grids [MC09], a simpler calculation than the reference method, without its flow-order sort. [FB13] Introduction: MODALL does not use the reference method's flow-order sort and was used to validate its fraction through. [BF13] Problem Description: on a model with flow loops MODALL did not delineate the capture areas (personal communication cited there). None of these says whether MODALL solves a linear system, iterates or sweeps, or how it treats weak sinks.
