# Summary: v1 (Phases 0–3)

Toronto crash coverage mostly describes the impact as something that happened to the pedestrian or cyclist, with a vehicle as the agent. Half of newsroom crash sentences are passives with an agent. When a driver or vehicle is named in the impact clause, it is the vehicle 84% of the time. "Accident" appears in under 1% of crash sentences. Full results are in `docs/writeup.md`.

## What was built

- Collection of CityNews Toronto, CTV News Toronto and Global News through sitemaps (January 2023 to October 2026), plus Toronto Police releases from the Wayback Machine. Rate-limited, robots.txt respected.
- Rule-based labeler for the grammatical labels (voice, driver reference, focus, pedestrian or cyclist as actor, "accident"), with a 312-template test suite.
- Quote detection and police-release matching, giving every crash sentence a `text_source` (quoted, police-matched, newsroom).
- Weak supervision for the two fuzzy labels: labeling functions (lexicon, NLI, local Qwen), a Snorkel label model and a SetFit end model.
- Aggregate tables with cluster-bootstrap intervals, and a Streamlit dashboard that runs locally.

## Corpus

942 in-scope articles and 3,114 crash sentences. Of the articles, 218 are linked to a police release. Four planned outlets were dropped (Toronto Sun, blogTO, Toronto Today, CBC). CTV covers 2025 onward only.

## Main results (newsroom text)

| Measure | Rate (95% CI) |
|---|---|
| Passive with agent | 50% (48–53) |
| No agent (agentless passive, intransitive, nominal) | 39% |
| Vehicle as agent, when a driver or vehicle is named | 84% |
| Focus on the pedestrian or cyclist | 63% (60–66) |
| "Accident" | 0.9% (0.4–1.5) |
| Articles that mention a driver (exceptional / ordinary) | 87% / 80%, intervals overlap |

- Police-matched sentences use the active voice about three times as often as newsroom sentences (31% vs 10%).
- Headlines lean further toward the victim than body text.
- No outlet differs from another: all intervals overlap.

## Evaluation

The test set has 240 sentences, labeled by a Claude Code subagent, not a human. Rules on random test rows score:

| Label | Accuracy | Macro-F1 |
|---|---|---|
| Voice | 0.98 | 0.97 |
| Driver reference | 0.90 | 0.85 |
| Focus | 0.86 | 0.61 |
| Text source | 0.90 | 0.85 |

The Snorkel and SetFit models for `thematic_cue` and `vru_conduct_detail` did worse than single labeling functions. Their article-level rates are not reported as findings. Kappa between two LLM annotators was 1.0 on 26 rows. That reflects one model reading one codebook, not independent agreement.

## Changes made during evaluation

The annotators found articles outside v1 scope in the sample: US wire stories on CityNews Toronto pages, car-only crashes, regional Global stories, and wrong police-release links. The scope and linking rules were tightened (D-54, D-56, D-58), which cut the corpus from 1,671 to 942 articles. Out-of-scope eval rows were replaced by new random draws (D-55). Every change is in `DECISIONS.md`.

## Open items

- Global's in-scope count drops sharply after mid-2024; the cause was not traced.
- The codebook has gaps the annotators found: charge names with "accident", a bare "man" or "woman" who was struck, general statements about crashes, and emergency vehicles. Settling them needs a codebook revision and relabeling.
- The fuzzy-label models need work on the dev set before their rates can be used.
- Fevyer & Aldred (2022) could not be read, so it is not compared.
