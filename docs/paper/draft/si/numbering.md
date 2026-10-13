<!-- PLAN, NOT FOR THE BUILD: SI numbering plan written by the SI editor in round 2. The build must not render this file. It maps each {SI: short name} placeholder to its SI label and records the merges; the orchestrator applies the renames in sections/ and display/. -->

# SI numbering plan

Order: first citation, reading `sections/` in file order, with each display caption counted at its `[[Table n]]` or `[[Figure n]]` marker. Within one line, placeholders are taken in the order they appear. Labels are numbered separately for Texts, Tables and Figures.

| placeholder | label | merged into | first cited at (file:line) |
|---|---|---|---|
| {SI: Table 1 notes and sources} | Text S1 | – | display/A.md:3, counted at sections/01_introduction.md:13 (`[[Table 1]]`) |
| {SI: net accounting, fixed cells} | Text S2 | – | sections/02_methods.md:39 |
| {SI: example and test models} | Text S3 | – | sections/02_methods.md:41 |
| {SI: solution of the linear systems} | Text S4 | – | sections/02_methods.md:49 |
| {SI: travel-time identity} | Text S5 | – | sections/02_methods.md:71 |
| {SI: water volume options} | Text S6 | – | sections/02_methods.md:87 |
| {SI: transient checks on the seasonal example model} | Text S7 | – | sections/03_implementation.md:9 |
| {SI: verification errors per check and model} | Table S1 (parts a–c) | – | display/C.md:3, counted at sections/04_verification.md:9 (`[[Figure 2]]`) |
| {SI: numerical dispersion maps and time steps} | Figure S1 | – | sections/04_verification.md:27 |
| {SI: per-well gross and net} | Table S2 | – | sections/05_neversink.md:17 |
| {SI: end states of the published particles} | Text S8 | – | sections/05_neversink.md:21 |
| {SI: net attribution and PRT-area maps} | Figure S2 | – | sections/05_neversink.md:21 |
| {SI: delineations on one flow field} | Table S3 | – | sections/05_neversink.md:25 |
| {SI: diagnosis of the first PRT runs} | Text S9 | – | sections/05_neversink.md:25 |
| {SI: Monte Carlo offsets and scenario rule} | Text S10 | – | sections/05_neversink.md:41 |
| {SI: ensemble statistics} | Table S4 | – | sections/05_neversink.md:43 |
| {SI: scenario medians} | Table S5 | – | sections/05_neversink.md:51 |
| {SI: growth mechanism} | Figure S3 | – | sections/05_neversink.md:55 |
| {SI: one convention at a time} | Table S6 | – | sections/05_neversink.md:57 |
| {SI: faster growth of weight-losing particles} | Text S11 | – | sections/05_neversink.md:57 |
| {SI: PRT abort in thin-film cells} | Text S12 | – | sections/07_limitations.md:13 |

**Count:** 21 SI items: 12 Texts (S1–S12), 6 Tables (S1–S6), 3 Figures (S1–S3).

## Where each item lives

| label | heading | file |
|---|---|---|
| Text S1 | {SI: Table 1 notes and sources} | si/A.md |
| Text S2 | {SI: net accounting, fixed cells} | si/B.md |
| Text S3 | {SI: example and test models} | si/C.md |
| Text S4 | {SI: solution of the linear systems} | si/B.md |
| Text S5 | {SI: travel-time identity} | si/B.md |
| Text S6 | {SI: water volume options} | si/B.md |
| Text S7 | {SI: transient checks on the seasonal example model} | si/C.md |
| Table S1 | {SI: verification errors per check and model} | si/C.md |
| Figure S1 | {SI: numerical dispersion maps and time steps} | si/C.md |
| Table S2 | {SI: per-well gross and net} | si/F_editor.md |
| Text S8 | {SI: end states of the published particles} | si/F_editor.md |
| Figure S2 | {SI: net attribution and PRT-area maps} | si/E.md |
| Table S3 | {SI: delineations on one flow field} | si/D.md |
| Text S9 | {SI: diagnosis of the first PRT runs} | si/F_editor.md |
| Text S10 | {SI: Monte Carlo offsets and scenario rule} | si/D.md |
| Table S4 | {SI: ensemble statistics} | si/F_editor.md |
| Table S5 | {SI: scenario medians} | si/F_editor.md |
| Figure S3 | {SI: growth mechanism} | si/D.md |
| Table S6 | {SI: one convention at a time} | si/F_editor.md |
| Text S11 | {SI: faster growth of weight-losing particles} | si/F_editor.md |
| Text S12 | {SI: PRT abort in thin-film cells} | si/E.md |

The SI should be assembled in label order: Texts S1–S12, then Tables S1–S6, then Figures S1–S3, or in first-citation order as in the first table; the labels hold either way.

## Renames to apply

1. Every placeholder maps one to one as in the first table. The round-2 merges ({SI: per-well comparison} into {SI: per-well gross and net}; {SI: Monte Carlo bookkeeping offsets} into {SI: Monte Carlo offsets and scenario rule}) no longer appear in sections/ as of round 5.
2. The SI files cite other SI items by placeholder too, and these need the same renames: si/F_editor.md cites {SI: Monte Carlo offsets and scenario rule}, {SI: growth mechanism} and {SI: one convention at a time}.

## Notes on labels

- **Table S1** holds three tables under one heading: (a) largest error per check, (b) steady and snapshot checks per model, (c) transient tracking checks per model. Since round 4 the test models are described in {SI: example and test models}, not in a preamble to Table S1. Label them Table S1a–c, or Tables S1–S3 if the journal wants one number per table; in that case every later Table label moves up by two.
- **Figure S1** is the PNG docs/paper/figures/figS1_numerical_dispersion.png (panels a–n), redrawn by studies/paper/si_dispersion_figure.py from the outputs behind DS Figs 1, 3 and 5; its caption is in si/C.md.
- **Figure S2** is the PNG docs/paper/figures/figS2_net_and_envelope.png (formerly figS1_net_and_envelope.png).
- **Figure S3** is the PNG docs/paper/figures/figS3_growth_mechanism.png (formerly Fig. 10 of the main text, fig10_growth_mechanism.png).
- No heading holds both a table and a figure, so no label is split. Figures S2 and S3 each come with a paragraph of numbers behind the figure, which stays under the figure label.
- **Texts S8, S9 and S11** each hold one short table inside the text (end states of the particles; PRT delivery by crediting rule; the calibrated-model growth table, NS Table 7). They stay unnumbered parts of their Text. If the journal wants every table numbered, label them Tables S7, S8 and S9 in that order. Text S3 holds the table of test models in the same way.
- brief.md §2 planned Tables S1–S6 and Texts S1–S5 in a different order; decisions_r1 item 5 replaces that plan with first-citation order, which this file follows.
- Six main-text citations stand without parentheses: sections/02_methods.md:39 and :65 (the last a bare placeholder after the sentence), sections/06_discussion.md:11 and :15, sections/07_limitations.md:7 and :9. When the labels go in, write them as "(Text S2)", "(Table S2)" and so on.
- **Round 5 (writer C): renumbered.** Since round 4, three Text items are new: {SI: example and test models} (si/C.md, Text S3), and {SI: solution of the linear systems} and {SI: water volume options} (writer B, si/B.md, Texts S4 and S6). {SI: transient checks on tutorial 08} is now {SI: transient checks on the seasonal example model} (Text S7). The labels above follow first citation as of round 5, so every Text from the old S3 on has moved: travel-time identity S3 → S5, transient checks S4 → S7, end states S5 → S8, diagnosis S6 → S9, Monte Carlo offsets S7 → S10, faster growth S8 → S11, PRT abort S9 → S12. Tables and Figures keep their labels. Line numbers are those of round 5; recheck them if a section changes. The list of main-text citations without parentheses above dates from round 2.
