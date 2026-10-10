# Round 1 review: voice and style (role `voice`)

Scope: voice-hugman failures, GMDSI register, terminology (terms.md), brief §4 style rules, captions, and consistency across the five writers. Draft at commit b845e71. Line numbers are those of the section and display files.

General verdict: the draft is not over-styled. There is no "earns its keep" or "binding constraint", no filler adverbs (crucially, notably, furthermore, moreover, indeed: zero hits), and almost no puffery. The voice problems are of three other kinds:
- terminology slips that undo distinctions the paper makes on purpose (thresholds, "reference", "modes", "zone" against "area", "tracking" used alone);
- density in Methods: stacked appositives, symbol-initial sentences, paragraphs with several points;
- captions that repeat the text, four of them over 300 words.

---

## 00_front.md

- **00:3**, "contributing areas in seconds, checked against the water budget, also backward in time" (SHOULD).
  - Problem: this is a feature list, not a reason to read (brief §1), and "also backward in time" will not mean much to a reader who has not read the paper yet. It is 127 characters.
  - Fix (121 characters): "Contributing areas from MODFLOW 6 budgets in seconds, each checked against the water budget, and traced backward in time."
- **00:5**, "What is added is backward tracking in time" (SHOULD).
  - Problem: a cleft sentence whose reference is unclear: added to what?
  - Fix: "New here is backward tracking in time: …"

## 01_introduction.md

- **01:3**, "risk-based workflows delineate the contributing area across an ensemble" (SHOULD). "Workflow" is coder register. Fix: "risk-based studies delineate the contributing area across an ensemble of models".
- **01:5**, "At a weak sink, a cell whose well takes only part" (MUST, hard rule 5: each term is defined once, by its assigned writer).
  - Problem: "weak sink" is defined here and again at 02:13, and the brief assigns it to B.
  - Fix: keep this definition, because the reader needs it here, and delete the sentence at 02:13 (see below). The orchestrator should record the reassignment.
- **01:5**, "And each destination needs its own particles" (SHOULD). "Destination" is used two paragraphs before it is defined (01:9). Fix: "And each well needs its own particles, so analyses of many wells or whole models become expensive".
- **01:5**, "backward particle tracking through time-varying flows is awkward" (SHOULD).
  - Problem: "awkward" is an adjective doing the work of a reason.
  - Fix: if EA 2019 gives the reason, state it, e.g. "requires the time-varying flows to be reversed step by step". Otherwise write "is described as awkward (Environment Agency 2019)".
- **01:9**, "Under full mixing each cell is fully mixed" (SHOULD). Tautology. Fix: "Full-mixing methods treat each cell as fully mixed, so all water leaving it carries the same mix of origins."
- **01:13**, "groundwater age and life expectancy are Eulerian measures of travel time" (SHOULD). terms.md: use "Eulerian" only when contrasting with particle (Lagrangian) times. Fix: "groundwater age and life expectancy are mean travel times computed on the model grid".
- **01:15**, "the reference method's forward mode has been described as an Eulerian transport tool" (SHOULD).
  - Problem: the same terms.md issue as 01:13, and "mode" is close to the banned "net mode".
  - Fix: "the forward calculation of the reference method has been described as a transport tool (Black et al. 2021)".
- **01:15**, "(for unit-concentration transport, on an abstract and the authors' slides only; …)" (SHOULD).
  - Problem: the hedge carries weight but is buried in a parenthesis that is hard to parse.
  - Fix: "None of the methods we read tracks water backward in time; for unit-concentration transport this rests on an abstract and the authors' slides (Bedekar et al. 2023, 2024)."
- **01:15**, "deletes the smallest-flow connection in each flow loop" (SHOULD). "Flow loop" is used before its definition (§2.4). Fix: add a pointer, "in each flow loop (§2.4)".
- **01:19**, "add forward tracking through storage, and add backward tracking in time" (SHOULD).
  - Problem: four lines after "Forward tracking through storage is not new", "add forward tracking" reads as a novelty claim.
  - Fix: "implement forward tracking through storage, as GWT does, and add backward tracking in time".
- **01:21–23**, "(Sections 2 and 4)" (SHOULD). Every other section writes "§4.1". Pick one style for the whole paper; NGWA house style is "Section 4" in running text, so change the "§" everywhere or change these three.
- **01:23**, "eight supply wells" (SHOULD). §5 and every caption say "priority wells". Fix: "eight priority supply wells".

## 02_methods.md

The section is 2,148 words against a budget of 1,900. The cuts below save about 150 words.

- **02:13**, "A weak sink is a cell whose sink term takes only part" (MUST, hard rule 5; duplicate of 01:5).
  - Fix: delete the sentence and fold the term into the next one: "We use gross accounting by default: in a weak sink, as in every cell, each sink term takes its share of the cell's total outflow, and the rest passes on to the neighbours."
- **02:13**, "$d_i$ is the outflow of cell $i$ through the destination's sink terms" (SHOULD).
  - Problem: the sentence starts with a symbol, as do several others in §2.
  - Fix: "The outflow of cell $i$ through the destination's sink terms is $d_i$, and its inflow through the selected source terms $s_i$."
- **02:33**, "From the fractions follow volumes: $F_i O_i$ is the water passing…" (SHOULD; one of the two worst paragraphs in the paper).
  - Problem: the paragraph has four points: volumes, boundary-control maps, the Fig. 1b example and "not a probability". Its first sentence is elliptical, and the paragraph ends on a caveat rather than its point.
  - Fix: move the Fig. 1b sentence up, directly after the "In words:" at 02:21, where it illustrates the equation. Give "F is a share of flow, not a probability (McLane and Cecan 2009)" its own sentence after it. Rewrite the volume sentence as: "The fractions give volumes. $F_i O_i$ is the water passing through cell $i$ that reaches the destination; $F_i$ times a source term is the water entering through that term that reaches it; $G_i$ times a sink term is the water leaving through that term that came from the source."
  - Also cut "Giving every sink term its own group yields boundary-control maps …". The check is defined at 02:53; say "boundary-control maps (§2.5)" once.
- **02:37**, "for the 5.0 m³/d well of tutorial 02, whose cell carries 33.7 m³/d, …" (SHOULD; the second worst paragraph).
  - Problem: one sentence of about 70 words carries the head-on gross/net confusion that brief rule 2 asks for in one sentence.
  - Fix: "Net accounting credits a weak-sink well with all the water passing its cell, 33.7 m³/d or 6.7 times its 5.0 m³/d pumping in tutorial 02; gross accounting gives $F = 0.15$ in the well cell and credits the pumping (Fig. 1c)." Put this directly after the definition of net accounting, and move "Which cells are fixed depends on the selection …" after it.
- **02:41**, "this is the reference method's sweep written as equations" (SHOULD). "Sweep" sits next to the banned "topological sweep". Fix: "this is the reference method's flow-order pass written as equations".
- **02:41, 02:63, 02:75, 03:19**, "one factorisation serves every destination group" / "reuses the factorisation of (1)" / "one factorisation per step" / "factorises each step's matrix once" (SHOULD).
  - Problem: this is linear-algebra vocabulary outside the one sentence §2.4 allows.
  - Fix: "the matrix is the same for every destination group, so all groups are solved together"; "uses the same matrix as (1)"; "one matrix per step, shared by all tagged groups".
- **02:41, 02:55, 02:75, 03:5, 03:7, 03:17, 04:13, 04:21, 04:23, 06:23**, "the solve" / "the flow solve" / "the tracking solve" (SHOULD). Coder nominalisation; the phrase drifts against "flow solver tolerance" at 04:23. Fix: "the solution", "solving the equations", "the flow solution", and use "flow solver tolerance" consistently.
- **02:55**, "Their error therefore measures the assembly and the solve, not the flow model." (SHOULD).
  - Problem: the paragraph opens with a pronoun and a connective, and the sentence is a negation-then-alternative (§2 has five; see below).
  - Fix: "The errors of these checks therefore measure only how the equations are built and solved; the flow model's budget error is already inside the identities."
- **02:55**, "tests the solve only in sum" (SHOULD). Unclear. Fix: "tests only the sum over all cells, not each cell".
- **02:63**, "The turnover time $\sum_i V_i F_i / \sum_i d_i$ equals …" (SHOULD). There is no plain-words gloss. Fix: add terms.md's wording, "the volume of water that ends at the destination divided by the destination's inflow".
- **02:75**, "(flow-error correction, as in MF6 GWT; Langevin et al. 2022; on by default)" (SHOULD).
  - Problem: three stacked parentheticals, in a paragraph of seven sentences that drifts across three points.
  - Fix: "This flow-error correction, on by default, follows GWT (Langevin et al. 2022)." Start a new paragraph at "The solvers of §2.4 apply step by step …".
- **02:77**, "Transport sub-steps are described in §3.2." (SHOULD). The paragraph lands on a pointer, not its point. Fix: delete the sentence; §3.2 introduces them.
- **02:79**, "Forward tracking is not new. Hydraulic mixing cells step forward in time …" (SHOULD).
  - Problem: this repeats 01:11 and 01:15 nearly verbatim.
  - Fix: cut to two sentences: "Forward tracking is not new: hydraulic mixing cells, GWT and the reference method's forward calculation all step forward in time (§1; Table 1, footnote 3). What we add is backward tracking in time (§2.9)."
- **02:83**, "it splits the destination's outflow by source term, time step and initial water (closure)." (SHOULD). The bare "(closure)" is cryptic. Fix: "… and initial water, and these parts add up to the destination's outflow (the closure check)."
- **§2 overall**: negation-then-alternative appears five times (02:33, 02:55, 02:63, 02:79, 02:83) against the brief's limit of one per section (SHOULD).
  - Keep the three the brief mandates as head-on confusions: "not a probability", "not MODPATH backward tracking" and "Forward tracking is not new".
  - Recast 02:55 as above.
  - Recast 02:63 as: "It is a mean over mixed water (Eulerian); particles (Lagrangian) give first arrival instead."
- **§2 overall**: "MF6" is never defined; GWT and SFR are not expanded either (MUST, journal rule §1: define abbreviations at first use). Fix:
  - write "MODFLOW 6" in place of "MF6" throughout the prose (eight uses);
  - expand at first use: "Groundwater Transport (GWT) Model" at 01:13 and "streamflow-routing (SFR)" at 02:5;
  - expand "GWF" at 03:7.

## 03_implementation.md

- **03:11, 03:13**, "an ensemble routine traces each realisation"; "A post-processing routine for MODFLOW 6 particle tracking" (SHOULD). "Routine" is coder register. Fix: "the code traces each realisation of an ensemble in turn …"; "For MODFLOW 6 particle tracking (PRT), the code writes flow-weighted release points: …".
- **03:11**, "Results go to npz, netCDF or GeoPackage files" (SHOULD). "npz" means nothing to MODFLOW users. Fix: "NumPy (npz), netCDF or GeoPackage files".
- **03:13**: a paragraph of two sentences (SHOULD). Merge it with 03:11 or add the consequence: "it is the particle tool used in §4.1 and §5.3".
- **03:17**, "On the 1.68-million-cell Neversink model a trace takes seconds" (SHOULD; the worst adjective-for-number in the paper). Fix: "takes 2 to 3 s (§5.1)".
- **03:19**, "There is no timing yet on a large transient model [check]." (SHOULD, caveat first). Fix: open the paragraph with "Transient tracking has been timed only on tutorial 08 (1,600 cells, 121 steps; §4.4) [check]: with one transport step per flow step it took 0.75 s forward and 0.80 s backward, factorising …".

## 04_verification.md

This section, especially §4.1–4.2, is the best voice model in the draft (see the end of this review).

- **04:5**, "(Table S4: per model)" (MUST, cross-reference clash).
  - Problem: Table S4 is per-well agreement (brief §2; 05:15 "per well, Table S4"). The Table 2 caption also sends readers to "Table S4" for errors per model.
  - Fix: number the per-model verification table separately (for example "Table S7"), or point to Text S1. Fix the Table 2 caption to match.
- **04:11**, "DISU builds of model 1 give the DIS results exactly" (SHOULD). "Builds" is coder register. Fix: "DISU versions of model 1".
- **04:15**, "a release-point error (from the finite number of release points) below 0.6 %" (SHOULD). The parenthesis interrupts the number. Fix: "…, a release-point error below 0.6 %, from the finite number of release points."
- **04:19**, "on models 6 (also with five transport sub-steps), 6 split into four models, 7 and 9" (SHOULD). Hard to parse. Fix: "on model 6 (also with five transport sub-steps, and split into four models) and on models 7 and 9".
- **04:23**, "at the other end of the run they differ by at least 0.40 and 0.52" (SHOULD). Unclear which end goes with which fraction. Fix: "at the start of the run c differs from G by at least 0.40, and at the end w differs from F by at least 0.52, so the agreement is not trivial".
- **04:27**, "compared west of the river, where no method mixes at the gaining river" (SHOULD). Unclear. Fix (check against DS §1): "compared only west of the river, so that the gaining river, where every method mixes, is left out".
- **04:31**, "kept the rate (§7)" (SHOULD). Fix: "but kept the $h^{0.5}$ rate (§7)".
- **04:41–45**: tense drifts within §4.4: "give", "was", "agreed", "differed", "nearly doubles", "move" (SHOULD; brief rule 9). Fix: past for the runs ("agreed", "differed", "nearly doubled", "moved"); present only where a figure is described ("Snapshots give … (Fig. 4a)").
- **04:47**, "The model has one layer, so each cell mixes over its whole saturated thickness" (SHOULD; caveat first, and one of the worst SHOULDs).
  - Problem: the caveat closes the section, after every number it qualifies.
  - Fix: move it into 04:37: "Tutorial 08 is a synthetic, one-layer model; the paper has no transient application to a real model (§7). With one layer each cell mixes over its whole saturated thickness, recharge cannot form a young layer on top of old water, and the shares below are those of a vertically mixed aquifer."

## 05_neversink.md

- **05:7**: a paragraph of two sentences (SHOULD). Merge it with 05:11.
- **05:11**, "and the closure check (§2.5) held to 1e-12 m³/d or less" (SHOULD).
  - Problem: code notation; the rest of the paper writes 10⁻¹². The same at 05:41 ("3e-12"). This paragraph also mixes the benchmark definition with cost.
  - Fix: write "10⁻¹² m³/d" and "3 × 10⁻¹² m³/d", and start a new paragraph at "A trace of nine destination groups …".
- **05:15**, "The F > 0.1 area is about twice the published area" (SHOULD; adjective where a number is available). Fix (check against NS §2): "The F > 0.1 area, 2,139 start cells or 2.2 times the published area, still misses 27 % of it."
- **05:15 onward**, "the published cells" (SHOULD). This short form is not in terms.md; the section heading also uses it. Fix: write "published contributing cells" at first use in each subsection and "published area" otherwise.
- **05:33**, "the weight-losing PRT zone P > 0.5, the particle reference of §4.3" (MUST, terminology).
  - Problem: terms.md reserves "reference" for the dispersion tests. Calling a Neversink delineation a "reference" undoes the section's own opening, "a benchmark, not a reference". 06:11 repeats it: "the PRT reference shares full mixing at weak sinks".
  - Fix (05:33): "the weight-losing PRT area (P > 0.5), which plays the role here that fine-grid PRT plays in §4.3".
  - Fix (06:11): "the PRT area shares full mixing at weak sinks".
- **05:33**, "The gap to the published cells is therefore mixing against advective paths, plus documented particle conventions." (SHOULD).
  - Problem: "mixing against advective paths" is opaque. The unhedged "is" also claims more than the abstract's "we attribute", even though the sentence follows two caveats.
  - Fix: "We therefore attribute the rest of the gap to the published area to mixing within cells, where particles follow advective paths, and to the documented particle conventions."
- **05:37**, "Over the ensemble (§5.5–5.6), the median area with the stream network is 1,534 …" (SHOULD). Ensemble numbers appear before the ensemble is introduced. Fix: move the sentence to the end of §5.5 (base) and §5.6 (maximum), or cut it to "the stream network enlarges the median area 1.7 times at base pumping (§5.5)".
- **05:41**, "are stored in run numbers sorted as text" (SHOULD). Unclear. Fix: "are numbered in text-sorted run order (1, 10, 100, 101, …)".
- **05:57**, "Weight-losing particles grow faster than full mixing" (SHOULD). Particles do not grow. Fix: "The area of weight-losing particles grows faster than the full-mixing area".
- **Fig. 9 caption against 05:41**: "61 realisations" against "60 realisations tested" (SHOULD; a consistency note for the numbers reviewer). Reconcile them, or say "60 realisations plus the calibrated model".

## 06_discussion.md

- **06:3**, "What follows is guidance … within that evidence, not general rules." (SHOULD).
  - Problem: this is the second negation-then-alternative in three sentences ("a benchmark, not a reference" is the first), and §6 has a third at 06:23.
  - Fix: "What follows is guidance for choosing a protection-zone method within that evidence."
- **06:7**, "combine the F = 0.5 area with particle tracking" (MUST, terminology and hard rule 3). No such threshold is used anywhere: the paper uses F > 0.5 (Neversink) or F ≥ 0.5 (dispersion tests). Fix: "combine the F > 0.5 area with particle tracking".
- **06:7**, "many destinations from one trace in seconds (§3.3)" (SHOULD). Fix: "in 2 to 3 s on Neversink (§5.1)".
- **06:9**, "Each of these steps is about a third, as large as or larger…" (MUST, misleading).
  - Problem: "a third" here means about 0.33 in overlap units. The next sentence uses "by a third" for a 35 % change in flow, so readers will take both as fractions.
  - Fix: "Each of these steps changes the overlap by about 0.33, as much as or more than the difference between weight-losing particles and full mixing (0.62 against 0.30 to 0.41). Release depth changes the water that particles deliver by 35 % (2,413 against 3,736 m³/d), while full mixing and weight-losing particles agree on it within 2 %."
- **06:11**, "and F = 0.5 as an advective core" (MUST; same threshold slip as 06:7). Fix: "and the F > 0.5 area as an advective core".
- **06:11**, "Two caveats apply: the PRT reference shares full mixing at weak sinks, …" (SHOULD; caveat first, duplication).
  - Problem: the caveats repeat 05:33 word for word, and they arrive after the numbers they qualify.
  - Fix: put a back-reference before the Neversink numbers: "On Neversink, within the two caveats of §5.3, the F > 0.1 area misses …". Delete the restated caveats.
- **06:11** and throughout §6: "zone" and "area" drift ("F ≥ 0.1 as a wide zone", "the 30-year zone", "PRT zone", "the zones above 0.5") (SHOULD; one term per concept). Fix: use "area" for any F- or P-threshold delineation ("F > 0.1 area", "PRT area (P > 0.5)"); keep "zone" for "protection zone", "capture zone" and the analytical capture zone. The same applies to Fig. 3 ("zone F ≥ 0.1") and Fig. S1 ("F > 0.1 and F > 0.5 zones").
- **06:7, 06:9, 06:11, 06:17**, "therefore" (SHOULD; a tic: four times in §6, three of them in paragraph closers). Fix: keep 06:9; drop the word at 06:7 ("Full mixing suits budget questions …"), 06:11 and 06:17 ("The group-level match is partly differences of both signs cancelling").
- **06:17**, "Both modes fall short of the published count" (MUST, banned word; terms.md: "net accounting" (not "net mode")). Fix: "Gross and net accounting both fall short of the published count …".
- **06:21**: a paragraph of eight sentences (SHOULD; the brief allows 3–7). Split after "only tracking answers the question".
- **06:21, 06:23**, "only tracking answers the question"; "Tracking needs porosity" (SHOULD).
  - Problem: in a paper that compares full mixing with particle tracking, bare "tracking" can be read as particle tracking.
  - Fix: "transient tracking" at least at the first use in each paragraph.
- **06:23**, "The post-processor adds backward tracking in time" (SHOULD). The draft otherwise says "the code". Fix: "The code adds …".
- **06:23**, "Use GWT where dispersion or reactions matter, and tracking where …" (SHOULD).
  - Problem: imperative mood, when the rest of §6 gives guidance as a named stance ("we would").
  - Fix: "We would use GWT where dispersion or reactions matter, and transient tracking where a well's catchment in time, or many sources at once, are needed."
- **06:29**: a paragraph of one sentence that repeats 05:43 (SHOULD). Merge it into 06:27 and land it on the consequence: "…, so variation of a published area between realisations need not reflect variation in the water reaching the wells."
- **06:31**, "Last, on reusing published benchmarks: two bookkeeping offsets …" (SHOULD). A signpost-and-colon template. Fix: "Two bookkeeping offsets in the published Monte Carlo contributing areas, a one-row shift and a text-sorted run order, had to be inferred before …".

## 07_limitations.md

- **07:3**, "The transition band narrows only as about h^0.5 (§4.3), so a finer grid spreads the edge of a zone over more cells." (SHOULD).
  - Problem: the statement is true in cell counts, but it reads as a paradox; the practical point is that refining the grid helps slowly. The exponent is also plain text, where §4 writes $h^{0.5}$.
  - Fix: "The transition band narrows only as about $h^{0.5}$ (§4.3): halving the cell size narrows it by about 30 %."

## 08_conclusions.md

- **08:3** (SHOULD). Sentences 3 and 5 run to about 60 words each. Split the last one so that the paragraph lands on the recommendation: "… and the treatment of streams changes the contributing area. A protection zone should therefore be reported with its method, its particle conventions and its threshold."

## 09_availability.md

No voice findings.

---

## Captions (display/)

Word counts, without the HTML comments, against the brief's target of about 120:

| caption | words |
|---|---|
| Table 1 | 242 |
| Fig. 1 | 344 |
| Fig. 2 | 339 |
| Fig. 3 | 177 |
| Fig. 4 | 429 |
| Fig. 6 | 147 |
| Fig. 7 | 175 |
| Fig. 9 | 126 |
| Fig. S1 | 332 |
| Table 3 notes | 168 |

Figs 5, 8 and 10 are within the limit.

- **C.md:15, Fig. 4 (429 words)** (SHOULD; the worst caption). Nearly every number repeats 04:41–45. Proposed caption (about 150 words):
  > **Figure 4.** Snapshots and transient tracking on the seasonal model of tutorial 08 (one layer of 1,600 cells of 50 m; 121 steps over 30 years; §4.4). A river (dashed) runs 100 m east of the supply well (triangle); constant heads on the west edge, 1.4 km away, bring regional inflow. (a) Snapshots: the well's water by source, each step traced on its own flows with storage release as a source term. (b) Transient tracking forward: the well's water by tagged source (recharge, river leakage, west-edge inflow, initial water); dashed line, the initial water's share of all water pumped so far. (c) Steady backward fraction F for the flows of the first step. (d–f) Backward tracking in time: for the water in each cell at the start, the fraction that leaves through the well within 30 years (w), leaves through the river, or is still stored; the three add up to 1 in every cell. Default "flow" volumes, four transport sub-steps per flow step.
- **C.md:3, Fig. 2 (339 words)** (SHOULD). The caption restates Table 2 and §4.1–4.2. "Machine epsilon" is numerics jargon. Proposed caption:
  > **Figure 2.** Largest error of each verification check on the synthetic test models (markers), against machine precision (dashed line) and the test tolerance (grey bars); values and error measures in Table 2. Upper block: steady and snapshot checks. Lower block: transient tracking checks. The steady G against GWT (model 7) and the steady limits (model 10) are limited by the flow solver tolerance. "Exact" marks errors of zero.
- **B.md:3, Fig. 1 (344 words)** (SHOULD).
  - In (a), drop the restated rule for F ("All outflows carry the same water, so …"); it is the "In words:" of §2.2.
  - Shorten (d) to: "(d) Transient models. Left: a snapshot traces one time step as a steady state on its own flows, with storage release as a source term; nothing is carried to the next step. Right: transient tracking carries the cell's water volume $V_i$ and tagged fraction $c_i$ from step to step; storage terms change $V_i$ and are not source or sink terms. Shading: tagged fraction. The cell budget error (not drawn) leaves at $c_i^{n+1}$."
  - In (b), "recharge of 1 on every cell" lacks units.
- **E.md:3, Fig. S1 (332 words)** (SHOULD). Move the SV_227 explanation, the 4,621 m³/d double count and the seeding counts to Text S or the table note. The "not an independent advective zone" caveat should open (b–d), not close it (caveat first).
- **A.md:3, Table 1 (242 words)** (SHOULD). Drop the restated definitions of F and G, which already appear in the row labels and the text, and the meta-sentence on [check]; keep the [check] mark itself in the cell. Target about 120 words.
- **C.md:9, Fig. 3** (SHOULD). "the zone F ≥ 0.1" and "the zone F ≥ 0.5": use "area" (see 06:11).
- **D.md:11, Fig. 7 (175 words)** (SHOULD). Cut the definitions of plain and weight-losing particles to a back-reference ("§5.3"); the published-starts conventions can point to Table 3.

---

## Consistency of voice across the five writers

- **A (front, §1)**: fluent and well sourced. Paragraphs land, for example "all three are written for continuous transport". The weaknesses are terms used before they are defined (destination, flow loop) and one buried hedge (01:15).
- **B (§2)**: reads least like the rest. Long sentences with stacked appositives and parentheticals, symbol-initial sentences, several points per paragraph, five negation-then-alternatives, and linear-algebra and coder words ("factorisation", "assembly", "the solve") outside §2.4. The "In words:" translations are good and should stay.
- **C (§3–4)**: the plainest and most consistent. Topic sentences state the point ("The two 'flow'-volume balances test different things."), numbers carry the claims, and paragraphs land. Its weaknesses are tense drift in §4.4 and one caveat placed last (04:47).
- **D (§5)**: close to C. It leads with numbers and hedges well ("this reading is untested"; "we infer, without tracing it cell by cell"). Its weaknesses are code notation (1e-12), some cramming (05:11, 05:37) and the "reference" slip at 05:33.
- **E (§6–9)**: strong caveat-first openings (06:3, 06:21, 07:5) and honest stances ("we would"). Its weaknesses are a "therefore" tic, three negation pairs in §6, an imperative at 06:23, the "a third" ambiguity and the F = 0.5 slips.

**Best model:** §4.1–4.2 (C), with §7 (E) as the model for caveats. In a second pass, bring §2 toward §4.1's sentence length (one claim per sentence, one point per paragraph) without touching its equations or "In words:" paragraphs.

---

## Top five changes

1. **Fix the terminology slips that undo the paper's own distinctions:**
   - "F = 0.5" to "F > 0.5" (06:7, 06:11);
   - "reference" for the Neversink PRT area to "PRT area (P > 0.5)" (05:33, 06:11);
   - "Both modes" to "Gross and net accounting both" (06:17);
   - one term, "area", for threshold delineations (§6, Figs 3 and S1);
   - "transient tracking" rather than bare "tracking" in §6.3;
   - define MF6, GWT, GWF and SFR at first use;
   - resolve the Table S4 clash (04:5 and the Table 2 caption against 05:15).
2. **Cut the captions of Figs 1, 2 and 4, Fig. S1 and Table 1** to about 120–150 words, moving numbers and explanations to the text (proposed Fig. 2 and Fig. 4 captions above). This also saves page charges.
3. **Thin §2's prose:**
   - split 02:33 and 02:37;
   - use the brief's one-sentence head-on for gross against net;
   - replace the duplicated novelty paragraph at 02:79 with two sentences;
   - drop "factorisation", "assembly" and "the solve" outside §2.4;
   - cut negation pairs to the three the brief mandates.
   This brings §2 nearer its 1,900-word budget.
4. **Put caveats first:**
   - move the one-layer caveat to the start of §4.4 (04:47 to 04:37);
   - lead §3.3's transient timing with "timed only on tutorial 08";
   - in §6.1, replace the restated PRT caveats with a back-reference placed before the Neversink numbers.
5. **Clean up §6:**
   - rewrite the "about a third … by a third" pair at 06:9 with 0.33 and 35 %;
   - drop three of the four uses of "therefore";
   - replace the imperative "Use GWT …" with "We would use …";
   - write "the code", not "the post-processor";
   - split 06:21;
   - merge the one-sentence paragraph at 06:29;
   - remove "Last, on …:".
