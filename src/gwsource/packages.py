"""Read the budget files of advanced packages (SFR, LAK, MAW, UZF) and of the water mover (MVR).

Each enabled package gets one node per reach, lake, well or UZF cell (gwsource.network). Its own
budget file (BUDGET FILEOUT in the package OPTIONS) lists every flow of every package node as
IMETH = 6 records: ID1 = the package node (1-based), ID2 = the other end, q positive INTO the
package node. Record names and their role, checked with the MF6 6.9 nightly (test models 7-9):

| Package | Record | Role in the graph |
|---|---|---|
| SFR, LAK, UZF | FLOW-JA-FACE (ID2 = other node of the package) | package-package edge; listed from both ends (antisymmetric), counted once |
| SFR, LAK, MAW, UZF | GWF (ID2 = GWF cell, user node) | cell-package edge; replaces the aquifer-side record of the GWF budget (below) |
| SFR | RAINFALL, EVAPORATION, RUNOFF, EXT-INFLOW, EXT-OUTFLOW | source/sink terms of the reach |
| LAK | RAINFALL, EVAPORATION, RUNOFF, EXT-INFLOW, WITHDRAWAL, EXT-OUTFLOW, CONSTANT | source/sink terms of the lake |
| MAW | RATE, FW-RATE, CONSTANT | source/sink terms of the well (RATE: pumping or injection) |
| UZF | INFILTRATION, REJ-INF, UZET | source/sink terms of the UZF cell |
| all | STORAGE (auxiliary VOLUME) | storage term (positive = release), and the node's water volume |
| all | FROM-MVR | source term; becomes part of an MVR edge when the provider is in the graph |
| SFR, LAK | TO-MVR | sink term; becomes part of an MVR edge when the receiver is in the graph |
| MAW | RATE-TO-MVR, FW-RATE-TO-MVR | as TO-MVR |
| UZF | REJ-INF-TO-MVR | as TO-MVR |
| any | DATA-* | not flows; skipped |

Aquifer-side records in the GWF budget (ID1 = cell, ID2 = package node) that the GWF record of
the package budget replaces, so that the exchange is counted once, as an edge:
SFR (SFR), LAK (LAK), MAW (MAW), UZF (UZF-GWRCH). The other UZF records of the GWF budget stay
cell terms: UZF-GWD (groundwater seepage to land surface, a sink), UZF-GWET (groundwater ET, a
sink) and 'UZF-GWD TO-MVR' (seepage handed to the mover; a sink unless routed by MVR).

The MVR budget file (BUDGET FILEOUT in the MVR OPTIONS) has one MOVER-FLOW record per provider
and receiver package pair (PAKNAM = provider, PAKNAM2 = receiver), ID1 = provider bound or
package node, ID2 = receiver package node, q = minus the moved rate.

MF6 balances each package node itself, so the sum of all its records is the node's residual
(reported, as the FLOW-JA-FACE diagonal is for a cell).
"""

from dataclasses import dataclass, field
from pathlib import Path

import flopy
import numpy as np
import scipy.sparse as sp

from .mf6io import _block_lines, _decode, _fileout, _name_file_packages, _step_record_indices

PACKAGE_TYPES = ("SFR", "LAK", "MAW", "UZF")
DIMENSION_KEYS = {"SFR": "NREACHES", "LAK": "NLAKES", "MAW": "NMAWWELLS", "UZF": "NUZFCELLS"}
AQUIFER_TEXTS = {"SFR": ("SFR",), "LAK": ("LAK",), "MAW": ("MAW",), "UZF": ("UZF-GWRCH",)}
INTERNAL_TEXT = "FLOW-JA-FACE"
AQUIFER_TEXT = "GWF"
STORAGE_TEXT = "STORAGE"
VOLUME_AUX = "VOLUME"
FROM_MOVER_TEXT = "FROM-MVR"
MOVER_FLOW_TEXT = "MOVER-FLOW"
ANTISYMMETRY_RTOL = 1e-10


@dataclass
class PackageFiles:
    """One advanced package of a GWF model: its name in the GWF budget, type, size, budget file."""

    model: str
    name: str
    package_type: str
    n: int
    input_file: Path
    budget_file: Path


@dataclass
class PackageStep:
    """One time step of one package budget, in 0-based package nodes and GWF user cells.

    internal: package-package edges (src, dst, q > 0); aquifer: (node, cell, q into node) per
    connection; terms: {record text: (node, q into node)}; volume: per node (NaN if the budget
    has no STORAGE VOLUME); residual: per-node sum of all records.
    """

    files: PackageFiles
    internal: tuple[np.ndarray, np.ndarray, np.ndarray]
    aquifer: tuple[np.ndarray, np.ndarray, np.ndarray]
    terms: dict[str, tuple[np.ndarray, np.ndarray]]
    volume: np.ndarray
    residual: np.ndarray


@dataclass
class MoverTransfer:
    """Water moved by MVR in one step: provider package and bound, receiver package and node."""

    provider: np.ndarray
    provider_id: np.ndarray
    receiver: np.ndarray
    receiver_id: np.ndarray
    q: np.ndarray = field(default_factory=lambda: np.zeros(0))


# ---------------------------------------------------------------- locating files


def _dimension(path: Path, key: str) -> int:
    """Return an integer from the DIMENSIONS block of an input file."""
    for tokens in _block_lines(path, "DIMENSIONS"):
        if tokens[0].upper() == key:
            return int(tokens[1])
    raise AssertionError(f"{key} not found in the DIMENSIONS block of {path}")


def find_package_files(nam_file: Path, model: str, package_types) -> list[PackageFiles]:
    """Return the advanced packages of the given types in a model name file (BUDGET FILEOUT)."""
    wanted = {t.upper() for t in package_types}
    unknown = wanted - set(PACKAGE_TYPES)
    assert not unknown, f"package nodes are supported for {PACKAGE_TYPES}, not {sorted(unknown)}"
    found = []
    for ftype, path, pname in _name_file_packages(nam_file):
        if ftype not in wanted:
            continue
        budget = _fileout(path, "BUDGET")
        assert budget is not None, (
            f"{ftype} package {pname} of model {model} has no budget file: add BUDGET FILEOUT "
            "to its OPTIONS to trace through its nodes"
        )
        n = _dimension(path, DIMENSION_KEYS[ftype])
        found.append(PackageFiles(model, pname, ftype, n, path, nam_file.parent / budget))
    missing = wanted - {p.package_type for p in found}
    assert not missing, f"model {model} has no {sorted(missing)} package"
    return found


def find_mover_budget(nam_file: Path) -> Path | None:
    """Return the MVR budget file of a model, or None if it has no MVR package."""
    entries = [e for e in _name_file_packages(nam_file) if e[0] == "MVR"]
    if not entries:
        return None
    budget = _fileout(entries[0][1], "BUDGET")
    assert budget is not None, (
        "the model has MVR: add BUDGET FILEOUT to the MVR OPTIONS to route moved water"
    )
    return nam_file.parent / budget


# ---------------------------------------------------------------- reading one step


def _internal_edges(
    node: np.ndarray, node2: np.ndarray, q: np.ndarray, n: int, label: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return package-package edges (q > 0) from a FLOW-JA-FACE record listed from both ends."""
    flows = sp.coo_matrix((q, (node, node2)), shape=(n, n)).tocsr()
    scale = max(float(np.abs(q).max(initial=0.0)), 1.0)
    assert np.abs((flows + flows.T).data).max(initial=0.0) <= ANTISYMMETRY_RTOL * scale, (
        f"{label}: FLOW-JA-FACE is not antisymmetric"
    )
    keep = q < 0.0  # flow out of node into node2
    return node[keep], node2[keep], -q[keep]


def read_package_step(
    cbc: flopy.utils.CellBudgetFile, files: PackageFiles, kstpkper: tuple[int, int]
) -> PackageStep:
    """Read one time step of a package budget file."""
    n, label = files.n, f"{files.model}/{files.name}"
    empty = np.zeros(0, dtype=np.int64)
    internal = (empty, empty, np.zeros(0))
    aquifer = (empty, empty, np.zeros(0))
    terms: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    volume = np.full(n, np.nan)
    residual = np.zeros(n)
    for idx in _step_record_indices(cbc, kstpkper):
        text = _decode(cbc.recordarray[idx]["text"])
        if text.startswith("DATA-"):
            continue
        data = cbc.get_record(idx, full3D=False)
        node = np.asarray(data["node"], dtype=np.int64) - 1
        node2 = np.asarray(data["node2"], dtype=np.int64) - 1
        q = np.asarray(data["q"], dtype=float)
        assert node.size == 0 or node.max() < n, f"{label}: node beyond the package dimension"
        np.add.at(residual, node, q)
        if text == INTERNAL_TEXT:
            internal = _internal_edges(node, node2, q, n, label)
        elif text == AQUIFER_TEXT:
            aquifer = (node, node2, q)
        else:
            assert text not in terms, f"{label}: duplicate record {text}"
            terms[text] = (node, q)
            if text == STORAGE_TEXT and VOLUME_AUX in (data.dtype.names or ()):
                volume[node] = np.asarray(data[VOLUME_AUX], dtype=float)
    return PackageStep(files, internal, aquifer, terms, volume, residual)


def read_mover_step(cbc: flopy.utils.CellBudgetFile, kstpkper: tuple[int, int]) -> MoverTransfer:
    """Read one time step of an MVR budget file: every provider -> receiver transfer."""
    parts = {"provider": [], "provider_id": [], "receiver": [], "receiver_id": [], "q": []}
    for idx in _step_record_indices(cbc, kstpkper):
        header = cbc.recordarray[idx]
        if _decode(header["text"]) != MOVER_FLOW_TEXT:
            continue
        data = cbc.get_record(idx, full3D=False)
        if len(data) == 0:
            continue
        parts["provider"].append(np.full(len(data), _decode(header["paknam"]).upper(), object))
        parts["receiver"].append(np.full(len(data), _decode(header["paknam2"]).upper(), object))
        parts["provider_id"].append(np.asarray(data["node"], dtype=np.int64))
        parts["receiver_id"].append(np.asarray(data["node2"], dtype=np.int64))
        parts["q"].append(np.abs(np.asarray(data["q"], dtype=float)))
    if not parts["q"]:
        none = np.zeros(0, dtype=object)
        return MoverTransfer(none, np.zeros(0, np.int64), none, np.zeros(0, np.int64))
    return MoverTransfer(**{k: np.concatenate(v) for k, v in parts.items()})
