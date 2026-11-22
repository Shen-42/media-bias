# Progress

Autonomous run of Phases 0–3. Updated after each task. A new session resumes from "Next".

## Done
- Phase 0: plan decisions (PLAN.md §3); CLAUDE.md autonomous rules; skeleton; device detection; TPS archive check; dependency spike; codebook v1.0 (D-01..D-18); sources, licenses, config pins, lockfile; GitHub repo with CI.
- Phase 1 code: sitemap discovery with fetch tiers (D-32, D-38), polite fetcher, Wayback police releases, crash metadata and linking (D-39, D-40), dedupe (D-34).
- Phase 2 code: sentence split and crash filter, dependency rules (template suite 312/312), quotes, overlap/text_source, coref, NLI, Qwen labeler, LFs, Snorkel fit/predict, SetFit, labeling orchestrator, eval sampler with excluded_ids test, triage, scoring (P/R/F1, macro-F1, bootstrap CI, kappa), dev-only threshold tuning, article labels.
- Phase 3 code: analysis/aggregate.py (cluster bootstrap CIs; text_source, headline/body, outlet with/without wire, year, fatal, initial/follow-up, exceptional driver split, matched-vs-unmatched check, corpus stats, excerpts); Streamlit app (public/local modes); README with LLM-annotator disclosure; docs/method.md; run_pipeline.sh.
- Dry run of every pipeline step on the partial corpus succeeded. Qwen (digest pinned, ~3 s/sentence) and NLI (MPS, ~0.5 s/pair) smoke-tested.
- UD EWT passive component check: clausal participles P 0.92 / R 0.80 / F1 0.85 (D-41). PolNeAR skipped (no license, D-42).
- Annotator instructions (eval/annotation/instructions.md) and merge tool (eval/merge_labels.py).
- Coverage rules (D-45): outlet comparisons in the common window, per-outlet trends, Bill 212 pre/post (cutoff 2024-11-25, D-47) only for outlets on both sides, coverage-by-quarter table. Wayback distinction logged (D-46). docs/writeup.md skeleton with coverage, methods and limitations sections.
- Police releases complete (2026-11-19 19:54, retry pass done): 5,336 of 5,347 archived IDs; 5,219 in window; 334 collision releases; 11 unrecoverable 404s (D-49).
- Pooled tables each have a per-outlet breakdown and outlet sample shares with the largest contributor flagged (D-48); shown in the dashboard; app handles empty tables (headless smoke test passes).

## Outlets
- Collected: CityNews Toronto, CTV News Toronto (sitemaps start 2025; 2023-24 daily sitemaps are empty), Global News (national; Toronto filter applies).
- Dropped: Toronto Sun (Postmedia terms ban scraping, D-19); blogTO and Toronto Today (403 / Cloudflare to scripted clients; Wayback copies not used either, D-20); CBC (robots.txt unreachable from this network, last retried 2026-11-19, D-22/D-33).

## Collection resilience (D-43)
- Every per-item result is committed to SQLite, so a killed or slept process resumes from where it stopped on restart.
- Article fetch: failures stored as `failed:*` per URL and printed to the log; `--retry-failed` requeues them (not blocks or 404s). Police: non-ok IDs are retried automatically on rerun.
- Fetcher waits out network outages (up to 2 h) instead of failing a run of URLs. Discovery skips and logs failed sitemaps, records finished ones, and treats non-200 as failed.
- Jobs started before this change (police, CityNews fetch, CTV discovery) run old code; the retry pass in Next step 1 covers them. Failures so far: 0.

## Phase 3 run (finished 2026-11-20)
- Rescope after annotator findings (D-54, D-56, D-58): 942 in-scope articles, 3,114 crash sentences, 218 release-linked.
- Eval: dev 100 rows and test 240 rows (160 random + 80 disagreement) labeled by claude-subagent; out-of-scope rows replaced (D-55); second annotator 30 rows (kappa 1.0 on 26 crash rows).
- Pipeline: tune (dev macro-F1 0.915, thresholds embed 0.6 / char 0.2), Snorkel, SetFit, article labels, scoring, aggregates. Offline model loading (D-59).
- docs/writeup.md filled; docs/related-work.md has verified Ralph et al. (2019) rates; SUMMARY.md written.
- CLAUDE.md untracked and removed from git history (D-57).

## Phase 4 (v1.5), started 2026-11-20
Done:
- Model choice: Snorkel + SetFit for stance and frames (author, D-60). CLAUDE.md updated.
- Codebook Part B draft (sections 7–9): topic, source_role, policy_frame, three stance targets, loaded_language feature (D-63); label mapping in docs/related-work.md.
- Bill 212 timeline with sources (`analysis/timeline_bill212.csv`, D-64).
- Fetch fix for non-crash topics (D-62); broader bike lane slugs and `--rescan` (D-61); topic tagger `nlp/topic.py` (D-65).
- Source extraction `nlp/sources.py` (D-66); v1.5 LFs, NLI hypotheses, Qwen prompt `v15_v1.txt` (D-67).
- v1.5 pipeline `nlp/v15.py` (topics, sources, pools, nli, qwen, snorkel, setfit, babe; D-72), eval sampler `eval/sample_v15.py` and merge `eval/merge_v15.py` (D-73), scorer `eval/score_v15.py`, tables `analysis/aggregate_v15.py`, dashboard tab, `run_v15.sh`.
- Collection: CTV and Global fetch + rescan done; CityNews fetch done (2026-11-21).

## v1 follow-ups (2026-11-21)
- Global drop traced: Global stopped running routine Toronto crash briefs after June 2024; not a collection defect (D-68). Write-up and SUMMARY updated.
- Codebook v1.1 settles the five annotator gaps (D-69); rules updated with tests; all test/dev crash rows relabeled blind (8 of 100 test labels changed; second annotator unchanged). v1.0 metrics kept as `eval/reports/*_v10.csv`.
- Fuzzy-label rework (D-70, D-71): dev +100 context rows; NLI cutoffs and Snorkel/SetFit thresholds tuned on dev (`eval/tune_fuzzy.py`); SetFit trains at up to 3:1 negatives.

## v1.5 run (finished 2026-11-22)
- Sampling chain finished (V15_SAMPLE_DONE). Topics and sources re-run under D-76/D-77: 1,167 articles in scope; out-of-scope eval rows dropped (D-79).
- Dev-only fix for `policy_frame` = `other` (frame lexicon cues, NLI hypothesis; D-78); NLI, Snorkel and SetFit re-run.
- 40 disagreement rows annotated and merged. Scores in `eval/reports/v15_*.csv`; tables in `analysis/tables/v15_*.csv`.
- Result: SetFit stance and frame rates fail validation and are not findings (D-80); dashboard tab shows them under a warning. Write-up addendum, SUMMARY updated.

- Author chose to count attributed positions as stance (D-81). Stance relabeled blind on test, dev and the second annotator; dev stance sample added (D-82); removal rule, Qwen prompt v15_v3 and a no-cue `none` LF (D-83); NLI, Qwen, Snorkel and SetFit re-run.
- Stance rates are reported from annotated samples; stance tables come from Snorkel on the pool's random target-mention stratum (D-84), exploratory. Write-up addendum, SUMMARY and dashboard warning rewritten. Pushed.

## v1.5 measurement (2026-11-22)
- Measurement sample `eval/measure_v15.csv` (D-85): 1,613 body sentences annotated (census of bike infrastructure/cyclist sentences, 200 transit per outlet); second annotator on 100. Tables `analysis/tables/v15m_*.csv` from `analysis/measure_v15.py`; dashboard v1.5 tab reads them.
- `stance_holder` added to codebook 9.2 and labeled on the 512 stance rows (D-87): 7 are the outlet's own position.
- Transit stance end model (D-86): SetFit on the real Snorkel class mix, `python -m nlp.v15 --steps endmodel`; failed the pre-set validation on newsroom text (`eval/validate_endmodel.py`, D-88). Snorkel stance tables dropped.

- Step 3 done: Qwen's infrastructure stance vote removed from Snorkel (D-89); prompt stays v3.

- Step 4 done: frames reported from the measurement sample; SetFit frame tables dropped (D-90).

- Quality checks done (D-91 attribution, D-92 transit topic, D-93 source roles); public-data research in `docs/public-data.md`.

- PolNeAR attribution check done (D-94): precision 0.90, recall 0.49 (`eval/reports/polnear_attribution.csv`). Snorkel and the transit end model refit after D-92; end model still fails validation on newsroom text.

Next (author's order, 2026-11-22): remaining public-data checks (`docs/public-data.md`: Media Frames Corpus, TPS KSI); old list: then quality checks (source roles, transit topic precision, attribution detector recall, human-labeled sample).

## Blockers
- None.
