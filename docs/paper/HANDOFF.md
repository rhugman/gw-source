# Paper handoff: editing and review sessions

How to pick up the gwsource paper for *Groundwater* in a new Claude session, and how the author likes the editing and review loop to run. Written 2026-10-16 at the end of the session that produced the reduced draft.

> **Round 2 (2026-10-19 to 2026-10-20).** Work moved to branch `paper-draft-r2` (from `paper-draft-alt` at 3a709b6), worktree `.claude/worktrees/clever-mirzakhani-153553/.paper-wt/draft-r2`, artifact https://claude.ai/artifact/PVmLprZ7bRKNfzY2iX2z1v (code URL …/b62d33e3-a16b-4038-b7c9-9b74bda70aa1), outline artifact https://claude.ai/artifact/P7RNgY9zgxRSFUXEkXzetv. `paper-draft-alt` and its artifacts are frozen. The source is still `docs/paper/draft_reduced/`. At v76 the main text typesets to 11 two-column pages (last page 15 % full) and the SI to 16 pages (`docs/paper/export_reduced/paper_draft_r2_print.pdf`, `supporting_information.pdf`). Round 2 decisions are in `docs/paper/outline.md` §1.5, rows 1–21. Notebook 11 (numerical dispersion) is on `tutorials-paper-sync` at bea5b9b, merged into `paper-draft-r2` on 2026-10-20 (12203e1). The sections below describe the state at the end of round 1 unless they say otherwise.

## Where things are

**Branch:** `paper-draft-alt`.
- It is a local branch in the main gw-source repository. Never push it or merge it to main without the author's go-ahead.
- The tutorial fixes live on `tutorials-paper-sync`, a branch from main that is merged into `paper-draft-alt`. It is 20 commits ahead of main. It goes to main only on the author's go-ahead.
- The other paper branch, `paper-draft`, and its artifact `LP5ehahvpe2gdh53mxtg5d` belong to another session. Do not edit, publish to or reply on them.

**Checkout:** the last session worked in `.claude/worktrees/clever-mirzakhani-153553/.paper-wt/draft-alt`. The app may delete that worktree. If it is gone, check the branch out again:

```bash
git -C /Users/ruihugman/GitHub/gw-source worktree add <path> paper-draft-alt
```

Run `git worktree add` outside the sandbox, because the sandbox blocks writes to `.git/worktrees`. Then symlink `bin` to the main checkout's `bin/` (MODFLOW 6, PEST++).

**Two drafts:**

| | Full draft | Reduced draft (the submission candidate) |
|---|---|---|
| Source | `docs/paper/draft/` | `docs/paper/draft_reduced/` |
| Exports | `docs/paper/export/` | `docs/paper/export_reduced/` (`paper_draft.md`/`.pdf`, `supporting_information.md`/`.pdf`) |
| Artifact | https://claude.ai/artifact/LX8KVAs1Q3Z2rzakLcKkbs (code URL …/9e12753c-e64a-4ea4-ae81-07681c063612) | https://claude.ai/artifact/GyJwNMpBqzqEg6KSeQWe3a (code URL …/8155c90b-1474-46bf-a372-7f3f8c356221) |
| Size | about 22 typeset pages (NJD print layout), plus a long SI | 6 typeset pages (last page 92 % full), plus a 25-page SI |

- The outline is `docs/paper/outline.md`. Its artifact is https://claude.ai/artifact/NT8m758JEdjy2nDXjhdrts.
- Each draft folder has the same layout:
  - `sections/NN_*.md`: the text, with `<!-- evidence: … -->` comments that give the source of every number;
  - `display/*.md`: figure and table captions, `**Figure n.**` blocks, with `<!-- file: … -->` and `<!-- width: single -->` rules;
  - `si/*.md`: the SI, ordered and labelled by `si/numbering.md`, with `{SI: name}` markers in the text;
  - `reviews/`: the review reports, which hold the reasoning behind past changes.
- Terms and words to avoid: `docs/paper/terms.md`.

**Publishing to the artifacts from a new session:**
1. `Artifact` `action: "read"` on the URL. This is required before the first publish.
2. Publish with `url` set and `files` mapping every `fig/*.png` that changed.
3. Comments only reach a session that watches the artifact. Call `ArtifactComments` `action: "watch"` with the URL early in the session.

## Build, export, typeset

All commands run from the branch root, in the `gw-source` conda env (`~/miniforge3/envs/gw-source/bin/python`).

| Task | Command |
|---|---|
| Page for the artifact | `python studies/paper/page/build_draft.py . draft_reduced` (no last argument for the full draft). Output goes to `studies/paper/page/output/site_reduced/`, which is git-ignored. It must print `unplaced: []`. |
| Outline page | `python studies/paper/page/outline_page.py .` |
| Markdown export | `python studies/paper/page/export_md.py . docs/paper/export_reduced draft_reduced` |
| Pandoc PDF of the export | `pandoc paper_draft.md -o paper_draft.pdf --pdf-engine=xelatex --resource-path=. -H hdr.tex -V mainfont="STIX Two Text" -V mathfont="STIX Two Math" -V monofont=Menlo -V geometry:margin=2.2cm -V fontsize=11pt -V colorlinks=true -V linestretch=1.15 -f markdown-implicit_figures`, run in the export folder. `hdr.tex` maps ≤ and ≥ with `newunicodechar`; the header is in `si_pdf.py`. |
| SI as its own PDF | `python studies/paper/latex/si_pdf.py docs/paper/export_reduced` |
| Typeset page count, the real test | `python studies/paper/latex/typeset_groundwater.py reduced print` (also `submission`, and `full`). It reports the pages and how full the last page is. |
| Word-based page estimate (rough) | `python studies/paper/page_estimate.py docs/paper/draft_reduced`. It overestimates long drafts. |

Notes on these tools:
- The page builder used to live outside git, in `.paper-wt/draft_page_alt/`. It is now committed in `studies/paper/page/` with the same code and output under `page/output/`. Use this copy.
- Typesetting uses the author's Wiley NJD class: WileyNJDv5.cls, NJDnatbib, wileyNJD-Harvard.bst and Fonts/. It expects them in `../gw_template_njd/`, next to the checkout. They are Wiley's files and stay out of git. If the folder is missing, copy those files (not the manuscript) from `/Users/ruihugman/GitHub/emulator-demo-clean/paper`.
  - The **print** layout (`HARVARD,Times2COL`) approximates published pages.
  - The **submission** layout (`HARVARD,Times1COL,doublespace`, line numbers) is what gets sent to the journal.
  - The script works around `\reserveinserts` and the `.bst` filename case. See `studies/paper/latex/README.md`.
- Page budget: Groundwater gives 6 free published pages, or 7 for NGWA members, and charges US $250 for each page beyond that. The reduced draft must stay at 6 pages or under in the print layout. Rerun the typesetting after every text change that adds words.

## Figures

- Every figure has a script in `studies/paper/`. Each script has `main(...)` gates for the individual figures, and a `QUOTED` dict that asserts every number the caption or text quotes.
- Run a single figure, not the whole set. For example:

  ```bash
  PYTHONPATH=src:tutorials:studies/paper python -c "import example_figures_b as m; m.main(fig7=True, fig8=False, fig10=False, fig11=False, run_ies=False)"
  ```

  Look at the PNG after every change.
- Scripts by figure:

  | Script | Figures |
  |---|---|
  | `gallery_figure.py` | reduced Fig. 2: one panel per output type; gate `method` draws Fig. 1 (a: eight-cell example, b: snapshot against transient tracking); gate `examples` draws Fig. 3 (particle share, Bedekar curves) and SI Figure S4 |
  | `method_figures.py` | method schematic of the full draft; `draw_transient` supplies Fig. 1b |
  | `example_figures.py` | full Figs 2–6 |
  | `example_figures_b.py` | full Figs 7, 8, 10, 11 |
  | `transient_figure.py` | full Fig. 9 |
  | `neversink_figures.py` | Neversink figures; gate `fig_single` is reduced Fig. 4 (round 2), gate `fig_si_cd` the SI figure |
  | `si_dispersion_figure.py` | SI numerical dispersion |
  | `verification.py` | verification figures |

- Outputs go to `docs/paper/figures/`.
- Neversink data come from the main checkout's `studies/neversink/output`. The study notes are in `docs/neversink_study.md`.
- Some runs need the sandbox disabled, for these reasons:
  - Jupyter kernels and PEST++ workers need local ports.
  - gmsh (used by vorflow) crashes with an OpenMP error inside the sandbox.
- Numbers come from the tutorial notebooks in `tutorials/` (`herebedragons.py` holds the shared builders). The paper and the tutorials must stay in step. If the paper needs a cleaner example, change the tutorial on `tutorials-paper-sync`, re-run it in place (`jupyter nbconvert --execute --inplace`), run `pytest -m tutorials -k NN`, and merge the branch into `paper-draft-alt`.
- Repository docs that the SI points to:
  - `docs/verification.md`
  - `tests/models/README.md`
  - `docs/neversink_study.md`
  - `docs/dispersion_study.md`

## How the author runs a review session

- The author reads the artifact and leaves comment threads, often only a few words long: "weird", "cut sentence", "totals of what?", "a and b". Each one arrives as a message in the session.
- For each comment:
  1. Read the anchored text in the source file.
  2. Make the change.
  3. Rebuild and publish to the same artifact URL.
  4. Reply in the thread with the new wording and the version number.
  5. Resolve the thread.
- In the session, write one short line saying what was done.
- When the comment is a question ("is that implemented?", "why 2 ensembles?"), answer it in the thread. If the answer points to a text change, make it.
- When the comment says "discuss before any changes", reply with your reading and the options, and leave the thread open.
- Short replies such as "replaced", "a and b" or "implemented" answer a question you asked in the thread. Read the thread first to see what they refer to. For example, "implemented" meant "replace the word 'read' with 'implemented'", not "the feature now exists".
- Apply a wording fix everywhere it occurs: both drafts, the SI, captions and `terms.md`. Not just the anchored sentence.
- Large jobs go to subagents with a full brief:
  - writing and revising;
  - figures;
  - reviews from separate lenses, for example scope, structure, prose, facts.

  The orchestrator checks their numbers, looks at every figure, publishes, and replies.
- Each subagent brief should contain:
  - the prose rules;
  - "never change a number; keep evidence comments";
  - "commit by explicit paths, no attribution lines, never push";
  - "don't edit files another agent is working on".
- Commit as you go. The worktree can disappear, and the overnight purge of `/tmp` has already destroyed uncommitted work once.
- Downloads from the internet need the author's explicit go-ahead, as do pushes and merges to main.

## Lessons from the author's feedback

The voice rules live in the `voice-hugman` skill. Load it for any manuscript prose, and put its rules in every writer's and reviewer's brief. The memory notes `paper-prose-feedback`, `paper-voice-orchestration` and `paper-draft-alt-fork`, in `~/.claude/projects/-Users-ruihugman-GitHub-gw-source/memory/`, add these points from this round:

**Words**
- "credit" or "credited" is an LLM-ism. Use "attribute", "count as" or "gives the well".
- "X gives no Y" is an LLM-ism too. Use "does not report Y" or "cannot say when…".
- Name the thing. "Totals" became "a well's water by source and the mean travel time". "Read" became "implemented".

**Sentences**
- One idea per sentence.
- No semicolons. No colon or ", and" two-part sentences. No appositive packing. No participle openers.
- Don't jump with "So …" when the step in between is missing. Put the missing step back.

**Framing**
- Frame the paper as the tool for practitioners: fast, checked against other common approaches, open about trade-offs.
- Don't narrow it to wells or capture zones. The tool traces sources, fate, travel time and any sink.
- Don't pick on FlowSource. Name it neutrally, and only in the paper text, never in code, docs, figures or notebooks.
- Climate-neutral seasons: wet, wet-to-dry, dry, dry-to-wet. Never winter and summer.
- Explain each concept where it first appears. Shorter must not mean cryptic.
- Keep honest hedges ("we read this as …") where a check is partial. Don't overclaim.
- Every cut must keep its caveats. When the reduced draft lost "not an independent test" or "did not improve", the claims became stronger than the full draft's.
- Abstract, conclusions and impact statement must say the same thing. When one changes, update the others.

**Figures**
- Panel tops aligned. Colour bars as tall as their panels.
- Figures sized for the journal: single column 8.25 cm, double 17.15 cm.
- Compact composite figures are preferred over many full-width ones. The gallery figure is the model.

**Layout**
- Section titles fit on one line of a column.
- Subsections are bold run-in heads.
- The SI holds only what a reviewer needs to check a claim. Repository detail goes to `docs/` or the notebooks, which the Zenodo release archives.

**Science**
- When a result surprises the author, such as the Voronoi grid giving a wider edge, the author wants a test before an explanation goes in the text. That case led to the rotated-grid and finer-grid check in tutorial 04.

## Open items

- Round 2: two Methods sentences carry `<!-- [author to confirm] -->` (why gross accounting is the default, and why travel times are gross only).
- Round 2: the Fig. 4 legend still says "published cells". A redraw to match the text was offered and not yet answered.
- Round 2: an alternative journal, *Environmental Modelling & Software*, was checked on 2026-10-20. It fits the scope as a research article. It would need an abstract of at most 150 words, 3–5 highlights, possibly a graphical abstract, and a fixed-field "Software availability" section. No length limit was found, and preprints are allowed anywhere. The Guide for Authors blocked automated reading, so check these limits in the live guide.
- §7 of both drafts has these `[check]`s: the public URL, the release version and tag, the Zenodo DOI, and pinned MODFLOW 6 and FloPy versions. They wait for the author's Zenodo release, which comes before submission.
- `10_references.md` has two `[check]`s: the page numbers of the Foley and Black proceedings paper, and one other entry.
- Visser et al. (2009): the methods section has not been read to confirm how the particle-splitting precedent is cited.
- Groundwater's key-word limit is unconfirmed. The draft uses 9.
- The full draft is about 22 typeset pages. It is kept as the long version and as the source of the SI material. It has not been updated for the reduced draft's later prose fixes, except the shared ones: the wording of "credit", "gives no", MVE and "totals".
- Merging `tutorials-paper-sync` into main needs the author's go-ahead.
- The two new feedback rules ("credit", "gives no") belong in the voice-hugman skill files. The fork session's sandbox could not write to `~/.claude/skills`.

## Suggested skills

- `voice-hugman`: for all paper text, captions, SI, review replies and subagent briefs.
- `python-style`: for figure scripts, tutorial helpers and the build tools.
- `artifact-design`: only if the page template (`studies/paper/page/template.html`) changes.
- `anthropic-skills:pdf`: for checks on the exported PDFs.
