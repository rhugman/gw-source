## Figure 2

**Figure 2.** Largest error of each verification check on the synthetic test models (markers), against machine precision (dashed line) and the test tolerance of each check (grey bars); values and error measures are in {SI: verification errors per check and model}. Upper block: steady and snapshot checks. Lower block: transient tracking checks. The exact identities (closure, forward–backward, boundary control and the water balances) reach round-off. The steady G against GWT on model 7 and the steady limits on model 10 are limited by the flow solver tolerance. "Exact" marks errors of zero.

<!-- Source: README_method.md, Fig. 2 caption and largest-error table; verification_table.md / .csv -->

## Figure 3

**Figure 3.** Numerical dispersion of full mixing against cell size h. Top row: problem A, uniform flow to a well, with the analytical capture zone (Javandel and Tsang 1986) as reference; flow along the grid rows (solid) and at 30° to them (dotted). Bottom row: problem B, a model-1-like aquifer, with PRT on the finest grid as reference, compared west of the river. (a, d) Width of the transition band (0.1 < F < 0.9); dashed guide, narrowing as $h^{0.5}$. Face-to-face routing narrows the band but keeps the rate. The cell-averaged exact zone (A) and PRT on the same grid (B) set a floor of about one cell. (b, e) Relative area error of the area F ≥ 0.1. (c, f) Relative area error of the area F ≥ 0.5; grey band, ±5 %.

<!-- Source: README_method.md, Fig. 3 caption; DS §2, §5 (problem A includes the DISV grids, mean cell size slightly above nominal h) -->

## Figure 4

**Figure 4.** Snapshots and transient tracking on the seasonal model of tutorial 08 (one layer of 1,600 cells of 50 m; 121 steps over 30 years; §4.4). A river (dashed) runs east of the supply well (triangle); constant heads on the west edge bring regional inflow. (a) Snapshots: the well's water by source, each step traced on its own flows. (b) Transient tracking forward: the well's water by tagged source (recharge, river leakage, west-edge inflow, initial water); dashed line, the initial water's share of all water pumped so far. (c) Steady backward fraction F to the well for the flows of the first step. (d–f) Backward tracking in time: for the water in each cell at the start, the fractions that leave through the well (w) or the river within 30 years, and the fraction still stored; they add up to 1. Default "flow" volumes, four transport sub-steps per flow step.

<!-- Source: README_method.md, Fig. 4 caption and notes; studies/paper/transient_figure.py (QUOTED, check_quoted). Table 2 moved to si/C.md under {SI: verification errors per check and model} (decisions_r1). -->
