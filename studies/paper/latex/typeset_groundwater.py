"""Typeset the main text of an exported paper draft in Wiley's LaTeX template and count pages.

Groundwater (NGWA, Wiley) has no journal-specific LaTeX template, and its printed design is its
own (Times body, sans-serif headings). The closest official template is Wiley's authoring
template for its standard PDF design, USG.cls in WileyDesign.zip (Wiley Author Services): same
trim size, two columns, Harvard (author-date) references. The script uses that class with its
twocolumn and HARVARD options, in one of two layouts:

- "groundwater" (default): the template with its page geometry and type sizes set to those
  measured on printed Groundwater pages (Hugman et al. 2023, Groundwater 61(3); Bedekar et al.
  2024, Groundwater 62(2)): page 210 x 276 mm, text block 17.1 x 24.9 cm, columns 8.2 cm with a
  0.63 cm gutter, Times 10/12 pt body, 9/11 pt captions, 9/10 pt references.
- "wiley": the template exactly as shipped: text block 17.8 x 23.4 cm, columns 8.6 cm, STIX Two
  9/11.5 pt body (about 15 % more text per page than Groundwater).

Steps: cut the export at the Supporting Information heading; take the title, impact statement,
abstract and key words into the front matter; convert the body to LaTeX with pandoc; place each
figure and table at its marker; set the references as a thebibliography list; compile twice
with pdflatex -no-shell-escape; report the pages and how full the last page is.

A figure goes in one column when it was drawn at column width (8.25 cm, read from the PNG's
dpi), because a full-width drawing shrunk to a column would set its labels at under half size.
Otherwise it spans both columns. Figures without dpi fall back on the aspect ratio.

python typeset_groundwater.py reduced [groundwater|wiley] [template_dir]
python typeset_groundwater.py full
python typeset_groundwater.py docs/paper/export_reduced/paper_draft.md

Output (git-ignored): studies/paper/output/latex/<draft>_<layout>/main.tex and main.pdf.
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
TEMPLATE_DIR = os.path.normpath(os.path.join(REPO, "..", "gw_template", "WileyDesign", "Optimal-Design-layout"))
OUT_ROOT = os.path.join(REPO, "studies", "paper", "output", "latex")
PANDOC = "/opt/homebrew/bin/pandoc"
TEXBIN = "/Library/TeX/texbin"
DRAFTS = {"reduced": "export_reduced", "full": "export"}

SI_HEADING = re.compile(r"^# Supporting Information.*$", re.M)
FIGURE = re.compile(r"!\[[^\]]*\]\((\S+?)\)\s*\n\s*\n\*\*Figure (\d+)\.\*\*[ \t]*(.+?)(?=\n\s*\n|\Z)", re.S)
TABLE = re.compile(r"\*\*Table (\d+)\.\*\*[ \t]*(.+?)\n\s*\n((?:\|.*(?:\n|\Z))+)")
SPLIT = "ZZSPLITZZ"
SINGLE_MAX_CM = 11.0  # drawn at most this wide: still legible at 8.25 cm (labels >= 75 %)

# Page geometry in pt (x from the left edge, y from the top), used for \geometry and to
# measure how full the last page is.
LAYOUTS = {
    "groundwater": dict(left=55.0, top=35.0, width=484.5, height=706.0, colsep=18.0),
    "wiley": dict(left=45.354, top=34.016, width=504.567, height=663.307, colsep=17.008),
}

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
    cmd = [PANDOC, "-f", "markdown+tex_math_dollars+autolink_bare_uris-auto_identifiers-implicit_figures-subscript-superscript",
           "-t", "latex", "--wrap=none", "--syntax-highlighting=none"]
    out = subprocess.run(cmd, input=src, capture_output=True, text=True, check=True).stdout
    parts = [p.strip() for p in re.split(rf"\n*{SPLIT}\n*", out)]
    assert len(parts) == len(chunks), f"pandoc split mismatch: {len(parts)} parts for {len(chunks)} chunks"
    return parts


def figure_width(png: str, column_cm: float = 8.25) -> tuple:
    """'single' or 'double' for a figure PNG, with the reason."""
    im = Image.open(png)
    w_px, h_px = im.size
    aspect = w_px / h_px
    dpi = im.info.get("dpi")
    if dpi and dpi[0] > 1:
        drawn_cm = w_px / dpi[0] * 2.54
        if drawn_cm <= SINGLE_MAX_CM:
            return "single", f"drawn {drawn_cm:.1f} cm wide, w/h {aspect:.2f}: reads at {column_cm} cm"
        shrink = column_cm / drawn_cm
        return "double", f"drawn {drawn_cm:.1f} cm wide, w/h {aspect:.2f}: labels at {shrink:.0%} in one column"
    if aspect >= 1.3:
        return "double", f"no dpi, w/h {aspect:.2f}: wide multi-panel"
    return "single", f"no dpi, w/h {aspect:.2f}: compact"


def figure_tex(n: str, png: str, width: str, caption: str) -> str:
    """LaTeX float for one figure."""
    env = "figure" if width == "single" else "figure*"
    size = r"width=\columnwidth" if width == "single" else r"width=\textwidth,height=0.8\textheight,keepaspectratio"
    return (f"\\begin{{{env}}}[tbp]\n\\setcounter{{figure}}{{{int(n) - 1}}}\n\\centering\n"
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
    return (f"\\begin{{table*}}[tbp]\n\\setcounter{{table}}{{{int(n) - 1}}}\n\\caption{{{caption}}}\\label{{tab{n}}}\n"
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


def tidy_body(tex: str) -> str:
    """Unnumbered headings (the drafts carry their numbers), no pandoc wrappers, code wrapped to the column."""
    tex = re.sub(r"\\(section|subsection|subsubsection)\{", r"\\\1*{", tex)
    tex = re.sub(r"\\pandocbounded\{(.*?)\}$", r"\1", tex, flags=re.M)
    tex = tex.replace(r"\begin{verbatim}", r"\begin{Verbatim}[breaklines,fontsize=\footnotesize]")
    return tex.replace(r"\end{verbatim}", r"\end{Verbatim}")


def convert(md_path: str) -> dict:
    """LaTeX pieces of the main text: front matter, body with floats, references, figure choices."""
    title, impact, abstract, keywords, body = split_front(main_text(open(md_path).read()))
    body, refs = split_refs(body)
    body, displays = take_displays(body, os.path.dirname(md_path))
    cells = [c for d in displays if d["kind"] == "Table" for r in d["rows"] for c in r]
    chunks = [title, impact, abstract, keywords, body] + refs + [d["caption"] for d in displays] + cells
    out = pandoc_many(chunks)
    t_title, t_impact, t_abs, t_kw, t_body = out[:5]
    t_refs = out[5:5 + len(refs)]
    t_caps = out[5 + len(refs):5 + len(refs) + len(displays)]
    t_cells = iter(out[5 + len(refs) + len(displays):])
    choices = []
    for i, d in enumerate(displays):
        if d["kind"] == "Figure":
            width, why = figure_width(d["png"])
            choices.append((f"Figure {d['n']}", os.path.basename(d["png"]), width, why))
            tex = figure_tex(d["n"], d["png"], width, t_caps[i])
        else:
            rows_tex = [[next(t_cells) for _ in r] for r in d["rows"]]
            choices.append((f"Table {d['n']}", "", "double", f"{len(d['rows'][0])} columns, {len(d['rows'])} rows"))
            tex = table_tex(d["n"], t_caps[i], rows_tex, d["rows"])
        assert f"ZZDISPLAY{i}ZZ" in t_body, f"display token {i} lost in pandoc output"
        t_body = t_body.replace(f"ZZDISPLAY{i}ZZ", tex)
    kw = " | ".join(k.strip() for k in t_kw.split(";"))
    return dict(title=t_title, impact=t_impact, abstract=t_abs, keywords=kw, body=tidy_body(t_body),
                refs=t_refs, choices=choices)


def unicode_preamble() -> str:
    """newunicodechar mappings for the symbols pdflatex's T1 fonts lack."""
    return "\n".join(rf"\newunicodechar{{{ch}}}{{{tex}}}" for ch, tex in UNICODE_MAP.items())


def layout_preamble(layout: str, geo: dict) -> str:
    """Settings that turn the template's page into a measured Groundwater page."""
    if layout == "wiley":
        return ""
    return rf"""\geometry{{paperwidth=210mm,paperheight=782.362pt,left={geo['left']}pt,right={595.276 - geo['left'] - geo['width']:.3f}pt,
  top={geo['top']}pt,textheight={geo['height']}pt,columnsep={geo['colsep']}pt,headheight=0pt,headsep=0pt,footskip=30pt}}
\usepackage{{newtxtext}}
\makeatletter
\renewcommand\normalsize{{\@setfontsize\normalsize{{10\p@}}{{12\p@}}%
  \abovedisplayskip 8\p@ \@plus2\p@ \belowdisplayskip 8\p@ \@plus2\p@
  \abovedisplayshortskip \z@ \@plus3\p@ \belowdisplayshortskip 4\p@ \@plus2\p@ \let\@listi\@listI}}
\renewcommand{{\textbaselineskip}}{{\baselineskip12\p@}}
\normalsize
\def\fnum@figure{{Figure~\thefigure.}}
\def\fnum@table{{Table~\thetable.}}
\long\def\@makecaption#1#2{{\vskip4\p@{{\fontsize{{9}}{{11}}\selectfont\textbf{{#1}}\enskip #2\par}}\vskip4\p@}}
\renewcommand{{\bibfont}}{{\fontsize{{9}}{{10}}\selectfont}}
\makeatother"""


def bib_label(ref_tex: str) -> str:
    """natbib author-year label, {First author}(Year), that the author-year style requires."""
    year = re.search(r"\b((?:19|20)\d\d[a-z]?)\.", ref_tex)
    assert year, f"no year in reference: {ref_tex[:60]}"
    first = ref_tex.split(",")[0].split(".")[0].strip()
    return f"{{{first}}}({year.group(1)})"


def after_title(layout: str) -> str:
    """Groundwater indents paragraphs by 1 em; the template's title block resets the indent to 0."""
    return r"\setlength{\parindent}{1em}" if layout == "groundwater" else ""


def document(parts: dict, layout: str, geo: dict) -> str:
    """Full LaTeX source on the template's class and front-matter fields."""
    refs = "\n\n".join(rf"\bibitem[{bib_label(r)}]{{ref{i + 1}}} {r}" for i, r in enumerate(parts["refs"]))
    return rf"""\documentclass[HARVARD,twocolumn]{{USG}}
\usepackage{{newunicodechar}}
\usepackage{{xurl}}
\usepackage{{fvextra}}
{layout_preamble(layout, geo)}
{unicode_preamble()}
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\setcounter{{topnumber}}{{3}}\setcounter{{dbltopnumber}}{{3}}\setcounter{{totalnumber}}{{4}}
\renewcommand{{\topfraction}}{{0.9}}\renewcommand{{\dbltopfraction}}{{0.9}}\renewcommand{{\bottomfraction}}{{0.6}}
\renewcommand{{\textfraction}}{{0.1}}\renewcommand{{\floatpagefraction}}{{0.75}}\renewcommand{{\dblfloatpagefraction}}{{0.75}}
\articletype{{RESEARCH PAPER}}
\received{{00}}\revised{{00}}\accepted{{00}}
\journal{{Groundwater}}\volume{{0}}\copyyear{{2026}}\startpage{{1}}\articledoi{{10.1111/gwat.00000}}
\begin{{document}}
\title{{{parts['title']}}}
\author[1]{{Author One}}
\author[2]{{Author Two}}
\authormark{{AUTHOR \textsc{{et al.}}}}
\titlemark{{FLOW TRACING FOR MODFLOW 6}}
\address[1]{{\orgdiv{{Department, }}\orgname{{Institution, }}\orgaddress{{\state{{City, }}\country{{Country}}}}}}
\address[2]{{\orgdiv{{Department, }}\orgname{{Institution, }}\orgaddress{{\state{{City, }}\country{{Country}}}}}}
\corres{{Author One (\email{{author@example.org}})}}
\keywords{{{parts['keywords']}}}
\abstract[ABSTRACT]{{{parts['abstract']}}}
\maketitle
{after_title(layout)}
{{\renewcommand\thefootnote{{}}\footnotetext{{\textit{{Article impact statement}}: {parts['impact']}}}}}

{parts['body']}

\begin{{thebibliography}}{{99}}
{refs}
\end{{thebibliography}}
\end{{document}}
"""


def check_glyphs(tex: str) -> list:
    """Non-ASCII characters in the source that neither T1 nor the mappings cover."""
    return sorted({ch for ch in tex if ord(ch) > 127 and ch not in UNICODE_MAP and ch not in T1_OK})


def compile_pdf(tex_path: str, template_dir: str) -> str:
    """Run pdflatex twice without shell escape; return the log text."""
    env = dict(os.environ, TEXINPUTS=template_dir + "//:", PATH=TEXBIN + ":" + os.environ["PATH"])
    out_dir = os.path.dirname(tex_path)
    cmd = [os.path.join(TEXBIN, "pdflatex"), "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
           os.path.basename(tex_path)]
    for _ in range(2):
        run = subprocess.run(cmd, cwd=out_dir, env=env, capture_output=True, text=True, errors="replace")
        log = open(tex_path[:-4] + ".log", errors="replace").read()
        assert run.returncode == 0, "pdflatex failed:\n" + "\n".join(re.findall(r"^!.*$", log, re.M)[:10])
    return log


def page_count(pdf: str) -> int:
    """Pages of a PDF, from pdfinfo."""
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))


def is_ink_row(px, y: int, width: int) -> bool:
    """A pixel row holds text or figure ink, and is not a full-width rule (the footer line)."""
    dark = sum(1 for x in range(width) if px[x, y] < 160)
    return 0 < dark < 0.9 * width


def column_fill(pdf: str, page: int, geo: dict, work_dir: str) -> tuple:
    """Share of each column's height that holds ink on a page (text and figures)."""
    stem = os.path.join(work_dir, "lastpage")
    subprocess.run(["pdftoppm", "-r", "72", "-gray", "-png", "-singlefile", "-f", str(page), "-l", str(page),
                    pdf, stem], check=True)
    im = Image.open(stem + ".png").convert("L")
    col_w = (geo["width"] - geo["colsep"]) / 2
    fills = []
    for x0 in (geo["left"], geo["left"] + col_w + geo["colsep"]):
        box = im.crop((round(x0), round(geo["top"]), round(x0 + col_w), round(geo["top"] + geo["height"])))
        px = box.load()
        rows = [y for y in range(box.height) if is_ink_row(px, y, box.width)]
        fills.append((rows[-1] + 1) / box.height if rows else 0.0)
    os.remove(stem + ".png")
    return tuple(fills)


def overfull_boxes(log: str) -> list:
    """Overfull box warnings in the text wider than 2 pt (the template's footer always overflows)."""
    found = re.findall(r"^Overfull \\hbox \((\d+\.\d+)pt too wide\) in (paragraph|alignment)", log, re.M)
    return [m for m, _ in found if float(m) > 2]


def float_warnings(log: str) -> list:
    """Float placement warnings from the log."""
    return re.findall(r"^LaTeX Warning: (Float too large.*|.*float specifier changed.*)$", log, re.M)


def typeset(draft_arg: str, layout: str = "groundwater", template_dir: str = TEMPLATE_DIR) -> dict:
    """Typeset one draft's main text and return the page measures."""
    assert layout in LAYOUTS, f"layout must be one of {list(LAYOUTS)}"
    assert os.path.isfile(os.path.join(template_dir, "USG.cls")), f"no USG.cls in {template_dir}"
    md_path, name = resolve_draft(draft_arg)
    geo = LAYOUTS[layout]
    out_dir = os.path.join(OUT_ROOT, f"{name}_{layout}")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    parts = convert(md_path)
    tex = document(parts, layout, geo)
    missing = check_glyphs(tex)
    tex_path = os.path.join(out_dir, "main.tex")
    with open(tex_path, "w") as f:
        f.write(tex)
    log = compile_pdf(tex_path, template_dir)
    pdf = tex_path[:-4] + ".pdf"
    n = page_count(pdf)
    fills = column_fill(pdf, n, geo, out_dir)
    return dict(md=md_path, pdf=pdf, layout=layout, pages=n, fills=fills, choices=parts["choices"],
                missing=missing, overfull=overfull_boxes(log), floats=float_warnings(log))


def report(res: dict) -> None:
    """Print the figure choices and page measures of one run."""
    print(f"\n{res['md']}  [{res['layout']} layout]")
    for item, png, width, why in res["choices"]:
        print(f"  {item:<10} {png:<32} {width:<6}  {why}")
    left, right = res["fills"]
    last = (left + right) / 2
    print(f"  pages: {res['pages']}  (last page {last:.0%} full: left column {left:.0%}, right {right:.0%};"
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
    report(typeset(args[0], args[1] or "groundwater", args[2] or TEMPLATE_DIR))
