# Writers' brief: full-mixing flow tracing for MODFLOW 6 (*Groundwater* research paper)

Branch `paper-draft`, local only: never push, do not commit. Each writer writes only `docs/paper/draft/sections/<letter>_<name>.md`. Sources of truth: `docs/paper/outline.md` (claims, numbers), `docs/paper/terms.md` (wording), figure captions in `docs/paper/figures/README_method.md` and `README.md`, Tables 1–2 in `docs/paper/figures/`, `docs/neversink_study.md` (NS), `docs/dispersion_study.md` (DS), `PLAN.md`, tutorials 02, 05, 06, 08. On structure follow this brief; on numbers follow the evidence file and flag disagreements [check].

## 1. Journal rules

NGWA pages (Instructions for Authors; Types of Articles; Reference Samples), read 2026-10-10.

- **Type:** Research Paper. First six published pages free (seven for an NGWA-member corresponding author), then US$250 per page. No fixed word limit: subheadings, equations, figures with captions and tables reduce the allowance in proportion. The Neversink paper (Fienen et al. 2022) ran to 16 pages (*Groundwater* 60, no. 1: 71–86).
- **Our limit:** 7,500 words of main text (Introduction to Code and Data Availability; captions, tables, abstract, acknowledgements and references not counted). With 10 figures and 3 tables this is about 15–16 pages. Keep to your budget ±5 %.
- **Title:** fewer than 100 characters with spaces (the outline's has ~140). Recommended (96): *Full-mixing flow tracing for MODFLOW 6: contributing areas, budget checks and transient tracking*.
- **Article Impact Statement:** ≤ 140 characters with spaces; why read it, not a mini-abstract.
- **Abstract:** fewer than 250 words, one paragraph (contribution, methods, results). Start from outline §4.
- **Key words:** not in NGWA guidance; prepare five or six in case the submission system asks.
- **Parts, in order:** title; Article Impact Statement; Abstract; sections of §2 below; Acknowledgments (significant contributions, funding, permission, reviews only); References; Supporting Information.
- **Data availability:** Wiley requires a statement for research articles; *Groundwater* encourages repository deposit. §9 is that statement.
- **References:** Harvard author–year: (Pollock 2016), (Foley and Black 2013), (Fienen et al. 2022), (Jones 1999a, 1999b). List alphabetical, then chronological; "Surname, I., and I. Surname. Year. Title. *Journal* 32, no. 4: 257–269." Other types per NGWA reference samples. No limited-access reports.
- **Figures and tables:** no count limit; 8.25 or 17.15 cm wide, ≥ 300 dpi; tables inline. No footnotes except in tables. Define symbols and abbreviations at first use.

## 2. Structure and word budget

| § | section | words | first cited |
|---|---|---|---|
| 1 | Introduction (A) | 900 | Table 1 |
| 2 | Methods (B) | 1,900 | |
| 2.1 | Cells, flows, source and sink terms | 200 | Fig. 1a |
| 2.2 | Backward and forward fractions | 350 | Fig. 1b |
| 2.3 | Gross and net accounting | 200 | Fig. 1c |
| 2.4 | Solution in flow order | 150 | |
| 2.5 | Water-budget checks | 250 | |
| 2.6 | Mean travel time | 100 | |
| 2.7 | Transient models: snapshots | 150 | Fig. 1d |
| 2.8 | Transient tracking through storage; water volumes | 300 | |
| 2.9 | Backward tracking in time | 200 | |
| 3 | Implementation (C) | 450 | |
| 3.1 | MF6 output, package networks, multi-model | 200 | |
| 3.2 | Selections, exports, ensembles, sub-steps, PRT routine | 100 | |
| 3.3 | Cost | 150 | |
| 4 | Verification and Transient Demonstration (C) | 1,250 | |
| 4.1 | Steady and snapshot checks | 350 | Fig. 2, Table 2 |
| 4.2 | Transient tracking checks | 250 | |
| 4.3 | Numerical dispersion | 250 | Fig. 3 |
| 4.4 | Transient demonstration (tutorial 08) | 400 | Fig. 4 |
| 5 | Demonstration and Benchmark: the Neversink Model (D) | 1,400 | |
| 5.1 | Model and benchmark | 200 | Fig. 5 |
| 5.2 | Calibrated model against the published cells | 300 | Fig. 6a–c, Table 3 |
| 5.3 | Particle tracking on the same flow field | 300 | Fig. 7 |
| 5.4 | Streams as cells and as a stream network | 150 | Fig. 6d–f |
| 5.5 | Ensemble at base pumping | 200 | Fig. 8 |
| 5.6 | Pumping scenarios | 250 | Figs 9, 10 |
| 6 | Discussion (E) | 1,000 | Fig. S1 |
| 7 | Limitations (E) | 300 | |
| 8 | Conclusions (E) | 200 | |
| 9 | Code and Data Availability (E) | 100 | |
| | **Total** | **7,500** | |

**Tables.** Table 1: `table1_methods.md` as is. Table 2: the two model × check parts of `verification_table.md`. Table 3 (new; merges outline Tables 3 and 4): delineations of the eight wells' area on one flow field. Rows: full mixing gross (F > 0.1, F > 0.5, area-matched) and net; PRT plain and weight-losing by release depth; PRT from published starts, MF6 defaults to published conventions. Columns: overlap, expected area (cells), flow reaching the wells (m³/d). D drafts it from NS Tables 1, 3 and the §3 reproduction table and the CSVs behind them.

**Supporting Information.** Tables S1–S3: outline Tables 5–7 (NS Tables 4–6). S4–S6: per-well agreement (NS Table 2), gross vs net per well (NS 2a–2b), PRT-zone envelope (NS 3a). Fig. S1. Texts S1–S5: verification error measures; diagnosis of the first PRT runs; end states of published particles; the Monte Carlo bookkeeping offsets and inferred scenario rule; faster growth of weight-losing particles (NS Table 7). DS Figs 1, 3, 5. If pages must fall, move Figs 9–10 to SI first and keep their numbers in §5.6.

## 3. Section assignments

All writers read outline §1, §3, §5–7, terms.md, this brief, and the captions of their figures. Each claim keeps the evidence path the outline gives it.

**A: title, impact statement, abstract, Introduction.**
- Carries outline §1, §4, §5.1. Introduction moves: (1) contributing areas, and particle tracking's trouble with weak sinks, transient flow and many destinations [POL88, POL16, EA19, BF13]; (2) capture fraction in the budget sense [LEA10, BAR18] is not F; (3) flux-based alternatives [POT08, MC09, FB13, BF13, PAR11, BED24, PRY22] and adjoint/age methods [NW99, GOO96, CP06]; (4) gaps (outline §5.1 bullet 4), citing Table 1; (5) aims as three questions, each answered by a later section.
- Abstract numbers only: 1.68 million cells; 2–3 s per trace; 81 % of water pumped in the first ten years was in the aquifer at the start; GWT agreement "to round-off". No ensemble, scenario or overlap numbers.
- Check: outline §1, §4, §7 item 10; `table1_methods.md`; bibliography §F.
- Defines: full mixing, the reference method, destination, source, contributing area, capture fraction (budget sense). Says "gross by default" without defining it; uses "backward"/"forward" in words, no symbols.

**B: Methods (§2).**
- Carries key messages 1 and 3 (method) and outline §5.2 except sub-steps and steady limit (to C). Equations, each followed by "In words:": (I − P) F = S D; (I − Q) G = R T; backward closure; forward–backward check; (I − P) m = τ ∘ F; the tracking step V^new c^n − V^old c^(n−1) = Δt [...]; transient forward–backward identity.
- Numbers: Fig. 1b F = 6/11 = 0.55; Fig. 1c 5.0 vs 33.7 m³/d (6.7 times); snapshot storage release up to 50 % in the dry season (forward to §4.4); model 6 volume options ≤ 1.2e-4 forward, ≤ 6e-3 backward.
- Novelty sentence from outline §5.2: forward tracking is not new; backward tracking in time is what is added (Table 1, footnote 3).
- Check: `README_method.md` (Fig. 1); PLAN §2.1–2.7.
- Defines: every [B] item of §6, plus P, Q, S D, R T, net attribution, flow loops and closed recirculation loops, flow order (one precise sentence with "strongly connected components", "M-matrix", "pivoting"), boundary-control check ("duality" once, at the forward–backward check), mean travel time, turnover time, "flow"/"gwt" volumes, flow-error correction, backward tracking in time (not MODPATH backward tracking; "adjoint" once), fractions to other sinks and still stored.

**C: Implementation, Verification, Transient Demonstration (§3–4).**
- Carries key messages 2, 4, 5 and the numbers of 3; outline §5.3–5.4 with sub-steps and steady limit.
- Numbers: 1M cells 0.55 s for four groups (assembly 0.24 s), 0.42 s with 7,000 flow loops, ~90 MB per group per million cells; tutorial 08 0.75 s forward, 0.80 s backward (no large transient timing: say so). Table 2 largest errors; tracking vs GWT ≤ 2.2e-15 (model 6), ≤ 1e-14 (model 7); steady G vs GWT ≤ 2.8e-11 (model 7 1.0e-8, flow-solve limited); model 10 9.7e-14 and 6.8e-10 (1.2e-14, 1.4e-11 tight). PRT 9574 vs 9590 d, 800.4 of 800 m³/d. DS: band ~h^0.5; F ≥ 0.5 area within 5 % for h ≤ 50 m; F ≥ 0.1 contains the reference, 8–90 % too large. Fig. 4: snapshots 60/12/15 % (storage peak 50 %); tracked 95/3/<2 % (year 1), 52/33/16 % (year 30); initial water 98/81/68 % of water pumped so far; 30-year split 13.8/18.5/67.7 %; checks ≤ 4.3e-16, 9.8e-14; volumes 1.9e-4 and 3.7e-3; sub-steps 0.0078 vs 0.0042; the one-layer caveat.
- Check: `verification_table.md`; `README_method.md` (Figs 2–4); DS §3–5; tutorial 08 §§1–9; PLAN Phase 2, 4B. Use Fig. 4's four-sub-step shares, not tutorial 08's (outline §5.4).
- Defines: transport sub-steps; models 1–10; "MODFLOW 6 particle tracking (PRT)"; flow-weighted release; weight-losing particles; numerical dispersion; transition band; face-to-face routing; reference. States once that DS thresholds are non-strict (F ≥ 0.1) and NS strict.

**D: Neversink demonstration (§5).**
- Carries key messages 6–7 and outline §5.5. Opens with what Neversink demonstrates (items i–v) and "a benchmark, not a reference".
- Numbers: 4 × 680 × 619, heads within 8.6 mm, 122,021 particles, 980 cells, 3,671 m³/d, closure ≤ 1e-12 m³/d. Overlap 0.30/0.41/0.41; sum of F 910; 96 % in start cells; core 94 % inside, covering 43 %. Net (one sentence, rest SI): 3,944 vs 3,671 m³/d, U___7 2.26 times, sum of F 978. PRT: weight-losing +1.8 % (0.0 to +1.8 %, no trend), plain 2.6 times; stream 43 vs 51 %; envelope 87 % and 92 % with both caveats; published conventions 0.998, defaults 0.62–0.65, face 0.65 → 0.998. Streams 57/43 % → 100 % recharge; 1,534 vs 911, 5,247 vs 3,725 cells; 1.51 times. Ensemble r = 0.80, 0.90, overlap 0.48; S region CV 32 %, r 0.997 vs 0.00; corrected areas median overlap 0.996. Scenarios within 10 %; 4.09 vs 3.68, published 3.60, PRT 3.62; stream share 42 → 28 %; r = 0.94; 72 %/18 %; buried stream cells 4.76 → 3.83. Cost 2–3 s; 76 min on six processes.
- Word as interpretation (outline §7 item 6): leakage on flow lines; narrow paths in Fig. 8.
- Check: NS §1–7 and tables; `README.md` (Figs 5–10); CSVs in outline §5.5.
- Defines: overlap ("Jaccard index" once) and the other Neversink terms of terms.md ("Comparison with particle tracking" and "Streams" tables) not already assigned to C. Cites §2.3 for gross/net.

**E: Discussion, Limitations, Conclusions, Code and Data (§6–9).**
- Discussion, outline §5.6: (1) full mixing or particles; (2) conventions matter as much as the method (about a third each; 2,413 vs 3,736 m³/d); (3) thresholds: F ≥ 0.1 held the reference in synthetic tests, not fully on Neversink (27 %, 13 %, 89 cells, 6 %); (4) net accounting and published counts (978/980; 214 vs 58, 249 vs 163; "differences of both signs cancelling"; the untested reading stays untested); (5) snapshots, tracking or a GWT run (12 % vs none; 68 %; 9.8e-14; 2e-4/4e-3); (6) streams, ensembles; (7) reproducibility of benchmarks, brief and neutral.
- Limitations: all six bullets of outline §5.7, incl. ~1.6 GB per array at 1.68M cells × 121 steps and no real-model transient application. Conclusions: 4–5 sentences mirroring outline §3, no new numbers. Code and data: outline §5.9 with its [check]s.
- Check: outline §5.6–5.9; NS §5, §8; DS §5–6; tutorial 08 §§2, 7.
- Defines nothing new; cites back (§2.3, §4.4, §5.3) instead of re-deriving.

## 4. Style rules

**Style model.** Fienen et al. (2022) is subscription-only (Europe PMC: not open access; USGS Pubs Warehouse links no full text); only its 250-word abstract was read. Moves to copy: open on the decision context before the tool; motivate the method by a practical cost; name the real application as motivation, not subject; close on the decision served (protection chosen by risk tolerance) and open tools. Voice, tense and equations below follow the GMDSI register of Fienen et al. (2024, *Groundwater*), as excerpted in the voice-hugman references; not checked against the Neversink paper's body.

1. **"In words:" after every equation.** Do: "In words: the share of a cell's water that reaches the destination is the share leaving directly through it plus the outflow-weighted mean of its neighbours' shares." Don't: stack equations.
2. **Name confusions head-on, in one sentence.** Gross vs net: "Net accounting credits a weak-sink well with all the water passing its cell, 6.7 times its pumping in tutorial 02; gross accounting credits its pumping." Fraction vs probability: "F is a share of flow, not a probability [MC09]; the published probability of contribution is a share of realisations." Also capture fraction vs F; backward tracking in time vs MODPATH backward tracking; benchmark vs reference.
3. **Hedges as named stances.** Do: "we infer this from per-reach budgets; it was not traced cell by cell"; "one possible reading, not tested"; "an upper bound". Don't: drop the outline's caveats or stack adverbs.
4. **Numbers, not adjectives.** Do: "2 to 3 s per trace, against 44 s for the MODFLOW 6 run"; "overlap 0.30 to 0.41". Don't: "fast", "good agreement", "moderate overlap", "significantly larger".
5. **No filler or puffery.** Cut crucially, importantly, notably, furthermore, moreover, indeed; robust, novel, powerful, comprehensive, efficient (without a number); and terms.md's banned words.
6. **Caveat first.** "Neversink is steady state, so the paper has no real-model transient application." Not after the result.
7. **Negation, then alternative**, at most once per section: "The published areas are not a reference; they are one particle convention."
8. **Person:** "we" for choices and contributions ("We write the method as one sparse linear system per direction"); passive only where the actor does not matter.
9. **Tense:** present for the method, figures and standing facts; past for runs made ("PRT delivered 3,736 m³/d") and what a cited paper did; present for what it states.
10. **Figures:** "Fig. 6a", "Figs 9 and 10", "Table S1", in parentheses after the claim ("Full mixing lies inside the particle range (Fig. 7)"), not "Figure 7 shows that". First citations in numerical order.
11. **Paragraphs:** 3–7 sentences, one point, ending on the consequence; at most one aphorism per section.
12. **Register:** MODFLOW, MODPATH, PEST vocabulary; "decision" and "protection zone" where they fit; no computer-science terms beyond §2.4's one sentence.

## 5. Hard rules

1. Never write the product name or the joined word "Flow"+"Source", in any case. Write "the reference method (Foley and Black 2013; Black and Foley 2013)". [FB13], [BF13], [BFW21], [DAL22] have the name in their titles: cite by author–year only; their list entries are added at assembly.
2. Citations: outline keys, written author–year per the map below. Unknown sources: [check: source], never from memory.
3. **Every number traces to an evidence file**, noted after the sentence as `<!-- NS §2, Table 1; agreement_with_mp7.csv -->`. Keep source precision, strict thresholds for NS and non-strict for DS, and every [check] from the outline.
4. **Novelty:** claim only the linear-system formulation with exact solves through flow loops; gross accounting with net as an option; the exact checks; backward tracking in time and its forward–backward check; one code for all MF6 grids, multi-model simulations and package networks; the Neversink comparison. Forward tracking is not new [PAR11; Partington et al. 2013; Nogueira et al. 2022; BED24]; steady G equals GWT at equilibrium, and [BFW21] already describe forward mode as transport. Keep [check] on Table 1's GWT backward-in-time cell; Schilling et al. (2017) only with [check: not read]; do not cite Okkonen (2016).
5. terms.md wording only; each term is defined once, by the writer §3 assigns it to.

## 6. Shared definitions

Full wording in terms.md; writer in brackets.

- **full mixing:** each cell fully mixed, so all water leaving it carries the same mix of origins [A].
- **destination / source:** the sink term(s) traced to / source term(s) traced from [A].
- **contributing area:** cells with F above a threshold, or the expected area (sum of F) [A; thresholds D].
- **q_ij, O, I, r:** cell-to-cell flow (FLOW-JA-FACE); total outflow; total inflow; cell budget error r = I − O, reported, never forced to zero [B].
- **F:** backward fraction, share of the water leaving a cell that leaves the model through the destination; (I − P) F = S D, P_ij = q_ij / O_i [B].
- **G:** forward fraction, share of the water entering a cell that came from the source; (I − Q) G = R T [B].
- **gross accounting:** each sink term takes its share of the cell's total outflow, the rest passes on; a weak-sink well is credited with its pumping. Default [B].
- **net accounting:** the reference method's bookkeeping (net sources, destination cells fixed at F = 1); a weak-sink well is credited with all the water passing its cell [B].
- **weak sink:** a cell whose sink term takes only part of its outflow [B].
- **closure check:** traced source volumes, corrected by cell budget errors, add up to the destination inflow (backward) or a source's inflow (forward) [B].
- **forward–backward check:** the source-to-destination volume is the same traced either way, once cell budget errors are included [B].
- **snapshot:** a time step traced as a steady state on its own flows, storage release a source and storage gain a sink; nothing carried between steps [B].
- **transient tracking:** tagged water carried step to step through each cell's water volume; implicit, upstream, no dispersion; needs porosity and every step saved [B].
- **c:** tagged fraction of a cell's water (= GWT unit concentration with "gwt" volumes) [B].
- **w:** backward fraction in time, fraction of a cell's water at the start of a step (or entering during it) that leaves through the destination before the end; with the fractions to other sinks and still stored it sums to 1, less the flow-error correction [B].
- **initial water:** water in the model at the start of the simulation, not "pre-pumping water" [B].
- **overlap:** cells in both areas as a share of cells in either [D; A if used in the abstract].

## Key → citation map

In-text form, then short reference. Full entries in `references/bibliography.md` unless marked "add".

| key | in text | reference |
|---|---|---|
| FB13 | Foley and Black 2013 | MODFLOW and More 2013 proceedings, pp. 571–581 [check]; title added at assembly |
| BF13 | Black and Foley 2013 | MODFLOW and More 2013 proceedings, pp. 652–663 [check]; title added at assembly |
| BFW21 | Black et al. 2021 | slide deck; title added at assembly |
| DAL22 | Daley et al. 2022 | poster, Groundwater Modellers' Forum 2022; title added at assembly |
| EA19 | Environment Agency 2019 | Manual for the production of Groundwater Source Protection Zones |
| MAU21 | Maurice et al. 2021 | Geol. Soc. London Spec. Publ. 517 |
| CHO16 | Chowdhury 2016 | MASc thesis, University of Waterloo |
| POT08 | Potter et al. 2008 | *Ground Water* 46, no. 2: 335–340 |
| MC09 | McLane and Cecan 2009 | *Ground Water* 47, no. 2 |
| BAR18 | Barlow et al. 2018 | *Groundwater* 56, no. 5: 694–704 |
| LEA10 | Leake et al. 2010 | *Ground Water* 48, no. 5: 690–700 |
| BED24 | Bedekar et al. 2024 | *Groundwater* 62, no. 2: 303–309 |
| — | Bedekar et al. 2023 | CWEMF slides (add) |
| PRY22 | Pryet et al. 2022 | *Frontiers in Earth Science* 10: 975156 |
| PAR11 | Partington et al. 2011 | *Environmental Modelling & Software* 26, no. 7: 886–898 |
| — | Partington et al. 2012 | *Journal of Hydrology* 458–459: 28–39 (add) |
| — | Partington et al. 2013 | *Water Resources Research* 49: 5501–5519 (add) |
| — | Nogueira et al. 2022 | *Hydrology and Earth System Sciences* 26: 1883– (add) |
| — | Schilling et al. 2017 | *Water Resources Research*, doi 10.1002/2017WR020754 (add; not read) |
| — | Campana and Simpson 1984 | *Journal of Hydrology* 72: 171–185 (add) |
| — | Tosco et al. 2010 | *Ground Water Monitoring & Remediation* 30, no. 2: 46–52 (add) |
| NW99 | Neupauer and Wilson 1999 | *Water Resources Research* 35, no. 11: 3389–3398 |
| GOO96 | Goode 1996 | *Water Resources Research* 32, no. 2: 289–296 |
| CP06 | Cornaton and Perrochet 2006 | *Advances in Water Resources* 29, no. 9: 1267–1291 |
| FRI02 | Frind et al. 2002 | *Ground Water* 40, no. 6: 586–598 |
| POL88 | Pollock 1988 | *Ground Water* 26, no. 6: 743–750 |
| POL16 | Pollock 2016 | USGS Open-File Report 2016–1086 (MODPATH 7) |
| LAN17 | Langevin et al. 2017 | USGS Techniques and Methods 6-A55 (GWF) |
| LAN22 | Langevin et al. 2022 | USGS Techniques and Methods 6-A61 (GWT) |
| MF6IO | [check: author, year] | MODFLOW 6 input/output guide |
| — | [check] | MODFLOW 6 PRT documentation (add) |
| FLOPY | Bakker et al. 2016; Hughes et al. 2024 | FloPy (add) |
| — | White et al. 2020 | PEST++ iES (add) |
| COR22 | Corson-Dosch et al. 2022 | USGS Scientific Investigations Report 2021–5112 |
| FIE21 | Fienen et al. 2022 | *Groundwater* 60, no. 1: 71–86 (online 2021; key keeps "21") |
| — | [check: authors] 2021 | USGS data release, doi 10.5066/P9HWSOHP |
| — | Javandel and Tsang 1986 | *Ground Water* 24, no. 5 (add) |
| — | Fienen et al. 2024 | *Groundwater* Methods Brief (GLM); style source, cite only if used |
