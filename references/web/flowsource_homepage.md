# FlowSource product page (Groundwater Science Ltd)

- Source URL: https://groundwater-science.co.uk/flowsource/
- Accessed: 2026-10-01
- Note: these are notes and short excerpts of the technical content, not a full copy of the page. The site returns HTTP 403 to non-browser user agents. A normal browser User-Agent string works.

## Overview (paraphrased)
- FlowSource is described as a "volumetric tracking tool for MODFLOW groundwater models".
- It has two modes:
  - **Backwards** mode: shows where water comes from (provenance). It is used to measure and map groundwater catchments, typically for wells.
  - **Forwards** mode: shows where water goes (fate). It is described as "a simple and intuitive contaminant tracking tool".
- Named outputs:
  - "Fractional Flow Through" and "Volume Flow Through" (the pathway);
  - "Fraction Flow From/To" and "Volume Flow From/To" (the original source, or the final destination in forward mode).
- The page says it is used extensively in the UK to delineate Source Protection Zones (SPZs) and to support conceptual-model review. Elsewhere it is used for wellhead protection and contaminant-plume scoping.

## Related downloads (all PDFs, all saved in `references/docs/`)
| Link text on page | URL | Local copy |
|---|---|---|
| FSv6 Application Paper | /wp-content/uploads/2013_FSv6_ApplicationPaper.pdf | docs/2013_Black_Foley_FlowSource_application.pdf |
| FSv6 Internal Workings Paper | /wp-content/uploads/2013_FSv6_DAGPaper.pdf | docs/2013_Foley_Black_FlowSource_DAG_algorithms.pdf |
| 2021 FlowSource20 Primer | /wp-content/uploads/2021_FS20.pdf | docs/2021_Black_Foley_Witterick_FlowSource20_primer.pdf |
| 2013 FSv6 Poster | /wp-content/uploads/POSTER_FS.pdf | docs/2013_Black_Foley_FlowSource_poster.pdf |
| 2022 FlowSource GWMF | /wp-content/uploads/FlowSource.pdf | docs/2022_Daley_etal_FlowSource20_GWMF_poster.pdf |

The page describes these downloads as follows (paraphrased):
- The 2013 papers are "the initial publications developed for the MODFLOW 1996 and SURFACT predecessor code", plus the US MODFLOW and More conference poster.
- The FS20 slideshow covers "FS20 ... for current MODFLOW 6 and USG models".

## Features (technical content, condensed)
- Inputs: "FlowSourcev6 and FlowSource20 require the standard cell-by-cell flow MODFLOW output file and instructions from the user on where and when to track flows from or to". The user also chooses forward or backward tracking.
- The page describes backward (capture) mode only. It states that "Forward tracking would be the opposite."
- PATHWAY outputs:
  - **Fractional Flow Through**: the proportion of water passing through each cell that becomes abstracted [%].
  - **Flux Flow Through**: the pathway normalised by cell area [m/d]. The page says this helps in variable-resolution models.
  - **Volume Flow Through**: the volumetric pathway [m3/d].
- SOURCE outputs (Destination outputs in forward mode):
  - **Fractional Flow From**: the proportion of the abstracted water that entered the model at a given cell, e.g. from recharge or stream leakage [%].
  - **Flux Flow From**: the area-normalised source [m/d].
  - **Volume Flow From**: the volumetric source zone [m3/d]. The page says "The sum of this dataset is the abstraction rate."

## Typical applications (condensed)
- Capture zones of wells (SPZ / wellhead protection).
- Capture zones of any group of cells. Applied to a river reach, this gives a volumetric groundwater capture zone for the river.
- Running FlowSource once per boundary condition and combining the results in GIS. This shows which boundaries control flow in each part of the model, and by how much.
- Wellfield optimisation (interference and capture overlap).
- Pump-and-treat design, using both modes.
- Forward mode as a "conservative advective transport tool":
  - The page says it is faster and easier to set up than full fate-and-transport modelling, but limited to conservative, advective transport.
  - "Volume To" gives the final destination of the tracked water.
  - "Fraction To" accounts for dilution by regional freshwater flow.
