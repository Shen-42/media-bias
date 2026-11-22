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
- Against police records (City of Toronto KSI data), 26% (23–30) of pedestrian and cyclist crashes that killed or seriously injured someone got an initial report in the corpus: 53% of fatal and 21% of serious-injury crashes. On 257 linked reports, `road_users` agreed with police on 98% and `severity` on 90%; most severity disagreements are victims who died after the first report (D-95).

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

Positions on bike lanes and transit in Toronto news almost always belong to sources, not to the outlets: 7 of 511 annotated sentences with a stated position give it as the outlet's own claim. Sources' positions on bike lanes are common: 68% (61–76) of quoted sentences that name bike infrastructure, 52% (46–58) of attributed sentences and 28% (23–33) of other newsroom sentences, split about 3 to 2 between support and oppose. Transit positions are rarer and almost all support: 26% (17–35) of quoted transit sentences and 4–6% of newsroom sentences. Rates come from an annotated measurement sample of 1,601 in-scope sentences (D-85). Full details are in the addendum to `docs/writeup.md`.

- Corpus: 1,149 Toronto articles tagged bike lane or transit, 26,208 sentences.
- Measurement sample: every body sentence naming bike infrastructure or cyclists (1,014) and about 200 random transit sentences per outlet (588). Second-annotator kappa: infrastructure stance 0.94, transit stance 1.0, frame 0.76 (n = 100).
- Outlets: CityNews bike-lane sentences carry a source's position more often than at least one other outlet in each text type (quoted 80% vs CTV 54%; attributed 64% vs Global 39%; newsroom 34% vs CTV 18%). Transit intervals all overlap. No outlet differs in its own stated positions (0–1%).
- Bill 212 periods: stance differences across periods are near chance (10 of 135 comparisons) and are not reported as a finding.
- Frames (annotated, D-90): bike-lane newsroom sentences are framed mostly as law (39%) and politics (26%); quotes frame them by safety (20%) and quality of life (21%). Legal framing rose from 19–33% before the law to 47–64% while it was in force and in court. Outlets do not differ.
- Components on test: topic precision bike lane 0.97 (n = 29), transit 0.82 (n = 45); attribution precision 0.93, recall 0.73 (n = 150); source-role accuracy 0.60 (n = 53).
- Models: no stance model passed validation. A SetFit transit model retrained on the real class mix (D-86) matched annotated rates overall and per outlet but missed the newsroom rate (1.6% against 2.1–8.0%), failing a pass rule set before scoring (D-88). Snorkel overstates stance. Frames are reported from annotations too; the best frame model reached macro-F1 0.51.
