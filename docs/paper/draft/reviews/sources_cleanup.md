# Sources clean-up: non-publications removed

Rule applied: cite only what Groundwater accepts in a reference list (peer-reviewed papers, books, conference proceedings papers, agency reports, theses, software and data releases with a DOI or report number). No slides, posters, talk recordings or web pages standing in for a publication. Draft at commit f19d33f, branch paper-draft; edits not committed.

## Reference entries

Line numbers in "where it was cited" are those of f19d33f. The edits changed text within lines only, so they still hold for sections/, display/ and si/.

| Entry | Publication? | Action | Where it was cited |
|---|---|---|---|
| Bakker et al. 2016 | Yes, journal paper | Kept | — |
| Barlow et al. 2018 | Yes, journal paper | Kept | — |
| **Bedekar et al. 2023** | **No: slides, CWEMF annual meeting (title slide, references/docs/text/2023_Bedekar_etal_CWEMF_unit_concentration_slides.txt); no published abstract or paper found** | **Removed** | sections/01_introduction.md:17; display/A.md:27 (footnote 5); si/A.md:10, :17, :31, :32, :60, :62 |
| Bedekar et al. 2024 | Yes, journal paper | Kept | — |
| Black and Foley 2013 | Yes, proceedings paper: a 12-page paper with abstract and reference list (text copy 2013_Black_Foley_FlowSource_application.txt), pp. 652–663 of the MODFLOW and More 2013 proceedings as cited in Maurice et al. (2021). The separate 2013 poster (bibliography.md [BF13p]) is not cited. | Kept | — |
| **Black et al. 2021** | **No: 11-slide deck on the vendor's web site, no meeting given (bibliography.md [BFW21])** | **Removed** | sections/01_introduction.md:13, :17; display/A.md:3; si/A.md:31, :42, :44, :47 |
| Campana and Simpson 1984 | Yes, journal paper | Kept | — |
| Chowdhury 2016 | Yes, MASc thesis | Kept | — |
| Cornaton and Perrochet 2006 | Yes, journal paper | Kept | — |
| Corson-Dosch et al. 2022 | Yes, USGS SIR | Kept | — |
| **Daley et al. 2022** | **No: poster, Groundwater Modellers' Forum 2022 (bibliography.md [DAL22])** | **Removed** | sections/01_introduction.md:13 (twice); display/A.md:3, :15; si/A.md:31, :41, :42, :44, :46, :47 |
| Environment Agency 2019 | Yes, agency report | Kept | — |
| Fienen and Corson-Dosch 2021 | Yes, USGS data release with DOI | Kept | — |
| Fienen et al. 2022 | Yes, journal paper | Kept | — |
| Foley and Black 2013 | Yes, proceedings paper: an 11-page paper with abstract, methods and reference list (text copy 2013_Foley_Black_FlowSource_DAG_algorithms.txt). Pages 571–581 still unverified (existing check marker). | Kept | — |
| Frind et al. 2002 | Yes, journal paper | Kept | — |
| Goode 1996 | Yes, journal paper | Kept | — |
| Hughes et al. 2024 | Yes, journal paper | Kept | — |
| Javandel and Tsang 1986 | Yes, journal paper | Kept | — |
| Langevin et al. 2017 | Yes, USGS TM | Kept | — |
| Langevin et al. 2022 | Yes, USGS TM | Kept | — |
| Langevin et al. 2026 | Yes, USGS software release with DOI | Kept | — |
| Leake et al. 2010 | Yes, journal paper | Kept | — |
| McLane and Cecan 2009 | Yes, journal comment | Kept | — |
| MODFLOW 6 Development Team 2026 | Doubtful: input/output guide from the develop branch on GitHub, with no DOI or report number of its own | Kept; **author's decision** (see below) | sections/03_implementation.md:11, 09_availability.md:3; si/A.md:19, :31, :64 |
| Neupauer and Wilson 1999 | Yes, journal paper | Kept | — |
| Nogueira et al. 2022 | Yes, journal paper | Kept | — |
| Partington et al. 2011, 2012, 2013 | Yes, journal papers | Kept | — |
| Pollock 1988 | Yes, journal paper | Kept | — |
| Pollock 2016 | Yes, USGS OFR | Kept | — |
| Potter et al. 2008 | Yes, journal paper | Kept | — |
| Provost et al. 2017 | Yes, USGS TM | Kept | — |
| Pryet et al. 2022 | Yes, journal paper | Kept | — |
| Rushton 2003 | Yes, book | Kept | — |
| Schilling et al. 2017 | Yes, journal paper (not read) | Kept | — |
| Tosco et al. 2010 | Yes, journal paper | Kept | — |
| White et al. 2020 | Yes, USGS TM | Kept | — |

In 10_references.md the three entries and their HTML comments were deleted. The closing comment now gives 36 entries and 12 works not in bibliography.md, drops Bedekar et al. 2023 from the list of entries completed from text copies, and drops the note on the author list of Black et al. 2021.

Citations checked both ways after the edits (sections/, display/, si/; HTML comments ignored): all 36 entries are cited, and every author–year citation has an entry. `tests/test_naming.py`: 2 passed.

## Claims reworded or cut

Ordered by how much they change what the paper says.

1. **sections/01_introduction.md:17, credit to FlowSource20 (cut).** Old: "…and GWT implicitly, and the steady forward fraction of FlowSource20 has been read as a relative concentration (Black et al. 2021)." New: "…and GWT implicitly." The credit rested on slide 10 only. The 2013 papers have no forward fraction: their "fractional flow from" is a backward quantity on each cell's inputs. Reading a fraction as a concentration is credited to the unit-concentration method, already in Section 1 at line 11 (Bedekar et al. 2024). No section claims that equivalence as new.
2. **sections/00_front.md:5, abstract (reworded, weaker).** Old: "is described only in conference papers and has no open implementation". New: "has not been described in a journal article and has no open implementation". The old wording was not strictly true even before the cut, because slides, a poster, the Environment Agency (2019) manual and Chowdhury (2016) also describe the method. The new claim follows from the old one and rests on bibliography.md (no peer-reviewed journal article found). "No open implementation" is unchanged: the 2013 papers offer the program and its source code (academic use) on request.
3. **sections/01_introduction.md:13 (reworded).** Old: "is described only in conference papers, slides and a poster (…; Black et al. 2021; Daley et al. 2022) and has no open implementation. … the changes in its 2020 version, FlowSource20, are listed but not described (Daley et al. 2022)." New: "is described in two conference papers (Foley and Black 2013; Black and Foley 2013); we found no journal article on it, and it has no open implementation. … We found no published description of later versions of the program." FlowSource20 is no longer named.
4. **display/A.md:11, Table 1 Outputs, FlowSource (cut).** Old: "F, volumes through and from; forward fraction; particle travel time". New: "F, volumes through and from; particle travel time". The forward fraction (C/C0) came from the slides and poster only. si/A.md:14 and :42 cut to match.
5. **display/A.md:16, Table 1 Grids and packages, FlowSource (reworded).** Old: "Structured MODFLOW grids (2013); MODFLOW 6, MODFLOW-USG unstructured (2020); package networks not documented". New: "Structured MODFLOW grids; method said to apply to unstructured grids (2013); package networks not documented". From Foley and Black (2013) Abstract. The table no longer says that FlowSource20 reads MODFLOW 6. si/A.md:47 cut to match ("not mentioned in either paper").
6. **display/A.md:15, Table 1 Built-in checks, FlowSource (cut).** Old: "None described in the papers we found; flow loops reported (2013); unspecified "error checking" (2020; Daley et al. 2022)". New: "None described; flow loops reported (2013)". si/A.md:46 cut to match.
7. **display/A.md:3, Table 1 caption (reworded).** Removed "for its 2020 version, FlowSource20, Black et al. 2021 and Daley et al. 2022". Old: "Years in parentheses date a statement to the 2013 papers or to FlowSource20." New: "The FlowSource column describes the program as published in 2013, and years in parentheses date a statement to those papers; we found no published description of later versions." si/A.md:3 reworded the same way.
8. **sections/01_introduction.md:17, backward in time (reworded).** Old: "for unit-concentration transport we read only an abstract and slides (Bedekar et al. 2023, 2024)". New: "…we read only the abstract of Bedekar et al. (2024)". The claim "We found no method in Table 1 that tracks water backward in time" is unchanged. For GWT it now rests on Langevin et al. (2022) and the abstract, which still carries the [check] marker. The slides showed only forward runs.
9. **display/A.md:27, footnote 5 (reworded).** Old: "…, and the authors' slides on the method show only forward runs (Bedekar et al. 2023); of Bedekar et al. (2024) we read only the abstract." New: "…; of Bedekar et al. (2024) we read only the abstract, which lists well capture analysis among the uses without saying how it is done." The added clause comes from si/A.md:17.
10. **si/A.md:17 (cut).** Removed the description of the 2023 slides: four forward transient runs, one per tagged source, and no code or weak sinks named.
11. **si/A.md:10, :60, :62 (cut).** Removed the slide citations from the notes on advection and dispersion, outputs and backward in time. Each claim keeps its abstract-based or Langevin-based support.
12. **si/A.md:41 (reworded).** Old: "Dated 2013 because Daley et al. (2022) lists unspecified improvements to the flow routing in the 2020 version." New: "Dated 2013 because we found no published description of later versions."
13. **si/A.md:44 (cut).** The sources for "Backward in time: none" are now the two 2013 papers only.
14. **si/A.md:31, :32 (cut).** Removed the slides and poster from the "Read in full" list, and the sentence "The 2023 slides above present the same method but are not the paper."

## For the author's decision

- **"Commercial" in Table 1 (display/A.md:17).** It rests only on the vendor's web pages (si/A.md:31, :48). The 2013 papers say only "available on request", with source code for academic use on request. The pages are not an author–year citation and were left in place. If they also fall under the rule, change the cell to "No: program and VB.NET source (academic use) on request (2013)" and remove the web pages from si/A.md:31 and :48.
- **MODFLOW 6 Development Team 2026.** This is the input/output guide on the develop branch, with no DOI or report number. One option is to cite it as the guide distributed with the MODFLOW 6 software release (Langevin et al. 2026, DOI 10.5066/P1PGE9XW), after checking that the cited sections appear in that release.
- **Web pages as access routes in si/A.md:32–34.** Semantic Scholar, Clear Creek Associates, Europe PMC and Aquanty are named only as the routes by which abstracts were read; the citations are to the papers. The Aquanty research summary is the only basis for what si/A.md:9 says about Schilling et al. (2017). That paper's abstract should be checked before submission.
- **Foley and Black 2013, pp. 571–581.** The page range has no checked source (existing [check] marker). Both 2013 items are full proceedings papers, not slides.
