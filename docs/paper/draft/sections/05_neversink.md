# 5. Demonstration and Benchmark: the Neversink Model

The Neversink/Rondout model is steady state, so this section demonstrates the steady method: (i) cost on 1.68 million cells and a 358-realisation ensemble, (ii) the closure check, (iii) gross and net accounting at real weak-sink wells, (iv) the stream network and (v) how full mixing compares with a published particle delineation, and which particle conventions account for the differences. <!-- NS §1, §6; outline §5.5 --> The published areas are a benchmark, not a reference: they are one particle convention.

## 5.1 Model and benchmark

The USGS Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022) has 4 layers of 680 × 619 cells of 50 m and 12,316 SFR reaches (Fig. 5). <!-- NS §1 --> Rerun with MODFLOW 6 version 6.9, the model reproduces the published heads within 8.6 mm. <!-- NS §1 Checks; mf6_runs.csv -->

[[Figure 5]]

The benchmark is the published MODPATH 7 (Pollock 2016) delineation for eight priority wells, which pump 3,671 m³/d in all. <!-- NS §1 --> One particle starts in each uppermost active cell of three regions (the start cells; 122,021 particles), and particles are stopped at every weak sink: a particle ends in the first weak-sink cell it enters, credited in full to that cell's sink. <!-- NS §1, §2 --> The published contributing cells are the 980 start cells whose particle ends in a priority well. <!-- NS §1, §2; mp7_status.csv --> All comparisons are made on the start cells, where 96 % of the wells' water enters the model. <!-- NS §2 Coverage; mp7_coverage.csv --> A trace of nine destination groups (each well and the eight together) took 2 to 3 s, against 44 s for the MODFLOW 6 run, and the closure check (§2.5) held to 1e-12 m³/d or less for every group. <!-- NS Summary, §1, §4; checks_cells.csv (2.3 s), checks_sfr_network.csv (2.6 s); mf6_runs.csv -->

## 5.2 Calibrated model against the published cells

Agreement is measured by the overlap: cells in both areas as a share of cells in either (the Jaccard index). The full-mixing contributing area is the start cells with F > 0.1 or F > 0.5, or the area-matched set, the 980 start cells with the largest F; its expected area is the sum of F over the start cells, in cells. With gross accounting (§2.3), the overlap is 0.30 for F > 0.1 and 0.41 for F > 0.5 and the area-matched set, and the expected area is 910 cells against 980 published (Fig. 6a–c; Table 3; per well, Table S4). <!-- NS §2, Table 1; agreement_with_mp7.csv; net_vs_gross_mp7.csv --> The F > 0.5 area is a core: 94 % of its 445 cells are published cells, covering 43 % of the published area. <!-- NS §2, Table 1 --> The F > 0.1 area is about twice the published area and still misses 27 % of it. <!-- NS §2, §5 -->

[[Figure 6]]

[[Table 3]]

Part of the difference lies at weak sinks. The well of U___7 takes 44 % of its cell's outflow; a published particle that enters the cell stops there, while full mixing passes the rest of the water downstream. <!-- NS §2; net_vs_gross_wells.csv --> Buried stream cells, SFR reach cells with an active cell above, also stop particles where the reach gains from the aquifer, because the stream exchange stays distributed in the cell; open-top stream cells let particles leave through the top face (Text S3). Net accounting (§2.3) credits the eight wells with 3,944 m³/d against 3,671 m³/d pumped, and U___7 with 2.26 times its pumping, and gives an expected area of 978 cells (Table 3; Table S5). <!-- NS §2, Tables 2a–2b; net_vs_gross_wells.csv, net_vs_gross_mp7.csv -->

## 5.3 Particle tracking on the same flow field

We ran PRT on the same flow field, with flow-weighted release from the source terms of every cell with F > 10⁻⁶. Weight-losing particles delivered 3,736 m³/d against a well inflow of 3,671 m³/d (+1.8 %; 0.0 to +1.8 % over five release layouts, with no trend in particle number) [check: the five-layout scripts are not in the repository]. <!-- NS §3, Table 3; prt_comparison.csv; outline §7 item 1 --> Plain particles, which lose weight only to the wells, delivered 2.6 times the inflow. <!-- NS §3, Table 3; prt_comparison.csv (9,555 m³/d) --> Stream leakage is 43 % of the wells' water under full mixing and 51 % along the particle paths. <!-- NS §3; prt_sources_by_well.csv -->

The particle share P is the flow-weighted share of the water released in a cell that particles deliver to the wells. For start cells with P > 0.5, the overlap with the published cells is 0.29 to 0.62, depending on weight loss and release depth; full mixing (0.30 to 0.41) lies inside this range (Fig. 7). <!-- NS §3, Table 3; agreement_with_mp7.csv -->

[[Figure 7]]

PRT reproduces the published cells only with the published particle conventions: recharge and stream flows on the top face where it is open, set through IFLOWFACE (the cell face a boundary flow is assigned to); particles stopped at every weak sink; and draping (MODPATH DrapeOption), which moves a particle starting in a dry cell down to the first active cell below. With these, 99.0 % of particles end in the same cell as published and the overlap is 0.998. <!-- NS §3 reproduction table; mp7_reproduction.csv --> With MODFLOW 6's default distributed boundary flows it is 0.62 to 0.65; the face assignment alone raises it from 0.65 to 0.998. <!-- NS §3 reproduction table; mp7_reproduction.csv -->

Two caveats apply to the comparison with the weight-losing PRT zone P > 0.5, the particle reference of §4.3: PRT was seeded only where F > 10⁻⁶, so coverage is an upper bound, and weight-losing particles lose weight at sinks as full mixing does, so the test covers only the spreading between sinks. <!-- NS §5, Table 3a; envelope_prt_notes.csv --> Within these, F > 0.1 covers 87 % of the PRT zone, and 92 % of the F > 0.5 area lies inside it (Table S6). <!-- NS §5, Table 3a; envelope_prt.csv --> The gap to the published cells is therefore mixing against advective paths, plus documented particle conventions.

## 5.4 Streams as cells and as a stream network

With streams as cells, SFR leakage is a source term of the aquifer cell and tracing stops at the stream; the stream share of the wells' water is 43 % (Fig. 6a–c). <!-- NS §4; sources_cells.csv --> With the stream network, the 12,316 SFR reaches are added as extra cells linked by stream routing, so leakage is traced up the stream to where its water entered. All the wells' water then traces to recharge, and the contributing area extends upstream along the streams (Fig. 6d–f). <!-- NS §4; sources_sfr_network.csv --> The network's 8 flow loops were solved exactly, in a 2.6 s trace. <!-- NS §4; checks_sfr_network.csv --> Over the ensemble (§5.5–5.6), the median area with the stream network is 1,534 against 911 cells at base pumping and 5,247 against 3,725 at maximum pumping, and mean F gives 1.51 times the published expected area. <!-- NS Tables 4–5; scenarios/area_table.csv; ensemble/probability_comparison.csv -->

## 5.5 Ensemble at base pumping

We rebuilt the published PEST interface and traced all 358 realisations of the published ensemble in 76 min on six processes, with closure to 3e-12 m³/d in each. <!-- NS §6; ensemble/summary.csv --> The published Monte Carlo contributing areas lie one row south of their cells and are stored in run numbers sorted as text; we inferred both offsets (Text S4). With both corrected, PRT with the published conventions matches each of the 60 realisations tested, at a median overlap of 0.996. <!-- NS §6; scenarios/mechanisms60/mask_matches.csv -->

The published probability of contribution is the share of the 357 published Monte Carlo contributing areas that contain a cell. Mean F correlates with it at r = 0.80 and gives 90 % of its expected area, and the zones above 0.5 overlap at 0.48 (Fig. 8; Table S1). <!-- NS §6, Table 4; ensemble/probability_comparison.csv --> Where the zones differ, the published probability follows narrow paths, which we read as single-particle paths through cells that send most of their water elsewhere under full mixing; this reading is untested. In the S region the published area varies between realisations (coefficient of variation 32 %); PRT with the published conventions follows it (r = 0.997) and the sum of F does not (r = 0.00). <!-- NS §6 --> There, the variation comes from the particle conventions.

[[Figure 8]]

## 5.6 Pumping scenarios

We inferred the scenario rule, which raises pumping at the priority wells only, from the published Monte Carlo areas (Text S4). With streams as cells, the median full-mixing area is within 10 % of the published median at every rate (Fig. 9; Table S2). <!-- NS §7, Table 5; scenarios/area_table.csv --> It grows 4.09 times while pumping grows 3.68 times and the published area 3.60 times. <!-- NS §7; scenarios/area_table.csv -->

[[Figure 9]]

The faster growth comes mainly from the stream share, which falls from 42 % to 28 % (medians), so the recharge reaching the wells grows 4.57 times. <!-- NS §7; scenarios/source_table.csv --> Across realisations, the excess of area growth over pumping growth follows the drop in stream share at r = 0.94 (Fig. 10). <!-- NS §7; figures/README.md Fig. 10 --> Of the increase in stream water reaching the wells, 72 % is a larger share of the leakage of reaches already losing at base pumping and 18 % comes from reaches that switch to losing. <!-- NS §7; mechanisms60/stream_by_state.csv --> Most of the extra pumping is recharge that discharged to streams at base pumping.

[[Figure 10]]

PRT with the published conventions reproduces the published growth (3.62). <!-- NS §7, Table 6; mechanisms60/growth_decomposition.csv --> Changing one convention at a time, stopping particles in buried stream cells cuts the growth from 4.76 to 3.83, because the capture zone reaches these cells only at higher pumping (Table S3). <!-- NS §7, Table 6; mechanisms60/growth_decomposition.csv, stream_stops.csv --> Weight-losing particles grow faster than full mixing; we infer, without tracing it cell by cell, that at base pumping the leakage of reaches near the U wells stays on flow lines ending in the wells, while full mixing gives it the average fate of the cells' outflow (Text S5).
