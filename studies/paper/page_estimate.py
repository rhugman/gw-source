"""Estimate the published Groundwater pages of a paper draft folder.

Groundwater (NGWA) gives 6 free pages (7 for NGWA members) and estimates about 850 words
per page. Figures count as the page area they take in a two-column layout: one column is
8.25 cm wide, two columns 17.15 cm, and the text block is 17.15 x 25.4 cm.

The estimate adds:
- prose words (title, abstract, sections 01-09 and the captions and tables placed in them)
  / 850; the impact statement and key words of the front matter are left out;
- for each placed figure, its height at the chosen width (from the PNG aspect ratio) plus
  1.5 cm for the caption, times its width, as a share of the text block;
- 0.15 page per display equation in the main text;
- reference words / 1,100, because references are set smaller.

A figure is double-column unless its caption block holds <!-- width: single -->. A caption
block may name its image with <!-- file: name.png -->; otherwise the image is the
docs/paper/figures PNG whose name starts with fig<n>_.

python studies/paper/page_estimate.py docs/paper/draft docs/paper/draft_reduced
"""

import glob
import os
import re
import sys

from PIL import Image

WORDS_PER_PAGE = 850
REF_WORDS_PER_PAGE = 1100
EQUATION_PAGES = 0.15
CAPTION_CM = 1.5
BLOCK_W_CM, BLOCK_H_CM = 17.15, 25.4
COLUMN_CM = {"single": 8.25, "double": 17.15}
MARK = re.compile(r"\[\[(Figure|Table) (S?\d+)\]\]")


def strip(text: str) -> str:
    """Text without HTML comments, display maths and placement markers."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    return MARK.sub(" ", text)


def count_words(text: str) -> int:
    """Whitespace-separated tokens that hold a letter or digit (a URL or DOI is one word)."""
    return sum(1 for t in strip(text).split() if re.search(r"\w", t))


def front_text(text: str) -> str:
    """Title and abstract of the front matter, without the impact statement and key words."""
    return re.sub(r"^\*\*(Article Impact Statement|Key words):\*\*.*$", "", text, flags=re.M)


def read(path: str) -> str:
    """Contents of a text file."""
    with open(path) as f:
        return f.read()


def displays(draft_dir: str) -> dict:
    """Figure and table blocks keyed by (kind, number), from display/*.md."""
    out = {}
    for path in sorted(glob.glob(os.path.join(draft_dir, "display", "*.md"))):
        parts = re.split(r"^## (Figure|Table) (S?\d+)\s*$", read(path), flags=re.M)
        for kind, n, body in zip(parts[1::3], parts[2::3], parts[3::3]):
            out[(kind, n)] = body.strip()
    return out


def figure_png(n: str, body: str, fig_dir: str) -> str:
    """Image file of a figure block."""
    m = re.search(r"<!-- file: (\S+?) -->", body)
    if m:
        return os.path.join(fig_dir, m.group(1))
    found = glob.glob(os.path.join(fig_dir, f"fig{n}_*.png"))
    assert len(found) == 1, f"no single PNG for Figure {n} in {fig_dir}"
    return found[0]


def figure_pages(png: str, width: str) -> float:
    """Share of the text block that a figure and its caption take."""
    w_px, h_px = Image.open(png).size
    w_cm = COLUMN_CM[width]
    return w_cm * (w_cm * h_px / w_px + CAPTION_CM) / (BLOCK_W_CM * BLOCK_H_CM)


def estimate(draft_dir: str, fig_dir: str) -> list:
    """Rows of (item, measure, pages) for one draft folder."""
    sections = sorted(glob.glob(os.path.join(draft_dir, "sections", "0[0-9]*.md")))
    blocks = displays(draft_dir)
    rows = []
    main = ""
    for path in sections:
        text = read(path)
        main += text
        n = count_words(front_text(text) if os.path.basename(path).startswith("00_") else text)
        rows.append((os.path.basename(path), f"{n:,} words", n / WORDS_PER_PAGE))
    placed = []
    for kind, n in MARK.findall(main):
        if (kind, n) in blocks and (kind, n) not in placed:
            placed.append((kind, n))
    for kind, n in placed:
        body = blocks[(kind, n)]
        words = count_words(body)
        rows.append((f"{kind} {n} caption/text", f"{words:,} words", words / WORDS_PER_PAGE))
        if kind == "Figure":
            width = "single" if "<!-- width: single -->" in body else "double"
            png = figure_png(n, body, fig_dir)
            rows.append((f"Figure {n} area ({width})", os.path.basename(png), figure_pages(png, width)))
    n_eq = len(re.findall(r"\$\$.*?\$\$", re.sub(r"<!--.*?-->", "", main, flags=re.S), flags=re.S))
    rows.append(("display equations", f"{n_eq}", n_eq * EQUATION_PAGES))
    ref_path = os.path.join(draft_dir, "sections", "10_references.md")
    ref_text = re.sub(r"^#.*$", "", read(ref_path), flags=re.M)
    n_ref = len([p for p in strip(ref_text).split("\n\n") if p.strip()])
    ref_words = count_words(ref_text)
    rows.append(("references", f"{n_ref} entries, {ref_words:,} words", ref_words / REF_WORDS_PER_PAGE))
    return rows


def print_table(name: str, rows: list) -> None:
    """Print the rows and the total of one draft."""
    print(f"\n{name}")
    print(f"{'item':<34} {'measure':<34} {'pages':>6}")
    for item, measure, pages in rows:
        print(f"{item:<34} {measure:<34} {pages:6.2f}")
    prose = sum(p for i, m, p in rows if m.endswith("words") and not i.startswith("references"))
    print(f"{'prose subtotal':<34} {'':<34} {prose:6.2f}")
    print(f"{'TOTAL':<34} {'':<34} {sum(p for _, _, p in rows):6.2f}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    paper = os.path.join(here, "..", "..", "docs", "paper")
    drafts = sys.argv[1:] or [os.path.join(paper, "draft"), os.path.join(paper, "draft_reduced")]
    for draft in drafts:
        print_table(os.path.normpath(draft), estimate(draft, os.path.join(paper, "figures")))
