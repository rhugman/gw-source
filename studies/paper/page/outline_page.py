"""Render docs/paper/outline.md (paper-draft-alt) as one HTML page with the draft template."""
import os
import re
import subprocess
import sys

import mistune

import build_draft as bd

HERE = os.path.dirname(os.path.abspath(__file__))


def build(repo: str, out_dir: str) -> str:
    """Write outline.html into out_dir and return its path."""
    with open(os.path.join(repo, "docs", "paper", "outline.md")) as f:
        text = f.read()
    title, _, rest = text.partition("\n")
    renderer = bd.Renderer()
    md = mistune.create_markdown(renderer=renderer, plugins=["table"])
    body = md(rest).replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"\[check\]", '<span class="chk">check</span>', body)
    body = re.sub(r"\[tutorial\]", '<span class="chk">tutorial</span>', body)
    toc = "\n".join(f'<li class="l{lvl}"><a href="#{hid}">{t}</a></li>' for lvl, hid, t in renderer.toc)
    commit = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%h %cs"], capture_output=True, text=True)
    with open(bd.TEMPLATE) as f:
        page = f.read()
    page = (page.replace("<title>Paper Draft (Examples)</title>", "<title>Paper Outline (Examples)</title>")
            .replace("<span>Full draft</span>", "<span>Outline</span>")
            .replace("{{H1}}", title.lstrip("# ")).replace("{{TOC}}", toc).replace("{{BODY}}", body)
            .replace("{{COMMIT}}", commit.stdout.strip())
            .replace("{{WORDS}}", f"{len(re.findall(r'\\w+', rest)):,}")
            .replace("words in the main text", "words in the outline")
            .replace("{{NCHECK}}", str(len(re.findall(r"\[(?:check|tutorial)\]", text)))))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "outline.html")
    with open(out, "w") as f:
        f.write(page)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1], os.path.join(HERE, "output", "site_outline")))
