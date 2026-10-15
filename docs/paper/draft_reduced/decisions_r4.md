# Orchestrator decisions after the round-4 reviews

These decisions apply on top of decisions_r3.md. The reviews are `reviews/r4_content.md`, `r4_style.md` and `r4_reader.md`. In your files, apply:
- every MUST;
- every SHOULD that doesn't conflict with these decisions;
- the PARTLY items of r4_reader's comment table that fall in your sections.

## A. The Neversink headline claim (A, D, E): honest framing
1. **Drop "full mixing lies within the spread/range of particle results"** everywhere: abstract, §5, §6 and §8. That claim rests on two particle runs that do not conserve water:
   - particles that lose weight only at wells deliver 2.6 times the inflow;
   - water-table release delivers 66 %.
   
   Particle runs that conserve water give overlaps of 0.62–0.998, depending on settings. Full mixing gives 0.30–0.41. Say this plainly.
2. **Replace the claim with what the evidence supports** (verify each number against its evidence file before use):
   - Particle settings alone move the overlap with the published area from about 0.65 (MODFLOW 6 defaults) to 0.998 (published settings).
   - Full mixing agrees less (0.30–0.41). The main reason is that full mixing splits each cell's water over all its outflows, where a particle follows one path, so its areas are wider and more diffuse.
   - The particle runs that lose weight at sinks, the like-for-like test, show this mixing effect between sinks. The F > 0.1 area holds 87 % of their area, and the F > 0.5 area 59 %.
   - For a protection zone, the F > 0.1 area contains 73 % of the published area. It misses 27 %.
3. **Name the low-end runs once in §5.3** (one sentence each, or one sentence for both) so the reader knows the 0.29–0.39 runs lose or gain water. Then compare only water-conserving runs in the headline.
4. **The abstract's Neversink sentence** says what was compared:
   - full-mixing areas against the published particle-tracked areas of a regional model;
   - the agreement (overlap 0.30–0.41 against 0.65–0.998 for particle runs with different settings);
   - and why: full mixing spreads water over more cells.
   
   Keep it to two sentences. The trace time (2–3 s on 1.68 million cells) stays.

## B. Transient results (A, C, E)
5. The 81 % stored-water result is from **forward** transient tracking, and a GWT run gives it too. Don't credit it to backward tracking in time.
   - The product only backward tracking in time gives is the **time-limited area** (e.g. the 30-year area of Fig. 4d).
   - Put that in the abstract and in §1's contributions.
   - The 81 % may stay in the abstract as a transient-tracking result, if words allow.
6. **"Particles do not give the stored-water share":** cite Environment Agency 2019, Appendix C4.3 (backward particle tracking through transient flows is awkward to set up and interpret), or soften the claim to what that source says (04:45, 01:7).

## C. Consistency (all)
7. **Weak sink** is a cell whose sink terms take only part of the cell's outflow. Use that definition, in §1 only. §2.3 refers back.
8. **Define "trace" once**, in §1 or at the start of §2: one solve for one set of destination or source groups.
   - Define "destination group" before §2.2 uses it.
9. **Define F once in plain words (§1) and once formally (§2.2).** Later sections refer back ("F, the share of a cell's water that ends at the well").
   - Do this at most once per section, and only where a reader may have jumped in (§4.3, §5.2).
   - Delete other redefinitions. Apply the same rule to full mixing, snapshots, overlap and weak sink.
10. **The number of checks:**
    - §2.5 names the checks and gives their count.
    - §1 and the abstract use the same count, or say "budget checks" without a number.
11. **Snapshots have "no travel lag"** (not "no travel time").
12. **Stream share:**
    - 43 % is the calibrated model;
    - 42 % is the median over realisations at base pumping.
    
    Say which is which.
13. **357 published areas vs 358 realisations:** one clause in §5.5 giving the reason (from the evidence, NS §6 or si/D), or move it to the SI.
14. **Flow loops:**
    - remove "around a pair of wells" (01:11);
    - the causes are XT3D and two-way stream–aquifer exchange;
    - add, fairly, that Foley and Black (2013) treat loops as rare artefacts of unstable models whose removal changes little, if their text says so (check the text copy in /Users/ruihugman/GitHub/gw-source/references/docs/text/).
15. **Broken "Section 4.4" pointers** at 02:83, 06:23 and 06:43: point them to where the material now lives (Section 3.2 or the SI item on transient checks of the seasonal example model).
16. **§9:**
    - the eight-cell example lives in a figure script, not a tutorial;
    - say "the example models and test models ship with the code";
    - name the tutorials only for the ones that are tutorials.
17. **3.3 memory:**
    - "about 20 GB for 100 wells" is an estimate for 100 groups in one trace, not a run;
    - hedge it ("we estimate").

## D. Prose (all): from r4_style
18. **Allowed and encouraged:** "because", "so that", "but", "which" when it joins one idea, not two.
    - Staccato lists of short sentences (abstract, 01:19, 02:81, 08:3) read as badly as packed ones.
    - Aim for varied, natural sentences that each carry one idea.
19. **No appositive packing** ("X, the share of …, does Y"). Define in its own sentence, or after the verb.
20. **No paragraph openers that are rhetorical questions**, at most one in the whole paper.
    - No announcements ("Three outcomes frame this discussion.", "Five pieces of advice follow.").
    - Vary closers: no "therefore" or "a user can" closers in more than one paragraph per section.
21. **"In words:" only after a numbered equation**, and always as a full sentence. No "In words:" fragments.
22. **No participle openers** ("Traced backward from …", "Rerun with …").

## E. Section-specific (from r4_reader and r4_content)
23. **§5.3, paragraph 05:33 (the hardest in the paper):**
    - put the conclusion first;
    - then the evidence;
    - then the caveats in one sentence;
    - "covers" becomes "holds 87 % of".
24. **§5.5:**
    - the published area changes between realisations because the same particle settings act on each realisation's flows (where particles stop), while the water reaching the wells (sum of F) barely changes;
    - say what each correlation is between.
25. **§5.6:** give "4.76 → 3.83" its context or move it to the SI. Mention the stream-network curve in Fig. 9 in one sentence, or remove it from the figure description.
26. **§6.5 item 1:** give a rule for choosing an area, from the evidence:
    - with cells of 50 m or less, the F > 0.5 area is stable to grid size (§4.3);
    - the F > 0.1 area is the cautious choice, but on Neversink it still missed 27 % of the published area, so add a particle check where it ends at a weak sink.
    
    Drop "take the size from the expected area" unless it can be said how.
    
    Also add short advice, only where the evidence supports it, on:
    - which layer to map (the start cells, §5.1);
    - ensembles (mean F over realisations, §5.5);
    - what to report with a zone (accounting, stream representation, threshold, closure).
    
    No advice without evidence.
27. **§6.4 merges into §6.5's stream item**, or is cut to what §5.4 doesn't already say.
28. **§8:** the first sentence is what this work provides (open code, checks, transient tracking, speed). FlowSource appears in the second or third sentence, as the method we build on.
29. **§1:** end the Bedekar paragraph and the adjoint paragraph on their own topic. Move the general gap statement into the contributions paragraph.
30. **§2:**
    - cut to 2,000 words;
    - the loop solve gets one technical sentence (decision r3-15);
    - move the rest to si/B.md.

## F. Figures and captions
31. **Fig. 2 (C):**
    - the markers include the Foley and Black (2013) example and a hand-built 15-cell network, not only test models;
    - say so;
    - say that a check can have a different tolerance for some models (two rows have two bars).
32. **Fig. 4 (C):**
    - say the dashed line is the river and why F extends east of it;
    - explain why the caption gives 95 % for year 1 while the panel shows 98 %, or give the panel's number.
33. **Fig. 6 (D):** "pale area south-east of the U wells" becomes the colour class it now is (F 0.1–0.25).
34. **Fig. 7 and Fig. 8:** a figure agent will:
    - rename Fig. 7's "plain particles" row to "particles losing weight only at wells";
    - redraw Fig. 8 with the Fig. 6 colour map.
    
    D updates the captions once docs/paper/figures/README.md says so.
35. **The lost result:** 89 missed cells receiving 6 % of the particle water (227 of 3,736 m³/d). Put it back in §5.3 or in si/E or si/D with its evidence.

## G. Length
36. **The main text cap stays at 8,500 words.** Every addition needs a cut. Take cuts from:
    - the r4_reader and r4_style cut lists;
    - repeated definitions;
    - repeated purpose paragraphs (05:3 and 05:25);
    - numbers repeated in §6.
