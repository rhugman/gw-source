# 4. Verification and Transient Demonstration

## 4.1 Steady and snapshot checks

The test models are small MODFLOW 6 models built with FloPy (Bakker et al. 2016; Hughes et al. 2024). Model 1 is one steady DIS layer with recharge, a pumping well, a river and a constant-head west edge; model 2 has three layers and a weak-sink well. Models 3 to 5 are model 1 on a Voronoi DISV grid, on a DISU grid (with and without cell vertices) and with XT3D, which creates flow loops; model 6 is model 1 with storage (13 time steps). Models 7 to 9 add package networks: drains feeding an SFR stream through MVR (7), a MAW well screened in three layers (8), and two lakes with UZF cells (9). Model 10 holds model 1's steady flows for 4 × 10⁵ d in 120 equal steps. <!-- tests/models/ builders (structured.py, mover.py, networks.py); verification_table.csv notes (13 steps; 121 steps = 1 + 120) --> Table 2 and Fig. 2 give the largest error per check (Table S4: per model).

[[Figure 2]]

[[Table 2]]

The closure, forward–backward and boundary-control checks (§2.5) are exact identities, so their errors measure round-off: at most 1.8 × 10⁻¹⁵ on every model, including model 6 as snapshots and the networks of models 7 to 9. <!-- verification_table.md, largest error per check --> Net accounting reproduces the worked example of Foley and Black (2013) exactly. DISU builds of model 1 give the DIS results exactly, and simulations split into two to four models [check: model splitter reference] agree with the single model to ≤ 7.4 × 10⁻¹⁰, the MF6 solver tolerance. <!-- verification_table.md; README_method.md Fig. 2 caption -->

The steady forward fraction G tests gross accounting against an independent code. MF6 GWT (Langevin et al. 2022), run to equilibrium (10⁷ d) on the steady flows with upstream advection and no dispersion, lets water leave through a sink term at its cell's concentration, as gross accounting does. G equals the GWT unit concentration to ≤ 2.8 × 10⁻¹¹ on models 1 and 2, including a weak-sink well. <!-- verification_table.csv (steady_g_vs_gwt); PLAN Phase 4B notes --> On model 7 the difference is 1.0 × 10⁻⁸, limited by the flow solve: with the flow model solved about 100 times tighter it falls to 2.5 × 10⁻¹¹. <!-- verification_table.csv note (m7_mover) -->

Weight-losing PRT particles (§3.2) delivered 800.4 of the 800 m³/d well inflow on model 1 and 402.6 of 405 m³/d on model 2, a release-point error (from the finite number of release points) below 0.6 %. <!-- verification_table.csv (prt_capture) --> On model 1 the full-mixing mean travel time to the well cell (§2.6) is 9574 d, against 9590 d for the particles. <!-- PLAN Phase 3 notes; tests/test_prt.py -->

## 4.2 Transient tracking checks

With "gwt" volumes, forward tracking is upstream, dispersion-free unit-concentration transport in MF6 GWT (§2.8), so GWT checks it directly. The tagged fraction c matched GWT at every step to ≤ 2.2 × 10⁻¹⁵ on model 6 (five tagging cases, including initial water) and to ≤ 1.0 × 10⁻¹⁴ in the cells and reaches of model 7. <!-- verification_table.csv (tracking_vs_gwt); outline §5.4 --> Forward tracking and backward tracking in time (§2.9) gave the same tagged volumes to ≤ 7.7 × 10⁻¹⁶ on models 6 (also with five transport sub-steps), 6 split into four models, 7 and 9, with both volume options. <!-- verification_table.csv (tracking_duality) -->

The two "flow"-volume balances test different things. Each cell's water balance holds by construction, because the volume is carried on by the storage flows; its error, ≤ 9.5 × 10⁻¹⁷ of the water volume, tests the volume carry, the clipping of volumes at zero and round-off, not the flow solution. The tagged-water balance of each group tests the tracking solve, and closed to ≤ 1.0 × 10⁻¹⁵. <!-- verification_table.csv (water_balance, tagged_balance); README_method.md error measures -->

On model 10, c at the end matched the steady G to 9.7 × 10⁻¹⁴, and w at the start matched the steady F to 6.8 × 10⁻¹⁰; at the other end of the run they differ by at least 0.40 and 0.52. <!-- verification_table.csv (m10_constant) --> Both errors are limited by the flow solver tolerance, not by round-off: with the flow model solved 100 times tighter they fall to 1.2 × 10⁻¹⁴ and 1.4 × 10⁻¹¹. <!-- verification_table.csv notes --> Three transport sub-steps equal a flow model with three times as many steps of the same flows to 1.6 × 10⁻¹⁶ (a hand-built 15-cell network). <!-- verification_table.csv (substeps) -->

## 4.3 Numerical dispersion

Numerical dispersion is the spreading of a traced area caused by mixing whole cells: water entering a cell leaves through all its outflow faces, whatever face it came in by. We measure it against two references, delineations taken as correct for the comparison (Fig. 3): the analytical capture zone of uniform flow to a well (Javandel and Tsang 1986; problem A), and PRT on a 12.5 m grid of a model-1-like aquifer (problem B), compared west of the river, where no method mixes at the gaining river. <!-- DS §1 --> These tests use non-strict thresholds (F ≥ 0.1); the Neversink comparison of §5 uses strict ones (F > 0.1). <!-- terms.md (core, envelope); DS §5; NS §2 -->

[[Figure 3]]

The transition band (0.1 < F < 0.9), the edge cells where F is neither near 0 nor near 1, narrowed only as about $h^{0.5}$ with cell size h. <!-- DS Summary, §2 --> The F ≥ 0.5 area was within 5 % of the reference area for h ≤ 50 m. The F ≥ 0.1 area contained the reference zone in every run (missing at most 0.1 %) but was 8 to 90 % too large for h = 12.5 to 50 m. <!-- DS §5; README_method.md Fig. 3 caption --> Face-to-face routing (Chowdhury 2016), an experimental 2D option that routes water between cell faces instead of mixing it across the cell, removed 35 to 70 % of the excess spreading but kept the rate (§7). <!-- DS Summary, §4 -->

Long time steps add numerical dispersion in time. With problem B's flows held for 2000-day flow steps, one transport step per flow step roughly doubled the share of new water reaching the well in the first step (0.18 against 0.09 for particles); 16 sub-steps (125 d) removed this. <!-- DS §3 and its sub-step table -->

## 4.4 Transient demonstration (tutorial 08)

Tutorial 08 is a synthetic model; the paper has no transient application to a real model (§7). Its one layer has 1,600 cells (50 m), specific yield 0.2 and porosity 0.3, a river 100 m east of a supply well, and constant heads on the west edge, 1.4 km away. A 1-day steady period is followed by four seasons a year for 30 years (121 steps), with little recharge in summer, when pumping peaks at 1,120 m³/d. <!-- README_method.md Fig. 4 caption; tutorial 08 §1 --> The well pumps from the start. Fig. 4 uses the default "flow" volumes and four transport sub-steps per flow step. <!-- README_method.md Fig. 4 notes; studies/paper/transient_figure.py -->

[[Figure 4]]

Snapshots (§2.7) give the well's water as, on average, 60 % recharge, 12 % west-edge inflow and 15 % storage release, which reaches 50 % in summer (Fig. 4a). Tracked forward, the well's water in the last season of year 1 was 95 % initial water, 3 % river leakage and under 2 % recharge, and in year 30 52 % initial water, 33 % recharge and 16 % river leakage (Fig. 4b). <!-- README_method.md Fig. 4 caption (four sub-steps) --> No west-edge water reached the well within 30 years; snapshots, with no travel lag, credit it from the first step. <!-- README_method.md Fig. 4a–b caption --> Of all water pumped so far, 98 % after 1 year, 81 % after 10 years and 68 % after 30 years was in the aquifer at the start. <!-- README_method.md Fig. 4b caption --> Snapshots cannot give these numbers.

Backward tracking in time gives, for the water in each cell at the start, the fractions that leave through the well within 30 years, leave through the river or are still stored (Fig. 4d–f); they add up to 1 in every cell. Unlike the steady F of the first step (Fig. 4c), the 30-year zone does not reach the west edge. With every source tagged, the well's 30-year pumping of 8,766,800 m³ splits into 13.8 % river leakage, 18.5 % recharge and 67.7 % initial water, with a closure error of 0; the initial-water share equals the forward cumulative share. <!-- README_method.md Fig. 4 caption (1.21, 1.62, 5.94 million m³) and notes; tutorial 08 §5 -->

Forward and backward tracking agreed to ≤ 4.3 × 10⁻¹⁶ per tag. With "gwt" volumes and GWT's own stepping, the tracked recharge fraction matched a GWT run on the same flows to 9.8 × 10⁻¹⁴. <!-- README_method.md Fig. 4 notes; tutorial 08 §8 --> The two volume options differed by up to 1.9 × 10⁻⁴ in the forward and 3.7 × 10⁻³ in the backward fraction. <!-- tutorial 08 §7 --> One transport step per 91-day flow step nearly doubles the share of new recharge in the first step (0.0078 against 0.0042 with 16 sub-steps); from four sub-steps to 16, the year-1 shares move by at most 0.2 percentage points. <!-- tutorial 08 §9; README_method.md Fig. 4 caption -->

The model has one layer, so each cell mixes over its whole saturated thickness and recharge cannot form a young layer on top of old water. This vertical mixing is a form of numerical dispersion, and the shares above are those of a vertically mixed aquifer. <!-- tutorial 08 §3 -->
