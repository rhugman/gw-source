# Case study: priority-well capture in the Neversink/Rondout model

Phase 5 case study, 2026-10-02: stage 1 (calibrated model), stage 2 (358-realisation ensemble) and stage 3 (pumping scenarios). Code: `studies/neversink/workflow.py` (stage 1), `studies/neversink/pest_rebuild.py` (realisations), `studies/neversink/ensemble_run.py` and `studies/neversink/scenarios.py` (stages 2 and 3), `studies/neversink/figures.py`. Generated tables: `studies/neversink/output/` (not tracked).

## Summary

- **Model and benchmark.** The study runs full-mixing backward tracing [FB13, BF13] on the USGS Neversink/Rondout MODFLOW 6 model (1.68 million cells, 50 m) from the eight priority wells (3,671 m³/d). It compares the result with the published MODPATH 7 areas contributing recharge to the same wells.
- **Counts.** The cell counts are close: the sum of F over the particle start cells is 910, against 980 contributing cells in the published runs. 96 % of the well water enters the model in cells where the published particles start.
- **Cell by cell, agreement is moderate.** The Jaccard index with the published cells is 0.30 for F > 0.1, 0.41 for F > 0.5 and 0.41 for the same number of cells ranked by F. Particle tracking on the same flow field gives 0.29 to 0.62 depending on weak-sink treatment and release depth, and with thinning it captures the wells' inflow to 2 %. Run with the published particle conventions, MF6 PRT reproduces the published mask (Jaccard 0.998), so the mask is one particle convention, now fully accounted for, not ground truth at cell level.
- **Streams.** With streams as cells, 43 % of the priority-well water is stream-reach leakage. With the 12,316 SFR reaches as nodes of the graph, all of it traces back to recharge. The contributing area then extends upstream along the streams, outside what a recharge-cell mask can show.
- **Ensemble.** Over the 358 realisations at base pumping, the mean F correlates with the published probability of contribution at 0.80 and gives 90 % of its expected area; the zones above 0.5 overlap with a Jaccard index of 0.48. The published Monte Carlo masks lie one row south of their cells and are numbered in a text-sorted run order; with both corrected, PRT with the published conventions reproduces each realisation's mask (median Jaccard 0.996, Section 6).
- **Pumping scenarios.** With the scenario rule inferred from the published masks, the median full-mixing area is within 11 % of the published median from base to maximum pumping (911 against 998 cells at base, 3,709 against 3,590 at maximum; 357 realisations per scenario). It grows faster than pumping mainly because the stream share of the wells' water falls as pumping rises. The additional pumping is mostly recharge that discharged to streams at base pumping; the published area grows more slowly (3.60 against 4.07 times) mainly because the published particles stop at buried stream cells, which PRT with the published conventions reproduces (3.60).
- **Cost.** The trace takes 2 to 3 s for nine destination groups; MODFLOW 6 takes 44 s. The ensemble (358 realisations, two traces each) took 76 min on six processes.

## 1. Model, benchmark and method

**Model.** The model is the calibrated ("optimal", base-parameter) USGS Neversink/Rondout model [FIE21, COR22]. It is public domain (CC0), from `github.com/usgs/neversink_workflow` and the USGS data release doi 10.5066/P9HWSOHP.

- MODFLOW 6, steady state, NEWTON, DIS 4 layers × 680 rows × 619 columns of 50 m (1,683,680 cells).
- Packages: RCHA, CHD, WEL (34 entries with boundnames) and SFR (12,316 reaches, with its own budget file).
- The input is from 2021 (MF6 6.2). It was re-run here with MF6 6.9 (development build) after renaming the IMS keywords `OUTER_HCLOSE`/`INNER_HCLOSE` to `*_DVCLOSE` and dropping `OUTER_RCLOSEBND`. `SAVE_SPECIFIC_DISCHARGE` and `SAVE_SATURATION` were added to the NPF package for the particle check.

**Benchmark.** The published MODPATH 7 runs are forward runs with weak sinks stopping particles, in three regions (NE, S, W) around the well clusters. One particle starts at the centre of each cell of the uppermost active layer (122,021 particles). A cell counts as contributing if its particle ends in one of the eight priority wells (SV_193, SV_227, SV_407, SV_487, U_917, U__55, U___7, U___8). Their total pumping is 3,671 m³/d.

**Comparison.** Each particle start cell is given the backward fraction F of that cell, the share of its water that reaches the wells. The MODPATH mask and F > threshold are then compared cell by cell. PRT checks use the Phase 3 helper (`gwsource.track_particles`) on the same flow field, with porosity 0.3 as in the published MODPATH files. Each particle carries the gross accounting along its path: in every cell it passes, the wells take their share of the cell's outflow from the particle's remaining weight. With `thin_weak_sinks=True` the cell's other sinks remove their share too; with `False` they do not, as in a plain particle run.

**Checks.**

| run | time (s) | max head difference to the published run (mm) |
|---|---|---|
| published solver settings | 44 | 8.6 |
| tight (OUTER_DVCLOSE 1e-4, INNER_DVCLOSE 1e-6) | 75 | 5.6 |

Both are below the model's own convergence criterion (0.01 m). The tight run is used only for the stream network (Section 4). The backward closure check (`gwsource.diagnostics.backward_closure`) is 1e-12 m³/d or smaller for every group, with streams as cells and as nodes.

## 2. Results: contributing cells

![Capture maps](figures/neversink_capture_maps.png)

*Figure 1. F of the uppermost active cell for the eight priority wells (blue), with the published MODPATH 7 contributing cells (outline) and the wells (dots). Top: streams as cells. Bottom: SFR reaches as nodes. Windows: the north SV wells, the southern SV well, the U cluster.*

**Table 1. Priority wells together, versus the published cells (980)**

| measure | cells | Jaccard index |
|---|---|---|
| F > 0 | 50,703 | 0.02 |
| F > 0.1 | 2,139 | 0.30 |
| F > 0.5 | 445 | 0.41 |
| 980 cells with the largest F (F ≥ 0.28) | 980 | 0.41 |
| sum of F over start cells | 910 | – |

Every published cell has F > 0. Their mean F is 0.42. Of the 445 cells with F > 0.5, 417 (94 %) are published cells, which are 43 % of the published area. The F > 0.1 zone has 2,139 cells, about twice the published area, and contains 711 of the 980 published cells (73 %). Only 5 published cells have F > 0.9.

**Source water in the published cells.** The published cells receive 4,278 m³/d of source water (recharge 2,297 and stream leakage 1,981 m³/d), 17 % more than the wells pump. Not all of it can reach the wells. This is consistent with the stopping rule of the published runs: a cell contributes if its particle ends in a priority well, and a particle stops at the first weak sink it meets. The well takes only part of its cell's outflow where the cell also passes water on, for example 44 % in the cell of U___7 and 69 % in the cell of SV_487 (85 to 100 % in the other six). Full mixing lets the rest continue downstream.

**Table 2. Per well**

| well | pumping (m³/d) | published cells | sum of F | Jaccard F > 0.1 | Jaccard F > 0.5 | Jaccard, same number of cells |
|---|---|---|---|---|---|---|
| SV_193 | 63 | 48 | 26 | 0.37 | 0.00 | 0.30 |
| SV_227 | 203 | 115 | 69 | 0.29 | 0.16 | 0.25 |
| SV_407 | 94 | 32 | 34 | 0.29 | 0.16 | 0.60 |
| SV_487 | 381 | 97 | 65 | 0.18 | 0.04 | 0.17 |
| U_917 | 1,054 | 351 | 313 | 0.56 | 0.53 | 0.68 |
| U__55 | 250 | 116 | 81 | 0.06 | 0.00 | 0.13 |
| U___7 | 516 | 58 | 94 | 0.20 | 0.00 | 0.05 |
| U___8 | 1,110 | 163 | 229 | 0.10 | 0.00 | 0.22 |
| all eight | 3,671 | 980 | 910 | 0.30 | 0.41 | 0.41 |

The wells of the U cluster share cells and capture areas, and a published cell belongs to the one well its particle reaches. A cell that sends water to several wells therefore scores for one of them in the benchmark, and for all of them under full mixing. Per-well agreement is correspondingly low, and the union of the wells is the fair comparison. The sum of F is above the published count for U___7 and U___8 and below it for the other wells.

**Coverage.** 96 % of the priority-well water (95 to 100 % per well) enters in the start cells of the published particles. Water entering elsewhere (deeper layers, outside the three regions) is invisible to the published runs; it is small here.

**End states of the published particles.** Each published particle ends in one of three ways (`studies/neversink/output/mp7_status.csv`). The end cells are classed on the MF6 budget: a strong sink sends all its outflow to boundary sinks, a weak sink only part of it.

- Status 2 (89,920 particles): the particle leaves through a face. 88,781 of them leave through the top face of a stream cell: the published MPBAS file places SFR (and RCH) flows on the top face (IFACE 6), and that works where the top face is the model boundary, i.e. where no active cell lies above the stream cell. The other 1,139 leave sideways, every one of them into a dry neighbour, which the published runs treat as inactive. None of the status-2 particles ends in a priority well.
- Status 3 (27,631): stopped on entering a weak-sink cell (the weak-sink option of the published runs), every one of them. Most are stream cells with an active cell above (26,828). There the top face is internal, and the stream flow acts as a sink inside the cell: every particle that stops in a stream cell (status 3 or 5) has an active cell above it, and none of those that leave through a stream cell's top face has. The MODPATH 7 source agrees (ModpathCellData.f90 puts an IFACE flow on the face only where the face has no active neighbour; otherwise it stays a distributed source or sink). The rest are well (612) and CHD (191) cells. 466 of these particles end in the five priority wells that take only part of their cell's outflow (SV_407, SV_487, U__55, U___7, U___8).
- Status 5 (4,470): ended in a cell with no exit face, every one of them a strong-sink cell. These are wells (2,570), stream cells with an active cell above (1,472) and CHD cells (428). 514 of them end in the three priority wells that take all of their cell's outflow (SV_193 48, SV_227 115, U_917 351).

Status 5 is therefore the normal capture outcome at a strong sink, not an abnormal stop: the 980 published cells are the 514 particles that end in strong-sink wells plus the 466 stopped in weak-sink wells. The PRT runs of Section 3 end every particle the same way, also with status 5. The split between status 2 and status 3 does show a convention of the published runs that the comparison inherits: a stream cell with an active cell above stops particles as a weak sink, while one without lets them pass and leave only through its top face.

## 3. Results: particle tracking on the same flow field

**Table 3. Agreement with the published cells (Jaccard, priority wells)**

| method | Jaccard | cells expected | captured flow (m³/d) |
|---|---|---|---|
| full mixing, F > 0.5 | 0.41 | 910 (sum of F) | 3,671 |
| PRT, spread over the cell volume, thinned, P > 0.5 | 0.62 | 794 | 3,736 |
| PRT, spread over the cell volume, plain, P > 0.5 | 0.29 | 2,857 | 9,555 |
| PRT, released at the water table, thinned, P > 0.5 | 0.39 | 592 | 2,413 |
| PRT, released mid-cell, thinned, P > 0.5 | 0.62 | 781 | 3,722 |

P is the flow-weighted share of the water released in a cell that reaches the wells, evaluated at the published start cells (uppermost active layer). "Plain" means no weak-sink thinning. Particles were released from every source term (flux-weighted) of the 30,180 cells with F > 0 that have one, in all layers, with one plan sub-division per cell (4 points), at four heights through the saturated thickness ("spread over the cell volume", 488,448 particles) or at one (122,112). Together these cells receive 90,349 m³/d. The captured flow is the PRT total, to be compared with the inflow of the wells, 3,671 m³/d.

- With the points spread over the cell volume and thinning, the particles capture 3,736 m³/d, 1.8 % more than enters the wells, and each well gets within 11 % of its rate (SV_227 180 of 203 m³/d, U___8 1,171 of 1,110, the others closer). That is the agreement the duality of the gross method leads one to expect: the totals match and the paths differ. The excess is not systematic. Over five seeding layouts (122,112 to 488,448 particles) the total lay between 0.0 % and +1.8 % above the well inflow, without a trend: it is the net of local errors of both signs in how cells pass particle weight on to their neighbours (1,200 to 1,900 m³/d in absolute terms). The constant thinning factor per cell accounts for less than 2 m³/d of it, and a thinning rule based on each particle's residence time in the cell gives totals within 0.6 %. The per-well errors shrink as release heights are added (root-mean-square error 18 % with one height, 6 % with four; SV_227 from −35 % to −11 %) but not with more plan points at one height. This was a one-off analysis; its scripts are not in the repository.
- Plain particles over-count the wells' water by a factor of 2.6 (2.1 to 2.5 for single-height releases). They pass every weak sink other than the wells without losing weight, so water that streams and other sinks take on the way is counted as reaching the wells. Thinning corrects this.
- The mean absolute difference between F and P over the seeded cells is 0.025 to 0.027 for thinned particles and 0.09 for plain ones; the maximum is 0.81 to 1.00.
- Which source supplies the wells differs between the methods: under full mixing 57 % of the water is recharge and 43 % stream leakage, along the particle paths 49 % and 51 % (`prt_sources_by_well.csv`, one PRT run evaluated for every well). In a cell that receives both, the two sources reach the wells in the same proportion under either method, so the difference comes from where each source enters.
  - *Stream water* (+344 m³/d along the paths). No stream cell lies within 75 m of a priority well. The stream water that reaches the wells leaks from reaches 0.4 to 1.3 km south of the U wells and 0.5 to 1.2 km from SV_487. From these the particles carry 1,909 m³/d to the wells against 1,494 m³/d under full mixing. In 13 of their cells every particle reaches a well while F is 0.26 to 0.80: along the paths the leaked water keeps together, whereas under full mixing it is mixed in the cells it passes with water bound for other sinks. The effect is not one-sided: 20 stream cells with F > 0.1, mostly 400 to 450 m from the U wells, send almost no particles to a well (−130 m³/d).
  - *Recharge* (−279 m³/d). 220 m³/d of the difference is recharge more than 2 km from every priority well. There full mixing spreads small fractions over 6,578 cells with F > 0.001, but particles from only 548 of them reach a well with P > 0.001.
  - Within the U cluster the particles also move stream water between wells: U___7 +171 and U___8 +298 m³/d, U_917 −149 and U__55 −21.
  - Release height is not the cause: capture falls with height for both sources alike, and the stream share is 49 to 53 % at each of the four heights.

  Both shifts are differences of method, not errors of either.
- Release depth matters at the water table only. Released there, particles in the top layer never leave it: the top face carries no flow, so their vertical velocity is zero. Wells in deeper layers then get little (U__55 28 of 250 m³/d, SV_193 none of 63), and the total is 2,413 m³/d. Mid-cell release and release spread over the volume agree (3,722 and 3,736 m³/d, Jaccard 0.62 for both).
- Thinning changes the agreement with the published cells more than anything else (0.62 thinned against 0.29 plain), because the benchmark stops particles at every weak sink. Thinned particles at mid-cell or spread over the volume agree best with it (0.62).

**Why the first PRT runs captured too little.** An earlier version of the PRT helper captured 1,940 m³/d (53 %, water table) and 3,005 m³/d (82 %, mid-cell) with thinning. Running PRT without a stop zone and evaluating both rules on the same tracks separates two defects of that version, both in the helper rather than in either method. The `diagnose_prt` gate of `workflow.py` repeats this evaluation and writes the totals per rule and per well to `prt_diagnosis.csv`.

| release | first well cell only (earlier rule) | weight followed on (current) |
|---|---|---|
| water table | 1,940 (53 %) | 2,413 (66 %) |
| mid-cell | 3,005 (82 %) | 3,722 (101 %) |
| four heights through the cell | 3,015 (82 %) | 3,736 (102 %) |

- **Weight dropped in partial well cells** (+720 m³/d, 20 % of the inflow). The earlier rule stopped a particle in the first well cell it entered and credited the well with the share d/O that the well takes of the cell's outflow; the rest was dropped. The well of U___7 takes 44 % of its cell's outflow, but 97 % of the water in that cell reaches a priority well (F = 0.97): most of what passes on flows to U___8 and U_917. Followed on, the particles credit U___8 with 609 m³/d and U_917 with 111 m³/d more. The helper now applies the gross accounting along the whole path: in each cell, the destination takes d/O of the remaining weight and the cell's sinks remove Snk/O; there is no stop zone.
- **Particles trapped at the water table** (−1,300 m³/d at the water table against mid-cell). MF6 spreads recharge and the other boundary sources over the cell volume, and PRT's velocity field matches that. The helper now releases at several heights through the saturated thickness by default.
- Ruled out: every particle ended in a cell with no exit face (status 5) with no weight left after its last cell, so no water was lost to other termination states, and no particle entered a cell twice, so thinning was applied once per cell.

On the 3-layer test model with a weak well upstream of a strong one, the same two defects gave 266 of 405 m³/d. The current helper gives 402.6 m³/d (a regression test, `tests/test_prt.py`).

**Reproducing the published mask with PRT.** The published particles were rerun with MF6 PRT on the same flow field: one particle per published start position, stopping at weak sinks, porosity 0.3, no stop zone (gate `reproduce_mp7`, `studies/neversink/mp7_convention.py`, output `mp7_reproduction.csv`). Two published conventions had to be added.

- *Faces.* Recharge and stream flows go on the top face through the MF6 auxiliary variable IFLOWFACE (−1 = top face), which PRT reads from the budget file; it leaves heads and flows unchanged. As in MODPATH 7, this is done only where the top face is a model boundary: all recharge cells and 10,107 of the 12,316 stream reaches. The 2,209 reaches with an active cell above keep the flow distributed (PRT would otherwise end particles at such an internal face).
- *Dry start cells.* 25,610 start cells are dry in the Newton solution. The published runs drape these particles (MODPATH DrapeOption 1) to the first active cell below, at the same local position; PRT would drop them to the water table, so they were moved explicitly. That the published runs treat dry cells as inactive is inferred from the end points.

| PRT run | recharge and stream flows | dry start cells | same end cell | Jaccard | cells (in both) |
|---|---|---|---|---|---|
| published conventions | top face where it is open | draped | 99.0 % | 0.998 | 982 (980) |
| without draping | top face where it is open | dropped to the water table | 89.9 % | 0.96 | 969 (956) |
| MF6 default | distributed | draped | 42.3 % | 0.65 | 754 (680) |
| MF6 default, without draping | distributed | dropped | 39.6 % | 0.62 | 730 (656) |

With the published conventions, 99.0 % of the particles end in the same cell as in the published runs, and for 99.98 % of those the travel time agrees within 1 %. The PRT mask contains all 980 published cells and 2 more (Jaccard 1.00 for seven wells, 0.98 for SV_487). Nearly all remaining differences (all but 28 of 1,167 end cells) come from one further convention: the published runs stop the 1,139 particles that reach a side face with a dry neighbour (status 2, Section 2), whereas PRT passes them on; two of them then reach SV_487. The published MF6 6.2 flows give the same result as the rerun. One particle, in a cell wet only by a film (saturation 1.4e-16), was left out because MF6 PRT aborts at its release (Section 8).

Full mixing (0.41 for F > 0.5) lies inside the range of particle results (0.29 to 0.62 for the flux-weighted runs) that the same flow field yields under different conventions. With the published mask reproduced by PRT, its gap to full mixing is the difference between mixing and advective paths plus documented particle conventions, with no unexplained remainder at the scale of the mask. It is not a shortfall of water: both close on the wells' inflow.

## 4. Streams

With streams as cells, SFR cells are just cells that exchange water with the aquifer. Of the priority-well water, 2,100 m³/d (57 %) traces to recharge, and 1,571 m³/d (43 %) to SFR leakage. By well, SFR provides a large share of the water of SV_487 (51 %), U_917 (38 %), U___7 (63 %) and U___8 (57 %), and almost none of that of SV_193, SV_227 and SV_407.

With the SFR reaches as nodes of the graph (`package_nodes=("SFR",)` in `gwsource.read_network`), leakage is traced up the stream to where its water entered. All 3,671 m³/d then traces to recharge, none to the stream's external inflow or to CHD. This is consistent with stream leakage being groundwater that discharged upstream and re-infiltrates. The contributing area extends upstream along the streams. In Figure 1 (bottom), this is the pale area south-east of the U wells, with F of about 0.2, and the larger low-F area around the southern SV well. A mask built from recharge cells' particle ends does not contain it.

**Network reader tolerance.** `read_network` requires the GWF and SFR budgets to agree on the aquifer exchange of every reach to a tolerance of 1e-4 of the largest reach flow. With the published convergence criterion (0.01 m), 3 of the 12,316 reaches miss it (largest disagreement 1.9e-4 of the largest exchange, 869 m³/d). A tighter solve (OUTER_DVCLOSE 1e-4, INNER_DVCLOSE 1e-6, heads within 5.6 mm of the published run) meets it. `open_simulation` and `read_network` take an `aquifer_rtol` option for this; the difference then stays in the reaches' budget residuals, which the closure check includes. With `aquifer_rtol=5e-4` the published run reads directly and gives the same result (all 3,671 m³/d from recharge). Closure of the network trace is 1e-12 m³/d. The closure error that would remain if the cells' budget residuals were ignored falls from 4e-3 m³/d (streams as cells, published solve) to 1.5e-5 m³/d (network, tight solve) for the eight wells together.

**Cycles.** With streams as cells the flow graph has no cycles, so the solve is a single topological sweep. With reaches as nodes it has 8 small cycles of 4 to 130 nodes (reaches mixed with the cells they exchange water with), which the block solver handles exactly. The trace takes 2.6 s.

## 5. Interpretation and guidance

- **The published mask is a convention.** It uses one particle at each cell centre and stops at every weak sink. It is a valid delineation, but at the scale of single cells it is not a reference that full mixing, or any other method, should reproduce exactly. On the same flow field, flux-weighted particles span 0.29 to 0.62 agreement with it, depending on weak-sink treatment and release depth, and full mixing (0.30 to 0.41) is inside that range. PRT reproduces it (0.998) only when the published conventions are copied: top-face recharge and stream flows where the top is open, stopping at weak sinks, and dry cells treated as inactive.
- **Thresholds.** `docs/dispersion_study.md` Section 5 recommends F = 0.5 for an advective zone and F ≥ 0.1 as a conservative envelope. Here, the F > 0.5 zone (445 cells) is a core that lies almost entirely inside the published area (980 cells) and covers 43 % of it. The F > 0.1 zone (2,139 cells) is about twice the size of the published area and still misses 27 % of its cells, so it was not a conservative envelope at cell level, unlike in the dispersion study (one well, analytical or particle reference zone). The published area sits between the two. That guidance was derived against references that do not stop at weak sinks, and this case does not test it in that sense.
- **State the conventions.** Release depth and weak-sink treatment both change the agreement with the published mask substantially (Section 3). A comparison with it should state where particles start and what stops them.
- **Streams.** With streams as cells, 43 % of the wells' water is attributed to stream leakage and the contributing area stops at the streams. Whether that is the intended reading depends on the question: it is correct for "which source package delivers the water", and incomplete for "where does the water come from".

## 6. Stage 2: the ensemble at base pumping

**Ensemble.** The published PEST interface (`run_data/`) is not in the source repository, so it was rebuilt from the notebooks in `studies/neversink/pest_rebuild.py` without PEST++ or pyemu (pilot-point kriging of K, K33 and recharge, geology-zone multipliers, caps, streambed K, well multipliers). The rebuilt base realisation equals the published calibrated input. Realisations base, 0 and 280 reproduce the stored iES heads to 2 cm (median 0.3 mm) and the flows exactly; the published calibrated run differs from its own stored values by the same 2 cm. The Monte Carlo ensemble is the notebook's rejection sample of iES iteration 4: 358 realisations.

**Runs.** `studies/neversink/ensemble_run.py` writes, runs and traces every realisation in six processes (76 min in total; per realisation about 50 s of MF6 and 9 s for both traces) and keeps F of the uppermost active layer. Both traces use the published solver criterion; the stream network is read with `aquifer_rtol=1e-3` (Section 4). Closure holds in every realisation to 3e-12 m³/d. The wells' inflow ranges from 3,586 to 3,756 m³/d and the stream-leakage share (streams as cells) from 30 to 45 %.

**Pairing the published masks with the realisations.** Two bookkeeping steps of the published pipeline (`studies/neversink/mc_masks.py`) first hid the pairing:

- The masks lie one row south of their cells. `scripts/get_endpoints.py` computes the row as `nrow - (y0 - 25) / 50`, which is the 1-based row of the cell centre, while the column is 0-based. Row 0 is empty in every mask of every scenario. Unshifted, 24 published cells at base (827 at maxrat) lie off the published start cells; moved one row north, none do.
- Mask k is not run k. `scripts/modpath_mc_varq.py` saves run r (row r of the parameter table) as `mp_results_{r}_{qrat}.zip`, and the masks follow those names sorted as text, where `100_` comes before `10_`. The step that wrote the masks is not archived, so this order is inferred: it predicts the best-matching mask for all 60 realisations tested in each of three scenarios. Runs 0 to 356 have masks; run 357, the base realisation, has none. The order is the same in every scenario.

With both corrections, PRT with the published conventions (Section 3) on the rebuilt flow fields matches the paired published mask at Jaccard 0.989 to 1.000 (median 0.996) at base pumping, against a median of 0.75 for the second-best mask. The masks therefore come from the rebuilt flow fields. Full mixing agrees with its own mask only slightly better than with another realisation's: area-matched Jaccard 0.41 against 0.40, and better than with the neighbour's mask for 315 of 357. In the S region the published area varies by 32 % between realisations (coefficient of variation). PRT with the published conventions follows it (r = 0.997, 60 realisations) while the sum of F does not (r = 0.00). There, the differences between realisations show up through the particle conventions, not in the full-mixing capture. Stages 2 and 3 were run with the masks as stored. The areas are not affected, because masks are counted per index, so the area statistics need no correction. The probability maps were recomputed on the corrected masks for Table 4 and Section 7. Figure 2 still shows the uncorrected outline, one row (50 m) south.

**Table 4. Ensemble comparison at base pumping (357 published masks, 358 realisations, published start cells)**

| gwsource map | correlation with published probability | sum ratio | Jaccard, both > 0.5 |
|---|---|---|---|
| mean F, streams as cells | 0.80 (0.76) | 0.90 | 0.48 (0.43) |
| share of realisations with F > 0.5, streams as cells | 0.76 (0.71) | 0.47 | 0.48 (0.43) |
| mean F, stream network | 0.72 (0.70) | 1.51 | 0.49 (0.44) |

In brackets: against the masks as stored, one row south (see above).

The sum ratio compares the expected number of contributing cells (sum of the map over the start cells). The mean F, the full-mixing counterpart of the published probability, gives 90 % of the published expected area, as in the calibrated model (Section 2). With the stream network the area is 1.5 times larger, because it includes the upstream area that feeds the losing reaches.

![Probability maps](figures/neversink_probability_maps.png)

*Figure 2. Published probability of contribution (top) and gwsource's ensemble mean F with streams as cells (middle) and as a network (bottom), base pumping. Outline: published probability 0.5, from the masks as stored (one row south of the true position).*

The core zones agree; the differences are where the published probability follows narrow paths: the strip north-west of the U wells, where it is about 0.8 and mean F is low, and the band north-west of the southern SV well. These look like single-particle paths through cells that, under full mixing, send most of their water elsewhere. That reading has not been tested.

## 7. Stage 3: pumping scenarios

**Scenario rule.** The scripts that built the scenario ensembles are not archived. `studies/neversink/scenarios.py` infers the rule from the 6 × 357 published masks: only the eight priority wells change, with q = q_base + f (q_max − q_base), f = 0, 0.25, 0.5, 0.75 and 1 (baserat to maxrat) and, for maxrange, f drawn from U(0, 1) per well and realisation. In every realisation and region the published area grows monotonically from baserat to maxrat. The median area ratios fit this rule with a log rms of 0.05, against 0.36 for f × q_max (which would cut the U-cluster pumping below base at f = 0.25 while the published U area grows 1.7 times) and 0.18 for a geometric interpolation. The spread of the area in maxrange matches independent draws per well. The table footnote of the source repository says maximum rates were simulated only at the priority wells. Each realisation's own priority-well multiplier (0.93 to 1.08) was kept in the published runs, q = m (q_base + f (q_max − q_base)): on six paired realisations, R1 reproduces the masks at a median Jaccard of 0.998 (base) and 0.995 (maximum pumping) with it kept, against 0.965 and 0.967 with it replaced (`mc_masks.py`). The stage-3 runs below replace it, which changes the priority-well pumping of a realisation by −7 to +8 %. The medians in Tables 5 and 6 are expected to change little but have not been rerun. Open: the maxrange draws, which can now be estimated from each realisation's own mask but are reproduced here only in distribution.

**Runs.** The five scenarios were run on the 357 realisations that have a published mask (1,785 runs, about 20 min per scenario on six processes on an otherwise idle machine). A first pass on 60 of them gave medians within 0.2 % of these, except maxrange (2,319 against 2,362 cells), whose rates are drawn per realisation.

**Table 5. Median contributing area (start cells) against pumping**

| scenario | f | pumping (m³/d) | published | full mixing, streams as cells | full mixing, stream network |
|---|---|---|---|---|---|
| baserat | 0 | 3,663 | 998 | 911 | 1,534 |
| 0.25rat | 0.25 | 6,095 | 1,794 | 1,606 | 2,510 |
| 0.5rat | 0.5 | 8,548 | 2,475 | 2,324 | 3,455 |
| 0.75rat | 0.75 | 11,001 | 3,034 | 3,033 | 4,366 |
| maxrat | 1 | 13,453 | 3,590 | 3,709 | 5,249 |
| maxrange | U(0, 1) | 8,661 | 2,413 | 2,362 | 3,493 |

Published: median over the 357 masks of the scenario; gwsource: median sum of F over the start cells (358 realisations at base, 357 otherwise).

![Area growth](figures/neversink_area_growth.png)

*Figure 3. Median contributing area relative to base pumping. Dashed: the pumping ratio.*

With streams as cells, the full-mixing area is within 11 % of the published median in every scenario (−10 % at 0.25rat, +3 % at maxrat). It grows faster than pumping (4.07 times at 3.67 times the pumping), the published area and the network area a little slower (3.60 and 3.42 times). The stream share accounts for most of the difference (`scenarios/source_table.csv`): with streams as cells, the share of the wells' water that is stream leakage falls from 42 % at base pumping to 29 % at maxrat (median over the realisations), so the recharge the wells capture grows 4.54 times. The area per unit of captured recharge falls by 11 % over the same range, and 4.54 × 0.89 ≈ 4.06, close to the area growth. Across realisations, the excess of the area growth over the pumping growth follows the drop in stream share (r = 0.94). Against the published probability maps of the scenarios, the correlation of mean F rises from 0.80 at base to 0.82 to 0.84, and the Jaccard index of the zones above 0.5 lies between 0.48 and 0.54 (corrected masks; 0.76, 0.80 to 0.82 and 0.43 to 0.49 against the masks as stored).

**Where the stream water changes.** `studies/neversink/growth_mechanisms.py` reruns 61 realisations (60 spread evenly over the masks, and the base realisation) at base, half and maximum pumping. It saves, per SFR reach, the exchange with the aquifer and the part of the reach's leakage that reaches each well cluster under full mixing. The reruns reproduce the stage-3 values of the same realisations exactly (stream share 42 % to 29 %, area growth 4.07). A first sample of 11 realisations gives the same results within a few percent. From base to maximum pumping, the stream water reaching the wells grows from 1,506 to 3,814 m³/d (mean), 2.5 times against 3.7 times the pumping:

- 73 % of the increase is a larger share of the leakage of reaches that already lose water at base pumping.
- 5 % is more leakage from those reaches, and 22 % is the product of the two.
- 17 % of the increase comes from reaches that switch from gaining to losing (about 50 per realisation, nearly all within 2 km of a well). No losing reach switches to gaining.
- 64 % of the increase comes from reaches within 1 km (plan) of the cluster's nearest well, and 82 % from within 2 km.
- One segment south of the U wells (83 reaches, starting 206 m from them) gives 38 % of the increase. Its leakage grows by 10 %.
- The reaches 250 m to 1 km from the U wells pass 40 % of their leakage to the wells at base pumping and 60 % at maximum pumping, while their leakage grows by 18 %.

In the budget, the 9,790 m³/d of additional pumping is balanced by 8,780 m³/d less discharge to gaining reaches and 940 m³/d more leakage from losing ones (means). In terms of where the wells' water comes from, the recharge reaching the wells grows by 7,480 m³/d and the stream water by 2,310 m³/d. Most of the additional pumping is therefore recharge that discharged to streams at base pumping. Little is new stream leakage, which is why the stream share falls.

**Why the published area grows more slowly.** On the same flow fields (with RCH and SFR given an IFLOWFACE column, which does not change the flows), PRT is run from the published starts three times:

- with the published conventions (Section 3);
- the same without stopping at weak sinks, with tracks;
- with all boundary flows distributed over the cell, with tracks.

The other stopping and thinning rules are applied to the tracks afterwards. Stopping at every weak sink on the tracks gives exactly the result of the first run.

With the published conventions, PRT reproduces the published growth in distribution: the median area goes from 1,001 to 3,600 cells, growth 3.60, against 998 to 3,590 and 3.60 for the published masks. At half pumping the growth is 2.49 against 2.48. The median of the ratios per realisation is 3.55 for both. Table 6 changes one convention at a time.

**Table 6. Median contributing area at base and maximum pumping, 61 realisations**

| area | base | maxrat | growth |
|---|---|---|---|
| full mixing (F of the start cell; of the draped start cell gives the same) | 911 | 3,707 | 4.07 |
| PRT, all flows distributed, thinned at every sink | 820 | 3,696 | 4.51 |
| PRT, RCH and SFR on open top faces, thinned at the distributed sinks | 969 | 4,616 | 4.76 |
| same, stopped at stream weak sinks, thinned elsewhere | 947 | 3,600 | 3.80 |
| same, stopped at every weak sink (the published conventions) | 1,001 | 3,600 | 3.60 |
| published masks (357) | 998 | 3,590 | 3.60 |

PRT rows: particles from the published starts, seeded where F > 0. Thinned: the gross accounting of `gwsource.prt`. The areas are the sum of the captured weight or the number of captured particles.

The published area grows more slowly mainly because the particles stop at stream cells that are weak sinks (4.76 to 3.80):

- The stops remove captured weight equal to 34 contributing cells at base, 519 at half and 993 at maximum pumping (means).
- All of it is at SFR reaches under an active cell, where the stream flow is a distributed sink: 85 % in layer 2 and 90 % 1 to 4 km from the nearest well.
- The capture zone reaches these cells only at higher pumping. Under full mixing or thinning they pass on all but the stream's share of their outflow; under the published convention every particle that enters them stops.

Stopping at the remaining weak sinks, mainly the well cells that take only part of their cell's outflow, counts those cells as fully captured. This raises the base area by 54 cells and leaves the maximum one unchanged, because at maximum pumping seven of the eight wells take all of their cell's outflow (3.80 to 3.60). The restriction to start cells plays no part: 96 % of the wells' water enters in start cells in every scenario, and draping changes the full-mixing area by less than one cell. Going from full mixing to thinned particles raises the growth (4.07 to 4.51 with distributed flows, 4.76 with the top-face convention); why was not examined.

Against the published Monte Carlo masks, corrected and paired (Section 6), the R1 mask of each of the 60 realisations matches its own mask best in every scenario. The median Jaccard index is 0.996 at base, 0.969 at half and 0.965 at maximum pumping, against 0.75 to 0.83 for the second-best mask. The lower values at higher pumping come from the replaced well multiplier: with it kept, the maximum-pumping value is 0.995.

## 8. Limitations and open points

- The published Monte Carlo masks lie one row south of their cells, and the order that pairs them with the realisations (text-sorted run names) is inferred, because the step that wrote them is not archived (Section 6). The inference is strong: with both corrections, PRT with the published conventions matches every tested realisation's own mask, at 0.989 to 1.000 at base. The stage-2 and stage-3 code still reads the masks as stored (`ensemble_run.read_mask`), and the stage-3 runs replace the realisations' priority-well multiplier, which the published runs kept; neither is rerun yet.
- Why particles thinned at sinks give a faster area growth than full mixing (4.51 against 4.07 from base to maximum pumping, Table 6) was not examined.
- `baserat.zip` contains 357 masks against 358 realisations: the base realisation, the last row of the parameter table, has no mask.
- The scenario rule is inferred (Section 7); maxrange is reproduced in distribution only (its median area depends on the draws: 2,319 cells on 60 realisations, 2,362 on 357).
- The comparison is on the uppermost active layer. Contributing areas in deeper layers are not compared.
- MF6 PRT (6.9.0 development build) aborts (SIGILL) when a particle is in a cell wet only by a film so thin that the cell top PRT computes, bottom + saturation × thickness, rounds to the bottom in double precision. PRT then divides by a zero thickness (MethodDis `load_cell`, from the backtrace; the line is inferred from the source), and the build traps floating-point division by zero, which macOS arm64 reports as SIGILL. This happens for a particle released in such a cell and for one flowing into it, even alone. In the calibrated model two cells qualify, among them the one published start left out (saturation 1.4e-16, bottom 403 m, thickness 35.6 m). `growth_mechanisms.py` leaves out starts with saturation below 1e-10 (132 starts over 183 runs; no table changed against runs that tracked them); this does not protect particles that flow into a film cell, which did not happen in these runs. The abort in realisation 443 at maxrat (films of 1.3e-15 to 1.3e-13) was not traced to a cell. `studies/neversink/prt_film_repro/` holds a five-cell reproducer and a draft upstream issue: the abort threshold equals the rounding limit (saturation 2.84e-15 at a 300 m bottom, 5.68e-15 at 1,000 m, 10 m cell; none at a 0 m bottom), and setting the film cell's DATA-SAT to 0 in a copy of the budget file avoids it. Not yet reported upstream.

## Reproducing

```
python studies/neversink/workflow.py
```

Stage 1 is `workflow.py`; the ensemble and the scenarios need `python studies/neversink/pest_rebuild.py` (about 3 min, rebuilds the interface) and then `python studies/neversink/ensemble_run.py` (about 3 h on 6 processes on an idle machine, longer under load: 76 min for the base ensemble, 102 min for the five scenarios; resumable; outside the Claude Code sandbox, which blocks process pools). `python studies/neversink/growth_mechanisms.py` reruns a sample at base, half and maximum pumping with the per-reach volumes and the three PRT runs (about 80 s per run on one process; 11 realisations in 10.5 min and, with `main(sample_n=60, out=...)`, 61 realisations in 59 min on six processes; resumable; output in `output/scenarios/mechanisms/` and `mechanisms60/`). In each script the gates in `__main__` select the parts to run; in `workflow.py` they are the two MF6 runs, the MODPATH comparison, the PRT checks, the PRT source split by well, the PRT diagnosis (off by default), the PRT reproduction of the published mask and the figures. The two MF6 runs take 44 s and 75 s. The two PRT runs released at four heights (488,448 particles) take about 13 minutes each and write a track file of about 6 GB; the two single-height runs (122,112 particles) take about 5 minutes and 1.5 GB. The source split by well is one more run released at four heights. The PRT diagnosis runs PRT once per release mode (water table, mid-cell, four heights) and evaluates both capture rules on the same tracks; it took 8 minutes on an otherwise idle machine. The reproduction of the published mask builds a copy of the model with IFLOWFACE (MF6 15 s) and runs PRT five times (about 30 s each; only termination records are written), about 3 minutes in all. The workflow deletes the track files after use. Output goes to `studies/neversink/output/`, which is not tracked by git. The USGS repository goes in `studies/neversink/external/neversink_workflow/` (also not tracked) as a sparse checkout:

```
git clone --filter=blob:none --sparse https://github.com/usgs/neversink_workflow.git studies/neversink/external/neversink_workflow
cd studies/neversink/external/neversink_workflow
git sparse-checkout set neversink_optimal output/neversink_mf6_optimal_output \
  output/neversink_mp7_optimal_output output/modpath_mc output/parallel scripts \
  notebooks_workflow_complete neversink_mf6 processed_data python_packages_static
```

## References

Black & Foley (2013) [BF13]; Foley & Black (2013) [FB13]; full entries in `references/bibliography.md`. Pollock (2016) [POL16] for MODPATH 7.

[COR22] Corson-Dosch, N.T., Fienen, M.N., Finkelstein, J.S., Leaf, A.T., White, J.T., Woda, J. & Williams, J.H. (2022). *Areas contributing recharge to priority wells in valley-fill aquifers in the Neversink River and Rondout Creek drainage basins, New York.* USGS Scientific Investigations Report 2021–5112, 50 p. https://doi.org/10.3133/sir20215112

[FIE21] Fienen, M.N., Corson-Dosch, N.T., White, J.T., Leaf, A.T. & Hunt, R.J. (2021). Risk-based wellhead protection decision support: a repeatable workflow approach. *Groundwater*. https://doi.org/10.1111/gwat.13129

Model, workflow and data: U.S. Geological Survey, `github.com/usgs/neversink_workflow` (public domain, CC0-1.0) and its data release, doi 10.5066/P9HWSOHP.
