<!-- PLAN, NOT FOR THE BUILD: SI numbering plan, regenerated in alt round 1 (SI reorganisation after reviews/alt_r1.md). The page builder (draft_page_alt/build_draft.py, si_plan) reads the first table: the type of each item (Text, Table or Figure) and, in the third column, the item an alias marker is merged into. The builder numbers the items itself, by first citation in the main text; the labels below are those it assigns to the layout of this round. -->

# SI numbering plan

Order: first citation, reading `sections/` in file order, with each display caption counted at its `[[Table n]]` or `[[Figure n]]` marker. Markers inside HTML comments count too. Within one line, markers are taken in the order they appear. Labels are numbered separately for Texts, Tables and Figures. Items that the main text does not cite are numbered after the cited ones, in the order of the files si/A.md to si/F_editor.md.

| placeholder | label | merged into | first cited at (file:line) |
|---|---|---|---|
| {SI: comparison of methods} | Table S1 | – | through its alias below, sections/01_introduction.md:15 |
| {SI: Table 1 notes and sources} | Table S1 | {SI: comparison of methods} | sections/01_introduction.md:15 (alias; the marker name predates the move of the table into the SI) |
| {SI: method in full} | Text S1 | – | sections/02_methods.md:3 |
| {SI: net accounting, fixed cells} | Text S1 | {SI: method in full} | not cited (alias for older markers) |
| {SI: solution of the linear systems} | Text S1 | {SI: method in full} | not cited (alias for older markers) |
| {SI: travel-time identity} | Text S1 | {SI: method in full} | not cited (alias for older markers) |
| {SI: water volume options} | Text S1 | {SI: method in full} | not cited (alias for older markers) |
| {SI: verification on the test models} | Figure S1 | – | sections/03_software.md:43 |
| {SI: example and test models} | Text S2 | – | sections/04a_examples.md:3 |
| {SI: numerical dispersion maps and time steps} | Figure S2 | – | sections/04a_examples.md:17 |
| {SI: numerical dispersion} | Figure S2 | {SI: numerical dispersion maps and time steps} | sections/04a_examples.md:17 (alias) |
| {SI: transient checks on the seasonal example model} | Text S3 | – | display/C.md, Figure 9 caption, counted at sections/04b_examples.md:39 (`[[Figure 9]]`) |
| {SI: ensemble and history-matching set-up} | Text S4 | – | sections/04c_examples.md:9 |
| {SI: ensemble statistics} | Table S2 | – | sections/05_neversink.md:7 |
| {SI: Monte Carlo offsets} | Text S5 | – | through its alias below, display/N.md:5, counted at sections/05_neversink.md:9 (`[[Figure 12]]`) |
| {SI: Monte Carlo offsets and scenario rule} | Text S5 | {SI: Monte Carlo offsets} | display/N.md:5 (alias; the scenario rule was deleted) |
| {SI: delineations on one flow field} | Table S3 | – | sections/05_neversink.md:15 |
| {SI: end states of the published particles} | Text S6 | – | sections/05_neversink.md:19 |
| {SI: net attribution and PRT-area maps} | Figure S3 | – | sections/05_neversink.md:19 |
| {SI: notes and sources for the comparison of methods} | Text S7 | – | not cited in the main text; cited from {SI: comparison of methods} |
| {SI: verification errors per check and model} | Table S4 | – | not cited in the main text; cited from {SI: verification on the test models} |
| {SI: per-well gross and net} | Table S5 | – | not cited in the main text; cited from {SI: delineations on one flow field} |
| {SI: diagnosis of the first PRT runs} | Text S8 | – | not cited in the main text; cited from {SI: delineations on one flow field} |

**Count:** 16 SI items: 8 Texts (S1–S8), 5 Tables (S1–S5), 3 Figures (S1–S3). Six further rows are aliases, so that older markers still resolve.

## Where each item lives

| label | heading | file |
|---|---|---|
| Table S1 | {SI: comparison of methods} | si/A.md (moved from display/A.md) |
| Text S7 | {SI: notes and sources for the comparison of methods} | si/A.md (formerly {SI: Table 1 notes and sources}) |
| Text S1 | {SI: method in full} | si/B.md |
| Text S2 | {SI: example and test models} | si/C.md |
| Text S4 | {SI: ensemble and history-matching set-up} | si/C.md |
| Figure S1 | {SI: verification on the test models} | si/C.md (caption moved from display/C.md "## Figure S10"; image docs/paper/figures/figS10_verification.png) |
| Table S4 | {SI: verification errors per check and model} | si/C.md |
| Figure S2 | {SI: numerical dispersion maps and time steps} | si/C.md (image docs/paper/figures/figS1_numerical_dispersion.png) |
| Text S3 | {SI: transient checks on the seasonal example model} | si/C.md |
| Table S3 | {SI: delineations on one flow field} | si/D.md |
| Text S5 | {SI: Monte Carlo offsets} | si/D.md (formerly {SI: Monte Carlo offsets and scenario rule}) |
| Figure S3 | {SI: net attribution and PRT-area maps} | si/E.md (image docs/paper/figures/figS2_net_and_envelope.png) |
| Table S5 | {SI: per-well gross and net} | si/F_editor.md |
| Text S6 | {SI: end states of the published particles} | si/F_editor.md |
| Text S8 | {SI: diagnosis of the first PRT runs} | si/F_editor.md |
| Table S2 | {SI: ensemble statistics} | si/F_editor.md |

## Changes in alt round 1

1. **Merged into {SI: method in full}** (si/B.md): the items net accounting, fixed cells; travel-time identity; solution of the linear systems; water volume options. Added: the derivation of Eqs (2)–(4) and (8), why the closure, forward–backward and boundary-control checks hold, the flow-loop block solve, mean travel time, transport sub-steps, and backward tracking in time with the transient forward–backward identity (text reused from previous/02_methods.md). New equations are numbered S1–S8.
2. **Verification.** {SI: verification on the test models} is a new Figure item holding the old verification figure (display/C.md "## Figure S10", formerly main-text Fig. 2). The three tables stay under {SI: verification errors per check and model}, which the figure caption cites. The builder needs SI_FIGS["verification on the test models"] = "figS10_verification.png" to show the image.
3. **Example models.** {SI: example and test models} now describes every example model of Section 4. {SI: ensemble and history-matching set-up} is new and holds the PEST++ IES details moved out of Section 4.9.
4. **Numerical dispersion.** {SI: numerical dispersion maps and time steps} now also holds the test problems and the numbers behind Fig. 13 and Section 6. {SI: numerical dispersion} is an alias for it.
5. **Comparison of methods.** The table of display/A.md is now the SI item {SI: comparison of methods}. Its notes are {SI: notes and sources for the comparison of methods}.
6. **Deleted** (pumping scenarios dropped from the paper, outline §6 decision 3): {SI: scenario medians}, {SI: growth mechanism}, {SI: one convention at a time}, {SI: faster growth of weight-losing particles}, the scenario-rule half of {SI: Monte Carlo offsets and scenario rule} (now {SI: Monte Carlo offsets}) and the scenario paragraph of {SI: ensemble statistics}.
7. **Kept although not cited in the main text:** {SI: per-well gross and net} and {SI: diagnosis of the first PRT runs}, because {SI: delineations on one flow field} cites both.

## Notes on labels

- **Table S4** holds three tables under one heading: (a) largest error per check, (b) steady-state and snapshot checks per model, (c) transient tracking checks per model. Label them Table S4a–c, or Tables S4–S6 if the journal wants one number per table.
- **Texts S6 and S8** and **Text S2** each hold short tables inside the text (end states of the particles; PRT delivery by crediting rule; the test models). **Text S4** holds the table of phi by iteration. They stay unnumbered parts of their Text.
- The display files display/D.md ("## Figure S5" to "## Figure S9", the earlier Neversink figures) are not SI items and no marker places them. Their fixed labels do not clash with Figures S1–S3. Figure S9 serves the dropped pumping scenarios.
- The labels above hold for the main text as of alt round 1. The builder renumbers on every build, so a new or moved citation changes them. Recheck with the build rather than editing labels by hand.
