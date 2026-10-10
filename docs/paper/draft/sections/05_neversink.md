# 5. Demonstration and Benchmark: the Neversink Model

The published Neversink contributing areas are a benchmark, not a reference: they come from one particle convention, and we use them to explain differences between methods. The model is steady state, so this section demonstrates the steady method only: (i) cost on 1.68 million cells and a 358-realisation ensemble, (ii) the closure check, (iii) gross and net accounting at weak-sink wells, (iv) the stream network and (v) a comparison with particle tracking. <!-- NS §1, §6; outline §5.5 -->

## 5.1 Model and benchmark

The USGS Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022) has four layers of 680 × 619 cells of 50 m and 12,316 SFR reaches; rerun with MODFLOW 6 version 6.9, it reproduces the published heads within 8.6 mm. <!-- NS §1 and Checks; mf6_runs.csv --> The benchmark is the published MODPATH 7 (Pollock 2016) delineation for eight priority wells, which pump 3,671 m³/d and form three clusters (U, SV_W and SV_S) in three regions (NE, W and S; Fig. 5). <!-- NS §1; figures/README.md Fig. 5 --> One particle starts in each uppermost active cell of the three regions (the start cells; 122,021 particles) and stops in the first weak-sink cell it enters, credited in full to that cell's sink. <!-- NS §1, §2 --> The published contributing cells are the 980 start cells whose particle ends in a priority well. <!-- NS §1, §2; mp7_status.csv -->

[[Figure 5]]

Comparisons are made on the start cells, where 96 % of the wells' water enters the model. <!-- NS §2 Coverage; mp7_coverage.csv --> A trace of nine destination groups (each well and all eight) took 2–3 s, against 44 s for the MODFLOW 6 run, and the closure check (§2.5) held to 1 × 10⁻¹² m³/d or less for every group. <!-- NS Summary, §1, §4; checks_cells.csv (2.3 s), checks_sfr_network.csv (2.6 s); mf6_runs.csv -->

## 5.2 Calibrated model against the published contributing cells

The overlap, the cells in both areas as a share of those in either (the Jaccard index), measures agreement with one particle convention, not accuracy: PRT on the same flow field gives 0.29–0.998, depending on its conventions (§5.3). <!-- NS §3, Table 3 and reproduction table; prt_comparison.csv, mp7_reproduction.csv --> Full mixing lies inside this spread. With gross accounting (§2.3), the overlap is 0.30 for F > 0.1 and 0.41 for F > 0.5 and for the 980 start cells with the largest F (Fig. 6a–c; per well, {SI: per-well gross and net}). <!-- NS §2, Tables 1–2; agreement_with_mp7.csv --> The expected area, the sum of F over the start cells, is 910 cells against 980 published. <!-- NS §2, Table 1 -->

[[Figure 6]]

The F > 0.5 area is a core: 94 % of its 445 cells are published contributing cells, covering 43 % of the published area. <!-- NS §2, Table 1 --> The F > 0.1 area, 2,139 start cells or 2.2 times the published area, still misses 27 % of it. <!-- NS §2, Table 1, §5 --> Part of the difference lies at weak sinks: the well of U___7 takes 44 % of its cell's outflow, and a published particle entering the cell stops there, while full mixing passes the rest downstream ({SI: end states of the published particles}). <!-- NS §2; net_vs_gross_wells.csv --> Net accounting (§2.3) credits U___7 with 2.26 times its pumping and raises the expected area to 978 cells ({SI: net attribution and PRT-area maps}). <!-- NS §2, Tables 2a–2b; net_vs_gross_wells.csv, net_vs_gross_mp7.csv -->

## 5.3 Particle tracking on the same flow field

With flow-weighted release in every cell with F > 10⁻⁶, weight-losing PRT particles delivered 3,736 m³/d against a well inflow of 3,671 m³/d (+1.8 %). <!-- NS §3, Table 3; prt_comparison.csv --> Plain particles, which lose weight only to the wells, delivered 2.6 times the inflow ({SI: diagnosis of the first PRT runs}). <!-- NS §3, Table 3; prt_comparison.csv (9,555 m³/d) --> Stream leakage is 43 % of the wells' water under full mixing and 51 % along the particle paths. <!-- NS §3; prt_sources_by_well.csv; prt_diagnosis.csv --> The particle share P is the flow-weighted share of the water released in a cell that particles deliver to the wells; for start cells with P > 0.5, the overlap with the published contributing cells is 0.29–0.62, depending on weight loss and release depth (Fig. 7; {SI: delineations on one flow field}). <!-- NS §3, Table 3; agreement_with_mp7.csv -->

[[Figure 7]]

PRT reproduces the published contributing cells only with the published particle conventions: recharge and stream flows on the top face where it is open, set through IFLOWFACE (§3.2); particles stopped at every weak sink, including buried stream cells; and draping (MODPATH DrapeOption), which moves a particle starting in a dry cell down to the first active cell below. Buried stream cells are SFR reach cells with an active cell above; the stream exchange stays in the cell, so a gaining reach there is a weak sink. With these, 99.0 % of particles end in the same cell as published and the overlap is 0.998; with boundary flows distributed through the cell, the MODFLOW 6 default, it is 0.65 even with draping. <!-- NS §2, §3 reproduction table; mp7_reproduction.csv (0.998, 0.65 draped, 0.62 dropped), mp7_status.csv -->

For weight-losing particles released over the cell volume, the PRT area (P > 0.5) has 691 start cells. Two caveats apply: PRT was seeded only where F > 10⁻⁶, so coverage is an upper bound, and these particles lose weight at sinks as full mixing does, so only the spreading between sinks is tested. <!-- NS §5, Table 3a; envelope_prt_notes.csv --> Within these caveats, F > 0.1 covers 87 % of the PRT area, missing 89 cells that receive 6 % of the water PRT delivers, and 92 % of the F > 0.5 area lies inside it ({SI: net attribution and PRT-area maps}). <!-- NS §5, Table 3a; envelope_prt.csv: 0.871, 89, 226.7 of 3,736 m³/d, 0.917 --> We attribute the gap to the published contributing cells to two things: full mixing spreads each cell's water over all its outflows, where a particle follows one path, and the published particle conventions. The PRT-area comparison supports the first only between sinks.

## 5.4 Streams as cells and as a stream network

With streams as cells, SFR leakage is a source term of the aquifer cell and tracing stops at the stream; 43 % of the wells' water enters as SFR leakage, the stream share (Fig. 6a–c). <!-- NS §4; sources_cells.csv --> With the stream network, the SFR reaches are added as extra cells linked by stream routing, so leakage is traced up the stream to where its water entered. All the wells' water then traces to recharge, and the contributing area extends upstream along the streams (Fig. 6d–f). <!-- NS §4; sources_sfr_network.csv --> The network's eight flow loops were solved exactly, in a 2.6 s trace. <!-- NS §4; checks_sfr_network.csv -->

## 5.5 Ensemble at base pumping

We rebuilt the PEST interface and traced the 358 realisations of the published ensemble, drawn from the posterior of the PEST++ iterative ensemble smoother (White et al. 2020), in 76 min on six processes, with closure to 3 × 10⁻¹² m³/d in each. <!-- NS §6; ensemble/summary.csv --> After two offsets in the stored published Monte Carlo contributing areas are corrected, PRT with the published conventions reproduces each of the 60 realisations tested (median overlap 0.996; {SI: Monte Carlo offsets and scenario rule}). <!-- NS §6; mechanisms60/mask_matches.csv: baserat median 0.9961, minimum 0.9886, 60 realisations -->

The published probability of contribution is the share of the 357 published Monte Carlo contributing areas that contain a cell. Mean F correlates with it at r = 0.80 and gives 90 % of its expected area, and the areas above 0.5 overlap at 0.48 (Fig. 8; {SI: ensemble statistics}). <!-- NS §6, Table 4; ensemble/probability_comparison.csv --> In the S region the published area varies between realisations (coefficient of variation 32 %), and PRT with the published conventions follows it (r = 0.997, 60 realisations) while the sum of F does not (r = 0.00). <!-- NS §6 --> There, the variation follows the particle conventions rather than the water reaching the wells.

[[Figure 8]]

## 5.6 Pumping scenarios

With the scenario rule inferred from the published areas, which raises pumping at the priority wells only ({SI: Monte Carlo offsets and scenario rule}), the median full-mixing area is within 10 % of the published median at every rate ({SI: scenario medians}). <!-- NS §7, Table 5; scenarios/area_table.csv --> It grows 4.09 times while pumping grows 3.68 times and the published area 3.60 times (Fig. 9), mainly because the stream share falls from 42 % to 28 %, so more of the pumping is recharge ({SI: growth mechanism}). <!-- NS §7; scenarios/area_table.csv, scenarios/source_table.csv --> PRT with the published conventions reproduces the published growth (3.62 against 3.60, 61 realisations), and the published area grows more slowly mainly because its particles stop at buried stream cells, which the area reaches only at higher pumping ({SI: one convention at a time}). <!-- NS §7, Table 6 and bullets after it; mechanisms60/growth_decomposition.csv (r1 3.622, r2_thinned 4.76, r2_streams_thinned 3.83), stream_stops.csv -->

[[Figure 9]]
