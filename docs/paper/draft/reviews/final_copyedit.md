# Final copy edit (before the author's first read)

Draft at commit 091903f, branch paper-draft. Read: sections/00–10, display/A–E, si/A–F and numbering.md, decisions_r1/r2, terms.md. Line numbers refer to the files after the edits below.

Mechanical checks:
- Every `{SI: …}` citation in sections/, display/ and si/ matches a `## {SI: …}` heading exactly (18 headings, all cited; no orphans).
- Every §, Fig. and Table cross-reference in the main text points to an existing target with the right content.
- Main text about 7,170 words (rough count, headings included, equations left out), under 7,500.
- Naming test: 2 passed.

## Issues reported (not fixed)

### Contradictions between sections

1. **sections/04_verification.md:37 vs si/C.md:92**: in the last season of year 1 the main text gives 95 % initial water and 3 % river leakage (four sub-steps, as in Fig. 4). The SI gives 97.6 % initial and 3.1 % river for four sub-steps, which together come to more than 100 %. The SI probably gives the cumulative share ("pumped so far", 98 % in 04:37). Check against tutorial 08 §9 and make the SI say which share it gives.
2. **sections/06_discussion.md:13 and si/F_editor.md:25 vs Table S2 (si/F_editor.md:11)**: these say net accounting is above the published count "at U___7 and U___8" and below it "at SV_487 and U__55". SV_407 is also above (37 against 32). Add SV_407 or say "mainly".
3. **sections/00_front.md:5 vs sections/08_conclusions.md:5**: the abstract says full mixing "agrees with" the published areas within the particle spread. §8 and §5.2 say it "lies within" that spread, at its low end (0.30–0.41 against 0.29–0.998). Use "lies within" in the abstract too, so the abstract does not claim more than the body.
4. **sections/02_methods.md:73, 03_implementation.md:5, 07_limitations.md:5**: the Output Control keyword is written two ways, "OC BUDGET ALL" and "BUDGET SAVE". MODFLOW 6 syntax is `SAVE BUDGET ALL`. Use one form, and spell out "Output Control" once.
5. **sections/06_discussion.md:9**: "Each of these steps changes the overlap by about 0.33". The second step is 0.998 − 0.65 = 0.35. Write "by 0.33–0.35". In the same sentence, "weight loss at weak sinks" separates plain from weight-losing particles. But plain particles lose weight only at the wells (si/F_editor.md:50), so the difference is weight loss at all the other sinks. Reword to "weight loss at the other sinks".
6. **display/C.md:15 (Fig. 4 caption) vs sections/02_methods.md:81**: the caption says the backward fractions "add up to 1". §2.9 says they add up to 1 "less the flow-error correction". Add "to within the flow-error correction", or leave as is if the caption is meant to stay simple.

### Claims that look unsupported, or need a source in the text

7. **sections/06_discussion.md:27**: "it held 59 % of the PRT area". §5.2–5.3 do not give this number (it is 0.917 × 445 / 691). State it in §5.3 or cite {SI: net attribution and PRT-area maps}.
8. **sections/04_verification.md:9**: "simulations split into two to four models". si/C.md:43 mentions only three-model and four-model splits (model 3 and model 6 have no count). Check that a two-model split was run, or write "three or four".
9. **sections/07_limitations.md:7**: this states that stream leakage "stays on flow lines to the wells along particle paths", but the main text never introduces that reading or the faster growth of weight-losing particles behind it. A reader of §7 has no context for it. Add a half sentence in §5.6, or drop the sentence from §7 (r2 decision 3).
10. **sections/05_neversink.md:33**: "All the wells' water then traces to recharge". Constant heads and other boundary inflows could supply some of it. Check the stream-network source table and write "all" only if the share is 100 %.
11. **sections/04_verification.md:37**: under snapshots the well's water is 60 % recharge, 12 % west-edge inflow and 15 % storage. That leaves 13 % unaccounted for, presumably river leakage. Name it, or a reviewer will ask.
12. **sections/09_availability.md:3 and the reference list**: Hughes et al. 2024, Provost et al. 2017, White et al. 2020, Nogueira et al. 2022, Schilling et al. 2017, the USGS data release, the MODFLOW 6 input/output guide and the Mf6Splitter entry are all incomplete, and PRT has no citation at all (03:11). An associate editor will send all of these back.
13. **sections/10_references.md:67**: Pryet et al. (2022) is in the reference list but cited nowhere in the text or the SI. Cite it or remove it.
14. **Unread sources**: one novelty claim (01:17) depends on Bedekar et al. 2024 (abstract only), and two background statements depend on McLane and Cecan 2009 and Schilling et al. 2017 (not read). Reading the full texts before submission would close the [check] markers.

### What an associate editor would send back

15. **sections/00_front.md:5**: the abstract is 258 words. *Groundwater* allows 250. Cut 8 or more words, for example the clause "run from the end of the simulation to its start".
16. **Section budgets (decisions_r1/r2)**, rough counts: §2 1,793 (limit 1,750), §3 421 (400), §4 1,081 (1,050), §6 1,166 (1,150), §8 182 (180), §9 115 (100). The total is within the limit. Trim if the budgets are hard limits.
17. **sections/05_neversink.md:45**: §5.6 gives the growth result in three sentences. r2 decision 19 allows at most two.
18. **si/D.md:37**: "Formerly Fig. 10 of the main text (`docs/paper/figures/fig10_growth_mechanism.png`)" is draft history with a repository path. Delete it before submission (more than a clause, so not cut here). The same applies to si/numbering.md (plan file, not for the build); its first-citation line numbers are stale but the names are correct.
19. **SI ranges**: the SI writes ranges as "0.989 to 1.000", "36 to 44 %" and so on throughout. r2 decision 7 asks for "2–3 s" style. Convert them all at once, or keep "to" consistently in the SI.
20. **sections/10_references.md:13, 15, 25, 31**: four titles contain the product name as two words. The naming test allows this and the titles are what the authors published, but confirm that the citation style is acceptable to you (memory rule: cite as the reference method).
21. **si/F_editor.md:115**: PRT in Table S6 is "seeded where F > 0", while elsewhere seeding is where F > 10⁻⁶. Check whether these were different runs or one threshold is a typo.
22. **sections/01_introduction.md:5**: "one forward run serves every well". A reviewer may say that wellhead areas are usually drawn by backward tracking from each well. The sentence follows r1 decision 10, so it may be worth a half-clause noting that forward release from every cell is meant.

## Edits made (13)

1. sections/00_front.md:5: "forward tracking matches" → "forward transient tracking matches" (r1 decision 17).
2. sections/01_introduction.md:7: "The destination is the sink terms … the source is the source terms" → "the set of sink terms … the set of source terms" (number agreement).
3. sections/06_discussion.md:7: "deliver the same water" → "deliver the same volume of water". §5.3 shows the sources differ (43 % against 51 % stream water), so only the volume is the same.
4. sections/06_discussion.md:9: "moves particles from the published starts from 0.65" → "moves particles released at the published starts from 0.65" (double "from").
5. sections/07_limitations.md:3: "35 to 70 %" → "35–70 %" (r2 decision 7; matches §4.3).
6. display/D.md:3: "(4 wells," → "(four wells," (r2 decision 7, number below ten with no unit).
7. si/A.md:38: added a semicolon before the run-on citation "Foley and Black (2013) Introduction".
8. si/A.md:40: added a semicolon before the run-on citation "Foley and Black (2013) Method".
9. si/A.md:43: added a semicolon before the run-on citation "Black and Foley (2013) Introduction".
10. si/A.md:86: put the run-on citation in parentheses: "(McLane and Cecan 2009 [check: not read])".
11. si/A.md:80: "GVE compares" → "The global volume error compares" (abbreviation never defined).
12. si/C.md:90: "Forward tracking and backward tracking in time" → "Forward transient tracking and …" (r1 decision 17).
13. si/D.md:3: cut the draft-history clause "Formerly Table 3 of the main text;".

## Naming test

`PYTHONPATH=src ~/miniforge3/envs/gw-source/bin/python -m pytest -q tests/test_naming.py`: 2 passed in 0.06 s, after all edits.

## Fixes applied

1. si/C.md: the SI initial-water shares (96.9, 97.6, 97.8 %) are the share of all water pumped so far after 1 year, not the last season; now said so. The river shares (3.6, 3.1, 3.0 %) are the last season. Source: README_method.md Fig. 4 notes and tutorial 08 §§3–4, 9. Main text unchanged.
2. sections/06_discussion.md and si/F_editor.md: SV_407 added to the wells where net accounting is above the published count (37 against 32). In §6.2, the other five wells are all below it (Table S2).
3. sections/00_front.md: abstract now says full mixing "lies within" the spread, as §5.2 and §8 do.
4. sections/02, 03, 07: one form, SAVE BUDGET ALL; "Output Control (OC)" spelled out at first use (§2.8), "OC" after that.
5. sections/06_discussion.md: "by about 0.33" changed to "by 0.33–0.35"; "weight loss at weak sinks" changed to "weight loss at the other sinks".
6. display/C.md: Fig. 4 caption now says "add up to 1 to within the flow-error correction".
7. sections/05_neversink.md §5.3: added "The F > 0.5 area covers 59 % of the PRT area" (envelope_prt.csv, coverage 0.590), which §6.5 relies on.
8. Two-model split confirmed (model 3 split into two: tests/test_multimodel.py labels_for; studies/paper/verification.py says "2 to 4 models"). Main text kept as is; si/C.md now gives the count for each split model.
9. sections/07_limitations.md: the sentence now says what the reading explains (weight-losing particles give a smaller area at base pumping and so grow faster) and points to {SI: faster growth of weight-losing particles}, which holds it.
10. sections/05_neversink.md §5.4: "all" confirmed (sources_sfr_network.csv: RCHA 3,671.0 m³/d, CHD 0, SFR external inflow 0); added "none to constant heads or to the streams' external inflow".
11. sections/04_verification.md §4.4: the snapshot remainder is now named ("the rest river leakage"). No number added: the river mean is not quoted in transient_figure.py or the tutorial.
13. sections/01_introduction.md: Pryet et al. (2022) now cited in the flux-based-alternatives paragraph (outline §1, brief move 3), in one sentence on particle source shares weighted by cell-budget mixing ratios. Reference kept.
15. sections/00_front.md: cut "run from the end of the simulation to its start". The abstract is now 249 words, without the heading and the HTML comments.
17. sections/05_neversink.md §5.6: two sentences now. Dropped "so more of the pumping is recharge"; the mechanism stays in {SI: growth mechanism}.
18. si/D.md: deleted "Formerly Fig. 10 of the main text (…)" and the repository path. si/numbering.md not changed.
19. SI ranges changed to the en-dash style in si/D.md, si/E.md and si/F_editor.md, with no values changed. Not converted: "from X to Y" changes (e.g. 94 to 214 cells), "between … and …", page ranges in si/A.md (pp. 1–1 to 1–8, where an en dash would be ambiguous), and HTML comments.
21. Not a typo: these are different runs. Table S6 runs one particle per published start, seeded where F > 0 (growth_mechanisms.py; NS Table 6 note). §5.3 uses flow-weighted release in cells with F > 10⁻⁶ (NS Table 3 note). The Table S6 caption now says so.

Naming test after these fixes: 2 passed.
