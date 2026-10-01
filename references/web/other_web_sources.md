# Other web sources consulted (notes)

Accessed: 2026-10-01

## UWSpace record: Chowdhury (2016) MASc thesis
- URL: https://uwspace.uwaterloo.ca/items/aa5faa79-52f2-4075-bcc3-38e215385595 (handle http://hdl.handle.net/10012/10981)
- PDF bitstream: https://uwspace.uwaterloo.ca/bitstreams/db44651b-9713-4e39-8afc-08204c2ee639/download
  - The front-end URL serves a bot-check page. The download was taken from the repository's own 302 redirect target, a DSpace API URL. Local copy: `docs/2016_Chowdhury_MASc_thesis_FlowSource_connectivity.pdf`.
- Supervisor: Dr James Craig (University of Waterloo). The acknowledgements thank Alastair Black and Chris Foley (Groundwater Science) for answering questions and collaborating.

## GitHub: maseology/ptrack (Go, GPL-3.0)
- URL: https://github.com/maseology/ptrack (last push 2026-04-21 per GitHub API)
- The README describes it as a "generalized particle tracking and flux-field analysis suite" that reads MODFLOW 6 output.
- Its "work in progress" list includes "FlowSource volumetric flow tracking (Foley and Black, 2017)". The same paper is dated 2013 in all other sources.
- Grep of the repo found no FlowSource-like flux-tracking code (files: Pollock, Waterloo, Euler/RK, mf6.go, flx.go, ...). It is a possible open-source reference for reading MF6 output in Go, nothing more.

## Groundwater Modellers' Forum 2022 (UK)
- Programme PDF: https://www.hydrogroup.org.uk/wp-content/uploads/2022/09/GWMF2022_programme.pdf (download blocked, HTTP 403/HTML). Details below are from a search-engine summary.
- Modellers' Fair item: "Going with the Flow: Tracking groundwater flow in MODFLOW6 and MODFLOW USG with FlowSource", presented by Stuart Daley (Groundwater Science), 6 Oct 2022, Birmingham. The poster is `docs/2022_Daley_etal_FlowSource20_GWMF_poster.pdf`.

## ResearchGate
- Black & Foley (2013) record: https://www.researchgate.net/publication/288981763 (not fetched; ResearchGate blocks automated fetches).
- Alastair Black profile: https://www.researchgate.net/profile/Alastair-Black (not fetched).

## MODFLOW 6 docs (budget-file format)
- `doc/mf6io/framework/binaryoutput.tex` (develop branch), fetched from https://raw.githubusercontent.com/MODFLOW-ORG/modflow6/develop/doc/mf6io/framework/binaryoutput.tex. Local copy: `docs/mf6io_binaryoutput_develop.tex`.
- It documents:
  - FLOW-JA-FACE (IMETH=1, size NJA, aligned with the binary-grid JA array; zero in each cell's diagonal position);
  - storage terms STO-SS/STO-SY (IMETH=1);
  - stress/advanced package terms (IMETH=6 lists with ID1 = cell, ID2 = bound number);
  - GWF-GWF exchange flows, written as FLOW-JA-FACE with IMETH=6, where TXT2ID1 is the exchange name and ID2 is the node in the connected model;
  - DATA-SPDIS and DATA-SAT.
- The latest MF6 release is 6.8.1 (GitHub API). mf6io.pdf ships inside the executable zip archives, which were not downloaded.

## FloPy / MF6 examples (not downloaded; for the implementation step)
- flopy.utils.postprocessing (e.g. `get_structured_faceflows`, `get_specific_discharge`, `get_residuals`): https://flopy.readthedocs.io/en/latest/source/flopy.utils.postprocessing.html
- "Capture Fraction Analysis" MF6 example: https://modflow6-examples.readthedocs.io/en/master/_notebooks/ex-gwf-capture.html
  - Note: this is Leake et al. (2010)-style *capture*, i.e. the change in boundary flows caused by pumping, computed with the MF6 API. It is not FlowSource-style flow tracing.
