# How Toronto news frames crashes involving pedestrians and cyclists

Toronto crash coverage usually describes the impact so that it happens to the pedestrian or cyclist, with a vehicle rather than a person as the agent. In 1,661 newsroom-written crash sentences, 50% are passives with an agent ("a pedestrian was struck by a vehicle"). Where a driver or vehicle appears in the impact clause, 84% of the time it is the vehicle. The word "accident" is almost absent (under 1% of crash sentences). These patterns are close to those Ralph et al. (2019) found in US local news, except for "accident", which they found in 47% of body sentences.

All rates come from rule-based labels on 942 in-scope articles (3,114 crash sentences) from CityNews Toronto, CTV News Toronto and Global News, January 2023 to October 2026. Intervals are 95% bootstrap intervals over articles. The test labels behind every accuracy figure came from an LLM annotator, not a human (see Evaluation).

## Coverage

In-scope crash articles per outlet per quarter (`analysis/tables/coverage_by_quarter.csv`):

| Quarter | CityNews | CTV | Global |
|---|---|---|---|
| 2023Q1 | 25 | 0 | 25 |
| 2023Q2 | 20 | 0 | 42 |
| 2023Q3 | 35 | 0 | 36 |
| 2023Q4 | 33 | 0 | 31 |
| 2024Q1 | 23 | 0 | 16 |
| 2024Q2 | 26 | 0 | 20 |
| 2024Q3 | 21 | 0 | 5 |
| 2024Q4 | 36 | 0 | 2 |
| 2025Q1 | 20 | 22 | 2 |
| 2025Q2 | 31 | 35 | 2 |
| 2025Q3 | 47 | 52 | 4 |
| 2025Q4 | 38 | 38 | 8 |
| 2026Q1 | 24 | 36 | 1 |
| 2026Q2 | 32 | 40 | 9 |
| 2026Q3 | 34 | 44 | 6 |
| 2026Q4 | 7 | 13 | 1 |

Coverage is uneven. CTV's sitemaps start in 2025. Global's in-scope count falls from about 30 a quarter to under 10 after mid-2024; the cause was not traced (see Limitations). Outlet comparisons use only the window all three outlets cover (2025-01-14 to 2026-10-02), which holds only 28 Global articles. Trends are reported within each outlet. The before/after Bill 212 comparison uses only outlets with articles on both sides of 2024-11-25.

## Key results

Crash-sentence rates by text source (`overall_by_text_source.csv`). Quoted text is scored separately and left out here.

| Measure | Newsroom (n = 1,661) | Police-matched (n = 121) |
|---|---|---|
| Passive with agent | 50% (48–53) | 29% (21–37) |
| Agentless passive | 12% (10–13) | 12% (7–18) |
| Active | 10% (9–12) | 31% (23–39) |
| Nominal ("the crash") | 23% (21–26) | 19% (12–27) |
| Intransitive | 4% (3–5) | 9% (4–15) |
| Driver as vehicle | 60% (58–63) | 37% (28–46) |
| Driver as person | 12% (10–14) | 17% (11–24) |
| Driver absent | 28% (26–30) | 45% (37–55) |
| Focus on pedestrian or cyclist | 63% (60–66) | 47% (39–55) |
| Pedestrian or cyclist as actor | 0.6% (0.2–1.0) | 1.7% (0–4.5) |
| "Accident" | 0.9% (0.4–1.5) | 0% |

- **Newsroom text vs police-matched text.** Sentences that closely restate a Toronto Police release use the active voice about three times as often as newsroom sentences, and name the vehicle as agent less often. The intervals do not overlap. Police-matched sentences come from the 161 articles linked to a release, and those articles differ from unlinked ones (more fatal, more hit-and-run, more 2023; `matched_vs_unmatched.csv`), so this is a comparison within that subset.
- **Headlines vs body.** Headlines lean further toward the pedestrian or cyclist: 65% are passives with an agent (body 49%), 81% focus on the pedestrian or cyclist (body 62%), and 3% are active (body 12%). The intervals do not overlap (`headline_vs_body.csv`).
- **Initial reports vs follow-ups.** Follow-ups are more often active (22% vs 12%) and name the vehicle as agent less often (32% vs 59%) (`initial_vs_follow_up.csv`).
- **Fatal vs non-fatal.** Fatal crash sentences name the vehicle as agent somewhat less often (51% vs 62%) and focus on the victim less often (55% vs 65%) (`fatal_vs_nonfatal.csv`).
- **Driver mentioned anywhere in the article.** 81% of articles (79–84) mention a driver in newsroom or police-matched text. Split by `driver_exceptional`: 87% (81–93) when the driver fled, was impaired or was charged, and 80% (77–83) otherwise. The intervals overlap, so this corpus does not show the "rogue driver" gap that Fevyer & Aldred (2022) describe. Counting quoted text adds under one point to each.
- **Outlets.** In the common window, all outlet intervals overlap on every grammatical measure (`outlet_without_wire.csv`, `outlet_headlines.csv`). The closest case is driver as vehicle in body text: CityNews 63% (57–68), CTV 54% (49–58). This report does not claim any outlet differs from another.
- **Bill 212.** Within CityNews and within Global, pre- and post-cutoff intervals overlap on every grammatical measure (`bill212_pre_post_by_outlet.csv`). The comparison is descriptive.

**Pooled tables lean toward CityNews.** In every pooled table (text source, headline vs body, fatal vs non-fatal, initial vs follow-up, exceptional vs ordinary driver, article-level rates), CityNews supplies the most units: 48–50% of sentences and 48–49% of articles (`pooled_sample_shares.csv`). CTV supplies 26–28% and Global 22–25%. Each pooled table has a per-outlet breakdown of the same sample (`*_by_outlet.csv`). These breakdowns decompose the pooled figure; they are not outlet comparisons.

**Two article labels are not reported as findings.** The model behind `thematic_frame` (73% of articles) and `vru_conduct_any` (55%) scored poorly on the test set (see Evaluation), and both rates are far above the prior study. They are in the tables for completeness only.

## Methods

See `docs/method.md` for the full method. Points that affect how to read the results:

- **Test labels came from an LLM annotator** (a Claude Code subagent given only the codebook and the raw sentences), not a human. A second LLM annotator labeled 30 test sentences for Cohen's kappa. Accuracy figures therefore measure agreement with an LLM reading of the codebook.
- **Scope.** An article is in scope if a crash sentence names a pedestrian or cyclist (or a person who was struck), a motor vehicle appears, and the crash is in Toronto. During evaluation the annotators found US wire stories and car-only crashes in the sample. The scope rules were tightened (D-54, D-58), which cut the corpus from 1,671 to 942 articles, and eval rows that left scope were replaced by new random draws (D-55).
- **Police releases from the Wayback Machine.** The Toronto Police site blocks scripted access, so releases come from Wayback Machine copies. They are public government records, not commercial content, and the project publishes no release text beyond short excerpts. Wayback copies of blogTO and Toronto Today were not used: those are commercial outlets whose live sites block scripted access, and using archive copies would get around that choice. About 42% of releases in the window are archived. A release links to an article only when both name the same two streets within the date window (D-56); 218 articles are linked.
- Grammatical labels come from dependency rules. Two fuzzy labels come from a SetFit model trained on Snorkel labels. Rates have 95% bootstrap intervals over articles.

## Evaluation

Test set: 240 sentences (100 crash, 100 context, 40 text-source), labeled by an LLM annotator. Headline figures use the 160 random rows; the 80 disagreement rows (chosen where labeling functions disagreed) are reported separately. Crash-set figures cover the 51 random rows the annotator judged crash-describing. Full tables are in `eval/reports/metrics_summary.csv` and `metrics_per_class.csv`.

| Label | System | Accuracy (random) | Macro-F1 (random) | Macro-F1 (disagreement) |
|---|---|---|---|---|
| voice | rules | 0.98 | 0.97 (0.88–1.00) | 0.93 |
| driver_reference | rules | 0.90 | 0.85 (0.70–0.96) | 0.47 |
| focus | rules | 0.86 | 0.61 (0.35–0.84) | 0.53 |
| text_source | rules + dev-tuned thresholds | 0.90 | 0.85 (0.66–0.97) | n/a |
| thematic_cue | lexicon LF | 0.93 | 0.78 | 0.56 |
| thematic_cue | Qwen LF | 0.93 | 0.81 | 0.80 |
| thematic_cue | Snorkel | 0.68 | 0.57 | 0.32 |
| thematic_cue | SetFit | 0.83 | 0.70 | 0.59 |
| vru_conduct_detail | Snorkel | 0.98 | 0.83 | 0.25 |
| vru_conduct_detail | SetFit | 0.27 | 0.22 | 0.25 |

- **The grammatical rules hold up.** Voice is near the ceiling. Driver reference is good on random rows but weak on the disagreement rows, which are the hard cases by construction.
- **`vru_as_actor` and `accident_term` scored 1.0, which tells us little.** The random rows contain no positive case of either label, so the score only shows the rules do not fire falsely.
- **The trained end model did not work for the two fuzzy labels.** For `thematic_cue`, the Snorkel label model and SetFit both did worse than the lexicon and Qwen labeling functions alone. For `vru_conduct_detail`, the random sample holds one positive in 60 rows, and SetFit marks most rows positive (accuracy 0.27). The article-level `thematic_frame` and `vru_conduct_any` rates are therefore not reliable. Nothing was tuned on the test set to fix this.
- **NLI was a weak labeling function** for every grammatical label (voice macro-F1 0.15).
- **Second annotator.** Kappa was 1.0 on all five crash labels, over the 26 of 30 rows both annotators judged crash-describing (`agreement_kappa.csv`). Both annotators are instances of the same model reading the same codebook, so this shows the codebook gives consistent answers to that model. It does not show agreement between independent people.
- **Component check.** UD English EWT passive detection (clausal participles): P 0.92, R 0.80, F1 0.85 (`component_ud_passive.csv`). PolNeAR was skipped (no license, D-42).

## Comparison with prior studies

Ralph, Iacobucci, Thigpen & Goddard (2019) coded 200 US local news articles from February–March 2018 (100 pedestrian, 100 cyclist crashes) by hand. Their rates against this project's (newsroom text, 2023–2026, Toronto):

| Pattern | Ralph et al. 2019 | This project | Note |
|---|---|---|---|
| Crash sentences with no agent | one-third (p. 667) | 39% (agentless passive + intransitive + nominal) | Similar. This project splits the no-agent cases into three classes. |
| Object-based reference when driver or vehicle is mentioned | 81% (p. 667) | 84% (vehicle ÷ vehicle + person) | Similar. |
| Driver not mentioned anywhere in the article | 27% (p. 667) | 19% | Lower here; this project counts police-matched text and any driver mention. |
| "A VRU was hit by a car" (passive, vehicle agent) | 40% of body sentences, 29% of titles (p. 667) | 50% passive with agent in body, 65% in headlines | Not the same unit: this project's figure includes passives with a person as agent. |
| "Accident" | 47% of body sentences, 11% of titles (p. 669) | 0.9% of crash sentences, 0.1% of headlines | Large gap, checked below. |
| Thematic elements | 16% of articles (p. 668) | 73% (not reliable) | See Evaluation. |
| Counterfactuals (victim conduct) | one-third of articles (p. 668) | 55% (not reliable) | See Evaluation. |

The "accident" gap was checked against the raw text before reporting it. Only 52 of 3,114 crash sentences contain the word at all, and only 64 of 942 articles use it anywhere. Most of those uses are charge names ("leaving the scene of an accident") or "accident benefits", which the codebook excludes. The low rate is in the text, not a rule failure. Ralph et al. measured the share of crash references that used "accident", so their denominator differs from this project's. The gap is too large for the denominator to explain. The sample years also differ: theirs is 2018, this one 2023–2026.

Fevyer & Aldred (2022) studied fatal-crash reporting in the London *Evening Standard*, 2012–2019. This project could not read the paper's text (the open copy returned HTTP 403), so no rate from it is compared here. Its "rogue driver" framing is the source of the `driver_exceptional` split above.

## Limitations

- **Dropped outlets.** Four planned outlets are not in the corpus:
  - Toronto Sun: Postmedia's terms ban scraping (D-19).
  - blogTO and Toronto Today: both block scripted access; their Wayback copies were not used (D-20, D-46).
  - CBC: its robots.txt could not be reached from the collection network, which is treated as no permission (D-33).

  Dropping the Toronto Sun removes the main right-leaning outlet in the planned set. The remaining outlets (CityNews, CTV, Global) are mainstream broadcasters' news sites, so outlet comparisons cover a narrower range of editorial positions than planned and cannot speak to differences across the political spectrum.
- **Uneven coverage.** CTV covers 2025 onward only. Global is national (a Toronto filter selects local crashes), and its in-scope count drops sharply after mid-2024. The cause was not traced. Candidates include a change in Global's sitemaps or page titles, and the Toronto filter. Only 28 Global articles fall in the common window, so Global's outlet intervals are wide.
- **LLM-annotated test set.** See Methods. The kappa of 1.0 is between two runs of the same model.
- **Fuzzy labels failed.** The Snorkel and SetFit models for `thematic_cue` and `vru_conduct_detail` did worse than single labeling functions, so the article-level thematic and conduct rates are not results.
- **Small test cells.** Several labels have few or no positive test cases (`vru_as_actor`, `accident_term`, random-row `vru_conduct_detail`), so their scores say little about recall.
- **Codebook gaps found by annotators.** The codebook does not settle: charge names that contain "accident"; whether a bare "man" or "woman" who was struck counts as a road user; general statements about crashes; emergency vehicles responding to a crash; and whether the sentence filter should also apply the pedestrian-or-cyclist scope. Each annotator resolved these by its own reading, and the codebook was not changed after labeling.
- **Release linking.** Linking requires two shared street names, which misses some correct links. Some linked releases are update or arrest notices rather than the first release about the crash. Release text stored from Wayback includes page navigation, which may dilute character-overlap scores.
- **Police-matched subset.** Linked articles are more often fatal and hit-and-run than unlinked ones, so police-vs-newsroom differences apply to that subset.
