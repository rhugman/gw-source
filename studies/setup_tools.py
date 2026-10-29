"""Set up the tools and data the paper's scripts need, in the active gw-source-paper environment.

Three parts, each skipped when it is already done, so the script can be rerun at any time:

1. MODFLOW 6 6.8.1 into bin/ (get-modflow). The results were made with the development build of
   23 September 2026 (6.9.0.dev0+67116fb). Release 6.8.1 is that commit plus two commits that
   change only the version string, so it computes the same. Development builds are deleted after
   a few weeks, which is why the release is pinned. It has builds for Linux, macOS on Apple
   silicon and Windows, but not for macOS on Intel. An mf6 already in bin/ is kept; delete it to
   get 6.8.1.
2. FloPy's MODFLOW 6 classes, generated from the input definitions (DFNs) of MODFLOW 6 6.8.1. A
   stamp file next to the generated classes records the version, so this runs once per
   environment.
3. The USGS Neversink/Rondout model (Fienen and others 2021; Corson-Dosch and others 2021, public
   domain): a sparse checkout of usgs/neversink_workflow at the commit the study was run on, in
   studies/neversink/external/neversink_workflow/ (git-ignored, about 1 GB). Only the folders
   the study reads are checked out. Needs git.

Run from anywhere, with the environment active:

    python studies/setup_tools.py                 # everything
    python studies/setup_tools.py --no-neversink  # skip the 1 GB Neversink data
    python studies/setup_tools.py --dry-run       # print what would be done
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "bin"
MF6_RELEASE = "6.8.1"
NEVERSINK_URL = "https://github.com/usgs/neversink_workflow.git"
NEVERSINK_COMMIT = "6e4a5fb4c87f54d875675906380d0a0029fadd6c"
NEVERSINK_DIR = REPO / "studies" / "neversink" / "external" / "neversink_workflow"
NEVERSINK_FOLDERS = (
    "neversink_optimal", "neversink_mf6", "processed_data",
    "output/neversink_mf6_optimal_output", "output/neversink_mp7_optimal_output",
    "output/modpath_mc", "output/parallel", "scripts", "notebooks_workflow_complete",
    "supplementary_tables", "python_packages_static",
)
STAMP_NAME = "gw_source_dfn_ref.txt"


def run(cmd: list[str], dry_run: bool) -> None:
    """Print cmd and run it unless dry_run."""
    print("  $", " ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def mf6_path(bin_dir: Path = BIN) -> Path:
    """Return the path of the mf6 executable in bin_dir."""
    return bin_dir / ("mf6.exe" if sys.platform.startswith("win") else "mf6")


def install_mf6(bin_dir: Path = BIN, release: str = MF6_RELEASE, dry_run: bool = False) -> None:
    """Download the MODFLOW 6 release into bin_dir unless an mf6 is already there."""
    exe = mf6_path(bin_dir)
    if exe.is_file():
        version = subprocess.run([str(exe), "--version"], stdout=subprocess.PIPE, text=True,
                                 encoding="utf-8").stdout.strip()
        print(f"MODFLOW 6: found {exe} ({version}), skipped")
        if release not in version:
            print(f"  note: not release {release}; delete {exe} and rerun to get it")
        return
    print(f"MODFLOW 6: downloading release {release} into {bin_dir}")
    if not dry_run:
        bin_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as downloads:
        run([sys.executable, "-m", "flopy.utils.get_modflow", "--repo", "modflow6",
             "--release-id", release, "--downloads-dir", downloads, str(bin_dir)], dry_run)


def flopy_stamp() -> Path:
    """Return the stamp file in FloPy's generated MODFLOW 6 class folder."""
    spec = importlib.util.find_spec("flopy")
    assert spec is not None and spec.origin, "FloPy is not installed: activate gw-source-paper"
    return Path(spec.origin).parent / "mf6" / "modflow" / STAMP_NAME


def generate_flopy_classes(ref: str = MF6_RELEASE, dry_run: bool = False) -> None:
    """Generate FloPy's MODFLOW 6 classes from the DFNs of ref, unless the stamp says it is done."""
    stamp = flopy_stamp()
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == ref:
        print(f"FloPy classes: already generated from MODFLOW 6 {ref}, skipped")
        return
    print(f"FloPy classes: generating from the MODFLOW 6 {ref} DFNs")
    run([sys.executable, "-m", "flopy.mf6.utils.generate_classes", "--ref", ref], dry_run)
    if not dry_run:
        stamp.write_text(ref + "\n", encoding="utf-8")


def git_head(repo_dir: Path, git: str) -> str:
    """Return the commit checked out in repo_dir, or '' if there is none."""
    proc = subprocess.run([git, "-C", str(repo_dir), "rev-parse", "HEAD"], stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    return proc.stdout.strip() if proc.returncode == 0 else ""


def fetch_neversink(dest: Path = NEVERSINK_DIR, url: str = NEVERSINK_URL,
                    commit: str = NEVERSINK_COMMIT, folders: tuple[str, ...] = NEVERSINK_FOLDERS,
                    dry_run: bool = False) -> None:
    """Make (or finish) the sparse checkout of the Neversink repository at commit in dest."""
    git = shutil.which("git")
    assert git, "git not found: install git, or skip the data with --no-neversink"
    if (dest / folders[0]).is_dir() and git_head(dest, git) == commit:
        print(f"Neversink data: found {dest} at {commit[:7]}, skipped")
        return
    print(f"Neversink data: sparse checkout of {url} at {commit[:7]} (about 1 GB)")
    if not (dest / ".git").exists():
        run([git, "clone", "--filter=blob:none", "--no-checkout", url, str(dest)], dry_run)
    run([git, "-C", str(dest), "sparse-checkout", "set", "--cone", *folders], dry_run)
    run([git, "-C", str(dest), "checkout", commit], dry_run)


def main(mf6: bool = True, flopy_classes: bool = True, neversink: bool = True,
         dry_run: bool = False) -> None:
    """Set up the selected parts."""
    if mf6:
        install_mf6(dry_run=dry_run)
    if flopy_classes:
        generate_flopy_classes(dry_run=dry_run)
    if neversink:
        fetch_neversink(dry_run=dry_run)
    print("dry run: nothing changed" if dry_run else "set-up done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up MODFLOW 6, FloPy classes and the "
                                                 "Neversink data for the paper's scripts.")
    parser.add_argument("--no-neversink", action="store_true",
                        help="skip the 1 GB Neversink data (enough for --quick)")
    parser.add_argument("--dry-run", action="store_true", help="print what would be done")
    args = parser.parse_args()
    main(neversink=not args.no_neversink, dry_run=args.dry_run)
