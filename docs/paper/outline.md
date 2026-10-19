# Paper outline, round 2: more method, three worked examples, one table

Branch `paper-draft-r2`, 2026-10-19. This outline replaces the outline of 2026-10-15, which planned ten worked examples. That outline is still in git history and on branch `paper-draft-alt`. The starting point for this round is the reduced draft in `docs/paper/draft_reduced/`. Items marked [check] need verifying before they go into the text. Terms follow `docs/paper/terms.md`.

## 1. Notes for writers

### 1.1 Why a new round

External readers commented on the reduced draft of 6 pages. Their two main points were these:
- The method section needs a good part of the method detail that now sits in the Supporting Information (SI). Methods is the big thing. The rest is wordsmithing and figure comments.
- The paper can carry fewer worked examples and direct readers to the Jupyter notebooks. Neversink should stay, because it shows that the method works and scales on a real model.

They also found the prose dry. The reduced draft prefers short declarative sentences, and a paper made only of these reads as a list of facts.

The author has relaxed the 6-page cap. The paper should stay short, but a reader must be able to follow it without the SI. Page limits are decided later.

### 1.2 The framing

The paper presents a tool for practitioners. Three things make it worth using:
- it is fast;
- it is checked against other common approaches (particle tracking, transport with tagged water, published studies);
- it is open about its trade-offs.

The tool is not only for wells or capture zones. It traces where the water of any sink comes from, where the water of any source goes, a sink's water by source, and mean travel times. Every example should keep this general view, even where the example sink is a well.

### 1.3 Style for the coming draft

All prose follows the `voice-hugman` skill and its `references/manuscript_rules.md`. Every writer and reviewer brief carries them.

The bans stay:
- no semicolons, and no colon or ", and" joins of two claims;
- no appositive packing (define a term in its own sentence);
- no participle or absolute openers;
- no LLM constructions ("We do X by Y", "credit", "X gives no Y", filler transitions, puffery).

What changes in this round:
- A sentence may carry a main idea plus its reason or its consequence. "Because", "so that" and a restrictive "which" are the tools for this. Two independent claims still get two sentences.
- Paragraphs need connecting sentences. Each paragraph says why it follows from the last ("This means …", "For this reason …", "The check cannot show …").
- Vary sentence length. A run of five-word sentences reads as badly as a packed sentence.
- Shorter must not mean cryptic. Explain each concept where it first appears, in plain words, even if that costs a sentence.

The reduced draft read as dry staccato. Methods and the three worked examples should read like a hydrogeologist explaining the work to a colleague.

### 1.4 Rules that carry over

- Never change or invent a number. Every number keeps its `<!-- evidence: … -->` comment.
- The paper text names FlowSource only where it cites it (Foley and Black 2013). Elsewhere it says "the reference method" or describes it.
- No "tutorial" in the text, captions or figures. The notebooks are named once, in the opening of Section 4, and in the new Table 1 (see open question 2).
- Seasons are wet, wet-to-dry, dry and dry-to-wet.
- Keep honest hedges where a check is partial ("we read this as …", "not an independent test").
- Abstract, conclusions and impact statement say the same thing. When one changes, the others change with it.

### 1.5 Decisions log

| # | Date | Decision | Trigger |
|---|---|---|---|
| 1 | 2026-10-19 | Methods grows to about 1,500–2,000 words. It takes the method from SI Text S1 (`si/B.md`) and the full draft's Section 2. | External feedback: "move a good chunk of detail from SI on method to paper" |
| 2 | 2026-10-19 | Three worked examples in depth: A (contributing area), B (transient tracking), C (the sink's water by source and by travel time). The other examples go to a table. | External feedback: "fewer worked examples and direct reader to jupyter notebooks" |
| 3 | 2026-10-19 | A main-text table at the end of Section 4, with one row per notebook (all ten). | Same |
| 4 | 2026-10-19 | Fig. 2 (the gallery) stays as the overview of output types. | Author |
| 5 | 2026-10-19 | Neversink stays and grows to about 400–600 words. It reports cost against PRT, not against the MODFLOW 6 run. | External feedback ("keeping neversink in there is good to show it works on a real model"); author ("against MF6 is irrelevant, against PRT would matter") |
| 6 | 2026-10-19 | The ensemble example leaves the worked examples and becomes a table row. The speed argument for ensembles stays in Section 3. | Author: "replace ensembles with trace splits of water source and travel time" |
| 7 | 2026-10-19 | Style: one idea per sentence stays, but a sentence may carry its reason or consequence, and paragraphs get connecting sentences. | External feedback: "a pretty dry read" |
| 8 | 2026-10-19 | The 6-page cap is relaxed. Comprehension beats length. Page limits are decided later. | Author |
| 9 | 2026-10-19 | Example C is the sink's water by source and by travel time, as read in this outline. | Author, open question 1 |
| 10 | 2026-10-19 | Table 1 names the notebooks by number only. Section 7 points once to the repository. | Author, open question 2 |
| 11 | 2026-10-19 | Methods gets the snapshot-against-tracking schematic as a second panel of Fig. 1, and shows the backward-in-time equation (Eq. S14) with its plain reading. | Author, open question 3 |
| 12 | 2026-10-19 | A compact main-text figure for examples A and B: the particle-share map and the Bedekar et al. (2024) curves. | Author, open question 4 |
| 13 | 2026-10-19 | The MODFLOW 6 run time (44 s) leaves the abstract and Section 3. The speed argument rests on the trace time. | Author, open question 5 |
| 14 | 2026-10-19 | Equations get a short plain reading of their core idea, one or two sentences, not a derivation in words. | Author, after Methods v1 came out at 2,605 words |

Decisions carried forward from 2026-10-15 (the outline on `paper-draft-alt`, its Section 6):
- The notebooks are named once, in the Section 4 opening.
- The test-model verification stays in the SI.
- The Neversink pumping scenarios stay out.
- The title is *Where does it come from and where does it go? Fast, open-source flow tracing for MODFLOW 6 models*.

## 2. Key messages

The abstract, the closing paragraph of Section 6 and the impact statement must all carry these five messages and no others.

1. From the flows a MODFLOW 6 model already saves, the code maps where the water of any sink comes from and where the water of any source goes. It also splits a sink's water by source and gives mean travel times, in steady-state and transient flow.
2. It extends the full-mixing method of Foley and Black (2013) to every MODFLOW 6 grid type, stream networks and linked models. It counts only the water a weak sink takes (gross accounting), it carries tagged water through storage forward and backward in time, and it checks every result against the water budget.
3. It is checked against other common approaches. It matches MODFLOW 6 transport (GWT) to round-off when both use the same water volumes. It reproduces a published unit-concentration study and a published worked example. It agrees with MODFLOW 6 particle tracking (PRT) in a sink's total water and mean travel time, but differs from it at the edge of a contributing area.
4. It scales. On a published regional model of 1.68 million cells, one trace of eight wells, alone and together, takes 2–3 s and 2.5 GB of memory. PRT on the same flows takes from about 30 s to about 13 min, depending on what it writes. This cost is small enough to repeat a trace for every realisation of an ensemble.
5. Full mixing has costs. Its areas are wider and more diffuse than particle areas. The threshold on F is a judgement. Particles remain better where a sharp edge or a first arrival matters, and transport where dispersion or reactions matter.

## 3. Section plan

Word counts below are prose words with HTML comments removed (the count used here: `perl -0pe 's/<!--.*?-->//gs' file | wc -w`). On that count the reduced draft's sections 00–07 hold 4,043 words. The brief for this round gives about 2,550 words for the same sections, so the two counts differ [check: which count the author means]. The targets below use the comment-stripped count.

| § | Section | Reduced draft (words) | Target (words) | Figures and tables |
|---|---|---|---|---|
| 00 | Title, impact statement, abstract, key words | 337 | 340 | – |
| 1 | Introduction | 581 | 650 | – |
| 2 | Method | 655 | 1,630 | Fig. 1 (and a proposed Fig. 2, see Section 4 of this outline) |
| 3 | Software and cost | 144 | 250 | – |
| 4 | Worked examples (A, B, C and Table 1) | 1,376 | 2,050 (table text about 450 of it) | Fig. 2 gallery, Table 1, perhaps one example figure |
| 5 | A regional model: Neversink | 504 | 550 | Fig. 4 |
| 6 | Trade-offs and conclusions | 349 | 400 | – |
| 7 | Code and data availability | 97 | 100 | – |
| | Total | 4,043 | about 5,930 | |

### 3.0 Title, impact statement, abstract, key words (about 340 words)

**Purpose.** The reader decides from these whether the tool answers their question. They must carry the five key messages of Section 2 of this outline and nothing more.

**Changes from the reduced draft (`draft_reduced/sections/00_front.md`).** The reduced front matter leans on ensembles in three places. Each needs adjusting:
- Impact statement: "fast enough for ensembles". Replace with the speed message of key message 4, for example "fast enough for regional models and for repeated runs" [author's wording].
- Abstract: "The paper presents ten worked examples. Each checks an output a practitioner would use against other commonly used approaches." Change to three worked examples and a table of ten notebooks.
- Abstract: "Tracing is cheap enough to include in history matching and similar analyses." Keep only as the cost sentence of key message 4. Its evidence comment already notes that tracing inside each PEST++ run is untested.
- Abstract: "That is small next to the model run itself" compares against MODFLOW 6. Replace with the PRT comparison of key message 4 (see open question 5).
- Key words: "ensemble" can go, since no worked example is about ensembles. Nine key words become eight.

Title stays (decision of 2026-10-15).

### 3.1 Introduction (about 650 words)

**Purpose.** Tell the practitioner which questions the tool answers, which methods already answer them, and what this work adds.

The reduced introduction (`draft_reduced/sections/01_introduction.md`) has the right content. It needs the connecting sentences of Section 1.3 of this outline and three changes.

Points in order:
1. The practical problem. Practitioners ask where groundwater comes from and where it goes. They also need to know how the answers change through the year. Protection zones are one use (Environment Agency 2019). evidence: `draft_reduced/sections/01_introduction.md` paragraph 1.
2. Four families of methods (particle tracking, transport with tagged water, adjoint and age methods, full-mixing flow tracing), in one overview paragraph before the detail. evidence: same file, paragraph 2.
3. Particles need a stop-or-pass rule at weak sinks. Define sink term and weak sink here. evidence: same file, paragraph 3.
4. Full mixing lets a weak sink take its share. FlowSource (Foley and Black 2013) and MODALL (Potter et al. 2008) apply different rules. Name net and gross accounting here. evidence: same file, paragraph 4.
5. What this work adds: open source, every MODFLOW 6 grid type, stream networks and linked models, gross accounting by default, budget checks, transient tracking forward and backward in time, and speed.
   - Change: the reduced draft's sentence on ensembles ("Risk-based studies run an ensemble … The code is fast enough to trace every version.") becomes one sentence on speed at scale that points to Section 5. Keep the Fienen et al. (2022) citation, because Section 5 uses their model.
6. What the paper does. Change: "Section 4 works through ten examples" becomes "Section 4 works through three examples in depth and summarises ten notebooks in a table". Section 5 tests the code on a published regional model. Section 6 sets out the trade-offs.

### 3.2 Method (about 1,630 words)

**Purpose.** A reader must be able to understand every output in Sections 4 and 5 from this section alone, without the SI. Each concept is explained where it first appears. Each equation gets a plain reading. "In words:" appears at most once.

**What moves in.** Most of SI Text S1 (`draft_reduced/si/B.md`) and the full draft's Section 2 (`draft/sections/02_methods.md`, 1,757 words):
- `si/B.md` "The backward and forward fractions" (Eqs. S1–S5);
- `si/B.md` "Volumes";
- `si/B.md` "Why the water-budget checks hold exactly" (Eqs. S6–S8 and the boundary-control check);
- `si/B.md` "Mean travel time" (Eqs. S10 and S11), without the exit-cell variant;
- `si/B.md` "Transient tracking" (Eq. S12, the flow-imbalance correction, initial water);
- `si/B.md` "Backward tracking in time" (the meaning of w, the fraction still stored, the transient forward–backward check);
- `draft/sections/02_methods.md` Sections 2.4 (gross and net accounting) and 2.7 (snapshots), whose prose is closer to the target than the SI's.

Notebook 02's small-well example is absorbed by Fig. 1. The gross and net numbers of the eight-cell example carry the point in Methods, and the small-well result goes to Table 1.

**What stays in the SI.** The solution of the linear systems (flow order, flow loops, closed recirculation loops), the details of net accounting (Eq. S9, which cells are fixed), the matrix form of each transient step and its solution, the water volume options ("flow" and "gwt"), transport sub-steps, and the travel time to the point where water enters the sink cell.

Proposed subsections, as bold run-in heads:

**2.1 Overview (about 100 words).**
- A trace starts from a destination (backward) or a source (forward). It works on the saved cell-by-cell flows of one time step, or of every step in a transient model. evidence: `draft/sections/02_methods.md` Section 2.1.
- Say what each subsection gives the reader: fractions, volumes, the rule at weak sinks, the checks, travel times, and the two ways to trace transient flow.

**2.2 Full mixing and the cell budget (about 200 words).**
- Full mixing treats each active cell as one well-mixed volume of water. All water leaving a cell has the same mix of origins and fates. evidence: `docs/paper/terms.md` (full mixing).
- The cell-to-cell flows (FLOW-JA-FACE) and the source and sink terms come from the budget file. Each source and sink term stays separate by package and boundary. evidence: `si/B.md` "The backward and forward fractions", paragraph 1.
- Eq. (1), the cell's total inflow, total outflow and cell budget error (now Eq. S1). The budget of a MODFLOW model never balances exactly, so the error is small but not zero. The code reports it and never forces it to zero. evidence: `si/B.md`; `src/gwsource/diagnostics.py`.

**2.3 Backward fraction F (about 250 words).**
- Purpose first: F answers "where does this sink's water come from?". Define F as the share of the water leaving cell i that later leaves the model through the destination.
- Eq. (2) in volume form (now Eq. S2): the water leaving a cell that ends at the destination is the part that leaves directly plus each neighbour's share of what it receives. Then the fraction form (the reduced draft's Eq. 1).
- Fig. 1 works through the eight-cell example. In the well cell F = 6/11 = 0.55 under gross accounting. evidence: `display/B.md` Figure 1; `studies/paper/method_figures.py` GRAPH_EDGES, GRAPH_TERMS.
- One sentence on the matrix form: one solve gives every destination group. One sentence on the solution: the code solves the equations in the order the water flows, and solves each flow loop as one block ({SI: method in full}). evidence: `si/B.md` "Solution of the linear systems".
- A contributing area is the set of cells where F exceeds a threshold that the user chooses. The choice is a judgement (Section 6).

**2.4 Forward fraction G (about 150 words).**
- Purpose first: G answers "where does this source's water go, and how much of each cell's water came from it?".
- Eq. (3) in volume form (now Eq. S4), with a plain reading. It mirrors Eq. (2) with inflows in place of outflows.
- G is the long-run share. It equals the concentration of a unit-concentration transport run at equilibrium (checked in Table 1, row 03).

**2.5 Volumes and the water-budget checks (about 200 words).**
- A fraction times a flow gives a volume of water per unit time. Volume through = F × O. Volume from = F × the cell's inflow through its source terms. evidence: `si/B.md` "Volumes"; `src/gwsource/metrics.py`.
- The volume from, summed over all cells package by package, splits the destination's water by source (Fig. 2b, example C). The forward trace gives the matching volumes to each sink.

- The checks, condensed (author comment 2026-10-19: "not too important; can be condensed or folded into other sections or SI"). About 80 words, as the last points of this subsection:
  - Adding Eq. (2) over all cells gives the closure check. In plain words: the source water traced to the destination, corrected for the cell budget errors, adds up to the water the destination takes. No equation in the main text. evidence: `si/B.md` "Why the water-budget checks hold exactly".
  - One sentence names the other two checks (forward–backward and boundary control) and says that, because they include the cell budget errors, they hold exactly for any flow field ({SI: method in full}).
  - Keep the caveat: the checks test the solution. They cannot show that the flow model is right, or that full mixing describes how water moves in the aquifer. evidence: `draft/sections/02_methods.md` Section 2.5, last paragraph.
  - The derivations of all three checks (Eqs S6 and S8, and the reason the double sum cancels) stay in the SI.

**2.6 Gross and net accounting at weak sinks (about 200 words).**
- Recall the weak sink of Section 1. Under gross accounting each sink term takes its share of the cell's outflow, as in a transport model. This is the default. evidence: `draft/sections/02_methods.md` Section 2.4; `src/gwsource/config.py`.
- Under net accounting, all the water passing through a destination cell counts as the destination's water, so the cell is fixed at F = 1. This is how FlowSource counts water (Foley and Black 2013).
- In Fig. 1, gross accounting gives the well the 6 m³/d it pumps. Net accounting adds the 5 m³/d that flow on through the well cell to the river. evidence: `display/B.md`; `studies/paper/method_figures.py` GRAPH_TERMS (cell 6: 6 to the well, 5 on).
- At a small well the difference can be several times the pumping (Table 1, row 02: 6.7 times). We would use net accounting to compare with a FlowSource study.
- One sentence: net accounting needs no cell budget error term, and its details are in {SI: method in full}.

**2.7 Mean travel time (about 200 words).**
- Purpose first: fractions say how much water arrives, not when.
- The water volume of a cell, V = porosity × saturated volume. Fractions need no porosity, but travel times do. Porosity is an explicit input with no default. evidence: `si/B.md` "Mean travel time"; `src/gwsource/traveltime.py`.
- The mean residence time of a cell, τ = V/O. Eq. (6) (now Eq. S10) and the mean travel time m/F, with a plain reading: each cell adds its residence time weighted by its F, and the sum passes upstream with the outflow shares.
- The travel-time closure check, Eq. (7) (now Eq. S11): the volume of water that will end at the destination, divided by the destination's inflow, equals the flow-weighted mean travel time of all its water. This sentence is needed in example C, where it explains why the overall PRT agreement is not an independent test.
- A mean travel time averages fast and slow water that have mixed in the cells. It is not a first-arrival time.
- Defined under gross accounting only.

**2.8 Transient flow: snapshots and transient tracking (about 300 words).**
- Purpose first: in a transient model, the water reaching a sink depends on what happened in earlier steps.
- A snapshot traces each time step on its own flows, as if they were steady. Storage release becomes a source term and storage gain a sink term. A snapshot assumes that water reaches the sink in the same step it entered, so it cannot show wet-season recharge reaching the well in the dry season. It also cannot say where the water released from storage came from. The published descriptions of the reference method treat transient models in this way. evidence: `draft/sections/02_methods.md` Section 2.7, paragraph 1; `draft_reduced/sections/01_introduction.md` (Environment Agency 2019, Appendix C4.4).
- Transient tracking extends full mixing through time. We refer to it as transient tracking. Water from the chosen sources is tagged. Storage terms are not source or sink terms. Instead they change the water volume of the cell from step to step.
- Eq. (8) (now Eq. S12), the tagged-water balance of one cell over one step, with a plain reading.
- The scheme is implicit in time and adds no dispersion, as GWT does without dispersion (Langevin et al. 2022). The cell budget error leaves at the cell's own mix, as GWT's flow-imbalance correction does. evidence: `si/B.md` "Transient tracking".
- It needs porosity and the budget of every time step (SAVE BUDGET ALL).
- The water in the model at the start can be tagged as its own group, initial water. Initial water is not necessarily water from before pumping began.
- Mention that the water volumes and the length of the transport step affect the result, and point to {SI: method in full} for the two volume options and transport sub-steps. Example B quotes their effect.
- Hydraulic mixing cells (Partington et al. 2011) carry mixed water through storage in a similar way. evidence: `draft_reduced/sections/02_methods.md`.

**2.9 Backward tracking in time (about 230 words).**
- Purpose first: forward tracking cannot tell which of the water now in the aquifer will reach the sink, and by when.
- Backward tracking in time solves the backward counterpart of each step, from the end of the simulation to its start. Say once that this is not MODPATH backward tracking, in which particles run against the flow from the sink. It is the discrete analogue of adjoint methods (Neupauer and Wilson 1999; Cornaton and Perrochet 2006). evidence: `docs/paper/terms.md` (backward tracking in time); `si/B.md` "Backward tracking in time".
- Eq. (9) (now Eq. S14), or its plain reading only if the writer judges the equation too heavy (see open question 3).
- Define the backward fraction in time w: the share of the water in a cell at the start of a step, or entering it during the step, that leaves through the destination before the simulation ends. A map of w is a time-limited contributing area (Fig. 2f).
- The same run gives the fraction that leaves through other sinks and the fraction still stored at the end. The three add up to 1.
- The transient forward–backward check: the tagged water the destination takes equals the tagged inflow and initial water times their share that later reaches the destination. Under flows held constant, c tends to G and w to F.

### 3.3 Software and cost (about 250 words)

**Purpose.** Tell the reader what the code needs and what a trace costs, because cost decides whether a trace can be repeated for every realisation of an ensemble.

Points in order:
1. `gwsource` is an open-source Python package (MIT licence). It reads the binary grid file and budget file of a MODFLOW 6 GWF model, on any grid type. Stream reaches, lakes and multi-aquifer wells can be traced as extra cells. evidence: `draft_reduced/sections/03_software.md`.
2. Inputs, selections and outputs are in {SI: inputs, selections and outputs}.
3. Cost on the regional model of Section 5: 2–3 s for nine destination groups, peak memory 2.5 GB, of which 0.52 GB is the loaded budget. Each further group adds about 0.19 GB. evidence: `draft/reviews/r4_memory.md` (Apple M4 Max, 16 cores, 64 GB; load 1.0–1.2 s, trace 1.4–1.5 s).
4. The speed argument for ensembles stays here, as one or two sentences without a worked example:
   - 50 realisations of the example model are traced in 0.69 s. evidence: `tutorials/09_ensembles/09_ensembles.ipynb` cell 6 output.
   - On the regional model, two traces of each of 358 realisations took about 9 s per realisation. evidence: `docs/neversink_study.md` §6 "Runs".
   - Table 1 (row 09) points to the ensemble and history-matching notebook.
   - Keep the caveat: tracing inside each PEST++ model run is untested. evidence: `draft_reduced/sections/04_examples.md` (Ensembles, last paragraph).
5. Testing: ten test models and two published examples ({SI: verification checks on the test models}). evidence: `draft_reduced/sections/03_software.md`.

Change: drop the MODFLOW 6 run time (44 s) from this section (decision 13). The main comparison of cost is against particle tracking (author comment 2026-10-19):
- Point 3 sets the trace against PRT on the same flows in one sentence: 2–3 s for the trace, against about 30 s for a PRT run that writes only end points and 5 to 13 min with full tracks (Section 5 gives the detail and the fairness caveat). evidence: NS "Reproducing" and the workflow run times.
- Add the same comparison on the example model if the notebooks record it: the F trace against the PRT run of notebook 01 §8 (18,208 particles) [check: the notebook does not print the PRT run time yet; add a timing to tutorial 01 on `tutorials-paper-sync` or leave the example-model comparison out].
- The speed argument for ensembles (point 4) then reads as: a trace costs a small fraction of a particle run, so it can be repeated for every realisation where a particle run could not.

### 3.4 Worked examples (about 2,050 words)

**Opening paragraph (about 120 words).**
- Purpose: three examples show the main kinds of output in depth, each checked against another approach. Table 1 summarises all ten notebooks. Fig. 2 shows one output of each type.
- The shared example model, as in the reduced draft: one unconfined layer of 40 × 40 cells of 50 m, recharge of 5 × 10⁻⁴ m/d, a constant head along the west edge, a north–south river, and a supply well pumping 800 m³/d 100 m west of the river. evidence: `draft_reduced/sections/04_examples.md` paragraph 1; `tutorials/herebedragons.py` AquiferSpec.
- Each example ships with the code as a Jupyter notebook that reproduces its numbers and figure. Name this once here (decision of 2026-10-15).

#### Example A. Where does the well's water come from, and how far out does it reach? (about 500 words; notebook 01, with one sentence on 03)

**Purpose.** A protection zone starts from the land whose water reaches the well. The practitioner wants the area, how far it reaches, and how much to trust its edge.

**What moves in.** `draft_reduced/sections/04_examples.md` "Sources and area" (paragraphs 1–2) and `si/G_examples.md` "Sources and area". The gross-and-net paragraph of the reduced "Sources and area" moves to Methods (Fig. 1) and to Table 1 row 02.

Points in order:
1. F map (Fig. 2a). Cells with F > 0.5 cover 1.143 km² (457 cells). Cells with F > 0.1 cover 1.575 km² (630 cells). evidence: `tutorials/01_quickstart/01_quickstart.ipynb` §5, cell 16.
2. How far out the area reaches. Water from as far as the west edge of the model, about 1.4 km from the well, reaches it, because 15 % of the well's water enters there as regional inflow. evidence: 01 §6, cell 20 (west edge 118.1 m³/d, 0.148); well cell centre at x = 1,425 m, from `tutorials/05_transient_snapshots/05_transient_snapshots.ipynb` cell 6 output (same grid and well). Whether the F > 0.1 area itself reaches the west edge is not printed in 01 [check]. The area also has a tail east of the river. The writer should explain it from the figure. A distance from the well to the far edge of the F > 0.1 area is not printed in the notebook [check: print it in 01 if the text wants a distance].
3. The expected area, the sum of F times cell area, is 1.173 km². It is a size of the area that needs no threshold. evidence: 01 §5, cell 16.
4. The closure check. The traced sources add up to the 800 m³/d pumped (800.0000 against 800.0000 m³/d, relative error 0.0). This check tests the solution, not the position of the edge. evidence: 01 §7, cell 22.
5. Why particles. The edge is where full mixing and particles disagree, so the edge needs a check of its own. Introduce weight-losing PRT particles with their purpose: they lose weight at every sink they pass in proportion to the flow that sink takes, as full mixing does. Cite Visser et al. (2009) and Winston et al. (2018) as precedents. evidence: `draft_reduced/sections/04_examples.md` "Sources and area", paragraph 2; `src/gwsource/prt.py`.
6. The particles deliver 799.9 of the 800 m³/d pumped (18,208 particles from 1,133 cells). This total says little about the area, because particles that conserve water must deliver what the well pumps. evidence: 01 §8, cell 24.
7. The areas. Cells with a particle share above 0.5 cover 1.168 km². The F > 0.5 area is 2.1 % smaller and leaves out 14 particle cells. The F > 0.1 area is 34.9 % larger and holds every particle cell. evidence: 01 §8, cell 24.
8. The trade-off. In the 372 cells with F between 0.05 and 0.95, the particle share and F differ by 0.164 on average (0.058 over all 1,133 release cells). In those cells most particles either reach the well or miss it, while full mixing gives the cell an in-between value. evidence: 01 §8, cell 24. The practitioner reading: the F > 0.5 area is close to the particle area in size, and the F > 0.1 area is a cautious outer limit on this model. Section 6 shows that this does not hold on every model.
9. The forward trace in one sentence. A forward trace from the recharge on a 300 m × 300 m field shows that 39 % of it reaches the well (Fig. 2c). evidence: `tutorials/03_forward/03_forward.ipynb` §6, cell 16 (45.0 m³/d, 17.7 m³/d to the well).

Figure: Fig. 2a and 2c. See Section 4 of this outline for a possible example figure ({SI: contributing area against particle tracking} promoted).

#### Example B. How much of the pumped water is already in the aquifer? (about 650 words; notebook 08, with 05 as the contrast and 10 as the external check)

**Purpose.** A manager may ask how much of the water pumped over the coming decades is already in the aquifer today, and how the answer changes once seasonal storage is followed through time. Snapshots cannot answer this, and the example shows why.

**What moves in.** `draft_reduced/sections/04_examples.md` "Transient tracking" (both paragraphs), and from `si/G_examples.md` "Transient tracking", "The contributing area through the seasons" and "A new well's source mix".

Points in order:
1. The model. The example model made transient, with seasonal recharge (factors 1.8, 1.0, 0.1, 1.1) and pumping (640–1,120 m³/d) over the wet, wet-to-dry, dry and dry-to-wet seasons. evidence: `tutorials/05_transient_snapshots/05_transient_snapshots.ipynb` cell 4; `tutorials/herebedragons.py` SEASON_RECHARGE, SEASON_PUMPING.
2. The contrast: what snapshots show. In seasonal snapshots the F > 0.5 area grows from 0.59 km² in the wet season to 1.35 km² in the dry season. evidence: 05 §3, cell 6. In the dry season, 52.5 % of the well's water comes from storage in the snapshot. evidence: 05 §4, cell 9 (dry storage 0.525). That storage water is of unknown origin, so the snapshot cannot say whether it is old water or last season's recharge.
3. Snapshots also give nested zones (Fig. 2e: inner 0.52 km², seasonal 0.93 km², ring 0.41 km²). One sentence only, with a pointer to Table 1 row 05. evidence: 05 §7, cell 21.
4. Transient tracking on the 30-year run, one step per season (121 steps), porosity 0.3. The run starts from a steady state in which the well already pumps, so initial water is not water from before pumping began. evidence: `tutorials/08_transient_tracking/08_transient_tracking.ipynb` Settings and §1.
5. Averaged over time, snapshots give the well's water as about 60 % recharge and 15 % storage release. evidence: 08 §3, cell 8.
6. With transient tracking, the well's water in the last season of year 30 is 51.6 % initial water, 32.9 % recharge and 15.5 % river water. evidence: 08 §3 table. Of all the water pumped in the first 10 years, 81 % was initial water (98 % in year 1, 68 % over 30 years). evidence: 08 §4 table (0.976, 0.813, 0.677).
7. Why so much old water. A column of this aquifer holds about 64 years of recharge, so new recharge mixes into a large volume of older water. evidence: 08 §3 (water column 11.4 m, recharge 0.18 m/yr). With one layer, the model cannot hold young water above old water, so a layered model may give other shares. Keep this caveat.
8. Backward tracking in time. Only the water near the well and along the main flow path reaches the well within 30 years (Fig. 2f). Most of the water in the steady-state contributing area is still on its way at the end. evidence: 08 §5, cells 14 and 15 (read off the maps). Of the 8.77 million m³ pumped, backward tracking attributes 67.7 % to initial water, matching the forward share. evidence: 08 §5, cell 16; `si/G_examples.md` "Transient tracking".
9. Check against GWT. With GWT's water volumes and one transport step per flow step, transient tracking matched a GWT run with tagged recharge to 9.8 × 10⁻¹⁴ in every cell and step. evidence: 08 §8, cell 22. Say that this is a consistency test, because both codes solve the same equations.
10. The default volumes. The code's default water volumes keep every cell's water balance exact. Here they change the fractions by less than 0.004 (1.9 × 10⁻⁴ in c, 3.7 × 10⁻³ in w). evidence: 08 §7, cell 20. Transport sub-steps: the main runs use four, because long steps make new water arrive too early (first step 0.0078 with one step against 0.0042 with 16). evidence: 08 §9, cell 24. One or two sentences, with the detail in the SI.
11. The external check against a published transient study. Bedekar et al. (2024) used the unit-concentration method, with MODFLOW-2005 and MT3D-USGS, to show how a new well's water changes from stored water to water from its sources. The rebuilt model and one forward tracking run with four tags give the well's water at year 25 as 48.2 % lateral inflow, 29.2 % recharge and 22.5 % stream water, against the published 48 %, 29 % and 23 %. evidence: `tutorials/10_unit_concentration/10_unit_concentration.ipynb` §2 table; Bedekar et al. 2024 p. 306.
12. Over 15 times read off the published Figure 2, the largest difference is 1.3 percentage points, on the lateral-inflow front at year 10. Transport sub-steps of 7.6 days bring it to 0.6 percentage points over the first 15 years. The read-offs are good to about one percentage point. evidence: 10 §4 and §6, cell 16.
13. One tracking run replaces four transport runs, one per source. Four MODFLOW 6 GWT runs give the same fractions to 1.5 × 10⁻¹⁰. evidence: 10 §3. Backward tracking adds the time-limited contributing area: 841 cells of layer 2 within 1 year, 6,825 within 25 years, close to the 6,829 cells of the steady-state F > 0.5 area. evidence: 10 §7, cell 18. Keep the hedge "we expect that a forward unit-concentration model would need one run per zone" from `si/G_examples.md`.
14. Limits in one or two sentences: every step must be saved, porosity is needed, and memory grows with the number of steps. Tested on synthetic models only. evidence: `draft_reduced/sections/06_tradeoffs.md` paragraph 3.

Figure: Fig. 2e and 2f. See Section 4 of this outline for a possible example figure for B.

#### Example C. Where does the well's water come from by source, and how old is it? (about 450 words; notebooks 01 §6, 06 and 07)

> **Decided (2026-10-19).** The author confirmed this reading: one worked example on a sink's water split by source and by travel time, checked against the closure check and PRT mean travel times.

**Purpose.** Many studies need the integral answers more than the edge of an area. How much of the well's water is river water? How old is the water from each source? These answers depend much less on mixing than the edge does, which makes them the outputs a practitioner can use with most confidence.

**What moves in.** `draft_reduced/sections/04_examples.md` (the travel-time and stream paragraphs of "Further examples"), and from `si/G_examples.md` "Mean travel time", "Where each source's water goes" and "Streams, drains and linked models".

Points in order:
1. The split by source. The 800 m³/d pumped is 71 % recharge, 15 % inflow at the west edge and 14 % river leakage (Fig. 2b). evidence: 01 §6, cell 20 (568.6, 118.1, 113.3 m³/d). The closure check holds (point A4).
2. The forward trace gives the same split from G in the well cell (0.711, 0.148, 0.142). The forward and backward volumes from each source agree within 1 × 10⁻⁶ m³/d, and the difference equals the cell budget error term of the forward–backward check. evidence: 03 §3, cell 10 and §7, cell 18 (2.8 × 10⁻⁹ to 4.7 × 10⁻⁷ m³/d).
3. The split depends on where the trace stops. Introduce the stream-network variant of the model (a stream fed by drains through the water mover). With stream reaches left as source terms of the aquifer cells, stream leakage supplies 32 % of the well's water (255.2 m³/d). With the reaches traced as cells, that water splits into 129 m³/d of upstream stream inflow and 126 m³/d of recharge that reached the stream through the drains. evidence: `tutorials/07_networks_multimodel/07_networks_multimodel.ipynb` §2 (share 0.319) and §3 (SFR:EXT-INFLOW 129.4; RCH +125.8 m³/d). Closure holds both ways (relative error 1.4 × 10⁻¹⁶ and 0.0). evidence: 07 §3. Note for the writer: this is a different variant of the example model from points 1 and 2, and the text must say so.
4. The practitioner reading. The answer to "how much is stream water?" depends on whether streams are traced as cells, so a study should report which choice it made.
5. Travel time by source, porosity 0.3. Mean travel times to the well cell: river leakage 2.1 years, recharge 41.6 years, west edge 108.4 years, all water 45.9 years. evidence: `tutorials/06_travel_time/06_travel_time.ipynb` cell 16 output. Fig. 2d maps the mean travel time where F > 0.5.
6. Check against weight-losing PRT particles. All water: 45.7 against 45.9 years (−0.5 %). By source: recharge −2.1 %, west edge +2.1 %, river −20.1 %. evidence: 06 cell 20 output.
7. Keep the caveat. The overall agreement is not an independent test, because in both methods the mean travel time of all the water is close to the volume of water that will end at the well divided by the pumping rate (Eq. 7), and that volume is nearly the same in both. evidence: 06 §5 (identity, relative error 0.0); `si/G_examples.md` "Mean travel time".
8. The informative comparison is cell by cell. In the 456 cells with F ≥ 0.5 (the well cell left out), the median ratio of particle time to full-mixing time is 0.96. In the 676 cells with F < 0.5, it is 5.72. A particle from such a cell follows one slow path around the edge of the area, while full mixing averages over all the paths that the cell's water takes. evidence: 06 cell 22 output.
9. Time-of-travel zones. The 25-year zone is 0.455 km² under full mixing and 0.465 km² for particles (+2.2 %). The 5-year zone is 0.098 against 0.122 km² (+25.6 %). evidence: 06 cell 24 output. The practitioner reading: short time-of-travel zones need particles (Section 6).
10. Supporting evidence from the dispersion study, one sentence: on its test problems the shares by source were the same to three digits under mixing, face routing and particles. evidence: `docs/dispersion_study.md` Summary, third bullet.

Figure: Fig. 2b and 2d.

#### Table 1 and its paragraph (about 450 words including the table text)

**Purpose.** Give the reader the full set of questions the code answers, what each notebook checks and how well, and where to find it. The paragraph before the table says that each notebook ships with the code (Section 7) and runs in seconds to about a minute.

Draft rows. Numbers come from the notebooks' stored outputs. Cell references are to the notebook cells as stored. The column "Fig. 2" gives the gallery panel, if any.

| Notebook | Question | Output | Checked against | Agreement | Fig. 2 |
|---|---|---|---|---|---|
| 01 | Where does a well's water come from? | F map, F > 0.1 and F > 0.5 areas (1.575 and 1.143 km²), the well's water by source | Closure check; weight-losing PRT particles | Closure error 0.0. Particles deliver 799.9 of 800 m³/d. Particle area 1.168 km², F > 0.5 area 2.1 % smaller, F > 0.1 area holds every particle cell. Mean difference of F and particle share 0.164 in 372 edge cells. evidence: 01 §5 c16, §7 c22, §8 c24 | a, b (example A) |
| 02 | What is computed, and what changes at a weak sink? | Gross and net accounting, boundary-control map | The published worked example of Foley and Black (2013); boundary-control check | Published example reproduced to 1 × 10⁻¹⁴. Fractions to all sinks add up to 1 within 1 × 10⁻¹⁵. At a small well, net accounting attributes 33.7 m³/d against the 5 m³/d pumped (6.7 times). evidence: 02 §2 c7, c9; §3 c13, c15; §5 c26 | – (Fig. 1) |
| 03 | Where does a source's water go? | G maps, fate of field recharge (39 % to the well) | GWT unit concentration at equilibrium; forward–backward check | G and GWT agree to 4.2 × 10⁻¹³ in all 1,600 cells. Forward and backward volumes agree within 1 × 10⁻⁶ m³/d. evidence: 03 §6 c16, §7 c18, §9 c24 | c (example A) |
| 04 | Does it work on my grid? | The same trace on DIS, Voronoi DISV and DISU grids; flow loops with XT3D | DIS against DISU; block solve against a plain sparse solve; DISV against DIS | DISU equals DIS in every cell. Block and plain solves agree to 3.3 × 10⁻¹⁶. On DISV the expected area is 1.178 against 1.173 km² (+0.4 %), but the edge is wider (186 against 121 m, 215 m on squares turned 45°). evidence: 04 §4 c15, c20, c22, c25; §6 c37 | h |
| 05 | How does the area change through the seasons? | Seasonal snapshots of F; nested zones (0.52, 0.93 and 0.41 km²) | Statistics recomputed from the stored steps; closure in every snapshot | Statistics agree to 1 × 10⁻¹⁴. Every snapshot closes within 1 × 10⁻⁶ m³/d (largest 7.2 × 10⁻⁷). evidence: 05 §4 c8, §7 c21, §8 c25 (assert atol 1e-14) | e (example B) |
| 06 | How old is the water reaching the well? | Mean travel time map, 5- and 25-year zones, age by source | Weight-losing PRT particles; travel-time closure check | All water 45.7 against 45.9 years (−0.5 %), not an independent test. River −20.1 %, recharge −2.1 %, west edge +2.1 %. Median particle-to-full-mixing ratio 0.96 where F ≥ 0.5 and 5.72 where F < 0.5. evidence: 06 c14, c16, c20, c22, c24 | d (example C) |
| 07 | What if water passes through streams, drains, wells or linked models? | Stream reaches and the mover traced as cells; a multi-aquifer well; a model split into three | Closure check; the same model unsplit | Stream share 32 % with reaches as source terms, traced back to upstream inflow and recharge with reaches as cells. Closure error 1.4 × 10⁻¹⁶ and 0.0. Split and single models agree to 2.1 × 10⁻¹³ in F. evidence: 07 §2, §3 c20, §5 c33 | – (example C) |
| 08 | How much of the pumped water was already in the aquifer? | The well's water by origin through time; backward fate maps | GWT with tagged recharge; transient forward–backward check; tagged-water balances | GWT to 9.8 × 10⁻¹⁴ over 1,600 cells and 121 steps. Forward and backward volumes to 4.3 × 10⁻¹⁶. Tagged-water balances to 9.9 × 10⁻¹⁶ [check: the SI table gives 8.0 × 10⁻¹⁶]. evidence: 08 c12, c18, c22; `si/G_examples.md` table | f (example B) |
| 09 | How sure are we? | Probability of contribution from 50 realisations, before and after history matching with PEST++ IES | A synthetic true model; exact against histogram quantiles; serial against parallel runs | The band where the probability lies between 0.1 and 0.9 narrows from 1.10 to 0.35 km². The posterior gives a probability of at least 0.5 to 93 % of the true F > 0.5 area (prior 79 %). Of the cells with a probability of at least 0.9, 86–87 % lie in the true area, and that share did not improve. Serial and parallel runs bit-identical. evidence: 09 c18, c28 | g |
| 10 | Does it reproduce a published unit-concentration study? | The well's water by source over 25 years; time-limited contributing areas | Bedekar et al. (2024), Figure 2; four GWT runs | Within 1.3 percentage points of the published curves (0.6 with 7.6-day sub-steps). 48.2, 29.2 and 22.5 % at year 25 against the published 48, 29 and 23 %. GWT to 1.5 × 10⁻¹⁰. evidence: 10 §2, §3, §4, §6 c16 | – (example B) |

Notes on the table:
- Row 09 must keep its caveat that a narrower posterior is not necessarily a correct one, and that one synthetic case cannot show how reliable posteriors are in general. evidence: `draft_reduced/sections/04_examples.md` (Ensembles, last paragraph). The text paragraph, not the table cell, may be the better place for it.
- Fig. 2g (posterior probability) stays in the gallery. With the ensemble example gone, its caption needs one sentence on what a posterior realisation is, or a pointer to row 09.
- A run-time column is possible. Stored run times: 01 4 s, 02 2 s, 03 1 s, 04 7 s, 05 2 s, 06 4 s, 07 3 s, 08 10 s, 09 71 s (with PEST++ IES, 61 s of it). evidence: the last output cell of each notebook; 09 c26. Notebook 10 prints no total [check: the README gives about 2.5 min].
- Row 04: the reference method's deletion of the smallest flow in each loop changes F by up to 0.155 under net accounting. evidence: 04 §6 c39. This fits in the row only if the writer frames it politely as a difference of approach, so it may stay in the SI.

### 3.5 A regional model: Neversink (about 550 words)

**Purpose.** Show that the method works and scales on a real, published regional model, and explain why its areas differ from the published particle areas. The practitioner needs both: the cost tells them whether the tool fits their workflow, and the explanation tells them how to read a full-mixing area next to a particle area.

**What moves in.** From `docs/neversink_study.md` "Reproducing" (PRT run times) and §3 (source split along particle paths), and from `draft/reviews/r4_memory.md` (memory). From `si/D.md`, the net-accounting overlap and the 227 m³/d of missed particle water, if space allows.

Points in order:
1. The model. The USGS Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022) is steady state, with 4 layers of 680 × 619 cells of 50 m (1,683,680 cells) and 12,316 SFR reaches. Eight priority wells pump 3,671 m³/d. Its 358 realisations come from history matching with PEST++ IES. evidence: `docs/neversink_study.md` §1; `si/D.md`.
2. The benchmark. The published study mapped the wells' contributing areas with MODPATH 7, one particle in the uppermost active cell of each column near the wells (122,021 start cells). 980 start cells send their particle to a priority well. evidence: NS §1, §2.
3. Cost of the trace. One trace of nine destination groups (each well alone and all eight together) took 2–3 s, of which about 1 s is reading the budget file. Peak memory was 2.5 GB. evidence: NS Summary "Cost"; `draft/reviews/r4_memory.md`.
4. Cost of PRT on the same flows. PRT runs that write only where each particle ends took about 30 s each (published start cells, one particle each). PRT with full particle tracks took about 5 min for 122,112 particles released at one height and about 13 min for 488,448 particles released at four heights. Their track files were about 1.5 GB and 6 GB. evidence: NS "Reproducing". PRT memory was not measured [check: measure it, or leave memory out of the comparison].
5. A fair-comparison caveat. One PRT run gives one particle convention for all wells together. The trace gives F for every group, the volumes and the checks in one run. The weight-losing PRT runs were seeded from the 30,180 cells with F > 10⁻⁶, so they needed the trace first. evidence: NS §3. The writer should say what the comparison does and does not show, in one sentence.
6. Closure held to 1 × 10⁻¹² m³/d or better for every group. evidence: NS §1 "Checks".
7. Across the ensemble, two traces per realisation took about 9 s, and closure held to 3 × 10⁻¹² m³/d in every realisation. Mean F over the realisations correlates with the published probability of contribution at r = 0.80. Its expected area is 0.90 times the published one. evidence: NS §6 "Runs"; `si/D.md` "The ensemble".
8. Why the areas differ (prose, about 250 words, as in the reduced draft's Section 5 with its connecting sentences restored):
   - The overlap score: cells in both areas divided by cells in either. evidence: NS §2.
   - The published area is one reasonable choice of particle settings. PRT on the same flows reproduces it (overlap 0.998) only with all three published settings (top-face recharge and stream flows, stopping at weak sinks, draping). Among particle runs that conserve water, the settings alone move the overlap from 0.62 to 0.998. evidence: NS §3 reproduction table; `si/D.md` table.
   - Full-mixing overlaps are 0.41 (F > 0.5) and 0.30 (F > 0.1). We infer that the main reason is that full mixing splits each cell's water among all its outflows, while a particle follows one path. The published cells send 42 % of their water to the wells on average. The F > 0.1 area holds 73 % of them (711 of 980). evidence: NS §2, Table 1.
     - [Deferred 2026-10-19, may follow up later. Keep the sentence as a marked inference for now. Author comment: "surely we could design a test example to validate this inference?"] Options:
       1. Restate it as a measured split using existing runs. The thinned PRT run (`prt_volume_thin1`) uses the same flows and the same weak-sink shares as full mixing, so the only difference is mixing between sinks. Published against thinned PRT gives an overlap of 0.62, which is the particle settings. Thinned PRT P > 0.5 against F > 0.5 gives 0.56, which is the mixing. Published against F > 0.5 gives 0.41, which is both. The mean |F − P| is 0.025 to 0.027. evidence: NS Table 3, Table 3a. Caveat: PRT was seeded only where F > 10⁻⁶.
       2. A synthetic test that isolates mixing: a well and a gaining stream in uniform flow, with a water divide between them, run on a grid aligned with the flow, the same grid rotated, and finer grids. Measure the share of particle-area cells with F < 0.5 and the width of the band. Mixing predicts a band that narrows with cell size and widens on the rotated grid. This extends `docs/dispersion_study.md` problem B.
       3. Face-to-face routing (the experimental prototype) on Neversink. If mixing is the cause, the overlap with the thinned PRT zone should rise.
   - Against weight-losing particles the F > 0.1 area holds 87 % of the 691 cells where those particles deliver more than half their water. The 89 missed cells supply 227 m³/d, 6 % of what the particles deliver. evidence: NS §5, Table 3a; `si/D.md`.
   - Weak sinks add to the difference. Published particles stop in buried stream cells (26,828 particles) and in five weak-sink wells (466 particles), where full mixing passes the rest of the cell's water on. Net accounting raises the F > 0.5 overlap only from 0.41 to 0.44. evidence: NS §2 "End states"; `si/D.md`.
   - Do not write that full mixing lies "within the range" of particle results. Among particle runs that conserve water, it lies below that range (0.30–0.41 against 0.62–0.998). The "inside that range" of NS §2 and its summary includes particles that lose weight only at wells, which do not conserve water.
9. The link to example C. With streams as cells, stream leakage supplies 43 % of the wells' water. With the stream network it all traces back to recharge. Along weight-losing particle paths the split is 49 % recharge and 51 % stream, against 57 % and 43 % under full mixing. evidence: NS Summary "Streams"; NS §3 (`prt_sources_by_well.csv`). This shows that on a regional model the split by source can differ between methods by several percentage points, even though the totals agree. Mark the reason as inferred.

Figure: Fig. 4 (was Fig. 3) stays (F with the published cells, and F > 0.1 against the published cells). See Section 4 of this outline for a possible third panel.

### 3.6 Trade-offs and conclusions (about 400 words)

**Purpose.** Turn the results into advice and close with the five key messages. Open with the outcome, not a hedge.

Keep the reduced draft's Section 6 (`draft_reduced/sections/06_tradeoffs.md`), with these changes:
1. Open with a framing of the outcomes: the integral answers (a sink's water by source, mean travel time) depend much less on mixing than the edge of an area does (examples A and C).
2. The edge band. In two test problems, halving the cell size made the band only about 30 % narrower. On squares turned 45° to the flow the band was 1.8 times as wide. evidence: `docs/dispersion_study.md` Summary and §2; 04 §4 c20–c25.
3. The threshold, in one sentence and without prescribing values (author comment 2026-10-19: "very prescriptive; not sure i follow the value of including it"). No single threshold on F reproduces a particle area everywhere. The choice depends on what the area is for, so it is reported with the area (point 4). The numbers from the dispersion test problems (F > 0.5 within 5 % of the reference area, F > 0.1 missed at most 0.1 % and was 8 to 90 % larger) and the Neversink result that F > 0.1 is not a full envelope stay in the SI (Text S5) and Section 5. evidence: `docs/dispersion_study.md` Summary and §7; NS Table 3a.
4. What to report with an area: the threshold, the accounting and whether streams were traced as cells (example C point 4).
5. Limits of the code: transient tracking tested on synthetic models only, memory grows with time steps, movers between models (MVE) not implemented, no maps on DISU grids without vertices. evidence: reduced Section 6, paragraph 3.
6. When to use what: particles where a sharp edge or first arrival matters (example C point 9), GWT where dispersion, sorption or decay matter, full mixing for many sinks, unstructured grids, package networks and repeated runs.
7. Closing paragraph: the five key messages of Section 2 of this outline, in the same words as the abstract and impact statement. The reduced draft's closer "Full mixing suits questions about … many realisations" stays, because it is about speed, not about a worked example.

### 3.7 Code and data availability (about 100 words)

Unchanged from `draft_reduced/sections/07_availability.md`, with its four [check]s (public URL, release version and tag, Zenodo DOI, pinned MODFLOW 6 version). If Table 1 names the notebooks by file name, this section says once where they are.

## 4. Figures and tables

| Item | Status | Notes |
|---|---|---|
| Fig. 1, the eight-cell example | Stays, may change | It now carries gross and net accounting in Methods. Propose a second small panel or a caption sentence that gives net F = 1 in the well cell beside gross F = 6/11 = 0.55. `studies/paper/gallery_figure.py` make_method_single; `method_figures.py` draw_gross_net already draws a gross-and-net panel. |
| Fig. 1 panel (b): snapshot against transient tracking | Decided (decision 11) | Methods now explains transient tracking and backward tracking in time at length. A schematic would help. The full draft's Figure 1, panel (d), already draws one cell as a snapshot and the same cell carried through storage from step n to n + 1 (`studies/paper/method_figures.py` draw_transient). It could join Fig. 1 as panel (b), one column wide. |
| Fig. 2, the gallery | Stays | Panels a–h map onto examples A, B, C and Table 1 (see the Fig. 2 column). Caption: panel (g) needs a sentence on posterior realisations, now that the ensemble example is gone. |
| New Fig. 3, examples A and B | Decided (decision 12) | Examples A and B make claims the gallery cannot show: F against the particle share (A) and the well's water by origin through time against the published curves (B). One compact two-panel figure could hold the particle-share map ({SI: contributing area against particle tracking}, panel b) and the Bedekar curves with the read-offs ({SI: the unit-concentration example rebuilt}, panel a). The Neversink figure becomes Fig. 4. |
| Table 1, the ten notebooks | New | Section 3.4 of this outline. It is the first main-text table. |
| Fig. 4 (was Fig. 3), Neversink | Stays, may grow | Section 5 grows. Propose adding panel (c), the F > 0.1 area against the weight-losing particle area, from {SI: Neversink particle area and ensemble mean F}, panel (a), because point 8 of Section 3.5 quotes it. |
| Cost table for Neversink | Proposal, not decided | The trace and the four PRT runs of point 4 of Section 3.5, with time, number of particles and output size, could be a short table instead of prose. |

## 5. The SI after the move

- **Text S1, method in full** (`si/B.md`, 3,294 words). Shrinks to about a third. It keeps the solution of the linear systems, the details of net accounting (Eq. S9 and which cells are fixed), the matrix form and solution of each transient step (Eq. S13), the derivation of the transient forward–backward check (Eq. S15), the water volume options, transport sub-steps, and the travel time to where the water enters the sink cell. Everything else moves to Section 2. Its equation numbers change.
- **Text S2, software, verification and models** (`si/C.md`). Stays. The sentence comparing PRT and trace cost on Neversink moves to Section 5.
- **Table S2, inputs, selections and outputs.** Stays.
- **Figure S1, verification on the test models.** Stays.
- **Text S3, the worked examples in brief** (`si/G_examples.md`, 3,613 words). Shrinks. Its paragraphs "Sources and area", "Transient tracking", "Mean travel time" and "A new well's source mix" move into examples A, B and C. Its paragraphs on accounting, the forward trace, grids, seasonal snapshots, streams and linked models, and ensembles stay, because they back the rows of Table 1. The transient check table stays.
- **Figures S2–S5.** S2 (area against particles) and S5 (the unit-concentration example) move to the main text if the proposed example figure is accepted. Otherwise they stay. S3 (snapshots against transient tracking) stays. S4 (probability of contribution before and after history matching) stays and is now cited from Table 1 row 09.
- **Text S4, the Neversink comparison** (`si/D.md`). Stays. The ensemble timing moves to Section 5.
- **Figure S6, Neversink particle area and ensemble mean F.** Its panel (a) moves to Fig. 4 if that proposal is accepted.
- **Text S5 and Figure S7, numerical dispersion.** Stay.
- `si/numbering.md` needs a rebuild after the move. Labels are reassigned on every build.

## 6. Open questions for the author

All five were answered on 2026-10-19 (decisions 9–13 in Section 1.5). Example C stands as read. Table 1 names the notebooks by number. Fig. 1 gets the transient panel and Methods shows the backward-in-time equation. Examples A and B get a compact main-text figure. The MODFLOW 6 run time leaves the abstract and Section 3.

## 7. Numbers not found

- PRT memory on Neversink. `docs/neversink_study.md` gives PRT track-file sizes (about 1.5 GB and 6 GB) but no peak memory.
- A distance from the well to the far edge of the steady-state contributing area in notebook 01 (example A, point 2). The notebook prints areas and the source split, not a reach.
- The total run time of notebook 10. The notebook prints run times of its parts only (for example 15.1 s to build and run the model, 20.2 s for forward tracking, 28.4 s for four GWT runs). The README gives about 2.5 min.
- The tagged-water balance of notebook 08: the notebook prints 9.9 × 10⁻¹⁶ (cell 12), and the SI table in `si/G_examples.md` gives 8.0 × 10⁻¹⁶.
- The word count of the reduced draft: 4,043 words with comments removed, against the brief's about 2,550.
