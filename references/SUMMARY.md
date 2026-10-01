# FlowSource: technical summary for a MODFLOW 6 reimplementation

Compiled 2026-10-01.

**How to read this document**
- Citations in square brackets, such as [FB13], refer to entries in [`bibliography.md`](bibliography.md). Local PDFs are in [`docs/`](docs/); their text extractions are in [`docs/text/`](docs/text/). Web-page notes are in [`web/`](web/).
- Substantive statements are labelled:
  - **(source)**: stated by the cited source;
  - **(inferred)**: our own derivation or interpretation, not stated in any source;
  - **(unverified)**: plausible, but no source was found.

## 1. What FlowSource is

**Definition (source)**
- FlowSource is a **post-processor for MODFLOW cell-by-cell flow output**. It calculates "the volume and proportion of water in every groundwater model cell that ultimately reaches a predefined destination" [FB13, BF13].
- The destination is a user-defined set of cells (one or many, not necessarily adjacent).
- It traces flow by **graph traversal of the intercell flows**. It does not use particle tracking or a transport solution, except for an optional particle-based travel-time feature [FB13, BF13, CHO16].

**Modes (source)** [GWS-web, BFW21]
- **Backward ("capture")**: provenance of water reaching the destination, e.g. SPZs and well or river catchments.
- **Forward**: fate of water leaving a source, e.g. advective, conservative plume scoping. FS20 calls forward mode an "Eulerian transport tool" in which the pathway fraction is a dilution ratio C/C0.

**Developers (source)**
- Alastair Black (Groundwater Science Ltd, Shrewsbury) and Christopher Foley (Dept. of Computer & Information Sciences, University of Strathclyde; by 2022 at Nice Code Ltd, Glasgow) [FB13, BF13, DAL22].
- FlowSource20 adds Will Witterick, Stuart Daley and Mal Graham (Groundwater Science) [BFW21, DAL22].
- Beta-testing and feedback are acknowledged from the Environment Agency, AMEC E&I UK, ESI Ltd and Mott MacDonald [FB13, BF13].

**History and versions (source unless marked)**

| Version | Date | Notes |
|---|---|---|
| FlowSource v3–v6 | 2007–2013 [DAL22, BFW21] | Built for MODFLOW-96 and a "SURFACT predecessor code" [GWS-web]. |
| FlowSourcev5.exe | 2013 [BF13] | Current at time of writing. v6 "in progress" to add coupled surface-water graphs and readers for other simulators. |
| v6.13 | c. 2015–2019 | Used in the EA West Cumbria SPZ case study [EA19, App. D case study 2]. |
| FlowSource20 ("FS20") | c. 2020–2021 | Supports MODFLOW 6 and MODFLOW-USG, including triangular, quadtree and Voronoi meshes; "minor improvements to flow routing methodology, error checking" [BFW21, DAL22]. Website claims compatibility with "all major versions since 1996 spanning to present MODFLOW6" [GWS-web]. |

**Implementation and licensing (source)**
- Written in VB.NET [FB13]. In 2013: available on request, with source code available for academic use on request [FB13, BF13].
- Now sold commercially: GBP 1,000 node-locked, GBP 3,000 dongle, GBP 3,000 VM/shared licence [GWS-web, accessed 2026-10-01]. In 2013 it was GBP 750 + VAT per seat [BF13p].
- No public manual, control-file specification or test dataset was found (§8).

**Regulatory status (source)**
- The Environment Agency (England) SPZ manual recommends FlowSource alongside MODPATH for numerical SPZ delineation, following an independent review (EA 2015, unpublished) which found it useful for SPZ delineation and comparing well to other codes [EA19 §C4.4].
- FlowSource is also available inside the EA's National Groundwater Modelling System (NGMS), limited to three stress periods and with no travel time [EA19 §C4.5].
- Maurice et al. (2021) state that most UK SPZs are now delineated using MODFLOW, more recently with the FlowSource adaptation of Black and Foley (2013) [MAU21].

**Close relative (source)**
- MODALL [POT08] computes a steady-state "capture fraction" from cell-by-cell flow balances. FlowSource's developers say this is equivalent to FlowSource's Fractional Flow Through, and MODALL was used to validate FlowSource [FB13, BF13].
- FlowSource adds transient (time-step-by-time-step) processing, volumetric outputs, statistics, a DAG/topological-sort algorithm, and cycle handling [BF13, CHO16].

## 2. The algorithm

### 2.1 Data model: a directed, weighted flow graph (source)

[FB13] (restated in [CHO16 §2.4.1]) builds the graph as follows:
- **Nodes** are model cells.
- **Edges** are intercell flows, directed in the direction of flow and weighted by flow magnitude. All weights are positive; direction is carried by the edge, not by sign. One edge per connection with non-zero flow.
- **Dummy nodes** are added in two places:
  1. *Destination out-edges*: every out-edge of a destination cell is re-attached to start from a dummy node. Nothing downstream of a destination is counted, and the sort has a valid start. Destination cells are therefore **absorbing**.
  2. *Cell mass balance*: dummy nodes "balance the mass transfer in a cell", representing water added to or removed from the cell. These simplify the volume-from calculation.
- **Lazy node creation**: nodes are created only when reached by upstream traversal from the destination; cells outside the capture area are never touched. With multiple time steps, nodes are reused and edges rebuilt each step [FB13].
- The approach is **geometry-agnostic**, applying to MODFLOW-USG and even finite-element meshes [FB13]. FS20 realises this for MF6/USG unstructured grids [DAL22].

### 2.2 Notation (inferred formalisation of [FB13]'s worked example)

For one time step:
- $q_{ij} \ge 0$: intercell flow from cell $i$ to neighbour $j$ (from FLOW-JA-FACE, or FRF/FFF/FLF in older MODFLOW).
- $I_i=\sum_k q_{ki}$: total intercell inflow to $i$.
- $O_i=\sum_j q_{ij}$: total intercell outflow from $i$.
- $s_i = O_i - I_i$: **net external exchange** (recharge, boundary conditions, storage, wells, ...). $s_i>0$ is a net source; $s_i<0$ a net sink. [FB13]: "When the volume of water exiting a cell exceeds the volume entering, it implies that this excess water was stored [i.e. originated] in the cell."
- $T_i = I_i + \max(s_i,0) = O_i + \max(-s_i,0)$: **throughflow** of cell $i$.
- $\mathcal{D}$: the set of destination cells.

### 2.3 Backward (capture) mode

**Fraction through** (capture fraction, "Fractional Flow Through"):

$$
f_d = 1 \quad (d\in\mathcal{D}),\qquad
f_i = \frac{1}{T_i}\sum_{j:\,q_{ij}>0} q_{ij}\, f_j \quad (i\notin\mathcal{D})
$$

- Flow leaving the model at $i$ (the net-sink part $\max(-s_i,0)$), or across the model edge, goes to a dummy node with $f=0$.
- **(inferred)** The equation is not written in any source. It is the rule that reproduces every number in [FB13]'s worked example (Figs 5–8), and matches its prose: all water starting in or passing through a destination cell reaches the destination; divergent cells combine downstream contributions in proportion to flow; each cell is computed from its immediate downstream neighbours.

**Volume through** ("Volume Flow Through", m³/d):

$$V^{\text{thr}}_i = f_i\,T_i$$

**Volume from** ("Volume Flow From", m³/d): the part of the cell's own net source that reaches $\mathcal{D}$.

$$V^{\text{from}}_i = f_i\,\max(s_i,0)$$

- [FB13]: the excess of outflow over inflow "is multiplied by the fractional volume through to determine the volume of water originating in each cell that arrives in the destination cell". If the cell is balanced or a net sink, volume from is zero.

**Fraction from** ("Fractional Flow From") — two definitions in the sources:
- **2013** [FB13/BF13 Fig. 4 caption]: percentage of water input to each cell (e.g. from boundary conditions) that is ultimately extracted at the abstraction cell, i.e. $f_i$ restricted to net-source cells.
- **Website and FS20** [GWS-web, BFW21, DAL22]: proportion of abstracted water that entered the model at a given cell, summing to 100%, i.e. $V^{\text{from}}_i/\sum_k V^{\text{from}}_k$.
- **(inferred)** The definition seems to have changed between versions. A reimplementation should output both, under distinct names.

**Flux variants** (FS20 / website): "Flux Flow Through" and "Flux Flow From" are the volumes divided by cell plan area (m/d), intended for variable-resolution grids [GWS-web].

**Source breakdown by process**
- [FB13]: if other MODFLOW budget terms are included, the volume from recharge, storage release and each boundary condition can be computed. [EA19 Fig C.6]: storage release contributes to Volume From.
- **(unverified)** How a cell's net source is split between several inflow processes is undocumented. Pro-rata by each process's share of gross inflow is the natural reading.

**Closure property (inferred)**
- Flow is conserved over the DAG, so $\sum_i V^{\text{from}}_i = \sum_{d\in\mathcal D} T_d$ (all water entering the destination cells).
- This equals the abstraction rate only when each destination cell is a **strong sink**. How FS20 treats weak-sink destinations is undocumented (§8).

**Worked example from [FB13] (source numbers, checked against the formulas)**
- 3×3 grid, cells A–I, destination A.
- Flows: B→A 5, D→A 5; C→B 5, E→B 5, B sends 5 out of the pictured area; E→D 5; C→F 5; F→E 8, I→F 1; H→E 2; C receives 10 from outside.
- Results:
  - $f$: A 100%, D 100%, B 50%, E 75%, F 75%, H 75%, I 75%, C 62.5%, G 0%. E.g. $f_C = (5\cdot0.5 + 5\cdot0.75)/10$.
  - $V^{\text{thr}}$: A 10, B 5, C 6.25, D 5, E 7.5, F 6, H 1.5, I 0.75.
  - $V^{\text{from}}$: F 1.5 (net source 2 × 0.75), H 1.5, I 0.75 (printed "0.7"); all others 0.
- One label in Fig. 5 is ambiguous (an arrow on C's right face labelled −10); the text implies C's throughflow is 10, which was used.

### 2.4 Forward (fate / destination) mode

**Sources:** the website says only that forward tracking "would be the opposite" [GWS-web]. Forward outputs are "Fraction Flow To" and "Volume Flow To": Volume To is the loading on the final destination (rivers, wells); Fraction To accounts for dilution by regional water [GWS-web]. FS20 equates the pathway fraction with $C/C_0$ [BFW21, DAL22].

**(inferred) Formulation** — the same recursion on the reversed graph, normalised by throughflow. For source set $\mathcal S$:

$$
g_s = 1\ (s\in\mathcal S),\qquad g_i=\frac{1}{T_i}\sum_{k:\,q_{ki}>0} q_{ki}\,g_k,\qquad
V^{\text{to}}_i = g_i\max(-s_i,0)
$$

- $g_i$ is the fraction of water passing through $i$ that originated in $\mathcal S$, i.e. $C/C_0$. This is the steady-state, dispersion-free, upstream-weighted **mixing-cell** concentration for unit source concentration (§5.2).

**(inferred) Duality check:** total flow from $\mathcal S$ to $\mathcal D$ must agree between modes — $\sum_{i\in\mathcal S} V^{\text{from}}_i$ (backward on $\mathcal D$) $= \sum_{i\in\mathcal D} V^{\text{to}}_i$ (forward on $\mathcal S$). Useful as an implementation test.

### 2.5 Core assumption: fully mixed cells

**Sources:**
- Water passing through a cell leaves through its out-faces **in proportion to the out-face flows**, regardless of entry face ("complete mixing") [CHO16 §2.4.3].
- Consequences: grid-size-dependent **numerical dispersion** (lateral spreading of capture fractions; peripheral cells included whose streamlines never reach the destination) [CHO16, EA19 §C4.4, MC09 for MODALL]; zones "much wider" than older particle-based zones [EA19]; poor definition of small zones (SPZ1/SPZ2), so EA pairs FlowSource with MODPATH [EA19].
- FS20 claims reduced numerical dispersion on Voronoi grids [DAL22].

**Chowdhury's proposed fix** [CHO16]
- Partition each rectilinear cell's inflow faces to outflow faces using Pollock's semi-analytical velocity field (mass balance or analytic streamtube reconstruction), then route face-to-face instead of fully mixing. In a planar 3×3 test, peripheral cells changed from small non-zero fractions to 0%.
- Limits: rectilinear cells only, no internal sources/sinks (no weak sinks), small correction for zero-velocity-gradient cases. Written in MATLAB for translation into FlowSource. **Whether FS20 includes it is unknown** (§8).

### 2.6 Numerical solution: DAG + topological sort (source)

**Three stages** [FB13]: (1) build the graph; (2) topologically sort it; (3) one arithmetic pass in reverse flow order from the destinations upstream, so every downstream $f_j$ is known before $f_i$. The DAG replaced slower, memory-hungry recursive scans of earlier versions.

**Cycle handling** [FB13, BF13, CHO16]
- Cycles ("water flowing uphill") are attributed to model flaws: unstable or unconverged multilayer models, flows below convergence tolerance.
- FlowSource detects cycles during traversal and **removes the lowest-volume edge in each cycle**, repeating until acyclic. The choice of edge is called an open research question; cycles tend to appear as networks, not single loops.
- Cycle locations are worth reporting as a model diagnostic.

**Performance** [FB13]: ~4×10⁶ active nodes, one abstraction: <0.5 s per stress period on a laptop (~80% file I/O). ~150,000 destination cells together: up to ~30 s per stress period.

**Binary I/O** [FB13]: raw bytes marshalled directly into float arrays; the paper notes CBC binary layout depends on the Fortran compiler.

**(inferred) Linear-algebra view**
- The recursion is $(\mathbf I-\mathbf P)\mathbf f=\mathbf b$, with $P_{ij}=q_{ij}/T_i$ for $i\notin\mathcal D$, zero rows for $d\in\mathcal D$, $b_d=1$, other $b=0$.
- On a DAG, $\mathbf P$ is permutation-triangular and the topological sort is forward substitution, $O(N+E)$.
- With cycles, if every cell eventually drains to a sink, $\mathbf P$ is substochastic (spectral radius < 1) and the system still has a unique solution via sparse direct or iterative solve. Cycle-breaking then becomes optional — a mixing-cell solution with recirculation. [FB13] calls the cyclic result "ill-defined", but under full mixing it is mathematically well-defined.
- Design choice: keep FlowSource-compatible edge removal for regression; offer the linear solve as the robust option.

**(inferred) Cheap topological order for two-point-flux models**
- With standard two-point (conductance) flux, $q_{ij}>0 \iff h_i>h_j$, so **sorting by head is a valid topological order** and cycles cannot occur.
- Cycles can only come from non-TPFA terms (MF6 XT3D cross-terms, MF-USG ghost-node correction), vertical-flow corrections not following the head gradient, precision mismatch between flows and heads, or multi-model/exchange inconsistencies.

### 2.7 Transient models (source)

- Each time step (or a selected subset) is processed **independently as a "time-instant steady state"** (Rushton 2003) [FB13, BF13, CHO16]. No carry-over of tracked water between steps; this is **not transient transport**.
- Storage release acts as a source and enters Volume From [EA19 Fig C.6]. **(inferred)** Water into storage is a sink with $f=0$.
- **Aggregate statistics** over time steps [FB13, BF13, EA19]:
  - minimum, maximum and mean ("long-term average", LTA) of each metric;
  - **ASN (always/sometimes/never)**: 1 if a cell contributes more than a set minimum volume in every analysed step, 0.5 if sometimes, 0 if never;
  - **probability within range**: fraction of steps in which a metric is within a range (EA practice: proportion of time that Volume Through to the abstraction is >1 m³/d);
  - travel-time statistics (§2.8).
- EA practice applies 1–10% capture-fraction cut-offs to suppress numerical noise [EA19 §C4.4, C5].

### 2.8 Travel time (source)

- The **only particle-based component**: MODPATH-like (Pollock), "heavily based on MODPATH 6 with minor modifications", designed to match MODPATH [BF13, BF13p, EA19].
- Particles are placed automatically only in cells already contributing to the destination: cell centre; centre plus face centres; or centre plus corners.
- Particles are tracked **forward** through each time step's steady field until captured; the travel time is assigned to the starting cell (EA: travel time to the edge of the abstraction cell).
- Requires porosity (EA uses 1% for the Chalk) [EA19].
- Outputs: travel time per cell; e.g. percentage of time steps a cell lies within the 50-day or 400-day envelope [EA19].
- Unknown whether FS20 supports travel time on unstructured grids (§8).

### 2.9 Inputs and outputs

**Inputs (source):** the MODFLOW cell-by-cell budget file plus a user control file setting destination/source cells, time steps, mode, metrics and options [GWS-web, BF13]. [CHO16] lists DIS, heads and CBB as inputs. Porosity for travel time [BF13]. [EA19]: EA tools do not work with the EA's non-drying MODFLOW variant.

**Outputs (source):** gridded datasets per cell/layer and time step, or aggregated over time — Fraction/Flux/Volume Flow Through; Fraction/Flux/Volume Flow From (or To); min/max/mean, ASN, probability within range; travel time. Delivered in formats for common analysis/GIS tools, usually viewed as rasters [BF13, EA19]. Exact formats are not public.

**Supported codes and grids (source)**

| Code | Status | Sources |
|---|---|---|
| MODFLOW-96 | Original target | [FB13, BF13] |
| A "SURFACT predecessor" | Supported early on | [GWS-web] |
| "All major versions since 1996" | Claimed | [GWS-web] |
| MODFLOW-USG | Supported in FS20 | [BFW21, DAL22] |
| MODFLOW 6 (structured, quadtree, Voronoi, triangular) | Supported in FS20 | [BFW21, DAL22] |
| FEFLOW | "could be used with" — not stated as implemented | [BFW21, DAL22] |

Support for MF6 GWF-GWF exchanges, MVR, and SFR/LAK/MAW/UZF routing is **not documented** (§8).

## 3. Applications and case studies

**[BF13] / [BF13p]** (UK, MODFLOW-96-era regional models)
1. Three wellfields, 1971–2004 (ESI): "Flow From" source zones migrate as competing abstractions develop; used for diffuse-pollution catchment management.
2. Confined Chalk abstraction (AMEC): LTA Flow Through and Flow From over 1970–2010 show a source zone dislocated from the well (vertical leakage plus unconfined outcrop); compared with MODPATH.
3. SPZs in high-transmissivity aquifers (AMEC): FlowSource volumes alongside MODPATH back-tracks; "Flow From" cut off at >1% of abstraction.
4. River groundwater catchment (Mott MacDonald): all stream and abstraction cells in a catchment as destinations; Max Flow Through 1970–2007 used to size an MT3D sub-model.
5. Boundary control mapping (Groundwater Science): Fraction Through to GHB, STR, WEL and adjacent layers in a ~4M-node model with ~150k destination cells; the four maps sum to 1 in every cell.
6. London Basin model: fault parameterisation changes the simulated provenance of central London abstractions [BF13p].
7. "Map of main water users": the dominant destination (>50%) per cell [BF13p].

**EA SPZ practice** [EA19 App. C4, App. D]
- **Duxford** (Cam & Bedfordshire Ouse Chalk model, 250 m cells): proportion of time with travel time ≤50 d and ≤400 d; travel time; Volume From and Volume Through for dry, wet and average stress periods; proportion of time with Volume Through >1 m³/d. Used with MODPATH and manual "nudging".
- **West Cumbria Sandstone**: purpose-built 20 m-cell model (partly to reduce numerical dispersion); three fault conceptualisations; monthly stress periods 1965–2011; FlowSource v6.13 and MODPATH for SPZ1–3.

**Academic** [CHO16]: synthetic MODFLOW-2000 models; screening wells drawing mostly on surface water (GUDI); Leake-style maps of volumetric stream capture vs well location and time; effects on existing wells and hyporheic flow; comparison with Leake et al. (2010).

**Other claimed uses (no published detail)** [FB13, BF13, GWS-web, BFW21]: pump-and-treat optimisation, mine pit-slope depressurisation, groundwater-divide mapping, wellfield interference, mining contaminant leakage. Mining and pump-and-treat examples are confidential [BF13].

## 4. Strengths and limitations

**vs particle tracking (MODPATH)**
- **+** Volume-weighted: avoids massless-particle capture "tails" carrying sub-precision flow; fills gaps between diverging back-tracks [BF13, EA19].
- **+** Weak sinks/sources handled naturally by fractions [EA19 §A; inferred for FlowSource]; backward analysis of transient models is easy (awkward with MODPATH) [EA19]; whole-model analyses with thousands of destinations [BF13].
- **−** No time information without particles [BF13].
- **−** Numerical dispersion from full mixing: wider zones, small zones poorly defined [CHO16, EA19, MC09].
- **−** Transient results are a sequence of snapshots, not transient transport [FB13].

**vs solute transport (MT3D / MF6 GWT)**
- **+** Seconds per stress period; no dispersivity, porosity (for main metrics) or transport time stepping; thousands of destinations in one pass [FB13, BF13].
- **−** Conservative, advective, fully mixed only: no dispersion, reactions or storage lag [GWS-web].
- **(inferred)** For steady flow, forward fractions equal a steady-state, upstream-weighted, dispersion-free unit-concentration transport solution (subject to the net/gross caveat in §5.2). Its numerical dispersion is first-order upwind numerical dispersion.

**Model-quality sensitivity (source):** cycles and uphill flows come from unconverged or unstable models [FB13]. LTA outputs can expose odd model behaviour (e.g. a river drying in a few time steps) [EA19].

## 5. Related and alternative methods

### 5.1 Flux-based capture-fraction and mixing-cell methods
- **MODALL** [POT08]: steady-state cell-balance capture fraction, equivalent to Fraction Through; grid-dependence critiqued in [MC09].
- **Hydraulic mixing-cell (HMC)** [PAR11]: same full-mixing assumption applied to integrated SW/GW flow (HydroGeoSphere); **steps forward in time** — a transient-capable analogue of forward mode.
- **Chowdhury (2016) face-to-face partitioning** [CHO16]: dispersion fix for rectilinear grids (§2.5).

### 5.2 Transport-based alternatives
- **Unit-concentration method** [BED24]: C=1 for the tagged source water, 0 elsewhere; concentration = source fraction. Works with MT3D or MF6 GWT.
- **(inferred) Correspondence with forward mode.** Steady MF6 GWT with upstream advection, no dispersion, and SSM concentration 1 on tagged sources has cell balance

$$C_n\,(O_n+B^-_n)=\sum_m q_{mn}C_m + B^{+,\text{tagged}}_n,$$

  where $B^\pm$ are **gross** boundary/storage inflows and outflows. FlowSource's (apparently) **net** $s_i$ differs whenever a cell has both sources and sinks (e.g. recharge plus a drain). Net vs gross is a design decision (§6).
- **Backward/adjoint transport** [NW99, FRI02] and **life expectancy** [CP06] are continuum analogues of backward mode; **Eulerian age** [GOO96] is an alternative to particle travel times.

### 5.3 Particle approaches
- MODPATH 7 [POL16] and the MF6 PRT model handle weak sinks/sources with user options.
- **TrackTools** [PRY22]: MF6 + MODPATH7 particle source apportionment using cell budgets for mixing ratios in weak-source cells.

### 5.4 Not the same thing
- **Leake / Barlow "capture"** [LEA10, BAR18] is the *change* in boundary flows caused by pumping (superposition/perturbation runs), as in the MF6 capture-fraction example [MF6EX]. FlowSource's "capture fraction" is a flow-tracing quantity [EA19, CHO16].

### 5.5 Existing open tools
- No open-source FlowSource equivalent for MF6 was found.
- FloPy provides the readers needed (`CellBudgetFile`, `MfGrdFile` for IA/JA, face-flow utilities) [FLOPY].
- `maseology/ptrack` (Go) lists FlowSource-style tracking as future work only [PTRACK].

## 6. Implications for a MODFLOW 6 implementation

*This section is design inference built on the sources above. MF6 file details are from [MF6IO], [LAN17] and [LAN22].*

### 6.1 Required MF6 output

**Budget file (`.cbc`)** — `SAVE_FLOWS` in NPF, STO and every stress/advanced package; `BUDGET SAVE` in OC.
- **FLOW-JA-FACE** (IMETH=1, length NJA): intercell flows aligned with IA/JA in the binary grid file; diagonal entries are 0. Positive = flow *into* cell *n* from *m* (verify against FloPy, e.g. `get_structured_faceflows`). Same for DIS, DISV, DISU; IDOMAIN = −1 pass-through cells are already bypassed in the connectivity.
- **STO-SS, STO-SY** (IMETH=1): storage exchange per cell, for the transient time-instant treatment.
- **Package terms** (IMETH=6 lists; ID1 = cell node, ID2 = bound number, plus auxiliaries): CHD, WEL, DRN, RIV, GHB, RCH/RCHA, EVT/EVTA, MAW, LAK, SFR, UZF-GWRCH/GWET/GWD, *-TO-MVR, CSUB. Needed to (a) define destinations by package/bound (e.g. "WEL bound 12", "SFR reaches 30–60") and (b) split Volume From by process.
- **DATA-SAT / DATA-SPDIS**: optional; for travel time and plotting.

**Binary grid file (`.grb`)**: IA, JA, cell areas/geometry (for flux variants and raster output), IDOMAIN, top, bottom.

**Heads (`.hds`)**: only for head-ordered sorting, travel time (unless DATA-SAT is used) and dry-cell detection.

**Multi-model simulations**: GWF-GWF exchange flows appear in each model's budget as **FLOW-JA-FACE with IMETH=6** (TXT2ID1 = exchange name, ID2 = node in the connected model). A global graph needs a (model, node) → global-index map.

**Precision**: MF6 binary output is double precision (verify for the version in use); FloPy handles this.

### 6.2 Algorithm choices to make explicit

1. **Net vs gross per-cell source/sink accounting.** FlowSource appears to use net $s_i$ (inferred from [FB13]). A gross formulation is closer to transport (§5.2) and handles **weak-sink destinations** properly: add an explicit sink node per package bound, so the destination is that bound's flow, not the whole cell. Recommend supporting both: "FlowSource-compatible" (net, absorbing destination cell) for regression against [FB13], and "gross / bound-level" as the physically consistent default.
2. **Destination definition.** By cell list, package + bound IDs, or package name. FlowSource treats a destination cell as absorbing all its throughflow.
3. **Solution method.** Topological sort (Kahn) on the FLOW-JA-FACE graph, or head ordering for TPFA flows. With cycles: (a) remove minimum edge (FlowSource-compatible), or (b) solve $(\mathbf I-\mathbf P)\mathbf f=\mathbf b$ with `scipy.sparse` — simpler and robust with XT3D. Report cycles and the flow they carry. Many destinations at once: multi-column RHS, $\mathbf F=(\mathbf I-\mathbf P)^{-1}\mathbf B$, one column per destination group — gives boundary-control maps summing to 1 across all sinks [BF13].
4. **Forward mode.** Same machinery on the transposed graph with inflow normalisation (§2.4); test against a steady GWT unit-concentration run.
5. **Transient treatment.** Default to time-instant steady state per step with storage as source/sink, plus min/max/mean, ASN, probability-within-range and threshold statistics. Optional *true transient* mixing-cell mode (à la HMC [PAR11]) carrying tracer volumes between steps — needs cell water volumes from heads/storage and changes the meaning of outputs.
6. **Advanced packages and MVR.** To trace through SFR/LAK/MAW, add package nodes and edges from the package budget files (SFR inter-reach FLOW-JA-FACE; GWF exchange terms per reach/lake/well) and MVR transfers. MAW wells connecting several cells need their own node. Matches FlowSource's stated plans for coupled surface-water graphs [FB13, BF13]; unknown whether implemented.
7. **Numerical dispersion.** Consider Chowdhury's face-to-face partitioning for DIS grids [CHO16], or at least document grid sensitivity. Pollock-type partitioning does not extend directly to DISV/DISU.
8. **Travel time.** Don't reimplement: seed MF6 PRT or MODPATH 7 from contributing cells, as FlowSource does. Optionally add a mixing-cell mean residence time as a new Eulerian metric (not FlowSource behaviour).
9. **Residuals.** Absorb small per-cell budget residuals into the net source/sink, or report them (analogous to GWT FMI flow-error correction [LAN22]).

### 6.3 Alternative route: MF6 GWT
- **Forward mode**: GWT via FMI on saved GWF budget/head files, SSM unit concentrations (one model or species per source), upstream advection, no dispersion. GWT has **no single-step steady-state option** [LAN22], so each time-instant steady state needs a transient run to equilibrium — though a transient run gives true transient fractions.
- **Backward mode** needs a reversed flow field (synthetic budget file with negated FLOW-JA-FACE, swapped sources/sinks): feasible but awkward.
- **Overall**: a standalone post-processor reading `.cbc` and `.grb` via FloPy with NumPy/SciPy sparse graphs is simpler, exact for FlowSource's definitions, and fast. Keep GWT as a validation oracle for forward mode.

### 6.4 Suggested regression tests
1. [FB13]'s 3×3 worked example: f, V_thr, V_from as in §2.3.
2. [CHO16 §4.1.2] planar 3×3 case (fully mixed vs streamtube).
3. Closure: $\sum V^{\text{from}}$ = destination inflow; forward/backward duality (§2.4); boundary-control fractions summing to 1 per cell [BF13].
4. Steady GWT unit-concentration comparison for forward mode (gross accounting).

## 7. Quick reference: FlowSource outputs

| FlowSource name | Formula | Units | Definition source |
|---|---|---|---|
| Fractional Flow Through (capture fraction) | $f_i$ | – (%) | FB13, BF13, EA19, GWS-web |
| Volume Flow Through | $f_i T_i$ | m³/d | FB13, GWS-web |
| Flux Flow Through | $f_i T_i / A_i$ | m/d | GWS-web (FS20) |
| Volume Flow From | $f_i \max(s_i,0)$ | m³/d | FB13, GWS-web |
| Fractional Flow From | $f_i$ on source cells (2013), or $V^{from}_i/\sum V^{from}$ (FS20/web) | % | BF13 Fig 4; GWS-web, BFW21 |
| Flux Flow From | $V^{from}_i / A_i$ | m/d | GWS-web |
| Fraction To / Volume To (forward) | $g_i$ / $g_i\max(-s_i,0)$ | –, m³/d | GWS-web (names); formulas inferred |
| ASN | 1 / 0.5 / 0 by threshold over time steps | – | BF13 |
| Probability within range | fraction of time steps in range | – | BF13, EA19 |
| Travel time | forward particle time to destination | d | BF13, EA19 |

## 8. Gaps: not found or not verified

**FlowSource documentation**
1. **No public user manual, control-file format, output-file format or example dataset.** Support material is behind a vendor login.
2. **FS20 algorithm changes** are described only as "minor improvements to flow routing methodology, error checking". Unknown: whether Chowdhury's partitioning was adopted; whether weak-sink destinations are treated at bound level; how unstructured-grid travel time works.

**Algorithm details**
3. **Formulas are never written out** in the sources. §2 equations are reconstructed from [FB13]'s worked example and prose; they reproduce all its numbers, but net-vs-gross treatment of mixed cells is an interpretation.
4. **Process breakdown of Volume From** is mentioned but not described.
5. **Forward mode** has no worked example or equations in any source; §2.4 is inferred.
6. **Fraction From** is defined inconsistently between 2013 papers and FS20/website.
7. **No information** on MF6 exchanges, MVR or SFR/LAK/MAW/UZF routing support.

**Inaccessible documents**
8. **EA (2015) independent review** of FlowSource is unpublished — the best independent verification; would need a request to the EA.
9. **MODALL** [POT08] and comment [MC09] not read in full (paywalled); the MODALL ≡ Fraction Through equivalence relies on FlowSource's authors and Chowdhury.
10. **Barlow et al. (2018), Bedekar et al. (2024), Partington et al. (2011)** not downloaded (paywall / 403); abstracts and metadata only.
11. GWMF 2022 programme PDF and ResearchGate pages could not be fetched.

**Literature coverage**
12. **No peer-reviewed journal paper** on FlowSource was found, nor a BGS NORA report about it. Google Scholar citation lists were not directly accessible; further consultancy applications (e.g. EA regional model reports) likely exist but are not indexed.
