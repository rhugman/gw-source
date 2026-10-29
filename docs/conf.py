"""Sphinx configuration for the gwsource documentation."""

import shutil
from pathlib import Path

import gwsource

DOCS_DIR = Path(__file__).parent
REPO_DIR = DOCS_DIR.parent

project = "gwsource"
author = "Rui Hugman"
copyright = "2026, Rui Hugman"
version = gwsource.__version__
release = gwsource.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_nb",
    "sphinx_copybutton",
]

# The notebooks are committed with their outputs and need MODFLOW 6 to run, so they are shown
# as they are, not executed. They live in tutorials/ and are copied here at build time.
nb_execution_mode = "off"
TUTORIALS_SRC = REPO_DIR / "tutorials"
TUTORIALS_DST = DOCS_DIR / "tutorials"
shutil.rmtree(TUTORIALS_DST, ignore_errors=True)
shutil.copytree(
    TUTORIALS_SRC,
    TUTORIALS_DST,
    ignore=shutil.ignore_patterns("_work", ".ipynb_checkpoints", "__pycache__", "README.md"),
)
# The tutorials README is the index page; a hidden toctree adds the notebooks to the navigation.
notebooks = sorted(path.relative_to(TUTORIALS_DST) for path in TUTORIALS_DST.glob("*/*.ipynb"))
toctree = "\n".join(["", "```{toctree}", ":hidden:", ""] + [nb.with_suffix("").as_posix() for nb in notebooks] + ["```", ""])
(TUTORIALS_DST / "index.md").write_text((TUTORIALS_SRC / "README.md").read_text() + toctree)

autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "show-inheritance": True}
autodoc_typehints = "description"
autosummary_generate = True
templates_path = ["_templates"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
}

exclude_patterns = ["_build", "**/.ipynb_checkpoints"]
suppress_warnings = ["mystnb.unknown_mime_type", "myst.xref_missing"]

html_theme = "pydata_sphinx_theme"
html_title = f"gwsource {release}"
html_theme_options = {
    "github_url": "https://github.com/rhugman/gw-source",
    "navigation_with_keys": False,
}
html_show_sourcelink = False


def docstring_as_text(app, what, name, obj, options, lines):
    """Show docstrings verbatim: they are plain text (formulas, aligned lists), not reStructuredText."""
    if lines:
        lines[:] = ["::", ""] + [f"    {line}" for line in lines] + [""]


def setup(app):
    app.connect("autodoc-process-docstring", docstring_as_text)
