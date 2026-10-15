# Typeset page count

`typeset_groundwater.py` sets the main text of an exported draft (`docs/paper/export*/paper_draft.md`)
in Wiley's LaTeX authoring template and reports the pages. The Supporting Information is cut off.

```
~/miniforge3/envs/gw-source/bin/python studies/paper/latex/typeset_groundwater.py reduced
~/miniforge3/envs/gw-source/bin/python studies/paper/latex/typeset_groundwater.py full wiley
```

Arguments: draft (`reduced`, `full`, an export folder name or a `.md` path), layout
(`groundwater`, the default, or `wiley`), and the template folder.

**Template.** Groundwater has no LaTeX template of its own. The script uses Wiley's "PDF design"
template (`USG.cls`, from https://authors.wiley.com/asset/WileyDesign.zip), with its two-column and
Harvard options. The template is not in git. By default it is read from
`../gw_template/WileyDesign/Optimal-Design-layout` beside the repository; that folder's
`README.txt` gives the source and version.

**Layouts.**
- `groundwater`: the template with the page measured on printed Groundwater articles: text block
  17.1 × 24.9 cm, columns 8.2 cm, Times 10/12 pt body, 9 pt captions and references. A full text
  page holds about 1,040 words, as on the printed pages.
- `wiley`: the template as shipped: text block 17.8 × 23.4 cm, STIX Two 9 pt. It holds about 15 %
  more text per page than Groundwater.

**Figures.** A figure drawn at column width (≤ 11 cm, from the PNG's dpi) goes in one column.
Wider drawings span both columns, because in one column their labels would shrink to under half
size. The script prints each choice.

**Requirements.** pandoc, pdflatex (TeX Live 2025, with `newtx`, `newunicodechar`, `xurl` and
`fvextra`), poppler (`pdfinfo`, `pdftoppm`) and Pillow. LaTeX runs with `-no-shell-escape`.

Output goes to `studies/paper/output/latex/<draft>_<layout>/` (git-ignored): `main.tex`, `main.pdf`.
The page count is the PDF's page count. The last-page fill is the inked height of each column.
