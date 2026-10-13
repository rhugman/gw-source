# Round 4 reader review

Reviewer: a practising groundwater modeller who knows MODFLOW, MODPATH and protection zones, but not linear algebra, PRT options or this paper's vocabulary. Read-only review of `sections/00–09`, `display/*.md` and the figure PNGs, with the SI skimmed only where the text sends the reader. Line numbers are those of the files on branch `paper-draft`.

Main-text word count, with HTML comments removed: §1 1,049; §2 2,156; §3 509; §4 1,206; §5 1,498; §6 1,361; §7 349; §8 250; §9 139. That totals **8,517**, and the abstract is about 250. §2 is 156 over its budget of 2,000.

## 1. The author's comments

The 55 comments are the 51 bullets of `user_r3_comments.md`, with four bullets split because they make two points each: §3.3 (heading and RAM), Fig. 2 (noise and "identities"), Fig. 6 (colormap and map content) and §6.5 (incomprehensible, and no advice).

| # | Comment (short) | Verdict | Where | Reason |
|---|---|---|---|---|
| 1 | Title should say what the tool provides | YES | 00_front.md:7 | The title now names the outputs: contributing areas, the sources of pumped water and the budget check. |
| 2 | **Abstract opener** too hard; open for a non-technical reader | YES | 00_front.md:11 | It now opens on protection zones, contributing areas and the model. The stop-or-pass detail comes in sentence 4. The abstract is now choppy, though (see reader's pass A1). |
| 3 | "We write it as one sparse linear system…" | YES | 00_front.md:11 | Gone. |
| 4 | "exact identities" | YES | 00_front.md:11 | Replaced by "checked against the water budget". |
| 5 | Harsh: "not described in a journal article" | YES | 00_front.md:11 | It now reads "used for protection zones in England. It is not open source. We extend the method…". |
| 6 | 81 % sentence weird in mid-abstract | YES | 00_front.md:11 | It is now introduced by the question it answers. It is attributed to the wrong direction of tracking, though (MUST A2). |
| 7 | Neversink sentence jumbled ("compared to Neversink? faster?") | PARTLY | 00_front.md:11 | The two points are now separate sentences. The reader still cannot tell what was compared: the published area is not mentioned, and "within the range" does not say a range of what. The 2–3 s has no comparator. |
| 8 | **Introduction lacks flow** | PARTLY | 01_introduction.md:3–19 | The structure is now logical: context, overview, then one paragraph per family. Two paragraphs still end off-topic. 01:15 ends on "we read only the abstract of Bedekar et al." 01:17 bolts two general gaps (the budget check, and no large-model comparison) onto the adjoint paragraph. |
| 9 | Two-part sentence (particle tracking) | YES | 01:7 | Split. |
| 10 | Overview paragraph of all methods first | YES | 01:5 | Four families are named before any detail. |
| 11 | Why weak sinks? missing chaining | YES | 01:7 | "But particles need a rule at weak sinks", followed by a definition and why the rule matters. |
| 12 | "The destination is the set of sink terms…" weird | YES | 01:9 | Gone. "Destination group" is now used before it is defined, though (B2). |
| 13 | Capture fractions vs F unclear | YES | 01:9 | Three explicit sentences: Leake's fraction comes from two runs; F comes from one run. |
| 14 | MODALL "frequently" | YES | 01:11 | Moot. The sentence is rewritten without it. |
| 15 | FlowSource paragraph lands flat | YES | 01:11 | It now follows from the full-mixing paragraph and introduces flow loops, net accounting and snapshots. Its last sentence, "FlowSource is not open source.", still ends it abruptly. |
| 16 | Fig. 1 busy; no "tutorial" | YES | fig1 PNG; display/B.md:3 | No tutorial labels remain. It has one idea per panel. |
| 17 | Eq. (1) missing predecessor | YES | 02:7, 02:17 | The budget equation is Eq. (1) and the per-cell rule is Eq. (2). |
| 18 | "bookkeeping of FlowSource" weird | YES | 02:37 | "credits a sink with all the water that passes through its cell, as FlowSource does". |
| 19 | "tutorial 02" | YES | 02:39 | "a three-layer example model", described in the SI. |
| 20 | Flow loops: first mention unexplained | YES | 01:11; 02:45 | Defined at both places, with the reason it matters ("A single pass in flow order therefore cannot solve a loop exactly"). |
| 21 | "For the specialist" | YES | 02:47 | The wording is gone. The four linear-algebra sentences remain, though (B5). |
| 22 | Merge snapshots into the transient subsection | YES | 02:71–83 | §2.7 now covers snapshots (existing methods) and then transient tracking (the extension). |
| 23 | Flow-error sentence unclear | YES | 02:81 | Two plain sentences, then the GWT parallel. |
| 24 | §2.9 "well" → "sink" | YES | 02:87, 02:89 | "will reach the sink" and "how much of the water a sink took". |
| 25 | PRT appears out of the blue | YES | 03:11 | A lead sentence gives the purpose ("so that the same problem can be run with particles and the two methods compared"). |
| 26 | Heading "Cost" → "compute cost" | YES | 03:13 | Done. |
| 27 | RAM? | YES | 03:15 | Measured peak 2.5 GB, 0.19 GB per further group, and advice to batch wells. |
| 28 | §4.1 test models need details | YES | 04:5 | Each model is named with what it adds. Full set-ups are in the SI. |
| 29 | Fig. 2 noisy; prose guidance needed | PARTLY | 04:7; fig2 PNG | Three reading sentences were added. The figure itself is unchanged and still shows labels the reader cannot decode: the x-axis says "measure per check in **Table 2**" (there is no Table 2), "[FB13] example", "5 XT3D, cycles", "machine epsilon" (the text says "machine precision"), and a "hand-built 15-cell network" and "sub-steps vs refined steps" row that the text never mentions. |
| 30 | Caption word "identities" | YES | display/C.md:3 | "The checks that must hold exactly". |
| 31 | Weight-losing PRT particles not explained | YES | 03:11; 06:7 | Weight, loss at each sink and the credit to the destination are all explained in plain words. |
| 32 | "holds by construction" weird | YES | 04:21 | Replaced by "follows from how the volumes are carried… tests only the bookkeeping". |
| 33 | Model 10: why should the reader care | YES | 04:23 | "The two methods agree where flows are steady, so a user can trust either." The sentence before it ("they differ by at least 0.40 and 0.52") is unclear (B11). |
| 34 | Strict/non-strict thresholds: what is F, why care | PARTLY | 04:31 | F and the meaning of 0.1 and 0.5 are now explained. The ≥/> note is still in the main text, and nothing answers "why do I care". Decision 24 suggested moving it to the SI. Simpler: use one notation throughout. |
| 35 | "Tutorial 08" in §4.4 | YES | 04:37–39 | The seasonal example model is described before its results. |
| 36 | Jaccard hard to follow | YES | 05:15 | Plain definition, with what 1 and 0 mean. |
| 37 | "is a core" | YES | grep | The word "core" no longer appears. |
| 38 | Fig. 6 blue colormap | YES | fig6 PNG; display/D.md:7 | Five classes of reversed viridis, with 0.1 and 0.5 as class edges. |
| 39 | Fig. 6 streams, wells, shared axes | YES | fig6 PNG | Wells and SFR reaches are shown, with equal windows and one scale bar. |
| 40 | "Text S6)" unexplained | YES | display/A.md:3 | The first SI citation is written in full ("Supporting Information, Text S1"), and later ones follow that pattern. |
| 41 | "Plain particles": what and why | PARTLY | 05:29; fig7 PNG; display/D.md:11 | The term is gone from the text but is still a row label in **Fig. 7** ("cell volume, plain particles"). That row sets the 0.29 that begins the headline range "0.29 to 0.998" (05:25), so the low end of the range is no longer explained in the main text (MUST C3). |
| 42 | **§5.3: why this analysis? shouldn't we only compare with the published convention?** | PARTLY | 05:3; 05:25 | The purpose is now clear and up front: "Why not compare with the published area alone? Then every difference would count as an error of full mixing." That answers the author's question. The section is still hard to follow at 05:33 (the F-against-P paragraph, the hardest in the paper), so "I don't understand this section" still partly applies. |
| 43 | §5.5 "76 min on six processes" | YES | 05:41 | Dropped. |
| 44 | §5.5 confusing: what is compared, why it matters, why different | PARTLY | 05:41–47 | What is compared, and why it matters, are now clear. Why they differ is not: "the published area changes with the particle settings, not with the water reaching the wells" (05:47) makes no sense to a reader, because the settings are the same in every realisation. The r = 0.997 and r = 0.00 do not say what is correlated with what. |
| 45 | §5.6 needs more context | PARTLY | 05:55–57 | The buried-stream mechanism is now explained. The last sentence still drops "weight-losing particles from 4.76 to 3.83 times" with no context: these particles are not in Fig. 9, and they grow faster than full mixing. Fig. 9's stream-network curve (3.42) is never discussed. |
| 46 | §6 opening hedges | YES | 06:3 | Opens on the three outcomes. |
| 47 | §6.1 whose published cells | YES | 06:11 | "the published Neversink contributing cells, those whose published particle ends in a supply well". |
| 48 | §6.3 two-part sentences | YES | 06:21 | Split. |
| 49 | §6.3 "tutorial 08" | YES | 06:21 | "the seasonal example model (Section 4.4)". |
| 50 | **§6.5 "incomprehensible"** | PARTLY | 06:35 | Each piece of advice now leads in bold. Item 1 still offers three different areas (F > 0.5, the expected area, F > 0.1) with no rule for which one to draw. "Take the size of the zone from the expected area, the sum of F" does not say how to turn a number into a map. |
| 51 | **§6.5 "no advice after this statement"** | YES | 06:33–43 | Five numbered pieces of advice, each with its reason and a pointer to the evidence. |
| 52 | **§6.5 "terrible… repeat of results… no discussion"** | YES | 06:31–43 | It now reads as practical advice, not results. Item 5 still repeats a Fig. 4 result. §6.4 (06:29) still nearly repeats §5.4 (D5). |
| 53 | **§7 should be limitations of the method** | YES | 07:3–15 | Mixing in a cell, grid spacing, steady flow per step, memory, porosity, and the remaining weak-sink choice. Only one short paragraph is about testing scope. |
| 54 | **§8 opening: not "we did the other guys' work differently"** | PARTLY | 08:3 | It still opens by describing FlowSource and then "It is not open source.", the framing the author asked to avoid. The author asked for "We extended [their method] to do x, y, z … and open source", with open source as the last of the gains. |
| 55 | §8: make Neversink generic | YES | 08:5 | "Tested against a published real-world regional model". |

**Counts: YES 45, PARTLY 10, NO 0.**

## 2. Reader's pass

I read the main text once, in order. MUST means a reader or referee will stumble on it, or that it misstates a result. SHOULD means it costs clarity or words.

### A. Title, impact statement, abstract (00_front.md)

- **A1, SHOULD, 00:11.** The abstract is now 23 short sentences, many of 4–8 words ("That choice changes the area." "It is not open source." "Each well is credited only with what it pumps."). It reads as a list. "Each well is credited only with what it pumps" does not say why that is better, since the reader does not yet know that the alternative credits more. *Fix:* group the additions into two or three sentences. For example: "We extend the method in open-source code for MODFLOW 6. It solves the shares exactly, also where water circulates between cells. It credits each well with what it pumps rather than all the water passing its cell, and it checks every trace against the water budget."
- **A2, MUST, 00:11.** "Backward tracking tells a manager how much pumped water was already stored in the aquifer. In a seasonal example model, this was 81 %…" The 81 % (and the 98 % and 68 %) come from **forward** transient tracking (Fig. 4b, "Transient tracking forward"; 04:45). Forward tracking, as §2.7 says (02:83), "is not new" and is GWT unit-concentration transport. The product only backward tracking gives is the time-limited area: which water now in the aquifer reaches the well within a horizon (Fig. 4d; 04:47). The abstract therefore sells the new capability on a result the old one gives. *Fix:* "Transient tracking tells a manager how much pumped water was already stored in the aquifer (81 % of the first ten years' pumping in a seasonal example). Run backward in time, it maps which water now in the aquifer will reach the well within a stated time." The intro says the same at 01:19 ("Backward tracking… A manager can then see how much pumped water was already stored"), and §4.4 says it at 04:45 under forward tracking. Make all three consistent.
- **A3, MUST, 00:11.** "The full-mixing areas fall within the range particle tracking gives under different particle settings." It does not say what is measured (agreement with the published particle-tracked area) or what the range is. As written, the reader pictures areas nested inside other areas. *Fix:* "Their agreement with the published particle-tracked areas lies within the spread that particle tracking itself shows when its settings change." See also C3 for whether that claim is fair.
- **A4, SHOULD, 00:11.** The most useful finding for practitioners, that particle settings changed the area as much as the choice of method (06:11, 08:5), is not in the abstract. *Fix:* add it as the last sentence, together with the reporting advice of 08:5.
- **A5, SHOULD, 00:9.** In the impact statement, "including how much pumped water was already stored" hangs off "each checked against the water budget". *Fix:* "…in seconds, each checked against the water budget, and, for transient models, how much of the pumped water was already stored."

### B. Introduction and Methods (01, 02)

- **B1, SHOULD, 01:3.** "Such studies need the share of each cell's water that reaches the well." This is a leap. Risk-based studies need an area per realisation, and why a share is needed is not said. *Fix:* "Such studies need, for every cell, how much of its water reaches the well, so that each realisation gives an area." Then say why the budget check matters: a zone that does not account for all the pumped water is incomplete.
- **B2, SHOULD, 02:25.** "destination group" is first used here (and at 02:47) but defined only at 03:15. *Fix:* define it at 02:9: "A destination is one or more sink terms traced together, such as one well or all the wells of a wellfield; each is traced as a group."
- **B3, SHOULD, 01:15.** "For unit-concentration transport we read only the abstract of Bedekar et al. (2024)." A referee will read this as an unfinished literature review. It also leaves the paragraph ending off-topic. *Fix:* resolve the [check] before submission. Until then, keep the caveat in the Table 1 footnote only (display/A.md:27). Introduce hydraulic mixing cells in a few words ("a mixing-cell model that tracks fractions of water by origin"). "As documented, both run forward" leaves "both" unclear; name them.
- **B4, SHOULD, 01:17.** "Two further gaps remain" (no budget check in any method; no comparison on a large real model) are general gaps bolted onto the adjoint paragraph. *Fix:* move them to the start of 01:19 as the bridge to "This paper…": "None of these methods checks… and no full-mixing delineation has been compared with particle-tracked areas on a large real model. This paper…"
- **B5, SHOULD, 02:47.** "Numerically, the solve is a block-triangular sparse LU factorisation over the strongly connected components… M-matrix… pivoting". Four sentences this reader cannot use. *Fix:* keep one plain sentence on what the user gets ("Under gross accounting one factorisation serves every destination group, so tracing many wells costs little more than tracing one"). Move the rest to the SI (saves about 45 words).
- **B6, SHOULD, 02:43.** "the cells can be put in flow order, each after the cells its water flows to". A modeller reads "flow order" as upstream to downstream, and this sentence describes the reverse. *Fix:* "ordered so that each cell's downstream neighbours come before it when tracing backward, and its upstream neighbours come before it when tracing forward".
- **B7, SHOULD, 02:37.** "It uses the cell-to-cell flows only, with each cell's net source (cell-to-cell outflow minus inflow) in place of its source and sink terms. The destination cells are fixed at F = 1." This is opaque. *Fix:* "In effect, every cell containing the well is treated as if all the water leaving it went to the well (F = 1)." The Fig. 1b sentence that follows then reads easily.
- **B8, SHOULD, 01:19 against 02:51.** The intro says "two budget checks", while §2.5 says "Three checks". *Fix:* make them agree. Either say "budget checks", or name all three in §1.
- **B9, SHOULD, 02:59.** "Boundary-control check" and "boundary-control maps" are named but not explained. The reader does not know why the term is used or what a map is for. *Fix:* one clause: "…boundary-control maps, which show for every cell which sink takes its water".
- **B10, MUST, 02:83 and 06:23.** Both send the reader to Section 4.4 for the difference between the "flow" and "gwt" volume options ("tagged water appears or disappears at step boundaries"; "give different results"). §4.4 no longer says anything about it, because the material was moved to the SI (04:49 comment). The 02:83 paragraph is already the second-hardest in §2: two volume options, and no advice on which to use. *Fix:* point both to the SI item {SI: transient checks on the seasonal example model}. In 02:83, add one sentence of advice: "Use the default unless the result must match a GWT run."

### C. Implementation, verification (03, 04)

- **C1, SHOULD, 03:11.** PRT is not placed for a reader who knows MODPATH. *Fix:* "PRT, the particle-tracking model built into MODFLOW 6 since version 6.5 and the successor to MODPATH". The last sentence, "Compared with full mixing, they test only how water spreads between sinks", is hard. *Fix:* "Because they lose water at sinks exactly as full mixing does, any difference between the two comes from how water spreads between sinks: along particle paths, or mixed across whole cells."
- **C2, SHOULD, 03:15.** "the solve for four groups took 0.55 s, or 0.42 s with 7,000 flow loops". Faster with loops is counter-intuitive and unexplained. *Fix:* drop the sentence, since the Neversink timing already makes the point, or add the reason (saves 25 words). Also at 03:9, the snapshot running-statistics sentence does not belong to this paragraph. Drop it.
- **C3, MUST, 04:7 and Fig. 2.** As for comment 29. The axis label cites "Table 2", which does not exist in the paper. "[FB13]" is an internal citation key. "cycles" should be "flow loops". The legend says "machine epsilon" and the text "machine precision". Two rows ("hand-built 15-cell network", "sub-steps vs refined steps") are never mentioned in the text. *Fix (figure agent):* relabel the axis "error reached (measure per check in Table S1)". Use "Foley and Black (2013) example", "flow loops (XT3D)" and "machine precision". In 04:7, add one sentence saying that the lower rows test transient tracking (§4.2) and transport sub-steps (SI).
- **C4, SHOULD, 04:19.** "Both directions therefore rest on an independent code." The meaning is unclear. *Fix:* "Forward tracking is thus checked against GWT, and backward tracking against forward tracking."
- **C5, SHOULD, 04:23.** "At the other end of the run they differ by at least 0.40 and 0.52": which "they", and which end? *Fix:* "At the start of the run, c still differs from G by up to 0.40. At the end, w differs from F by up to 0.52. The agreement at the far ends is therefore not trivial."
- **C6, SHOULD, 04:27.** "against PRT on a 12.5 m grid west of the gaining river, where no method meets a weak sink". This is cryptic. *Fix:* "compared only west of the river, so that neither method has to deal with a weak sink".
- **C7, SHOULD, 04:33.** The numerical-dispersion results stop without a "so what". *Fix:* end with one practical sentence: "On cells of 50 m or less, the F ≥ 0.5 area is within 5 % of the true size. The F ≥ 0.1 area holds the true area but is 1.1–1.9 times too large."
- **C8, SHOULD, 04:37.** "The paper has no transient application to a real model (Section 7)." A hedge in the opening line of the demonstration. It already appears at 07:15. *Fix:* drop it here. At 04:39, "With one layer, recharge cannot form a young layer on top of old water" does not say why the reader should care. *Fix:* "…so the shares in Fig. 4 are not affected by layering."
- **C9, SHOULD, Fig. 4 and display/C.md:15.** The dashed vertical line (the river) is not identified in the caption. Panel (c) shows F > 0 east of the river, and a reader asks how water from across the river reaches the well. The caption gives "95 % initial water" for year 1, while the panel shows "98 %" at year 1. Both are right (one is the last season, the other the cumulative share), but side by side they look like an error. *Fix:* add to the caption "Dashed line: river. East of it, water passes beneath the river, which takes only part of its cells' water." Either drop the 95 % sentence or say "in that season alone".

### D. Neversink (05)

- **D1, SHOULD, 05:11.** "2–3 s, against 44 s for the MODFLOW 6 run". The comparator a modeller wants is the particle run. *Fix:* add the MODPATH 7 or PRT run time, if one is available in the evidence.
- **D2, SHOULD, 05:17.** "The expected area, the sum of F over the start cells". Why a sum of shares is an "area" is not explained, and it is used again at 05:21, 05:43, 06:15 and 06:35. *Fix:* "the expected area, the sum of F over the start cells, counts each cell by the share of its water that reaches the wells".
- **D3, MUST, 05:25 and 05:29, with Fig. 7.** The headline range "0.29 to 0.998", repeated in the §5 intro, the abstract, §6 and §8, has its low end set by the "plain particles" row of Fig. 7. Those particles pass weak sinks without losing weight (in effect MODPATH's pass-through option) and deliver 2.6 times the wells' water (SI, diagnosis of the first PRT runs). The second-lowest value, 0.39, comes from release at the water table, which delivers 66 % of the inflow. The main text no longer explains either. The particle runs that conserve water score 0.62–0.998, all above full mixing (0.30–0.41). "Full mixing lies within the range" is true but depends on the two weakest particle settings, and a referee will notice. *Fix:* in 05:29, keep one sentence naming the low end: "Particles that pass weak sinks without losing water, as with MODPATH's pass-through option, credit the wells with water that streams take on the way. Their P > 0.5 area overlaps at 0.29." State the result honestly in 05:33, 06:3 and 08:5. For example: "full mixing agrees with the published area less well than particles that lose water at sinks (0.41 against 0.62). The gap comes from mixing, which §5.3 measures, and from the published settings." Rename the Fig. 7 row in the same words.
- **D4, MUST, 05:33 (the hardest paragraph in the paper).** It opens with a question ("Which F area should match the P > 0.5 area?"), then the mechanism, then counts, then "Covering it takes the lower threshold F > 0.1", then two caveats, then four percentages, then the conclusion. "Covering" is also overstated, since F > 0.1 covers only 87 %. *Fix:* lead with the conclusion and one number, and put the caveats at the end. For example: "Mixing spreads the water that reaches the wells over more cells, each with a lower F. The full-mixing area that matches the particle area is therefore drawn at a lower threshold. F > 0.1 covers 87 % of the P > 0.5 area, while F > 0.5 covers 59 %. Nearly all F > 0.5 cells (92 %) lie inside the particle area. [caveats]. The gap to the published area therefore comes from both mixing and the published particle settings."
- **D5, SHOULD, 05:27.** "Buried stream cells: SFR reach cells with an active cell above, where a gaining reach is usually a weak sink." A modeller pictures streams at the surface. *Fix:* say why they exist ("where the stream is connected to layer 2 or below, under an active layer-1 cell") and why they matter ("a particle starting above passes down into the cell and stops there").
- **D6, SHOULD, Fig. 6 caption (display/D.md:7).** "(pale area south-east of the U wells)". In panel (d) the area added south-east of U is green (F 0.1–0.25), not pale. The pale (yellow, F 0.01–0.1) extension is in panel (f), west of SV_S. *Fix:* "(green area south-east of the U wells in d; pale area west of SV_S in f)".
- **D7, MUST, 05:47.** As for comment 44. "There, the published area changes with the particle settings, not with the water reaching the wells." The settings are identical in every realisation, so the reader cannot follow the sentence. "PRT… follows this variation (r = 0.997, 60 realisations). The sum of F does not (r = 0.00)" does not say which variables are correlated. *Fix:* "In the S region, the published area varies between realisations by 32 %. PRT with the published settings reproduces this variation from realisation to realisation (r = 0.997). The water reaching the wells, measured by the sum of F, does not vary with it (r = 0.00). The variation comes from how the stop rule meets each realisation's weak sinks, not from a change in the water the wells take." Also explain in a clause why there are 357 published areas but 358 realisations (05:41).
- **D8, SHOULD, 05:51.** "the median full-mixing area" does not say how a full-mixing area is counted here (the sum of F, according to the Fig. 9 caption). *Fix:* say "the median expected area (sum of F)".
- **D9, SHOULD, 05:55.** "Most of the added pumping is recharge that discharged to streams at base pumping." This is the bridge to Leake's capture (01:9) that the reader has been prepared for, but it is not used. *Fix:* "In Leake's terms the added pumping is captured stream discharge. Traced through the aquifer, that water is recharge, so the area grows."
- **D10, MUST, 05:57 and Fig. 9.** As for comment 45. "lowers the growth of weight-losing particles from 4.76 to 3.83 times". Weight-losing particles are not in Fig. 9, and growing 4.76 times is faster than full mixing (4.09), which the text never mentions. The stream-network curve in Fig. 9 (3.42, slower than pumping) is never discussed. *Fix:* either drop the 4.76 → 3.83 sentence to the SI and say only "Stopping particles at buried stream cells accounts for most of the difference ({SI: one convention at a time})", or add the curve to Fig. 9. Add one sentence on the stream-network curve, or drop it from Fig. 9. In the Fig. 9 legend, "published conventions" should be "published settings", as in the text.
- **D11, SHOULD, Fig. 8.** It still uses a blue sequential map in which low values vanish into the background. The SV_S network panel (i) is almost invisible. The author asked for Fig. 6 to change for this reason, and will say the same here. *Fix (figure agent):* use the Fig. 6 classes and colours for probability and mean F.

### E. Discussion, limitations, conclusions (06–08)

- **E1, SHOULD, 06:11.** "Releasing particles at the water table cut the water they delivered by 35 %." This is a new result in the Discussion, and its reason (zero vertical velocity at the water table) is in the SI only. *Fix:* move it to 05:29 with that reason, or drop it. It is useful advice, so prefer the move.
- **E2, SHOULD, 06:29.** §6.4 nearly restates §5.4 ("extra cells linked by stream routing… extends the area upstream"). Its one discussion idea is "decides which question a trace answers", but it never says which question each representation suits. *Fix:* merge it into §6.5 item 4 as advice. For example: "Treat streams as cells when the zone protects the aquifer recharge the well draws on. Use the stream network when stream water quality upstream also matters, for example where losing reaches feed the well." This saves about 80 words.
- **E3, MUST, 06:35 (item 1).** As for comment 50. Three areas (F > 0.5, the expected area, F > 0.1) are offered with no rule for choosing between them. "Take the size of the zone from the expected area" cannot be acted on. *Fix:* give one procedure. For example: "Draw the F > 0.5 cells. If the zone must match the volume pumped, extend it to the cells with the largest F until their number equals the sum of F (the area-matched zone of Fig. 7). Where the decision calls for caution, use F > 0.1 instead." Also say which layer to map: the F of the uppermost active cell, as in Fig. 6.
- **E4, MUST, 06:33–43.** §1 opens on risk-based zones from ensembles (01:3), and §5.5 traces 358 realisations. Yet §6.5 gives no advice on ensembles: whether to map mean F, the share of realisations with F > 0.5, or something else. *Fix:* add item 6: "For an ensemble, map …, because … (Section 5.5)". If the authors have no basis for a recommendation, say so as a named stance.
- **E5, SHOULD, 06:43 (item 5).** The most common time-limited zone is a short one (the 50-day inner zone in England). The text says short horizons "were not tested", and does not draw the practical conclusion. *Fix:* "For short time-limited zones, such as 50-day inner zones, use particle tracking (item 2) until the sub-step approach has been tested." Also say which flow field to use for a steady zone from a transient model.
- **E6, SHOULD, §6.5 and 08:5.** The reporting advice ("method, particle settings, stream representation and threshold", 08:5) appears first in the Conclusions. *Fix:* make it the last item of §6.5, so the Conclusions summarise it rather than introduce it.
- **E7, MUST, 08:3.** As for comment 54. *Fix:* "We extended the full-mixing method of FlowSource (Foley and Black 2013; Black and Foley 2013), used for protection zones in England, in open-source code for MODFLOW 6. The code solves… [list]." This drops the standalone "It is not open source."

## 3. Answers

**Can I state the paper's three findings from the abstract alone?** Mostly. (1) Every trace meets the water-budget checks and matches MODFLOW 6 transport to rounding error. (2) A trace of a 1.68-million-cell regional model takes 2–3 s. (3) On that model, the full-mixing areas fall within the range that particle tracking gives under different particle settings. I can also pick out a fourth, the 81 % of stored water. Finding 3 is too vague to repeat with confidence: a range of what, and against what? The abstract does not give the "why" that §1's third question promises (mixing spreads water over more cells, and the particle stop rule at buried streams). It also omits the practical lesson that particle settings moved the area as much as the method did. The 81 % is credited to backward tracking although it is a forward result (A2).

**After §6.5, could I draw a protection zone with this tool? What would I still need?** I could draw a first zone: trace the well with gross accounting, map F, and draw F > 0.5, or F > 0.1 for caution. I would still need:
- which layer to map (uppermost active cell?);
- what to do with the expected-area advice, that is, how to turn a number into a map (E3);
- a cell-size rule (§4.3 implies 50 m or less, but §6.5 does not say so);
- how to use an ensemble, the case the Introduction opens with (E4);
- which flow field to use for a steady zone from a transient model;
- what to do for a 50-day zone: probably particles, which should be said (E5);
- how to choose between the stream representations, which §6.4 frames but does not answer (E2);
- what to report with the zone, which is now only in §8 (E6).

**Hardest paragraph:** 05_neversink.md:33 ("Which F area should match the P > 0.5 area?"). Mechanism, counts, a threshold, two caveats and four percentages come before the conclusion, and "covering" is overstated (D4). The runner-up is 02_methods.md:83, on the "flow" against "gwt" volume options, with no advice on which to use (B10).

**Is the paper too long anywhere?** The main text is about 8,520 words by my count and about 8,570 by the orchestrator's, against a cap of about 8,500. These cuts save about 330 words and lose nothing a reader needs:

| Cut or move | Where | Words saved |
|---|---|---|
| §6.4: merge its single discussion idea into §6.5 item 4 | 06:27–29 | ~80 |
| Linear-algebra sentences (LU, strongly connected components, M-matrix, pivoting) to the SI | 02:47 | ~45 |
| Repeated definitions of F and of the 0.1/0.5 areas, after §4.3 and §5.2 | 06:9, 06:15, 06:35, display/D.md:7 | ~50 |
| Synthetic one-million-cell benchmark sentence | 03:15 | ~25 |
| Snapshot running-statistics sentence | 03:9 | ~15 |
| "4.76 → 3.83" sentence to the SI (D10) | 05:57 | ~30 |
| Strict/non-strict note to the SI (comment 34) | 04:31 | ~25 |
| "The paper has no transient application" (duplicate of §7) | 04:37 | ~15 |
| "we read only the abstract of Bedekar" sentence (B3) | 01:15 | ~15 |
| Water-table 35 % sentence, moved to §5.3 rather than cut (E1) | 06:11 | ~15 |
| Eq. (9) words "In words: …" overlap with 02:89 | 02:93 | ~15 |

§2 is the section most over its budget (2,156 against 2,000). The 02:47 and 02:89–93 trims bring it close to budget.

## 4. Short report

- **Author's comments: YES 45, PARTLY 10, NO 0.** The PARTLY items are 7 (abstract Neversink sentence), 8 (Introduction flow), 29 (Fig. 2), 34 (thresholds), 41 (plain particles still in Fig. 7), 42 (§5.3), 44 (§5.5), 45 (§5.6), 50 (§6.5 item 1) and 54 (§8 opening). Of the six the author flagged hardest:
  - the abstract opener, §6 opening and §7 are fixed;
  - §6.5 is much better but item 1 is still not actionable;
  - §5.3's purpose is fixed but its last paragraph is not;
  - §8 still opens on FlowSource and "It is not open source."
- **The five most serious reader problems:**
  1. **The headline Neversink claim rests on the two weakest particle settings** (D3; 05:25, 05:29, 06:3, 08:5, abstract). The low end of "0.29–0.998" comes from pass-through particles that deliver 2.6 times the wells' water, and the text no longer explains them. Every particle run that conserves water agrees with the published area better than full mixing does.
  2. **The abstract credits the 81 % stored-water result to backward tracking** (A2; 00:11, 01:19). It is a forward result that GWT also gives. The genuinely new backward product, the time-limited area, is missing from the abstract.
  3. **05:33, the F-against-P paragraph, is the hardest in the paper** (D4). It puts its conclusion last and overstates "covering".
  4. **§6.5 still cannot be followed to a zone** (E3, E4). Item 1 offers three areas with no rule. There is no ensemble advice, although the Introduction opens on ensembles. Layer and cell-size advice are also missing.
  5. **§5.5 and §5.6 still lose the reader** (D7, D10). "Changes with the particle settings" makes no sense when the settings are fixed. An unexplained weight-losing growth of 4.76 → 3.83, and an undiscussed stream-network curve in Fig. 9, follow.
  - Close behind: Fig. 2 still cites a non-existent "Table 2" and "[FB13]" (C3). Two cross-references send the reader to §4.4 for material that has moved to the SI (B10).
