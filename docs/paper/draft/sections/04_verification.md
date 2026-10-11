# 4. Verification and Transient Demonstration

## 4.1 Steady and snapshot checks

The ten test models are small MODFLOW 6 models built with FloPy (Bakker et al. 2016; Hughes et al. 2024). Model 1 is one steady layer with recharge, a pumping well, a river and a constant-head edge; the others add a weak-sink well in three layers (model 2), DISV and DISU grids (3, 4), flow loops from XT3D (5), storage (6), SFR with MVR (7), MAW (8), LAK and UZF (9), and model 1's flows held constant over 120 steps (10). <!-- tests/models/ builders; verification_table.csv notes --> Fig. 2 shows the largest error of each check; values and error measures are in {SI: verification errors per check and model}.

[[Figure 2]]

The closure, forward–backward and boundary-control checks (Section 2.5) are exact identities, so their errors measure round-off: at most 1.8 × 10⁻¹⁵ on every model, including model 6 traced as snapshots. <!-- verification_table.md, largest error per check --> Net accounting reproduces the worked example of Foley and Black (2013) exactly, DISU versions of model 1 give the DIS results exactly, and simulations split into two to four models with the FloPy model splitter (Hughes et al. 2024) agree with the single model to ≤ 7.4 × 10⁻¹⁰, the solver tolerance. <!-- verification_table.md; README_method.md Fig. 2 caption ("split into 2 to 4 models"); evidence: studies/paper/verification.py; tests/test_multimodel.py labels_for (models 1, 3 and 6 into three, two and four models) -->

GWT, run to equilibrium with upstream advection and no dispersion, removes water through sinks at the cell's concentration, as gross accounting does; its unit concentration equals the steady forward fraction G to ≤ 2.8 × 10⁻¹¹ on models 1 and 2, including the weak-sink well. <!-- verification_table.csv (steady_g_vs_gwt) --> On model 7 the difference, 1.0 × 10⁻⁸, is limited by the flow solver tolerance; with the flow model solved about 100 times tighter it falls to 2.5 × 10⁻¹¹. <!-- verification_table.csv note (m7_mover) -->

Weight-losing PRT particles (Section 3.2) delivered the well inflow to within 0.6 %, a release-point error. <!-- verification_table.csv (prt_capture: 800.4 of 800, 402.6 of 405 m³/d) --> On model 1 the flow-weighted mean time for the water reaching the well to enter its cell is 9,574 d, against 9,590 d for the particles, which stop on entering it ({SI: travel-time identity}). <!-- PLAN Phase 3 notes; tests/test_prt.py -->

## 4.2 Transient tracking checks

With GWT's water volumes ("gwt"), transient tracking matched GWT to round-off: ≤ 2.2 × 10⁻¹⁵ on model 6 and ≤ 1.0 × 10⁻¹⁴ on model 7. <!-- verification_table.csv (tracking_vs_gwt) --> Forward transient tracking and backward tracking in time (Section 2.9) gave the same tagged volumes to ≤ 7.7 × 10⁻¹⁶ on models 6, 7 and 9, with both volume options. <!-- verification_table.csv (tracking_duality) -->

With the default "flow" volumes, each cell's water balance holds by construction, so its error (≤ 9.5 × 10⁻¹⁷) tests only bookkeeping and round-off, not the flow solution; the tagged-water balance tests the transient tracking itself, and closed to ≤ 1.0 × 10⁻¹⁵. <!-- verification_table.csv (water_balance, tagged_balance); README_method.md error measures -->

On model 10, c at the end matched the steady G to 9.7 × 10⁻¹⁴ and w at the start matched the steady F to 6.8 × 10⁻¹⁰, although c at the start differs from G by at least 0.40 and w at the end differs from F by at least 0.52. <!-- verification_table.csv (m10_constant) --> Both are limited by the flow solver tolerance: with the flow model solved 100 times tighter they fall to 1.2 × 10⁻¹⁴ and 1.4 × 10⁻¹¹. <!-- verification_table.csv notes -->

## 4.3 Numerical dispersion

Numerical dispersion, the spreading of a traced area by mixing whole cells, is measured against two references (Fig. 3): the analytical capture zone of uniform flow to a well (Javandel and Tsang 1986; problem A), and PRT on a 12.5 m grid of a model-1-like aquifer (problem B), compared only west of the gaining river, where no method meets a weak sink. <!-- DS §1 --> Thresholds here are non-strict (F ≥ 0.1); Section 5 uses strict ones (F > 0.1). Maps and time-step tests are in {SI: numerical dispersion maps and time steps}.

[[Figure 3]]

The transition band (0.1 < F < 0.9) narrowed only as about $h^{0.5}$ with cell size h: halving the cell size narrowed it by about 30 %. <!-- DS Summary, §2 (fitted rates 0.4 to 0.6); 2^-0.5 = 0.71 --> The F ≥ 0.5 area stayed within 5 % of the reference area for h ≤ 50 m. The F ≥ 0.1 area contained the reference area (missing at most 0.1 %), but for h = 12.5–50 m it was 30–90 % too large in problem A and 8–16 % in problem B. <!-- DS §5; README_method.md Fig. 3 --> Face-to-face routing (Chowdhury 2016), an experimental 2D option that routes water between cell faces instead of mixing it, removed 35–70 % of the excess spreading but kept the $h^{0.5}$ rate (Section 7). <!-- DS Summary, §4 -->

## 4.4 Transient demonstration (tutorial 08)

Tutorial 08 is a synthetic, one-layer model; the paper has no transient application to a real model (Section 7). With one layer, recharge cannot form a young layer on top of old water, and the shares below are those of a vertically mixed aquifer. <!-- tutorial 08 §3 --> It has 1,600 cells of 50 m, a river 100 m from the supply well and constant heads 1.4 km west of it, and runs a 1-day steady period and then four seasons a year for 30 years (121 steps); the well pumps most in summer, when recharge almost stops. <!-- README_method.md Fig. 4 caption; tutorial 08 §1 --> Fig. 4 uses the default "flow" volumes and four transport sub-steps per flow step. <!-- README_method.md Fig. 4 notes -->

[[Figure 4]]

Snapshots (Section 2.7) give the well's water as, on average, 60 % recharge, 12 % west-edge inflow, 15 % storage release, which reaches 50 % in summer, and the rest river leakage (Fig. 4a). <!-- evidence: studies/paper/transient_figure.py (QUOTED; snapshot_shares: recharge, river, west edge and storage are the only source terms); tutorial 08 §2 --> With transient tracking, the well's water in the last season of year 1 was 95 % initial water, 3 % river leakage and under 2 % recharge; in the last season of year 30 it was 52 % initial water, 33 % recharge and 16 % river leakage (Fig. 4b). <!-- README_method.md Fig. 4 caption (four sub-steps) --> No west-edge water reached the well within 30 years; snapshots credit it from the first step. Of all water pumped so far, 98 % after 1 year, 81 % after 10 years and 68 % after 30 years was initial water. <!-- README_method.md Fig. 4a–b -->

Backward tracking in time splits the water in each cell at the start into the fractions leaving through the well or the river within 30 years and the fraction still stored (Fig. 4d–f). Unlike the steady F (Fig. 4c), the 30-year area does not reach the west edge: it is an area for a stated time horizon. With every source tagged, the well's 30-year pumping of 8.77 million m³ splits into 13.8 % river leakage, 18.5 % recharge and 67.7 % initial water. <!-- README_method.md Fig. 4 caption (1.21, 1.62, 5.94 million m³; 8,766,800 m³) and notes; tutorial 08 §5 -->

With GWT's water volumes and time steps, transient tracking matched GWT to 9.8 × 10⁻¹⁴ ({SI: transient checks on tutorial 08}). <!-- README_method.md Fig. 4 notes; tutorial 08 §§6, 8 --> With one transport step per flow step, the two volume options differed by up to 1.9 × 10⁻⁴ (forward) and 3.7 × 10⁻³ (backward), and the first-step share of new recharge nearly doubled (0.0078 against 0.0042 with 16 sub-steps). <!-- tutorial 08 §§7, 9 -->
