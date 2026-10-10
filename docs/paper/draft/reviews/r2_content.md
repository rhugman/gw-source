# Round 2 review: content and accuracy

Reviewer role: `content`. Draft: branch paper-draft, commit 4b750f2, revised against `reviews/r1_content.md` and `decisions_r1.md`. SI material is in `si/A–E.md`.

The format follows `review_common.md`: findings grouped by file, each with `file:line`, a quote of at most 15 words, the problem and a fix, marked MUST or SHOULD.

**Evidence used:**
- `docs/neversink_study.md` (paperdraft copy) and `studies/neversink/output/*.csv`;
- `docs/dispersion_study.md`;
- `docs/paper/figures/verification_table.*`;
- `src/gwsource`.

**New or changed numbers checked:** the 691-cell PRT area, the 2,413 m³/d water-table release, the 4.76, 3.83 and 4.53 growth figures, the per-well net counts, and the 9574 / 9607 d travel times. They match their sources unless a finding says otherwise.

---

## 1. Round 1 MUST items: status

| # | r1 item | Resolved | Where now |
|---|---|---|---|
| 1 | 00_front: "with GWT's water volumes" qualifier | yes | 00_front.md:5 |
| 2 | 01: McLane and Cecan [check: not read] | yes | 01_introduction.md:9 |
| 3 | 01: BFW21 implied the reference method carries water through storage | yes | 01_introduction.md:17 |
| 4 | 01: "None of the methods we read tracks water backward" | yes | 01_introduction.md:17 |
| 5 | 01: "Nor has … been compared": hedge restored | yes | 01_introduction.md:17 |
| 6 | 02: McLane and Cecan removed from "not a probability" | yes | 02_methods.md:21 |
| 7 | 04: double Table S4 | yes (SI placeholders) | 04_verification.md:5 |
| 8 | 04: error measures (Text S1) not cited | yes | 04_verification.md:5 |
| 9 | 04: 9574 d vs §2.6 m/F (9607 d) | yes | 02_methods.md:65; 04_verification.md:13; si/B.md:15 |
| 10 | 05: IFLOWFACE redefined | yes | 05_neversink.md:27; si/D.md:22 |
| 11 | 05: "particle reference of §4.3" | yes | 05_neversink.md:29 |
| 12 | 05: "variation comes from the particle conventions" | yes | 05_neversink.md:39 |
| 13 | 05: SI numbering in §5 | partly: 7 of the 9 placeholders cited in §5 have no SI section (S-1) | 05_neversink.md:15–51 |
| 14 | 06: "net exceeds" only in sum; 608 m³/d caveat | yes, but the new wording creates a new error (06-1) | 06_discussion.md:15 |
| 15 | 06: "§2.8" should be "§4.4" | yes | 06_discussion.md:21 |
| 16 | 08: "with GWT's water volumes" | yes | 08_conclusions.md:3 |
| 17 | display/C: Table 2 caption "Table S4" | yes (Table 2 moved to SI) | si/C.md:1 |
| 18 | SI numbering (cross-cutting) | partly: 9 placeholders have no SI section, and one name does not match (S-1) | — |

---

## 2. New findings by file

### 01_introduction.md

**01_introduction.md:7 — SHOULD.** Quote: "or the expected area, the sum of the fractions, in cells".
- **Problem:** the sentence makes a contributing area either a set of cells or a number.
- **Fix:** "A contributing area is the set of cells whose backward fraction exceeds a threshold; the expected area is the sum of the fractions, in cells."

**01_introduction.md:13 — SHOULD.** Quote: "its 2020 changes are not documented".
- **Problem:** Daley et al. (2022) does list the changes (si/A.md:41, 46), though without detail. "Not documented" overstates.
- **Fix:** "its 2020 changes are listed but not described (Daley et al. 2022)".

**01_introduction.md:17 — SHOULD.** Quote: "Nor does any of them check that the volume".
- **Problem:** the nearest antecedent is the adjoint methods, but the claim is about the Table 1 methods.
- **Fix:** "Nor does any method in Table 1 check …".

### 02_methods.md

**02_methods.md:5, 43 — SHOULD.**
- **Problem:** acronyms are defined more than once or used before they are defined (decisions item 14):
  - SFR is defined at 01:19, 02:5 and 03:5;
  - GWF at 01:19 and 03:5;
  - GWT at 01:11 and 04:11;
  - XT3D is used at 02:43 but defined only at 04:5.
- **Fix:** define each once, at first use in §1 (XT3D at 02:43), and drop the later glosses.

**02_methods.md:65 — SHOULD.** Quote: "should not be used alone to draw a time-of-travel zone (§6)".
- **Problem:** the guidance is in §6.5.
- **Fix:** "(§6.5)".

### 03_implementation.md

**03_implementation.md:11 — SHOULD.** Quote: "For MODFLOW 6 particle tracking (PRT), the code writes".
- **Problem:** the round 1 marker "[check: PRT documentation]" was deleted, but no citation replaced it. PRT is now uncited, although the brief.md map still has "MODFLOW 6 PRT documentation (add)".
- **Fix:** restore "[check: PRT documentation]" until the reference is added.

### 04_verification.md

**04_verification.md:25 — MUST.** Quote: "compared only west of the gaining river, where every method mixes".
- **Problem:** the meaning is now reversed. DS §1 says the zone metrics are taken west of the river "where no method mixes at weak sinks". East of the river, the PRT helper also thins by full mixing at the gaining river. As written, the sentence says PRT mixes everywhere, which contradicts its use as a reference.
- **Fix:** "compared only west of the gaining river, where no method meets a weak sink (east of it, all water passes the river, which PRT also treats by full mixing)".

**04_verification.md:13 — SHOULD.** Quote: "the full-mixing mean time to enter the well cell is 9574 d".
- **Problem:** the text does not say over which water the mean is taken. Both 9574 and 9590 d are flow-weighted over all the water reaching the well.
- **Fix:** "the flow-weighted mean time for the water reaching the well to enter its cell is 9574 d …".

The 9574 / 9607 d definitions are now consistent across 02:65, 04:13 and si/B.md:15. Two points were checked:
- (m − x)/F in si/B equals "m/F less the mean residence there" for a single-cell destination.
- The identity Σ Src m − Σ r m = Σ V F follows from eq. (5).

### 05_neversink.md

**05_neversink.md:37 — SHOULD.** Quote: "PRT with the published conventions reproduces those tested".
- **Problem:** "those tested" is vague, and the evidence was moved out (si/D.md:31).
- **Fix:** "reproduces each of the 60 realisations tested (median overlap 0.996)".

The missing SI sections for §5 citations are covered under S-1.

### 06_discussion.md

**06_discussion.md:15 — MUST (06-1).** Quotes: "The sum of F rises from 910 to 978" and "net accounting exceeds the published count only in sum".
- **Problem 1:** the 978 is the group trace. The per-well counts that follow come from single-well traces, and they add up to 1,104 (414 + 690). The text gives no reason for the gap, so the numbers look inconsistent. NS §2 says "690 as a sum of single-well traces".
- **Problem 2:** "only in sum" is wrong. Net accounting also exceeds the published count at U___7 and U___8 individually, as the next sentence says.
- **Fix:** "At the five weak-sink wells net accounting exceeds the published count in sum but not at every well: 690 against 466 cells as a sum of single-well traces, which count the 608 m³/d passing from U___7's cell into U___8's for both wells (the group trace counts it once, hence 978 rather than 1,104 in all)."

**06_discussion.md:19 — MUST.** Quote: "only transient tracking answers the question".
- **Problem:** this over-claims. A GWT unit-concentration run with the initial water tagged gives the same forward answer, and 06:21 says forward transient tracking *is* a GWT run.
- **Fix:** "… only transient tracking, or a GWT run with the initial water tagged, answers the question; snapshots cannot."

**06_discussion.md:31 — MUST.** Quote: "and covers every well in one trace (§2.3)".
- **Problem:** the cross-reference no longer works. The round 2 cut removed from §2.3 the statement that net accounting solves one group at a time. "One factorisation serves every destination group" is in §2.4, and the per-solve contrast is in Table 1 ("Gross: all groups in one solve; net: one group per solve").
- **Fix:** "(§2.4; Table 1)".

**06_discussion.md:9 — SHOULD.** Quote: "Release depth changes the water that particles deliver by 35 %".
- **Problem:** only release at the water table changes it (2,413 m³/d). Mid-cell release gives 3,722 m³/d against 3,736 m³/d over the cell volume (prt_comparison.csv; NS §3: "Release depth matters at the water table only").
- **Fix:** "Release at the water table cuts the water particles deliver by 35 % (2,413 against 3,736 m³/d) …".

**06_discussion.md:31 — SHOULD.** Quote: "the F > 0.5 area as the single best estimate".
- **Problem:** decisions item 13 says "a single estimate", and DS calls the F = 0.5 contour unbiased, not best. Also, the synthetic evidence cited (§4.3) is for F ≥ 0.5, not F > 0.5.
- **Fix:** "We would take the F = 0.5 area (F ≥ 0.5 in §4.3, F > 0.5 on Neversink) as the single estimate of the advective zone".

### 07_limitations.md

**07_limitations.md:7 — MUST.** Quote: "the narrow paths the published probability follows are single particle paths (§5.5; Fig. 8)".
- **Problem:** the round 2 cut removed this observation and its "untested" hedge from §5.5. It is not in any SI section either (there is no {SI: ensemble statistics} section), so the limitation now refers to a statement that appears nowhere. The evidence is NS §6, "These look like single-particle paths … That reading has not been tested."
- **Fix:** restore one sentence to §5.5 ("Where the zones differ, the published probability follows narrow paths, which we read, untested, as single-particle paths"), or place it in {SI: ensemble statistics} and cite that.

### 08_conclusions.md, 09_availability.md, display/

No new content errors.

The display items were checked and match the sections:
- Fig. 4 panels (c) and (d–f);
- Fig. 5 clusters (U 4, SV_W 3, SV_S 1);
- the Table 1 footnotes.

display/E.md is now only a comment.

---

## 3. Supporting Information

**S-1 — MUST.** Nine `{SI: …}` placeholders cited in the text have no SI section. Decisions item 6 says "nothing is lost", but some cut material now has no home.

| Placeholder | Cited at | Status |
|---|---|---|
| per-well comparison | 05:15 | no section (NS Table 2) |
| end states of the published particles | 05:19 | no section. The old 05:21 sentence on open-top stream cells, where particles leave through the top face (NS status 2), was cut and is not in any SI file. |
| diagnosis of the first PRT runs | 05:23 | no section |
| ensemble statistics | 05:39 | no section (NS Table 4). The narrow-paths reading should go here (see 07:7). |
| scenario medians | 05:45 | no section (NS Table 5). The stream-network medians sit in {SI: growth mechanism} (si/D.md:43) instead. |
| one convention at a time | 05:51 | no section (NS Table 6) |
| faster growth of weight-losing particles | 05:51; 07:7 | no section (NS Table 7) |
| per-well gross and net | 06:15 | no section (NS Tables 2a–2b). It may be the same table as "per-well comparison"; settle on one name. |
| Monte Carlo bookkeeping offsets | 06:27 | name mismatch. The section is "Monte Carlo offsets and scenario rule" (si/D.md:24). |

**Fix:**
- write the missing sections from the NS tables and texts, keeping their evidence comments;
- unify the two per-well names;
- rename 06:27 to "{SI: Monte Carlo offsets and scenario rule}".

**si/D.md:22 — MUST.** Quote: "Net accounting credits each well with all the water passing through its cell, so its 3,944 m³/d".
- **Problem:** 3,944 m³/d is the group attribution, which counts each passage once. The per-well throughflows add up to 4,621 m³/d (si/E.md:6; net_vs_gross_wells.csv). As written, the note contradicts si/E and si/B.md:5.
- **Fix:** "Net accounting credits the wells with all the water passing through their cells, each passage counted once (3,944 m³/d; the single-well values add up to 4,621 m³/d, {SI: net attribution and PRT-area maps}), so it is more than the inflow."

**si/E.md:6 — SHOULD.** Quote: "because water passing from one well cell to another counts for both wells".
- **Problem:** the difference of 678 m³/d has two parts:
  - 608 m³/d passes directly from U___7's cell into U___8's;
  - 70 m³/d leaves a well cell and reaches the group again (NS §2; `dest_to_dest_flow` 607.7 and `dest_onward_to_dest` 70.1).

  si/B.md:5 names both mechanisms.
- **Fix:** give the split: "608 m³/d passes directly from U___7's cell into U___8's and 70 m³/d leaves a well cell and reaches the group again".

**si/E.md:4 — SHOULD.**
- **Problem:** the strip extent (1.48 km) and distance (1.1–2.5 km) are, by the comment's own note, "not yet asserted in si_figures.py".
- **Fix:** add both to the QUOTED values in `studies/paper/si_figures.py`.

**si/C.md:80 — SHOULD.**
- **Problem:** the dispersion maps and time-step figure are given as repository paths (`docs/figures/…png`). They are not SI figures with captions.
- **Fix:** include them as SI figures with short captions, or cite the archived release.

**Evidence present and correct for:**
- {SI: verification errors per check and model}: every value matches verification_table.*; the per-model values support 04:9–21;
- {SI: transient checks on tutorial 08};
- {SI: numerical dispersion maps and time steps}: 1.2–12 cells and 0.18/0.09 match DS;
- {SI: travel-time identity};
- {SI: net accounting, fixed cells}: matches `trace.py::net_fixed_cells`, including the "any term criterion, also with cells or a zone" rule;
- {SI: delineations on one flow field}: all values match prt_comparison.csv and net_vs_gross_mp7.csv;
- {SI: Monte Carlo offsets and scenario rule};
- {SI: growth mechanism}: 72 % = 1,643.7 / 2,291.3 and 18 % = 413.7 / 2,291.3;
- {SI: net attribution and PRT-area maps}: 691, 89, 226.7 m³/d, 0.917;
- {SI: PRT abort in thin-film cells}.

---

## 4. Length (SHOULD)

**Global — SHOULD.** The main text (§1–8, headings and equations included, comments excluded) is 7,585 words, against the 7,500 limit (decisions item 1).

Sections over budget:

| Section | Words | Budget |
|---|---|---|
| §1 | 897 | 850 |
| §2 | 1,996 | 1,750 |
| §3 | 471 | 400 |
| §4 | 1,138 | 1,050 |
| §5 | 1,445 | 1,350 |
| §6 | 1,156 | 1,100 |
| §7 | 302 | 300 |
| §9 | 121 | 100 |

---

## 5. Citations missing from the brief.md map

- **Provost et al. 2017 (XT3D):** cited at 04_verification.md:5, not in the map.
- **Model splitter reference:** still [check] at 04:9 and 09:3.
- **MODFLOW 6 PRT documentation:** listed in the map as "(add)". Now uncited (see 03:11).

## 6. Open [check] markers

**Main text and display:**
1. 01_introduction.md:9 — McLane and Cecan (2009) [check: not read]
2. 01_introduction.md:9 — Schilling et al. 2017 [check: not read]
3. 03_implementation.md:15 — no large transient timing [check]
4. 04_verification.md:9 — [check: Mf6Splitter citation]
5. 05_neversink.md:23 — [check: the five-layout scripts are not in the repository]
6. 09_availability.md:3 — [check: public URL]
7. 09_availability.md:3 — [check: DOI]
8. 09_availability.md:3 — [check: authors] 2021 (USGS data release)
9. 09_availability.md:3 — [check: MF6 input/output guide, author, year]
10. 09_availability.md:3 — [check: model splitter reference]
11. 09_availability.md:3 — [check: pin to released versions, PLAN D3]
12. display/A.md:13 — GWT backward in time "No⁵ [check]" (keep, hard rule 4)

**SI:**
13. si/A.md:9 — Schilling et al. (2017) [check: not read]
14. si/A.md:19, 31, 64 (×2) — MODFLOW 6 input/output guide [check: author, year]
15. si/A.md:33, 86 — McLane and Cecan (2009) [check: not read]
16. si/A.md:62 — [check: the paper of Bedekar et al. (2024) itself not read]
17. si/E.md:10 — [check: cite the issue once reported]

**To restore:** 03_implementation.md:11 [check: PRT documentation].

---

## 7. Counts

New findings in round 2:

| File | MUST | SHOULD |
|---|---|---|
| 01_introduction | 0 | 3 |
| 02_methods | 0 | 2 |
| 03_implementation | 0 | 1 |
| 04_verification | 1 | 1 |
| 05_neversink | 0 | 1 |
| 06_discussion | 3 | 2 |
| 07_limitations | 1 | 0 |
| 08, 09, display | 0 | 0 |
| SI | 2 | 3 |
| length | 0 | 1 |
| **Total** | **7** | **14** |

Of the 18 round 1 MUSTs, 16 are resolved and 2 are partly resolved (the SI placeholders).

## 8. Five most important changes

1. **Give every `{SI: …}` placeholder an SI section** (S-1). Nine have none, and the cut material on open-top stream cells and narrow paths now exists nowhere. Rename "Monte Carlo bookkeeping offsets" to match its section.
2. **Restore the meaning at 04_verification.md:25:** compare west of the river "where no method meets a weak sink", not "where every method mixes".
3. **Reconcile the net numbers.**
   - 06_discussion.md:15: the group trace gives 978, while the single-well counts add up to 1,104; and "only in sum" is wrong.
   - si/D.md:22: it describes the group's 3,944 m³/d as per-well throughflow, which actually adds up to 4,621 m³/d.
4. **Fix 07_limitations.md:7.** It cites §5.5 for the narrow-paths reading, which §5.5 no longer contains. Restore the hedged sentence, or move it to {SI: ensemble statistics}.
5. **Fix the 06_discussion over-claim and cross-reference.**
   - 06:19 "only transient tracking answers the question" ignores a GWT run with tagged initial water.
   - 06:31 "(§2.3)" should be "(§2.4; Table 1)".
