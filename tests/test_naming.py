"""Enforce the naming rule: the commercial product name never appears in the repository."""

from pathlib import Path

SKIP_DIRS = frozenset(
    {"references", "bin", ".claude", ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
     ".ipynb_checkpoints", "_work", "output", "large_ws"}
)  # source, vendored and generated (git-ignored) folders


def forbidden_terms() -> tuple[str, ...]:
    """Return the forbidden terms, built by concatenation so this file does not contain them."""
    return ("flow" + "source", "fs" + "20")


def repo_files(root: Path, skip_dirs: frozenset[str] = SKIP_DIRS) -> list[Path]:
    """Return every file under root outside the skipped directories and egg-info folders."""
    files = []
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if any(p in skip_dirs or p.endswith(".egg-info") for p in parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def find_violations(root: Path) -> list[str]:
    """Return 'path: term' for each file whose name or content contains a forbidden term."""
    violations = []
    for path in repo_files(root):
        text = path.read_bytes().decode("utf-8", errors="ignore").lower()
        name = str(path.relative_to(root)).lower()
        for term in forbidden_terms():
            if term in text or term in name:
                violations.append(f"{path.relative_to(root)}: {term}")
    return violations


def test_no_forbidden_name_in_repo():
    """No file name or file content outside references/ uses the product name."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "PLAN.md").is_file()
    violations = find_violations(root)
    assert not violations, "forbidden name found:\n" + "\n".join(violations)


def test_detector_catches_joined_word_only(tmp_path):
    """The joined word and its short form are caught; spaced or hyphenated phrases are not."""
    bad = tmp_path / "bad.txt"
    bad.write_text("Uses " + "Flow" + "Source" + " and " + "FS" + "20.")
    ok = tmp_path / "ok.txt"
    ok.write_text("flow source tracing; flow-source fractions; flows ourselves")
    found = find_violations(tmp_path)
    assert found == ["bad.txt: " + forbidden_terms()[0], "bad.txt: " + forbidden_terms()[1]]
