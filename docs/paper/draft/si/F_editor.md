<!-- SI items written by the editor in round 2 for placeholders that had no heading. Evidence paths: docs/neversink_study.md (NS) and the CSV files of studies/neversink/output/, which git does not track (NS, "Reproducing"). Merges and numbering are in si/numbering.md. -->

## {SI: per-well gross and net}

**Table.** Contributing area of each priority well against its published contributing cells, under gross and net accounting (Section 2.4); calibrated Neversink model, streams as cells. Where two values are given, the first is gross accounting and the second net accounting.

| well | pumping (m³/d) | well's share of its cell's outflow | net attribution (m³/d) | published contributing cells | expected area (sum of F) | overlap, F > 0.1 | overlap, F > 0.5 | overlap, area-matched |
|---|---|---|---|---|---|---|---|---|
| SV\_193 | 63 | 1.00 | 63 | 48 | 26 / 26 | 0.37 / 0.37 | 0.00 / 0.00 | 0.30 / 0.30 |
| SV\_227 | 203 | 1.00 | 199 | 115 | 69 / 74 | 0.29 / 0.29 | 0.16 / 0.19 | 0.25 / 0.26 |
| SV\_407 | 94 | 0.91 | 103 | 32 | 34 / 37 | 0.29 / 0.26 | 0.16 / 0.25 | 0.60 / 0.60 |
| SV\_487 | 381 | 0.69 | 545 | 97 | 65 / 94 | 0.18 / 0.10 | 0.04 / 0.15 | 0.17 / 0.17 |
| U\_917 | 1,054 | 1.00 | 1,054 | 351 | 313 / 314 | 0.56 / 0.56 | 0.53 / 0.53 | 0.68 / 0.68 |
| U\_\_55 | 250 | 0.85 | 293 | 116 | 81 / 97 | 0.06 / 0.16 | 0.00 / 0.00 | 0.13 / 0.13 |
| U\_\_\_7 | 516 | 0.44 | 1,167 | 58 | 94 / 214 | 0.20 / 0.08 | 0.00 / 0.00 | 0.05 / 0.05 |
| U\_\_\_8 | 1,110 | 0.93 | 1,197 | 163 | 229 / 249 | 0.10 / 0.10 | 0.00 / 0.00 | 0.22 / 0.22 |
| all eight | 3,671 | – | 3,944 | 980 | 910 / 978 | 0.30 / 0.28 | 0.41 / 0.44 | 0.41 / 0.40 |

Gross accounting credits each well with its pumping. Net attribution is the source water that net accounting credits to the well. Overlap: cells in both areas as a share of cells in either, on the 122,021 start cells; thresholds are strict. Area-matched: as many start cells as the well has published contributing cells, taken in decreasing order of F. <!-- evidence: docs/neversink_study.md §2, Tables 2, 2a, 2b; studies/neversink/output/net_vs_gross_mp7.csv (mp7_cells, expected_cells, jaccard_F>0.1, jaccard_F>0.5, jaccard_area_matched, by accounting); studies/neversink/output/net_vs_gross_wells.csv (pumping, well_share_of_outflow, net_volume_from) -->

The per-well overlaps are lower than the group's because the wells of the U cluster share cells. A published cell belongs to the one well its particle reaches, while under full mixing a cell that sends water to several wells counts for each of them; the union of the eight wells is the fairer comparison. <!-- evidence: docs/neversink_study.md §2, text after Table 2 -->

Under gross accounting the per-well expected areas add up to the group's 910 cells. Under net accounting they add up to 1,104 cells against the group's 978, and the per-well net attributions to 4,621 m³/d against 3,944 m³/d, because a trace of one well fixes only that well's cell. The 608 m³/d that passes from U\_\_\_7's cell into U\_\_\_8's, and the 70 m³/d that leaves a well cell and reaches the group again, then count for both wells. <!-- evidence: studies/neversink/output/net_vs_gross_mp7.csv (sum of expected_cells over the eight wells: 910.2 gross, 1,103.6 net; priority row 910.2 and 978.5); studies/neversink/output/net_vs_gross_wells.csv (priority row: net_dest_throughflow_sum 4,621.3, net_volume_from 3,943.5, dest_to_dest_flow 607.7, dest_onward_to_dest 70.1); docs/neversink_study.md §2 -->

Net accounting changes the expected area most where the well takes a small share of its cell's outflow: from 94 to 214 cells at U\_\_\_7 (44 %) and from 65 to 94 at SV\_487 (69 %). At the three wells that take all of their cell's outflow it changes the area by at most 5 cells. At these three wells gross and net accounting both give about 410 cells against 514 published contributing cells. At the other five, the single-well net traces add up to 690 cells and the gross traces to 502, against 466 published contributing cells: net accounting is above the published count at SV\_407, U\_\_\_7 and U\_\_\_8 and below it at SV\_487 and U\_\_55. One possible reading, not tested, is that stopping a particle at the first weak sink credits the well with all the water reaching its cell, as net accounting does; the per-well counts do not support it. <!-- evidence: studies/neversink/output/net_vs_gross_mp7.csv; net_vs_gross_wells.csv (well_share_of_outflow 0.442, 0.695); largest change at a full-outflow well: SV_227, 69.3 to 73.9 cells; full-outflow wells SV_193, SV_227, U_917: gross 408, net 414, published 514; other five: net 689.7, gross 502.1, published 466; SV_407 net 37 against 32 published (table above) -->

## {SI: end states of the published particles}

Each published MODPATH 7 particle on the calibrated model ends in one of three ways (MODPATH status codes 2, 3 and 5). We classed each end cell on the MODFLOW 6 budget: a strong sink sends all of its outflow to boundary sinks, a weak sink only part of it.

**Table.** End states of the 122,021 published particles, calibrated model.

| end state (MODPATH status) | particles | end cells | particles ending in a priority well |
|---|---|---|---|
| leaves the model through a cell face (2) | 89,920 | top face of a stream cell with no active cell above: 88,781; side face next to a dry cell: 1,139 | 0 |
| stopped on entering a weak-sink cell (3) | 27,631 | buried stream cells: 26,828; wells: 612; constant heads: 191 | 466 (SV\_407 32, SV\_487 97, U\_\_55 116, U\_\_\_7 58, U\_\_\_8 163) |
| ends in a cell with no exit face (5) | 4,470 | wells: 2,570; buried stream cells: 1,472; constant heads: 428 | 514 (SV\_193 48, SV\_227 115, U\_917 351) |
| all | 122,021 | | 980 |

<!-- evidence: studies/neversink/output/mp7_status.csv (particles, top_face, end_SFR_0, end_WEL_0, end_CHD_0 and per-well columns by status); docs/neversink_study.md §2, "End states of the published particles" -->

Status 5 is the normal end at a strong sink, not an abnormal stop. The 980 published contributing cells are the 514 particles that end in the three priority wells that take all of their cell's outflow, plus the 466 stopped in the five priority wells that take only part of it. <!-- evidence: docs/neversink_study.md §2; mp7_status.csv -->

The split between status 2 and status 3 shows a convention that the comparison inherits. The published runs put recharge and stream flows on the top face of the cell. MODPATH 7 does this only where the top face has no active neighbour; elsewhere the flow stays distributed in the cell. A particle that reaches a stream cell with no active cell above therefore leaves through the top face (status 2), while one that reaches a buried stream cell is stopped there as at a weak sink (status 3). Every particle that stops in a stream cell (status 3 or 5) has an active cell above it, and none of those that leave through a stream cell's top face has. The 1,139 particles that leave sideways all leave into a dry neighbour, which the published runs treat as inactive. <!-- evidence: docs/neversink_study.md §2 (MPBAS IFACE 6; ModpathCellData.f90) -->

At the weak-sink wells the published convention and full mixing part ways. The well of U\_\_\_7 takes 44 % of its cell's outflow, so a published particle entering the cell is credited in full to U\_\_\_7. Under full mixing the other 56 % of the cell's outflow passes on, most of it to U\_\_\_8 and U\_917, so that 97 % of the water in the cell reaches a priority well (F = 0.97). <!-- evidence: docs/neversink_study.md §2 and §3, "Why the first PRT runs captured too little"; net_vs_gross_wells.csv (well_share_of_outflow 0.442) -->

## {SI: diagnosis of the first PRT runs}

The PRT comparisons of Section 5 and {SI: delineations on one flow field} use flow-weighted release and, unless stated, weight-losing particles. Particles that lose weight only at the eight priority wells pass every other sink with full weight. So water that streams and other sinks take on the way is counted as reaching the wells. Released over the cell volume they delivered 9,555 m³/d, 2.6 times the wells' inflow of 3,671 m³/d (2.1–2.5 times for releases at one height). Weight loss at the other sinks removes this excess. <!-- evidence: docs/neversink_study.md §3, Table 3; studies/neversink/output/prt_diagnosis.csv (captured_whole_path with thin_weak_sinks False: 9,554.6 volume, 7,684.8 water table, 9,181.7 mid-cell) -->

An earlier version of our PRT helper gave the opposite error for weight-losing particles: it delivered only 53–82 % of the inflow. To find out why, PRT was run without a stop zone and both rules for crediting weight were evaluated on the same particle tracks (gate `diagnose_prt` of `studies/neversink/workflow.py`).

**Table.** Water delivered to the eight priority wells by PRT particles on the calibrated model (m³/d, and share of the wells' inflow of 3,671 m³/d), by release height and crediting rule.

| release | weight-losing, first well cell only (earlier rule) | weight-losing, weight followed along the whole path (current) | losing weight only at the wells, whole path |
|---|---|---|---|
| at the water table | 1,940 (53 %) | 2,413 (66 %) | 7,685 (209 %) |
| mid-cell | 3,005 (82 %) | 3,722 (101 %) | 9,182 (250 %) |
| four heights through the cell | 3,015 (82 %) | 3,736 (102 %) | 9,555 (260 %) |

<!-- evidence: studies/neversink/output/prt_diagnosis.csv (captured_first_cell and captured_whole_path for releases z1, z0.5 and volume, thin_weak_sinks True and False); docs/neversink_study.md §3 -->

The two defects were in the helper, not in either method.

- **Weight dropped in weak-sink well cells** (+720 m³/d, 20 % of the inflow, for release over the cell volume). The earlier rule stopped a particle in the first well cell it entered, credited the well with the share of the cell's outflow that the well takes, and dropped the rest. The well of U\_\_\_7 takes 44 % of its cell's outflow, but most of what passes on reaches U\_\_\_8 and U\_917. Followed along the whole path, the particles credit U\_\_\_8 with 609 m³/d and U\_917 with 111 m³/d more. The helper now loses weight along the whole path: in each cell the wells take their share of the remaining weight and the cell's other sinks remove theirs, with no stop zone. <!-- evidence: prt_diagnosis.csv (volume, thinned: captured_whole_path − captured_first_cell = 720.4; U___8 1,170.8 − 561.9; U_917 1,013.8 − 902.4); docs/neversink_study.md §3 -->
- **Particles held at the water table** (about 1,300 m³/d less at the water table than at mid-cell). MODFLOW 6 spreads recharge and the other boundary flows through the cell volume, and PRT's velocity field matches. A particle released at the water table of a top-layer cell has zero vertical velocity there and never leaves the layer, so wells in deeper layers receive little. The helper now releases at several heights through the saturated thickness by default. <!-- evidence: prt_diagnosis.csv (whole path, thinned: 3,721.9 mid-cell − 2,413.2 water table); docs/neversink_study.md §3 -->

Two other explanations were ruled out. Every particle ended in a cell with no exit face (status 5) with no weight left after its last cell, so no water was lost to other end states, and no particle entered a cell twice, so weight was removed once per cell. On the three-layer test model with a weak-sink well upstream of a strong one, the same two defects gave 266 of 405 m³/d; the current helper gives 402.6 m³/d, which is now a regression test. <!-- evidence: prt_diagnosis.csv (status_5 equal to particles, repeat_visits 0, left_status_5 below 10⁻²⁹⁶ for weight-losing runs); docs/neversink_study.md §3; tests/test_prt.py -->

## {SI: ensemble statistics}

**Table.** Ensemble maps at base pumping against the published probability of contribution (357 published Monte Carlo contributing areas, 358 realisations, published start cells). Values in brackets are against the published areas as stored, before they were moved one row north ({SI: Monte Carlo offsets}).

| map | correlation with the published probability (r) | expected area relative to the published | overlap of the areas above 0.5 |
|---|---|---|---|
| mean F, streams as cells | 0.80 (0.76) | 0.90 | 0.48 (0.43) |
| share of realisations with F > 0.5, streams as cells | 0.76 (0.71) | 0.47 | 0.48 (0.43) |
| mean F, stream network | 0.72 (0.70) | 1.51 | 0.49 (0.44) |

Expected area: the sum of the map over the start cells. Mean F is the full-mixing counterpart of the published probability. {SI: Neversink probability of contribution} maps the published probability and the ensemble mean F around each cluster of wells. <!-- evidence: docs/neversink_study.md §6, Table 4; studies/neversink/output/ensemble/probability_comparison.csv (correlation 0.799, 0.760, 0.722; sum_ratio 0.905, 0.468, 1.508; jaccard_P>0.5 0.483, 0.479, 0.487) -->

Mean F gives 90 % of the published expected area, close to the calibrated model's 910 against 980 cells ({SI: delineations on one flow field}). With the stream network it gives 1.51 times the published expected area, because it includes the area upstream that feeds the losing reaches (Section 5). <!-- evidence: docs/neversink_study.md §6, text after Table 4 -->

Across the 358 realisations the wells' inflow was 3,586–3,756 m³/d and the stream share 30–45 %. Each realisation took about 50 s for the MODFLOW 6 run and 9 s for its two traces (streams as cells and stream network). The 358 realisations took 76 min in all, run in six parallel processes. Closure held to 3 × 10⁻¹² m³/d in every realisation. <!-- evidence: docs/neversink_study.md Summary ("The ensemble (358 realisations, two traces each) took 76 min on six processes") and §6, "Runs"; studies/neversink/output/ensemble/summary.csv; the 76 min moved from Section 5 (review alt_r1, §5 cuts) -->

Paired with its own published area, each realisation's F at base pumping gives an overlap of 0.42 (F > 0.5) and 0.41 (area-matched), against 0.40 with the neighbouring realisation's area and 0.37 under the uncorrected pairing. It agrees better with its own area than with the neighbour's in 315 of 357 realisations. The published area correlates with the sum of F at r = 0.56 across realisations, against −0.04 under the uncorrected pairing. In the S region the published area varies between realisations with a coefficient of variation of 32 %; PRT with the published conventions follows it (r = 0.997, 60 realisations) and the sum of F does not (r = 0.00). <!-- evidence: docs/neversink_study.md §6, "Pairing the published masks with the realisations" -->
