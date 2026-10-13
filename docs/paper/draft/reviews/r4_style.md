# Round 4 review: sentence style (role `style`)

Scope: every sentence of the main text (`sections/00`–`09`) and the captions (`display/*.md`). Checked against the author's comments (`user_r3_comments.md`), the prose rules of `decisions_r3.md` §2–3 and voice-hugman. Line numbers are those of the round-4 files. Each paragraph is one line, so a line number points to a paragraph and the quote finds the sentence. British spelling is left to the copy edit.

**MUST** means the author has already objected to this kind of sentence, or a groundwater modeller would have to read it twice. **SHOULD** is a smaller gain. Every MUST has a rewrite.

## Overall

The round-4 text is much better than draft v6. Most of the long two-part sentences are gone. "tutorial" appears only in §9, and "core" appears nowhere. The section openers now usually say why the reader is there.

Splitting has created two new problems:

- **Packing has moved into appositives.** A sentence that used to be "X; Y" is now often "X, the Y of Z, does W". That is still two ideas in one sentence, and it is the most common problem left (pattern 1).
- **Some paragraphs have become staccato lists.** Examples are the abstract, 01:19, 02:81 and 08:3. Short sentences with no links read as a feature list. One idea per sentence does not ban "because", "so that", "but" or "where" inside a sentence. Use them to keep the logic visible.

**Word budgets.** Several sections are at or just over their caps, counting visible words without display equations:

| § | Words | Cap |
|---|---|---|
| 1 | about 1,050 | 1,050 |
| 2 | about 2,040 | 2,000 |
| 3 | about 510 | 500 |
| 4 | about 1,205 | 1,200 |
| 6 | about 1,360 | 1,350 |

Many rewrites below add a few words. Pay for them with the cuts this review also lists:

- repeated definitions (pattern 6);
- the duplicate purpose paragraph in §5 (05:3 against 05:25);
- §6.4, which repeats §5.4;
- the result numbers repeated in §6.3 and §6.5;
- the "In words:" fragments in §2.

---

## The five patterns that recur most (fix these across your files)

| # | Pattern | Count | Where most |
|---|---|---|---|
| 1 | **Appositive packing.** A definition or comment is pushed into an appositive ("X, the share of …, does Y"; "…, a spread that is not …"; "…, an error of …"), or a sentence is chained with appositives. This is the old two-part sentence in disguise. | about 40 | §2 (7), §4 (6), §5 (7), §6 (6), captions (5) |
| 2 | **Clause joins that make two-part sentences.** These are ", which …", ", whose …", ", of which …" and ", so …" tails that add a second claim, and colons or semicolons in running text. | about 25 | §1, §3.3, §5.1–5.3, Figs 5 and 7 |
| 3 | **Compression: labels the reader has not been given.** Examples: "trace" (never defined), "destination group" (used in §2.2, defined in §3.3), "flow"/"gwt" volumes, "expected area", "stream share", "release height", "steady limits", "net source", "bookkeeping", "upper bound", "test mixing like for like", "a benchmark, not a reference", "set a floor of about one cell", "travel lag". | about 18 | §2, §4.2, §5.3, §7, Fig. 3 |
| 4 | **Participle and absolute constructions.** Examples: "Traced backward from …", "Written for every cell …", "Mapped, they …", "Compared with full mixing, …", "Rerun with MODFLOW 6 …", "Changing only this setting, …", "Run backward in time, …", "…, storage release being …", "…, showing which …", "…, flow loops included". | 13 | §1, §2, §3.2, §5, §8, Fig. 1 |
| 5 | **The same paragraph move repeated.** Paragraphs open with a rhetorical question (4 of 6 in §5) or with an announcement ("Four families …", "Two further gaps remain.", "The fractions give volumes.", "Three outcomes frame this discussion.", "Five pieces of advice follow …"). They close on a "therefore" sentence (16 in the visible text) or on a "a user can …/tells a manager …" sentence (6). §2 has 9 "In words:" paragraphs, 2 of them fragments. | 4 + 7 + 16 + 6 + 9 | §2, §4, §5, §6 |

A sixth pattern costs words more than clarity:

- **(6) Re-definitions.** F is defined again in 01:9, 04:31, 05:17, 06:9 and Figs 3 and 6. Full mixing is defined in 00, 01:9, 02:5, 06:7 and 07:5. Snapshots are defined in 01:11, 02:73 and 06:21. Overlap is defined in 05:15, 06:11 and Fig. 7. Weak sink is defined in 01:7, 02:35 and 06:7.
- One reminder in §4.3 and one in §5.2 is what decisions_r3 item 24 asks for. The repeats in §6 can go. That frees about 120 words.

**How to fix each pattern:**

1. Give the definition its own sentence, before the sentence that uses it ("F is the share …. The F > 0.5 area holds …").
2. Split at the comma and restate the subject ("… stops in the first weak-sink cell it enters. That cell's sink is credited …").
3. Define the label once where it first appears, in plain words, or replace it with the plain words.
4. Make the actor the subject ("We reran the model with …"; "Full mixing can be traced backward from …").
5. Vary the openers and keep at most one rhetorical question per section. Cut the announcements and start with the content. Keep "In words:" after Eqs (2), (5), (6), (8) and (9), and drop it elsewhere.

---

## 00_front.md

**00:9 SHOULD.** "Open-source contributing areas for MODFLOW 6 wells in seconds, each checked against the water budget, including how much pumped water was already stored."
- Areas are not open source.
- The appositive chain packs three claims into a fragment (patterns 1 and 4).
- → "Open-source code maps the contributing areas of MODFLOW 6 wells in seconds and checks every result against the water budget." (If the stored-water point must stay: "… It also shows how much of the pumped water was already stored in the aquifer.")

**00:11 SHOULD.** "Protection zones around supply wells restrict activities on the land whose water reaches the well, its contributing area."
- "land whose water" is odd, and the definition is a tail appositive.
- → "Protection zones around supply wells restrict land use where water enters the ground and later reaches the well. This land is the well's contributing area."

**00:11 SHOULD.** "Particle tracking, the usual method, follows water along flow paths."
- Appositive. It also repeats "usually" from the sentence before.
- → "The usual method is particle tracking, which follows imaginary particles of water along their flow paths."

**00:11 MUST.** "Where a well or stream takes only part of a cell's water, a particle must stop or pass."
- Too compressed for the non-technical opener the author asked for. The reader does not know that a particle cannot split.
- → "A particle cannot split. Where a well or stream takes only part of the water in a model cell, the particle must either stop there or pass on."

**00:11 SHOULD.** "Full-mixing methods, such as MODALL and FlowSource (…), instead treat each cell as fully mixed."
- Circular: full-mixing methods treat cells as fully mixed.
- → "Full-mixing methods, such as MODALL and FlowSource (…), avoid this choice. They assume that the water in each model cell is fully mixed, so a well takes only its share of the cell's water."

**00:11 SHOULD.** "Shares are solved exactly, also where water circulates between cells."
- "also where" is awkward.
- → "The code computes the shares exactly, including where water circulates between cells."

**00:11 SHOULD.** "Every trace is checked against the water budget."
- "trace" is not defined for an abstract reader (pattern 3).
- → "Every result is checked against the model's water budget."

**00:11 SHOULD.** "In tests, traces met the budget checks and matched MODFLOW 6 transport to rounding error."
- Two claims.
- → "In tests, every result passed the budget checks. Results also matched MODFLOW 6 transport to rounding error."

**00:11 SHOULD.** "On a published regional model of 1.68 million cells, a trace takes 2–3 s. The full-mixing areas fall within the range …"
- The author asked "the point is we compared to Neversink? Plus it was faster?" Put the comparison first and the speed second, and say what the speed is compared with.
- → "We also tested the method on a published regional model of 1.68 million cells. Its contributing areas fall within the range that particle tracking gives under different particle settings. Each trace took 2–3 s, against 44 s for the flow model run."
- The abstract is at 250 words. Pay for this with the circular sentence above.

## 01_introduction.md

**01:3 SHOULD.** "Each zone is drawn from the well's contributing area, the land whose water ends at the well."
- Tail appositive (pattern 1). "land whose water" again.
- → "Each zone is drawn from the well's contributing area. This is the area where water enters the aquifer and later reaches the well."

**01:3 SHOULD.** "Such studies need the share of each cell's water that reaches the well. The answers must agree with the water budget."
- "Such studies need the share" jumps. "The answers" refers to no question.
- → "To draw these areas, a study needs to know how much of each model cell's water reaches the well. These shares must agree with the model's water budget. They must also be cheap enough to compute for every realisation."

**01:5 SHOULD.** "Four families of methods give these answers. … Full-mixing flow tracing works from the flows between fully mixed cells. … Adjoint and age methods work backward in time or on travel times."
- Announcement opener (pattern 5).
- Two of the four descriptions say how a method works but not what it gives, so the reader still has no bird's-eye view.
- → "Four families of methods can compute these shares. Particle tracking follows imaginary particles along flow paths. Full-mixing flow tracing assumes the water in each cell is mixed, and splits it among the cell's outflows. Transport with tagged water labels the water from one source and follows it through time. Adjoint and age methods solve transport equations backward in time, or for travel times. The next four paragraphs take each family in turn."

**01:9 MUST.** "Traced backward from a destination, such as a well, full mixing gives the backward fraction F: the share of a cell's water that ends there."
- Participle opener, plus a colon definition (patterns 2 and 4).
- "destination" is used here for the first time without a definition (pattern 3).
- → "Full mixing can be traced backward from a destination, the sink terms the user chooses, such as a well's pumping. This gives the backward fraction F of each cell. F is the share of the cell's water that ends at the destination."

**01:9 MUST.** "Traced forward from a source, such as recharge, it gives the forward fraction G: the share of a cell's water that came from it."
- Same construction, repeated in the next sentence.
- → "Full mixing can also be traced forward from a source, such as recharge. This gives the forward fraction G. G is the share of the cell's water that came from that source."

**01:9 SHOULD.** "The capture fraction is the share of a well's pumping supplied by changes in other budget terms, such as reduced stream discharge, from two runs with and without pumping (…). F is the share of each cell's water that ends at the well, from one run."
- The ", from two runs …" and ", from one run" tails (pattern 1). The contrast decision 12 asks for is there, but it is buried in the tails.
- → "The capture fraction is the share of a well's pumping that comes from changes in other budget terms, such as reduced stream discharge (Leake et al. 2010; Barlow et al. 2018). It is computed from two model runs, with and without pumping. F comes from one run. It says where the water the well pumps comes from, not how pumping changes the budget."

**01:11 SHOULD.** "McLane and Cecan (2009) showed that its fractions spread more widely on coarser grids, a spread that is not hydrodynamic dispersion."
- Tail appositive (pattern 1).
- → "… spread more widely on coarser grids. This spreading comes from the grid, not from hydrodynamic dispersion."

**01:11 SHOULD.** "As published, it handles three cases in its own way (Table 1)."
- Announcement (pattern 5). "in its own way" is vague.
- → "The published method makes a simplifying choice in three cases (Table 1)."

**01:11 SHOULD.** "It credits a weak-sink well with all the water passing its cell, which we call net accounting (Section 2.3)."
- ", which" tail (pattern 2).
- → "At a weak sink, it credits the well with all the water that passes through the well's cell. We call this net accounting (Section 2.3)."

**01:11 MUST.** "It traces each step of a transient model as a steady state, a snapshot, with nothing carried between steps."
- Appositive chain ("…, a snapshot, with …").
- → "For a transient model, it traces each time step as if the flows were steady. We call each such trace a snapshot. No water is carried from one step to the next."

**01:15 MUST.** "Hydraulic mixing cells step such fractions forward in stream cells (Partington et al. 2011), then overland cells (…) and aquifer cells (…)."
- The method is named before it is explained (pattern 3). "step such fractions forward" is jargon.
- → "The hydraulic mixing-cell method computes similar fractions, stepping forward in time on the flow model's time steps. It was developed for stream cells (Partington et al. 2011) and later extended to overland cells (Partington et al. 2013) and aquifer cells (Schilling et al. 2017; Nogueira et al. 2022)."

**01:15 SHOULD.** "For unit-concentration transport we read only the abstract of Bedekar et al. (2024)."
- This interrupts the paragraph between two statements about forward runs.
- Table 1, footnote 5, already says it. Cut it here, or move it to the end of the paragraph.

**01:17 MUST.** "These methods solve for concentrations in continuous transport, not water fractions on a flow model's time steps."
- Two noun stacks in a "not X" frame. A modeller cannot see why this is a gap.
- → "These methods solve a transport equation of their own. They do not work directly from the flows that a MODFLOW model has already computed for each time step."

**01:17 SHOULD.** "Two further gaps remain. No method in Table 1 checks that a source-to-destination volume is the same traced backward or forward."
- The announcement (pattern 5) and the noun stack (pattern 3).
- These gaps are not about adjoint methods, so they sit badly at the end of the adjoint paragraph. Move them to open 01:19.
- → "None of the methods in Table 1 checks that the volume of water moving from a source to a destination is the same whether it is traced backward or forward. We also found no published comparison of a full-mixing delineation with particle-tracked areas on a large real model."

**01:19 SHOULD.** The paragraph has 15 sentences in the form "X is Y (Section n)", and it reads as a feature list.
- Split it in two:
  - what is made exact and checked (exact solve, accounting, checks);
  - what is new in scope (all of MODFLOW 6, transient tracking, backward in time, speed).
- Open each half with the reason, for example "Three changes make the fractions exact and checkable."

**01:19 SHOULD.** "The fractions are solved exactly, flow loops included (Section 2.4)."
- Absolute construction (pattern 4).
- → "The code solves for the fractions exactly, including in flow loops, and deletes no flows (Section 2.4)."

**01:19 SHOULD.** "Every trace comes with two budget checks that must hold exactly (Section 2.5)."
- "trace" is never defined (pattern 3). Define it here.
- "two" conflicts with the "Three checks" of 02:51.
- → "A trace is one run of the method for a chosen set of sources or destinations. Every trace comes with checks that must hold exactly (Section 2.5)." Then keep the two sentences on what they test.

**01:19 SHOULD.** "Transient tracking carries tagged water through storage, as GWT does."
- The term is used before it is explained (pattern 3).
- → "For transient models, the code can also carry tagged water from one time step to the next through the water stored in each cell, as GWT does. We call this transient tracking."

**01:19 SHOULD.** "A trace of a 1.68-million-cell model takes 2–3 s (Section 5.1)."
- Noun stack.
- → "On a model of 1.68 million cells, one trace takes 2–3 s (Section 5.1)."

## 02_methods.md

**02:5 SHOULD.** "Every other budget term (recharge, wells, drains, river and SFR leakage, constant heads, storage) is kept separate, by package and boundary, as a source term (into the cell) or a sink term (out of it)."
- The definitions of source and sink term are packed into parentheses.
- → "All other budget terms, such as recharge, wells, drains, river and SFR leakage, constant heads and storage, are kept separate by package and boundary. A term that brings water into a cell is a source term. A term that takes water out is a sink term."

**02:9 MUST.** "In words: a cell's total inflow … The outflow of cell i through the destination's sink terms is d_i. Its inflow through the selected source terms is s_i."
- "In words:" after a definition is not needed (pattern 5).
- The new symbols d_i and s_i, and the first use in §2 of "destination" and "selected source terms", are hidden inside the "In words" paragraph. The author called the old definition of destination weird.
- → First paragraph: "A cell's total inflow I_i is the water from its neighbours plus its source terms. Its total outflow O_i is the water to its neighbours plus its sink terms. The difference r_i is the cell budget error. It is reported and never forced to zero."
- → New paragraph: "Each trace starts from the user's choice of terms. The destination is the sink terms traced to, such as the pumping of one well or of a group of wells. The outflow of cell i through them is d_i. The source is the source terms traced from, such as recharge over an area. The inflow of cell i through them is s_i."

**02:15 SHOULD.** "A contributing area rests on the backward fraction F_i, the share of the water leaving cell i that leaves the model through the destination."
- Appositive definition (pattern 1).
- → "A contributing area is drawn from the backward fraction F_i. F_i is the share of the water leaving cell i that later leaves the model through the destination."

**02:19 SHOULD.** "So F = 6/11 = 0.55 there and in the cells that drain only through it."
- Compressed.
- → "So F = 6/11 = 0.55 in the well cell. Cells whose water all flows through the well cell have the same F."

**02:21 SHOULD.** "Written for every cell at once, with P_ij = q_ij/O_i the outflow shares, Eq. (2) becomes"
- Participle opener (pattern 4).
- → "Let P_ij = q_ij/O_i be the share of cell i's outflow that goes to cell j. For every cell at once, Eq. (2) then becomes"

**02:25 MUST.** "… and D marks which sink terms belong to which destination group. In words: Eq. (2), for every cell and every destination group at once."
- "destination group" is used here but defined only in 03:15 (pattern 3).
- The "In words:" line is a fragment (pattern 5).
- → "… and D marks which sink terms belong to which destination group. A destination group is a set of sink terms traced as one unit, such as one well or all the supply wells together. Each column of F holds the fractions to one group, so one solve gives every group."

**02:31 SHOULD.** "In words: the same rule, run downstream with inflow shares."
- Fragment (pattern 5). The sentence before it already says this. Cut it.

**02:31 SHOULD.** "The fractions give volumes. Of the water passing through cell i, … Of the water entering … Of the water leaving …"
- A short announcement, then three sentences in the same frame, tacked onto the G paragraph.
- Start a new paragraph that says why it matters: "Multiplying a fraction by a flow gives a volume of water. These volumes are what the checks of Section 2.5 add up." Then keep the three sentences.

**02:35 SHOULD.** "Under gross accounting, our default, each sink term takes its share of the cell's total outflow."
- Appositive (pattern 1).
- → "Our default is gross accounting. Each sink term then takes its share of the cell's total outflow."
- Also, "weak sink" is defined here as a sink term, but in 01:7 as a cell. Make them agree.

**02:37 MUST.** "It uses the cell-to-cell flows only, with each cell's net source (cell-to-cell outflow minus inflow) in place of its source and sink terms."
- A new term in a "with" tail. A modeller would read it twice.
- → "It works from the cell-to-cell flows only. Each cell's source and sink terms are replaced by one net term, equal to the cell's cell-to-cell outflow minus its cell-to-cell inflow."

**02:37 SHOULD.** "The destination cells are fixed at F = 1 (…)."
- Say why.
- → "The destination cells are fixed at F = 1, so all the water that passes through them counts as reaching the destination ({SI: net accounting, fixed cells})."

**02:37 SHOULD.** "It credits the well with its 6 m³/d of pumping plus the 5 m³/d that flow on to the river."
- Decision 19 asks for the contrast. Add: "Gross accounting credits only the 6 m³/d it pumps."

**02:39 SHOULD.** "The gap grows with the flow past the sink."
- "gap" has no referent.
- → "The difference between the two grows with the flow that passes the sink."

**02:39 SHOULD.** "Gross accounting gives F = 0.15 in the well cell and credits the pumping."
- Two claims, and the second is vague.
- → "Gross accounting credits the well with its 5.0 m³/d. F in the well cell is then 0.15."

**02:43 MUST.** "Where water moves between cells in one direction only, the cells can be put in flow order, each after the cells its water flows to."
- The tail "each after the cells its water flows to" is hard to parse.
- The paragraph does not say why the reader needs flow order.
- → "Equation (2) gives a cell's F from the F of the cells downstream of it. If water never returns to a cell it has left, the cells can be sorted so that each cell comes after every cell its water flows to. The equations can then be solved one cell at a time …"

**02:45 SHOULD.** "Loops arise with the XT3D (extended three-dimensional) option of MODFLOW 6 (Provost et al. 2017) and where stream reaches and aquifer cells exchange water both ways."
- Says where loops occur but not why, which decision 14 asks for.
- → "Loops are common with the XT3D option of MODFLOW 6 (Provost et al. 2017), which can give small flows against the main gradient between neighbouring cells. They also occur where stream reaches and aquifer cells exchange water in both directions, and around well pairs [check: mechanism wording with B]."

**02:47 SHOULD.** "Such loops are found beforehand, given F = 0 and reported."
- The reason is missing.
- → "Water in such a loop never leaves it, so its F is 0. The code finds these loops before the solve and reports them."

**02:47 SHOULD.** "Numerically, the solve is a block-triangular sparse LU factorisation … The matrix is therefore an M-matrix. Its factorisation needs no pivoting (reordering for numerical stability). Under gross accounting, one factorisation serves every destination group."
- Four technical sentences with no plain lead-in. "M-matrix" is not explained.
- Decision 15 keeps one technical sentence, introduced plainly.
- → "In linear-algebra terms, the solve is a block-triangular sparse LU factorisation, with each flow loop as one block. Because each cell's outflow shares add up to at most 1, the factorisation is stable without reordering. Under gross accounting, one factorisation serves every destination group, which keeps the cost of extra groups small (Section 3.3)."

**02:51 SHOULD.** "Three checks, which must hold exactly in any model, tell the user whether a trace is right."
- ", which" insert (pattern 2).
- → "Three checks tell the user whether a trace is right. Each must hold exactly in any model, because each follows from adding up the cell equations."

**02:55 SHOULD.** "In words: the water entering through every source term, weighted by its share that reaches the destination and corrected by the cell budget errors, adds up to the destination inflow."
- The participle chain sits inside the subject.
- → "In words: take the water entering through every source term and weight it by its F. After a correction for the cell budget errors, the total equals the water that leaves through the destination."

**02:55 SHOULD.** "The forward closure check, ∑…, is its mirror image."
- Equation as an appositive.
- → "The forward closure check is its mirror image: …" (the colon here introduces an equation, which is fine).

**02:59 SHOULD.** "It holds because Eqs (3) and (4) mirror each other (a duality)."
- "(a duality)" adds a term for no gain. Cut it.

**02:59 SHOULD.** "Mapped, they show each cell's share going to each sink (boundary-control maps)."
- Participle opener (pattern 4), and a coined label in parentheses.
- → "Maps of these fractions, called boundary-control maps, show which sinks each cell's water goes to."

**02:61 SHOULD.** "Because the flow model's budget error enters each check through r_i, a failed check points to the tracing itself. A budget term that was not read shows up instead as a large cell budget error."
- Compressed. "instead" is unclear.
- → "The checks include the flow model's budget errors r_i. A failed check therefore points to an error in the tracing, not in the flow model. A budget term the code failed to read shows up differently, as a large cell budget error."

**02:65 MUST.** "With V_i the water volume of a cell (porosity times saturated volume) and τ_i = V_i/O_i its mean residence time, the mean travel time from entering cell i to leaving the model through the destination is m_i/F_i, where"
- Two definitions packed in front of the main clause. This is the densest sentence in §2.
- → "Let V_i be the volume of water in cell i, which is porosity times saturated volume. Water stays in the cell for a mean time τ_i = V_i/O_i, its residence time. The mean travel time from entering cell i to leaving the model through the destination is then m_i/F_i, where"

**02:69 SHOULD.** "Because they are means over mixed water, they should not be used alone to draw a time-of-travel zone (Section 6.5)."
- "means over mixed water" is compressed.
- → "A mean travel time averages fast and slow water that have mixed in the cells. The first water can arrive much earlier. A mean travel time should therefore not be used alone to draw a time-of-travel zone (Section 6.5)."

**02:73 SHOULD.** "Snapshots show each step's flow paths. They have no travel time. The water released from storage has no known origin."
- Staccato, with the links lost.
- → "Snapshots show where each step's water goes under that step's flows. They give no travel times. Nor do they say where the water released from storage came from."
- Then end the paragraph on the number: "… up to 50 % of the well's water in summer, so in summer half of the well's water has no known origin."

**02:75 SHOULD.** "Transient tracking, the extension used here, carries tagged water through storage from step to step (Fig. 1d, right)."
- Appositive (pattern 1).
- "tagged water" is not defined in §2.
- → "Transient tracking is our extension. Water from the chosen sources is tagged, as a tracer would be, and carried through storage from step to step (Fig. 1d, right)."

**02:81 MUST.** "The scheme is implicit, … No dispersion is added. The scheme runs on the flow model's own time steps. The budget of every step must therefore be saved (…). The water volume needs porosity. MODFLOW's cell budget never balances exactly. The small error r_i is allowed to leave each cell carrying that cell's own mix of water. GWT handles the error the same way, as its flow-error correction (Langevin et al. 2022)."
- This paragraph is nine staccato statements on three topics, with no opener saying why the reader is there.
- The last sentence is the one the author called "Not clear" in v6. It still ends on an appositive tail.
- Split it into three short paragraphs:
  - → "The numerical scheme follows GWT. It is implicit, with outflows at the cell's mix at the end of the step. It is upstream weighted, with inflows at the mix of the cell they come from. No dispersion is added."
  - → "The user must supply two things. The scheme runs on the flow model's own time steps, so the budget of every step must be saved (SAVE BUDGET ALL in the Output Control (OC) file). The water volume of each cell needs a porosity."
  - → "MODFLOW's cell budget never balances exactly, and each cell has a small error r_i. We let this error leave the cell carrying the cell's own mix of water. GWT treats the error in the same way, which Langevin et al. (2022) call the flow-error correction."

**02:83 SHOULD.** "Initial water, the water in the model at the start of the simulation, can be tagged as its own group."
- Appositive definition.
- → "The water already in the model at the start of the simulation can be tagged as its own group, called initial water."

**02:83 MUST.** "The default "flow" volumes start at porosity times saturated volume and are then carried by the storage flows. … With the "gwt" volumes, porosity times saturated volume at the end of each step as in GWT, forward transient tracking is unit-concentration transport in GWT (…). But where porosity differs from specific yield, tagged water appears or disappears at step boundaries (Section 4.4)."
- Two labels arrive with no opener (pattern 3).
- An appositive chain defines "gwt" (pattern 1).
- The reader is not told why the two options exist or why tagged water would appear.
- → "The code offers two ways to set each cell's water volume. In the default, called "flow", each volume starts at porosity times saturated volume and then changes only by the storage flows of the flow model. Every cell's water balance and tagged-water balance then close exactly. In the "gwt" option, the volume is reset to porosity times saturated volume at the end of each step, as in GWT. Forward transient tracking with this option is unit-concentration transport in GWT (Bedekar et al. 2024; Langevin et al. 2022). Where porosity differs from specific yield, though, the reset volume does not match the storage flows. Tagged water then appears or disappears at step boundaries (Section 4.4)."

**02:83 SHOULD.** "Forward transient tracking is not new (Section 1; Table 1). What we add is backward tracking in time."
- This is good, but it is the opener §2.8 needs. Move it to the start of 02:87.

**02:87 MUST.** "Its result, the backward fraction in time w_i^n, is the fraction of the water in cell i at the start of step n, or entering it during the step, that leaves through the destination before the end of the simulation."
- An appositive name, then an inserted clause inside a long definition. A modeller reads it twice.
- → "The result is the backward fraction in time, w_i^n. Take the water in cell i at the start of step n, together with the water that enters the cell during the step. w_i^n is the share of that water that leaves through the destination before the simulation ends."

**02:87 SHOULD.** "It is solved from the end of the simulation back to the start, each step with the forward step's equations transposed (inflow and outflow swap roles)."
- Absolute construction (pattern 4).
- → "The code solves it one step at a time, from the end of the simulation back to the start. Each step uses the forward equations with the roles of inflow and outflow swapped."

**02:89 SHOULD.** "With w, they add up to 1, less the flow-error correction and, with "gwt" volumes, the step-boundary adjustments."
- Compressed.
- → "Together with w, these fractions add up to 1. The only departures are the flow-error correction and, with the "gwt" volumes, the water created or lost at step boundaries."

**02:89 SHOULD.** "This split tells a manager how much of the water a sink took was already stored at the start (Section 4.4)."
- This is the fourth "tells a manager / a manager can see" (pattern 5).
- → "From this split, a sink's water that was already stored at the start can be read directly (Section 4.4)."

**02:93 SHOULD.** "… equals each step's tagged inflow and the tagged initial water, each times its fraction that later reaches the destination (backward)."
- "each times its fraction" is compressed.
- → "… equals the sum of each step's tagged inflow and the tagged initial water, each multiplied by the fraction of it that later reaches the destination (backward)."

## 03_implementation.md

**03:5 SHOULD.** "The code reads only MODFLOW 6 output (Langevin et al. 2017)."
- Say why the reader cares.
- → "The code needs only the output of a MODFLOW 6 run, not its input files (Langevin et al. 2017)."

**03:5 SHOULD.** "The GWF budget files give the flows, saved with SAVE_FLOWS and, in the Output Control (OC) file, SAVE BUDGET ALL."
- A participle tail with an inserted phrase. OC is already defined at 02:81.
- → "The flows come from the GWF budget files. The user saves them with SAVE_FLOWS in each package and SAVE BUDGET ALL in the OC file."

**03:5 SHOULD.** "The GWF and package budgets must agree on each aquifer exchange, by default to 1 × 10⁻⁴ of the largest exchange."
- Compressed, and the purpose is missing.
- → "For each exchange between a package cell and the aquifer, the code checks that the GWF budget and the package budget give the same flow. By default they must agree to within 1 × 10⁻⁴ of the largest exchange."

**03:9 SHOULD.** The paragraph joins three unrelated items: selections, snapshot statistics and sub-steps. Give it an opener ("The user chooses what to trace and what to keep.").
- "running statistics such as time-weighted means" needs a "why" in a few words.

**03:9 SHOULD.** "Each flow step can be split into equal transport sub-steps, which stop tagged water from arriving too early when flow steps are long (…)."
- ", which" tail (pattern 2). The mechanism is not said.
- → "With long flow steps, tagged water can arrive too early, because the implicit scheme lets it cross the model faster than the flow would carry it [check wording with C]. Each flow step can therefore be split into equal transport sub-steps ({SI: …})."

**03:11 MUST.** "Particles start from every source term, each with a weight, the share of that term's flow it represents. Particle sums are then volumes of water."
- Appositive chain (pattern 1). The author said weight-losing particles were not explained.
- → "Particles start where water enters the model through a source term. Each particle carries a weight, which is the flow of water it represents. Adding up the weights of particles therefore gives a flow of water."

**03:11 MUST.** "In each cell a weight-losing particle passes, it loses the share of its weight that the cell's sinks take."
- The relative clause comes first ("In each cell a … particle passes, it …"), which reads as weird structure. The term is also used before it is named.
- → "We call these weight-losing particles. When such a particle passes through a cell with a sink, it loses the share of its weight that the sink takes from the cell's water. It carries the rest on."

**03:11 MUST.** "Compared with full mixing, they test only how water spreads between sinks."
- Participle opener (pattern 4), and compressed.
- → "These particles and full mixing therefore treat weak sinks in the same way. They differ only in how water spreads between sinks: along particle paths, or by mixing in every cell." (The colon introduces two options, not a second claim.)

**03:15 SHOULD.** "A steady trace of nine groups on the 1.68-million-cell Neversink model took 2–3 s (Section 5.1), of which about 1 s was reading the budget. It peaked at 2.5 GB of memory, of which 0.5 GB was the loaded budget (…)."
- Two ", of which" tails (pattern 2) and a noun stack.
- → "On the Neversink model, with 1.68 million cells, a steady trace of nine groups took 2–3 s (Section 5.1). About 1 s of this was reading the budget file. Memory use peaked at 2.5 GB, including 0.5 GB for the budget (Apple M4 Max, 64 GB)."

**03:15 SHOULD.** "A group is a destination traced as one unit, such as one well."
- Too late. The term is used at 02:25. Move the definition there (see 02:25) and drop it here.

**03:15 MUST.** "One hundred wells traced separately would need about 20 GB, so wells are best grouped or traced in batches."
- Over-asserts: this is an estimate, not a run (the evidence comment says so). It also has a ", so" tail.
- → "From this rate, we estimate that 100 wells traced as separate groups would need about 20 GB. On a smaller machine, wells can be grouped or traced in batches."

**03:15 SHOULD.** "On one million synthetic cells, the solve for four groups took 0.55 s, or 0.42 s with 7,000 flow loops."
- ", or" tail. The faster time with loops will puzzle the reader.
- → "On a synthetic model of one million cells, the solve for four groups took 0.55 s. Adding 7,000 flow loops did not slow it (0.42 s)."

**03:17 SHOULD.** "Its memory grows with the number of time steps (Section 7)."
- "Its" is ambiguous.
- → "The memory needed for transient tracking grows with the number of time steps (Section 7)."

## 04_verification.md

**04:13 SHOULD.** The paragraph has no opener. Add one: "Three further tests compare the code with independent results."

**04:13 SHOULD.** "Simulations split into two to four models (…) agree with the single model to 7.4 × 10⁻¹⁰, the flow solver tolerance. Results therefore do not depend on the grid type or on model splitting."
- Tail appositive (pattern 1), and a "therefore" closer (pattern 5) that generalises beyond three test models.
- → "… agree with the single model to 7.4 × 10⁻¹⁰. This is the tolerance of the flow solver, so the difference comes from the flow solution, not the tracing. On these models, the results did not depend on the grid type or on splitting."

**04:15 MUST.** "GWT, run to equilibrium with upstream advection and no dispersion, removes water through each sink at the cell's concentration, as gross accounting does. Its unit concentration equals the steady forward fraction G …"
- Participle chain inside the subject (pattern 4). "Its unit concentration" is odd.
- → "GWT gives an independent check on gross accounting. We ran GWT with upstream weighting and no dispersion until the concentrations stopped changing. GWT removes water through each sink at the cell's concentration, as gross accounting does. The concentration of the tagged source water then equalled G to 2.8 × 10⁻¹¹ or better on models 1 and 2, including the weak-sink well."

**04:15 SHOULD.** "Weight-losing PRT particles (Section 3.2) delivered the well inflow to within 0.6 %, an error of the finite number of release points."
- Tail appositive (pattern 1). The reader is not told why this matters.
- → "The weights of the weight-losing PRT particles (Section 3.2) that reached the well added up to its inflow within 0.6 %. The small difference comes from the finite number of release points. This checks the particles used in Section 5."

**04:19 MUST.** "Both directions therefore rest on an independent code."
- Unclear: which code, and what does "rest on" mean?
- The paragraph also has no opener.
- → Open with: "Transient tracking has no analytical answer to compare with, so we compared it with GWT and with itself run backward." Close with: "Forward tracking agrees with GWT, an independent code, and backward tracking agrees with forward tracking. Both directions are therefore checked against GWT."
- The closing "and" joins the two links of one argument. If the writer prefers, split it into two sentences.

**04:21 MUST.** "With the default "flow" volumes, each cell's water balance follows from how the volumes are carried. Its error, at most 9.5 × 10⁻¹⁷, therefore tests only the bookkeeping. The tagged-water balance, which tests the tracking itself, closed to 1.0 × 10⁻¹⁵."
- "follows from how the volumes are carried" and "bookkeeping" are compressed (pattern 3), and there is a ", which" insert. This is the v6 "holds by construction" sentence in new words.
- → "With the default "flow" volumes, each cell's water volume is updated from the storage flows. The cell's water balance therefore closes automatically. Its error, at most 9.5 × 10⁻¹⁷, only confirms the arithmetic. The real test is the balance of tagged water in each cell. It closed to 1.0 × 10⁻¹⁵, so no tagged water is created or lost between steps."

**04:23 MUST.** "At the other end of the run they differ by at least 0.40 and 0.52, so the test is not trivial."
- "the other end of the run" is hard to follow. "so the test is not trivial" is a compressed second claim.
- → "Early in the run, c is still far from G, by 0.40. Late in the run, w is far from F, by 0.52 [check: 'at least' against m10_constant]. The agreement at the ends is therefore not built into the test."

**04:23 SHOULD.** "The two methods agree where flows are steady, so a user can trust either."
- A "user can …" closer (pattern 5). "trust either" over-reaches.
- → "Where flows are steady, transient tracking and the steady trace give the same answer."

**04:27 MUST.** "Problem B is an aquifer like model 1, against PRT on a 12.5 m grid west of the gaining river, where no method meets a weak sink."
- "against" is compressed. The ", where" tail hides the reason for the choice.
- → "Problem B is an aquifer like model 1. Its reference is PRT on a 12.5 m grid. The comparison is made west of the gaining river, where water reaches the well without passing a weak sink. Any difference there comes from mixing alone."
- Also for Problem A: "against the analytical capture zone" → "compared with the analytical capture zone".

**04:31 MUST.** "The F ≥ 0.1 area, every cell that sends at least a tenth, is meant as a cautious outer limit. Section 5 writes them as F > 0.5 and F > 0.1, which give the same areas here (…)."
- Appositive in the subject.
- Decision 24 asks that the strict/non-strict note go to the SI if it changes no result. The note still tells the reader nothing they need.
- → "The F ≥ 0.1 area holds every cell that sends at least a tenth of its water to the well. It is meant as a cautious outer limit."
- Then cut the second sentence. Use one notation, ">", in §4, §5, §6 and Figs 3 and 6. Put the "no cell has F exactly 0.1 or 0.5" note in the SI.

**04:33 MUST.** "The transition band, the edge cells with 0.1 < F < 0.9, narrowed only as about h^0.5 with cell size h."
- An appositive definition, then a rate law in the same sentence.
- → "The transition band is the strip of edge cells where F lies between 0.1 and 0.9. Its width shrank only with about the square root of the cell size h. Halving h narrowed it by about 30 %."

**04:37 SHOULD.** "The seasonal example model, a synthetic model, shows what transient tracking adds to snapshots (Section 2.7). The paper has no transient application to a real model (Section 7)."
- Appositive (pattern 1).
- The second sentence is the hedging opener the author disliked in §6. §7 already says it.
- → "A synthetic seasonal example model shows what transient tracking adds to snapshots (Section 2.7), and what it tells a manager about stored water." Cut the second sentence.

**04:39 SHOULD.** "A 1-day steady period, with the well already pumping, is followed by 30 years of four seasons (121 steps). … With one layer, recharge cannot form a young layer on top of old water."
- The last sentence does not say why it matters.
- → "The run starts with a 1-day steady period, with the well already pumping. Thirty years of four seasons follow, one time step per season (121 steps in all)."
- Then: "Because the model has one layer, recharge mixes over the full thickness. It cannot form a layer of young water on top of old water, which affects the shares below [check: say how, with C]."

**04:43 SHOULD.** "…, with river leakage the rest (Fig. 4a)."
- A number exists. Give it: "and 13 % river leakage".

**04:45 SHOULD.** "No west-edge water arrived within 30 years."
- Make the contrast with the snapshot's 12 % explicit.
- → "Snapshots credit 12 % of the well's water to the west edge. With transient tracking, none of that water arrived within 30 years."

**04:47 SHOULD.** "Backward tracking in time gives, for the water in each cell at the start, the fractions that leave through the well or the river within 30 years and the fraction still stored (Fig. 4d–f)."
- An inserted phrase splits the verb from its object.
- → "Backward tracking in time follows the water in each cell at the start of the run. It gives the fractions of that water that leave through the well and through the river within 30 years, and the fraction still stored (Fig. 4d–f)."

**04:47 SHOULD.** "It is an area for a stated time horizon. The well's 30-year pumping splits into 13.8 % river leakage, 18.5 % recharge and 67.7 % initial water."
- The first sentence is an aphorism-like closer.
- The split repeats the 68 % of 04:45 without saying why.
- → "It shows which water reaches the well within the 30-year horizon. The backward split of the well's 30-year pumping, 67.7 % initial water, agrees with the forward result, as the check of Eq. (9) requires."

## 05_neversink.md

**05:3 MUST.** "Its published contributing areas come from one set of particle settings, so they are a benchmark, not a reference. … Particles that lose water at sinks as full mixing does then test mixing like for like (Section 5.3)."
- "a benchmark, not a reference" and "test mixing like for like" are compressed (pattern 3).
- 05:25 repeats the purpose almost word for word. Keep the full version in one place, preferably here per decision 26, and shorten 05:25.
- → "The published contributing areas come from one choice of particle settings. They are a benchmark to compare with, not the true answer. We therefore rerun particles on the same flow field to show how far the settings alone move the area. We also run particles that lose water at each sink in the same way as full mixing. Any remaining difference from full mixing then comes from how mixing spreads water (Section 5.3)."

**05:7 SHOULD.** "Rerun with MODFLOW 6 version 6.9, it reproduces the published heads within 8.6 mm."
- Participle opener (pattern 4).
- → "We reran it with MODFLOW 6 version 6.9. The heads matched the published heads to within 8.6 mm."

**05:7 SHOULD.** "One particle starts in each uppermost active cell of the regions (the start cells; 122,021 particles)."
- A coined label in parentheses. The present tense hides that this describes the published runs.
- → "In the published runs, one particle starts in the uppermost active cell of each column in the three regions, 122,021 particles in all. We call these cells the start cells."

**05:7 SHOULD.** "A particle stops in the first weak-sink cell it enters, whose sink is credited with all of its water."
- ", whose" tail (pattern 2).
- → "A particle stops in the first weak-sink cell it enters. That cell's sink is credited with all of the particle's water."

**05:11 SHOULD.** "A trace of nine destination groups took 2–3 s, against 44 s for the MODFLOW 6 run."
- The reader does not know what the nine groups are.
- → "A trace of nine destination groups, each well alone and all eight together, took 2–3 s. The MODFLOW 6 run takes 44 s."

**05:15 MUST.** "We measure agreement with the overlap: the cells both areas share, as a share of all cells in either area (the Jaccard index)."
- A colon definition with "share … as a share". The author called the v6 version hard to follow.
- → "To measure how well two areas agree, we use an overlap score, the Jaccard index. It is the number of cells that lie in both areas, divided by the number of cells that lie in either." Keep the two sentences on 1 and 0.

**05:17 SHOULD.** "An area drawn from F, the share of a cell's water that ends at the wells, needs a threshold. The F > 0.5 area holds the cells where more than half the water ends at the wells, the cells most certainly in the area. The F > 0.1 area, where more than a tenth does, is a wider, cautious area (Section 4.3)."
- Three appositives in three sentences (pattern 1).
- → "F gives each cell a share of water, not a yes or a no, so drawing an area needs a threshold on F. The F > 0.5 area holds the cells where more than half the water ends at the wells. These are the cells most certainly in the area. The F > 0.1 area, where more than a tenth of the water ends at the wells, is wider and more cautious (Section 4.3)."
- The last appositive is short and can stay.

**05:17 MUST.** "The expected area, the sum of F over the start cells, is 910 cells against 980 published."
- A new term in an appositive (pattern 1). It is not explained, yet §6.5 rests advice on it (pattern 3).
- → "Adding up F over the start cells gives the expected area. It counts each cell in proportion to the share of its water that reaches the wells. The expected area is 910 cells, against 980 published contributing cells."

**05:21 SHOULD.** "The F > 0.5 area lies almost wholly inside the published area: 94 % of its 445 cells are published contributing cells."
- Colon join (pattern 2).
- → "The F > 0.5 area has 445 cells, and 94 % of them are published contributing cells." Or split into two sentences.

**05:21 MUST.** "The F > 0.1 area, 2,139 start cells or 2.2 times the published area, still misses 27 % of it."
- Appositive chain in the subject.
- → "The F > 0.1 area is much larger, with 2,139 start cells, 2.2 times the published area. It still misses 27 % of the published cells."

**05:21 SHOULD.** "A published particle stops in the cell of U___7, whose well takes 44 % of the cell's outflow."
- ", whose" tail.
- → "Well U___7 takes 44 % of its cell's outflow. A published particle stops in that cell, but full mixing passes the other 56 % downstream (…)."

**05:21 SHOULD.** "Net accounting (Section 2.3), which credits U___7 with 2.26 times its pumping, raises the expected area to 978 cells (…)."
- ", which" insert.
- → "Net accounting (Section 2.3) credits U___7 with 2.26 times its pumping. It raises the expected area to 978 cells (…)."

**05:21 SHOULD.** "Whether overlaps of 0.30–0.41 are low depends on the published particle settings."
- A compressed bridge.
- → "Whether overlaps of 0.30–0.41 are low depends on how much the published area itself depends on its particle settings. Section 5.3 tests this."

**05:25 SHOULD.** "Why not compare with the published area alone?"
- This is the first of four question openers in §5 (pattern 5). With 05:3 rewritten, cut this paragraph's first three sentences down to one: "On the same flow field, PRT gives overlaps from 0.29 to 0.998, depending on the particle settings alone (…)."
- Also: "The published area is therefore one particle setting among several" is a category slip, since an area is not a setting.
- → "The published area is therefore the result of one set of particle settings among several. It is not ground truth."

**05:27 MUST.** "PRT reproduces the published area only with three published settings: recharge and stream flows on the top face …, particles stopped at every weak sink, and draping (MODPATH DrapeOption), which moves a particle that starts in a dry cell down to the first active cell below."
- A colon list of three long items, with a ", which" definition inside the third.
- → "PRT reproduces the published area only with all three published settings. First, recharge and stream flows enter through the top face of a cell where that face is open (IFLOWFACE). Second, particles stop at every weak sink. Third, a particle that starts in a dry cell is moved down to the first active cell below, which MODPATH calls draping (DrapeOption)."

**05:27 MUST.** "The weak sinks include buried stream cells: SFR reach cells with an active cell above, where a gaining reach is usually a weak sink."
- A colon definition and a ", where" tail. Buried stream cells are on the decision 4 list of terms to explain.
- → "The weak sinks include buried stream cells. A buried stream cell holds an SFR reach but has an active aquifer cell above it. A gaining reach there takes only part of the cell's water, so it is usually a weak sink."

**05:29 SHOULD.** "To test mixing itself, weight-losing particles (Section 3.2) were released from the source terms of all cells with F > 10⁻⁶, each weighted by its flow."
- Participle tail.
- → "… were released from the source terms of all cells with F > 10⁻⁶. Each particle's weight is the flow it represents."

**05:29 SHOULD.** "Their particle share P, like F, is the share of a cell's water that reaches the wells, but along particle paths instead of by full mixing."
- "like F, … but … instead of" packs a comparison into one sentence.
- → "From these particles we compute each cell's particle share P. Like F, P is the share of a cell's water that reaches the wells. P follows the water along particle paths. F follows it by mixing in every cell."

**05:29 SHOULD.** "… depending on release height (Fig. 7)."
- "release height" is not defined. Fig. 7 says "over the cell volume, at mid-cell or at the water table".
- → "depending on where in the cell the particles are released (Fig. 7)".

**05:33 MUST.** The whole paragraph. It opens with a question (pattern 5) and has ten sentences carrying three areas and five percentages. The caveats sit in the middle ("so the coverage is an upper bound", "Within these caveats"), so the reader holds them while the numbers arrive.
- "so the coverage is an upper bound" does not say why (pattern 3).
- Rewrite as two paragraphs, with the reason first, the caveats next and the numbers last:
  - → "Mixing and particles spread water differently, so the F > 0.5 area is not the counterpart of the P > 0.5 area. Full mixing spreads each cell's water over all its outflows. The water that reaches the wells is therefore shared over more cells, each with a lower F. Along a particle path, the water stays together until a sink takes it. On Neversink the P > 0.5 area has 691 start cells, against 445 for F > 0.5. Covering it takes the lower threshold F > 0.1."
  - → "Two caveats apply to the coverage. Particles were released only where F > 10⁻⁶, so cells that particles would reach but full mixing would not are missing from the P > 0.5 area. The coverage may be overstated for that reason. And because the particles lose weight at sinks as full mixing does, only the spreading between sinks is tested. With these caveats, F > 0.1 covers 87 % of the P > 0.5 area, and F > 0.5 covers 59 %. Of the F > 0.5 cells, 92 % lie inside the P > 0.5 area (…). The gap to the published area therefore comes from both mixing and the published particle settings."

**05:37 SHOULD.** "How streams are represented also changes the area."
- Fine as an opener, but name the two options here, before "With streams as cells …": "The code offers two representations of SFR streams."
- "(the stream share)" is a parenthetical coinage. → "We call this the stream share."

**05:41 SHOULD.** "The published study also mapped a probability of contribution, an uncertainty product for protection zones."
- Appositive (pattern 1).
- → "The published study also mapped a probability of contribution for each cell. This is an uncertainty product meant for protection zones."
- The reader will also wonder why there are 357 areas but 358 realisations. Say so in a clause, or point to Fig. 9 or the SI.

**05:47 MUST.** "Why do the two differ? … There, the published area changes with the particle settings, not with the water reaching the wells."
- This is the third question opener.
- "changes with the particle settings" is confusing, because the settings are the same in every realisation. The author's v6 comment asked what is compared and why the two differ.
- → "In the S region the two differ most. There, the published area varies between realisations, with a coefficient of variation of 32 %. PRT with the published settings reproduces this variation (r = 0.997 over 60 realisations). The sum of F, the water reaching the wells, does not vary with it (r = 0.00). So in the S region the published area changes between realisations while the water reaching the wells does not. We infer that the variation comes from how the particle settings act on each realisation's flow field."
- "We infer" keeps the evidence comment's caution about not naming buried streams.

**05:51 SHOULD.** "How does the area grow as pumping rises? This matters when a zone must be redrawn for planned rates."
- The fourth question opener.
- → "A zone may have to be redrawn for planned pumping rates, so it matters how the area grows as pumping rises."

**05:55 SHOULD.** "The recharge reaching the wells, and with it the area, therefore grows faster than pumping."
- Parenthetical insert plus a "therefore" closer.
- → "The recharge reaching the wells therefore grows faster than pumping, 4.57 times. The area, which is drawn from that recharge, grows faster too." (4.57 is in the evidence comment.)

**05:57 MUST.** "Changing only this setting, stopping at buried stream cells, lowers the growth of weight-losing particles from 4.76 to 3.83 times (…)."
- Participle opener with an appositive (patterns 1 and 4).
- It is also not said that weight-losing particles grow faster than full mixing (4.76 against 4.09), so the reader is lost.
- → "Weight-losing particles, which pass buried stream cells as full mixing does, give an area that grows 4.76 times. When we make them stop at buried stream cells, and change nothing else, the growth falls to 3.83 times, closer to the published 3.60 (…)."

## 06_discussion.md

**06:3 MUST.** "Three outcomes frame this discussion."
- This is the announcement the brief names (pattern 5).
- The second sentence ("hold exactly, to the computer's precision, on every test model and, for closure, on every Neversink trace") is broken up by three inserts.
- "The subsections discuss what these outcomes mean in practice." is a second announcement.
- → "On a published regional model, full mixing gave contributing areas within the range that particle tracking gives under different particle settings on the same flow field (Section 5). The water-budget checks held to the computer's precision on every test model (Sections 4.1 and 4.2). The closure check also held on every Neversink trace (Section 5.1). Transient tracking answered a question that snapshots cannot: how much of the pumped water was already stored in the aquifer (Section 4.4). For a modeller, these results bear on five choices: the method, the accounting, transient tracking, the stream representation and the zone itself."
- In the last sentence the colon introduces a list, not a second claim. It replaces both announcements.

**06:7 SHOULD.** "Full mixing assumes that the water in each cell is fully mixed, so every outflow carries the same mix of origins."
- The fifth definition of full mixing (pattern 6). Cut it.

**06:7 SHOULD.** "Weight-losing particles give up, at each sink they pass, the share of their flow that the sink takes, as full mixing does."
- An inserted phrase, and it comes after the sentence that uses the term. Cut it (it is defined in §3.2), or move it before the 2 % sentence as "Weight-losing particles treat sinks as full mixing does (Section 3.2)."

**06:7 SHOULD.** "Full mixing gives exact budgets and many destinations from one trace, in 2–3 s on Neversink (Section 5.1). It also gives the share of water taken by each weak sink, a well or stream that takes only part of the water passing its cell. Particles give what full mixing cannot, flow paths and first arrival times."
- "exact budgets" is compressed.
- There are two tail appositives, and one is a re-definition.
- → "Full mixing traces many destinations at once, in 2–3 s on Neversink (Section 5.1). Every trace is checked against the budget. It also gives the share of water each weak sink takes. Particles give flow paths and first arrival times, which full mixing cannot."

**06:9 SHOULD.** "Mixing whole cells blurs the edge of an area into a transition band of cells where F, the share of a cell's water that ends at the well, lies between 0.1 and 0.9 (Section 4.3). In a small zone this band spans much of the width."
- The appositive re-defines F (pattern 6).
- "much of the width" is under-specific. Give the band width in cells from §4.3 or Fig. 3 if it is available.
- → "Mixing blurs the edge of an area into a transition band, where F lies between 0.1 and 0.9 (Section 4.3). The band is several cells wide [check: number from Fig. 3], so in a small zone it covers much of the zone."

**06:11 MUST.** "Two settings each moved the overlap with the published Neversink contributing cells, those whose published particle ends in a supply well, by 0.33–0.35 (Fig. 7)."
- Appositive in the middle of the sentence.
- The sentence before it ("Agreement was measured as the overlap, the share of cells two areas have in common.") is a re-definition, and a looser one than §5.2.
- → Cut the overlap sentence. Then: "Two settings each moved the overlap with the published Neversink contributing cells by 0.33–0.35 (Fig. 7)."
- Decision 33 is met by "the published Neversink contributing cells". The "those whose …" definition is not needed in §6.

**06:11 SHOULD.** "A particle check raises its own question, which settings to use."
- Tail appositive.
- → "A particle check raises its own question: which particle settings should it use?" Or: "A particle check needs its own choice of particle settings."

**06:11 SHOULD.** "Each moved the overlap as much as or more than the switch from weight-losing particles to full mixing."
- Clumsy.
- → "Each moved it at least as much as switching from weight-losing particles to full mixing."

**06:15 SHOULD.** "On Neversink, net accounting raised the sum of F, the expected number of contributing cells, from 910 to 978, against 980 published contributing cells."
- Appositive (pattern 1).
- → "On Neversink, net accounting raised the expected area from 910 to 978 cells. The published area has 980 cells."

**06:17 SHOULD.** "The group-level match is therefore partly differences of both signs cancelling."
- Noun stack.
- → "The close match for the eight wells together therefore comes partly from errors of opposite sign cancelling out."

**06:21 SHOULD.** "A snapshot traces one time step as if its flows were steady."
- The third definition (pattern 6). Cut it.
- "On the seasonal example model (Section 4.4), a synthetic one-layer aquifer, …" has an appositive. Cut "a synthetic one-layer aquifer".
- The paragraph repeats three §4.4 results. Decision 35 asks for discussion, not repeated numbers. Keep one: "On the seasonal example model, snapshots credit the well with west-edge water that, with transient tracking, does not arrive within 30 years (Section 4.4)."

**06:23 SHOULD.** "Transient tracking needs porosity and every time step saved (Section 7)."
- Zeugma.
- → "Transient tracking needs a porosity, and it needs the budget of every time step to be saved (Section 7)." Or split into two sentences.
- Also, the cross-reference "(Section 4.4)" for the two volume options now points to text that moved to the SI. Point to the SI item instead.

**06:29 SHOULD.** "Tracing then stops at the stream, showing which package delivers the water."
- Participle tail (pattern 4).
- → "Tracing then stops at the stream. It shows which package delivers the water."
- §6.4 repeats §5.4 sentence for sentence ("stream reaches become extra cells linked by stream routing"). Replace the repeat with the discussion point: which question each representation answers. For example: "Streams as cells answer which boundary supplies the well. The stream network answers which land the water fell on, including land upstream along the streams. A zone for land-use control needs the second."
- That last sentence is a judgement. Hedge it ("in our judgement") or leave it out.

**06:33 SHOULD.** "Five pieces of advice follow for a modeller drawing a protection zone with full mixing."
- Announcement (pattern 5). The 06:3 rewrite already names the five choices, so cut this sentence.

**06:35 MUST.** "Take the size of the zone from the expected area, the sum of F, since the F > 0.5 area is smaller (Section 5.2)."
- This is the sentence the author called incomprehensible in v6, and it is still compressed: how does one "take a size" from a sum? It also has an appositive.
- → "The F > 0.5 area is smaller than the published area, because mixing spreads the well's water over more cells (Section 5.3). For the size of the zone, use the expected area, the sum of F over the cells, which came closer to the published size (Section 5.2)."
- The second sentence keeps one short appositive as a reminder. Drop it if 05:17 defines the expected area plainly.

**06:35 SHOULD.** "This area changed little with cell size in the synthetic tests and lay almost wholly inside both particle-tracked areas on Neversink (Sections 4.3 and 5.2–5.3)."
- Two claims joined by "and".
- → "This area changed little with cell size in the synthetic tests (Section 4.3). On Neversink, it lay almost wholly inside both particle-tracked areas (Sections 5.2–5.3)."

**06:35 SHOULD.** "It is not a guaranteed envelope, because on Neversink it missed some cells next to weak sinks and between sinks (Sections 5.2–5.3)."
- "between sinks" is unclear.
- → "… it missed some cells next to weak sinks, and some cells where particles and mixing spread water differently between sinks (Sections 5.2–5.3)."

**06:37 SHOULD.** "A check under stated settings shows how far the rule to stop or pass particles there moves the edge (Section 5.3; Fig. 7)."
- Compressed: "a check under stated settings".
- → "Run particles once stopping at these cells and once passing them, and report the settings. The difference shows how far the edge of the zone depends on that rule (Section 5.3; Fig. 7)."

**06:41 SHOULD.** "The choice changes the area, which stops at the streams when they are treated as cells (Section 6.4; Fig. 6)."
- ", which" tail.
- → "The choice changes the area. When streams are treated as cells, the area stops at the streams (Section 6.4; Fig. 6)."

**06:43 SHOULD.** "On the seasonal example model, the 30-year area stops short of the west edge, unlike the steady area (Fig. 4c–d)."
- This repeats a result (decision 35). Cut it. The pointer "(Section 4.4; Fig. 4)" in the previous sentence is enough.
- Also, "Short horizons, which need transport sub-steps (Section 4.4), were not tested.": sub-steps are now explained in §3.2 and the SI, not §4.4. → "(Section 3.2)".

## 07_limitations.md

**07:5 SHOULD.** "Face-to-face routing, an experimental option, removes 35–70 % of the excess spreading. It works in 2D only and has no effect in cells with weak sinks or vertical through-flow."
- In the main text, the option is named here without saying what it does (pattern 3). There is an appositive, and the second sentence joins two claims with "and".
- → "An experimental option, face-to-face routing, passes water between cell faces instead of mixing it in the cell. It removes 35–70 % of the excess spreading. It works in 2D only. It has no effect in cells with weak sinks or vertical through-flow."

**07:7 MUST.** "Steady traces and snapshots treat the flows as steady, so their results have no travel lag."
- "travel lag" is a coined term (pattern 3). It also seems to contradict §2.6, where steady traces give mean travel times.
- → "Steady traces and snapshots treat the flows as steady. Their fractions describe where water goes, not when it gets there. Only the mean travel time of Section 2.6 adds timing."

**07:7 SHOULD.** "Its memory is one (steps × cells) array per group and output."
- Compressed.
- → "It stores one value per cell and time step for each group and each output. At 1.68 million cells and 121 steps, each such array takes about 1.6 GB."

**07:11 SHOULD.** "Full mixing removes the stop-or-pass rule at weak sinks from the tracing only."
- Compressed.
- → "Full mixing removes the need for a stop-or-pass rule at weak sinks while tracing. It does not remove the modeller's choices. The modeller still decides how to credit a weak-sink well and which threshold on F draws the area (Sections 2.3 and 6.5)."

## 08_conclusions.md

**08:3 SHOULD.** The paragraph is a 12-sentence staccato feature list (see Overall).
- Group it into what is made exact and checked, then what is new in scope, then speed.
- Use "because" or "so" where one fact explains the next.

**08:3 SHOULD.** "Run backward in time, it gives the fractions of each cell's water that reach the well, leave through other sinks or stay stored. Snapshots cannot give these."
- Participle opener (pattern 4).
- → "Backward tracking in time gives the fractions of each cell's water that reach the well, leave through other sinks or stay stored. Snapshots cannot give these."

**08:3 SHOULD.** "A steady trace on 1.68 million cells takes 2–3 s, fast enough for ensembles."
- Tail appositive, and an unhedged generalisation where evidence exists.
- → "A steady trace on 1.68 million cells takes 2–3 s, and all 358 realisations of the published ensemble were traced (Section 5.5)."
- That ", and" joins two facts. If preferred, split it into two sentences.

**08:5 SHOULD.** "Tested against a published real-world regional model, full mixing gave contributing areas within the range …"
- Participle opener (pattern 4). The author's suggested wording can be kept as a main clause.
- → "We tested the method against a published real-world regional model. Full mixing gave contributing areas within the range …"

## 09_availability.md

- Clean. "tutorials" appears once, where decision 38 allows it. No changes.

## Captions (display/*.md)

**A:3 (Table 1) SHOULD.** "Four ways to compute, from a groundwater flow model's flows, the share of each cell's water that reaches a destination or came from a source."
- An inserted phrase splits the verb from its object.
- → "Four ways to compute the share of each cell's water that reaches a destination, or that came from a source, from the flows of a groundwater flow model."

**A:3 SHOULD.** "The fractions F, G, c and w and gross and net accounting are defined in Section 2."
- The "and … and" is ambiguous.
- → "Section 2 defines the fractions F, G, c and w, and gross and net accounting."

**A:3 SHOULD.** "Fuller notes on each cell, and the sources it rests on, …"
- In a paper about model cells, "cell" is ambiguous here.
- → "Fuller notes on each table entry, and their sources, …"

**A:3 SHOULD.** "this formulation"
- Not used elsewhere. Match the column head to the main text ("This paper" or `gwsource`).

**A:19 (footnote 1) SHOULD.** "In our test, one step with porosity 0 gave the steady G to 1 × 10⁻¹², an undocumented use."
- Tail appositive.
- → "… gave the steady G to 1 × 10⁻¹². This use of porosity 0 is not documented."

**A:25 (footnote 4) SHOULD.** "A group of cells with no outflow to any sink or to a cell outside the group; reported, with no connections deleted."
- A fragment joined to a fragment by a semicolon.
- → "A closed recirculation loop is a group of cells with no outflow to any sink or to a cell outside the group. Such loops are reported. No connections are deleted."

**B:3 (Fig. 1) SHOULD.** "(a) A fully mixed cell i with cell-to-cell flows, recharge (source term) and a well (sink term, d_i), defining I_i, O_i and r_i (Eq. 1)."
- Participle tail.
- → "… and a well (sink term, d_i). These define I_i, O_i and r_i (Eq. 1)."

**B:3 SHOULD.** "(c) Water credited to a weak-sink well pumping 5.0 m³/d: …"
- Say which model, since panel (b) is the eight-cell example: "in the three-layer example model".

**B:3 MUST.** "(d) Left: a snapshot traces one step on its own flows, storage release being a source of unknown origin."
- Absolute construction ("storage release being"), the most machine-sounding phrase in the captions.
- → "(d) Left: a snapshot traces one step on that step's flows. Storage release is a source of unknown origin."

**C:3 (Fig. 2) SHOULD.** "The checks that must hold exactly (…) reach round-off, within ten times machine precision."
- "reach round-off" is jargon.
- → "… have errors within ten times machine precision, the size of rounding error."

**C:3 MUST.** "The steady G against GWT on model 7 (1.0 × 10⁻⁸) and the steady limits on model 10 are limited by the flow solver tolerance."
- "the steady limits" is an undefined label (pattern 3). The sentence is a noun stack.
- → "Two comparisons are limited by the tolerance of the flow solver, not by the tracing. They are G against GWT on model 7 (1.0 × 10⁻⁸), and transient tracking against the steady F and G on model 10."

**C:9 (Fig. 3) SHOULD.** "Bottom row: problem B, an aquifer like model 1, with PRT on the finest grid as reference, compared west of the river."
- Appositive chain.
- → "Bottom row: problem B, an aquifer like model 1. The reference is PRT on the finest grid, compared west of the river."

**C:9 MUST.** "Face-to-face routing (Chowdhury 2016), an experimental 2D option that routes water between cell faces instead of mixing it, removes 35–70 % of the excess spreading but keeps the rate."
- A long appositive in the subject (pattern 1). "keeps the rate" is compressed.
- → "Face-to-face routing (Chowdhury 2016) is an experimental 2D option that routes water between cell faces instead of mixing it in the cell. It removes 35–70 % of the excess spreading. The band still narrows only as h^0.5."

**C:9 MUST.** "The cell-averaged exact zone (A) and PRT on the same grid (B) set a floor of about one cell."
- "set a floor of about one cell" is compressed (pattern 3).
- → "Even the exact zone averaged onto the grid (A), and PRT on the same grid (B), have a band about one cell wide. No cell-based method can do better."

**C:9 SHOULD.** "(b, e) … F ≥ 0.1 area. (c, f) … F ≥ 0.5 area"
- Use the same notation as §5 and §6 (see 04:31).

**C:15 (Fig. 4)** Clean. "Dashed line, the initial water's share of all water pumped so far." is acceptable caption style.

**D:3 (Fig. 5) SHOULD.** "The wells form the U cluster (…), SV_W (3) and SV_S (1); well names are those of the published model. Coordinates are km from the grid origin (EPSG:5070); true north is 12.9° west of grid north."
- Two semicolon joins (pattern 2). Split each into two sentences.
- "Black: the published contributing cells of the eight priority wells, calibrated model." → "… in the calibrated model."

**D:7 (Fig. 6) SHOULD.** "… of the uppermost active cell for the eight priority wells, calibrated model."
- → "… in the calibrated model".

**D:11 (Fig. 7) MUST.** "Overlap (cells in both areas as a share of cells in either; 1 means identical areas, 0 no common cells) between the published contributing cells and other delineations on the same flow field."
- The definition interrupts the title.
- → "Overlap between the published contributing cells and other delineations on the same flow field. The overlap is the number of cells in both areas divided by the number in either. It is 1 for identical areas and 0 for areas with no common cells."

**D:11 MUST.** "PRT, flow-weighted: start cells with particle share P > 0.5, for weight-losing particles released over the cell volume, at mid-cell or at the water table, and for particles that lose weight only at the wells (…). PRT, published starts: one particle per published start, stopped at every weak sink, with boundary flows distributed through the cell (MODFLOW 6 default) or on the top face where it is open, and with or without draping of dry starts (published settings: top face and draping)."
- Each of these is one sentence with four or five stacked qualifiers. A reader cannot match markers to runs.
- "flow-weighted" is a third name for the weight-losing particles.
- → "PRT with weight-losing particles: start cells with particle share P > 0.5. Particles are released over the cell volume, at mid-cell or at the water table. One further run uses particles that lose weight only at the wells (…). PRT from the published starts: one particle per published start, stopped at every weak sink. Boundary flows are spread through the cell (the MODFLOW 6 default) or placed on the top face where it is open. Dry starts are draped or not. The published settings are top face and draping."

**D:15 (Fig. 8) SHOULD.** "(areas moved one row north onto their cells)"
- This is cryptic in a caption (pattern 3).
- → "The stored published areas are offset by one row, so we moved them one row north onto their cells ({SI: Monte Carlo offsets and scenario rule})."

**D:19 (Fig. 9) SHOULD.** "PRT with the published conventions: 61 realisations."
- The main text says "settings". Use one word.
- Also, "the pumping fraction f of the scenario rule" is defined only in the SI. Add a few words, e.g. "f, the share of the maximum scenario pumping [check: definition]".

---

## Counts

| File | MUST | SHOULD |
|---|---|---|
| 00_front.md | 1 | 8 |
| 01_introduction.md | 5 | 14 |
| 02_methods.md | 8 | 29 |
| 03_implementation.md | 4 | 9 |
| 04_verification.md | 7 | 10 |
| 05_neversink.md | 9 | 17 |
| 06_discussion.md | 3 | 17 |
| 07_limitations.md | 1 | 3 |
| 08_conclusions.md | 0 | 4 |
| 09_availability.md | 0 | 0 |
| display/A.md (Table 1) | 0 | 6 |
| display/B.md (Fig. 1) | 1 | 2 |
| display/C.md (Figs 2–4) | 3 | 3 |
| display/D.md (Figs 5–9) | 2 | 4 |
| display/E.md | 0 | 0 |
| **Total** | **44** | **126** |

Non-style items noticed in passing, for the content reviewer:

- "two budget checks" (01:19) against "Three checks" (02:51).
- The cross-references "(Section 4.4)" at 06:23 and 06:43 point to text now in the SI.
- 357 against 358 realisations is unexplained in the main text.
- "weak sink" is defined as a cell (01:7) but as a sink term (02:35).
