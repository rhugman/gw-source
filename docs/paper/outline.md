# Paper outline: full-mixing flow-source fractions for MODFLOW 6

Draft outline, 2026-10-05. For co-author review. All numbers are from `docs/neversink_study.md` (cited as NS §n / Table n), `docs/dispersion_study.md` (DS §n / Table n), `PLAN.md` (status notes per phase) and the tests. Untracked outputs are in `studies/neversink/output/` and `studies/dispersion/output/` of the main checkout. Items marked [check] need verifying before submission.

## 1. Title and contribution

Working titles:

1. *Full-mixing capture and source fractions from MODFLOW 6 budgets: an open implementation and a comparison with particle-tracked contributing areas* (recommended)
2. *Capture fractions by full mixing and by particle tracking on a regional MODFLOW 6 model: what the differences are made of*
3. *Cell-mixing flow tracing for MODFLOW 6, with closure checks, stream networks and ensembles*

**Contribution.** The reference method [FB13, BF13] computes, from cell-by-cell flows, the fraction of the water in every cell that reaches a destination (backward) or came from a source (forward), assuming each cell is fully mixed. It is used for source protection zones in England [EA19] but is described only in conference papers, and no open implementation exists. We write the method as one sparse linear system per mode, solved exactly with or without flow cycles, with gross accounting so that weak sinks take only their share. Exact closure and duality identities verify every result. The implementation reads MODFLOW 6 budgets on structured and unstructured grids, multi-model simulations and stream, lake and well networks. On the USGS Neversink/Rondout model (1.68 million cells) we compare it with the published MODPATH 7 contributing areas for eight supply wells, for the calibrated model, a 358-realisation ensemble and five pumping scenarios. The cell-level differences are accounted for: MF6 PRT reproduces the published masks only with the published particle conventions, full mixing lies within the range of particle results on the same flow field, and the remaining differences come from mixing versus advective paths and from how streams are treated.

## 2. Target journals

| journal | fit | length [check] | |
|---|---|---|---|
| *Groundwater* (NGWA) | Audience of [FIE21], [BAR18], [POT08]; wellhead protection practitioners; the Neversink benchmark is a *Groundwater* workflow paper | research papers about 7,000–8,000 words incl. references [check]; supporting information unlimited | **recommended** |
| *Environmental Modelling & Software* | Method plus open software; [PAR11] (hydraulic mixing cells) published there; requires code availability | no strict word limit for research papers [check] | second choice, if the paper stays software-heavy |
| *Water Resources Research* (Technical Report: Methods) | Theory (linear system, adjoint identities) and the particle/mixing comparison | 25 publication units [check] | higher bar on novelty; the method itself is from 2013 |

Recommendation: *Groundwater*, with verification details, the PRT diagnosis and Tables 6–7 of NS moved to supporting information. Alternative: split into a method/software paper (EMS) and a Neversink comparison paper (*Groundwater*); decide after the first full draft.

## 3. Key messages

1. **The reference method is a linear system.** Backward fractions solve (I − P) F = S D on the out-normalised flow matrix, forward fractions the in-normalised analogue. The reference method's topological sweep is the acyclic special case; its net accounting is kept as an option and reproduces the [FB13] worked example exactly. Gross accounting gives a weak-sink well only its share: net accounting attributes 6.7 times the pumping to a weak-sink well in tutorial 02. (`src/gwsource/assemble.py`, `solve.py`; `tests/test_fb13_example.py`; `tests/test_mf6_integration.py::test_weak_sink_gross_vs_net`; `tutorials/02_accounting`.)
2. **Every result carries its own check.** Backward closure, forward closure and forward/backward duality are exact identities that include the cell budget residuals. They hold to round-off on the synthetic test models (1–9) and to 1e-12 m³/d on the 1.68-million-cell Neversink model; transient tracking matches MF6 GWT to ≤ 1e-14. (`src/gwsource/diagnostics.py`; `tests/test_closure_duality.py`, `tests/test_tracking_mf6.py`; NS §1 Checks; PLAN Phase 4B notes.)
3. **It is cheap enough for ensembles.** On Neversink the trace takes 2 to 3 s for nine destination groups against 44 s for MODFLOW 6; 358 realisations with two traces each took 76 min on six processes. (NS Summary, §6.)
4. **A published particle mask is one convention, not ground truth at cell level.** On the same flow field, flux-weighted particles agree with the published MODPATH 7 mask at Jaccard 0.29 to 0.62 depending on weak-sink treatment and release depth; full mixing (0.30 to 0.41) lies inside that range. PRT reproduces the mask (Jaccard 0.998) only with the published conventions (top-face recharge and stream flows where the top is open, stopping at every weak sink, dry start cells draped). Both full mixing and thinned particles close on the wells' inflow (exactly, and within 2 %). (NS §2–3, Tables 1, 3; `mp7_reproduction.csv`.)
5. **Across an ensemble and pumping scenarios full mixing tracks the published areas.** Mean F correlates with the published probability of contribution at 0.80 and gives 90 % of its expected area. The median area is within 10 % of the published median from base to maximum pumping (911 vs 998 cells; 3,725 vs 3,592). The full-mixing area grows faster than pumping (4.09 vs 3.68 times) because the stream share of the wells' water falls (42 % to 28 %); the published area grows more slowly (3.60) mainly because particles stop at buried stream cells, which PRT with the published conventions reproduces (3.62). (NS §6–7, Tables 4–6.)
6. **How streams are represented changes the answer.** With streams as cells, 43 % of the wells' water is stream leakage and the contributing area stops at the streams. With the 12,316 SFR reaches as graph nodes, all of it traces to recharge and the median area is 1.7 times larger at base pumping and 1.4 times at maximum pumping (1,534 vs 911 and 5,247 vs 3,725 cells); the ensemble mean F gives 1.51 times the published expected area. (NS §4, Tables 4–5.)

## 4. Draft abstract (about 250 words)

Full-mixing flow tracing computes, from the cell-by-cell flows of a groundwater model, the fraction of the water in each cell that reaches a destination or came from a source. It is used for source protection zones but is described only in conference papers and has no open implementation. We write it as a sparse linear system, solved exactly with or without flow cycles, with gross accounting of weak sinks and exact closure and duality checks, and implement it for MODFLOW 6 grids, multi-model simulations and stream, lake and well networks. On synthetic models the checks hold to round-off and transient tracking matches MODFLOW 6 transport to 1e-14. On the USGS Neversink/Rondout model (1.68 million cells) a trace takes 2–3 s. Against the published MODPATH 7 areas contributing recharge to eight supply wells, cell-by-cell agreement is moderate (Jaccard index 0.30–0.41), but particle tracking on the same flow field spans 0.29–0.62 depending on how particles are released and stopped. MODFLOW 6 particle tracking reproduces the published areas (Jaccard 0.998) only when it copies their conventions, chiefly stopping at every weak sink. Over 358 realisations and five pumping scenarios the median full-mixing area is within 10 % of the published median. It grows faster than pumping because the stream share of the wells' water falls from 42 % to 28 %; the published areas grow more slowly mainly because particles stop at buried stream cells. Tracing through the stream network attributes all well water to recharge and enlarges the contributing area 1.4 to 1.7 times. Particle conventions and stream treatment should be stated with any delineation.

(About 250 words.)

## 5. Section outline

### 5.1 Introduction

- Contributing areas and capture zones: particle tracking [POL88, POL16] is standard; weak sinks, transient flow and many destinations are awkward for it [EA19, BF13]. Evidence: `references/SUMMARY.md` §4.
- Terminology: capture fraction in the budget sense [LEA10, BAR18] is a different quantity; state this early. Evidence: `references/bibliography.md` §D.
- Flux-based alternatives: MODALL [POT08] and its critique [MC09], the reference method [FB13, BF13], hydraulic mixing cells [PAR11], unit-concentration transport [BED24], particle source apportionment [PRY22], adjoint and age methods [NW99, GOO96, CP06]. Evidence: `references/SUMMARY.md` §5.
- Gaps: no peer-reviewed description of the reference method, no open code, cycles handled by deleting edges, net accounting of weak sinks, no published comparison with particle masks on a large real model. Evidence: `references/bibliography.md` §F; PLAN §1 table.
- Aims, as three questions: (i) exact and checkable formulation; (ii) cost on a regional model and ensemble; (iii) what the differences from a published particle delineation consist of.

### 5.2 Method

- **Graph and accounting.** Cells as nodes, FLOW-JA-FACE as edges, every budget term kept as its own source or sink term; outflow O, inflow I, residual r reported and never forced to zero. Evidence: PLAN §2.1; `assemble.py` docstring.
- **Backward and forward systems.** (I − P) F = S D; (I − Q) G = R T; derived volumes through/from/to, split by package; boundary-control maps (rows sum to 1). Evidence: PLAN §2.2–2.3; `metrics.py` docstring; `tests/test_closure_duality.py::test_steady_boundary_control`.
- **Net mode and the reference method.** Destination cells absorbing, net source per cell; reproduces [FB13] Figs 5–8; weak-sink over-attribution. Evidence: PLAN §2.4; `tests/test_fb13_example.py`; tutorial 02.
- **Solution.** Topological substitution when acyclic; block-triangular LU over strongly connected components otherwise; closed recirculation loops isolated; M-matrix, no pivoting. Evidence: `solve.py` docstring; PLAN Phase 2 notes; `tests/test_mf6_integration.py::test_xt3d_cycles_detected_and_solved_by_block_lu`.
- **Diagnostics.** Closure Σ F Src − Σ F r = destination inflow; forward closure; duality Σ_S F q − Σ_D G |q| = Σ F G r. Evidence: `diagnostics.py` docstring.
- **Travel time.** Eulerian mean time (I − P) m = τ ∘ F reusing the factorisation; identity ΣVF/Q. Evidence: PLAN §2.6 and Phase 3 notes; `traveltime.py`.
- **Transient (brief).** Snapshots with streaming statistics; true transient forward tracking and its adjoint through storage. Keep to one paragraph, or leave for a later paper (see §7). Evidence: PLAN Phase 2 and 4B notes; `tracking.py`.

### 5.3 Implementation

- MF6 reader: binary grid IA/JA in user numbering for DIS/DISV/DISU, list and array budget records, MVR double records. Evidence: `mf6io.py` docstring; PLAN Phase 1–2 notes.
- Package networks: SFR/LAK/MAW/UZF nodes from the package budget files, MVR edges, aquifer-exchange tolerance check (`aquifer_rtol`). Multi-model GWF-GWF exchanges. Evidence: `network.py`, `packages.py`; PLAN Phase 4A notes.
- Selectors, exports (npz, netCDF, GeoPackage), ensemble driver. Evidence: `selectors.py`, `export.py`, `ensemble.py`.
- PRT comparison helper: flux-weighted release per source term, IFLOWFACE-aware, gross accounting along each path (thinning). Evidence: `prt.py`; PLAN Phase 3 PRT revision and IFLOWFACE notes.
- Performance: 1M-cell synthetic grid, topological solve 0.55 s, block solve with 7,000 cycles 0.42 s; memory about 90 MB per group per million cells. Evidence: PLAN Phase 2 notes; `benchmarks/`.

### 5.4 Verification on synthetic models

- [FB13] worked example, net mode: exact. Evidence: `tests/test_fb13_example.py`.
- Closure, duality and boundary control to 1e-10 relative (observed round-off): models 1–5 and transient steps of model 6 (`tests/test_closure_duality.py`), package-network models 7–9 (`tests/test_package_network.py`, `tests/test_mover.py`). Evidence also PLAN Phase 1 "Done when", Phase 4A notes.
- Grid independence of the code: DIS = DISU to machine precision; split simulations equal the single model to ≤ 7e-10. Evidence: `tests/test_mf6_integration.py::test_dis_and_disu_identical`; `tests/test_multimodel.py`; PLAN Phase 4A.
- Transient tracking vs MF6 GWT: ≤ 2e-15 (model 6), ≤ 1e-14 (model 7 with SFT and MVT). Evidence: `tests/test_tracking_mf6.py`; PLAN Phase 4B.
- Particles: Eulerian vs PRT mean arrival 9574 vs 9590 d (model 1); captured particle flow 800.4 of 800 m³/d; 3-layer model 402.6 of 405 m³/d. Evidence: `tests/test_prt.py`; PLAN Phase 3.
- Numerical dispersion against Javandel–Tsang and PRT references: edge band narrows as about h^0.5; F = 0.5 area within 5 % for h ≤ 50 m; F ≥ 0.1 always contains the reference zone but is 8–90 % too large; source shares identical to three digits. Evidence: DS Summary, Tables 1–2, §5.

### 5.5 Neversink case study

**Model and benchmark.**
- USGS Neversink/Rondout MF6 model [FIE21, COR22]: 4 × 680 × 619 cells of 50 m, NEWTON, RCHA/CHD/WEL/SFR (12,316 reaches); rerun with MF6 6.9, heads within 8.6 mm. Evidence: NS §1.
- Benchmark: published MODPATH 7 forward runs, one particle per uppermost active cell (122,021), weak sinks stop particles; 980 cells contributing to eight priority wells (3,671 m³/d). Evidence: NS §1.

**Calibrated model vs published masks.**
- Jaccard 0.30 (F > 0.1), 0.41 (F > 0.5 and area-matched); sum of F 910 vs 980 cells; 96 % of the well water enters in published start cells. Evidence: NS §2, Table 1; `output/agreement_with_mp7.csv`, `mp7_coverage.csv`.
- F > 0.5 is a core (94 % inside the published area, covering 43 % of it); F > 0.1 is twice the area and misses 27 %. Evidence: NS §2, §5.
- Per-well agreement is low because the U-cluster wells share capture areas and a particle scores for one well only. Evidence: NS Table 2.
- End states of the published particles: buried stream cells stop particles as weak sinks, open-top ones let them leave. SI. Evidence: NS §2; `output/mp7_status.csv`.

**Particle tracking on the same flow field.**
- Thinned PRT captures 3,736 of 3,671 m³/d (+1.8 %, quadrature, 0.0 to +1.8 % over five layouts); plain particles over-count 2.6 times. Evidence: NS §3, Table 3; `output/prt_comparison.csv`.
- Why the first PRT runs under-captured (53 % and 82 %): weight dropped in partial well cells (+720 m³/d) and particles trapped at the water table (−1,300 m³/d at the water table vs mid-cell); both defects of the helper, not of either method. Evidence: NS §3 table "first well cell only vs weight followed on"; `output/prt_diagnosis.csv`; `tests/test_prt.py::test_capture_along_paths_follows_weight_past_partial_sinks`.
- Source split differs by method (stream 43 % vs 51 %), from reaches 0.4–1.3 km from the wells. Evidence: NS §3; `output/prt_sources_by_well.csv`.
- Reproducing the published mask: top-face IFLOWFACE where the top is open, drape dry starts, stop at weak sinks: 99.0 % same end cell, Jaccard 0.998; MF6 default conventions 0.62–0.65. Evidence: NS §3 table; `output/mp7_reproduction.csv`.

**Streams.**
- Streams as cells: 57 % recharge, 43 % stream leakage. SFR reaches as nodes: 100 % recharge; area extends upstream along streams; 8 small cycles handled exactly; trace 2.6 s. Evidence: NS §4; `output/sources_cells.csv`, `sources_sfr_network.csv`, `checks_sfr_network.csv`.

**Ensemble at base pumping.**
- Rebuilt PEST interface; 358 realisations; closure ≤ 3e-12 m³/d in each; stream share 30–45 %. Evidence: NS §6.
- Published masks lie one row south and follow a text-sorted run order; corrected, PRT with the published conventions matches each realisation's own mask (median Jaccard 0.996). Evidence: NS §6; `studies/neversink/mc_masks.py`; `output/scenarios/mechanisms60/mask_matches.csv`.
- Mean F vs published probability: r = 0.80, sum ratio 0.90, Jaccard 0.48 for zones > 0.5; stream network 1.51 times the area. Evidence: NS Table 4; `output/ensemble/probability_comparison.csv`.
- In the S region the published area varies by 32 % between realisations, follows PRT (r = 0.997) but not the sum of F (r = 0.00). Evidence: NS §6.

**Pumping scenarios and growth mechanisms.**
- Scenario rule inferred from the masks (log rms 0.05), well multipliers kept. Evidence: NS §7; `scenarios.py`.
- Median areas within 10 % of published across five rates. Evidence: NS Table 5; `output/scenarios/area_table.csv`.
- Growth 4.09 vs pumping 3.68: stream share falls 42 % → 28 %; recharge captured grows 4.57 times; r = 0.94 across realisations. Evidence: NS §7; `output/scenarios/source_table.csv`.
- Where the stream water changes: 72 % of the increase is a larger captured share of reaches already losing; 18 % from reaches switching to losing; most of the extra pumping is recharge that discharged to streams at base. Evidence: NS §7; `output/scenarios/mechanisms60/growth_decomposition.csv`, `stream_by_state.csv`, `stream_by_distance.csv`.
- Why the published area grows more slowly: one convention at a time (Table 6); stopping at buried stream weak sinks takes growth from 4.76 to 3.83. Evidence: NS Table 6; `mechanisms60/stream_stops.csv`.
- Why thinned particles grow faster than full mixing: a 10 % shortfall at base from partly captured reaches near the U wells, gone at higher pumping. Supporting information. Evidence: NS §7, Table 7; `output/scenarios/advective_growth/`.

### 5.6 Discussion

- **Full mixing or particles.** Same water totals, different paths. Full mixing gives exact budgets, weak-sink shares and many destinations in seconds; particles give advective paths and first arrival. Use F = 0.5 for an advective core and particles where zones are small [EA19]. Evidence: DS §5; NS §3, §5.
- **Conventions matter more than method.** Release depth (2,413 vs 3,736 m³/d), thinning (Jaccard 0.29 vs 0.62) and face assignment (0.65 vs 0.998) each move the result more than the switch from particles to full mixing. A delineation should state release position, stopping rule and face convention. Evidence: NS Table 3, §3 reproduction table, §5.
- **Thresholds.** The F ≥ 0.1 envelope was conservative against non-stopping references (DS) but not against a stopping-particle mask at cell level (NS §5). Present this as untested in the second sense (see §7).
- **Streams.** Streams as cells answers "which package delivers the water"; as a network it answers "where did the water enter". Pumping growth is controlled by the stream share either way. Evidence: NS §4–5, §7.
- **Ensembles.** Realisation-to-realisation variation of a particle mask can come from the particle conventions rather than from capture (S region). Evidence: NS §6.
- **Reproducibility of published benchmarks.** Two bookkeeping offsets in the published Monte Carlo masks had to be inferred; archive the steps that write masks. Brief, neutral. Evidence: NS §6, §8.

### 5.7 Limitations

- Full mixing is grid-dependent (band ~h^0.5); face routing removes 35–70 % of the excess but is 2D and experimental. Evidence: DS §4, §6.
- Steady and snapshot results have no travel lag; transient tracking is advective, upstream, implicit. Evidence: PLAN §2.7; DS §3.
- Neversink comparison is on the uppermost active layer only; the scenario rule and mask pairing are inferred; maxrange reproduced in distribution only. Evidence: NS §8.
- Some mechanism statements are inferred, not traced cell by cell (leakage staying on flow lines; narrow paths in Fig. 2). Evidence: NS §6, §7, §8.
- MF6 PRT aborts in film-wet cells (one start left out); reproducer prepared, not yet reported upstream. Evidence: NS §8; `studies/neversink/prt_film_repro/`.
- PRT supports DIS and DISV only; DISU has Eulerian times only. Evidence: PLAN §2.8.

### 5.8 Conclusions

- Four or five sentences mirroring the key messages.

### 5.9 Code and data availability

- `gwsource` (MIT) on GitHub, with tests, tutorials and the study scripts (`studies/neversink/`, `studies/dispersion/`); archive a release on Zenodo with a DOI [check].
- Neversink model and MODPATH outputs: USGS, `github.com/usgs/neversink_workflow` (CC0) and data release doi 10.5066/P9HWSOHP.
- Software versions: MF6 6.9 development build and FloPy `develop` [check: pin to released versions before submission, PLAN D3].
- Generated tables in `studies/neversink/output/` are not tracked; deposit the CSVs behind every table and figure with the release.

## 6. Figures and tables

| # | content | status | source |
|---|---|---|---|
| Fig. 1 | Schematic: a cell with intercell edges and source/sink terms; backward and forward systems; gross vs net on a weak-sink cell | made | `docs/paper/figures/fig1_method_schematic.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 2 | Verification summary: closure and duality errors over test models; GWT agreement; DIS/DISU/split agreement | made | `docs/paper/figures/fig2_verification.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 3 | Numerical dispersion: band width and area error against cell size | made | `docs/paper/figures/fig3_numerical_dispersion.png` / `.pdf`; code `studies/paper/method_figures.py` |
| Fig. 4 | Neversink model, wells, regions and published contributing cells (location map) | made | `docs/paper/figures/fig4_location_map.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 5 | F with published cells; streams as cells and as network | made | `docs/paper/figures/fig5_capture_maps.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 6 | Jaccard with the published mask by method and convention (full mixing thresholds; PRT plain/thinned, release depth; PRT MF6 default to published conventions) | made | `docs/paper/figures/fig6_agreement.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 7 | Published probability vs ensemble mean F (cells, network) | made | `docs/paper/figures/fig7_probability_maps.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 8 | Area growth against pumping: published, full mixing, network, PRT with published conventions | made | `docs/paper/figures/fig8_area_growth.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Fig. 9 | Growth mechanism: stream share vs pumping, and area-growth excess vs stream-share drop across realisations (r = 0.94) | made | `docs/paper/figures/fig9_growth_mechanism.png` / `.pdf`; code `studies/paper/neversink_figures.py` |
| Table 1 | Comparison of the reference method and this formulation (solve, accounting, cycles, outputs) | to adapt | PLAN §1 table |
| Table 2 | Verification checks with tolerance and observed error | made | `docs/paper/figures/verification_table.md` / `.csv`; code `studies/paper/verification.py` |
| Table 3 | Calibrated model vs published cells (counts, Jaccard) | exists | NS Table 1 |
| Table 4 | Particle tracking variants: Jaccard, expected cells, captured flow | exists | NS Table 3 plus reproduction table |
| Table 5 | Ensemble comparison | exists | NS Table 4 |
| Table 6 | Median areas by scenario | exists | NS Table 5 |
| Table 7 | One convention at a time: areas at base and maximum pumping | exists | NS Table 6 |
| SI | Per-well table (NS Table 2); end states; PRT diagnosis; Table 7 of NS; dispersion maps and transient sub-steps (DS Figs 1, 3, 5) | exist | NS, DS |

## 7. Claims–evidence gaps (priority order)

1. **Quadrature analysis scripts are missing.** NS §3 says the five-layout analysis of the +1.8 % excess "was a one-off analysis; its scripts are not in the repository". Add them (or drop the claim) before the paper cites it.
2. **Threshold guidance on Neversink against a non-stopping reference.** The paper wants to say whether F ≥ 0.1 is a conservative envelope on a real model. Compute coverage of the thinned-PRT P > 0.5 zone by F ≥ 0.1 and F ≥ 0.5 from existing PRT outputs (no new runs; `prt_volume_thin1`).
3. **Gross vs net on Neversink.** Key message 1 rests on a tutorial example. Run net mode on the calibrated model and report the over-attribution at the partial-capture wells (U___7 takes 44 % of its cell's outflow, SV_487 69 %). One trace, seconds.
4. **Verification table and figure.** Done: `studies/paper/verification.py` collects the checks over test models 1–9 (Table 2, Fig. 2); all pass, the largest round-off error is 1.5e-15.
5. **Travel time on Neversink.** The published MODPATH runs have travel times and PRT agrees with them within 1 % (NS §3), but Eulerian mean times were not compared. Needed only if the paper keeps travel time in scope.
6. **Inferred mechanisms.** Leakage staying on flow lines to the wells (NS §7) and the narrow-path reading of Fig. 7 (NS §6) are inferred. Either trace one reach cell by cell or word them as interpretation.
7. **Transient scope.** No real-model transient application. Either limit the paper to steady state and ensembles (recommended) or add one.
8. **References missing from `references/bibliography.md`:** MF6 PRT documentation, FloPy, PEST++/iES, Javandel & Tsang (1986) (cited only inline in DS), Mf6Splitter. Add before drafting.
9. **Report the PRT film-cell abort upstream** (NS §8) so the paper can cite the issue.

## 8. Reference skeleton

Keys as in `references/bibliography.md`, which holds the full entries. The titles of [FB13], [BF13] and [BFW21] contain the product name, which this repository's naming test forbids, so they are not repeated here.

- **Reference method:** [FB13] Foley & Black 2013 and [BF13] Black & Foley 2013 (MODFLOW and More 2013 proceedings; page ranges from secondary citations [check]); [BFW21] Black, Foley & Witterick 2021 (slides; cite only for the later fraction-from definition); [EA19] Environment Agency 2019 (SPZ manual); [MAU21] Maurice et al. 2021; [CHO16] Chowdhury 2016 (thesis; face routing).
- **Related flux-based and transport methods:** [POT08] Potter et al. 2008 (MODALL); [MC09] McLane & Cecan 2009; [PAR11] Partington et al. 2011; [BED24] Bedekar et al. 2024; [PRY22] Pryet et al. 2022; [NW99] Neupauer & Wilson 1999; [GOO96] Goode 1996; [CP06] Cornaton & Perrochet 2006; [FRI02] Frind et al. 2002.
- **Capture terminology:** [BAR18] Barlow, Leake & Fienen 2018; [LEA10] Leake, Reeves & Dickinson 2010.
- **Particle tracking and MODFLOW 6:** [POL88] Pollock 1988; [POL16] Pollock 2016 (MODPATH 7); [LAN17] Langevin et al. 2017 (GWF); [LAN22] Langevin et al. 2022 (GWT); [MF6IO] input/output guide. Not yet in the bibliography [check]: MF6 PRT documentation; FloPy (Bakker et al. 2016; Hughes et al. 2024).
- **Case study:** [COR22] Corson-Dosch et al. 2022; [FIE21] Fienen et al. 2021; USGS data release doi 10.5066/P9HWSOHP. Not yet in the bibliography [check]: PEST++ iES (White et al. 2020).
- **Synthetic reference:** Javandel & Tsang 1986, Ground Water 24(5) (cited inline in DS only; add to the bibliography).
