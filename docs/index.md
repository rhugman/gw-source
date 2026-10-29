# gwsource

`gwsource` post-processes MODFLOW 6 groundwater-flow output to answer two questions for every cell:
where does its water go (capture), and where did it come from (fate). It reads the binary grid and
cell-by-cell budget files that a MODFLOW 6 model saves, treats the water in each cell as fully mixed,
and solves the trace as one sparse system of linear equations. The method builds on the
cell-mixing flow tracing of Foley & Black (2013) and Black & Foley (2013).

```{toctree}
:maxdepth: 2

installation
tutorials/index
api/index
```
