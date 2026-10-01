# Bibliography: FlowSource and related methods

Compiled 2026-10-01.

**How to read this file**
- Status codes:
  - **[D]** downloaded, with the local path given;
  - **[W]** web page captured as notes in `references/web/`;
  - **[C]** citation only, with the reason given.
- Plain-text extractions of every downloaded PDF are in `references/docs/text/`. They were made with `pdftotext -layout`.
- IDs such as `[FB13]` are used for cross-referencing from `SUMMARY.md`.

---

## A. Primary FlowSource sources (developer-authored)

**[FB13] Foley, C. & Black, A. (2013).**
- Citation: "Efficiently delineating volumetric capture areas and flow pathways using directed acyclic graphs and MODFLOW; description of the algorithms within FlowSource." In *Proceedings of MODFLOW and More 2013: Translating Science into Practice*, 2–5 June 2013, Golden, CO. IGWMC, Colorado School of Mines, pp. 571–581. The page range is from a secondary citation and is not checked against the proceedings.
- URL: https://groundwater-science.co.uk/wp-content/uploads/2013_FSv6_DAGPaper.pdf
- **[D]** `docs/2013_Foley_Black_FlowSource_DAG_algorithms.pdf`
- Relevance: **the key algorithm paper.**
  - Covers the graph construction, the worked 3x3 example (Figs 5–8), topological sort, cycle handling, dummy nodes, lazy node creation, per-time-step processing and binary-file marshalling.
  - The ptrack README cites the same paper as "Foley and Black, 2017", which looks like a mis-dating.

**[BF13] Black, A. & Foley, C. (2013).**
- Citation: "FlowSource: A program to efficiently delineate volumetric capture areas, pathways and source areas in groundwater models." In *Proceedings of MODFLOW and More 2013*, pp. 652–663. Pages as cited in [MAU21].
- URLs: https://groundwater-science.co.uk/wp-content/uploads/2013_FSv6_ApplicationPaper.pdf ; ResearchGate record https://www.researchgate.net/publication/288981763
- **[D]** `docs/2013_Black_Foley_FlowSource_application.pdf`
- Relevance:
  - Defines the outputs, the aggregate statistics (min/max/mean, ASN, probability within range) and the particle-based travel time.
  - Compares FlowSource with MODALL.
  - Gives five UK case examples.
  - States the version at the time of writing: FlowSourcev5.exe, with v6 in progress.

**[BF13p] Black, A. & Foley, C. (2013).** *FlowSource: A program to efficiently delineate volumetric capture areas, pathways and source areas in groundwater models*, conference poster, MODFLOW and More 2013.
- URL: https://groundwater-science.co.uk/wp-content/uploads/POSTER_FS.pdf
- **[D]** `docs/2013_Black_Foley_FlowSource_poster.pdf`
- Relevance:
  - Condensed version of [BF13] and [FB13], with extra examples: the London Basin fault refinement and a "map of main water users".
  - Gives licence terms: GBP 750 + VAT single seat, via ESI Ltd or Groundwater Science.

**[BFW21] Black, A., Foley, C. & Witterick, W. (2021).** *Advances in capture zone delineation and visualisation: 'FlowSource20' for MODFLOW6*, slide deck (11 slides).
- URL: https://groundwater-science.co.uk/wp-content/uploads/2021_FS20.pdf
- **[D]** `docs/2021_Black_Foley_Witterick_FlowSource20_primer.pdf`
- Relevance:
  - FS20 is the successor to FlowSource v3–v6 (2007–2013).
  - It handles variable-resolution and unstructured meshes and works with MODFLOW 6 and MF-USG; the authors say it could also be used with FEFLOW.
  - Describes forward mode as an "Eulerian transport tool" in which the fraction pathway equals the C/C0 dilution.

**[DAL22] Daley, S., Black, A., Witterick, W., Graham, M. & Foley, C. (2022).** *Going with the flow: Tracking groundwater flow in Modflow 6 and Modflow USG with FlowSource20*, poster, Groundwater Modellers' Forum 2022, Birmingham, UK.
- URL: https://groundwater-science.co.uk/wp-content/uploads/FlowSource.pdf
- **[D]** `docs/2022_Daley_etal_FlowSource20_GWMF_poster.pdf`
- Relevance:
  - FS20 supports triangular, quadtree and Voronoi meshes.
  - Mentions "minor improvements to flow routing methodology, error checking".
  - Shows an SPZ comparison of HCGM (structured) and VGC (Voronoi) models, noting reduced numerical dispersion on the Voronoi grid.
  - Chris Foley's affiliation is now Nice Code Ltd, Glasgow.

**[GWS-web] Groundwater Science Ltd.** FlowSource web page; Innovation page; shop/licence pages.
- URLs: https://groundwater-science.co.uk/flowsource/ , /innovation/ , /shop/
- **[W]** `web/flowsource_homepage.md`, `web/groundwater-science_innovation_and_shop.md`
- Relevance: output definitions (including the Flux variants), the forward/backward modes, supported MODFLOW versions, and current licence prices.

## B. Regulatory guidance and third-party descriptions or applications of FlowSource

**[EA19] Environment Agency (2019).** *Manual for the production of Groundwater Source Protection Zones*. Environment Agency, Bristol, March 2019, 113 pp.
- URL: https://assets.publishing.service.gov.uk/media/5d41a020e5274a0a0bf7757c/Manual-for-the-production-of-Groundwater-Source-Protection-Zones.pdf
- **[D]** `docs/2019_EnvironmentAgency_SPZ_manual.pdf`
- Relevance: **the most detailed independent description of FlowSource practice.**
  - Appendix C4.4, "How Flowsource works": capture fraction, volume from/through, probabilistic outputs, travel time from a single forward particle per cell, kinematic porosity, cut-offs (1–10%), and numerical dispersion.
  - C4.5: access via NGMS and Groundwater Science spreadsheet tools.
  - Case studies 1 (Duxford, Chalk) and 2 (West Cumbria Sandstone, "FlowSource (v 6.13)").

**[EA15] Environment Agency (2015).** *Independent review of the use of FlowSource for Source Protection Zones*. Unpublished Environment Agency report.
- **[C]** Not publicly available; cited in [EA19]. According to [EA19], it found FlowSource "useful for SPZ delineation, and compares well to other codes".
- A useful target for a request to the EA.

**[EA09] Environment Agency (2009).** *Groundwater Source Protection Zones – Review of Methods*. Science Report SC070004/SR1. Withdrawn in 2019.
- URL: https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/822430/WITHDRAWN-Groundwater-Source-Protection-Zones-Review-of-Methods.pdf
- **[D]** `docs/2009_EnvironmentAgency_SPZ_review_of_methods_WITHDRAWN.pdf`
- Relevance: background on SPZ methods and weak sinks. A full-text search found **no mention of FlowSource or MODALL**, which is consistent with FlowSource's adoption being new in [EA19].

**[CHO16] Chowdhury, M.A. (2016).** *Assessing the Connectivity of Groundwater Wells to Surface-Water Using a Volumetric Capture Delineation Tool*. MASc thesis, University of Waterloo (supervisor J.R. Craig), 157 pp.
- URL: http://hdl.handle.net/10012/10981
- **[D]** `docs/2016_Chowdhury_MASc_thesis_FlowSource_connectivity.pdf`
- Relevance: **an independent restatement of the FlowSource algorithm** (§2.4).
  - States that FlowSource reads the DIS, heads/drawdown and CBB files.
  - Explains the fully-mixed-cell assumption as a source of numerical dispersion.
  - Develops a Pollock-based within-cell face-to-face flow-partitioning algorithm to remove it (§3.1–3.4, §4.1.2). This was in MATLAB and was "to be translated" into FlowSource; it is not known whether this happened.
  - Applies FlowSource to well/stream connectivity and Leake-style mapping.

**[MAU21] Maurice, L., Farrant, A.R., Mathewson, E. & Atkinson, T. (2021).** "Karst hydrogeology of the Chalk and implications for groundwater protection." *Geological Society, London, Special Publications* 517, SP517-2020-267.
- DOI: https://doi.org/10.1144/SP517-2020-267 (open access, CC BY 4.0, NORA eprint 531562)
- **[D]** `docs/2021_Maurice_etal_Chalk_karst_groundwater_protection.pdf`
- Relevance: states that most UK SPZs are delineated with MODFLOW, "more recently with the Flowsource adaptation of Black and Foley (2013)". Also discusses the limits of grid-based methods for karst.

## C. Comparable flux-based ("capture fraction") tools

**[POT08] Potter, S.T., Moreno-Barbero, E. & Divine, C.E. (2008).** "MODALL: A practical tool for designing and optimizing capture systems." *Ground Water* 46(2), 335–340.
- DOI: https://doi.org/10.1111/j.1745-6584.2007.00410.x
- **[C]** Paywalled (Wiley).
- Relevance:
  - The closest predecessor to FlowSource.
  - Builds steady-state cell-by-cell flow balances and gives the "capture fraction", the percentage of flow in each cell that comes from a source or goes to a sink. This is equivalent to FlowSource's Fraction Through ([FB13], [BF13]).
  - Was compared with an analytical solution, MODPATH and MT3DMS.
  - Its algorithm details were not seen first-hand.

**[MC09] McLane, C.F. & Cecan, L. (2009).** Comment on "MODALL: A practical tool for designing and optimizing capture systems." *Ground Water* 47(2).
- DOI: https://doi.org/10.1111/j.1745-6584.2008.00527_1.x
- **[C]** Paywalled.
- Relevance (from abstract and search summary): capture-fraction values are flow fractions per cell, not capture probabilities. Their spread is controlled by grid resolution and orientation (numerical dispersion). Cited by [CHO16].

## D. Context: capture, particle tracking, transport-based source tracking

**[BAR18] Barlow, P.M., Leake, S.A. & Fienen, M.N. (2018).** "Capture versus capture zones: Clarifying terminology related to sources of water to wells." *Groundwater* 56(5), 694–704.
- DOI: https://doi.org/10.1111/gwat.12661 ; USGS record https://pubs.usgs.gov/publication/70216327
- **[C]** Marked open access, but the Wiley PDF download returned 403; not downloaded.
- Relevance: separates water-budget "capture" from transport "capture zones". Needed to avoid confusing FlowSource "capture fraction" with Leake-style capture.

**[LEA10] Leake, S.A., Reeves, H.W. & Dickinson, J.E. (2010).** "A new capture fraction method to map how pumpage affects surface water flow." *Ground Water* 48(5), 690–700.
- DOI: https://doi.org/10.1111/j.1745-6584.2010.00701.x
- **[C]** Paywalled.
- Relevance: the "LRD" capture-fraction map, a different concept from FlowSource. [CHO16] compares the two.

**[FIE18] Fienen, M.N., Bradbury, K.R., Kniffin, M. & Barlow, P.M. (2018).** "Depletion mapping and constrained optimization to support managing groundwater extraction." *Groundwater* 56(1), 18–31.
- DOI: https://doi.org/10.1111/gwat.12536
- **[C]** Not downloaded.
- Relevance: context for depletion (capture) mapping. It came up in a FlowSource search, but whether it cites FlowSource was not checked.

**[BED24] Bedekar, V., Neville, C., Tonkin, M.J., Bartlett, R.D. & Plato, P. (2024).** "A unit-concentration method to quantify source contribution." *Groundwater* 62(2), 303–309.
- DOI: https://doi.org/10.1111/gwat.13333
- **[C]** Paywalled.
- Relevance: **the transport-model alternative.** Assign C=1 to the source water of interest and C=0 elsewhere; the resulting concentration is the source fraction. It applies directly to MF6 GWT. Abstract only was seen.

**[PRY22] Pryet, A., Matran, P., Cousquer, Y. & Roubinet, D. (2022).** "Particle tracking as a vulnerability assessment tool for drinking water production." *Frontiers in Earth Science* 10, 975156.
- DOI: https://doi.org/10.3389/feart.2022.975156 (CC BY 4.0)
- **[D]** `docs/2022_Pryet_etal_particle_tracking_vulnerability.pdf`
- Relevance: an MF6 + MODPATH7 particle approach to source apportionment ("TrackTools" Python module). It uses cell budgets for source-cell mixing ratios to handle weak sources. A contrasting particle-based workflow; it does not cite FlowSource.

**[PAR11] Partington, D., Brunner, P., Simmons, C.T., Therrien, R., Werner, A.D., Dandy, G.C. & Maier, H.R. (2011).** "A hydraulic mixing-cell method to quantify the groundwater component of streamflow within spatially distributed fully integrated surface water–groundwater flow models." *Environmental Modelling & Software* 26(7), 886–898.
- DOI: https://doi.org/10.1016/j.envsoft.2011.02.007
- **[C]** Paywalled.
- Relevance: **an independently developed method with the same core assumption** (fully mixed cells, flow-weighted fractions computed from the flow solution only, no transport run). It was implemented in HydroGeoSphere and is solved forward in time, so it is transient-capable.

**[POL88] Pollock, D.W. (1988).** "Semianalytical computation of path lines for finite-difference models." *Ground Water* 26(6), 743–750.
- DOI: https://doi.org/10.1111/j.1745-6584.1988.tb00425.x
- **[C]** Paywalled.
- Relevance: the basis of FlowSource's travel-time particles and of Chowdhury's within-cell flow-partitioning algorithm.

**[POL16] Pollock, D.W. (2016).** *User guide for MODPATH Version 7—A particle-tracking model for MODFLOW*. USGS Open-File Report 2016–1086.
- URL: https://pubs.usgs.gov/of/2016/1086/ofr20161086.pdf
- **[D]** `docs/2016_Pollock_MODPATH7_OFR2016-1086.pdf`
- Relevance: the MF6-compatible particle tracker, including weak-sink options. The comparison method used alongside FlowSource in SPZ work.

**[POL12] Pollock, D.W. (2012).** *User guide for MODPATH version 6*. USGS TM 6-A41.
- **[C]** Cited by [BF13] as the basis of FlowSource travel time. Not downloaded, since MODPATH 7 supersedes it.

**[FRI02] Frind, E.O., Muhammad, D.S. & Molson, J.W. (2002).** "Delineation of three-dimensional well capture zones for complex multi-aquifer systems." *Ground Water* 40(6), 586–598.
- DOI: https://doi.org/10.1111/j.1745-6584.2002.tb02545.x
- **[C]** Context: backward advective–dispersive (capture-probability) approach.

**[NW99] Neupauer, R.M. & Wilson, J.L. (1999).** "Adjoint method for obtaining backward-in-time location and travel time probabilities of a conservative groundwater contaminant." *Water Resources Research* 35(11), 3389–3398.
- DOI: https://doi.org/10.1029/1999WR900190
- **[C]** Context: adjoint/backward transport, the continuum analogue of FlowSource's backward mode.

**[GOO96] Goode, D.J. (1996).** "Direct simulation of groundwater age." *Water Resources Research* 32(2), 289–296.
- DOI: https://doi.org/10.1029/95WR03401
- **[C]** Context: Eulerian age, an alternative to particle travel time.

**[CP06] Cornaton, F. & Perrochet, P. (2006).** "Groundwater age, life expectancy and transit time distributions in advective–dispersive systems: 1. Generalized reservoir theory." *Advances in Water Resources* 29(9), 1267–1291.
- DOI: https://doi.org/10.1016/j.advwatres.2005.10.009
- **[C]** Context: forward age and backward life expectancy, the Eulerian analogues of the forward and backward modes.

## E. MODFLOW 6 implementation references

**[LAN17] Langevin, C.D., Hughes, J.D., Banta, E.R., Niswonger, R.G., Panday, S. & Provost, A.M. (2017).** *Documentation for the MODFLOW 6 Groundwater Flow Model*. USGS TM 6-A55.
- URL: https://pubs.usgs.gov/tm/06/a55/tm6a55.pdf
- **[D]** `docs/2017_Langevin_etal_MF6_GWF_TM6-A55.pdf`
- Relevance: CVFD formulation, connectivity (IA/JA), intercell flow, DISU/DISV, Newton, XT3D.

**[LAN22] Langevin, C.D., Provost, A.M., Panday, S. & Hughes, J.D. (2022).** *Documentation for the MODFLOW 6 Groundwater Transport Model*. USGS TM 6-A61.
- URL: https://pubs.usgs.gov/tm/06/a61/tm6a61.pdf
- **[D]** `docs/2022_Langevin_etal_MF6_GWT_TM6-A61.pdf`
- Relevance:
  - Covers GWT with FMI, which can read a saved GWF budget/head file; SSM source concentrations; the flow-residual correction; and the upstream advection scheme.
  - It states (Abstract; "Limitations" item 10, p. 1–7/1–8) that there is **no single-step steady-state transport option**: the solution must be run in time to steady state.

**[MF6IO] MODFLOW 6 Input/Output guide, binary output section** (`doc/mf6io/framework/binaryoutput.tex`, develop branch).
- URL: https://github.com/MODFLOW-ORG/modflow6/blob/develop/doc/mf6io/framework/binaryoutput.tex
- **[D]** `docs/mf6io_binaryoutput_develop.tex`
- Relevance: the budget-file record definitions (FLOW-JA-FACE, STO-SS/SY, package terms, GWF-GWF exchange flows, DATA-SPDIS/DATA-SAT) and the binary grid file (IA/JA).

**[FLOPY] FloPy documentation:** postprocessing utilities and CellBudgetFile/MfGrdFile readers.
- URL: https://flopy.readthedocs.io/en/latest/source/flopy.utils.postprocessing.html
- **[C]** Online documentation; not downloaded.

**[MF6EX] MODFLOW 6 Examples:** "Capture Fraction Analysis" (ex-gwf-capture).
- URL: https://modflow6-examples.readthedocs.io/en/master/_notebooks/ex-gwf-capture.html
- **[C]** Leake-style capture computed with the MF6 API; a different concept from FlowSource.

**[PTRACK] maseology/ptrack** (Go, GPL-3.0).
- URL: https://github.com/maseology/ptrack
- **[W]** `web/other_web_sources.md`
- Relevance: an MF6-reading particle tracker that lists FlowSource-style tracking as "work in progress". No such code was found in the repo.

## F. Searched but not found or not available
- **No FlowSource user manual, control-file specification, release notes, FAQ or example dataset** is publicly available. The website support forum needs a login.
- The full text of the MODFLOW and More 2013 proceedings volume was not located. Only the two FlowSource papers, hosted by Groundwater Science, were obtained.
- BGS NORA and the Lyell Collection: the only FlowSource mention found was [MAU21]. No BGS-authored FlowSource description was found.
- **Authorship:** there is no evidence that Andrew Hughes, Christopher Jackson or BGS were involved in FlowSource. The developers are Alastair Black (Groundwater Science Ltd) and Christopher Foley (University of Strathclyde, later Nice Code Ltd), with W. Witterick, S. Daley and M. Graham on FS20.
- **Journal articles:** no peer-reviewed journal article describing FlowSource was found. The method descriptions are conference papers, a poster, slides, a regulator manual and a thesis.
