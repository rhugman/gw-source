<!-- SI items written by the editor in round 2 for placeholders that had no heading. Evidence paths: docs/neversink_study.md (NS) and the CSV files of studies/neversink/output/, which git does not track (NS, "Reproducing"). Merges and numbering are in si/numbering.md. -->

## {SI: per-well gross and net}

**Table.** Contributing area of each priority well against its published contributing cells, under gross and net accounting (§2.3); calibrated Neversink model, streams as cells. Where two values are given, the first is gross accounting and the second net accounting.

| well | pumping (m³/d) | well's share of its cell's outflow | net attribution (m³/d) | published contributing cells | expected area (sum of F) | overlap, F > 0.1 | overlap, F > 0.5 | overlap, area-matched |
|---|---|---|---|---|---|---|---|---|
| SV_193 | 63 | 1.00 | 63 | 48 | 26 / 26 | 0.37 / 0.37 | 0.00 / 0.00 | 0.30 / 0.30 |
| SV_227 | 203 | 1.00 | 199 | 115 | 69 / 74 | 0.29 / 0.29 | 0.16 / 0.19 | 0.25 / 0.26 |
| SV_407 | 94 | 0.91 | 103 | 32 | 34 / 37 | 0.29 / 0.26 | 0.16 / 0.25 | 0.60 / 0.60 |
| SV_487 | 381 | 0.69 | 545 | 97 | 65 / 94 | 0.18 / 0.10 | 0.04 / 0.15 | 0.17 / 0.17 |
| U_917 | 1,054 | 1.00 | 1,054 | 351 | 313 / 314 | 0.56 / 0.56 | 0.53 / 0.53 | 0.68 / 0.68 |
| U__55 | 250 | 0.85 | 293 | 116 | 81 / 97 | 0.06 / 0.16 | 0.00 / 0.00 | 0.13 / 0.13 |
| U___7 | 516 | 0.44 | 1,167 | 58 | 94 / 214 | 0.20 / 0.08 | 0.00 / 0.00 | 0.05 / 0.05 |
| U___8 | 1,110 | 0.93 | 1,197 | 163 | 229 / 249 | 0.10 / 0.10 | 0.00 / 0.00 | 0.22 / 0.22 |
| all eight | 3,671 | – | 3,944 | 980 | 910 / 978 | 0.30 / 0.28 | 0.41 / 0.44 | 0.41 / 0.40 |

Gross accounting credits each well with its pumping. Net attribution is the source water that net accounting credits to the well. Overlap: cells in both areas as a share of cells in either, on the 122,021 start cells; thresholds are strict. Area-matched: as many start cells as the well has published contributing cells, taken in decreasing order of F. <!-- evidence: docs/neversink_study.md §2, Tables 2, 2a, 2b; studies/neversink/output/net_vs_gross_mp7.csv (mp7_cells, expected_cells, jaccard_F>0.1, jaccard_F>0.5, jaccard_area_matched, by accounting); studies/neversink/output/net_vs_gross_wells.csv (pumping, well_share_of_outflow, net_volume_from) -->

The per-well overlaps are lower than the group's because the wells of the U cluster share cells. A published cell belongs to the one well its particle reaches, while under full mixing a cell that sends water to several wells counts for each of them; the union of the eight wells is the fairer comparison. <!-- evidence: docs/neversink_study.md §2, text after Table 2 -->

Under gross accounting the per-well expected areas add up to the group's 910 cells. Under net accounting they add up to 1,104 cells against the group's 978, and the per-well net attributions to 4,621 m³/d against 3,944 m³/d, because a trace of one well fixes only that well's cell. The 608 m³/d that passes from U___7's cell into U___8's, and the 70 m³/d that leaves a well cell and reaches the group again, then count for both wells. <!-- evidence: studies/neversink/output/net_vs_gross_mp7.csv (sum of expected_cells over the eight wells: 910.2 gross, 1,103.6 net; priority row 910.2 and 978.5); studies/neversink/output/net_vs_gross_wells.csv (priority row: net_dest_throughflow_sum 4,621.3, net_volume_from 3,943.5, dest_to_dest_flow 607.7, dest_onward_to_dest 70.1); docs/neversink_study.md §2 -->

Net accounting changes the expected area most where the well takes a small share of its cell's outflow: from 94 to 214 cells at U___7 (44 %) and from 65 to 94 at SV_487 (69 %). At the three wells that take all of their cell's outflow it changes the area by at most 5 cells. At these three wells gross and net accounting both give about 410 cells against 514 published contributing cells. At the other five, the single-well net traces add up to 690 cells and the gross traces to 502, against 466 published contributing cells: net accounting is above the published count at U___7 and U___8 and below it at SV_487 and U__55. One possible reading, not tested, is that stopping a particle at the first weak sink credits the well with all the water reaching its cell, as net accounting does; the per-well counts do not support it. <!-- evidence: studies/neversink/output/net_vs_gross_mp7.csv; net_vs_gross_wells.csv (well_share_of_outflow 0.442, 0.695); largest change at a full-outflow well: SV_227, 69.3 to 73.9 cells; full-outflow wells SV_193, SV_227, U_917: gross 408, net 414, published 514; other five: net 689.7, gross 502.1, published 466 -->

## {SI: end states of the published particles}

Each published MODPATH 7 particle on the calibrated model ends in one of three ways (MODPATH status codes 2, 3 and 5). We classed each end cell on the MODFLOW 6 budget: a strong sink sends all of its outflow to boundary sinks, a weak sink only part of it.

**Table.** End states of the 122,021 published particles, calibrated model.

| end state (MODPATH status) | particles | end cells | particles ending in a priority well |
|---|---|---|---|
| leaves the model through a cell face (2) | 89,920 | top face of a stream cell with no active cell above: 88,781; side face next to a dry cell: 1,139 | 0 |
| stopped on entering a weak-sink cell (3) | 27,631 | buried stream cells: 26,828; wells: 612; constant heads: 191 | 466 (SV_407 32, SV_487 97, U__55 116, U___7 58, U___8 163) |
| ends in a cell with no exit face (5) | 4,470 | wells: 2,570; buried stream cells: 1,472; constant heads: 428 | 514 (SV_193 48, SV_227 115, U_917 351) |
| all | 122,021 | | 980 |

<!-- evidence: studies/neversink/output/mp7_status.csv (particles, top_face, end_SFR_0, end_WEL_0, end_CHD_0 and per-well columns by status); docs/neversink_study.md §2, "End states of the published particles" -->

Status 5 is the normal end at a strong sink, not an abnormal stop. The 980 published contributing cells are the 514 particles that end in the three priority wells that take all of their cell's outflow, plus the 466 stopped in the five priority wells that take only part of it. <!-- evidence: docs/neversink_study.md §2; mp7_status.csv -->

The split between status 2 and status 3 shows a convention that the comparison inherits. The published runs put recharge and stream flows on the top face of the cell. MODPATH 7 does this only where the top face has no active neighbour; elsewhere the flow stays distributed in the cell. A particle that reaches a stream cell with no active cell above therefore leaves through the top face (status 2), while one that reaches a buried stream cell is stopped there as at a weak sink (status 3). Every particle that stops in a stream cell (status 3 or 5) has an active cell above it, and none of those that leave through a stream cell's top face has. The 1,139 particles that leave sideways all leave into a dry neighbour, which the published runs treat as inactive. <!-- evidence: docs/neversink_study.md §2 (MPBAS IFACE 6; ModpathCellData.f90) -->

At the weak-sink wells the published convention and full mixing part ways. The well of U___7 takes 44 % of its cell's outflow, so a published particle entering the cell is credited in full to U___7. Under full mixing the other 56 % of the cell's outflow passes on, most of it to U___8 and U_917, so that 97 % of the water in the cell reaches a priority well (F = 0.97). <!-- evidence: docs/neversink_study.md §2 and §3, "Why the first PRT runs captured too little"; net_vs_gross_wells.csv (well_share_of_outflow 0.442) -->

## {SI: diagnosis of the first PRT runs}

The PRT comparison of §5.3 uses flow-weighted release and, unless stated, weight-losing particles. Plain particles lose weight only to the eight priority wells and pass every other sink with full weight, so water that streams and other sinks take on the way is counted as reaching the wells. Released over the cell volume they delivered 9,555 m³/d, 2.6 times the wells' inflow of 3,671 m³/d (2.1 to 2.5 times for releases at one height). Weight loss at the other sinks removes this excess. <!-- evidence: docs/neversink_study.md §3, Table 3; studies/neversink/output/prt_diagnosis.csv (captured_whole_path with thin_weak_sinks False: 9,554.6 volume, 7,684.8 water table, 9,181.7 mid-cell) -->

An earlier version of our PRT helper gave the opposite error for weight-losing particles: it delivered only 53 to 82 % of the inflow. To find out why, PRT was run without a stop zone and both rules for crediting weight were evaluated on the same particle tracks (gate `diagnose_prt` of `studies/neversink/workflow.py`).

**Table.** Water delivered to the eight priority wells by PRT particles on the calibrated model (m³/d, and share of the wells' inflow of 3,671 m³/d), by release height and crediting rule.

| release | weight-losing, first well cell only (earlier rule) | weight-losing, weight followed along the whole path (current) | plain, whole path |
|---|---|---|---|
| at the water table | 1,940 (53 %) | 2,413 (66 %) | 7,685 (209 %) |
| mid-cell | 3,005 (82 %) | 3,722 (101 %) | 9,182 (250 %) |
| four heights through the cell | 3,015 (82 %) | 3,736 (102 %) | 9,555 (260 %) |

<!-- evidence: studies/neversink/output/prt_diagnosis.csv (captured_first_cell and captured_whole_path for releases z1, z0.5 and volume, thin_weak_sinks True and False); docs/neversink_study.md §3 -->

The two defects were in the helper, not in either method.

- **Weight dropped in weak-sink well cells** (+720 m³/d, 20 % of the inflow, for release over the cell volume). The earlier rule stopped a particle in the first well cell it entered, credited the well with the share of the cell's outflow that the well takes, and dropped the rest. The well of U___7 takes 44 % of its cell's outflow, but most of what passes on reaches U___8 and U_917. Followed along the whole path, the particles credit U___8 with 609 m³/d and U_917 with 111 m³/d more. The helper now loses weight along the whole path: in each cell the wells take their share of the remaining weight and the cell's other sinks remove theirs, with no stop zone. <!-- evidence: prt_diagnosis.csv (volume, thinned: captured_whole_path − captured_first_cell = 720.4; U___8 1,170.8 − 561.9; U_917 1,013.8 − 902.4); docs/neversink_study.md §3 -->
- **Particles held at the water table** (about 1,300 m³/d less at the water table than at mid-cell). MODFLOW 6 spreads recharge and the other boundary flows through the cell volume, and PRT's velocity field matches. A particle released at the water table of a top-layer cell has zero vertical velocity there and never leaves the layer, so wells in deeper layers receive little. The helper now releases at several heights through the saturated thickness by default. <!-- evidence: prt_diagnosis.csv (whole path, thinned: 3,721.9 mid-cell − 2,413.2 water table); docs/neversink_study.md §3 -->

Two other explanations were ruled out. Every particle ended in a cell with no exit face (status 5) with no weight left after its last cell, so no water was lost to other end states, and no particle entered a cell twice, so weight was removed once per cell. On the three-layer test model with a weak-sink well upstream of a strong one, the same two defects gave 266 of 405 m³/d; the current helper gives 402.6 m³/d, which is now a regression test. <!-- evidence: prt_diagnosis.csv (status_5 equal to particles, repeat_visits 0, left_status_5 below 10⁻²⁹⁶ for weight-losing runs); docs/neversink_study.md §3; tests/test_prt.py -->

## {SI: ensemble statistics}

**Table.** Ensemble maps at base pumping against the published probability of contribution (357 published Monte Carlo contributing areas, 358 realisations, published start cells). Values in brackets are against the published areas as stored, before they were moved one row north ({SI: Monte Carlo offsets and scenario rule}).

| map | correlation with the published probability (r) | expected area relative to the published | overlap of the areas above 0.5 |
|---|---|---|---|
| mean F, streams as cells | 0.80 (0.76) | 0.90 | 0.48 (0.43) |
| share of realisations with F > 0.5, streams as cells | 0.76 (0.71) | 0.47 | 0.48 (0.43) |
| mean F, stream network | 0.72 (0.70) | 1.51 | 0.49 (0.44) |

Expected area: the sum of the map over the start cells. Mean F is the full-mixing counterpart of the published probability. <!-- evidence: docs/neversink_study.md §6, Table 4; studies/neversink/output/ensemble/probability_comparison.csv (correlation 0.799, 0.760, 0.722; sum_ratio 0.905, 0.468, 1.508; jaccard_P>0.5 0.483, 0.479, 0.487) -->

Mean F gives 90 % of the published expected area, close to the calibrated model's 910 against 980 cells (§5.2). With the stream network it gives 1.51 times the published expected area, because it includes the area upstream that feeds the losing reaches (§5.4). <!-- evidence: docs/neversink_study.md §6, text after Table 4 -->

Across the 358 realisations the wells' inflow ranged from 3,586 to 3,756 m³/d and the stream share from 30 to 45 %. Each realisation took about 50 s for the MODFLOW 6 run and 9 s for its two traces (streams as cells and stream network), and closure held to 3 × 10⁻¹² m³/d in every one. <!-- evidence: docs/neversink_study.md §6, "Runs"; studies/neversink/output/ensemble/summary.csv -->

Paired with its own published area, each realisation's F at base pumping gives an overlap of 0.42 (F > 0.5) and 0.41 (area-matched), against 0.40 with the neighbouring realisation's area and 0.37 under the uncorrected pairing. It agrees better with its own area than with the neighbour's in 315 of 357 realisations. The published area correlates with the sum of F at r = 0.56 across realisations, against −0.04 under the uncorrected pairing. In the S region the published area varies between realisations with a coefficient of variation of 32 %; PRT with the published conventions follows it (r = 0.997, 60 realisations) and the sum of F does not (r = 0.00). <!-- evidence: docs/neversink_study.md §6, "Pairing the published masks with the realisations" -->

In the pumping scenarios, the correlation of mean F with the published probability rises from 0.80 at base pumping to 0.83 to 0.84, and the overlap of the areas above 0.5 lies between 0.48 and 0.54 (0.80 to 0.82 and 0.44 to 0.49 against the areas as stored). <!-- evidence: docs/neversink_study.md §7, text after Table 5 -->

## {SI: scenario medians}

**Table.** Median contributing area of the eight priority wells (start cells) against pumping. Priority-well pumping is q = m (q_base + f (q_max − q_base)), with m each realisation's well multiplier ({SI: Monte Carlo offsets and scenario rule}).

| scenario | f | pumping (m³/d) | published | full mixing, streams as cells | full mixing against published | full mixing, stream network | stream share, streams as cells |
|---|---|---|---|---|---|---|---|
| baserat | 0 | 3,663 | 998 | 911 | −9 % | 1,534 | 42 % |
| 0.25rat | 0.25 | 6,118 | 1,794 | 1,619 | −10 % | 2,516 | 37 % |
| 0.5rat | 0.5 | 8,571 | 2,475 | 2,339 | −5 % | 3,458 | 33 % |
| 0.75rat | 0.75 | 11,024 | 3,035 | 3,051 | +1 % | 4,368 | 30 % |
| maxrat | 1 | 13,480 | 3,592 | 3,725 | +4 % | 5,247 | 28 % |
| maxrange | U(0, 1) per well and realisation | 8,671 | 2,413 | 2,396 | −1 % | 3,497 | 32 % |
| growth, baserat to maxrat | | 3.68 | 3.60 | 4.09 | | 3.42 | |

Published: median over the 357 published Monte Carlo contributing areas of the scenario. Full mixing: median sum of F over the start cells, over 358 realisations at base pumping and 357 otherwise. Pumping and stream share: medians over the realisations. <!-- evidence: docs/neversink_study.md §7, Table 5; studies/neversink/output/scenarios/area_table.csv (inflow, published_cells, cells_expected, network_expected and their growth columns); studies/neversink/output/scenarios/source_table.csv (stream_share) -->

The full-mixing area grows faster than pumping, and the published area a little slower. Recharge reaching the wells grows 4.57 times from base to maximum pumping, while the full-mixing area per unit of that recharge falls by 11 %; 4.57 × 0.89 ≈ 4.08, close to the growth of the area. Why the stream share falls is in {SI: growth mechanism}. <!-- evidence: studies/neversink/output/scenarios/source_table.csv (rch_growth 4.569; area_per_rch 0.432 to 0.386); docs/neversink_study.md §7 -->

Paired with its own published area, each realisation's F gives an area-matched overlap of 0.49 to 0.54 across the scenarios (0.47 in maxrange), and agrees better with its own area than with the neighbouring realisation's in 236 to 306 of 357 realisations. <!-- evidence: docs/neversink_study.md §7 -->

The maxrange scenario is reproduced in distribution only, because its rates are drawn independently in the published and the rebuilt ensembles; the paired areas do not correlate (r = 0.07). Each area's position between the same realisation's base and maximum areas has a median of 0.55 (published) and 0.52 (rebuilt), with a standard deviation of 0.12 in both, and the coefficient of variation of the area is 0.135 and 0.144. <!-- evidence: docs/neversink_study.md §7 and §8 -->

## {SI: one convention at a time}

**Table.** Median contributing area at base, half and maximum pumping, 61 realisations (60 spread over the ensemble, and the calibrated model), changing one particle convention at a time. Particles start from the published starts, seeded where F > 0.

| area | base | half pumping | maximum pumping | growth, base to maximum |
|---|---|---|---|---|
| full mixing (F of the start cell) | 911 | 2,341 | 3,731 | 4.09 |
| PRT, all boundary flows distributed through the cell, weight-losing at every sink | 820 | 2,405 | 3,709 | 4.53 |
| PRT, recharge and stream flows on open top faces, weight-losing at the distributed sinks | 969 | 3,001 | 4,618 | 4.76 |
| as above, but stopped at buried stream cells | 947 | 2,502 | 3,626 | 3.83 |
| as above, but stopped at every weak sink (the published conventions) | 1,001 | 2,504 | 3,626 | 3.62 |
| published Monte Carlo contributing areas (357 realisations) | 998 | 2,475 | 3,592 | 3.60 |

Areas: sum of F, sum of the particle weight reaching the wells, or number of particles reaching the wells, in cells. Recharge and stream flows were put on the top face through IFLOWFACE (§3.2), which does not change the flows. <!-- evidence: docs/neversink_study.md §7, Table 6; studies/neversink/output/scenarios/mechanisms60/growth_decomposition.csv (variants f_start, r3_thinned, r2_thinned, r2_streams_thinned, r1, published; area_baserat, area_scenario, growth_of_medians for 0.5rat and maxrat) -->

With the published conventions, PRT reproduces the published growth: 3.62 against 3.60 from base to maximum pumping and 2.50 against 2.48 to half pumping. The medians of the per-realisation growth are 3.57 and 3.55. Paired with its own published area, the PRT area is within 1.4 % in every realisation and scenario, and its growth correlates with the published growth at r ≥ 0.999. <!-- evidence: docs/neversink_study.md §7; growth_decomposition.csv (r1: 2.501, 3.622; published: 2.480, 3.599; median_growth 3.570 and 3.552); studies/neversink/output/scenarios/mechanisms60/mask_matches.csv -->

The published area grows more slowly mainly because the particles stop at buried stream cells (growth 4.76 against 3.83). The capture zone reaches these cells only at higher pumping. Under full mixing or weight loss they pass on all but the stream's share of their outflow, while under the published conventions every particle that enters them stops. The stops remove particle weight equal to 34 contributing cells at base, 522 at half and 987 at maximum pumping (means over the realisations). All of it is at buried stream cells, 85 % of it in layer 2 and 90 % of it 1 to 4 km from the nearest priority well. <!-- evidence: docs/neversink_study.md §7, bullets after Table 6; studies/neversink/output/scenarios/mechanisms60/stream_stops.csv -->

Stopping particles also at the remaining weak sinks, mainly the well cells that take only part of their cell's outflow, counts those cells as F = 1. This adds 54 cells at base pumping and none at maximum pumping, where seven of the eight wells take all of their cell's outflow (growth 3.83 against 3.62). Restricting the comparison to start cells plays no part in the difference: 96 % of the wells' water enters in start cells in every scenario, and draping changes the full-mixing area by less than one cell. <!-- evidence: docs/neversink_study.md §7; growth_decomposition.csv (r1 base 1,001 − r2_streams_thinned base 947.3; f_draped against f_start) -->

## {SI: faster growth of weight-losing particles}

With all boundary flows distributed through the cell, the area of weight-losing particles grows 4.53 times from base to maximum pumping, against 4.09 for full mixing ({SI: one convention at a time}). Over the 61 realisations their area is 0.905 times the full-mixing area at base pumping, 1.02 times at half and 1.00 times at maximum pumping (medians), so the faster growth is a shortfall at base pumping that disappears as pumping rises. Across the realisations the ratio of the two growths follows the base-pumping ratio (r = −0.98), which in turn follows the stream share under full mixing (r = −0.75). <!-- evidence: docs/neversink_study.md §7, "Why thinned particles grow faster"; studies/neversink/output/scenarios/mechanisms60/growth_decomposition.csv (r3_thinned 4.525, f_start 4.095) -->

To find the cause, six realisations (the calibrated model and five spread over the range of growth ratios) were rerun at the three rates with flow-weighted release from every source term: four plan points at four heights per term, weight-losing at every sink. <!-- evidence: docs/neversink_study.md §7; studies/neversink/advective_growth.py -->

**Table.** Calibrated model, boundary flows distributed through the cell.

| | base | half pumping | maximum pumping | growth, base to maximum |
|---|---|---|---|---|
| full mixing, expected area (sum of F over the start cells) | 910 | 2,340 | 3,734 | 4.10 |
| particles from the recharge of the start cells, expected area | 794 | 2,377 | 3,685 | 4.64 |
| one particle per start cell, expected area | 799 | 2,419 | 3,676 | 4.60 |
| recharge of the start cells reaching the wells, full mixing (m³/d) | 2,099 | 5,771 | 9,666 | 4.60 |
| recharge of the start cells reaching the wells, particles (m³/d) | 1,821 | 5,695 | 9,496 | 5.21 |
| stream share, full mixing / particles | 43 / 51 % | 33 / 33 % | 28 / 29 % | |

<!-- evidence: studies/neversink/output/scenarios/advective_growth/areas.csv (real base, convention distributed: area:f_start, area:dense, area:single, rch_mix_starts, rch_prt_starts at baserat, 0.5rat, maxrat); area_growth.csv (growth columns; rch_prt_starts growth 5.215); summary.csv (mixing:stream_share and distributed:stream_share, real base). NS Table 7 gives 5,772 m³/d, 5.22, 33 / 34 % and 29 / 29 % for four of these cells; the CSV values are used here. -->

- **The release is not the cause.** One particle per start cell gives the area of the full release to within 6 % in all six realisations, and four times as many release points change that area by less than 2 cells. At base pumping the particle area converges to 794 cells, not to the 910 of full mixing. <!-- evidence: docs/neversink_study.md §7, bullets after Table 7 -->
- **The area follows the recharge that reaches the wells.** The area per unit of recharge reaching the wells is the same under both methods to within 4 % in all six realisations. <!-- evidence: docs/neversink_study.md §7 -->
- **The recharge differs because the stream water differs.** At base pumping the particles deliver the wells' inflow to within 2 % (3,736 against 3,671 m³/d), but with 344 m³/d more stream water. Nearly all of it comes from 17 losing reach cells 0.5 to 1 km from the U wells, which leak 1,655 m³/d. Full mixing sends 69 % of that leakage to the wells, the particles 90 %, and water that particles carry into these cells from elsewhere also reaches the wells in full, where full mixing gives F = 0.60. The wells then take 279 m³/d less recharge, mostly from start cells with F between 0.1 and 0.5 in the top layer of the valley fill, and the particle area is 13 % smaller. We infer from these budgets, without tracing it cell by cell, that along the particle paths the leakage stays on flow lines that end in the wells, while full mixing gives it the average fate of all the water leaving these cells. <!-- evidence: docs/neversink_study.md §3 (+344 m³/d, 3,736 m³/d) and §7, §8 -->
- **The shortfall disappears as pumping rises.** At half and maximum pumping these reach cells send nearly all their water to the wells (F = 0.94 and 0.99; particles 0.97 and 1.00), and the excess stream water along the particle paths drops to 47 and 10 m³/d. The source splits then agree to within one percentage point and the areas to within 2 %. Across the six realisations, the growth of the particle area relative to full mixing ranges from 0.95 to 1.20 and follows the excess stream water along the paths at base pumping (0 to 10 percentage points). Realisation 231, whose stream share under full mixing is 35 %, has no excess and grows more slowly than full mixing (3.39 against 3.80). <!-- evidence: docs/neversink_study.md §7; studies/neversink/output/scenarios/advective_growth/area_growth.csv (real 231, distributed: area:single growth 3.394, area:f_start growth 3.800) -->
- **The top-face convention behaves in the same way.** With recharge and stream flows on the top face, one particle at mid-height of the start cell overstates the recharge reaching the wells by 18 to 23 % at every rate, compared with releasing the recharge on the top face (953 against 809 cells at base, 4,617 against 3,837 at maximum pumping), which adds only 2 % to the growth but puts the top-face areas of {SI: one convention at a time} above full mixing. We take this to be because recharge on the top face is the shallowest water of the column; it was not tested further. <!-- evidence: studies/neversink/output/scenarios/advective_growth/areas.csv (real base, convention top_face: area:single 953.2, 3,030.2, 4,617.2; area:dense 808.7, 2,462.8, 3,836.7); docs/neversink_study.md §7 -->
- **Per cell the differences are much larger than the net.** The sum over the start cells of the absolute difference between the particle area and F is 885 cells at base and 1,927 at maximum pumping (mean per realisation), against net differences of −62 and −17 cells. <!-- evidence: docs/neversink_study.md §7 -->
