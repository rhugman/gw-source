# 4. Verification and Transient Demonstration

## 4.1 Steady and snapshot checks

A user needs to know that the traced numbers are right before drawing a zone from them. We tested the code on ten small MODFLOW 6 models built with FloPy (Bakker et al. 2016; Hughes et al. 2024). Model 1 is one steady layer with recharge, a pumping well, a river and a constant-head edge. The others add a weak-sink well in three layers (model 2), DISV and DISU grids (3, 4), flow loops from XT3D (5), storage (6), SFR with MVR (7), MAW (8), LAK and UZF (9), and model 1's flows held constant over 120 steps (10). <!-- tests/models/ builders (common.py, structured.py, unstructured.py, mover.py, networks.py); verification_table.csv notes --> They are described in {SI: example and test models}.

The closure, forward–backward and boundary-control checks (Section 2.5) must hold exactly on any model. Fig. 2 shows the largest error of each check (rows) on each model (markers). The dashed line is machine precision, the smallest relative difference the computer resolves. The grey bars are the tolerances of the automated tests.

[[Figure 2]]

The three exact checks held to 1.8 × 10⁻¹⁵ or better on every model, including model 6 traced as snapshots. <!-- verification_table.md, largest error per check --> Errors this close to machine precision mean that the checks passed. On a user's model, a much larger error would flag a problem with the trace.

Net accounting reproduces the worked example of Foley and Black (2013) exactly. DISU copies of model 1 give the DIS results exactly. Simulations split into two to four models (Hughes et al. 2024) agree with the single model to 7.4 × 10⁻¹⁰, the flow solver tolerance. <!-- verification_table.md; README_method.md Fig. 2 caption ("split into 2 to 4 models"); evidence: studies/paper/verification.py; tests/test_multimodel.py labels_for (models 1, 3 and 6 into three, two and four models) --> Results therefore do not depend on the grid type or on model splitting.

GWT, run to equilibrium with upstream advection and no dispersion, removes water through each sink at the cell's concentration, as gross accounting does. Its unit concentration equals the steady forward fraction G to 2.8 × 10⁻¹¹ or better on models 1 and 2, including the weak-sink well. <!-- verification_table.csv (steady_g_vs_gwt) --> <!-- verification_table.csv note (m7_mover: 1.0e-8 on model 7, flow-solver limited; given in the Fig. 2 caption and Table S1) --> A user can read G as the steady concentration of a dispersion-free tracer, without a GWT run. Weight-losing PRT particles (Section 3.2) delivered the well inflow to within 0.6 %, an error of the finite number of release points. <!-- verification_table.csv (prt_capture: 800.4 of 800, 402.6 of 405 m³/d) -->

## 4.2 Transient tracking checks

With GWT's water volumes ("gwt"; Section 2.7), transient tracking matched GWT to 2.2 × 10⁻¹⁵ on model 6 and 1.0 × 10⁻¹⁴ on the stream network of model 7. <!-- verification_table.csv (tracking_vs_gwt) --> Backward tracking in time (Section 2.8) gave the same tagged volumes as forward tracking to 7.7 × 10⁻¹⁶ or better on models 6, 7 and 9, with both volume options. <!-- verification_table.csv (tracking_duality) --> Both directions therefore rest on an independent code.

With the default "flow" volumes, each cell's water balance follows from how the volumes are carried. Its error, at most 9.5 × 10⁻¹⁷, therefore tests only the bookkeeping. The tagged-water balance, which tests the tracking itself, closed to 1.0 × 10⁻¹⁵. <!-- verification_table.csv (water_balance, tagged_balance); README_method.md error measures --> No tagged water is created or lost between steps.

When flows do not change, transient tracking should reach the steady result. Model 10 holds model 1's flows for 4 × 10⁵ d in 120 equal steps. At the end, the tagged fraction c matched the steady G to 9.7 × 10⁻¹⁴. At the start, the backward fraction in time w matched the steady F to 6.8 × 10⁻¹⁰. <!-- verification_table.csv (m10_constant) --> At the other end of the run they differ by at least 0.40 and 0.52, so the test is not trivial. <!-- verification_table.csv (m10_constant); README_method.md Fig. 2 caption --> <!-- verification_table.csv notes (both errors flow-solver limited: 1.2e-14 and 1.4e-11 with the flow model solved 100 times tighter; Fig. 2 caption, Table S1) --> The two methods agree where flows are steady, so a user can trust either.

## 4.3 Numerical dispersion

Full mixing spreads a traced area, because cells along its edge mix water bound for the well with water that is not. This numerical dispersion widens any area drawn from F. We measured it on two problems (Fig. 3). Problem A is uniform flow to a well, against the analytical capture zone (Javandel and Tsang 1986). Problem B is an aquifer like model 1, against PRT on a 12.5 m grid west of the gaining river, where no method meets a weak sink. <!-- DS §1 --> Maps and time-step tests are in {SI: numerical dispersion maps and time steps}.

[[Figure 3]]

A contributing area is the set of cells above a threshold on F, the share of a cell's water that ends at the well. The F ≥ 0.5 area holds the cells where at least half the water ends at the well. The F ≥ 0.1 area, every cell that sends at least a tenth, is meant as a cautious outer limit. Section 5 writes them as F > 0.5 and F > 0.1, which give the same areas here ({SI: numerical dispersion maps and time steps}). <!-- studies/dispersion/output/a_maps.npz, b_maps.npz: no full-mixing value equal to 0.1 or 0.5 (to 1e-12); counted in round 4; details in si/C.md -->

The transition band, the edge cells with 0.1 < F < 0.9, narrowed only as about $h^{0.5}$ with cell size h. Halving h narrowed it by about 30 %. <!-- DS Summary, §2 (fitted rates 0.4 to 0.6); 2^-0.5 = 0.71 --> The F ≥ 0.5 area stayed within 5 % of the reference area for h ≤ 50 m. The F ≥ 0.1 area contained the reference area (missing ≤ 0.1 %). For h = 12.5–50 m, it was 30–90 % too large in problem A and 8–16 % in problem B. <!-- DS §5; README_method.md Fig. 3 --> <!-- face-to-face routing (DS Summary, §4) now in the Fig. 3 caption and Section 7 -->

## 4.4 Transient demonstration

The seasonal example model, a synthetic model, shows what transient tracking adds to snapshots (Section 2.7). The paper has no transient application to a real model (Section 7).

The model has one layer of 40 × 40 cells of 50 m. Constant heads on the west edge, 1.4 km from the supply well, bring regional inflow. A river runs 100 m east of the well. Recharge averages 0.18 m/yr, with 1.8 times the mean in winter and 0.1 times in summer. The well pumps 800 m³/d on average and 1,120 m³/d in summer. Specific yield is 0.2 and porosity 0.3. A 1-day steady period, with the well already pumping, is followed by 30 years of four seasons (121 steps). <!-- tutorials/herebedragons.py (AquiferSpec: 40 x 40 cells of 50 m, rech 5e-4 m/d, riv_col 30, supply_well (20, 28) -800 m3/d; build_transient: sy 0.2; SEASON_RECHARGE (1.8, 1.0, 0.1, 1.1), SEASON_PUMPING (0.8, 1.0, 1.4, 0.8)); tutorials/08_transient_tracking/08_transient_tracking.ipynb settings (N_YEARS 30, STEPS_PER_SEASON 1, POROSITY 0.3); README_method.md Fig. 4 caption --> With one layer, recharge cannot form a young layer on top of old water. <!-- tutorial 08 §3 -->

[[Figure 4]]

On average, snapshots give the well's water as 60 % recharge, 12 % west-edge inflow and 15 % storage release, with river leakage the rest (Fig. 4a). Storage release reaches 50 % in summer. <!-- evidence: studies/paper/transient_figure.py (QUOTED; snapshot_shares: recharge, river, west edge and storage are the only source terms); tutorial 08 §2 -->

With transient tracking, the well's water in the last season of year 30 was 52 % initial water, 33 % recharge and 16 % river leakage (Fig. 4b). <!-- README_method.md Fig. 4 caption (four sub-steps) --> No west-edge water arrived within 30 years. Of all water pumped so far, initial water made up 98 % after 1 year, 81 % after 10 years and 68 % after 30 years. <!-- README_method.md Fig. 4a–b --> This share tells a manager how much of the pumped water was already stored in the aquifer at the start. Snapshots and particles do not give it directly.

Backward tracking in time gives, for the water in each cell at the start, the fractions that leave through the well or the river within 30 years and the fraction still stored (Fig. 4d–f). Unlike the steady F (Fig. 4c), the 30-year area does not reach the west edge. It is an area for a stated time horizon. The well's 30-year pumping splits into 13.8 % river leakage, 18.5 % recharge and 67.7 % initial water. <!-- README_method.md Fig. 4 caption (1.21, 1.62, 5.94 million m³; 8,766,800 m³) and notes; tutorial 08 §5 -->

On this model, transient tracking matched GWT to 9.8 × 10⁻¹⁴ ({SI: transient checks on the seasonal example model}). <!-- README_method.md Fig. 4 notes; tutorial 08 §§6, 8 --> <!-- sub-step and volume-option numbers (tutorial 08 §§7, 9) moved to si/C.md Text S4 -->
