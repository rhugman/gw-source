# SI review, round 1: scope (what belongs in the SI at all)

Associate editor's report on `export_reduced/supporting_information.pdf` (69 pages) against the reduced main text (about 6 pages). Page counts are read from the PDF.

## Overall view

The SI does three jobs, and only two of them belong in it. It holds the evidence a reviewer needs to check main-text claims: the derivations, the comparison of methods, the verification and the numbers behind each example. It also holds a lab notebook: literature reading notes, file-offset forensics, the debugging history of the PRT helper, and per-check and per-well tables. Most of the second kind already exists in `docs/neversink_study.md`, `docs/dispersion_study.md` and the ten notebooks. Those 69 pages are about 28 pages of evidence and 41 pages of repository-level detail.

My target is **about 21 pages**, not 15. Two items cannot shrink much: the method (Text S1, about 4 pages) and the comparison table (Table S1, about 2.5 pages). Together they are a third of a 20-page SI. Going below about 19 pages would mean dropping figures that are the only visual evidence for a cited claim.

Material moved to the repository is only citable if it is fixed in time. The Data Availability statement should cite the tagged release and its Zenodo DOI, not the live repository.

One more constraint applies to the repository moves. The house rule keeps the name of the Foley and Black (2013) program out of `docs/` and code. So Text S13, which names it on every page, cannot simply be copied into `docs/`.

## Item by item

"Cited" means cited from the main text. Pages saved are approximate.

| Item | Cited? Claim supported | Recommendation | Repository home | Pages now → saved |
|---|---|---|---|---|
| Text S1 Method | §2 ×2: derivations, mean travel time | **Shorten** to ~3.5–4 pp. Keep Eqs S1–S15 and their derivations. Cut the flow-loop report paragraph, the "time to enter the exit cell" paragraph with its test-model-1 numbers (one sentence stays, because the PRT comparisons need it), the volume-option numbers (they belong in the example text) and the clipping note | the cut detail is already in code docstrings | 6.5 → 3 |
| Text S2 Models | §4, §7: every model described; notebooks | **Shorten** to ~2 pp. Give the shared model in full, then one or two sentences per variant (only what changes), the Bedekar rebuild choices as a short list, the ensemble set-up from S5, and a one-line-per-model test table. Cut the solver criteria, GWT solver settings, Voronoi sizing, XT3D formula and percentile memory | notebooks 04, 05, 07, 08, 09, 10 (exist). The test-model table goes to a new `tests/models/README.md` (does not exist; the docstrings in `tests/models/*.py` are partial). The feet-per-day rerun is not in notebook 10 and must be added | 8.5 → 6.5 |
| Text S3 Small well | §4: Foley–Black example to 10⁻¹⁴ | **Merge** into one "worked examples" text (~0.3 pp) | `02_accounting` (exists) | 1 → 0.7 |
| Text S4 Transient checks | §4: GWT match 9.8 × 10⁻¹⁴ | **Merge** (~0.3 pp). Keep the 30-year split, the GWT match, the forward–backward check and one sub-step sentence | `08_transient_tracking` (exists) | 0.6 → 0.3 |
| Text S5 Ensemble set-up | §4: 40 noisy heads | **Merge** into Text S2 (~0.3 pp). Move the phi table and the prior statistics | `09_ensembles` (phi and NOPTMAX already there) | 1 → 0.7 |
| Text S6 Forward | §4: GWT 4.2 × 10⁻¹³ | **Merge** (~0.3 pp). Move the nitrate and chloride illustration | `03_forward` (exists) | 1 → 0.7 |
| Text S7 Grids | §4, §6: 186 vs 121 m; 45° band 1.8× | **Merge** (~0.35 pp). Keep 186/121 m and 215 m at 45°. Move the west-edge discussion and the XT3D loop details | `04_grids` (exists) | 1 → 0.65 |
| Text S8 Seasons | §4: 0.59 → 1.35 km² | **Merge** (~0.25 pp) | `05_transient_snapshots` | 0.8 → 0.55 |
| Text S9 Travel time | §4: 45.7 vs 45.9 yr; "differ cell by cell" | **Merge** (~0.3 pp). Keep the medians 0.96 and 5.7 | `06_travel_time` | 0.8 → 0.5 |
| Text S10 Networks | §4: 32 % stream leakage | **Merge** (~0.3 pp). Move the MAW numbers | `07_networks_multimodel` | 1 → 0.7 |
| Text S11 Bedekar | §4: 48.2/29.2/22.5 % | **Merge** (~0.35 pp). Keep the read-off error and the step sensitivity | `10_unit_concentration` | 1 → 0.65 |
| Text S12 End states | §5: weak-sink stopping | **Shorten** to ~0.5 pp. Keep the table and one paragraph each on buried stream cells and U\_\_\_7 (F = 0.97) | `neversink_study.md` §2 (exists) | 1 → 0.5 |
| Text S13 Literature notes | not cited | **Cut**. Replace with a ~0.4 pp "Sources" note under Table S1, giving the pages or sections read for each column, and keep the GWT porosity-0 test as footnote 1 | archive with the paper files on Zenodo, or rewrite for `docs/` under the naming rule | 9 → 8.6 |
| Text S14 MC offsets | not cited | **Move** | `neversink_study.md` §6 (exists) | 0.5 → 0.5 |
| Text S15 PRT diagnosis | not cited | **Move** | `neversink_study.md` §3 (exists, with the `diagnose_prt` gate) | 1 → 1 |
| Table S1 Comparison | §1 | **Keep**. Trim footnote 2 | – | 2.5 → 0.2 |
| Table S2 I/O | §3 | **Shorten** to 1 pp (compact layout). Option: move to the README and cut the pointer | README has no such table yet | 3 → 2 |
| Table S3 Neversink | §3, §5 ×2 | **Keep** the table. Cut the note to ~0.3 pp: definitions, run times, and one sentence each for 602/691 and 711/980 | – | 2 → 1 |
| Table S4 Verification | not cited (backs Fig. S2) | **Move**. Figure S2 shows the values, and its caption should name the error measures | new `docs/verification.md`, generated by the tests (does not exist) | 3.5 → 3.5 |
| Table S5 Per-well | not cited | **Move** | `neversink_study.md` §2 (exists) | 1 → 1 |
| Table S6 Ensemble | not cited | **Move**. One timing sentence goes to the Table S3 note (see below) | `neversink_study.md` §6 (exists) | 1 → 1 |
| Fig S1 Schematic | indirectly, via Text S1 | **Cut**. Panel b is main-text Fig. 1, and panel c repeats the 33.7 m³/d of §4. Panel a may go into Text S1 as a small inline figure if wanted | – | 1 → 1 |
| Fig S2 Verification | §3 | **Keep** | – | 0 |
| Fig S3 Area vs PRT | §4: 0.164 | **Keep**. Optionally reduce it to panel b, since a and c are Fig. 2a, b | – | 0 |
| Fig S4 Transient | §4: snapshots 60/15 % | **Keep** | – | 0 |
| Fig S5 Ensembles | §4: narrowing | **Keep** | – | 0 |
| Fig S6 Neversink maps | §5 | **Shorten** to panels a–c. Panel d is the Neversink ensemble, which the main text never discusses | `docs/figures/neversink_probability_maps.png` | 0 |
| Fig S7 Dispersion maps + set-up text | §6 | **Move** the figure. Keep the set-up and numbers as a ~0.7 pp text (problems A and B; band width; 5 %, 0.1 %, 8–90 %). Move the threshold-strictness and sub-step paragraphs | `dispersion_study.md`, `docs/figures/dispersion_*` (exist) | 2 → 1.3 |
| Fig S8 Dispersion vs h | §6 | **Keep** | – | 0 |
| Fig S9 Net/PRT maps | not cited | **Move** | `neversink_study.md` §2 (`net_and_envelope.py`) | 1.5 → 1.5 |
| Fig S10 Location map | not cited | **Cut**. The inset of Fig. S6 already shows it | – | 0.5 → 0.5 |
| Fig S11 Backward fractions | not cited | **Move** | `docs/figures/neversink_capture_maps.png` (exists) | 1 → 1 |
| Fig S12 Overlap maps | not cited | **Move** | `neversink_study.md` §3 (the figure must be added) | 1 → 1 |
| Fig S13 Probability | not cited | **Move** | `neversink_probability_maps.png` (exists) | 1 → 1 |
| Figs S14–S19 Example figures | not cited | **Move**. Each notebook draws its figure, and Fig. 2 shows one panel of each | notebooks 02, 03, 04, 05, 06, 07 | 4.5 → 4.5 |
| Fig S20 Bedekar | indirectly, via S11 | **Keep**. It is the only external check shown as a figure. Cite it from §4 | – | 0 |
| References | – | Shrink. About ten references serve only Text S13 | – | 1.5 → 0.9 |

Total saved: about 47 pages, which leaves **about 21 pages**. Two optional cuts reach about 19 pages: move Table S2 to the README, and reduce Fig. S3 to panel b.

## Slim SI outline

| New item | Contents (from) | Pages |
|---|---|---|
| Text S1. Method in full | old S1, trimmed | 4 |
| Text S2. Example, test and published models | old S2 condensed, S5 set-up, Bedekar choices, one-line test-model table | 2 |
| Text S3. The worked examples in brief | old S3, S4, S6–S11: set-up change, result, check; 0.3 pp each | 2.5 |
| Text S4. End states of the published particles | old S12, shortened | 0.5 |
| Text S5. Numerical dispersion test problems | text of old Fig. S7, trimmed | 0.7 |
| Table S1. Comparison of methods, with sources | old Table S1 plus a short sources note | 2.8 |
| Table S2. Inputs, selections and outputs | old Table S2, compacted | 1 |
| Table S3. Delineations on one flow field | old Table S3, shorter note | 1 |
| Figures S1–S7 | old S2 (verification), S3, S4, S5, S6 a–c, S8, S20 | 6.3 |
| References | – | 0.6 |
| **Total** | | **~21** |

The builder numbers items by first citation, so the labels above follow from the main text order. In `si/numbering.md`, the merged placeholders become alias rows of `{SI: worked examples}` and `{SI: example and test models}`.

## Main-text pointers that change

| § | Current pointer | Under this plan |
|---|---|---|
| 1 | Table S1 | unchanged |
| 2 | Text S1 (×2) | unchanged |
| 3 | Table S2 | unchanged, or a README pointer if moved |
| 3 | Table S3 (44 s) | unchanged |
| 3 | Figure S2 | becomes Figure S1 |
| 4 | Text S2 (models) | unchanged; add "and its notebook" |
| 4 | Figure S3 | becomes Figure S2 |
| 4 | Text S3 (Foley–Black) | becomes Text S3 (merged placeholder) |
| 4 | Figure S4a | becomes Figure S3a |
| 4 | Text S4 (GWT 9.8 × 10⁻¹⁴) | becomes Text S3 |
| 4 | Text S5 (40 heads) | becomes Text S2 |
| 4 | Figure S5 | becomes Figure S4 |
| 4 | Texts S6, S7, S8, S9, S10 | all become Text S3 |
| 4 | Text S11 | becomes "Text S3; Figure S7" |
| 5 | Figure S6 | becomes Figure S5 |
| 5 | Table S3 (×2) | unchanged |
| 5 | Text S12 | becomes Text S4 |
| 6 | "Figure S7; Figure S8" | becomes "Text S5; Figure S6" |
| 6 | Text S7 (45° grid) | becomes Text S3 |
| 7 | Text S2 (notebooks) | better as a direct repository/DOI pointer with the notebook list |

The SI-internal cross-references to S14, S15, S4–S6 tables and S9–S19 must also go. The affected captions and notes are those of Table S3, Table S6, Figs S6 and S13, and Table S2's "Shown in" column, which should point to Text S3 or to the notebooks.

## Claims that would lose support, and how to keep it

1. **§4, travel time: "Cell by cell, the two differ most outside the F > 0.5 area."** This claim now rests on Fig. S18b. Keep the median ratios (0.96 inside, 5.7 outside) in Text S3, with a pointer to notebook 06.
2. **§5: "The F > 0.1 area holds 73 % of them"** (711/980) and **"87 % of the 691 start cells"** (602/691). Main-text Fig. 3 covers one window only (538/688), so the full counts sit only in the captions of Figs S12 and S9. Put both counts in one sentence of the Table S3 note.
3. **§1/abstract: "fast enough to trace every version."** The only regional ensemble timing is in the Table S6 note (358 realisations, about 9 s of tracing each). Keep it as one sentence in the Table S3 note, with a pointer to `neversink_study.md` §6.
4. **§6: band 1.8× wider at 45°; within 5 %, missed ≤ 0.1 %, 8–90 % larger.** These need Text S5 and the grid paragraph of Text S3, not the Fig. S7 maps.
5. **Table S1 entries.** These lose their page-level sources when Text S13 goes. The short sources note keeps them checkable. Footnote 1 (GWT, porosity 0) is our own test and must stay with its numbers.
6. **Figure S2 (verification).** Without Table S4 a reader sees magnitudes only. The caption should state the error measure per check, and the full table should go to `docs/verification.md`.
7. **§4, Bedekar comparison.** The main text cites Text S11 only, yet the evidence is the curve in Fig. S20. Add the figure pointer.

Several §4 numbers are already backed only by the notebooks, not by the SI: the 64 years of recharge, the 1.10 → 0.35 km² narrowing and the 93 % vs 79 %. That is acceptable once the notebooks are archived with a DOI. Even so, one number each in Text S3 would cost little.
