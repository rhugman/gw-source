# SI review, round 1: structure and duplication

Scope: docs/paper/export_reduced/supporting_information.md (69 pp) against the main text of paper_draft.md. Review only; no files were edited.

Current page budget, from the PDF: Text S1 6 pp, Text S2 9 pp, Texts S3–S12 8 pp, Text S13 9 pp, Texts S14–S15 2 pp, Tables S1–S6 14 pp, Figures S1–S20 19 pp, references 2 pp.

## 1. Main findings

1. **The SI is grouped by item type, not by topic.** Every Text comes first, then every Table, then every Figure. The figure for Text S3 is Figure S14, about 45 pages later. The builder numbers the figures the main text cites first, then the rest in file order. So the Neversink figures (S9–S13) come before the example figures (S14–S20), even though the example texts (S3–S11) come before the Neversink text (S12). Table S3, a Neversink table, is numbered third only because Section 3 cites it for one run time.
2. **The Neversink material is spread over 11 items:** Figures S6 and S9–S13, Tables S3, S5 and S6, and Texts S12, S14 and S15, plus "Terms" in Text S2. Figure S6 repeats panels from other figures. Panels (a, b) are main Fig. 3, (c) is in S12d–f, (d) is in S13d–f and its inset is S10. Figure S9a repeats a column of Table S5, and S9b–d repeat S12d–f. The one-row-south offset is explained four times: S6 and S13 captions, the Table S6 caption, and Text S14. The 4,621 / 608 / 70 m³/d numbers appear under both Table S5 and Figure S9. Text S15 repeats the release-height rows of Table S3.
3. **Each model is described twice.** Text S2 describes each example model, and the example text then describes it again. Examples: the seasonal model (S2 and S8, almost word for word), the Voronoi grid (S2 and S7), the stream, drains and MAW (S2 and S10), the Bedekar model (S2 and S11), and the three-layer model (S2 and S3).
4. **The example texts restate the main text.** Six texts open with the same sentence ("This text gives in full one of the worked examples…"). Each then repeats the main-text headline numbers: 33.7 m³/d, 6.7× and 1 × 10⁻¹⁴ (S3); 39 % and 4.2 × 10⁻¹³ (S6); 186 against 121 m (S7); 0.59 and 1.35 km² (S8); 45.7 against 45.9 years and "not an independent test" (S9); 32 % and 2 × 10⁻¹³ (S10); 48.2/29.2/22.5 % (S11). Several also repeat a motivation paragraph that Section 4 already gives.
5. **Text S1 overlaps the other texts.**
   - The FlowSource flow-loop paragraph (loops reported as rare, smallest flow deleted) is in S1, again in S7 and again in the S13 notes.
   - The volume-option differences (1.9 × 10⁻⁴ and 3.7 × 10⁻³) are in both S1 and S4.
   - The travel times on test model 1 (9,607 and 9,574 d) are in both S1 and the notes under Table S4.
   - Transport sub-steps are covered in four places: S1, S4, S11 and the Figure S7 item with panels (m, n).
6. **Table S1 and Text S13 (11 pp) say most things twice.** "Notes on the cells" and "Sources by column" cover the same entries. For example, weak-sink accounting in FlowSource is in both, and so are the MODALL entries. The MODALL, Chowdhury and McLane paragraphs are a literature review, not table notes.
7. **The numerical-dispersion set-up sits under a figure.** It is in the Figure S7 item. The Figure S8 caption then sends the reader to "Figure S7" for the methods. Panels (a–d) of S7 (flow aligned with the rows) add little to S8. Panels (m, n) are about time steps, not dispersion.
8. **Verification is given three times.** Figure S2 plots the per-case errors. Table S4 gives them again as the largest error per check, and a third time in two per-model tables.
9. **Example figures repeat the gallery (main Fig. 2).** The redundant panels are:
   - S3a = 2a and S3c = 2b
   - S4c ≈ 2a (the first step is the pumped steady state) and S4d = 2f
   - S5b = 2g
   - S15b = 2c
   - S16a = 2a and S16b = 2h (keep its inset)
   - S17e = 2e
   - S18a = 2d

   Also, Figure S1b is main Fig. 1, and S1c only repeats the numbers in Text S3.

## 2. Merge plan

| Current items | New item | Contents | Est. pp (now) |
|---|---|---|---|
| Table S1, Text S13 | Table S1 | Table with its footnotes; one short source paragraph per column with page or section numbers. Cut "Notes on the cells" and the MODALL literature paragraphs | 3.5 (11) |
| Text S1, Fig S1, S2 "eight-cell example" | Text S1, Fig S1 | Method. One copy of the flow-loop and sub-step text. Figure S1 keeps panels (a, d) only | 5.5 (7) |
| Table S2, S2 "Test models", Fig S2, Table S4, run times under Table S3 | Text S2, Table S2, Fig S2, Table S3 | Software, cost and verification. Keep the per-check error table. Move the per-model tables to the data archive | 6 (10) |
| S2 common settings, shared model, PRT, notebooks; Fig S3 | Text S3, Fig S3 | Example models in common; Fig S3 = particle share panel only | 2 (3) |
| Text S3, Fig S14, S2 three-layer and F&B | Text S4, Fig S4 | Small well. Model described once | 1.5 (2) |
| Text S4, Fig S4, S2 30-year model; sub-step results from S1, S11 and S7m–n | Text S5, Fig S5 | Transient tracking checks. Fig S5 = old S4 (a, b, e, f) | 2 (2.5) |
| Text S5, Fig S5, S2 ensemble | Text S6, Fig S6 | Ensemble set-up. Fig S6 = old S5 (a, c) | 2 (2.5) |
| Text S6, Fig S15, S2 field and GWT | Text S7, Fig S7 | Forward trace. Fig S7 = old S15 (a, c) | 1.3 (2) |
| Text S7, Fig S16, S2 grids | Text S8, Fig S8 | Grids. Fig S8 = old S16c plus the two insets. Drop the loop paragraph | 2 (2.5) |
| Text S8, Fig S17, S2 seasonal model | Text S9, Fig S9 | Seasons. Fig S9 = old S17 (a–d) | 1.3 (2) |
| Text S9, Fig S18 | Text S10, Fig S10 | Travel time. Fig S10 = old S18b | 1 (1.5) |
| Text S10, Fig S19, S2 networks | Text S11, Fig S11 | Unchanged figure | 2.2 (3) |
| Text S11, Fig S20, S2 Bedekar | Text S12, Fig S12 | Unchanged figure | 2.3 (3) |
| Texts S12, S14, S15, S2 Neversink terms; Tables S3, S5, S6; Figs S6, S9–S13 | Text S13, Tables S4–S5, Figs S13–S15 | One Neversink text: terms, the end-states table, the offsets explained once, PRT release height cut to two sentences, and the notes now spread under the tables. Table S4 = old S3 plus old S6 as a lower block. Table S5 = old S5. Fig S13 = old S10 as panel (a) plus old S11. Fig S14 = old S12. Fig S15 = old S13. Drop old S6 and S9 | 8 (14) |
| Fig S7 item, Fig S8 | Text S14, Fig S16 | Dispersion set-up and results as a text. One figure: old S8 plus old S7 (e–l) | 2.5 (3.5) |
| References | References | Fewer entries after the Text S13 cut | 1.5 (2) |

**Total: about 44 pp, down from 69.** This counts structural cuts only. Content cuts from the other reviews come on top of it.

## 3. Proposed table of contents

Each item is placed after the main-text paragraph that first cites it, or after its parent text. Figures and tables sit directly after their text.

1. Table S1. Comparison of methods, with notes and sources — 3.5
2. Text S1. Method in full; Figure S1. Schematic — 5.5
3. Text S2. Software, cost and verification; Table S2. Inputs, selections and outputs; Figure S2. Verification; Table S3. Errors per check — 6
4. Text S3. The example models; Figure S3. Particle share — 2
5. Text S4. Accounting at a small well; Figure S4 — 1.5
6. Text S5. Transient tracking over 30 years; Figure S5 — 2
7. Text S6. Ensemble and history matching; Figure S6 — 2
8. Text S7. Where each source's water goes; Figure S7 — 1.3
9. Text S8. The same trace on different grids; Figure S8 — 2
10. Text S9. The contributing area through the seasons; Figure S9 — 1.3
11. Text S10. Mean travel time; Figure S10 — 1
12. Text S11. Streams, drains, wells and linked models; Figure S11 — 2.2
13. Text S12. A new well's source mix; Figure S12 — 2.3
14. Text S13. Neversink comparison; Table S4. Delineations and ensemble maps; Table S5. Per-well gross and net; Figures S13–S15 — 8
15. Text S14. Numerical dispersion; Figure S16 — 2.5
16. References — 1.5

The builder needs one rule change: number items in order of placement, not "cited items first, then uncited items in file order". Under the current rule, the uncited items are what push the Neversink figures ahead of the example figures.

## 4. Cross-references that change

**Main text**
- Section 3: "Table S3" (run time) → Text S2. Table S2 and Figure S2 are unchanged.
- Section 4: Text S2 → S3. Text S3 → S4. Text S4 → S5. Text S5 → S6. Texts S6–S11 → S7–S12. Figure S4 → S5. Figure S5 → S6. Figure S3 is unchanged.
- Section 5: Figure S6 → Figure S13. Table S3 (twice) → Table S4. Text S12 → Text S13.
- Section 6: "Figure S7; Figure S8" → Text S14, Figure S16. Text S7 → Text S8.
- Section 7: Text S2 → Text S3.

**Within the SI**
- Table S1 caption: drop "Text S13".
- Text S1: drop the references to Figure S1 (b, c). "Table S4" → Table S3. Text S9 → S10. Text S6 → S7. Text S4 → S5.
- Table S2, "Shown in" column: every Text S3–S11 moves up by one.
- Figure S2 caption: Table S4 → Table S3.
- Neversink items: cross-references to Figures S10–S13, Table S5 and Text S14 become Figures S13–S15, Table S5 and Text S13.
- Old Figure S8 caption: "given in Figure S7" → Text S14.
- Example texts: references to "Text S2" become references to their own model paragraph. "Text S4" → S5. Figure S14–S20 references → Figures S4, S7–S12.
- numbering.md: merge the aliases {SI: Neversink …}, {SI: net attribution…}, {SI: numerical dispersion…}, {SI: notes and sources…}, {SI: Monte Carlo offsets…} and {SI: diagnosis…} into the new items. Then rebuild to regenerate the labels.
