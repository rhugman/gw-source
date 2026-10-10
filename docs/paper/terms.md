# Paper terminology

The single list of terms for the paper, its figures and its supporting information. Readers are groundwater modellers (MODFLOW, MODPATH, PEST users), so terms stay in that field's vocabulary. Each line gives the wording the paper uses and its plain definition. Words in the right-hand column marked "not in text" may appear in code, file names or column names but not in the paper prose.

## Method

| term | wording used in the paper | definition |
|---|---|---|
| full mixing | "full mixing", "full-mixing flow tracing" | Each model cell is treated as fully mixed, so all water leaving a cell carries the same mix of origins. Fractions are computed from the cell-by-cell flows of the flow model. |
| the reference method | "the reference method [FB13]" | The full-mixing method of Foley and Black [FB13, BF13]. Never use the product name. |
| destination, source | "destination", "source" | Destination: the sink term(s) traced to, e.g. the eight priority wells. Source: the source term(s) traced from, e.g. recharge or SFR leakage. |
| backward fraction F | "backward fraction F", "F" | Share of the water leaving a cell that ends up leaving the model through the destination. |
| forward fraction G | "forward fraction G", "G" | Share of the water entering a cell that came from the selected source. |
| cell-to-cell flows | "cell-to-cell flows (FLOW-JA-FACE)" | The intercell flows of the MF6 cell-by-cell budget. Not "edges" in the text. |
| source and sink terms | "source and sink terms" | Every other budget term of a cell (recharge, wells, SFR leakage, CHD, storage), each kept separate. |
| gross accounting | "gross accounting" | Each sink term in a cell takes its share of the cell's total outflow, and the rest passes on to the neighbours. A weak-sink well is credited with its pumping only. The default. |
| net accounting | "net accounting" (not "net mode") | The reference method's bookkeeping: it uses the cell-to-cell flows and each cell's net source (cell-to-cell outflow minus inflow), and fixes a destination cell at F = 1. A weak-sink well is then credited with all the water passing through its cell. |
| weak sink | "weak sink", "weak-sink well" | A cell whose sink term takes only part of the cell's outflow (standard MODPATH usage). |
| cell budget error | "cell budget error r" (r = I − O) | Difference between a cell's total inflow I and total outflow O in the MF6 budget. Reported, never forced to zero. Code and docstrings call it the residual (not in text). |
| closure check | "closure check" (backward, forward) | Backward: the volumes traced from all sources add up to the destination inflow. Forward: the volume from a source traced to all sinks adds up to that source's inflow. Both hold exactly once the cell budget errors are included. Table 2 and Fig. 2 label them "backward closure" and "forward closure". |
| forward–backward check | "forward–backward check" | The volume from a source to a destination is the same whether traced backward from the destination or forward from the source, once the cell budget errors are included. Mathematically a duality identity; Table 2 and Fig. 2 label it "duality" (not in text otherwise). |
| boundary-control check | "boundary-control check" | In every cell with outflow, the backward fractions to all sink terms add up to 1. |
| flow loops | "flow loops" | Groups of cells whose cell-to-cell flows form closed circuits, e.g. with XT3D or where reaches exchange water with aquifer cells in both directions. Not "circulation cells" (that term means Tóthian flow systems). A "closed recirculation loop" is a group of cells with no outflow to any sink or to a cell outside the group; it is found before the solve, given F = 0 and reported (no connections are deleted). Not "cycles" or "strongly connected components" in the text, except once in §5.2. |
| flow order | "solved cell by cell in flow order" | Without flow loops, the system is solved one cell at a time from downstream to upstream (backward) or upstream to downstream (forward). Replaces "topological sweep/substitution" (not in text). |
| block solve | "solved loop by loop in flow order" | With flow loops, each loop is solved as one small block and the blocks in flow order. The one precise phrase, in §5.2 only: "block-triangular sparse LU over the strongly connected components; the matrix is an M-matrix (each cell's outflow shares sum to at most 1), so the factorisation needs no reordering for stability (no pivoting)". |
| mean travel time | "mean travel time (full mixing)" | Mean time from entering a cell to leaving through the destination under full mixing: m / F, where m solves (I − P) m = τ ∘ F (same matrix as F) and τ = V / O is the cell's mean residence time (water volume over outflow). Say "Eulerian" only when contrasting with particle (Lagrangian) times. |
| turnover time | "turnover time" | Σ V F / Q: the volume of water that ends at the destination divided by its inflow. Equals the flow-weighted mean travel time of all water reaching the destination, once the cell budget errors are included. |
| numerical dispersion | "numerical dispersion" | Spreading of the traced area caused by mixing whole cells. The effective dispersion scales with cell size h; the width of the transition band grows as about h^0.5 (DS §4). |
| transition band | "transition band (0.1 < F < 0.9)" | The cells at the edge of a traced area where F is neither near 0 nor near 1. Its width measures numerical dispersion. |
| face-to-face routing | "face-to-face routing" at first use, then "face routing" (the Fig. 3 legend) | Experimental 2D option [CHO16] that routes water between cell faces instead of mixing it across the whole cell; reduces numerical dispersion. |

## Comparison with particle tracking

| term | wording used in the paper | definition |
|---|---|---|
| PRT | "MODFLOW 6 particle tracking (PRT)" at first use, then "PRT" | The MF6 particle-tracking model. |
| published contributing cells | "published contributing cells", "published area" | The 980 cells whose published MODPATH 7 particle ends in a priority well (calibrated model). Replaces "mask" (not in text). |
| published Monte Carlo areas | "published Monte Carlo contributing areas" | The contributing-cell arrays of the published ensemble runs: 357 per scenario (one per realisation; 6 × 357 in all). Replaces "Monte Carlo masks". |
| published probability of contribution | "published probability of contribution" | Share of the 357 published Monte Carlo areas that contain a cell. |
| contributing area (full mixing) | "contributing area", "F > 0.1 area", "F > 0.5 area" | Cells with F above a threshold, or the expected area below. |
| start cells | "start cells", "published start cells" | The uppermost active cells where the published particles start (122,021); the Neversink comparisons are made on them. |
| expected area | "expected area (sum of F)" | Sum of F over the start cells, in cells. For particles: the particle weight reaching the wells, in cells, or the number of particles reaching the wells. |
| area-matched | "area-matched" | The same number of cells as the published area, taken in decreasing order of F. |
| core, envelope | "core (F > 0.5)", "envelope (F ≥ 0.1)" | The F > 0.5 area approximates the advective zone; the F ≥ 0.1 area is meant as a conservative outer limit. Keep each threshold as its source uses it: strict (F > 0.1, F > 0.5) for Neversink (NS), F ≥ 0.1 and F ≥ 0.5 for the dispersion tests (DS); say so once in the text. |
| overlap | "overlap" | Cells in both areas as a share of cells in either. Define it in the abstract and at first use in the body (§5.5), where the name "Jaccard index" may be given once in parentheses; figure captions repeat the short definition. 1 means identical areas, 0 no common cells. Always give the value. |
| reference | "reference" | A delineation taken as correct for the comparison: the analytical zone, or fine-grid PRT, in the dispersion tests. Not "ground truth". |
| benchmark | "benchmark" | The published Neversink MODPATH 7 contributing areas. A benchmark, not a reference: it is one particle convention. |
| flow-weighted release | "flow-weighted release" (not "flux-weighted") | Particles released from every source term, each carrying a weight proportional to that term's flow. |
| weight-losing particles | "weight-losing particles" | Particles that carry a share of the flow and, in every cell they pass, lose weight to each sink in proportion to the flow that sink takes from the cell's outflow. The particle analogue of gross accounting. Code and NS call this "thinning" (not in text). |
| plain particles | "plain particles" | Particles that lose weight only to the destination wells and pass all other sinks with full weight, so water that streams and other sinks take on the way is counted as reaching the wells. |
| P | "particle share P" | Flow-weighted share of the water released in a cell that particles deliver to the wells. |
| release-point error | "release-point error" | Error from representing each source term by a finite number of release points; use for the synthetic models (Fig. 2). Do not use it for the +1.8 % on Neversink, which NS §3 finds not systematic (0.0 to +1.8 % over five release layouts, no trend in the number of particles). Replaces "quadrature error" (not in text). |
| published conventions | "the published particle conventions" | One particle at the centre of each uppermost active cell; recharge and stream flows on the top face where it is open; particles stopped at every weak sink; particles in dry start cells draped; dry cells treated as inactive, so particles that reach a side face next to a dry cell stop there (1,139 particles, NS §2). PRT copies all but the last, which accounts for nearly all of the 1 % of end cells that still differ. |
| IFLOWFACE | "IFLOWFACE (the cell face a boundary flow is assigned to)" | MF6 auxiliary variable read by PRT; −1 puts recharge or stream flow on the top face instead of spreading it through the cell. |
| draping | "draping (MODPATH DrapeOption)" | A particle that starts in a dry cell is moved down to the first active cell below, at the same local position. |
| stopping at weak sinks | "stopped at every weak sink" | The MODPATH weak-sink option: a particle ends in the first weak-sink cell it enters, and its whole weight is credited to that cell's sink. |
| buried stream cells | "buried stream cells" | SFR reach cells with an active cell above. The stream exchange stays distributed in the cell; where the reach gains from the aquifer it is a sink (usually weak) and stops particles under the published conventions. Open-top stream cells instead let particles leave through the top face. |

## Streams

| term | wording used in the paper | definition |
|---|---|---|
| streams as cells | "streams as cells" | SFR leakage is a source term of the aquifer cell; tracing stops at the stream, and the stream share is reported as SFR leakage. |
| stream network | "stream network" | The SFR reaches (12,316 on Neversink) are added to the traced system as extra cells linked by stream routing, so stream leakage is traced up the stream to where its water entered. Replaces "reaches as graph nodes" (not in text). |
| stream share | "stream share" | Share of the wells' water that enters as SFR leakage (streams as cells). |

## Capture wording

| term | wording used in the paper | definition |
|---|---|---|
| capture fraction | not used for F | Reserved for the budget sense [LEA10, BAR18]: the share of a well's pumping supplied by increased recharge or reduced discharge (for example streamflow depletion). |
| captured | avoid; prefer "reaching the wells" | "Captured recharge" → "recharge reaching the wells"; "captured flow" → "flow reaching the wells"; "fully captured" → "F = 1". "Capture zone" for a well's zone of contribution is standard and may stay. |

## Words not used in the paper prose

Jaccard (except once at the definition of overlap), graph, node, edge, adjoint (except once, naming the backward-in-time methods [NW99] in §5.1), duality (except once at the forward–backward check, and as the Table 2 / Fig. 2 label), topological, pivoting (except once in §5.2), out-normalised, mask, thinning/thinned, flux-weighted, net mode, circulation cells (for flow loops), captured (see above), ground truth, quadrature, residual (use cell budget error), pipeline, robust, leverage, plumbing, first-class, out of the box, under the hood.
