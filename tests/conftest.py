"""Shared pytest fixtures: locate the MF6 and triangle executables in <repo>/bin and report versions."""

import json
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import pytest


def repo_dir() -> Path:
    """Return the repository root (the parent of tests/)."""
    return Path(__file__).resolve().parents[1]


def find_exe(name: str, bin_dir: Path | None = None) -> Path:
    """Return the path of an executable in <repo>/bin, failing with a setup hint if it is missing."""
    bin_dir = repo_dir() / "bin" if bin_dir is None else bin_dir
    suffix = ".exe" if sys.platform.startswith("win") else ""
    exe = bin_dir / f"{name}{suffix}"
    assert exe.is_file(), f"{exe} not found; run python scripts/setup_env.py to download it into bin/"
    return exe


def flopy_version() -> str:
    """Return the installed FloPy version and, for a git install, its commit hash."""
    import flopy

    direct_url = distribution("flopy").read_text("direct_url.json") or "{}"
    commit = json.loads(direct_url).get("vcs_info", {}).get("commit_id", "unknown")
    return f"FloPy {flopy.__version__} (commit {commit})"


def mf6_version(exe: Path) -> str:
    """Return the output of `mf6 --version`."""
    out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, check=True)
    return " ".join(out.stdout.split())


def pytest_report_header(config) -> list[str]:
    """Print the FloPy and MF6 versions in the pytest header."""
    lines = [flopy_version()]
    bin_dir = repo_dir() / "bin"
    mf6 = bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")
    lines.append(mf6_version(mf6) if mf6.is_file() else f"mf6 not found in {bin_dir}")
    return lines


@pytest.fixture(scope="session")
def mf6_exe() -> Path:
    """Path of the MF6 executable in <repo>/bin."""
    return find_exe("mf6")


@pytest.fixture(scope="session")
def triangle_exe() -> Path:
    """Path of the triangle executable in <repo>/bin (used by the Voronoi test model)."""
    return find_exe("triangle")


@pytest.fixture(scope="session")
def model_run(tmp_path_factory, mf6_exe, triangle_exe):
    """Return a function key -> ModelRun that builds and runs each test model once per session."""
    from models import build_model

    cache = {}

    def get(key: str):
        if key not in cache:
            cache[key] = build_model(key, tmp_path_factory.mktemp(key), mf6_exe, triangle_exe)
        return cache[key]

    return get
