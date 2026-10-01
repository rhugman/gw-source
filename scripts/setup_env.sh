#!/usr/bin/env bash
# Create or update the "gw-source" mamba environment, install FloPy develop,
# regenerate FloPy's MF6 classes from the MF6 develop DFNs, and download the
# MF6 nightly build (plus triangle, used by the Voronoi test model) into bin/.
#
# Usage: scripts/setup_env.sh
# Environment overrides: MAMBA (mamba/micromamba/conda executable), ENV_NAME.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BIN_DIR="${REPO_DIR}/bin"
ENV_NAME="${ENV_NAME:-gw-source}"
FLOPY_URL="git+https://github.com/modflowpy/flopy.git@develop"
MAMBA="${MAMBA:-$(command -v mamba || command -v micromamba || command -v conda || true)}"

if [[ -z "${MAMBA}" ]]; then
    echo "error: no mamba, micromamba or conda executable found on PATH (set MAMBA=...)" >&2
    exit 1
fi

run_in_env() {
    "${MAMBA}" run -n "${ENV_NAME}" "$@"
}

# 1. Create or update the environment. Run from the repo root so "-e ." in
#    environment.yml resolves to this package.
cd "${REPO_DIR}"
if "${MAMBA}" env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    echo "==> Updating environment '${ENV_NAME}'"
    "${MAMBA}" env update -n "${ENV_NAME}" -f environment.yml
else
    echo "==> Creating environment '${ENV_NAME}'"
    "${MAMBA}" env create -y -n "${ENV_NAME}" -f environment.yml
fi

# 2. Reinstall FloPy develop so a moving branch is always pulled fresh.
echo "==> Installing FloPy develop"
run_in_env python -m pip install --upgrade --force-reinstall --no-deps "flopy[codegen] @ ${FLOPY_URL}"
run_in_env python -m pip install "flopy[codegen] @ ${FLOPY_URL}"

# 3. Regenerate FloPy's MF6 classes from the MF6 develop definition files.
echo "==> Regenerating FloPy MF6 classes from MODFLOW 6 develop DFNs"
run_in_env python -m flopy.mf6.utils.generate_classes --ref develop

# 4. Download the MF6 nightly build, and triangle for the Voronoi test grid.
echo "==> Downloading MODFLOW 6 nightly build into ${BIN_DIR}"
#    Archives go to a throwaway folder rather than get-modflow's default ~/Downloads.
mkdir -p "${BIN_DIR}"
DOWNLOADS_DIR="$(mktemp -d)"
trap 'rm -rf "${DOWNLOADS_DIR}"' EXIT
run_in_env get-modflow --repo modflow6-nightly-build --downloads-dir "${DOWNLOADS_DIR}" "${BIN_DIR}"
run_in_env get-modflow --repo executables --subset triangle --downloads-dir "${DOWNLOADS_DIR}" "${BIN_DIR}"

# 5. Record versions.
echo "==> Versions"
run_in_env python - <<'EOF'
import json
from importlib.metadata import distribution

import flopy

direct_url = distribution("flopy").read_text("direct_url.json") or "{}"
commit = json.loads(direct_url).get("vcs_info", {}).get("commit_id", "unknown")
print(f"FloPy {flopy.__version__} (commit {commit})")
EOF
"${BIN_DIR}/mf6" --version
