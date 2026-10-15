## {SI: delineations on one flow field}

**Table.** Delineations of the eight priority wells' contributing area on one flow field (calibrated Neversink model, streams as cells), against the 980 published contributing cells.

| method | delineation | overlap | expected area (cells) | flow credited to the wells (m³/d) |
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
| PRT, flow-weighted, losing weight only at wells | released over the cell volume, P > 0.5 | 0.29 | 2,857 | 9,555 |
| PRT, published starts | MODFLOW 6 default, dry starts dropped to the water table | 0.62 | 730 | – |
| | MODFLOW 6 default, dry starts draped | 0.65 | 754 | – |
| | top face where open, dry starts dropped | 0.96 | 969 | – |
| | top face where open, dry starts draped (published settings) | 0.998 | 982 | – |

Overlap: cells in both areas as a share of cells in either, on the 122,021 start cells. Thresholds are strict (F > 0.1, F > 0.5, P > 0.5). Area-matched: the 980 start cells with the largest F (F ≥ 0.28 gross, F ≥ 0.30 net). Expected area: sum of F over the start cells (full mixing), particle weight reaching the wells in cells (flow-weighted PRT), or number of start cells whose particle ends in a priority well (published starts). Flow credited to the wells: the wells' inflow is 3,671 m³/d, which gross accounting credits exactly. Net accounting credits the eight wells together with 3,944 m³/d, the group's credited flow, which is more than the inflow because it counts the water passing on from the well cells; the per-well net attributions sum to 4,621 m³/d, because water passing from one well cell to another counts for both wells ({SI: per-well gross and net}). Weight-losing particles deliver within 2 % of the inflow; particles that lose weight only at the wells keep the weight that streams and other sinks take on the way. Their 9,555 m³/d, 2.6 times the wells' inflow, is therefore credited water, not inflow ({SI: diagnosis of the first PRT runs}). This setting gives the lowest overlap in the table, 0.29. Flow-weighted PRT: particles released from the source terms of the 30,180 cells with F > 10⁻⁶, in all layers; P is the flow-weighted share of the water released in a start cell that particles deliver to the wells. Published starts: one unweighted particle per published start, stopped at every weak sink; "MODFLOW 6 default" spreads recharge and stream flows through the cell, "top face where open" puts them on the top face through IFLOWFACE, the MODFLOW 6 setting that assigns a boundary flow to one cell face, which PRT reads. <!-- NS §2, Tables 1, 2a, 2b, 3, §3 reproduction table; agreement_with_mp7.csv, net_vs_gross_wells.csv (priority row: net_volume_from 3,943.5, net_dest_throughflow_sum 4,621.3), net_vs_gross_mp7.csv (area_matched_F 0.279 gross, 0.303 net), prt_comparison.csv, mp7_reproduction.csv -->

## {SI: Monte Carlo offsets}

Two bookkeeping steps of the published workflow first hid the pairing of the published Monte Carlo contributing areas with the realisations. The step that wrote the areas is not archived, so both corrections are inferred. <!-- NS §6, §8 -->

- **One row south.** The published script computes the row of a particle's start cell as the 1-based row of the cell centre and the column as 0-based, so every area lies one row south of its cells. Row 0 is empty in every published area. Unshifted, 24 published cells at base pumping lie off the published start cells. Moved one row north, none do. <!-- NS §6; studies/neversink/mc_masks.py -->
- **Run order.** The published runs are saved under their run numbers, and the areas follow those file names sorted as text, so run 100 comes before run 10 (1, 10, 100, 101, …). This order predicts the best-matching area for all 60 realisations tested. Runs 0–356 have areas. Run 357, the calibrated (base) realisation, has none. <!-- NS §6; mc_masks.py -->

With both corrected, PRT with the published settings on the rebuilt flow fields matches each paired published area at base pumping. The overlap is 0.989–1.000 (median 0.996, 60 realisations), against a median of 0.75 for the second-best area. <!-- NS §6, §7; scenarios/mechanisms60/mask_matches.csv: baserat median 0.9961, min 0.9886 -->
