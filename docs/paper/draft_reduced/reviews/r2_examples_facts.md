# Round 2 review: Sections 4 and 5, facts and numbers

Scope: `sections/04_examples.md` (examples A, B, C, Table 1), `sections/05_neversink.md`, captions `display/C.md` (Fig. 2), `display/AB.md` (Fig. 3), `display/N.md` (Fig. 4), and `si/G_examples.md` (Text S3) and `si/D.md` (Text S4). Context: `sections/02_methods.md`, `sections/03_software.md`, `sections/06_tradeoffs.md`, `outline.md` §3.4–3.5, `terms.md`.

Method: every number was checked against its evidence comment and the source named there. For the notebooks I read the stored JSON outputs of the cited cells (all ten notebooks). For Neversink I read `docs/neversink_study.md` (NS) in full and `docs/paper/draft/reviews/r4_memory.md`. I rebuilt the notebook 01 model with the worktree's `src/gwsource` to check the two statements read off Fig. 2a (finding 11). For the notebook 08 tagged-water balance I traced the notebook history (finding 2).

Most numbers check out. The findings below are the exceptions. A list of what was verified is at the end.

## Must-fix

### 1. SI Text S3: the two volume options' year-30 shares are swapped

- **Location.** `si/G_examples.md`, transient checks: "With "gwt" volumes, about 5,300 m³ of the 45.6 million m³ of initial water is lost over 30 years. The year-30 share of initial water is then 0.5166, against 0.5167 with the default "flow" volumes."
- **Problem.** The notebook gives the reverse: 0.5166 with "flow" and 0.5167 with "gwt". Section 4 has it right ("0.5166 with the default volumes and 0.5167 with GWT's volumes"), so the SI now contradicts the main text. The error goes back to the full draft (`draft/si/C.md` line 252).
- **Evidence.** `tutorials/08_transient_tracking/08_transient_tracking.ipynb` cell 20 output: row "well water that is initial, year 30": flow (default) 0.5166, gwt 0.5167.
- **Fix.** "With "gwt" volumes, about 5,300 m³ of the 45.6 million m³ of initial water is lost over 30 years. The year-30 share of initial water is 0.5167 with these volumes and 0.5166 with the default "flow" volumes." Add "with one transport step per flow step", because cell 20 runs both modes with `substeps=1` (see finding 5).

### 2. The open item on the tagged-water balance: 8.0 × 10⁻¹⁶ is no longer backed by any stored output

- **Location.** The `si/G_examples.md` check table, row "tagged-water balances, one transport step per flow step | 8.0 × 10⁻¹⁶". Against it: Table 1 row 08, "Tagged-water balances to 9.9 × 10⁻¹⁶".
- **Settled.** Each number was right for its own set-up, but only one is backed today.
  - 8.0 × 10⁻¹⁶ was printed by notebook 08 cell 12 before commit `ab7f1d8` (2026-10-15, "Tutorial 08: four transport sub-steps in the main runs"). At that time the main run used the default of one transport step per flow step. The diff of `ab7f1d8` shows the line `largest relative error of the tagged-water balances: 8.0e-16` replaced by `9.9e-16`. The SI row was written from the older output (commit `4b750f2`, evidence "tutorial 08 §§5, 6").
  - 9.9 × 10⁻¹⁶ is the current cell 12 output, for the main run with `TRANSPORT_SUBSTEPS = 4` and "flow" volumes. Table 1 row 08 is correct.
  - No current cell computes the tagged-water balance of a one-step run. The 8.0 × 10⁻¹⁶ cannot be reproduced from the shipped notebook, and its evidence pointer is stale.
- **The same table mixes set-ups without saying so.** "forward against backward … 4.3 × 10⁻¹⁶" (cell 18) and "backward closure 0" (cell 16) come from the main run with four sub-steps. "… must add up to 1 in every cell 2.5 × 10⁻¹¹" is cell 20's "largest |unaccounted fraction|" (2.625 × 10⁻¹¹) of the one-step "flow" run (cell 14 prints only "1.0000 to 1.0000" for the main run). The GWT row, 9.8 × 10⁻¹⁴, is the one-step "gwt" run and says so.
- **Fix.** Change the row to "tagged-water balances, main run (four transport sub-steps) | 9.9 × 10⁻¹⁶". Add one sentence above the table: "The rows use the main run, with four transport sub-steps and "flow" volumes, except the GWT row (one step per flow step, "gwt" volumes) and the sum-to-1 row (one step per flow step, "flow" volumes)." If a one-step balance is wanted, add a print to cell 20 and quote that.

### 3. The caveat that weight-losing particles are not an independent reference is missing from the main text

- **Location.** §4 example A, where the particles are introduced ("This is the particle counterpart of gross accounting… We refer to these as weight-losing particles."), and the conclusion drawn from them ("The F > 0.1 area holds every particle cell, so here it serves as a cautious outer limit"). §5: "Weight-losing particles (Section 4) give a closer comparison, because they lose water at each sink as full mixing does. The F > 0.1 area holds 87 % of the 691 start cells…".
- **Problem.** This is a required caveat. It is now only in SI Text S4. The particles lose weight at each sink by the full-mixing shares (`src/gwsource/prt.py` docstring: "multiply particle weights by the full-mixing survival of every cell they pass"). So they share full mixing at the sinks, and they measure only the spreading that full mixing adds between sinks. §5 states the shared rule as a strength ("closer comparison") and leaves out what follows from it. On the example model this matters: the river is a weak sink wherever it gains, and the dispersion study compares problem B (this model) only west of the river for that reason (`draft/si/C.md`, problem B). §5 has also lost the second caveat on the same number: the 87 % is an upper bound, because only cells with F > 10⁻⁶ were seeded.
- **Evidence.** NS §5, the two caveats below Table 3a ("the reference shares full mixing at the sinks and is not an independent advective zone. The comparison measures only the spreading that full mixing adds between sinks"; "The 87 % coverage is therefore an upper bound"). `si/D.md` repeats both.
- **Fix.** §4, after "We refer to these as weight-losing particles.", add: "Because they lose weight at each sink by the full-mixing shares, they are not an independent particle reference. They show how much full mixing spreads water between sinks." §5: replace the "closer comparison" sentence with "Weight-losing particles (Section 4) lose weight at each sink as full mixing does, so they measure only the spreading that full mixing adds between sinks." After the 87 %, add "This share is an upper bound, because the particles started only in cells with F > 10⁻⁶ ({SI: the Neversink comparison})."

### 4. §5 states as fact a reading that the source says the evidence does not support

- **Location.** §5: "Net accounting counts a weak-sink well's water much as a stopping particle does. It raises the F > 0.5 overlap only from 0.41 to 0.44."
- **Problem.** NS §2, below Table 2b, puts this as a hypothesis and rejects it: "One reading is that the stopping rule acts like net accounting at the wells … The per-well counts do not support this, since gross accounting is closer at the weak-sink wells, and we have not tested it further." The draft states it as fact. It also uses the claim to imply that weak-sink wells explain little of the gap.
- **Fix.** Describe what net accounting does, not what it resembles: "Net accounting credits a weak-sink well with all the water that enters its cell. It raises the F > 0.5 overlap only from 0.41 to 0.44, and per well it moves the weak-sink wells further from the published counts." Evidence: NS Tables 2b and 2c (U___7 94 → 214 cells against 58 published).

## Should-fix

### 5. §4: the volume-option comparison does not say it uses one transport step per flow step

- **Location.** §4 example B: "Between them, the forward fractions differ by up to 1.9 × 10⁻⁴ and the backward fractions by up to 3.7 × 10⁻³. The share of initial water in year 30 is 0.5166 with the default volumes and 0.5167 with GWT's volumes."
- **Problem.** Three sentences earlier the text says that the tracking uses four transport sub-steps per flow step. A reader will take these numbers to be for the four-sub-step run. They come from cell 20, which runs both modes with `substeps=1` (`config_flow1 … # substeps=1`, `config_gwt`). The main run's year-30 share is 0.516 (cell 8). The SI says "With one transport step per flow step" for the 1.9 × 10⁻⁴ and 3.7 × 10⁻³. The main text has dropped it.
- **Fix.** "With one transport step per flow step, the forward fractions of the two options differ by up to …".

### 6. §5: "only with all three settings" is more than the reproduction runs test

- **Location.** §5: "PRT on the same flows reproduces the published area (overlap 0.998) only with all three settings."
- **Problem.** The reproduction table (NS §3, `mp7_reproduction.csv`) changes two settings, faces and draping: 0.998, 0.96, 0.65, 0.62. Stopping at weak sinks stays on in all four runs. The runs that do not stop particles (flow-weighted, weight-losing, 0.62) also differ in how particles are released, so they do not isolate the stopping rule.
- **Fix.** "PRT on the same flows reproduces the published area (overlap 0.998) with these settings. Without the top-face setting the overlap falls to 0.65, and without draping to 0.96."

### 7. §5: the top-face setting applies only where the top face is open

- **Location.** §5: "Recharge and stream flows enter a cell through its top face."
- **Problem.** The published runs put these flows on the top face only where it is a model boundary: all recharge cells and 10,107 of the 12,316 reaches. The 2,209 buried reaches keep the flow spread through the cell (NS §3 "Faces"; §2 "End states"). The next paragraph depends on this, because buried stream cells stop particles for exactly that reason. As written, the two paragraphs disagree.
- **Fix.** "Recharge and stream flows enter a cell through its top face where no active cell lies above."

### 8. §5: "particle runs that conserve water" needs defining, and the runs left out should be named

- **Location.** §5: "Among particle runs that conserve water, the settings alone move the overlap from 0.62 to 0.998… Full mixing lies below that range."
- **Problem.** The "below, not within" caveat is correctly in place. But the range 0.62–0.998 is made mostly of the published-start runs, which use one unweighted particle per start and carry no water (column "–" in the SI D table). Calling them runs "that conserve water" is loose. The SI D table also lists the runs that lose weight only at the wells (0.29) and released at the water table (0.39). A reader who sees them will find full mixing (0.30–0.41) inside 0.29–0.998, which is what NS §3 and §5 still say ("lies inside the range"). The main text should say why those two runs are left out: they deliver 260 % and 66 % of the wells' inflow (NS "Why the first PRT runs…" table).
- **Fix.** "Leaving out the particle runs that do not deliver the wells' inflow (2.6 times and 0.66 times it; {SI: the Neversink comparison}), the settings alone move the overlap from 0.62 to 0.998." Also fix the "inside that range" wording in NS §3 (line 186) and §5 (line 200), or note there that it includes the non-conserving runs, so that the archived study does not contradict the paper.

### 9. §5: the reason given for "not like with like" does not hold

- **Location.** §5: "These times do not compare like with like, because one PRT run follows one particle convention for all wells, while one trace gives F, the volumes and the checks for every group."
- **Problem.** The same study evaluates one PRT run for every well (NS §3, `prt_sources_by_well.csv`, "one PRT run evaluated for every well"). So per-well results do not set the two apart. The real differences are what each run gives: the trace gives F in every cell plus the checks, while PRT gives P only in seeded cells and needs the trace to seed it. The sentence on seeding is already there. Also, PRT memory was not measured, so the memory figure has no PRT counterpart (the evidence comment says so, but the text does not).
- **Fix.** "These times do not compare like with like. One trace gives F in every cell, the volumes and the checks. A PRT run gives particle shares only in the cells it seeds, and the weight-losing runs needed the trace first…". Optionally add "PRT memory was not measured."

### 10. §4 example C and §6: "depend much less on mixing" is contradicted by §5

- **Location.** §4 example C: "These answers depend much less on mixing than the edge of an area does, so a practitioner can use them with more confidence." The same sentence is in §6: "A well's water by source and the mean travel time of all its water depend much less on mixing than the edge of its area does (Section 4)." Also §4: "In the test problems of {SI: numerical dispersion test problems}, the shares by source were the same to three digits under full mixing, face-to-face routing and particles."
- **Problem.** On Neversink the split by source changes from 57/43 to 49/51 between full mixing and weight-losing particles (§5; NS §3). That is an 8-point shift, although the totals agree within 2 %. The general claim rests on two single-layer synthetic models. The dispersion evidence comes from one problem with two sources (problem B, RIV/RCH, on one DIS grid; `docs/dispersion_study.md` §2 "Shares of the well water"), not from "the test problems".
- **Fix.** §4: "On the example model these answers depend much less on mixing than the edge of an area does. Section 5 shows that on a regional model the split by source can still shift by several percentage points." Dispersion sentence: "In the test problem with a river and recharge ({SI: …}), the shares by source were the same to three digits under full mixing, face-to-face routing and particles on the same grid." §6: add "on the synthetic models", or cite §5.

### 11. Example C and SI Text S3: "recharge that reached the stream through the drains" is narrower than the notebook

- **Location.** §4: "that water splits into 129 m³/d of inflow at the upstream end of the stream and 126 m³/d of recharge that reached the stream through the drains." `si/G_examples.md`: "That recharge reached the stream through the drains and the mover."
- **Problem.** The notebook says only that "the extra 126 m³/d is recharge that the cells-only trace lost at the drains or the stream" (07 cell 21). Reach 2 gains, and the reaches below it lose to the aquifer near the well (07 cell 14, gaining reaches [2, 22–40]). So part of the 126 m³/d can be recharge that discharged to the stream directly. The notebook also shows that the mover route carries 188 m³/d of the well's water, more than 126 m³/d, because of a flow loop. The route is not a simple drain-only path.
- **Fix.** "…and 126 m³/d of recharge that had discharged to the drains or the stream."

### 12. The same Neversink cost numbers appear in §3, §5 and the abstract

- **Location.** §3: "The regional model of Section 5 has 1.68 million cells. On an Apple M4 Max with 64 GB of memory, one trace of its eight wells, alone and together, took 2–3 s… Its memory peaked at 2.5 GB." §5: "a steady-state MODFLOW 6 model of 1.68 million cells… One trace of nine destination groups (each well alone and all eight together) took 2–3 s and peaked at 2.5 GB of memory. Each further group added about 0.19 GB." The abstract also gives 1.68 million cells and 2–3 s.
- **Problem.** Section 3 and Section 5 each state the same three numbers. §3's evidence comment says the 0.19 GB was "left out for length", but §5 now has it. The machine is named in §3 and in SI D but not in §5, where the cost is discussed.
- **Fix.** Keep the cost in §5, with "(Apple M4 Max, 64 GB)", next to the PRT comparison. Cut §3 to one pointer: "On the regional model of Section 5, a trace of eight wells took seconds." Or the reverse: keep §3, and in §5 say only "The trace cost is given in Section 3" before the PRT comparison. Either way, give each number once.

### 13. Table 1 row 07: the stream wording

- **Location.** Table 1 row 07: "with stream reaches traced as cells or not", "with the stream reaches as source and sink terms or as cells".
- **Problem.** The Methods and `terms.md` wording is "traced as cells of their own" or "the stream network". "As cells" on its own is easy to confuse with NS's "streams as cells", which means the opposite: reaches left as source and sink terms. The §5 evidence comments use the NS sense.
- **Fix.** "with stream reaches traced as cells of their own or not"; "…as source and sink terms or traced as cells of their own".

### 14. §5 no longer cites the SI figure behind the 87 %

- **Location.** §5, the 87 % sentence. `{SI: Neversink particle area and ensemble mean F}` is now cited only inside the HTML comment of `display/N.md`.
- **Problem.** Panel (a) of that SI figure is the F > 0.1 area against the weight-losing particle area (495/86/1,133 cells in the window; 602/89/1,537 in the whole model). The round 1 text cited it, and nothing in the main text points to it now. Its panel (b), the ensemble mean F, also has no citation.
- **Fix.** Add "({SI: Neversink particle area and ensemble mean F}a)" after the 87 %. If panel (b) stays, add a short ensemble clause where §5 gives the ensemble cost, for example "Mean F over the realisations correlates with the published probability of contribution at r = 0.80 ({SI: …}b)" (NS §6, Table 4).

### 15. The two statements read off Fig. 2a are correct but understated; replace the "read off the figure" evidence

- **Location.** §4 example A: "The F > 0.1 area reaches the west edge of the model…" and "The area also extends east of the river."
- **Check.** I rebuilt the notebook 01 model (`hbd.build_quickstart`, worktree `src`) and traced the well. The counts match cell 16 (630 cells with F > 0.1, 457 with F > 0.5).
  - West edge: F > 0.1 is in column 1 in rows 12–30, and F > 0.5 in rows 14–28 (1-based). F = 1.0 in the column-1 cells of rows 18–24. So both contours reach the west edge, not only F > 0.1.
  - East of the river (columns 32–40): 105 cells with F > 0.1 and 69 with F > 0.5. Both areas run from the river to the east edge of the model (column 40), in a band centred on the well's row. The losing reaches are rows 19–23 (03 cell 12; my run gives the same, 0-based 18–22). This fits the stated mechanism.
- **Fix.** Either "Both the F > 0.1 and F > 0.5 areas reach the west edge…" and "The area also extends east of the river, to the east edge of the model", or keep the wording. In either case, add a print to notebook 01 §5 (columns reached, cells east of the river), so that the evidence is a stored output rather than "read off the figure".

## Minor

### 16. Release threshold of the particles

§4: "Particles start from every source term in cells with F > 0." The code seeds cells with F > 10⁻⁶ (`PrtConfig.fraction_threshold = 1e-6`, `prt.py` line 138; notebook 01 cell 24 uses the default). §5 says 10⁻⁶. Fix: "in cells with F > 10⁻⁶".

### 17. Table 1 row 10: the 0.6 covers the first 15 years only

"Within 1.3 percentage points of the published curves (0.6 with 7.6-day sub-steps)". The sub-step run covers only 15 years (10 cell 16; §4 text says "over the first 15 years"). Fix: "(0.6 up to year 15 with 7.6-day sub-steps)".

### 18. Table 1 row 05: the 1 × 10⁻¹⁴

"Statistics agree to 1 × 10⁻¹⁴". Min and max are checked with `atol=1e-14`. The mean is checked with `rtol=1e-12, atol=1e-14` (05 cell 25). Fix: "to 10⁻¹² or better", or "min and max to 10⁻¹⁴".

### 19. Table 1 row 09: one check has no agreement value

"Exact quantiles against quantiles from histograms" is listed as a check, but the Agreement column gives nothing for it. Notebook 09 §6: "every histogram quantile is within one bin width of the exact one". Fix: add "Histogram quantiles within one bin width".

### 20. Example B: 67.7 % against 68 % is the forward–backward identity

"backward tracking attributes 67.7 % to initial water. This matches the 68 % of the forward run." This agreement is the forward–backward check (4.3 × 10⁻¹⁶, cell 18), not separate evidence. Fix: "…as the forward–backward check requires."

### 21. Mean travel time: to the well or to the well cell

Methods Eq. (4) defines t to leaving through the destination: 46.0 years for all water, 16,791 d = volume / pumping (06 cells 14 and 16). §4 quotes the time to entering the well cell (45.9 years) and says why. But "Any method that conserves water gives the mean travel time of all the water as the volume of water bound for the sink divided by its inflow" is exactly the 46.0-year quantity, while the comparison uses 45.9. The Fig. 2d caption ("Mean travel time where F > 0.5") does not say which time is mapped. Fix: name the quantity in the caption. In the "not an independent test" sentence, say the identity holds for the time to the well, and that the time to the well cell differs from it by the residence in the well cell (0.1 years here).

### 22. Evidence path

§5 and SI D cite `reviews/r4_memory.md`. The file is `docs/paper/draft/reviews/r4_memory.md`, not `draft_reduced/reviews/`. Fix the path in the comments.

### 23. Smaller repeats

- (White 2018; White et al. 2020) is cited both in §4 (row 09 paragraph) and §5. The second could go.
- "Transient tracking has so far been tested on synthetic models only" is in both §4 and §6.
- SI Text S3 says it backs "the rows of Table 1" that the examples do not cover in full. It still restates numbers that §4 already gives: 39 %, 45 m³/d, the 14/15/71 % split and 1 × 10⁻⁶ ("Where each source's water goes"); 0.59/1.35 km² and 0.52/0.93/0.41 km² (seasons); 32 %, 129 and 126 m³/d (streams); 1.10/0.35 km² and 93/79 % (ensembles). Trim these paragraphs to what is new: the GWT check of row 03, the edge width and XT3D, the storage reasoning, the multi-aquifer well.

### 24. "reproduces its numbers and figure"

§4: "Each example ships with the code as a Jupyter notebook that builds its model and reproduces its numbers and figure." Figs 2 and 3 are drawn by `studies/paper/gallery_figure.py`, not by the notebooks. Each notebook draws its own figures. Fix: "…reproduces its numbers and draws its figures."

### 25. Fig. 4b against the whole-model count

§5: "The F > 0.1 area holds 73 % of them (711 of 980; Fig. 4b)." Fig. 4b shows a window (538 of the 688 window cells, 78 %). The caption says so, but the text pairs a whole-model count with a window figure. Fix: "(711 of 980; Fig. 4b shows the 688 cells around the U wells)", or leave the figure pointer to the caption.

### 26. Outside the reviewed files, noted for the orchestrator

- Abstract: "Tracing is cheap enough to include in history matching and similar analyses." §4 row 09 says running the trace inside each PEST++ run is untested. The abstract claim should be about cost only: "cheap enough to run on every realisation".
- §3 still gives "The MODFLOW 6 run of that model takes 44 s", although outline §6 records the decision that the MODFLOW 6 run time leaves the abstract and Section 3.

## Caveats from round 1: status

| caveat | status |
|---|---|
| closure check tests the solution, not the edge | kept (§4 example A) |
| travel-time agreement not an independent test | kept (§4 example C; Table 1 row 06) |
| weight-losing particles share full mixing at weak sinks | **lost from the main text** (finding 3); in SI D only |
| 87 % is an upper bound | **lost from the main text** (finding 3); in SI D only |
| Neversink mixing reason is an inference | kept ("We infer that the main reason…"; source split "We infer, without tracing it cell by cell") |
| full mixing lies below, not within, the conserving particle runs | kept ("Full mixing lies below that range"); definition of the range needs care (finding 8) |
| narrower posterior not necessarily correct | kept (row 09 paragraph) |
| one synthetic case | kept |
| tracing inside each PEST++ run untested | kept (abstract overreaches, finding 26) |
| GWT agreement is a consistency test | kept (§4 example B) |
| one layer cannot hold young over old water | kept |

## Numbers verified

These numbers match their sources.

- **Notebook 01** (cells 4, 16, 20, 22, 24): 1.143 and 1.575 km², 1.173 km², 568.6/118.1/113.3 m³/d and 0.711/0.148/0.142, closure 0.0, 18,208 particles from 1,133 cells, 799.9 m³/d, 1.168 km², −2.1 %, +34.9 %, 14 and 0 cells outside, 0.164 over 372 cells. Grid, rates and the 100 m river offset.
- **Notebook 03** (cells 2, 10, 12, 16, 18, 24): a 300 m × 300 m field, 45.0 and 17.7 m³/d (39 %), losing rows 19–23, 2.8 × 10⁻⁹ to 4.7 × 10⁻⁷ m³/d, 4.2 × 10⁻¹³.
- **Notebook 04** (cells 15, 17, 22, 37): DISU 0.0, 1.178 against 1.173 km², 121 and 186 m, 3.3 × 10⁻¹⁶, x = 1,425 m and 25 m.
- **Notebook 05** (cells 4, 6, 8, 9, 12, 21, 25): recharge and pumping factors, 640–1,120 m³/d, 0.592 and 1.350 km², storage share 0.525, 36 steps, 0.52/0.93/0.41 km², 7.2 × 10⁻⁷ m³/d.
- **Notebook 06** (cells 14, 16, 20, 22, 24): 2.1/41.6/108.4/45.9 years, 45.7 years and −0.5 %, −2.1/+2.1/−20.1 %, 456 and 676 cells with medians 0.96 and 5.72, 0.098/0.122 and 0.455/0.465 km².
- **Notebook 07** (cells 8, 16, 20, 33): 255.2 m³/d and 0.319, 129.4 and +125.8 m³/d, 1.4 × 10⁻¹⁶ and 0.0, 2.07 × 10⁻¹³.
- **Notebook 08** (cells 2, 4, 8, 10, 12, 16, 18, 20, 22, 24): 121 steps, 0.60 and 0.15, 0.516/0.329/0.155, 0.976/0.813/0.677, 11.4 m and 64 years, 8,766,800 m³ and 0.677, 4.3 × 10⁻¹⁶, 9.8 × 10⁻¹⁴, 1.9 × 10⁻⁴ and 3.7 × 10⁻³, 0.0078/0.0049/0.0042, 9.9 × 10⁻¹⁶.
- **Notebook 09** (cells 18, 22, 26, 28): 1.098 and 0.350 km², 79.268 and 93.415 %, 86.099 and 87.468 %, bit-identical serial and parallel runs, 40 observations, 61 s for PEST++ IES.
- **Notebook 10** (cells 8, 10, 12, 16, 18): 0.482/0.292/0.225, 4.4 × 10⁻¹¹ to 1.5 × 10⁻¹⁰, 1.3 points at year 10, 6,829 cells.
- **Notebook 02**: 33.67 and 5.00 m³/d, Foley and Black to 10⁻¹⁴.
- **Run times**: 01 4 s, 02 2 s, 03 1 s, 04 7 s, 05 2 s, 06 4 s, 07 3 s, 08 10 s, 09 71 s. So eight of the ten ran in 10 s or less.
- **Neversink** (NS and `r4_memory.md`): 1,683,680 cells, 3,671 m³/d, 358 realisations, 122,021 start cells and 980 published cells, 2–3 s, 2.52 GB, 0.19 GB, 1 × 10⁻¹² and 3 × 10⁻¹², about 30 s, 5 and 13 min, 1.5 and 6 GB, 122,112 and 488,448 particles, 30,180 cells, 9 s. Overlaps 0.998, 0.96, 0.65, 0.62, 0.41, 0.30, 0.44, 0.28. Mean F 0.42, 711 of 980, 87 % of 691, 89 cells, 227 of 3,736 m³/d, 26,828 and 466 particles, 57/43 and 49/51, +344 and −279 m³/d, 2,100 and 1,571 m³/d, 76 min, r = 0.80, sum ratio 0.90.
- **Fig. 4**: the window counts 688, 538/150/1,090 (`figures/README.md`), and the whole-model counts 711 + 1,428 = 602 + 1,537 = 2,139.
- **SI D table**: every row matches NS Tables 1, 2b and 3 and the reproduction table.
- **Fig. 2 and Fig. 3 captions**: the quoted numbers match the scripts' QUOTED values and the notebooks.
- **Cross-references**: the Fig. 2 panel letters in the text and Table 1, Fig. 3a/3b, Fig. 4a/4b, Eq. (5), "the expected area of Section 2", "the two volume options of Section 2" and every SI pointer used resolve to existing items.
