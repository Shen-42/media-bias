# Summary: v1 (Phases 0–3)

Toronto crash coverage mostly describes the impact as something that happened to the pedestrian or cyclist, with a vehicle as the agent. Half of newsroom crash sentences are passives with an agent. When a driver or vehicle is named in the impact clause, it is the vehicle 83% of the time. "Accident" appears in under 1% of crash sentences. Full results are in `docs/writeup.md`.

## What was built

- Collection of CityNews Toronto, CTV News Toronto and Global News through sitemaps (January 2023 to October 2026), plus Toronto Police releases from the Wayback Machine. Rate-limited, robots.txt respected.
- Rule-based labeler for the grammatical labels (voice, driver reference, focus, pedestrian or cyclist as actor, "accident"), with a 312-template test suite.
- Quote detection and police-release matching, giving every crash sentence a `text_source` (quoted, police-matched, newsroom).
- Weak supervision for the two fuzzy labels: labeling functions (lexicon, NLI, local Qwen), a Snorkel label model and a SetFit end model.
- Aggregate tables with cluster-bootstrap intervals, and a Streamlit dashboard that runs locally.

## Corpus

979 in-scope articles and 3,126 crash sentences (codebook v1.1). Of the articles, 218 are linked to a police release. Four planned outlets were dropped (Toronto Sun, blogTO, Toronto Today, CBC). CTV covers 2025 onward only.

## Main results (newsroom text)

| Measure | Rate (95% CI) |
|---|---|
| Passive with agent | 51% (48–53) |
| No agent (agentless passive, intransitive, nominal) | 39% |
| Vehicle as agent, when a driver or vehicle is named | 83% |
| Focus on the pedestrian or cyclist | 63% (60–66) |
| "Accident" | 0.8% (0.3–1.4) |
| Articles that mention a driver (exceptional / ordinary) | 86% / 79%, intervals overlap |

- Police-matched sentences use the active voice about three times as often as newsroom sentences (30% vs 11%).
- Headlines lean further toward the victim than body text.
- No outlet differs from another: all intervals overlap.

## Evaluation

The test set has 240 sentences, labeled by a Claude Code subagent, not a human. Rules on random test rows score:

| Label | Accuracy | Macro-F1 |
|---|---|---|
| Voice | 0.98 | 0.96 |
| Driver reference | 0.90 | 0.85 |
| Focus | 0.85 | 0.57 |
| Text source | 0.90 | 0.85 |

Crash rows were relabeled under codebook v1.1 (8 of 100 test labels changed). After a dev-only rework (D-70, D-71), the Snorkel label model matches the Qwen labeling function for `thematic_cue` and `vru_conduct_detail` (macro-F1 0.81 and 0.83), but SetFit, the only model that labels the whole corpus, still trails (0.57 and 0.60). The article-level rates are not reported as findings. Kappa between two LLM annotators was 1.0 on 26 rows. That reflects one model reading one codebook, not independent agreement.

## Changes made during evaluation

The annotators found articles outside v1 scope in the sample: US wire stories on CityNews Toronto pages, car-only crashes, regional Global stories, and wrong police-release links. The scope and linking rules were tightened (D-54, D-56, D-58), which cut the corpus from 1,671 to 942 articles. Out-of-scope eval rows were replaced by new random draws (D-55). Codebook v1.1 then settled five gaps the annotators found (charge names, bare person nouns, general statements, emergency vehicles, separate car-only collisions; D-69); headline rates moved by under a point. Every change is in `DECISIONS.md`.

## Coverage note

Global's in-scope count drops sharply after mid-2024. Global stopped publishing routine Toronto crash briefs at that point; collection and filtering were checked and are not the cause (D-68).

## Open items

- Corpus-wide fuzzy-label rates need an end model that matches Snorkel; SetFit on MiniLM does not yet.
- Fevyer & Aldred (2022) could not be read, so it is not compared.

# Summary: v1.5 (bike lanes and transit)

v1.5 did not produce reportable stance or frame rates. The SetFit model labels a stance on 48% of sentences naming transit, while the annotated test sample has 1% (1 of 69; 95% CI 0–8%). Under codebook 9.2, a newsroom sentence that reports a position neutrally is `none`, and most transit coverage is service and project news. Full details are in the addendum to `docs/writeup.md`.

- Corpus: 1,167 Toronto articles (105 bike lane, 1,062 transit), 26,637 sentences.
- Topic precision on test: bike lane 0.97 (n = 29), transit 0.80 (n = 46), after dev-only fixes (D-76).
- Source-role accuracy on test: 0.62 (n = 53); 32% of quote units get `unknown` (D-77).
- Frames in 75 random annotated sentences: no policy content 49%, `other` 15%, quality of life 13%, economic 12%, safety, political and legality 3–5% each.
- Model ranking on test frames: Snorkel (accuracy 0.60) > NLI (0.55) > Qwen (0.52) > SetFit (0.45). Dev gave the same order.
- Open item for the author: whether to count positions held by sources (attributed stance), which would change codebook 9.2 (D-80).
