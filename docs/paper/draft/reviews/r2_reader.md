# Round 2 review: reader and editor (`reader`)

Draft at commit 4b750f2, `paper-draft`. I read it against `reviews/r1_reader.md` and `decisions_r1.md`, from the same two seats: a consulting modeller who draws wellhead zones with MODPATH, and a *Groundwater* associate editor.

**Editor's verdict.** This is a clear improvement. The paper now opens fairly to particle tracking, frames the benchmark caveat first, and has a guidance paragraph (§6.5). It prints at about 16 pages. Before sending it to review, I would still return it for four things:
- nine SI citations point at sections that do not exist;
- the novelty claim on backward tracking in time rests on an unread *Groundwater* paper (Bedekar et al. 2024), and two other citations are marked "not read";
- PRT has lost its citation;
- §6.5 recommends F > 0.5 as the "single best estimate" without saying that on Neversink this area was less than half the size of the particle-tracked areas.

---

## 1. Round 1 MUSTs and top changes: status

| r1 item | status | where |
|---|---|---|
| MUST W5: main text over length | **Partly.** 7,926 → 7,652 words. Within the brief's ±5 %, but above the ≤ 7,500 set in decisions_r1. | §2 |
| MUST 01:5: one forward particle run serves every well | **Resolved** | 01:5 |
| MUST 05:33: "therefore" attribution | **Resolved**: now "We attribute … supports this only for the spreading between sinks" | 05:29 |
| MUST 05:57: undefined 4.76 | **Resolved**: the configuration is now named | 05:51 |
| MUST 06:9: "a third" used two ways | **Resolved**: "about 0.33" and "35 %" | 06:9 |
| MUST 08:3: forward–backward check on Neversink | **Resolved**: "the closure check on Neversink" | 08:3 |
| MUST D:29: Table 3 "flow reaching the wells" | **Resolved**: the table moved to the SI as "flow credited to the wells" | si/D.md |
| Top 1: prescriptive §6 with a workflow | **Mostly.** §6.5 added. Gaps remain: F > 0.5 is undersized on Neversink, there is no route to a time-limited area from a steady model, and streams are left out. | 06:31 |
| Top 2: fair to particles; caveat first in §5.2 | **Resolved.** 01:5 still has a weak sentence ("described as awkward"). | 01:5, 05:15 |
| Top 3: one home per explanation; fewer duplicated numbers | **Partly.** Gross/net, novelty, the benchmark caveat and the §4 numbers are fixed. Still repeated: S region (05:39 and 06:25), thresholds (06:11 and 06:31), the GWT match (04:41 and 06:21), "halving … about 30 %" (04:29 and 07:3), Monte Carlo offsets (05:37 and 06:27). | below |
| Top 4: display items down to 15–16 pages | **Resolved.** About 16 pages; all captions within the limits. | §2 |
| Top 5: overreaching claims | **Resolved** | — |

## 2. Length, pages and cuts

Word counts leave out HTML comments, `[[...]]` markers, headings and display equations.

| § | words | r1 budget (decisions) | over |
|---|---|---|---|
| 1 | 892 | 850 | +42 |
| 2 | 1,827 | 1,750 | +77 |
| 3 | 447 | 400 | +47 |
| 4 | 1,105 | 1,050 | +55 |
| 5 | 1,384 | 1,350 | +34 |
| 6 | 1,118 | 1,100 | +18 |
| 7 | 299 | 300 | −1 |
| 8 | 177 | 180 | −3 |
| 9 | 115 | 100 | +15 |
| **Main text** | **7,652** | **7,500** | **+152 (+2.0 %)** |

Front matter: the title has 96 characters, the Article Impact Statement 136 (limit 140) and the abstract 248 words (limit 250, so no room). Captions: Fig. 1 has 170 words; every other caption is ≤ 150. Table 1 is about 795 words with five footnotes.

**Page estimate.** This uses the same assumptions as round 1: about 1,000 words per page of body text and about 1,300 per page of caption or table type.

| part | pages |
|---|---|
| body | 7.7 |
| front matter | 0.5 |
| headings and 9 display equations | 0.6 |
| 9 figures (Figs 3, 4, 6, 8 at ~0.6 page; Figs 1, 2, 5 at ~0.45; Figs 7, 9 at ~0.3) | 4.35 |
| captions (~1,060 words) | 0.8 |
| Table 1 | 0.9 |
| references | 1.3 |
| **total** | **~16 (range 16–17)** |

Page charges are US$2,500–2,750 at 6 free pages, or US$250 less for an NGWA-member corresponding author. The cuts below, with Fig. 9 moved to the SI, bring it to about 15–16 pages (US$2,250–2,500).

**Cuts to reach ≤ 7,500 words**, ranked from least to most cost to the reader. The list gives ~−550, which leaves ~150 words for the §6.5 additions asked for below.

| # | cut | words | cost to the reader |
|---|---|---|---|
| 1 | 06:25: drop the S-region sentence, which repeats 05:39. Keep "a report should say so". | −45 | none (repeat) |
| 2 | 07:3: drop "so halving the cell size narrows it by about 30 %", which repeats 04:29 | −12 | none (repeat) |
| 3 | 06:27: the Monte Carlo offsets paragraph repeats 05:37. Fold the archiving advice into the SI. | −45 | none (repeat) |
| 4 | 06:11: fold the threshold paragraph into §6.5, giving each number once | −90 | none (repeat) |
| 5 | 06:21: drop "to 9.8 × 10⁻¹⁴ on tutorial 08" and the volume-option numbers; cite §4.4 | −30 | none (repeat) |
| 6 | 07:9: move the PRT thin-film abort to its SI section, which already exists | −22 | negligible |
| 7 | 02:39: move the fixed-cells sentence to its SI section, which already exists | −25 | negligible |
| 8 | 02:65: move the well-cell residence sentence ("This time includes … mean residence there") to {SI: travel-time identity}; do the same for 9607 d at 04:13 | −55 | low; a consultant is confused by it here |
| 9 | 03:9: shorten the statistics list to "running statistics per cell (extremes, means, threshold counts)" | −30 | low |
| 10 | 02:79: move the model 6 volume-option numbers to §4.2 or the SI, keeping the reason in one sentence | −40 | low |
| 11 | 06:15: move the per-well counts to {SI: per-well gross and net} and keep the pattern in words. r1 asked for this; the section has grown from 8 numbers to 14. | −80 | low |
| 12 | 05:51: move "one convention at a time" (4.76, 3.83, 4.53) and the inference to the SI, keeping "PRT with the published conventions reproduces the published growth (3.62 against 3.60)" | −75 | moderate; Neversink-specific mechanism |

---

## 00_front.md

- **00:5 · SHOULD** · "Its agreement … lies within the spread of particle tracking under different conventions". This is accurate, but it does not carry the practitioner message (conventions matter as much as the method; report them). With the abstract at 248 words this is optional. If the abstract is touched again, change the last sentence to "…within the spread of particle tracking under different conventions, which change the area as much as the choice of method."

## 01_introduction.md

- **01:5 · SHOULD** · "Backward analysis of transient models is described as awkward with particles". Attributing it to the Environment Agency makes it a hedge, but it is still weak, and it is now the only transient motivation in §1. Fix: "Particles also cannot say what share of the pumped water was released from storage, or was in the aquifer at the start of the simulation."
- **01:9, 01:17 · MUST** · Three citations rest on unread sources:
  - "McLane and Cecan (2009) [check: not read]"
  - "Schilling et al. 2017 [check: not read]"
  - "this rests on an abstract and the authors' slides (Bedekar et al. 2023, 2024)"

  An editor will send this paper to a GWT developer or to Bedekar. Claiming that unit-concentration transport has no backward-in-time option, while having read only the abstract of a paper in this same journal (*Groundwater* 62, no. 2), invites a rejection on reviewer goodwill alone. Fix: read Bedekar et al. (2024) in full before submission and update Table 1 footnote 5. Read McLane and Cecan (2009) and Schilling et al. (2017), or drop them.

## 02_methods.md

- **02:13 · SHOULD** · "The outflow of cell $i$ through the destination's sink terms is $d_i$…". This is now a one-sentence paragraph after Fig. 1. Fix: join it to the end of the first paragraph of §2.1.
- **02:39 · SHOULD** · "For a group selected by package or boundary, only the cells … are fixed". This is implementation detail with an SI home. Fix: cut it to the SI pointer (cut 7).
- **02:65 · SHOULD** · "particles stopped on entering a well cell measure the time to enter it". A newcomer stumbles here, and it matters only for §4.1's 9574 vs 9607 d. Fix: move it to {SI: travel-time identity} (cut 8).
- **02:79 · SHOULD** · The volume-options paragraph is the densest in §2, and a consultant needs only "the default keeps every cell's balance exact; the "gwt" option reproduces GWT". Fix: keep the reason in one sentence and move the model 6 numbers (cut 10).

## 03_implementation.md

- **03:11 · MUST** · "For MODFLOW 6 particle tracking (PRT), the code writes…". PRT, a central tool of the paper, has no citation. The r1 draft's "[check: PRT documentation]" was dropped, which breaks hard rule 3 ("keep every [check]"). Fix: restore "[check: PRT documentation]" or give the citation.
- **03:9 · SHOULD** · The statistics list runs to ~40 words. Fix: shorten it (cut 9).

## 04_verification.md

- **04:13 · SHOULD** · "m/F of §2.6, which includes the residence in the well cell, is 9607 d". A third number for one comparison. Fix: keep 9574 vs 9590 d and move 9607 d to the SI.

## 05_neversink.md

- **05:23 · SHOULD** · "[check: the five-layout scripts are not in the repository]". An editor checking reproducibility will ask about a range quoted from scripts that cannot be found. Fix: add the scripts or quote only the single run.
- **05:39 / 06:25 · SHOULD** · The S-region result appears twice with the same numbers. Fix: cut it from §6.4 (cut 1).
- **05:49–51 · SHOULD** · §5.6 spends ~140 words on growth mechanisms (4.57, r = 0.94, 3.62, 4.76, 3.83, 4.53). It is the most Neversink-specific part of the paper (see §4 of this review). Fix: cut 12 and move Fig. 9 to the SI, keeping the two numbers 4.09 and 3.60 in the text.

## 06_discussion.md

- **06:7 · SHOULD** · "as the Environment Agency (2019) does for inner zones". The sentence still does not say what is combined, or when a zone counts as small. Fix: "…e.g. a zone only a few cells wide, where the transition band of §4.3 spans most of it, we would draw the inner zone with particles, as the Environment Agency (2019) does [check: EA 2019 inner-zone method]."
- **06:11 · SHOULD** · This threshold paragraph and §6.5 give the same numbers (27 %, 13 %, 92 %). Fix: fold it into §6.5 (cut 4).
- **06:15 · SHOULD** · 14 numbers in 195 words, more than in round 1. Fix: cut 11.
- **06:21 · SHOULD** · "to 9.8 × 10⁻¹⁴ on tutorial 08 (§4.4)" and "(tutorial 08: 2 × 10⁻⁴ forward, 4 × 10⁻³ backward…)" repeat §4.4. Fix: cite §4.4 without the numbers (cut 5).
- **06:27 · SHOULD** · This repeats 05:37. Fix: cut 3.
- **06:31 · MUST** · "We would take the F > 0.5 area as the single best estimate of the advective zone". The recommendation cites only the favourable evidence:
  - On Neversink the F > 0.5 area covers 43 % of the published cells (05:19).
  - It holds about 409 of the 691 cells of the PRT area, about 59 % [derived: 0.917 × 445; check envelope_prt.csv].
  - It has 445 cells against an expected area of 910 (05:15).

  It is a core, not a size estimate, and §5.2 calls it that. A consultant following §6.5 would draw a zone roughly half the size of every particle-tracked area. Fix: "We would take the F > 0.5 area as the core of the advective zone: it was within 5 % of the reference area in the synthetic tests (§4.3), but on Neversink, with weak sinks and streams, it held only about 60 % of the PRT area and 43 % of the published cells (§5.2–5.3). We would therefore also report the expected area (sum of F), which was close to the published count (910 against 980 cells), and…"
- **06:31 · SHOULD** · "We would draw the F ≥ 0.1 area as the wider area, although on Neversink it missed 13 to 27 %". The next sentence offers a particle check "where the area ends at weak sinks", but the 13 % miss against weight-losing PRT is spreading between sinks, not a weak-sink effect (05:29). The check as written does not cover it. Fix: "F ≥ 0.1 is not a guaranteed envelope: on Neversink it missed 13 % of the PRT area even where particles and full mixing treat sinks alike (§5.3)."
- **06:31 · SHOULD** · "covers every well in one trace (§2.3)". That statement is in §2.4, not §2.3. Fix: cite §2.4.
- **06:31 · SHOULD** · "For an area tied to a travel time, we would use backward tracking in time over the stated horizon". Most protection-zone models are steady, like Neversink, and the paragraph does not say how to get, say, a 50-day area from one. Fix: one sentence. Say that the steady flows can be run as a transient simulation over the horizon, as model 10 does (§4.2). Say that short horizons need transport sub-steps, since one step per flow step nearly doubled the first-step share of new water (§4.4). Add "not tested for short horizons here" as the hedge.
- **06:31 · SHOULD** · §6.5 is silent on streams, but how streams are represented changes the area (§5.4, Fig. 6). Fix: "We would draw the zone with streams as cells, and report that it stops at the streams; where the quality of stream water reaching the well matters, we would add the stream network area (§5.4)."

## 07_limitations.md

- **07:3 · SHOULD** · "so halving the cell size narrows it by about 30 %". This repeats 04:29. Fix: cut 2.
- **07:9 · SHOULD** · "MF6 PRT aborts in a cell wet only by a thin film". This is a defect of another code and already has an SI home. Fix: cut 6.

## 09_availability.md

- **09:3 · SHOULD** · Six [check]s remain: public URL, DOI, MF6 I/O guide, data-release authors, model splitter, version pinning. The model splitter [check] also appears at 04:9. These are mechanical but must be closed before submission.

## display/ (main-text display items)

- **D:15 · SHOULD** · Fig. 8: "moved one row north onto their cells". The reader meets this bookkeeping in a caption with no context. Fix: append "({SI: Monte Carlo offsets and scenario rule})".
- **D:19 · SHOULD** · Fig. 9 is Neversink-specific; moving it to the SI makes the display items 4 method and 4 Neversink. Fix: move it, as the brief already planned if pages must fall.

## si/ (citation targets)

- **SI · MUST** · Nine `{SI: …}` placeholders cited in the main text have no section in `si/*.md`:
  - "per-well comparison" (05:15)
  - "end states of the published particles" (05:19)
  - "diagnosis of the first PRT runs" (05:23)
  - "ensemble statistics" (05:39)
  - "scenario medians" (05:45)
  - "one convention at a time" (05:51)
  - "faster growth of weight-losing particles" (05:51, 07:7)
  - "per-well gross and net" (06:15)
  - "Monte Carlo bookkeeping offsets" (06:27; the section is named "Monte Carlo offsets and scenario rule")

  An editor numbering the SI in order of first citation cannot do so. Fix: writers D and E add these sections from NS Tables 2, 2a–2b, 4–7 and Texts S2–S5, and fix the 06:27 name.

---

## 3. Can a newcomer follow §1–2 and then draw a zone with §6.5?

**§1–2: yes, with two stumbles.**
- §1 now defines weak sink, full mixing, destination, source and the reference method before using them.
- In §2.2 the 6/11 example sits right after the cell rule. That is the single best fix in the round.
- §2.5 now says what a failed check means.
- §2.9 opens with the question it answers.
- The stumbles are the well-cell residence detail (02:65) and the volume-options paragraph (02:79). Neither is needed to use the method.

**§6.5: not yet safely.** A consultant following it would:
- draw an F > 0.5 zone about half the size of any particle-tracked area, because the paragraph omits that evidence (MUST at 06:31);
- treat F ≥ 0.1 as an envelope checked at weak sinks, which misses the between-sink gaps;
- not know how to get a 50-day area from a steady model;
- not know which stream treatment to use.

The four fixes above, about +120 words, make §6.5 usable.

## 4. Method-first?

The abstract, §1 and §2–4 are method-first, and §5 opens with "a benchmark, not a reference", which works. Neversink still takes about 2,000 of 7,650 words: §5 is 1,384, and §6.1, §6.2 and §6.4 add about 650 between them. It also takes five of nine figures (Figs 5–9). The parts that read as a Neversink study rather than a demonstration are:
- the growth-mechanism detail (05:49–51);
- the per-well gross/net counts (06:15);
- the Monte Carlo bookkeeping (05:37, 06:27).

Cuts 3, 11 and 12 and moving Fig. 9 to the SI shift the balance to four method figures against four Neversink figures. They take Neversink to about 22 % of the words, without losing any demonstration item (i)–(v) listed at 05:3.

## 5. What an associate editor would send back before review

1. The missing SI sections (nine citations).
2. Unread sources behind a novelty claim: Bedekar et al. (2024), and McLane and Cecan (2009) and Schilling et al. (2017) marked "not read".
3. PRT uncited (03:11).
4. The open [check]s on code and data availability, and the five-layout scripts (05:23).
5. The main text over the stated 7,500.

The §6.5 F > 0.5 issue a reviewer would catch rather than the editor, but it is the one most likely to mislead a practitioner reader.

---

## Five most important changes

1. **Correct §6.5's F > 0.5 recommendation** (06:31 MUST). Call it a core, give the Neversink sizes (about 60 % of the PRT area, 43 % of the published cells), and pair it with the expected area. Add the between-sink caveat for F ≥ 0.1, the steady-model route to time-limited areas, and the stream treatment.
2. **Write or rename the nine missing SI sections** (SI MUST).
3. **Read Bedekar et al. (2024) in full**, and read or drop McLane and Cecan (2009) and Schilling et al. (2017) (01:9, 01:17 MUST). Restore the PRT citation (03:11 MUST).
4. **Cut to ≤ 7,500 words**, using cuts 1–12. Most are removals of repeats at no cost to the reader.
5. **Reduce the Neversink detail**: Fig. 9 to the SI, the §5.6 mechanisms and the §6.2 per-well counts to the SI. This keeps the paper read as a method with a benchmark.

## Counts

| file | MUST | SHOULD |
|---|---|---|
| 00_front | 0 | 1 |
| 01_introduction | 1 | 1 |
| 02_methods | 0 | 4 |
| 03_implementation | 1 | 1 |
| 04_verification | 0 | 1 |
| 05_neversink | 0 | 3 |
| 06_discussion | 1 | 9 |
| 07_limitations | 0 | 2 |
| 08_conclusions | 0 | 0 |
| 09_availability | 0 | 1 |
| display | 0 | 2 |
| si | 1 | 0 |
| length (§2 of this review; r1 W5 carried over) | 1 | 0 |
| **total** | **5** | **25** |
