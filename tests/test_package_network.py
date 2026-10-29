"""Package networks: MAW (model 8), SFR + MVR (model 7) and LAK + UZF + MVR (model 9) as nodes.

Checks on every saved step: the residual of every node (cells and package nodes) is small and
matches MF6's own (FLOW-JA-FACE diagonal for cells, the package budget's balance for package
nodes, up to the solver-level difference between the two sides of an exchange); closure,
duality and boundary control hold to 1e-10 with residual terms; so do the travel-time and age
identities, with package water volumes. The routing test (model 7) shows that, with SFR nodes,
part of the well's water is attributed to the drained area upstream (DRN -> MVR -> SFR ->
aquifer -> well), and that without package nodes it is not. A loosely solved model 7 (the
budgets' two sides of the stream-aquifer exchange differ by about 1e-3) fails the default
aquifer check and reads with a relaxed aquifer_rtol, the difference then in the reach residuals.
"""

import shutil
import subprocess

import numpy as np
import pytest
from test_closure_duality import check_boundary_control, check_identities
from test_mf6io import mf6_diagonal

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.traveltime import exit_cell_closure, travel_time_closure
from models.networks import MAW_RATE

NETWORKS = {"m7_mover": ("SFR",), "m8_maw": ("MAW",), "m9_lak_uzf": ("LAK", "UZF")}
POROSITY = 0.3
RTOL = 1e-10
DRAIN_CELLS = (6 * 30 + 12, 14 * 30 + 12)
LOOSE_IMS = {"outer_dvclose": 1.0e-2, "inner_dvclose": 1.0e-3, "rcloserecord": 1.0e3}


def network_steps(model_run, key: str) -> list[gs.FlowStep]:
    """Return every saved step of a test model read with its package nodes."""
    reader = gs.open_simulation(model_run(key).ws, package_nodes=NETWORKS[key], boundnames=True)
    return [reader.read(ks) for ks in reader.steps]


@pytest.mark.parametrize("key", list(NETWORKS))
def test_node_residuals(key, model_run):
    """Every node's residual is small; cells match MF6's, package nodes their own budget."""
    for step in network_steps(model_run, key):
        budget = cell_budget(step, flow_edges(step))
        scale = np.maximum(np.maximum(budget.inflow, budget.outflow), 1.0)
        assert np.all(np.abs(budget.residual) <= 1e-8 * scale)
        cells = np.arange(step.block(step.model_names[0]).n)
        diag = mf6_diagonal(step)
        assert np.all(np.abs(budget.residual - diag)[cells] <= 1e-8 * scale[cells])
        assert np.all(np.abs(budget.residual - diag) <= 1e-7 * scale)
        assert any(b.kind == "package" for b in step.blocks)


@pytest.mark.parametrize("key", list(NETWORKS))
def test_network_identities(key, model_run):
    """Closure, duality and boundary control hold on the network (cells and package nodes)."""
    for step in network_steps(model_run, key):
        check_identities(step)
        check_boundary_control(step)


@pytest.mark.parametrize("key", list(NETWORKS))
def test_network_travel_time_identities(key, model_run):
    """Travel-time and age identities hold with package-node volumes from the package budgets."""
    for step in network_steps(model_run, key):
        packages = np.concatenate([b.nodes for b in step.blocks if b.kind == "package"])
        assert np.all(np.isfinite(step.fixed_volume[packages]))
        assert np.all(step.fixed_volume[packages] >= 0.0)
        groups = gs.groups_by_package(step)
        back, fwd = gs.backward(step, groups), gs.forward(step, groups)
        tt_back, tt_fwd = gs.travel_time(step, back, POROSITY), gs.travel_time(step, fwd, POROSITY)
        np.testing.assert_array_equal(tt_back.water_volume[packages], step.fixed_volume[packages])
        for name in groups:
            for check in (
                travel_time_closure(step, back, tt_back, name),
                exit_cell_closure(step, back, tt_back, name),
                travel_time_closure(step, fwd, tt_fwd, name),
            ):
                assert abs(check.error) <= RTOL * max(abs(check.rhs), 1.0), (name, check)


def test_aquifer_records_become_edges(model_run):
    """The GWF budget's SFR record is replaced by cell-reach edges, never counted twice."""
    run = model_run("m7_mover")
    step = gs.read_step(run.ws)
    net = gs.read_network(run.ws, package_nodes=("SFR",))
    assert "SFR" in step.package_names and "SFR" not in net.package_names
    reaches = net.block("SFR").nodes
    edges = flow_edges(net)
    into_reach = np.isin(edges.dst, reaches) & (edges.src < reaches[0])
    out_of_reach = np.isin(edges.src, reaches) & (edges.dst < reaches[0])
    seepage = into_reach & ~np.isin(edges.src, DRAIN_CELLS)  # the rest are MVR edges
    sfr = gs.select(step, package="SFR")
    gains = -step.term_flow[sfr.terms & (step.term_flow < 0)].sum()  # aquifer -> stream
    losses = step.term_flow[sfr.terms & (step.term_flow > 0)].sum()  # stream -> aquifer
    assert edges.q[seepage].sum() == pytest.approx(gains, rel=1e-12)
    assert edges.q[out_of_reach].sum() == pytest.approx(losses, rel=1e-12)


def test_net_package_selection_fixes_only_flowing_nodes(model_run):
    """Net backward select(package="SFR") fixes only the reach nodes with a sink record.

    On model 7 that is the outlet reach (EXT-OUTFLOW), so the net inflow equals the gross inflow
    (22.913).
    """
    step = gs.read_network(model_run("m7_mover").ws, package_nodes=("SFR",))
    groups = {"sfr": gs.select(step, package="SFR")}
    net = gs.backward(step, groups, gs.TraceConfig(accounting="net"))
    gross = gs.backward(step, groups)
    assert gs.trace.net_fixed_cells(step, groups["sfr"], -1).sum() == 1
    assert gross.destination_inflow["sfr"] == pytest.approx(22.913140, rel=1e-6)
    assert net.destination_inflow["sfr"] == pytest.approx(gross.destination_inflow["sfr"], rel=1e-8)


@pytest.mark.parametrize("kstpkper", [(0, 0), (0, 1)])
def test_mover_routes_drained_water_to_the_well(kstpkper, model_run):
    """With SFR nodes, drained water reaches the well through MVR, the stream and the aquifer."""
    run = model_run("m7_mover")
    off = gs.read_step(run.ws, kstpkper=kstpkper, boundnames=True)
    on = gs.read_network(run.ws, kstpkper=kstpkper, package_nodes=("SFR",), boundnames=True)
    back_off = gs.backward(off, {"well": gs.select(off, boundnames=["well_east"])})
    back_on = gs.backward(on, {"well": gs.select(on, boundnames=["well_east"])})
    f_off, f_on = back_off.fraction_through["well"], back_on.fraction_through["well"]
    drains = list(DRAIN_CELLS)
    np.testing.assert_array_equal(f_off[drains], 0.0)  # the moved water is a sink: lost
    assert np.all(f_on[drains] > 0.1)
    # the drain -> reach edges carry exactly the TO-MVR records of the cells-only step
    moved = -off.term_flow[gs.select(off, package="DRN-TO-MVR").terms].sum()
    assert on.notes["mover_routed"] == pytest.approx(moved, rel=1e-8)
    edges = flow_edges(on)
    mover = np.isin(edges.src, drains) & np.isin(edges.dst, on.block("SFR").nodes)
    assert edges.q[mover].sum() == pytest.approx(moved, rel=1e-8)
    via_mover = float(edges.q[mover] @ f_on[edges.dst[mover]])
    assert via_mover > 0.1 * back_on.destination_inflow["well"]
    assert not gs.select(on, package="DRN-TO-MVR").terms.any() or np.all(
        on.term_flow[gs.select(on, package="DRN-TO-MVR").terms] == 0.0
    )
    # without nodes the stream is an opaque source; with nodes it is traced to its origins
    by_term_off = {k: v.sum() for k, v in back_off.volume_from_by_term["well"].items()}
    by_term_on = {k: v.sum() for k, v in back_on.volume_from_by_term["well"].items()}
    assert by_term_off["SFR"] > 0 and "SFR" not in by_term_on
    assert by_term_on["RCH"] > by_term_off["RCH"] + 0.5 * via_mover
    assert sum(by_term_on.values()) == pytest.approx(back_on.destination_inflow["well"], rel=1e-8)


def test_without_package_nodes_mover_stays_a_sink(model_run):
    """open_simulation without package nodes gives the cells-only results."""
    run = model_run("m7_mover")
    step, net = gs.read_step(run.ws), gs.read_network(run.ws)
    assert net.package_names == step.package_names
    a = gs.backward(step, gs.groups_by_package(step))
    b = gs.backward(net, gs.groups_by_package(net))
    for g in a.groups:
        np.testing.assert_array_equal(a.fraction_through[g], b.fraction_through[g])


def test_maw_moves_water_between_layers(model_run):
    """The MAW well takes water from layer 1 and injects part of it into layer 3."""
    run = model_run("m8_maw")
    net = gs.read_network(run.ws, package_nodes=("MAW",))
    well = int(net.block("MAW").nodes[0])
    row, col = run.notes["maw_cell"]
    cells = [k * 15 * 25 + row * 25 + col for k in range(3)]
    edges = flow_edges(net)
    into = {int(s): q for s, d, q in zip(edges.src, edges.dst, edges.q) if d == well}
    out = {int(d): q for s, d, q in zip(edges.src, edges.dst, edges.q) if s == well}
    assert set(into) == {cells[0], cells[1]} and set(out) == {cells[2]}
    pumping = gs.select(net, package="MAW", bounds=[1], term="RATE")
    assert pumping.terms.sum() == 1
    back = gs.backward(net, {"pump": pumping})
    assert back.destination_inflow["pump"] == pytest.approx(-run.notes["maw_rate"])
    f = back.fraction_through["pump"]
    assert f[well] == pytest.approx(-run.notes["maw_rate"] / sum(into.values()), rel=1e-10)
    # forward: the well bore mixes its inflows, and its water is traced on into layer 3
    fwd = gs.forward(net, {"rch": gs.select(net, package="RCH")})
    g = fwd.source_fraction["rch"]
    mixed = sum(q * g[c] for c, q in into.items()) / sum(into.values())
    assert g[well] == pytest.approx(mixed, rel=1e-12)
    assert fwd.volume_through["rch"][cells[2]] > 0.0
    # without MAW nodes the well-bore exchange is a pair of opaque terms on the cells
    step = gs.read_step(run.ws)
    maw = gs.select(step, package="MAW")
    assert step.term_flow[maw.terms].sum() == pytest.approx(run.notes["maw_rate"], rel=1e-8)


def test_lake_and_uzf_routing(model_run):
    """Rejected infiltration (UZF) moves to lake A, spills to lake B and leaves the model."""
    run = model_run("m9_lak_uzf")
    net = gs.read_network(run.ws, package_nodes=("LAK", "UZF"), boundnames=True)
    lakes, uzf = net.block("LAK").nodes, net.block("UZF").nodes
    edges = flow_edges(net)
    assert np.any((edges.src == lakes[0]) & (edges.dst == lakes[1]))  # outlet A -> B
    assert np.sum(np.isin(edges.src, uzf) & (edges.dst == lakes[0])) == 8  # MVR edges
    assert np.any(np.isin(edges.src, uzf) & (edges.dst < uzf[0]) & ~np.isin(edges.dst, lakes))
    outflow = gs.select(net, package="LAK", bounds=[2], term="EXT-OUTFLOW")
    back = gs.backward(net, {"lake_b_out": outflow})
    assert back.destination_inflow["lake_b_out"] > 0.5
    f = back.fraction_through["lake_b_out"]
    assert f[lakes[0]] > 0.0 and f[lakes[1]] > f[lakes[0]]
    east = [uzf[i] for i, (_, c) in enumerate(run.notes["uzf_cells"]) if c >= 7]
    assert np.all(f[east] > 0.0)
    assert np.all(net.fixed_volume[lakes] > 1e5)
    selected = gs.select(net, package="LAK", term="RAINFALL")
    assert selected.terms.sum() == 2 and np.all(net.term_cell[selected.terms] == lakes)
    names = net.term_boundname[gs.select(net, package="LAK", term="RAINFALL").terms]
    assert list(names) == ["lake_a", "lake_b"]


def test_transient_network(model_run):
    """trace_transient runs on a NetworkReader; its statistics match a per-step brute force."""
    run = model_run("m9_lak_uzf")
    reader = gs.open_simulation(run.ws, package_nodes=("LAK", "UZF"))
    spec = {"out": {"package": "LAK", "bounds": [2], "term": "EXT-OUTFLOW"}}
    res = gs.trace_transient(reader, spec, config=gs.TransientConfig(weighting="equal"))
    per_step = []
    for ks in reader.steps:
        step = reader.read(ks)
        per_step.append(gs.backward(step, {"out": gs.select(step, **spec["out"])})
                        .fraction_through["out"])
    np.testing.assert_allclose(res.stats["mean"]["fraction_through"]["out"],
                               np.mean(per_step, axis=0), rtol=1e-12)
    view = gs.network.transient_view(res)
    assert view.stats["max"]["fraction_through"]["out"].shape == (net_cells(res),)


def net_cells(res) -> int:
    """Return the number of cells of the one model of a transient network result."""
    return res.template.block(res.template.model_names[0]).n


def test_prt_rejects_package_destinations(model_run):
    """The PRT helper raises NotImplementedError for package-node destinations and networks."""
    run = model_run("m8_maw")
    net = gs.read_network(run.ws, package_nodes=("MAW",))
    pumping = gs.select(net, package="MAW", term="RATE")
    with pytest.raises(NotImplementedError, match="package nodes"):
        gs.prt.check_cells_only(net, pumping)
    with pytest.raises(NotImplementedError, match="single-model"):
        gs.prt.check_cells_only(net, gs.select(net, package="WEL"))
    gs.prt.check_cells_only(gs.read_step(run.ws), gs.select(gs.read_step(run.ws), package="WEL"))


def test_selector_errors(model_run):
    """term= with an unknown record text fails clearly."""
    net = gs.read_network(model_run("m8_maw").ws, package_nodes=("MAW",))
    with pytest.raises(AssertionError, match="no record text"):
        gs.select(net, package="MAW", term="NOT-A-RECORD")


def test_package_type_selects_default_named_package(model_run, mf6_exe, tmp_path):
    """With no package name in the name file (MF6 names it 'MAW-1'), package='MAW' still selects."""
    shutil.copytree(model_run("m8_maw").ws, tmp_path, dirs_exist_ok=True)
    nam_file = tmp_path / "m8_maw.nam"
    text = nam_file.read_text(encoding="utf-8")
    nam_file.write_text(text.replace("m8_maw.maw  maw", "m8_maw.maw"), encoding="utf-8")
    subprocess.run([str(mf6_exe)], cwd=tmp_path, capture_output=True, check=True)
    net = gs.read_network(tmp_path, package_nodes=("MAW",))
    assert net.block("MAW-1").package_type == "MAW"
    pumping = gs.select(net, package="maw", bounds=[1], term="RATE")
    assert pumping.terms.sum() == 1
    assert net.term_flow[pumping.terms].sum() == pytest.approx(MAW_RATE)
    named = gs.select(net, package="MAW-1", term="RATE")
    np.testing.assert_array_equal(named.terms, pumping.terms)


@pytest.fixture(scope="module")
def loose_mover_run(tmp_path_factory, mf6_exe):
    """Model 7 solved with loose closure criteria (outer 1e-2, inner 1e-3)."""
    from models import build_mover_dis

    return build_mover_dis(tmp_path_factory.mktemp("m7_loose"), mf6_exe, ims_kwargs=LOOSE_IMS)


def test_aquifer_rtol_admits_a_loose_solve(loose_mover_run):
    """A loose solve fails the default aquifer check; with aquifer_rtol the mismatch is residual."""
    ws = loose_mover_run.ws
    message = r"disagree by up to .*\(aquifer_rtol=0\.0001\).*OUTER_DVCLOSE"
    with pytest.raises(AssertionError, match=message):
        gs.read_network(ws, package_nodes=("SFR",))
    reader = gs.open_simulation(ws, package_nodes=("SFR",), aquifer_rtol=1e-2)
    assert reader.aquifer_rtol == 1e-2
    for ks in reader.steps:
        step = reader.read(ks)
        budget = cell_budget(step, flow_edges(step))
        reaches = step.block("SFR").nodes
        scale = np.maximum(budget.inflow, budget.outflow)[reaches].max()
        # the budgets' difference stays in the reach residuals, which closure includes
        assert np.abs(budget.residual - mf6_diagonal(step))[reaches].max() > 1e-4 * scale
        check_identities(step)


def test_network_reader_closes_its_files(model_run):
    """A NetworkReader closes every model and package budget file at the end of a with block."""
    with gs.open_simulation(model_run("m8_maw").ws, package_nodes=("MAW",)) as reader:
        reader.read()
    files = [r.cbc.file for r in reader.models.values()]
    files += [cbc.file for _, cbc in reader.packages] + [cbc.file for cbc in reader.movers.values()]
    assert len(files) >= 2 and all(f.closed for f in files)
