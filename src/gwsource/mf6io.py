"""Read MODFLOW 6 binary grid (.grb) and budget (.cbc) files into a FlowStep.

Node numbering (checked on MF6 6.x nightly with IDOMAIN = 0 cells on DIS and DISU):
- The .grb file stores IA/JA in *user* node numbering for DIS, DISV and DISU. Cells removed by
  IDOMAIN (<= 0) keep an empty row (no diagonal either) and no other row points at them.
- FLOW-JA-FACE has NJA entries aligned with those IA/JA arrays, so it needs no remapping.
- List budget records (IMETH = 6) give the 1-based user node in ID1 and the bound number in ID2.
- Array budget records (IMETH = 1, e.g. STO-SS) hold one value per user node.
So every array is in user numbering; cells with IDOMAIN <= 0 are flagged inactive.

Sign convention: every budget term is positive INTO the cell, including storage (positive =
release from storage). MF6 writes the per-cell residual (sum of all flows into the cell) in the
diagonal of FLOW-JA-FACE; it is not a connection and is ignored here. DATA-* records (DATA-SPDIS,
DATA-SAT) are not flows and are skipped.

Cell area: DELR x DELC (DIS); vertex polygons (DISV, and DISU when vertices were written);
otherwise AREA from the DISU input file read with FloPy, or None if that is not available.

Water mover (checked on test model 7, DRN -> MVR -> SFR): a provider package with MOVER writes
two disjoint aquifer-side records, e.g. DRN (the part of the drain outflow that leaves the model)
and DRN-TO-MVR (the part handed to the mover). Both are outflows from the cell and together they
equal the drain's head-dependent flow, so both are kept as sink terms; the cell budget closes
against MF6's own residual with both, and would not close without the -TO-MVR record. Where the
mover sends the water (here into the stream, which may leak it back into the aquifer through
the SFR record) is a package-network question left to Phase 4. Records of one package share its
name (paknam2); the second and later records of a package in a step are named
'<package>:<text>' (e.g. 'DRN:DRN-TO-MVR') and keep the package as their parent.

Boundnames are not in the budget file. ID2 of a list record is the bound's position (1-based)
in the package's list for the current stress period, so read_boundnames() loads the list input
of every package with BOUNDNAMES through FloPy, per stress period (a period without a PERIOD
block reuses the last list, as in MF6). SFR boundnames come from its PACKAGEDATA (ID2 = reach).
"""

from dataclasses import dataclass
from pathlib import Path

import flopy
import numpy as np

from .flowstep import FlowStep, Package

COMMENT_CHARS = ("#", "!", "//")


@dataclass
class ModelFiles:
    """Paths of the files of one GWF model that a FlowStep is read from."""

    model: str
    grb_file: Path
    budget_file: Path
    dis_file: Path
    dis_type: str
    nam_file: Path | None = None
    tdis_file: Path | None = None


@dataclass
class GridData:
    """Connectivity and geometry read from a binary grid file."""

    grid_type: str
    ia: np.ndarray
    ja: np.ndarray
    idomain: np.ndarray
    shape: tuple[int, ...]
    area: np.ndarray | None


# ---------------------------------------------------------------- name-file parsing


def _block_lines(path: Path, block: str) -> list[list[str]]:
    """Return the tokenised lines inside 'BEGIN block' ... 'END block' of an MF6 input file."""
    lines, inside = [], False
    for raw in Path(path).read_text().splitlines():
        tokens = raw.split()
        if not tokens or tokens[0].startswith(COMMENT_CHARS):
            continue
        key = tokens[0].upper()
        if key == "BEGIN" and len(tokens) > 1 and tokens[1].upper() == block.upper():
            inside = True
        elif key == "END" and inside:
            return lines
        elif inside:
            lines.append(tokens)
    return lines


def _find_model_entry(ws: Path, model: str | None) -> tuple[str, Path]:
    """Return (model name, name file) of a GWF model listed in mfsim.nam."""
    entries = [t for t in _block_lines(ws / "mfsim.nam", "MODELS") if t[0].upper() == "GWF6"]
    assert entries, f"no GWF6 model in {ws / 'mfsim.nam'}"
    if model is None:
        assert len(entries) == 1, "several GWF models; pass model= to choose one"
        return entries[0][2], ws / entries[0][1]
    match = [t for t in entries if t[2].lower() == model.lower()]
    assert match, f"model {model!r} not found in mfsim.nam"
    return match[0][2], ws / match[0][1]


def _fileout(path: Path, keyword: str) -> str | None:
    """Return the file name of a '<keyword> FILEOUT <name>' option in an input file, if present."""
    for tokens in _block_lines(path, "OPTIONS"):
        if len(tokens) >= 3 and tokens[0].upper() == keyword and tokens[1].upper() == "FILEOUT":
            return tokens[2]
    return None


def find_model_files(ws: str | Path, model: str | None = None) -> ModelFiles:
    """Locate the binary grid and budget files of a GWF model from its name and OC files."""
    ws = Path(ws)
    name, nam_file = _find_model_entry(ws, model)
    packages = {t[0].upper(): t[1] for t in _block_lines(nam_file, "PACKAGES")}
    dis_type = next(k for k in ("DIS6", "DISV6", "DISU6") if k in packages)
    dis_file = ws / packages[dis_type]
    assert "OC6" in packages, f"no OC package in {nam_file}"
    budget = _fileout(ws / packages["OC6"], "BUDGET")
    assert budget is not None, "OC does not save a budget file (BUDGET FILEOUT)"
    grb = _fileout(dis_file, "GRB6") or f"{packages[dis_type]}.grb"
    timing = {t[0].upper(): t[1] for t in _block_lines(ws / "mfsim.nam", "TIMING")}
    tdis = ws / timing["TDIS6"] if "TDIS6" in timing else None
    return ModelFiles(name, ws / grb, ws / budget, dis_file, dis_type[:-1], nam_file, tdis)


def _option_value(path: Path | None, keyword: str) -> str | None:
    """Return the value of '<keyword> <value>' in an input file's OPTIONS block, if present."""
    if path is None or not Path(path).is_file():
        return None
    for tokens in _block_lines(path, "OPTIONS"):
        if tokens[0].upper() == keyword and len(tokens) > 1:
            return tokens[1].lower()
    return None


def read_units(files: ModelFiles) -> dict[str, str]:
    """Return {'length': ..., 'time': ...} from DIS LENGTH_UNITS and TDIS TIME_UNITS."""
    return {
        "length": _option_value(files.dis_file, "LENGTH_UNITS") or "unknown",
        "time": _option_value(files.tdis_file, "TIME_UNITS") or "unknown",
    }


# ---------------------------------------------------------------- binary grid


def polygon_areas(vertices: np.ndarray, iavert: np.ndarray, javert: np.ndarray) -> np.ndarray:
    """Return plan areas of polygons given vertex xy and 0-based CSR vertex lists (shoelace)."""
    x, y = vertices[javert, 0], vertices[javert, 1]
    nxt = np.arange(1, len(javert) + 1)
    nxt[iavert[1:] - 1] = iavert[:-1]  # last vertex of each polygon wraps to its first
    cross = x * y[nxt] - x[nxt] * y
    return 0.5 * np.abs(np.add.reduceat(cross, iavert[:-1]))


def _vertex_areas(grb: flopy.mf6.utils.MfGrdFile) -> np.ndarray | None:
    """Return cell-polygon areas from the grid file's vertices, or None if it has none."""
    if grb.iavert is None or grb.verts is None:
        return None
    verts = np.asarray(grb.verts, dtype=float)[:, -2:]  # FloPy prefixes DISU vertices with an id
    return polygon_areas(verts, np.asarray(grb.iavert), np.asarray(grb.javert))


def _grid_area(grb: flopy.mf6.utils.MfGrdFile) -> np.ndarray | None:
    """Return the plan area of every user node, or None if the grid file has no geometry."""
    if grb.grid_type == "DIS":
        cell = np.outer(grb.delc, grb.delr).ravel()
        return np.tile(cell, grb.nlay)
    areas = _vertex_areas(grb)
    if areas is not None and grb.grid_type == "DISV":
        return np.tile(areas, grb.nlay)
    return areas


def _grid_shape(grb: flopy.mf6.utils.MfGrdFile) -> tuple[int, ...]:
    """Return the array shape of the grid: (nlay, nrow, ncol), (nlay, ncpl) or (nodes,)."""
    if grb.grid_type == "DIS":
        return (int(grb.nlay), int(grb.nrow), int(grb.ncol))
    if grb.grid_type == "DISV":
        return (int(grb.nlay), int(grb.ncpl))
    return (int(grb.nodes),)


def read_grid(grb_file: str | Path) -> GridData:
    """Read connectivity, IDOMAIN, shape and (if available) cell areas from a binary grid file."""
    grb = flopy.mf6.utils.MfGrdFile(str(grb_file), verbose=False)
    assert grb.grid_type in ("DIS", "DISV", "DISU"), f"unsupported grid type {grb.grid_type}"
    idomain = np.ravel(grb.idomain) if grb.idomain is not None else np.ones(grb.nodes, int)
    return GridData(
        grid_type=grb.grid_type,
        ia=np.asarray(grb.ia, dtype=np.int64),
        ja=np.asarray(grb.ja, dtype=np.int64),
        idomain=np.asarray(idomain, dtype=int),
        shape=_grid_shape(grb),
        area=_grid_area(grb),
    )


def read_disu_area(ws: str | Path, model: str) -> np.ndarray:
    """Return AREA from a model's DISU input, read with FloPy."""
    sim = flopy.mf6.MFSimulation.load(sim_ws=str(ws), load_only=["disu"], verbosity_level=0)
    gwf = sim.get_model(model)
    return np.asarray(gwf.disu.area.array, dtype=float).ravel()


# ---------------------------------------------------------------- boundnames


@dataclass
class BoundnameTable:
    """Boundnames per package and stress period: {PACKAGE: {first kper: names by bound - 1}}."""

    periods: dict[str, dict[int, np.ndarray]]

    def names(self, package: str, kper: int, bounds: np.ndarray) -> np.ndarray:
        """Return the boundname of each 1-based bound number of a package in stress period kper."""
        bounds = np.asarray(bounds, dtype=np.int64)
        out = np.full(len(bounds), "", dtype=object)
        by_period = self.periods.get(package.upper())
        if not by_period:
            return out
        defined = [k for k in by_period if k <= kper]
        if not defined:
            return out
        names = by_period[max(defined)]
        assert bounds.size == 0 or bounds.max() <= len(names), (
            f"{package}: bound number beyond the stress-period list in period {kper}"
        )
        return names[bounds - 1] if bounds.size else out


def _name_file_packages(nam_file: Path) -> list[tuple[str, Path, str]]:
    """Return (ftype without '6', file, package name) of each entry of a model name file."""
    entries = []
    counts: dict[str, int] = {}
    for tokens in _block_lines(nam_file, "PACKAGES"):
        ftype = tokens[0].upper().removesuffix("6")
        counts[ftype] = counts.get(ftype, 0) + 1
        pname = tokens[2] if len(tokens) > 2 else f"{ftype}-{counts[ftype]}"
        entries.append((ftype, nam_file.parent / tokens[1], pname.upper()))
    return entries


def _has_boundnames(path: Path) -> bool:
    """Return True if an input file sets the BOUNDNAMES option."""
    return any(t[0].upper() == "BOUNDNAMES" for t in _block_lines(path, "OPTIONS"))


def _names_array(records) -> np.ndarray:
    """Return the boundname column of a FloPy recarray as an object array ('' if missing)."""
    if records is None or "boundname" not in (records.dtype.names or ()):
        return np.zeros(0, dtype=object) if records is None else np.full(len(records), "", object)
    return np.array([str(b) if b is not None else "" for b in records["boundname"]], dtype=object)


def _package_boundnames(package) -> dict[int, np.ndarray]:
    """Return {first kper: names} for a FloPy package with list or SFR package data."""
    if package.package_type == "sfr":
        return {0: _names_array(package.packagedata.get_data())}
    spd = getattr(package, "stress_period_data", None)
    assert spd is not None, (
        f"boundnames of {package.package_type.upper()} packages are not supported yet"
    )
    return {int(k): _names_array(v) for k, v in (spd.get_data() or {}).items()}


def read_boundnames(files: ModelFiles, ws: str | Path) -> BoundnameTable:
    """Load, through FloPy, the boundnames of every package of a model that has BOUNDNAMES."""
    entries = [e for e in _name_file_packages(files.nam_file) if _has_boundnames(e[1])]
    if not entries:
        return BoundnameTable({})
    load_only = sorted({ftype.lower() for ftype, _, _ in entries})
    sim = flopy.mf6.MFSimulation.load(sim_ws=str(ws), load_only=load_only, verbosity_level=0)
    gwf = sim.get_model(files.model)
    periods = {}
    for _, _, pname in entries:
        package = gwf.get_package(pname.lower())
        assert package is not None, f"package {pname} not loaded by FloPy"
        periods[pname] = _package_boundnames(package)
    return BoundnameTable(periods)


# ---------------------------------------------------------------- budget file


def available_steps(budget_file: str | Path) -> list[tuple[int, int]]:
    """Return the 0-based (kstp, kper) of every time step saved in a budget file."""
    cbc = flopy.utils.CellBudgetFile(str(budget_file))
    return [(int(k), int(p)) for k, p in cbc.get_kstpkper()]


def _step_record_indices(cbc: flopy.utils.CellBudgetFile, kstpkper: tuple[int, int]) -> list[int]:
    """Return the record indices of one (0-based) time step."""
    kstp, kper = kstpkper
    rec = cbc.recordarray
    idx = np.flatnonzero((rec["kstp"] == kstp + 1) & (rec["kper"] == kper + 1))
    assert idx.size, f"time step {kstpkper} not in budget file"
    return [int(i) for i in idx]


def _decode(value) -> str:
    """Decode and strip a budget-header text field."""
    return value.decode().strip() if isinstance(value, bytes) else str(value).strip()


def _array_term(data: np.ndarray, active: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (0-based cell, flow) for an IMETH=1 array record, one entry per active cell."""
    flow = np.asarray(data, dtype=float).ravel()
    assert flow.size == active.size, "array budget record does not match the number of nodes"
    cells = np.flatnonzero(active)
    return cells, flow[cells]


def _record_package(parent: str, text: str, used: set[str]) -> Package:
    """Return the Package of a record; a second record of the same package gets '<pkg>:<text>'."""
    name = parent if parent not in used else f"{parent}:{text}"
    assert name not in used, f"duplicate budget record {name}"
    used.add(name)
    return Package(name=name, text=text, parent=parent if name != parent else "")


def _read_terms(cbc, indices: list[int], active: np.ndarray) -> dict:
    """Collect external term entries and the FLOW-JA-FACE array from one step's records."""
    out = {"cell": [], "flow": [], "package": [], "bound": [], "packages": [], "flowja": None}
    used: set[str] = set()
    for idx in indices:
        header = cbc.recordarray[idx]
        text, imeth = _decode(header["text"]), int(header["imeth"])
        data = cbc.get_record(idx, full3D=False)
        if text == "FLOW-JA-FACE":
            assert imeth == 1, "FLOW-JA-FACE exchange records (multi-model) are not supported yet"
            out["flowja"] = np.asarray(data, dtype=float).ravel()
            continue
        if text.startswith("DATA-"):
            continue
        if imeth == 6:
            parent = _decode(header["paknam2"]) or text
            cells, flow, bound = data["node"] - 1, data["q"], data["node2"]
        else:
            parent = text
            cells, flow = _array_term(data, active)
            bound = cells + 1
        out["packages"].append(_record_package(parent, text, used))
        out["cell"].append(np.asarray(cells, dtype=np.int64))
        out["flow"].append(np.asarray(flow, dtype=float))
        out["bound"].append(np.asarray(bound, dtype=np.int64))
        out["package"].append(np.full(len(cells), len(out["packages"]) - 1, dtype=np.int64))
    assert out["flowja"] is not None, "FLOW-JA-FACE not saved for this time step"
    return out


def _concat(parts: list[np.ndarray], dtype) -> np.ndarray:
    """Concatenate a possibly empty list of arrays."""
    return np.concatenate(parts).astype(dtype) if parts else np.zeros(0, dtype=dtype)


def _term_boundnames(
    table: BoundnameTable, packages: list[Package], term_package, term_bound, kper: int
) -> np.ndarray:
    """Return the boundname of every term entry (looked up by the record's parent package)."""
    out = np.full(len(term_bound), "", dtype=object)
    for p, package in enumerate(packages):
        sel = term_package == p
        out[sel] = table.names(package.parent or package.name, kper, term_bound[sel])
    return out


@dataclass
class StepReader:
    """Grid and budget file opened once; reads a FlowStep for any saved time step.

    The grid (IA/JA, IDOMAIN, areas) is read once and shared by every FlowStep it returns.
    """

    grid: GridData
    cbc: flopy.utils.CellBudgetFile
    area: np.ndarray | None = None
    boundnames: BoundnameTable | None = None
    notes: dict | None = None

    @property
    def steps(self) -> list[tuple[int, int]]:
        """0-based (kstp, kper) of every saved time step."""
        return [(int(k), int(p)) for k, p in self.cbc.get_kstpkper()]

    def step_length(self, kstpkper: tuple[int, int]) -> float:
        """Return the length (DELT) of a saved time step, from the budget record header."""
        return float(self.cbc.recordarray[_step_record_indices(self.cbc, kstpkper)[0]]["delt"])

    def read(self, kstpkper: tuple[int, int] = (0, 0)) -> FlowStep:
        """Read one time step into a FlowStep."""
        active = self.grid.idomain > 0
        indices = _step_record_indices(self.cbc, kstpkper)
        terms = _read_terms(self.cbc, indices, active)
        assert terms["flowja"].size == self.grid.ja.size, "FLOW-JA-FACE length does not match NJA"
        term_package = _concat(terms["package"], np.int64)
        term_bound = _concat(terms["bound"], np.int64)
        names = None
        if self.boundnames is not None:
            names = _term_boundnames(
                self.boundnames, terms["packages"], term_package, term_bound, kstpkper[1]
            )
        header = self.cbc.recordarray[indices[0]]
        return FlowStep(
            ia=self.grid.ia,
            ja=self.grid.ja,
            flowja=terms["flowja"],
            term_cell=_concat(terms["cell"], np.int64),
            term_flow=_concat(terms["flow"], float),
            term_package=term_package,
            term_bound=term_bound,
            packages=terms["packages"],
            term_boundname=names,
            area=self.area if self.area is not None else self.grid.area,
            active=active,
            grid_shape=self.grid.shape,
            grid_type=self.grid.grid_type,
            kstpkper=tuple(int(k) for k in kstpkper),
            totim=float(header["totim"]),
            notes={**(self.notes or {}), "delt": float(header["delt"])},
        )


def open_files(
    grb_file: str | Path, budget_file: str | Path, area: np.ndarray | None = None
) -> StepReader:
    """Open a binary grid file and a budget file once for reading many time steps."""
    notes = {"grb_file": str(grb_file), "budget_file": str(budget_file)}
    return StepReader(
        grid=read_grid(grb_file),
        cbc=flopy.utils.CellBudgetFile(str(budget_file)),
        area=None if area is None else np.asarray(area, dtype=float),
        notes=notes,
    )


def open_model(
    ws: str | Path,
    model: str | None = None,
    area: np.ndarray | None = None,
    boundnames: bool = False,
) -> StepReader:
    """Open a GWF model's grid and budget files once; optionally load its boundnames (FloPy).

    For DISU grids without vertices the cell area is read from the DISU input (AREA).
    """
    files = find_model_files(ws, model)
    reader = open_files(files.grb_file, files.budget_file, area=area)
    if reader.area is None and reader.grid.area is None and files.dis_type == "DISU":
        reader.area = read_disu_area(ws, files.model)
    if boundnames:
        reader.boundnames = read_boundnames(files, ws)
    reader.notes.update({"model": files.model, "units": read_units(files)})
    return reader


def read_step_files(
    grb_file: str | Path,
    budget_file: str | Path,
    kstpkper: tuple[int, int] = (0, 0),
    area: np.ndarray | None = None,
) -> FlowStep:
    """Read one time step from a binary grid file and a budget file into a FlowStep."""
    return open_files(grb_file, budget_file, area=area).read(kstpkper)


def read_step(
    ws: str | Path,
    model: str | None = None,
    kstpkper: tuple[int, int] = (0, 0),
    area: np.ndarray | None = None,
    boundnames: bool = False,
) -> FlowStep:
    """Read one time step of a GWF model in a simulation folder into a FlowStep.

    For DISU grids without vertices the cell area is read from the DISU input (AREA).
    boundnames=True also fills FlowStep.term_boundname from the package input (FloPy).
    """
    return open_model(ws, model, area=area, boundnames=boundnames).read(kstpkper)
