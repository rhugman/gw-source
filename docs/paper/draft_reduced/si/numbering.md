<!-- PLAN, NOT FOR THE BUILD: SI numbering of the reduced draft (docs/paper/draft_reduced). The page builder (draft_page_alt/build_draft.py, si_plan) reads the first table: the type of each item and, in the third column, the item an alias marker is merged into. It numbers the items itself, by first citation in the main text; the labels below are those it assigns to this draft. Items moved out of the full draft's main text: the seven worked examples of its Sections 4.2-4.7 and 4.10 (si/G_examples.md, Texts and Figures), its Figures 1, 12 and 13 (si/G_examples.md) and its Table 1 (si/H_tables.md). References cited only in the SI are in si/references.md, which the builder appends after the items. -->

# SI numbering plan (reduced draft)

Order: first citation in the main text (sections/ in file order, with each display caption counted at its marker; markers inside HTML comments count too), then the items the main text does not cite, in the order of the files si/A.md to si/H_tables.md. Texts, Tables and Figures are numbered separately.

| placeholder | label | merged into | first cited in the main text |
|---|---|---|---|
| {SI: method in full} | Text S1 | – | 02_methods.md |
| {SI: net accounting, fixed cells} | Text S1 | {SI: method in full} | 02_methods.md |
| {SI: solution of the linear systems} | Text S1 | {SI: method in full} | 02_methods.md |
| {SI: travel-time identity} | Text S1 | {SI: method in full} | 02_methods.md |
| {SI: water volume options} | Text S1 | {SI: method in full} | 02_methods.md |
| {SI: example and test models} | Text S2 | – | 04_examples.md |
| {SI: accounting at a small well} | Text S3 | – | 04_examples.md |
| {SI: transient checks on the seasonal example model} | Text S4 | – | 04_examples.md |
| {SI: ensemble and history-matching set-up} | Text S5 | – | 04_examples.md |
| {SI: where each source's water goes} | Text S6 | – | 04_examples.md |
| {SI: the same trace on different grids} | Text S7 | – | 04_examples.md |
| {SI: the contributing area through the seasons} | Text S8 | – | 04_examples.md |
| {SI: mean travel time to the well} | Text S9 | – | 04_examples.md |
| {SI: streams, drains, wells and linked models} | Text S10 | – | 04_examples.md |
| {SI: a new well's source mix} | Text S11 | – | 04_examples.md |
| {SI: end states of the published particles} | Text S12 | – | 05_neversink.md |
| {SI: notes and sources for the comparison of methods} | Text S13 | – | not cited in the main text |
| {SI: Monte Carlo offsets and scenario rule} | Text S14 | {SI: Monte Carlo offsets} | not cited in the main text |
| {SI: Monte Carlo offsets} | Text S14 | – | not cited in the main text |
| {SI: diagnosis of the first PRT runs} | Text S15 | – | not cited in the main text |
| {SI: Table 1 notes and sources} | Table S1 | {SI: comparison of methods} | 01_introduction.md |
| {SI: comparison of methods} | Table S1 | – | 01_introduction.md |
| {SI: inputs, selections and outputs} | Table S2 | – | 03_software.md |
| {SI: delineations on one flow field} | Table S3 | – | 03_software.md |
| {SI: verification errors per check and model} | Table S4 | – | not cited in the main text |
| {SI: per-well gross and net} | Table S5 | – | not cited in the main text |
| {SI: ensemble statistics} | Table S6 | – | not cited in the main text |
| {SI: method schematic} | Figure S1 | – | 02_methods.md |
| {SI: verification on the test models} | Figure S2 | – | 03_software.md |
| {SI: Neversink full-mixing maps} | Figure S3 | – | 05_neversink.md |
| {SI: numerical dispersion maps and time steps} | Figure S4 | – | 06_tradeoffs.md |
| {SI: numerical dispersion} | Figure S4 | {SI: numerical dispersion maps and time steps} | 06_tradeoffs.md |
| {SI: net attribution and PRT-area maps} | Figure S5 | – | not cited in the main text |
| {SI: Neversink model and published regions} | Figure S6 | – | not cited in the main text |
| {SI: Neversink backward fractions} | Figure S7 | – | not cited in the main text |
| {SI: Neversink areas against particle tracking} | Figure S8 | – | not cited in the main text |
| {SI: Neversink probability of contribution} | Figure S9 | – | not cited in the main text |
| {SI: the worked example of Foley and Black (2013) and a small well} | Figure S10 | – | not cited in the main text |
| {SI: forward fractions of river water and field recharge} | Figure S11 | – | not cited in the main text |
| {SI: backward fractions on different grids} | Figure S12 | – | not cited in the main text |
| {SI: seasonal snapshots} | Figure S13 | – | not cited in the main text |
| {SI: mean travel time against particles} | Figure S14 | – | not cited in the main text |
| {SI: backward fractions through streams and a multi-aquifer well} | Figure S15 | – | not cited in the main text |
| {SI: the unit-concentration example rebuilt} | Figure S16 | – | not cited in the main text |
| {SI: numerical dispersion against cell size} | Figure S17 | – | not cited in the main text |

Labels are reassigned on every build. Recheck them with the build rather than editing them by hand.
