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
    return ModelFiles(name, ws / grb, ws / budget, dis_file, dis_type[:-1])


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


def _read_terms(cbc, indices: list[int], active: np.ndarray) -> dict:
    """Collect external term entries and the FLOW-JA-FACE array from one step's records."""
    out = {"cell": [], "flow": [], "package": [], "bound": [], "packages": [], "flowja": None}
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
            name = _decode(header["paknam2"]) or text
            cells, flow, bound = data["node"] - 1, data["q"], data["node2"]
        else:
            name = text
            cells, flow = _array_term(data, active)
            bound = cells + 1
        out["packages"].append(Package(name=name, text=text))
        out["cell"].append(np.asarray(cells, dtype=np.int64))
        out["flow"].append(np.asarray(flow, dtype=float))
        out["bound"].append(np.asarray(bound, dtype=np.int64))
        out["package"].append(np.full(len(cells), len(out["packages"]) - 1, dtype=np.int64))
    assert out["flowja"] is not None, "FLOW-JA-FACE not saved for this time step"
    return out


def _concat(parts: list[np.ndarray], dtype) -> np.ndarray:
    """Concatenate a possibly empty list of arrays."""
    return np.concatenate(parts).astype(dtype) if parts else np.zeros(0, dtype=dtype)


def read_step_files(
    grb_file: str | Path,
    budget_file: str | Path,
    kstpkper: tuple[int, int] = (0, 0),
    area: np.ndarray | None = None,
) -> FlowStep:
    """Read one time step from a binary grid file and a budget file into a FlowStep."""
    grid = read_grid(grb_file)
    active = grid.idomain > 0
    cbc = flopy.utils.CellBudgetFile(str(budget_file))
    indices = _step_record_indices(cbc, kstpkper)
    terms = _read_terms(cbc, indices, active)
    assert terms["flowja"].size == grid.ja.size, "FLOW-JA-FACE length does not match NJA"
    return FlowStep(
        ia=grid.ia,
        ja=grid.ja,
        flowja=terms["flowja"],
        term_cell=_concat(terms["cell"], np.int64),
        term_flow=_concat(terms["flow"], float),
        term_package=_concat(terms["package"], np.int64),
        term_bound=_concat(terms["bound"], np.int64),
        packages=terms["packages"],
        area=grid.area if area is None else np.asarray(area, dtype=float),
        active=active,
        grid_shape=grid.shape,
        grid_type=grid.grid_type,
        kstpkper=tuple(int(k) for k in kstpkper),
        totim=float(cbc.recordarray[indices[0]]["totim"]),
    )


def read_step(
    ws: str | Path,
    model: str | None = None,
    kstpkper: tuple[int, int] = (0, 0),
    area: np.ndarray | None = None,
) -> FlowStep:
    """Read one time step of a GWF model in a simulation folder into a FlowStep.

    For DISU grids without vertices the cell area is read from the DISU input (AREA).
    """
    files = find_model_files(ws, model)
    step = read_step_files(files.grb_file, files.budget_file, kstpkper, area=area)
    if step.area is None and files.dis_type == "DISU":
        step.area = read_disu_area(ws, files.model)
    step.notes["model"] = files.model
    step.notes["grb_file"] = str(files.grb_file)
    step.notes["budget_file"] = str(files.budget_file)
    return step
