# Round 1 review: reader and editor (`reader`)

Draft at commit b845e71, `paper-draft`. I read it twice: once as a consulting hydrogeologist who builds MODFLOW models and draws wellhead protection zones with MODPATH, and once as a *Groundwater* associate editor.

**Editor's verdict.** The paper is in scope and its contribution is real: an exact, checked, open formulation of full mixing, plus backward tracking in time. I would send it out for review, but not in this form. It runs to about 19–20 printed pages against the 15–16 in the brief. It repeats its caveats and its gross/net explanation four or five times. Its Discussion describes rather than advises. A practitioner who finishes it knows that conventions matter, but not which zone to draw on Monday.

**The consulting reader.** §1, §2.1–2.2, §4.3 and §6.1 work well. The reader gets lost in §2.3 (selection rules), §2.5 (what to do with a check), §2.8 (volume options) and §2.9 (transpose). They then wade through about 140 numbers in §4 and 110 in §5. They meet "overlap 0.30" before learning that particle runs on the same flow field range from 0.29 to 0.998, so full mixing looks like a failure when it is not.

---

## Length and pages

Word counts are of the main text only. HTML comments, `[[...]]` markers, headings and display equations are left out; inline symbols are counted.

| § | words | budget | over |
|---|---|---|---|
| 1 Introduction | 954 | 900 | +54 |
| 2 Methods | 1,979 | 1,900 | +79 |
| 2.8 (of which) | 405 | 300 | +105 |
| 3 Implementation | 481 | 450 | +31 |
| 4 Verification | 1,378 | 1,250 | +128 |
| 4.4 (of which) | 466 | 400 | +66 |
| 5 Neversink | 1,430 | 1,400 | +30 |
| 6 Discussion | 1,084 | 1,000 | +84 |
| 7 Limitations | 299 | 300 | −1 |
| 8 Conclusions | 211 | 200 | +11 |
| 9 Code and Data | 110 | 100 | +10 |
| **Main text** | **7,926** | **7,500** | **+426 (+5.7 %)** |

Front matter: the title has 96 characters, the Article Impact Statement 127 characters and the abstract 245 words, so all three are within the limits. Captions and tables come to about 5,200 words: Table 1 with its footnotes alone is about 1,850 words, Fig. 2's caption about 370 and Fig. 4's about 420.

**Page estimate.** This is my estimate, assuming about 1,000 words per two-column page of body text and about 1,300 per page of caption or table type:

| part | pages |
|---|---|
| body | 7.9 |
| front matter | 0.5 |
| headings and 9 display equations | 0.6 |
| 10 figures (Figs 3, 4, 6, 8 at ~0.6 page; Figs 1, 2, 5 at ~0.45; Figs 7, 9, 10 at ~0.3) | 4.7 |
| figure captions (~2,200 words) | 1.7 |
| Tables 1–3 (Table 1 ~1.8) | 2.8 |
| references | 1.3 |
| **total** | **~19.5 (range 18–20)** |

At 6 free pages that is 12–14 charged pages, US$3,000–3,500 (US$2,750–3,250 for an NGWA-member corresponding author). The cut list below brings the paper to about 15–16 pages (US$2,250–2,500) and the main text to about 7,250 words, which leaves room for the guidance paragraph I ask for under §6.

**Ranked cut list**, by the space it saves for the least loss of substance:

| # | cut | main-text words saved | pages saved |
|---|---|---|---|
| 1 | Table 1: footnotes to one line each; move the full footnotes to the SI ("Text S0, sources for Table 1"); cut the caption to ≤ 80 words | 0 | ~1.2 |
| 2 | Move Fig. 2 to the SI. It duplicates Table 2, and its 370-word caption repeats Table 2 and §4.1–4.2. | 0 | ~0.8 |
| 3 | §4.1–4.2: replace the number lists with one verdict sentence plus Table 2; move the description of models 1–10 to Table S4 | ~250 | 0.25 |
| 4 | §6: cut repeated caveats and numbers (opening paragraph, the caveat sentence in §6.1, the first sentence and numbers of §6.3, the second and third paragraphs of §6.4) | ~200 | 0.2 |
| 5 | Move Fig. 10 to the SI with the 72 %/18 % reach-state split (§5.6); move the Monte Carlo offsets and the 60-realisation check (§5.5) to Text S4; move the ensemble areas in §5.4 to §5.5 or Table S2. If more pages must go, Fig. 9 follows, as the brief already plans. | ~150 | ~0.6 |
| 6 | §2: cut the third paragraph of §2.8 ("Forward tracking is not new") to one clause; move the selection rule in §2.3 to the code docs; move the statistics list in §2.7 to §3.2 | ~130 | 0.15 |
| 7 | Captions: Fig. 4 from ~420 to ~120 words, Fig. 1 from ~340 to ~180; the numbers stay in the text | 0 | ~0.4 |
| 8 | Fig. 7 and Table 3 show the same overlaps. Keep one in the main text, or redesign Fig. 7 to carry Table 3's flow column. | 0 | ~0.4 |
| 9 | §4.3–4.4: give the sub-step doubling once (keep tutorial 08 and move problem B to the SI); move the per-tag checks in §4.4 to a Table 2 note | ~100 | 0.1 |
| 10 | §1: the capture-fraction paragraph to two sentences; trim the gap paragraph | ~80 | 0.1 |
| 11 | §7: move the PRT thin-film abort to Text S2. It is a bug in another code, not a limitation of the method. | ~40 | — |

---

## Whole paper

- **W1 · SHOULD · No "what do I do on Monday" guidance.** §6 describes trade-offs but rarely recommends anything. The only firm advice is at 06:9 ("should therefore state its release position…"), 06:23 ("Use GWT where…") and 06:27 ("a report should say so"). Fix: end §6 with a ~150-word paragraph, "A workflow for protection zones", using only numbers already in §4–5:
  1. Save the flows (SAVE_FLOWS, BUDGET SAVE).
  2. Trace F with gross accounting for all wells in one solve, and check closure.
  3. Draw F > 0.5 as the best single estimate of the advective zone and F ≥ 0.1 as the wider zone.
  4. Check with particles where the zone ends at weak sinks or is only a few cells wide, and state the particle conventions.
  5. Report the accounting, stream treatment and threshold.
  6. For transient flow, use snapshots for where water enters, tracking for when it arrives and how much was stored, and GWT where dispersion or reactions matter.
- **W2 · SHOULD · Travel-time zones are raised and never answered.** 01:3 opens on zones "set by travel time to the source", but the paper never says how to draw a time-of-travel zone. §2.6 gives an Eulerian mean, which is not first arrival. §4.4 (04:43) shows that backward tracking in time gives a zone for a stated horizon that, unlike steady F, does not reach the west edge. That is the most practical result in the paper, and it is buried. Fix: one paragraph in §6.3 (or §6.1). Say that mean travel time should not be used alone for a 50-day or 400-day zone [check: EA 2019 zone definitions], and that backward tracking in time over a horizon gives a time-limited zone that includes storage.
- **W3 · SHOULD · Overlap 0.30 reads as failure.** A reader meets "0.30 for F > 0.1" (05:15) before learning that PRT on the same flow field ranges from 0.29 to 0.998 depending on conventions (05:27, 05:31). Fix: put caveat first (style rule 6) at the head of §5.2. For example: "Overlap measures agreement with one particle convention, not accuracy: PRT on the same flow field gives 0.29 to 0.65 under other conventions and 0.998 under the published ones (§5.3)."
- **W4 · SHOULD · Repetition.** Keep each item once:

| item | where it appears | keep | cut or cite |
|---|---|---|---|
| gross vs net explained | 01:15, 02:13, 02:37, 05:21, 06:17; Fig. 1c, Fig. 7, Fig. S1, Table 1 caption, Table 3 note | §2.3 + Fig. 1c | 02:13 (keep only the weak-sink definition); 05:21 → "(Table 3; §6.2)"; Table 1 caption → cite §2.3 |
| forward tracking not new; hydraulic mixing cells history | 01:11, 01:15, 02:79, Table 1 fn 3 | 01:15 + Table 1 | 02:79 → one clause |
| "benchmark, not a reference … one particle convention" | 05:3, 06:3 | 05:3 | 06:3 |
| synthetic-only / no real transient application | 04:37, 06:3, 06:21, 07:5 | 04:37 + 07:5 | 06:3, 06:21 |
| PRT-zone caveats (F > 10⁻⁶ seeding, shared weak-sink treatment) | 05:33, 06:11, Fig. S1 | 05:33 | 06:11 → "(§5.3)" |
| S region r = 0.997 vs 0.00 | 05:43, 06:29 | 05:43 | 06:29 |
| Monte Carlo offsets | 05:41, 06:31 | 06:31 (one sentence) | 05:41 → Text S4 |
| stream share r = 0.94 | 05:53, 06:27 | 05:53 | 06:27 |
| sub-steps double new water in step 1 | 04:33, 04:45 | 04:45 | 04:33 → SI |
| 12 % west-edge / 68 % initial water | 04:41, 06:21, Fig. 4 caption | 04:41 | caption; 06:21 one clause |
| volume options 2e-4 / 4e-3 | 02:77, 04:45, 06:21, Fig. 4 | 04:45 | 06:21 → "(§4.4)" |

- **W5 · MUST · Over length.** The main text is 7,926 words against 7,500 ±5 % (limit 7,875), and the paper prints at roughly 19–20 pages. See the cut list.
- **W6 · SHOULD · Number notation.** The draft mixes "1e-12" (05:11), "3e-12" (05:41) and "10⁻¹⁵" elsewhere. Use "× 10⁻ⁿ" throughout.
- **W7 · SHOULD · Spelling.** The draft uses British spelling ("realisation", "factorisation", "licence"). Wiley copy-edits *Groundwater* to US English [check: journal style]. Settle this before assembly.
- **W8 · SHOULD · Well names.** "U___7" and "U___8" (05:21, 06:17) look like typos to a reader. Use the published IDs with a note in the Fig. 5 caption, or relabel them (U7) with a mapping there.

## 00_front.md

- **00:3 · SHOULD** · "contributing areas in seconds, checked against the water budget, also backward in time". A MODPATH user reads "backward" as their normal mode, so the line names no gain. Fix (118 characters): "Open MODFLOW 6 tool: well contributing areas in seconds, budget-checked, and how much pumped water was already stored."
- **00:5 · SHOULD** · "lacks a peer-reviewed description and open code". This leads with a deficit of a commercial method used by a regulator, and an editor will sense a fight. Fix: "is described only in conference papers and has no open implementation."
- **00:5 · SHOULD** · "solved exactly with or without flow loops". This is jargon in an abstract. Fix: cut "with or without flow loops", which also saves words, or write "including where flows circulate between cells".
- **00:5 · SHOULD** · "Two exact identities check every result against the water budget". The identities are model-wide sums per trace, not checks of each cell's result. Fix: "check every trace against the water budget".
- **00:5 · SHOULD** · "What is added is backward tracking in time". Readers will confuse this with MODPATH backward tracking. Fix: "New is backward tracking in time (not particle backward tracking):"
- **00:5 · SHOULD** · "we attribute its differences … to particle conventions, mixing and stream treatment". This is vague and misses the practitioner message. Fix (no numbers): "PRT on the same flow field reproduces the published areas only with the published particle conventions, which change the area as much as the choice between particles and full mixing."
- **00:7 · SHOULD** · "mixing cell" suggests Campana-type mixing-cell models. Fix: replace it with "capture zone"; consider adding "wellhead protection" and "particle tracking", the terms practitioners search for.

## 01_introduction.md

- **01:5 · MUST** · "each destination needs its own particles, so analyses of many wells … expensive". This is wrong for forward tracking, and the paper's own benchmark shows it: one forward particle per start cell served all eight wells in one run (05:11). A MODPATH reviewer will catch it. Fix: "Backward tracking needs particles for each destination, and forward tracking needs a particle per source cell and a rule at every weak sink, so analyses of many wells … repeat the full particle run for each realisation and scenario."
- **01:5 · SHOULD** · "backward particle tracking through time-varying flows is awkward". MODPATH 7 does transient backward tracking, so "awkward" is weak and contestable. Fix: state the real gap: "particles do not say what share of the pumped water was released from storage, or was in the aquifer at the start, and still need a stop-or-pass rule at weak sinks."
- **01:7 · SHOULD** · The capture-fraction paragraph breaks the line from particle tracking (¶2) to flux-based methods (¶4). Fix: move it after the definitions at 01:9 and cut it to two sentences.
- **01:13 · SHOULD** · Probabilistic capture zones by backward transport, Frind et al. (2002), key FRI02 in the citation map, are not cited, and they are close to what practitioners know. Fix: add one clause next to Neupauer and Wilson (1999).
- **01:15 · SHOULD** · This 7-sentence, ~170-word paragraph mixes the reference method's status with what no method does. Fix: split it into (a) the reference method as published and (b) the three gaps, which are backward tracking in time, the forward–backward check and a large-model comparison. Write "the published descriptions we found" in place of "the methods we read".
- **01:19–23 · SHOULD** · The three questions never ask what the results mean for drawing a zone, so §6 has no question to answer. Fix: extend Q3 with "… and what do they mean for how a protection zone is drawn and reported (Section 6)?"

## 02_methods.md

- **02:13 · SHOULD** · "We use gross accounting by default". This duplicates §2.3, and neither place gives the reason. Fix: keep only the weak-sink definition in §2.1. In §2.3 add: "Gross accounting is how transport models treat sink terms (§4.1), and credits a well with what it pumps."
- **02:21–33 · SHOULD** · The Fig. 1b worked example ("F = 6/11 = 0.55") is the sentence that rescues the consulting reader, but it sits at the end of a paragraph on volumes and boundary-control maps. Fix: move it directly after the "In words" of Eq. 1.
- **02:33 · SHOULD** · "Giving every sink term its own group yields boundary-control maps". This useful output is mentioned only in passing. Fix: "… boundary-control maps: for each cell, the share of its water that ends in the river, the drains, each well (Fig. …)." If there is no figure, say so in plain words.
- **02:37 · SHOULD** · "Which cells are fixed depends on the selection: a group selected by package…". This is implementation detail, and the consulting reader is lost here. Fix: move it to the code documentation or the SI, which saves ~50 words.
- **02:41 · SHOULD** · "needs no reordering for stability, no pivoting". This is redundant within a sentence that is already technical. Fix: "so the factorisation needs no pivoting."
- **02:55 · SHOULD** · "Their error therefore measures the assembly and the solve, not the flow model." The paragraph break leaves "therefore" without its antecedent, and the reader is not told what to do with a check. Fix: join it to the previous paragraph and add: "A failed check points to the tracing, for example a budget term not saved or a dropped MVR record, not to the flow model, whose own budget error is carried in r."
- **02:55 · SHOULD** · "Under net accounting the closure check has no cell budget error term…". This is opaque. Fix: one plain clause on why (net sources absorb r), or move it to §4.1.
- **02:63 · SHOULD** · "It gives a mean over mixed water (Eulerian), not a particle's (Lagrangian) first arrival." Add the consequence: "so it should not be used alone to draw a time-of-travel zone (§6.3)."
- **02:67 · SHOULD** · "(minimum, maximum, time-weighted mean, always/sometimes/never above a threshold, …)". This is an implementation list. Fix: move it to §3.2.
- **02:77 · SHOULD** · "where porosity differs from specific yield, tagged water appears or disappears". The reason is not given. Fix: "because GWT recomputes each cell's volume from the new heads with porosity, while the storage flows use specific yield."
- **02:79 · SHOULD** · "Forward tracking is not new." This paragraph repeats 01:11 and 01:15. Fix: "Forward tracking through storage is not new (§1; Table 1); what we add is §2.9." This saves ~60 words.
- **02:83 · SHOULD** · "with the transpose of each forward step's matrix". The consulting reader needs the question it answers, and Fig. 1 does not show it. Fix: add "It answers: of the water in this cell at time t, how much will the well pump before the end of the simulation? (Fig. 4d–f)". Drop "(and the "gwt" step-boundary adjustments)".

## 03_implementation.md

- **03:17 · SHOULD** · "On a synthetic three-dimensional grid of one million cells…". A consultant trusts a real model more. Fix: lead with Neversink (2–3 s for nine groups on 1.68 million cells; §5.1) and give the synthetic benchmark second. Say whether the solve uses the "16 cores"; otherwise drop the core count.
- **03:17 · SHOULD** · "each costs about 90 MB per million cells". Translate it into a practitioner's case: "tracing 100 wells individually on a 1.68-million-cell model needs about 15 GB" [check against PLAN Phase 2].

## 04_verification.md

- **04:5 · SHOULD** · The 10-model description runs to ~110 words. Fix: one sentence ("ten small MODFLOW 6 models cover DIS, DISV and DISU grids, XT3D flow loops, storage, SFR with MVR, MAW, and LAK with UZF") and the details in Table S4.
- **04:11–15 · SHOULD** · The prose repeats Table 2 and Fig. 2 number for number. Fix: "Every exact identity reached round-off (≤ 1.8 × 10⁻¹⁵); every comparison with an independent result (GWT, PRT, the worked example, DISU and split builds) agreed to within the flow-solver tolerance or the release-point error (Table 2)." Then keep only the model 7 flow-solve note and 9574 vs 9590 d, which is not in Table 2.
- **04:19–23 · SHOULD** · About 260 words of numbers. Condense to ~100 words: GWT match, forward–backward match and steady limit in one sentence each, with the values in Table 2.
- **04:21 · SHOULD** · "Each cell's water balance holds by construction". The reader will ask why a check that holds by construction is reported. Fix: drop it from the prose; Table 2 footnote 4 covers it.
- **04:31 · SHOULD** · "narrowed only as about h^0.5". Translate it: "halving the cell size narrows the band by only about 30 %, so on a finer grid it spans more cells." Add the practical rule: the F ≥ 0.5 area stayed within 5 % for h ≤ 50 m in these tests.
- **04:31 · SHOULD** · "8 to 90 % too large". This merges two problems. Fig. 3's caption gives 30–90 % (problem A) and 8–16 % (problem B), and a reader will take 90 % as the realistic number. Fix: give both.
- **04:33 · SHOULD** · Sub-step doubling (0.18 vs 0.09) is repeated at 04:45 (0.0078 vs 0.0042). Fix: keep tutorial 08 and move problem B to the SI (DS).
- **04:43 · SHOULD** · "8,766,800 m³" and "closure error of 0". The precision is spurious. Fix: "8.77 million m³" and "closes exactly".
- **04:43 · SHOULD** · "the 30-year zone does not reach the west edge". This is the practitioner hook (time-limited zone). Carry it to §6 (W2).
- **04:45 · SHOULD** · The per-tag forward–backward and GWT values duplicate the §4.2 checks. Fix: move them to a Table 2 note.

## 05_neversink.md

- **05:11, 05:41 · SHOULD** · "1e-12 m³/d", "3e-12 m³/d". Fix: "10⁻¹²" and "3 × 10⁻¹²" (W6).
- **05:15 · SHOULD** · "the overlap is 0.30 for F > 0.1 and 0.41 for F > 0.5". Fix: caveat first (W3), giving the particle spread before full mixing's number. Move the definition of "area-matched" to the Table 3 note.
- **05:21 · SHOULD** · "Buried stream cells, SFR reach cells with an active cell above, also stop particles". This appears before the particle conventions are explained (05:31) and is needed again at 05:57. Fix: move it into the conventions paragraph of §5.3.
- **05:21 · SHOULD** · "Net accounting … credits the eight wells with 3,944 m³/d". These numbers recur in §6.2, Table 3 and Fig. S1. Fix: "(net accounting: Table 3; §6.2)".
- **05:33 · SHOULD** · "the particle reference of §4.3". §4.3's reference was fine-grid PRT on a synthetic aquifer; the Neversink weight-losing PRT zone is a different object. Fix: "the weight-losing PRT zone (P > 0.5), used as a reference in the sense of §4.3".
- **05:33 · MUST** · "The gap to the published cells is therefore mixing against advective paths". "Therefore" claims more than the envelope test supports. By the paragraph's own caveats, coverage is an upper bound and the test covers only the spreading between sinks. The sentence also drops stream treatment, which the abstract names. Fix: "We read the gap to the published cells as mixing against advective paths plus the published particle conventions; the test above supports this only for the spreading between sinks."
- **05:37 · SHOULD** · "the median area with the stream network is 1,534 against 911". These ensemble numbers come before the ensemble is introduced (§5.5). Fix: move them to §5.6 or Table S2.
- **05:41 · SHOULD** · "lie one row south of their cells and are stored in run numbers sorted as text". This is bookkeeping. Fix: one clause ("after correcting two bookkeeping offsets, Text S4") and move the 60-realisation check to Text S4.
- **05:43 · SHOULD** · "There, the variation comes from the particle conventions." This rests on a correlation. Fix: "There, the variation follows the particle conventions."
- **05:53 · SHOULD** · "72 % is a larger share of the leakage of reaches already losing". This is study-specific mechanism. Fix: move it to the SI with Fig. 10.
- **05:57 · MUST** · "cuts the growth from 4.76 to 3.83". The reader cannot tell which configuration gives 4.76, and it is in no main-text table. Fix: name it ("PRT with the published conventions except stopping in buried stream cells grows 4.76 times; adding that stop gives 3.83") or move it to Table S3 and cite.
- **05:57 · SHOULD** · "Weight-losing particles grow faster than full mixing". No number is given. Fix: give the growth factor or cut the sentence and leave it to Text S5.

## 06_discussion.md

- **06:3 · SHOULD** · This opening paragraph repeats 04:37, 05:3 and 07:5. Fix: one sentence: "For transient flow the guidance below rests on synthetic models, and for steady flow on one benchmark that is a particle convention, not a reference (§4.4, §5)."
- **06:7 · SHOULD** · "we would combine the F = 0.5 area with particle tracking, as the Environment Agency (2019) does". The sentence says neither how nor when a zone counts as "small". Fix: say which zone comes from which method, and give "small" in cells from §4.3's transition band. Write "F > 0.5 area", not "F = 0.5 area" (terms.md); the same applies at 06:11.
- **06:9 · MUST** · "Each of these steps is about a third". This is ambiguous: the overlap rises by about 0.33 in absolute terms, while two sentences later "by a third" means a relative change (2,413 vs 3,736 m³/d, −35 %). Fix: "each raises the overlap by about 0.33, as much as or more than…" and "Release depth changes the water particles deliver by 35 %".
- **06:11 · SHOULD** · "We therefore present F ≥ 0.1 as a wide zone … and F = 0.5 as an advective core." A consultant cannot act on this. Fix: "For a protection zone we suggest F > 0.5 as the best single estimate of the advective zone and F ≥ 0.1 as a wider zone. Where the zone ends at weak sinks (gaining streams, wells taking part of their cell's outflow), check it with particle tracking under stated conventions: there F > 0.1 missed 13 to 27 % of particle-tracked zones on Neversink." Replace the repeated "Two caveats apply…" sentence with "(caveats in §5.3)".
- **06:17 · SHOULD** · "For a decision, the choice is what a well should be credited with". This leaves the choice to the reader. Fix: add "We use gross accounting for protection zones and source budgets, and net accounting only to reproduce a study made with the reference method." Move the per-well counts (214/58, 249/163, 502/466, 410/514) to Table S5 and keep the pattern in words.
- **06:21 · SHOULD** · "This comparison rests on the one-layer synthetic model". This repeats the caveat, and the numbers repeat §4.4. Fix: cut the first sentence; cite Fig. 4 with only "12 % vs none". Add the time-limited zone (W2).
- **06:27 · SHOULD** · "(r = 0.94 across realisations; Fig. 10)". This repeats 05:53. Fix: cut the sentence and keep "a report should say so".
- **06:29 · SHOULD** · This paragraph repeats 05:43 almost word for word. Fix: replace it with the action: "Where a particle-tracked probability varies between realisations, check whether the water reaching the wells varies too (§5.5)."
- **§6 general · SHOULD** · The Discussion has no guidance on cost and memory for many wells, or on grid resolution, both of which are first questions for a consultant. Fix: one sentence each, citing §3.3 and §4.3, in the W1 workflow paragraph.

## 07_limitations.md

- **07:3–9 · SHOULD** · Missing: the checks test the tracing, not the flow model; a model with wrong recharge gives exactly checked wrong zones. Fix: add one sentence. Consultants need to hear this.
- **07:5 · SHOULD** · Vertical mixing is limited to the tutorial 08 caveat (04:47), but it applies to every model with thick layers, including Neversink. Fix: "Each cell mixes over its saturated thickness, so thick layers spread a zone vertically as well as laterally."
- **07:9 · SHOULD** · "MF6 PRT aborts in cells wet only by a thin film". This is a defect of another code, not of the method. Fix: move it to Text S2 and keep the DISU sentence.

## 08_conclusions.md

- **08:3 · MUST** · "they held on the synthetic test models and on the Neversink model". Here "they" is the closure and forward–backward checks, but §5.1 reports only the closure check on Neversink. Fix: report the Neversink forward–backward error in §5.1 [check NS], or write "the closure check held on the Neversink model".
- **08:3 · SHOULD** · This is one 211-word paragraph of five long sentences. Fix: split it into method and checks, then what it means for practice. It already ends well, on "reported with its method, its conventions and its threshold".

## 09_availability.md

- **09:3 · SHOULD** · Several [check]s remain open (public URL, Zenodo DOI, released MF6 and FloPy versions, data-release authors). Editors check these at submission. Fix: resolve them before submission, as PLAN D3 already says.

## display/A.md (Table 1)

- **A:3 · SHOULD** · The caption runs to ~230 words. It repeats the definitions of F, G, gross and net, and includes a drafting note ("[check] marks a cell…"). Fix: ≤ 80 words. Cite §2 for the definitions and put the MODALL sentence in a footnote.
- **A:19–51 · SHOULD** · There are 17 footnotes, about 1,100 words, and they read as lab notes. Footnote 2 quotes an error message from an MF6 development build; footnote 3 spends 230 words on Partington et al. (2013) sub-steps. Fix: one line per footnote in the main table, with the full text in the SI. This saves about 1.2 printed pages.
- **A:7 · SHOULD** · "no steady-state option (Langevin et al. 2022)". Footnote 2 shows that porosity 0 gives the steady state in one step, so a GWT reviewer will object. Fix: "no documented steady-state option".
- **A:15 · SHOULD** · "None described" (reference method, checks). Fix: "None described in the papers we found", which is fair to a method whose current version is not documented.

## display/B.md (Fig. 1)

- **B:3 · SHOULD** · The caption runs to ~340 words. Panel (a) repeats Eq. 1's "In words" and panel (c) repeats the §2.3 numbers. Fix: about 180 words, describing the panels only.

## display/C.md (Figs 2–4, Table 2)

- **C:3 · SHOULD** · Fig. 2 duplicates Table 2, and its caption (~370 words) repeats Table 2 and §4.1–4.2. Fix: move Fig. 2 to the SI. If it stays, cut the caption to about 60 words.
- **C:15 · SHOULD** · Fig. 4's caption (~420 words) carries every number in §4.4. Fix: about 120 words of setup and panel descriptions, with the numbers in the text.
- **C:23–42 · SHOULD** · Table 2 is readable, but its "model" column mixes IDs and descriptions ("6 transient, 13 snapshots", "7 SFR + MVR vs SFT + MVT"), so the reader must remember ten models. Fix: replace "model" with "what is compared" (for example "G vs MF6 GWT at equilibrium", "DISU build vs DIS build") and move model IDs to Table S4. Fold "error measure" into footnotes, since most entries are "relative to …".

## display/D.md (Figs 5–10, Table 3)

- **D:3 · SHOULD** · Fig. 5 is a location map. Fix: print it at single-column width, or as an inset in Fig. 6.
- **D:11 / D:27 · SHOULD** · Fig. 7 and Table 3 show the same overlaps. Fix: keep one, or redesign Fig. 7 to plot overlap against flow to the wells so that it carries Table 3.
- **D:23 · SHOULD** · Fig. 10 is study-specific mechanism. Fix: move it to the SI (cut list item 5).
- **D:29 · MUST** · The column header "flow reaching the wells (m³/d)" is wrong for the net and plain-PRT rows. The well inflow is 3,671 m³/d in every row, and 3,944 and 9,555 are water credited to the wells, as the note itself explains. Fix: rename the column "water credited to the wells (m³/d)".
- **D:31–36 · SHOULD** · The expected area (910, 978) and flows repeat on three rows each. Fix: merge the cells. Cut the ~150-word note to the definitions not already given in the text.

---

## Five changes that would most improve the paper

1. **Make §6 prescriptive and add a workflow paragraph (W1, W2, 06:11, 06:17).** Say which zone to draw (F > 0.5, F ≥ 0.1, a particle check at weak sinks), which accounting to use (gross; net only to reproduce studies), and how to get a time-limited zone (backward tracking in time; not the mean travel time).
2. **Be fair to particle tracking and frame the benchmark caveat first (01:5 MUST, W3).** Fix the per-destination cost claim, which the paper's own benchmark contradicts, and state the real transient gap. Open §5.2 with the 0.29–0.998 particle spread so that 0.30–0.41 reads as "inside the range", not "failed".
3. **Cut duplication of numbers and explanations (W4, cut list items 3–7, 9).** §4 prose becomes verdict sentences plus Table 2. Gross/net, the novelty statement and the caveats each get one home. This brings the main text from 7,926 to about 7,250 words, even after the guidance paragraph is added.
4. **Reduce display items to reach 15–16 pages (cut list items 1, 2, 5, 7, 8).** Move Table 1's footnotes, Fig. 2 and Fig. 10 to the SI; cut the Fig. 1 and Fig. 4 captions; resolve the Fig. 7 / Table 3 duplicate.
5. **Fix the claims that overreach or mislead.** These are 08:3 (forward–backward check on Neversink), 05:33 ("therefore"), 06:9 ("a third" used two ways), 05:57 (undefined 4.76) and D:29 (credited water labelled as flow reaching the wells).

## Counts

| file | MUST | SHOULD |
|---|---|---|
| whole paper | 1 | 7 |
| 00_front | 0 | 7 |
| 01_introduction | 1 | 5 |
| 02_methods | 0 | 12 |
| 03_implementation | 0 | 2 |
| 04_verification | 0 | 10 |
| 05_neversink | 2 | 10 |
| 06_discussion | 1 | 8 |
| 07_limitations | 0 | 3 |
| 08_conclusions | 1 | 1 |
| 09_availability | 0 | 1 |
| display A (Table 1) | 0 | 4 |
| display B (Fig. 1) | 0 | 1 |
| display C (Figs 2–4, Table 2) | 0 | 3 |
| display D (Figs 5–10, Table 3) | 1 | 4 |
| **total** | **7** | **78** |
