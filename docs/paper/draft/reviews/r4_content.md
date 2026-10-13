# Round 4 content review

Scope: numbers and claims against evidence, cross-references, novelty and fairness, and lost content compared with 0082a1e. Line numbers refer to the files as they stand on branch paper-draft. Only problems are listed.

## sections/00_front.md

- **00_front.md:11, SHOULD.** "In tests, traces ... matched MODFLOW 6 transport to rounding error" is too general. Only forward transient tracking with the "gwt" volume option matches to round-off. Steady G against GWT differs by 2.8e-11 and 1e-8, which is limited by the flow solver (Fig. 2; §4.1). Fix: "forward transient tracking matched MODFLOW 6 transport to rounding error; steady traces matched to the flow solver's tolerance."
- **00_front.md:11, SHOULD.** "every MODFLOW 6 ... boundary package" is broader than tested (si/C lists the packages tested). Fix: "any package that writes its flows to the budget file", or name the tested set.
- **00_front.md:11, SHOULD.** MODALL is named but not cited, while FlowSource is. Add Potter et al. 2008, or drop the name from the abstract.

## sections/01_introduction.md

- **01_introduction.md:11, MUST.** "Where water circulates between cells, for example around a pair of wells" has no support. Under standard conductance flow a well pair does not create a cell-to-cell flow loop. FB13 (Method) attributes loops to unstable multilayer models, and the loops found in this work come from XT3D and from two-way reach–aquifer exchange (terms.md; NS §4 "Cycles": 8 network loops of 4–130 nodes, none with streams as cells). Fix: "Where water circulates, for example with the XT3D flow formulation or where a stream and the aquifer exchange water both ways (Section 2.4)".
- **01_introduction.md:11, SHOULD (fairness).** The sentence says FlowSource deletes the smallest-flow connection, but not why. FB13 treats loops as rare artefacts of unconverged or unstable models, with flows below convergence limits and negligible effect (FB13 lines 283–289; BF13 line 160). Add half a sentence saying so, then that under MODFLOW 6 with XT3D or package networks such loops carry real flow. This states the contrast without implying FB13 was careless.
- **01_introduction.md:7, MUST.** "particles also do not directly give the share of pumped water that was already stored" has no source or evidence comment. It is the same claim as §4.4:45. Fix: cite Environment Agency 2019, Appendix C4.3 (backward particle tracking through transient flows is awkward to set up and the results hard to interpret), or soften to "particles do not readily give".
- **01_introduction.md:19, SHOULD.** "two budget checks" conflicts with §2.5 (02_methods.md:51), which opens "Three checks" and then names four (backward closure, forward closure, forward–backward agreement, boundary control). Reconcile the count in both places.
- **01_introduction.md:17, SHOULD (novelty).** "We found no published comparison ... on a large real model" must stay a gap statement, not a claimed contribution beyond decisions_r3 item 9. Also note that Environment Agency 2019 already recommends sense-checking MODPATH zones against FlowSource output; acknowledge this so the gap is not overstated.
- **01_introduction.md:17, SHOULD.** "These methods solve for concentrations" does not fit the age and life-expectancy methods cited in the same sentence. Fix: "These methods solve a transport or adjoint equation".
- **01_introduction.md:9, SHOULD (optional).** Environment Agency 2019 (C4.4) itself calls F a "capture fraction". One clause saying so would show why the contrast with Leake et al. 2010 capture matters.

## sections/02_methods.md

- **02_methods.md:83, MUST.** "(Section 4.4)" for the step-boundary appear/disappear effect is a broken reference. The volume-option numbers moved to the SI Text on transient checks of the seasonal example model. Fix: point to {SI: transient checks on the seasonal example model}.
- **02_methods.md:73, SHOULD.** "They have no travel time" is wrong for snapshots, since the mean times of §2.6 apply per snapshot. v6 said "no travel lag", and §7 still says that. Restore "no travel lag".
- **02_methods.md:47, SHOULD.** Decision 15 asked for one technical sentence on the loop solve. There are now four (LU over strongly connected components, M-matrix, pivoting). Cut to one and move the rest to si/B.
- **02_methods.md:51, SHOULD.** See 01_introduction.md:19: "Three checks" followed by four named items.

## sections/03_implementation.md

- **03_implementation.md:15, SHOULD.** "One hundred wells traced separately would need about 20 GB" is ambiguous. Traced separately, each would need about 1 GB. The 20 GB figure is for 100 groups in one trace (0.52 GB load + 100 × 0.19 GB) and was not run. Fix: "One hundred wells as separate groups in one trace would need about 20 GB (an estimate; not run)".
- **03_implementation.md, SHOULD (lost content, minor).** Lost from v3.2 with no home: output formats (npz, netCDF, GeoPackage), ensemble tracing per realisation, and "volumes interpolated" for sub-steps. Restore one sentence or move them to si/B.

All memory numbers match r4_memory.md (2.52 GB peak, 0.52 GB load, 0.19 GB per group, about 115 MB per group per million cells, about 1 s load, 2.4–2.7 s total).

## sections/04_verification.md

- **04_verification.md:45, MUST.** "Snapshots and particles do not give it directly" has no source. Fix: "Snapshots cannot give it, because water released from storage has no known origin (Section 2.7); backward particle tracking through transient flows is awkward to set up and interpret (Environment Agency 2019, Appendix C4.3)." Or drop "and particles".
- **04_verification.md:39, SHOULD (lost caveat).** v6 said the shares are those of a vertically mixed aquifer. Restore it after the one-layer sentence, with the reason it matters (in layered aquifers shallow and deep water reach the well in different shares).
- **04_verification.md:19, SHOULD.** "Both directions therefore rest on an independent code" reads as if the method depends on that code. Fix: "Both directions are therefore checked against independent code".
- **04_verification.md, SHOULD (lost result).** The PRT travel-time comparison (9,574 against 9,590 d) left the main text and now sits under Table S1 in si/C.md. That is an acceptable home, but si/B.md:15 still points to it as "Section 4.1" (see si/B.md).

The §4.4 seasonal model matches herebedragons.py and its notebook: 40 × 40 cells of 50 m, K 5, CHD 10 m, river in column 30 (100 m east of the well at row 20, column 28), recharge 5e-4 m/d (0.18 m/yr) with season factors 1.8/1.0/0.1/1.1, pumping factors 0.8/1.0/1.4/0.8, Sy 0.2, porosity 0.3, a 1-day steady period plus 120 seasons (121 steps). The shares 60/12/15/50, 52/33/16, 98/81/68 and 13.8/18.5/67.7 match README_method.

## sections/05_neversink.md

- **05_neversink.md:47, MUST.** "the published area changes with the particle settings, not with the water reaching the wells" misstates the mechanism. The particle settings are fixed across realisations. NS §6 says the variation shows up through the particle conventions, not in the full-mixing capture. Fix: "varies through how the fixed particle settings act on each realisation's flows (where particles stop), while the sum of F does not follow it."
- **05_neversink.md:33, SHOULD.** "therefore comes from both mixing and the published particle settings" is firmer than the evidence. v6 said "We attribute". Restore the hedge.
- **05_neversink.md:33, SHOULD (lost result).** "The 89 missed cells receive 6 % of the water PRT delivers (227 of 3,736 m³/d)" was removed. The HTML comment says it is now only in Fig. S2, but si/E.md has neither 6 % nor 227. Add it to the numbers paragraph of si/E.md or restore it here.
- **05_neversink.md:37 and 55, SHOULD.** The stream share is 43 % in §5.4 (calibrated model) and 42 % in §5.6 (median over realisations). Say which is which at each use.
- **05_neversink.md:57, SHOULD.** "mainly" was lost. NS says the published area grows more slowly mainly because of buried-stream stops (4.76 → 3.83 km²; the rest, 3.83 → 3.62, is other weak sinks). Restore "mainly". Also state that the weight-losing particles here are single particles from the published starting points with the top-face setting, not the flow-weighted particles of §5.3.
- **05_neversink.md:21, SHOULD (optional).** "A published particle stops in the cell of U___7" reads as one particle. Fix: "Published particles stop ...".

All other numbers match NS: 0.41/0.30; 445 cells at 94 %; 2,139; 27 %; 910/978; 0.29–0.998; 99.0 %; 3,736 m³/d (+1.8 %); 0.39–0.62; 691; 87/59/92 %; r = 0.80; 90 %; 0.48; CV 32 %; r = 0.997/0.00; 3.68/4.09/3.60/3.62; 4.57.

## sections/06_discussion.md

- **06_discussion.md:23, MUST.** "(Section 4.4)" for the difference between the volume options is a broken reference; those numbers moved to the SI. Fix: point to Section 3.2 and {SI: transient checks on the seasonal example model}.
- **06_discussion.md:43, MUST.** "Short horizons, which need transport sub-steps (Section 4.4)" is the same broken reference. Same fix.
- **06_discussion.md:35, SHOULD.** "missed some cells" understates the result (27 % of the published cells; 13 % of the P > 0.5 area). Fix: "missed parts of both particle areas (Section 5.3)".
- **06_discussion.md:35, SHOULD.** "Take the size ... from the expected area ... since the F > 0.5 area is smaller" does not say smaller than what. Fix: say it is smaller than the published area, and that the sum of F came close to the published cell count.
- **06_discussion.md, SHOULD (lost content, minor).** The v6 advantage "many sources at once, with no transport run" is gone. One clause in §6.3 would restore it.

The 0.33–0.35 and 35 % figures at 06_discussion.md:11 check out, and the Environment Agency 2019 C4.3–C4.4 citation is supported. Each piece of §6.5 advice was checked against the section it cites; only item 5 (line 43) has a broken reference.

## sections/07_limitations.md

No MUST or SHOULD items. The decision-36 rewrite dropped the Neversink scope caveats, but each has a home: the inferred scenario rule (§5.6), inferred pairing (si/D), maxrange (si/D and si/F_editor) and the faster-growth inference (si/F_editor Text S8). "Uppermost active layer only" was dropped (minor). 1.6 GB per array is correct.

## sections/09_availability.md and si/C.md

- **09_availability.md:3 and si/C.md:3, SHOULD.** "The example models ... ship with the code as tutorials" is not true of the eight-cell example. It lives in studies/paper/method_figures.py (GRAPH_EDGES), not in tutorials, and the FB13 worked example and the sub-step network are tests. Fix: "ship with the code as tutorials, tests or figure scripts", or name where each lives.

## display/D.md

- **display/D.md:7 (Fig. 6 caption), MUST.** "(pale area south-east of the U wells)" no longer fits the redrawn reversed-viridis map. That area is green (F 0.1–0.25); pale yellow is F 0.01–0.1. Fix: "green area (F 0.1–0.25) south-east of the U wells".

The rest of the caption matches figures/README.md (classes 0.01/0.1/0.25/0.5/0.75/1; 7.1 × 9.25 km windows; 2 km scale bar in (a); orange dots; SFR lines; black outline with white halo). display/B.md (Fig. 1: 6/11, 5.0 vs 33.7, panels a–d) and display/C.md (Fig. 2: 2.5e-11, 1.2e-14/1.4e-11; Fig. 4 numbers) match their sources.

## si/B.md

- **si/B.md:15, SHOULD.** "compared with particles in Section 4.1" now dangles; the comparison moved to si/C under Table S1. Fix: point to {SI: verification errors per check and model}.

## si/C.md

- **si/C.md (model 8 row), SHOULD.** "model 2's grid and stresses" is not exact. Model 8 has no 400 m³/d well; it has the 5 m³/d WEL plus a MAW at 30 m³/d. Fix: "model 2's grid, with the 400 m³/d well replaced by a MAW well (30 m³/d)".
- **si/C.md (model 6 row), SHOULD.** The periods use a time-step multiplier of 1.2, which the table omits. Add it.

The rest of the table matches tests/models/*.py (BaseSpec 20 × 30, 6 inactive cells, CHD 5, RIV column 22 stage 6, WEL 800, RCH 1e-3; model 2 3 × 15 × 25 with wells 400/5; model 5 XT3D; model 7 20 SFR reaches, inflow 500, DRN factors 0.7/1.0; model 9 LAK/UZF/MVR; model 10 4e5 d in 120 steps). The three-layer example matches build_layered (botm 0/−12/−30; K 10/1/15; weak well at (2, 16, 12), 800 m west and 200 m north).

## Cross-references and citations checked with no problems

Eqs 1–9 in the sections, the Fig. 1 caption and si/B; Fig. 4 panel references (c, d–f); §2.8:89 and §6.3:25 references to Section 4.4; no stale §2.9 references. Every author–year citation in the main text and display files has an entry in sections/10_references.md.

## Summary

MUST: 8. SHOULD: 27.

Five most serious:

1. **05_neversink.md:47.** The S-region sentence attributes the variation to "the particle settings", which are fixed. It should say the fixed settings act differently on each realisation's flows.
2. **01_introduction.md:11.** The "pair of wells" loop example is unsupported. Loops here come from XT3D and two-way reach–aquifer exchange. Also add FB13's own view that loops are rare artefacts with negligible effect.
3. **04_verification.md:45 and 01_introduction.md:7.** The claim that particles do not give the stored-water share has no source. Cite Environment Agency 2019 C4.3 or soften.
4. **02_methods.md:83, 06_discussion.md:23 and 06_discussion.md:43.** These "Section 4.4" references are broken: the content moved to Section 3.2 and the SI transient-checks Text.
5. **display/D.md:7.** The Fig. 6 caption's "pale area" does not match the redrawn colours. Also, the lost 6 % / 227 m³/d result has no home in si/E, and si/B.md:15 dangles.
