# Author's comments on draft v6 (2026-10-13)

The author's 55 comments on the published draft, grouped by section. The quoted text is what each comment was anchored to. Every comment must be addressed in round 4; `decisions_r3.md` says how.

## Title, impact statement, abstract (writer A)
- Title: "Titles should be about what the tool provides, not what it is."
- "Contributing areas of supply wells are usually delineated by particle tracking, which needs a stop-or-pass rule at every weak sink.": "Pretty hard start to the abstract. Should be an opener aimed at the non-technical reader framing the use of these approaches."
- "We write it as one sparse linear system per direction, solved exactly.": "'We do bla bla, by bla bla' is Claude-ish. No one speaks or writes like this."
- "exact identities": "Non-technical readers will not know what this means."
- "but has not been described in a journal article and has no open implementation": "Harsh and impolite. No need to say it is not published; just say it is not open source, and what it does versus what we do. Frame it as the value we add to existing methods."
- "On a seasonal test model, 81 % of the water pumped in the first ten years had been in the aquifer at the start.": "Weird sentence here in the middle of the abstract."
- "On the USGS Neversink/Rondout model (1.68 million cells) a trace takes 2–3 s. Compared with the published particle-tracked contributing areas, full mixing lies within the spread …": "Seems jumbled. The point is we compared to Neversink? Plus it was faster?"

## 1. Introduction (writer A)
- Whole section: "There seems a lack of flow in this whole Introduction; these paragraphs in particular. Perhaps relax the target word count so it can be structured logically."
- "Particle tracking (Pollock 1988, 2016) is the standard tool, and one forward run serves every well.": "Two-part sentences: hallmark of LLM writing."
- Same paragraph: "A paragraph introducing all of the methods first, before each of the detailed paragraphs, would make it easier for the reader to keep a bird's-eye view of where we are going."
- "A weak sink is a cell whose sink term … In transient models, particles do not directly give the share …": "Feels like it's missing a chaining thought. Why are we talking about weak sinks?"
- "The destination is the set of sink terms traced to, such as a well's pumping;": "Weird sentence structure."
- "These fractions are not capture fractions, the share of a well's pumping supplied by increased recharge or reduced discharge (Leake et al. 2010; Barlow et al. 2018); they follow water along the flows of a single run.": "Needs to be clearer what they are, and how they are not the 'capture fractions' of Leake."
- MODALL paragraph: "...frequently..." (meaning unclear; asked the author. Leave as is unless the rewrite makes it moot.)
- "The FlowSource method (Table 1) is described in two conference papers …; we f…": "This paragraph lands flat here suddenly. It needs to be woven into the coherent story of the intro."

## 2. Methods (writer B)
- Fig. 1: "Very busy figure. Don't refer to 'tutorial' models in a figure; you can say in the text it comes from one of the tutorials if you like." (figure agent F1 redraws; writer B rewrites the caption)
- Eq. (1): "missing eq?" (the per-cell rule above it and the §2.1 budget equation are unnumbered, so Eq. 1 looks like it is missing a predecessor)
- §2.3 "Net accounting is the bookkeeping of FlowSource": "Weird sentence."
- §2.3 "in the accounting tutorial (tutorial 02; Section 9)": "Readers of a paper have no idea what tutorial is being referred to. You can say 'example' if it is described in the paper; you can say these are included as tutorials in the software repository."
- §2.4 "flow loops": "First mention of flow loops? The reader will not know what this is about or why it matters."
- §2.4 "For the specialist,": "Weird wording."
- §2.7 Snapshots: "Probably makes sense to merge into 2.8, explaining that that is how existing methods work, and our enhancement."
- §2.8 "The cell budget error leaves at the cell's own fraction, the flow-error correction of GWT (Langevin et al. 2022).": "Not clear."
- §2.9: "well" → "sink".

## 3–4. Implementation and verification (writer C)
- §3.2 PRT paragraph: "This shows up out of the blue. Why are we talking about PRT? This will be unclear to the reader."
- §3.3 heading "Cost": "compute cost"; its text: "RAM?"
- §4.1 "The ten test models are small MODFLOW 6 …": "Readers will want to know more details; include as supplementary material?"
- Fig. 2: "Noisy and complex figure; readers will need guidance in the prose on how to read it." Caption word "identities": "What is an 'identity'?"
- §4.1 "Weight-losing PRT particles": "This has not been adequately explained."
- §4.2 "… holds by construction": "Weird writing style."
- §4.2 "On model 10, c at the end matched the steady G to 9.7 × 10⁻¹⁴ …": "The reader needs to be told why this is important for them to know."
- §4.3 "Thresholds here are non-strict (F ≥ 0.1); Section 5 uses strict ones (F > 0.1).": "Reader doesn't know what this means; what's F, why do I care, what does it mean."
- §4.4 "Tutorial 08 is a synthetic, one-layer model …": "Reader doesn't know about tutorials; the paper is independent of the repo. This should be described, perhaps in supplementary material. The reader needs enough context in the paper body to understand the figures and why it matters."

## 5. Neversink (writer D)
- §5.2 "The overlap, the cells in both areas as a share of those in either (the Jaccard index), measures agreement …": "Hard to follow. Seems like you are condensing words to keep the word count down, but that makes it hard to understand. Clear, explicit explanation of uncommon concepts for hydrogeologists."
- §5.2 "is a core": "What does that mean?"
- Fig. 6: "Blue colormap is hard to read; prefer a colormap that distinguishes the gradient better." and "Include stream and well locations? Share x/y axes across rows/columns?" (figure agent F6)
- §5.3 "Text S6)": "What does this mean?" (SI cross-references are unexplained to the reader)
- §5.3 "Plain particles,": "What are plain particles? Why are we discussing this? The reader needs to be told."
- §5.3 heading: "I don't understand this section. Shouldn't we only be comparing to the published convention? Why are we doing this analysis?"
- §5.5 "in 76 min on six processes, with closure to 3 × 10⁻¹² m³/d in each.": "Unnecessary."
- §5.5 (inferred location): "Confusing; what's being compared? Why does it matter? Why is it different?"
- §5.6 "PRT with the published conventions reproduces the published growth (3.62 against 3.60, 61 realisations), which is slower mainly because …": "Needs a bit more context for the reader."

## 6–8. Discussion, limitations, conclusions (writer E)
- §6 opening "For transient flow the guidance below rests on synthetic models …": "Hedging. Instead, start with a general framing of the outcomes for discussion."
- §6.1 "published contributing cells": "for Neversink..." (say whose published cells)
- §6.3 "Snapshots say where a time step's water enters under that step's flows, in seconds and without porosity.": "Two-part sentences; I don't like."
- §6.3 "tutorial 08,": "Do not use tutorial refs in the paper; either describe in supplementary material or let's work out how we reference them."
- §6.5 "From these tests we would draw a protection zone as follows. The F > 0.5 area is the core area …": "This is incomprehensible." and "The text doesn't give any advice after this statement??"
- §6.5 heading: "This section is terrible; it reads as a repeat of results; there is no discussion here."
- §7 heading: "This should be limitations of the method, not specifically the paper."
- §8 heading: "Don't start this off as 'we did the other guys' work differently'. Go for: we extended their implementation to do x, y, z, faster, handling weak sinks, all the boundary types, networks, etc., and open source."
- §8 "On Neversink, full mixing lies within the spread of particle results …": "Make this generic: 'tested against a published real-world model'."
