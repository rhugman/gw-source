# Review of the reduced draft, round 1

Scope: `docs/paper/draft_reduced/` (sections, display, si), checked against `docs/paper/draft/` and `export_reduced/paper_draft.md`. Paths below are relative to `docs/paper/draft_reduced/`. Line numbers are paragraph lines of the section files.

Verdict: every number in the reduced main text and captions matches the full draft and its evidence. The problems come from the cuts. Four caveats that kept claims honest were dropped. A few paragraphs lost the sentence that tied them together. Two SI cross-references point to full-draft section numbers.

## 1. Facts

1. **Selective reporting in 4.3** (`sections/04_examples.md:33`). The reduced text keeps the favourable check (93 % against 79 % of the true area) and drops the unfavourable one. The full draft (`draft/sections/04c_examples.md:15`) adds that 86–87 % of cells with probability ≥ 0.9 lie inside the true area in both ensembles: "That share did not improve." As cut, the paragraph opens "not necessarily a correct one" and then gives only evidence that the posterior is better. Fix: restore the 86–87 % sentence and "That share did not improve."
2. **History-matching claim is stronger than the full draft makes it** (`00_front.md:7`, `06_tradeoffs.md:3`). The caveat that the trace ran after PEST++ finished, and that tracing inside each PEST++ run is untested, now sits only in a comment (`04_examples.md:33`). Fix: restore it as one sentence at the end of 4.3: "Here the trace ran on each realisation after PEST++ had finished. We have not tested running it inside each PEST++ model run."
3. **Particle totals made to sound like a test** (`04_examples.md:11`). The full draft says the 799.9 m³/d total "says little about the area". The reduced text says "as any method that conserves water must", which keeps the reason but drops the conclusion. In 4.4 (`04_examples.md:37`), 45.7 against 45.9 years appears with no caveat. Text S9 says "This agreement is not an independent test." The abstract then presents both as matches. Fix: in 4.1, add "That total says little about the area." In 4.4, add "Both follow from the same water volume, so this agreement is not an independent test."
4. **Visser et al. misdescribed** (`04_examples.md:11`). "Visser et al. (2009) and Winston et al. (2018) reduce particle weights at sinks". The full draft says that Visser *split particles at weak sinks* to derive travel times. Fix: "Visser et al. (2009) split particles at weak sinks to derive travel times. Winston et al. (2018) reduce particle weights at sinks in a solute-transport method."
5. **F > 0.1 benefit given without its cost** (`06_tradeoffs.md:7`). "missed at most 0.1 %" now stands without "8 to 90 % larger" (full draft 4.1 and 6). Fix: append "at the cost of 8–90 % more area."
6. **Transient-tracking novelty, by omission.** The main text no longer cites hydraulic mixing cells (Partington et al. 2011), which carry mixed water through storage forward in time. Without them, `01_introduction.md:11` and `02_methods.md:29` read as if forward tracking through storage were new. The full draft says forward tracking is not new and that backward tracking in time is the addition. Fix: add to 2.4 "Hydraulic mixing cells carry mixed water through storage in integrated models in a similar way (Partington et al. 2011)." Then move Partington 2011 to the main reference list.
7. **"Nine well groups"** (`00_front.md:7`; `03_software.md:5`). This conflicts with "eight priority wells" (Section 5). The groups are never defined. Fix in Section 3: "nine destination groups (each of the eight wells alone and all eight together)". Also restore the hardware for the 2–3 s and 2.5 GB figures ("Apple M4 Max, 64 GB"). A reviewer will ask for it.
8. **Volumes behind the GWT match** (`04_examples.md:21`; abstract "with the same water volumes"). The shares in 4.2 use the default volumes and four sub-steps. The GWT match uses GWT's volumes and one step. Neither choice is explained, and the reader cannot tell whether the shares would change. Fix: restore from the full draft (`04b_examples.md:37`): "The default volumes keep every cell's water balance exact. Here they change the fractions by less than 0.004."
9. Stale evidence: the abstract's evidence comment (`00_front.md:9`) and its inline comment ("§3.4") cite full-draft section numbers (2.6, 2.7, 4.9, 4.10, 7). The comment at `06_tradeoffs.md:9` lost its parenthetical (what pp. 76–78 support). Fix: renumber both, and copy the parenthetical back from the full draft.

## 2. Story

1. **Neversink "why they differ" lost its links** (`05_neversink.md`). The three reasons are still there (particle settings, mixing against one path, weak sinks). Gaps:
   - "Our areas" (`:5`) is never defined. Which model? The calibrated model, also undefined anywhere in the reduced draft. Which accounting, and are streams cells or a network? Fix: before `:5`, add "We traced the eight wells in the calibrated model, the realisation with the base parameters, with gross accounting and streams as cells."
   - The 42 % sentence (`:7`) floats. Fix: follow it with "So under full mixing many published cells fall below F = 0.5."
   - The size of the weak-sink effect moved to the SI. Fix: restore "Net accounting, which treats weak-sink wells as stopping particles do, raises the F > 0.5 overlap only from 0.41 to 0.44 (Table S3)." This shows that mixing, not weak sinks, is the main reason.
   - `:9` dropped "Where the reach gains water, the stream is a weak sink." Without it, the reader cannot see why a buried stream cell is a weak sink. Restore it.
   - The section ends with no practical meaning. Fix: close with "An overlap of 0.41 should be read against the 0.62–0.998 range that particle settings alone produce."
2. **Intro gap for transient flow is gone** (`01_introduction.md`). Nothing says why snapshots or forward-only transport fall short. That is the motivation for backward tracking in time. Fix: one sentence from the full draft: "As documented, the unit-concentration method steps forward in time only."
3. **Intro does not promise the checks.** The roadmap paragraph was cut. The "checked against other approaches" pillar first appears in the abstract and is never announced in the text. Fix: end Section 1 with "Section 4 works through ten examples, each with a check against another approach. Section 5 applies the code to a published regional model."
4. **4.4 is a list of numbers without checks** (`04_examples.md:37`). It does not support the abstract's "Each checks … against other commonly used approaches". Fix: name the check in each sentence:
   - forward trace: "matches a steady GWT run to 4.2 × 10⁻¹³";
   - grids: "DISU gives the DIS result cell for cell";
   - networks: "a model split in three matches the single model to 2 × 10⁻¹³";
   - Bedekar: name the sources (lateral inflow, recharge, stream);
   - Voronoi: say what 186 m against 121 m means (a wider edge band).
5. **Limitations a reviewer will look for are missing from the main text.** These are movers between models (MVE) not read, DISU without vertices giving no maps, PRT not on DISU, and transient memory. Fix: one sentence in Section 6.
6. **Choice of accounting has no advice.** 2.2 defines gross and net accounting, but no sentence says when to use net (to reproduce a FlowSource study). Fix: add that sentence to 2.2.
7. **Method figure.** I agree it is the strongest addition. The reduced main text has one equation and no picture of mixing at a weak sink. Panels (b) and (c) of Figure S1 (the eight-cell F and gross against net) would carry it.

## 3. Cross-references

1. `si/C.md:129` (Text S5): "Section 4.9 traces the well…" should read **Section 4.3**.
2. `si/G_examples.md:5` (Text S3): "summarised in Section 4.4" should read **Section 4.1**. The accounting example is in 4.1.
3. `04_examples.md:3`: "Three of ten worked examples follow". But 4.1 also carries the accounting example, and 4.4's "other seven" includes it. Fix: "Four of the ten worked examples follow. Section 4.4 summarises the other six."
4. `06_tradeoffs.md:5`: {SI: numerical dispersion} resolves to **Figure S4** ("maps and time steps"). The 30 % result is plotted in Figure S17, which is cited nowhere in the main text. Fix: cite {SI: numerical dispersion against cell size} as well, so that it is numbered next to S4.
5. `si/B.md:141`: "follows from Eqs. (S13) and (S7)". The derivation uses S13 and **S14**.
6. `si/B.md:3`: "{SI: method schematic} illustrates the method. It then gives net accounting…". Here "It" now reads as the figure. Move the figure sentence to the end of the paragraph.
7. `si/G_examples.md:123` and `si/B.md` ("Long steps … (Section 4.2)"): Section 4.2 no longer shows early arrival. Point to Text S4 instead.
8. `06_tradeoffs.md:9`: "(Section 4.4)" for totals should be "(Sections 4.1 and 4.4)".
9. SI terms with no definition: **calibrated model** (Table S3, Figures S3, S5, S7, Text S12) and **expected area** (used in Text S7 before Table S3 defines it). Fix: define both in Text S2.
10. References: the main list covers every main-text citation (17). The SI-only list covers every SI-only citation, and every entry is cited. No gaps. Display captions: Figures 1–3 are cited in order and point to the right panels. Fig. 2 caption: say "(b)" for the dashed line, as Text S4 does.

## 4. Prose rules

The rules are mostly met: no semicolons in prose, no filler adverbs, no "credit", and "steady-state" is correct. Issues:

1. **Contradiction from squeezing** (`01_introduction.md:9`). "Under full mixing, a weak sink takes its share of the cell's water." The next sentences say FlowSource counts *all* the water. Fix: "Under full mixing, a weak sink can take just its share of the cell's water, and the rest passes on." Then introduce the two accountings as two rules.
2. `01_introduction.md:7` "But particles need a rule at weak sinks." The paragraph before lists four families, so "But" has no antecedent. Fix: "Particle tracking has one difficulty at weak sinks."
3. Undefined at first use:
   - "source protection zones" (`01:9`). Restore "These zones restrict activities that could pollute the water a supply well pumps."
   - what a unit concentration means (`01:5`). Restore "A cell's concentration is then the share of its water that came from that source."
   - "SFR" (`05:3`). Write "Streamflow Routing (SFR)".
   - "transport sub-steps" (`04:17`). Add "Sub-steps shorten the transport step without changing the flow model."
   - "GWT's water volumes" (`04:21`).
   - "a separate synthetic true aquifer" (`04:29`). Restore "A separate random field stands for the true aquifer. Its heads in 40 cells, with added noise, are the measurements."
4. Squeezed logic:
   - `04:17` "The run starts from a steady state in which the well already pumps." The reason was cut. Add "Initial water is therefore not water from before pumping began."
   - `04:19` "A layered model may give other shares." Restore the reason ("With one layer, the model cannot hold young water above old water").
   - `04:13` "Accounting matters only at weak sinks." This opens abruptly and never states the gross figure. Add "Gross accounting attributes the 5 m³/d it pumps."
5. `02_methods.md:15`: "The sum over all cells of F times each cell's inflow…" sits in the forward-trace paragraph, after G, so readers will think G does this. Fix: move it to the end of the backward paragraph, starting "The backward trace also splits…".
6. `02_methods.md:27`: "It therefore assumes that water reaches the well in the same step it entered." The "therefore" does not follow from treating storage as a source term. Fix: "A snapshot traces each step as if its flows were steady. It has no travel lag. Water released from storage appears as a source of unknown origin."
7. Two-part sentences:
   - `00_front.md:7` "They matched particle tracking in totals and mean travel times, not cell by cell at area edges." Change to: "… mean travel times. At the edges of areas the two differ cell by cell."
   - `01:11` "…risk-based studies, which run an ensemble…". Split it: "Risk-based studies run an ensemble … (Fienen et al. 2022). The code is fast enough to trace every member."
   - `06:7` "It should be reported with the area, as should the accounting." Change to "Both the threshold and the accounting should be reported with the area."
8. Appositive tail: `04:11` "Particles start from every source term in cells with F > 0, each weighted by a share of the term's flow." Change to "… with F > 0. Each carries a share of its term's flow as a weight."
9. Polite framing: `01:9` "As published, neither program reads MODFLOW 6 output." Softer: "Both programs predate MODFLOW 6."
10. `06_tradeoffs.md` ends on a hedge, with no closing line for a section titled "conclusions". Add a final advice sentence, or retitle to "Trade-offs".

## 5. Budget

`python studies/paper/page_estimate.py docs/paper/draft docs/paper/draft_reduced` gives **6.00 pages** (prose 4.18, Figure 2 0.61, Figures 1 and 3 0.38 each, references 0.49, Eq. 1 0.15). There is no slack. The fixes above add about 150–200 words (0.2 page), so the space has to be found first.

Schematic cost: single-column 0.115 page of area plus a ~60-word caption, about 0.19 page. Double-column is about 0.5 page. At single width, use only panels (b) and (c), or the labels will be too small.

Where to find 0.3–0.5 page:
- Figure 2 (0.54 of area) is the biggest item. Drop panel (c), because the text compares against it only in words. Or reflow to two rows of three. Saves about 0.1–0.15.
- `01_introduction.md:3` repeats the abstract's opening questions almost word for word. Cut it to one sentence. Saves about 0.05.
- 2.2 re-defines net and gross accounting after Section 1 has already defined them. Keep one sentence plus the advice sentence. Saves about 0.04.
- `03_software.md:3` lists selections and exports that Table S2 already gives. Saves about 0.05.
- If the schematic returns with panel (b), shorten the "In words" and eight-cell sentences of 2.1. Saves about 0.03.
- References: cite Black and Foley (2013) and Corson-Dosch et al. (2022) only in the SI. Saves about 0.05.
- `05_neversink.md:3`: merge the two MODPATH set-up sentences. Saves about 0.03.

Total: about 0.35–0.4 page. That covers the restored caveats, or the schematic, but not both. The author should choose.
