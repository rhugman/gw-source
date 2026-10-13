# 4. Verification and Transient Demonstration

## 4.1 Steady-state and snapshot checks

Before drawing a zone, a user needs to know that the trace is right. We tested the code on ten small MODFLOW 6 models built with FloPy (Bakker et al. 2016; Hughes et al. 2024). Model 1 is one steady-state layer with recharge, a pumping well, a river and a constant-head edge. The others add a weak-sink well in three layers (model 2), DISV and DISU grids (3, 4), flow loops from XT3D (5), storage (6), SFR with MVR (7), MAW (8), LAK and UZF (9), and model 1's flows held constant over 120 steps (10). <!-- tests/models/ builders (common.py, structured.py, unstructured.py, mover.py, networks.py); verification_table.csv notes --> They are described in {SI: example and test models}.

The closure, forward–backward and boundary-control checks (Section 2.5) must hold exactly on any model. Fig. 2 shows the largest error of each check (rows) on each model (markers), against machine precision (dashed line) and the tolerances of the automated tests (grey bars).

[[Figure 2]]

The three exact checks held to 1.8 × 10⁻¹⁵ or better on every model, including model 6 traced as snapshots. <!-- verification_table.md, largest error per check --> Errors this close to machine precision mean that the checks passed. On a user's model, a much larger error flags a problem.

Further tests compare the code with independent results. Net accounting reproduces the worked example of Foley and Black (2013) exactly. DISU copies of model 1 give the DIS results exactly. Simulations split into two to four models (Hughes et al. 2024) agree with the single model to 7.4 × 10⁻¹⁰. This is the flow solver's tolerance. <!-- verification_table.md; README_method.md Fig. 2 caption ("split into 2 to 4 models"); evidence: studies/paper/verification.py; tests/test_multimodel.py labels_for (models 1, 3 and 6 into three, two and four models) --> On these models, results did not depend on grid type or splitting.

GWT removes water through each sink at the cell's concentration, as gross accounting does. We ran it with upstream weighting and no dispersion until the concentrations stopped changing. The tagged concentration then equalled the steady-state forward fraction G to 2.8 × 10⁻¹¹ or better on models 1 and 2, including the weak-sink well. <!-- verification_table.csv (steady_g_vs_gwt) --> <!-- verification_table.csv note (m7_mover: 1.0e-8 on model 7, flow-solver limited; given in the Fig. 2 caption and Table S1) --> G is therefore the steady-state concentration of a tracer without dispersion. Weight-losing PRT particles (Section 3.2) delivered the well's inflow to within 0.6 %. The difference comes from the finite number of release points. This checks the particles used in Section 5. <!-- verification_table.csv (prt_capture: 800.4 of 800, 402.6 of 405 m³/d) -->

## 4.2 Transient tracking checks

Transient tracking has no analytical answer, so we compared it with GWT and with itself run backward. With GWT's water volumes (the "gwt" option of Section 2.7), transient tracking matched GWT to 2.2 × 10⁻¹⁵ on model 6 and 1.0 × 10⁻¹⁴ on the stream network of model 7. <!-- verification_table.csv (tracking_vs_gwt) --> Backward tracking in time (Section 2.8) gave the same tagged volumes as forward tracking to 7.7 × 10⁻¹⁶ or better on models 6, 7 and 9, with both volume options. <!-- verification_table.csv (tracking_duality) -->

With the default "flow" volumes, each cell's water balance closes automatically, because its volume is updated from the storage flows. Its error, at most 9.5 × 10⁻¹⁷, only confirms the arithmetic. The real test is the balance of tagged water. It closed to 1.0 × 10⁻¹⁵, so no tagged water is created or lost between steps. <!-- verification_table.csv (water_balance, tagged_balance); README_method.md error measures -->

On model 10, where flows do not change, transient tracking should reach the steady-state result. At the end, the tagged fraction c matched the steady-state G to 9.7 × 10⁻¹⁴. At the start, the backward fraction in time w matched the steady-state F to 6.8 × 10⁻¹⁰. <!-- verification_table.csv (m10_constant) --> At the opposite ends of the run, c differs from G by at least 0.40 and w from F by at least 0.52. The agreement is therefore not built into the test. <!-- verification_table.csv (m10_constant); README_method.md Fig. 2 caption --> <!-- verification_table.csv notes (both errors flow-solver limited: 1.2e-14 and 1.4e-11 with the flow model solved 100 times tighter; Fig. 2 caption, Table S1) -->

## 4.3 Numerical dispersion

Full mixing spreads a traced area, because cells along its edge mix water bound for the well with water that is not. We measured this numerical dispersion on two problems (Fig. 3; maps in {SI: numerical dispersion maps and time steps}). Problem A is uniform flow to a well, compared with the analytical capture zone (Javandel and Tsang 1986). Problem B is an aquifer like model 1, compared with PRT on a 12.5 m grid. Only the area west of the gaining river is compared, so that neither method meets a weak sink. <!-- DS §1 -->

[[Figure 3]]

F is the share of a cell's water that ends at the well (Section 2.2). The F > 0.5 area holds the cells that send more than half their water to the well. The F > 0.1 area holds every cell that sends more than a tenth. It is meant as a cautious outer limit. <!-- the dispersion study drew its areas as F >= 0.1 and F >= 0.5; studies/dispersion/output/a_maps.npz, b_maps.npz: no full-mixing value equal to 0.1 or 0.5 (to 1e-12), so the areas are the same; counted in round 4; note moved to si/C.md {SI: numerical dispersion maps and time steps} in round 5 (r4_reader comment 34) -->

The transition band is the strip of edge cells where F lies between 0.1 and 0.9. Its width shrank only with about the square root of the cell size h. Halving h narrowed it by about 30 %. <!-- DS Summary, §2 (fitted rates 0.4 to 0.6); 2^-0.5 = 0.71 --> The F > 0.1 area contained the reference area, missing at most 0.1 % of it. For h = 12.5–50 m, it was 30–90 % too large in problem A and 8–16 % in problem B. On cells of 50 m or less, the F > 0.5 area came within 5 % of the reference size. <!-- DS §5; README_method.md Fig. 3 --> <!-- face-to-face routing (DS Summary, §4) now in the Fig. 3 caption and Section 7 -->

## 4.4 Transient demonstration

A synthetic seasonal example model shows what transient tracking adds to snapshots (Section 2.7).

The model has one layer of 40 × 40 cells of 50 m ({SI: example and test models}). Constant heads on the west edge, 1.4 km from the supply well, bring regional inflow. A river runs 100 m east of the well. Recharge is highest in winter and pumping in summer, when the well takes 1,120 m³/d against 800 m³/d on average. Thirty years of four seasons, one time step each, follow a 1-day steady-state period (121 steps). <!-- tutorials/herebedragons.py (AquiferSpec: 40 x 40 cells of 50 m, rech 5e-4 m/d, riv_col 30, supply_well (20, 28) -800 m3/d; build_transient: sy 0.2; SEASON_RECHARGE (1.8, 1.0, 0.1, 1.1), SEASON_PUMPING (0.8, 1.0, 1.4, 0.8)); tutorials/08_transient_tracking/08_transient_tracking.ipynb settings (N_YEARS 30, STEPS_PER_SEASON 1, POROSITY 0.3); README_method.md Fig. 4 caption --> With one layer, the shares below are those of a vertically mixed aquifer. In a layered aquifer, shallow and deep water would reach the well in different shares. <!-- tutorial 08 §3; v6 caveat restored (r4_content 04:39) -->

[[Figure 4]]

On average, snapshots give the well's water as 60 % recharge, 12 % west-edge inflow and 15 % storage release, with about 13 % river leakage (Fig. 4a). Storage release reaches 50 % in summer. <!-- evidence: studies/paper/transient_figure.py (QUOTED; snapshot_shares: recharge, river, west edge and storage are the only source terms); tutorial 08 §2; river leakage 13 % by difference, 1 − 0.60 − 0.12 − 0.15 -->

With forward transient tracking, the well's water in the last season of year 30 was 52 % initial water, 33 % recharge and 16 % river leakage (Fig. 4b). <!-- README_method.md Fig. 4 caption (four sub-steps) --> Unlike the snapshots' 12 %, no west-edge water arrived within 30 years. Of all water pumped so far, initial water made up 98 % after 1 year, 81 % after 10 years and 68 % after 30 years. <!-- README_method.md Fig. 4a–b --> This share tells a manager how much of the pumped water was already stored in the aquifer at the start. A GWT run with tagged initial water gives it too ({SI: transient checks on the seasonal example model}). Snapshots cannot give it, because water released from storage has no known origin (Section 2.7). Backward particle tracking through transient flows can be awkward to set up and hard to interpret (Environment Agency 2019, Appendix C4.3). <!-- references/docs/text/2019_EnvironmentAgency_SPZ_manual.txt, C4.3 "Pros and Cons of using MODPATH"; decisions_r4 items 5 and 6 -->

Only backward tracking in time gives a time-limited area. For the water in each cell at the start, it gives the fractions that leave through the well and through the river within 30 years, and the fraction still stored (Fig. 4d–f). The 30-year area (Fig. 4d) shows which water now in the aquifer reaches the well within that horizon. Unlike the steady-state F area (Fig. 4c), it does not reach the west edge. <!-- backward split of the 30-year pumping (13.8 % river, 18.5 % recharge, 67.7 % initial) moved to the Fig. 4 caption in round 5; README_method.md Fig. 4 caption (1.21, 1.62, 5.94 million m³; 8,766,800 m³) and notes; tutorial 08 §5 -->

<!-- moved to the Fig. 4 caption in round 5: on this model, transient tracking matched GWT to 9.8 × 10⁻¹⁴ (README_method.md Fig. 4 notes; tutorial 08 §§6, 8); sub-step and volume-option numbers (tutorial 08 §§7, 9) in si/C.md -->
