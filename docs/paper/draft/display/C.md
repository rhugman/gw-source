## Figure 2

**Figure 2.** Errors reached by the verification checks on the synthetic test models (markers), against machine epsilon (dashed line) and the test tolerance of each check (grey bars); error measures as in Table 2. Upper block, steady and snapshot checks. The closure, forward–backward and boundary-control checks are exact identities and reach round-off (≤ 1.8 × 10⁻¹⁵) on every model, including model 6 as 13 snapshots and the stream, MAW, lake and UZF networks (models 7–9). The steady forward fraction G equals the MF6 GWT unit concentration run to equilibrium to ≤ 2.8 × 10⁻¹¹ on models 1 and 2; on model 7 the difference, 1.0 × 10⁻⁸, is limited by the flow solver tolerance (2.5 × 10⁻¹¹ with the flow model solved about 100 times tighter). DISU builds give the DIS results exactly, and split simulations agree with the single model to ≤ 7.4 × 10⁻¹⁰. Weight-losing PRT particles deliver the well inflow to within 0.6 % (release-point error). Net accounting reproduces the worked example of Foley and Black (2013) exactly. Lower block, transient tracking checks. Tracking matches MF6 GWT to ≤ 1.0 × 10⁻¹⁴, and forward tracking and backward tracking in time agree to ≤ 7.7 × 10⁻¹⁶ (models 6, 6 split into four models, 7 and 9; both volume options). With "flow" volumes each cell's water balance holds by construction, so its error (≤ 9.5 × 10⁻¹⁷) tests the volume carry, the clipping of volumes at zero and round-off, not the flow solution; the tagged-water balance of each group closes to ≤ 1.0 × 10⁻¹⁵. With model 1's flows held for 4 × 10⁵ d (model 10), c at the end and w at the start equal the steady G and F to 9.7 × 10⁻¹⁴ and 6.8 × 10⁻¹⁰, limited by the flow solver tolerance (1.2 × 10⁻¹⁴ and 1.4 × 10⁻¹¹ with the flow model solved 100 times tighter). Three transport sub-steps equal three times as many flow steps to 1.6 × 10⁻¹⁶ (hand-built 15-cell network, not an MF6 model). "Exact" marks errors of zero.

<!-- Source: README_method.md, Fig. 2 caption and largest-error table; verification_table.md / .csv -->

## Figure 3

**Figure 3.** Numerical dispersion of full mixing against cell size h. Top row: problem A, uniform flow to a well, with the analytical capture zone (Javandel and Tsang 1986) as reference; flow along the grid rows (solid) and at 30° to them (dotted). Bottom row: problem B, a model-1-like aquifer, with PRT on the 12.5 m grid as reference, compared west of the river. (a, d) Width of the transition band (0.1 < F < 0.9). For full mixing it narrows as about $h^{0.5}$ (dashed guide); face-to-face routing narrows it but keeps the rate. The cell-averaged exact zone (A) and PRT on the same grid (B) set a floor of about one cell. (b, e) Relative area error of the zone F ≥ 0.1: it contains the reference zone but is too large, by 30 to 90 % in problem A and 8 to 16 % in problem B for h = 12.5 to 50 m. (c, f) Relative area error of the zone F ≥ 0.5: within 5 % (grey band) for h ≤ 50 m.

<!-- Source: README_method.md, Fig. 3 caption; DS §2, §5 (problem A includes the DISV grids, mean cell size slightly above nominal h) -->

## Figure 4

**Figure 4.** Snapshots and transient tracking on the 30-year seasonal model of tutorial 08: one layer of 1,600 cells (50 m), specific yield 0.2, porosity 0.3, a 1-day steady period and then four seasons a year (121 time steps of about 91 days). Recharge is 1.8 times its mean in winter and 0.1 times in summer; pumping is 1.4 times its mean in summer (1,120 m³/d). The well pumps throughout, so the simulation starts from a pumped steady state. A river (dashed) runs 100 m east of the supply well (triangle); constant heads on the west edge, 1.4 km from the well, bring regional inflow. (a) Snapshots: each step traced backward on its own flows, with storage release as a source term. On average the well's water is 60 % recharge, 12 % west-edge inflow and 15 % storage release, which reaches 50 % in summer; where the storage release came from is unknown. (b) Transient tracking forward, with recharge, river leakage, west-edge inflow and initial water tagged. In the last season of year 1 the well's water is 95 % initial water, 3 % river leakage and under 2 % recharge; in year 30 it is 52 % initial water, 33 % recharge and 16 % river leakage, and no west-edge inflow has reached the well. Dashed line: the initial water's share of all water pumped so far, 98 % after 1 year, 81 % after 10 years and 68 % after 30 years. (c) Steady backward fraction F to the well for the flows of the first step, with no time limit; the zone reaches the west edge. (d–f) Backward tracking in time from the end of the simulation: for the water in each cell at the start, the fraction that leaves through the well within 30 years (w), the fraction to the river (the only other sink) and the fraction still stored after 30 years; they add up to 1 in every cell. With every source tagged, the well's 30-year pumping of 8,766,800 m³ splits into 1.62 million m³ of recharge, 1.21 million m³ of river leakage and 5.94 million m³ of initial water (67.7 %, equal to the forward cumulative share after 30 years). Default "flow" volumes and four transport sub-steps per flow step (about 23 days); 16 sub-steps change the year-1 shares by at most 0.2 percentage points. With MF6 GWT's volumes, the tracked recharge fraction matches a GWT unit-concentration run on the same flows to 9.8 × 10⁻¹⁴; the two volume options differ by less than 2 × 10⁻⁴ in the forward fraction.

<!-- Source: README_method.md, Fig. 4 caption and notes; studies/paper/transient_figure.py (QUOTED, check_quoted) -->

## Table 2

**Table 2.** Verification checks on the synthetic test models: the largest error of each check over all models, groups and time steps, the model where it occurs, and the test tolerance. Errors per model are in Table S4.

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
| PRT flow to the well | 5.9 × 10⁻³ | 2 DIS, 3 layers, weak sink³ | 2 × 10⁻² | relative to well inflow |
| Foley and Black (2013) example | 0 | worked example, net accounting | 10⁻¹⁴ | absolute (published values) |
| ***Transient tracking checks*** | | | | |
| tracking vs GWT | 1.0 × 10⁻¹⁴ | 7 SFR + MVR vs SFT + MVT | 10⁻⁸ | absolute (fraction) |
| transient forward–backward | 7.7 × 10⁻¹⁶ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to source-to-destination volume |
| water balance ("flow")⁴ | 9.5 × 10⁻¹⁷ | 9 LAK + UZF + MVR network | 10⁻¹⁰ | relative to the cell's water volume |
| tagged-water balance ("flow") | 1.0 × 10⁻¹⁵ | 6 transient | 10⁻¹⁰ | relative to largest balance term |
| steady limit, c to G⁵ | 9.7 × 10⁻¹⁴ | 10, model 1 flows held 4 × 10⁵ d | 10⁻¹¹ | absolute (fraction) |
| steady limit, w to F⁵ | 6.8 × 10⁻¹⁰ | 10, model 1 flows held 4 × 10⁵ d | 10⁻⁸ | absolute (fraction) |
| sub-steps vs refined steps | 1.6 × 10⁻¹⁶ | hand-built 15-cell network (not MF6) | 10⁻¹² | relative to output maximum |

¹ Absolute, in m³/d, where the reference flow is below 1 m³/d.
² Models 1 and 2: ≤ 2.8 × 10⁻¹¹ (tolerance 10⁻¹⁰). Model 7 is limited by the flow solve: 2.5 × 10⁻¹¹ with the flow model solved about 100 times tighter.
³ 402.6 of 405 m³/d; a release-point error. Models 1 and 3: 800.4 of 800 m³/d (tolerance 10⁻²).
⁴ Holds by construction with "flow" volumes; tests the volume carry, the clipping of volumes at zero and round-off, not the flow solution.
⁵ Limited by the flow solver tolerance: 1.2 × 10⁻¹⁴ (c to G) and 1.4 × 10⁻¹¹ (w to F) with the flow model solved 100 times tighter.

<!-- Source: docs/paper/figures/verification_table.md ("Largest error per check") and verification_table.csv notes; README_method.md error measures -->
