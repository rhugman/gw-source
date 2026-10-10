# Method and verification figures (Figs 1–3, Table 2)

Made by `studies/paper/method_figures.py` (run from the repository root; about 7 s, models built in `studies/paper/output/`, git-ignored). Each figure is saved as PNG (300 dpi) and PDF at the *Groundwater* double-column width of 7 in, with fonts of 7 pt or larger and the Okabe–Ito colour-blind-safe palette. The Neversink figures and the main `README.md` of this folder are written separately.

## Fig. 1. Method schematic

`fig1_method_schematic.png` / `.pdf`

*Figure 1. Full-mixing flow tracing. (a) Cell i receives intercell flows q_ji and source terms (here recharge) and passes water to neighbours (q_ik) and to sink terms (here a well, d_i). I_i and O_i are its total inflow and outflow; the cell budget error r_i = I_i − O_i is reported, not forced to zero. Because the cell is fully mixed, its outflows carry the same water, so the backward fraction F_i (the share of the cell's water that reaches the destination) is the flow-weighted mean of its downstream neighbours' fractions plus the share leaving directly through the destination sink. (b) Backward fractions F to a 6 m³/d well on an eight-cell example with boundary inflow (west), recharge of 1 on every cell and a river (east); arrows show flows. Computed with gwsource (gross accounting). The well takes 6 of the 11 units passing through its cell, so F = 6/11 = 0.55 there and in the cells upstream of it that drain only through it. (c) Gross and net accounting on the 5 m³/d weak-sink well of tutorial 02, whose cell carries 33.7 m³/d. Gross accounting, in which each sink takes its share of the cell's outflow, gives the well F = 0.15 in its cell and attributes 5.0 m³/d to it, its pumping. Net accounting, as in the reference method [FB13], fixes F = 1 in the well cell and attributes the whole throughflow, 33.7 m³/d, 6.7 times the pumping.*

Numbers in (b) and (c) are computed on each run: (b) from the hand-built `FlowStep` in `graph_step()`, whose backward closure is checked; (c) by building tutorial 02's layered model (`tutorials/herebedragons.py::build_layered`) and tracing the weak well in both modes.

## Table 2 and Fig. 2. Verification

`verification_table.csv` (long format: model, check, error, tolerance, measure, number of compared values, status, seconds, note), `verification_table.md` (models × checks, plus the largest error per check), `fig2_verification.png` / `.pdf`.

*Figure 2. Errors reached by the verification checks on the synthetic test models (markers) against machine epsilon (dashed) and the tolerance each check is tested to (grey bars). Closure (the traced volumes add up to the destination or source inflow), duality (backward and forward tracing give the same volume between a source and a destination) and boundary control (in every cell the fractions to all sinks add up to 1) are exact identities of the method; their errors are round-off (≤ 1.8 × 10⁻¹⁵) on every model, including the transient model (13 steps, storage as source and sink terms) and the stream, multi-aquifer-well, lake and unsaturated-zone networks. DISU builds of model 1 give the DIS results exactly, and simulations split into 2 to 4 models with GWF-GWF exchanges agree with the single model to ≤ 7.4 × 10⁻¹⁰, the MF6 solver tolerance. Transient tracking matches MF6 GWT unit concentrations to ≤ 1.0 × 10⁻¹⁴. Flux-weighted MF6 PRT particles capture the well inflow to within 0.6 %, an error from the finite number of release points. Net mode reproduces the worked example of [FB13] exactly. "Exact" marks errors of zero. Error measures are given in Table 2.*

Largest error per check (tolerance in brackets):

| check | largest error | model |
|---|---|---|
| backward closure | 1.3e-15 (1e-10) | 6 transient |
| forward closure | 1.1e-15 (1e-10) | 6 transient |
| duality | 1.5e-15 (1e-10) | 7 SFR + MVR network |
| boundary control | 1.8e-15 (1e-12) | 6 transient |
| DISU vs DIS | 0 (1e-12) | 4, both variants |
| split vs single | 7.4e-10 (1e-8) | 1 DIS, three models |
| tracking vs GWT | 1.0e-14 (1e-8) | 7 SFR + MVR vs SFT + MVT |
| PRT capture | 5.9e-3 (2e-2) | 2 DIS, 3 layers (402.6 of 405 m³/d) |
| [FB13] example | 0 (1e-14) | worked example, net mode |

Every check ran; none was skipped. Error measures:
- closure and duality: |lhs − residual term − rhs| / max(|rhs|, 1 m³/d), one group per package, the largest over groups, all destination/source pairs and all steps;
- boundary control: max |Σ_g F_g − 1| over cells with outflow, one group per sink term;
- DISU vs DIS and split vs single: max |a − b| / max |a| per output, the largest over all backward, forward and (split) travel-time outputs;
- tracking vs GWT: max |c − C_GWT| over all steps and active cells (and reaches), the largest over the tagging cases of `tests/test_tracking_mf6.py`;
- PRT capture: |captured particle flow / destination inflow − 1|;
- [FB13] example: max |value − published| over fraction, volume through and volume from.

## Fig. 3. Numerical dispersion

`fig3_numerical_dispersion.png` / `.pdf`

Decision: the two convergence figures of `docs/dispersion_study.md` (Figs 2 and 4, `docs/figures/dispersion_analytic_convergence.png` and `dispersion_model1_convergence.png`) are merged into one paper figure, one row per problem, with the same three columns. Both problems carry the same three messages (band width ~h^0.5, F ≥ 0.1 too large but containing the zone, F ≥ 0.5 close in area), and one figure saves a slot. It is redrawn from the study's tables (`studies/dispersion/output/a_metrics.csv`, `b_metrics.csv`) with the study's axis helper (`studies/dispersion/figures.py::_size_axis`). The Jaccard panel of the old problem-B figure is replaced by the F ≥ 0.5 area error, so both rows have the same columns. The maps (DS Figs 1 and 3) and the transient sub-steps (DS Fig. 5) stay in the supporting information.

*Figure 3. Numerical dispersion of full mixing against cell size h. Top row: problem A, uniform flow to a well with the analytical capture zone [Javandel & Tsang 1986] as reference, with flow along the grid rows (solid) and at 30° (dotted). Bottom row: problem B, a model-1-like aquifer with MF6 PRT on the 12.5 m grid as reference. (a, d) Width of the band where 0.1 < F < 0.9. For full mixing it narrows as about h^0.5 (dashed guide); face-to-face routing narrows it but keeps the rate. The cell-averaged exact zone (A) and PRT on the same grid (B) set the floor of about one cell. (b, e) Relative area error of the zone F ≥ 0.1: the zone always contains the reference zone but is too large, by 30 to 90 % in problem A and 8 to 16 % in problem B for h = 12.5 to 50 m. (c, f) Relative area error of the zone F ≥ 0.5: within 5 % (grey band) for h ≤ 50 m.*

The ranges in the caption are those of DS §5 (problem A includes the DISV grids, whose mean cell size is slightly above the nominal h).
