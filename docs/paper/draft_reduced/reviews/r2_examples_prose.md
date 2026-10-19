# Review of round 2 Sections 4 and 5: prose and voice

Scope: `docs/paper/draft_reduced/sections/04_examples.md` (with Table 1 and its caption) and `sections/05_neversink.md`, both as of commit d6a958f, HTML comments ignored. Checked against the `voice-hugman` skill, its `references/manuscript_rules.md` and `references/feedback_pairs.md`, `docs/paper/outline.md` Section 1.3, `docs/paper/terms.md`, and the approved Methods (`sections/02_methods.md`) as the model for tone. Lines are file lines of the section with comments stripped. Each paragraph is one line, so "L21" means the paragraph that starts on line 21.

Verdict. Both sections keep the hard bans well. There are no semicolons in prose, no colon joins, no filler transitions, no puffery, no "credit" and no "X gives no Y". The examples open with the practitioner's question and its reason, as asked. The main problems are different. Five results paragraphs put the numbers first and the meaning last, or leave the meaning out. Seven paragraphs are number-dumps. Three terms are new and undefined in the paper ("nested zones", "face-to-face routing", "particle runs that conserve water"). About 300 words of Section 4 are restatements of checks, implementation detail or numbers that the reader's question does not need. Methods reads like a colleague explaining the work. Section 4 still reads in places like a notebook printout.

## Counts

| check | §4 | §5 |
|---|---|---|
| semicolons in prose (outside citation brackets) | 0 | 0 |
| colon joins of two claims | 0 | 0 |
| ", and" joins of two claims | 0 strict, 1 borderline | 0 |
| ", so" / ", while" tails or stacks that add a second claim | 1 | 2 |
| ", which" tails that add a claim | 0 | 0 |
| appositive packing | 0 strict, 4 borderline (trailing numbers) | 0 |
| participle or absolute openers | 1 | 0 |
| "We do X by Y" | 0 | 0 |
| filler transitions, puffery, "credit", "X gives no Y", "So …" jumps | 0 | 0 |
| vague stand-in nouns | 3 | 0 |
| announcements | 1 | 0 |
| rhetorical questions in body text (run-in headings excluded) | 2 | 0 |
| "therefore" / "thus" | 5 (4 paragraphs, 2 as closers) | 1 |
| one word per concept broken | 1 | 3 |
| staccato runs (three or more sentences of 12 words or fewer in a row) | 4 strict, 3 near | 2 strict, 1 near |
| number-dumps | 6 | 1 |
| paragraphs that land flat or lack a connecting sentence | 3 | 2 |
| terms undefined or used before definition | 6 (3 in Table 1) | 5 |
| Methods content restated | 2 | 1 |
| ambiguous referents | 5 | 1 |
| results paragraphs not in conclusion → evidence → caveat order | 3 | 1 |
| sentences the author would likely call unnecessary | 17 | 4 |
| Table 1 cells that are really paragraphs | 4 | – |
| safe savings (prose + table) | about 290 + 70 = 360 words | about 35 words |

## 1. Banned constructions and words

### 1.1 Two-claim joins and tails

1. §4 L33, ", so" and "therefore" stacked: "Its well therefore takes a different mix of water from the well above, so the shares below cannot be compared with the 14 % of river leakage above." Two claims, plus positional referents ("above", "below").
   Rewrite: "The well of this version therefore takes a different mix of water. Its shares cannot be compared with those of the first version."
2. §5 L5, "because" plus ", while" in one 32-word sentence: "These times do not compare like with like, because one PRT run follows one particle convention for all wells, while one trace gives F, the volumes and the checks for every group."
   Rewrite: "These times do not compare like with like. One PRT run follows one set of particle settings for all wells together. One trace gives F, the volumes and the checks for every well group."
3. §5 L15, interrupter plus ", while", 40 words: "We infer, without tracing it cell by cell, that leaked stream water near the wells stays on particle paths that end at a well, while full mixing gives it the average fate of the water leaving the cells it passes."
   Rewrite: "We infer, without tracing it cell by cell, that stream water leaking near the wells stays on particle paths that end at a well. Full mixing instead gives that water the average fate of all the water leaving the cells it passes."
4. Borderline ", and", §4 L3: "This section shows how a practitioner can use the code to answer three common questions, and how far each answer can be trusted." One idea, but the comma makes it read as two. Rewrite: "This section shows how a practitioner can use the code to answer three common questions and how far each answer can be trusted."

The other ", so" sentences carry a consequence of one idea and are fine (§4 L9, L11, L17, L25 twice, L31, L39; §5 L3).

### 1.2 Participle opener

1. §4 L21: "Averaged over time, snapshots of the 30-year run give the well's water as about 60 % recharge and 15 % storage release."
   Rewrite: "The time-averaged snapshots of the same run give the well's water as about 60 % recharge and 15 % storage release."

### 1.3 Vague stand-in nouns, announcements, rhetorical questions

1. §4 L13 "That total says little about the area" ("totals" is on the ban list). See cut S4, which removes the sentence. If it stays: "That match says little about the area."
2. §4 L27 "The read-offs themselves are good to about one percentage point." Rewrite: "The values read off the published figure are themselves good to about one percentage point."
3. §4 L19 "Statistics over 36 snapshots can still combine the seasonal maps into nested zones." Which statistics? See 3.1 for the rewrite, which names them.
4. Announcement, §4 L39: "Row 09 needs a few words of explanation." Rewrite: "Row 09 applies the trace to an ensemble of models."
5. Rhetorical questions, §4 L31: "How much of a well's water is river water? How old is the water from each source?" The rules allow at most one in the paper. Rewrite as a statement: "A water-quality study, for example, may need to know how much of a well's water is river water and how old the water from each source is."

### 1.4 Borderline appositives (trailing numbers)

"Weight-losing particles give 45.7 years for all the water, 0.5 % less." (L35). "… 0.465 km² for particles, 2.2 % more." and "… 0.098 against 0.122 km², 25.6 % more." (L37). "Four MODFLOW 6 GWT runs, one per source, give …" (L27). These read naturally and can stay. Use parentheses if the author wants them quieter: "0.465 km² for particles (+2.2 %)".

### 1.5 "therefore" and "thus"

§4 has five (L21 twice, L33 "therefore" and "thus", L35). Two close a paragraph: "A layered model may therefore give other shares." (L21) and "… thus depends on whether the stream reaches are traced." (L33). The rules allow a "therefore" closer in one paragraph per section. The L33 sentence is cut under S9. For L21: "With one layer, the model cannot hold young water above old water, so a layered model may give other shares."

### 1.6 One word per concept

1. §5 uses "particle convention" (L5) and "particle settings" (L7) for the same thing. Use "particle settings" in both, because L7 defines it.
2. §5 L7 "overlap score". `terms.md` uses "overlap". Write "We measure the difference with the overlap."
3. §5 L15 "With the reaches traced as the stream network". Methods says "traced as a cell of its own", and §4 L33 says "traced as cells of their own". Use the same wording: "With the stream reaches traced as cells of their own, …"
4. §4 L13 "particle cells" and "particle area" are used without being named. See 3.1.

## 2. Flow: staccato runs, number-dumps and flat paragraphs

### 2.1 Staccato runs

1. §4 L3: "Example A maps where a well's water comes from. Example B follows that water through a transient model. Example C splits the well's water by source and by travel time." (9, 9, 12 words, three identical openers.)
   Rewrite: "The three examples ask where a well's water comes from (example A), how much of it is already in the aquifer (example B), and how much comes from each source and how old it is (example C)."
2. §4 L9: "Fig. 2a maps F for the supply well. Cells with F > 0.5 cover 1.143 km². Cells with F > 0.1 cover 1.575 km². The expected area of Section 2 gives a size without a threshold. Here it lies between the two, at 1.173 km²." (7, 8, 8, 12, 9.) Also a number-dump. Rewrite in 2.2, item 1.
3. §4 L13: "The F > 0.1 area is 35 % larger. It holds every cell of the particle area. The two methods differ most at the edge." (9, 8, 8.) Rewrite in 4.1.
4. §4 L39: "We refer to each set as a realisation. A set of realisations is an ensemble. History matching … The history-matched ensemble is the posterior." (8, 7, 19, 6.) Rewrite: "Many sets of parameters can fit the measured heads about equally well. We refer to each set as a realisation and to a group of realisations as an ensemble. History matching with PEST++ IES (White 2018; White et al. 2020) adjusts the realisations until they fit the measurements. We refer to the history-matched ensemble as the posterior."
5. Near-runs in §4: the model description (L5, 8 to 15 words, five sentences), the PRT description (L11, eight sentences of 7 to 21 words), and the end of L25 ("Transport sub-steps matter more. … Long steps make new water arrive too early. Here, four sub-steps remove most of this effect." 4, 8, 8 words). L5 can stay as a plain description, though one merge helps: "It is a single unconfined layer of 40 × 40 cells of 50 m, with recharge of 5 × 10⁻⁴ m/d on every cell." L11 and L25 are rewritten in 4.1 and 5.
6. §5 L7: "Recharge and stream flows enter a cell through its top face. A particle stops in the first weak-sink cell it enters. A particle that starts in a dry cell is moved down to the first active cell." (11, 10, 16.) The three settings are one idea, so one list sentence reads better: "The published runs put recharge and stream flows on the top face of each cell, stopped a particle in the first weak-sink cell it entered and moved a particle that started in a dry cell down to the first active cell below."
7. §5 L3, near-run: "Eight priority wells pump 3,671 m³/d." (6 words), followed by short definition sentences. Acceptable, apart from the undefined "priority" (3.2).

### 2.2 Number-dumps (three or more numbers before any sentence that says what they mean)

1. §4 L9 (1.143, 1.575, 1.173 km²). The reader is not told why there are three areas.
   Rewrite: "Fig. 2a maps F for the supply well. The size of the contributing area depends on the threshold that the user chooses. Cells with F > 0.5 cover 1.143 km², against 1.575 km² for cells with F > 0.1. The expected area of Section 2 needs no threshold and lies between the two, at 1.173 km²."
2. §4 L19 (1.8, 1.0, 0.1, 1.1, 640, 1,120, 3-year, three steps, 0.59, 1.35, 52.5 %, 36). The meaning ("a snapshot cannot say where that stored water came from") comes last. See the rewrite in 4.2.
3. §4 L21 (30 years, 121 steps, 0.3, four sub-steps, 60 %, 15 %, 51.6 %, 32.9 %, 15.5 %, 81 %, 98 %, 68 %, 64 years). Twelve numbers before the conclusion. Rewrite in 4.2.
4. §4 L25 (9.8 × 10⁻¹⁴, 0.3, 0.2, 1.9 × 10⁻⁴, 3.7 × 10⁻³, 0.5166, 0.5167, 0.0078, 0.0049, 0.0042). Cuts S5 and S6.
5. §4 L27 (48.2, 29.2, 22.5, 48, 29, 23, 15 times, 1.3, year 10, 7.6 days, 0.6, 15 years, 1 point, 1.5 × 10⁻¹⁰). Rewrite in 5, cut S16.
6. §4 L35 (2.1, 41.6, 108.4, 45.9, 45.7, 0.5 %, then −2.1, +2.1, −20.1 %). The −20.1 % for river leakage is a large difference that the text never explains. A reader will ask why. Rewrite in 4.3.
7. §5 L5 (2–3 s, 2.5 GB, 0.19 GB, 1 × 10⁻¹², 30 s, 5 min, 122,112, 13 min, 488,448, 1.5 GB, 6 GB, 10⁻⁶, 9 s, 3 × 10⁻¹²). Fourteen numbers and no sentence that says what the cost means for the practitioner. Rewrite in 4.4.

L13, L37 and §5 L9 also hold many numbers, but each is read for the reader in the same paragraph. They pass.

### 2.3 Paragraphs that land flat or lack a connecting sentence

1. §4 L17, last two sentences: "A forward trace answers the reverse question of where the water of a source goes. Of the recharge on a field of 300 m × 300 m, 39 % reaches the well (Fig. 2c)." These follow the practitioner reading of the particle comparison and have nothing to do with it. Cut them (S13) and leave the forward trace to Table 1, row 03, and to Methods, which already cites Fig. 2c. If the author wants them kept, give them their own short paragraph with a connecting sentence: "Example A asks where a sink's water comes from. A forward trace answers the reverse question for a source. …"
2. §4 L29 ends with "Transient tracking has so far been tested on synthetic models only (Section 6)." This closer follows a paragraph about the time-limited area and reads as tacked on. Section 6 says it again. See S14.
3. §4 L31 ends on the SI test problems and an undefined label. The paragraph does not lead into L33. With S7 and the rewrite in 3.1, it ends on the reason the split can be trusted, and L33's "The split by source also depends on where the trace stops" then follows.
4. §5 L5 opens with a number. It needs a topic sentence (rewrite in 4.4).
5. §5 L15 ends with "With the reaches traced as the stream network, all of the wells' water traces back to recharge." This point belongs next to the 57 % and 43 % split, which it qualifies. Moved there, the paragraph ends on the inference, which is its point. See 4.4.

## 3. Terms and referents

### 3.1 §4

1. "nested zones" (L19, Table 1 row 05). Not defined anywhere in the paper. Notebook 05 §7 defines them.
   Rewrite: "Statistics over the 36 snapshots can still combine the seasonal maps into nested zones (Fig. 2e; Table 1, row 05). The inner zone holds the cells with F > 0.5 in every step. The seasonal zone holds the cells with F > 0.5 in some steps only. An outer ring holds the cells where F exceeds 0.1 in at least one step but never exceeds 0.5."
2. "face-to-face routing" (L31). Not defined in the main text. Methods and Section 6 do not name it.
   Rewrite without the label: "In the test problems of {SI: numerical dispersion test problems}, the shares by source were the same to three digits whether water was mixed across whole cells, routed from face to face or followed with particles."
3. "particle cells", "particle area" (L13). Name them once: "We refer to the cells with a particle share above 0.5 as the particle area."
4. "particles that conserve water" (L13). The reader is not told which particles do not. §5 relies on this ("particle runs that conserve water"). Define it once here: "Particles conserve water when the weight they deliver to each sink equals the water that sink takes."
5. The Bedekar et al. (2024) model is not described (L27). "Lateral inflow" and "stream water" appear without the reader knowing the model has those sources. Add one sentence after the citation: "Their model is [one-line description: layers, a well, recharge, a stream and lateral inflow; check against `tutorials/10_unit_concentration` §1 and Bedekar et al. 2024]."
6. Table 1 cells with undefined terms. Row 04 "Loop-by-loop solve against a plain sparse solve" ("plain sparse solve"). Row 05 "Statistics recomputed from the stored steps". Row 09 "Exact quantiles against quantiles from histograms". See Section 6 of this review.

Methods content restated:
- L13 "Full mixing instead gives each cell an in-between value, because it splits the cell's water among all its outflows." This repeats Methods' "Full mixing and the cell budget" paragraph almost word for word. One reminder per section is allowed. Keep this one and point back: "… while full mixing gives the cell an in-between value (Section 2)."
- L9 "The expected area of Section 2 gives a size without a threshold." This repeats the Methods definition. It is folded into the rewrite in 2.2, item 1.

Ambiguous referents:
- L33 "Its well", "the well above", "the shares below" (1.1, item 1).
- L27 "The paper gives 48 %, 29 % and 23 %." "The paper" could be this paper. Write "Bedekar et al. (2024) give 48 %, 29 % and 23 %."
- L29 "Within 25 years, the area covers 6,825 cells of that layer." Which area? Write "the time-limited area".
- L13 "That total" (1.3).
- L11 "The traced sources add up to the 800 m³/d pumped, with a relative closure error of 0.0, as the closure check requires." "As the check requires" makes the check confirm itself. Cut the tail (S3).

### 3.2 §5

1. "priority wells" (L3). Never defined. Rewrite: "Eight wells that the published study chose for its contributing-area maps, which it refers to as priority wells, pump 3,671 m³/d." Check what "priority" means in Fienen et al. (2022) before writing a reason.
2. "base parameters" (L3). Write "the realisation with the base parameter values of the published model" or "the published calibrated model". Check the source's wording.
3. "two traces of each realisation" (L5). The reader is not told why two, or which two. Name them or write "the traces of each realisation". The cost figures (NS Summary: 358 realisations, two traces each, 76 min on six processes) do not say. [check]
4. "one particle convention" (L5) comes before the settings are introduced in L7 (1.6, item 1).
5. "The weight-losing PRT runs also needed the trace first, because they were released only from cells with F > 10⁻⁶." (L5). Weight-losing runs on Neversink are first introduced four sentences later (L9). Move the sentence to L9, after "Weight-losing particles (Section 4) give a closer comparison …".
6. "Full mixing lies below that range." (L9). A method does not lie below a range of overlaps. Write "The full-mixing areas overlap the published area less than any of these particle runs do."

Methods content restated: L9 "full mixing splits each cell's water among all its outflows, while a particle follows one path" is the third statement of this point (Methods, §4 L13). As an inference it can stay, but shorter: "We infer that the main reason is the one seen in example A. Full mixing splits each cell's water among all its outflows, while a particle follows one path."

## 4. Openers and results order

All three examples open with the practitioner question and why it matters. Example A: protection zones. Example B: water quality after a change in land use. Example C: integral answers depend less on mixing. Section 5 opens with its two purposes. The order inside the results paragraphs is the weak point.

### 4.1 Example A, particle comparison (L13 and L17): evidence before conclusion

The conclusion ("the F > 0.5 area is close in size to the particle area") arrives in the next paragraph, after the figure.
Rewrite of L13 and the first three sentences of L17 as one paragraph:

"Weight-losing particles show that on this model the F > 0.5 area is close in size to the area that particles deliver to the well. The particle share of a cell is the share of the weight released there that reaches the well (Fig. 3a). We refer to the cells with a particle share above 0.5 as the particle area. It covers 1.168 km². The F > 0.5 area is 2.1 % smaller and leaves out 14 of its cells. The F > 0.1 area is 35 % larger. It holds every cell of the particle area, so on this model it serves as a cautious outer limit. The two methods differ most at the edge of the area. In the 372 cells with F between 0.05 and 0.95, the particle share and F differ by 0.164 on average. In those cells most particles either reach the well or miss it, while full mixing gives the cell an in-between value (Section 2). Section 5 shows that a regional model need not behave in the same way."

The PRT paragraph (L11) reads better with the name next to the rule it names:
"For this check the code runs MODFLOW 6 PRT on the same flows. Particles start from every source term in cells with F > 0. Each particle carries a share of its term's flow as a weight. It loses part of that weight at every other sink it passes, in proportion to the flow that sink takes from the cell. We refer to these as weight-losing particles. They are the particle counterpart of gross accounting. Visser et al. (2009) split particles at weak sinks in a similar way to derive travel times. Winston et al. (2018) reduce particle weights at sinks in a solute-transport method."

### 4.2 Example B, snapshots and transient tracking (L19 and L21): evidence before conclusion

Rewrite of L19 from "A seasonal version":

"A seasonal version of the example model shows why. In this version, recharge is multiplied by 1.8, 1.0, 0.1 and 1.1 in the wet, wet-to-dry, dry and dry-to-wet seasons. The well pumps between 640 and 1,120 m³/d. Snapshots of a 3-year run, with three time steps per season, show the contributing area moving with the seasons. The F > 0.5 area grows from 0.59 km² in the wet season to 1.35 km² in the dry season. In the dry season, the snapshots attribute 52.5 % of the well's water to storage. A snapshot cannot say where that stored water came from. It may be old water or recharge of the last wet season." Then the nested-zones sentences of 3.1, item 1.

Rewrite of L21, conclusion first:

"Transient tracking follows the stored water. It shows that most of the water pumped in the first decades was already in the aquifer. For this run, the seasonal model runs for 30 years with one time step per season, or 121 time steps in all. The tracking uses a porosity of 0.3 and four transport sub-steps per flow step. The run starts from a steady state in which the well already pumps. Initial water is therefore not water from before pumping began. Of all the water pumped in the first 10 years, 81 % was initial water. This share is 98 % for the first year and 68 % over 30 years. Even in the last season of year 30, the well's water is 51.6 % initial water, 32.9 % recharge and 15.5 % river water. The time-averaged snapshots of the same run give a different picture, with about 60 % recharge and 15 % storage release ({SI: snapshots and transient tracking over 30 years}a). They count the stored water as a source of unknown origin. New recharge mixes into a large volume of older water, because a column of this aquifer holds about 64 years of recharge. With one layer, the model cannot hold young water above old water, so a layered model may give other shares."

### 4.3 Example C, travel time (L35): evidence, caveat, then more evidence

The by-source numbers come after the caveat, and the river difference is not explained.
Rewrite:

"Full mixing and weight-losing particles give nearly the same mean travel time for all of the well's water, but they agree less well for river water. With a porosity of 0.3, the backward trace gives mean travel times (Fig. 2d). The times are taken to the point where the water enters the well cell, because particle trackers stop particles there ({SI: method in full}). The mean travel time is 2.1 years for river leakage, 41.6 years for recharge and 108.4 years for inflow at the west edge. Over all the water, it is 45.9 years, against 45.7 years for the particles. By source, the particle times differ by −2.1 % for recharge, +2.1 % for the west edge and −20.1 % for river leakage. [One sentence on why river water differs most, from notebook 06, or a marked inference. If neither is available, move the by-source differences to Table 1, row 06.] The close agreement for all the water is not an independent test. Any method that conserves water gives this mean travel time as the volume of water bound for the sink divided by its inflow. The agreement therefore tests only the volume attributed to the sink. That volume is nearly the same in both methods."

L37 passes. It gives the evidence, explains it and ends on advice ("On this evidence, we would …"). That ending suits a closing paragraph.

### 4.4 Section 5, cost (L5): no conclusion

Rewrite:

"A trace of every well group took less time than the fastest PRT run on the same flows. One trace of nine destination groups (each well alone and all eight together) took 2–3 s and peaked at 2.5 GB of memory. Each further group added about 0.19 GB ({SI: the Neversink comparison}). The closure check held to 1 × 10⁻¹² m³/d or better for every group. PRT took about 30 s when it wrote only where each particle ends. With full particle tracks, it took about 5 min with particles released at one height in each start cell and about 13 min with particles released at four heights. These times do not compare like with like. One PRT run follows one set of particle settings for all wells together. One trace gives F, the volumes and the checks for every well group. Across the ensemble, the two traces of each realisation [say which] took about 9 s."

The one-height and four-height wording replaces 122,112 and 488,448. NS line 150 and its table (line 162) confirm the four heights. It tells the reader why the counts differ, which the bare counts do not. Check that the 122,112 run is the one-height run before using it.

Section 5, last paragraph (L15), with the stream-network sentence moved to where it belongs:

"Example C (Section 4) showed that a sink's split by source depends on how the stream reaches are traced. On this model the split also depends on the method. Full mixing attributes 57 % of the wells' water to recharge and 43 % to stream leakage. With the stream reaches traced as cells of their own, all of that water traces back to recharge. Along weight-losing particle paths the split is 49 % recharge and 51 % stream leakage, although both methods deliver the wells' total inflow to within 2 %. We infer, without tracing it cell by cell, that stream water leaking near the wells stays on particle paths that end at a well. Full mixing instead gives that water the average fate of all the water leaving the cells it passes."

L7, L9 and L13 of Section 5 are in the right order (conclusion, evidence, caveat).

## 5. Sentences the author would likely call unnecessary

These are restatements, implementation detail or numbers the reader's question does not need. Counts are approximate word savings. All of them are in the safe list of Section 7.

| # | where | sentence(s) | why | words saved |
|---|---|---|---|---|
| S1 | §4 L5 | "The notebooks are numbered as in Table 1." | Table 1 shows it | 8 |
| S2 | §4 L5 | "Every example model is described in {SI: software, verification and models}." | The Table 1 caption says the same | 11 |
| S3 | §4 L11 | ", as the closure check requires" | Restates what a check is | 5 |
| S4 | §4 L13 | "The 18,208 particles from 1,133 cells deliver 799.9 of the 800 m³/d pumped. That total says little about the area, because … The comparison of areas is more telling." | The paragraph states a number and then says it means little. Table 1 row 01 keeps the 799.9 if wanted. | 35 |
| S5 | §4 L25 | "Here porosity (0.3) differs from specific yield (0.2) … The share of initial water in year 30 is 0.5166 with the default volumes and 0.5167 with GWT's volumes." (three sentences) | Four numbers to say "little". Replace with: "The two volume options of Section 2 change the fractions by less than 0.004 on this model, although porosity (0.3) differs from specific yield (0.2) ({SI: …})." | 45 |
| S6 | §4 L25 | sub-step sentences | Three numbers where two make the point. Replace with: "Transport sub-steps matter more, because long implicit steps make new water arrive too early. With one transport step per flow step, new recharge made up 0.0078 of the well's water in the first step, against 0.0042 with 16 sub-steps. Four sub-steps (0.0049) remove most of this effect." | 15 |
| S7 | §4 L31 | "A forward trace from each source gives the same split. The forward and backward volumes … agree within 1 × 10⁻⁶ m³/d, as the forward–backward check requires." | A check that holds by construction says nothing about mixing, which is the paragraph's point. Table 1 row 03 keeps it. | 32 |
| S8 | §4 L33 | "The closure check holds both ways." | Table 1 row 07 | 6 |
| S9 | §4 L33 | "The answer to … thus depends on whether the stream reaches are traced. For this reason, a study should report which choice it made." | Restates the paragraph's first sentence. Replace with: "A study that reports how much of a well's water is stream water should therefore say which of the two choices it made." | 12 |
| S10 | §4 L33 | "Its well therefore takes … above." | Shorter rewrite in 1.1, item 1 | 10 |
| S11 | §4 L39 | "The three examples above use seven of the ten notebooks in full or in part. Table 1 lists all ten, with the question each answers, its main output, the check behind it and how closely the check agrees." | A number nobody needs. The second sentence repeats the caption. Replace with "Table 1 lists all ten notebooks." | 33 |
| S12 | §4 L39 | "Row 09 needs a few words of explanation." | Announcement (1.3, item 4) | 8 |
| S13 | §4 L17 | The forward-trace sentences | Off-topic tail (2.3, item 1). Table 1 row 03 and Methods cover it. | 33 |
| S14 | §4 L29 | "Transient tracking has so far been tested on synthetic models only (Section 6)." | Section 6 says it. Keep it only if the author wants the caveat at the point of the claim. | 13 |
| S15 | §4 L9 | "The expected area of Section 2 gives a size without a threshold." | Restates Methods. Folded into 2.2, item 1. | 6 |
| S16 | §4 L27 | "Four MODFLOW 6 GWT runs, one per source, give the same fractions to 1.5 × 10⁻¹⁰." | A second consistency test against GWT, already in Table 1 row 10. The point it serves, one run against one per source, is better stated with the tracking run (rewrite in Section 7). | 16 |
| S17 | §4 Table 1 caption | (none cut). If S2 is not taken, cut "All examples use the example model of this section or a version of it ({SI: …})" instead. | Duplicate | (0) |
| N1 | §5 L5 | "Their track files were about 1.5 and 6 GB." | Disk size does not serve the cost comparison | 9 |
| N2 | §5 L5 | "Closure held to 3 × 10⁻¹² m³/d in every realisation." | The closure check was already reported for the calibrated model | 10 |
| N3 | §5 L7 | the three settings sentences | One list sentence (2.1, item 6) | 8 |
| N4 | §5 L5 | particle counts 122,112 and 488,448 | Replaced by "one height" and "four heights" (4.4) | 2 |

Rewrites in this review add words back where the reader needs them: nested zones (+40), the Bedekar model (+20), the particle area and "conserve water" (+25), the river travel-time reason (+15), priority wells (+12), and the conclusion-first sentences (+40). The net saving in §4 is therefore about 220 words, not 360.

## 6. Table 1

The column design is good. Questions are parallel and phrased the way a practitioner would ask them. The letters in the Notebook column tie rows to the examples. Four problems remain.

1. **Cells that are paragraphs.** Agreement in row 01 (4 sentences, 30 words), row 02 (4 sentences, 45 words), row 04 (4 sentences, 45 words) and row 09 (4 sentences, 60 words). Row 09 is a paragraph.
2. **Full stops between noun phrases** ("F map. F > 0.5 and F > 0.1 areas (…). The well's water by source"). These read as fragments. Use commas, or a line break (`<br>`) if the journal's table style allows it.
3. **Results in the wrong column.** Row 02 Agreement: "A small well pumps 5 m³/d from a cell that carries 33.7 m³/d. Net accounting attributes all 33.7 m³/d to it, 6.7 times its pumping." This is an output, not agreement with a check. Move it to Output.
4. **Rows covered by examples A, B and C repeat the prose.** The table needs only a headline number for these rows. Rows 02, 04 and 09 have no prose behind them, so their detail is worth keeping.

Smaller points:
- The verbs are not parallel ("GWT to 9.8 × 10⁻¹⁴" in row 08, "G and GWT agree to …" in row 03). Use "Agrees with … to …" throughout.
- The caption does not say what a number such as 1 × 10⁻¹⁴ means. Add: "Values such as 1 × 10⁻¹⁴ are the largest difference between the two results." Check that this holds in every row first.
- Row 09's question "How sure are we?" is vague next to the other questions. Write "How does parameter uncertainty change the area?"

Proposed cells (numbers unchanged):

| Row | Column | Proposed |
|---|---|---|
| 01 | Output | F map, F > 0.5 and F > 0.1 areas, the well's water by source |
| 01 | Agreement | Closure error 0.0. F > 0.5 area 2.1 % smaller than the particle area, F > 0.1 area holds every particle cell |
| 02 | Output | Gross and net accounting, fractions to every sink. At a well pumping 5 m³/d, net accounting attributes 33.7 m³/d (6.7 times) |
| 02 | Agreement | Published example to 1 × 10⁻¹⁴. Fractions to all sinks add up to 1 within 1 × 10⁻¹⁵ |
| 04 | Checked against | DIS against DISU and DISV. Loop-by-loop solve against a solve of all cells at once [check that this is what "plain sparse solve" means] |
| 04 | Agreement | DISU equals DIS. The two solves agree to 3.3 × 10⁻¹⁶. On DISV the expected area differs by +0.4 %, but F falls from 0.5 to 0.1 over 186 m against 121 m |
| 05 | Output | Seasonal snapshots of F, nested zones (0.52, 0.93 and 0.41 km²) |
| 05 | Checked against | Statistics over the snapshots recomputed step by step [check against 05 §8]. Closure check in every snapshot |
| 06 | Agreement | All water −0.5 % (not an independent test). Median ratio of particle to full-mixing time 0.96 where F ≥ 0.5, 5.72 where F < 0.5 |
| 08 | Agreement | Agrees with GWT to 9.8 × 10⁻¹⁴ in every cell and step. Forward and backward volumes agree to 4.3 × 10⁻¹⁶. Tagged-water balances close to 9.9 × 10⁻¹⁶ |
| 09 | Question | How does parameter uncertainty change the area? |
| 09 | Checked against | A synthetic true model. Serial against parallel runs. (Drop "exact quantiles against quantiles from histograms", or say in the SI what it tests.) |
| 09 | Agreement | The uncertain band (probability 0.1 to 0.9) shrinks from 1.10 to 0.35 km². The posterior covers 93 % of the true F > 0.5 area (prior 79 %). Cells with a probability of at least 0.9 lie in the true area as often as before (86–87 %) |
| 10 | Agreement | Within 1.3 percentage points of the published curves (0.6 with 7.6-day sub-steps). Agrees with four GWT runs to 1.5 × 10⁻¹⁰ |

Saving: about 70 words.

## 7. Length

§4 is 3,392 words against a target of about 2,050. §5 is 847 words against 550–650. The safe cuts and the rewrites above bring §4 to about 3,170 and leave §5 at about 840 with the added definitions. The targets cannot be reached without losing explanation. The outside feedback asked for fewer worked examples, with readers sent to the notebooks. The cuts below therefore move content to Table 1 or the SI rather than losing it.

### 7.1 Safe cuts (no explanation lost)

§4: S1–S16 (about 290 words) and the Table 1 cell trims (about 70 words), **about 360 words in all**. After the definitions and conclusion-first sentences added back (about 150), the net saving is about 210 words.

§5: N1–N4, **about 30 words**, plus about 5 from the split cost sentence. **About 35 words in all.** After priority wells and the topic sentence are added back (about 30), the net saving is close to zero.

### 7.2 Cuts that lose explanation (the author's call)

§4:

| # | cut | what is lost | saving |
|---|---|---|---|
| L1 | Bedekar et al. (L27) down to four sentences: purpose, one run against one per source, year-25 shares against published, largest difference with the read-off caveat. The 7.6-day sub-steps go to Table 1 row 10. | Why the remaining 1.3 points are due to time stepping | ~90 |
| L2 | Time-limited area paragraph (L29) down to two sentences in L23, with the cell counts in the SI | The reader no longer sees that the 25-year area reaches the steady area | ~80 |
| L3 | GWT check paragraph (L25): keep the consistency test and one sentence on sub-steps. The volume options go to the SI. | Why the volume options barely matter | ~40 beyond S5/S6 |
| L4 | Row 09 paragraph (L39): move the realisation and posterior definitions into the Fig. 2 caption (2g) and drop the PEST++ caveat | The caveat that the trace was not tested inside a PEST++ run. Manuscript rules ask for how the work scales in PEST++ workflows, so I would keep it. | ~70 |
| L5 | Snapshot detail (L19): drop the 3-year run detail and the nested-zones sentences, keep the 0.59–1.35 km² and 52.5 % contrast | Nested zones then appear only in Table 1 row 05, and Fig. 2e needs its caption to carry the definition | ~60 with the definitions |
| L6 | Travel time by source (L35): keep all water and the caveat, move by-source differences to Table 1 row 06 | The river-leakage difference. This is also the way out if no reason for the −20.1 % can be given. | ~35 |
| L7 | Example C stream variant (L33) down to three sentences | Section 5 L15 builds on it, so I would not cut it | ~70 |

L1–L6 total about 375 words. §4 would then come to about 2,800. The target of 2,050 would need one of the three external checks of example B (GWT, Bedekar et al., time-limited area) moved to Table 1 entirely. That is a scope decision for the author.

§5:

| # | cut | what is lost | saving |
|---|---|---|---|
| M1 | Full-track PRT times. Keep the 30 s end-point run only. | The cost of PRT with tracks, which many users run | ~30 |
| M2 | Ensemble timing and the realisation sentences of L3. The calibrated model then becomes "the published calibrated model". | Evidence that the trace scales across an ensemble | ~40 |
| M3 | Weak-sink paragraph (L13): keep the buried-stream definition and the stopping counts, drop the net-accounting sentences | That net accounting barely closes the gap (0.41 to 0.44) | ~25 |
| M4 | The weight-losing comparison in L9 (87 % of 691 cells, 89 cells, 227 m³/d) | The closest like-for-like comparison on the real model. I would keep it. | ~45 |
| M5 | "Each further group added about 0.19 GB" | How memory scales with the number of groups (a practical limit) | ~11 |

M1, M2, M3 and M5 total about 105 words and would bring §5 to about 740. Reaching 650 would also need M4. I would not cut it, because it is the comparison that separates the effect of mixing from the effect of particle settings.
