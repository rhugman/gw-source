# PRT aborts (SIGILL) when a particle is in a cell whose saturated thickness rounds to zero

Draft upstream issue for MODFLOW 6. Not filed yet.

## Summary

A PRT simulation aborts with `Program received signal SIGILL: Illegal instruction.` (exit
status 132; no MODFLOW error message, the list files stop without one and the track file is
empty) as soon as a particle
is in a DIS cell whose GWF saturation is a positive film so small that
`bot + sat * (top - bot)` equals `bot` in double precision. It happens for a particle released
in that cell and for a particle that flows into it. One particle is enough. The threshold is
exactly that rounding limit: saturation below half a unit in the last place of the cell bottom
elevation, divided by the cell thickness. Cells with the same film at datum 0 m track normally.

Such films arise with NEWTON: a head slightly above the cell bottom gives a very small quadratic
saturation in DATA-SAT (in the reproducer a head 1.1e-10 m above the bottom of a 10 m cell gives
a saturation of 6.2e-17).

## Environment

- MODFLOW 6 `6.9.0.dev0+67116fb.dirty`: built locally from develop at commit
  67116fb4c217c6886ac0d64f2e1b73eb1308e855 (2026-09-23). The version string says the build
  tree had local changes; I have not identified them. The PRT source files cited below are
  those of that commit.
- Compiler: GCC 13.4.0 gfortran (Homebrew). The compiler options recorded in the binary
  include `-mcpu=apple-m1 -O3 -O1 ... -ffpe-trap=overflow,zero,invalid`.
- macOS 26.3.1 (Darwin 25.3.0), Apple Silicon (arm64).
- flopy 3.12.0.dev0, Python 3.12, numpy 2.5.

## Steps to reproduce

```
python make_repro.py /path/to/mf6
```

The script needs flopy and numpy only. It writes and runs everything under `_work/`:

1. A GWF model: one layer, one row, five columns of 100 m x 100 m, 10 m thick, convertible,
   NEWTON, steady state. Recharge 1e-3 m/d everywhere, CHD in column 2 at bottom + 5 m, a drain
   at the cell bottom with conductance 1e12 m2/d in column 0 and one with 1e2 m2/d in column 4.
   Column 0 ends with a film (head - bottom 1.1e-10 m, saturation 6.2e-17); columns 1 to 4 are
   normally wet (saturation 0.1 to 0.5). Built at three datums (cell bottom 300 m, 0 m and
   1000 m); heads relative to the bottom and saturations are the same at all three.
2. Separate PRT simulations, each with one particle at the cell centre, local z 0.5, PRP options
   LOCAL_Z, EXTEND_TRACKING, STOP_AT_WEAK_SINK, EXIT_SOLVE_TOLERANCE 1e-5 (one case with
   LOCAL_Z only), FMI reading the GWF head and budget files, EMS.
3. A bisection of the abort threshold: the DATA-SAT value of column 0 is overwritten in a copy
   of the budget file (nothing else changed) and bisected in log10 between 1e-17 and 1e-10
   (40 steps).

## Results

| Datum (cell bottom) | Release | Result |
|---|---|---|
| 300 m | column 0 (the film cell) | SIGILL, exit status 132 |
| 300 m | column 1 (flows into the film cell) | SIGILL, exit status 132 |
| 300 m | column 3 (flows to the column 4 drain) | normal termination, ends in column 4 (istatus 5) |
| 300 m | column 0, LOCAL_Z only | SIGILL, exit status 132 |
| 300 m | column 0, DATA-SAT of column 0 set to 0 | normal termination, ends in column 0 (istatus 3) |
| 300 m | column 1, DATA-SAT of column 0 set to 0 | normal termination, ends in column 0 (istatus 3) |
| 0 m | column 0 (same film) | normal termination, ends in column 0 (istatus 5) |
| 1000 m | column 0 (same film) | SIGILL, exit status 132 |

istatus 3: terminated in a weak sink cell; 5: terminated in a cell with no exit face.

Threshold (10 m thick cell):

| Cell bottom | Aborts below saturation | `bot + sat * 10 > bot` in double precision from |
|---|---|---|
| 300 m | 2.842171e-15 | 2.842171e-15 |
| 1000 m | 5.684342e-15 | 5.684342e-15 |

The bisection brackets agree with the rounding limit to the printed seven digits at both
datums, and the limit doubles with the binary exponent of the bottom elevation (half of the
spacing of doubles near 300 m is 2.84e-14 m, near 1000 m 5.68e-14 m).

The same happened in a regional steady-state NEWTON model (4 layers, 1.68 million cells): a
single particle released in a cell with saturation 1.4e-16, bottom 403.35 m and thickness
35.58 m aborted the run. In that model 29 cells have a saturation between 0 and 1e-10; in two of
them (saturation 1.4e-16 and 5.5e-16) `bot + sat * (top - bot)` rounds to `bot`, in the other 27
(2.1e-15 to 4.7e-13) it does not.

## Expected

Either the particle is tracked (the cell has a positive saturated thickness), or the cell is
treated as dry (pass to bottom), or the run stops with an error message that names the cell.

## Actual

```
Program received signal SIGILL: Illegal instruction.

Backtrace for this error:
```

The backtrace addresses, resolved with `atos` against the (unstripped) binary:

```
_gfortrani_show_backtrace
_gfortrani_backtrace_handler
__methoddismodule_MOD_load_cell + 151
__methoddismodule_MOD_load_dis + 147
__methodmodule_MOD_track + 99
__methoddismodule_MOD_apply_dis + 43
__prtmodule_MOD_prt_solve + 967
__explicitsolutionmodule_MOD_solve
__explicitsolutionmodule_MOD_sln_ca
__solutiongroupmodule_MOD_sgp_ca
__mf6coremodule_MOD_mf6dotimestep
__mf6coremodule_MOD_mf6update
__mf6coremodule_MOD_mf6run
main
```

## Suspected cause

The crash is in `MethodDisType%load_cell` (backtrace above). The line is inferred from the
source; the binary has no line information.

- `src/Model/ParticleTracking/prt-fmi.f90` (line 122): a cell counts as wet
  (`ibdgwfsat0 = 1`) whenever `gwfsat > 0`.
- `src/Solution/ParticleTracker/Method/MethodDis.f90`, `load_cell_properties` (lines 366-368):
  `defn%top = dis%bot(ic) + gwfsat(ic) * (dis%top(ic) - dis%bot(ic))`. For a film this rounds
  to `defn%top == defn%bot`.
- `load_cell` (line 107): `dz = cell%defn%top - cell%defn%bot`, which is then exactly 0. The
  dry-cell branch (line 128) is skipped because `ibdgwfsat0 = 1`, and lines 138-139 compute
  `areax = dy * dz` and `term = factor / areax`, a division by zero.
- With `-ffpe-trap=zero` the division traps. On macOS arm64 a gfortran floating-point trap is
  delivered as SIGILL (a 10-line gfortran program built with the same trap flags and dividing
  by `(300 + 1e-15) - 300` gives the same message and exit status 132). On other platforms it
  would presumably be SIGFPE; without trapping the velocities would be infinite (not tested).

The exact match of the threshold with the rounding limit, and the datum dependence, support
this. `MethodDisv.f90` (lines 371-372) computes the cell top the same way, so DISV grids are
probably affected too; I have not tested DISV.

Possible fixes (suggestions only): compute the saturated thickness directly as
`gwfsat * (top - bot)` instead of as a difference of elevations, which is exact for any
positive saturation (velocities in such a cell are then very large but finite); or treat a cell
as dry when its saturated thickness is not positive (or below a tolerance), so that it gets the
pass-to-bottom method; or both.

## Workaround

- Leave out releases in cells with a saturation below a small threshold (we used 1e-15 and,
  more conservatively, 1e-10). This does not cover particles that flow into such a cell from
  elsewhere (column 1 case above).
- Or set DATA-SAT to 0 for such cells in a copy of the budget file before the PRT run, so that
  PRT treats them as dry. In the reproducer this makes both the release in the film cell and
  the particle flowing into it run normally.
