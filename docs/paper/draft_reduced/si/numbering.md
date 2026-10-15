<!-- PLAN, NOT FOR THE BUILD: SI numbering of the reduced draft (docs/paper/draft_reduced). The page builder (draft_page_alt/build_draft.py, si_plan and si_order) reads the first table: the type of each item and, in the third column, the item an alias marker is merged into. For this draft (PLACEMENT_ORDER in build_draft.py) it places the items in the row order of the table, alias rows left out, and numbers Texts, Tables and Figures separately in that order. Each item's figures and tables follow it. The labels below are those it assigns. SI round 1 (reviews/si_r1_scope.md, si_r1_structure.md, si_r1_prose.md) slimmed the SI: the worked examples merged into one text (si/G_examples.md), the Neversink items into one text (si/D.md), the models, software and verification into one text (si/C.md), and the literature notes of the comparison of methods became a short sources note (si/A.md). References cited only in the SI are in si/references.md, which the builder appends after the items. -->

# SI numbering plan (reduced draft)

Order: the rows of this table, alias rows left out. The order follows the first citation in the main text. Texts, Tables and Figures are numbered separately.

| placeholder | label | merged into | first cited in the main text |
|---|---|---|---|
| {SI: comparison of methods} | Table S1 | – | 01_introduction.md |
| {SI: Table 1 notes and sources} | Table S1 | {SI: comparison of methods} | – |
| {SI: method in full} | Text S1 | – | 02_methods.md |
| {SI: net accounting, fixed cells} | Text S1 | {SI: method in full} | – |
| {SI: solution of the linear systems} | Text S1 | {SI: method in full} | – |
| {SI: travel-time identity} | Text S1 | {SI: method in full} | – |
| {SI: water volume options} | Text S1 | {SI: method in full} | – |
| {SI: software, verification and models} | Text S2 | – | 03_software.md |
| {SI: example and test models} | Text S2 | {SI: software, verification and models} | – |
| {SI: ensemble and history-matching set-up} | Text S2 | {SI: software, verification and models} | – |
| {SI: inputs, selections and outputs} | Table S2 | – | 03_software.md |
| {SI: verification checks on the test models} | Figure S1 | – | 03_software.md |
| {SI: verification on the test models} | Figure S1 | {SI: verification checks on the test models} | – |
| {SI: the worked examples in brief} | Text S3 | – | 04_examples.md |
| {SI: accounting at a small well} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: transient checks on the seasonal example model} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: where each source's water goes} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: the same trace on different grids} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: the contributing area through the seasons} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: mean travel time to the well} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: streams, drains, wells and linked models} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: a new well's source mix} | Text S3 | {SI: the worked examples in brief} | – |
| {SI: contributing area against particle tracking} | Figure S2 | – | 04_examples.md |
| {SI: snapshots and transient tracking over 30 years} | Figure S3 | – | 04_examples.md |
| {SI: probability of contribution before and after history matching} | Figure S4 | – | 04_examples.md |
| {SI: the unit-concentration example rebuilt} | Figure S5 | – | 04_examples.md |
| {SI: the Neversink comparison} | Text S4 | – | 05_neversink.md |
| {SI: delineations on one flow field} | Text S4 | {SI: the Neversink comparison} | – |
| {SI: end states of the published particles} | Text S4 | {SI: the Neversink comparison} | – |
| {SI: Neversink particle area and ensemble mean F} | Figure S6 | – | 05_neversink.md |
| {SI: Neversink full-mixing maps} | Figure S6 | {SI: Neversink particle area and ensemble mean F} | – |
| {SI: numerical dispersion test problems} | Text S5 | – | 06_tradeoffs.md |
| {SI: numerical dispersion} | Text S5 | {SI: numerical dispersion test problems} | – |
| {SI: numerical dispersion maps and cell size} | Figure S7 | – | 06_tradeoffs.md |
| {SI: numerical dispersion against cell size} | Figure S7 | {SI: numerical dispersion maps and cell size} | – |

Alias rows keep older placeholder names working. They were merged in SI round 1. Dropped in that round: the literature notes of the comparison of methods (the full draft's SI keeps them), the Monte Carlo offsets, the diagnosis of the first PRT runs, the per-well and ensemble tables (all now in docs/neversink_study.md), the per-check verification table (docs/verification.md), the method schematic (its panel b is main-text Fig. 1), the Neversink figures not cited by the main text and the example figures that the notebooks draw.

Labels are reassigned on every build. Recheck them with the build rather than editing them by hand.
