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

When a Toronto news sentence names transit, 9% (95% CI 6–13%, n = 207) take a position on it, nearly all support. The positions come mostly from sources: 18% of quoted sentences and 14% of attributed newsroom sentences, against 3% of the outlet's own text. Bike infrastructure sentences take a position more often (48%, 28–68), from only 21 sentences. These rates come from annotated random samples. Stance counts a source's stated position (codebook 9.2, revised by the author, D-81). Full details are in the addendum to `docs/writeup.md`.

- Corpus: 1,167 Toronto articles (105 bike lane, 1,062 transit), 26,637 sentences.
- Topic precision on test: bike lane 0.97 (n = 29), transit 0.80 (n = 46). Source-role accuracy: 0.62 (n = 53).
- Frames in 75 random annotated sentences: no policy content 49%, `other` 15%, quality of life 13%, economic 12%, safety, political and legality 3–5% each.
- Models: the Snorkel label model is the best system on dev and test (frame accuracy 0.64; transit stance 0.88 on dev), but it overstates stance about 2× (transit 18% vs 9%). Its tables show where stance sits, not how much. SetFit failed validation for both frames and stance (D-80, D-84).
- Not possible with these samples: outlet comparisons and Bill 212 period comparisons.
