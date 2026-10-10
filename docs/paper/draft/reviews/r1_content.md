# Round 1 review: content and accuracy

Reviewer role: `content`. Draft: branch paper-draft, commit b845e71. Findings are grouped by file and give `file:line`, a short quote, the problem, and a fix. Each is marked MUST or SHOULD.

These were checked against their evidence and found correct:
- every number in §4 against `docs/paper/figures/verification_table.md/.csv`;
- every number in §5 against `docs/neversink_study.md` and `studies/neversink/output/`;
- the equations in §2 against `src/gwsource` (`trace.py`, `diagnostics.py`, `tracking.py`) and PLAN §2.

The findings below list only the discrepancies.

---

## 00_front.md

**00_front.md:5 — MUST.** Quote: "this matches dispersion-free unit-concentration transport in MODFLOW 6 to round-off".
- **Problem:** the qualifier is gone. Tracking matches GWT to round-off only with GWT's water volumes ("gwt" option), and the outline keeps that qualifier. With the default "flow" volumes the two differ by up to 1.9 × 10⁻⁴ in c (tutorial 08) and 1.2 × 10⁻⁴ (model 6). As written, the abstract claims round-off agreement for the default.
- **Fix:** "with GWT's water volumes, this matches dispersion-free unit-concentration transport in MODFLOW 6 to round-off."

## 01_introduction.md

**01_introduction.md:5 — SHOULD.** Quote: "At a weak sink, a cell whose well takes only part".
- **Problem:** the term is defined here and again at 02_methods.md:13, with different wording ("well" vs "sink term").
- **Fix:** keep the general definition here ("a cell whose sink takes only part of the cell's outflow"). In §2.1, refer back to it instead of defining it again.

**01_introduction.md:11 — MUST.** Quote: "McLane and Cecan (2009) discuss its spreading on coarse grids".
- **Problem:** the source was not read (references/SUMMARY.md). It is known only through secondary accounts as a grid-dependence critique of MODALL, so the citation needs the marker the draft uses elsewhere.
- **Fix:** "McLane and Cecan (2009) [check: not read] discuss …". Otherwise drop the sentence, since §7 makes the grid-dependence point from our own results.

**01_introduction.md:15 — MUST.** Quote: "Forward tracking through storage is not new … described as an Eulerian transport tool (Black et al. 2021)".
- **Problem:** placed after "forward tracking through storage is not new", the BFW21 citation implies that the reference method carries water through storage. Table 1 says it does not ("No: snapshots"). BFW21 describes the steady forward fraction read as C/C0, not a storage-carrying transient forward mode.
- **Fix:** Keep the hydraulic-mixing-cell and GWT examples for "through storage". Move BFW21 to its own clause: "the reference method's steady forward fraction has been read as a relative concentration (Black et al. 2021)".

**01_introduction.md:15 — MUST.** Quote: "None of the methods we read tracks water backward in time".
- **Problem:** line 13 has just cited adjoint and backward-in-time methods for transport (the adjoint literature). The unqualified sentence contradicts it and over-claims novelty (hard rule 4).
- **Fix:** "None of the mixing-cell or flux-based methods in Table 1 tracks water backward in time; adjoint transport (…) does, but for concentrations, not for water fractions on the flow model's steps."

**01_introduction.md:15 — MUST.** Quote: "Nor has a flux-based delineation been compared with particle-tracked contributing areas".
- **Problem:** the hedge is gone. Our evidence is a literature search, not proof of absence. Elsewhere the draft says "we found no".
- **Fix:** "Nor did we find a published comparison of a flux-based delineation with …".

**01_introduction.md:19 — SHOULD.** Quote: "add backward tracking in time, run from the end of".
- **Problem:** at this first use, the reader with MODPATH in mind will read "backward tracking" as particles run in reverse from the well. The clarification comes only at 02_methods.md:83.
- **Fix:** add once here: "(not MODPATH's backward tracking; §2.9)".

## 02_methods.md

**02_methods.md:13 — SHOULD.**
- **Problem:** weak sink is defined a second time (see 01_introduction.md:5).
- **Fix:** "A weak sink (§1) is …", or drop the sentence.

**02_methods.md:33 — MUST.** Quote: "$F$ is a share of flow, not a probability (McLane and Cecan 2009)".
- **Problem:** the source is unread. Nothing in references/SUMMARY.md says it makes this point. The statement is our own definition and needs no citation.
- **Fix:** delete "(McLane and Cecan 2009)".

**02_methods.md:37 — SHOULD.** Quote: "a cell or zone selection fixes all its cells".
- **Problem:** this is incomplete for combined selections. `trace.py::net_fixed_cells` (commits 88cc2ac, b1752f0) behaves as follows:
  - a pure cell or zone selection keeps all its cells;
  - a selection with any term criterion, also when combined with cells or a zone, fixes only the cells where a selected term flows in the traced direction.
- **Fix:** "… while a pure cell or zone selection fixes all its cells; any term criterion, also with cells or a zone, restricts the fixed cells to those where the selected terms flow in the traced direction."

**02_methods.md:63 — SHOULD.** Quote: "not a particle's (Lagrangian) first arrival".
- **Problem:** §4.1 compares the full-mixing mean with the particles' mean travel time (9574 vs 9590 d), not with first arrival. "First arrival" sets up the wrong contrast.
- **Fix:** "a mean over mixed water (Eulerian), not the travel time along one particle path (Lagrangian)."

**02_methods.md:63 — SHOULD (supports the 04_verification.md:15 MUST).**
- **Problem:** m/F as defined includes the residence time in the destination cell. The verification quantity (`mean_time_to_exit_cell`) excludes it.
- **Fix:** add after eq. (5): "m/F includes the residence in the destination cell; the time to enter it is m/F minus that residence."

**02_methods.md:77 — SHOULD.** Quotes: "On test model 6 (porosity 0.3" and "the backward fraction in time".
- **Problem:** test models are introduced in §4.1, and "backward fraction in time" is defined in §2.9.
- **Fix:** "On test model 6 (§4.1; …)" and "in the backward fraction in time (§2.9)".

**02_methods.md:79 — SHOULD.** Quote: "first in stream and overland cells (Partington et al. 2011, 2013)".
- **Problem:** Partington et al. 2011 is stream cells only (Table 1 footnote 16). The 2013 paper adds overland cells.
- **Fix:** "first in stream cells (Partington et al. 2011) and then also overland cells (Partington et al. 2013)".

**02_methods.md:87–89 — SHOULD.** Quote: "$V_i^0 c_i^0$ the tagged initial water".
- **Problem:** the code uses the volume at the start of step 1, V^(old,1). This equals porosity × saturated volume only for the initial head. Under "gwt" volumes the initial volume is GWT's, so V⁰ is ambiguous.
- **Fix:** "with $V_i^0$ the water volume of cell $i$ at the start of the first step".

**02_methods.md:37 — SHOULD.** Quote: "for the 5.0 m³/d well of tutorial 02".
- **Problem:** tutorials are not introduced before this point (§3 and §9 mention them later), so "tutorial 02" means nothing to the reader.
- **Fix:** "for the 5.0 m³/d well of the accounting tutorial (tutorial 02; §9)", or give the model in one clause.

**02_methods.md (whole) — SHOULD.**
- **Problem:** 2,146 words against the 1,900 budget (+13 %).
- **Fix:** candidates for cuts or moves to the SI: the turnover-time sentence at line 63 and the sub-step pointer at line 77.

## 03_implementation.md

**03_implementation.md:17 — SHOULD.** Quote: "the solve took 0.42 s (one desktop computer, 16 cores)".
- **Problem:** PLAN's benchmark machine is "macOS, 16 cores, 64 GB". Also, 0.55 s and 0.42 s are the solve only. Components (0.10 s), loop check (0.10 s) and metrics (0.11 s) add about 0.3 s, so a reader may take 0.55 s as the time to trace.
- **Fix:**
  - "(16-core, 64 GB macOS computer)";
  - "the solve alone took 0.55 s, and the full trace including assembly and metrics about 1.1 s".

**03_implementation.md:19 — note.** "[check]" for the missing large transient timing is kept correctly. See the [check] list.

## 04_verification.md

**04_verification.md:5 — MUST.** Quote: "(Table S4: per model)". The Table 2 caption (display/C.md:21) has the same problem.
- **Problem:** 05_neversink.md:15 also cites "per well, Table S4", so two different tables carry the number S4. The brief's Table S plan has S4 as per-well Neversink and has no per-model verification table.
- **Fix:** add a per-model verification table to the brief's plan and renumber the SI by first citation (see "SI numbering" below). It becomes Table S1.

**04_verification.md:5 or display/C.md:21 — MUST (part of SI numbering).**
- **Problem:** Text S1 (error measures) is never cited, although Table 2 and Fig. 2 rely on its error definitions.
- **Fix:** "Table 2 and Fig. 2 give the largest error per check (error measures in Text S1; per model, Table S1)."

**04_verification.md:11 — SHOULD.** Quote: "[check: model splitter reference]".
- **Problem:** the reference is missing from the brief.md citation map.
- **Fix:** add the MF6 model-splitter reference (FloPy `Mf6Splitter`, in Hughes et al. 2024 or the FloPy documentation) to the map, then resolve the [check].

**04_verification.md:15 — MUST.** Quote: "the full-mixing mean travel time to the well cell (§2.6) is 9574 d".
- **Problem:** 9574 d is `mean_time_to_exit_cell`, the time to enter the well cell, which excludes residence in it. §2.6 defines m/F, which includes that residence and gives 9607 d on model 1. The cross-reference therefore points at a different quantity. The comparison with particles (9590 d) is right only because particles stop on entering the cell.
- **Fix:** "the full-mixing mean travel time to the well cell, excluding the residence in it as particles stop on entering it, is 9574 d (9607 d including it; §2.6), against 9590 d for the particles."

**04_verification.md:45 — SHOULD.** Quote: "differed by up to 1.9 × 10⁻⁴ in the forward and 3.7 × 10⁻³".
- **Problem:** these values come from runs with one transport step per flow step (tutorial 08 §7; README_method.md). The same paragraph and the Fig. 4 caption use four sub-steps, so the reader will assume these values belong to the Fig. 4 runs.
- **Fix:** add "(one transport step per flow step)".

**04_verification.md (whole) — SHOULD.**
- **Problem:** 1,405 words against 1,250 (+12 %).
- **Fix:** move the split-model and PRT release-point sentences into Table 2 footnotes.

## 05_neversink.md

**05_neversink.md (§5.1) — SHOULD.**
- **Problem:** the text uses "U wells", "S region" and well names (U___7, SV_487) without introducing the three regions (NE, S, W) or the well clusters (U, SV_W, SV_S).
- **Fix:** one sentence in §5.1 or in the Fig. 5 caption: "The priority wells lie in three regions (NE, S, W) and form three clusters (U, SV_W, SV_S; Fig. 5)."

**05_neversink.md:31 — MUST** (writer flag, confirmed). Quote: "set through IFLOWFACE (the cell face a boundary flow is assigned to)".
- **Problem:** IFLOWFACE is already defined at 03_implementation.md:13, and display/D.md:46 explains it a third time.
- **Fix:** "set through IFLOWFACE (§3.2)". Keep the gloss only in §3.2.

**05_neversink.md:25–33 — SHOULD.**
- **Problem:** Text S2 (PRT diagnosis) is never cited. The PRT paragraphs are where it belongs.
- **Fix:** add to §5.3: "Text S3 diagnoses where PRT and full mixing part (end states, release conventions)", using the renumbered Text S3 (see "SI numbering").

**05_neversink.md:33 — MUST** (writer flag, confirmed). Quote: "the weight-losing PRT zone P > 0.5, the particle reference of §4.3".
- **Problem:** §4.3's particle reference is fine-grid PRT on synthetic problem B, not this zone. What the two share is only the rule that defines the zone (P > 0.5 of particle weight).
- **Fix:** "the weight-losing PRT zone P > 0.5, defined as the particle reference zone of §4.3".

**05_neversink.md:33 — SHOULD.** Quote: "The gap to the published cells is therefore mixing against advective paths".
- **Problem:**
  - "therefore" does not follow from the envelope paragraph, which compares full mixing with PRT, not with the published cells.
  - The sentence states an attribution as fact.
  - Weight-losing PRT shares full mixing at weak sinks, so the PRT reference is not purely advective (06_discussion.md:11 says so).
- **Fix:** move the sentence to the end of the reproduction paragraph (line 31) and hedge it: "We attribute the gap to the published cells to mixing against advective paths, plus the documented particle conventions."

**05_neversink.md:33 / 06_discussion.md:11 — SHOULD** (hand-off to E).
- **Problem:** the 89 missed cells and the 6 % of PRT-delivered water first appear in §6.1, not in §5.3, the results section the outline assigns them to. The Discussion then reports new results.
- **Fix:** add to §5.3: "it misses 89 cells of the PRT zone, carrying 6 % of the water PRT delivers (226.7 of 3,736 m³/d; Fig. S1d)". In §6.1, refer back to it.

**05_neversink.md:43 — MUST.** Quote: "There, the variation comes from the particle conventions."
- **Problem:** this states an interpretation as fact. NS §6 says the variation "shows up through the particle conventions, not in the full-mixing capture". The outline has "can come from". The evidence is a correlation (r = 0.00 for the sum of F), not an attribution.
- **Fix:** "There, the variation shows up through the particle conventions rather than in the full-mixing capture."

**05_neversink.md:49–57 — SHOULD.** The figures 72 %/18 % and 3.62 (growth decomposition).
- **Problem:** these come from the 61-realisation mechanisms subset (`mechanisms60/`), not the full ensemble. Read next to "all 358 realisations", the reader will take them as full-ensemble statistics.
- **Fix:** "(61 realisations; Table S7)", using the renumbered table.

**05_neversink.md:15, 21, 33, 43, 49, 57 — MUST** (SI numbering). See below.

## 06_discussion.md

**06_discussion.md:7 — SHOULD.** Quote: "as the Environment Agency (2019) does (§4.3)".
- **Problem:**
  - EA19 pairs the reference method with MODPATH for small inner zones in general, not with the F = 0.5 area specifically.
  - §4.3 does not discuss small zones or EA practice, so the cross-reference is empty.
- **Fix:** "we would combine full mixing with particle tracking for such zones, as the Environment Agency (2019) does for inner zones", and drop "(§4.3)".

**06_discussion.md:11 — SHOULD.** Quote: "There, the F ≥ 0.1 area contained the reference zone".
- **Problem:** the paragraph uses the non-strict F ≥ 0.1 for the synthetic tests (correct, DS) and the strict F > 0.1 for Neversink (correct, NS), but never says why the sign changes. A reader will think it is a typo.
- **Fix:** add one clause at first use: "(thresholds non-strict in the synthetic tests, strict on Neversink, as in each study)". Otherwise state it once in the Table 3 and Fig. 7 notes, and keep both signs.

**06_discussion.md:17 — MUST.** Quote: "At the five weak-sink wells net accounting exceeds it (U___7 214".
- **Problem 1:**
  - "Exceeds" holds only in sum, 690 against 466 cells. Per well it fails at SV_487 (94 vs 97) and U__55 (97 vs 116).
- **Problem 2:**
  - The outline's caveat is missing. Single-well traces of U___7 and U___8 both count the 608 m³/d that passes from U___7's cell into U___8's, so the two per-well counts overlap.
- **Fix:** "At the five weak-sink wells net accounting exceeds it in sum (690 against 466 cells; U___7 214 against 58, U___8 249 against 163, both counting the 608 m³/d passing from U___7's cell into U___8's), while gross accounting is closer (502 against 466)."

**06_discussion.md:21 — MUST.** Quote: "(tutorial 08: 2 × 10⁻⁴ forward, 4 × 10⁻³ backward; §2.8)".
- **Problem:** the cross-reference is wrong. §2.8 gives the model-6 values (1.2 × 10⁻⁴ and 6 × 10⁻³). The tutorial-08 values are in §4.4.
- **Fix:** replace "§2.8" with "§4.4".

## 07_limitations.md

**07_limitations.md:3 — SHOULD.** Quote: "so a finer grid spreads the edge of a zone over more cells".
- **Problem:** this is true, but it reads as a cost of refining, when the point is the slow return. With band ∝ h^0.5, halving the band needs a grid four times finer.
- **Fix:** "so halving the width of a zone's edge needs a grid four times finer".

**07_limitations.md:7 — SHOULD.** Quote: "and that the published probability follows narrow paths".
- **Problem:** the list is of inferences, but this item is an observation from the maps. The inference is the reading behind it: that the narrow paths are single-particle paths along stream-leakage flow lines.
- **Fix:** "and that the narrow paths the published probability follows are single particle paths (Text S5)".

## 08_conclusions.md

**08_conclusions.md:3 — MUST.** Quote: "it matches the dispersion-free unit-concentration transport of MF6 GWT".
- **Problem:** the same missing qualifier as in the abstract. The match holds with GWT's water volumes. The default "flow" volumes differ by about 10⁻⁴.
- **Fix:** "forward, with GWT's water volumes, it matches …".

## 09_availability.md

No content findings. All [check] markers are kept and listed below.

## display/

**display/A.md:23 — SHOULD** (writer flag "package node").
- **Problem:** "package node" does not occur in §2 or anywhere else. The only "node" in the draft is Table 1 footnote 3, "stream and overland nodes", which terms.md bans.
- **Fix:** "stream and overland cells".

**display/C.md:21 — MUST.** The Table 2 caption says "Errors per model are in Table S4". This is the same clash as 04_verification.md:5.
- **Fix:** "Table S1", after renumbering.

**display/D.md:46 — SHOULD.**
- **Problem:** the IFLOWFACE gloss is repeated (third definition).
- **Fix:** "through IFLOWFACE (§3.2)".

**display/E.md:3 (Fig. S1 caption) — SHOULD** (writer flag, strip distance settled).
- **Problem:** the caption does not describe the location of the missed cells. The README and the outline seemed to disagree ("1 to 2.4 km west" vs "about 1.5 km long"), but they describe different dimensions.
- **Data:** P > 0.5 and F ≤ 0.1 at start cells, NE region:
  - 86 of the 89 missed cells form a strip one to five cells wide (columns 487–514, rows 234–248);
  - its greatest extent is 1.48 km;
  - it lies 1.1 to 2.5 km west of the U wells (columns 536–538).
- **Fix:**
  - caption: "86 of the 89 cells form a narrow strip about 1.5 km long, 1 to 2.5 km west of the U wells";
  - add the 1.1–2.5 km distance and the 1.48 km extent to `studies/paper/si_figures.py` QUOTED, so the figure tests assert them.

---

## SI numbering (cross-cutting) — MUST

**Current order of first citation, tables:**
1. Table S4 per model (§4.1)
2. Table S4 per well (§5.2)
3. Table S5 (§5.2)
4. Table S6 (§5.3)
5. Table S1 (§5.5)
6. Table S2 (§5.5)
7. Table S3 (§5.6)

There are two different Table S4s, and the order runs 4, 4, 5, 6, 1, 2, 3.

**Renumber tables by first citation:**

| New | Content | Old |
|---|---|---|
| S1 | verification errors per model | new; old "S4" in §4.1 |
| S2 | Neversink per-well comparison | NS 2; old S4 in §5.2 |
| S3 | gross vs net per well | NS 2a–b; old S5 |
| S4 | PRT envelope | NS 3a; old S6 |
| S5 | ensemble statistics | NS 4; old S1 |
| S6 | scenario medians | NS 5; old S2 |
| S7 | one convention at a time | NS 6; old S3 |

**Current state of the texts:**
- Text S1 (error measures) is not cited.
- Text S2 (PRT diagnosis) is not cited.
- S3, S4 and S5 are cited in order.

**Fix for the texts:**
- cite error measures at §4.1 or in the Table 2 caption;
- cite the PRT diagnosis in §5.3;
- renumber by first citation:

| New | Content | Cited at |
|---|---|---|
| Text S1 | error measures | §4.1 |
| Text S2 | end states | §5.2 |
| Text S3 | PRT diagnosis | §5.3 |
| Text S4 | MC offsets and scenario rule | §5.5 |
| Text S5 | faster growth | §5.6 |

**SI figures:**
- Only Fig. S1 is cited.
- The dispersion-study SI figures planned in the brief (DS Figs 1, 3, 5) are never cited.
- Fix: cite them in §4.3 and renumber so they come before the net/envelope figure (which then becomes Fig. S4), or drop them from the SI plan.

Main-text figures and tables are first cited in order.

---

## Writer-flagged items: status

| Flag | Status |
|---|---|
| "package node" in §2 | Not found in §2. The only instance is display/A.md:23 ("nodes"); fix above. |
| §5.3 "particle reference of §4.3" | Confirmed; fix at 05_neversink.md:33. |
| IFLOWFACE redefined in §5 | Confirmed, also in display/D.md:46; fixes above. |
| Fig. S1 strip distance | Settled from the data; caption fix above. |
| McLane and Cecan not read | Confirmed. Mark [check: not read] at §1:11; remove at §2:33. |
| SI order | Confirmed, and worse than flagged (double Table S4). |
| Text S2 not cited | Confirmed. Text S1 is not cited either. |
| Hand-offs D→C | Met (PRT, flow-weighted release, weight loss defined in §3.2/§4.1), except the IFLOWFACE redefinition and the wrong §4.3 reference. |
| Hand-offs E | Met, except the 89 cells / 6 % first appearing in §6.1 and the §6.3 "§2.8" cross-reference. |

Also checked:
- The product name does not appear.
- "adjoint", "duality", "Jaccard" and "pivoting" stay within the terms.md limits.
- Novelty sentences comply with hard rule 4, except the two §1:15 items above.

## Citations in the text but missing from the brief.md map

- The MF6 model-splitter reference (04_verification.md:11, "[check: model splitter reference]").
- MODFLOW 6 input/output guide (display/A.md:43, "[check: author, year]").
- McLane and Cecan (2009) is in the map, but marked not read. Its use at 02_methods.md:33 is not supported by the map's note.
- Map entries that are not cited:
  - White et al. 2020 (PEST++ iES) is in the map but never cited. §5.5 ("rebuilt the published PEST interface … 358 realisations") should cite it.
  - The FB13/BF13 page ranges still carry [check] in the map. This is for reference assembly, not for the text.

## [check] markers in the draft

1. 01_introduction.md:11 — Schilling et al. 2017 [check: not read]
2. 02_methods.md:79 — Schilling et al. 2017 [check: not read]
3. 03_implementation.md:13 — [check: PRT documentation]
4. 03_implementation.md:19 — no timing on a large transient model [check]
5. 04_verification.md:11 — [check: model splitter reference]
6. 05_neversink.md:25 — [check: the five-layout scripts are not in the repository]
7. 07_limitations.md:9 — [check: cite the issue once reported]
8. 09_availability.md:3 — [check: public URL]
9. 09_availability.md:3 — Zenodo DOI [check]
10. 09_availability.md:3 — USGS data release ([check: authors] 2021)
11. 09_availability.md:3 — [check: pin to released versions before submission, PLAN D3]
12. display/A.md:3 — the caption's explanation of the [check] convention (not an open item)
13. display/A.md:13 — GWT "Backward in time? No¹¹ [check]"
14. display/A.md:23 — footnote 3, Schilling et al. (2017) [check: not read]
15. display/A.md:43 — footnote 13, MODFLOW 6 input/output guide [check: author, year]

To add: 01_introduction.md:11 McLane and Cecan (2009) [check: not read].

---

## Five most important changes

1. **Restore "with GWT's water volumes"** wherever the match to GWT is claimed (00_front.md:5, 08_conclusions.md:3). The default volumes do not match to round-off.
2. **Fix the SI numbering.**
   - Remove the double Table S4.
   - Renumber Tables S1–S7 and Texts S1–S5 by first citation.
   - Cite Text S1 (error measures) and the PRT diagnosis text.
   - Cite or drop the DS SI figures.
3. **Correct the novelty sentences in 01_introduction.md:15.**
   - BFW21 does not show forward tracking through storage.
   - "None … tracks backward in time" contradicts the adjoint methods just cited; restrict it to the Table 1 methods.
   - Restore "we found no" for the particle comparison.
4. **Fix the McLane and Cecan citations.** Delete the citation at 02_methods.md:33 (unsupported and unread). Mark 01_introduction.md:11 [check: not read].
5. **Correct the mismatched quantities and cross-references:**
   - 04_verification.md:15: 9574 d excludes the well-cell residence, while §2.6's m/F gives 9607 d.
   - 06_discussion.md:21: "§2.8" should be "§4.4".
   - 05_neversink.md:33: "particle reference of §4.3".
   - 06_discussion.md:17: "exceeds" holds only in sum, and the 608 m³/d overlap is missing.
   - 05_neversink.md:43: interpretation stated as fact ("comes from the particle conventions").
