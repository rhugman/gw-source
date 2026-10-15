# Paper outline: gwsource, a tool paper built on worked examples

Branch `paper-draft-alt`, 2026-10-15. This replaces the method-and-benchmark outline of 2026-10-10 (still on branch `paper-draft`). Items marked [check] need verifying. Items marked [tutorial] need a change to a tutorial notebook so that the paper and the notebooks stay in step. Terms follow `docs/paper/terms.md`.

## 1. What changes

The paper demonstrates an open-source tool to practitioners. It is not a methods paper and not a benchmark study.

- **Results are worked examples.** Each example answers one practitioner question on a small model that a reader can rerun in seconds. Each example shows the output a practitioner would use and checks it against an independent approach where one exists.
- **The order of the examples follows the tutorial notebooks.** The paper describes each example model in its own words. The notebooks are the runnable version of the same examples.
- **All ten examples stay for now.** Cutting happens in review. Tutorial 10 (the Bedekar et al. 2024 unit-concentration example) was added on main on 2026-10-14 and merged into this branch.
- **Neversink becomes a short demonstration at the end.** It shows cost at scale and an ensemble on a real regional model. It explains in prose why our areas differ from the published MODPATH 7 areas. The detail moves to the Supporting Information (SI).
- **Limitations and trade-offs get their own section.** These are the limits of full mixing and of the code, with numbers from the examples.
- **Methods shrink to what a user needs to read the outputs.** Equations stay. Derivations and the solver detail move to the SI.

Model papers named by the author: Hugman and White (2026, *Groundwater*, pyEMU emulator), Bakker and Brakenhoff (2026, *Groundwater*, Timflow), White et al. (2016, *Environmental Modelling & Software*, pyEMU). [check] Read their structure and length before fixing the word budget.

## 2. Title, impact statement and key messages

Title (author's choice, 2026-10-15): a practitioner's question, then what the tool is.

- *Where does it come from and where does it go? Fast, open-source flow tracing for MODFLOW 6 models* (chosen 2026-10-15, replacing *Where does my well's water come from? Open-source flow tracing for MODFLOW 6*)
- Variants in the same style:
  - *Which land feeds my well? Open-source flow tracing for MODFLOW 6*
  - *Where does a well's water come from, and how old is it? Open-source flow tracing for MODFLOW 6*

Key messages, one per paragraph of the conclusions:

1. From the cell-by-cell flows a MODFLOW 6 model already saves, the tool maps contributing areas, the sources of a sink's water, travel times and the fate of water from a source.
2. Every result is checked against the water budget. The tool reproduces a published unit-concentration study (Bedekar et al. 2024) and a published worked example, agrees with MODFLOW 6 GWT to round-off, and with MODFLOW 6 PRT in totals and means. Per cell, it differs from PRT at the edge of a zone.
3. The answers come in seconds on small models. On a 1.68-million-cell model, one trace of nine destination groups takes 2–3 s. Ensembles of hundreds of realisations are therefore affordable.
4. The tool works on every MODFLOW 6 grid type, with stream networks, movers, multi-aquifer wells and multi-model simulations, in steady-state and transient flow.
5. Full mixing has costs. Its areas are wider and more diffuse than particle areas. Its thresholds need judgement. Snapshots of a transient model have no travel lag. Transient tracking and ensembles need memory. The paper states when to use particles or transport instead.

## 3. Section plan with word budgets

Word budgets are first guesses for a *Groundwater* research paper. [check] the journal's current limit.

| § | Section | Words | Figures |
|---|---|---|---|
| 1 | Introduction | 900 | — |
| 2 | Method in brief | 1,100 | Fig. 1 (schematic) |
| 3 | The software | 600 | Table 1 (inputs and outputs) |
| 4 | Worked examples (ten) | 4,000 (about 400 each) | Figs 2–11 |
| 5 | A regional model: Neversink | 600 | Fig. 12 |
| 6 | Trade-offs and limitations | 900 | Fig. 13 (dispersion) or SI |
| 7 | Conclusions | 300 | — |
| 8 | Code and data availability | 150 | — |
| | Total | about 8,550 | 13 figures (too many; cut in review) |

### 3.1 Introduction (about 900 words)

- **The practitioner's questions.** Where does the water pumped by a well come from? Which land should be protected? How old is the water? How do the answers change through the seasons, and how sure are we? Protection zones and risk-based studies need these answers for many wells and many realisations [EA19, Fienen et al. 2022].
- **Existing tools, framed politely as what we add.**
  - Particle tracking (MODPATH, MODFLOW 6 PRT) is the standard. It needs a stop-or-pass rule at weak sinks.
  - Transport with tagged water (GWT, unit concentration [BED24]) needs one run per source.
  - Full-mixing flow tracing: the reference method [FB13, BF13], used for source protection zones in England [EA19], and MODALL [POT08]. Neither is open source for MODFLOW 6.
- **What the tool adds.**
  - Open source, for MODFLOW 6 output.
  - Every grid type, package networks and multi-model simulations.
  - Gross and net accounting at weak sinks.
  - Water-budget checks on every result.
  - Transient tracking through storage, backward and forward.
  - Low cost, so ensembles are affordable.
- **What the paper does.** It shows each capability on a small example with the output a practitioner uses and a check against another approach. It closes with one regional model and an honest list of trade-offs.
- Reuse: the current §1 paragraphs on weak sinks, MODALL, unit concentration and adjoint methods, shortened. Table 1 of the current draft (method comparison) moves to the SI or becomes part of the new Table 1.

### 3.2 Method in brief (about 1,100 words)

Only what a reader needs to read the outputs. Each concept is explained in plain words where it first appears.

- **Full mixing.** Each cell is a fully mixed volume. Its water leaves through its outflows in proportion to the flows.
- **Backward fraction F and forward fraction G.** One equation each, (I − P) F = S D and its forward analogue, with a plain reading. A contributing area is a threshold on F.
- **Volumes.** Volume through, volume from, and the split of a sink's water by source.
- **Gross and net accounting.** Gross credits a weak-sink well with its pumping. Net credits it with all the water passing through its cell, as the reference method does.
- **Budget checks.** Closure and the forward–backward check, in one sentence each, with what they test and what they do not.
- **Mean travel time.** The equation, porosity as an explicit input.
- **Transient flow.** Snapshots (each step as a steady state), and transient tracking (tagged water carried through storage, forward and backward in time). One equation for the tracking step.
- To the SI: solution in flow order and flow loops, net-accounting details, the backward-in-time derivation, the current §2.4 and §2.8 in full.
- Fig. 1: the current method schematic (`fig1_method_schematic`). Its panel c already uses the three-layer example model.

### 3.3 The software (about 600 words)

- **Workflow.** Run MODFLOW 6 with the flows saved, read a step, select destinations or sources (by package, boundname, cells or zone), trace, read the outputs, export. A short code block of about ten lines, the quickstart example.
- **Inputs.** Grid file, budget file, and (for package networks) the package budget files. Which save options are needed.
- **Outputs.** F and G maps, volumes, source splits, travel time, transient statistics, ensemble statistics. Export to npz, netCDF and GeoPackage.
- **Cost.**
  - On a 1-million-cell synthetic grid, the solve takes 0.55 s for four groups, about 1.1 s in all with assembly, loop detection and outputs, on 16 cores (PLAN Phase 2 benchmarks).
  - This number is only in an HTML comment in the current §3.3. [check] Rerun the benchmark before quoting it.
  - Memory: Neversink peaked at 2.5 GB, plus about 0.19 GB per extra group.
  - Use under the PEST++ run manager is untested.
  - Neversink timings stay in §5.
- **Testing.** The test suite runs ten test models and the published worked example. The full verification table (current Fig. 2 and Table S1) moves to the SI (decided). The main text uses the checks in the examples.
- Table 1: inputs, selections and outputs in one table, each with the example that shows it.

### 3.4 Worked examples (about 3,600 words)

**Shared example model (opening paragraph).** A 2 km × 2 km unconfined aquifer of 40 × 40 cells of 50 m:
- top at 20 m and bottom at −30 m, with K 5 m/d;
- recharge of 5 × 10⁻⁴ m/d;
- a constant head of 10 m on the west edge;
- a north–south river (stage 6 m) 1.5 km from the west edge;
- a supply well pumping 800 m³/d 100 m west of the river. Each example changes this model where its question needs it. One sentence names the notebooks (decided): each example ships as a runnable notebook that reproduces its numbers and figure (Section 8). This replaces the earlier rule of never writing "tutorial" in the main text. Elsewhere, the text still describes the models in its own words rather than pointing to notebooks.

Each subsection follows the same pattern:
1. the question;
2. the model change;
3. the output a practitioner uses;
4. the check against another approach;
5. one sentence on the limit it shows.

#### 4.1 Where does the well's water come from? (tutorial 01)

- Output:
  - F map with the F > 0.1 and F > 0.5 contours, 1.575 and 1.143 km² (630 and 457 cells; the same with ≥ or >);
  - [tutorial] tutorial 01 prints 1.142, while 06 and 09 print 1.143. Use one rounding.
  - expected area ΣF·A of 1.173 km²;
  - the well's water by source: recharge 71 %, west edge 15 %, river 14 %.
- Check:
  - closure (the traced sources add up to the 800 m³/d pumped);
  - **needs an independent check**: the PRT captured fraction against F on the same model.
    - Tutorial 06 already runs PRT on this model. Mean |PRT captured fraction − F| is 0.058 over all release cells and 0.164 over the 372 edge cells.
    - Cite that here, or move a short version into tutorial 01 [tutorial].
- Limit: the threshold is a judgement.
  - In the dispersion study, F ≥ 0.5 is within 5 % of the advective area at cells of 50 m or less.
  - F ≥ 0.1 contains the advective area. It is 8–16 % larger on a recharge-fed problem like this aquifer, and 30–90 % larger with regional flow.
  - The narrow tail east of the river shows a weak-sink river in one layer.
- Figure: F map with both contours, plus a source bar or pie.

#### 4.2 What is being computed, and what changes at a small well? (tutorial 02)

- Check: the Foley and Black (2013) 3 × 3 worked example, reproduced exactly (to 10⁻¹⁴), and a direct dense solve.
- Output: the three-layer model with a 5 m³/d well in a cell carrying 33.7 m³/d. Gross credits it with 5 m³/d, net with 33.7 m³/d (6.7 times). Boundary-control and dominant-sink maps.
- Limit: net accounting over-credits weak sinks. Use it to compare with the reference method only.
- Figure: net against gross F maps around the weak well (layer 3), or reuse the current Fig. 1c.
- [tutorial] Rerun: the net-accounting code changed on 2026-10-10, after the stored outputs were made. Print the claims that are now only read off maps (the "about 93 %" strip, gross = net × 5/33.7).

#### 4.3 Where does each source's water go? (tutorial 03)

- Output:
  - G maps of river, west-edge and recharge water;
  - the well's water by source, matching the backward split of §4.1;
  - fate of each source: 29 % of recharge reaches the well, 71 % the river;
  - a 300 m × 300 m field: 39 % of its recharge reaches the well, nitrate diluted from 50 to 1.11 mg/L at the well (invented concentrations, stated);
  - mixed chloride at the well, 18.6 mg/L.
- Check:
  - forward–backward agreement for each source (to the cell budget residual);
  - **needs an independent check**, G against MODFLOW 6 GWT at equilibrium on this model [tutorial].
    - The notebook says tutorial 08 makes this comparison. It does not: 08 compares transient tracking.
    - The paper already has GWT agreement to 2.8 × 10⁻¹¹ on test models 1 and 2 (Table S1), which could be cited instead.
- Limit: G is the long-run value, with no arrival time and no reactions.
- Figure: field plume G map with its fate split, beside the river G map near the well.

#### 4.4 Does it work on my grid? (tutorial 04)

- Output:
  - the same trace on DIS, Voronoi DISV and DISU (with and without vertices);
  - land-use zones (farmland, village, woodland) with the recharge each sends to the well;
  - GeoPackage export.
- Checks:
  - DIS = DISU exactly;
  - XT3D with 5 flow loops, where the block solver equals a plain sparse LU (3.3 × 10⁻¹⁶);
  - the reference method's edge deletion changes F by up to 0.155;
  - On DISV, the expected area ΣF·A is 8 % smaller (1.082 against 1.173 km²) and the river share is 21 % instead of 14 %. The notebook attributes this to the river cell lying 70 m from the well cell instead of 100 m. That is a reading, not a test.
- Limit:
  - DISU without vertices gives fractions but no maps;
  - PRT runs on DIS and DISV only;
  - Voronoi cells do not reduce numerical dispersion.
- Figure: DIS against DISV F maps with a grid inset; optionally XT3D F with the loop cells.
- [tutorial]:
  - the tables are stored as HTML only;
  - "flow cycles" should become "flow loops";
  - name the area metric (ΣF·A vs F > 0.5 area);
  - remove the PLAN.md references.

#### 4.5 How does the contributing area change through the seasons? (tutorial 05)

- Model: storage, seasonal recharge (×1.8, 1.0, 0.1, 1.1) and pumping (640–1,120 m³/d), 3 years of 3 steps per season.
- Output:
  - seasonal F maps;
  - the well's water by source per season (in the dry season 52.5 % comes from storage);
  - min, mean and max F;
  - always, sometimes and never;
  - nested protection zones:
    - inner (always F > 0.5): 0.52 km²;
    - seasonal (sometimes F > 0.5): 0.93 km²;
    - outer envelope (max F ≥ 0.1): 1.86 km², of which 0.41 km² lies outside the other two;
    - [tutorial] use one threshold form.
- Check: the step-by-step statistics equal a brute-force calculation over the stored steps (10⁻¹⁴). Every snapshot closes.
- Limit:
  - snapshots have no travel lag;
  - storage hides the true source;
  - equal weighting of steps of different length distorts the mean.
- Figure: four seasonal F maps over the protection-zone composite.
- [tutorial]:
  - use strict thresholds as the paper does;
  - print the per-season areas quoted in the text;
  - one HTML-only table.

#### 4.6 How old is the water reaching the well? (tutorial 06)

- Output:
  - mean travel-time map;
  - 5-year and 25-year time-of-travel zones (0.098 and 0.455 km²);
  - age by source (river 2 years, recharge 42 years, west edge 108 years);
  - porosity scaling without a rerun.
- Check against MODFLOW 6 PRT. The particles are weight-losing: they lose weight at weak sinks as full mixing does.
  - All water: 45.7 against 45.9 years (−0.5 %). This overall agreement follows largely from the volume identity, so it is not an independent test of travel times.
  - By source: recharge −2.1 %, west edge +2.1 %, river −20 %.
  - 799.9 of 800 m³/d captured.
  - Per cell, the informative comparison: the PRT/full-mixing time ratio is near 1 in the core (median 0.96) and large at the zone edge (median 5.7).
- Internal identity: ΣVF/Q equals the flow-weighted mean time, up to the budget residual.
- Limit:
  - mean time, not first arrival;
  - 50 m cells cannot resolve 50-day zones;
  - zone edges disagree with particles.
- Figure: travel-time map with zone contours, beside the PRT scatter.
- [tutorial]:
  - the zone comparison uses the time to the well instead of the time to the well cell, and should use the latter;
  - "a little larger" should be +24 %;
  - "flux-weighted" should become "flow-weighted".

#### 4.7 What if the water passes through streams, drains, wells or other models? (tutorial 07)

- Output:
  - with streams as cells, 32 % of the well's water is "stream water";
  - with SFR reaches and the mover as a network, that water resolves into upstream inflow and recharge, and the drained areas join the contributing area;
  - 188 of 800 m³/d passes through the mover;
  - a weakly pumped multi-aquifer well (10 m³/d, screened in all three layers) carries 14.3 m³/d of shallow water down to the deep supply well.
- Check: a model split into three models matches the single model (F to 2 × 10⁻¹³). Closure holds on both graphs.
- Limit:
  - movers between models are not read;
  - flux outputs are not defined on package nodes;
  - the PRT helper is single-model only;
  - the save options are required.
- Figure: F with streams as cells | F with the network | F per reach.
- [tutorial]:
  - the 10⁻¹³ agreement is called "the solver tolerance" (the paper uses 7.4 × 10⁻¹⁰ for the test models); reconcile;
  - print the closure value;
  - remove the PLAN.md references.

#### 4.8 How much of the pumped water arrived since the start? (tutorial 08)

- Model: the seasonal model run for 30 years, 1 step per season (121 steps), porosity 0.3.
- Output:
  - the well's water by origin through time (initial water 52 % at year 30);
  - backward fate maps (share reaching the well within 30 years, the river, or still stored);
  - snapshot shares against tracked shares, so the snapshot error is visible.
- Check against MODFLOW 6 GWT: 9.8 × 10⁻¹⁴ over 1,600 cells and 121 steps, with GWT's water volumes and the recharge tag.
  - The default volumes keep every cell's water balance exact. They differ from GWT's by up to 1.9 × 10⁻⁴ in the forward fraction and 3.7 × 10⁻³ in the backward fraction.
- Internal identities: forward–backward agreement (2.9 × 10⁻¹⁶); every tagged balance closes.
- Limit:
  - every step must be saved;
  - porosity is needed;
  - long steps make early arrival too early, so sub-steps are needed;
  - memory grows with the number of steps.
- Figure: the current Fig. 4.
- [tutorial]: the notebook uses 1 sub-step; the paper's Fig. 4 uses 4. Pick one and align the numbers (river share at year 1, cumulative initial water). Print the snapshot means (60/12/15/13 %).

#### 4.9 How sure are we? (tutorial 09)

- Model: 20 random-K realisations (prior, K = 5·exp(0.8 z)).
- Output:
  - P(F > 0.5) and P(F > 0.1) maps;
  - a zone at a stated risk level;
  - spread of the river share (0.7–27 %) and travel time (36–54 years, 5–95 %);
  - traced in 0.84 s for all 20.
- Main finding: parameter uncertainty dominates the integral answers (area, shares, travel time). But the uncertain edge band from the ensemble (0.77 km²) is about the same size as the band from mixing in one model (0.80 km²).
- Checks:
  - exact against histogram quantiles, within one bin width for values inside the histogram range (45 cells fell above it, unbounded);
  - ΣP·A = mean area;
  - serial and parallel runs bit-identical.
- Limit:
  - memory for exact quantiles: 4 GB per series for 1,000 realisations of 1 million cells, 24 GB for the six series of this example;
  - the same grid is needed in every realisation;
  - prior only.
- Figure: probability maps beside the source-share box plot. Once the PEST++ run exists, show prior against posterior P(F > 0.5).
- PEST++ (decided: run it). The notebook conditions the ensemble on heads with PEST++ IES and traces the posterior realisations. That shows the practitioner output that matters: how history matching narrows the capture probability.
- [tutorial]:
  - make the PEST++ section run end to end. It currently has an undefined `write_parameters` and a hard-coded `f[1234]`. pestpp-ies is not installed yet;
  - the grid-and-mixing column is hard-coded text;
  - the travel-time range is quoted two ways.

#### 4.10 Does it reproduce a published unit-concentration study? (tutorial 10)

- Model: the Bedekar et al. (2024) example, rebuilt in MODFLOW 6, including the values the paper leaves open.
- Output: the well's water by source over 25 years (lateral inflow, recharge, stream, stored water). Backward time-limited contributing areas show where the pumped recharge and stream water entered.
- Checks: against four MF6 GWT unit-concentration runs (≤ 1.5 × 10⁻¹⁰), and against the paper's Figure 2 (≤ 1.3 percentage points). Over long times it tends to the steady-state result.
- Why it matters: one tracking run replaces four transport runs, one per source, and it adds the backward view.
- Limit: transport sub-steps are needed for arrival fronts. Run time is about 2.5 min, the longest of the examples.
- Figure: the well's source shares over time, set against the published curves.
- [check] This entry was written from the tutorials README only. Read the notebook before drafting.

### 3.5 A regional model: Neversink (about 600 words, one figure)

- **Model.** USGS Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022):
  - 4 layers of 680 × 619 cells of 50 m (1.68 million cells), 12,316 SFR reaches;
  - 8 priority wells pumping 3,671 m³/d;
  - the calibrated model and its 358-realisation ensemble.
- **Cost.**
  - One trace of nine destination groups (each well alone and all eight together) takes 2–3 s, about 1 s of it reading the budget file.
  - The MODFLOW 6 run takes 44 s. PRT takes about 30 s when it writes end points only, and 5–13 min with full tracks.
  - Closure to 10⁻¹² m³/d.
  - The 358 realisations took 76 min on six processes. Per realisation, that is about 50 s of MODFLOW 6 and about 9 s for two traces.
- **Practitioner output.**
  - ensemble mean F, correlated with the published probability of contribution at r = 0.80;
  - expected area 90 % of the published one;
  - the stream share of the wells' water (43 %), which traces to recharge with the stream network.
- **Why our areas differ from the published ones (prose, about 250 words).**
  1. The published area is where each start cell's single particle stops. Three particle settings decide it: recharge and stream flows enter at the top face, particles stop at every weak sink, and particles in dry cells are draped. PRT reproduces it (overlap 0.998) only with all three.
  2. On the same flow field, particle settings alone move the overlap from 0.62 to 0.998.
  3. Full mixing splits each cell's water among all its outflows, so its areas are wider and more diffuse. The published cells send on average 42 % of their water to the wells. F > 0.1 is the counterpart of a particle area, not F > 0.5. F > 0.1 holds 87 % of the area of particles that lose water at sinks as full mixing does.
  4. At weak-sink wells and buried stream cells, particles stop and credit all their water to the sink. Full mixing passes the rest on.
  5. Gross or net accounting changes the overlap little (0.41 to 0.44).
  6. With the stream network, stream water traces to recharge upstream, and the area grows.

  Do not write that full mixing lies "within the range" of particle results. With water-conserving runs only, it lies below it (0.30–0.41 against 0.62–0.998). Mark points 3 and 6 as interpretation where they are inferred.
- **Figure.** One row in the U-cluster window:
  - (a) F with the published outline;
  - (b) F > 0.1 against the published cells;
  - (c) F > 0.1 against the particle P > 0.5 area;
  - (d) ensemble mean F;
  - a locator inset replaces the current Fig. 5.
- **To the SI.** The current §5 in full, with Figs 5–9 and Figures S2–S3: the reproduction table, end states, net attribution, ensemble statistics and pumping scenarios.
  - The pumping scenarios are dropped (decided): Fig. 9, Tables S5–S6, Text S11 and Figure S3.
  - The scenario rule in Text S10 goes too. Its first half, the Monte Carlo offsets, stays, because the ensemble comparison needs it.

### 3.6 Trade-offs and limitations (about 900 words)

One paragraph each, with the numbers from the examples:

1. **Full mixing against particles.**
   - Areas are wider and more diffuse. The band width narrows with cell size h, roughly as h^0.5.
   - On the dispersion-study problems, F ≥ 0.5 is within 5 % of the advective area at cells of 50 m or less. F ≥ 0.1 contains it but is larger.
   - On Neversink, F > 0.1 misses 27 % of the published cells and 13 % of the particle P > 0.5 cells. So "contains" does not hold in general.
   - Use particles where a sharp edge matters. Use full mixing for coverage, any grid, networks and ensembles.
   - (Dispersion study; §4.1, §4.6, §4.9, §5.)
2. **Choosing a threshold.** A judgement that depends on the purpose; state it.
3. **Weak sinks.** Gross against net, and what each answers (§4.2).
4. **Snapshots, transient tracking or GWT.** Snapshots are cheap but have no travel lag. Tracking needs every step saved and porosity. GWT is the reference transport (§4.5, §4.8).
5. **Memory and cost.**
   - Transient series and exact ensemble quantiles grow with steps and realisations.
   - Histogram quantiles bound the memory (§4.8, §4.9).
   - On Neversink, the peak was 2.5 GB, plus about 0.19 GB per extra group.
6. **What the code does not read.** Movers between models, PRT on DISU, flux outputs on package nodes (§4.4, §4.7).

Reuse: current §6.1–6.4 and §7, cut to the trade-offs (they currently lean on Neversink). Fig. 12: the current Fig. 3 (numerical dispersion), or move it to the SI.

### 3.7 Conclusions (about 300 words)

The five key messages of section 2, one short paragraph each.

### 3.8 Code and data availability (about 150 words)

The repository, the version used, the ten example notebooks with their run times, the Neversink scripts and the published model archive.

## 4. Supporting Information

- **Text S1:** sources by column (current Text S1).
- **Text S2:** the method in full.
  - Current §2.4 and §2.8, net accounting and flow loops.
  - Current Texts S4–S6: solution of the linear systems, the travel-time identity, and the water-volume options.
- **Text S3:**
  - the example models in full: every builder, with the parameters needed to rebuild them without the code;
  - the ten test models and the hand-built 15-cell network (current Text S3, si/C.md).
- **Table S1 and Figure S1:** the verification on the test models (current Fig. 2 and Table S1).
- **Text S4:** transient checks on the seasonal model (current Text S7), aligned with §4.8.
- **Figure S2:** numerical dispersion (current Fig. 3 and Fig. S1), if it leaves the main text.
- **Texts S5 onwards:** Neversink in full (current §5, Figs 5–9, Figures S2–S3, Tables S2–S6, Texts S8–S11).

## 5. Work on the tutorials before drafting

The paper and the notebooks must give the same numbers.

1. **Rerun all ten notebooks** on the current code. Tutorial 02's outputs predate the net-accounting change of 2026-10-10.
2. **Independent checks for tutorials 01 and 03.**
   - 01: cite PRT from 06, or add a short PRT comparison.
   - 03: add a GWT-at-equilibrium comparison.
3. **Consistency fixes**, listed in each subsection above:
   - the 06 travel-time end point;
   - the 08 sub-steps;
   - the 07 tolerance wording;
   - the 09 PEST++ section and hard-coded text;
   - strict thresholds in 05;
   - HTML-only tables in 04 and 05.
4. **Print every number the text quotes.** Several claims are currently read off plots.
5. **Terms.** Use "flow loops", "flow-weighted", "weight-losing particles" and "net accounting" (not "net mode"). Rows and columns should be 1-based in prose.
6. **Remove references to `PLAN.md`** and other internal notes. They appear in tutorials 01, 02, 03, 04, 06, 07, 08 and 09.
7. **Runtimes.** The README and the notebook headers disagree; print the measured times.

## 6. Decisions (author, 2026-10-15)

1. Name the notebooks once in the §4 opening: yes.
2. Test-model verification moves to the SI. The main text uses the checks in the examples.
3. Neversink pumping scenarios: dropped.
4. Tutorial 09's PEST++ section: run it.
5. Title: *Where does my well's water come from? Open-source flow tracing for MODFLOW 6*, or one in that style.
