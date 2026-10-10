# Orchestrator decisions after review round 1

These decisions apply to every writer and override brief.md where the two differ. The reviews are in `reviews/r1_content.md`, `r1_voice.md` and `r1_reader.md`.

## Length and display items
1. The main text stays at 7,500 words or fewer, and the paper should come to about 16 printed pages. New section budgets:

   | Section | Budget (words) |
   |---|---|
   | §1 | 850 |
   | §2 | 1,750 |
   | §3 | 400 |
   | §4 | 1,050 |
   | §5 | 1,350 |
   | §6 | 1,100, including the new guidance paragraph |
   | §7 | 300 |
   | §8 | 180 |
   | §9 | 100 |

2. Display items in the main text are Figs 1–9 and Table 1. The rest move to the Supporting Information (SI):
   - Fig. 10. In §5.6, one sentence carries its point.
   - Table 2. Fig. 2 carries the verification; the per-check and per-model numbers go to the SI.
   - Table 3. Fig. 7 carries the overlaps.
3. Table 1 keeps at most 5 short footnotes, the ones a reader needs to read the cells. The other footnotes, and the sources, go to an SI text.
4. Captions are at most 150 words; Fig. 1 may have up to 180. Numbers belong in the text or the SI, not the caption. A caption says what is shown and how to read it.

## SI references
5. Do not number SI items. Cite them with a placeholder, `{SI: short name}`, e.g. `{SI: verification errors per model}` or `{SI: per-well gross and net}`. The editor numbers them in order of first citation in round 2.
6. Material you move out of the main text goes to `docs/paper/draft/si/<your letter>.md`, under headings `## {SI: short name}`. Nothing is lost. Keep its evidence comments.

## One home for each explanation
7. Each explanation lives in one place:
   - **Gross and net accounting:** defined in §2.3 only. §1 may say "gross accounting by default". Other sections cite §2.3.
   - **Novelty:** stated in §1. §2.8 keeps at most one pointer sentence: "forward tracking is not new (Table 1); §2.9 adds backward tracking in time".
   - **Benchmark caveat** ("a benchmark, not a reference"): opens §5. §6 and §7 cite back to it.
   - **Weak sink:** defined in §1 (writer A). Delete the definition in §2.
   - **PRT and IFLOWFACE:** defined in §3.2 only.
   - "Reference" is used only for the dispersion tests (§4.3). The Neversink PRT area is "the PRT area (P > 0.5)".

## Claims to fix everywhere
8. Wherever tracking is said to match GWT to round-off, add the qualifier "with GWT's water volumes".
9. Abstract: say the reference method "is described only in conference papers and has no open implementation". Do not say "lacks a peer-reviewed description".
10. Be fair to particle tracking. One forward particle run serves every well (fix 01:5). §5.2 opens with the spread of particle runs on the same flow field (0.29–0.998), so full mixing's 0.30–0.41 reads as lying inside that spread.
11. McLane and Cecan (2009) has not been read.
    - Delete it at §2.
    - Mark it "[check: not read]" in §1.
12. The Fig. S1 strip is "about 1.5 km long, 1 to 2.5 km west of the U wells".

## Guidance in §6 (writer E)
13. Add a practical paragraph. Hedge it as our recommendation from this evidence ("from these tests we would…"), not as a rule. It covers:
    - **Which area to draw:** F > 0.5 as a single estimate; F ≥ 0.1 as the wider area; a particle check where the area ends at weak sinks.
    - **Accounting:** gross by default; net accounting to reproduce studies made with the reference method.
    - **Time-limited areas:** these come from backward tracking in time, e.g. the 30-year area in Fig. 4d.

    State the evidence behind each point, with section and figure references.

## Style (from r1_voice)
14. Define MODFLOW 6 (MF6), GWT, GWF, SFR and the other acronyms at first use, in the section that comes first.
15. Do not start a sentence with a symbol.
16. In §2, the words "factorisation", "assembly" and "the solve" may appear only in the one technical sentence in §2.4.
17. Write "transient tracking" in full wherever bare "tracking" could be read as particle tracking.
18. Write numbers as 1 × 10⁻¹² in prose, not 1e-12.
19. Keep British spelling for now; the journal copy-edits.
