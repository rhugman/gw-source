# Paper figures 4 to 9: Neversink case study

Made by `studies/paper/neversink_figures.py` (`main()`, one gate per figure, output folder `fig_dir`, default this folder). Each figure is saved as PNG (300 dpi) and PDF. They are sized for *Groundwater*: single column 3.5 in (89 mm), double column 7 in (178 mm), fonts 7 to 8 pt. Run time is about 3 s, because every figure is drawn from existing outputs and nothing is rerun:

```
PYTHONPATH=src python studies/paper/neversink_figures.py
```

The inputs are in `studies/neversink/output/` and `studies/neversink/external/neversink_workflow/`, both git-ignored. Before plotting, the module asserts that every number quoted below rounds to the value in `docs/neversink_study.md` (NS). Colours: published contributing cells in ink, full mixing with streams as cells in blue, PRT in orange, the stream network in aqua and pumping in grey (dashed). These are the first slots of the validated default palette. Every series also has its own marker or line style. Map conventions follow `studies/neversink/figures.py`.

Cluster names follow `growth_mechanisms.CLUSTERS`: U = U_917, U__55, U___7 and U___8; SV_W = SV_193, SV_227 and SV_407 (the "north SV wells" of NS Fig. 1); SV_S = SV_487.

## Fig. 4: location map (single column)

`fig4_location_map.{png,pdf}`

Sources: `output/optimal/neversink.dis.grb` (IDOMAIN); `output/optimal/neversink_packagedata.dat` and `neversink.sfr` (reach cells and downstream connections); the published MODPATH 7 endpoint files `external/neversink_workflow/output/neversink_mp7_optimal_output/*.mpend` (start cells by region); `output/mp7_priority.npz` (published contributing cells); `workflow.PRIORITY_WELLS`.

> **Figure 4.** The Neversink/Rondout model [FIE21, COR22]. Shown are the active model area (grey), the 12,316 SFR reaches (blue lines from each reach to its downstream reach), the three regions of the published MODPATH 7 runs (dashed; the start cells of their 122,021 particles), and the 980 cells that contribute recharge to the eight priority wells in the published calibrated-model run (black). Wells are grouped into the U cluster (4 wells), SV_W (3) and SV_S (1). Coordinates are km from the grid origin (x = 1,742,955 m, y = 2,258,285 m, EPSG:5070). The grid is not rotated, and true north (arrow) is 12.9° west of grid north.

Notes: four connections longer than 250 m (routing between distant reaches) are not drawn. The four U wells lie within about 1 km of each other, and their markers overlap at this scale.

## Fig. 5: F with the published cells, streams as cells and as a stream network (double column)

`fig5_capture_maps.{png,pdf}`. A paper-size version of `docs/figures/neversink_capture_maps.png` (NS Fig. 1), with the same data and windows widened to one aspect ratio so that the panels tile.

Sources: `output/fractions_cells.npz`, `output/fractions_sfr_network.npz` (group `priority`), `output/mp7_priority.npz`.

> **Figure 5.** Backward fraction F of the uppermost active cell for the eight priority wells (blue, 0 to 1), calibrated model, around the three well clusters. The published MODPATH 7 contributing cells are outlined and the wells are dots. (a–c) Streams as cells, with stream leakage as a source term of the aquifer cell: 43 % of the wells' water is stream leakage. (d–f) Stream network, with the SFR reaches as extra cells linked by stream routing: all of it traces to recharge, and the contributing area extends upstream along the streams (pale area south-east of the U wells, F ≈ 0.2). Sum of F over the published start cells: 910, against 980 published cells. Overlap with the published cells (cells in both as a share of cells in either): 0.30 (F > 0.1) and 0.41 (F > 0.5). Coordinates in km from the grid origin.

## Fig. 6: overlap with the published cells by method and convention (single column)

`fig6_agreement.{png,pdf}`

Sources: `output/agreement_with_mp7.csv` (full mixing), `output/prt_comparison.csv` (column `jaccard_mp7_prt>0.5`), `output/mp7_reproduction.csv` (column `jaccard`; the duplicate `mp7_conventions_published_flows` run, also 0.998, is not shown).

> **Figure 6.** Overlap between the 980 published contributing cells and other delineations of the eight priority wells' area on the same flow field, as the cells in both as a share of the cells in either. *Full mixing*: F > 0.1 (0.30), F > 0.5 (0.41), and the 980 cells with the largest F (0.41). *PRT, flux-weighted*: particles released from every source term in proportion to its flow, counted where the flow-weighted share P reaching the wells is above 0.5. Weight-losing particles, which lose weight at every sink in proportion to the flow it takes, give 0.62 when released over the cell volume or at mid-cell and 0.39 at the water table. Plain particles, which pass weak sinks without losing weight, give 0.29. *PRT, published starts*: one particle per published start, stopping at weak sinks. With MF6's default distributed boundary flows the overlap is 0.62 (dry starts dropped to the water table) or 0.65 (draped, i.e. moved down to the first active cell below). With recharge and stream flows on the top face where it is open (IFLOWFACE) it is 0.96 (dry starts dropped) or 0.998 (draped; the published conventions).

Values checked against NS Table 1, Table 3 and the Section 3 reproduction table. All match.

## Fig. 7: published probability against ensemble mean F (double column)

`fig7_probability_maps.{png,pdf}`. A paper-size version of `docs/figures/neversink_probability_maps.png` (NS Fig. 2), from the same file, which was regenerated with the corrected published Monte Carlo areas.

Source: `output/ensemble/probability_maps.npz` (`mp7`, `cells:mean_F`, `network:mean_F`).

> **Figure 7.** Base pumping. (a–c) Published probability of contribution (357 published Monte Carlo contributing areas, moved one row north onto their cells). (d–f) Ensemble mean F with streams as cells and (g–i) with the stream network (358 realisations). Outline: published probability 0.5. Mean F correlates with the published probability at r = 0.80 and gives 90 % of its expected area. The zones above 0.5 have an overlap (cells in both as a share of cells in either) of 0.48. With the stream network the values are r = 0.72, an area ratio of 1.51 and an overlap of 0.49 (NS Table 4).

## Fig. 8: area growth against pumping (single column)

`fig8_area_growth.{png,pdf}`. An extension of `docs/figures/neversink_area_growth.png` (NS Fig. 3) with the PRT curve.

Sources: `output/scenarios/area_table.csv` (published, full mixing as cells and as a network, pumping); `output/scenarios/mechanisms60/growth_decomposition.csv` (variant `r1`, `growth_of_medians`, baserat, 0.5rat and maxrat).

> **Figure 8.** Median contributing area of the eight priority wells relative to base pumping, for pumping fractions f = 0 to 1, where q = m (q_base + f (q_max − q_base)). At maximum pumping, the full-mixing area with streams as cells grows 4.09 times while pumping grows 3.68 times (dashed). The published area grows 3.60 times and PRT with the published conventions 3.62 times (61 realisations, base, half and maximum pumping). Full mixing with the stream network grows 3.42 times. The areas are the median sum of F over the start cells (358 realisations at base, 357 otherwise), the median number of published contributing cells (357 Monte Carlo areas), or the median number of PRT-captured start cells. Each curve is the median area of the scenario divided by the median at base.

Values checked against NS Tables 5 and 6 and Section 7. All match.

## Fig. 9: growth mechanism (double column)

`fig9_growth_mechanism.{png,pdf}`

Sources: per-realisation summaries `output/ensemble/summary/*.json` (base, 358) and `output/scenarios/<qrat>/summary/*.json` (357 each). Stream share = `cells:SFR_0` / `inflow` per realisation, as in `ensemble_run.source_table` (`output/scenarios/source_table.csv` holds its median, minimum and maximum, not quantiles). Area = `cells:expected_cells`.

> **Figure 9.** Why the full-mixing area grows faster than pumping (streams as cells). (a) Stream leakage as a share of the priority wells' water: the median over realisations is 42 % at base pumping and 28 % at maximum pumping, with a band from the 5th to the 95th percentile (base 36 to 44 %, maximum 25 to 31 %). (b) For each of the 357 realisations with a published Monte Carlo area, the area growth minus the pumping growth (base to maximum pumping) is plotted against the drop in stream share. The two are correlated at r = 0.94 (line: least squares, slope 0.063 per percentage point). The median drop is 13.7 percentage points and the median excess 0.39.

r = 0.94 reproduced. This is a Pearson correlation of the difference (area growth − pumping growth) with the drop in share (base − maximum) over the 357 paired realisations: r = 0.943 (0.942 for the ratio of the growths). The medians of 42 % and 28 % match NS Section 7.

## Not changed

`docs/figures/neversink_*.png` (the NS figures) are left as they are.
