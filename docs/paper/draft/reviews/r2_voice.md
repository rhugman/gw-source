# Round 2 review: voice and style (role `voice`)

Draft at commit 4b750f2. Checked against `r1_voice.md`, `decisions_r1.md`, brief §4 and terms.md. Line numbers are those of the round-2 files.

Overall: the draft has improved a lot.
- All captions are within their limits (Fig. 4 is one word over).
- "Factorisation", "the solve" and "post-processor" are gone from the prose.
- "Therefore" appears once per section at most.
- The "PRT area (P > 0.5)" wording is used consistently.

What remains is mostly at the seams:
- acronyms defined two or three times by different writers;
- SI placeholder names that do not match each other or any SI heading;
- small drifts in number style and "area"/"zone";
- some awkward phrases that came in with the cuts.

---

## 1. Round-1 MUSTs: status

| r1 MUST | Where | Status |
|---|---|---|
| "F = 0.5" threshold | 06:7, 06:11 | Resolved. 06:7 now says "combine full mixing with particle tracking"; 06:11 says "F > 0.5 area". |
| "about a third … by a third" | 06:9 | Resolved: 0.33 and 35 %. |
| "Both modes" | 06:17 (now 06:15) | Resolved: "Gross and net accounting both". |
| "reference" for the Neversink PRT area | 05:33, 06:11 | Resolved. "PRT area (P > 0.5)" at 05:29, 06:11 and 06:31. |
| "weak sink" defined twice | 01:5, 02:13 | Resolved: defined at 01:5 only. |
| Acronyms defined at first use | throughout | **Partly resolved.** MF6, GWT, GWF and SFR are defined in §1, but GWT, GWF and SFR are defined again later. XT3D is used unexpanded in §2 and expanded only in §4. See the MUSTs below. |
| Table S4 clash | 04:5, 05:15 | Resolved by the `{SI: …}` placeholders. The placeholders now have their own naming problem; see below. |

---

## 2. Findings by file

### 00_front.md

- **00:3**, "Open MODFLOW 6 tool: … and how much pumped water was already stored." (SHOULD).
  - Problem: the list mixes kinds of item: a noun phrase, a participle, then a clause. It is 136 characters, within the 140 limit.
  - Fix (136): "Well contributing areas from MODFLOW 6 in seconds, checked against the water budget, including how much pumped water was already stored."
- **00:5**, "Its published form (the reference method), used for source protection zones…" (SHOULD).
  - Problem: "its published form" implies that full mixing has a single published form.
  - Fix: "One full-mixing method, here called the reference method, is used for source protection zones in England but is described only in conference papers and has no open implementation."
- **00:5**, "New here is backward tracking in time (not particle backward tracking):" (SHOULD; one of the top five).
  - Problem: an inverted sentence with a parenthetical denial. The "New here is" was my round-1 suggestion; together with the parenthesis it reads badly.
  - Fix: "We add backward tracking in time, run from the end of the simulation to its start: for the water in each cell at each time, it gives the fractions that leave through the destination or other sinks, or stay stored." §2.9 already carries the contrast with MODPATH.
- **00:5**, "Its agreement with the published particle-tracked contributing areas lies within the spread …" (SHOULD).
  - Problem: "Its" grammatically refers back to "a trace" in the previous sentence.
  - Fix: "Full mixing agrees with the published particle-tracked contributing areas within the spread that particle conventions alone produce on the same flow field."
- **00:5 against 03:17 and 05:11**, "2–3 s" in the abstract, "2 to 3 s" in the text (SHOULD; number style). Pick one style, "2 to 3 s", and use it everywhere.

### 01_introduction.md

- **01:11, 01:19 against 00:5, 02:5, 03:5, 04:11**: acronyms are defined more than once (MUST; decision 14 and hard rule 5, define once). Define each at its first body use and nowhere else:
  - **GWT** is defined at 01:11 ("Groundwater Transport (GWT) Model") and again at 04:11 ("The MODFLOW 6 Groundwater Transport (GWT) model"). The capital "Model" also differs between the two. Fix 04:11: "GWT (§1), run to equilibrium …".
  - **GWF** is defined at 01:19 and again at 03:5 ("groundwater flow (GWF) model"). Fix 03:5: "the GWF budget files".
  - **SFR** is defined three times: "Streamflow Routing (SFR) reaches" (01:19), "streamflow-routing (SFR) leakage" (02:5) and "Stream reaches (SFR)" (03:5). Fix: keep 01:19; write "SFR leakage" at 02:5 and "SFR reaches, lakes (LAK), …" at 03:5.
- **01:17**, "Adjoint methods run backward, but they solve … not water fractions" (SHOULD).
  - Problem: §1 now has four negation constructions: 01:7 "not capture fractions", 01:17 "is not new", 01:17 "not water fractions", and 01:19 "not MODPATH backward tracking".
  - Fix: recast 01:17 as a positive statement: "Adjoint methods run backward in time for concentrations in continuous transport; we track water fractions on the flow model's time steps." Drop "(not MODPATH backward tracking; §2.9)" at 01:19 and keep "(§2.9)".
- **01:19**, "solved exactly also where flows form loops" (SHOULD). Awkward. Fix: "solved exactly, including where flows form loops".
- **01:19**, "reads MF6 … output on every grid type, multi-model simulations, and package networks" (SHOULD).
  - Problem: the list is not parallel; output is not read "on" multi-model simulations.
  - Fix: "The open code reads MF6 Groundwater Flow (GWF) model output for every grid type, for multi-model simulations and for package networks such as Streamflow Routing (SFR) reaches."
- **01:23**, question 3, which runs to about 50 words (SHOULD). Move the benchmark description out of the question: "3. What do the differences from a published particle-tracked benchmark consist of, and what do they mean for how a protection zone is drawn and reported (§5, §6)?" The Neversink details already appear at 05:7.
- **01:11 against 05, 07, 08, 09**: "MF6" is defined at 01:11, but §2–4 spell out "MODFLOW 6" eight times while §5, §7 and §8 use "MF6" (SHOULD; one voice). Use "MF6" after 01:11 everywhere except in headings and the name "MODFLOW 6 particle tracking (PRT)".

### 02_methods.md

- **02:43**, "as with the XT3D option" (MUST, acronym at first use). XT3D is expanded only at 04:5. Fix: move the expansion here: "as with the XT3D (extended three-dimensional) option of the NPF package (Provost et al. 2017)". At 04:5, write "XT3D (§2.4)".
- **02:43**, "the matrix is an M-matrix, so the factorisation needs no pivoting" (SHOULD). The cut removed the one clause a groundwater reader can follow. Restore it: "the matrix is an M-matrix (each cell's outflow shares sum to at most 1), so …".
- **02:13** is a one-sentence paragraph stranded after the figure marker (SHOULD). Move it into the 02:5–9 paragraph, before `[[Figure 1]]`. 02:35, also a single sentence, can join 02:33.
- **02:65**, "This time includes the residence in the cell where the water leaves, for a well its own cell; …" (SHOULD). Dense. Fix: "This time includes the time spent in the well's own cell. Particles that stop on entering the well cell measure the time to reach it, which is $m_i/F_i$ less the mean residence time of that cell."
- **02:65**, "Being means over mixed water, they should not be used alone …" (SHOULD). An awkward participle opening. Fix: "Because they are means over mixed water, they should not be used alone to draw a time-of-travel zone (§6.5)."
- **02:85**, "less the flow-error correction and, with "gwt" volumes, the step-boundary losses" (MUST, misleading).
  - Problem: 02:79 says that tagged water "appears or disappears" at step boundaries, so "losses" is wrong in sign half the time.
  - Fix: "the step-boundary adjustments" (terms.md wording).
- **`{SI: …}` placement at 02:65, 06:11, 06:15 and 07:7** (SHOULD; one voice). These placeholders stand bare after the sentence or inside it. Elsewhere they sit in parentheses, e.g. "({SI: per-well comparison})". Put all of them in parentheses.

### 03_implementation.md

- **03:5**, "which stores cell connections alike for structured (DIS), vertex (DISV) and unstructured (DISU) grids" (SHOULD). "Alike" is awkward here. Fix: "which stores cell connections in the same form for structured (DIS), vertex (DISV) and unstructured (DISU) grids".
- **03:15–17**: the transient timing (03:15) now comes before the steady benchmark (03:17) (SHOULD; a seam). This is a side effect of my round-1 caveat-first request. The section reads backwards: an untimed transient case first, the headline steady cost second. Swap the two paragraphs, and keep the caveat at the start of the transient paragraph.
- **03:17**, "group the wells or trace them in batches" (SHOULD). This is the paper's only bare imperative. Fix: "so wells are grouped or traced in batches".

### 04_verification.md

- **04:5**: the model list no longer maps numbers to models (SHOULD; a seam). The text later cites models 2, 6, 7, 9 and 10, but the reader learns only which ones are 1 and 10. Fix: add the numbers in passing: "a weak-sink well in three layers (model 2), DISV and DISU grids (3, 4), flow loops from XT3D (5), storage (6), SFR with MVR (7), MAW (8), LAK and UZF (9), and model 1's flows held constant over 120 steps (10)". Check this mapping against the SI test-model list.
- **04:13**, "9574 d, against 9590 d … is 9607 d" (SHOULD; number style). Elsewhere four-digit numbers carry a comma (1,600; 3,671; 2,139). Write "9,574 d", "9,590 d" and "9,607 d".
- **04:13**, "; m/F of §2.6, which includes …" (SHOULD). The clause starts with a symbol (decision 15). Fix: "; the mean travel time of §2.6, $m/F$, which includes the time in the well cell, is 9,607 d".
- **04:17**, "Forward tracking and backward tracking in time (§2.9) gave the same tagged volumes" (SHOULD; decision 17). Fix: "Forward transient tracking and backward tracking in time …".
- **04:21**, "where at the other end of the run they differ from G and F by at least 0.40 and 0.52" (SHOULD; carried over from round 1). It is still unclear which end goes with which fraction. Fix: "c at the start differs from G by at least 0.40, and w at the end differs from F by at least 0.52".
- **04:25**, "compared only west of the gaining river, where every method mixes" (MUST, misleading; new in round 2).
  - Problem: "where" can attach to "west of the river", which reverses the meaning.
  - Fix: "compared only west of the river, away from the gaining river, where every method mixes".
- **04:29**, "within 5 % of the reference area … contained the reference zone" (SHOULD; area/zone drift within one paragraph). Write "reference area" both times, and at 06:11 also.
- **04:37**, "Tracked forward, the well's water in the last season was, in year 1, 95 % …" (SHOULD). The commas stack up. Fix: "With transient tracking, the well's water in the last season of year 1 was 95 % initial water, 3 % river leakage and under 2 % recharge; in the last season of year 30 it was 52 % initial water, 33 % recharge and 16 % river leakage (Fig. 4b)."

### 05_neversink.md

- **05:3**, "a benchmark, not a reference: … used to explain differences, not to score methods" (SHOULD). Two negations in the section's first sentence; 05:15 adds a third ("not accuracy"). Fix: "The published Neversink contributing areas are a benchmark, not a reference: they come from one particle convention, and we use them to explain differences between methods."
- **05:27**, a definition of buried stream cells nested in parentheses inside a list (SHOULD). Fix: end the list at "including buried stream cells; and draping …", then add a sentence: "Buried stream cells are SFR reach cells with an active cell above; the stream exchange stays in the cell, so a gaining reach there is a weak sink."
- **05:29**, "to mixing against advective paths plus the published particle conventions" (SHOULD; carried over from round 1; "mixing against advective paths" is still opaque). Fix: "We attribute the gap to the published contributing cells to two things: mixing within cells, where particles follow advective paths, and the published particle conventions. The PRT-area comparison supports the first only for the spreading between sinks."
- **05:29**, "Within these, F > 0.1 covers 87 %" (SHOULD). Fix: "Within these caveats, …".
- **05:33**, "The network's 8 flow loops" (SHOULD; number style). The paper writes "eight priority wells" and "nine destination groups". Fix: "eight flow loops". At 05:7, "4 layers" can stay, because it is a dimension.
- **05:37**, "PRT with the published conventions reproduces those tested" (SHOULD). The cut lost both the count and the result; 05:39 and Fig. 9 still give 60 and 61. Fix: "reproduces each of the 60 realisations tested (median overlap 0.996)".
- **05:37**, "drawn from the PEST++ iES posterior" (SHOULD). Expand iES once: "PEST++ iterative ensemble smoother (iES)".
- **05:39**, "the zones above 0.5 overlap at 0.48" (SHOULD; area/zone). Fix: "the areas above 0.5 overlap at 0.48".
- **05:45**, "With the scenario rule inferred from the published areas, which raises pumping…" (SHOULD).
  - Problem: "which" can attach to "the published areas".
  - Fix: "We inferred the scenario rule, which raises pumping at the priority wells only, from the published areas ({SI: …}). Under it, the median full-mixing area is within 10 % of the published median at every rate."
- **05:51**, "PRT grows 4.76 times"; "weight loss at every sink inside a cell" (SHOULD). PRT does not grow, and the second phrase is unclear. Fix: "the PRT area grows 4.76 times with weight-losing particles and boundary flows on open top faces".

### 06_discussion.md

- **06:9, 06:11**, "the published cells" (SHOULD; term drift). §5 uses "published contributing cells" throughout. Fix: "published contributing cells".
- **06:7**, "For small zones, where the transition band … is a large part of the zone's width" (SHOULD). Fix: "For small protection zones, …".
- **06:27 against 05:37**: "{SI: Monte Carlo bookkeeping offsets}" against "{SI: Monte Carlo offsets and scenario rule}" (MUST, cross-reference). Two names for one SI item, and only the second exists as an SI heading.
  - 06:15 "{SI: per-well gross and net}" and 05:15 "{SI: per-well comparison}" may also be one item; decide.
  - Seven more placeholders have no `## {SI: …}` heading in `si/*.md`: diagnosis of the first PRT runs, end states of the published particles, ensemble statistics, scenario medians, one convention at a time, faster growth of weight-losing particles, and per-well comparison.
  - Fix: one name per item, each matching a heading, so the editor can number them. For items that existed as SI before round 2, add the headings.
- **06:31**, six of seven sentences start with "We would" (SHOULD; a mechanical tic).
  - Problem: the hedge is right, since decision 13 asks for it, but it needs stating only once.
  - Fix: "From these tests we recommend the following, as practice rather than rule. The F > 0.5 area is the single best estimate of the advective zone: … The F ≥ 0.1 area serves as the wider area, although on Neversink it missed 13 to 27 % of the particle-tracked areas (§6.1). Where the area ends at weak sinks, such as gaining streams, a particle check under stated conventions is worthwhile (§5.3; Fig. 7). Gross accounting is the default, because …; net accounting is for reproducing studies made with the reference method. For an area tied to a travel time, backward tracking in time over the stated horizon is the right tool, not the mean travel time (§2.6)."
- **06:31 against 06:11**: the 92 % and 13–27 % figures are given twice, in §6.1 and §6.5 (SHOULD). In §6.5, cite §6.1 for both rather than restating one of them.
- **06:3**: a one-sentence opening paragraph (SHOULD; the brief asks for 3–7 sentences). It is acceptable as a lead-in, but it could open §6.1 instead.

### 07_limitations.md, 08_conclusions.md, 09_availability.md

No new voice findings. §7 remains the best-written section. Its opening, "a model with wrong recharge gives wrong areas that pass every check", is exactly the plain register of the GMDSI tutorials.

---

## 3. Captions (display/)

Word counts, without comments:

| caption | words |
|---|---|
| Fig. 1 | 172 (limit 180) |
| Fig. 2 | 92 |
| Fig. 3 | 134 |
| Fig. 4 | 151 |
| Fig. 5 | 104 |
| Fig. 6 | 94 |
| Fig. 7 | 149 |
| Fig. 8 | 56 |
| Fig. 9 | 121 |
| Table 1 | 144 |

- **C.md:15, Fig. 4 (151 words)** (SHOULD). One word over the limit. Cut "(dashed)" after "river", or "each step traced on its own flows".
- **C.md:9, Fig. 3**, "(b, e) Relative area error of the area F ≥ 0.1" (SHOULD). "Area error of the area" is clumsy. Fix: "(b, e) Relative error in the size of the F ≥ 0.1 area. (c, f) The same for the F ≥ 0.5 area; grey band, ±5 %."
- **D.md:11, Fig. 7** (SHOULD). The caption does not tell the reader how to read the axis. Add: "1 means identical areas, 0 no common cells." This fits within 150 if "the published conventions use the top face and draping" becomes "(published conventions: top face and draping)".
- **D.md:15, Fig. 8**, "the share of the 357 published Monte Carlo contributing areas, moved one row north onto their cells, that contain a cell" (SHOULD). The embedded clause breaks the definition. Fix: "the share of the 357 published Monte Carlo contributing areas that contain a cell (areas moved one row north onto their cells)".
- **A.md:27, Table 1 footnote 5**, "the paper itself was read as abstract only" (SHOULD). Fix: "of Bedekar et al. (2024) we read only the abstract".
- **A.md:14, Table 1 row heading**, "Destinations or sources per solve"; cells "one implicit solve", "all groups in one solve" (SHOULD; "solve" used as a noun is coder register). Fix: "per run" in the heading; "one implicit solution over all cells"; "all groups in one run".

---

## 4. One voice across the five writers

Compared with round 1, the writers are much closer. B (§2) now reads like C and E. The remaining seams:
- the acronym redefinitions (A, B, C each define GWT, GWF or SFR);
- MF6 against MODFLOW 6 (B and C against D and E);
- SI placeholder naming (D against E);
- "published cells" against "published contributing cells" (E against D);
- the order of the cost paragraphs in §3.3.

Each of these is fixable by search and replace at assembly. The best model is still §7, then §4.2. The weakest paragraph is now §6.5, because of the "we would" anaphora.

---

## 5. Top five

1. **Acronyms:**
   - define GWT, GWF and SFR once, in §1, and remove the later definitions at 02:5, 03:5 and 04:11;
   - expand XT3D at its first use (02:43);
   - expand iES;
   - use "MF6" consistently after 01:11.
2. **SI placeholders:** one name per item, each matching an SI heading. Fix the Monte Carlo alias (05:37 against 06:27), settle "per-well comparison" against "per-well gross and net", and add the missing headings.
3. **Awkward phrases from the cuts:**
   - in the abstract, "New here is … (not particle backward tracking)" and the dangling "Its agreement";
   - "compared only west of the gaining river, where every method mixes" (04:25);
   - "step-boundary losses" (02:85);
   - "mixing against advective paths" (05:29);
   - "reproduces those tested" (05:37);
   - "Being means over mixed water" (02:65).
4. **Rewrite §6.5** so that it states the hedge once ("we recommend, as practice rather than rule") and then gives plain statements. At present six sentences open with "We would".
5. **Small consistency drifts:**
   - number style: "2–3 s" against "2 to 3 s", "9574" against "3,671", "8 flow loops";
   - "zone" where "area" is meant (04:29, 05:39, 06:7);
   - "published cells" in §6;
   - bare "Forward tracking" at 04:17;
   - parentheses around every `{SI: …}`.
