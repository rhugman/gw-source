# Round 2 Methods review: facts and equations

Scope: `sections/02_methods.md` (main Eqs 1–8), `si/B.md` (Text S1, Eqs S1–S9) and the Fig. 1 caption in `display/E1.md`. Checked against `src/gwsource/` (`assemble.py`, `solve.py`, `metrics.py`, `diagnostics.py`, `traveltime.py`, `tracking.py`, `config.py`), the evidence comments, `terms.md`, outline §3.2, the full draft `draft/sections/02_methods.md` and the round 1 SI (`git show 2ff9c39:docs/paper/draft_reduced/si/B.md`).

## Summary

Every equation (main 1–8, SI S1–S9) matches the code. The backward-in-time equation, Eq. (8), is right. It is row i of (Aⁿ)ᵀ: `step_matrix` puts −Δt q_ij at A[j, i] (rows `e.dst`, cols `e.src`), so row i of Aᵀ is (V_i^new + Δt(O_i + r_i)) w_i − Δt Σ_j q_ij w_j. `_backward_substeps` passes the carry `sub.old * w` from step n+1, which is V^(old,n+1) w^(n+1). The flow-imbalance correction is on by default (`TrackingConfig.flow_error_correction: bool = True`; terms.md: "On by default").

The plain reading of the bracket in Eq. (8) is also right, because V_i^new + Δt(O_i + r_i) = V_i^old + Δt × (non-storage inflow). That identity needs two facts the main text does not state, and one of them is a must-fix (finding 2).

Must-fix: 2 findings. Should-fix: 9. Minor: 13.

## Must-fix

**1. The net-accounting number in the Fig. 1a example is wrong: 10 m³/d, not 11.**
- Location: §2, "Gross and net accounting": "Net accounting adds the 5 m³/d that flow on through the well cell to the river, so the well is attributed all 11 m³/d."
- Problem: net accounting works from the cell-to-cell flows only (SI Text S1, Eq. S6). It never sees the 1 m³/d of recharge that enters the well cell itself. The throughflow of the well cell is T₆ = I^e + max(O^e − I^e, 0) = 10 + max(5 − 10, 0) = 10 m³/d. The net sources upstream (cells 0, 4, 1, 5, 2: 5 + 5 + 1 + 1 + 1, times f = 0.64, 1, 0.55, 1, 0.25) add up to the same 10 m³/d.
- Evidence: I ran `gs.backward(method_figures.graph_step(), {"well": select(package="WEL")}, TraceConfig(accounting=...))`. Gross gives destination_inflow 6.0 and F₆ = 0.545. Net gives destination_inflow 10.0, volume_from 10.0 and f₆ = 1. The evidence comment ("cell 6: 11 in") counts the gross inflow, recharge included.
- The sentence before it has a related problem: "Under net accounting, all the water passing through a destination cell counts as the destination's water". That is true only of the water passing through by cell-to-cell flow.
- Fix: "Net accounting adds the 5 m³/d that flow on through the well cell to the river. It does not see the cell's own recharge, because it uses only the cell-to-cell flows. The well is therefore attributed the 10 m³/d that enter its cell from the neighbouring cells." Or change the example so that the well cell has no recharge. Also add a check to `make_method_single` or `method_figures.py` that asserts the net value, so the number is tied to code.

**2. r_i in Eqs. (7) and (8) is not defined, and the obvious reading of it is wrong.**
- Location: §2, after Eq. (7): "where $O_i$ now leaves out the storage terms." Eq. (8) uses the same $(O_i + r_i)$.
- Problem: in the code, r_i is the cell budget error over all terms, storage included: `residual = edge_in + source - edge_out - sink + storage`. Only O_i (and s_i, d_i) drop the storage terms. A reader told that "O_i now leaves out the storage terms" will recompute r_i = I_i − O_i with storage left out of both, which gives r − S. With that r, c = 1 no longer solves Eq. (7), contrary to the next paragraph's claim. The plain reading of Eq. (8) would then also be false: "the bracket on the left is the volume of all the water that was in the cell at the start of the step or entered it during the step." That reading holds only because V^old − V^new = Δt S_i, with S_i the net storage release, holds in both volume options. Then V^new + Δt(O + r) = V^new + Δt(I′ + S) = V^old + Δt I′, where I′ is the non-storage inflow.
- Evidence: `tracking.py` module docstring ("r_i the node's flow residual (net inflow over all terms, storage included)"; "Both modes satisfy V^old − V^new = dt S within a step"); `step_flows`.
- Fix: after Eq. (7), write: "where $O_i$ and $s_i$ now leave out the storage terms, and $r_i$ is still the cell budget error of Eq. (1), with the storage terms included. The storage terms change the volume over the step by $V_i^{\mathrm{old}} - V_i^{\mathrm{new}} = \Delta t\, S_i$, where $S_i$ is the net release from storage." The bracket reading of Eq. (8) can then say "because $V_i^{\mathrm{new}} + \Delta t (O_i + r_i) = V_i^{\mathrm{old}} + \Delta t \times$ (the cell's inflow)". Name the flow-imbalance correction as the default once at Eq. (7) (see minor 13).

## Should-fix

**3. The boundary-control check does not include the cell budget errors.**
- Location: §2, checks paragraph: "Because all three checks include the cell budget errors, they hold exactly for any flow field".
- Problem: S3 and S5 carry r_i terms. The boundary-control check has none. It holds because Σ_j q_ij + Snk_i = O_i by definition (SI: "A value of 1 in every cell solves that equation, because Σ_j q_ij + Snk_i = O_i"). It also fails on closed recirculation loops, where F = 0. The main text drops the SI's "outside closed recirculation loops".
- Fix: "The closure and forward–backward checks include the cell budget errors. The boundary-control check follows from the definition of the outflow. So all three hold exactly for any flow field, outside closed recirculation loops ({SI})."

**4. The plain reading of Eq. (6) lost the hedge on the budget errors.**
- Location: "The check says that this volume equals the destination's inflow times the flow-weighted mean travel time of all the water the destination takes."
- Problem: Eq. (6) is exact, but the reading is not. The flow-weighted mean is Σ Src m / Σ Src F, and Σ Src F = Q_D + Σ F r, so the reading holds "up to the residual terms" (`traveltime.py` docstring). The round 1 SI said "once the cell budget errors are included". So does terms.md under turnover time.
- Fix: append ", apart from the cell budget error terms."

**5. "G equals the concentration that a transport model reaches at equilibrium" says more than the evidence shows.**
- Location: "The forward fraction G" paragraph.
- Problem: the evidence (tutorial 03 §9) is a GWT run with upstream weighting, no dispersion and the same grid. With dispersion, or a TVD advection scheme, the equilibrium concentration differs from G. The tutorial itself says the agreement holds "for an upstream-weighted transport model".
- Fix: "...reaches at equilibrium on the same grid, with upstream weighting and no dispersion, when the source water carries a concentration of 1...".

**6. Transient tracking is advection only, but the text says only "no dispersion term".**
- Location: "The scheme has no dispersion term."
- Problem: the brief asks that this caveat survive. The code docstring says "transport is advective only (no dispersion), upstream weighted". The text should also say that mixing still arises from whole-cell mixing and from long implicit time steps (numerical dispersion; SI "Long implicit time steps make tagged water arrive too early"). It should also note that there is no diffusion, sorption or decay. Otherwise a reader may read "no dispersion" as "no spreading".
- Fix: "Water moves by advection only. The scheme has no dispersion, diffusion, sorption or decay. Some spreading still comes from mixing whole cells and from long time steps ({SI: method in full})."

**7. The stated cause of the cell budget error has no evidence and is too absolute (writer's addition).**
- Location: "The budget of a MODFLOW model never balances exactly, because the solver stops once the heads meet a convergence tolerance. The cell budget error $r_i$ is therefore small but not zero."
- Problem: the cited evidence (`diagnostics.py`, terms.md) supports "reported, never forced to zero" but says nothing about the cause. The cause given is also only partly right. MODFLOW 6 stops on both a head-change criterion (outer DVCLOSE) and a residual criterion (inner RCLOSE). In nonlinear (Picard) runs, the conductances lag the final heads. The error comes from both. "Never" and "small" are also absolute: a linear model solved tightly can balance to round-off, and a poorly converged model can have a large error.
- Fix: "The cell budgets of a MODFLOW model do not balance exactly, because the solver stops once the heads and residuals meet convergence tolerances. The cell budget error $r_i$ is usually small but not zero." Cite the MODFLOW 6 IMS documentation (Hughes et al. 2017), or drop the "because" clause.

**8. The cross-references to Section 4 use labels that Section 4 does not have, and one points to a result Section 4 does not report.**
- Locations: "Example B (Section 4) reports their effect." and "(example C in Section 4)".
- Problem: Section 4 uses run-in heads ("Sources and area", "Transient tracking", ...), not the outline's example letters A–C. The "Transient tracking" paragraph reports the effect of the volume options ("less than 0.004") but not of transport sub-steps. Fig. 3's caption uses "examples A and B", which suggests the letters may come back. Until they do, the references have no target.
- Fix: refer to the run-in heads, e.g. "Section 4 (Transient tracking) reports the effect of the volume option", and "(Section 4, mean travel time)". Either drop the sub-steps from that sentence or add the sub-step result to Section 4 or point to the SI.

**9. "Not an independent test when both use the same water volumes" is right but imprecise (writer's addition).**
- Location: "For this reason, agreement with another method in the mean travel time of all the water a sink takes is not an independent test when both use the same water volumes".
- Problem: the overall mean of any water-conserving advective method is the water volume that ends at the sink divided by its inflow (the turnover time). Agreement therefore tests whether the two methods put the same water volume in the contributing area, not the travel times. "Same water volumes" alone is not enough, because the two methods must also agree on which water reaches the sink. Section 4 says "nearly the same water volume", which is the honest form.
- Fix: "Any method that conserves water gives this overall mean as the water volume that ends at the destination divided by its inflow. Agreement between two methods in this mean therefore tests the volume of water they attribute to the destination, not their travel times." Keep "not an independent test".

**10. The assumption behind Eq. (5) was dropped.**
- Location: Eq. (5) and the sentence after it.
- Problem: Eq. (5) needs the residence time in a cell to be independent of the route by which the water leaves. The round 1 SI said so ("Under full mixing, the time a parcel spends in a cell does not depend on the route by which it leaves"), and so does `traveltime.py` ("R_i ... is independent of the route"). Without it, a reader cannot see why τ_i is weighted by F_i.
- Fix: before Eq. (5), add "Under full mixing, the time water spends in a cell does not depend on which outflow it then takes."

**11. The "gwt" volume option matches GWT only under stated conditions (SI).**
- Location: SI, Water volume options: "Forward transient tracking with this option is unit-concentration transport in GWT".
- Problem: the evidence (SI examples table: "'gwt' volumes, one transport step per flow step", 9.8 × 10⁻¹⁴; SI A.md: "upstream weighting, no dispersion and the flow-imbalance correction on") holds only under those settings. GWT with dispersion, TVD or its own transport step lengths differs.
- Fix: "...is unit-concentration transport in GWT with upstream weighting, no dispersion, the flow-imbalance correction and one transport step per flow step".

## Minor

**12. "Outflow-weighted mean" is a weighted sum, not a mean.** Location: "In words: ... plus the outflow-weighted mean of the shares of its downstream neighbours." The weights q_ij/O_i add up to 1 − Snk_i/O_i, not 1. Fix: "outflow-weighted sum".

**13. Say that the flow-imbalance correction is the default and can be switched off.** Location: "GWT treats the error in the same way, which Langevin et al. (2022) call the flow-imbalance correction." Eqs. (7) and (8) are written with a = 1. The code allows a = 0 (`flow_error_correction`), and then the closure misses Σ Δt r·w. Fix: add "The code applies it by default."

**14. m_i is not "a mean travel time weighted by F_i".** Location: "Let $m_i$ be the mean travel time ... weighted by $F_i$." m_i = E[T 1_D] is F_i times the conditional mean. The next sentences make this clear, but the definition reads as if m were itself a time. Fix: "Let $m_i$ be $F_i$ times the mean travel time from entering cell $i$ to leaving the model through the destination."

**15. Time-step superscripts and Δt.** Main Eqs. (7)–(8) write Δt, V^new, O_i, r_i and q_ij without n, but V^(old,n+1), s_i^n and d_i^n with it. SI S7–S9 write Δtⁿ. Fix: one sentence: "All flows and volumes are those of step n." Use Δtⁿ in Eq. (8), since it spans two steps. Also say that cⁿ is the value at the end of step n and wⁿ the value at its start.

**16. The plain reading of Eq. (8), "stay in the cell into the next step", is exact only for "flow" volumes.** With "gwt" volumes the water carried into step n+1 is V^(old,n+1), not V^(new,n). The difference is the step-boundary adjustment. A parenthesis "(with the volume at the start of the next step)" is enough.

**17. The evidence pointer for Fig. 2 is wrong.** Location: evidence comment after "The three shares add up to 1": "display/E1.md Figure 2 caption (f), 30 years". Figure 2 is in `display/C.md`. Fix the path.

**18. Name the "small remainder".** Location: "The three shares add up to 1, apart from a small remainder that the code reports." The remainder is the water removed by the flow-error correction and, with "gwt" volumes, the step-boundary adjustments (`tracking.py`; terms.md "fraction still stored"). With "gwt" volumes it need not be small. Fix: "apart from a remainder, from the cell budget errors and (with "gwt" volumes) the step-boundary adjustments, that the code reports".

**19. A map of w is a fraction map, not an area.** Location: "A map of w at the start of the simulation is a time-limited contributing area". As with F, the area is the cells above a threshold. Fix: "A map of w at the start of the simulation, with a threshold, gives a time-limited contributing area".

**20. Table 1 does not exist yet.** "Table 1, row 02" and "row 03" have no target in `display/`. Check them once the table is written.

**21. The SI header comment lists old S14 twice.** It says "old S1, S2, S4, S10, S11, S12 and S14 are now main-text Eqs. 1, 2, 4, 5, 6, 7 and 8; old ... S13, S14 and S15 are now ... S7, S8 and S9". Main Eq. (8) is new (the row form of S8), and old main Eq. (1) is now Eq. (3). Fix the comment. Outline §3.2 and line 392 still use the old numbers (Eq. S9, S13, S15; "Eq. (7)" for the travel-time closure), which may mislead later agents.

**22. Symbol clash in the SI.** Bold **T** (source-group marker, S2) and T_i (net throughflow, S6), and bold **R** (inflow shares) next to r_i. Consider renaming the net throughflow (e.g. $H_i$) or the marker matrix.

**23. The 1M-cell timing claim points only at a docstring.** SI: "A model of a million cells with thousands of small loops is factorised in well under a second." The evidence is the `solve.py` docstring. `benchmarks/bench_solver.py` has the case ("1M", 10 cycles per 1000 cells, "block"). Cite the benchmark and its recorded output, or give the hardware.

**24. "One factorisation per step" (SI S7).** With sub-steps and changing volumes, `_forward_substeps` refactorises on every sub-step (`if factor is None or not steady`). Fix: "one factorisation per step, or per sub-step when the volumes change, serves every tagged group".

## Checked and correct

- Eq. (1): `CellBudget` (outflow, inflow, residual = I − O).
- Eqs. (2)–(3) and (4): `gross_backward_system`, `gross_forward_system` and the `assemble.py` docstring rows.
- Fig. 1a: F₆ = 6/11 = 0.545 (run), 11 m³/d gross inflow, 5 m³/d on to cell 7, which drains to the river.
- Eq. (5): `travel_time` ((I − P) m = τ ∘ F, same factor). The threshold is 1e-10 and the method is gross only.
- Eq. (6): `travel_time_closure`. I re-derived it from Eq. (5) × O_i.
- S1, S2: zero-outflow and zero-inflow rows are identity rows.
- S3, S4, S5: re-derived. The signs match `backward_closure`, `forward_closure` and `duality`.
- S6: `net_balance`, `net_system`.
- Eq. (7) and S7: `step_matrix`, `_forward_substeps`.
- Eq. (8) and S8: `step_matrix(...).T`, `_backward_rhs`, carry = V^old w. w^(N+1) = 0 (carry None at the last step).
- S9: `tracking.py` identity (3) and `tracking_duality`. The steady-state limits match the docstring.
- Porosity is required and has no default (`travel_time`, `TrackingConfig`). "SAVE BUDGET ALL" is the right MF6 OC syntax.
- 6.7 times the pumping (tutorial 02: 33.667 / 5 = 6.733).
- Initial water (writer's addition): terms.md and Section 4 agree that a run need not start before pumping. Fig. 3b's "water in the aquifer when pumping started" is consistent, because that example starts at pumping.
- Hedges kept: the checks test the solution, not the model or full mixing. The mean travel time is not a first-arrival time.
- Equation numbering: main 1–8 and SI S1–S9 are sequential. Every cross-reference between main text and SI points to the right equation.
- Fig. 1 caption: V and c match Eq. (7). F and the flows match the main text.
