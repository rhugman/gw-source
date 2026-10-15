# Review round 1 of the examples draft (paper-draft-alt), 2026-10-15

Two read-only reviews: prose and story (P), facts and cross-references (F). The orchestrator's notes are marked (O). The abstract was rewritten (commit 8e4b2e8) while the prose review ran. Check P1 against the current abstract before acting on it.

## Story and prose (P)

Overall: the draft is close to the author's voice. Sections 4.1, 4.3, 4.6 and 4.7 follow the pattern well. The weak points are the story and the length. The prose is about 10,370 words against a budget of 8,550, and every section is over.

- **P1. Abstract and §7 do not mention the ten worked examples.**
  - In the old abstract, the 81 % result appears mid-abstract, and the text ends on the Neversink overlaps. Check the new abstract.
  - In §7 ¶1, add: "Ten worked examples, each a runnable notebook, show how to use it."
- **P2. "P" has three meanings.**
  - It means the outflow shares P_ij (§2.2), the particle share (§4.1, §5 "P > 0.5"), and the capture probability (§4.9, Fig. 10).
  - "Capture" breaks terms.md, which reserves it for Leake's budget sense.
  - In §4.9, use "probability of contribution, the share of realisations in which F > 0.5". This matches the published product in §5.
  - Rename the particle share so that P means only one thing, for example "particle share" or F_PRT.
- **P3. "The limit this example shows is that …" ends six subsections.**
  - This breaks r4 D20 ("vary closers"). Fold each limit into the last paragraph in its own words, as §4.6 does.
  - Cut §4 ¶2, the pattern announcement, to one sentence.
- **P4. §6 brings in new results (dispersion tests, h^0.5, face routing 35–70 %, "within 2 % of particle tracking") and repeats numbers.**
  - Move the dispersion numbers to the §4.1 limit, or to the SI.
  - Keep §6 as advice with pointers.
  - Cut the last paragraph to a pointer to §4.4 and §4.7.
- **P5. §4.10 and §4.2 are framed as validation, not as practitioner questions.**
  - Suggested titles: "How does a new well's source mix change in its first years?" (4.10) and "How much water should a small well be credited with?" (4.2).
  - Open §4.2 with the practitioner case, reproducing an existing FlowSource protection zone.
  - In §4.10, keep one consistency number and the read-off comparison. Turn the transport-step numbers into the limit.
- **P6. §4.9 uses two priors without saying so.**
  - Say plainly that the history-matching prior is a second ensemble of 50 realisations with K at 100 pilot points.
  - Move the run counts, objective-function values and "workers" to the SI.
  - In §3.4, use "history-matched realisation" in place of "posterior realisation", which is defined only later.
- **P7. §4.5 has no check against another approach.**
  - Add: "Section 4.8 compares these snapshots with transient tracking of the same model."
  - "Travel lag" is never explained. In §2.7, write: "A snapshot assumes water reaches the well in the same step it entered. Water recharged in winter cannot appear at the well in summer. We refer to this as having no travel lag."
- **P8. Repeats across sections.**
  - Full mixing is defined in §1 and again in §2.1. Transient tracking is introduced in §1 and §2.7. Gross and net are defined in §1 and §2.4, and again in §4.2 and §6.
  - "2–3 s" on 1.68 million cells appears six times. Keep it in the abstract, §5 and §7.
  - The capability list in §1 ¶7 is repeated in §3.2 and §7 ¶4.
- **P9. §5 "buried stream cell": say why it matters.** "A buried stream cell has an SFR reach and another active cell above it. A particle cannot leave through its top face. Where the reach gains water, the stream is a weak sink, and a published particle stops there."
- **P10. Terms used before they are explained.**
  - "ensemble" and "realisation" in §1: add "a set of equally plausible versions of the model".
  - "U cluster" (§5) is never explained.
  - "the steady-state F area" (§4.8) gives no threshold.
  - "strong sink" (§4.2) is undefined.
  - "Expected area" is redefined in §5 as a cell count.
- **P11. Small breaks of the prose rules.**
  - The abstract has an appositive tail: ", which is used for protection zones in England,".
  - §7 ¶1 packs an appositive after "`gwsource`, open-source code that…".
  - §4.2 "For the supply well, a strong sink, the two accountings agree" is an appositive.
  - "Given a porosity, …" (§1, §3.3) is a participle opener. Write "With a porosity, …".
  - §4.7 "They pass 80 % and all of their water" should read "One passes 80 % of its water and the other all of it."
  - Use one wording for the GWT agreement (see F2–F3).
  - §5's last paragraph lands flat. End §5 with one sentence that points to the advice in §6.
- **Cheapest cuts.**
  - §1 (1,186/900): ¶7 repeats §3 and §5. ¶8 repeats §4.2 and §4.10. Cut the adjoint paragraph to two sentences.
  - §2 (1,635/1,100):
    - §2.4: drop the repeated MODALL and FlowSource attributions.
    - §2.2: the contributing-area paragraph repeats §1.
    - §2.7 ¶3: the MODPATH and adjoint sentences repeat §1.
  - §3 (732/600): the Neversink cost repeats §5. The PEST++ sentences belong in §4.9. The output list duplicates Table 1.
  - §4 (4,570/4,000):
    - §4.6 ¶3 repeats the definition of weight-losing particles.
    - §4.9: the PEST++ run details.
    - §4.10: the transport-step numbers.
  - §5 (698/600):
    - Cut the PRT timings and the 76-minute ensemble timing.
    - Move the net-accounting overlap sentence to the SI.
  - §6 (987/900): the dispersion results, the cost paragraph, and the last paragraph.
  - §7 (338/300): ¶5 repeats §6.
  - §8 (218/150): the list of notebook names and run times can move to the SI or the README.

## Facts and cross-references (F)

- **F1. §4.4 mixes two loop quantities.** 4.42 m³/d is the summed circulation, about 0.016 % of the throughflow. 0.08 % is the circulating throughflow, 21.9 m³/d, over the model throughflow (diagnostics.py:184, 199). Say "4.4 m³/d, 0.016 %" or "a circulating throughflow of 21.9 m³/d, 0.08 %". Notebook 04 cell 27 makes the same mistake. (O: the notebook is fixed separately on tutorials-paper-sync.)
- **F2. §7 "agreed with MODFLOW 6 GWT within the solver tolerance" leaves out the condition.** State each case:
  - steady state: 4.2 × 10⁻¹³ (§4.3);
  - transient with GWT's water volumes: 9.8 × 10⁻¹⁴ (§4.8, recharge tag, one transport step per flow step) and ≤ 1.5 × 10⁻¹⁰ (§4.10, within GWT's 10⁻⁹ tolerance).
  - With the default volumes, the difference is 1.7 × 10⁻⁴ (nb08 cell 22).
- **F3. §6 has the same gap.** Add "with GWT's water volumes". Note that 9.8 × 10⁻¹⁴ is at round-off level.
- **F4. §7 and §4.1 treat PRT agreement as validation.**
  - §4.6 says the agreement in totals and means is not an independent test: both reduce to volume over pumping, and delivery is near-certain for weight-losing particles.
  - Only the cell-by-cell comparison is informative. Reword §4.1's "gives an independent check" and §7 to match.
- **F5. §4.10 "about 840 cells per layer" is wrong.** Only layer 2 has 841. Layers 1 and 3 have 766 and 756 (nb10 cell 18).
- **F6. §8 run times are wrong.** Stored run times:
  - 01: 4 s, 03: 1 s, 04: 5 s, 05: 4 s, 06: 4 s, 07: 3 s, 08: 16 s;
  - 09: 95 s;
  - 10: about 2 to 2.5 min. The README says ~2.5 min.
- **F7. §4.9 compares two different priors.** The second prior's band, 1.098 km², is not the first ensemble's 0.77 km². Say so (see P6).
- **F8. §4.6 "456 cells with F > 0.5" is wrong.**
  - There are 457 such cells. 456 is the release cells with F ≥ 0.5, less the well cell.
  - "Edge" means 0.05 < F < 0.95 in §4.1 (372 cells) and F < 0.5 in §4.6 (676 cells). Rename one.
- **F9. Rounded shares add to 101 %.** §4.8 "52/33/16" and the snapshot shares "60/14/12/15" both do. Give one decimal or adjust.
- **F10. §6 "8–90 % more area" holds only for h = 12.5–50 m.** The study says "missed ≤ 0.1 %", not "contained".
- **F11. §6 "an error of one bin width" needs a condition.** Write "within one bin width, for values inside the histogram range" (nb09: 45 cells lie outside it).
- **F12. §5 redefines expected area.** Align it with §4.1 (Σ F × cell area), or say plainly that §5 counts start cells.
- **F13. Stale display files carry bold labels that conflict with the new numbers.**
  - A.md: "## Table S0" carries "**Table 1.**".
  - C.md: "## Figure S10" carries "**Figure 2.**" and "(Section 4.1)".
  - D.md: "## Figure S5–S9" carry "**Figure 5.**"–"**Figure 9.**".
- **F14. Stale cross-references in the SI.**
  - si/C.md: "Test models of Section 4.1". "Seasonal example model (Section 4.4, Fig. 4)" and the transient checks (Section 4.4, Fig. 4, Fig. 4b) should be §4.8 and Fig. 9. "Fig. 3" should be Fig. 13. "(Section 9)" should be Section 8. The text says "tutorials".
  - si/B.md: "Eq. 8" for travel time should be Eq. 7.
  - si/A.md: "Table 1" is now the software table. "Section 4.1; Fig. 2" and "Section 4.2 and Fig. 2" point to the old verification figure.
- **F15. Minor.**
  - §5 cites PEST++ IES as White et al. 2020, §4.9 as White 2018. Choose one, or cite both consistently.
  - The Fig. 9 caption says "Triangle: supply well", the others "Star". (O: Fig. 9 also still uses blue for F, unlike Figs 2–6. Redraw it in viridis with a white star.)
  - The abstract's evidence comments cite older sources.
- **Passed.**
  - All other numbers in §4.1–4.10, §5 and §3.4.
  - Consistency across sections for 2–3 s, 2.5/0.19 GB, 71 %/14 %/46 yr, 81 %, 0.77/0.80 km², 4 GB and 73 %/87 %.
  - Threshold disclosures.
  - Labels on the internal checks in §4.2, 4.4, 4.5, 4.7 and 4.8.
  - FlowSource and "tutorial" usage.

## Missing or orphaned SI items (F)

1. **{SI: method in full}** (§2 intro, §2.2, §2.7). Merge into it the si/B.md items "solution of the linear systems", "travel-time identity", "net accounting, fixed cells" and "water volume options". Add the derivation of Eqs (2)–(4) and (8), the flow-loop block solve, the steps of backward tracking in time, and the closure and forward–backward identities.
2. **{SI: verification on the test models}** (§3.4). The content exists as {SI: verification errors per check and model} in si/C.md. Rename the heading or the marker. Include the old verification figure (Figure S10).
3. **{SI: example and test models}** lacks:
   - the shared single-layer model;
   - the 3-year, 3-steps-per-season snapshot model;
   - the Voronoi and XT3D set-ups;
   - the field zone;
   - the SFR/DRN/MVR and MAW models;
   - the ensemble and PEST++ set-up, including the run counts moved out of §4.9;
   - the Bedekar rebuild choices (units, well-screen layer, 300 steps of 30.4 d).
4. **{SI: Table 1 notes and sources}.** The method-comparison table it annotates (display/A.md) needs a Table S label and a heading that no longer says Table 1.
5. **Orphaned.** These are no longer cited from the main text. Delete them, or cite them from the Neversink SI text:
   - {SI: per-well gross and net}
   - {SI: diagnosis of the first PRT runs}
   - {SI: scenario medians}
   - {SI: growth mechanism}
   - {SI: one convention at a time}
   - {SI: faster growth of weight-losing particles}
   - The pumping scenarios are dropped from the paper.
6. Regenerate si/numbering.md for the new layout.

## Figures (O)

- §4.3 cites Fig. 4a for pumping drawing the water table below the river stage. Fig. 4a shows G only. Re-point the citation or reword.
- Fig. 4a outlines the river cells. The caption says "Blue cells: river".
