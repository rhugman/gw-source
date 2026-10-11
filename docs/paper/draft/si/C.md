## {SI: verification errors per check and model}

### Test models

The test models are small MODFLOW 6 models built with FloPy; each writes the binary grid file and a budget file with SAVE_FLOWS on every package. Model 1 is one steady unconfined layer with recharge, a pumping well, a river line and a constant-head edge, with inactive cells in one corner so that the mapping from user to reduced cell numbers is tested. Model 2 has three layers and a weak-sink well. Model 3 is model 1 on a Voronoi (DISV) grid, with the stresses placed by geometry. Model 4 is a cell-for-cell DISU copy of model 1, with and without cell vertices. Model 5 adds XT3D anisotropy, which creates flow loops. Model 6 adds storage (STO) and stress periods; it is traced both with transient tracking and as 13 snapshots. Model 7 replaces the river with an SFR stream fed by two drains through MVR. Model 8 adds a multi-aquifer well (MAW) screened in all three layers of model 2, which moves water between layers. Model 9 is a three-layer model with a lake (LAK), unsaturated-zone cells (UZF) and MVR. Model 10 holds model 1's flows constant for 4 × 10⁵ d in 120 equal steps. The sub-step check uses a hand-built network of 15 cells, not a MODFLOW 6 model: three transport sub-steps are compared with three times as many flow steps. <!-- tests/models/*.py docstrings; verification_table.md row labels -->

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

Problem B was also run with 2,000-day flow steps. With one transport step per flow step, the first-step share of new water was roughly doubled, 0.18 against 0.09 for the particles. Sixteen sub-steps of 125 d removed this, leaving a difference of about 0.001 at 12.5 m, averaged over the 30 steps. <!-- DS §3 -->

## {SI: transient checks on tutorial 08}

All values are for tutorial 08 (Section 4.4). Forward transient tracking and backward tracking in time gave the same tagged volumes to ≤ 4.3 × 10⁻¹⁶ for every tag. With GWT's water volumes ("gwt") and one transport step per flow step, the tracked recharge fraction matched a GWT unit-concentration run on the same flows to 9.8 × 10⁻¹⁴. <!-- tutorial 08 §§6, 8; README_method.md Fig. 4 notes --> The backward fractions to the well, to the river and still stored added up to 1 in every cell to within 2.5 × 10⁻¹¹, the backward closure error was 0, and the tagged-water balances closed to 8.0 × 10⁻¹⁶ with one transport step per flow step. <!-- tutorial 08 §§5, 6 -->

With one, four and 16 transport sub-steps per flow step, the river's share of the well's water in the last season of year 1 was 3.6, 3.1 and 3.0 %, and the initial water's share of all water pumped so far after 1 year was 96.9, 97.6 and 97.8 %. From four sub-steps to 16, the year-1 shares moved by at most 0.2 percentage points; Fig. 4 uses four. <!-- tutorial 08 §9; evidence: docs/paper/figures/README_method.md Fig. 4 notes ("the year-1 river leakage share is 3.6 % with one step, 3.1 % with 4 and 3.0 % with 16, and the year-1 cumulative initial-water share 96.9 %, 97.6 % and 97.8 %") --> With "gwt" volumes, about 5,300 m³ of the 45.6 million m³ of initial water is lost over 30 years, so the year-30 share of initial water is 0.5166 against 0.5167 with "flow" volumes. <!-- tutorial 08 §7 -->
