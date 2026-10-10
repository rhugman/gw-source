## Figure 5

**Figure 5.** The Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022): active model area (grey), the 12,316 SFR reaches (blue, each reach joined to its downstream reach), the three regions of the published MODPATH 7 runs (dashed), whose 122,021 particles start in the uppermost active cells, and the 980 published contributing cells of the eight priority wells, calibrated model (black). The wells form the U cluster (4 wells), SV_W (3) and SV_S (1); the U wells lie within about 1 km of each other. Coordinates are km from the grid origin (x = 1,742,955 m, y = 2,258,285 m, EPSG:5070); true north is 12.9° west of grid north. <!-- figures/README.md Fig. 5; NS §1 -->

## Figure 6

**Figure 6.** Backward fraction F (0 to 1) of the uppermost active cell for the eight priority wells, calibrated model, around the three well clusters, with the published contributing cells outlined and the wells as dots. (a–c) Streams as cells: stream leakage is a source term of the aquifer cell and supplies 43 % of the wells' water. (d–f) Stream network: the SFR reaches are extra cells linked by stream routing, all the water traces to recharge, and the area extends upstream along the streams (pale area south-east of the U wells, F ≈ 0.2). With streams as cells, the sum of F over the start cells is 910, against 980 published cells, and the overlap with them (cells in both as a share of cells in either) is 0.30 for F > 0.1 and 0.41 for F > 0.5. Coordinates in km from the grid origin. <!-- figures/README.md Fig. 6; NS §2, §4, Table 1 -->

## Figure 7

**Figure 7.** Overlap (cells in both as a share of cells in either) between the 980 published contributing cells and other delineations of the eight priority wells' area on the same flow field. Full mixing: F > 0.1, F > 0.5 and the 980 cells with the largest F (area-matched), with gross accounting (filled) and net accounting (open), which fixes F = 1 in the well cells. PRT, flow-weighted: particles released from the source terms of the 30,180 cells with F > 10⁻⁶, counted where the particle share P reaching the wells exceeds 0.5; weight-losing particles lose weight at every sink in proportion to the flow it takes from the cell's outflow, and plain particles lose weight only to the wells. PRT, published starts: one particle per published start, stopped at every weak sink, with MODFLOW 6's distributed boundary flows (MF6 default) or with recharge and stream flows on the top face where it is open, and with or without draping of dry starts to the first active cell below; the published conventions use both. <!-- figures/README.md Fig. 7; NS Tables 1, 2b, 3, §3 reproduction table; agreement_with_mp7.csv, net_vs_gross_mp7.csv, prt_comparison.csv, mp7_reproduction.csv -->

## Figure 8

**Figure 8.** Base pumping. (a–c) Published probability of contribution, from the 357 published Monte Carlo contributing areas moved one row north onto their cells. (d–f) Ensemble mean F with streams as cells and (g–i) with the stream network, 358 realisations. Outline: published probability 0.5. Mean F with streams as cells correlates with the published probability at r = 0.80, gives 90 % of its expected area, and its zone above 0.5 has an overlap (cells in both as a share of cells in either) of 0.48 with the published one; with the stream network the values are 0.72, 1.51 and 0.49. Windows as in Fig. 6. <!-- figures/README.md Fig. 8; NS §6, Table 4; ensemble/probability_comparison.csv -->

## Figure 9

**Figure 9.** Median contributing area of the eight priority wells relative to base pumping, for pumping q = m (q_base + f (q_max − q_base)) at the priority wells, f = 0 to 1, with m each realisation's well multiplier. At maximum pumping, pumping grows 3.68 times (dashed), the full-mixing area with streams as cells 4.09 times, the published area 3.60 times, PRT with the published conventions 3.62 times (61 realisations; base, half and maximum pumping) and full mixing with the stream network 3.42 times. Areas are the median sum of F over the start cells (358 realisations at base, 357 otherwise), the median count of published contributing cells (357 areas per scenario) or the median count of start cells whose PRT particle reaches the wells. <!-- figures/README.md Fig. 9; NS §7, Tables 5–6; scenarios/area_table.csv, mechanisms60/growth_decomposition.csv -->

## Figure 10

**Figure 10.** Why the full-mixing area grows faster than pumping (streams as cells). (a) Stream leakage as a share of the priority wells' water: median over realisations 42 % at base and 28 % at maximum pumping; band, 5th to 95th percentile (36 to 44 % at base, 25 to 31 % at maximum). (b) For each of the 357 realisations with a published Monte Carlo area, area growth minus pumping growth from base to maximum pumping, against the drop in stream share; r = 0.94 (line: least squares, 0.063 per percentage point). <!-- figures/README.md Fig. 10; NS §7; scenarios/source_table.csv -->

## Table 3

**Table 3.** Delineations of the eight priority wells' contributing area on one flow field (calibrated Neversink model, streams as cells), against the 980 published contributing cells.

| method | delineation | overlap | expected area (cells) | flow reaching the wells (m³/d) |
|---|---|---|---|---|
| Full mixing, gross accounting | F > 0.1 | 0.30 | 910 | 3,671 |
| | F > 0.5 | 0.41 | 910 | 3,671 |
| | area-matched (980 cells) | 0.41 | 910 | 3,671 |
| Full mixing, net accounting | F > 0.1 | 0.28 | 978 | 3,944 |
| | F > 0.5 | 0.44 | 978 | 3,944 |
| | area-matched (980 cells) | 0.40 | 978 | 3,944 |
| PRT, flow-weighted, weight-losing | released over the cell volume, P > 0.5 | 0.62 | 794 | 3,736 |
| | released mid-cell, P > 0.5 | 0.62 | 781 | 3,722 |
| | released at the water table, P > 0.5 | 0.39 | 592 | 2,413 |
| PRT, flow-weighted, plain | released over the cell volume, P > 0.5 | 0.29 | 2,857 | 9,555 |
| PRT, published starts | MF6 default, dry starts dropped to the water table | 0.62 | 730 | – |
| | MF6 default, dry starts draped | 0.65 | 754 | – |
| | top face where open, dry starts dropped | 0.96 | 969 | – |
| | top face where open, dry starts draped (published conventions) | 0.998 | 982 | – |

Overlap: cells in both areas as a share of cells in either, on the 122,021 start cells. Thresholds are strict (F > 0.1, F > 0.5, P > 0.5). Area-matched: the 980 start cells with the largest F. Expected area: sum of F over the start cells (full mixing), particle weight reaching the wells in cells (flow-weighted PRT), or number of start cells whose particle ends in a priority well (published starts). Flow reaching the wells: the well inflow is 3,671 m³/d; net accounting credits each well with all the water passing through its cell. Flow-weighted PRT: particles released from the source terms of the 30,180 cells with F > 10⁻⁶, in all layers; P is the flow-weighted share of the water released in a start cell that particles deliver to the wells. Published starts: one unweighted particle per published start, stopped at every weak sink; MF6 default spreads recharge and stream flows through the cell, "top face where open" puts them on the top face through IFLOWFACE. <!-- NS §2, Tables 1, 2a, 2b, 3, §3 reproduction table; agreement_with_mp7.csv, net_vs_gross_wells.csv, net_vs_gross_mp7.csv, prt_comparison.csv, mp7_reproduction.csv -->
