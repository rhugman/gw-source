"""Write the Supporting Information of an exported draft as its own Markdown file and PDF.

The export (export_md.py) holds the main text and then the SI under "# Supporting Information".
This keeps the SI part, titles it for the paper, lifts its headings one level and runs pandoc.

python si_pdf.py <export dir>     e.g. docs/paper/export_reduced
"""

import re
import subprocess
import sys
from pathlib import Path

SI_HEADING = re.compile(r"^# Supporting Information.*$", re.M)
HEADER_TEX = r"""\usepackage{newunicodechar}
\newunicodechar{≤}{\ensuremath{\leq}}
\newunicodechar{≥}{\ensuremath{\geq}}
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\small}
"""  # tables in a smaller font, as is usual for SI tables
PANDOC_OPTS = ["--pdf-engine=xelatex", "-V", "mainfont=STIX Two Text", "-V", "mathfont=STIX Two Math",
               "-V", "monofont=Menlo", "-V", "geometry:margin=2.2cm", "-V", "fontsize=11pt",
               "-V", "colorlinks=true", "-V", "linestretch=1.15", "-f", "markdown-implicit_figures"]


def si_markdown(paper_md: str) -> str:
    """Return the SI part of an exported draft, titled for the paper, with headings lifted one level."""
    title = paper_md.splitlines()[0].lstrip("# ").strip()
    match = SI_HEADING.search(paper_md)
    assert match, "no '# Supporting Information' heading in the export"
    body = paper_md[match.end():]
    body = re.sub(r"^##(#*) ", r"#\1 ", body, flags=re.M)
    return f"# Supporting Information for “{title}”\n{body.rstrip()}\n"


def write_si(export_dir: Path) -> Path:
    """Write supporting_information.md and .pdf into export_dir; return the PDF path."""
    md_path = export_dir / "supporting_information.md"
    md_path.write_text(si_markdown((export_dir / "paper_draft.md").read_text()))
    header = export_dir / ".si_header.tex"
    header.write_text(HEADER_TEX)
    pdf_path = export_dir / "supporting_information.pdf"
    subprocess.run(["pandoc", md_path.name, "-o", pdf_path.name, "--resource-path=.", "-H", header.name,
                    *PANDOC_OPTS], cwd=export_dir, check=True)
    header.unlink()
    return pdf_path


if __name__ == "__main__":
    print(write_si(Path(sys.argv[1])))
