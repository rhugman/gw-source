# 7. Limitations

A trace is only as good as the flow model behind it. The checks of Section 2.5 confirm that the trace agrees with the model's flows. They cannot tell whether those flows are right. If a model's recharge is too high, for example, its contributing areas are too small. The trace still passes every check.

Because each cell is fully mixed, no cell can hold a sharp boundary between waters of different origin. Each cell mixes over its saturated thickness, so thick layers spread an area vertically as well as laterally. The transition band narrows only as about $h^{0.5}$ with cell size $h$ (Section 4.3). <!-- DS §2, §4, §5, Summary --> An experimental option, face-to-face routing, passes water between cell faces instead of mixing it in the cell. It removes 35–70 % of the excess spreading. It works in 2D only. It has no effect in cells with weak sinks or vertical through-flow. <!-- DS Summary, §4, §6 -->

Steady-state traces and snapshots assume steady-state flow. Their fractions say where water goes but not when it gets there, so they have no travel lag. Only the mean travel time of Section 2.6 adds timing. Transient tracking holds the flows constant within each time step. It carries water between steps by advection only, with upstream weighting and implicit time steps. By default it keeps one value per cell and time step in memory, for each group and each output. At 1.68 million cells and 121 steps, each such array takes about 1.6 GB. <!-- PLAN Phase 4B notes (Output); NS §1 (1,683,680 cells); 1,683,680 × 121 × 8 bytes = 1.63 × 10⁹; src/gwsource/transient.py TransientConfig.keep_series (default True: series[output][group] -> (n_steps, n_cells)) --> We estimate that nine groups, as in the Neversink study, would need about 15 GB for one output. <!-- 9 × 1.63 GB = 14.7 GB; estimate, not a run --> Memory can therefore limit transient tracking on large models with many time steps or groups. The code can keep only the last step's values instead. That saves the memory but gives up the time series.

Travel times and transient tracking need a porosity, which fractions of water do not (Sections 2.6 and 2.7). Their results are only as good as the porosity assigned.

Full mixing removes the need for a stop-or-pass rule at weak sinks while tracing. The modeller still decides how to credit a weak-sink well and which threshold on F draws the area (Sections 2.3 and 6.4).

The particle check of Section 6.4 relies on PRT, which supports DIS and DISV grids only. On DISU grids the full-mixing mean travel time is the only travel-time option. <!-- PLAN §2.8 -->

Transient tracking has been tested on synthetic models only (Sections 4.2 and 4.4). It has no real-world application yet, because the Neversink model is steady state.
