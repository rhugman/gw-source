## {SI: example and test models}

All models below are small and synthetic. They ship with the code (Section 9): the test models and the two hand-built networks as automated tests, the three-layer and seasonal examples as tutorials, and the eight-cell example as a figure script. Lengths are in metres and times in days.

### Test models of Section 4.1

Models 1 to 10 are MODFLOW 6 models built with FloPy. Each writes the binary grid file and a budget file with SAVE_FLOWS on every package. Two further cases are not MODFLOW 6 models. All cells are 50 m wide in plan, except on the Voronoi grid of model 3.

| model | grid and size | packages | flow | what it tests |
|---|---|---|---|---|
| 1 | DIS, 1 layer of 20 × 30 cells, top 20 m, bottom −30 m; 6 inactive cells in one corner (594 active) | CHD on the west edge (5 m); RIV along one column (stage 6 m); WEL (800 m³/d); RCH (1 × 10⁻³ m/d); K 10 m/d | steady | the base case: closure, forward–backward and boundary-control checks, GWT at equilibrium, PRT, split into three models; the inactive cells test the mapping of cell numbers |
| 2 | DIS, 3 layers of 15 × 25 cells (1,125 cells), top 10 m, layer bottoms −10, −30 and −60 m | CHD on the west (9 m) and east (2 m) edges of every layer; RCH (5 × 10⁻⁴ m/d) on layer 1; two WEL in layer 3 (400 and 5 m³/d); K 10, 2 and 15 m/d, vertical K one tenth of it | steady | a weak-sink well (5 m³/d) under gross accounting, GWT at equilibrium, PRT; a copy with recharge on the top cell face (IFLOWFACE = −1) tests PRT release on a face |
| 3 | DISV Voronoi grid over model 1's area, from a Triangle mesh with triangles of at most 2,500 m²; all cells active | as model 1, placed by geometry; river conductance scaled to model 1's total | steady | reading a vertex grid, PRT on a vertex grid, split into two models |
| 4 | DISU, a cell-for-cell copy of model 1, with and without cell vertices | as model 1 | steady | DISU results equal DIS results exactly |
| 5 | as model 1 | as model 1, with XT3D; log-normal K (median 10 m/d), K across the main axis 0.05 times K, main axes rotated by up to 45° | steady | flow loops |
| 6 | as model 1 | as model 1, with STO (specific yield 0.2, specific storage 10⁻⁵ /m); a 1-day steady period, then three 100-day periods of four steps with a time-step multiplier of 1.2 (13 steps); pumping 800, 1,200, 400 and 1,000 m³/d; recharge 1, 0.3, 1.5 and 0 times model 1's | transient | 13 snapshots with storage as source and sink terms; transient tracking against GWT; transient forward–backward check; water balances; split into four models |
| 7 | as model 1 | model 1 with the river replaced by an SFR stream of 20 reaches (inflow 500 m³/d at the first reach); two DRN drains feeding the first reach through MVR (70 % and 100 % of their outflow); named wells whose list changes between two periods | steady (two periods) | a package network (SFR and MVR); GWT at equilibrium and transient tracking against GWT with stream and mover transport (SFT and MVT) |
| 8 | as model 2 | model 2's grid, with the 400 m³/d well replaced by a MAW well (30 m³/d) screened in all three layers; the 5 m³/d WEL kept; vertical K one hundredth of K | steady | a multi-aquifer well that moves water between layers |
| 9 | as model 2, with the layer-1 cells of two lakes removed | LAK with two lakes (lake A spills into lake B, lake B out of the model); UZF on a block of layer-1 cells, whose rejected infiltration MVR moves into lake A; RCH (4 × 10⁻⁴ m/d) elsewhere; WEL (150 m³/d) in layer 3; CHD on the west (9 m) and east (4 m) edges; STO | transient: a 1-day steady period, then a 50-day period of two steps | a lake and unsaturated-zone network; transient forward–backward check; water balances |
| 10 | as model 1 | as model 1, without STO; a 1-day period, then 4 × 10⁵ d in 120 equal steps of unchanged flows | steady flows over many time steps | transient tracking reaches the steady fractions |
| worked example | hand-built network of 3 × 3 cells and two outside nodes (Foley and Black 2013) | none (flows given between cells) | steady | net accounting against the published values |
| sub-step network | hand-built network of 15 cells with flow loops, no storage, 6 time steps | none | steady flows over time steps | transport sub-steps equal a flow model with proportionally more time steps |

<!-- tests/models/common.py docstring (binary grid file, SAVE_FLOWS on every package, OC SAVE BUDGET ALL); tests/models/gwt.py (SFT and MVT on model 7); tests/test_prt.py (PRT on m1_dis and m3_disv); tests/test_multimodel.py labels_for (models 1, 3 and 6 split into three, two and four models); tests/models/common.py (BaseSpec: 20 x 30 cells of 50 m, top 20, botm -30, k 10, rech 1e-3, chd_head 5, riv_col 22, riv_stage 6, wel_rate -800, six inactive cells); tests/models/structured.py (build_base_dis; build_layered_dis / build_layered_top_rch_dis: 3 x 15 x 25, botm -10/-30/-60, k 10/2/15, k33 0.1 k, CHD 9 and 2 m, RCH 5e-4, wells -400 and -5; build_xt3d_dis / xt3d_k_field: k = 10 exp(N(0, 1)), k22 0.05 k, angle1 up to 45 degrees; build_transient_dis: periods (1, 1), (100, 4, 1.2) x 3, wells -800/-1200/-400/-1000, rch factors 1/0.3/1.5/0, sy 0.2, ss 1e-5; build_constant_flow_dis: (1, 1), (4e5, 120)); tests/models/unstructured.py (build_voronoi_disv: max_area 2500, riv_cond scaled to the same total; build_base_disu: with and without vertices); tests/models/mover.py (20 SFR reaches, INFLOW 500, DRN_TO_SFR factors 0.7 and 1.0, WELLS changing between two steady periods); tests/models/networks.py (build_maw_dis: k33 0.01 k, MAW_RATE -30, WEL -5; build_lak_uzf_dis: two lakes, outlets A to B and B out, UZF rejected infiltration to lake A by MVR, RCH 4e-4, LAK_WELL -150 in layer 3, CHD 9 and 4 m, periods (1, 1), (50, 2)); studies/paper/verification.py docstring (sub-step network: hand-built 15-cell network with flow loops and no storage, 6 steps; [FB13] example: 3 x 3 cells); tutorials/02_accounting/02_accounting.ipynb §2 (worked example: cells A to I and outside nodes J and K) -->

### Accounting examples (Fig. 1)

**Eight-cell example (Fig. 1b).** A hand-built network of two rows of four cells, not a MODFLOW 6 model. Boundary inflow of 4 m³/d enters each of the two western cells. Recharge of 1 m³/d enters every cell. A well takes 6 m³/d from one cell of the third column. A river takes 4 and 6 m³/d from the two eastern cells. Inflow and outflow are both 16 m³/d. <!-- studies/paper/method_figures.py (GRAPH_EDGES, GRAPH_TERMS: CHD 4 in cells 0 and 4; RCH 1 in cells 0 to 7; WEL -6 in cell 6; RIV -4 in cell 3 and -6 in cell 7) -->

**Three-layer example (Fig. 1c).** A steady DIS model of 3 layers of 40 × 40 cells of 50 m. The top is at 20 m and the layer bottoms at 0, −12 and −30 m. Hydraulic conductivity is 10, 1 and 15 m/d, with vertical conductivity one tenth of it. Constant heads of 10 m hold the west edge of every layer. A river (RIV; stage 6 m, bottom 4 m, conductance 500 m²/d) runs along one column of layer 1, 1.5 km from the west edge. Recharge of 5 × 10⁻⁴ m/d falls on layer 1. A supply well pumps 800 m³/d from layer 3, 100 m west of the river. A small well pumps 5 m³/d from layer 3, 800 m west and 200 m north of the supply well. Its cell carries 33.7 m³/d, so it is a weak sink. <!-- tutorials/herebedragons.py (AquiferSpec: 40 x 40 cells of 50 m, top 20, chd_head 10, riv_col 30, riv_stage 6, riv_rbot 4, riv_cond 500, rech 5e-4; build_layered: LAYER_BOTM (0, -12, -30), LAYER_K (10, 1, 15), k33_ratio 0.1, LAYERED_WELLS supply_well (2, 20, 28) -800 and weak_well (2, 16, 12) -5); README_method.md Fig. 1c (33.7 m³/d) -->

### Seasonal example model (Section 4.4, Fig. 4)

A DIS model of one convertible layer of 40 × 40 cells of 50 m, 2 km on each side. The top is at 20 m and the bottom at −30 m. Hydraulic conductivity is 5 m/d. Constant heads of 10 m hold the west edge, 1.4 km from the supply well. A river (RIV; stage 6 m, bottom 4 m, conductance 500 m²/d) runs north–south along one column, 100 m east of the well. Recharge averages 5 × 10⁻⁴ m/d (0.18 m/yr). Its seasonal multipliers are 1.8 (winter), 1.0 (spring), 0.1 (summer) and 1.1 (autumn). The supply well pumps 800 m³/d on average, with multipliers 0.8, 1.0, 1.4 and 0.8, so 1,120 m³/d in summer. Specific yield is 0.2 and specific storage 10⁻⁵ /m. Porosity for transport is 0.3. A 1-day steady period, with the well pumping at its mean rate, is followed by 120 seasons of about 91 days, one time step each (121 steps over 30 years). Every step's budget is saved. <!-- tutorials/herebedragons.py (AquiferSpec: nrow = ncol = 40, delr 50, top 20, botm -30, k 5, chd_head 10, riv_col 30, riv_stage 6, riv_rbot 4, riv_cond 500, rech 5e-4, supply_well (20, 28) -800; SEASON_RECHARGE (1.8, 1.0, 0.1, 1.1); SEASON_PUMPING (0.8, 1.0, 1.4, 0.8); seasonal_periods: 1-day steady period, then 365.25 / 4 d per season; build_transient: sy 0.2, ss 1e-5, icelltype 1); tutorials/08_transient_tracking/08_transient_tracking.ipynb settings (N_YEARS 30, STEPS_PER_SEASON 1, POROSITY 0.3); studies/paper/transient_figure.py (same model, n_years 30, steps_per_season 1) -->

## {SI: verification errors per check and model}

The test models are described in {SI: example and test models}.

### Largest error per check

Errors are the largest over groups, group pairs and time steps of each model; Fig. 2 plots these values.

| check | largest error | model | test tolerance | error measure |
|---|---|---|---|---|
| ***Steady and snapshot checks*** | | | | |
| backward closure | 1.3 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹⁰ | relative to destination inflow¹ |
| forward closure | 1.1 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹⁰ | relative to source inflow¹ |
| forward–backward | 1.5 × 10⁻¹⁵ | 7 SFR + MVR network | 10⁻¹⁰ | relative to source-to-destination flow¹ |
| boundary control | 1.8 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹² | absolute (fraction) |
| steady G vs GWT at equilibrium² | 1.0 × 10⁻⁸ | 7 SFR + MVR network | 10⁻⁷ | absolute (fraction) |
| DISU vs DIS | 0 | 4 DISU (both variants) | 10⁻¹² | relative to output maximum |
| split vs single | 7.4 × 10⁻¹⁰ | 1 DIS, three models | 10⁻⁸ | relative to output maximum |
| PRT flow to the well³ | 5.9 × 10⁻³ | 2 DIS, 3 layers, weak sink | 2 × 10⁻² | relative to well inflow |
| Foley and Black (2013) example | 0 | worked example, net accounting | 10⁻¹⁴ | absolute (published values) |
| ***Transient tracking checks*** | | | | |
| transient tracking vs GWT⁴ | 1.0 × 10⁻¹⁴ | 7 SFR + MVR vs SFT + MVT | 10⁻⁸ | absolute (fraction) |
| transient forward–backward | 7.7 × 10⁻¹⁶ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to source-to-destination volume |
| water balance ("flow")⁵ | 9.5 × 10⁻¹⁷ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to the cell's water volume |
| tagged-water balance ("flow") | 1.0 × 10⁻¹⁵ | 6 transient | 10⁻¹⁰ | relative to the largest balance term |
| steady limit, c to G⁶ | 9.7 × 10⁻¹⁴ | 10, model 1 flows held 4 × 10⁵ d | 10⁻¹¹ | absolute (fraction) |
| steady limit, w to F⁶ | 6.8 × 10⁻¹⁰ | 10, model 1 flows held 4 × 10⁵ d | 10⁻⁸ | absolute (fraction) |
| sub-steps vs refined steps | 1.6 × 10⁻¹⁶ | hand-built 15-cell network | 10⁻¹² | relative to output maximum |

¹ Absolute, in m³/d, where the reference flow is below 1 m³/d.
² Models 1 and 2: ≤ 2.8 × 10⁻¹¹ (tolerance 10⁻¹⁰). Model 7 is limited by the flow solver tolerance: 2.5 × 10⁻¹¹ with the flow model solved about 100 times tighter.
³ 402.6 of 405 m³/d on model 2, and 800.4 of 800 m³/d on models 1 and 3 (tolerance 10⁻²); a release-point error.
⁴ With GWT's water volumes ("gwt"). On model 6, five tagging cases.
⁵ Holds by construction with "flow" volumes; tests the carrying of volumes from step to step, the clipping of volumes at zero and round-off, not the flow solution.
⁶ Limited by the flow solver tolerance: 1.2 × 10⁻¹⁴ (c to G) and 1.4 × 10⁻¹¹ (w to F) with the flow model solved 100 times tighter. With 30 growing time steps instead of 120 equal ones the errors were 1.4 × 10⁻⁸ and 5.9 × 10⁻⁷.

<!-- docs/paper/figures/verification_table.md ("Largest error per check") and verification_table.csv notes; README_method.md error measures; PLAN Phase 5 notes (model 10, 30 growing steps) -->

On model 1 the flow-weighted mean time for the water reaching the well to enter its cell is 9,574 d, against 9,590 d for weight-losing PRT particles, which stop on entering it. The mean travel time of Section 2.6, $m/F$, includes the residence in the well cell and is 9,607 d ({SI: travel-time identity}). <!-- PLAN Phase 3 notes; tests/test_prt.py -->

The split simulations divide model 1 into three models (7.4 × 10⁻¹⁰), model 3 into two (1.4 × 10⁻¹⁰) and model 6 into four (1.5 × 10⁻¹²); the four-model split of model 6 also passes the transient forward–backward check (4.5 × 10⁻¹⁶). <!-- verification_table.md per-model tables; evidence: studies/paper/verification.py (split_vs_single: models 1, 3 and 6 split into 2 to 4 models); tests/test_multimodel.py labels_for (m1_dis three models, m3_disv two, m6_transient four) -->

### Steady and snapshot checks, per model

| model | backward closure | forward closure | forward–backward | boundary control | steady G vs GWT at equilibrium | DISU vs DIS | split vs single | PRT flow to the well | Foley and Black (2013) example |
|---|---|---|---|---|---|---|---|---|---|
| Foley and Black (2013) worked example, net accounting | – | – | – | – | – | – | – | – | 0 |
| 1 DIS | 1.7 × 10⁻¹⁶ | 3.3 × 10⁻¹⁶ | 1.6 × 10⁻¹⁶ | 5.6 × 10⁻¹⁶ | 1.4 × 10⁻¹¹ | – | 7.4 × 10⁻¹⁰ | 5.1 × 10⁻⁴ | – |
| 2 DIS, 3 layers, weak sink | 1.6 × 10⁻¹⁶ | 1.3 × 10⁻¹⁶ | 1.9 × 10⁻¹⁶ | 6.7 × 10⁻¹⁶ | 2.8 × 10⁻¹¹ | – | – | 5.9 × 10⁻³ | – |
| 3 DISV Voronoi | 2.8 × 10⁻¹⁶ | 1.5 × 10⁻¹⁶ | 3.2 × 10⁻¹⁶ | 6.7 × 10⁻¹⁶ | – | – | 1.4 × 10⁻¹⁰ | 4.8 × 10⁻⁴ | – |
| 4 DISU (vertices) | 1.7 × 10⁻¹⁶ | 3.3 × 10⁻¹⁶ | 1.6 × 10⁻¹⁶ | 5.6 × 10⁻¹⁶ | – | 0 | – | – | – |
| 4 DISU (no vertices) | 1.7 × 10⁻¹⁶ | 3.3 × 10⁻¹⁶ | 1.6 × 10⁻¹⁶ | 5.6 × 10⁻¹⁶ | – | 0 | – | – | – |
| 5 XT3D, cycles | 4.1 × 10⁻¹⁶ | 1.9 × 10⁻¹⁶ | 2.7 × 10⁻¹⁶ | 4.4 × 10⁻¹⁶ | – | – | – | – | – |
| 6 transient (STO) | 1.3 × 10⁻¹⁵ | 1.1 × 10⁻¹⁵ | 9.4 × 10⁻¹⁶ | 1.8 × 10⁻¹⁵ | – | – | 1.5 × 10⁻¹² | – | – |
| 7 SFR + MVR network | 6.2 × 10⁻¹⁶ | 3.4 × 10⁻¹⁶ | 1.5 × 10⁻¹⁵ | 1.1 × 10⁻¹⁵ | 1.0 × 10⁻⁸ | – | – | – | – |
| 8 MAW network | 7.5 × 10⁻¹⁶ | 1.3 × 10⁻¹⁶ | 4.8 × 10⁻¹⁶ | 8.9 × 10⁻¹⁶ | – | – | – | – | – |
| 9 LAK + UZF + MVR network | 4.4 × 10⁻¹⁶ | 3.2 × 10⁻¹⁶ | 6.4 × 10⁻¹⁶ | 1.1 × 10⁻¹⁵ | – | – | – | – | – |
| *test tolerance* | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹² | 10⁻¹⁰ / 10⁻⁷ | 10⁻¹² | 10⁻⁸ | 10⁻² / 2 × 10⁻² | 10⁻¹⁴ |

Error measures. **backward closure**: relative to destination inflow (absolute in m³/d below 1 m³/d). **forward closure**: relative to source inflow (absolute in m³/d below 1 m³/d). **forward–backward**: relative to forward source-to-destination flow (absolute in m³/d below 1 m³/d). **boundary control**: absolute (fraction). **steady G vs GWT at equilibrium**: absolute (fraction). **DISU vs DIS**: relative to output maximum. **split vs single**: relative to output maximum. **PRT flow to the well**: relative to destination inflow. **Foley and Black (2013) example**: absolute (published values).

### Transient tracking checks, per model

| model | tracking vs GWT | transient forward–backward | water balance ("flow") | tagged-water balance ("flow") | steady limit, c to G | steady limit, w to F | sub-steps vs refined steps |
|---|---|---|---|---|---|---|---|
| 6 transient (STO) | 2.2 × 10⁻¹⁵ | 5.9 × 10⁻¹⁶ | 6.9 × 10⁻¹⁷ | 1.0 × 10⁻¹⁵ | – | – | – |
| 6 transient, split into 4 models | – | 4.5 × 10⁻¹⁶ | – | – | – | – | – |
| 7 SFR + MVR network | 1.0 × 10⁻¹⁴ | 4.7 × 10⁻¹⁶ | – | – | – | – | – |
| 9 LAK + UZF + MVR network | – | 7.7 × 10⁻¹⁶ | 9.5 × 10⁻¹⁷ | 1.8 × 10⁻¹⁶ | – | – | – |
| 10 model 1 flows, held 4 × 10⁵ d | – | – | – | – | 9.7 × 10⁻¹⁴ | 6.8 × 10⁻¹⁰ | – |
| hand-built 15-cell network (not a MODFLOW 6 model) | – | – | – | – | – | – | 1.6 × 10⁻¹⁶ |
| *test tolerance* | 10⁻⁸ | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹¹ | 10⁻⁸ | 10⁻¹² |

Error measures. **tracking vs GWT**: absolute (fraction). **transient forward–backward**: relative to forward source-to-destination volume (absolute when zero). **water balance ("flow")**: relative to the cell's water volume. **tagged-water balance ("flow")**: relative to largest term of the tagged-water balance. **steady limit, c to G**: absolute (fraction). **steady limit, w to F**: absolute (fraction). **sub-steps vs refined steps**: relative to output maximum.

<!-- docs/paper/figures/verification_table.md, generated by studies/paper/method_figures.py (studies/paper/verification.py); numbers rewritten as × 10⁻ⁿ -->

## {SI: numerical dispersion maps and time steps}

**Figure.** Numerical dispersion maps and time steps. Colour is F, the fraction of a cell's water that reaches the well (dot); the wider the band of intermediate colours across the dashed line, the stronger the numerical dispersion. (a–h) Problem A, uniform flow along the grid rows (a–d) and at 30° to them (e–h), 50 m cells. The first column is the exact capture zone averaged over each cell, the best a cell-based method can do; dashed: analytical capture-zone edge. (i–l) Problem B: PRT on the 12.5 m grid and the three methods on 50 m cells; dashed: the PRT F = 0.5 edge; grey: gaining river. Compared west of the river only. DIS: square cells; DISV: Voronoi cells. (m) Share of the well's water that entered after tagging started, per 2,000-day flow step, 12.5 m grid, for 1 to 64 transport sub-steps and for PRT; (n) difference to PRT. <!-- docs/paper/figures/figS1_numerical_dispersion.png, studies/paper/si_dispersion_figure.py; redrawn from DS Figs 1, 3, 5 (studies/dispersion/output) -->

Across cell sizes the transition band was 1.2–12 cells wide, and the fitted narrowing rates were 0.4–0.6. <!-- DS §2 -->

The dispersion study draws areas with non-strict thresholds (F ≥ 0.1, F ≥ 0.5). The main text and the panel titles of Fig. 3 write strict ones (F > 0.1, F > 0.5), as the Neversink study did. A strict threshold leaves out cells with F exactly at the threshold. No full-mixing cell in the dispersion tests has F exactly 0.1 or 0.5, so the two forms give the same full-mixing and face-routing areas there. The comparison zones in Fig. 3 are different. The PRT zones hold cells at exactly 0.5, because a particle fraction is a ratio of particle counts. The cell-averaged exact zones hold cells at exactly 0.1 and 0.5. These comparison zones are drawn with ≥, as in the study. A strict threshold would shrink them by at most about 0.8 % of their area, about 0.007 in area error. <!-- round 5 figure agent: counted on the whole stored a_maps.npz and b_maps.npz (50, 25 and 12.5 m maps only), not the evaluation window -->
 <!-- studies/dispersion/output/a_maps.npz and b_maps.npz, counted in round 4: no full-mixing map value equal to 0.1 or 0.5 within 1e-12; PRT maps (b_maps.npz DIS_*_particles, ref) and cell-averaged exact zones hold values equal to 0.5; studies/dispersion/analysis.py (reference zone R >= 0.5, zone F >= t) -->

Problem B was also run with 2,000-day flow steps. With one transport step per flow step, the first-step share of new water was roughly doubled, 0.18 against 0.09 for the particles. Sixteen sub-steps of 125 d removed this, leaving a difference of about 0.001 at 12.5 m, averaged over the 30 steps. <!-- DS §3 -->

## {SI: transient checks on the seasonal example model}

All values are for the seasonal example model (Section 4.4). Unless stated otherwise, they use the default "flow" volumes and four transport sub-steps per flow step, as Fig. 4 does. In the last season of year 1 alone, the well's water was 95 % initial water, 3 % river leakage and under 2 % recharge. The dashed line in Fig. 4b is the cumulative share, 98 % after 1 year. Over 30 years the well pumped 8.77 million m³. Backward tracking in time splits this into 13.8 % river leakage, 18.5 % recharge and 67.7 % initial water, which matches the forward cumulative share of 68 %. <!-- studies/paper/transient_figure.py QUOTED ("year 1 initial" 0.95, "year 1 river" 0.03, BELOW "year 1 recharge" 0.02, "cumulative initial, year 1" 0.98, "pumping, 30 years (m3)" 8,766,800, volumes 1.21, 1.62 and 5.94 million m³, "share initial, backward" 0.677); README_method.md Fig. 4 caption and notes; tutorial 08 §5; moved from the Fig. 4 caption and §4.4 in round 5 --> Forward transient tracking and backward tracking in time gave the same tagged volumes to ≤ 4.3 × 10⁻¹⁶ for every tag. With GWT's water volumes ("gwt") and one transport step per flow step, the tracked recharge fraction matched a GWT unit-concentration run on the same flows to 9.8 × 10⁻¹⁴. <!-- tutorial 08 §§6, 8; README_method.md Fig. 4 notes --> The backward fractions to the well, to the river and still stored added up to 1 in every cell to within 2.5 × 10⁻¹¹, the backward closure error was 0, and the tagged-water balances closed to 8.0 × 10⁻¹⁶ with one transport step per flow step. <!-- tutorial 08 §§5, 6 -->

With one, four and 16 transport sub-steps per flow step, the river's share of the well's water in the last season of year 1 was 3.6, 3.1 and 3.0 %, and the initial water's share of all water pumped so far after 1 year was 96.9, 97.6 and 97.8 %. From four sub-steps to 16, the year-1 shares moved by at most 0.2 percentage points; Fig. 4 uses four. <!-- tutorial 08 §9; evidence: docs/paper/figures/README_method.md Fig. 4 notes ("the year-1 river leakage share is 3.6 % with one step, 3.1 % with 4 and 3.0 % with 16, and the year-1 cumulative initial-water share 96.9 %, 97.6 % and 97.8 %") --> With "gwt" volumes, about 5,300 m³ of the 45.6 million m³ of initial water is lost over 30 years, so the year-30 share of initial water is 0.5166 against 0.5167 with "flow" volumes. <!-- tutorial 08 §7 --> With one transport step per flow step, the two volume options differed by up to 1.9 × 10⁻⁴ in the forward fractions and 3.7 × 10⁻³ in the backward fractions. With one transport step per flow step, the first-step share of new recharge in the well's water was 0.0078, against 0.0042 with 16 sub-steps. Long transport steps make tagged water arrive too early, which sub-steps correct. <!-- tutorial 08 §§7, 9; README_method.md Fig. 4 notes (1.9 × 10⁻⁴) -->
