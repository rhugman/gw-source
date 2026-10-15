# Verification: errors per check and model

This file lists the largest error of every check that the automated tests run, on each test model. The test models are described in `tests/models/README.md`. The values come from `studies/paper/verification.py`, run by `studies/paper/method_figures.py`, which also writes them to `docs/paper/figures/verification_table.md` and `.csv`. The figure of these errors is Figure S1 of the paper's Supporting Information (`docs/paper/figures/figS21_verification.png`). [FB13] is Foley & Black (2013); full entry in `references/bibliography.md`.

## Largest error per check

Each error is the largest over the groups, group pairs and time steps of a model. Figure S1 of the paper's Supporting Information plots these values.

| check | largest error | model | test tolerance | error measure |
|---|---|---|---|---|
| ***Steady-state and snapshot checks*** | | | | |
| backward closure | 1.3 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹⁰ | relative to destination inflow¹ |
| forward closure | 1.1 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹⁰ | relative to source inflow¹ |
| forward–backward | 1.5 × 10⁻¹⁵ | 7 SFR + MVR network | 10⁻¹⁰ | relative to source-to-destination flow¹ |
| boundary control | 1.8 × 10⁻¹⁵ | 6 transient, 13 snapshots | 10⁻¹² | absolute (fraction) |
| steady-state G vs GWT at equilibrium² | 1.0 × 10⁻⁸ | 7 SFR + MVR network | 10⁻⁷ | absolute (fraction) |
| DISU vs DIS | 0 | 4 DISU (both variants) | 10⁻¹² | relative to output maximum |
| split vs single | 7.4 × 10⁻¹⁰ | 1 DIS, three models | 10⁻⁸ | relative to output maximum |
| PRT flow to the well³ | 5.9 × 10⁻³ | 2 DIS, 3 layers, weak sink | 2 × 10⁻² | relative to well inflow |
| [FB13] example | 0 | worked example, net accounting | 10⁻¹⁴ | absolute (published values) |
| ***Transient tracking checks*** | | | | |
| transient tracking vs GWT⁴ | 1.0 × 10⁻¹⁴ | 7 SFR + MVR vs SFT + MVT | 10⁻⁸ | absolute (fraction) |
| transient forward–backward | 7.7 × 10⁻¹⁶ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to source-to-destination volume |
| water balance ("flow")⁵ | 9.5 × 10⁻¹⁷ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to the cell's water volume |
| tagged-water balance ("flow") | 1.0 × 10⁻¹⁵ | 6 transient | 10⁻¹⁰ | relative to the largest balance term |
| steady-state limit, c to G⁶ | 9.7 × 10⁻¹⁴ | 10, model 1 flows held 4 × 10⁵ d | 10⁻¹¹ | absolute (fraction) |
| steady-state limit, w to F⁶ | 6.8 × 10⁻¹⁰ | 10, model 1 flows held 4 × 10⁵ d | 10⁻⁸ | absolute (fraction) |
| sub-steps vs refined steps | 1.6 × 10⁻¹⁶ | hand-built 15-cell network | 10⁻¹² | relative to output maximum |

¹ Absolute, in m³/d, where the reference flow is below 1 m³/d.

² Models 1 and 2: ≤ 2.8 × 10⁻¹¹ (tolerance 10⁻¹⁰). Model 7 is limited by the flow solver tolerance: 2.5 × 10⁻¹¹ with the flow model solved about 100 times tighter.

³ 402.6 of 405 m³/d on model 2, and 800.4 of 800 m³/d on models 1 and 3 (tolerance 10⁻²); a release-point error.

⁴ With GWT's water volumes ("gwt"). On model 6, five tagging cases.

⁵ Holds by construction with "flow" volumes; tests the carrying of volumes from step to step, the clipping of volumes at zero and round-off, not the flow solution.

⁶ Limited by the flow solver tolerance: 1.2 × 10⁻¹⁴ (c to G) and 1.4 × 10⁻¹¹ (w to F) with the flow model solved 100 times tighter. With 30 growing time steps instead of 120 equal ones the errors were 1.4 × 10⁻⁸ and 5.9 × 10⁻⁷.

On model 1 the flow-weighted mean time for the water reaching the well to enter its cell is 9,574 d, against 9,590 d for weight-losing PRT particles, which stop on entering the cell. The full-mixing mean travel time m/F, which includes the time spent in the well cell, is 9,607 d. 

The split simulations divide model 1 into three models (7.4 × 10⁻¹⁰), model 3 into two (1.4 × 10⁻¹⁰) and model 6 into four (1.5 × 10⁻¹²). The four-model split of model 6 also passes the transient forward–backward check (4.5 × 10⁻¹⁶). 

## Steady-state and snapshot checks, per model

| model | backward closure | forward closure | forward–backward | boundary control | steady-state G vs GWT at equilibrium | DISU vs DIS | split vs single | PRT flow to the well | [FB13] example |
|---|---|---|---|---|---|---|---|---|---|
| [FB13] worked example, net accounting | – | – | – | – | – | – | – | – | 0 |
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

Error measures. **backward closure**: relative to destination inflow (absolute in m³/d below 1 m³/d). **forward closure**: relative to source inflow (absolute in m³/d below 1 m³/d). **forward–backward**: relative to forward source-to-destination flow (absolute in m³/d below 1 m³/d). **boundary control**: absolute (fraction). **steady-state G vs GWT at equilibrium**: absolute (fraction). **DISU vs DIS**: relative to output maximum. **split vs single**: relative to output maximum. **PRT flow to the well**: relative to destination inflow. **[FB13] example**: absolute (published values).

## Transient tracking checks, per model

| model | tracking vs GWT | transient forward–backward | water balance ("flow") | tagged-water balance ("flow") | steady-state limit, c to G | steady-state limit, w to F | sub-steps vs refined steps |
|---|---|---|---|---|---|---|---|
| 6 transient (STO) | 2.2 × 10⁻¹⁵ | 5.9 × 10⁻¹⁶ | 6.9 × 10⁻¹⁷ | 1.0 × 10⁻¹⁵ | – | – | – |
| 6 transient, split into 4 models | – | 4.5 × 10⁻¹⁶ | – | – | – | – | – |
| 7 SFR + MVR network | 1.0 × 10⁻¹⁴ | 4.7 × 10⁻¹⁶ | – | – | – | – | – |
| 9 LAK + UZF + MVR network | – | 7.7 × 10⁻¹⁶ | 9.5 × 10⁻¹⁷ | 1.8 × 10⁻¹⁶ | – | – | – |
| 10 model 1 flows, held 4 × 10⁵ d | – | – | – | – | 9.7 × 10⁻¹⁴ | 6.8 × 10⁻¹⁰ | – |
| hand-built 15-cell network (not a MODFLOW 6 model) | – | – | – | – | – | – | 1.6 × 10⁻¹⁶ |
| *test tolerance* | 10⁻⁸ | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹⁰ | 10⁻¹¹ | 10⁻⁸ | 10⁻¹² |

Error measures. **tracking vs GWT**: absolute (fraction). **transient forward–backward**: relative to forward source-to-destination volume (absolute when zero). **water balance ("flow")**: relative to the cell's water volume. **tagged-water balance ("flow")**: relative to largest term of the tagged-water balance. **steady-state limit, c to G**: absolute (fraction). **steady-state limit, w to F**: absolute (fraction). **sub-steps vs refined steps**: relative to output maximum.
