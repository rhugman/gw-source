"""Finish the gw-source environment: FloPy develop, its MODFLOW 6 classes, and the programs in bin/.

Run it with the gw-source environment active, from anywhere, on Linux, macOS or Windows:

    mamba env create -f environment.yml   # once, from the repository root
    mamba activate gw-source
    python scripts/setup_env.py

The script:

1. reinstalls FloPy from its develop branch, so a moving branch is always pulled fresh;
2. regenerates FloPy's MODFLOW 6 classes from the MODFLOW 6 develop input definitions (DFNs);
3. downloads the MODFLOW 6 nightly build, triangle (used by the Voronoi grids) and PEST++ (used by
   tutorial 09) into bin/;
4. prints the FloPy version and commit and `mf6 --version`.

Rerun it whenever you want to pick up new FloPy or MODFLOW 6 changes.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "bin"
FLOPY_URL = "git+https://github.com/modflowpy/flopy.git@develop"


def run(cmd: list[str]) -> None:
    """Print cmd and run it, stopping on failure."""
    print("  $", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def python_module(module: str, *args: str) -> list[str]:
    """Return the command that runs a module with this environment's Python."""
    return [sys.executable, "-m", module, *args]


def install_flopy_develop() -> None:
    """Reinstall FloPy develop without touching its dependencies, then add any new ones."""
    print("==> Installing FloPy develop", flush=True)
    run(python_module("pip", "install", "--upgrade", "--force-reinstall", "--no-deps",
                      f"flopy[codegen] @ {FLOPY_URL}"))
    run(python_module("pip", "install", f"flopy[codegen] @ {FLOPY_URL}"))


def generate_flopy_classes() -> None:
    """Regenerate FloPy's MODFLOW 6 classes from the MODFLOW 6 develop DFNs."""
    print("==> Regenerating FloPy MF6 classes from MODFLOW 6 develop DFNs", flush=True)
    run(python_module("flopy.mf6.utils.generate_classes", "--ref", "develop"))


def download_programs(bin_dir: Path = BIN) -> None:
    """Download the MF6 nightly build, triangle and PEST++ into bin_dir."""
    print(f"==> Downloading MODFLOW 6, triangle and PEST++ into {bin_dir}", flush=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    # Archives go to a throwaway folder rather than get-modflow's default ~/Downloads.
    with tempfile.TemporaryDirectory() as downloads:
        run(python_module("flopy.utils.get_modflow", "--repo", "modflow6-nightly-build",
                          "--downloads-dir", downloads, str(bin_dir)))
        run(python_module("flopy.utils.get_modflow", "--repo", "executables", "--subset",
                          "triangle", "--downloads-dir", downloads, str(bin_dir)))
        run(python_module("pyemu.utils.get_pestpp", "--downloads-dir", downloads, str(bin_dir)))


def print_versions(bin_dir: Path = BIN) -> None:
    """Print the FloPy version and commit and the MF6 version."""
    import flopy

    direct_url = distribution("flopy").read_text("direct_url.json") or "{}"
    commit = json.loads(direct_url).get("vcs_info", {}).get("commit_id", "unknown")
    print("==> Versions")
    print(f"FloPy {flopy.__version__} (commit {commit})")
    mf6 = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    run([str(mf6), "--version"])


def main() -> None:
    """Run every set-up step in order."""
    assert importlib.util.find_spec("gwsource"), (
        "gwsource not found: activate the gw-source environment first"
    )
    install_flopy_develop()
    generate_flopy_classes()
    download_programs()
    print_versions()


if __name__ == "__main__":
    main()
