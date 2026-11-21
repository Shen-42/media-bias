# How Toronto news frames crashes involving pedestrians and cyclists

Toronto crash coverage usually describes the impact so that it happens to the pedestrian or cyclist, with a vehicle rather than a person as the agent. In 1,687 newsroom-written crash sentences, 51% are passives with an agent ("a pedestrian was struck by a vehicle"). Where a driver or vehicle appears in the impact clause, 83% of the time it is the vehicle. The word "accident" is almost absent (under 1% of crash sentences). These patterns are close to those Ralph et al. (2019) found in US local news, except for "accident", which they found in 47% of body sentences.

All rates come from rule-based labels (codebook v1.1) on 979 in-scope articles (3,126 crash sentences) from CityNews Toronto, CTV News Toronto and Global News, January 2023 to October 2026. Intervals are 95% bootstrap intervals over articles. The test labels behind every accuracy figure came from an LLM annotator, not a human (see Evaluation).

## Coverage

In-scope crash articles per outlet per quarter (`analysis/tables/coverage_by_quarter.csv`):

| Quarter | CityNews | CTV | Global |
|---|---|---|---|
| 2023Q1 | 28 | 0 | 31 |
| 2023Q2 | 22 | 0 | 42 |
| 2023Q3 | 35 | 0 | 37 |
| 2023Q4 | 33 | 0 | 31 |
| 2024Q1 | 24 | 0 | 17 |
| 2024Q2 | 26 | 0 | 20 |
| 2024Q3 | 23 | 0 | 5 |
| 2024Q4 | 37 | 0 | 3 |
| 2025Q1 | 22 | 22 | 4 |
| 2025Q2 | 32 | 38 | 3 |
| 2025Q3 | 48 | 53 | 4 |
| 2025Q4 | 38 | 38 | 9 |
| 2026Q1 | 26 | 38 | 2 |
| 2026Q2 | 32 | 39 | 9 |
| 2026Q3 | 34 | 45 | 6 |
| 2026Q4 | 8 | 13 | 2 |

Coverage is uneven. CTV's sitemaps start in 2025. Global's in-scope count falls from about 30 a quarter to under 10 after mid-2024, because Global stopped running routine Toronto crash briefs (see Limitations). Outlet comparisons use only the window all three outlets cover (2025-01-14 to 2026-10-29), which holds only 31 Global articles. Trends are reported within each outlet. The before/after Bill 212 comparison uses only outlets with articles on both sides of 2024-11-25.

## Key results

Crash-sentence rates by text source (`overall_by_text_source.csv`). Quoted text is scored separately and left out here.

| Measure | Newsroom (n = 1,687) | Police-matched (n = 112) |
|---|---|---|
| Passive with agent | 51% (48–53) | 29% (20–38) |
| Agentless passive | 12% (10–13) | 13% (8–20) |
| Active | 11% (9–12) | 30% (22–39) |
| Nominal ("the crash") | 23% (21–26) | 20% (12–28) |
| Intransitive | 4% (3–5) | 8% (3–14) |
| Driver as vehicle | 60% (57–62) | 35% (26–44) |
| Driver as person | 12% (10–14) | 17% (10–25) |
| Driver absent | 28% (26–30) | 48% (39–57) |
| Focus on pedestrian or cyclist | 63% (60–66) | 48% (39–58) |
| Pedestrian or cyclist as actor | 0.6% (0.2–1.1) | 1.8% (0–4.5) |
| "Accident" | 0.8% (0.3–1.4) | 0% |

- **Newsroom text vs police-matched text.** Sentences that closely restate a Toronto Police release use the active voice about three times as often as newsroom sentences, and name the vehicle as agent less often. The intervals do not overlap. Police-matched sentences come from 81 of the articles linked to a release, and those articles differ from unlinked ones (more fatal, more hit-and-run, more 2023; `matched_vs_unmatched.csv`), so this is a comparison within that subset.
- **Headlines vs body.** Headlines lean further toward the pedestrian or cyclist: 65% are passives with an agent (body 49%), 81% focus on the pedestrian or cyclist (body 62%), and 3% are active (body 12%). The intervals do not overlap (`headline_vs_body.csv`).
- **Initial reports vs follow-ups.** Follow-ups are more often active (23% vs 12%) and name the vehicle as agent less often (33% vs 58%) (`initial_vs_follow_up.csv`).
- **Fatal vs non-fatal.** Fatal crash sentences name the vehicle as agent somewhat less often (52% vs 61%) and focus on the victim less often (55% vs 65%) (`fatal_vs_nonfatal.csv`).
- **Driver mentioned anywhere in the article.** 80% of articles (78–83) mention a driver in newsroom or police-matched text. Split by `driver_exceptional`: 86% (80–91) when the driver fled, was impaired or was charged, and 79% (76–82) otherwise. The intervals overlap, so this corpus does not show the "rogue driver" gap that Fevyer & Aldred (2022) describe. Counting quoted text adds under one point to each.
- **Outlets.** In the common window, all outlet intervals overlap on every grammatical measure (`outlet_without_wire.csv`, `outlet_headlines.csv`). The closest case is driver as vehicle in body text: CityNews 63% (58–67), CTV 52% (47–57). This report does not claim any outlet differs from another.
- **Bill 212.** Within CityNews and within Global, pre- and post-cutoff intervals overlap on every grammatical measure (`bill212_pre_post_by_outlet.csv`). The comparison is descriptive.

**Pooled tables lean toward CityNews.** In every pooled table (text source, headline vs body, fatal vs non-fatal, initial vs follow-up, exceptional vs ordinary driver, article-level rates), CityNews supplies the most units: 48–50% of sentences and 48–49% of articles (`pooled_sample_shares.csv`). CTV supplies 26–29% and Global 23–25%. Each pooled table has a per-outlet breakdown of the same sample (`*_by_outlet.csv`). These breakdowns decompose the pooled figure; they are not outlet comparisons.

**Two article labels are not reported as findings.** The model behind `thematic_frame` (91% of articles) and `vru_conduct_any` (49%) scored poorly on the test set (see Evaluation), and both rates are far above the prior study. They are in the tables for completeness only.

## Methods

See `docs/method.md` for the full method. Points that affect how to read the results:

- **Test labels came from an LLM annotator** (a Claude Code subagent given only the codebook and the raw sentences), not a human. A second LLM annotator labeled 30 test sentences for Cohen's kappa. Accuracy figures therefore measure agreement with an LLM reading of the codebook.
- **Scope.** An article is in scope if a crash sentence names a pedestrian or cyclist (or a person who was struck), a motor vehicle appears, and the crash is in Toronto. During evaluation the annotators found US wire stories and car-only crashes in the sample. The scope rules were tightened (D-54, D-58), which cut the corpus from 1,671 to 942 articles (979 after the 2026-11-21 collection added crash stories found under bike lane and transit URLs), and eval rows that left scope were replaced by new random draws (D-55).
- **Police releases from the Wayback Machine.** The Toronto Police site blocks scripted access, so releases come from Wayback Machine copies. They are public government records, not commercial content, and the project publishes no release text beyond short excerpts. Wayback copies of blogTO and Toronto Today were not used: those are commercial outlets whose live sites block scripted access, and using archive copies would get around that choice. About 42% of releases in the window are archived. A release links to an article only when both name the same two streets within the date window (D-56); 218 articles are linked.
- Grammatical labels come from dependency rules under codebook v1.1 (D-69). Two fuzzy labels come from a SetFit model trained on Snorkel labels, with thresholds tuned on dev (D-71). Rates have 95% bootstrap intervals over articles.

## Evaluation

Test set: 240 sentences (100 crash, 100 context, 40 text-source), labeled by an LLM annotator. Crash rows were relabeled blind under codebook v1.1 (8 of 100 labels changed); v1.0 figures are in `metrics_summary_v10.csv`. Headline figures use the 160 random rows; the 80 disagreement rows (chosen where labeling functions disagreed) are reported separately. Crash-set figures cover the 52 random rows the annotator judged crash-describing. Full tables are in `eval/reports/metrics_summary.csv` and `metrics_per_class.csv`.

| Label | System | Accuracy (random) | Macro-F1 (random) | Macro-F1 (disagreement) |
|---|---|---|---|---|
| voice | rules | 0.98 | 0.96 (0.75–1.00) | 0.94 |
| driver_reference | rules | 0.90 | 0.85 (0.71–0.96) | 0.50 |
| focus | rules | 0.85 | 0.57 (0.32–0.82) | 0.55 |
| text_source | rules + dev-tuned thresholds | 0.90 | 0.85 (0.66–0.97) | n/a |
| thematic_cue | lexicon LF | 0.93 | 0.78 | 0.56 |
| thematic_cue | Qwen LF | 0.93 | 0.81 | 0.80 |
| thematic_cue | Snorkel | 0.93 | 0.81 | 0.83 |
| thematic_cue | SetFit | 0.72 | 0.57 | 0.52 |
| vru_conduct_detail | Qwen LF | 0.98 | 0.83 | 0.39 |
| vru_conduct_detail | Snorkel | 0.98 | 0.83 | 0.32 |
| vru_conduct_detail | SetFit | 0.90 | 0.60 | 0.49 |

- **The grammatical rules hold up.** Voice is near the ceiling. Driver reference is good on random rows but weak on the disagreement rows, which are the hard cases by construction.
- **`vru_as_actor` and `accident_term` scored 0.99, which tells us little.** The random rows contain almost no positive cases of either label, so the score mostly shows the rules do not fire falsely.
- **The trained end model still trails for the two fuzzy labels.** v1.0 SetFit marked most rows positive for `vru_conduct_detail` (accuracy 0.27). The rework (D-70, D-71) added 100 dev context rows, tuned the NLI cutoffs and the Snorkel and SetFit thresholds on dev, and trained SetFit at up to 3 negatives per positive. On test this lifted SetFit for conduct detail to 0.60 macro-F1 and the Snorkel label model for `thematic_cue` from 0.57 to 0.81, level with Qwen alone. SetFit for `thematic_cue` fell from 0.70 to 0.57. Dev gave the same ranking as test (Snorkel ≥ SetFit on random dev rows). Snorkel needs Qwen and NLI votes, which exist only for a pool of sentences, so SetFit is the only model that labels the whole corpus, and it is not good enough. The article-level `thematic_frame` and `vru_conduct_any` rates remain unreliable. Nothing was tuned on the test set.
- **NLI was a weak labeling function** for every grammatical label (voice macro-F1 0.15).
- **Second annotator.** Kappa was 1.0 on all five crash labels, over the 26 of 30 rows both annotators judged crash-describing (`agreement_kappa.csv`). Both annotators are instances of the same model reading the same codebook, so this shows the codebook gives consistent answers to that model. It does not show agreement between independent people.
- **Component check.** UD English EWT passive detection (clausal participles): P 0.92, R 0.80, F1 0.85 (`component_ud_passive.csv`). PolNeAR was skipped (no license, D-42).

## Comparison with prior studies

Ralph, Iacobucci, Thigpen & Goddard (2019) coded 200 US local news articles from February–March 2018 (100 pedestrian, 100 cyclist crashes) by hand. Their rates against this project's (newsroom text, 2023–2026, Toronto):

| Pattern | Ralph et al. 2019 | This project | Note |
|---|---|---|---|
| Crash sentences with no agent | one-third (p. 667) | 39% (agentless passive + intransitive + nominal) | Similar. This project splits the no-agent cases into three classes. |
| Object-based reference when driver or vehicle is mentioned | 81% (p. 667) | 83% (vehicle ÷ vehicle + person) | Similar. |
| Driver not mentioned anywhere in the article | 27% (p. 667) | 20% | Lower here; this project counts police-matched text and any driver mention. |
| "A VRU was hit by a car" (passive, vehicle agent) | 40% of body sentences, 29% of titles (p. 667) | 51% passive with agent in body, 65% in headlines | Not the same unit: this project's figure includes passives with a person as agent. |
| "Accident" | 47% of body sentences, 11% of titles (p. 669) | 0.8% of crash sentences, 0.1% of headlines | Large gap, checked below. |
| Thematic elements | 16% of articles (p. 668) | 91% (not reliable) | See Evaluation. |
| Counterfactuals (victim conduct) | one-third of articles (p. 668) | 49% (not reliable) | See Evaluation. |

The "accident" gap was checked against the raw text before reporting it. Only 45 of 3,126 crash sentences contain the word at all, and only 70 of 979 articles use it anywhere. Most of those uses are charge names ("leaving the scene of an accident", excluded under codebook v1.1, D-69) or "accident benefits". The low rate is in the text, not a rule failure. Ralph et al. measured the share of crash references that used "accident", so their denominator differs from this project's. The gap is too large for the denominator to explain. The sample years also differ: theirs is 2018, this one 2023–2026.

Fevyer & Aldred (2022) studied fatal-crash reporting in the London *Evening Standard*, 2012–2019. This project could not read the paper's text (the open copy returned HTTP 403), so no rate from it is compared here. Its "rogue driver" framing is the source of the `driver_exceptional` split above.

## Limitations

- **Dropped outlets.** Four planned outlets are not in the corpus:
  - Toronto Sun: Postmedia's terms ban scraping (D-19).
  - blogTO and Toronto Today: both block scripted access; their Wayback copies were not used (D-20, D-46).
  - CBC: its robots.txt could not be reached from the collection network, which is treated as no permission (D-33).

  Dropping the Toronto Sun removes the main right-leaning outlet in the planned set. The remaining outlets (CityNews, CTV, Global) are mainstream broadcasters' news sites, so outlet comparisons cover a narrower range of editorial positions than planned and cannot speak to differences across the political spectrum.
- **Uneven coverage.** CTV covers 2025 onward only. Global is national (a Toronto filter selects local crashes), and its in-scope count drops sharply after mid-2024. The drop comes from what Global published, not from collection (D-68). Global's sitemaps grew more slowly after mid-2024 (about 4 sitemaps of 1,000 URLs a month in early 2024, about 2.3 later), and short routine items such as "Pedestrian seriously injured after being hit by vehicle in Toronto" almost stop after June 2024. The Global articles that remain are mostly car-only crashes and policy stories, which are out of scope. The share of Toronto URLs in each sitemap did not change. Only 31 Global articles fall in the common window, so Global's outlet intervals are wide.
- **LLM-annotated test set.** See Methods. The kappa of 1.0 is between two runs of the same model.
- **Fuzzy labels are not reliable corpus-wide.** After the dev-only rework, Snorkel matches the Qwen labeling function, but SetFit, the only model that covers every sentence, still trails it, so the article-level thematic and conduct rates are not results.
- **Small test cells.** Several labels have few or no positive test cases (`vru_as_actor`, `accident_term`, random-row `vru_conduct_detail`), so their scores say little about recall.
- **Codebook gaps found by annotators, settled after the first scoring.** Codebook v1.1 (D-69) settles five cases the v1.0 annotators had to resolve by their own reading: charge names containing "accident", a bare "man" or "woman" who was struck, general statements about crashes, emergency vehicles at the scene, and separate car-only collisions. The rules were changed to match and the test and dev crash rows were relabeled blind. The revision came after the first test scores were seen; it changed 8 test labels and moved no headline rate by more than a point, but readers should know the order.
- **Release linking.** Linking requires two shared street names, which misses some correct links. Some linked releases are update or arrest notices rather than the first release about the crash. Release text stored from Wayback includes page navigation, which may dilute character-overlap scores.
- **Police-matched subset.** Linked articles are more often fatal and hit-and-run than unlinked ones, so police-vs-newsroom differences apply to that subset.

## Addendum: bike lane and transit coverage (v1.5)

v1.5 did not produce stance or policy-frame rates that can be reported. The trained model (SetFit) failed validation by a wide margin, and stance, as the codebook defines it, turned out to be rare. In the annotated test sample, 1 of 69 sentences naming transit (1%, 95% CI 0–8%) and 2 of 9 naming bike infrastructure take a position. SetFit labels a position on 48% and 98% of such sentences. What v1.5 did measure is below.

### Corpus

1,167 Toronto articles are tagged bike lane (105) or transit (1,062), with 26,637 sentences, from the same three outlets and window as v1. Topic tags come from keyword rules on the headline and first two paragraphs (D-65). A headline about a crash or about a crime or police incident keeps an article out (D-76).

### What was measured

| Measure | Result (test) | Before dev tuning |
|---|---|---|
| Topic precision, bike lane | 0.97 (n = 29) | 0.94 (n = 32) |
| Topic precision, transit | 0.80 (n = 46) | 0.64 (n = 58) |
| Source-role accuracy | 0.62 (n = 53) | 0.57 (n = 60) |

Topic and role rules were tuned on separate dev samples (D-75 to D-77). Test errors were not used. The "after" columns have smaller n because test rows from articles that left scope are dropped (D-79). Topic tagging is precision-only: recall was not measured. The role extractor labels 32% of quote units `unknown`; the annotator, who read the full article, never did. Role counts are therefore not reported as a finding. Of the quote units with a known role, transit and city staff (`agency_staff`) are the most common.

Policy frames in 75 random annotated test sentences: no policy content 49% (38–60), `other` 15% (8–24), quality of life 13% (7–23), economic 12% (6–21), safety 5% (2–13), political 3% (1–9), legality 3% (1–9). These are pooled across outlets and both topics, and are too few to compare outlets or the Bill 212 periods. `other` here is mostly transit service reliability, maintenance and project delivery, which the codebook places under capacity and policy evaluation.

### Model results

Scores are on the same test rows (random rows for frames). Gold labels came from an LLM annotator.

| System | Frame accuracy | Frame macro-F1 |
|---|---|---|
| Frame lexicon (29% coverage) | 0.17 | 0.39 |
| NLI zero-shot | 0.55 | 0.49 |
| Qwen | 0.52 | 0.27 |
| Snorkel label model | 0.60 | 0.42 |
| SetFit | 0.45 | 0.35 |

Stance metrics are not given: the random test rows hold one stance-positive sentence for transit, two for infrastructure and none for cyclists, so any score rests on the `none` class. Kappa against a second annotator run is 0.75 for policy frame (n = 24). Both runs labeled every stance `none`.

SetFit fails for two reasons. First, its training labels come from Snorkel, whose NLI and Qwen inputs vote for a stance far more often than the codebook allows. A newsroom sentence that reports a position in neutral words is `none` (codebook 9.2), and most transit sentences in this corpus are service and project news. Second, the rarer frames got few training examples (13 for `other` after the dev fix, D-78). Dev showed the same ranking (Snorkel above SetFit) before test was scored.

### What this means

Under this codebook, newsroom text about Toronto transit almost never takes a side, and quoted text rarely does in a random sample. That is itself a result, but its interval is wide. Measuring outlet or period differences in a rate near 1% would need thousands of annotated sentences or a different definition. One option is to count the positions that sources hold (attributed stance) and report them by source role. That would change codebook 9.2, so it is left to the author (D-80).

### Limitations specific to v1.5

- The incident-headline rule removed one true bike lane article in the dev sample ("arrested as … bike lane removal protests continue").
- Bike lane coverage is small (105 articles), so the Bill 212 period comparison planned in PLAN.md has few sentences per period even before the model problem.
- The BABE loaded-language score (`mediabiasgroup/da-roberta-babe-ft`) was computed for every sentence but was not validated on this corpus, so it is not reported.
