"""Hand-built networks: exchange of a package node with a cell, and the MVR sharing rule.

One UZF cell (package node) sits over GWF cell 0. It receives 5 of infiltration, sends 4 to the
water table and rejects 1 to the mover. Cell 0 passes 1 to cell 1 (a well takes it) and loses 3
as groundwater seepage to the mover. MVR moves 4 from UZF cell 1 to SFR reach 1, which lets it
out of the model. The provider bound (UZF cell 1) has two TO-MVR records, so the 4 is shared
3 : 1 between the cell and the UZF node. Backward from the reach outflow:
F(cell 0) = 3/4, F(UZF) = 1/5 + 4/5 x 3/4 = 4/5, F(reach) = 1.
"""

from pathlib import Path

import numpy as np
import pytest

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.network import build_network
from gwsource.packages import MoverTransfer, PackageFiles, PackageStep

GWF_PACKAGES = [
    gs.Package("UZF", "UZF-GWRCH"),
    gs.Package("UZF:UZF-GWD TO-MVR", "UZF-GWD TO-MVR", parent="UZF"),
    gs.Package("WEL", "WEL"),
]


def gwf_step() -> gs.FlowStep:
    """Return the two-cell GWF step: recharge from UZF, seepage to MVR, a well."""
    return gs.from_edges(
        2, [0], [1], [1.0], term_cell=[0, 0, 1], term_flow=[4.0, -3.0, -1.0],
        term_package=[0, 1, 2], packages=list(GWF_PACKAGES),
    )


def package_step(name: str, aquifer: tuple, terms: dict) -> PackageStep:
    """Return a one-node package step."""
    files = PackageFiles("gwf", name, name, 1, Path("x"), Path("x"))
    empty = np.zeros(0, dtype=np.int64)
    as_arrays = {k: (np.array([0]), np.array([q], float)) for k, q in terms.items()}
    aquifer = tuple(np.asarray(a) for a in aquifer)
    return PackageStep(files, (empty, empty, np.zeros(0)), aquifer, as_arrays, np.zeros(1),
                       np.zeros(1))


def uzf_step() -> PackageStep:
    """Return the UZF node: infiltration 5, to the water table 4, rejected to the mover 1."""
    return package_step(
        "UZF", ([0], [0], [-4.0]), {"INFILTRATION": 5.0, "REJ-INF-TO-MVR": -1.0}
    )


def sfr_step() -> PackageStep:
    """Return the SFR reach: 4 from the mover, 4 out of the model."""
    empty = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0))
    return package_step("SFR", empty, {"FROM-MVR": 4.0, "EXT-OUTFLOW": -4.0})


def transfer(q: float) -> MoverTransfer:
    """Return one MVR transfer from UZF cell 1 to SFR reach 1."""
    return MoverTransfer(
        np.array(["UZF"], object), np.array([1]), np.array(["SFR"], object), np.array([1]),
        np.array([q]),
    )


def test_mover_shared_between_cell_and_package_records():
    """The moved water leaves the UZF node and its cell in proportion to their TO-MVR rates."""
    net = build_network({"gwf": gwf_step()}, [uzf_step(), sfr_step()], {"gwf": transfer(4.0)})
    assert [b.label for b in net.blocks] == ["gwf", "gwf/UZF", "gwf/SFR"]
    uzf, reach = 2, 3
    edges = flow_edges(net)
    pairs = {(int(s), int(d)): q for s, d, q in zip(edges.src, edges.dst, edges.q)}
    assert pairs == {(0, 1): 1.0, (uzf, 0): 4.0, (uzf, reach): 1.0, (0, reach): 3.0}
    movers = gs.select(net, term=["UZF-GWD TO-MVR", "REJ-INF-TO-MVR", "FROM-MVR"])
    np.testing.assert_array_equal(net.term_flow[movers.terms], 0.0)
    assert "UZF" not in net.package_names  # the UZF-GWRCH record became the uzf -> cell edge
    np.testing.assert_allclose(cell_budget(net, flow_edges(net)).residual, 0.0, atol=1e-15)
    back = gs.backward(net, {"out": gs.select(net, package="SFR", term="EXT-OUTFLOW")})
    np.testing.assert_allclose(back.fraction_through["out"], [0.75, 0.0, 0.8, 1.0], rtol=1e-15)
    assert back.volume_from["out"].sum() == pytest.approx(4.0)


def test_mover_to_a_receiver_without_nodes_stays_a_sink():
    """Without SFR nodes the transfer cannot be routed: both TO-MVR records stay sinks."""
    net = build_network({"gwf": gwf_step()}, [uzf_step()], {"gwf": transfer(4.0)})
    movers = gs.select(net, term=["UZF-GWD TO-MVR", "REJ-INF-TO-MVR"])
    np.testing.assert_array_equal(np.sort(net.term_flow[movers.terms]), [-3.0, -1.0])
    assert net.notes["mover_routed"] == 0.0


def test_mover_remainder_snaps_to_zero():
    """A moved rate that differs from the records at solver level leaves no tiny terms."""
    net = build_network(
        {"gwf": gwf_step()}, [uzf_step(), sfr_step()], {"gwf": transfer(4.0 * (1 + 1e-9))}
    )
    movers = gs.select(net, term=["UZF-GWD TO-MVR", "REJ-INF-TO-MVR", "FROM-MVR"])
    np.testing.assert_array_equal(net.term_flow[movers.terms], 0.0)
    residual = cell_budget(net, flow_edges(net)).residual  # the difference moves here
    np.testing.assert_allclose(residual, [-3e-9, 0.0, -1e-9, 4e-9], atol=1e-15)


def test_blocks_must_tile_the_nodes():
    """A FlowStep's blocks must cover its nodes in order."""
    step = gwf_step()
    bad = gs.NodeBlock("gwf", "model", "gwf", 0, 1, (1,), "graph")
    with pytest.raises(AssertionError, match="tile"):
        gs.FlowStep(**{**step.__dict__, "blocks": [bad]})
