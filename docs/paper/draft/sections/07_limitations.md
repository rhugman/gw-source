# 7. Limitations

The checks test the tracing, not the flow model. A model with wrong recharge gives wrong areas that pass every check.

Full mixing treats each cell as one fully mixed volume of water. A cell therefore cannot hold a sharp boundary between waters of different origin. Each cell mixes over its saturated thickness, so thick layers spread an area vertically as well as laterally. How far an area spreads also depends on grid spacing. The transition band narrows only as about $h^{0.5}$ with cell size $h$ (Section 4.3). <!-- DS §2, §4, §5, Summary --> Face-to-face routing, an experimental option, removes 35–70 % of the excess spreading. It works in 2D only and has no effect in cells with weak sinks or vertical through-flow. <!-- DS Summary, §4, §6 -->

Steady traces and snapshots treat the flows as steady, so their results have no travel lag. Transient tracking holds the flows constant within each time step. It carries water between steps by advection only, with upstream weighting and implicit time steps. It needs the budget of every time step saved (OC SAVE BUDGET ALL). Its memory is one (steps × cells) array per group and output. At 1.68 million cells and 121 steps, each array takes about 1.6 GB. <!-- PLAN Phase 4B notes (Output); NS §1 (1,683,680 cells); 1,683,680 × 121 × 8 bytes = 1.63 × 10⁹ -->

Fractions of water need no porosity. Travel times and transient tracking do, because they depend on the volume of water in each cell (Sections 2.6 and 2.7). Their results are only as good as the porosity assigned.

Full mixing removes the stop-or-pass rule at weak sinks from the tracing only. The modeller still decides how to credit a weak-sink well and which threshold on F draws the area (Sections 2.3 and 6.5).

The particle check of Section 6.5 relies on PRT, which supports DIS and DISV grids only. On DISU grids the full-mixing mean travel time is the only travel-time option. <!-- PLAN §2.8 --> PRT can also stop with an error in cells wet only by a thin film of water ({SI: PRT abort in thin-film cells}). <!-- NS §3, §8 -->

Transient tracking has been tested on synthetic models only (Sections 4.2 and 4.4). It has no real-world application yet, because the Neversink model is steady state.
