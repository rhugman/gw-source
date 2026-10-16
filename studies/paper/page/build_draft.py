"""Assemble docs/paper/draft (paper-draft branch) into one HTML page with figures and tables."""
import glob
import html
import os
import re
import shutil
import subprocess
import sys

import mistune

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.html")
MARK = re.compile(r"^\s*\[\[(Figure|Table) (S?\d+)\]\]\s*$", re.M)


def slug(text: str) -> str:
    """Anchor id from heading text."""
    text = re.sub(r"<[^>]+>", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


class Renderer(mistune.HTMLRenderer):
    """HTML renderer that gives headings ids and collects a contents list."""

    def __init__(self):
        super().__init__(escape=False)
        self.toc = []

    def heading(self, text, level, **attrs):
        hid = slug(text)
        if level in (1, 2):
            self.toc.append((level + 1, hid, re.sub(r"<[^>]+>", "", text)))
        return f'<h{level + 1} id="{hid}">{text}</h{level + 1}>\n'


def displays(draft_dir: str) -> dict:
    """Figure and table blocks keyed by ("Figure", "1"), from display/*.md."""
    out = {}
    for path in sorted(glob.glob(os.path.join(draft_dir, "display", "*.md"))):
        with open(path) as f:
            text = f.read()
        parts = re.split(r"^## (Figure|Table) (S?\d+)\s*$", text, flags=re.M)
        for kind, n, body in zip(parts[1::3], parts[2::3], parts[3::3]):
            out[(kind, n)] = body.strip()
    return out


def fig_files(fig_dir: str) -> dict:
    """PNG file name by figure number."""
    out = {}
    for name in os.listdir(fig_dir):
        m = re.match(r"fig(S?\d+)_.*\.png$", name)
        if m:
            out[m.group(1)] = name
    return out


FILE_NOTE = re.compile(r"<!-- file: (\S+?) -->")


def fig_file(n: str, body: str, figs: dict):
    """Image of a figure block: a <!-- file: name.png --> note in its caption wins over the number in the file name."""
    m = FILE_NOTE.search(body)
    return m.group(1) if m else figs.get(n)


def noted_files(blocks: dict) -> set:
    """Images named by <!-- file: ... --> notes in the figure blocks."""
    return {m for body in blocks.values() for m in FILE_NOTE.findall(body)}


def render_block(kind: str, n: str, body: str, figs: dict, md) -> str:
    """HTML for one figure or table at its marker."""
    if kind == "Figure":
        img = fig_file(n, body, figs)
        src = f'<a href="fig/{img}" target="_blank"><img src="fig/{img}" alt="Figure {n}" loading="lazy"></a>' if img else ""
        return f'<figure id="fig{n}">{src}<figcaption>{md(body)}</figcaption></figure>'
    return f'<div class="tblock wide" id="table{n}">{md(body)}</div>'


SI_FIGS = {"numerical dispersion maps and time steps": "figS1_numerical_dispersion.png",
           "net attribution and PRT-area maps": "figS2_net_and_envelope.png",
           "verification on the test models": "figS10_verification.png",
           "Neversink model and published regions": "figS5_location_map.png",
           "Neversink backward fractions": "figS6_capture_maps.png",
           "Neversink areas against particle tracking": "figS7_overlap_maps.png",
           "Neversink probability of contribution": "figS8_probability_maps.png",
           # main-text figures that the reduced draft (draft_reduced) moves into the SI
           "the worked example of Foley and Black (2013) and a small well": "fig3_accounting.png",
           "forward fractions of river water and field recharge": "fig4_forward.png",
           "backward fractions on different grids": "fig5_grids.png",
           "seasonal snapshots": "fig6_seasons.png",
           "mean travel time against particles": "fig7_travel_time.png",
           "backward fractions through streams and a multi-aquifer well": "fig8_networks.png",
           "the unit-concentration example rebuilt": "fig11_unit_concentration.png",
           "Neversink full-mixing maps": "fig12_neversink.png",
           "numerical dispersion against cell size": "fig13_numerical_dispersion.png",
           "method schematic": "fig1_method_schematic.png",
           # main-text figures of the first reduced draft, moved into the SI when the gallery replaced them
           "contributing area against particle tracking": "fig2_contributing_area.png",
           "snapshots and transient tracking over 30 years": "fig9_transient_tracking.png",
           "probability of contribution before and after history matching": "fig10_ensembles.png",
           # SI figures of the reduced draft drawn in its SI round 1
           "verification checks on the test models": "figS21_verification.png",
           "Neversink particle area and ensemble mean F": "figS22_neversink_cd.png",
           "numerical dispersion maps and cell size": "figS23_numerical_dispersion.png"}
SI_FIG_WIDTH = {  # Markdown export only: width of an SI image in the reduced draft's SI PDF
    "figS21_verification.png": "90%",
    "fig9_transient_tracking.png": "80%",
    "fig11_unit_concentration.png": "80%"}
INLINE_MATH = re.compile(r"(?<![\\$])\$(?!\$)([^$\n]+?)\$")
SI_REF = re.compile(r"\{SI: ([^}]+)\}")


def si_plan(draft_dir: str) -> tuple:
    """Item type and merge target by SI name, from si/numbering.md."""
    kinds, merges = {}, {}
    path = os.path.join(draft_dir, "si", "numbering.md")
    if not os.path.exists(path):
        return kinds, merges
    with open(path) as f:
        for row in f:
            m = re.match(r"\| \{SI: ([^}]+)\} \| (Text|Table|Figure) S\d+[^|]*\| (.*?) \|", row)
            if m:
                kinds[m.group(1)] = m.group(2)
                t = SI_REF.match(m.group(3).strip())
                if t:
                    merges[m.group(1)] = t.group(1)
    return kinds, merges


PLACEMENT_ORDER = {"draft_reduced"}  # drafts whose SI items are numbered in the order they are placed


def si_order(draft_dir: str) -> list:
    """SI item names in the row order of si/numbering.md, alias rows left out."""
    kinds, merges = si_plan(draft_dir)
    return [n for n in kinds if n not in merges]


def si_chunks(draft_dir: str) -> dict:
    """SI item bodies by name, from the ## {SI: name} headings in si/*.md."""
    out = {}
    for path in sorted(glob.glob(os.path.join(draft_dir, "si", "*.md"))):
        if path.endswith("numbering.md"):
            continue
        with open(path) as f:
            parts = re.split(r"^## \{SI: ([^}]+)\}\s*$", f.read(), flags=re.M)
        for name, body in zip(parts[1::2], parts[2::2]):
            out[name.strip()] = out.get(name.strip(), "") + body.strip() + "\n\n"
    return out


def si_section(draft_dir: str, main: str) -> str:
    """Number SI items and return the SI markdown. A draft in PLACEMENT_ORDER numbers and places
    its items in the row order of si/numbering.md; the others number them by first citation in
    the main text, then the rest in file order, and place Texts, Tables and Figures in turn."""
    kinds, merges = si_plan(draft_dir)
    chunks = si_chunks(draft_dir)
    placed = os.path.basename(os.path.normpath(draft_dir)) in PLACEMENT_ORDER
    if placed:
        listed = si_order(draft_dir)
        names = [n for n in listed if n in chunks] + [n for n in chunks if n not in listed]
    else:
        names = [merges.get(n, n) for n in SI_REF.findall(main)] + list(chunks)
    labels, count = {}, {"Text": 0, "Table": 0, "Figure": 0}
    for name in names:
        if name not in labels and name in chunks:
            kind = kinds.get(name, "Text")
            count[kind] += 1
            labels[name] = f"{kind} S{count[kind]}"
    out = ["# Supporting Information (draft)"]
    if placed:
        order = list(labels)
    else:
        order = sorted(labels, key=lambda n: (["Text", "Table", "Figure"].index(labels[n].split()[0]), int(labels[n].split("S")[-1])))
    for name in order:
        img = SI_FIGS.get(name)
        pic = f'\n\n<a href="fig/{img}" target="_blank"><img src="fig/{img}" alt="{labels[name]}"></a>\n' if img else ""
        out.append(f"## {labels[name]}. {name[0].upper() + name[1:]}{pic}\n\n{chunks[name]}")
    refs = os.path.join(draft_dir, "si", "references.md")  # SI-only reference list, if the draft has one
    if os.path.exists(refs):
        with open(refs) as f:
            out.append(f.read().strip())
    sub = lambda m: labels.get(merges.get(m.group(1), m.group(1)), m.group(0))
    return SI_REF.sub(sub, "\n\n".join(out)), labels


def main_words(draft_dir: str) -> int:
    """Words of main-text prose in sections 01-09, without comments, headings, markers or display equations."""
    n = 0
    for path in sorted(glob.glob(os.path.join(draft_dir, "sections", "0[1-9]_*.md"))):
        with open(path) as f:
            t = re.sub(r"<!--.*?-->|\$\$.*?\$\$", "", f.read(), flags=re.S)
        t = re.sub(r"^#.*$|\[\[.*?\]\]", "", t, flags=re.M)
        n += len(re.findall(r"\w+", t))
    return n


PAGE_TITLES = {"draft_reduced": "Paper Draft (Reduced)"}


def build(repo: str, out_dir: str, draft: str = "draft") -> str:
    """Write paper_draft.html and copy the figure PNGs into out_dir; draft names the folder in docs/paper."""
    draft_dir = os.path.join(repo, "docs", "paper", draft)
    fig_dir = os.path.join(repo, "docs", "paper", "figures")
    parts = []
    for path in sorted(glob.glob(os.path.join(draft_dir, "sections", "*.md"))):
        with open(path) as f:
            parts.append(f.read().strip())
    text = "\n\n".join(parts)
    blocks, figs = displays(draft_dir), fig_files(fig_dir)
    inl = []

    def stash_inline(s: str) -> str:
        """Swap inline $...$ maths for placeholders, so markdown leaves it alone."""
        def keep(m):
            inl.append(html.escape(m.group(0), quote=False))
            return f"INLMATH{len(inl) - 1}X"
        parts = re.split(r"(\$\$.+?\$\$)", s, flags=re.S)
        return "".join(x if x.startswith("$$") else INLINE_MATH.sub(keep, x) for x in parts)

    text = stash_inline(text)
    blocks = {k: stash_inline(v) for k, v in blocks.items()}
    inline = mistune.create_markdown(escape=False, plugins=["table", "footnotes"])
    placed = {}

    def place(m):
        key = (m.group(1), m.group(2))
        if key in placed or key not in blocks:
            return ""
        placed[key] = True
        return "\n\n" + render_block(*key, blocks[key], figs, inline) + "\n\n"

    text = MARK.sub(place, text)
    si_md, labels = si_section(draft_dir, text)
    si_md = stash_inline(si_md)
    kinds, merges = si_plan(draft_dir)
    def si_cite(m):
        """Cite an SI item in the main text the Wiley way: 'Supporting Information, Text S1'."""
        label = labels.get(merges.get(m.group(1), m.group(1)))
        return f"Supporting Information, {label}" if label else m.group(0)

    text = SI_REF.sub(si_cite, text)
    text += "\n\n" + si_md
    maths = []

    def stash(m):
        maths.append(html.escape(m.group(0), quote=False))
        return f"\n\nMATHBLOCK{len(maths) - 1}X\n\n"

    text = re.sub(r"\$\$.+?\$\$", stash, text, flags=re.S)
    text = re.sub(r"\A\s*(?:<!--.*?-->\s*)+", "", text, flags=re.S)  # a leading comment is not the title
    title, _, rest = text.partition("\n")
    renderer = Renderer()
    md = mistune.create_markdown(renderer=renderer, plugins=["table", "footnotes"])
    body = md(rest).replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<p>MATHBLOCK(\d+)X</p>", lambda m: f'<div class="eq">{maths[int(m.group(1))]}</div>', body)
    body = re.sub(r"INLMATH(\d+)X", lambda m: inl[int(m.group(1))], body)
    body = re.sub(r"\[check(?:: ([^\]]+))?\]", lambda m: f'<span class="chk">check{": " + m.group(1) if m.group(1) else ""}</span>', body)
    body = re.sub(r"\{SI: ([^}]+)\}", r'<span class="si">SI: \1</span>', body)  # unresolved only
    missing = [f"{k} {n}" for k, n in blocks if (k, n) not in placed]
    if missing:
        body += '<h2 id="unplaced">Not yet cited in the text</h2>' + "".join(
            render_block(k, n, blocks[(k, n)], figs, inline) for k, n in blocks if (k, n) not in placed)
    toc = "\n".join(f'<li class="l{lvl}"><a href="#{hid}">{html.escape(t)}</a></li>' for lvl, hid, t in renderer.toc)
    words = main_words(draft_dir)
    commit = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%h %cs"], capture_output=True, text=True)
    with open(TEMPLATE) as f:
        page = f.read()
    page = (page.replace("{{H1}}", html.escape(title.lstrip("# "))).replace("{{TOC}}", toc)
            .replace("{{BODY}}", body).replace("{{COMMIT}}", commit.stdout.strip())
            .replace("{{WORDS}}", f"{words:,}").replace("Paper Draft (Examples)", PAGE_TITLES.get(draft, "Paper Draft (Examples)")).replace("{{NCHECK}}", str(len(re.findall(r"\[check", text)))))
    os.makedirs(os.path.join(out_dir, "fig"), exist_ok=True)
    for name in set(figs.values()) | noted_files(blocks):
        shutil.copy2(os.path.join(fig_dir, name), os.path.join(out_dir, "fig", name))
    out = os.path.join(out_dir, "paper_draft.html")
    with open(out, "w") as f:
        f.write(page)
    print("unplaced:", missing)
    return out


if __name__ == "__main__":
    name = sys.argv[2] if len(sys.argv) > 2 else "draft"  # docs/paper/<name>; draft_reduced builds into site_reduced
    site = "site" if name == "draft" else "site_" + name.removeprefix("draft_")
    print(build(sys.argv[1], os.path.join(HERE, "output", site), name))  # output/ is git-ignored
