# Paper outline: full-mixing flow-source fractions for MODFLOW 6

Draft outline, 2026-10-05. For co-author review. All numbers are from `docs/neversink_study.md` (cited as NS §n / Table n), `docs/dispersion_study.md` (DS §n / Table n), `PLAN.md` (status notes per phase) and the tests. Untracked outputs are in `studies/neversink/output/` and `studies/dispersion/output/` of the main checkout. Items marked [check] need verifying before submission. Terms follow `docs/paper/terms.md`.

## 1. Title and contribution

Working titles:

1. *Full-mixing contributing areas and source fractions from MODFLOW 6 budgets: an open implementation and a comparison with particle-tracked contributing areas* (recommended)
2. *Contributing areas by full mixing and by particle tracking on a regional MODFLOW 6 model: what the differences are made of*
3. *Cell-mixing flow tracing for MODFLOW 6, with water-budget checks, stream networks and ensembles*

**Contribution.** The reference method [FB13, BF13] computes, from cell-by-cell flows, the fraction of the water in every cell that reaches a destination (backward) or came from a source (forward), assuming each cell is fully mixed. It is used for source protection zones in England [EA19] but is described only in conference papers, and no open implementation exists. We write the method as one sparse linear system per direction, solved exactly whether or not the cell-to-cell flows form loops. Gross accounting, in which each sink term takes its share of its cell's outflow, credits a weak-sink well with its pumping only. Two exact identities check every result against the water budget: the traced volumes add up to the inflow of each destination and of each source (closure), and backward and forward tracing give the same volume between each source and destination. The implementation reads MODFLOW 6 budgets on structured and unstructured grids, multi-model simulations and stream, lake and well networks. On the USGS Neversink/Rondout model (1.68 million cells) we compare it with the published MODPATH 7 contributing areas for eight supply wells, for the calibrated model, a 358-realisation ensemble and five pumping scenarios. MODFLOW 6 particle tracking (PRT) on the same flow field reproduces the published contributing cells once the published particle conventions are copied (overlap 0.998), and full mixing lies within the range of particle results under other conventions. We attribute the remaining differences to mixing versus advective paths and to how streams are treated; some of these mechanisms are inferred rather than traced cell by cell.

## 2. Target journals

| journal | fit | length [check] | |
|---|---|---|---|
| *Groundwater* (NGWA) | Audience of [FIE21], [BAR18], [POT08]; wellhead protection practitioners; the Neversink benchmark is a *Groundwater* workflow paper | research papers about 7,000–8,000 words incl. references [check]; supporting information unlimited | **recommended** |
| *Environmental Modelling & Software* | Method plus open software; [PAR11] (hydraulic mixing cells) published there; requires code availability | no strict word limit for research papers [check] | second choice, if the paper stays software-heavy |
| *Water Resources Research* (Technical Report: Methods) | Theory (linear system, forward–backward identities) and the particle/mixing comparison | 25 publication units [check] | higher bar on novelty; the method itself is from 2013 |

Recommendation: *Groundwater*, with verification details, the PRT diagnosis and Tables 6–7 of NS moved to supporting information. Alternative: split into a method/software paper (EMS) and a Neversink comparison paper (*Groundwater*); decide after the first full draft.

## 3. Key messages

1. **The reference method is a linear system.** Backward fractions solve (I − P) F = S D, where P holds each cell's outflow to each neighbour as a share of the cell's total outflow and S D is the share of each cell's outflow that leaves through the destination sink terms; forward fractions solve the analogous system built from inflow shares. The reference method's cell-by-cell sweep is the special case without flow loops. Its net accounting, which credits a destination cell with all the water passing through it, is kept as an option and reproduces the [FB13] worked example exactly. Gross accounting credits a weak-sink well with its pumping only; net accounting credits it with all the water passing through its cell. How much that matters depends on the well's share of its cell's outflow. Net accounting attributes 6.7 times the pumping to the weak-sink well of tutorial 02. On Neversink it attributes 2.26 times the pumping to U___7, which takes 44 % of its cell's outflow, and 1.43 times to SV_487 (69 %), but only 7 % more than the pumping to the eight wells together (3,943.5 vs 3,671 m³/d). (`src/gwsource/assemble.py`, `solve.py`; `tests/test_fb13_example.py`; `tests/test_mf6_integration.py::test_weak_sink_gross_vs_net`; `tutorials/02_accounting`; `studies/neversink/net_and_envelope.py`, NS §2, Table 2a.)
2. **Every result carries its own check.** The backward and forward closure checks and the forward–backward check are exact identities once the cell budget errors are included. They hold to round-off on the synthetic test models (1–9) and to 1e-12 m³/d on the 1.68-million-cell Neversink model; transient tracking matches MF6 GWT to ≤ 1e-14. (`src/gwsource/diagnostics.py`; `tests/test_closure_duality.py`, `tests/test_tracking_mf6.py`; NS §1 Checks; PLAN Phase 4B notes.)
3. **It is cheap enough for ensembles.** On Neversink a trace takes 2 to 3 s for nine destination groups, against 44 s for the MODFLOW 6 run; 358 realisations with two traces each took 76 min on six processes. (NS Summary, §6.)
4. **A published particle delineation is one convention, not a cell-level reference.** On the same flow field, flow-weighted particles agree with the published MODPATH 7 contributing cells at an overlap (cells in both areas as a share of cells in either) of 0.29 to 0.62, depending on release depth and on how particles lose weight at weak sinks; full mixing (0.30 to 0.41) lies inside that range. PRT reproduces the published cells (overlap 0.998) only with the published conventions: recharge and stream flows on the top face where it is open, particles stopped at every weak sink, and particles in dry start cells draped to the first active cell below. The face assignment alone raises the overlap from 0.65 to 0.998. Full mixing traces exactly the wells' inflow; particles that lose weight at every sink in proportion to the flow that sink takes from the cell's outflow (weight-losing particles) deliver it within 2 %. (NS §2–3, Tables 1, 3; `mp7_reproduction.csv`.)
5. **Across an ensemble and pumping scenarios, full mixing follows the published areas.** Mean F correlates with the published probability of contribution at 0.80 and gives 90 % of its expected area (the sum of the cell values, in cells). The median area is within 10 % of the published median from base to maximum pumping (911 vs 998 cells; 3,725 vs 3,592). The full-mixing area grows faster than pumping (4.09 vs 3.68 times) mainly because the stream share of the wells' water falls (42 % to 28 %). The published area grows more slowly (3.60), mainly because particles stop in buried stream cells (SFR reach cells with an active cell above, where a gaining reach is a weak sink inside the cell), which PRT with the published conventions reproduces (3.62). (NS §6–7, Tables 4–6.)
6. **How streams are represented changes the answer.** With streams as cells, stream leakage is a source term of the aquifer cell: 43 % of the wells' water is stream leakage and the contributing area stops at the streams. With the 12,316 SFR reaches added as a stream network, leakage is traced up the stream to where its water entered. All of it then traces to recharge, and the median area is 1.7 times larger at base pumping and 1.4 times at maximum pumping (1,534 vs 911 and 5,247 vs 3,725 cells); the ensemble mean F gives 1.51 times the published expected area. (NS §4, Tables 4–5.)

## 4. Draft abstract (about 250 words)

Full-mixing flow tracing computes from cell-by-cell flows the fraction of each cell's water that reaches a destination or came from a source. It is used for source protection zones but lacks a peer-reviewed description and open code. We write it as a sparse linear system, solved exactly even with flow loops, with gross accounting of weak sinks and exact water-budget checks, for MODFLOW 6 grids, multi-model simulations and stream, lake and well networks. The checks hold to round-off, and transient tracking matches MODFLOW 6 transport to 1e-14. On the USGS Neversink/Rondout model (1.68 million cells), where a trace takes 2–3 s, cell-by-cell agreement with the published MODPATH 7 contributing areas of eight supply wells is moderate (overlap 0.30–0.41: cells in both areas over cells in either). Flow-weighted particles on the same flow field give 0.29–0.62, depending on release depth and weight loss at weak sinks. MODFLOW 6 particle tracking reproduces the published areas (overlap 0.998) only with their conventions (stopping at every weak sink, draped dry starts, recharge and stream flows on the top face); the face assignment alone raises the overlap from 0.65. Over 358 realisations and five pumping scenarios the median full-mixing area is within 10 % of the published median. It grows faster than pumping mainly because the wells' stream share falls from 42 % to 28 %; the published areas grow more slowly mainly because particles stop in stream cells below active cells. Tracing through the stream network attributes all well water to recharge and enlarges the area 1.4 to 1.7 times. Particle conventions and stream treatment should be stated with any delineation.

(About 250 words.)

## 5. Section outline

### 5.1 Introduction

- Contributing areas and capture zones: particle tracking [POL88, POL16] is standard; weak sinks, transient flow and many destinations are hard to handle with it [EA19, BF13]. Evidence: `references/SUMMARY.md` §4.
- Terminology: capture fraction in the budget sense [LEA10, BAR18], the share of a well's pumping supplied by increased recharge or reduced discharge (for example streamflow depletion), is a different quantity from F; state this early. Evidence: `references/bibliography.md` §D.
- Flux-based alternatives: MODALL [POT08] and its critique [MC09], the reference method [FB13, BF13], hydraulic mixing cells [PAR11], unit-concentration transport [BED24], particle source apportionment [PRY22], backward-in-time (adjoint) and groundwater-age methods [NW99, GOO96, CP06]. Evidence: `references/SUMMARY.md` §5.
- Gaps: no peer-reviewed description of the reference method, no open code, flow loops handled by deleting cell-to-cell connections, net accounting that credits a weak-sink well with all the water passing its cell, no published comparison with particle-tracked contributing areas on a large real model. Evidence: `references/bibliography.md` §F; PLAN §1 table.
- Aims, as three questions: (i) an exact formulation whose results can be checked against the water budget; (ii) cost on a regional model and ensemble; (iii) what the differences from a published particle delineation consist of.

### 5.2 Method

- **Cells, flows and accounting.** Each active cell is a fully mixed volume. The cell-to-cell flows (FLOW-JA-FACE) connect the cells, and every other budget term is kept as its own source or sink term. Each cell's total outflow O, total inflow I and cell budget error r = I − O are reported; r is never forced to zero. Gross accounting: each sink term in a cell takes its share of the cell's total outflow, and the rest passes to the neighbours, so a weak-sink well is credited with its pumping only. Evidence: PLAN §2.1; `assemble.py` docstring.
- **Backward and forward systems.** Backward: (I − P) F = S D, with P_ij = q_ij / O_i the share of cell i's outflow that goes to neighbour j, and S D the share of each cell's outflow that leaves through the destination sink terms. Forward: (I − Q) G = R T, built in the same way from inflow shares, with R T the share of each cell's inflow that enters through the selected source terms. Derived volumes: the water passing through each cell that reaches the destination, the water entering the model in each cell that reaches it, and (forward) the water leaving through each sink that came from the source, each split by package. Boundary-control maps give, in every cell, the fractions going to each sink; they add up to 1. Evidence: PLAN §2.2–2.3; `metrics.py` docstring; `tests/test_closure_duality.py::test_steady_boundary_control`.
- **Net accounting and the reference method.** Destination cells are fixed at F = 1 (all their water is credited to the destination), and each cell's net source (cell-to-cell outflow minus inflow) is used; this reproduces [FB13] Figs 5–8 and over-attributes water to weak-sink wells. Evidence: PLAN §2.4; `tests/test_fb13_example.py`; tutorial 02.
- **Solution.** Without flow loops, the system is solved cell by cell in flow order, which is the reference method's sweep in matrix form. With loops, each loop is solved as one small block, the blocks in flow order (block-triangular sparse LU over the strongly connected components). Closed recirculation loops (groups of cells with no outflow to any sink or to a cell outside the group) are found before the solve, given F = 0 and reported. The matrix is an M-matrix (each cell's outflow shares sum to at most 1), so the factorisation needs no reordering for stability (no pivoting). Evidence: `solve.py` docstring; PLAN Phase 2 notes; `tests/test_mf6_integration.py::test_xt3d_cycles_detected_and_solved_by_block_lu`.
- **Diagnostics.** Backward closure Σ F Src − Σ F r = destination inflow: the source volumes traced to the destination, corrected by the cell budget errors, add up to its inflow. Forward closure: the same for a source's inflow. Forward–backward check Σ_S F q − Σ_D G |q| = Σ F G r: the volume from source to destination is the same traced either way (a duality identity of the two systems). Evidence: `diagnostics.py` docstring.
- **Travel time.** Mean travel time under full mixing: (I − P) m = τ ∘ F, with τ_i = V_i / O_i the mean residence time of cell i (water volume over outflow) and m the travel time weighted by the fraction reaching the destination; the mean travel time is m / F. The system is solved with the factorisation already computed for F. Identity ΣVF/Q: the flow-weighted mean travel time of all water reaching the destination equals the volume of water that ends there divided by its inflow (a turnover time), once the cell budget errors are included. Evidence: PLAN §2.6 and Phase 3 notes; `traveltime.py`.
- **Transient (brief).** Snapshots, each time step traced on its own flows, with statistics accumulated step by step; transient forward tracking through storage, and the matching backward tracking. Keep to one paragraph, or leave for a later paper (see §7). Evidence: PLAN Phase 2 and 4B notes; `tracking.py`.

### 5.3 Implementation

- MF6 reader: binary grid IA/JA in user numbering for DIS/DISV/DISU, list and array budget records, and both budget records of a package that hands water to the mover (e.g. DRN and DRN-TO-MVR), each kept as a sink term. Evidence: `mf6io.py` docstring; PLAN Phase 1–2 notes.
- Package networks: SFR reaches, lakes, MAW wells and UZF cells added as extra cells from the package budget files, MVR transfers as connections between them, and a check that the GWF and package budgets agree on each aquifer exchange (tolerance `aquifer_rtol`). Multi-model GWF-GWF exchanges. Evidence: `network.py`, `packages.py`; PLAN Phase 4A notes.
- Selection of destinations and sources (by package, boundname, cells or zone), exports (npz, netCDF, GeoPackage), and an ensemble routine that traces each realisation in turn and keeps running statistics per cell. Evidence: `selectors.py`, `export.py`, `ensemble.py`.
- PRT post-processing routine: flow-weighted release from each source term; reads IFLOWFACE (the cell face a boundary flow is assigned to); gross accounting along each path, so that particles lose weight at every sink in proportion to the flow that sink takes from the cell's outflow (weight-losing particles). Evidence: `prt.py`; PLAN Phase 3 PRT revision and IFLOWFACE notes.
- Performance: 1M-cell synthetic grid; solve without flow loops 0.55 s, block solve with 7,000 flow loops 0.42 s; memory about 90 MB per group per million cells. Evidence: PLAN Phase 2 notes; `benchmarks/`.

### 5.4 Verification on synthetic models

- [FB13] worked example, net accounting: exact. Evidence: `tests/test_fb13_example.py`.
- Closure, forward–backward and boundary-control checks to 1e-10 relative (observed: round-off): models 1–5 and transient steps of model 6 (`tests/test_closure_duality.py`), package-network models 7–9 (`tests/test_package_network.py`, `tests/test_mover.py`). Evidence also PLAN Phase 1 "Done when", Phase 4A notes.
- Same results on every grid type: DIS = DISU to machine precision; split simulations equal the single model to ≤ 7e-10. Evidence: `tests/test_mf6_integration.py::test_dis_and_disu_identical`; `tests/test_multimodel.py`; PLAN Phase 4A.
- Transient tracking vs MF6 GWT: ≤ 2e-15 (model 6), ≤ 1e-14 (model 7 with SFT and MVT). Evidence: `tests/test_tracking_mf6.py`; PLAN Phase 4B.
- Particles: mean travel time to the well cell, full mixing vs PRT, 9574 vs 9590 d (model 1; 9607 d with the residence in the well cell); flow delivered by particles 800.4 of 800 m³/d; 3-layer model 402.6 of 405 m³/d. Evidence: `tests/test_prt.py`; PLAN Phase 3.
- Numerical dispersion against Javandel–Tsang and PRT references: the transition band (0.1 < F < 0.9) narrows as about h^0.5; F = 0.5 area within 5 % for h ≤ 50 m; F ≥ 0.1 always contains the reference zone (analytical, or PRT on the finest grid) but is 8–90 % too large; source shares identical to three digits. Evidence: DS Summary, Tables 1–2, §5.

### 5.5 Neversink case study

**Model and benchmark.**
- USGS Neversink/Rondout MF6 model [FIE21, COR22]: 4 × 680 × 619 cells of 50 m, NEWTON, RCHA/CHD/WEL/SFR (12,316 reaches); rerun with MF6 6.9, heads within 8.6 mm. Evidence: NS §1.
- Benchmark: published MODPATH 7 forward runs, one particle per uppermost active cell (122,021), weak sinks stop particles; 980 cells contributing to eight priority wells (3,671 m³/d). Evidence: NS §1.

**Calibrated model vs published contributing cells.**
- Overlap, defined as the cells in both areas as a share of the cells in either (the Jaccard index): 0.30 (F > 0.1), 0.41 (F > 0.5, and area-matched, i.e. the 980 cells with the largest F); sum of F 910 vs 980 cells; 96 % of the well water enters in published start cells. The Neversink thresholds are strict (F > 0.1, F > 0.5), as in NS; the dispersion tests use F ≥ 0.1 and F ≥ 0.5. Evidence: NS §2, Table 1; `output/agreement_with_mp7.csv`, `mp7_coverage.csv`.
- The F > 0.5 area is a core (94 % inside the published area, covering 43 % of it); the F > 0.1 area is twice as large and misses 27 %. Evidence: NS §2, §5.
- Per-well agreement is low because the U-cluster wells share contributing areas and a particle counts for one well only. Evidence: NS Table 2.
- Net accounting on the same flow field (NS §2, Tables 2a–2b; Fig. S1a): the eight wells are credited with 3,943.5 m³/d against 3,671 m³/d pumped. The difference is large only at U___7 (2.26 times its pumping) and SV_487 (1.43 times), the wells that take the smallest shares of their cells' outflow. The flow field has no flow loops, so removing loops, as the reference method does, makes no difference here. Against the published cells, net accounting gives a sum of F of 978.5 vs 980 (gross 910.2) and an overlap of 0.44 at F > 0.5 (gross 0.41) and 0.28 at F > 0.1 (gross 0.30). Per well it moves away from the published counts at U___7 (214 vs 58 cells) and U___8 (249 vs 163). Evidence: `studies/neversink/net_and_envelope.py`; `output/net_vs_gross_wells.csv`, `net_vs_gross_mp7.csv`, `net_vs_gross_cell_classes.csv`.
- End states of the published particles: in buried stream cells (an active cell above) the stream exchange stays distributed in the cell, and where the reach gains from the aquifer it is a weak sink that stops particles; open-top stream cells let them leave through the top face. SI. Evidence: NS §2; `output/mp7_status.csv`.

**Particle tracking on the same flow field.**
- Weight-losing PRT particles deliver 3,736 m³/d against a well inflow of 3,671 m³/d (+1.8 %; between 0.0 and +1.8 % over five release layouts, with no trend in the number of particles); plain particles, which lose weight only to the wells, over-count 2.6 times. Evidence: NS §3, Table 3; `output/prt_comparison.csv`.
- Why the first PRT runs delivered too little (53 % and 82 %): particle weight dropped in well cells that take only part of the cell's outflow (+720 m³/d), and particles trapped at the water table (−1,300 m³/d at the water table vs mid-cell). Both were defects of an earlier version of the PRT post-processing routine, not of either method. Evidence: NS §3 table "first well cell only vs weight followed on"; `output/prt_diagnosis.csv`; `tests/test_prt.py::test_capture_along_paths_follows_weight_past_partial_sinks`.
- The source split differs by method (stream 43 % vs 51 %), from reaches 0.4–1.3 km from the wells. Evidence: NS §3; `output/prt_sources_by_well.csv`.
- F zones against the weight-losing PRT zone P > 0.5 (691 start cells), the particle reference zone as the dispersion study defines it (NS §5, Table 3a; Fig. S1b–d). F > 0.1 covers 87 % of the PRT zone and misses 89 cells, 86 of them in the U cluster, where they form a strip about 1.5 km long north-west of the U wells. 87 of the 89 receive only recharge; their median F is 0.066, they hold 276 m³/d of recharge, and PRT delivers 227 m³/d from them to the wells (6 % of 3,736 m³/d). The F > 0.5 area lies 92 % inside the PRT zone. Two caveats: PRT was seeded only where F > 1e-6, so the PRT zone can lie only inside F's own support (all 2,139 start cells with F > 0.1 were seeded); and weight-losing particles share full mixing at weak sinks, so the reference is not an independent advective zone and the test covers only the spreading between sinks. Evidence: `studies/neversink/net_and_envelope.py`; `output/envelope_prt.csv`, `envelope_prt_notes.csv`.
- Reproducing the published cells: recharge and stream flows on the top face where it is open (IFLOWFACE), dry starts draped, particles stopped at weak sinks: 99.0 % end in the same cell, overlap 0.998; MF6 default conventions 0.62–0.65. Evidence: NS §3 table; `output/mp7_reproduction.csv`.

**Streams.**
- Streams as cells: 57 % recharge, 43 % stream leakage. Stream network (SFR reaches as extra cells linked by stream routing): 100 % recharge; the area extends upstream along streams; 8 small flow loops solved exactly; trace 2.6 s. Evidence: NS §4; `output/sources_cells.csv`, `sources_sfr_network.csv`, `checks_sfr_network.csv`.

**Ensemble at base pumping.**
- Rebuilt PEST interface; 358 realisations; closure ≤ 3e-12 m³/d in each; stream share 30–45 %. Evidence: NS §6.
- The published Monte Carlo contributing areas lie one row south of their cells and are ordered by run numbers sorted alphabetically (100 before 10); with both corrected, PRT with the published conventions matches the published area of each of the 60 realisations tested (median overlap 0.996). Evidence: NS §6; `studies/neversink/mc_masks.py`; `output/scenarios/mechanisms60/mask_matches.csv`.
- Mean F vs published probability of contribution: r = 0.80, ratio of expected areas 0.90, overlap 0.48 for the zones > 0.5; stream network 1.51 times the area. Evidence: NS Table 4; `output/ensemble/probability_comparison.csv`.
- In the S region the published area varies between realisations with a coefficient of variation of 32 %, follows PRT (r = 0.997) but not the sum of F (r = 0.00). Evidence: NS §6.

**Pumping scenarios and growth mechanisms.**
- Scenario pumping rule inferred from the published Monte Carlo areas (root-mean-square misfit of the log area ratios 0.05), each realisation's well multipliers kept. Evidence: NS §7; `scenarios.py`.
- Median areas within 10 % of published across five rates. Evidence: NS Table 5; `output/scenarios/area_table.csv`.
- Area growth 4.09 vs pumping growth 3.68: the stream share falls 42 % → 28 %; the recharge reaching the wells grows 4.57 times, and the area per unit of that recharge falls 11 %; r = 0.94 across realisations. Evidence: NS §7; `output/scenarios/source_table.csv`.
- Where the stream water changes: 72 % of the increase is a larger share of the leakage from reaches already losing that reaches the wells; 18 % comes from reaches switching to losing; most of the extra pumping is recharge that discharged to streams at base pumping. Evidence: NS §7; `output/scenarios/mechanisms60/growth_decomposition.csv`, `stream_by_state.csv`, `stream_by_distance.csv`.
- Why the published area grows more slowly: one convention at a time (Table 6); stopping particles in buried stream cells where the reach is a weak sink takes growth from 4.76 to 3.83. Evidence: NS Table 6; `mechanisms60/stream_stops.csv`.
- Why weight-losing particles grow faster than full mixing: a 10 % shortfall at base pumping from reaches near the U wells whose leakage only partly reaches the wells, gone at higher pumping. Supporting information. Evidence: NS §7, Table 7; `output/scenarios/advective_growth/`.

### 5.6 Discussion

- **Full mixing or particles.** Same water totals, different paths. Full mixing gives exact budgets, weak-sink shares and many destinations in seconds; particles give advective paths and first arrival. Use F = 0.5 for an advective core and particles where zones are small [EA19]. Evidence: DS §5; NS §3, §5.
- **Particle conventions matter as much as the method.** On overlap with the published cells, weight loss at sinks (0.29 vs 0.62, flow-weighted particles) and face assignment (0.65 vs 0.998, particles from the published starts) each move the result by about a third, as much as or more than the switch from weight-losing particles to full mixing (0.62 vs 0.30–0.41). Release depth changes the flow particles deliver by a third (2,413 vs 3,736 m³/d), while full mixing and weight-losing particles agree on it within 2 %. A delineation should state release position, stopping rule and face convention. Evidence: NS Table 3, §3 reproduction table, §5.
- **Thresholds.** In the synthetic tests the F ≥ 0.1 zone contained the reference zone (analytical, or fine-grid PRT) in every run, missing at most 0.1 % of it (DS). On Neversink the F > 0.1 area is not a full envelope. It misses 27 % of the published cells, whose particles stop at every weak sink, and 13 % of the weight-losing PRT zone P > 0.5, whose particles do not (89 cells, 6 % of the water PRT delivers to the wells). The F > 0.5 area stays a core (92 % inside the PRT zone). Because the PRT reference shares full mixing at weak sinks, this tests only the spreading between sinks. Present F ≥ 0.1 as a wide zone that contained the reference in the synthetic tests but not fully on Neversink. Evidence: DS §5; NS §5, Table 3a.
- **Net accounting and the published counts.** Net accounting brings the sum of F close to the published count (978.5 vs 980; gross 910.2) and raises the overlap at F > 0.5 from 0.41 to 0.44; at F > 0.1 it is about the same (0.28 vs 0.30). Per well it moves away from the published counts at U___7 and U___8, so the group-level match is partly the net of differences of both signs. One possible reading, which we have not tested: stopping each particle at the first weak sink, as the published runs do, credits the whole cell to the well, which is what net accounting does. Evidence: NS §2, Table 2b.
- **Streams.** Streams as cells answers "which package delivers the water"; the stream network answers "where did the water enter". With streams as cells, the fall in stream share explains most of the faster area growth (r = 0.94 across realisations). Evidence: NS §4–5, §7.
- **Ensembles.** Realisation-to-realisation variation of a published particle-tracked area can come from the particle conventions rather than from differences in the water reaching the wells (S region). Evidence: NS §6.
- **Reproducibility of published benchmarks.** Two bookkeeping offsets in the published Monte Carlo contributing areas had to be inferred; archive the steps that write the contributing-area files. Brief, neutral. Evidence: NS §6, §8.

### 5.7 Limitations

- Full mixing is grid-dependent (transition band ~h^0.5); face-to-face routing removes 35–70 % of the excess but is 2D and experimental. Evidence: DS §4, §6.
- Steady and snapshot results have no travel lag; transient tracking is advection only, with upstream weighting and implicit time steps. Evidence: PLAN §2.7; DS §3.
- The Neversink comparison is on the uppermost active layer only; the scenario rule and the pairing of published areas with realisations are inferred; the maxrange scenario (each priority well's rate drawn at random between its base and maximum rate, independently per well and realisation) is reproduced in distribution only. Evidence: NS §8.
- Some mechanism statements are inferred, not traced cell by cell (leakage staying on flow lines; narrow paths in Fig. 7). Evidence: NS §6, §7, §8.
- MF6 PRT aborts in cells wet only by a thin film (one start left out); a reproducer is prepared, not yet reported upstream. Evidence: NS §8; `studies/neversink/prt_film_repro/`.
- PRT supports DIS and DISV only; for DISU there are full-mixing travel times only. Evidence: PLAN §2.8.

### 5.8 Conclusions

- Four or five sentences mirroring the key messages.

### 5.9 Code and data availability

- `gwsource` (MIT) on GitHub, with tests, tutorials and the study scripts (`studies/neversink/`, `studies/dispersion/`); archive a release on Zenodo with a DOI [check].
- Neversink model and MODPATH outputs: USGS, `github.com/usgs/neversink_workflow` (CC0) and data release doi 10.5066/P9HWSOHP.
- Software versions: MF6 6.9 development build and FloPy `develop` [check: pin to released versions before submission, PLAN D3].
- Generated tables in `studies/neversink/output/` are not tracked; deposit the CSVs behind every table and figure with the release.

## 6. Figures and tables

| # | content | status | source |
|---|---|---|---|
| Fig. 1 | Schematic: a cell with cell-to-cell flows and source/sink terms; backward and forward systems; gross vs net accounting on a weak-sink cell | made | `docs/paper/figures/fig1_method_schematic.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 2 | Verification summary: closure and forward–backward errors over test models; GWT agreement; DIS/DISU/split agreement | made | `docs/paper/figures/fig2_verification.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 3 | Numerical dispersion: transition-band width and area error against cell size | made | `docs/paper/figures/fig3_numerical_dispersion.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 4 | Neversink model, wells, regions and published contributing cells (location map) | made | `docs/paper/figures/fig4_location_map.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 5 | F with published cells; streams as cells and as a stream network | made | `docs/paper/figures/fig5_capture_maps.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 6 | Overlap with the published contributing cells by method and convention (full-mixing thresholds; PRT plain and weight-losing, release depth; PRT from MF6 default to published conventions) | made | `docs/paper/figures/fig6_agreement.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 7 | Published probability of contribution vs ensemble mean F (streams as cells, stream network) | made | `docs/paper/figures/fig7_probability_maps.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 8 | Area growth against pumping: published, full mixing, stream network, PRT with published conventions | made | `docs/paper/figures/fig8_area_growth.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 9 | Growth mechanism: stream share vs pumping, and area-growth excess vs stream-share drop across realisations (r = 0.94) | made | `docs/paper/figures/fig9_growth_mechanism.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Table 1 | Comparison of the reference method and this formulation (solve, accounting, flow loops, outputs) | to adapt | PLAN §1 table |
| Table 2 | Verification checks with tolerance and observed error | made | `docs/paper/figures/verification_table.md` / `.csv`; code `studies/paper/verification.py` |
| Table 3 | Calibrated model vs published cells (counts, overlap) | exists | NS Table 1 |
| Table 4 | Particle tracking variants: overlap, expected cells, flow reaching the wells | exists | NS Table 3 plus reproduction table |
| Table 5 | Ensemble comparison | exists | NS Table 4 |
| Table 6 | Median areas by scenario | exists | NS Table 5 |
| Table 7 | One convention at a time: areas at base and maximum pumping | exists | NS Table 6 |
| Fig. S1 | Gross vs net attribution per well (a); maps of the PRT-zone cells missed by F > 0.1 (b–d) | made | `docs/paper/figures/figS1_net_and_envelope` (branch paper-figs) |
| SI | Per-well table (NS Table 2); end states; PRT diagnosis; Table 7 of NS; gross vs net and envelope tables (NS Tables 2a–2b, 3a); dispersion maps and transient sub-steps (DS Figs 1, 3, 5) | exist | NS, DS |

## 7. Claims–evidence gaps (priority order)

1. **Scripts for the five-layout analysis are missing.** NS §3 says the five-layout analysis of the +1.8 % excess "was a one-off analysis; its scripts are not in the repository". Add them (or drop the claim) before the paper cites it.
2. **Threshold guidance on Neversink against a non-stopping reference.** Done: F > 0.1 covers 87 % of the weight-losing PRT zone P > 0.5, and the F > 0.5 area is 92 % inside it (NS §5, Table 3a; Fig. S1b–d). Evidence: `studies/neversink/net_and_envelope.py`; `output/envelope_prt.csv`, `envelope_prt_notes.csv`.
3. **Gross vs net on Neversink.** Done: net accounting credits the eight wells with 1.07 times their pumping, U___7 with 2.26 times and SV_487 with 1.43 times (NS §2, Tables 2a–2b; Fig. S1a). Evidence: `studies/neversink/net_and_envelope.py`; `output/net_vs_gross_wells.csv`, `net_vs_gross_mp7.csv`, `net_vs_gross_cell_classes.csv`.
4. **Verification table and figure.** Done: `studies/paper/verification.py` collects the checks over test models 1–9 (Table 2, Fig. 2); all pass, the largest round-off error is 1.5e-15.
5. **Travel time on Neversink.** The published MODPATH runs have travel times and PRT agrees with them within 1 % (NS §3), but full-mixing mean travel times were not compared. Needed only if the paper keeps travel time in scope.
6. **Inferred mechanisms.** Leakage staying on flow lines to the wells (NS §7) and the narrow-path reading of Fig. 7 (NS §6) are inferred. Either trace one reach cell by cell or word them as interpretation.
7. **Transient scope.** No real-model transient application. Either limit the paper to steady state and ensembles (recommended) or add one.
8. **References missing from `references/bibliography.md`:** MF6 PRT documentation, FloPy, PEST++/iES, Javandel & Tsang (1986) (cited only inline in DS), Mf6Splitter. Add before drafting.
9. **Report the PRT abort in thin-film cells upstream** (NS §8) so the paper can cite the issue.

## 8. Reference skeleton

Keys as in `references/bibliography.md`, which holds the full entries. The titles of [FB13], [BF13] and [BFW21] contain the product name, which this repository's naming test forbids, so they are not repeated here.

- **Reference method:** [FB13] Foley & Black 2013 and [BF13] Black & Foley 2013 (MODFLOW and More 2013 proceedings; page ranges from secondary citations [check]); [BFW21] Black, Foley & Witterick 2021 (slides; cite only for the later fraction-from definition); [EA19] Environment Agency 2019 (SPZ manual); [MAU21] Maurice et al. 2021; [CHO16] Chowdhury 2016 (thesis; face-to-face routing).
- **Related flux-based and transport methods:** [POT08] Potter et al. 2008 (MODALL); [MC09] McLane & Cecan 2009; [PAR11] Partington et al. 2011; [BED24] Bedekar et al. 2024; [PRY22] Pryet et al. 2022; [NW99] Neupauer & Wilson 1999; [GOO96] Goode 1996; [CP06] Cornaton & Perrochet 2006; [FRI02] Frind et al. 2002.
- **Capture terminology:** [BAR18] Barlow, Leake & Fienen 2018; [LEA10] Leake, Reeves & Dickinson 2010.
- **Particle tracking and MODFLOW 6:** [POL88] Pollock 1988; [POL16] Pollock 2016 (MODPATH 7); [LAN17] Langevin et al. 2017 (GWF); [LAN22] Langevin et al. 2022 (GWT); [MF6IO] input/output guide. Not yet in the bibliography [check]: MF6 PRT documentation; FloPy (Bakker et al. 2016; Hughes et al. 2024).
- **Case study:** [COR22] Corson-Dosch et al. 2022; [FIE21] Fienen et al. 2021; USGS data release doi 10.5066/P9HWSOHP. Not yet in the bibliography [check]: PEST++ iES (White et al. 2020).
- **Synthetic reference:** Javandel & Tsang 1986, Ground Water 24(5) (cited inline in DS only; add to the bibliography).
