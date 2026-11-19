# Method

## Corpus

- **Outlets:** CityNews Toronto, CTV News Toronto, Global News. The Toronto Sun, blogTO, Toronto Today and CBC were excluded (terms of use, blocked scripted access, or an unreachable robots.txt). CTV's sitemaps start in 2025, so CTV covers a shorter window.
- **Window:** 2023-01-01 to 2026-10-31.
- **Discovery:** outlet sitemaps filtered by URL slug. Slugs naming a pedestrian, cyclist or strike construction were fetched first; slugs with only "crash" or "collision" second.
- **In scope:** a motor vehicle struck at least one pedestrian or cyclist in Toronto, fatal or non-fatal (codebook §0).
- **Wire copy:** near-duplicate bodies (MinHash, Jaccard ≥ 0.7) form wire groups. Body sentences count once at corpus level. Per-outlet rates are shown with and without wire stories.
- **Article type:** primary analysis uses each outlet's first report of a crash. Follow-ups are reported separately. Roundups are excluded.

## Police releases

Toronto Police news releases come from Wayback Machine copies only; the TPS site blocks scripted access. Releases are public government records, not commercial content, and the project publishes no release text beyond short excerpts. Wayback copies of blogTO and Toronto Today were not used: they are commercial outlets whose live sites block scripted access, and using archive copies would get around that choice (D-46). About 42% of release IDs in the window are archived, so the police comparison is a secondary analysis on the subset of articles linked to an archived release. A bias check compares linked and unlinked articles.

An article is linked to a release when the dates are close and they share street names. Each article sentence is compared with the release sentences by embedding similarity (all-mpnet-base-v2) and character 5-gram overlap. Thresholds were tuned on the dev set only.

## Labels

- **Grammatical labels** (voice, driver reference, grammatical subject, VRU as actor, "accident"): spaCy dependency rules on `en_core_web_trf` parses, computed on the main impact clause. These rules are the reported system. A template suite of 312 constructed sentences checks them in CI; that is a unit test, not an accuracy result.
- **Fuzzy labels** (VRU conduct detail, thematic cue): five labeling functions each (lexicon, two negative heuristics, zero-shot NLI, Qwen3 4B via local Ollama) → Snorkel label model → SetFit (all-MiniLM-L6-v2) trained on confident Snorkel labels.
- **Text source:** quoted (direct speech) > police-matched > newsroom. Framing rates are reported for each separately.
- **Article labels:** driver ever mentioned (coreference + role nouns), reported split by exceptional driver behaviour (fled, impaired, Criminal Code charge, racing); thematic frame; conduct details; police overlap.

## Evaluation

- Test set: 100 crash sentences (60 random, 40 picked where rules, NLI and Qwen disagree) and 100 body sentences for the fuzzy labels (same split), plus 40 sentences for text source. Headline metrics use random rows only.
- Dev set: 30 + 30 + 40 sentences, used only for tuning.
- **Labels came from an LLM annotator (a Claude Code subagent), not a human.** A second LLM annotator labeled 30 test sentences for Cohen's kappa.
- Every labeling function, the Snorkel label model and the SetFit model are scored on the same test rows.

## Reporting

Rates come with 95% bootstrap intervals, resampling articles. Outlets are not ranked, and no difference is claimed where intervals overlap.

Coverage is uneven (D-45). Outlet comparisons use only the window all three outlets cover, because CTV starts in 2025. Trends over time are shown within each outlet and never pooled. Before/after Bill 212 (royal assent 2024-11-25) is compared only for outlets with articles on both sides.
