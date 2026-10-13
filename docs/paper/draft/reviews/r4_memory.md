# Round 4: peak memory of one steady Neversink trace (decision 40, F6)

Measured 2026-10-13 on branch `paper-draft` at 0082a1e (`src/gwsource` of this worktree; numpy 2.5.3, scipy 1.18.1).

## What was run

The trace of §3.3 ("A steady trace of nine groups on the 1.68-million-cell Neversink model took 2–3 s") is the streams-as-cells trace of `studies/neversink/workflow.trace_wells(ws)`: `gs.read_step(ws, boundnames=True)` on the calibrated (optimal) model, then `gs.backward(step, well_groups(step))`, with nine groups (the eight priority wells, one group each, plus `priority`, all eight together). The model is the published-solver run in `studies/neversink/output/optimal` of the main checkout, read only. Nothing is written.

The script (`$TMPDIR/r4mem/trace_memory.py`, not kept in the repository) does exactly these two calls and prints the process's peak resident set size (`resource.getrusage(RUSAGE_SELF).ru_maxrss`) after the load and after the trace. With the argument `load` it stops after the load; with `one` it traces only the `priority` group.

```
export PYTHONPATH=src
python $TMPDIR/r4mem/time_l.py ~/miniforge3/envs/gw-source/bin/python $TMPDIR/r4mem/trace_memory.py         # nine groups
python $TMPDIR/r4mem/time_l.py ~/miniforge3/envs/gw-source/bin/python $TMPDIR/r4mem/trace_memory.py load    # load only
```

`/usr/bin/time -l` could not be used: inside the Claude Code sandbox it fails (`time: sysctl kern.clockrate: Operation not permitted`) before printing the resource usage, and running it outside the sandbox was not permitted. `time_l.py` is a stand-in: it starts the command and reads the child's `ru_maxrss` from `os.wait4`, the same rusage field that `time -l` prints as "maximum resident set size". The in-process values agree with it to the byte. To repeat with `time -l` outside the sandbox:

```
PYTHONPATH=src /usr/bin/time -l ~/miniforge3/envs/gw-source/bin/python trace_memory.py
```

## Machine

- Apple M4 Max, 16 cores (`machdep.cpu.brand_string`, `hw.ncpu`)
- `hw.memsize` = 68,719,476,736 bytes (64 GB)
- macOS 26.3.1

## Results

| Run | Repeats | Peak RSS (GB) | Load (s) | Trace (s) | Whole process, wall (s) |
|---|---|---|---|---|---|
| Load only (baseline) | 2 | 0.52 (0.519, 0.520) | 1.0 | – | 2.8 |
| Load + nine-group trace | 3 | **2.52** (2.48 to 2.55) | 1.0 to 1.2 | 1.4 to 1.5 | 4.4 to 4.6 |
| Load + one-group trace (`priority`) | 2 | 0.98 (0.970, 0.984) | 1.2 to 1.3 | 0.7 to 0.75 | 3.8 to 4.2 |

- The peak RSS after the load, inside the trace runs, is 0.50 to 0.52 GB, the same as the load-only runs. The trace itself adds about 2.0 GB for nine groups.
- One group adds about 0.47 GB. Each further group adds about (2.52 − 0.98) / 8 = 0.19 GB, about 115 MB per group per million cells on 1.68 million cells. The fixed cost of the trace is then about 0.28 GB.
- Load plus trace takes 2.4 to 2.7 s, consistent with the "2–3 s" of §3.3. The trace alone (`gs.backward`) takes 1.4 to 1.5 s. Whole-process wall time includes about 1.7 s of Python start-up and imports.
- Each run printed the OpenMP warning `OMP: Warning #179: Function Can't set size of /tmp file failed` (the sandbox blocks the shared-memory file); the runs completed and the numbers above are unaffected as far as can be told.

## Bearing on §3.3

§3.3 says each group costs "about 90 MB of memory per million cells", so 100 wells traced separately would need about 15 GB (an estimate, not run; source PLAN Phase 2 notes). The measured marginal cost here is about 115 MB per group per million cells. With it, 100 separate wells on this model would need about 0.5 + 0.3 + 100 × 0.19 ≈ 20 GB, not 15 GB. The writer may want to quote the measured figure: "a steady trace of nine groups peaked at 2.5 GB of memory, of which 0.5 GB was the loaded budget (Apple M4 Max, 64 GB)", and revise the per-group figure to about 0.2 GB per group on this model.
