# Orchestrator decisions after review round 2

These decisions apply on top of decisions_r1.md. The reviews are in `reviews/r2_content.md`, `r2_voice.md` and `r2_reader.md`. Apply every round 2 MUST in your files, and the SHOULDs that don't conflict with the decisions below.

## Length
1. The main text must be at most 7,500 words. It is now 7,652 (r2_reader).
   - Take the ranked cuts in r2_reader that fall in your sections, starting with repeats.
   - Section budgets from decisions_r1 are now hard limits, except §6: §6 may reach 1,150 words if §5 drops to 1,300.

## SI placeholders
2. Use the exact SI names in `si/numbering.md`, the editor's plan, including its merges. Do not add new SI names. If you move more material out, put it under an existing name, or tell me.
3. Material the cuts dropped (open-top stream cells, narrow particle paths) either lives in an SI item or is not cited from the text. Fix 07:7, which cites §5.5 for the narrow-paths reading that §5.5 no longer holds.

## Acronyms and terms
4. Write "MODFLOW 6" in full throughout; drop "MF6".
   - GWT, GWF and SFR are defined once, in §1, and not again.
   - XT3D is spelled out at its first use, in §2.
   - iES is spelled out at first use.
5. Use "Area" for a threshold area. "Zone" is only for the analytical capture zone, selection by zone, and "protection zone" as the regulatory product.
6. Write "published contributing cells", not "published cells".
7. Numbers:
   - Use "2–3 s" style for ranges.
   - Put a thousands comma in numbers of 1,000 and above (9,574 d).
   - Write numbers below 10 in words unless a unit follows.

## §6.5 guidance (writer E)
8. State the hedge once at the start ("From these tests we would draw a protection zone as follows."), then write plain statements. Don't repeat "We would".
9. Call F > 0.5 the **core area**, not the "single best estimate". Give what it holds on Neversink from the §5.3 numbers. r2_reader's "about 60 % of the PRT area" is that reviewer's own calculation: check it against the evidence file before using it.
10. Say that F ≥ 0.1 can miss cells between sinks, not only at weak sinks.
11. Time-limited areas come from backward tracking in time over the flow periods. Say in one sentence how this applies to a steady model (repeat the steady flow over transient steps; §4.1, model 10 in equal steps) only if the evidence supports it. Otherwise mark it [check].
12. Stream treatment: give a recommendation only if §5 evidence supports one. Otherwise say it is a model choice that changes the area, and cite §5.3.

## Content fixes (r2_content)
13. **04:25:** make it "where no method meets a weak sink", as the dispersion study says.
14. **Net accounting numbers:**
    - Reconcile the group trace (978) with the per-well sum (1,104) at 06:15, and fix "only in sum".
    - Fix si/D:22: 3,944 m³/d is the group's credited flow, not per-well throughflow (that sums to 4,621).
    - Move the per-well counts in §6.2 to the SI item for per-well gross and net. Keep one sentence in §6.2 with the pattern and the two exceptions (r2_reader, method-first).
15. **06:19:** "only transient tracking answers" over-claims, because a GWT run with tagged initial water also answers. Say instead that transient tracking answers it from one flow run, for every source at once, with no transport run.
16. **06:31:** change "(§2.3)" to "(§2.4; Table 1)".
17. **03:11:** restore [check: PRT documentation].

## Unread sources
18. The novelty claim (backward tracking in time) covers only the methods we read. Keep the wording "We found no…" in §1. Mark Bedekar et al. (2024) "[check: abstract only]", McLane and Cecan (2009) and Schilling et al. (2017) "[check: not read]". The author may supply the full texts.

## Neversink weight (r2_reader 5)
19. §5.6 keeps the growth result in two sentences or fewer and points to the SI for the mechanism. Fig. 9 stays in the main text with a short caption.
