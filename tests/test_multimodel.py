"""Multi-model simulations: a model split with FloPy's Mf6Splitter must trace like the whole model.

Models 1 (DIS), 3 (DISV Voronoi) and 6 (transient DIS) are split into 2 to 4 models joined by
GWF-GWF exchanges (SAVE_FLOWS on), run with the same solver settings, read as one network and
traced. Every output, mapped back to the original grid with the splitter's node map, must equal
the single-model output to RTOL relative to the largest value of that output (the two runs
agree only to the MF6 solver tolerance; the agreement reached is about 1e-10, see
achieved_agreement()).
"""

import flopy
import numpy as np
import pytest
from flopy.mf6.utils import Mf6Splitter
from test_closure_duality import check_boundary_control, check_identities
from test_mf6io import mf6_diagonal

import gwsource as gs
from gwsource.assemble import cell_budget, flow_edges
from gwsource.traveltime import travel_time_closure

RTOL = 1e-8
POROSITY = 0.3
PACKAGES = ("WEL", "RIV", "CHD", "RCH")
TRANSIENT_STEPS = ((0, 0), (3, 1), (0, 2), (3, 3))


def labels_for(key: str, gwf) -> np.ndarray:
    """Return the splitter label array of a test model (2 to 4 models)."""
    if key == "m1_dis":  # three models: east half, south-west and north-west
        labels = np.zeros((20, 30), dtype=int)
        labels[:, 15:] = 1
        labels[12:, :15] = 2
        return labels
    if key == "m6_transient":  # four quadrants
        labels = np.zeros((20, 30), dtype=int)
        labels[:10, 15:], labels[10:, :15], labels[10:, 15:] = 1, 2, 3
        return labels
    assert key == "m3_disv", key  # two models: west and east of x = 700
    return (np.asarray(gwf.modelgrid.xcellcenters) > 700.0).astype(int)


def split_and_run(run, key: str, ws, exe) -> Mf6Splitter:
    """Split a test model with Mf6Splitter, save the exchange flows, write and run it."""
    sim = flopy.mf6.MFSimulation.load(sim_ws=str(run.ws), verbosity_level=0)
    splitter = Mf6Splitter(sim)
    new = splitter.split_model(labels_for(key, sim.get_model()))
    for exchange in new.exchange_files:
        exchange.save_flows = True
    new.set_sim_path(str(ws))
    new.exe_name = str(exe)
    new.write_simulation(silent=True)
    success, buff = new.run_simulation(silent=True, report=True)
    assert success, "\n".join(buff[-20:])
    return splitter


@pytest.fixture(scope="module")
def split_run(model_run, tmp_path_factory, mf6_exe):
    """Return a function key -> (single-model run, split workspace, splitter), built once."""
    cache = {}

    def get(key: str):
        if key not in cache:
            run = model_run(key)
            ws = tmp_path_factory.mktemp(f"{key}_split")
            cache[key] = (run, ws, split_and_run(run, key, ws, mf6_exe))
        return cache[key]

    return get


def map_back(splitter: Mf6Splitter, step: gs.FlowStep, values: np.ndarray) -> np.ndarray:
    """Return per-node values of a split network mapped to the original model's user nodes."""
    per_model = {}
    for block in step.blocks:
        number = int(block.model.rsplit("_", 1)[-1])
        per_model[number] = np.asarray(values[block.nodes], float).reshape(block.grid_shape)
    return np.asarray(splitter.reconstruct_array(per_model), float).ravel()


def groups(step: gs.FlowStep) -> dict[str, gs.Selection]:
    """Return one group per stress package (and storage), selected the same way in both steps."""
    names = [p for p in PACKAGES if any(p in pkg.aliases for pkg in step.packages)]
    names += [p for p in ("STO-SS", "STO-SY") if any(p in pkg.aliases for pkg in step.packages)]
    return {name: gs.select(step, package=name) for name in names}


def _by_local_name(by_term: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Return a by-term split summed over models ('<model>/RCH' and 'RCH' both become 'RCH')."""
    out: dict[str, np.ndarray] = {}
    for name, values in by_term.items():
        local = name.split("/")[-1]
        out[local] = out.get(local, 0.0) + values
    return out


def _flatten(prefix: str, result) -> dict[str, np.ndarray]:
    """Return every per-node array and per-group number of a result, keyed by name."""
    out = {}
    for field, value in vars(result).items():
        if isinstance(value, np.ndarray):
            out[f"{prefix}.{field}"] = value
        if not isinstance(value, dict) or field == "selections":
            continue
        for group, values in value.items():
            if isinstance(values, dict):
                for term, v in _by_local_name(values).items():
                    out[f"{prefix}.{field}.{group}.{term}"] = v
            elif isinstance(values, (np.ndarray, float)):
                out[f"{prefix}.{field}.{group}"] = np.atleast_1d(values)
    return out


def outputs(step: gs.FlowStep) -> dict[str, np.ndarray]:
    """Return every output of the backward and forward traces and of their travel times."""
    back, fwd = gs.backward(step, groups(step)), gs.forward(step, groups(step))
    out = {}
    out.update(_flatten("back", back))
    out.update(_flatten("fwd", fwd))
    out.update(_flatten("tt_back", gs.travel_time(step, back, POROSITY)))
    out.update(_flatten("tt_fwd", gs.travel_time(step, fwd, POROSITY)))
    return out


def _compared_cells(name: str, ref: dict[str, np.ndarray], active: np.ndarray) -> np.ndarray:
    """Return the cells compared for an output: active cells; for mean times, where F > 1e-6.

    A mean time is m / F; where F is tiny it amplifies the solver-level differences of m.
    """
    if ".mean_time" not in name:
        return active
    group = name.split(".")[2]
    frac = ref[f"back.fraction_through.{group}" if name.startswith("tt_back") else
               f"fwd.source_fraction.{group}"]
    return active & (frac > 1e-6)


def achieved_agreement(single: gs.FlowStep, net: gs.FlowStep, splitter) -> dict[str, float]:
    """Return, per output, max |split - single| / max |single| over the compared cells."""
    a, b = outputs(single), outputs(net)
    assert set(a) == set(b), set(a) ^ set(b)
    errors = {}
    for name, ref in a.items():
        if ref.size == 1:
            mine = b[name]
        else:
            cells = _compared_cells(name, a, single.active)
            mine, ref = map_back(splitter, net, b[name])[cells], ref[cells]
        assert np.array_equal(np.isfinite(ref), np.isfinite(mine)), name
        defined = np.isfinite(ref)
        scale = max(float(np.abs(ref[defined]).max(initial=0.0)), 1e-300)
        errors[name] = float(np.abs(mine[defined] - ref[defined]).max(initial=0.0)) / scale
    return errors


@pytest.mark.parametrize(
    "key, kstpkper", [("m1_dis", (0, 0)), ("m3_disv", (0, 0))]
    + [("m6_transient", ks) for ks in TRANSIENT_STEPS],
)
def test_split_equals_single(key, kstpkper, split_run):
    """Every output of the split simulation equals the single-model output (RTOL)."""
    run, ws, splitter = split_run(key)
    single = gs.read_step(run.ws, kstpkper=kstpkper)
    net = gs.read_network(ws, kstpkper=kstpkper)
    assert len(net.model_names) == len(net.blocks) > 1
    assert net.notes["exchanges"], "no exchange became an edge"
    assert not any(p.text == "GWF-GWF" for p in net.packages), "exchange left as a term"
    errors = achieved_agreement(single, net, splitter)
    worst = max(errors, key=errors.get)
    assert errors[worst] <= RTOL, f"{worst}: {errors[worst]:.2e}"


@pytest.mark.parametrize("key", ["m1_dis", "m3_disv", "m6_transient"])
def test_split_network_residuals_and_identities(key, split_run):
    """Network residuals equal MF6's per-cell residuals; closure, duality and travel time hold."""
    _, ws, _ = split_run(key)
    reader = gs.open_simulation(ws)
    for kstpkper in reader.steps[:3]:
        net = reader.read(kstpkper)
        budget = cell_budget(net, flow_edges(net))
        scale = np.maximum(np.maximum(budget.inflow, budget.outflow), 1.0)
        assert np.all(np.abs(budget.residual) <= 1e-8 * scale)
        np.testing.assert_allclose(budget.residual, mf6_diagonal(net), atol=1e-12)
        check_identities(net)
        check_boundary_control(net)
        back = gs.backward(net, gs.groups_by_package(net))
        tt = gs.travel_time(net, back, POROSITY)
        for group in back.groups:
            assert abs(travel_time_closure(net, back, tt, group).relative_error) <= 1e-10


def test_one_model_of_a_split_alone(split_run):
    """Read alone, a split model's exchanges are boundary terms ('GWF-GWF') and budgets close."""
    _, ws, _ = split_run("m1_dis")
    step = gs.read_step(ws, model="m1_dis_1")
    exchanges = [p for p in step.packages if p.text == "GWF-GWF"]
    assert {p.partner for p in exchanges} == {"M1_DIS_0", "M1_DIS_2"}
    budget = cell_budget(step, flow_edges(step))
    np.testing.assert_allclose(budget.residual, mf6_diagonal(step), atol=1e-12)
    check_identities(step)
    sel = gs.select(step, package="GWF-GWF")
    assert sel.terms.sum() == sum(int((step.term_package == step.packages.index(p)).sum())
                                  for p in exchanges)


def test_split_network_selects_per_model(split_run):
    """Selectors match term names with or without the model prefix, and restrict by model."""
    _, ws, _ = split_run("m1_dis")
    net = gs.read_network(ws)
    names = net.package_names
    assert "m1_dis_1/WEL" in names and all("/" in n for n in names)
    rch = gs.select(net, package="RCH")
    rch_east = gs.select(net, package="RCH", model="m1_dis_1")
    assert 0 < rch_east.terms.sum() < rch.terms.sum()
    block = net.block("m1_dis_1")
    assert np.all((net.term_cell[rch_east.terms] >= block.offset)
                  & (net.term_cell[rch_east.terms] < block.offset + block.n))
    nodes = gs.global_nodes(net, "m1_dis_1", [0, 1])
    np.testing.assert_array_equal(nodes, [block.offset, block.offset + 1])
    with pytest.raises(AssertionError, match="needs a network step"):
        gs.select(gs.read_step(split_run("m1_dis")[0].ws), package="RCH", model="m1_dis")


def test_unsplit_network_equals_read_step(model_run):
    """open_simulation on a one-model simulation gives the read_step results bit for bit."""
    run = model_run("m1_dis")
    step, net = gs.read_step(run.ws), gs.read_network(run.ws)
    np.testing.assert_array_equal(net.flowja, step.flowja)
    np.testing.assert_array_equal(net.ja, step.ja)
    a = gs.backward(step, gs.groups_by_package(step))
    b = gs.backward(net, gs.groups_by_package(net))
    for g in a.groups:
        np.testing.assert_array_equal(a.fraction_through[g], b.fraction_through[g])
