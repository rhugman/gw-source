"""Export the paper draft as one Markdown file with figures, for reading outside the artifact.

Same assembly as build_draft.py: sections in order, figures and tables at their [[...]]
markers, SI items numbered by first citation and appended. Evidence comments are removed.

python export_md.py <repo> <out_dir>
"""

import os
import re
import shutil
import sys

import build_draft as bd

COMMENT = re.compile(r"<!--.*?-->", re.S)


def clean(text: str) -> str:
    """Drop evidence comments and the blank runs they leave."""
    text = COMMENT.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"(?<=\S) {2,}(?=\S)", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def display_math(text: str) -> str:
    """Put each $$...$$ block on its own lines with blank lines around it."""
    return re.sub(r"\s*(\$\$.+?\$\$)\s*", lambda m: "\n\n" + m.group(1).strip() + "\n\n", text, flags=re.S)


def block_md(kind: str, n: str, body: str, figs: dict) -> str:
    """Markdown for one figure or table at its marker."""
    img = bd.fig_file(n, body, figs) if kind == "Figure" else None
    if img:
        return f"![](fig/{img})\n\n{body}"
    return body


def export(repo: str, out_dir: str, draft: str = "draft") -> str:
    """Write paper_draft.md and the figure PNGs into out_dir; return the file path."""
    draft_dir = os.path.join(repo, "docs", "paper", draft)
    fig_dir = os.path.join(repo, "docs", "paper", "figures")
    text = "\n\n".join(open(p).read().strip() for p in sorted(
        os.path.join(draft_dir, "sections", f) for f in os.listdir(os.path.join(draft_dir, "sections"))
        if f.endswith(".md")))
    blocks, figs = bd.displays(draft_dir), bd.fig_files(fig_dir)
    placed = set()

    def place(m):
        key = (m.group(1), m.group(2))
        if key in placed or key not in blocks:
            return ""
        placed.add(key)
        return "\n\n" + block_md(*key, blocks[key], figs) + "\n\n"

    text = bd.MARK.sub(place, text)
    si_md, labels = bd.si_section(draft_dir, text)
    kinds, merges = bd.si_plan(draft_dir)
    text = bd.SI_REF.sub(lambda m: f"Supporting Information, {labels[merges.get(m.group(1), m.group(1))]}"
                         if merges.get(m.group(1), m.group(1)) in labels else m.group(0), text)
    def si_image(m):
        """Markdown image of an SI figure, with its width from bd.SI_FIG_WIDTH if it has one."""
        width = bd.SI_FIG_WIDTH.get(os.path.basename(m.group(1)))
        return f"\n\n![]({m.group(1)})" + (f"{{width={width}}}" if width else "") + "\n\n"

    si_md = re.sub(r'\n*<a href="(fig/[^"]+)" target="_blank"><img src="[^"]+" alt="([^"]+)"></a>\n*',
                   si_image, si_md)
    out = display_math(clean(text + "\n\n" + si_md)).strip() + "\n"
    os.makedirs(os.path.join(out_dir, "fig"), exist_ok=True)
    for name in set(figs.values()) | bd.noted_files(blocks):
        shutil.copy2(os.path.join(fig_dir, name), os.path.join(out_dir, "fig", name))
    path = os.path.join(out_dir, "paper_draft.md")
    with open(path, "w") as f:
        f.write(out)
    missing = [f"{k} {n}" for k, n in blocks if (k, n) not in placed]
    print("unplaced:", missing)
    return path


if __name__ == "__main__":
    print(export(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "draft"))
