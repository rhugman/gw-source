# Round 2 review: worked examples and Neversink, structure and the practitioner reader

Reviewed: `sections/04_examples.md` (examples A, B, C and Table 1) and `sections/05_neversink.md`, with Fig. 2 (`figures/fig_gallery.png`, `display/C.md`), Fig. 3 (`figures/fig_examples_ab.png`, `display/AB.md`) and Fig. 4 (`figures/fig_neversink_single.png`, `display/N.md`). Context: the approved `sections/02_methods.md`, the round 1 `sections/01_introduction.md`, `03_software.md` and `06_tradeoffs.md`, and `outline.md` §1, §2, §3.4 and §3.5. Lens: a groundwater modeller who knows MODFLOW, PEST and particle tracking, but not this code, and who has just read the Methods. Word counts are prose words with HTML comments removed (`perl -0pe 's/<!--.*?-->//gs' | wc -w`).

## Overall judgement

The three worked examples are the right three, and each one answers a question a practitioner would ask. Each also compares its result with another approach and says what that comparison can and cannot show. Example A's "for the practitioner, this means" paragraph, example C's closing advice and the honest "not an independent test" and "consistency test" sentences are what the outside readers asked for. Section 5 shows scale convincingly. Its explanation of why the areas differ is polite to the published study, and the "below that range" sentence is honest.

The section does not yet deliver the "fewer examples, point to the notebooks" request, though. At 3,392 words, Section 4 is 65 % over the outline's 2,050. Most of the overrun sits in two places. Table 1 carries 733 words, because its Agreement column repeats the numbers that the worked examples already give in the text. Example B carries 955 words, because it runs two different snapshot models and adds a sensitivity study and a second backward-tracking result. A reader who has just finished Methods meets well over a hundred numbers in the prose of the three examples alone, before the table. Many of them do not change what the reader would do.

Three things matter more than length. First, example B never says what its result means for practice. Second, example C opens by saying that a sink's split by source can be used "with more confidence", but Section 5 then shows the split differing by 8 percentage points between methods on the regional model. Third, Section 5 promises to help a practitioner read a full-mixing area next to a particle area, but it ends without saying how.

With the cuts below, Section 4 comes to about 2,400 words and Section 5 to about 700. That saves about 1,150 words and leaves every check and every caveat in place.

## Word counts and proposed targets

| Part | Outline target | Now | Proposed | Where the words go |
|---|---|---|---|---|
| §4 opening (2 paragraphs) | 120 | 198 | 170 | Add one sentence on "any sink" (finding 8). Add K and thickness of the example model (finding 23) |
| Example A | 500 | 585 | 470 | Cut the particle total and the second citation sentence (finding 12). Move the forward trace to C (finding 7) |
| Example B | 650 | 955 | 680 | One snapshot model, not two (finding 4). Volume-option and sub-step detail to the SI (answer 2 below). Merge the two backward-tracking parts (finding 11). Add a practice reading (finding 1) |
| Example C | 450 | 628 | 500 | Scope the opening claim (finding 2). Take in the forward-trace sentence from A |
| Table 1 paragraph | – | 183 | 120 | Ensemble terms defined once (finding 14) |
| Table 1 caption | – | 102 | 90 | |
| Table 1 cells | 450 with paragraph | 733 | 380 | Agreement cells cut to the headline for rows covered in the text (finding 3) |
| **Section 4** | **2,050** | **3,392** | **about 2,410** | |
| §5 paragraph 1 (purpose, model, benchmark) | – | 174 | 150 | Split in two. Ensemble terms by reference to §4 (finding 14) |
| §5 paragraph 2 (cost) | – | 167 | 175 | Add hardware, which leaves §3 (finding 13) |
| §5 paragraphs 3–5 (why the areas differ) | 250 | 372 | 330 | Define "conserve water" and name the 0.62 run (finding 9) |
| §5 paragraph 6 (split by source) | – | 126 | 130 | Reorder, end with the practice reading (findings 2, 5) |
| §5 closing sentences | – | 0 | 40 | How to read the two areas side by side (finding 5) |
| **Section 5** | **550** | **847** | **about 700** | |

The outline target of 550 for Section 5 predates decision 5, which added the PRT cost comparison. A target of about 700 is, in my judgement, the honest size for what Section 5 now has to carry. The whole main text then drops from about 8,700 to about 7,550 words. The rest of the gap to the outline's 5,930 is Methods (2,984 against 1,630), which is approved.

**Where words buy comprehension, and should stay:** the description of weight-losing particles and why they are the fair comparison (A, paragraph 2), "That total says little about the area" as an idea (but see finding 12), the reason for the 64 years of recharge, "Both codes solve the same equations, so this is a consistency test", the "not an independent test" reasoning in C, the cell-by-cell explanation in C ("A particle from a cell with small F follows one slow path…"), the definition of the overlap score, "These times do not compare like with like" in Section 5, and the 42 % mean F that explains why many published cells fall below F = 0.5.

**Where words do not buy comprehension:** the 18,208 particles and 799.9 m³/d (A), the second snapshot model and its 52.5 % (B), the 0.5166 against 0.5167 and the three-number sub-step series (B), the 841 / 6,825 / 6,829 cells (B), the repeat of each example's numbers in Table 1, the second definition of realisations and PEST++ IES in Section 5, and the repeat of the Neversink cost in Section 3.

## Findings

### Must-fix

**1. Example B has no practice reading.**
Location: §4, example B, end of paragraph 2 ("…A layered model may therefore give other shares.") and the end of the example.
Problem: Examples A and C each close with what the result means for the practitioner. Example B opens with a manager's question and gives the answer (81 % of the first 10 years' water was already in the aquifer), but it never says what the manager should take from it. The key contrast is buried in the middle of a paragraph: snapshots average to about 60 % recharge, while transient tracking gives 32.9 % recharge in year 30. This is the reason a practitioner would use transient tracking, and the text does not draw it out.
Fix: Add two or three sentences after the GWT and Bedekar checks, in the form of A's "For the practitioner, this means…". For example: on this model, snapshots would lead a manager to expect the well's water to follow a change in recharge within a few years, while transient tracking shows that most of the water pumped in the next decade is already in the aquifer. Where the quality of new recharge differs from that of the stored water, the well's water will change over decades, not seasons. Keep the one-layer caveat next to it as a named stance. Move "Transient tracking has so far been tested on synthetic models only" to Section 6, where it already appears (finding 17).

**2. Example C's opening claim goes further than the evidence in Section 5.**
Location: §4, example C, paragraph 1 ("These answers depend much less on mixing than the edge of an area does, so a practitioner can use them with more confidence."). Also §5, last paragraph, and §6, paragraph 3.
Problem: Example C's evidence supports this for the well's total water and the mean travel time of all its water. For the split by source it rests on the small example model and the dispersion test problems. On Neversink the split is 57 % / 43 % under full mixing and 49 % / 51 % along weight-losing particle paths, although both deliver the wells' total within 2 %. By source, the river travel time also differs by −20.1 % in example C itself. A reader who finishes Section 5 will find the claim of example C contradicted. Section 6 repeats it without the qualification.
Fix: Scope the claim in C to what the examples show. The total and the overall mean travel time depend little on mixing. The split by source agreed closely on the test problems and the example model. Point forward: "Section 5 shows that on a regional model the split can differ between methods by several percentage points." End Section 5's last paragraph with the practice reading (report the method and the stream choice with any split by source). In Section 6, rewrite the sentence "A well's water by source and the mean travel time of all its water depend much less on mixing…" to match.

**3. Table 1 repeats the worked examples instead of pointing past them.**
Location: §4, Table 1, rows 01, 03, 05, 06, 07, 08 and 10, Agreement column.
Problem: The table is 733 words, more than any worked example. Seven of its ten rows are covered in the text, and their Agreement cells repeat the text's numbers (799.9 of 800 m³/d, 2.1 % smaller, 45.7 against 45.9 years, 0.96 and 5.72, 9.8 × 10⁻¹⁴, 1.3 percentage points and so on). The repeats cost words. They also hide the three rows that have no worked example (02, 04, 09), which are the rows a reader most needs the table for. This is the main reason Section 4 still feels like ten examples rather than three plus a guide.
Fix: For rows with a worked example, give only the headline agreement and the example letter ("Particle area within 2 % (example A)", "GWT to round-off. Published curves within 1.3 percentage points (example B)"). Keep the full cells for rows 02, 04 and 09. Target about 380 words for the table cells. See also finding 10.

**4. Example B runs two snapshot models with different numbers.**
Location: §4, example B, paragraph 1 (3-year run, three steps per season, 52.5 % storage in the dry season) and paragraph 2 (30-year run, one step per season, about 60 % recharge and 15 % storage on average).
Problem: The reader meets two snapshot runs of the seasonal model with different time steps and different headline numbers within two paragraphs. Nothing says why there are two, and the reader cannot tell whether 52.5 % and 15 % storage describe the same thing. The first run belongs to notebook 05 and Table 1 row 05. Only the second run is compared with transient tracking.
Fix: Keep one sentence on what snapshots show through the seasons, with the area change and a pointer to Fig. 2e and Table 1 row 05. Drop the 52.5 % and the nested-zone sentence from the text, because row 05 carries them. Then make the 30-year snapshot average the single contrast with transient tracking. This saves about 80 words and removes the confusion.

**5. Section 5 does not close with how to read a full-mixing area next to a particle area.**
Location: §5, paragraph 1 ("so that a practitioner can read one next to the other") and the end of the section.
Problem: The opening promises a reading guide. The section then gives three reasons for the difference (particle settings, mixing, weak sinks) and ends on the split by source. It never tells the practitioner what to do with the difference: which area to treat as the reference, which comparison is fair, and what to report. Section 6 (round 1) does not supply it either, because it repeats results.
Fix: End Section 5 with two or three sentences that answer the promise. For example: a particle area depends on its settings as much as on the flow model. The fair comparison for a full-mixing area is a particle run that loses weight at sinks as full mixing does. Against that run the F > 0.1 area held 87 % of the particle area on this model, so a low threshold did not give a complete outer limit. The threshold, the accounting and the stream choice should be reported with any area. Keep the advice itself for Section 6 and keep Section 5 to what the comparison showed.

**6. Section 3 still carries the MODFLOW 6 run time and repeats the Neversink cost.**
Location: `sections/03_software.md`, paragraph 2 ("The MODFLOW 6 run of that model takes 44 s"; "2–3 s"; "2.5 GB").
Problem: Decision 13 removed the 44 s from Section 3. Section 3 also repeats the trace time and memory that Section 5 now reports in context, next to PRT. The reader therefore meets the same numbers twice, the first time without the comparison that gives them meaning. Section 3 is outside this review, but the duplication affects how Section 5 reads.
Fix: In Section 3, drop the 44 s and the 2–3 s and 2.5 GB. Keep one sentence: "Section 5 reports the cost on a regional model of 1.68 million cells." Move the hardware sentence (Apple M4 Max, 64 GB) into Section 5, paragraph 2, where the times are given.

### Should-fix

**7. Example A's forward trace sentence lands flat.**
Location: §4, example A, last two sentences ("A forward trace answers the reverse question… 39 % reaches the well (Fig. 2c).").
Problem: The sentence follows the practice reading of the contributing area and has no link to it. It is the only place in Section 4 that shows a source rather than a sink, which matters for the framing (outline §1.2). Example C already uses a forward trace for the split by source.
Fix: Move the sentence to example C, paragraph 1, just before "A forward trace from each source gives the same split". Give it its purpose first ("A forward trace asks where a source's water goes, for example the recharge under a field where fertiliser is spread."). Fig. 2c then sits with the other source-side result.

**8. Section 4 never says that every output applies to any sink or source.**
Location: §4, opening paragraph.
Problem: All three worked examples use one supply well. The outline's framing (§1.2) says the tool is not only for wells, and the abstract and impact statement mention streams. A reader of Section 4 alone will conclude that it is a well-protection tool.
Fix: Add one sentence to the opening: the example sink is a well, but each output applies in the same way to a stream reach, a drain, a lake or a group of them, and Table 1 row 07 traces through streams and drains. Keep it to one sentence.

**9. "Particle runs that conserve water" is undefined, and the 0.62 run is not named.**
Location: §5, paragraph 3 ("Among particle runs that conserve water, the settings alone move the overlap from 0.62 to 0.998").
Problem: The reader does not know what it means for a particle run to conserve water, or why the published run (which stops particles at weak sinks) counts as one. The reader also does not know which settings give 0.62. Without this, "Full mixing lies below that range" cannot be judged.
Fix: Add one sentence that defines it: a particle run conserves water when the water its particles deliver to the sinks equals what the sinks take. Name the 0.62 run in plain words (the run with the particles started at the water table rather than moved down, if that is what "dropped" means in `mp7_reproduction.csv`; check against the evidence). Decision A.3 of `decisions_r4.md` asked for the runs that do not conserve water to be named once. That sentence can live in the SI.

**10. Table 1's "Checked against" column mixes independent checks with checks of the code against itself.**
Location: §4, Table 1, columns "Checked against" and "Agreement".
Problem: The column lists PRT, GWT and Bedekar et al. (2024) next to the closure check, the forward–backward check, "statistics recomputed from the stored steps" and "serial against parallel runs". The paper's framing rests on checks "against other common approaches". A practitioner scanning the table cannot see which rows have one. Agreement values of 4.2 × 10⁻¹³ and 1.5 × 10⁻¹⁰ also mean little to a reader without a sentence saying that these are round-off.
Fix: Rename the column "Compared with" and list only the other approach or published study (PRT, GWT, Bedekar et al. 2024, Foley and Black 2013, the same model unsplit, a synthetic true model). Say once in the caption that every notebook also runs the water-budget checks of Section 2. Say once in the caption that differences of 10⁻¹⁰ or smaller are round-off. Write such cells as "round-off".

**11. Example B's order splits backward tracking in time across the checks.**
Location: §4, example B, paragraphs 3–6.
Problem: The order is forward results, backward results, GWT check, Bedekar check, then backward results again (the time-limited area of the Bedekar model). The second backward-tracking paragraph also changes model without warning. "The published study does not report it" reads, in my judgement, slightly as a criticism.
Fix: Order the example as snapshots, forward results, backward results, then the two checks. Cut the time-limited area of the Bedekar model to one sentence inside the Bedekar paragraph, or move it to Table 1 row 10 and the SI. Keep the hedge on one run per zone, because it states the practical gain. Write the gain positively ("Backward tracking in time adds a map of the time-limited contributing area. We expect that a forward unit-concentration model would need one run per zone…").

**12. Example A spends a paragraph on numbers it then calls uninformative.**
Location: §4, example A, paragraph 2 (the citations of Visser et al. 2009 and Winston et al. 2018) and paragraph 3 ("The 18,208 particles from 1,133 cells deliver 799.9 of the 800 m³/d pumped.").
Problem: The particle total is given and then dismissed in the next sentence. The idea behind it (particles that conserve water must deliver what the well pumps) is worth one sentence, because Section 5 and the travel-time argument in C use it, but the counts are not. The two citation sentences give a precedent, which is good, but they read as two separate claims.
Fix: Replace the two sentences with one ("The particles deliver what the well pumps, as any particle run that conserves water must, so the total says little about the area."). Merge the citation sentences into one sentence that names both precedents. Leave the counts to Table 1 row 01 or the SI. This also gives finding 9 a definition to point back to.

**13. Section 5 gives times without the hardware.**
Location: §5, paragraph 2.
Problem: The trace and PRT times are given without the machine. The hardware is in Section 3. If Section 3 drops the cost (finding 6), the hardware must move.
Fix: Add "on an Apple M4 Max with 64 GB of memory" to the first cost sentence. Consider one sentence on what 9 s per realisation means for the 358 realisations, if a stored total exists. Do not compute one that is not in the evidence.

**14. Realisations, ensembles and PEST++ IES are defined twice.**
Location: §4, Table 1 paragraph ("Many sets of parameters can fit…"), and §5, paragraph 1 ("Its 358 realisations come from history matching with PEST++ IES (White 2018; White et al. 2020).").
Problem: Both places define the terms and cite White (2018) and White et al. (2020). The Introduction (round 1) also introduces ensembles. Rule: say a point once.
Fix: Keep the definitions in §4, where they first appear in the order of reading. In Section 5, write "Its 358 realisations come from history matching with PEST++ IES (Section 4)". When the Introduction is revised, drop its ensemble sentence, as the outline already plans (§3.1 point 5).

**15. Fig. 4 reverses the colour order of F used in Figs 2 and 3.**
Location: Fig. 4a against Fig. 2a, 2f, 2h and Fig. 3a.
Problem: In Figs 2 and 3, yellow means F or particle share near 1 and dark purple means near 0. In Fig. 4a, yellow means F of 0.01–0.1 and dark purple means F above 0.75. A reader who has learned the colours from Fig. 2 will read Fig. 4a backwards. Fig. 3a also uses the same viridis scale for the particle share as Fig. 2a uses for F, which invites a reader to compare the two maps directly, as intended.
Fix: Draw Fig. 4a with the colour order of Fig. 2a. If reversed viridis was chosen so that low F stands out on the grey background, use the classes of Fig. 4a with the colour order of Fig. 2a, or say in the caption that the order is reversed and why.

**16. Fig. 4 shows window counts, and the text cites it for whole-model counts.**
Location: §5, paragraph 4 ("The F > 0.1 area holds 73 % of them (711 of 980; Fig. 4b)") against the Fig. 4 caption (538 in both, 150 published only, in a window of 688 published cells).
Problem: A reader who checks the figure against the text finds 538 of 688 (78 %), not 711 of 980. The most informative comparison of the section, F > 0.1 against the weight-losing particle area (87 %), has no figure.
Fix: In the text, cite Fig. 4b as showing the window around four of the wells ("Fig. 4b shows this for four of the wells"). Consider the outline's proposal of a panel (c), the F > 0.1 area against the weight-losing particle area, from the SI figure. If Fig. 4 must stay single-column, that panel could replace panel (a), because the text needs (b) and (c) more than the F map.

**17. Section 6 (round 1) repeats results and must change to match Sections 4 and 5.**
Location: `sections/06_tradeoffs.md`, all three paragraphs.
Problem: Section 6 opens with a result ("Full-mixing areas are wider and more diffuse than particle areas (Section 5)"), not a framing of the outcomes. It keeps the dispersion-test threshold numbers that the outline (§3.6 point 3) moves to the SI. It repeats the Neversink F > 0.1 result. It repeats "tested on synthetic models only" from example B. Its integral-answer sentence needs the scoping of finding 2. It does not yet carry the list of what to report with an area (outline §3.6 point 4).
Fix: When Section 6 is revised, open with the outcome framing. Gather here the advice that Sections 4 and 5 now end on: what to report with an area (threshold, accounting, stream choice), when to use particles, GWT or full mixing, and the limits. Point to the evidence by section, without the numbers. Drop "tested on synthetic models only" from example B and keep it in Section 6.

**18. The Introduction (round 1) still describes ten examples and the old speed argument.**
Location: `sections/01_introduction.md`, last two paragraphs.
Problem: "Section 4 works through ten examples" no longer matches. The ensemble sentence ("The code is fast enough to trace every version") rests on a worked example that has gone. The Introduction does not introduce weight-losing particles, which is fine, but it should say that the examples compare with PRT, GWT and a published study, because that is the framing.
Fix: As the outline plans (§3.1 points 5 and 6): "Section 4 works through three examples in depth, each compared with particle tracking, transport or a published study, and Table 1 summarises ten notebooks." Replace the ensemble sentence with one sentence on speed that points to Section 5. The abstract (`00_front.md`) has the same three problems (ten examples, the MODFLOW 6 comparison, history matching) and the key word "ensemble".

**19. Section 7 does not tell the reader where the numbered notebooks are.**
Location: `sections/07_availability.md`; §4 opening ("The notebooks are numbered as in Table 1").
Problem: Decision 10 names the notebooks by number in Table 1 and relies on Section 7 to point to the repository. Section 7 says that each example ships as a notebook but not where, or that the numbers match Table 1. A reader cannot get from row 05 to the notebook.
Fix: Add one sentence to Section 7: the notebooks, numbered as in Table 1, are in a named folder of the release. Avoid the word "tutorial" (manuscript rules), so the folder may need naming in plain words, for example "the examples folder of the release".

### Minor

**20. Fig. 2g and 2h are cited only through Table 1.**
Location: Fig. 2 caption, panels (g) and (h); §4 text.
Problem: Every other panel is cited in the text of an example. Panels (g) and (h) are reached only through the table's last column. The caption of (g) uses "posterior realisations" and "true F", which the reader meets only in the paragraph after the table. Panel (e) uses "zone" for threshold areas, against the house rule that "zone" is kept for protection zones.
Fix: Cite Fig. 2g in the Table 1 paragraph sentence on row 09 and Fig. 2h in a short clause on row 04 (for example in finding 8's sentence on general grids). Add a pointer "(Table 1, row 09)" to the caption of (g). Consider "inner area", "seasonal area" and "ring" in (e), or define them in the caption.

**21. Fig. 3b says "stored water", while example B uses "initial water".**
Location: Fig. 3b legend and caption; §4, example B.
Problem: In the Bedekar model the two are the same, because pumping starts at the start of the run. In the seasonal model they are not, and example B says so ("Initial water is therefore not water from before pumping began"). A careful reader will wonder whether the two curves mean different things.
Fix: Add one clause to the caption or the Bedekar paragraph: here pumping starts with the run, so stored water is the initial water of Section 2.

**22. Fig. 2d's time-of-travel contours are not cited where the zones are discussed.**
Location: §4, example C, paragraph 4 ("The 25-year zone covers 0.455 km²…").
Fix: Add "(Fig. 2d)" to that sentence, because the 5-year and 25-year contours are drawn there.

**23. The example model lacks the two properties a reader needs for the travel times.**
Location: §4, opening paragraph 2.
Problem: The description gives grid, recharge, boundaries and pumping. It does not give the hydraulic conductivity (5 m/d) or the aquifer thickness (top 20 m, bottom −30 m in the evidence comment). A practitioner reading "45.9 years" and "64 years of recharge" in a column will want them.
Fix: Add one sentence with the hydraulic conductivity and the elevations of the top and bottom, from `tutorials/herebedragons.py` AquiferSpec.

**24. Fig. 4 legend uses "SFR reaches" and "published (a)".**
Location: Fig. 4 legend.
Problem: The text says "stream reaches" and never "SFR". "published (a)" reads as a code label.
Fix: Use "stream reaches" and "published cells (outline in a)".

**25. "Ten examples", "notebooks" and "worked examples" are used loosely.**
Location: §4, opening ("Table 1 … summarises all ten examples that ship with the code"); Table 1 paragraph ("All ten examples"); Table 1 caption ("The ten worked examples").
Problem: The section calls A, B and C "worked examples" and also calls all ten rows "worked examples". A reader may think there are ten worked examples, which is the old structure.
Fix: Use "worked examples" for A, B and C only and "notebooks" for the ten rows throughout, including the run-in head ("All ten notebooks") and the caption.

**26. Example C's stream-variant sentence refers to "the well above".**
Location: §4, example C, paragraph 2 ("Its well therefore takes a different mix of water from the well above, so the shares below cannot be compared with the 14 % of river leakage above.").
Problem: "Above" refers to text, twice, and the sentence carries two ideas.
Fix: "Its well takes a different mix of water from the well of example A. For this reason, its shares cannot be compared with the 14 % of river leakage given above." Keep both sentences, because the warning is needed.

**27. Section 5, paragraph 1 carries too much.**
Location: §5, paragraph 1 (174 words).
Problem: The paragraph holds the purpose, the model, the ensemble, the calibrated model, the published MODPATH study, the start cells and the trace settings. A reader has to hold all of it before the first result.
Fix: Split it after the definition of the calibrated model. The second paragraph then introduces the published benchmark and the settings of this trace. This adds no words.

## Answers to the six questions

1. **Practice and checks.** A and C answer their questions, show a check against another approach and state its limits. B answers its question and has the strongest checks (GWT and a published study), but it has no practice reading (finding 1). C's opening claim needs scoping against Section 5 (finding 2).
2. **Fewer examples.** Three worked examples plus Table 1 is the right structure. Section 4 still carries too much because Table 1 repeats the examples (finding 3), and B carries a second snapshot model (finding 4), a sensitivity study and a second backward-tracking result (finding 11). These should move to Table 1 rows 05 and 10 and the SI. The volume-option and sub-step numbers in B can be cut to one sentence each, with the detail in the SI, because Methods only promises that "Example B shows their effect".
3. **Table 1.** It works as a guide to the notebooks, because its questions are phrased as a practitioner would ask them and it gives the Fig. 2 panel. It works less well as the evidence table, because "Checked against" mixes independent comparisons with checks of the code against itself, and round-off values are not explained (finding 10). Section 7 must say where the notebooks are (finding 19).
4. **Section 5.** Scale is convincing. The cost comparison with PRT is fair and says what it does not compare. The explanation of the differences is polite ("one reasonable choice of particle settings"). It needs a definition of "particle runs that conserve water" (finding 9), consistent use of Fig. 4 (findings 15 and 16) and a closing reading guide (finding 5).
5. **Flow and duplication.** Methods leads cleanly into Section 4. Every forward pointer in Methods (examples A, B and C, Table 1 rows 02 and 03) is honoured. The duplications are the Neversink cost in Sections 3 and 5 (finding 6), the ensemble terms in Sections 1, 4 and 5 (finding 14), the integral-answer claim in Sections 4 and 6 (finding 2) and "synthetic models only" in Sections 4 and 6 (finding 17). Each figure supports its text. Fig. 2g and 2h are cited only through the table (finding 20). The rest of the panels are cited.
6. **Length.** See the table of targets above: about 2,410 words for Section 4 and about 700 for Section 5.
