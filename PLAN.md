# Media Bias & Framing Detector: Project Plan

Status: approved. Phase 0 in progress.
Last updated: 2026-11-18

## 1. Goal

Measure how Toronto local news frames traffic crashes, bike lane changes, and transit funding, and report the results by outlet and over time.

v1 answers one question: **how often do Toronto outlets describe crashes in ways that hide the driver, and how much of that language comes from police press releases rather than the newsroom?**

The tool measures framing. It does not start from a conclusion about any outlet or government. Results should hold up for a reader who disagrees with the author's view of bike lanes.

### Why this matters

Goddard et al. (2019) ran an experiment with 999 readers. Shifting from pedestrian-focused to driver-focused language reduced victim-blaming and increased perceived blame for the driver. Thematic framing increased support for infrastructure, enforcement, and lower speeds. A German replication found the same effects. So sentence-level framing is a measurable property with documented effects on readers, not only a style preference.

### What is new here

Manual content analyses of crash coverage exist for the US, UK, Netherlands, Switzerland, and German-speaking countries. Bike Frames (ICWSM 2025) automated part of this for US headlines. This project differs in three ways:

1. Canadian (Toronto) coverage, which none of the studies cover.
2. Full article text with sentence-level labels, not headlines only.
3. A direct comparison between each article and the Toronto Police news release it drew from. The Swiss study (Reymond & Rérat) explicitly did not assess police influence; this project measures it.

## 2. Context

- In November 2024 Ontario passed Bill 212 (Reducing Gridlock, Saving You Time Act). It required removal of bike lanes on Bloor Street, University Avenue, and Yonge Street.
- July 2025: Ontario Superior Court (Justice Schabas) ruled the removal unconstitutional.
- August 14, 2026: Court of Appeal for Ontario reversed that ruling (Cycle Toronto v Ontario (AG), 2026 ONCA 582).
- From September 2026 the province began restoring motor vehicle lanes on Bloor, Yonge, University, Queen's Park, Queen's Park Crescent and Avenue Road.

These dates give an event timeline for the bike lane analysis (v1.5). Verify each date against a primary source before publishing anything.

## 3. Decisions and open questions

| # | Question | Decision |
|---|---|---|
| Q1 | Audience: portfolio, course/research paper, or public tool? | **Answered:** portfolio piece with a short write-up |
| Q2 | v1 topic scope | **Answered:** crashes only. Discovery may collect `bike_lane` and `transit` URLs and raw text in the same crawl. They are tagged but not processed in v1 |
| Q3 | Outlets; access to paywalled Star and Globe text | **Answered:** CBC Toronto, CityNews, CTV Toronto, Global, Toronto Sun, blogTO, Toronto Today, minus any that fail the Phase 0 check. Star and Globe deferred. Phase 0 result: the Toronto Sun is excluded (Postmedia terms prohibit scraping); blogTO and Toronto Today are excluded (they block scripted access, and the block is not circumvented). See `DECISIONS.md` and `docs/sources.md` |
| Q4 | Time window | **Answered:** 2023-01-01 to 2026-10-31 (about two years before Bill 212) |
| Q5 | Data source | **Answered:** outlet sitemaps and RSS for URL discovery, plus GDELT where it covers the window; trafilatura for text. No services that need an account (Media Cloud dropped). Police releases from the Wayback Machine only |
| Q6 | Definition of bike lane/transit "bias" (v1.5) | Default: source counts + policy frames, not a single pro/anti score |
| Q7 | Labeling budget | **Answered:** training labels are automated (Section 9). No hand-labeled training data anywhere. Test (~100 sentences) and dev (~30 sentences, including `text_source`) labels come from a Claude Code subagent acting as an independent annotator, given only `codebook.md` and raw sentences. A second independent annotator labels 30 test sentences for Cohen's kappa. These are LLM labels, not human labels, and every report says so |
| Q8 | LLM API use and budget | **Answered:** no LLM APIs. Open models run locally only. A local Qwen model via Ollama is allowed as one weak labeler |
| Q9 | Output form | **Answered:** Streamlit dashboard + short write-up. The full-text article viewer runs locally only. The deployed app shows aggregate rates and at most one flagged sentence per article as an excerpt |
| Q10 | Which crashes are in scope? | **Answered:** crashes where at least one pedestrian or cyclist was involved, fatal and non-fatal, any striking vehicle (car, truck, TTC bus, streetcar). Car-only crashes are out. Tag severity so fatal-only results can be split out |
| Q11 | What is a crash-describing sentence? | **Answered:** a sentence that describes the collision itself: an impact verb (hit, struck, ran over, collided) or collision noun (crash, collision) plus at least one road user. Excluded: road closures, investigation, witness appeals, hospital transport without the collision mentioned |
| Q12 | Unit of annotation | **Answered:** the sentence. `voice`, `driver_reference`, `focus` and `vru_as_actor` are computed on the main impact clause only. Other clauses still count for article-level labels. "A cyclist was struck and the driver remained at the scene." → `agentless_passive`; `driver_reference` comes from the impact clause |
| Q13 | Sentences with no passive or active impact verb | **Answered:** two more `voice` values: `intransitive` ("A cyclist died", "a car crashed") and `nominal` (no impact verb: "Pedestrian dead after collision"). Reported separately from `agentless_passive`, never merged |
| Q14 | Precedence when a sentence fits two values | **Answered:** `driver_reference` = `person` if any human driver appears in the impact clause ("the driver of a pickup" → `person`). `text_source`: `quoted` > `police_matched` > `newsroom` |
| Q15 | Meaning of "driver named" | **Answered:** renamed to `driver_ever_mentioned`: any reference to a human driver (role noun, coreferent description, or name). Primary count uses newsroom + police-matched text; a second count with quotes included is reported separately |
| Q16 | Unit of analysis for articles | **Answered:** add `crash_id` (linked by date, location, release match) and `article_type`: `initial`, `follow_up`, `roundup`. Primary analysis uses initial reports. Follow-ups are reported separately. Roundups are excluded in v1 |
| Q17 | Wire copy and per-outlet rates | **Answered:** body sentences are counted once at corpus level. Per-outlet rates include wire stories each outlet ran and are reported with and without wire. Headlines are scored per outlet, not deduped |
| Q18 | Keeping codebook examples out of evaluation | **Answered:** article and sentence IDs used as codebook or prompt examples go in `eval/excluded_ids.txt`. The test/dev sampler skips them, and a unit test enforces it |
| Q19 | Git host and CI | **Answered:** GitHub, with GitHub Actions for CI |

## 4. Assumptions

- Solo project, about 8 weeks part-time.
- Python 3.11, spaCy, Hugging Face transformers, SQLite, and Streamlit for the front end.
- English-language outlets only.
- Headlines and body text are scored separately.
- No LLM APIs. Every model is a public, openly licensed checkpoint that runs locally. The pipeline is fully reproducible with no API cost.
- Local LLM: an Apache-2.0 Qwen model served by Ollama on the laptop: `qwen3:4b`, with the exact tag and digest pinned.
- Compute: an Apple M2 with 8 GB RAM. One model in memory at a time; every model output is cached to disk. Zero-shot NLI uses `deberta-v3-base-zeroshot-v2.0`. The trained end model is SetFit on a small sentence-transformer (`all-MiniLM-L6-v2`). No DeBERTa fine-tuning and no Colab.
- Work runs in autonomous mode: judgment calls are logged in `DECISIONS.md` and status in `PROGRESS.md`.
- Article text stays local and is not redistributed (copyright). The repo publishes code, labels, and aggregate statistics, not article bodies.

## 5. Scope

### v1 (MVP)
- Corpus of Toronto crash coverage where at least one pedestrian or cyclist was involved, fatal and non-fatal, any striking vehicle. Car-only crashes are out.
- Corpus of matching Toronto Police Service news releases.
- Sentence-level crash framing labels (Section 7).
- Quote detection so police and official quotes are scored separately from reporter text.
- Article-to-press-release overlap score.
- Rule-based grammatical labels; automated training labels (Snorkel) for the two fuzzy labels; evaluation against a small test set labeled by an annotator subagent.
- Outlet and time comparisons, headline vs. body comparison, newsroom vs. police comparison.
- Streamlit dashboard with aggregate rates and at most one flagged sentence per article as an excerpt.
- Local-only article viewer that highlights flagged sentences and shows which ones match the police release. Never deployed.

### v1.5
- Bike lane and transit coverage: who gets quoted, policy frames, stance.
- Separate framing of *cycling* (the activity, infrastructure) from *cyclists* (people). Rissel et al. (2010) found these diverge: coverage of cycling was more positive than negative, while coverage of cyclists was more negative.
- Bill 212 event timeline overlaid on results.

### Nice-to-haves
- Comparison cities (Montreal, Vancouver) as a baseline.
- Compare crashes that get covered with Toronto Police collision open data.
- Compare mainstream outlets with cycling or urbanist outlets (Bike Frames found differences between these in the US).
- Browser extension that scores the article being read.
- Suggested rewrites using the Road Collision Reporting Guidelines.
- French-language outlets (Radar de Parité shows the quote pipeline can extend to French).

## 6. Data pipeline

1. **URL discovery.** Outlet sitemaps and RSS (GDELT where it covers the window), filtered by outlet, date range, and keywords ("pedestrian", "cyclist", "struck", "collision", "crash", "hit-and-run", "bike lane", "TTC funding", "Bill 212"). Bike lane and transit articles are collected and stored in the same crawl but not processed in v1.
2. **Police news releases.** Collect Toronto Police Service news releases on collisions for the same window from the Wayback Machine only. The TPS site blocks scripted access, and about 42% of release IDs in the window are archived (72% in 2023, 25–35% after). The police comparison is therefore a **secondary analysis on the matched subset**. It includes a bias check that compares articles with and without an archived release (outlet, year, severity, road users, headline framing rates).
3. **Fetch and extract.** trafilatura for body text. Store raw HTML locally, gitignored. Record the fetch timestamp, since articles get edited.
4. **Topic tagging.** Keyword filter first, then a small classifier only if precision is poor. Tags: `crash`, `bike_lane`, `transit`.
5. **Crash metadata.** Severity (fatal / injury / no injury / unknown), road users (pedestrian, cyclist, driver, transit vehicle), hit-and-run flag, `article_type` (`initial`, `follow_up`, `roundup`). Articles without a pedestrian or cyclist are dropped from the crash set.
6. **Dedupe.** Near-duplicate detection (MinHash or embedding similarity). Canadian Press wire copy runs in many outlets and would inflate scores. Keep one canonical copy and record which outlets ran it. Body sentences count once at corpus level. Per-outlet rates include the wire stories each outlet ran, reported with and without wire. Headlines are scored per outlet and not deduped.
7. **Release matching and crash linking.** Link each crash article to its police release by date, location, and text similarity, and assign a `crash_id` so initial reports and follow-ups on the same crash are grouped. Store sentence-level similarity scores.
8. **Storage.** SQLite tables: `articles`, `crashes`, `police_releases`, `article_release_links`, `sentences`, `quotes`, `labels`, `predictions`, `events`.

Respect robots.txt and outlet terms. Rate-limit all fetches.

## 7. Codebook (crash framing)

The codebook follows the five dimensions used across the crash-reporting literature (Ralph et al. 2019; Goddard et al. 2019; Fevyer & Aldred 2022; Reymond & Rérat): **focus, agency, grammatical voice, language, and narrative framing.** Using the shared structure keeps results comparable to those studies.

### Crash-describing sentences and unit of annotation

A crash-describing sentence describes the collision itself: an impact verb (hit, struck, ran over, collided) or a collision noun (crash, collision) plus at least one road user. Road closures, investigation, witness appeals, and hospital transport without the collision mentioned are excluded.

The unit is the sentence. `voice`, `driver_reference`, `focus` and `vru_as_actor` are computed on the main impact clause only. Other clauses still count toward article-level labels. "A cyclist was struck and the driver remained at the scene." → `agentless_passive`, with `driver_reference` taken from the impact clause.

### Sentence-level labels (crash-describing sentences only)

| Dimension | Label | Values | Example | Detection |
|---|---|---|---|---|
| Voice | `voice` | `active`, `passive_with_agent`, `agentless_passive`, `intransitive`, `nominal` | "A pedestrian was struck." → `agentless_passive`; "A cyclist died." → `intransitive`; "Pedestrian dead after collision" → `nominal` | Rules |
| Agency | `driver_reference` | `person`, `vehicle` (metonymy), `absent` | "A car hit a cyclist." → `vehicle` | Rules |
| Focus | `focus` | `vru`, `driver`, `vehicle`, `other` | "A cyclist was hit by a driver." → `vru` | Rules (grammatical subject) |
| Agency | `vru_as_actor` | yes / no | "A cyclist collided with a car." / "pedestrian in collision with vehicle" | Rules |
| Language | `accident_term` | yes / no | Uses "accident" | Lexicon |
| Focus | `vru_conduct_detail` | yes / no | "The cyclist was not wearing a helmet." / "dressed in dark clothing" | Classifier |

`vru` = vulnerable road user (pedestrian or cyclist). `intransitive` and `nominal` are reported separately from `agentless_passive`, never merged.

Precedence: `driver_reference` is `person` if any human driver appears in the impact clause ("the driver of a pickup struck…" → `person`).

### Derived sentence attribute: `text_source`

`text_source` is deterministic, not a Snorkel target. Precedence `quoted` > `police_matched` > `newsroom`:
- `quoted` if the sentence is inside quotation marks or is attributed speech;
- else `police_matched` if its similarity to the linked police release is above a threshold tuned on the dev set;
- else `newsroom`.

### Article-level labels

| Label | Meaning | Detection |
|---|---|---|
| `driver_ever_mentioned` | Any reference to a human driver (role noun, coreferent description, or name). Primary count uses newsroom + police-matched text; a second count includes quotes | Coreference + rules |
| `driver_exceptional` | Driver described through exceptional behaviour (fled, impaired, charged) | Rules + lexicon |
| `thematic_frame` | Mentions road design, crash trends, policy, statistics, or experts (vs. episodic only) | Classifier |
| `police_overlap` | Share of sentences closely matching the linked police release | Text similarity |
| `severity`, `road_users` | Crash metadata | Rules |
| `crash_id` | The crash the article covers, linked by date, location, and release match | Rules + release matching |
| `article_type` | `initial`, `follow_up`, or `roundup`. Primary analysis uses initial reports; follow-ups are reported separately; roundups are excluded in v1 | Rules |

### Why `driver_exceptional` matters

Fevyer & Aldred (2022) found that drivers were usually referred to only through their cars, except when they showed exceptional behaviour such as failing to stop, which made them "rogue drivers." So a hit-and-run story that mentions "the driver" is not evidence of balanced framing. Report `driver_ever_mentioned` separately for exceptional and ordinary cases.

### Legitimate exceptions to record, not penalize
- Hit-and-runs where the driver is unknown.
- Text inside quotes. It is scored separately as source framing, not newsroom framing.

Write `codebook.md` with two or more real Toronto examples per label before labeling begins. Record the IDs of every example article and sentence in `eval/excluded_ids.txt` so they never enter the test or dev set. Use the Ralph et al. coding instrument and the Road Collision Reporting Guidelines as references for edge cases.

## 8. Models

### 8.1 Crash framing
- **Primary: spaCy dependency rules.** Voice, focus, and metonymy are grammatical, so rules are precise and explainable. Patterns: `nsubjpass` + `agent`; vehicle noun (car, SUV, truck, vehicle, van, streetcar, bus, TTC bus) as `nsubj` of hit/strike/strike down/run over/collide; VRU as `nsubj` of "collide with" or head of "in collision with". A rule-based crash-report extraction system from ORNL outperformed GPT-4o on subject–action–object extraction, which supports this choice.
- **Coreference: fastcoref** with the default FCoref model (LingMess fails on current transformers; see `DECISIONS.md`) to link "the driver", "he", and "a 34-year-old man" for `driver_ever_mentioned`. If the LingMess checkpoint's license is unclear, use the default FCoref model.
- **Grammatical labels (`voice`, `driver_reference`, `focus`, `vru_as_actor`, `accident_term`):** the rules are the reported system. They also serve as labeling functions, but no trained model is built for these labels.
- **Fuzzy labels (`vru_conduct_detail`, `thematic_frame`):** the only labels that get Snorkel + a trained model: SetFit on `all-MiniLM-L6-v2`, trained on Snorkel's labels (Section 9). No hand-labeled training data.
- **Baseline:** zero-shot NLI classifier `MoritzLaurer/deberta-v3-base-zeroshot-v2.0` (MIT license) on the same test set. Each label is written as a hypothesis, e.g. "This sentence says a driver caused the crash." `facebook/bart-large-mnli` is an older, weaker fallback.

### 8.2 Police release overlap
- Sentence embeddings (`sentence-transformers/all-mpnet-base-v2`) plus character n-gram overlap to find article sentences copied or lightly edited from the police release.
- Report framing labels three ways, by `text_source`: `police_matched` (reporter text that matches the release), `newsroom` (reporter text that does not), and `quoted`.
- This tests a claim that recurs in the literature: that news outlets often copy police language verbatim, and that journalists rely heavily on police releases.

### 8.3 Quotes and sources
- Reuse the Gender Gap Tracker quote extractor (SFU Discourse Processing Lab). It already targets Canadian English outlets including CBC and CTV. The code is provided as-is, so expect dependency fixes.
- Fallback: spaCy + regex for direct quotes and speech verbs.
- Source role categories for v1.5: police, driver/driver group, cyclist/pedestrian/advocate, business, politician (city), politician (province), expert, resident.

### 8.4 Bike lane and transit stance (v1.5)
- **Frames:** Policy Frames Codebook (Boydstun et al.), 15 categories. Focus on economic, safety, political, and quality-of-life frames. The Media Frames Corpus can serve as pre-training data, with domain shift expected.
- **Stance:** Snorkel combines labeling functions (stance lexicons, source-role counts, zero-shot NLI, Qwen) into training labels → fine-tune DeBERTa-v3 or ModernBERT (8192-token context fits whole articles). Hand-label a small test set only.
- **Target split:** label stance toward *cycling infrastructure* and toward *cyclists* separately (Rissel et al. 2010).
- **Test-set selection:** besides the random sample, label sentences where labeling functions disagree most (Section 9.5).
- **Baselines:** the zero-shot NLI model, and `mediabiasgroup/da-roberta-babe-ft` for general loaded language. Report BABE as a feature only. It was trained on US political news and does not measure anti-transit stance.

Zero-shot NLI handles explicit stance but will likely miss implicit framing (e.g., a story that quotes only business owners). Source counts by role cover part of that gap without a classifier. Report zero-shot and fine-tuned results against the same test set.

## 9. Automated labeling

Training labels are produced automatically. Hand labeling is reserved for the test and dev sets. Snorkel and trained end models apply only to `vru_conduct_detail` and `thematic_frame`. For the grammatical labels the rules are the reported system; they also vote as labeling functions so their agreement with NLI and Qwen feeds triage (9.5), but no model is trained on them. This follows what similar projects did: BABE pre-trained on distant labels and tested on expert labels; Anno-lexical trained on 48k LLM-made labels and tested on human benchmarks (BABE, BASIL); the Gender Gap Tracker used a rule pipeline and tested on manually annotated articles.

### 9.1 Weak supervision with Snorkel

Each labeling function votes on a label or abstains. Snorkel estimates each function's accuracy from where they agree and disagree, without ground truth, and outputs probabilistic labels for the whole corpus. Snorkel's authors report results within an average 3.6% of models trained on large hand-labeled sets.

Labeling functions:

| Function | Labels it votes on |
|---|---|
| spaCy dependency rules | `voice`, `driver_reference`, `focus`, `vru_as_actor` |
| Lexicons ("accident"; helmet, dark clothing, headphones, mid-block, jaywalk) | `accident_term`, `vru_conduct_detail` |
| Thematic cue lexicon (statistics, "this year", road design, Vision Zero, experts) | `thematic_frame` |
| Zero-shot NLI (`deberta-v3-base-zeroshot-v2.0`) | all labels, as hypotheses |
| Qwen via Ollama, few-shot prompt built from `codebook.md` examples | all labels |

`text_source` is not a labeling target; it is derived deterministically (Section 7).

The end model (SetFit on `all-MiniLM-L6-v2`) trains on Snorkel's labels for `vru_conduct_detail` and `thematic_frame` only. Following Anno-lexical, check that the trained model beats each individual labeling function on the test set; if it does not, the extra step adds nothing.

### 9.2 Qwen as a labeler

- Runs locally through Ollama. No API, no data leaves the machine.
- Non-thinking mode, temperature 0, fixed seed, JSON output constrained to the codebook's label set via a schema.
- The prompt contains the codebook definitions and 2–3 examples per label. Prompt text is versioned in the repo.
- Responses cached to disk keyed by (model digest, prompt hash, sentence ID).
- Qwen is one vote among several, never the sole source of a label.

### 9.3 Template test suite

Generate minimal pairs from templates where the label is known by construction, in the style of CheckList behavioral testing:

- "A driver struck a cyclist." / "A cyclist was struck by a driver." / "A cyclist was struck." / "A car struck a cyclist." / "A cyclist collided with a car."
- Vary road user (pedestrian, cyclist), vehicle (car, SUV, truck, TTC bus, streetcar), verb (hit, struck, ran over, pinned), tense, and added clauses.

This runs in CI as a unit test for the grammatical rules. It catches rule bugs automatically. It does not measure real-world accuracy, because templates are cleaner than news text.

### 9.4 Public validation sets for components

- Passive detection: Universal Dependencies English treebanks (EWT, PUD), which mark `nsubj:pass`, `aux:pass`, and `Voice=Pass`.
- Quote stripping: PolNeAR (political news attribution relations; code at networkdynamics/PolNeAR).
- Coreference: cite fastcoref's published OntoNotes scores.

Report these as component metrics, separate from end-to-end results.

### 9.5 Agreement-based triage

Run rules, NLI, and Qwen on every crash sentence. Where all agree, the label is high-confidence. Where they disagree, the sentence goes into a review queue. Disagreements also feed the error analysis.

### 9.6 What stays manual

- The test set (Section 10). Agreement between automated labelers is not accuracy: if they share a blind spot ("pinned under a truck"), they agree and are all wrong.
- Never use outlet identity as a label. BABE used outlet-level distant labels, but here that would assume which outlets are biased, which is the research question.

## 10. Evaluation

- Test set: about 100 crash-describing sentences, labeled by an independent annotator subagent (an LLM, not a human) that sees only `codebook.md` and the raw sentences.
  - 60 sampled at random, stratified by outlet and year. **Headline metrics come from this part only**, since it represents the corpus.
  - 40 sampled from triage disagreements. Used for error analysis, reported separately, never pooled into headline metrics.
- A second independent annotator subagent labels 30 of them. Report agreement (Cohen's kappa). Agreement between two LLM annotators is not the same as human agreement; say so.
- Metrics: per-label precision, recall, F1; confusion matrix; macro-F1. Rare labels (e.g. `vru_as_actor`) will have wide intervals with this sample size; say so.
- Report each labeling function, Snorkel's label model, and the trained end model on the same test set (for the grammatical labels, the rules are the reported system).
- Dev set: about 30 sentences, labeled for all sentence labels plus `text_source` so the release-match threshold can be tuned.
- The test/dev sampler skips every ID in `eval/excluded_ids.txt` (codebook and prompt examples). A unit test enforces this.
- Total annotator labeling: about 160 sentence passes (test, dev, and 30 second-annotator labels).
- Error analysis: read every error in the disagreement sample and categorize causes.
- Hold out the test set. Never tune rules, prompts, or thresholds on it. Use a separate small dev set (about 30 sentences) for tuning.
- Outlet comparisons: report rates with confidence intervals (bootstrap over articles). Do not rank outlets on differences inside the intervals.
- Sanity check against prior work: compare overall rates (e.g., share of agentless or vehicle-as-agent sentences, share of articles with thematic framing) with the US, UK, Dutch, and Swiss studies. Differences are findings, not errors, but very large gaps should trigger a recheck of the rules.

### Presentation lesson from Vision Zero Reporting
That tool gives each article a letter grade. A road.cc reader reported it gave a B to an article with no problems. Single grades hide what drove the score and invite disputes. This project shows per-sentence labels with evidence and reports rates, not grades.

## 11. Phases

### Phase 0: Codebook and setup (week 1)
- Feasibility first: check the Toronto Police news release archive covers the time window and allows fetching; install the full stack together on Python 3.11 and confirm it runs on CPU and MPS.
- Record the license of every model and reused code. Where a license is unclear, use the alternative (default FCoref instead of LingMess; spaCy + regex quote fallback instead of Gender Gap Tracker code).
- Repo skeleton (GitHub, GitHub Actions CI), environment, CLAUDE.md, codebook.md.
- Check robots.txt and terms for each outlet; flag any that fail.
- Read Ralph et al. 2019, Goddard et al. 2019, Fevyer & Aldred 2022, Reymond & Rérat, and the Road Collision Reporting Guidelines. Note each one's labels in `docs/related-work.md`.
- Bike Frames stays in related work only; it is not an evaluation set. (The author contact was dropped in autonomous mode.)
- Deliverable: codebook with Toronto examples; `eval/excluded_ids.txt`; empty pipeline that runs end to end on 5 articles.

### Phase 1: Corpus (weeks 2–3)
- URL discovery, extraction, topic tags, crash metadata, dedupe, SQLite.
- Toronto Police news release collection and article-to-release linking.
- Deliverable: 1–3k articles plus matching releases; re-runnable collection script; corpus stats table (articles per outlet per month, share linked to a release).

### Phase 2: Crash framing detector (weeks 4–5)
- Sentence filter, quote stripping, dependency rules, coreference, lexicons, release-overlap scoring.
- Template test suite in CI; component checks on UD and PolNeAR.
- Labeling functions + Snorkel label model; Qwen labeler via Ollama; triage queue.
- Train SetFit/DeBERTa on Snorkel labels for `vru_conduct_detail` and `thematic_frame` only.
- Annotator subagents label the 100-sentence test set and 30-sentence dev set; evaluate every labeling function, the label model, and the end model.
- Deliverable: `nlp/` labeler, eval report with component metrics, end-to-end metrics, and error analysis.

### Phase 3: Analysis and front end (weeks 6–7)
- Framing rates by outlet and month; headline vs. body; newsroom vs. police-matched vs. quoted text; exceptional vs. ordinary drivers; fatal vs. non-fatal; initial reports vs. follow-ups; with and without wire copy.
- Comparison with rates from prior studies.
- Streamlit dashboard with aggregate rates and at most one flagged sentence per article as an excerpt.
- Local-only article viewer with per-sentence labels and release matches.
- Deliverable: dashboard that is ready to deploy (hosting needs an account, so it runs locally in autonomous mode); write-up that states the key result in its first paragraph; SUMMARY.md.

**v1 = Phases 0–3.**

### Phase 4 (v1.5): Bike lanes and transit (week 8)
- Source counting by role, policy frames, stance toward cycling vs. cyclists, Bill 212 timeline.
- Deliverable: second dashboard view and an addendum to the write-up.

## 12. Repo structure

```
media-bias/
  PLAN.md
  CLAUDE.md
  codebook.md
  docs/
    related-work.md   # labels and findings from prior studies, for comparison
  pyproject.toml
  collect/        # URL discovery, fetch, extract, dedupe, police releases
  nlp/            # sentence filter, quotes, rules, coref, overlap, classifiers
    labeling/     # labeling functions, Snorkel label model, Qwen labeler, prompts
  eval/           # test/dev labels (CSV), excluded_ids.txt, template suite, UD/PolNeAR checks, metrics
  analysis/       # notebooks, aggregate tables, figures
  app/            # dashboard
  tests/
  data/           # SQLite + raw HTML (gitignored)
```

## 13. Risks

| Risk | Mitigation |
|---|---|
| Paywalls block Star/Globe | Defer; note the gap in the write-up |
| Too few crash articles per outlet | Include non-fatal crashes; widen the date window; pool by outlet type |
| Police release language dominates | Release matching; report newsroom and police-matched text separately |
| Some articles have no linkable police release | Report the matched share; analyze unmatched articles as their own group |
| Wayback coverage of TPS releases is partial and may not be random | Police comparison is secondary, on the matched subset only; bias check compares matched and unmatched articles |
| Wire copy inflates counts | Dedupe before any aggregation |
| Author's own view shapes labels | Written codebook from published instruments, random sampling, double-labeling subset |
| Hit-and-run stories inflate "driver mentioned" rates | `driver_exceptional` flag; report split |
| Follow-up stories (charges laid) inflate exceptional-driver counts | `crash_id` and `article_type`; primary analysis on initial reports |
| Outlet sites or archives unreachable or slow from the author's network | Sitemaps first, GDELT as fallback; exclude unreachable outlets and log it |
| Gender Gap Tracker code is stale | spaCy + regex fallback |
| Zero-shot NLI misses implicit framing | Add or fix labeling functions; retrain on Snorkel labels; add source-role counts |
| Labeling functions share blind spots, so Snorkel is confidently wrong | Diverse function types (syntax, lexicon, NLI, LLM); the annotator-labeled test set measures it |
| Qwen output drifts or breaks format | Pinned digest, temperature 0, JSON schema, cache; invalid output counts as abstain |
| Qwen too slow on a laptop for the full corpus | Run only on crash sentences (thousands, not millions); batch overnight; smaller Qwen if needed |
| Template suite passes but real text fails | Templates are unit tests only; real accuracy comes from the test set |
| 100-sentence test set too small for rare labels | Report intervals; extend the test set for rare labels if they drive a finding |
| No GPU and 8 GB RAM | Base-size NLI, small SetFit model, one model in memory at a time, cached outputs |

## 14. Related work

**Effects of framing on readers.**
- Goddard, Ralph, Thigpen & Iacobucci (2019), *Transportation Research Interdisciplinary Perspectives*. Experiment with 999 readers; driver-focused language reduced victim-blaming and thematic framing raised support for systemic fixes. A German replication found the same effects. This project does not test effects; it measures how often the patterns these studies tested appear in Toronto coverage.

**Manual content analyses of crash coverage.** All hand-coded, each a few hundred articles, none Canadian.
- Ralph, Iacobucci, Thigpen & Goddard (2019): 200 US local news articles. Source of the sentence-level codebook.
- Fevyer & Aldred (2022), *Mobilities*: Evening Standard, 2012–2019. Drivers referred to through their cars except as "rogue drivers"; cyclists always referred to directly. Source of `driver_exceptional`.
- "Framing systemic traffic violence: Media coverage of Dutch traffic crashes" (University of Amsterdam; verify author list): 368 local Dutch reports, including non-fatal crashes and all vehicle types. Source of the decision to include non-fatal crashes.
- Reymond & Rérat (*Findings*): 204 Swiss articles, 2020–2024. Uses the five-dimension structure this codebook adopts. Did not assess police influence; this project does.
- Von Schneidemesser et al. (2025), *Mobilities*: German-speaking countries; passive voice, metonymy, and reflexive verbs.
- Parachute (2020): Vision Zero media audit across Canadian jurisdictions. Covers Vision Zero policy coverage, not sentence-level crash framing, but is the closest Canadian precedent.

This project automates the sentence-level coding these studies did by hand, which allows a full multi-year corpus instead of a sample.

**Police press releases.**
- Ralph, Goddard, Thigpen & Davis (2022), "Intervening at the blotter, not the broadcast": journalists draw heavily from police releases; produced a guide for police.
- Laker (2024, for the Foundation for Integrated Transport): 227 UK police releases; "accident" is now rare, but 70% describe vehicles as autonomous agents. These studies examine releases or articles separately. This project links each article to its release and measures what the newsroom changed.

**Automated tools.**
- Zhao et al., "Bike Frames" (ICWSM 2025): 31,480 US headlines, 1,500 annotations; LLM chain-of-code for accident detection, fault, and cyclist perception. Headlines only, uses an LLM, US only. This project uses full text, open local models, and Canadian outlets. Bike Frames is not used as an evaluation set here, because its unit (headline), labels, and country differ. Their finding that outlet information improves prediction suggests outlet-level differences are real and worth reporting.
- Vision Zero Reporting (Lang, 2021): pastes in an article and returns a letter grade on six problems, built on Ralph et al. Method and code are not public. This project publishes its method, reports per-sentence evidence instead of grades, and evaluates against a labeled test set.

**Quote extraction.**
- Asr et al. (2021), Gender Gap Tracker, *PLoS ONE*: quote and speaker extraction on seven Canadian English outlets. Reused here for quote stripping and source counts.

**Cycling coverage and frames (v1.5).**
- Rissel et al. (2010): Sydney and Melbourne newspapers; coverage varied by outlet and over time; "cycling" framed more positively than "cyclists". Source of the cycling vs. cyclists split.
- Card et al. (2015), Media Frames Corpus; Boydstun et al., Policy Frames Codebook.
- Spinde et al. (2021), BABE media bias dataset.

**Reporting guidelines (used for rewrite suggestions, not for labels).**
- Road Collision Reporting Guidelines (Laker & Active Travel Academy, 2021), UK.
- Ralph et al., Guide to Improving Police Press Releases About Car Crashes (Rutgers).

**Automated labeling.**
- Ratner et al. (2017/2020), Snorkel: combines noisy labeling functions without ground truth. Used here as the main source of training labels.
- Spinde et al. (2021), BABE: pre-trained on distant labels from outlet identity, then fine-tuned and tested on 3,700 expert-labeled sentences. This project borrows the train-on-weak, test-on-human split but rejects outlet-based labels.
- Horych et al. (2025), Anno-lexical (NAACL Findings): 48k LLM-labeled sentences; the trained classifier beat each annotator LLM by 5–9%. This project uses a local open model (Qwen) as one Snorkel input rather than as the only labeler.
- Ribeiro et al. (2020), CheckList: template-based behavioral tests. Basis for the template suite.
- Newell et al. (2018), PolNeAR; Universal Dependencies English treebanks: public component checks.

**Models and tools.** spaCy, fastcoref, sentence-transformers, Snorkel, Ollama + Qwen, SetFit, Laurer et al. zeroshot-v2.0 NLI classifiers (arXiv:2312.17543), trafilatura, GDELT, Wayback Machine.
