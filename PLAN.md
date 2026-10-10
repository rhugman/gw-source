# Implementation plan: flow-source tracing for MODFLOW 6

Drafted 2026-10-02. Background, equations and sources are in [`references/SUMMARY.md`](references/SUMMARY.md); citation keys such as [FB13] refer to [`references/bibliography.md`](references/bibliography.md).

## 1. Goal

An open-source Python package that post-processes MODFLOW 6 groundwater-flow output to answer two questions for any cell:

- **Backward (capture):** what fraction and volume of the water here ends up at a chosen destination (well, river reach, drain, set of cells)?
- **Forward (fate):** what fraction of the water here came from a chosen source (recharge zone, river, boundary)?

It builds on the published cell-mixing flow-tracing method [FB13, BF13], called "the reference method" below. It reproduces that method's outputs as a special case, and improves on it where it is weak:

| Reference method | This package |
|---|---|
| Topological sort; cycles broken by deleting the smallest edge | Sparse linear solve; exact under full mixing, with or without cycles. A topological fast path is used when the graph is acyclic. |
| Net source/sink per cell; destination cell absorbs all its throughflow | Gross accounting with one node per package boundary; weak sinks take their proportional share. A net mode matching the reference method is kept for regression tests. |
| One destination group per sweep | One factorisation, many right-hand sides: fractions to every sink at once. |
| Transient = independent steady-state snapshots | Snapshots by default; true transient tracking through storage in a later phase. |
| Travel time from particles only | Eulerian mean travel time from the same matrix, plus a helper to seed MF6 PRT particles. |
| Probability only over time steps | Built to run cheaply over a parameter ensemble (e.g. PEST++ IES realisations). |

**Out of scope:** reactive transport, dispersion physics, a GUI, and non-MF6 simulators (MODFLOW-USG/2005 could be added later through the reader layer).

## 2. Method

### 2.1 Graph and accounting (one time step)

Unknowns are the active model cells. The read-only inputs are:

- **Intercell flows** $q_{ij} \ge 0$ from FLOW-JA-FACE. In MF6, a positive `flowja` at connection (n, m) means flow *into* n from m; confirmed against FloPy's `get_structured_faceflows`, which negates it to get outflow.
- **External terms per cell, kept by package and by boundary:** CHD, WEL, DRN, RIV, GHB, RCH, EVT, the UZF exchange terms, STO-SS, STO-SY, the MAW/LAK/SFR exchange terms and the *-TO-MVR terms. Each external flow with a positive (into-cell) value is a **source term**; each with a negative value is a **sink term**. Storage counts as a sink when water goes into storage and a source when it is released.

For each cell $i$:

- $O_i$ is the total outflow: intercell outflow plus all sink terms.
- $I_i$ is the total inflow: intercell inflow plus all source terms.
- $r_i = I_i - O_i$ is the budget residual. It is reported and never forced to zero.

### 2.2 Backward mode

Each cell is fully mixed. Water leaving cell $i$ splits across its out-edges and its sink terms in proportion to their flows. With the out-normalised transition matrix $P_{ij} = q_{ij}/O_i$:

$$
(\mathbf I - \mathbf P)\,\mathbf F = \mathbf S\,\mathbf D
$$

- $\mathbf S$ (cells × sink terms) holds $q_{i,k}/O_i$ for each sink term $k$ in cell $i$.
- $\mathbf D$ (sink terms × destination groups) is a 0/1 matrix of which sink terms belong to which group.
- $F_{ig}$ is the **fraction through**: the fraction of the water passing through cell $i$ that reaches group $g$.

Derived outputs:

- **Volume through:** $F_{ig}\,O_i$.
- **Volume from, per source term $k$:** $F_{ig}\,q_{i,k}$. This splits the contribution by process (recharge, storage, river leakage, and so on) without any extra assumption.
- **Fraction from:** both definitions. In the 2013 sense [BF13] it is $F_{ig}$ on source cells. In the later sense [BFW21] it is volume from divided by the group total. The two get distinct names.
- **Flux variants:** the volumes divided by cell plan area.

If every sink term is given its own column, each row of $\mathbf F$ sums to 1. That gives "boundary control" maps directly.

### 2.3 Forward mode

Use the in-normalised matrix $Q_{ij} = q_{ji}/I_i$ (inflow to $i$ from $j$), with source-term shares $q_{i,k}/I_i$ on the right-hand side:

$$
(\mathbf I - \mathbf Q)\,\mathbf G = \mathbf R\,\mathbf T
$$

- $G_{ig}$ is the fraction of water in cell $i$ that came from source group $g$, which is the dilution ratio $C/C_0$.
- **Volume to sink term $k$:** $G_{ig}\,q_{i,k}$.

Normalising backward mode by outflow and forward mode by inflow means the residuals cannot distort the fractions. The residual only shows up in the closure check (§7).

### 2.4 Net mode

Use the net source/sink per cell, $s_i = O^{\text{edges}}_i - I^{\text{edges}}_i$, with throughflow $T_i = I^{\text{edges}}_i + \max(s_i, 0)$, and fix $f = 1$ in destination cells. This must reproduce [FB13]'s 3×3 worked example exactly. It exists for regression testing and for comparison with existing studies that used the reference method. It is never the default.

The destination inflow in net mode is the water attributed to the group, each passage counted once:

$$
\sum_{d \in D} T_d \;-\; \sum_{D \to D} q \;-\; \sum_{D \to \neg D} q_{ij} f_j \;=\; \sum_i f_i \max(s_i, 0).
$$

The throughflow sum alone counts water twice when it passes from one destination cell to another, or leaves a destination cell and reaches the group again; it is kept as `destination_throughflow`. For a single destination cell that no water leaves and reaches again, the two are equal. Forward mode is the mirror image: the source inflow is $\sum_{s \in S} T_s - \sum_{S \to S} q - \sum_{\neg S \to S} q_{ji} g_j = \sum_i g_i \max(-s_i, 0)$, and the throughflow sum is kept as `source_throughflow`.

Unlike gross accounting, the net inflow uses the solved fractions just outside the group, so it depends on the solve and not on the budget alone; its meaning is pinned by the [FB13] test and the hand-built tests. The closure check is volume from (to) = net inflow, with no residual term. Its error is exactly the sum of the un-normalised row residuals over the cells outside the group, $\sum_{i \notin D} (T_i f_i - \sum_j q_{ij} f_j)$, so it tests the solve in sum.

### 2.5 Solution strategy

1. Build $\mathbf P$ (or $\mathbf Q$) as a CSR matrix from the binary-grid IA/JA arrays and `flowja`. That costs $O(\text{NJA})$.
2. Try a topological order using Kahn's algorithm on the edges with positive flow.
   - **If the graph is acyclic**, permute to triangular form and solve by substitution in $O(N + E)$ per right-hand side. This is the reference method's algorithm [FB13].
   - **If there are cycles**, use a sparse LU (`scipy.sparse.linalg.splu`) and reuse it for every right-hand side. If fill-in is too large on big 3D models, fall back to BiCGSTAB with an ILU preconditioner. Report the cycles: their size and the flow carried around them.
3. Removing the minimum edge in each cycle, as the reference method does, is available in net mode only.
4. Cells with $O_i = 0$ (dry, isolated or inactive) get the identity row and $f = 0$.

### 2.6 Eulerian mean travel time (phase 3)

This needs the water volume in each cell: porosity times saturated volume, with saturation from DATA-SAT or from heads. The mean residence time in cell $i$ is $\tau_i = V^w_i / O_i$. With $\mathbf m$ as the capture-weighted expected time,

$$
(\mathbf I-\mathbf P)\,\mathbf m = \mathbf F \circ \boldsymbol\tau, \qquad \bar t_{ig} = m_{ig}/F_{ig}
$$

This reuses the same factorisation. It is a mean over a mixed distribution, not the first advective arrival, so it complements particles for 50-day and 400-day zone criteria rather than replacing them.

### 2.7 Transient models

- **Phase 2 (snapshots):** process each selected time step independently, with storage acting as a source or sink term. Statistics across time steps:
  - min, max and mean;
  - always/sometimes/never above a threshold (ASN);
  - probability within a range;
  - an exceedance count.
  Statistics are accumulated in a streaming way, so all time steps never have to be held in memory at once.
- **Phase 4 (true transient):** a mixing-cell model in which tagged water volume is carried through storage between time steps. It is implicit and upwind, with no dispersion, and needs porosity.
  - **Forward:** validate against, or optionally delegate to, an MF6 GWT run with unit concentrations.
  - **Backward:** solve the adjoint backward in time.

### 2.8 Grid support: DIS, DISV and DISU

The core method only needs the cell connections and the flows across them. The binary grid file stores those connections (the IA and JA arrays) in the same form for DIS, DISV and DISU, and FLOW-JA-FACE is indexed by them in the same way. So the matrices, the solve, fractions, volumes, forward and backward modes, statistics and diagnostics do not depend on grid type. That is the point of building on IA/JA rather than on row and column face flows.

Some features need geometry, and the binary grid file does not always provide it:

| Feature | DIS | DISV | DISU |
|---|---|---|---|
| Fractions, volumes, forward/backward, statistics | yes | yes | yes |
| Flux variants (need cell area) | DELR × DELC | from the vertices in the grid file | the grid file has **no area**. Use the vertices if the user supplied them; otherwise read AREA from the DISU input through FloPy |
| Eulerian travel time (needs cell volume) | yes | yes | needs area, as above |
| Reshaping output to the grid | (nlay, nrow, ncol) | (nlay, ncpl) | (nodes,) |
| Maps and GeoPackage export | yes | yes | only if vertices were supplied (VERTICES, IAVERT and JAVERT in the grid file) |
| Particle check with MF6 PRT | yes | yes | **no**: PRT supports DIS and DISV only. The Eulerian travel time is the only travel-time option for DISU |
| Face-to-face routing within cells (phase 5) | yes | no | no |

Other notes:
- **Cycles:** unstructured grids often use XT3D, which adds cross-terms that can make flow loop back. The solver then takes the sparse LU path (§2.5) instead of the topological fast path.
- **MF6 vs MODFLOW-USG:** MF6 has no ghost-node correction (MODFLOW-USG does), so the only extra source of cycles on DISV and DISU is XT3D.
- **DISU layering:** DISU has no layer concept, so per-layer outputs and maps need a layer array supplied by the user, or one derived from the cell tops and bottoms.

## 3. Package layout

The working name is `gwsource` (decision D1). It is a reusable package, so it gets a `pyproject.toml` and, eventually, a small CLI. Example studies use the usual `workflow.py` pattern.

```
gw-source/
├── pyproject.toml
├── environment.yml          # mamba env "gw-source": numpy, scipy, pytest, (numba), (xarray, geopandas); flopy@develop via pip
├── bin/                     # mf6 nightly build (get-modflow); git-ignored
├── PLAN.md
├── references/
├── src/gwsource/
│   ├── __init__.py          # public API re-exports
│   ├── config.py            # @dataclass TraceConfig (mode, accounting, solver, thresholds)
│   ├── mf6io.py             # read .grb + .cbc → FlowStep (one time step), node maps
│   ├── flowstep.py          # @dataclass FlowStep: ia, ja, flowja, terms{(pkg, bound): (node, q)}, area, volume
│   ├── selectors.py         # build destination/source groups: by cells, package, bound ids, boundnames, zones
│   ├── assemble.py          # P/Q, S/R matrices from FlowStep; gross and net accounting
│   ├── solve.py             # topological fast path, splu, iterative fallback, cycle report
│   ├── metrics.py           # fraction/volume/flux through, from, to; fraction-from (both defs)
│   ├── traveltime.py        # Eulerian mean time; PRT seeding helper
│   ├── transient.py         # time-step loop, streaming statistics (min/max/mean/ASN/prob)
│   ├── diagnostics.py       # residuals, closure, duality checks, cycle summaries
│   └── export.py            # reshape to grid, npz, netCDF (xarray), GeoPackage (flopy modelgrid → geopandas)
├── tests/
│   ├── test_fb13_example.py
│   ├── test_assemble.py
│   ├── test_solve.py
│   ├── test_closure_duality.py
│   ├── models/              # FloPy builders for small MF6 test models
│   └── test_mf6_integration.py
└── examples/
    └── 01_steady_well/workflow.py
```

**Target public API** (a sketch, to be tested against the examples):

```python
import gwsource as gs

step = gs.read_step(ws, model="gwf", kstpkper=(0, 0))
dest = gs.select(step, package="WEL", bounds=[12])
res = gs.backward(step, {"well_12": dest}, config=gs.TraceConfig())
res.fraction_through["well_12"]      # (nodes,) array
res.volume_from_by_term["well_12"]   # {(pkg, term): (nodes,) array}
gs.export.to_netcdf(res, step.grid, "well_12.nc")
```

Following house style: small functions with explicit arguments, type hints, `assert` for validation, no module-level state, and configuration through one `@dataclass`.

**Naming rule:** the commercial product name never appears in code, comments, docstrings, docs, test names, file names or output variable names. Output names use neutral terms (`fraction_through`, `volume_from`, and so on), and the method is credited by citing the papers (Foley & Black 2013; Black & Foley 2013). A CI check (a grep in the test suite) enforces this.

## 4. MF6 input requirements (documented for users)

- **NPF and every stress or advanced package:** `SAVE_FLOWS`.
- **OC:** `BUDGET SAVE` for the time steps to analyse.
- **STO:** `SAVE_FLOWS` for transient models.
- **Binary grid file:** the `.grb` file, written by default, unless `NOGRB` is set.
- **Optional:** heads, and DATA-SAT (`SAVE_SATURATION` in NPF), for travel time.
- **Advanced packages:** each package's own budget file (`BUDGET FILEOUT`), needed only when tracing through package networks (phase 4).

## 5. Phases and deliverables

### Phase 0: scaffolding (about 1 day)
- `pyproject.toml`, pytest and CI on GitHub Actions.
- **Project-specific mamba environment** named `gw-source`, defined in `environment.yml`:
  - conda-forge packages: python, numpy, scipy, pytest, matplotlib, plus the optional xarray, geopandas and numba;
  - **FloPy from the `develop` branch**, installed with pip inside the environment: `pip install git+https://github.com/modflowpy/flopy.git@develop`;
  - this package itself, installed editable with `pip install -e .`.
- **MODFLOW 6 nightly build**, downloaded into the project's `bin/` folder: `get-modflow --repo modflow6-nightly-build ./bin`. The `bin/` folder is git-ignored. Code finds the executable relative to the repository and passes the path explicitly, never through an import-time global.
- **Keep FloPy's MF6 classes in step with the nightly MF6:** after updating either one, regenerate FloPy's MF6 classes from the MF6 `develop` definition files with `python -m flopy.mf6.utils.generate_classes --ref develop` (check this command on FloPy `develop`, where class generation has been under rework). This keeps package options in FloPy matching the MF6 binary.
- **Reproducibility:** both inputs move over time. Record the FloPy commit hash and the MF6 nightly version (`mf6 --version`) in the test output and in CI logs. CI rebuilds the environment on every run, plus a weekly scheduled run, so changes upstream show up early.
- One script, `scripts/setup_env.sh`, holds all of these steps: create or update the environment, install FloPy develop, regenerate the classes, download the nightly MF6.
- FloPy builders for test models:
  1. a 1-layer steady DIS model with a well, a river and recharge;
  2. a 3-layer DIS model with a partially penetrating well, which gives a weak sink;
  3. a DISV Voronoi version of model 1;
  4. a DISU version of model 1, built with `flopy.utils.gridutil.get_disu_kwargs`, in two variants: with vertices and without, to cover the missing-geometry case;
  5. a model 1 variant with XT3D, to produce cycles;
  6. a transient version of model 1 with STO.
- *Status (2026-10-02): done.* Notes from implementation: `generate_classes --ref develop` still works on FloPy `develop` but needs the `codegen` extra (`flopy[codegen]`, which pulls in `modflow-devtools`), so `environment.yml` installs that. `get-modflow` is given `--downloads-dir` (its default is `~/Downloads`), and also fetches `triangle` from the `executables` repo for the Voronoi model. Builders live in `tests/models/`; models 1, 4, 5 and 6 carry IDOMAIN = 0 cells; model 2 has a weak-sink well; model 5 has at least one flow cycle.

### Phase 1: steady-state core, the minimum viable product
- `mf6io`:
  - Reads `.grb` and FLOW-JA-FACE and the IMETH=6 package terms.
  - Maps user node numbers to reduced node numbers: MF6 package budget entries use user node numbers, while FLOW-JA-FACE is indexed by reduced node; to verify on a model with IDOMAIN = 0 cells.
  - Supports DIS, DISV and DISU.
- `assemble` in gross mode, and `solve` with both the topological path and splu.
- `backward` and `forward`; all fraction and volume metrics, including volume from by process.
- Net mode, plus the [FB13] regression test.
- Diagnostics: residuals, closure ($\sum$ volume from = inflow to the destination sink terms), and forward/backward duality.
- Export to arrays and npz; quick-look plots with the FloPy PlotMapView.
- **Done when:** the [FB13] numbers match exactly, the closure and duality tests pass to 1e-10 relative error on all steady test models, and the same model gives identical results to machine precision whether built as DIS or as DISU (same cells and connections, so same answer). DISV is compared with DIS on the same physical problem, within a tolerance tied to the cell size.
- *Status (2026-10-02): done.* Notes from implementation: the `.grb` IA/JA, FLOW-JA-FACE and all budget terms are already in user node numbering for DIS, DISV and DISU (cells with IDOMAIN ≤ 0 keep empty rows), so no node map is needed; MF6 stores the cell residual in the FLOW-JA-FACE diagonal. The DISU `.grb` does carry vertices when they are given in the input. `backward`/`forward` live in an extra module, `trace.py`. Boundnames are not in the budget file; the selector supports them once a reader fills `FlowStep.term_boundname` (Phase 2).

### Phase 2: transient snapshots and usability
- `transient`: loop over selected time steps, with streaming statistics.
- `selectors` by boundnames and by zone arrays.
- netCDF and GeoPackage export.
- A cycle report (location, magnitude), and timing on a model of about 1M cells.
- **Done when:** the transient test model runs, and the statistics match a brute-force calculation that stores every time step.
- *Status (2026-10-02): done.* Notes from implementation:
  - **MVR:** a provider with MOVER writes two disjoint aquifer-side records per bound, e.g. DRN (the part leaving the model) and DRN-TO-MVR (the part handed to the mover); together they equal the drain's C(h − elev). Both are kept as sink terms; the cell budget closes only with both (test model 7, DRN → MVR → SFR). MF6 computes the moved share at the last outer iteration, so its own residual and the records can differ at solver tolerance (~1e-9 relative). The second record of a package is named `<pkg>:<text>` (e.g. `DRN:DRN-TO-MVR`); selecting `DRN` selects both.
  - **Solver:** new `block` solver (SCC block-triangular order + SuperLU with natural ordering, no pivoting) is the `auto` choice for cyclic graphs; COLAMD `lu` is kept as a reference. Closed recirculation loops (SCC with no exit) are found before the solve, set to 0 and reported (`result.closed_loops`).
  - **Transient:** `trace_transient` re-selects groups on every step (dict of `select()` arguments or a function); mean and probability-in-range are time-weighted by DELT by default (`weighting="equal"` optional). `StepReader`/`open_model` read the grid once.
  - **Benchmarks** (`benchmarks/`, macOS, 16 cores, 64 GB; scipy 1.18): synthetic 3D grid, 4 groups, 1M cells: assembly 0.24 s, components 0.10 s, closed-loop check 0.10 s, topological solve 0.55 s, metrics 0.11 s; with 7,000 injected cycles (largest 649 cells) the block solve takes 0.42 s. COLAMD LU takes 2.8 s at 50k and 6.7 s at 100k cells and is not usable beyond that. MF6 model of 250k cells: ~0.01 s I/O, ~0.36 s per step for 6 groups, 1.2–1.3 s for 40 groups; opening the files 1.9 s once. **D5:** numba is not needed; the scipy topological path is compiled and is not the bottleneck.
  - **Memory limit:** each group costs about 90 MB per million cells (its outputs plus a solve column), so one group per term (thousands of wells) does not fit at 1M cells; aggregate with `groups_by_package`, `groups_by_boundname` or `groups_by_zone`, or trace groups in batches.

### Phase 3: travel time and ensembles
- Eulerian mean travel time (§2.6).
- PRT helper: seed forward particles in contributing cells, weighted by flux, and track them in MF6 PRT. PRT is forward-only and supports DIS and DISV. Backward checks on DIS grids would use MODPATH 7.
- Ensemble driver: run the trace over realisation folders, write per-cell capture probabilities and quantiles, optionally using pyemu to locate the realisations.
- **Done when:** Eulerian mean times agree with the mean of flux-weighted PRT arrival times on the steady test model, within a tolerance tied to the cell size.
- *Status (2026-10-02): done.* Notes from implementation:
  - **Travel time** (`traveltime.py`): $\tau = V/O$ backward, $V/I$ forward; the backward time runs from entering a cell until leaving through a destination sink term and includes the residence in the exit cell; `mean_time_to_exit_cell` (one more right-hand side, $\tau \circ \mathbf S\mathbf D$) stops at entry to that cell, as particle trackers do. Exact identity $\sum \mathrm{Src}\,m - \sum r\,m = \sum V F$ (flux-weighted mean time $= \sum VF / Q_D$), and the forward age analogue $\sum \mathrm{Snk}\,n + \sum r\,n = \sum V G$, hold to ~1e-16 on models 1–5. The factorisation is kept on gross results (`result.factor`, solver `Factor`) and reused. Saturated thickness comes from DATA-SAT, else heads (`FlowStep.saturated_thickness`); porosity is a required argument.
  - **PRT** (`prt.py`): `STOP_AT_WEAK_SINK` is not used (it also stops particles at other boundaries' weak sinks, e.g. gaining river cells). The destination cells are a PRT stop zone (status 6) weighted by $d_k/O_k$, and particle weights are thinned by the full-mixing survival $1-\mathrm{Snk}_j/O_j$ of other weak sinks passed. Model 1: PRT 9590 d vs Eulerian 9574 d to the exit cell (9607 d including it); model 3 (DISV): 9475 vs 9421 d; captured particle flow 800.4 of 800 m3/d. Test models now save DATA-SPDIS (not possible on DISU without vertices).
  - **PRT revision (2026-10-03).** The first version under-counted on layered models (Neversink: 53 % of the well inflow released at the water table, 82 % mid-cell). Two defects, no physics: (1) all points at one local z, while MF6 spreads boundary sources over the cell volume (no IFLOWFACE); at z = 1 the top face carries no flow, so top-layer particles stay at the water table and never reach deeper wells; (2) particles stopped in the first destination cell with $d_k/O_k$ of their weight and the rest was dropped, although it flows on to other destination cells (U___7 takes 44 % of its cell's outflow, and F = 0.97 there). Now: points at `z_levels` heights through the saturated thickness (one on a one-layer grid), no stop zone, and the gross accounting applied along each path (in every visited cell $d_j/O_j$ of the remaining weight is captured, $1-\mathrm{Snk}_j/O_j$ kept). Model 2 (3 layers): 402.6 of 405 m3/d (was 266); Neversink: 3,736 of 3,671 m3/d (+1.8 %). Models 1 and 3 unchanged. Termination status and repeat visits played no part (all particles end in strong sinks with no weight left; no cell visited twice).
  - **IFLOWFACE (2026-10-05).** Source terms whose package carries `AUXILIARY IFLOWFACE` are released where PRT's velocity field brings them in: top or bottom face (−1/−2) at the plan points with local z 1 or 0; lateral face i (the edge from vertex i to i + 1; DIS 1 W, 2 N, 3 E, 4 S) at points along the edge × the z levels; 0 or no aux: volume seeding as before. The value is read from the aux column of the GWF list budget record (where PRT reads it) into `FlowStep.term_iflowface`; DIS cell polygons now run clockwise from the south-west corner so that edge i is face i. Test model `m2_dis3lay_top` (model 2 with top-face recharge, same GWF flows): 405.8 of 405 m3/d, no recharge reaching the bottom-layer wells; volume seeding gives 412.7, including 6.9 m3/d of spurious recharge. Open: lateral faces are checked only by experiment (DIS CHD edges, the same ±2–3 % scatter as volume seeding), DISV lateral faces by no run.
  - **Neversink quadrature (2026-10-05).** The +1.8 % of the volume-seeded run is quadrature, not the thinning factor: five seeding layouts give 0.0 to +1.8 % with no trend; per-well errors shrink with z levels (RMS 18 % → 6 % from one to four), not with plan points at one height.
  - **Neversink stage 3 mechanisms (2026-10-05).** `studies/neversink/growth_mechanisms.py` (61 realisations, base/half/max pumping) saves per-reach stream volumes and runs PRT under the published conventions on the same flow fields. The extra pumping is balanced mostly by less discharge to gaining reaches (8,790 of 9,830 m³/d); the stream water reaching the wells grows 2.5 times, mostly as a larger captured share of reaches already losing near the wells. PRT with the published conventions reproduces the published growth (3.62 against 3.60); stopping at buried stream weak sinks explains most of the gap to full mixing (4.09). Thinned particles grow faster than full mixing (4.53) because at base pumping they bring more stream water from partly captured reaches near the U wells (`advective_growth.py`); the shortfall disappears once those reaches are captured. The Monte Carlo masks lie one row south and follow a text-sorted run order (`mc_masks.py`); corrected, PRT with the published conventions matches each realisation's own mask (median Jaccard 0.996 at base), and the published scenarios kept each realisation's well multiplier. `ensemble_run.read_mask` / `mask_indices` now return the corrected, paired masks and `scenarios.scenario_pars` keeps the multiplier; stage 3, the mechanism samples and Figures 2 and 3 were rerun with both (2026-10-05).
  - **Ensemble** (`ensemble.py`): exact quantiles from a float32 stack under `memory_budget`, else per-cell fixed-bin histograms (error ≤ one bin width). Process-pool runs are bit-identical to serial; the parallel test skips where the OS forbids semaphores (the agent sandbox). pyemu is not used; `list_realisations` globs folders.

### Phase 4: extensions
- Multi-model simulations: GWF-GWF exchange flows, with a global node index across models.
- Package networks: SFR/LAK/MAW/UZF nodes, with edges from the package budget files, and MVR transfers. MAW wells get their own node because they move water between cells.
- True transient mixing-cell tracking (§2.7), validated against MF6 GWT.
- *Status of part A (multi-model, package networks; 2026-10-02): done.* Notes from implementation:
  - **Global nodes** (`network.py`): `open_simulation(ws, models=None, package_nodes=("SFR", ...))` / `read_network()` return an ordinary `FlowStep` whose nodes are the cells of every GWF model, then one node per reach, lake, MAW well or UZF cell; `FlowStep.blocks` (`NodeBlock`) records the ranges. Package nodes are switched on at read time, not in `TraceConfig` (the graph is built when the step is read). `read_step` is unchanged and the default.
  - **Exchanges:** need `SAVE_FLOWS` in the exchange file (checked). Each GWF-GWF exchange is read from the first model's FLOW-JA-FACE IMETH = 6 record; the other side must be its exact negative. Read alone, a model's exchanges are boundary terms ('GWF-GWF'). MF6's FLOW-JA-FACE diagonal already includes exchange flows. Models 1, 3 (DISV) and 6 split into 3, 2 and 4 models with `Mf6Splitter`: every output, mapped back with the splitter, matches the single model to ≤ 7e-10 relative (DISV 1.4e-10, transient 1.5e-12) with the existing solver settings.
  - **Package records** (mapping table in `packages.py`): the package budget's GWF record replaces the aquifer-side GWF record (SFR, LAK, MAW, UZF-GWRCH); the edge takes the GWF-side value, because the two sides differ at solver tolerance (≈1e-8 absolute: head vs stage of the last iteration). Package water volume is the STORAGE record's VOLUME auxiliary (`FlowStep.fixed_volume`); UZF volume is 0 in steady state.
  - **Aquifer exchange tolerance** (`aquifer_rtol`, 2026-10-02): the check that the package budget's GWF record is the negative of the GWF budget's record defaults to `AQUIFER_RTOL` = 1e-4 of the package's largest exchange and is a keyword of `open_simulation` / `read_network` (stored on `NetworkReader`, passed to `build_network` / `aquifer_links`). The edges already take the GWF-side values, so a larger tolerance only leaves the difference in the package nodes' residuals, which closure and duality include as the residual term. The USGS Neversink model (12,316 SFR reaches, published OUTER_DVCLOSE 0.01 m) differs by up to 1.9e-4 of its largest exchange (0.17 of 12 m³/d on one reach, 3 reaches above 1e-4) and fails the default; with OUTER_DVCLOSE 1e-4 it passes, so the cause is solver tolerance (the two sides use the head and stage of different iterates). The failure message reports the largest relative difference and the number of connections above the tolerance, and suggests tightening the solver or passing `aquifer_rtol`. Test: model 7 with outer/inner DVCLOSE 1e-2/1e-3 (difference 1.2e-3) fails the default and, with `aquifer_rtol=1e-2`, closure and duality hold to 1e-10 with the residual term.
  - **MVR** needs `BUDGET FILEOUT` in MVR (MOVER-FLOW records per provider/receiver package pair). A transfer becomes an edge when the receiver has nodes and the provider's TO-MVR record is in the graph (on a cell or a package node); a provider bound with several TO-MVR records (UZF rejected infiltration and groundwater seepage) shares it by rate. Remainders within 1e-6 are zeroed and appear in the node residual. Simulation-level movers between models (MVE) are not read.
  - **Tests:** model 7 now saves SFR and MVR budgets (flows unchanged); new model 8 (MAW across 3 layers of the model 2 grid, injecting into layer 3) and model 9 (two lakes joined by an outlet, UZF whose rejected infiltration is moved to a lake). Residuals of every node, closure, duality, boundary control and the travel-time identities hold to 1e-10. Model 7: with SFR nodes, 0.40 and 0.57 of the drain cells' water reaches the east well (0 without), and the 369 m³/d of the well's water attributed to "SFR" leakage without nodes is traced to the stream inflow and to recharge. Not covered by an MF6 model: UZF cell-to-cell FLOW-JA-FACE (multi-layer UZF), MAW flowing wells, LAK/MAW TO-MVR providers (the hand-built test covers the sharing rule).
  - **Output:** `export.to_grid(step, values, model=)`, `model_view`/`result_view`/`transient_view` (one model's cells, for the existing exports), `save_network` (npz per model, package-node CSV, GeoPackage with a `package_nodes` point layer). The PRT helper raises `NotImplementedError` on network steps.
- *Status of part B (true transient tracking; 2026-10-02): done.* Notes from implementation:
  - **Scheme** (`tracking.py`, `track_forward` / `track_backward`): implicit, upstream, no dispersion, over the flow model's own steps (every step must be in the budget file; checked from TOTIM/DELT). Storage terms (STO-SS, STO-SY, package STORAGE, CSUB storage) leave the term table and act through the node volumes: $V^{new}c^n - V^{old}c^{n-1} = \Delta t[\sum_j q_{ji}c_j + s - (O+r)c]$. The node residual $r$ leaves at the node's fraction (as GWT's FLOW_IMBALANCE_CORRECTION; option `flow_error_correction`, default on). Each step's matrix is an M-matrix (row sums $V^{old}+\Delta t\,\mathrm{Src}$) with its own sparsity; the existing `factorize` (topological / block / lu) is used per step, on $A$ forward and $A^T$ backward; no closed-loop isolation is needed.
  - **Volume modes** (`TrackingConfig.volume_mode`): `"gwt"` copies MF6 GWT: $V^{new}$ = porosity × saturated volume (package nodes: STORAGE VOLUME), $V^{old} = V^{new} + \Delta t\,S$ (MST `mst_fc_sto`, APT `apt_get_volumes`), plus SFT's rule that a reach with zero storage flow keeps the previous step's volume (`sft_get_volumes`; 0 before step 1). Within a step the water balance closes, but between steps $V^{old,n+1} \ne V^{new,n}$ whenever porosity ≠ Sy, so tagged water appears or disappears at step boundaries (reported as `volume_adjustment`; on model 6 the initial water loses 30,400 of 15.9 million m³ this way). `"flow"`: volumes carried by the storage flows from porosity × saturated volume at the start; water and tagged-mass balances exact by construction; porosity only sets the starting volume. On model 6 (porosity 0.3, Sy 0.2) the modes differ by ≤1.2e-4 in c and ≤6e-3 in the adjoint fraction.
  - **Default volume mode (decided 2026-10-02):** `"flow"`, so every node's water balance is exact; `"gwt"` is kept for comparison with MF6 GWT.
  - **Adjoint and duality:** $A^{nT}w^n = \Delta t\,d^n + B^{n+1}w^{n+1}$ from the end; $w^n$ is the fraction of the water in a node at the start of step $n$ (or entering it during step $n$) that leaves through the destination before the end. Exact identity: forward tagged outflow $= \sum_n \Delta t\,s^n\cdot w^n + V^{old,1}c^0\cdot w^1$ (`tracking_duality`); backward closure (all sources + initial water = destination outflow) is exact except in gwt mode with SFR nodes. Extra adjoint columns give the fraction leaving through any sink and the fraction still stored at the end; the rest (`fraction_unaccounted`) is the flow-error correction and, in gwt mode, the volume adjustments.
  - **Validation:** GWT via FMI on model 6 (RCH, CHD+RIV, initial water, RCH+initial, RCH without correction): agreement ≤2e-15 at every step; model 7 network (SFR nodes + MVR) against GWT with SFT + MVT: ≤1e-14 for cells and reaches. Duality ≤1e-14 relative (tests: 1e-10) on model 6, model 6 split into 4 models, model 9 (LAK + UZF nodes, transient period) and model 7 (SFR + MVR); flow-mode water and tagged balances ≤1e-12. New model 10 (model 1's flows held 4e5 d): c at the end and $w$ at the start match the steady `source_fraction` / `fraction_through` to 1e-8 / 6e-7.
  - **Output:** per-step series (`keep_series`), balance tables, outflow by package and by sink group, volume from by package and source group; `export.tracking_dataset` (netCDF, time dimension) and `export.save_tracking_npz` (one npz per step). Memory is one (steps × nodes) array per group and output.

### Phase 5: research (optional)
- Quantify the grid-dependent numerical dispersion against flux-weighted particles.
- Prototype Chowdhury-style face-to-face routing within cells on DIS grids [CHO16].
- *Status (2026-10-02): done.* Write-up in [`docs/dispersion_study.md`](docs/dispersion_study.md); study in `studies/dispersion/workflow.py` (about 3 minutes end to end). Notes:
  - **References:** the analytical capture zone of uniform flow plus a well (Javandel & Tsang 1986; CHD perimeter at the analytical heads, flow along the rows and at 30°) and MF6 PRT on the finest DIS grid of a model-1-like problem. DIS 200 to 12.5 m and Voronoi DISV of matching size.
  - **Findings:** the F = 0.1 to 0.9 edge band of full mixing narrows only as about h^0.5 (1.2 to 12 cells wide). F = 0.5 is within 5 % in area of the reference for h ≤ 50 m. F ≥ 0.1 always covered the reference zone but is 8 to 90 % too large. Shares by source package and mean travel time are insensitive (≤ 2 to 4 %). Voronoi grids are not less dispersive.
  - **Face routing** (`gwsource.experimental.face_routing`, outside the stable API):
    - Pollock-field partition of each inflow face among the outflow faces (closed form; reproduces Chowdhury's case formulas and his 3×3 example exactly). Recharge enters through the top face (IFACE 6). Cells with internal sources or sinks, or with flow through both vertical faces, stay fully mixed.
    - Graph on connections, solved with the existing solvers; closure exact.
    - Removes 35 to 70 % of the excess spreading but keeps the h^0.5 rate (water is still mixed across each face).
    - Recommendation: keep it experimental until it has a 3D partition, a vectorised plan and forward mode.
  - **Tracking:** new `TrackingConfig.substeps` (equal transport sub-steps per flow step, volumes interpolated). substeps = 1 reproduces the previous results bit for bit; duality and closure stay exact. With 2000 d flow steps, one step per flow step doubles the early arrival at the well; 16 sub-steps remove this.
  - Optional 3-layer partially penetrating case not run (the prototype is 2D; in test model 2 only bottom-layer cells are routed).

## 6. Validation plan

| Test | Purpose |
|---|---|
| [FB13] 3×3 worked example (net mode) | Exact reproduction of the published numbers |
| Hand-built graphs (chain, split, merge, weak sink, cycle) | Unit tests of assembly and solve, with analytical answers |
| Topological path vs splu on acyclic graphs | The two solvers must agree to machine precision |
| Closure and residuals | $\sum$ volume from = destination sink inflow, up to the reported model residual |
| Forward/backward duality | Flow from set S to set D is the same whichever mode computes it |
| Boundary-control maps | The rows of $\mathbf F$ over all sink terms sum to 1 |
| GWT unit concentration, run long enough on constant flow to reach equilibrium, no dispersion, upstream advection | Forward fractions match the transport solution (gross accounting) |
| PRT, flux-weighted | Capture-zone extent and mean travel time are consistent; this measures how much full mixing spreads the zone |
| DIS vs DISV refinement series | Documents the sensitivity to cell size |
| Large-model benchmark (about 1M cells) | Runtime and memory per time step, factorisation fill-in |

## 7. Risks and how to handle them

| Risk | Mitigation |
|---|---|
| FloPy `develop` or the MF6 nightly build changes or breaks something | Record the FloPy commit and MF6 version in every test run; CI against the latest releases as well (D3); regenerate FloPy's MF6 classes after every update |
| DISU models without vertices | Core outputs still work; area read from the DISU input; maps and flux outputs disabled, with a clear message |
| Node numbering mismatch between package terms (user nodes) and FLOW-JA-FACE (reduced nodes) | An explicit node map from the `.grb` IDOMAIN; a test model with inactive cells |
| Sign conventions for storage and package terms | One shared sign convention in `mf6io` (positive = into the cell), with a unit test for each term type |
| Sparse LU fill-in on large 3D models | Topological fast path first, since most models with standard two-point flux are acyclic; iterative fallback |
| Pure recirculation loops with no exit (singular rows) | Detect when the solve fails; set those cells to zero and report them |
| Budget residuals in loosely converged models | Normalise as in §2.2–2.3 so the fractions stay bounded; report the residual alongside the closure check |
| Users comparing results with studies that used the reference method | Document the gross vs net differences; net mode for side-by-side runs |
| Implementation based on a published method that is also a commercial product | Clean-room implementation from the published papers only. The product name does not appear anywhere in code, docstrings, docs, test names or output names; cite the papers by author and year instead |

## 8. Decisions

Defaults adopted on 2026-10-02 so implementation can start. Any of them can be revisited.

- **D1. Package name:** `gwsource` (import name), distribution name `gw-source`.
- **D2. Licence:** MIT (changed from BSD-3-Clause on 2026-10-02).
- **D3. Versions:** development on FloPy `develop` and the MF6 nightly build. The oldest supported releases are fixed at the first package release.
- **D4. Output formats:** npz in Phase 1; netCDF (xarray) and GeoPackage in Phase 2.
- **D5. Numba:** not used; scipy only unless the Phase 2 benchmark shows a need.
- **D6. Real-world test model:** the USGS Neversink/Rondout MF6 model (public domain), against its published MODPATH 7 contributing areas for eight priority wells [COR22]; calibrated model, 358-realisation ensemble and five pumping scenarios in `docs/neversink_study.md`.

Original options considered:

- **D1. Package name.** `gwsource` is a placeholder.
- **D2. Licence.** The likely choice is BSD-3 or MIT, matching FloPy and pyemu.
- **D3. Supported versions for users.** Development runs on FloPy `develop` and the MF6 nightly build (Phase 0). Still to decide: the oldest released versions the package promises to support. Proposed: the latest MF6 and FloPy releases at the time of the first package release, with a second CI job that tests against those releases.
- **D4. Output formats for the MVP.** Proposed: npz and netCDF, with GeoPackage in phase 2.
- **D5. Numba.** Use it for the topological sweep, or rely on scipy alone. Proposed: scipy only until the benchmark shows it is needed.
- **D6. First real-world test model.** An existing MF6 model, ideally one with a published SPZ or capture-zone comparison.
