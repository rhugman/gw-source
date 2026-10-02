# Case study: priority-well capture in the Neversink/Rondout model

Phase 5 case study, stage 1 (calibrated model only), 2026-10-02. Code: `studies/neversink/workflow.py` (study) and `studies/neversink/figures.py` (figures). Generated tables: `studies/neversink/output/*.csv`.

## Summary

- **Model and benchmark.** The study runs full-mixing backward tracing [FB13, BF13] on the USGS Neversink/Rondout MODFLOW 6 model (1.68 million cells, 50 m) from the eight priority wells (3,671 m³/d). It compares the result with the published MODPATH 7 areas contributing recharge to the same wells.
- **Counts.** The cell counts are close: the sum of F over the particle start cells is 910, against 980 contributing cells in the published runs. 96 % of the well water enters the model in cells where the published particles start.
- **Cell by cell, agreement is moderate.** The Jaccard index with the published cells is 0.30 for F > 0.1, 0.41 for F > 0.5 and 0.41 for the same number of cells ranked by F. Particle tracking on the same flow field gives 0.20 to 0.60 depending on release depth and weak-sink treatment. The published mask is one particle convention, not ground truth at cell level.
- **Streams.** With streams as cells, 43 % of the priority-well water is stream-reach leakage. With the 12,316 SFR reaches as nodes of the graph, all of it traces back to recharge. The contributing area then extends upstream along the streams, outside what a recharge-cell mask can show.
- **Cost.** The trace takes 2 to 3 s for nine destination groups; MODFLOW 6 takes 44 s.

## 1. Model, benchmark and method

**Model.** The model is the calibrated ("optimal", base-parameter) USGS Neversink/Rondout model [FIE21, COR22]. It is public domain (CC0), from `github.com/usgs/neversink_workflow` and the USGS data release doi 10.5066/P9HWSOHP.

- MODFLOW 6, steady state, NEWTON, DIS 4 layers × 680 rows × 619 columns of 50 m (1,683,680 cells).
- Packages: RCHA, CHD, WEL (34 entries with boundnames) and SFR (12,316 reaches, with its own budget file).
- The input is from 2021 (MF6 6.2). It was re-run here with MF6 6.9 (development build) after renaming the IMS keywords `OUTER_HCLOSE`/`INNER_HCLOSE` to `*_DVCLOSE` and dropping `OUTER_RCLOSEBND`. `SAVE_SPECIFIC_DISCHARGE` and `SAVE_SATURATION` were added to the NPF package for the particle check.

**Benchmark.** The published MODPATH 7 runs are forward runs with weak sinks stopping particles, in three regions (NE, S, W) around the well clusters. One particle starts at the centre of each cell of the uppermost active layer (122,021 particles). A cell counts as contributing if its particle ends in one of the eight priority wells (SV_193, SV_227, SV_407, SV_487, U_917, U__55, U___7, U___8). Their total pumping is 3,671 m³/d.

**Comparison.** Each particle start cell is given the backward fraction F of that cell, the share of its water that reaches the wells. The MODPATH mask and F > threshold are then compared cell by cell. PRT checks use the Phase 3 helper (`gwsource.track_particles`) on the same flow field, with porosity 0.3 as in the published MODPATH files. The cells hosting the wells form a stop zone. With `thin_weak_sinks=True` particles pass other weak sinks with their weight reduced by the full-mixing survival fraction; with `False` they pass unchanged, as in a plain particle run.

**Checks.**

| run | time (s) | max head difference to the published run (mm) |
|---|---|---|
| published solver settings | 44 | 8.6 |
| tight (OUTER_DVCLOSE 1e-4, INNER_DVCLOSE 1e-6) | 75 | 5.6 |

Both are below the model's own convergence criterion (0.01 m). The tight run is used only for the stream network (Section 4). The backward closure check (`gwsource.diagnostics.backward_closure`) is 1e-12 m³/d or smaller for every group, with streams as cells and as nodes.

## 2. Results: contributing cells

![Capture maps](figures/neversink_capture_maps.png)

*Figure 1. F of the uppermost active cell for the eight priority wells (blue), with the published MODPATH 7 contributing cells (outline) and the wells (dots). Top: streams as cells. Bottom: SFR reaches as nodes. Windows: the north SV wells, the southern SV well, the U cluster.*

**Table 1. Priority wells together, versus the published cells (980)**

| measure | cells | Jaccard index |
|---|---|---|
| F > 0 | 50,703 | 0.02 |
| F > 0.1 | 2,139 | 0.30 |
| F > 0.5 | 445 | 0.41 |
| 980 cells with the largest F (F ≥ 0.28) | 980 | 0.41 |
| sum of F over start cells | 910 | – |

Every published cell has F > 0. Their mean F is 0.42. Of the 445 cells with F > 0.5, 417 (94 %) are published cells, which are 43 % of the published area. The F > 0.1 zone has 2,139 cells, about twice the published area, and contains 711 of the 980 published cells (73 %). Only 5 published cells have F > 0.9.

**Source water in the published cells.** The published cells receive 4,278 m³/d of source water (recharge 2,297 and stream leakage 1,981 m³/d), 17 % more than the wells pump. Not all of it can reach the wells. This is consistent with the stopping rule of the published runs: a cell contributes if its particle ends in a priority well, and a particle stops at the first weak sink it meets. The well takes only part of its cell's outflow where the cell also passes water on, for example 44 % in the cell of U___7 and 69 % in the cell of SV_487 (85 to 100 % in the other six). Full mixing lets the rest continue downstream.

**Table 2. Per well**

| well | pumping (m³/d) | published cells | sum of F | Jaccard F > 0.1 | Jaccard F > 0.5 | Jaccard, same number of cells |
|---|---|---|---|---|---|---|
| SV_193 | 63 | 48 | 26 | 0.37 | 0.00 | 0.30 |
| SV_227 | 203 | 115 | 69 | 0.29 | 0.16 | 0.25 |
| SV_407 | 94 | 32 | 34 | 0.29 | 0.16 | 0.60 |
| SV_487 | 381 | 97 | 65 | 0.18 | 0.04 | 0.17 |
| U_917 | 1,054 | 351 | 313 | 0.56 | 0.53 | 0.68 |
| U__55 | 250 | 116 | 81 | 0.06 | 0.00 | 0.13 |
| U___7 | 516 | 58 | 94 | 0.20 | 0.00 | 0.05 |
| U___8 | 1,110 | 163 | 229 | 0.10 | 0.00 | 0.22 |
| all eight | 3,671 | 980 | 910 | 0.30 | 0.41 | 0.41 |

The wells of the U cluster share cells and capture areas, and a published cell belongs to the one well its particle reaches. A cell that sends water to several wells therefore scores for one of them in the benchmark, and for all of them under full mixing. Per-well agreement is correspondingly low, and the union of the wells is the fair comparison. The sum of F is above the published count for U___7 and U___8 and below it for the other wells.

**Coverage.** 96 % of the priority-well water (95 to 100 % per well) enters in the start cells of the published particles. Water entering elsewhere (deeper layers, outside the three regions) is invisible to the published runs; it is small here.

## 3. Results: particle tracking on the same flow field

**Table 3. Agreement with the published cells (Jaccard, priority wells)**

| method | Jaccard | cells expected | captured flow (m³/d) |
|---|---|---|---|
| full mixing, F > 0.5 | 0.41 | 910 (sum of F) | 3,671 |
| PRT, released at the water table, thinned, P > 0.5 | 0.37 | 562 | 1,940 |
| PRT, released at the water table, plain, P > 0.5 | 0.20 | 2,297 | 6,692 |
| PRT, released mid-cell, thinned, P > 0.5 | 0.60 | 750 | 3,005 |
| PRT, released mid-cell, plain, P > 0.5 | 0.29 | 2,610 | 8,237 |

P is the flow-weighted share of the particles released from a cell that arrive at the wells, evaluated at the published start cells (uppermost active layer). "Plain" means no weak-sink thinning. Particles were released from every source term (flux-weighted) of the 30,180 cells with F > 0 that have one, in all layers; one release sub-division per cell. Together these cells receive 90,349 m³/d. The captured flow is the PRT total, to be compared with the inflow of the wells, 3,671 m³/d.

- Plain particles over-count the wells' water by a factor of 1.8 to 2.2. They pass every weak sink other than the wells without losing weight, so water that streams and other sinks take on the way is counted as reaching the wells. Thinning corrects this.
- Thinned particles capture 53 % (water table) and 82 % (mid-cell) of the inflow. The shortfall was not investigated. The PRT helper drops the weight that remains in a well's cell when the well takes only part of its outflow (see the module docstring of `src/gwsource/prt.py`). That may contribute here, since the wells of U___7 and SV_487 take 44 % and 69 % of their cells' outflow.
- The mean absolute difference between F and P over the seeded cells is 0.03 for thinned particles and 0.08 for plain ones; the maximum is 0.84 to 1.00.
- Release depth and weak-sink treatment each move the Jaccard index by 0.1 to 0.3: depth by 0.23 (thinned) or 0.09 (plain), thinning by 0.17 (water table) or 0.31 (mid-cell). Mid-cell release with thinning matches the conventions of the benchmark (centre release, stopping at weak sinks) and agrees best (0.60). Water-table release is where recharge actually enters, and it agrees less (0.37).

Full mixing lies inside the range of particle results (0.20 to 0.60) that the same flow field yields under different conventions. The 0.41 for F > 0.5 should not be read as an error of full mixing alone.

## 4. Streams

With streams as cells, SFR cells are just cells that exchange water with the aquifer. Of the priority-well water, 2,100 m³/d (57 %) traces to recharge, and 1,571 m³/d (43 %) to SFR leakage. By well, SFR provides a large share of the water of SV_487 (51 %), U_917 (38 %), U___7 (63 %) and U___8 (57 %), and almost none of that of SV_193, SV_227 and SV_407.

With the SFR reaches as nodes of the graph (`package_nodes=("SFR",)` in `gwsource.read_network`), leakage is traced up the stream to where its water entered. All 3,671 m³/d then traces to recharge, none to the stream's external inflow or to CHD. This is consistent with stream leakage being groundwater that discharged upstream and re-infiltrates. The contributing area extends upstream along the streams. In Figure 1 (bottom), this is the pale area south-east of the U wells, with F of about 0.2, and the larger low-F area around the southern SV well. A mask built from recharge cells' particle ends does not contain it.

**Network reader tolerance.** `read_network` requires the GWF and SFR budgets to agree on the aquifer exchange of every reach to a tolerance of 1e-4 of the largest reach flow. With the published convergence criterion (0.01 m), 3 of the 12,316 reaches miss it (largest disagreement 1.9e-4 of the largest exchange, 869 m³/d). A tighter solve (OUTER_DVCLOSE 1e-4, INNER_DVCLOSE 1e-6, heads within 5.6 mm of the published run) meets it. `open_simulation` and `read_network` take an `aquifer_rtol` option for this; the difference then stays in the reaches' budget residuals, which the closure check includes. With `aquifer_rtol=5e-4` the published run reads directly and gives the same result (all 3,671 m³/d from recharge). Closure of the network trace is 1e-12 m³/d. The closure error that would remain if the cells' budget residuals were ignored falls from 4e-3 m³/d (streams as cells, published solve) to 1.5e-5 m³/d (network, tight solve) for the eight wells together.

**Cycles.** With streams as cells the flow graph has no cycles, so the solve is a single topological sweep. With reaches as nodes it has 8 small cycles of 4 to 130 nodes (reaches mixed with the cells they exchange water with), which the block solver handles exactly. The trace takes 2.6 s.

## 5. Interpretation and guidance

- **The published mask is a convention.** It uses one particle at each cell centre and stops at every weak sink. It is a valid delineation, but at the scale of single cells it is not a reference that full mixing, or any other method, should reproduce exactly. On the same flow field, particles span 0.20 to 0.60 agreement with it, depending on release depth and weak-sink treatment, and full mixing (0.30 to 0.41) is inside that range.
- **Thresholds.** `docs/dispersion_study.md` Section 5 recommends F = 0.5 for an advective zone and F ≥ 0.1 as a conservative envelope. Here, the F > 0.5 zone (445 cells) is a core that lies almost entirely inside the published area (980 cells) and covers 43 % of it. The F > 0.1 zone (2,139 cells) is about twice the size of the published area and still misses 27 % of its cells, so it was not a conservative envelope at cell level, unlike in the dispersion study (one well, analytical or particle reference zone). The published area sits between the two. That guidance was derived against references that do not stop at weak sinks, and this case does not test it in that sense.
- **State the conventions.** Release depth and weak-sink treatment both change the agreement with the published mask substantially (Section 3). A comparison with it should state where particles start and what stops them.
- **Streams.** With streams as cells, 43 % of the wells' water is attributed to stream leakage and the contributing area stops at the streams. Whether that is the intended reading depends on the question: it is correct for "which source package delivers the water", and incomplete for "where does the water come from".

## 6. Limitations and open points

- `baserat.zip` in the published Monte Carlo output contains 357 masks, against 358 realisations reported. The rebuilt ensemble (`studies/neversink/pest_rebuild.py`) explains it: masks 0 to 356 are positions 0 to 356 of the 358-row parameter table, and the last row, the base realisation, has no mask.
- 4,470 of the 122,021 MODPATH particles end with status 5. By the MODPATH 7 status convention this is a stop in a cell with no exit face; 514 of the 980 contributing particles are among them. This was not investigated.
- Only the calibrated (base-parameter) model has been run so far. The published probability raster is from 358 parameter realisations.
- The thinned PRT runs capture less water than enters the wells (Section 3), and the cause was not isolated.
- The comparison is on the uppermost active layer. Contributing areas in deeper layers are not compared.

## 7. Next stages

1. **Stage 2, ensemble.** 358 realisations at base pumping, compared with the published per-realisation masks and the probability raster (the share of realisations in which a cell contributes) using the `gwsource` ensemble driver. The PEST interface (`run_data/`, not archived on GitHub) has been rebuilt in `studies/neversink/pest_rebuild.py` without PEST++ or pyemu: the rebuilt base realisation equals the published calibrated input, and three realisations reproduce the stored iES heads to within 2 cm (median 0.3 mm), the same spread as the 2021 runs among themselves. A realisation costs about 40 to 65 s (input, MF6, trace).
2. **Stage 3.** The other five pumping scenarios. The scripts that built their parameter ensembles are not in the source repository, so the pumping scaling rule has to be inferred.

## Reproducing

```
python studies/neversink/workflow.py
```

The gates in `__main__` select the parts to run: the two MF6 runs, the MODPATH comparison, the PRT checks and the figures. The two MF6 runs take 44 s and 75 s. Each of the four PRT runs (122,112 particles) takes about 7 minutes and writes a track file of about 1.5 GB, which the workflow deletes after use. Output goes to `studies/neversink/output/`, which is not tracked by git. The USGS repository goes in `studies/neversink/external/neversink_workflow/` (also not tracked) as a sparse checkout:

```
git clone --filter=blob:none --sparse https://github.com/usgs/neversink_workflow.git studies/neversink/external/neversink_workflow
cd studies/neversink/external/neversink_workflow
git sparse-checkout set neversink_optimal output/neversink_mf6_optimal_output \
  output/neversink_mp7_optimal_output output/modpath_mc output/parallel scripts \
  notebooks_workflow_complete neversink_mf6 processed_data python_packages_static
```

## References

Black & Foley (2013) [BF13]; Foley & Black (2013) [FB13]; full entries in `references/bibliography.md`. Pollock (2016) [POL16] for MODPATH 7.

[COR22] Corson-Dosch, N.T., Fienen, M.N., Finkelstein, J.S., Leaf, A.T., White, J.T., Woda, J. & Williams, J.H. (2022). *Areas contributing recharge to priority wells in valley-fill aquifers in the Neversink River and Rondout Creek drainage basins, New York.* USGS Scientific Investigations Report 2021–5112, 50 p. https://doi.org/10.3133/sir20215112

[FIE21] Fienen, M.N., Corson-Dosch, N.T., White, J.T., Leaf, A.T. & Hunt, R.J. (2021). Risk-based wellhead protection decision support: a repeatable workflow approach. *Groundwater*. https://doi.org/10.1111/gwat.13129

Model, workflow and data: U.S. Geological Survey, `github.com/usgs/neversink_workflow` (public domain, CC0-1.0) and its data release, doi 10.5066/P9HWSOHP.
