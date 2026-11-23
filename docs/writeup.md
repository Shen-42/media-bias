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

### Coverage against police records

About a quarter of pedestrian and cyclist crashes that police record as killing or seriously injuring someone got an initial report in the corpus: 173 of 661 (26%, 23–30) from 2023 to October 2026. Fatal crashes were covered more often than serious-injury crashes (53%, 44–63, against 21%, 18–25), and pedestrian crashes more often than cyclist crashes (30%, 26–34, against 15%, 10–21). Police records come from the City of Toronto KSI open dataset (D-95).

An initial report links to a collision when it was published 0–2 days after it and names both streets of the collision's location. All 25 links in a random sample were the same crash. These are lower bounds: a report that names only one street, or a crash the corpus filter missed, does not link, and collection gaps (CTV before 2025, Global after mid-2024) lower the rate in those years. Year-to-year changes therefore say more about collection than about newsrooms.

The 257 linked reports also check two article labels against police records. `road_users` agreed on pedestrian and on cyclist involvement for 253 of 257 (98%). `severity` agreed on fatal or not for 231 of 257 (90%, 86–93). In 22 of the 26 disagreements the report described an injury and police recorded a death, which fits a victim who died after the first report rather than a labeling error. Police records are a check, not ground truth: a York University study found that they undercount pedestrian and cyclist injuries.

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
- **Outlets.** In the common window, 5 of 72 outlet comparisons have intervals that do not overlap (12 grammatical measures, three outlet pairs, body and headlines; `outlet_without_wire.csv`, `outlet_headlines.csv`). All five are CityNews against CTV. In body text, CityNews named the vehicle as the striker more often (62%, 58–67, against 52%, 47–57) and used nominal sentences less often (20%, 16–25, against 31%, 27–35). In headlines, CityNews named the vehicle more often (76%, 69–81, against 57%, 51–64), named the driver as a person less often (5%, 2–8, against 15%, 10–20), and left the driver unnamed more often (95%, 92–98, against 85%, 80–90). Global overlaps both on every measure; it has only 31 articles in the window. An earlier version of this report said every outlet interval overlapped, which was wrong (D-103).
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

## Suggested rewrites

The local article viewer and `python -m nlp.rewrite --article <id>` offer suggestions for crash sentences, after the Road Collision Reporting Guidelines (Laker & Active Travel Academy, 2021). They are suggestions, not measured results, and quoted sentences get none. Each names a guideline point: say who did what, refer to the driver rather than only the vehicle, prefer "crash" to "accident", and leave out victim details that police do not tie to the crash. Where the parse allows a safe mechanical change, the suggestion includes a rewrite: "a pedestrian was struck by a vehicle" becomes "the driver of a vehicle struck a pedestrian". No language model is used (D-98).

The rewrite rules were tuned on the dev crash sentences and a second sample of 40. On a third sample of 40 rewrites from unseen non-quoted corpus sentences, 38 read as grammatical and kept the meaning; the two failures left a "before coming to rest" clause attached to the driver. That judgment came from Claude Code, not a human reader. Rewrites assume a driver, which fits nearly every pedestrian or cyclist crash in this corpus but should be checked against the facts before use.

## Comparison corpora

Three comparisons from the plan's nice-to-haves sit outside the main results, in their own databases (codebook §10, D-99 to D-101). All rates are rule labels on non-quoted body sentences of initial reports whose headline is a crash sentence, with 95% article-cluster bootstrap intervals. Police matching exists only for Toronto, so this measure pools newsroom and police-matched text and is not the v1 newsroom rate. The rules were tuned on Toronto English text and not retuned for the other corpora.

Share of crash sentences with no driver named (`driver_reference` is `vehicle` or `absent`):

| Group | Driver not named | Vehicle named instead | Nominal voice | Articles |
|---|---|---|---|---|
| Toronto mainstream (CityNews, CTV, Global) | 88% (86–90) | 60% (58–63) | 22% (20–24) | 751 |
| Canadian Cycling Magazine (Toronto) | 59% (44–72) | 18% (0–32) | 44% (29–57) | 13 |
| Vancouver (English) | 76% (71–81) | 38% (31–44) | 35% (28–41) | 103 |
| Montreal (English) | 85% (81–88) | 58% (53–62) | 32% (27–36) | 192 |
| Montreal (French, Radio-Canada) | 78% (68–86) | 51% (38–63) | 38% (25–53) | 31 |

**Cycling and urbanist outlets.** Canadian Cycling Magazine's Toronto crash reports named the driver more often than the mainstream outlets did: the driver was absent from 59% of its crash sentences against 88%. That rests on 13 articles. Spacing and The Local ran no crash reports in the window; their crash mentions were in opinion and policy pieces. On bike lanes, the urbanist outlets stated positions in their own voice where the mainstream outlets did not. Among annotated sentences naming bike infrastructure, 46% (30–63) of Spacing's and 6% (4–10) of Cycling Magazine's carry the outlet's own position, against 1% (0–1) for the Toronto mainstream outlets (D-85, D-87). Opposition to bike lanes appeared at a similar rate in Cycling Magazine (19%, 14–25) and the mainstream outlets (18%, 15–22). The urbanist sentences were labeled by annotator subagents with no second annotator; Cycling Magazine's 1,156 sentences were sampled down to 300.

**Comparison cities.** Vancouver coverage named the driver more often than Toronto coverage (driver absent in 76% against 88%; intervals do not overlap) and used the vehicle as the striker less (38% against 60%). Montreal English coverage was close to Toronto's. In all three other groups, more crash sentences were nominal ("a collision involving a pedestrian") than in Toronto. These are differences in what the rules measure; they were not checked by hand in the other cities.

**French.** Radio-Canada was the only French outlet that could be collected (La Presse blocks scripted access; see `docs/sources.md`). The French rules were scored on 80 annotated test sentences: crash detection precision 0.72 (0.60–0.82) and recall 0.95 (0.85–0.99); on sentences both the rules and the annotator call crash sentences, voice agreed on 0.95, driver reference 0.90 and focus 0.74 (n = 42). A second annotator agreed on all 30 shared sentences, but both are LLM annotators working from one codebook, which is a weak check. "Accident" is the standard Quebec French word for a road crash, so its rate is not compared across languages.

## Addendum: bike lane and transit coverage (v1.5)

Positions on bike lanes and transit in Toronto news almost always belong to sources, not to the outlets. Of 511 annotated sentences that state a position, 7 state it as the outlet's own claim (1.4%). Among all 955 body sentences that name bike infrastructure, 0.5% carry the outlet's own position (CityNews 5 of 450, CTV 0 of 212, Global 0 of 293). Positions from sources are common: 68% (61–76) of quoted sentences that name bike infrastructure take one, 52% (46–58) of attributed sentences and 28% (23–33) of other newsroom sentences, split between support and oppose about 3 to 2. Transit positions are rarer and almost all support: 26% (17–35) of quoted transit sentences, 6% (3–10) of attributed and 4% (2–7) of other newsroom sentences. All of these rates come from annotated sentences (D-85), not from a model. No model stance passed validation (D-88).

### Stance definition

Codebook 9.2 was revised at the author's request (D-81): a position attributed to a named or described source now counts as stance. Under the first definition, which counted only the sentence's own claim, stance was almost absent (1 of 69 transit sentences) and could not be compared across anything. A stance still needs an evaluation or an explicit position. Plans, actions, votes and facts are `none`. Opposing the removal of bike lanes is support for them (D-83). Attributed newsroom sentences are reported as their own text source, so a source's view is never counted as the outlet's.

### Corpus

1,149 Toronto articles are tagged bike lane or transit, with 26,208 sentences, from the same three outlets and window as v1. Topic tags come from keyword rules on the headline and first two paragraphs (D-65). A headline about a crash, crime or police incident keeps an article out (D-76, D-92).

### Annotated rates

The measurement sample (D-85) holds every body sentence that names bike infrastructure or cyclists (1,014 sentences in scope) and about 200 random transit-mention body sentences per outlet (588 in scope). An annotator subagent labeled all of them blind to every model. A second run on 100 rows agreed with kappa 0.94 for infrastructure stance, 1.0 for transit stance and 0.76 for policy frame. A second pass labeled who holds each stated position (`stance_holder`, D-87): a second run agreed on 60 of 60.

The `stance_holder` label was added because the attributed-sentence detector misses reported positions. A quality check (D-91) extended the detector to verbs of position (argue, warn, urge, vow, call for, criticize and others): test recall rose from 0.66 to 0.73 at precision 0.93. The remaining "newsroom" sentences with a stance still mostly report what a named group or person did or said ("Cycling advocates rally at High Park in opposition to…"). Newsroom text with a stance is therefore not the outlet's voice. Only `stance_holder` = `outlet` is.

Shares of body sentences that name the target, with article-cluster bootstrap 95% CIs. Transit rates weight each outlet by its share of transit sentences.

| Target | Text source | n | Any position | Support | Oppose |
|---|---|---|---|---|---|
| Bike infrastructure | quoted | 221 | 68% (61–76) | 41% | 27% |
| Bike infrastructure | attributed | 326 | 52% (46–58) | 29% | 23% |
| Bike infrastructure | other newsroom | 408 | 28% (23–33) | 19% | 9% |
| Transit | quoted | 114 | 26% (17–35) | 26% | 0% |
| Transit | attributed | 238 | 6% (3–10) | 5% | 1% |
| Transit | other newsroom | 236 | 4% (2–7) | 4% | 0% |
| Cyclists | all three | 127 | 5 sentences | 4 | 1 |

Outlet's own position (`stance_holder` = `outlet`): bike infrastructure CityNews 1.1% (0.2–2.2, n = 450), CTV 0 of 212, Global 0 of 293; transit CityNews 1 of 199, Global 1 of 189, CTV 0 of 200. With counts this small, no outlet differs from another.

**Outlets.** CityNews bike-lane sentences carry a source's position more often than at least one other outlet in every text type: quoted 80% (71–88) against 54% (38–68) at CTV; attributed 64% (55–74) against 39% (33–47) at Global; other newsroom 34% (26–42) against 18% (10–25) at CTV. Four of 27 outlet comparisons have non-overlapping intervals, all in this direction. For transit, every outlet interval overlaps. These are differences in which positions get reported, not in the outlets' own views.

**Bill 212 periods.** Reported opposition to bike lanes in attributed and newsroom sentences was lowest when the plan was announced (attributed 7%, newsroom 3%) and higher before the plan (28% and 19%). Only 10 of 135 period comparisons have non-overlapping intervals, close to chance, so this is not a finding.

**Policy frames.** Frames come from the same annotated sample (D-90), so they describe sentences that name the target. Annotator agreement on frames is kappa 0.83 (n = 184); the models are the weak point, so no model frame rate is reported.

| Frame | Bike lanes: quoted | attributed | newsroom | Transit: quoted | attributed | newsroom |
|---|---|---|---|---|---|---|
| Legality | 7% | 24% | 39% (33–45) | 1% | 1% | 4% |
| Political | 18% | 24% | 26% | 6% | 4% | 1% |
| Quality of life | 21% | 16% | 4% | 17% | 10% | 12% |
| Safety | 20% (15–26) | 9% | 4% | 13% | 14% | 9% |
| Economic | 4% | 8% | 4% | 16% | 12% | 16% |
| Other | 24% | 12% | 7% | 21% | 18% | 14% |
| No policy content | 6% | 6% | 17% | 26% | 41% | 43% |

Bike-lane sentences in the outlets' own text are framed mostly as law and politics. Quoted sources frame them by safety and daily life. Transit sentences are more often plain service news. Legal framing in bike-lane newsroom text moved with Bill 212: 19% (10–28) before the plan and 33% at its announcement, 55% (43–67) while the law was in force, 64% (42–85) under the injunction and 47% after it was struck down, then 31% after the appeal was allowed. Economic framing peaked at the announcement (17%, against 0–3% in other periods). Of 315 period comparisons, 44 have non-overlapping intervals, well above chance. Outlet frame comparisons are near chance (9 of 126), so no outlet differs in framing. A rate of zero gets a 0–0 bootstrap interval, which understates uncertainty in small cells.

Across all v1.5 sentences, policy frames in 75 random annotated test sentences: no policy content 49% (38–60), `other` 15% (8–24), quality of life 13% (7–23), economic 12% (6–21), safety 5% (2–13), political 3% (1–9), legality 3% (1–9). `other` here is mostly transit service reliability, maintenance and project delivery, which the codebook places under capacity and policy evaluation.

### Components

| Measure | Result (test) | Before the 2026-11-22 quality checks |
|---|---|---|
| Topic precision, bike lane | 0.97 (n = 29) | 0.97 (n = 29) |
| Topic precision, transit | 0.82 (n = 45) | 0.80 (n = 46) |
| Attribution (`attributed`), precision / recall | 0.93 / 0.73 (n = 150) | 0.92 / 0.66 |
| Source-role accuracy | 0.60 (n = 53) | 0.62 (n = 53) |
| Attribution on PolNeAR (public, human-labeled), precision / recall | 0.90 (0.88–0.92) / 0.49 (0.47–0.52), n = 2,275 sentences | not run (D-42) |

Each check used a new dev sample, because the earlier dev rows had been used up by tuning (D-75 to D-77): 80 transit-tagged articles (D-92), 150 sentences for attribution (D-91) and 80 quote units for roles (D-93). Test errors were not used. On the new dev sample the role extractor scored 0.66, against 0.81 on the old dev rows, so the old figure was overfit. The role fixes gained one dev row and lost one test row. The extractor labels 30% of test quote units `unknown`; the annotator, who read the full article, never did. Most remaining errors need the whole article to identify the speaker. Topic recall was not measured.

The PolNeAR check (D-94) is the only component check on human labels in v1.5. PolNeAR (84 test articles from 2016 US election news) marks every attribution, including polls that "show", questions, colons, refusals, endorsements and beliefs. The codebook's `attributed` is narrower, so PolNeAR recall is a lower bound. Precision on human labels (0.90) matches the precision against the LLM annotator (0.93), which supports those labels for this rule. The rule was not changed after the check.

### Model results

Gold labels came from an LLM annotator. Kappa against a second annotator run (n = 24) is 0.75 for policy frame, 0.78 for transit stance and 1.0 for infrastructure stance (one positive).

| System | Frame accuracy (random, n = 74) | Frame macro-F1 | Transit stance precision / recall (test) |
|---|---|---|---|
| Lexicon | 0.17 (29% coverage) | 0.39 | n/a |
| NLI zero-shot | 0.55 | 0.51 | n/a |
| Qwen | 0.58 | 0.35 | 1/6, 1/5 |
| Snorkel label model | 0.64 | 0.47 | 3/8, 3/5 |
| SetFit | 0.49 | 0.36 | 3/47, 3/5 |

Snorkel labels only the 3,000-sentence pool and overstates stance: on measurement rows in the pool its transit stance precision was 4/15. Its stance tables were dropped (D-88).

SetFit labeled a transit stance on 57% of dev sentences when trained on confident, class-capped Snorkel labels (D-84). Retrained on Snorkel's label for every pool transit sentence, with the real class mix (D-86), it scored dev macro-F1 0.78 at a 0.70 threshold, stable from 0.60 to 0.90, against 0.75 for logistic regression on frozen embeddings and for Snorkel. On 490 held-out measurement rows its precision was 21/37 and recall 21/46 (refit after D-92). A pass rule fixed before scoring required its stance rate to fall inside the annotated interval overall, per outlet and per text source. It passed everywhere except newsroom text (1.6% against 4.2%, 2.1–8.0), so transit is reported from annotations only. Infrastructure and cyclists got no end model: the census labels every sentence. SetFit frame tables were dropped too; frames are reported from annotations (D-90).

Two labeling-function problems surfaced on dev and were fixed (D-83). The support/oppose cue words fire on "oppose the removal", which is support, so they were taken out of Snorkel. Qwen made the same error: it read 8 of 11 "against the removal" infrastructure sentences as `oppose`. A removal rule in the prompt cut that to 6 of 11, and a 4B model may not do better. A second prompt revision with removal examples gained one dev sentence, and Qwen also read most neutral removal plans as `oppose`. Snorkel did better on dev without Qwen's infrastructure vote (accuracy 0.62 against 0.50), so that vote was removed (D-89). On test, infrastructure accuracy stayed at 0.94 and macro-F1 moved from 0.71 to 0.66 on few positives.

### Limitations specific to v1.5

- Transit rates rest on 600 annotated sentences (200 per outlet) out of 9,210. Period comparisons for transit were not attempted.
- The attributed-sentence detector still misses about a quarter of reported positions (test recall 0.73, D-91), so `newsroom` text with a stance mostly carries sources' views (D-87).
- Every gold label came from LLM annotators reading the codebook, with two runs of the same model as the agreement check.
- The incident-headline rule removed one true bike lane article in the dev sample ("arrested as … bike lane removal protests continue").
- Bike lane coverage is small (105 articles, 955 sentences that name bike infrastructure), so some Bill 212 periods have under 30 sentences per text source.
- The BABE loaded-language score (`mediabiasgroup/da-roberta-babe-ft`) was computed for every sentence but is not reported. On BABE's own test split it scored macro-F1 0.82 and AUC 0.94 and under-predicted bias (41% against 56%), but the model may have been trained on those sentences, and it has not been checked on local transport news (D-96).
