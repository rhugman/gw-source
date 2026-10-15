# Orchestrator decisions for round 4 (after the author's review of draft v6)

These decisions override `brief.md`, `decisions_r1.md` and `decisions_r2.md` where they differ. The author's comments are in `reviews/user_r3_comments.md`. Address every comment in your sections.

## 1. Length: relax the cap
1. The main text may reach **8,500 words**, not 7,500. Use the extra words to explain, not to add results. Budgets (hard limits):

   | Section | Words |
   |---|---|
   | §1 | 1,050 |
   | §2 | 2,000 |
   | §3 | 500 |
   | §4 | 1,200 |
   | §5 | 1,500 |
   | §6 | 1,350 |
   | §7 | 350 |
   | §8 | 250 |
   | §9 | 150 |

   The abstract stays at 250 words or fewer.

## 2. Prose rules (new; they come from the author's comments and apply to every sentence)
2. **One idea per sentence.** No two-part sentences that join two claims with a semicolon, a colon or ", and". Split them.
   - Don't: "Particle tracking is the standard tool, and one forward run serves every well."
   - Do: "Particle tracking is the standard tool for delineating contributing areas. One forward run serves every well in the model."
3. **No "We do X by Y" or "We write it as …, solved …" constructions.** Write the way a hydrogeologist would explain it to a colleague.
4. **Explain every uncommon concept when it first appears, in plain words, and say why the reader should care.** Assume the reader is a groundwater modeller who knows MODFLOW and MODPATH but not linear algebra, PRT options or our vocabulary. Terms that need this: full mixing, weak sink, flow loops, backward and forward fraction (F and G), identity (prefer "a check that must hold exactly"), closure check, weight-losing particles, flow-weighted release, the overlap score (Jaccard index), thresholds on F, strict and non-strict thresholds, net and gross accounting, snapshots, transient tracking, backward tracking in time, buried stream cells, draping.
5. **Each paragraph chains from the last.** Open each paragraph with the question or need it answers. A reader should always know why they are reading it.
6. No coined shorthand. Drop "core" and "core area". Say what the cells are: "cells where more than half the water ends at the well".
7. Keep the voice-hugman rules: numbers, not adjectives; no filler; honest hedges as named stances. And keep GMDSI and groundwater vocabulary.

## 3. Tutorials and the repository
8. Never write "tutorial", "tutorial 02" or "tutorial 08" in the main text, captions or figures.
   - Call them **example models**, and describe each in the paper in enough detail to read its figures.
     - Accounting example: the eight-cell model of Fig. 1.
     - **Seasonal example model**: the transient model of §4.4 and Fig. 4. Describe it in §4.4: one layer, size, boundaries, pumping, seasonal recharge, length of run.
   - Put full set-ups in the SI under a new item, `{SI: example and test models}`. It holds the ten test models of §4.1 (one row each: grid type, size, packages, steady or transient, what it tests) and the two example models.
   - Writer C owns that SI item and adds it to `si/numbering.md` as a Text item.
   - §9 says once that the example and test models ship with the code as tutorials and tests.

## 4. Framing of prior work (abstract, §1, §8)
9. **Be polite.**
   - Don't write that FlowSource "has not been described in a journal article". Say what it does, that it is not open source, and what we add.
   - What we add: an open-source implementation; exact solves including flow loops; gross accounting; budget checks on every trace; all MODFLOW 6 grid types, boundary packages, multi-model simulations and package networks; transient tracking with backward tracking in time; speed (2–3 s on 1.68 million cells).
10. **Abstract.**
    - Open for a non-technical reader: protection zones and why water managers need contributing areas.
    - Then the existing approaches (particle tracking, full mixing as in FlowSource and MODALL) and what each gives.
    - Then what this paper adds (item 9).
    - Then the two tests in plain words:
      - checked against the water budget and against MODFLOW 6 transport;
      - on a published real-world regional model (1.68 million cells), traces take 2–3 s, and the areas fall within the range that particle tracking gives under different particle settings.
    - The seasonal example result (81 %) may stay only if introduced as what backward tracking in time can answer ("how much of the pumped water was already stored"). Otherwise drop it.
11. **Title:** say what the tool gives the user. Example: "Contributing areas, water-budget checks and the age of pumped water from MODFLOW 6 flows". Offer the author two or three options in a comment at the top of 00_front.md.
12. **Introduction:**
    - Paragraph 1: the decision context.
    - Paragraph 2: an overview naming the families of methods (particle tracking, full-mixing flow tracing, transport with tagged water, adjoint and age methods) before any detail.
    - Then one paragraph per family, each ending on its gap.
    - Weak sinks come in as the reason particle tracking needs a rule: what a weak sink is, and why a stop-or-pass choice changes the area.
    - The FlowSource paragraph is woven into the full-mixing paragraph, not left standing alone.
    - Make the contrast with Leake's capture fraction explicit in two or three sentences:
      - Leake's capture fraction is the change in budget terms caused by pumping, from two runs;
      - F is the share of water that ends at the well, from one run.

## 5. Methods (§2)
13. **Equations:** number the §2.1 budget equation and the per-cell rule of §2.2 too. The matrix form becomes Eq. (3), and later equations shift.
14. **Flow loops:** define them where they first appear. Water that circulates between cells (for example around a well pair, or between layers) means no ordering of cells is purely downstream. Then say why that matters: a one-pass sweep cannot handle them, and an exact solve can.
15. **"For the specialist"** goes. Keep the one technical sentence in §2.4, and introduce it plainly.
16. **Merge §2.7 into §2.8.**
    - Snapshots are how existing full-mixing methods treat transient models: each time step's flows traced as if steady.
    - Transient tracking is our extension: water is carried through storage from step to step.
    - Renumber the later subsections.
17. **The flow-error sentence:** explain in two plain sentences that MODFLOW's cell budget never balances exactly. The small error is allowed to leave each cell carrying that cell's own mix of water, which is how GWT handles it.
18. **§2.9:** say "sink" where the text says "well", where the method is general.
19. **Net accounting:** rewrite the "bookkeeping of FlowSource" sentence. Net accounting credits a sink with all the water that passes through its cell, as FlowSource does. Gross accounting credits only the water the sink takes. Show it on the Fig. 1 example in words.

## 6. Implementation and verification (§3–4)
20. **PRT:** introduce it in §3.2 with one lead sentence. We also write release points for MODFLOW 6 particle tracking (PRT), so that the same problem can be run with particles and the two methods compared (§5.3). Explain weight-losing particles there in plain words: each particle carries a weight, the flow it represents, and loses the share each sink takes as it passes.
21. **§3.3 "Compute cost":** rename it. Report run time and memory. Writer C uses the measured peak memory of the Neversink trace if figure agent F6 supplies it (in `reviews/r4_memory.md`). Otherwise keep the per-group estimate and mark it [check: measured peak memory].
22. **Fig. 2:** add two or three sentences in §4.1 on how to read it: what each marker is, what the dashed line is, and what "at machine precision" means for the user (the check passes, and any larger error would flag a problem). Replace "identities" in the caption with "checks that must hold exactly".
23. **§4.2:** say why each result matters to the user. For example: transient tracking reduces to the steady result when flows don't change, so the two methods agree and the user can trust either.
24. **§4.3 thresholds:**
    - Define F again in the sentence ("the share of a cell's water that ends at the well").
    - Say what F ≥ 0.1 and F > 0.1 mean in practice.
    - Explain that the strict/non-strict difference changes no result. If that is the case, consider dropping the strict/non-strict note from the main text and keeping it in the SI.
25. **§4.4:** describe the seasonal example model (item 8) before its results, and say why the result matters. Backward tracking in time tells a manager how much of the pumped water was stored in the aquifer at the start, which particles and snapshots do not give directly.

## 7. Neversink (§5)
26. **Purpose up front.** Say early, and in plain words, why we compare with particle tracking at all. The published areas come from one set of particle settings, so they are not ground truth. We rerun particles on the same flow field to show how much the particle settings alone move the area (0.29–0.998). We also run a like-for-like check: particles that lose weight at sinks as full mixing does. §5.3 opens with this purpose.
27. **§5.2:** explain the overlap score in plain words (the cells both areas share, as a share of all cells in either area; 1 = identical, 0 = no common cells). Explain what F > 0.5 and F > 0.1 areas are. Drop "core".
28. **§5.3:**
    - Move "plain particles" and the 2.6 times diagnostic to the SI.
    - Explain F against P in one or two sentences: both are the share of a cell's water that reaches the wells, one by mixing, one along particle paths.
    - Mixing spreads water more widely, so F is lower and spread over more cells. That is why F > 0.1 is needed to cover the P > 0.5 area.
29. **SI cross-references:** the first one in the paper reads "(Supporting Information, Text S1)". Later ones may read "(Text S6)". Writer A owns the first one if it falls in §1; otherwise the first writer in order whose section has an SI citation.
30. **§5.5:**
    - Drop "in 76 min on six processes, with closure to 3 × 10⁻¹² m³/d in each".
    - Explain what is compared, why it matters and why the two differ:
      - the published probability of contribution is the share of 357 Monte Carlo particle areas that contain a cell; it is an uncertainty product for protection zones;
      - mean F over the 358 realisations is our counterpart;
      - in the S region, the published area changes between realisations while the water reaching the wells does not, because particles stop at buried streams.
31. **§5.6:** give context for the growth result. As pumping rises, the area reaches buried stream cells where published particles stop. Full mixing passes through them, so its area grows faster.

## 8. Discussion, limitations, conclusions (§6–9)
32. **§6 opening:** no hedging opener. Open with a framing of the outcomes:
    - full mixing gives areas in the range particle tracking gives;
    - the checks hold exactly;
    - transient tracking answers questions snapshots cannot.
   Then the subsections discuss what these mean for practice.
33. **§6.1:** "published contributing cells" becomes "the published Neversink contributing cells" at first use in §6.
34. **§6.3:** split the two-part sentences, and replace "tutorial 08" with "the seasonal example model (Section 4.4)".
35. **§6.5:** rewrite it as discussion, not a repeat of results. It is practical advice for a modeller drawing a protection zone, and the advice comes first. Each piece of advice has one sentence of reason and a pointer to the evidence (section or figure), not the numbers again:
    - which area to draw and when (more than half the water: the cells most certainly in; one tenth: a wider, cautious area);
    - when to add a particle check (where the area ends at a weak sink such as a buried stream);
    - which accounting to use (gross by default; net only to reproduce FlowSource studies);
    - how to treat streams (a model choice that changes the area; state the choice);
    - when to use transient tracking (time-limited zones; the share of stored water).
36. **§7:** rewrite it as limitations of the method:
    - full mixing within a cell;
    - grid spacing (numerical spreading);
    - memory of transient tracking;
    - steady flow per stress period;
    - porosity not needed for fractions but needed for times;
    - weak sinks still need a choice at the reporting stage.
   Drop paper-scope limits, or keep only one sentence on testing (no transient real-world application yet).
37. **§8:** open with what we extended (item 9). Make the Neversink claim generic ("tested against a published real-world regional model").
38. **§9:** says once that the example and test models ship as tutorials and tests (item 8).

## 9. Figures (figure agents)
39. **Fig. 1 (F1):**
    - simplify it: fewer labels, one idea per panel;
    - remove every "tutorial" label;
    - keep the eight-cell example numbers used in the text (F = 6/11; 5.0 vs 33.7 m³/d).
40. **Fig. 6 (F6):**
    - colour map: a perceptual sequential map with clear steps (e.g. viridis or cividis), with the 0.1 and 0.5 limits visible;
    - add the well locations and the stream (SFR) reaches;
    - use the same window size and one scale for every panel (shared axes are not possible, since each panel is centred on a different well; use equal extents and one scale bar);
    - F6 also measures the peak memory of one steady nine-group Neversink trace, and writes it to `reviews/r4_memory.md`.

## 10. Unchanged
41. These stay:
    - the product name in the paper text;
    - citations only of formally citable sources;
    - every [check] that is still open;
    - every number traced to its evidence comment;
    - SI names from `si/numbering.md`, plus the one new item in decision 8.
