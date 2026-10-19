"""Typeset the main text of an exported paper draft in Wiley's NJD LaTeX template and count pages.

Groundwater (NGWA, Wiley) has no journal-specific LaTeX template. The script uses the setup the
author used for an earlier Groundwater submission: Wiley's NJD class (WileyNJDv5.cls) with
Harvard (author-date) references from wileyNJD-Harvard.bst. It writes two layouts from one input:

- "submission": the author's setup as submitted: [HARVARD,Times1COL,doublespace], line numbers,
  \\articletype{Research Paper}, unnumbered sections, the Article Impact Statement as the first
  section, placeholder authors.
- "print": the same class in its two-column Times option, [HARVARD,Times2COL], single-spaced and
  without line numbers. It approximates published pages and gives the page count.

Steps: cut the export at the Supporting Information heading; take the title, impact statement,
abstract and key words into the front matter; turn the reference list into a .bib file; replace
the in-text author-year citations that match one reference with \\citet or \\citep; convert the
body to LaTeX with pandoc; place each figure and table at its marker; compile with pdflatex
-no-shell-escape and bibtex; report the pages and how full the last page is.

Citations: "Name (2013)" becomes \\citet. A parenthesis that holds only citations, "(A 2013; B
2016)", becomes \\citep. In a parenthesis that also holds other text, "(PRT; A 2026)", each
citation becomes \\citealp inside the literal parentheses. A citation whose name and year match
no single reference stays plain text and is reported.

Figures in the print layout go in one column when they were drawn at column width (read from the
PNG's dpi), because a full-width drawing shrunk to a column would set its labels at under half
size. Otherwise they span both columns. In the submission layout figures keep their drawn width.

python typeset_groundwater.py reduced [print|submission|both] [template_dir]
python typeset_groundwater.py full
python typeset_groundwater.py docs/paper/export_reduced/paper_draft.md print

Output (git-ignored): studies/paper/output/latex/<draft>_<layout>/main.tex, refs.bib, main.pdf.
"""

import os
import re
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
PAPER = os.path.join(REPO, "docs", "paper")
TEMPLATE_DIR = os.path.normpath(os.path.join(REPO, "..", "gw_template_njd"))
OUT_ROOT = os.path.join(REPO, "studies", "paper", "output", "latex")
PANDOC = "/opt/homebrew/bin/pandoc"
TEXBIN = "/Library/TeX/texbin"
DRAFTS = {"reduced": "export_reduced", "full": "export"}
BST_NAME = "WileyNJD-Harvard"  # the name the class asks for; the shipped file is wileyNJD-Harvard.bst

SI_HEADING = re.compile(r"^# Supporting Information.*$", re.M)
FIGURE = re.compile(r"!\[[^\]]*\]\((\S+?)\)\s*\n\s*\n\*\*Figure (\d+)\.\*\*[ \t]*(.+?)(?=\n\s*\n|\Z)", re.S)
TABLE = re.compile(r"\*\*Table (\d+)\.\*\*[ \t]*(.+?)\n\s*\n((?:\|.*(?:\n|\Z))+)")
SPLIT = "ZZSPLITZZ"
SINGLE_MAX_CM = 11.0  # drawn at most this wide: still legible in an 8.7 cm column (labels >= 79 %)
TEXT_WIDTH_CM = 17.78  # text width of the Times1COL and Times2COL layouts

LAYOUTS = {
    "submission": dict(options="HARVARD,Times1COL,doublespace", columns=1, lineno=True),
    "print": dict(options="HARVARD,Times2COL", columns=2, lineno=False),
}

# Groundwater-style reference: "Authors. Year. Rest" and the forms the rest takes.
REF_HEAD = re.compile(r"^(?P<authors>.+?) (?P<year>(?:19|20)\d\d[a-z]?)\. (?P<rest>.+)$", re.S)
LINK = r"(?:\s(?P<link>https?://\S+))?$"
REF_FORMS = [
    ("article", re.compile(r"^(?P<title>.+?[.?!])\s\*(?P<journal>[^*]+)\*\s(?P<volume>[^,:]+?)"
                           r"(?:, no\. (?P<number>[^:]+))?: (?P<pages>[^\s]+?)\." + LINK)),
    ("inproceedings", re.compile(r"^(?P<title>.+?)\. In \*(?P<booktitle>[^*]+)\*, (?P<details>.+?)\. "
                                 r"(?P<address>[^.:]+): (?P<publisher>.+?)\." + LINK)),
    ("mastersthesis", re.compile(r"^(?P<title>.+?)\. (?P<type>(?:MASc|MSc|MS|MA) thesis), (?P<school>[^,]+), "
                                 r"(?P<address>.+?)\." + LINK)),
    ("phdthesis", re.compile(r"^(?P<title>.+?)\. (?P<type>(?:PhD|Ph\.D\.) (?:thesis|dissertation)), "
                             r"(?P<school>[^,]+), (?P<address>.+?)\." + LINK)),
    ("techreport", re.compile(r"^(?P<title>.+?)\. (?P<institution>U\.S\. Geological Survey) (?P<series>(?:Techniques and "
                              r"Methods|Open-File Report|Scientific Investigations Report|Water-Resources "
                              r"Investigations Report|Professional Paper|Circular|Fact Sheet|Data Series).*?)\. "
                              r"(?P<address>[A-Z][^.:]*): (?P<publisher>[^.]+)\." + LINK)),
    ("book", re.compile(r"^\*(?P<title>[^*]+)\*\.\s(?P<address>[^:]+): (?P<publisher>.+?)\." + LINK)),
    ("misc", re.compile(r"^(?P<title>.+?)\. (?P<howpublished>.+?)\.?" + LINK, re.S)),
]
INITIALS = re.compile(r"^((?:[A-Z][a-z]?\.-?)+)\s+(.+)$")
YEARS = r"(?:19|20)\d\d[a-z]?(?:, (?:19|20)\d\d[a-z]?)*"
LOOSE_CITE = re.compile(r"\b[A-Z][\w'’-]+(?: and [A-Z][\w'’-]+| et al\.)? \(?(?:19|20)\d\d[a-z]?\b")

UNICODE_MAP = {
    "⁰": r"\ensuremath{^{0}}", "¹": r"\ensuremath{^{1}}", "²": r"\ensuremath{^{2}}",
    "³": r"\ensuremath{^{3}}", "⁴": r"\ensuremath{^{4}}", "⁵": r"\ensuremath{^{5}}",
    "⁶": r"\ensuremath{^{6}}", "⁷": r"\ensuremath{^{7}}", "⁸": r"\ensuremath{^{8}}",
    "⁹": r"\ensuremath{^{9}}", "⁻": r"\ensuremath{^{-}}", "⁺": r"\ensuremath{^{+}}",
    "₀": r"\ensuremath{_{0}}", "₁": r"\ensuremath{_{1}}", "₂": r"\ensuremath{_{2}}",
    "×": r"\ensuremath{\times}", "−": r"\ensuremath{-}", "±": r"\ensuremath{\pm}",
    "≤": r"\ensuremath{\leq}", "≥": r"\ensuremath{\geq}", "≈": r"\ensuremath{\approx}",
    "≠": r"\ensuremath{\neq}", "∼": r"\ensuremath{\sim}", "→": r"\ensuremath{\rightarrow}",
    "←": r"\ensuremath{\leftarrow}", "↔": r"\ensuremath{\leftrightarrow}", "∞": r"\ensuremath{\infty}",
    "°": r"\ensuremath{^{\circ}}", "µ": r"\ensuremath{\mu}", "·": r"\ensuremath{\cdot}",
    "√": r"\ensuremath{\surd}", "∑": r"\ensuremath{\sum}", "∂": r"\ensuremath{\partial}",
    "§": r"\S{}", "‰": r"\textperthousand{}", "✓": r"\ensuremath{\checkmark}",
    "α": r"\ensuremath{\alpha}", "β": r"\ensuremath{\beta}", "γ": r"\ensuremath{\gamma}",
    "δ": r"\ensuremath{\delta}", "ε": r"\ensuremath{\epsilon}", "θ": r"\ensuremath{\theta}",
    "κ": r"\ensuremath{\kappa}", "λ": r"\ensuremath{\lambda}", "μ": r"\ensuremath{\mu}",
    "ν": r"\ensuremath{\nu}", "π": r"\ensuremath{\pi}", "ρ": r"\ensuremath{\rho}",
    "σ": r"\ensuremath{\sigma}", "τ": r"\ensuremath{\tau}", "φ": r"\ensuremath{\phi}",
    "χ": r"\ensuremath{\chi}", "ψ": r"\ensuremath{\psi}", "ω": r"\ensuremath{\omega}",
    "Γ": r"\ensuremath{\Gamma}", "Δ": r"\ensuremath{\Delta}", "Θ": r"\ensuremath{\Theta}",
    "Λ": r"\ensuremath{\Lambda}", "Σ": r"\ensuremath{\Sigma}", "Φ": r"\ensuremath{\Phi}",
    "Ψ": r"\ensuremath{\Psi}", "Ω": r"\ensuremath{\Omega}",
}
# Characters that pdflatex sets directly with T1 fonts and UTF-8 input.
T1_OK = set("–—‘’“”…«»") | {chr(c) for c in range(0xC0, 0x100) if c not in (0xD7, 0xF7)} | {"\u00a0"}


def resolve_draft(arg: str) -> tuple:
    """Path of the exported Markdown file and a short name for the output folder."""
    if arg in DRAFTS:
        return os.path.join(PAPER, DRAFTS[arg], "paper_draft.md"), arg
    path = arg if arg.endswith(".md") else os.path.join(PAPER, arg, "paper_draft.md")
    path = os.path.abspath(path)
    assert os.path.isfile(path), f"no exported draft at {path}"
    return path, os.path.basename(os.path.dirname(path))


def main_text(md: str) -> str:
    """The export up to the Supporting Information heading."""
    m = SI_HEADING.search(md)
    assert m, "no '# Supporting Information' heading: cannot separate the main text"
    return md[:m.start()]


def split_front(text: str) -> tuple:
    """Title, impact statement, abstract, key words and the remaining body."""
    title = re.search(r"^# (.+)$", text, re.M)
    assert title, "no title line"
    fields = {}
    for name in ("Article Impact Statement", "Abstract", "Key words"):
        m = re.search(rf"^\*\*{name}:\*\*[ \t]*(.+?)(?=\n\s*\n|\Z)", text, re.M | re.S)
        assert m, f"no '**{name}:**' paragraph in the front matter"
        fields[name] = m.group(1).strip()
        text = text.replace(m.group(0), "")
    body = text.replace(title.group(0), "", 1)
    return title.group(1).strip(), fields["Article Impact Statement"], fields["Abstract"], fields["Key words"], body


def split_refs(body: str) -> tuple:
    """Body before the References heading and the list of reference paragraphs."""
    m = re.search(r"^# References\s*$", body, re.M)
    assert m, "no '# References' heading"
    refs = [p.strip() for p in re.split(r"\n\s*\n", body[m.end():]) if p.strip()]
    return body[:m.start()], refs


def pandoc_many(chunks: list) -> list:
    """LaTeX for each Markdown chunk, from one pandoc call."""
    if not chunks:
        return []
    src = f"\n\n{SPLIT}\n\n".join(chunks)
    cmd = [PANDOC, "-f", "markdown+tex_math_dollars+autolink_bare_uris-auto_identifiers-implicit_figures-subscript-superscript-fancy_lists",
           "-t", "latex", "--wrap=none", "--syntax-highlighting=none"]
    out = subprocess.run(cmd, input=src, capture_output=True, text=True, check=True).stdout
    parts = [p.strip() for p in re.split(rf"\n*{SPLIT}\n*", out)]
    assert len(parts) == len(chunks), f"pandoc split mismatch: {len(parts)} parts for {len(chunks)} chunks"
    return parts


# ---------------------------------------------------------------- references


def parse_authors(authors: str) -> tuple:
    """BibTeX author field and the surnames, from 'Last, I., I. Last, and I. Last.'."""
    if "," not in authors:  # a body as author, e.g. 'Environment Agency.'
        name = authors.rstrip(".")
        return f"{{{name}}}", [name]
    parts = [p.strip() for p in re.split(r",\s+(?:and\s+)?", authors.strip())]
    assert len(parts) >= 2, f"cannot read authors: {authors}"
    people = [(parts[0], parts[1])]
    for p in parts[2:]:
        m = INITIALS.match(p)
        assert m, f"cannot read author '{p}' in: {authors}"
        people.append((m.group(2).rstrip("."), m.group(1)))
    names = [f"{last}, {bib_initials(first)}" for last, first in people]
    return " and ".join(names), [last for last, _ in people]


def bib_initials(initials: str) -> str:
    """Initials BibTeX abbreviates correctly: 'M.J.' -> 'M. J.', 'C.-F.' -> '{\\relax C.-F}'."""
    if "-" in initials:
        return rf"{{\relax {initials.rstrip('.')}}}"
    return " ".join(re.findall(r"[A-Z][a-z]?\.", initials))


def cite_name(surnames: list) -> str:
    """The author part of an in-text citation, as Groundwater writes it."""
    if len(surnames) == 1:
        return surnames[0]
    if len(surnames) == 2:
        return f"{surnames[0]} and {surnames[1]}"
    return f"{surnames[0]} et al."


def parse_rest(rest: str) -> tuple:
    """BibTeX entry type and Markdown fields of the part after the year."""
    rest = rest.strip()
    for kind, pattern in REF_FORMS:
        m = pattern.match(rest)
        if m:
            fields = {k: v.strip() for k, v in m.groupdict().items() if v}
            return kind, fields
    raise AssertionError(f"reference form not recognised: {rest[:80]}")


def tidy_fields(kind: str, fields: dict, year: str) -> dict:
    """Split compound parts into BibTeX fields: link into doi or url, series into type and number."""
    link = fields.pop("link", None)
    if link and link.startswith("https://doi.org/") and kind == "article":
        fields["doi"] = link[len("https://doi.org/"):]  # the style prints a DOI only for articles
    elif link:
        fields["url"] = link
    fields["title"] = fields["title"].rstrip(".")
    if kind == "techreport":
        series = fields.pop("series")
        kind_part, number = series.split(", ", 1) if ", " in series else series.rsplit(" ", 1)
        fields["type"], fields["number"] = kind_part, number
        fields.pop("publisher")
    if kind == "inproceedings":
        details = fields.pop("details")
        note = re.search(r"\s*\[(.+?)\]", details)
        if note:
            fields["note"] = f"[{note.group(1)}]"
            details = details.replace(note.group(0), "")
        pages = re.search(r",\s*(\d+)[–-](\d+)\s*$", details)
        if pages:
            fields["pages"] = f"{pages.group(1)}--{pages.group(2)}"
            details = details[:pages.start()]
        details = re.sub(rf",\s*{year[:4]}\s*$", "", details.strip(", "))  # the style adds the year
        fields["booktitle"] = f"{fields['booktitle']}, {details}"
    if "pages" in fields:
        fields["pages"] = fields["pages"].replace("–", "--")
    return fields


def parse_reference(ref_md: str) -> dict:
    """One Groundwater-style reference as a BibTeX entry with its citation name and year."""
    m = REF_HEAD.match(ref_md.replace("\n", " "))
    assert m, f"no 'Authors. Year.' at the start of: {ref_md[:80]}"
    author_field, surnames = parse_authors(m.group("authors"))
    kind, fields = parse_rest(m.group("rest"))
    return dict(kind=kind, author=author_field, year=m.group("year"), name=cite_name(surnames),
                surname=surnames[0], fields=tidy_fields(kind, fields, m.group("year")))


def assign_keys(entries: list) -> None:
    """A unique BibTeX key for each entry: surname and year."""
    used = set()
    for e in entries:
        base = re.sub(r"[^a-z]", "", e["surname"].lower()) + e["year"]
        key, n = base, 1
        while key in used:
            n += 1
            key = f"{base}-{n}"
        used.add(key)
        e["key"] = key


def bib_value(name: str, value: str) -> str:
    """A field value in BibTeX braces; titles get double braces to keep their case."""
    if name == "doi":
        return "{" + re.sub(r"([_%&#])", r"\\\1", value) + "}"
    if name == "url":
        return "{" + value.replace("%", r"\%").replace("#", r"\#") + "}"
    if name in ("title", "type"):
        return "{{" + value + "}}"
    return "{" + value + "}"


def bib_entry(e: dict, tex_fields: dict) -> str:
    """One BibTeX entry."""
    lines = [f"@{e['kind']}{{{e['key']},", f"  author = {{{e['author']}}},", f"  year = {{{e['year']}}},"]
    lines += [f"  {k} = {bib_value(k, v)}," for k, v in tex_fields.items()]
    return "\n".join(lines) + "\n}\n"


def make_bib(refs_md: list) -> tuple:
    """BibTeX source for the reference list and the entries (with keys and citation names)."""
    entries = [parse_reference(r) for r in refs_md]
    assign_keys(entries)
    raw = {"doi", "url", "pages"}
    chunks = [(i, k, v) for i, e in enumerate(entries) for k, v in e["fields"].items() if k not in raw]
    tex = pandoc_many([v for _, _, v in chunks])
    tex_fields = [dict(e["fields"]) for e in entries]
    for (i, k, _), t in zip(chunks, tex):
        tex_fields[i][k] = t
    return "\n".join(bib_entry(e, f) for e, f in zip(entries, tex_fields)), entries


# ---------------------------------------------------------------- citations


def cite_index(entries: list) -> dict:
    """(citation name, year) -> key, with None where two references share both."""
    index = {}
    for e in entries:
        pair = (e["name"], e["year"])
        index[pair] = None if pair in index else e["key"]
    return index


def cite_keys(name: str, years: str, index: dict) -> list:
    """Keys for 'Name 2011, 2013', or None when any year matches no single reference."""
    keys = [index.get((name, y.strip())) for y in years.split(",")]
    return None if None in keys else keys


def cite_markdown(md: str, index: dict, store: list, unmatched: list) -> str:
    """Markdown with each matched citation replaced by a token; the LaTeX goes in store."""
    names = sorted({n for n, _ in index}, key=len, reverse=True)
    name_re = "|".join(re.escape(n) for n in names)
    item = re.compile(rf"(?P<name>{name_re}) (?P<years>{YEARS})")

    def token(latex: str) -> str:
        store.append(latex)
        return f"ZZCITE{len(store) - 1}ZZ"

    def narrative(m):
        keys = cite_keys(m.group("name"), m.group("years"), index)
        if keys is None:
            unmatched.append(m.group(0))
            return m.group(0)
        return token(rf"\citet{{{','.join(keys)}}}")

    def in_parens(m):
        parts = [p.strip() for p in m.group(1).split(";")]
        found = [item.fullmatch(p) for p in parts]
        if all(found):
            keys = [cite_keys(f.group("name"), f.group("years"), index) for f in found]
            if None not in keys:
                return token(rf"\citep{{{','.join(k for ks in keys for k in ks)}}}")

        def alp(c):
            keys = cite_keys(c.group("name"), c.group("years"), index)
            if keys is None:
                unmatched.append(c.group(0))
                return c.group(0)
            return token(rf"\citealp{{{','.join(keys)}}}")

        return "(" + item.sub(alp, m.group(1)) + ")"

    md = re.sub(rf"(?P<name>{name_re}) \((?P<years>{YEARS})\)", narrative, md)
    md = re.sub(r"\(([^()]*)\)", in_parens, md)
    surnames = {n.split()[0] for n in names}
    for m in LOOSE_CITE.finditer(re.sub(r"ZZCITE\d+ZZ", "", md)):
        text = m.group(0)
        seen = any(text.replace("(", "") in u.replace("(", "") for u in unmatched)
        if (" et al." in text or " and " in text or text.split()[0] in surnames) and not seen:
            unmatched.append(text)
    return md


def untoken(tex: str, store: list) -> str:
    """LaTeX with the citation tokens put back."""
    return re.sub(r"ZZCITE(\d+)ZZ", lambda m: store[int(m.group(1))], tex)


# ---------------------------------------------------------------- displays


def drawn_width_cm(png: str) -> tuple:
    """Drawn width of a PNG in cm (None without dpi) and its aspect ratio."""
    im = Image.open(png)
    w_px, h_px = im.size
    dpi = im.info.get("dpi")
    drawn = w_px / dpi[0] * 2.54 if dpi and dpi[0] > 1 else None
    return drawn, w_px / h_px


def figure_width(png: str, column_cm: float) -> tuple:
    """'single' or 'double' for a figure PNG in a two-column page, with the reason."""
    drawn, aspect = drawn_width_cm(png)
    if drawn:
        if drawn <= SINGLE_MAX_CM:
            return "single", f"drawn {drawn:.1f} cm wide, w/h {aspect:.2f}: reads at {column_cm} cm"
        return "double", f"drawn {drawn:.1f} cm wide, w/h {aspect:.2f}: labels at {column_cm / drawn:.0%} in one column"
    if aspect >= 1.3:
        return "double", f"no dpi, w/h {aspect:.2f}: wide multi-panel"
    return "single", f"no dpi, w/h {aspect:.2f}: compact"


def figure_tex(n: str, png: str, width: str, caption: str) -> str:
    """LaTeX float for one figure; width 'single', 'double' or a size in cm (one-column page)."""
    if width == "single":
        env, size = "figure", r"width=\columnwidth"
    elif width == "double":
        env, size = "figure*", r"width=\textwidth,height=0.8\textheight,keepaspectratio"
    else:
        env, size = "figure", rf"width={width},height=0.8\textheight,keepaspectratio"
    return (f"\\begin{{{env}}}[!tbp]\n\\setcounter{{figure}}{{{int(n) - 1}}}\n\\centering\n"
            f"\\includegraphics[{size}]{{{png}}}\n\\caption{{{caption}}}\\label{{fig{n}}}\n\\end{{{env}}}")


def pipe_rows(table_md: str) -> list:
    """Cells of a pipe table, header first, without the separator row."""
    rows = []
    for line in table_md.strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    assert rows and len({len(r) for r in rows}) == 1, "ragged pipe table"
    return rows


def table_tex(n: str, caption: str, rows_tex: list, rows_md: list) -> str:
    """LaTeX float for one table, full width with wrapping text columns."""
    n_col = len(rows_md[0])
    longest = [max(len(r[j]) for r in rows_md) for j in range(n_col)]
    spec = "".join(r">{\raggedright\arraybackslash}X" if L > 25 else "l" for L in longest)
    head = " & ".join(rf"\textbf{{{c}}}" if c else "" for c in rows_tex[0]) + r" \\"
    body = "\n".join(" & ".join(r) + r" \\" for r in rows_tex[1:])
    return (f"\\begin{{table*}}[!tbp]\n\\setcounter{{table}}{{{int(n) - 1}}}\n\\caption{{{caption}}}\\label{{tab{n}}}\n"
            f"\\footnotesize\n\\begin{{tabularx}}{{\\textwidth}}{{@{{}}{spec}@{{}}}}\n\\toprule\n{head}\n\\midrule\n"
            f"{body}\n\\bottomrule\n\\end{{tabularx}}\n\\end{{table*}}")


def take_displays(body: str, md_dir: str) -> tuple:
    """Body with a token at each figure and table, and the Markdown parts of each display."""
    displays = []

    def fig(m):
        png = os.path.normpath(os.path.join(md_dir, m.group(1)))
        assert os.path.isfile(png), f"missing figure file {png}"
        displays.append(dict(kind="Figure", n=m.group(2), png=png, caption=m.group(3).strip()))
        return f"\n\nZZDISPLAY{len(displays) - 1}ZZ\n\n"

    def tab(m):
        displays.append(dict(kind="Table", n=m.group(1), caption=m.group(2).strip(), rows=pipe_rows(m.group(3))))
        return f"\n\nZZDISPLAY{len(displays) - 1}ZZ\n\n"

    body = FIGURE.sub(fig, body)
    body = TABLE.sub(tab, body)
    return body, displays


def display_tex(d: dict, caption: str, rows_tex: list, columns: int) -> tuple:
    """LaTeX for one display and the line that reports its width choice."""
    if d["kind"] == "Table":
        why = f"{len(d['rows'][0])} columns, {len(d['rows'])} rows"
        return table_tex(d["n"], caption, rows_tex, d["rows"]), (f"Table {d['n']}", "", "full", why)
    name = os.path.basename(d["png"])
    if columns == 2:
        width, why = figure_width(d["png"], column_cm=8.7)
        return figure_tex(d["n"], d["png"], width, caption), (f"Figure {d['n']}", name, width, why)
    drawn, _ = drawn_width_cm(d["png"])
    size = f"{min(drawn, TEXT_WIDTH_CM):.2f}cm" if drawn else r"\textwidth"
    return figure_tex(d["n"], d["png"], size, caption), (f"Figure {d['n']}", name, size, "drawn width")


def tidy_body(tex: str) -> str:
    """No pandoc wrappers, code wrapped to the column. Headings keep the drafts' own numbers."""
    tex = re.sub(r"\\pandocbounded\{(.*?)\}$", r"\1", tex, flags=re.M)
    tex = tex.replace(r"\begin{verbatim}", r"\begin{Verbatim}[breaklines,fontsize=\footnotesize]")
    return tex.replace(r"\end{verbatim}", r"\end{Verbatim}")


def convert(md_path: str, columns: int) -> dict:
    """LaTeX pieces of the main text: front matter, body with floats, .bib source, figure choices."""
    title, impact, abstract, keywords, body = split_front(main_text(open(md_path).read()))
    body, refs = split_refs(body)
    bib, entries = make_bib(refs)
    body, displays = take_displays(body, os.path.dirname(md_path))
    index, store, unmatched = cite_index(entries), [], []
    cited = [cite_markdown(t, index, store, unmatched) for t in (impact, abstract, body)]
    captions = [cite_markdown(d["caption"], index, store, unmatched) for d in displays]
    cells = [cite_markdown(c, index, store, unmatched) for d in displays if d["kind"] == "Table"
             for r in d["rows"] for c in r]
    out = [untoken(t, store) for t in pandoc_many([title, *cited, keywords] + captions + cells)]
    t_title, t_impact, t_abs, t_body, t_kw = out[:5]
    t_caps = out[5:5 + len(displays)]
    t_cells = iter(out[5 + len(displays):])
    choices = []
    for i, d in enumerate(displays):
        rows_tex = [[next(t_cells) for _ in r] for r in d["rows"]] if d["kind"] == "Table" else []
        tex, choice = display_tex(d, t_caps[i], rows_tex, columns)
        choices.append(choice)
        assert f"ZZDISPLAY{i}ZZ" in t_body, f"display token {i} lost in pandoc output"
        t_body = t_body.replace(f"ZZDISPLAY{i}ZZ", tex)
    cited_keys = {k for s in store for k in re.search(r"\{(.+)\}", s).group(1).split(",")}
    uncited = [e["key"] for e in entries if e["key"] not in cited_keys]
    return dict(title=t_title, impact=t_impact, abstract=t_abs, keywords=", ".join(k.strip() for k in t_kw.split(";")),
                body=tidy_body(t_body), bib=bib, choices=choices, n_cites=len(store), unmatched=unmatched,
                uncited=uncited, kinds=[e["kind"] for e in entries])


# ---------------------------------------------------------------- document


def unicode_preamble() -> str:
    """newunicodechar mappings for the symbols pdflatex's T1 fonts lack."""
    return "\n".join(rf"\newunicodechar{{{ch}}}{{{tex}}}" for ch, tex in UNICODE_MAP.items())


def layout_preamble(layout: dict) -> str:
    """Line numbers for the submission; plain links for the print layout."""
    if layout["lineno"]:
        return "\\usepackage{lineno}\n\\linenumbers"
    return r"\hypersetup{hidelinks}"


def document(parts: dict, layout: dict) -> str:
    """Full LaTeX source on the NJD class and its front-matter fields."""
    return rf"""% WileyNJDv5 calls \reserveinserts, which etex.sty no longer defines on current LaTeX.
\providecommand{{\reserveinserts}}[1]{{}}
\documentclass[{layout['options']}]{{WileyNJDv5}}
{layout_preamble(layout)}
\usepackage{{newunicodechar}}
\usepackage{{booktabs}}
\usepackage{{xurl}}
\usepackage{{fvextra}}
{unicode_preamble()}
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\setcounter{{topnumber}}{{3}}\setcounter{{dbltopnumber}}{{3}}\setcounter{{totalnumber}}{{4}}
\renewcommand{{\topfraction}}{{0.9}}\renewcommand{{\dbltopfraction}}{{0.9}}\renewcommand{{\bottomfraction}}{{0.6}}
\renewcommand{{\textfraction}}{{0.1}}\renewcommand{{\floatpagefraction}}{{0.75}}\renewcommand{{\dblfloatpagefraction}}{{0.75}}
\articletype{{Research Paper}}
\received{{Date Month Year}}
\revised{{Date Month Year}}
\accepted{{Date Month Year}}
\journal{{Journal}}
\volume{{00}}
\copyyear{{00}}
\startpage{{1}}
\raggedbottom
\setcounter{{secnumdepth}}{{0}}
\makeatletter
\AtEndDocument{{\immediate\write16{{GEOMETRY odd=\the\dimexpr1in+\hoffset+\oddsidemargin\relax\space
  even=\the\dimexpr1in+\hoffset+\evensidemargin\relax\space top=\the\dimexpr1in+\voffset+\topmargin+\headheight+\headsep\relax\space
  width=\the\textwidth\space height=\the\textheight\space colsep=\the\columnsep}}}}
\makeatother
\begin{{document}}
\title{{{parts['title']}}}
\author[1]{{Author One}}
\author[2]{{Author Two}}
\authormark{{ONE \textsc{{et al.}}}}
\titlemark{{Flow tracing for MODFLOW 6}}
\address[1]{{\orgdiv{{Department}}, \orgaddress{{\city{{City}}, \country{{Country}}}}}}
\address[2]{{\orgdiv{{Department}}, \orgaddress{{\city{{City}}, \country{{Country}}}}}}
\corres{{Corresponding author Author One. \email{{author.one@example.org}}}}
\abstract[Abstract]{{{parts['abstract']}}}
\keywords{{{parts['keywords']}}}
\maketitle

\section{{Article Impact Statement}}
{parts['impact']}

{parts['body']}

\nocite{{*}}% list every reference of the draft, as its reference list does
\bibliography{{refs}}
\end{{document}}
"""


def check_glyphs(tex: str) -> list:
    """Non-ASCII characters in the source that neither T1 nor the mappings cover."""
    return sorted({ch for ch in tex if ord(ch) > 127 and ch not in UNICODE_MAP and ch not in T1_OK})


def run_tex(cmd: list, out_dir: str, env: dict) -> subprocess.CompletedProcess:
    """One TeX-tool run in the output folder."""
    return subprocess.run(cmd, cwd=out_dir, env=env, capture_output=True, text=True, errors="replace")


def compile_pdf(tex_path: str, template_dir: str) -> tuple:
    """pdflatex, bibtex, pdflatex twice, without shell escape; return the LaTeX and BibTeX logs."""
    env = dict(os.environ, TEXINPUTS=template_dir + "//:", PATH=TEXBIN + ":" + os.environ["PATH"])
    out_dir, stem = os.path.dirname(tex_path), os.path.basename(tex_path)[:-4]
    latex = [os.path.join(TEXBIN, "pdflatex"), "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", stem]
    bib_log = ""
    for step in ("latex", "bibtex", "latex", "latex"):
        if step == "bibtex":
            run = run_tex([os.path.join(TEXBIN, "bibtex"), stem], out_dir, env)
            bib_log = run.stdout
            assert run.returncode < 2, "bibtex failed:\n" + run.stdout[-2000:]
            continue
        run = run_tex(latex, out_dir, env)
        log = open(tex_path[:-4] + ".log", errors="replace").read()
        assert run.returncode == 0, "pdflatex failed:\n" + "\n".join(re.findall(r"^!.*$", log, re.M)[:10])
    return log, bib_log


def page_count(pdf: str) -> int:
    """Pages of a PDF, from pdfinfo."""
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))


def geometry(log: str) -> dict:
    """Text block in pt, as the document wrote it to the log."""
    m = re.search(r"GEOMETRY odd=([\d.]+)pt\s+even=([\d.]+)pt\s+top=([\d.]+)pt\s+width=([\d.]+)pt\s+"
                  r"height=([\d.]+)pt\s+colsep=([\d.]+)pt", log)
    assert m, "no GEOMETRY line in the log"
    keys = ("odd", "even", "top", "width", "height", "colsep")
    return dict(zip(keys, (float(v) for v in m.groups())))


def is_ink_row(px, y: int, width: int) -> bool:
    """A pixel row holds text or figure ink, and is not a full-width rule."""
    dark = sum(1 for x in range(width) if px[x, y] < 160)
    return 0 < dark < 0.9 * width


def column_fill(pdf: str, page: int, geo: dict, columns: int, work_dir: str) -> tuple:
    """Share of each column's height that holds ink on a page (text and figures)."""
    stem = os.path.join(work_dir, "lastpage")
    subprocess.run(["pdftoppm", "-r", "72", "-gray", "-png", "-singlefile", "-f", str(page), "-l", str(page),
                    pdf, stem], check=True)
    im = Image.open(stem + ".png").convert("L")
    left = geo["odd"] if page % 2 else geo["even"]
    col_w = (geo["width"] - (columns - 1) * geo["colsep"]) / columns
    fills = []
    for c in range(columns):
        x0 = left + c * (col_w + geo["colsep"])
        box = im.crop((round(x0), round(geo["top"]), round(x0 + col_w), round(geo["top"] + geo["height"])))
        px = box.load()
        rows = [y for y in range(box.height) if is_ink_row(px, y, box.width)]
        fills.append((rows[-1] + 1) / box.height if rows else 0.0)
    os.remove(stem + ".png")
    return tuple(fills)


def overfull_boxes(log: str, tex: str) -> list:
    """Overfull hbox warnings in the text wider than 2 pt, with their source lines.

    The class's own title block (at \\maketitle) and running heads always overflow; they are left out.
    """
    title_line = tex.splitlines().index(r"\maketitle") + 1
    found = re.findall(r"^Overfull \\hbox \((\d+\.\d+)pt too wide\) in (?:paragraph|alignment) at lines (\d+)--(\d+)",
                       log, re.M)
    return [f"{float(w):.1f} pt (lines {a}-{b})" for w, a, b in found
            if float(w) > 2 and not int(a) <= title_line <= int(b)]


def float_warnings(log: str) -> list:
    """Float placement warnings from the log."""
    return re.findall(r"^LaTeX Warning: (Float too large.*|.*float specifier changed.*)$", log, re.M)


def write_inputs(out_dir: str, tex: str, bib: str, template_dir: str) -> str:
    """main.tex, refs.bib and the class's bibliography style in a fresh output folder."""
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    shutil.copy(os.path.join(template_dir, "wileyNJD-Harvard.bst"), os.path.join(out_dir, BST_NAME + ".bst"))
    with open(os.path.join(out_dir, "refs.bib"), "w") as f:
        f.write(bib)
    tex_path = os.path.join(out_dir, "main.tex")
    with open(tex_path, "w") as f:
        f.write(tex)
    return tex_path


def typeset(draft_arg: str, layout_name: str = "print", template_dir: str = TEMPLATE_DIR) -> dict:
    """Typeset one draft's main text in one layout and return the page measures."""
    assert layout_name in LAYOUTS, f"layout must be one of {list(LAYOUTS)}"
    assert os.path.isfile(os.path.join(template_dir, "WileyNJDv5.cls")), f"no WileyNJDv5.cls in {template_dir}"
    layout = LAYOUTS[layout_name]
    md_path, name = resolve_draft(draft_arg)
    parts = convert(md_path, layout["columns"])
    tex = document(parts, layout)
    tex_path = write_inputs(os.path.join(OUT_ROOT, f"{name}_{layout_name}"), tex, parts["bib"], template_dir)
    log, bib_log = compile_pdf(tex_path, template_dir)
    pdf = tex_path[:-4] + ".pdf"
    n = page_count(pdf)
    fills = column_fill(pdf, n, geometry(log), layout["columns"], os.path.dirname(tex_path))
    return dict(md=md_path, pdf=pdf, layout=layout_name, options=layout["options"], pages=n, fills=fills,
                choices=parts["choices"], missing=check_glyphs(tex + parts["bib"]), overfull=overfull_boxes(log, tex),
                floats=float_warnings(log), n_cites=parts["n_cites"], unmatched=parts["unmatched"],
                uncited=parts["uncited"], kinds=parts["kinds"],
                bib_warnings=re.findall(r"^Warning--.*$", bib_log, re.M))


def report(res: dict) -> None:
    """Print the figure choices, citations and page measures of one run."""
    print(f"\n{res['md']}  [{res['layout']}: {res['options']}]")
    for item, png, width, why in res["choices"]:
        print(f"  {item:<10} {png:<32} {width:<8}  {why}")
    kinds = {k: res["kinds"].count(k) for k in sorted(set(res["kinds"]))}
    print(f"  references: {len(res['kinds'])} ({', '.join(f'{v} {k}' for k, v in kinds.items())});"
          f" citation commands: {res['n_cites']}")
    if res["unmatched"]:
        print(f"  UNMATCHED citations (left as text): {'; '.join(res['unmatched'])}")
    if res["uncited"]:
        print(f"  listed but not cited in the main text (kept with \\nocite): {', '.join(res['uncited'])}")
    if res["bib_warnings"]:
        print("  bibtex: " + "; ".join(res["bib_warnings"]))
    fills = res["fills"]
    last = sum(fills) / len(fills)
    cols = ", ".join(f"{f:.0%}" for f in fills)
    print(f"  pages: {res['pages']}  (last page {last:.0%} full, columns {cols};"
          f" about {res['pages'] - 1 + last:.2f} page-equivalents)")
    if res["missing"]:
        print(f"  WARNING unmapped characters: {' '.join(res['missing'])}")
    if res["overfull"]:
        print(f"  overfull boxes > 2 pt: {', '.join(res['overfull'])}")
    if res["floats"]:
        print(f"  float warnings: {len(res['floats'])}")
    print(f"  PDF: {res['pdf']}")


if __name__ == "__main__":
    assert len(sys.argv) >= 2, __doc__
    args = sys.argv[1:] + [None] * 2
    which = args[1] or "both"
    names = list(LAYOUTS) if which == "both" else [which]
    for layout_name in names:
        report(typeset(args[0], layout_name, args[2] or TEMPLATE_DIR))
