<!-- Reduced draft, SI round 1: one Neversink text, merged from the former Text S12 (end states), Table S3 (delineations) and its note, the full-model counts of the former Figs S9 and S12 captions and the timing note under the former Table S6. The Monte Carlo offsets, the diagnosis of the first PRT runs, the per-well table and the ensemble statistics moved to docs/neversink_study.md (§2, §3 and §6). Evidence paths: docs/neversink_study.md (NS) and the CSV files of studies/neversink/output/, which git does not track (NS, "Reproducing"). -->

## {SI: the Neversink comparison}

Section 5 compares full mixing with the published particle tracking of the Neversink/Rondout model (Fienen et al. 2022; Corson-Dosch et al. 2022). This text gives the terms of that comparison, the delineations behind its overlaps and how the published particles end. The model is in a USGS data release (Fienen and Corson-Dosch 2021). Its 358 realisations come from history matching with PEST++ IES (White 2018; White et al. 2020). We refer to the realisation with the base parameters as the calibrated model. <!-- evidence: docs/neversink_study.md §1, §6 and line 202 (rebuilt base realisation equals the published calibrated input); run 357 is the calibrated realisation; ensemble/summary.csv (358 realisations) -->

The published runs start one MODPATH 7 particle in the uppermost active cell of each column near the wells. We refer to these cells as the start cells. The published contributing cells are the 980 start cells whose particle ends in one of the eight priority wells. Two areas are compared by their overlap. It is the number of cells in both areas divided by the number of cells in either. The expected area of a map of F is the sum of F over the start cells. It is a size of the contributing area that needs no threshold. All Neversink cells are 50 m squares, so expected areas are given as numbers of cells. <!-- evidence: docs/neversink_study.md §1, §2 (three regions, 122,021 particles; Jaccard index); full draft Section 4.1 (expected area) and Section 5 (sum over the start cells; all cells are 50 m) -->

### Delineations on one flow field

The table compares the delineations of the eight wells' contributing area on the calibrated model, with streams as cells. Each is compared with the 980 published contributing cells. <!-- table moved from the former Table S3 (si/D.md) in SI round 1 -->

| method | delineation | overlap | expected area (cells) | flow attributed to the wells (m³/d) |
|------------------------|------------------------------------|---------|-------------|------------------|
| Full mixing, gross accounting | F > 0.1 | 0.30 | 910 | 3,671 |
| | F > 0.5 | 0.41 | 910 | 3,671 |
| | area-matched (980 cells) | 0.41 | 910 | 3,671 |
| Full mixing, net accounting | F > 0.1 | 0.28 | 978 | 3,944 |
| | F > 0.5 | 0.44 | 978 | 3,944 |
| | area-matched (980 cells) | 0.40 | 978 | 3,944 |
| PRT, flow-weighted, weight-losing | released over the cell volume, P > 0.5 | 0.62 | 794 | 3,736 |
| | released mid-cell, P > 0.5 | 0.62 | 781 | 3,722 |
| | released at the water table, P > 0.5 | 0.39 | 592 | 2,413 |
| PRT, flow-weighted, losing weight only at wells | released over the cell volume, P > 0.5 | 0.29 | 2,857 | 9,555 |
| PRT, published starts | MODFLOW 6 default, dry starts dropped to the water table | 0.62 | 730 | – |
| | MODFLOW 6 default, dry starts draped | 0.65 | 754 | – |
| | top face where open, dry starts dropped | 0.96 | 969 | – |
| | top face where open, dry starts draped (published settings) | 0.998 | 982 | – |

<!-- NS §2, Tables 1, 2a, 2b, 3, §3 reproduction table; agreement_with_mp7.csv, net_vs_gross_wells.csv (priority row: net_volume_from 3,943.5), net_vs_gross_mp7.csv (area_matched_F 0.279 gross, 0.303 net), prt_comparison.csv, mp7_reproduction.csv -->

Thresholds are strict. The area-matched delineation takes the 980 start cells with the largest F. For flow-weighted PRT, the expected area is the particle weight that reaches the wells, in cells. For published starts, it is the number of start cells whose particle ends in a priority well. The flow-weighted particles were released from the source terms of the 30,180 cells with F > 10⁻⁶, in all layers. P is the share of the water released in a start cell that the particles deliver to the wells. The published-start runs use one unweighted particle per published start, stopped at every weak sink. "MODFLOW 6 default" spreads recharge and stream flows through the cell. "Top face where open" puts them on the top face through IFLOWFACE, the MODFLOW 6 setting that assigns a boundary flow to one cell face. <!-- NS §3 (30,180 cells with F > 1e-6, flux-weighted release in all layers; reproduction with IFLOWFACE −1 and draping); note shortened in SI round 1 -->

The wells take 3,671 m³/d. Gross accounting attributes exactly this flow to them. Net accounting attributes 3,944 m³/d, because it also counts the water that passes on from the well cells. Weight-losing particles deliver within 2 % of the wells' inflow. Particles that lose weight only at the wells deliver 9,555 m³/d. That is 2.6 times the wells' inflow. They keep the weight that streams and other sinks take on the way. Their delivery is therefore water the particles assign to the wells, not water that flows into them. <!-- NS §2, Table 2a (net 3,943.5 m³/d); §3, Table 3 (9,555 m³/d, factor 2.6); prt_diagnosis.csv -->

The F > 0.1 area holds 711 of the 980 published contributing cells (73 %). It holds 602 (87 %) of the 691 start cells where weight-losing particles released over the cell volume deliver more than half their water to the wells. The particles deliver 227 m³/d to the wells from the 89 cells that the F > 0.1 area misses. That is 6 % of the water they deliver in all. <!-- NS §2 (711 of 980 published cells inside F > 0.1); NS §5, Table 3a; envelope_prt.csv (all, P>0.5, F>0.1: prt_cells 691, missed_cells 89, coverage 0.871 = 602 / 691; 226.7 of 3,736 m³/d) -->

### End states of the published particles

Each published MODPATH 7 particle on the calibrated model ends in one of three ways. We classed each end cell on the MODFLOW 6 budget. A strong sink sends all of its outflow to boundary sinks. A weak sink sends only part of it. <!-- evidence: studies/neversink/output/mp7_status.csv; docs/neversink_study.md §2, "End states of the published particles" -->

| end state (MODPATH status) | particles | end cells | particles ending in a priority well |
|----------------------------|-----------|---------------------------------------------|----------------|
| leaves the model through a cell face (2) | 89,920 | top face of a stream cell with no active cell above: 88,781; side face next to a dry cell: 1,139 | 0 |
| stopped on entering a weak-sink cell (3) | 27,631 | buried stream cells: 26,828; wells: 612; constant heads: 191 | 466 |
| ends in a cell with no exit face (5) | 4,470 | wells: 2,570; buried stream cells: 1,472; constant heads: 428 | 514 |

<!-- evidence: studies/neversink/output/mp7_status.csv (particles, top_face, end_SFR_0, end_WEL_0, end_CHD_0 and per-well columns by status); per-well counts (SV_407 32, SV_487 97, U__55 116, U___7 58, U___8 163; SV_193 48, SV_227 115, U_917 351) in docs/neversink_study.md §2 -->

The 980 published contributing cells are the 514 particles that end in the three priority wells that take all of their cell's outflow. They also include the 466 particles stopped in the five priority wells that take only part of it. <!-- evidence: docs/neversink_study.md §2; mp7_status.csv -->

A buried stream cell is a cell with an SFR reach and another active cell above it. The published runs put recharge and stream flows on the top face of the cell. MODPATH 7 does this only where the top face has no active neighbour. Elsewhere the flow stays spread through the cell. A particle that reaches a stream cell with no active cell above therefore leaves through the top face (status 2). A particle that reaches a buried stream cell is stopped there as at a weak sink (status 3). Every particle that stops in a stream cell has an active cell above it. None of those that leave through a stream cell's top face has. <!-- evidence: docs/neversink_study.md §2 (MPBAS IFACE 6; ModpathCellData.f90) -->

At the weak-sink wells, the published particles and full mixing treat the cell's water differently. The well of U\_\_\_7 takes 44 % of its cell's outflow. All the water of a published particle that enters the cell still counts as reaching U\_\_\_7. Under full mixing, the other 56 % of the cell's outflow passes on, most of it to U\_\_\_8 and U\_917. So 97 % of the water in the cell reaches a priority well (F = 0.97). <!-- evidence: docs/neversink_study.md §2 and §3, "Why the first PRT runs captured too little"; net_vs_gross_wells.csv (well_share_of_outflow 0.442) -->

### The ensemble

Each of the 358 realisations took about 50 s for the MODFLOW 6 run and 9 s for two traces, one with streams as cells and one with the stream network. The whole ensemble took 76 min in six parallel processes. Closure held to 3 × 10⁻¹² m³/d in every realisation. <!-- evidence: docs/neversink_study.md Summary ("The ensemble (358 realisations, two traces each) took 76 min on six processes") and §6, "Runs"; moved from the note under the former Table S6 in SI round 1 --> The published study maps a probability of contribution. It is the share of 357 published Monte Carlo contributing areas that contain a cell. Mean F over the realisations, with streams as cells, is the full-mixing counterpart ({SI: Neversink particle area and ensemble mean F}b). It correlates with the published probability at r = 0.80. Its expected area is 0.90 times the published one. The stored published areas lie one row south of their cells, so we moved them one row north before this comparison. The archived code release (Section 7) explains this offset in docs/neversink_study.md. <!-- evidence: docs/neversink_study.md §6, Table 4 and "Pairing the published masks with the realisations"; studies/neversink/output/ensemble/probability_comparison.csv (correlation 0.799; sum_ratio 0.905) -->

## {SI: Neversink particle area and ensemble mean F}

**Figure.** The eight priority wells of the Neversink/Rondout model, in the 7.1 × 9.25 km window of main-text Fig. 3. All maps show the uppermost active cell, with streams as cells and gross accounting. (a) The F > 0.1 area against the area where weight-losing PRT particles, released over the cell volume, deliver more than half their water to the wells (P > 0.5). Dark blue: in both (495 cells in this window). Orange: particles only (86). Light blue: F > 0.1 only (1,133). (b) Mean F over 358 realisations, with the published probability of contribution 0.5 outlined. Grey: below 0.01. (c) The model, the three regions of the published particle runs (dashed) and the window. Orange dots: wells. Blue lines: SFR reaches. Scale bar (a): 2 km.

<!-- Panels (c) and (d) and the inset of the full draft's Figure 12, drawn as docs/paper/figures/figS22_neversink_cd.png by studies/paper/neversink_figures.py neversink_si_cd (gate fig_si_cd), which asserts the window counts (DOC_U_WINDOW: P classes 495 / 86 / 1,133) and the whole-model counts (check_overlap: 602 / 89 / 1,537). figures/README.md Fig. 6 (window 142 × 185 cells, 7.1 × 9.25 km); docs/neversink_study.md §6 (runs 0–356 have areas; run 357, the calibrated realisation, has none) -->
