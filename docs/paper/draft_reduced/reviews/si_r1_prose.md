# SI review r1: prose slimming inside the items that stay

Scope: Texts S1–S11 and the figure captions, including the extra text under Figures S7 and S9. Words come from `export_reduced/supporting_information.md`. Pages come from the 69-page PDF. **[M]** marks a number that supports a main-text claim and must stay.

## 1. Lengths and targets

| item | words now | pages now | target words |
|---|---|---|---|
| S1 Method | 3,596 | ~6.5 | 2,900 |
| S2 Models (prose; test table kept) | 3,240 | ~9 with table | 2,480 |
| S3 Small well | 424 | ~1 | 260 |
| S4 Transient checks | 376 | ~0.5 | 230 + small table |
| S5 Ensemble set-up | 686 | ~1.3 | 570 |
| S6 Forward | 449 | ~0.8 | 320 |
| S7 Grids | 731 | ~1.2 | 470 |
| S8 Seasons | 440 | ~0.8 | 310 |
| S9 Travel time | 446 | ~0.6 | 350 |
| S10 Networks | 518 | ~0.8 | 370 |
| S11 New well | 477 | ~0.9 | 330 |
| Captions S1–S20 | 3,253 | in p49–67 | 2,500 |
| Text under Fig. S7, S9 | ~830 | ~1.5 | 470 |
| **Total** | ~15,500 | ~33 | ~11,600 |

## 2. Repeats to fix once, then cut everywhere

1. **F and G are never defined in words in S1.** S1 goes straight to Eq. S2. S6 and six captions (S3, S6, S11, S15, S16, S17) then define F or G again. Add two plain definitions at the start of S1. Keep the reminder only in the first caption of each group (S3, S6).
2. **Weak sink is used before it is defined.** S2 uses it. S3 and S12 define it. Define it once in S1, next to gross accounting. Keep one reminder in S3.
3. **The example model has three names:** "shared model", "shared example model" and "example model". The main text says "example model". Use that.
4. **Boilerplate opener, seven times.** "This text gives in full one of the worked examples summarised in Section 4 …" opens S3 and S6–S11 (~175 words). Cut it.
5. **Set-ups described twice.** S3, S6, S7, S8, S10 and S11 repeat the set-up from S2. Keep the set-up in S2. Each S-text names the change in one sentence and points to S2.
6. **The FlowSource loop treatment, three times** (S1 Solution, S1 Net accounting, S7). Keep it in S1 Solution.
7. **The two volume options, twice.** "1.9 × 10⁻⁴ … 3.7 × 10⁻³" is in S1 and S4. Keep it in S4 **[M: "less than 0.004"]**.
8. **The well-cell travel time, twice.** "9,607 d … 9,574 d" is in S1 and in the note under Table S4. Cut it from S1.
9. **Colour-scale wording.** "From 0 (dark purple) to 1 (yellow)" appears in eight captions (~80 words). The figures carry labelled colour bars (e.g. Figure S17). Cut the wording where a bar exists.

## 3. Cut list per item

**S1 (−700).**
- Cut the announcement "It defines the cell budget, derives the equations … in full."
- Drop the unnumbered equation before S6. Say in words that summing Eq. S2 over all cells gives S6.
- Cut the pivoting sentence, which also packs an appositive.
- Cut the selection rules to the rule plus one example (Rewrite 2).
- Cut the net-accounting error detail ("The check tests the sum of the equations … equation errors.").
- State the turnover result (S11) without the derivation.
- Shorten the S15 derivation in the same way.
- Apply items 6–8.
- Fix three participle openers: "Written for every cell at once", "Summed over the cells it leaves" and "Divided by the destination inflow".

**S2 (−760).**
- Cut the notebook table (−170). Its run times support no claim. Its names ("01 Quickstart") are tutorial references. Keep one sentence that the examples ship with the code. Section 7 cites S2 for this.
- Cut the percentile-memory paragraph ("4 GB … 0.8 GB"). It is software detail (−90).
- Bedekar model (−150):
  - Cut the closing result paragraph ("within 0.2 percentage points").
  - Cut the sub-step result from the Time-steps bullet. S11 has it.
  - Shorten the Units bullet to its effect.
- Cut the result sentences "Its cell carries 33.7 m³/d, so it is a weak sink" and "invented values". S3 and S6 give them.
- Shorten the eight-cell example. Main-text Fig. 1 describes it.
- Move the Figure S10 rerun sentence ("version 6.9 … 8.6 mm") to the Neversink terms. It is set-up, not caption.

**S3 (−165).** See Rewrite 1. Keep **[M]** 33.7 m³/d, 6.7 times, 0.149 and 1 × 10⁻¹⁴.

**S4 (−150).** This is a list of numbers. Make two small tables:
- the checks, with one value each (≤ 4.3 × 10⁻¹⁶, **[M]** 9.8 × 10⁻¹⁴, 2.5 × 10⁻¹¹, 0 and 8.0 × 10⁻¹⁶);
- the shares for 1, 4 and 16 sub-steps (3.6 / 3.1 / 3.0 %, 96.9 / 97.6 / 97.8 %, and 0.0078 against 0.0042).

Keep in prose:
- the 30-year split, 13.8 / 18.5 / 67.7 %;
- the 0.5166 against 0.5167 comparison;
- 3.7 × 10⁻³ **[M]**.

Add the 81 % share after 10 years **[M]**. The main text states it, but S4 gives only the 1-year and 30-year values.

**S5 (−115).**
- Cut "The largest phi of the posterior, 82, is below the smallest … 550". The table shows it.
- Cut the prior ln K check (1.60, 0.79).
- Shorten the 90-runs explanation to one sentence.
- Keep **[M]** 9.4 %.

**S6 (−130).**
- Cut the opener and the G re-definition.
- Cut the GWT set-up and replace it with "a GWT run at equilibrium (Text S2)".
- Drop the chloride example, or reduce it to one sentence.
- Keep **[M]** 39 %, 4.2 × 10⁻¹³ and 14 / 15 / 71 %.

**S7 (−260).**
- Cut the opener.
- Cut the Voronoi re-description to one sentence.
- Cut the loop repeat ("Foley and Black (2013) found flow loops rare … negligible").
- Cut the cell-centre explanation to one sentence.
- Keep **[M]** 186 against 121 m and **[M]** 215 m (Section 6, "1.8 times as wide").
- Keep the hedge "We did not test this reading …".
- The 215 and 126 m results belong to the dispersion study. Consider moving them under Figure S7.

**S8 (−130).**
- Cut the opener.
- Cut the specific yield, multipliers and pumping rates. S2 and the Figure S17 panel titles give them.
- Keep **[M]** 0.59 and 1.35 km².
- Keep "not a rule for drawing protection zones".

**S9 (−95).**
- Cut the opener.
- Resolve "46 years" against "45.9 years". The two likely differ only by the time in the well cell. State one value and its end point.
- Keep **[M]** 45.7 and 45.9.

**S10 (−150).**
- Cut the opener and the stream and drain set-up.
- Cut one of the two "consistency test" sentences.
- Keep **[M]** 32 % and 2 × 10⁻¹³.

**S11 (−145).**
- Cut the opener and the model re-description.
- Keep **[M]** 48.2 / 29.2 / 22.5 % and the hedge "We expect that …".

**Captions and figure text (−1,110).**
- S2: cut "Markers far above machine precision are limited by …". Table S4 says this.
- S4: cut "F extends east of the river because …". This is interpretation.
- S6: see Rewrite 3. Its panels (a, b) duplicate main-text Fig. 3. This is a scope question for the scope reviewers.
- S7 caption: split the three semicolon joins.
- S7 text: cut the "≥ against >" paragraph (~150 words) to two sentences. Cut the 2,000-day paragraph to its result. Keep **[M]** 5 %, 0.1 %, 8–90 % and the h^0.5 rate.
- S9: split the semicolon in the title. Cut the U___7, SV_487 and 3,944 m³/d numbers, which Table S5 gives. Cut 691 and 87 %, which Figure S12 gives **[M]**.
- S10: cut "Because each start cell has one particle, these cells form patches …". It describes what the reader sees.
- S12: cut "too small to see … every coloured cell". Keep **[M]** 711 and 602 of 691.
- S13: shorten the offset note to a pointer to S14.
- S16: cut the Voronoi sizes and "The band … is wider in (b)".
- S18: cut the last two sentences, which are results.
- S19: cut the MAW explanation and the colour wording (264 → 170).

## 4. Sample rewrites

### Rewrite 1. Text S3 (424 → about 250 words)

**Before** (opener, paragraphs 2 and 3, abridged): "This text gives in full one of the worked examples summarised in Section 4 of the main text. The shared model is the example model of that section. The two accountings of Section 2 differ only at weak sinks. A small well in strong regional flow is a weak sink. Its cell passes most of its water on to the neighbouring cells. This example shows how much … The shared model is split into three layers, of which the middle one is the least permeable (Text S2). The supply well pumps 800 m³/d from layer 3. A second, small well pumps 5 m³/d from layer 3 at row 17, column 13, upgradient of the supply well. … The supply well pumps all the water that flows into its cell. It is therefore not a weak sink. For this well the two accountings agree. Gross accounting treats the well as a transport model does. Net accounting remains an option, for comparison with studies that used it. Two checks test the code. The first is independent. … We refer to this as the boundary-control check. Here the fractions add up to 1 within 1 × 10⁻¹⁵. The same traces give boundary-control maps. Each map shows the share of every cell's water that leaves through one sink."

**After:**

The two accountings of Section 2 differ only at weak sinks. A weak sink takes only part of its cell's outflow (Text S1). A small well in strong regional flow is a typical weak sink. This example shows how much the choice of accounting changes the water attributed to such a well. It uses the three-layer model of Text S2. There a well pumps 5 m³/d from layer 3, upgradient of the supply well.

The small well's cell carries 33.7 m³/d. Gross accounting counts only the 5 m³/d that the well pumps. F in the well's cell is then 5/33.7 = 0.149. Net accounting fixes F = 1 in the cell. It attributes all 33.7 m³/d to the well. This is 6.7 times what the well pumps. Both accountings find the same flow path, a narrow strip along row 17 from the west edge to the well (Figure S14b, c). Under net accounting, 93–99 % of the water in layer 3 along that strip is assigned to the small well. Under gross accounting, 82 % of the water in the small well's cell flows on to the supply well. The supply well takes all the water that flows into its cell. Both accountings therefore give it the same water.

Net accounting reproduces the worked example of Foley and Black (2013) in every cell to 1 × 10⁻¹⁴ (Figure S14a). This check is independent of the code, because the example's fractions and volumes are published. On this model the boundary-control check of Text S1 holds to 1 × 10⁻¹⁵.

### Rewrite 2. Text S1, net-accounting selection rules (170 → about 90 words)

**Before:** "Which cells are fixed depends on how the group was selected. A pure cell or zone selection fixes all its cells, as FlowSource defines groups (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace, these are the cells where a selected term is a sink. In a forward trace, they are the cells where it is a source. This also holds when a term criterion is combined with cells or a zone. A cell with selected terms of both signs is fixed in both directions. A group with no such term fixes no cell, so every fraction is 0. A well listed at zero rate, a drain above the water table, or a losing river cell in a backward trace is therefore not fixed. On a stream network, a package selection fixes only the reaches whose records flow in the traced direction. To fix a whole stream, select its reaches as cells."

**After:**

Which cells are fixed depends on how the group was selected. A selection by cells or by zone fixes all its cells, as FlowSource does (Foley and Black 2013). A selection by package, boundary name or term fixes only the cells where a selected term flows in the traced direction. In a backward trace these are the cells where the term is a sink. In a forward trace they are the cells where it is a source. A well listed at zero rate is therefore not fixed in a backward trace. The same holds for a drain above the water table and a losing river cell.

### Rewrite 3. Figure S6 caption (289 → about 170 words)

**Before:** (full caption at SI line 783, including "Colours: five classes of reversed viridis (light = low F), with edges at 0.01, 0.1, 0.25, 0.5, 0.75 and 1 … The particles are PRT particles that lose weight at each sink as full mixing does. They were released over the cell volume. The particle share of a start cell is the share of its water that they deliver to the wells … The stored published areas lie one row south of their cells. We moved them one row north (Text S14). Inset: … Orange dots: wells. Blue lines: SFR reaches. White: inactive. Scale bar (a): 2 km.")

**After:**

**Figure.** Full-mixing maps for the eight priority wells of the Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022), in a 7.1 × 9.25 km window around four closely spaced wells. F is the share of a cell's water that ends at the wells. All panels show the uppermost active cell, with streams as cells and gross accounting. (a) F in the calibrated model. Grey: F < 0.01. Outlined: the published contributing cells, 688 of the 980 in all. (b) The F > 0.1 area against the published contributing cells. Dark blue: in both (538 cells). Orange: published only (150). Light blue: F > 0.1 only (1,090). (c) The F > 0.1 area against the cells where weight-losing PRT particles deliver more than half their water to the wells (Section 5). Dark blue: in both (495). Orange: particles only (86). Light blue: F > 0.1 only (1,133). (d) Mean F over 358 realisations. Outlined: published probability of contribution 0.5, corrected for a stored one-row offset (Text S14). Inset: the model, the three published particle regions and the window.


## 5. Estimate

The cuts remove about 3,900 words, about 25 % of these groups. That is roughly **5.5–6 pages of 69**: S1 ~1.2, S2 ~1.5, S3–S11 ~2, and captions and figure text ~1–1.5. The caption saving is the least certain, because figures sit on their own pages. Most of the saving comes from repeats. No cut removes an explanation at its first appearance in the SI. S1 gains plain definitions of F, G and weak sink.
