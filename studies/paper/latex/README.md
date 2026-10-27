# Typeset page count

`typeset_groundwater.py` sets the main text of an exported draft (`docs/paper/export*/paper_draft.md`)
in Wiley's NJD LaTeX template and reports the pages. The Supporting Information is cut off.

```
~/miniforge3/envs/gw-source/bin/python studies/paper/latex/typeset_groundwater.py reduced
~/miniforge3/envs/gw-source/bin/python studies/paper/latex/typeset_groundwater.py full print
```

Arguments: draft (`reduced`, `full`, an export folder name or a `.md` path), layout
(`submission`, `print` or `both`, the default), and the template folder.

**Template.** Groundwater has no LaTeX template of its own. The script uses the setup the author
used for an earlier Groundwater submission: Wiley's NJD class `WileyNJDv5.cls` (v5.0, 2022/04/05)
with `NJDnatbib.sty` and the Harvard style `wileyNJD-Harvard.bst`. The template is not in git. By
default it is read from `../gw_template_njd` beside the repository; that folder's `README.txt`
gives the source.

**Layouts.** Both use `\articletype{Research Paper}`, unnumbered sections
(`\setcounter{secnumdepth}{0}`), the Article Impact Statement as the first section, and
placeholder authors. The headings keep the draft's own numbers, which the text refers to.
- `submission`: `[HARVARD,Times1COL,doublespace]` with `lineno` line numbers, as submitted.
- `print`: `[HARVARD,Times2COL]`, single-spaced, no line numbers, links without boxes. It
  approximates the published pages (210 × 276 mm, text block 17.9 × 23.6 cm, 8.7 cm columns,
  Times) and gives the page count.

**References.** The script turns the draft's reference list into `refs.bib` (journal articles,
books, proceedings papers, theses, USGS reports, and data or software releases as `misc`) and sets
it with `\bibliography` and the Harvard style, as the author's manuscript does. All listed
references are printed (`\nocite{*}`). The style prints a DOI only for articles; for other types
the DOI link goes in the URL line. In-text citations become natbib commands where the name and
year match exactly one reference: `Name (2013)` becomes `\citet`, a parenthesis of citations only
becomes `\citep`, and a citation inside a parenthesis with other text becomes `\citealp`. The
script lists any citation it could not match; those stay as plain text.

**Figures.** In `print`, a figure drawn at column width (≤ 11 cm, from the PNG's dpi) goes in one
column; wider drawings span both columns, because in one column their labels would shrink to
under half size. In `submission`, figures keep their drawn width. The script prints each choice.

**Class fix.** `WileyNJDv5.cls` calls `\reserveinserts`, which current LaTeX no longer defines;
the document defines it as a no-op before `\documentclass`. The class asks for the style as
`WileyNJD-Harvard`; the script copies the `.bst` under that name into the output folder.

**Requirements.** pandoc, pdflatex and bibtex (TeX Live 2025, with `newunicodechar`, `xurl`,
`fvextra`, `booktabs`, `lineno`), poppler (`pdfinfo`, `pdftoppm`) and Pillow. LaTeX runs with
`-no-shell-escape`. The Times layouts need no fonts from the template's `Fonts/` folder.

Output goes to `studies/paper/output/latex/<draft>_<layout>/` (git-ignored): `main.tex`,
`refs.bib`, `main.pdf`. The page count is the PDF's page count. The last-page fill is the inked
height of each column.
