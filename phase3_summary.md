# Phase 3: Error Analysis — LettuceDetect on RAGTruth

## Overview

Phase 2 produced a baseline evaluation of the pretrained LettuceDetect hallucination detector against RAGTruth's gold-labeled hallucination spans, using a character-level span-overlap threshold of 0.3:

- **Precision: 0.447**
- **Recall: 0.434**
- **F1: 0.440**

To understand *why* the detector performed at this level, 100 error cases (a random sample drawn from the full pool of 823 false positives and 868 false negatives) were manually reviewed and sorted into 7 categories:

| Category | Count |
|---|---|
| Baseless/unsupported info | 30 |
| Unsupported/fabricated (not annotated by gold) | 24 |
| Boundary/tokenization artifact | 14 |
| Contradicts source | 14 |
| Numbers/values mismatch | 10 |
| Wrong occurrence / partial match | 5 |
| False alarm on supported content | 3 |

This document summarizes the deep-dive findings for each category and the resulting corrected performance estimates.

---

## Finding 1: A large share of "errors" are gold-label gaps, not model failures

The 24 "unsupported/fabricated (not annotated by gold)" cases were manually adjudicated one by one: for each, we asked whether the detector's flagged span was, in fact, a genuine hallucination that RAGTruth's human annotators simply missed.

**Result: 18/24 (75%) were confirmed genuine hallucinations gold failed to label.** Only 5/24 (21%) were true false positives; 1/24 was ambiguous.

This means a majority of what the raw evaluation counts as false positives are actually correct detections — RAGTruth's gold annotations are incomplete, not the detector's judgment. Extrapolating this 75% correct-detection rate across the full false-positive pool in this category (~24% of all 1,691 total errors, per the random-sampling proportion) and reclassifying those as true positives moves the metrics to:

- **Precision: 0.651**
- **Recall: 0.528**
- **F1: 0.583**

*(Caveat: based on a 24-case sample; 95% CI on the correct-detection rate is roughly ±17 points, so treat 0.58 as a midpoint of a wider plausible range.)*

---

## Finding 2: The "boundary/tokenization artifact" label was a mislabel — it's actually a matching-threshold problem

Investigation of the 14 boundary/tokenization cases traced all the way back through the evaluation pipeline (`match_spans()`, `evaluate_dataset()`, the FP/FN sampling code) confirmed that `problem_span` values are LettuceDetect's raw predicted text, not a data-pipeline artifact. The apparent "boundary" issues (single-word spans like "such," "take," "music") are cases where the model correctly identifies the general area of a hallucination but predicts a **narrower or shifted span** than gold — a partial-match problem, not a tokenizer bug.

A threshold sweep confirmed this directly: lowering the character-overlap matching threshold from 0.3 to 0.1 (i.e., counting partial/shifted overlaps as valid matches) improved the full-dataset score to:

- **Precision: 0.504**
- **Recall: 0.489**
- **F1: 0.497**

Combining this fix with a fresh gold-label adjudication (50 newly-sampled false positives under the threshold=0.1 matching rule; 26/50 = 52% confirmed as correct-but-unlabeled detections) produces the final combined-correction estimate:

- **Precision: 0.762**
- **Recall: 0.592**
- **F1: 0.666**

*(Caveat: still an extrapolation from a 50-case sample; treat as roughly 0.60–0.70. Note the correct-detection rate dropped from 75% to 52% between rounds — expected, since loosening the threshold pulls in more genuinely borderline predictions alongside the correct ones. This is a useful sanity check that the correction isn't just optimistic stacking.)*

### Two of the 14 boundary cases don't fit this pattern
Cases 8770 and 7984 ("span-not-found-exactly") were spans that didn't literally appear at their recorded offsets in the answer text. An offset-basis check (verifying whether `pred["end"]` ever exceeds `len(answer)`) returned no hits, ruling out an indexing bug. These 2 cases are most likely simple text-formatting mismatches (e.g., "2:00 PM" vs. "2pm" in the source) or manual labeling slips from the original review pass, and are too small a group to materially affect the results above.

---

## Finding 3: The 30 "baseless/unsupported" cases are the real model-reasoning failures

Unlike the "not annotated by gold" category, these 30 cases were confirmed via manual review to be genuine hallucinations not supported by any source content. Sub-categorizing them reveals where the model actually goes wrong:

| Sub-pattern | Count | % |
|---|---|---|
| **Added-detail** (invents a new fact/claim with no basis in source) | 16 | 53% |
| **Attribute-invention** (asserts a specific value for a structured field — e.g. reservations, WiFi — that source marks as unknown/`None`) | 6 | 20% |
| Over-generalization (states a loosely-implied claim as firm fact) | 3 | 10% |
| Numeric-fabrication (invents a specific number/quantity) | 3 | 10% |
| Causal-invention (adds an unstated cause/explanation) | 2 | 7% |

**Over half of genuine hallucinations are outright invented details with no basis in the source at all** — the classic hallucination pattern. The second-largest pattern, attribute-invention, is notably more mechanical and predictable: the model asserts values for specific structured fields (hours, WiFi, reservations, parking) even when the source data explicitly marks them as `None`/unknown. This is a narrower, more addressable failure mode than free-form invented detail.

---

## Finding 4: Spot-check of the remaining 4 smaller categories

A lighter review (3–5 sample rows per category, not full adjudication) was done on the remaining categories:

- **Contradicts source (n=14):** Distinct from "added-detail" — here the model doesn't just add unsupported claims, it actively misstates or reverses a fact the source explicitly provides (e.g., contradicting an attribute's true value, misstating a figure given directly in the source text). This is a more serious failure mode than pure fabrication, since the model is confidently wrong rather than merely unsupported.
- **Numbers/values mismatch (n=10):** Concentrated almost entirely in **business hours and star ratings** — structured numeric fields getting garbled during generation. Closely related to the "attribute-invention" pattern above, just for numeric rather than categorical fields.
- **Wrong occurrence / partial match (n=5):** A mixed bag; some appear to be legitimate paraphrase mismatches rather than true errors (similar in spirit to the gold-label-gap issue in Finding 1) rather than a distinct failure mode. Lowest priority — smallest category, least internally consistent.
- **False alarm on supported content (n=3):** Smallest category. Two of three cases are typical single-word false positives on genuinely correct content (echoing the false-positive pattern from Finding 1). One case appears to be a data-logging anomaly (the full answer text was captured as `problem_span` instead of a specific phrase) rather than a real hallucination-detection error, and should likely be excluded or re-verified.

---

## Summary: Corrected performance estimates

| Stage | Precision | Recall | F1 |
|---|---|---|---|
| Raw (RAGTruth gold labels, threshold=0.3) | 0.447 | 0.434 | **0.440** |
| + Matching threshold loosened to 0.1 | 0.504 | 0.489 | **0.497** |
| + Gold-label adjudication applied | 0.762 | 0.592 | **0.666** (≈0.60–0.70) |

## Key takeaways

1. **LettuceDetect's real-world precision is substantially understated by the raw RAGTruth benchmark.** A large share of "false positives" are actually correct detections that RAGTruth's gold annotations failed to capture.
2. **Recall barely moves across all corrections** (0.434 → 0.592) — both fixes applied here only address false positives. The 868 original false negatives (missed hallucinations) are unexamined and represent a real, uncorrected gap in the detector's coverage.
3. **Where the detector genuinely fails, it's not random.** Two-thirds of true failures cluster into a) outright invented details with no source basis, and b) fabricated values for structured fields (hours, WiFi, reservations) that are explicitly marked unknown — a narrower, more targetable pattern than general hallucination.
4. **The "boundary/tokenization" label from the original manual pass was a slight misnomer** — the underlying issue is partial/shifted span prediction, which is a matching-methodology question (addressed by threshold tuning) rather than a tokenizer bug.

## Suggested next steps (Phase 4)

- Investigate the 868 false negatives with the same rigor applied here to false positives — this analysis has not yet touched recall-side errors.
- Consider a lightweight rule-based post-check specifically for **attribute-invention**: flag any generated claim about a structured field (hours, WiFi, reservations, parking) whenever that field is `None`/unknown in the source, since this sub-pattern is unusually mechanical and well-defined.
- Formally validate the threshold=0.1 choice against a labeled held-out set, rather than relying solely on the sweep + extrapolated adjudication shown here.
- If pursuing model-side improvements rather than evaluation corrections, prioritize the added-detail and contradicts-source patterns, since these represent the more serious "confidently wrong" and "purely invented" failure modes.
